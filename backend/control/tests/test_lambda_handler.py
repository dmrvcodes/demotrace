"""Contract tests for the deployed, dependency-free Function URL handler."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from botocore.exceptions import ClientError


def load_handler():
    path = Path(__file__).parents[1] / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("control_lambda_handler", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handler = load_handler()


def client_error(code: str, operation: str = "UpdateItem") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


class Table:
    def __init__(self):
        self.items: dict[str, dict] = {}
        self.updates: list[dict] = []

    def put_item(self, *, Item):
        self.items[Item["pk"]] = dict(Item)

    def get_item(self, *, Key):
        item = self.items.get(Key["pk"])
        return {"Item": dict(item)} if item else {}

    def update_item(self, **kwargs):
        self.updates.append(kwargs)
        key = kwargs["Key"]["pk"]
        if key.startswith("LIMIT#"):
            item = self.items.setdefault(key, {"pk": key, "analyses": 0})
            values = kwargs["ExpressionAttributeValues"]
            if item["analyses"] >= values[":limit"]:
                raise client_error("ConditionalCheckFailedException")
            item["analyses"] += values[":one"]
            item["ttl"] = values[":ttl"]
            return {"Attributes": dict(item)}
        item = self.items[key]
        values = kwargs["ExpressionAttributeValues"]
        condition = kwargs.get("ConditionExpression", "")
        if "#s=:created" in condition and item["status"] != values[":created"]:
            raise client_error("ConditionalCheckFailedException")
        if ":queued" in values and "#s=:queued" in condition and item["status"] != "queued":
            raise client_error("ConditionalCheckFailedException")
        if "expires_at<=:now" in condition and item["expires_at"] > values[":now"]:
            raise client_error("ConditionalCheckFailedException")
        expression = kwargs["UpdateExpression"]
        if ":queued" in values and "#s=:queued" in expression:
            item["status"] = "queued"
            item.update({"claims": values[":claims"], "version_id": values[":version"]})
        if ":failed" in values and "#s=:failed" in expression:
            item.update({"status": "failed", "error_code": values[":code"], "error_message": values[":message"]})
        return {"Attributes": dict(item)}


class S3:
    def __init__(self):
        self.uploads = []
        self.head = {"VersionId": "version-1", "ContentLength": 100, "ContentType": "video/mp4"}

    def generate_presigned_post(self, **kwargs):
        self.uploads.append(kwargs)
        return {"url": "https://bucket.example/upload", "fields": {"key": kwargs["Key"], "Content-Type": "video/mp4"}}

    def head_object(self, **_kwargs):
        return self.head


class Worker:
    def __init__(self, error: ClientError | None = None):
        self.error = error
        self.events = []

    def invoke(self, **kwargs):
        if self.error:
            raise self.error
        self.events.append(kwargs)


def event(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"authorization": f"Bearer {token}"} if token else {}
    return {"requestContext": {"http": {"method": method}}, "rawPath": path, "headers": headers, "body": json.dumps(body) if body else None}


def setup(monkeypatch, worker_error: ClientError | None = None):
    table, s3, worker = Table(), S3(), Worker(worker_error)
    monkeypatch.setattr(handler, "boto3", SimpleNamespace(resource=lambda _: SimpleNamespace(Table=lambda _: table), client=lambda name: {"s3": s3, "lambda": worker}[name]))
    monkeypatch.setattr(handler.time, "time", lambda: 1_000)
    monkeypatch.setenv("JOBS_TABLE_NAME", "jobs")
    monkeypatch.setenv("VIDEOS_BUCKET_NAME", "videos")
    monkeypatch.setenv("WORKER_FUNCTION_NAME", "worker")
    return table, s3, worker


def create(monkeypatch):
    table, s3, worker = setup(monkeypatch)
    response = handler.handler(event("POST", "/jobs"), None)
    body = json.loads(response["body"])
    return table, s3, worker, body


def test_create_uses_presigned_post_with_type_and_size_limit(monkeypatch):
    table, s3, _worker, body = create(monkeypatch)
    assert body["job_token"]
    assert table.items[f"JOB#{body['job_id']}"]["token_hash"] != body["job_token"]
    request = s3.uploads[0]
    assert request["Fields"] == {"Content-Type": "video/mp4"}
    assert ["content-length-range", 1, handler.MAX_UPLOAD_BYTES] in request["Conditions"]
    assert body["upload_fields"]["Content-Type"] == "video/mp4"


def test_analyze_dispatches_only_the_job_id(monkeypatch):
    _table, _s3, worker, body = create(monkeypatch)
    response = handler.handler(event("POST", f"/jobs/{body['job_id']}/analyze", {"claims": ["one", "two", "three"]}, body["job_token"]), None)
    assert response["statusCode"] == 200
    assert json.loads(worker.events[0]["Payload"].decode()) == {"job_id": body["job_id"]}


def test_dispatch_failure_marks_job_failed(monkeypatch):
    table, _s3, _worker = setup(monkeypatch, client_error("ResourceNotFoundException", "Invoke"))
    created = json.loads(handler.handler(event("POST", "/jobs"), None)["body"])
    response = handler.handler(event("POST", f"/jobs/{created['job_id']}/analyze", {"claims": ["one", "two", "three"]}, created["job_token"]), None)
    assert response["statusCode"] == 503
    item = table.items[f"JOB#{created['job_id']}"]
    assert item["status"] == "failed" and item["error_code"] == "dispatch_failed"


def test_read_lazily_expires_stuck_job(monkeypatch):
    table, _s3, _worker, body = create(monkeypatch)
    item = table.items[f"JOB#{body['job_id']}"]
    item.update({"status": "processing", "expires_at": 999})
    response = handler.handler(event("GET", f"/jobs/{body['job_id']}", token=body["job_token"]), None)
    result = json.loads(response["body"])
    assert result["status"] == "failed" and result["error_code"] == "analysis_expired"


def test_daily_capacity_stops_before_queueing(monkeypatch):
    table, _s3, worker = setup(monkeypatch)
    monkeypatch.setenv("MAX_DAILY_ANALYSES", "1")
    first = json.loads(handler.handler(event("POST", "/jobs"), None)["body"])
    assert handler.handler(event("POST", f"/jobs/{first['job_id']}/analyze", {"claims": ["one", "two", "three"]}, first["job_token"]), None)["statusCode"] == 200
    second = json.loads(handler.handler(event("POST", "/jobs"), None)["body"])
    response = handler.handler(event("POST", f"/jobs/{second['job_id']}/analyze", {"claims": ["one", "two", "three"]}, second["job_token"]), None)
    assert response["statusCode"] == 429
    assert table.items[f"JOB#{second['job_id']}"]["status"] == "created"
    assert len(worker.events) == 1
