#!/usr/bin/env bash
set -e
# Ensure the service package is importable when running inside the
# container.  In the built image the code lives under /app/fees_h10, so we
# only need /app on PYTHONPATH.
export PYTHONPATH="/app:${PYTHONPATH}"
exec celery -A fees_h10.worker beat -l info
