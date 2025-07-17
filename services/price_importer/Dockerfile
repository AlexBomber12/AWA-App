FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder
WORKDIR /app
# install python deps for the importer
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt
COPY . /tmp/price_importer

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local /usr/local
# copy only the modules the importer relies on
COPY --from=builder /tmp/price_importer/services_common /app/services/common
COPY --from=builder /tmp/price_importer /app/price_importer
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
