from pathlib import Path

from fastapi.testclient import TestClient

from demotrace_control.app import create_app


def client(tmp_path: Path, delay: float = 0.0) -> TestClient:
    return TestClient(create_app(tmp_path / "state", fixture_delay_s=delay))


def create_job(client: TestClient) -> tuple[str, dict[str, str], str]:
    created = client.post("/jobs")
    assert created.status_code == 201
    data = created.json()
    return data["job_id"], {"Authorization": f"Bearer {data['job_token']}"}, data["upload_url"]


def test_local_flow_returns_fixture_result(tmp_path: Path) -> None:
    app_client = client(tmp_path)
    job_id, headers, upload_url = create_job(app_client)
    upload = app_client.put(upload_url, headers=headers, content=b"fake mp4 bytes")
    assert upload.status_code == 204

    queued = app_client.post(
        f"/jobs/{job_id}/analyze",
        headers=headers,
        json={"claims": ["Claim one", "Claim two", "Claim three"]},
    )
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"

    completed = app_client.get(f"/jobs/{job_id}", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert [claim["status"] for claim in completed.json()["result"]["claims"]] == [
        "shown", "told_only", "missing"
    ]


def test_job_token_is_required_and_not_stored_in_plaintext(tmp_path: Path) -> None:
    app_client = client(tmp_path)
    job_id, _headers, _upload_url = create_job(app_client)
    assert app_client.get(f"/jobs/{job_id}").status_code == 401
    assert app_client.get(f"/jobs/{job_id}", headers={"Authorization": "Bearer wrong"}).status_code == 404

    database = (tmp_path / "state" / "jobs.sqlite3").read_bytes()
    assert b"wrong" not in database


def test_analysis_requires_upload_and_three_claims(tmp_path: Path) -> None:
    app_client = client(tmp_path)
    job_id, headers, _upload_url = create_job(app_client)
    missing_upload = app_client.post(
        f"/jobs/{job_id}/analyze", headers=headers, json={"claims": ["one", "two", "three"]}
    )
    assert missing_upload.status_code == 409

    assert app_client.post(
        f"/jobs/{job_id}/analyze", headers=headers, json={"claims": ["one", "two"]}
    ).status_code == 422
