#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app:/app/packages}"

# Ensure pg_isready authenticates using the same credentials as the app
export PGPASSWORD="${PG_PASSWORD:-}"

until pg_isready \
  -h "${PG_HOST:-postgres}" \
  -p "${PG_PORT:-5432}" \
  -U "${PG_USER:-postgres}" \
  -d "${PG_DATABASE:-postgres}"; do
  echo "Postgres not ready – waiting"
  sleep 1
done

alembic -c "${ALEMBIC_CONFIG:-services/api/alembic.ini}" upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
