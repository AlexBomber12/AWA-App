# Restore Runbook

## Overview
The backup pipeline uses pgBackRest to capture encrypted PostgreSQL base backups plus continuous WAL archiving into a MinIO bucket. Full backups run on demand or by schedule; differential and incremental backups may be layered as needed. Each archive-push operation streams WAL segments into the same MinIO repository so point-in-time recovery is possible.

## Backup layout
- Repository: S3-compatible MinIO bucket defined by `MINIO_BUCKET` (default `awa-pgbackups`)
- Encryption: repo-level AES-256-CBC using `PG_BR_REPO_PASS`
- Compression: zstd (`compress-type=zst`, `compress-level=3`)
- Retention: `retention-full=7`, `retention-diff=14`, `retention-archive=7`
- WAL: `archive_mode=on`, `archive_command` pushes each segment to MinIO through pgBackRest

The baseline configuration template lives at `ops/backup/pgbackrest/pgbackrest.conf`. Scripts render it with environment-specific secrets before invoking pgBackRest.

## Local backup & restore
1. Start the stack (MinIO + pgBackRest-enabled Postgres):
   ```bash
   docker compose -f docker-compose.yml -f ops/backup/docker-compose.backup.yml up -d minio db-pgbr
   ```
2. Create or update the stanza and verify connectivity:
   ```bash
   bash ops/backup/bin/stanza-setup.sh
   ```
3. Trigger a full backup and generate a WAL record (set `WAL_TEST=1` to insert a sample row):
   ```bash
   WAL_TEST=1 bash ops/backup/bin/backup-now.sh
   ```
4. Validate restores into an isolated data directory:
   ```bash
   bash ops/backup/bin/restore-check.sh
   ```
5. Tear down when finished:
   ```bash
   docker compose -f docker-compose.yml -f ops/backup/docker-compose.backup.yml down -v
   ```

### Make shortcuts (optional)
- `make backup-now` → `bash ops/backup/bin/backup-now.sh`
- `make restore-check` → `bash ops/backup/bin/restore-check.sh`

## GitHub workflow secrets
The restore dry-run workflow reads the following GitHub secrets:

| Secret | Purpose |
| ------ | ------- |
| `MINIO_ENDPOINT` | S3 endpoint URL (e.g., `http://minio:9000` inside workflow network) |
| `MINIO_ACCESS_KEY` | Access key with bucket read/write permissions |
| `MINIO_SECRET_KEY` | Secret key for the user above |
| `PG_BR_REPO_PASS` | pgBackRest repository encryption password |

## Encryption and retention
Backups are encrypted at rest in the MinIO repository using `repo1-cipher-type=aes-256-cbc`. The cipher passphrase is injected via `PG_BR_REPO_PASS`. Retention policies keep seven full backups, fourteen differential backups, and seven days of WAL archives before pruning, mirroring production expectations. Adjust these in `ops/backup/pgbackrest/pgbackrest.conf` if policy changes are approved.

## Common failure modes
- **Bad S3 credentials**: `pgbackrest` reports `AccessDenied` or `SignatureDoesNotMatch`. Verify `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and bucket policy.
- **Missing bucket**: `stanza-setup.sh` fails while creating the repository. Ensure MinIO is running and that the credentials have bucket creation permissions.
- **Incorrect stanza**: `restore-check.sh` exits with `stanza missing`. Re-run `stanza-setup.sh` to recreate metadata or export `PGBACKREST_STANZA` if using a non-default name.
- **Empty repository**: `pgbackrest` restore fails with `no backup to restore`. Run `backup-now.sh` to seed a backup.
- **TLS verification errors**: set `S3_VERIFY_TLS=n` for self-signed or plain HTTP endpoints. For trusted TLS, provide the CA bundle and set `S3_VERIFY_TLS=y`.

Should any step fail, inspect the generated logs under `pgbackrest info` output, `pgbackrest.log` inside the container, and the workflow artifacts.
