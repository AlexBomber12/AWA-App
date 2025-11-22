#!/usr/bin/env bash
# Run the fast unit-suite with coverage as the single source of truth.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

export COVERAGE_FILE="${COVERAGE_FILE:-.coverage}"

PYTEST_CMD=(
  python -m pytest -q
  -m
  "not integration and not live"
  --cov=packages
  --cov=services
  --cov-config=.github/coverage.ini
  --cov-report=term-missing:skip-covered
  --cov-report=xml:coverage.xml
)

if [[ -n "${PYTEST_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=(${PYTEST_ARGS})
  PYTEST_CMD+=("${EXTRA_ARGS[@]}")
fi

echo "Executing: ${PYTEST_CMD[*]}"
"${PYTEST_CMD[@]}"

coverage report -m --rcfile=.github/coverage.ini > coverage.txt
coverage xml --rcfile=.github/coverage.ini -o coverage.xml
python3 scripts/ci/check_coverage_thresholds.py coverage.xml
