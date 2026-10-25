#!/usr/bin/env python3
"""Exercise production-only DemoTrace safety properties without exposing job tokens.

The check deliberately uses a real, short owned video and one model call.  It verifies four
properties that unit tests cannot prove against AWS: unauthenticated reads are denied, the Worker
uses the version pinned when a job is queued, every S3 version is removed after processing, and
the emergency capacity switch rejects new analyses before dispatching a Worker.

Run from the repository root:

    AWS_PROFILE=demotrace-key .venv/bin/python scripts/live_system_check.py \
      --video .local/eval/videos/todomvc-01.mp4 \
      --replacement .local/eval/videos/silent-missing-01.mp4

It restores the Control Lambda environment in a ``finally`` block, including if the capacity
probe fails.  Do not run it during a live public demo: capacity is set to zero for a few seconds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3

REGION = "us-east-1"
CONTROL_FUNCTION = "demotrace-control"
WORKER_FUNCTION = "demotrace-worker"
TABLE = "demotrace-jobs"
BUCKET = "demotrace-623588627433-us-east-1"
POLL_SECONDS = 2
TIMEOUT_SECONDS = 13 * 60
ORIGINAL_CLAIMS = [
    "Adding a task increases the items left counter.",
    "The Active filter hides completed tasks.",
    "Clear completed removes finished tasks.",
]


class CheckFailed(RuntimeError):
    """A production invariant did not hold."""


@dataclass(frozen=True)
class CreatedJob:
    job_id: str
    token: str
    upload_url: str
    upload_fields: dict[str, str]


def request_json(url: str, *, method: str = "GET", body: dict[str, Any] | None = None,
                 token: str | None = None) -> tuple[int, dict[str, Any]]:
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if payload else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else {}


def multipart_post(url: str, fields: dict[str, str], video: Path) -> None:
    boundary = f"----DemoTrace{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode(), b"\r\n",
        ])
    chunks.extend([
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="file"; filename="demo.mp4"\r\n',
        b"Content-Type: video/mp4\r\n\r\n",
        video.read_bytes(), b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ])
    request = urllib.request.Request(
        url,
        data=b"".join(chunks),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status not in {200, 201, 204}:
            raise CheckFailed(f"upload returned HTTP {response.status}")


def create_and_upload(api_url: str, video: Path) -> CreatedJob:
    status, body = request_json(f"{api_url}/jobs", method="POST")
    if status != 201:
        raise CheckFailed(f"job creation returned HTTP {status}: {body.get('detail', 'unknown error')}")
    created = CreatedJob(
        job_id=body["job_id"], token=body["job_token"], upload_url=body["upload_url"],
        upload_fields=body["upload_fields"],
    )
    multipart_post(created.upload_url, created.upload_fields, video)
    return created


def wait_for_terminal(table: Any, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        item = table.get_item(Key={"pk": f"JOB#{job_id}"}, ConsistentRead=True).get("Item", {})
        if item.get("status") in {"completed", "failed"}:
            return item
        time.sleep(POLL_SECONDS)
    raise CheckFailed("worker did not reach a terminal state before the live-check timeout")


def assert_no_versions(s3: Any, key: str) -> None:
    listing = s3.list_object_versions(Bucket=BUCKET, Prefix=key)
    remaining = len(listing.get("Versions", [])) + len(listing.get("DeleteMarkers", []))
    if remaining:
        raise CheckFailed(f"{remaining} S3 versions or delete markers remain under {key}")


def delete_all_versions(s3: Any, key: str) -> None:
    """Remove the capacity probe upload, which intentionally never reaches the Worker."""
    listing = s3.list_object_versions(Bucket=BUCKET, Prefix=key)
    objects = [
        {"Key": version["Key"], "VersionId": version["VersionId"]}
        for version in [*listing.get("Versions", []), *listing.get("DeleteMarkers", [])]
    ]
    if objects:
        s3.delete_objects(Bucket=BUCKET, Delete={"Objects": objects, "Quiet": True})
    assert_no_versions(s3, key)


def assert_log_is_private(logs: Any, job_id: str) -> None:
    messages = logs.filter_log_events(
        logGroupName=f"/aws/lambda/{WORKER_FUNCTION}", filterPattern=f'"{job_id}"',
        startTime=(int(time.time()) - 900) * 1000,
    ).get("events", [])
    text = "\n".join(event["message"] for event in messages)
    forbidden = ["Adding a task", "https://", "X-Amz-Signature", "ANTHROPIC_API_KEY"]
    leaked = [value for value in forbidden if value in text]
    if leaked:
        raise CheckFailed(f"worker logs contain private content markers: {', '.join(leaked)}")


def check_unauthenticated_read(api_url: str) -> None:
    status, _ = request_json(f"{api_url}/jobs/00000000-0000-0000-0000-000000000000")
    if status not in {401, 404}:
        raise CheckFailed(f"unauthenticated GET returned HTTP {status}, expected 401 or 404")
    print(f"ok security: unauthenticated GET returned {status}")


def check_pinned_version(api_url: str, session: boto3.Session, original: Path, replacement: Path) -> str:
    """Queue the original version, overwrite the key, then invoke the Worker from its stored row.

    The direct state transition eliminates a download timing race.  The public Control API is
    still used to create the job and constrained presigned upload; the Worker is tested against
    exactly the VersionId that a normal Control ``analyze`` stores.
    """
    s3 = session.client("s3", region_name=REGION)
    table = session.resource("dynamodb", region_name=REGION).Table(TABLE)
    worker = session.client("lambda", region_name=REGION)
    logs = session.client("logs", region_name=REGION)
    created = create_and_upload(api_url, original)
    key = f"incoming/{created.job_id}/video.mp4"
    try:
        item = table.get_item(Key={"pk": f"JOB#{created.job_id}"}, ConsistentRead=True)["Item"]
        original_version = s3.head_object(Bucket=BUCKET, Key=item["key"])["VersionId"]
        now = int(time.time())
        response = table.update_item(
            Key={"pk": item["pk"]},
            UpdateExpression="SET #s=:queued, claims=:claims, version_id=:version, queued_at=:now, expires_at=:expires",
            ConditionExpression="#s=:created",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":created": "created", ":queued": "queued", ":claims": ORIGINAL_CLAIMS, ":version": original_version,
                ":now": now, ":expires": now + 20 * 60,
            },
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise CheckFailed("could not queue the pinned-version test job")
        with replacement.open("rb") as body:
            replacement_version = s3.put_object(
                Bucket=BUCKET, Key=item["key"], Body=body, ContentType="video/mp4",
            )["VersionId"]
        if replacement_version == original_version:
            raise CheckFailed("S3 object overwrite did not create a new version")
        worker.invoke(FunctionName=WORKER_FUNCTION, InvocationType="Event", Payload=json.dumps({"job_id": created.job_id}).encode())
        terminal = wait_for_terminal(table, created.job_id)
        if terminal["status"] != "completed":
            raise CheckFailed(f"pinned-version job failed at {terminal.get('failed_stage')}: {terminal.get('error_code')}")
        statuses = {claim["claim_id"]: claim["status"] for claim in terminal["result"]["claims"]}
        if statuses.get("C1") != "shown" or statuses.get("C2") != "shown":
            raise CheckFailed(f"result does not match the original TodoMVC video: {statuses}")
        assert_no_versions(s3, key)
        assert_log_is_private(logs, created.job_id)
        print("ok pinning/privacy: Worker used the queued original version, cleaned S3 versions, logs held no prompt/video data")
        return created.job_id
    finally:
        # The Worker normally removes every version.  Clean here too if this diagnostic exits
        # before the asynchronous invocation reaches that branch.
        delete_all_versions(s3, key)


def check_emergency_capacity(api_url: str, session: boto3.Session, video: Path) -> None:
    control = session.client("lambda", region_name=REGION)
    s3 = session.client("s3", region_name=REGION)
    configuration = control.get_function_configuration(FunctionName=CONTROL_FUNCTION)
    original_environment = configuration.get("Environment", {}).get("Variables", {})
    temporary_environment = {**original_environment, "MAX_DAILY_ANALYSES": "0"}
    created: CreatedJob | None = None
    try:
        control.update_function_configuration(FunctionName=CONTROL_FUNCTION, Environment={"Variables": temporary_environment})
        control.get_waiter("function_updated_v2").wait(FunctionName=CONTROL_FUNCTION)
        created = create_and_upload(api_url, video)
        status, body = request_json(
            f"{api_url}/jobs/{created.job_id}/analyze", method="POST", token=created.token,
            body={"claims": ORIGINAL_CLAIMS},
        )
        if status != 429 or "capacity" not in body.get("detail", ""):
            raise CheckFailed(f"capacity=0 returned HTTP {status}: {body.get('detail', 'unknown error')}")
        print("ok capacity: MAX_DAILY_ANALYSES=0 returned the public 429 capacity message")
    finally:
        if created is not None:
            delete_all_versions(s3, f"incoming/{created.job_id}/video.mp4")
        control.update_function_configuration(
            FunctionName=CONTROL_FUNCTION, Environment={"Variables": original_environment},
        )
        control.get_waiter("function_updated_v2").wait(FunctionName=CONTROL_FUNCTION)
        restored = control.get_function_configuration(FunctionName=CONTROL_FUNCTION)["Environment"]["Variables"]
        if restored != original_environment:
            raise CheckFailed("Control Lambda environment did not restore exactly")
        print("ok capacity: restored Control Lambda environment")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="demotrace-key")
    parser.add_argument("--api-url", default="https://ysfenjjngidsfcg7miagyqsbbm0djzre.lambda-url.us-east-1.on.aws")
    parser.add_argument("--video", type=Path, required=True, help="owned MP4 used as the original TodoMVC input")
    parser.add_argument("--replacement", type=Path, required=True, help="different owned MP4 used to overwrite the S3 key")
    args = parser.parse_args()
    if not args.video.is_file() or not args.replacement.is_file():
        raise SystemExit("--video and --replacement must point at readable local MP4 files")
    if hashlib.sha256(args.video.read_bytes()).digest() == hashlib.sha256(args.replacement.read_bytes()).digest():
        raise SystemExit("--replacement must differ from --video")

    session = boto3.Session(profile_name=args.profile)
    account = session.client("sts", region_name=REGION).get_caller_identity()["Account"]
    if account != "623588627433":
        raise SystemExit(f"refusing AWS account {account}; expected 623588627433")
    api_url = args.api_url.rstrip("/")
    check_unauthenticated_read(api_url)
    check_pinned_version(api_url, session, args.video, args.replacement)
    check_emergency_capacity(api_url, session, args.video)
    print("PASS: live security, pinned-version, cleanup, log privacy and capacity checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckFailed as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
