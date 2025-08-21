#!/usr/bin/env bash

# default Postgres connection settings (overridable via environment)
: "${PG_HOST:=postgres}"
: "${PG_PORT:=5432}"
: "${PG_USER:=postgres}"
: "${PG_PASSWORD:=pass}"
: "${PG_DATABASE:=awa}"

# ensure these variables are available to subprocesses such as alembic
export PG_HOST PG_PORT PG_USER PG_PASSWORD PG_DATABASE

set -euo pipefail

# If the first argument looks like a command, run it directly.
if [[ $# -gt 0 ]]; then
  if [[ "$1" == -* ]] || command -v "$1" >/dev/null 2>&1; then
    exec "$@"
  fi
fi

echo "⏳ Waiting for Postgres..."
export PGPASSWORD="${PG_PASSWORD}"
until pg_isready -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DATABASE"; do
  sleep 1
done

alembic -c "${ALEMBIC_CONFIG:-alembic.ini}" upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
