FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY . /tmp/fees_h10

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY --from=builder /tmp/fees_h10 /app
CMD ["celery", "-A", "services.fees_h10.worker", "beat", "-l", "info"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
