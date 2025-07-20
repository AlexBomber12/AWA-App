#!/usr/bin/env bash
set -euo pipefail

python -m services.common.health_server &

exec python -m logistics_etl "$@"
