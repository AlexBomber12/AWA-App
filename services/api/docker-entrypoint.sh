#!/usr/bin/env bash
set -euo pipefail

until pg_isready -h postgres -p 5432 -U postgres; do
  echo "Postgres not ready – waiting"
  sleep 1
done

alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
