#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

require_cmd docker

RESTORE_TARGET_DIR="${RESTORE_TARGET_DIR:-/var/lib/postgresql/restoredata}"
RESTORE_PORT="${RESTORE_PORT:-55432}"
WAIT_SECONDS="${WAIT_SECONDS:-45}"

log "Rendering pgBackRest configuration for stanza '${PG_BACKREST_STANZA}'"
render_config

log "Restoring latest backup into '${RESTORE_TARGET_DIR}' and validating startup on port ${RESTORE_PORT}"
run_in_db bash -s <<'EOS'
set -euo pipefail

CONFIG_PATH=${CONFIG_PATH:-/var/lib/postgresql/pgbackrest/pgbackrest.conf}
TARGET_DIR=${RESTORE_TARGET_DIR:-/var/lib/postgresql/restoredata}
PORT=${RESTORE_PORT:-55432}
WAIT_SECONDS=${WAIT_SECONDS:-45}
STANZA=${PGBACKREST_STANZA:-awa}

DB_NAME=${POSTGRES_DB:-postgres}
DB_USER=${POSTGRES_USER:-postgres}
export PGPASSWORD=${POSTGRES_PASSWORD:-postgres}

pg_ctl_bin=$(command -v pg_ctl)
pg_isready_bin=$(command -v pg_isready)

cleanup() {
  if [[ -d "${TARGET_DIR}" ]]; then
    "${pg_ctl_bin}" -D "${TARGET_DIR}" -m fast stop >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}"

pgbackrest --config="${CONFIG_PATH}" --stanza="${STANZA}" --type=immediate --target-action=promote --delta --target-dir="${TARGET_DIR}" restore

"${pg_ctl_bin}" -D "${TARGET_DIR}" -w -o "-c listen_addresses='127.0.0.1' -c port=${PORT} -c archive_mode=off -c unix_socket_directories='/tmp'" start

deadline=$((SECONDS + WAIT_SECONDS))
until "${pg_isready_bin}" -h 127.0.0.1 -p "${PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
  if (( SECONDS > deadline )); then
    echo "Timed out waiting for restored PostgreSQL to become ready" >&2
    exit 1
  fi
  sleep 1
done

psql -h 127.0.0.1 -p "${PORT}" -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -c 'SELECT 1;'

echo "Restore check succeeded"
EOS

log "Restore validation completed"
