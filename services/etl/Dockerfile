# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services
WORKDIR /app
COPY services/etl/requirements*.txt services/etl/constraints.txt ./
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi
# copy shared modules under /app/services
COPY services/common/ ./services/common
COPY services/ingest/ ./services/ingest
COPY services/etl/ ./services/etl
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
