#!/usr/bin/env bash
set -euo pipefail

: "${PG_HOST:=postgres}"

./wait-for-it.sh "${PG_HOST}:5432" --timeout=30

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  exec python keepa_ingestor.py
fi
