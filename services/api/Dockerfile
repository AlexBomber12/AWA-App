# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services
WORKDIR /app
# install dependencies from repo root
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# copy application source under services
COPY services/api/ ./services/api
COPY services/common/ ./services/common
COPY services/ingest/ ./services/ingest
COPY services/etl/ ./services/etl
# configuration files for migrations
COPY services/api/alembic.ini ./alembic.ini
COPY alembic/ ./alembic/
COPY services/api/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENV ALEMBIC_CONFIG=/app/alembic.ini

FROM python:3.12-slim
ARG TZ_CACHE_BUST
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services
WORKDIR /app
ARG DEBIAN_FRONTEND=noninteractive
RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends tzdata postgresql-client curl; \
    rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
HEALTHCHECK --start-period=70s --interval=10s --timeout=3s --retries=6 \
  CMD curl -fsSL http://localhost:8000/health || exit 1
