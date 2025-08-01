# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# install dependencies from repo root
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# copy application source under services
COPY services/api/ ./services/api
COPY services/common/ ./services/common
# configuration files for migrations
COPY services/api/alembic.ini ./alembic.ini
COPY alembic/ ./alembic/
COPY services/api/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENV ALEMBIC_CONFIG=/app/alembic.ini

FROM python:3.12-slim
ARG TZ_CACHE_BUST
ENV PYTHONUNBUFFERED=1
WORKDIR /app
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=UTC
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
HEALTHCHECK --start-period=70s --interval=10s --timeout=3s --retries=6 \
  CMD curl -fsSL http://localhost:8000/health || exit 1
