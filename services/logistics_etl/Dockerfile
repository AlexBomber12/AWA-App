FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY . /tmp/logistics_etl

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY --from=builder /tmp/logistics_etl /app
CMD ["python", "-m", "logistics_etl"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
