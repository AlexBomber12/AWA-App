#!/usr/bin/env bash
set -euo pipefail

# gather system info
{
  echo "### Environment"
  env | sort | sed -E 's/(TOKEN|SECRET|PASSWORD|API_KEY|DSN|AUTH|COOKIE)=[^[:space:]]*/\1=[REDACTED]/Ig'
  echo
  echo "### Docker"
  docker info 2>/dev/null || true
  echo
  echo "### Git"
  git status --short --branch 2>/dev/null || true
} > system.txt

# docker compose logs when available
if docker compose ps >/dev/null 2>&1; then
  docker compose logs --no-color > compose-logs.txt || true
fi

# alembic information
mkdir -p migrations
if command -v alembic >/dev/null 2>&1; then
  {
    echo '$ alembic current'
    alembic current || true
    echo
    echo '$ alembic history -20'
    alembic history -20 || true
  } > migrations/alembic.txt
fi

# gather bundle files
bundle_files="system.txt"
for f in compose-logs.txt unit.log integ.log vitest.log tsc.log eslint.log docker-build.log;
do [ -f "$f" ] && bundle_files+=" $f"; done
[ -d migrations ] && bundle_files+=" migrations"

tar -czf debug-bundle.tar.gz $bundle_files
