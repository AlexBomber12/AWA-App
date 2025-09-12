#!/usr/bin/env bash
set -Eeuo pipefail

NAME="${1:-debug-bundle}"
OUT="${NAME}.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# gather environment (redacted later)
env > "$TMP/env.txt" || true

# system info
uname -a > "$TMP/uname.txt" || true

# docker info
if command -v docker >/dev/null 2>&1; then
  docker info > "$TMP/docker-info.txt" 2>&1 || true
  docker compose ps > "$TMP/docker-compose-ps.txt" 2>&1 || true
fi

# git status
if command -v git >/dev/null 2>&1; then
  git status --short > "$TMP/git-status.txt" 2>&1 || true
  git log -1 --stat > "$TMP/git-last-commit.txt" 2>&1 || true
fi

# docker compose logs snapshot
if command -v docker >/dev/null 2>&1; then
  docker compose logs --no-color > "$TMP/compose-logs.txt" 2>&1 || true
fi

# copy test logs if present
for f in unit.log integ.log vitest.log tsc.log eslint.log; do
  [ -f "$f" ] && cp "$f" "$TMP/$f"
done

# Alembic info if available
if [ -f alembic.ini ]; then
  alembic current > "$TMP/alembic-current.txt" 2>&1 || true
  alembic history > "$TMP/alembic-history.txt" 2>&1 || true
fi

# redact secrets
find "$TMP" -type f -print0 | xargs -0 -I{} sed -i -E 's/(TOKEN|SECRET|PASSWORD|KEY|DSN|AUTH|COOKIE)=\S+/\1=REDACTED/g' {}

# create archive
tar -czf "$OUT" -C "$TMP" .
echo "debug bundle saved to $OUT"
