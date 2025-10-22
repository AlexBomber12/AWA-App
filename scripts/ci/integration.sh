#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
source .venv/bin/activate
if [ -d tests/integration ]; then
  pytest -q -m integration tests/integration --maxfail=1 --disable-warnings --junitxml=.local-artifacts/integration-report.xml
else
  echo "no integration tests"
fi
