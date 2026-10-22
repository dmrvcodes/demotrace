"""Asynchronous Lambda worker: claim the job, prepare media, ask Claude, validate, save, clean up.

Every failure is attributed to the stage it happened in, so a failed job says what actually broke.
One JSON line per job goes to the log: ids, stage, error type, code, durations and token counts.
Never the transcript, the prompt, the API key or any URL.
"""

import json
import os
import tempfile
import time
import uuid
from decimal import Decimal
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from demotrace_shared.errors import ERROR_MESSAGES, ErrorCode

from .llm import ModelError
from .llm.client import call_model, make_client
from .llm.prompt import build_request
from .media import MediaError
from .prepare import prepare
from .smoke import load_frames
from .stages import StageTracker
from .validate import assemble_result, confidences

# What a stage's unexpected failure means when the error carries no code of its own.
STAGE_FALLBACK = {
    "download": ErrorCode.STORAGE_ERROR,
    "validate": ErrorCode.MODEL_INVALID_OUTPUT,
    "save": ErrorCode.STORAGE_ERROR,
}


def _clients():
    return boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE_NAME"]), boto3.client("s3"), boto3.client("secretsmanager")


def _api_key(secrets) -> str:
    value = secrets.get_secret_value(SecretId=os.environ["ANTHROPIC_SECRET_ARN"])["SecretString"]
    return json.loads(value).get("ANTHROPIC_API_KEY", value) if value.startswith("{") else value


def _dynamo(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_dynamo(item) for item in value]
    if isinstance(value, dict):
        return {key: _dynamo(item) for key, item in value.items()}
    return value


def _conditional_failed(error: BaseException) -> bool:
    return isinstance(error, ClientError) and error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"


def error_code(error: BaseException, stage: str | None) -> ErrorCode:
    if isinstance(error, (ModelError, MediaError)):
        return ErrorCode(error.code)
    return STAGE_FALLBACK.get(stage or "", ErrorCode.INTERNAL_ERROR)


def _log(**fields) -> None:
    print(json.dumps({"event": "demotrace_job", **fields}, separators=(",", ":"), default=str))


def handler(event, context):
    job_id, key, version, claims = event["job_id"], event["key"], event["version_id"], event["claims"]
    table, s3, secrets = _clients()
    pk = {"pk": f"JOB#{job_id}"}
    run_id = str(uuid.uuid4())
    names = {"#s": "status"}

    try:
        table.update_item(
            Key=pk,
            UpdateExpression="SET #s=:processing, run_id=:run, started_at=:now",
            ConditionExpression="#s=:queued",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues={":processing": "processing", ":queued": "queued", ":run": run_id,
                                       ":now": int(time.time())},
        )
    except ClientError as error:
        if _conditional_failed(error):
            _log(job_id=job_id, outcome="duplicate")  # another delivery already took this job
            return {"outcome": "duplicate"}
        _log(job_id=job_id, outcome="claim_error", error_type=type(error).__name__)
        raise

    tracker = StageTracker()
    info: dict = {}
    mine = {":processing": "processing", ":run": run_id}
    ownership = "#s=:processing AND run_id=:run"
    try:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            video = work / "input"
            with tracker.stage("download"):
                s3.download_file(os.environ["VIDEOS_BUCKET_NAME"], key, str(video), ExtraArgs={"VersionId": version})
            media = prepare(video, work / "prepared", tracker=tracker)
            info.update(frames=len(media.frames), segments=len(media.segments))
            with tracker.stage("secret"):
                os.environ["ANTHROPIC_API_KEY"] = _api_key(secrets)
            with tracker.stage("model"):
                request = build_request(media, load_frames(work / "prepared", media), claims)
                info.update(model=request.params["model"], request_bytes=request.size_bytes)
                result = call_model(make_client(), request,
                                    time_left_s=lambda: context.get_remaining_time_in_millis() / 1000)
                info.update(input_tokens=result.usage.get("input_tokens"),
                            output_tokens=result.usage.get("output_tokens"))
            with tracker.stage("validate"):
                payload = assemble_result(media, result.answer, claims)
        with tracker.stage("save"):
            table.update_item(
                Key=pk,
                UpdateExpression=("SET #s=:completed, #r=:result, model_confidence=:conf, timings=:timings, "
                                  "finished_at=:now"),
                ConditionExpression=ownership,
                ExpressionAttributeNames={**names, "#r": "result"},
                ExpressionAttributeValues={**mine, ":completed": "completed", ":result": _dynamo(payload),
                                           ":conf": confidences(result.answer),
                                           ":timings": _dynamo(tracker.durations), ":now": int(time.time())},
            )
        _log(job_id=job_id, outcome="completed", durations_s=tracker.durations, **info)
        return {"outcome": "completed"}
    except Exception as error:
        stage = tracker.failed or tracker.current or "worker"
        if stage == "save" and _conditional_failed(error):
            # A read-time timeout already failed this job; never overwrite it.
            _log(job_id=job_id, outcome="superseded", stage=stage, durations_s=tracker.durations, **info)
            return {"outcome": "superseded"}
        code = error_code(error, stage)
        _log(job_id=job_id, outcome="failed", stage=stage, error_type=type(error).__name__, code=str(code),
             durations_s=tracker.durations, **info)
        try:
            table.update_item(
                Key=pk,
                UpdateExpression=("SET #s=:failed, error_code=:code, error_message=:message, failed_stage=:stage, "
                                  "timings=:timings, finished_at=:now"),
                ConditionExpression=ownership,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues={**mine, ":failed": "failed", ":code": str(code),
                                           ":message": ERROR_MESSAGES[code], ":stage": stage,
                                           ":timings": _dynamo(tracker.durations), ":now": int(time.time())},
            )
        except ClientError as update_error:
            if not _conditional_failed(update_error):
                raise
            _log(job_id=job_id, outcome="superseded", stage=stage)
        return {"outcome": "failed", "code": str(code), "stage": stage}
    finally:
        try:
            s3.delete_object(Bucket=os.environ["VIDEOS_BUCKET_NAME"], Key=key, VersionId=version)
        except Exception as error:  # the S3 lifecycle rule is the backstop
            _log(job_id=job_id, outcome="cleanup_error", error_type=type(error).__name__)
