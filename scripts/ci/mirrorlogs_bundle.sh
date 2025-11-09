#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
ARTIFACT_ROOT="${ROOT}/artifacts"
TARGET_DIR="${ARTIFACT_ROOT}/mirrorlogs"
mkdir -p "${TARGET_DIR}"

copy_into_target() {
  local src="$1" rel
  if [[ -f "${src}" ]]; then
    rel="${src#${ROOT}/}"
    rel="${rel#./}"
    mkdir -p "${TARGET_DIR}/$(dirname "${rel}")"
    cp "${src}" "${TARGET_DIR}/${rel}"
  fi
}

collect_from_dir() {
  local base="$1"
  if [[ -d "${base}" ]]; then
    find "${base}" -type f \( -name '*.log' -o -name '*.txt' -o -name '*.json' -o -name '*junit*.xml' -o -name '*.junit.xml' \) -print0 |
      while IFS= read -r -d '' file; do
        copy_into_target "${file}"
      done
  fi
}

copy_into_target "${ROOT}/coverage.xml"
copy_into_target "${ROOT}/coverage.txt"
copy_into_target "${ROOT}/diff-coverage.txt"
copy_into_target "${ROOT}/diff-cover.html"
copy_into_target "${ROOT}/.coverage"

collect_from_dir "${ROOT}/artifacts"
collect_from_dir "${ROOT}/.pytest_cache"

# Capture Docker/service logs when available.
if command -v docker >/dev/null 2>&1; then
  mapfile -t containers < <(docker ps --format '{{.Names}}' 2>/dev/null || true)
  if [[ ${#containers[@]} -gt 0 ]]; then
    mkdir -p "${TARGET_DIR}/docker"
    for name in "${containers[@]}"; do
      safe_name="${name//[^a-zA-Z0-9_.-]/_}"
      docker logs --tail=1000 "${name}" > "${TARGET_DIR}/docker/${safe_name}.log" 2>&1 || true
    done
  fi
fi

# Include Alembic outputs and structlog-style JSON logs if present.
collect_from_dir "${ROOT}/services/api"
collect_from_dir "${ROOT}/logs"

# System snapshot
{
  echo "## System info"
  date -u
  echo
  python -V 2>&1 || true
  pip freeze 2>/dev/null || true
  git rev-parse HEAD 2>/dev/null || true
  uname -a 2>/dev/null || true
} > "${TARGET_DIR}/system-info.txt"

ARCHIVE="${ARTIFACT_ROOT}/mirrorlogs.tar"
rm -f "${ARCHIVE}" "${ARCHIVE}.zst" "${ARCHIVE}.gz"
tar -C "${ARTIFACT_ROOT}" -cf "${ARCHIVE}" mirrorlogs
if command -v zstd >/dev/null 2>&1; then
  zstd -T0 --rm "${ARCHIVE}"
else
  gzip -f "${ARCHIVE}"
fi
