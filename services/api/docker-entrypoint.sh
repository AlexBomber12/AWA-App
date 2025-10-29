#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app:/app/packages}"

# Ensure pg_isready authenticates using the same credentials as the app
export PGPASSWORD="${PG_PASSWORD:-}"

if command -v pg_isready >/dev/null 2>&1; then
  until pg_isready \
    -h "${PG_HOST:-postgres}" \
    -p "${PG_PORT:-5432}" \
    -U "${PG_USER:-postgres}" \
    -d "${PG_DATABASE:-postgres}"; do
    echo "Postgres not ready – waiting"
    sleep 1
  done
else
  echo "pg_isready not found; skipping database readiness check" >&2
fi

alembic -c "${ALEMBIC_CONFIG:-services/api/alembic.ini}" upgrade head

if [[ $# -gt 0 ]]; then
  exec "$@"
fi

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
