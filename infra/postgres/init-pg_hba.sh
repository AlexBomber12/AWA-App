#!/bin/bash
set -e
TARGET="${PGDATA:-/var/lib/postgresql/data}"
cp /etc/postgresql/pg_hba.conf "$TARGET/pg_hba.conf"
