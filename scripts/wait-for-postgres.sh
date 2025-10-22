#!/usr/bin/env bash
set -e
for i in {1..30}; do
  pg_isready -h "${PG_HOST:-localhost}" -p "${PG_PORT:-5432}" -U "${PG_USER:-postgres}" && exit 0
  sleep 1
done
echo "Postgres never became ready" >&2
exit 1
