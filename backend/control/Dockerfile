FROM python:3.12-slim

WORKDIR /app
COPY backend/shared /app/backend/shared
COPY backend/control /app/backend/control
RUN pip install --no-cache-dir /app/backend/shared /app/backend/control

ENV DEMOTRACE_LOCAL_DATA=/data
EXPOSE 8000
CMD ["uvicorn", "demotrace_control.app:app", "--host", "0.0.0.0", "--port", "8000"]
