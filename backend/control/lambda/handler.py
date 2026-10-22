"""Dependency-free Function URL control plane for the deployed DemoTrace API."""
import base64, hashlib, json, os, secrets, time, uuid
import boto3

TTL_SECONDS = 7 * 24 * 60 * 60

def _json(status, body):
    return {"statusCode": status, "headers": {"content-type": "application/json"}, "body": json.dumps(body)}

def _token(event):
    value = (event.get("headers") or {}).get("authorization") or (event.get("headers") or {}).get("Authorization")
    return value.removeprefix("Bearer ").strip() if value and value.startswith("Bearer ") else None

def _item(table, job_id, token):
    response = table.get_item(Key={"pk": f"JOB#{job_id}"})
    item = response.get("Item")
    if not item or not token or not secrets.compare_digest(item["token_hash"], hashlib.sha256(token.encode()).hexdigest()):
        return None
    return item

def _job(item):
    result = {"job_id": item["job_id"], "status": item["status"]}
    if "result" in item: result["result"] = item["result"]
    if "error_message" in item: result["error_message"] = item["error_message"]
    return result

def handler(event, _context):
    table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE_NAME"])
    s3 = boto3.client("s3"); worker = boto3.client("lambda")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    now = int(time.time()); bucket = os.environ["VIDEOS_BUCKET_NAME"]
    if method == "POST" and path == "/jobs":
        job_id, token = str(uuid.uuid4()), secrets.token_urlsafe(32)
        table.put_item(Item={"pk": f"JOB#{job_id}", "job_id": job_id, "token_hash": hashlib.sha256(token.encode()).hexdigest(), "status": "created", "created_at": now, "ttl": now + TTL_SECONDS})
        url = s3.generate_presigned_url("put_object", Params={"Bucket": bucket, "Key": f"incoming/{job_id}"}, ExpiresIn=600, HttpMethod="PUT")
        return _json(201, {"job_id": job_id, "job_token": token, "upload_url": url})
    parts = path.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "jobs": return _json(404, {"detail": "not found"})
    job_id, token = parts[1], _token(event); item = _item(table, job_id, token)
    if item is None: return _json(404, {"detail": "job not found"})
    if method == "GET" and len(parts) == 2: return _json(200, _job(item))
    if method != "POST" or len(parts) != 3 or parts[2] != "analyze": return _json(404, {"detail": "not found"})
    try: claims = json.loads(event.get("body") or "{}")["claims"]
    except (KeyError, json.JSONDecodeError): return _json(400, {"detail": "claims are required"})
    if not isinstance(claims, list) or not 3 <= len(claims) <= 5 or any(not isinstance(c, str) or not c.strip() for c in claims): return _json(422, {"detail": "submit 3 to 5 non-empty claims"})
    try: version = s3.head_object(Bucket=bucket, Key=f"incoming/{job_id}")["VersionId"]
    except Exception: return _json(409, {"detail": "upload the video before analysis"})
    try:
        table.update_item(Key={"pk": f"JOB#{job_id}"}, UpdateExpression="SET #s=:queued, claims=:claims, version_id=:version, queued_at=:now", ConditionExpression="#s=:created", ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":queued": "queued", ":created": "created", ":claims": claims, ":version": version, ":now": now})
    except Exception: return _json(409, {"detail": "analysis can only start once"})
    worker.invoke(FunctionName=os.environ["WORKER_FUNCTION_NAME"], InvocationType="Event", Payload=json.dumps({"job_id": job_id, "key": f"incoming/{job_id}", "version_id": version, "claims": claims}).encode())
    return _json(200, {"job_id": job_id, "status": "queued"})
