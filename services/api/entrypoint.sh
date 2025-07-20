#!/usr/bin/env bash

set -euo pipefail

for i in {1..30}; do
  pg_isready -h "${PG_HOST:-postgres}" -p "${PG_PORT:-5432}" && break || sleep 1
done

alembic upgrade head

exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
