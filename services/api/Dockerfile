# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# make service requirements visible when build context is repo root
COPY services/api/requirements.txt ./requirements.txt
COPY requirements-dev.txt constraints.txt ./
# copy root-level alembic files; build context is repo root
COPY ./alembic.ini ./
COPY ./alembic ./alembic
RUN alembic upgrade head && touch /.migrated
ARG CONSTRAINTS=""
RUN if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi
ENV ALEMBIC_CONFIG=/app/alembic.ini
COPY . .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY --from=base /app /app
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
HEALTHCHECK --start-period=70s --interval=10s --timeout=3s --retries=6 \
  CMD curl -fsSL http://localhost:8000/health || exit 1
