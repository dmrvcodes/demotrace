FROM --platform=linux/arm64 mwader/static-ffmpeg:6.1.1 AS ffmpeg

FROM public.ecr.aws/lambda/python:3.12-arm64
COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffprobe /usr/local/bin/ffprobe
COPY backend/shared /build/shared
COPY backend/worker /build/worker
RUN pip install --no-cache-dir /build/shared /build/worker

# The speech model is baked into the image: nothing is downloaded at run time, nothing is written
# outside /tmp, and HOME is left alone. The size is chosen by measurement (fix list item 8).
ARG WHISPER_MODEL=small.en
RUN python -c "from faster_whisper import download_model; download_model('${WHISPER_MODEL}', output_dir='/opt/models/${WHISPER_MODEL}')"
ENV DEMOTRACE_WHISPER_MODEL=/opt/models/${WHISPER_MODEL} \
    HF_HUB_OFFLINE=1

COPY backend/worker/demotrace ${LAMBDA_TASK_ROOT}/demotrace
CMD ["demotrace.handler.handler"]
