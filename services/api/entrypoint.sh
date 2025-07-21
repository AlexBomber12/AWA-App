#!/usr/bin/env bash
set -euo pipefail

# wait for Postgres
until pg_isready -h "${PG_HOST:-postgres}" -p "${PG_PORT:-5432}" -U "${POSTGRES_USER:-postgres}"; do
  echo "⏳ Waiting for Postgres…"
  sleep 1
done

# retry Alembic with exponential back-off
for d in 0 2 4 8 16; do
  [[ $d -gt 0 ]] && sleep "$d"
  alembic upgrade head && break || echo "Alembic failed, retry…"
done

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
