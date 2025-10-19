#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local-artifacts
bash scripts/ci/unit.sh
bash scripts/ci/migrations.sh
bash scripts/ci/integration.sh
echo "LOCAL CI OK"
