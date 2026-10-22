"""The worker handler against in-memory fakes: no AWS, no model, no ffmpeg."""

import json
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from demotrace import handler as worker
from demotrace.llm import ModelError
from demotrace.llm.client import ModelResult
from demotrace.llm.prompt import ModelRequest
from demotrace.media import MediaError
from demotrace_shared.errors import ErrorCode
from demotrace_shared.media import Frame, PreparedMedia, SpeechSegment

from .test_validate import CLAIMS, GOOD

MEDIA = PreparedMedia(
    duration_s=60.0, has_audio=True, width=1280, height=720, video_codec="h264",
    frames=[Frame(id="F001", t=0.0, file="F001.jpg", width=1024, height=576, bytes=1),
            Frame(id="F002", t=41.0, file="F002.jpg", width=1024, height=576, bytes=1)],
    segments=[SpeechSegment(id="S01", start=3.2, end=6.0, text="SECRET TRANSCRIPT TEXT")],
    sampling_step_s=1.0, candidates=2, estimated_request_bytes=0,
)
EVENT = {"job_id": "job-1", "key": "incoming/job-1", "version_id": "v1", "claims": CLAIMS}


def conditional_failed():
    return ClientError({"Error": {"Code": "ConditionalCheckFailedException", "Message": "no"}}, "UpdateItem")


class FakeTable:
    def __init__(self, status="queued"):
        self.item = {"status": status}
        self.updates = []
        self.fail_completion_with = None

    def update_item(self, **kw):
        self.updates.append(kw)
        values = kw["ExpressionAttributeValues"]
        condition = kw.get("ConditionExpression", "")
        if condition == "#s=:queued" and self.item["status"] != "queued":
            raise conditional_failed()
        if "run_id=:run" in condition:
            if self.item["status"] != "processing" or self.item.get("run_id") != values[":run"]:
                raise conditional_failed()
            if ":completed" in values and self.fail_completion_with:
                raise self.fail_completion_with
        for name in ("processing", "completed", "failed"):
            if f":{name}" in values and f"#s=:{name}" in kw["UpdateExpression"]:
                self.item["status"] = name
        if ":run" in values and "run_id=:run," in kw["UpdateExpression"]:
            self.item["run_id"] = values[":run"]
        for field in ("error_code", "failed_stage"):
            if f"{field}=:" in kw["UpdateExpression"]:
                self.item[field] = values[":code" if field == "error_code" else ":stage"]


class FakeS3:
    def __init__(self, download_error=None):
        self.download_error = download_error
        self.deleted = []

    def download_file(self, bucket, key, path, ExtraArgs):
        assert ExtraArgs == {"VersionId": "v1"}
        if self.download_error:
            raise self.download_error
        open(path, "wb").write(b"video")

    def delete_object(self, **kw):
        self.deleted.append(kw)


class FakeSecrets:
    def get_secret_value(self, SecretId):
        return {"SecretString": json.dumps({"ANTHROPIC_API_KEY": "sk-ant-test-secret"})}


CONTEXT = SimpleNamespace(get_remaining_time_in_millis=lambda: 800_000)


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("JOBS_TABLE_NAME", "jobs")
    monkeypatch.setenv("VIDEOS_BUCKET_NAME", "bucket")
    monkeypatch.setenv("ANTHROPIC_SECRET_ARN", "arn:secret")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def run(monkeypatch, capsys, *, table=None, s3=None, prepare_error=None, model_error=None, answer=GOOD):
    table = table or FakeTable()
    s3 = s3 or FakeS3()
    monkeypatch.setattr(worker, "_clients", lambda: (table, s3, FakeSecrets()))

    def fake_prepare(video, out, tracker):
        with tracker.stage("prepare"):
            with tracker.stage("transcribe"):
                if prepare_error:
                    raise prepare_error
        return MEDIA

    def fake_call(client, request, time_left_s):
        if model_error:
            raise model_error
        return ModelResult(answer=answer, usage={"input_tokens": 1000, "output_tokens": 200},
                           stop_reason="end_turn", request_id="req", elapsed_s=1.0)

    monkeypatch.setattr(worker, "prepare", fake_prepare)
    monkeypatch.setattr(worker, "load_frames", lambda d, m: [b"x", b"y"])
    monkeypatch.setattr(worker, "build_request", lambda m, i, c: ModelRequest({"model": "test-model"}, 1234))
    monkeypatch.setattr(worker, "make_client", lambda: object())
    monkeypatch.setattr(worker, "call_model", fake_call)
    out = worker.handler(dict(EVENT), CONTEXT)
    logs = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    return out, table, s3, logs


def test_completed_job_saves_result_timings_and_one_log_line(env, monkeypatch, capsys):
    out, table, s3, logs = run(monkeypatch, capsys)
    assert out == {"outcome": "completed"} and table.item["status"] == "completed"
    saved = table.updates[-1]["ExpressionAttributeValues"]
    assert saved[":result"]["claims"][0]["status"] == "shown"
    assert set(saved[":timings"]) >= {"download", "prepare", "transcribe", "secret", "model", "validate"}
    assert saved[":conf"] == {"C1": "high", "C2": "medium", "C3": "high"}
    assert s3.deleted == [{"Bucket": "bucket", "Key": "incoming/job-1", "VersionId": "v1"}]
    [log] = logs
    assert log["outcome"] == "completed" and log["input_tokens"] == 1000 and log["model"] == "test-model"


@pytest.mark.parametrize("kwargs, stage, code", [
    ({"s3": FakeS3(download_error=ClientError({"Error": {"Code": "403"}}, "GetObject"))}, "download", ErrorCode.STORAGE_ERROR),
    ({"prepare_error": MediaError(ErrorCode.VIDEO_TOO_LONG)}, "transcribe", ErrorCode.VIDEO_TOO_LONG),
    ({"prepare_error": RuntimeError("whisper exploded")}, "transcribe", ErrorCode.INTERNAL_ERROR),
    ({"model_error": ModelError(ErrorCode.MODEL_REFUSED, "cyber")}, "model", ErrorCode.MODEL_REFUSED),
    ({"model_error": TypeError("sdk bug")}, "model", ErrorCode.INTERNAL_ERROR),
    ({"answer": GOOD.model_copy(update={"claims": GOOD.claims[:2]})}, "validate", ErrorCode.MODEL_INVALID_OUTPUT),
])
def test_failures_are_attributed_to_their_stage(env, monkeypatch, capsys, kwargs, stage, code):
    out, table, s3, logs = run(monkeypatch, capsys, **kwargs)
    assert out == {"outcome": "failed", "code": str(code), "stage": stage}
    assert table.item["status"] == "failed" and table.item["error_code"] == str(code)
    assert table.item["failed_stage"] == stage
    assert s3.deleted  # clean-up runs on failure too
    [log] = logs
    assert log["stage"] == stage and log["code"] == str(code)


def test_logs_never_carry_the_transcript_or_the_key(env, monkeypatch, capsys):
    run(monkeypatch, capsys)
    run(monkeypatch, capsys, model_error=RuntimeError("boom sk-ant-test-secret"))
    raw = capsys.readouterr().out
    assert "SECRET TRANSCRIPT" not in raw and "sk-ant" not in raw and "https://" not in raw


def test_duplicate_delivery_leaves_the_job_alone(env, monkeypatch, capsys):
    table = FakeTable(status="processing")
    out, table, s3, logs = run(monkeypatch, capsys, table=table)
    assert out == {"outcome": "duplicate"} and len(table.updates) == 1
    assert not s3.deleted  # the first delivery owns the video
    assert logs == [{"event": "demotrace_job", "job_id": "job-1", "outcome": "duplicate"}]


def test_other_claim_errors_are_raised_not_hidden(env, monkeypatch, capsys):
    class Broken(FakeTable):
        def update_item(self, **kw):
            raise ClientError({"Error": {"Code": "ProvisionedThroughputExceededException"}}, "UpdateItem")

    with pytest.raises(ClientError):
        run(monkeypatch, capsys, table=Broken())


def test_completion_after_a_timeout_is_superseded(env, monkeypatch, capsys):
    table = FakeTable()
    table.fail_completion_with = conditional_failed()
    out, table, s3, logs = run(monkeypatch, capsys, table=table)
    assert out == {"outcome": "superseded"}
    assert not any(":failed" in u["ExpressionAttributeValues"] for u in table.updates)
    assert logs[-1]["outcome"] == "superseded"
