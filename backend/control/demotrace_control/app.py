"""FastAPI local Control API with the same public contract planned for the Function URL."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .fixture_worker import analyze
from .models import AnalyzeRequest, CreateJobResponse, JobResponse, JobStatus
from .store import InvalidJobToken, InvalidTransition, JobNotFound, LocalJobStore

MAX_UPLOAD_BYTES = 150 * 1024 * 1024


def create_app(data_dir: Path | None = None, fixture_delay_s: float = 0.15) -> FastAPI:
    app = FastAPI(title="DemoTrace Control API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.state.store = LocalJobStore(data_dir or Path(os.getenv("DEMOTRACE_LOCAL_DATA", ".local/demotrace")))
    app.state.fixture_delay_s = fixture_delay_s

    def bearer_token(authorization: str | None) -> str:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing job token")
        return authorization.removeprefix("Bearer ").strip()

    def authorized_job(job_id: str, authorization: str | None):
        try:
            return app.state.store.authorize(job_id, bearer_token(authorization))
        except (JobNotFound, InvalidJobToken) as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found") from error

    def job_response(job) -> JobResponse:
        return JobResponse(
            job_id=job.job_id,
            status=job.status,
            result=job.result,
            error_code=job.error_code,
            error_message=job.error_message,
        )

    async def run_fixture(job_id: str) -> None:
        try:
            await asyncio.sleep(app.state.fixture_delay_s)
            processing = app.state.store.transition(job_id, JobStatus.QUEUED, JobStatus.PROCESSING)
            await asyncio.sleep(app.state.fixture_delay_s)
            app.state.store.complete(job_id, analyze(processing))
        except InvalidTransition:
            return
        except Exception:
            app.state.store.fail(job_id, "local_worker_failed", "The local fixture worker could not finish.")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "local-fixture"}

    @app.post("/jobs", response_model=CreateJobResponse, status_code=status.HTTP_201_CREATED)
    def create_job(request: Request) -> CreateJobResponse:
        job, token = app.state.store.create()
        return CreateJobResponse(
            job_id=job.job_id,
            job_token=token,
            upload_url=str(request.url_for("upload_video", job_id=job.job_id)),
        )

    @app.put("/jobs/{job_id}/video", name="upload_video", status_code=status.HTTP_204_NO_CONTENT)
    async def upload_video(job_id: str, request: Request, authorization: str | None = Header(default=None)) -> Response:
        token = bearer_token(authorization)
        try:
            path = app.state.store.upload_path(job_id, token)
        except (JobNotFound, InvalidJobToken) as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found") from error
        except InvalidTransition as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="video exceeds 150 MB")
        body = await request.body()
        if not body:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="video body is empty")
        if len(body) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="video exceeds 150 MB")
        tmp_path = path.with_suffix(".uploading")
        tmp_path.write_bytes(body)
        tmp_path.replace(path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/jobs/{job_id}/analyze", response_model=JobResponse)
    async def start_analysis(job_id: str, payload: AnalyzeRequest,
                             authorization: str | None = Header(default=None)) -> JobResponse:
        token = bearer_token(authorization)
        try:
            job = app.state.store.queue(job_id, token, payload.claims)
        except (JobNotFound, InvalidJobToken) as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found") from error
        except InvalidTransition as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        asyncio.create_task(run_fixture(job.job_id))
        return job_response(job)

    @app.get("/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str, authorization: str | None = Header(default=None)) -> JobResponse:
        return job_response(authorized_job(job_id, authorization))

    return app


app = create_app()
