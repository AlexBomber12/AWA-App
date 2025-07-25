# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# expose alembic.ini for tests
COPY services/api/alembic.ini /app/services/api/alembic.ini
# install dependencies from repo root
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# copy application source
COPY services/api/ .
# shared common utilities
COPY services/common/ ../common/
# config and migrations
COPY alembic.ini .
COPY alembic/ ./alembic/
ENV ALEMBIC_CONFIG=/app/alembic.ini

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && cp /usr/share/zoneinfo/UTC /etc/localtime \
    && echo "UTC" > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
HEALTHCHECK --start-period=70s --interval=10s --timeout=3s --retries=6 \
  CMD curl -fsSL http://localhost:8000/health || exit 1
