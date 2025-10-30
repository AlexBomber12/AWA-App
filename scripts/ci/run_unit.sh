#!/usr/bin/env bash
# Run the fast unit-suite with coverage as the single source of truth.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

export COVERAGE_FILE="${COVERAGE_FILE:-.coverage}"

PYTEST_CMD=(
  python -m pytest -q
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

python -m coverage report -m > coverage.txt
