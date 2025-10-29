#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=".:packages:${PYTHONPATH:-}"
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

mkdir -p .local-artifacts

docker compose up -d --build --wait db redis

if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
if [ -f .env ]; then set -a; . .env; set +a; fi

export PG_HOST=${PG_HOST:-localhost}
export PG_PORT=${PG_PORT:-5432}
export PG_USER=${PG_USER:-postgres}
export PG_PASSWORD=${PG_PASSWORD:-pass}
export PG_DATABASE=${PG_DATABASE:-awa}

export DATABASE_URL=${DATABASE_URL:-"postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DATABASE}"}

ALEMBIC="alembic -c services/api/alembic.ini"

$ALEMBIC upgrade head
$ALEMBIC downgrade base
$ALEMBIC upgrade head
