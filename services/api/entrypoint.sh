#!/usr/bin/env bash
set -euo pipefail

# Default database variables for CI / local use
: "${PG_HOST:=postgres}"
: "${PG_PORT:=5432}"
: "${PG_USER:=postgres}"
: "${PG_PASSWORD:=postgres}"
: "${PG_DATABASE:=awa}"

# If arguments are supplied, run them instead of the full app startup.
if [[ $# -gt 0 ]]; then
  exec "$@"
fi

echo "⏳ Waiting for Postgres..."
until pg_isready -h "${PG_HOST:-postgres}" -p "${PG_PORT:-5432}" -U "${PG_USER:-postgres}" >/dev/null 2>&1; do
  sleep 1
done

alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
