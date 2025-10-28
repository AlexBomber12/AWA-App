#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

require_cmd docker

log "Rendering pgBackRest configuration for stanza '${PG_BACKREST_STANZA}'"
render_config

log "Ensuring MinIO bucket '${MINIO_BUCKET:-awa-pgbackups}' exists"
run_in_db bash -s <<'EOS'
set -euo pipefail

AWS_ARGS=(--endpoint-url "${MINIO_ENDPOINT:-http://minio:9000}")
if [[ "${S3_VERIFY_TLS:-n}" =~ ^(n|N|no|No)$ ]]; then
  AWS_ARGS+=(--no-verify-ssl)
fi

export AWS_ACCESS_KEY_ID="${MINIO_ACCESS_KEY:-minioadmin}"
export AWS_SECRET_ACCESS_KEY="${MINIO_SECRET_KEY:-minioadmin}"
export AWS_DEFAULT_REGION="${MINIO_REGION:-us-east-1}"
export AWS_EC2_METADATA_DISABLED=true

BUCKET="${MINIO_BUCKET:-awa-pgbackups}"

if aws "${AWS_ARGS[@]}" s3api head-bucket --bucket "${BUCKET}" >/dev/null 2>&1; then
  echo "Bucket ${BUCKET} already present"
else
  if [[ "${AWS_DEFAULT_REGION}" == "us-east-1" ]]; then
    aws "${AWS_ARGS[@]}" s3api create-bucket --bucket "${BUCKET}" >/dev/null
  else
    aws "${AWS_ARGS[@]}" s3api create-bucket --bucket "${BUCKET}" --create-bucket-configuration "LocationConstraint=${AWS_DEFAULT_REGION}" >/dev/null
  fi
  echo "Created bucket ${BUCKET}"
fi
EOS

log "Running pgBackRest stanza-create"
run_in_db pgbackrest --config="${PG_BACKREST_CONF_PATH}" --stanza="${PG_BACKREST_STANZA}" --log-level-console=info stanza-create

log "Running pgBackRest stanza-check"
run_in_db pgbackrest --config="${PG_BACKREST_CONF_PATH}" --stanza="${PG_BACKREST_STANZA}" --log-level-console=info stanza-check

log "Stanza '${PG_BACKREST_STANZA}' is ready for backups"
