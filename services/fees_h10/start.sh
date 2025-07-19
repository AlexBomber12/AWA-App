#!/usr/bin/env bash
set -e
exec celery -A services.fees_h10.worker beat -l info
