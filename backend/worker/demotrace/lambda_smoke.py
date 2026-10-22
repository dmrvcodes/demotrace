"""Run one job through the deployed worker Lambda, the way the Control API will.

Creates the job row (queued), uploads the video to incoming/{job_id}, invokes the worker
asynchronously, polls the row until it is completed or failed, and prints the stage timings, the
worker's own log line and whether any version of the video is left in S3. One paid model call.
"""

import json
import time
import uuid
from collections.abc import Sequence
from pathlib import Path

TERMINAL = {"completed", "failed"}
POLL_S = 5
GIVE_UP_S = 17 * 60  # just past the 16-minute processing timeout


def _plain(value):
    """DynamoDB numbers come back as Decimal."""
    return json.loads(json.dumps(value, default=lambda d: float(d)))


def run(session, account: str, video: Path, claims: Sequence[str], *, region: str = "us-east-1",
        table_name: str = "demotrace-jobs", function: str = "demotrace-worker") -> int:
    bucket = f"demotrace-{account}-{region}"
    table = session.resource("dynamodb", region_name=region).Table(table_name)
    s3 = session.client("s3", region_name=region)
    lam = session.client("lambda", region_name=region)
    logs = session.client("logs", region_name=region)

    job_id = str(uuid.uuid4())
    key = f"incoming/{job_id}"
    with video.open("rb") as body:
        version = s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType="video/mp4")["VersionId"]
    now = int(time.time())
    table.put_item(Item={"pk": f"JOB#{job_id}", "status": "queued", "claims": list(claims), "key": key,
                         "version_id": version, "created_at": now, "queued_at": now, "ttl": now + 7 * 86400})
    lam.invoke(FunctionName=function, InvocationType="Event",
               Payload=json.dumps({"job_id": job_id, "key": key, "version_id": version, "claims": list(claims)}))
    print(f"job {job_id}: uploaded {video.name} ({video.stat().st_size / 2**20:.1f} MB), queued, worker invoked")

    started, last = time.monotonic(), None
    while True:
        item = _plain(table.get_item(Key={"pk": f"JOB#{job_id}"}, ConsistentRead=True).get("Item", {}))
        status = item.get("status")
        if status != last:
            print(f"  {time.monotonic() - started:6.1f}s  {status}")
            last = status
        if status in TERMINAL or time.monotonic() - started > GIVE_UP_S:
            break
        time.sleep(POLL_S)

    print(f"timings (s): {item.get('timings')}")
    if status == "completed":
        for claim in item["result"]["claims"]:
            refs = ", ".join(f"{e['ref_id']}@{e['t']:.1f}s" for e in claim["evidence"]) or "-"
            print(f"  {claim['claim_id']} {claim['status'].upper():9} [{refs}]  {claim['text']}")
            print(f"      {claim['explanation']}")
    else:
        print(f"error: {item.get('error_code')} at stage {item.get('failed_stage')}")

    line = None
    for _ in range(12):  # CloudWatch can take a little while to deliver the line
        events = logs.filter_log_events(logGroupName=f"/aws/lambda/{function}", filterPattern=f'"{job_id}"',
                                        startTime=(now - 60) * 1000).get("events", [])
        line = next((e["message"].strip() for e in events if '"event":"demotrace_job"' in e["message"]), None)
        if line:
            break
        time.sleep(POLL_S)
    print(f"worker log: {line or '(not delivered yet)'}")
    left = s3.list_object_versions(Bucket=bucket, Prefix=key)
    remaining = len(left.get("Versions", [])) + len(left.get("DeleteMarkers", []))
    print(f"S3 versions or delete markers left under {key}: {remaining}")
    return 0 if status == "completed" else 1
