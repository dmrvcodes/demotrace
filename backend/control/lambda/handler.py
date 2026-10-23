"""Dependency-free Control API for the public Lambda Function URL."""

import hashlib
import json
import os
import secrets
import time
import uuid
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer

MAX_UPLOAD_BYTES = 150 * 1024 * 1024
TTL_SECONDS = 7 * 24 * 60 * 60
JOB_TIMEOUT_SECONDS = 20 * 60
UPLOAD_CONTENT_TYPE = "video/mp4"
MAX_CLAIM_CHARS = 240
_serializer = TypeSerializer()


def _daily_limit() -> int:
    return int(os.getenv("MAX_DAILY_ANALYSES", "30"))


def _json(status: int, body: dict) -> dict:
    def encode(value):
        if isinstance(value, Decimal):
            return int(value) if value == value.to_integral_value() else float(value)
        raise TypeError(f"cannot serialize {type(value)!r}")

    return {"statusCode": status, "headers": {"content-type": "application/json", "cache-control": "no-store"}, "body": json.dumps(body, default=encode)}


def _token(event: dict) -> str | None:
    headers = event.get("headers") or {}
    value = headers.get("authorization") or headers.get("Authorization")
    if not value or not value.lower().startswith("bearer "):
        return None
    return value[7:].strip() or None


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _is_conditional(error: ClientError) -> bool:
    return error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"


def _item(table, job_id: str, token: str | None) -> dict | None:
    item = table.get_item(Key={"pk": f"JOB#{job_id}"}).get("Item")
    if not item or not token or not secrets.compare_digest(item["token_hash"], _hash(token)):
        return None
    return item


def _expire_if_needed(table, item: dict, now: int) -> dict:
    if item["status"] not in {"created", "queued", "processing"} or item.get("expires_at", now + 1) > now:
        return item
    try:
        response = table.update_item(
            Key={"pk": item["pk"]},
            UpdateExpression="SET #s=:failed, error_code=:code, error_message=:message, finished_at=:now",
            ConditionExpression="#s IN (:created, :queued, :processing) AND expires_at<=:now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":created": "created", ":queued": "queued", ":processing": "processing", ":failed": "failed", ":code": "analysis_expired", ":message": "Analysis took too long. Please try again.", ":now": now},
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    except ClientError as error:
        if not _is_conditional(error):
            raise
        return table.get_item(Key={"pk": item["pk"]}).get("Item", item)


def _job(item: dict) -> dict:
    result = {"job_id": item["job_id"], "status": item["status"]}
    for field in ("result", "error_code", "error_message"):
        if field in item:
            result[field] = item[field]
    return result


def _claims(event: dict) -> list[str] | None:
    try:
        values = json.loads(event.get("body") or "{}")["claims"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(values, list) or not 3 <= len(values) <= 5:
        return None
    cleaned = [value.strip() if isinstance(value, str) else "" for value in values]
    return cleaned if all(cleaned) and all(len(value) <= MAX_CLAIM_CHARS for value in cleaned) else None


def _fail_dispatch(table, job_id: str, now: int) -> None:
    try:
        table.update_item(
            Key={"pk": f"JOB#{job_id}"},
            UpdateExpression="SET #s=:failed, error_code=:code, error_message=:message, finished_at=:now",
            ConditionExpression="#s=:queued",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":queued": "queued", ":failed": "failed", ":code": "dispatch_failed", ":message": "Analysis could not be started. Please try again.", ":now": now},
        )
    except ClientError as error:
        if not _is_conditional(error):
            raise


def _attribute_values(values: dict) -> dict:
    return {key: _serializer.serialize(value) for key, value in values.items()}


def _queue_with_capacity(client, *, job_id: str, claims: list[str], version: str, now: int) -> str:
    """Atomically reserve daily capacity and transition a job to queued.

    Capacity used to be incremented before the conditional job transition. A stale
    double-submit could therefore exhaust the global quota without creating work.
    The transaction makes those two state changes all-or-nothing.
    """
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    expires_at = now + JOB_TIMEOUT_SECONDS
    try:
        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": os.environ["JOBS_TABLE_NAME"],
                        "Key": _attribute_values({"pk": f"JOB#{job_id}"}),
                        "UpdateExpression": "SET #s=:queued, claims=:claims, version_id=:version, queued_at=:now, expires_at=:expires",
                        "ConditionExpression": "#s=:created AND expires_at>:now",
                        "ExpressionAttributeNames": {"#s": "status"},
                        "ExpressionAttributeValues": _attribute_values({
                            ":queued": "queued", ":created": "created", ":claims": claims,
                            ":version": version, ":now": now, ":expires": expires_at,
                        }),
                    },
                },
                {
                    "Update": {
                        "TableName": os.environ["JOBS_TABLE_NAME"],
                        "Key": _attribute_values({"pk": f"LIMIT#{day}"}),
                        "UpdateExpression": "ADD analyses :one SET #ttl=:ttl",
                        "ConditionExpression": "attribute_not_exists(analyses) OR analyses < :limit",
                        "ExpressionAttributeNames": {"#ttl": "ttl"},
                        "ExpressionAttributeValues": _attribute_values({
                            ":one": 1, ":limit": _daily_limit(), ":ttl": now + TTL_SECONDS,
                        }),
                    },
                },
            ]
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "TransactionCanceledException":
            reasons = error.response.get("CancellationReasons", [])
            # A duplicate submission can also see a full counter. Report the job conflict first;
            # it explains what the caller can actually fix and proves no new capacity was spent.
            if reasons and reasons[0].get("Code") == "ConditionalCheckFailed":
                return "already_started"
            if len(reasons) > 1 and reasons[1].get("Code") == "ConditionalCheckFailed":
                return "capacity"
            return "already_started"
        raise
    return "queued"


def handler(event: dict, _context) -> dict:
    table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE_NAME"])
    dynamodb = boto3.client("dynamodb")
    s3 = boto3.client("s3")
    worker = boto3.client("lambda")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    now, bucket = int(time.time()), os.environ["VIDEOS_BUCKET_NAME"]

    if method == "POST" and path == "/jobs":
        job_id, token = str(uuid.uuid4()), secrets.token_urlsafe(32)
        key = f"incoming/{job_id}/video.mp4"
        table.put_item(Item={"pk": f"JOB#{job_id}", "job_id": job_id, "token_hash": _hash(token), "status": "created", "key": key, "created_at": now, "expires_at": now + JOB_TIMEOUT_SECONDS, "ttl": now + TTL_SECONDS})
        upload = s3.generate_presigned_post(Bucket=bucket, Key=key, Fields={"Content-Type": UPLOAD_CONTENT_TYPE}, Conditions=[{"Content-Type": UPLOAD_CONTENT_TYPE}, ["content-length-range", 1, MAX_UPLOAD_BYTES]], ExpiresIn=600)
        return _json(201, {"job_id": job_id, "job_token": token, "upload_url": upload["url"], "upload_fields": upload["fields"]})

    parts = path.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "jobs":
        return _json(404, {"detail": "not found"})
    job_id, token = parts[1], _token(event)
    item = _item(table, job_id, token)
    if item is None:
        return _json(404, {"detail": "job not found"})
    if method == "GET" and len(parts) == 2:
        return _json(200, _job(_expire_if_needed(table, item, now)))
    if method != "POST" or len(parts) != 3 or parts[2] != "analyze":
        return _json(404, {"detail": "not found"})
    claims = _claims(event)
    if claims is None:
        return _json(422, {"detail": f"submit 3 to 5 non-empty claims of at most {MAX_CLAIM_CHARS} characters"})
    try:
        head = s3.head_object(Bucket=bucket, Key=item["key"])
        if head.get("ContentLength", 0) > MAX_UPLOAD_BYTES or head.get("ContentType") != UPLOAD_CONTENT_TYPE:
            return _json(422, {"detail": "upload an MP4 video up to 150 MB"})
        version = head["VersionId"]
    except ClientError:
        return _json(409, {"detail": "upload the video before analysis"})
    queue_result = _queue_with_capacity(dynamodb, job_id=job_id, claims=claims, version=version, now=now)
    if queue_result == "capacity":
        return _json(429, {"detail": "daily analysis capacity is reached; please try again tomorrow"})
    if queue_result == "already_started":
        return _json(409, {"detail": "analysis can only start once"})
    try:
        worker.invoke(FunctionName=os.environ["WORKER_FUNCTION_NAME"], InvocationType="Event", Payload=json.dumps({"job_id": job_id}).encode())
    except ClientError:
        _fail_dispatch(table, job_id, now)
        return _json(503, {"detail": "analysis could not be started; please try again"})
    return _json(200, {"job_id": job_id, "status": "queued"})
