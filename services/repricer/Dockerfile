# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY . /tmp/repricer

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY --from=builder /tmp/repricer /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
