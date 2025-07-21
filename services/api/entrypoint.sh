#!/usr/bin/env bash
set -euo pipefail

# wait for Postgres to become ready
until pg_isready -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER"; do
  echo "\u23F3 Waiting for Postgres..."
  sleep 1
done

# apply migrations with retries
for i in {1..5}; do
  if alembic upgrade head; then
    break
  fi
  echo "Alembic failed, retry $i/5"
  sleep 2
done

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
