#!/usr/bin/env bash

set -euo pipefail

for i in {1..20}; do
  if pg_isready -h "${PG_HOST:-postgres}" -U "${PG_USER:-postgres}" -d "${PG_DATABASE:-awa}"; then
    break
  fi
  echo "Waiting for Postgres..." >&2
  sleep 2
done

for i in {1..5}; do
  if alembic upgrade head; then
    break
  fi
  if [ "$i" -eq 5 ]; then
    echo "Migrations failed" >&2
    exit 1
  fi
  sleep 2
done

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
