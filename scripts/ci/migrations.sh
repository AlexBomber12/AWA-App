#!/usr/bin/env bash
set -euo pipefail

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

mkdir -p .local-artifacts
docker compose up -d --build --wait db redis
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
if [ -f .env ]; then set -a; . .env; set +a; fi
U=$(docker compose exec -T db bash -lc 'printf %s "postgres"')
