#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-debug-bundle.tar.gz}"
ROOT_DIR="${2:-.}"

TMP_DIR="$(mktemp -d)"
BUNDLE_ROOT="$TMP_DIR/debug-bundle"
mkdir -p "$BUNDLE_ROOT"

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
  python - <<'PY'
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
for file in docker-compose.yml docker-compose.ci.yml docker-compose.postgres.yml docker-compose.dev.yml; do
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

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  capture_cmd "$BUNDLE_ROOT/compose-ps.txt" docker compose "${COMPOSE_ARGS[@]}" ps
  capture_cmd "$BUNDLE_ROOT/compose-logs.txt" docker compose "${COMPOSE_ARGS[@]}" logs --no-color
else
  echo "docker compose not available" >"$BUNDLE_ROOT/compose-ps.txt"
  echo "docker compose not available" >"$BUNDLE_ROOT/compose-logs.txt"
fi

LOG_FILES=(
  unit.log
  integ.log
  vitest.log
  tsc.log
  eslint.log
  docker-build.log
  migrations.log
  preview-url.txt
)
for file in "${LOG_FILES[@]}"; do
  if [ -f "$ROOT_DIR/$file" ]; then
    cp "$ROOT_DIR/$file" "$BUNDLE_ROOT/$file"
  fi
done

mkdir -p "$BUNDLE_ROOT/migrations"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  capture_cmd "$BUNDLE_ROOT/migrations/alembic.txt" docker compose "${COMPOSE_ARGS[@]}" run --rm api alembic current
  capture_cmd "$BUNDLE_ROOT/migrations/alembic.txt" docker compose "${COMPOSE_ARGS[@]}" run --rm api alembic history -20
else
  echo "docker compose not available" >"$BUNDLE_ROOT/migrations/alembic.txt"
fi

tar -czf "$OUTPUT" -C "$TMP_DIR" debug-bundle
