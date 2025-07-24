# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# install dependencies from repo root
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# copy application source
COPY services/api/ .
# shared common utilities
COPY services/common/ ../common/
# config and migrations
COPY alembic.ini .
COPY alembic ./alembic
ENV ALEMBIC_CONFIG=/app/alembic.ini
RUN alembic upgrade head && touch /.migrated

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
HEALTHCHECK --start-period=70s --interval=10s --timeout=3s --retries=6 \
  CMD curl -fsSL http://localhost:8000/health || exit 1
