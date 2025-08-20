#!/usr/bin/env bash
set -euo pipefail

: "${PG_HOST:=postgres}"
./wait-for-it.sh --timeout=30 "$PG_HOST:5432" -- python keepa_ingestor.py
