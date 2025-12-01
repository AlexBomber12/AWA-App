#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app:/app/services}"

/app/scripts/wait-for-it.sh "${PG_HOST:-postgres}:${PG_PORT:-5432}" -t 30 -- true

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  exec python -m services.etl.healthcheck
fi
