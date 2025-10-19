#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
docker compose up -d db redis
sleep 5
source .venv/bin/activate
if [ -f .env ]; then set -a; source .env; set +a; fi
: "${DATABASE_URL:=postgresql+psycopg://postgres:postgres@localhost:5432/app}"
alembic upgrade head
echo "migrations ok" > .local-artifacts/migrations.ok
