#!/usr/bin/env bash

# Common helpers for backup automation scripts.

set -o errexit
set -o pipefail
set -o nounset

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BACKUP_ROOT="${REPO_ROOT}/ops/backup"
PG_BACKREST_CONF_PATH="${PG_BACKREST_CONF_PATH:-/var/lib/postgresql/pgbackrest/pgbackrest.conf}"
PG_BACKREST_STANZA="${PGBACKREST_STANZA:-awa}"

BACKUP_COMPOSE_FILES_DEFAULT="docker-compose.yml ops/backup/docker-compose.backup.yml"
BACKUP_COMPOSE_FILES="${BACKUP_COMPOSE_FILES:-$BACKUP_COMPOSE_FILES_DEFAULT}"

IFS=' ' read -r -a _BACKUP_COMPOSE_ARRAY <<< "${BACKUP_COMPOSE_FILES}"

COMPOSE_CMD=(docker compose)
for file in "${_BACKUP_COMPOSE_ARRAY[@]}"; do
  COMPOSE_CMD+=(-f "${file}")
done

BACKUP_EXEC_TTY_OPT="${BACKUP_EXEC_TTY_OPT:--T}"

log() {
  local msg="$*"
  printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "${msg}"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Required command '${cmd}' not found in PATH" >&2
    exit 1
  fi
}

compose() {
  (
    cd "${REPO_ROOT}"
    "${COMPOSE_CMD[@]}" "$@"
  )
}

run_in_db() {
  compose exec "${BACKUP_EXEC_TTY_OPT}" db-pgbr "$@"
}

render_config() {
  run_in_db bash -s <<'EOS'
set -euo pipefail
TEMPLATE_DIR=${TEMPLATE_DIR:-/pgbackrest-template}
CONFIG_DIR=${CONFIG_DIR:-/var/lib/postgresql/pgbackrest}
CONFIG_PATH=${CONFIG_PATH:-${CONFIG_DIR}/pgbackrest.conf}

mkdir -p "${CONFIG_DIR}"
export MINIO_BUCKET=${MINIO_BUCKET:-awa-pgbackups}
export MINIO_REGION=${MINIO_REGION:-us-east-1}
export S3_VERIFY_TLS=${S3_VERIFY_TLS:-n}
export MINIO_ENDPOINT=${MINIO_ENDPOINT:-http://minio:9000}
export MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY:-minioadmin}
export MINIO_SECRET_KEY=${MINIO_SECRET_KEY:-minioadmin}
export PG_BR_REPO_PASS=${PG_BR_REPO_PASS:-example-pgbackrest-pass}
envsubst < "${TEMPLATE_DIR}/pgbackrest.conf" > "${CONFIG_PATH}"
chmod 600 "${CONFIG_PATH}"
EOS
}
