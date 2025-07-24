#!/usr/bin/env bash
set -e
echo "⏳ Waiting for Postgres..."
until pg_isready -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done
alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
