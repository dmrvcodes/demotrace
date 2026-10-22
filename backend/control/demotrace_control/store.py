"""Local durable job storage. Its API mirrors the DynamoDB-backed repository planned for AWS."""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from uuid import uuid4

from .models import AnalysisResult, JobStatus


class JobNotFound(Exception):
    pass


class InvalidJobToken(Exception):
    pass


class InvalidTransition(Exception):
    pass


@dataclass(frozen=True)
class Job:
    job_id: str
    status: JobStatus
    video_path: Path
    claims: list[str]
    result: AnalysisResult | None
    error_code: str | None
    error_message: str | None


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class LocalJobStore:
    """SQLite + private local files; never use this implementation in a public deployment."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._video_dir = data_dir / "videos"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._video_dir.mkdir(exist_ok=True)
        self._connection = sqlite3.connect(data_dir / "jobs.sqlite3", check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                claims_json TEXT NOT NULL DEFAULT '[]',
                result_json TEXT,
                error_code TEXT,
                error_message TEXT
            )
            """
        )
        self._connection.commit()

    def create(self) -> tuple[Job, str]:
        job_id = str(uuid4())
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._connection.execute(
                "INSERT INTO jobs(job_id, token_hash, status) VALUES (?, ?, ?)",
                (job_id, token_hash(token), JobStatus.CREATED.value),
            )
            self._connection.commit()
        return self._read(job_id), token

    def upload_path(self, job_id: str, token: str) -> Path:
        job = self.authorize(job_id, token)
        if job.status is not JobStatus.CREATED:
            raise InvalidTransition("a video can only be uploaded before analysis starts")
        return job.video_path

    def authorize(self, job_id: str, token: str) -> Job:
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFound(job_id)
        if not secrets.compare_digest(row["token_hash"], token_hash(token)):
            raise InvalidJobToken(job_id)
        return self._job_from_row(row)

    def queue(self, job_id: str, token: str, claims: list[str]) -> Job:
        job = self.authorize(job_id, token)
        if job.status is not JobStatus.CREATED:
            raise InvalidTransition("analysis can only start once")
        if not job.video_path.exists():
            raise InvalidTransition("upload the video before analysis")
        with self._lock:
            changed = self._connection.execute(
                "UPDATE jobs SET status = ?, claims_json = ? WHERE job_id = ? AND status = ?",
                (JobStatus.QUEUED.value, json.dumps(claims), job_id, JobStatus.CREATED.value),
            ).rowcount
            self._connection.commit()
        if changed != 1:
            raise InvalidTransition("job was changed by another worker")
        return self._read(job_id)

    def transition(self, job_id: str, expected: JobStatus, target: JobStatus) -> Job:
        with self._lock:
            changed = self._connection.execute(
                "UPDATE jobs SET status = ? WHERE job_id = ? AND status = ?",
                (target.value, job_id, expected.value),
            ).rowcount
            self._connection.commit()
        if changed != 1:
            raise InvalidTransition(f"expected {expected.value}")
        return self._read(job_id)

    def complete(self, job_id: str, result: AnalysisResult) -> Job:
        with self._lock:
            changed = self._connection.execute(
                "UPDATE jobs SET status = ?, result_json = ? WHERE job_id = ? AND status = ?",
                (JobStatus.COMPLETED.value, result.model_dump_json(), job_id, JobStatus.PROCESSING.value),
            ).rowcount
            self._connection.commit()
        if changed != 1:
            raise InvalidTransition("job is no longer processing")
        return self._read(job_id)

    def fail(self, job_id: str, code: str, message: str) -> Job:
        with self._lock:
            self._connection.execute(
                "UPDATE jobs SET status = ?, error_code = ?, error_message = ? WHERE job_id = ?",
                (JobStatus.FAILED.value, code, message, job_id),
            )
            self._connection.commit()
        return self._read(job_id)

    def _read(self, job_id: str) -> Job:
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFound(job_id)
        return self._job_from_row(row)

    def _job_from_row(self, row: sqlite3.Row) -> Job:
        result = AnalysisResult.model_validate_json(row["result_json"]) if row["result_json"] else None
        return Job(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            video_path=self._video_dir / f"{row['job_id']}.mp4",
            claims=json.loads(row["claims_json"]),
            result=result,
            error_code=row["error_code"],
            error_message=row["error_message"],
        )
