#!/usr/bin/env bash
set -e
for i in {1..60}; do
  if pg_isready -h "${PG_HOST:-localhost}" -p "${PG_PORT:-5432}" -U "${PG_USER:-postgres}" -d "${PG_DATABASE:-awa}" > /dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done
echo "Postgres did not become ready" >&2
exit 1
