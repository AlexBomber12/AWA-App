#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

require_cmd docker

BACKUP_TYPE="${BACKUP_TYPE:-full}"
WAL_TEST="${WAL_TEST:-0}"

case "${BACKUP_TYPE}" in
  full|diff|incr) ;;
  *) echo "Unsupported BACKUP_TYPE '${BACKUP_TYPE}'. Use full, diff, or incr." >&2; exit 1 ;;
esac

log "Rendering pgBackRest configuration for stanza '${PG_BACKREST_STANZA}'"
render_config

if [[ "${WAL_TEST}" == "1" ]]; then
  log "Generating WAL traffic prior to backup"
  run_in_db bash -s <<'EOS'
set -euo pipefail
DB_NAME="${POSTGRES_DB:-postgres}"
DB_USER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
psql -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" <<'SQL'
CREATE TABLE IF NOT EXISTS public.backup_probe (
  id bigserial PRIMARY KEY,
  inserted_at timestamptz DEFAULT now(),
  note text DEFAULT 'wal-test'
);
INSERT INTO public.backup_probe(note) VALUES ('wal smoke test');
SQL
EOS
fi

log "Starting pgBackRest ${BACKUP_TYPE} backup"
run_in_db pgbackrest --config="${PG_BACKREST_CONF_PATH}" --stanza="${PG_BACKREST_STANZA}" --type="${BACKUP_TYPE}" --log-level-console=info backup

log "pgBackRest info after backup"
run_in_db pgbackrest --config="${PG_BACKREST_CONF_PATH}" --stanza="${PG_BACKREST_STANZA}" info

log "Backup completed"
