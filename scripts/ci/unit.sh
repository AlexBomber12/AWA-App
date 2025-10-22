#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
source .venv/bin/activate
python -m compileall -q packages services tests
ruff check --select E9,F63,F7,F82 .
pytest -q --maxfail=1 --disable-warnings --junitxml=.local-artifacts/unit-report.xml
