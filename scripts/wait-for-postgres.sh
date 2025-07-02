#!/bin/sh
set -e
while ! pg_isready -U awa -h ${POSTGRES_HOST:-postgres} >/dev/null 2>&1; do
  sleep 1
done
exec "$@"
