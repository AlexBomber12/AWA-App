#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
docker compose up -d db redis
sleep 8
source .venv/bin/activate
if [ -f .env ]; then set -a; source .env; set +a; fi
if [ -z "${DATABASE_URL:-}" ]; then
  U=$(docker compose exec -T db bash -lc 'printf %s "${POSTGRES_USER:-postgres}"')
  P=$(docker compose exec -T db bash -lc 'printf %s "${POSTGRES_PASSWORD:-postgres}"')
  D=$(docker compose exec -T db bash -lc 'printf %s "${POSTGRES_DB:-$POSTGRES_USER}"')
  PORT=$(docker compose port db 5432 | awk -F: '{print $2}')
  export DATABASE_URL="postgresql+psycopg://${U}:${P}@127.0.0.1:${PORT}/${D}"
  sed -i '/^DATABASE_URL=/d' .env 2>/dev/null || true
  echo "DATABASE_URL=$DATABASE_URL" >> .env
fi
alembic upgrade head
echo "migrations ok" > .local-artifacts/migrations.ok
