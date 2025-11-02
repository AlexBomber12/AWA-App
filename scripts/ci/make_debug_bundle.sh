#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-debug-bundle.tar.gz}"
ROOT_DIR="${2:-.}"

TMP_DIR="$(mktemp -d)"
BUNDLE_ROOT="$TMP_DIR/debug-bundle"
mkdir -p "$BUNDLE_ROOT"
mkdir -p "$BUNDLE_ROOT/artifacts"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

capture_cmd() {
  local outfile="$1"
  shift || true
  local cmd=("$@")
  (
    set +e
    echo "\$ ${cmd[*]}"
    "${cmd[@]}" 2>&1
    local status=$?
    echo "exit_code=$status"
  ) >>"$outfile"
}

sanitize_env() {
  if ! command -v python >/dev/null 2>&1; then
    echo "python command not available"
    return 0
  fi
  python - <<'PY' || true
import os
import re
sensitive = re.compile(r'([A-Za-z0-9_]*?(?:TOKEN|SECRET|PASSWORD|API_KEY|DSN|AUTH|COOKIE)[A-Za-z0-9_]*=)(.*)', re.IGNORECASE)
for key in sorted(os.environ):
    value = os.environ[key]
    line = f"{key}={value}"
    def repl(match: re.Match) -> str:
        return match.group(1) + '<redacted>'
    line = sensitive.sub(repl, line)
    print(line)
PY
}

COMPOSE_ARGS=()
for file in docker-compose.yml docker-compose.ci.yml; do
  if [ -f "$file" ]; then
    COMPOSE_ARGS+=("-f" "$file")
  fi
done

SYSTEM_FILE="$BUNDLE_ROOT/system.txt"
{
  echo "# System diagnostics"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "Hostname: $(hostname || echo 'unknown')"
  echo
  echo "## Git"
  if git rev-parse --short HEAD >/dev/null 2>&1; then
    echo "Commit: $(git rev-parse --short HEAD)"
    git status --short --branch || true
  else
    echo "Git information unavailable"
  fi
  echo
  echo "## Environment (sanitized)"
  sanitize_env || true
  echo
  if command -v docker >/dev/null 2>&1; then
    echo "## Docker"
    (docker version 2>&1 || true)
    (docker info 2>&1 || true)
  else
    echo "## Docker"
    echo "docker command not available"
  fi
} >"$SYSTEM_FILE"

capture_cmd "$BUNDLE_ROOT/python-version.txt" python --version
capture_cmd "$BUNDLE_ROOT/pip-freeze.txt" python -m pip freeze

if command -v docker >/dev/null 2>&1; then
  capture_cmd "$BUNDLE_ROOT/docker-ps.txt" docker ps -a
  if docker compose version >/dev/null 2>&1; then
    capture_cmd "$BUNDLE_ROOT/compose-ps.txt" docker compose "${COMPOSE_ARGS[@]}" ps
    capture_cmd "$BUNDLE_ROOT/compose-logs.txt" docker compose "${COMPOSE_ARGS[@]}" logs --no-color
  else
    echo "docker compose not available" >"$BUNDLE_ROOT/compose-ps.txt"
    echo "docker compose not available" >"$BUNDLE_ROOT/compose-logs.txt"
  fi
else
  echo "docker not available" >"$BUNDLE_ROOT/docker-ps.txt"
  echo "docker not available" >"$BUNDLE_ROOT/compose-ps.txt"
  echo "docker not available" >"$BUNDLE_ROOT/compose-logs.txt"
fi

LOG_FILES=(
  unit.log
  unit-setup.log
  integ.log
  integration-compose-up.log
  integration-ready.log
  vitest.log
  tsc.log
  eslint.log
  docker-build.log
  migrations.log
  preview-compose-up.log
  preview-ready.log
  preview-url.txt
  artifacts/lint.log
  artifacts/migrations.log
)
for file in "${LOG_FILES[@]}"; do
  if [ -f "$ROOT_DIR/$file" ]; then
    mkdir -p "$(dirname "$BUNDLE_ROOT/$file")"
    cp "$ROOT_DIR/$file" "$BUNDLE_ROOT/$file"
  fi
done

for file in "$ROOT_DIR"/coverage-*.xml "$ROOT_DIR"/coverage-*.txt; do
  if [ -f "$file" ]; then
    cp "$file" "$BUNDLE_ROOT/$(basename "$file")"
  fi
done

for file in "$ROOT_DIR"/.coverage*; do
  if [ -f "$file" ]; then
    cp "$file" "$BUNDLE_ROOT/$(basename "$file")"
  fi
done

for file in "$ROOT_DIR"/diff-coverage*.txt "$ROOT_DIR"/diff-base.txt; do
  if [ -f "$file" ]; then
    cp "$file" "$BUNDLE_ROOT/$(basename "$file")"
  fi
done

mkdir -p "$BUNDLE_ROOT/migrations"
if [ "${SKIP_ALEMBIC_DEBUG:-0}" != "1" ]; then
  ALEMBIC_FILE="$BUNDLE_ROOT/migrations/alembic.txt"
  : >"$ALEMBIC_FILE"
  if command -v alembic >/dev/null 2>&1 && [ -f "services/api/alembic.ini" ]; then
    capture_cmd "$ALEMBIC_FILE" alembic -c services/api/alembic.ini current -v
    capture_cmd "$ALEMBIC_FILE" alembic -c services/api/alembic.ini history -20
  elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    capture_cmd "$ALEMBIC_FILE" docker compose "${COMPOSE_ARGS[@]}" run --rm api alembic current -v
    capture_cmd "$ALEMBIC_FILE" docker compose "${COMPOSE_ARGS[@]}" run --rm api alembic history -20
  else
    echo "alembic not available in current environment" >"$ALEMBIC_FILE"
  fi
fi

if command -v curl >/dev/null 2>&1; then
  capture_cmd "$BUNDLE_ROOT/http-ready.txt" bash -c 'curl -fsS --max-time 5 http://localhost:8000/ready || true'
  capture_cmd "$BUNDLE_ROOT/http-metrics.txt" bash -c 'curl -fsS --max-time 5 http://localhost:8000/metrics || true'
else
  echo "curl not available" >"$BUNDLE_ROOT/http-ready.txt"
  echo "curl not available" >"$BUNDLE_ROOT/http-metrics.txt"
fi

tar -czf "$OUTPUT" -C "$TMP_DIR" debug-bundle
