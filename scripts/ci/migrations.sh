#!/usr/bin/env bash
set -euo pipefail
mkdir -p .local-artifacts
docker compose up -d db redis
sleep 6
if [ -f .venv/bin/activate ]; then . .venv/bin/activate; fi
if [ -f .env ]; then set -a; . .env; set +a; fi
U=$(docker compose exec -T db bash -lc 'printf %s "postgres"')
