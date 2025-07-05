#!/usr/bin/env bash

set -euo pipefail

./wait_db.sh
alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
