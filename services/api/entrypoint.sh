#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres to accept connections
until pg_isready \
  -h "${PG_HOST:-postgres}" \
  -p "${PG_PORT:-5432}" \
  -U "${POSTGRES_USER:-postgres}"; do
  echo "⏳  Waiting for Postgres..."
  sleep 1
done

# Retry Alembic in case the DB isn’t ready yet
for i in {1..5}; do
  alembic upgrade head && break
  echo "❌ Alembic failed – retry $i/5"
  sleep 2
done

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
