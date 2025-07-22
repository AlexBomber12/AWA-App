#!/usr/bin/env bash
set -eo pipefail

echo "⏳ Waiting for Postgres..."
until pg_isready -h "$PG_HOST" -p "$PG_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done

if [ -f /.migrated ]; then
  echo "⏭️  Migrations already applied"
else
  echo "🔄 Running Alembic migrations..."
  for backoff in 0 2 4 8 16 32; do
    [[ $backoff != 0 ]] && sleep "$backoff"
    alembic upgrade head && touch /.migrated && break || echo "Retry Alembic ($backoff s)"
  done
fi

echo "🚀 Launching Uvicorn..."
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
