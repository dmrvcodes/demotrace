"""Asynchronous Lambda worker: prepare media, ask Claude, and fail closed."""
import json, os, tempfile, time
from decimal import Decimal
from pathlib import Path
import boto3
from demotrace_shared.errors import ERROR_MESSAGES, ErrorCode
from .llm import ModelError
from .llm.client import call_model, make_client
from .llm.prompt import build_request
from .prepare import prepare
from .smoke import load_frames
from .media import MediaError

def _api_key():
    value = boto3.client("secretsmanager").get_secret_value(SecretId=os.environ["ANTHROPIC_SECRET_ARN"])["SecretString"]
    return json.loads(value).get("ANTHROPIC_API_KEY", value) if value.startswith("{") else value

def _dynamo(value):
    if isinstance(value, float): return Decimal(str(value))
    if isinstance(value, list): return [_dynamo(item) for item in value]
    if isinstance(value, dict): return {key: _dynamo(item) for key, item in value.items()}
    return value

def handler(event, context):
    job_id, key, version, claims = event["job_id"], event["key"], event["version_id"], event["claims"]
    table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE_NAME"]); s3 = boto3.client("s3")
    try:
        table.update_item(Key={"pk": f"JOB#{job_id}"}, UpdateExpression="SET #s=:processing, started_at=:now", ConditionExpression="#s=:queued", ExpressionAttributeNames={"#s":"status"}, ExpressionAttributeValues={":processing":"processing",":queued":"queued",":now":int(time.time())})
    except Exception: return {"duplicate": True}
    try:
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "input.mp4"; s3.download_file(os.environ["VIDEOS_BUCKET_NAME"], key, str(video), ExtraArgs={"VersionId": version})
            media = prepare(video, Path(directory) / "prepared")
            os.environ["ANTHROPIC_API_KEY"] = _api_key()
            answer = call_model(make_client(), build_request(media, load_frames(Path(directory) / "prepared", media), claims), time_left_s=lambda: context.get_remaining_time_in_millis() / 1000).answer
            refs = {frame.id: ("frame", frame.t) for frame in media.frames} | {segment.id: ("speech", segment.start) for segment in media.segments}
            by_id = {claim.claim_id: claim for claim in answer.claims}
            results = []
            for number, text in enumerate(claims, 1):
                claim = by_id[f"C{number}"]; evidence = [{"ref_id": ref, "kind": refs[ref][0], "t": refs[ref][1]} for ref in claim.evidence_ids]
                if any(ref not in refs for ref in claim.evidence_ids) or (claim.status.value == "shown" and not any(e["kind"] == "frame" for e in evidence)) or (claim.status.value == "missing" and evidence): raise ModelError(ErrorCode.MODEL_INVALID_OUTPUT, "invalid evidence")
                results.append({"claim_id": f"C{number}", "text": text, "status": claim.status.value, "explanation": claim.explanation, "evidence": evidence})
            table.update_item(Key={"pk": f"JOB#{job_id}"}, UpdateExpression="SET #s=:completed, result=:result, finished_at=:now", ConditionExpression="#s=:processing", ExpressionAttributeNames={"#s":"status"}, ExpressionAttributeValues={":completed":"completed",":processing":"processing",":result":_dynamo({"schema_version":1,"duration_s":media.duration_s,"claims":results}),":now":int(time.time())})
    except (ModelError, MediaError, Exception) as error:
        code = error.code if isinstance(error, (ModelError, MediaError)) else ErrorCode.MODEL_UNAVAILABLE
        table.update_item(Key={"pk": f"JOB#{job_id}"}, UpdateExpression="SET #s=:failed, error_code=:code, error_message=:message", ExpressionAttributeNames={"#s":"status"}, ExpressionAttributeValues={":failed":"failed",":code":str(code),":message":ERROR_MESSAGES[code]})
    finally:
        try: s3.delete_object(Bucket=os.environ["VIDEOS_BUCKET_NAME"], Key=key, VersionId=version)
        except Exception: pass
