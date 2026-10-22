FROM --platform=linux/arm64 mwader/static-ffmpeg:6.1.1 AS ffmpeg

FROM public.ecr.aws/lambda/python:3.12-arm64
COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffprobe /usr/local/bin/ffprobe
COPY backend/shared /build/shared
COPY backend/worker /build/worker
RUN pip install --no-cache-dir /build/shared /build/worker
COPY backend/worker/demotrace ${LAMBDA_TASK_ROOT}/demotrace
CMD ["demotrace.handler.handler"]
