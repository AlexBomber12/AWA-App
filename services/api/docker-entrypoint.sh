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
DB_NAME="${POSTGRES_DB:-${PG_DATABASE:-postgres}}"
export PGPASSWORD="${POSTGRES_PASSWORD:-${PG_PASSWORD:-}}"

if command -v pg_isready >/dev/null 2>&1; then
  ready=false
  for _ in {1..60}; do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
      ready=true
      break
    fi
    echo "Postgres not ready – waiting"
    sleep 1
  done
  if [[ "${ready}" != true ]]; then
    echo "Postgres not ready after 60 attempts" >&2
    exit 1
  fi
else
  echo "pg_isready not found; using psycopg fallback for DB readiness"
  python - <<'PY'
import os
import sys
import time

import psycopg

host = os.getenv("POSTGRES_HOST") or os.getenv("PG_HOST") or "localhost"
port = int(os.getenv("POSTGRES_PORT") or os.getenv("PG_PORT") or "5432")
user = os.getenv("POSTGRES_USER") or os.getenv("PG_USER") or "postgres"
password = os.getenv("POSTGRES_PASSWORD") or os.getenv("PG_PASSWORD") or ""
dbname = os.getenv("POSTGRES_DB") or os.getenv("PG_DATABASE") or "postgres"

last_exc: Exception | None = None
for attempt in range(60):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=1,
        ):
            last_exc = None
            break
    except Exception as exc:  # pragma: no cover - runtime guard
        last_exc = exc
        time.sleep(1)
else:  # pragma: no cover - runtime guard
    print(f"database not ready after 60 attempts: {last_exc}", file=sys.stderr)
    sys.exit(1)
PY
fi

python -m alembic -c "${ALEMBIC_INI}" upgrade head

DEFAULT_API_CMD=${DEFAULT_API_CMD:-"uvicorn services.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"}
exec ${DEFAULT_API_CMD}
