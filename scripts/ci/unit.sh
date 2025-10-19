#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
source .venv/bin/activate
python -m compileall -q packages services tests
pytest -q --maxfail=1 --disable-warnings --junitxml=.local-artifacts/unit-report.xml
