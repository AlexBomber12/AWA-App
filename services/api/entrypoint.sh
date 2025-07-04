#!/usr/bin/env bash

set -euo pipefail

: "${DB_HOST:=postgres}"
: "${DB_USER:=postgres}"

until pg_isready -h "$DB_HOST" -U "$DB_USER"; do
    sleep 1
done

alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
