# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services
WORKDIR /app
COPY constraints.txt ./constraints.txt
ENV PIP_CONSTRAINT=/app/constraints.txt
COPY services/etl/requirements.txt ./services/etl/requirements.txt
RUN pip install -r services/etl/requirements.txt
# copy shared modules under /app/services
COPY services/common/ ./services/common
COPY services/ingest/ ./services/ingest
COPY pg_utils/ ./pg_utils
COPY services/etl/ ./services/etl
COPY tests/fixtures/keepa_sample.json ./services/etl/tests/fixtures/keepa_sample.json
RUN chmod +x services/etl/wait-for-it.sh services/etl/entrypoint.sh

FROM python:3.12-slim
ARG TZ_CACHE_BUST
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services
WORKDIR /app/services/etl
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
ARG DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends tzdata; \
    rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]
# default to running the in-tree healthcheck; docker-compose may override
HEALTHCHECK CMD ["python", "-m", "services.etl.healthcheck"]
