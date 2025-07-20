#!/usr/bin/env bash
set -euo pipefail

python -m services.common.health_server &

exec python alert_bot.py "$@"
