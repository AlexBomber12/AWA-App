#!/usr/bin/env bash
set -euo pipefail

# Determine whether the integration suite must run based on changed files.
# Outputs "run_integration=true|false" via GITHUB_OUTPUT.

DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
BASE_REF_ENV="${BASE_REF:-}"
BASE_BRANCH_NAME="${BASE_BRANCH_NAME:-${DEFAULT_BRANCH}}"
FORCE_FULL="${FORCE_FULL_INTEGRATION:-false}"
LABEL_FORCE="${RUN_INTEGRATION_LABEL:-false}"

ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

is_commit_sha() {
  [[ "$1" =~ ^[0-9a-f]{7,40}$ ]]
}

if [[ "${FORCE_FULL}" == "true" ]]; then
  DECISION="true"
elif [[ "${LABEL_FORCE}" == "true" ]]; then
  DECISION="true"
else
  BASE_SHA="${BASE_REF_ENV}"
  if [[ -z "${BASE_SHA}" ]]; then
    # Fall back to the tracked default branch.
    git fetch --no-tags --prune --depth=1 origin "${DEFAULT_BRANCH}" >/dev/null 2>&1
    BASE_SHA="origin/${DEFAULT_BRANCH}"
  elif ! git cat-file -t "${BASE_SHA}" >/dev/null 2>&1; then
    if is_commit_sha "${BASE_SHA}"; then
      git fetch --no-tags --prune --depth=1 origin "${BASE_SHA}" >/dev/null 2>&1 || true
    else
      git fetch --no-tags --prune --depth=1 origin "${BASE_BRANCH_NAME}" >/dev/null 2>&1
      BASE_SHA="origin/${BASE_BRANCH_NAME}"
    fi
  fi

  if ! git rev-parse --quiet --verify "${BASE_SHA}^{commit}" >/dev/null; then
    echo "::warning ::Unable to resolve base ref ${BASE_SHA}; defaulting to full integration run"
    DECISION="true"
  else
    mapfile -t FILES < <(git diff --name-only "${BASE_SHA}"...HEAD)
    if [[ ${#FILES[@]} -eq 0 ]]; then
      DECISION="false"
    else
      PATTERN=$'^(services/.+/migrations/|services/(etl|logistics_etl|price_importer|fees_h10|worker)/|services/api/(routes|roi_.+|security|schemas|main|.*alembic.*|.*migrations.*)|packages/awa_common/(metrics|logging|security|dsn|settings)/|.*(\\.sql|docker-compose|compose\\.ya?ml|alembic\\.ini))'
      DECISION="false"
      for file in "${FILES[@]}"; do
        if [[ "${file}" =~ ${PATTERN} ]]; then
          DECISION="true"
          break
        fi
      done
    fi
  fi
fi

OUTPUT_FILE="${GITHUB_OUTPUT:-/tmp/github_output}"
mkdir -p "$(dirname "${OUTPUT_FILE}")"
echo "run_integration=${DECISION}" >> "${OUTPUT_FILE}"
echo "run_integration=${DECISION}"
