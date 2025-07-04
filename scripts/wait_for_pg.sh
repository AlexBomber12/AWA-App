#!/usr/bin/env bash
for i in {1..30}; do
  pg_isready -h localhost -p 5432 -U postgres && exit 0
  sleep 1
done
echo "Postgres never became ready" >&2
exit 1
