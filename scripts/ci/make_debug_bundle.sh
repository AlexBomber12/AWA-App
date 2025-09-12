#!/usr/bin/env bash
set -Eeuo pipefail

OUT="${1:-debug-bundle}"
TMP="$(mktemp -d)"
ROOT="$(pwd)"

mkdir -p "$TMP/$OUT"

# 1) System & env (redacted)
{
  echo "== GITHUB CONTEXT =="
  env | sort | sed -E 's/(TOKEN|SECRET|PASSWORD|KEY|DSN|AUTH|COOKIE)=.*/\1=REDACTED/g'
  echo
  echo "== DOCKER INFO =="
  docker info || true
  echo
  echo "== GIT STATUS =="
  git rev-parse HEAD || true
  git status -s || true
} > "$TMP/$OUT/system.txt"

# 2) Docker build logs, compose state & logs (if any)
mkdir -p "$TMP/$OUT/docker"
docker ps -a > "$TMP/$OUT/docker/ps.txt" || true
docker compose ps > "$TMP/$OUT/docker/compose-ps.txt" || true
docker compose logs --no-color > "$TMP/$OUT/docker/compose-logs.txt" || true

# 3) Test outputs if present (unit/integration, frontend)
for f in unit.log integ.log pytest-junit.xml vitest.log tsc.log eslint.log; do
  [ -f "$ROOT/$f" ] && cp "$ROOT/$f" "$TMP/$OUT/$f" || true
done

# 4) Alembic status & history if available
mkdir -p "$TMP/$OUT/migrations"
{ alembic current && alembic history -20; } \
  > "$TMP/$OUT/migrations/alembic.txt" 2>&1 || true

tar -C "$TMP" -czf "${OUT}.tar.gz" "$OUT"
echo "::set-output name=bundle::${OUT}.tar.gz" || true
echo "Bundle created: ${OUT}.tar.gz"
