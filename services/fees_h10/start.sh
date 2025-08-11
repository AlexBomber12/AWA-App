#!/usr/bin/env bash
set -e
export PYTHONPATH="/app:/app/services:${PYTHONPATH}"
exec celery -A fees_h10.worker beat -l info
