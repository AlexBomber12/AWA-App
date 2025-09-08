#!/usr/bin/env bash
set -euo pipefail

./wait-for-it.sh "${PG_HOST:-postgres}:${PG_PORT:-5432}" -t 30 -- true

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  exec python keepa_ingestor.py
fi
