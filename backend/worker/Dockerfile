FROM public.ecr.aws/lambda/python:3.12-arm64
RUN dnf -y install ffmpeg && dnf clean all
COPY backend/shared /build/shared
COPY backend/worker /build/worker
RUN pip install --no-cache-dir /build/shared /build/worker
COPY backend/worker/demotrace ${LAMBDA_TASK_ROOT}/demotrace
CMD ["demotrace.handler.handler"]
