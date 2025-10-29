#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="${REPO_DIR}:${PYTHONPATH:-}"
ALEMBIC_INI="${REPO_DIR}/services/api/alembic.ini"

if [[ $# -gt 0 ]]; then
  exec "$@"
fi

DB_HOST="${POSTGRES_HOST:-${PG_HOST:-localhost}}"
DB_PORT="${POSTGRES_PORT:-${PG_PORT:-5432}}"
DB_USER="${POSTGRES_USER:-${PG_USER:-postgres}}"
export PGPASSWORD="${POSTGRES_PASSWORD:-${PG_PASSWORD:-}}"

if command -v pg_isready >/dev/null 2>&1; then
  until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
    echo "Postgres not ready – waiting"
    sleep 1
  done
else
  echo "pg_isready not found; skipping database readiness check" >&2
fi

python -m alembic -c "${ALEMBIC_INI}" upgrade head

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
