# Dry-run Specification

“Dry-run” is the shared safeguard for workflows that could otherwise mutate production state. When the flag is enabled a task processes inputs, validates permissions, and emits structured logs/metrics, but it refuses to persist changes. The feature is implemented consistently across backup/restore, the logistics ETL, the price importer CLI, and microservices that accept operational write requests (currently the repricer service).

## Responsibilities
| Workflow | Responsibilities while `dry_run` is enabled |
| -------- | ------------------------------------------- |
| Backup / restore validation | Exercise pgBackRest scripts end-to-end (MinIO access, stanza bootstrap, WAL replay) without promoting the restored data directory. The workflow must log the commands it would run and capture artifacts for auditing. |
| Logistics ETL (`services/logistics_etl.flow`) | Fetch sources, parse CSV/JSON payloads, and report how many rows would be upserted per carrier without writing to `logistics_rates` or calling `mark_load`. Metrics and logs still emit to confirm coverage. |
| Price importer (`python -m services.price_importer.import`) | Parse vendor spreadsheets, resolve vendor IDs, and report insert/update counts. No `vendor_prices` rows are written; the repository returns `(len(rows), 0)` to make metrics predictable. |
| Repricer service (`POST /pricing/apply`) | Validate payloads, fetch decision context, and return `changed` flags for every ASIN. When `dry_run` is true the API skips insertions into `price_updates_log` and avoids committing the session. |

## Controls
- **Restore workflow:** GitHub Actions jobs call `ops/backup/bin/restore-check.sh`, which always restores into `RESTORE_TARGET_DIR` and never promotes the temporary cluster. Local runs mimic this by invoking the same script (optionally overriding `RESTORE_TARGET_DIR`/`RESTORE_PORT`).
- **Logistics ETL:** Pass `--dry-run` to `python -m services.logistics_etl.flow` or call `flow.full(dry_run=True)` from celery/cron contexts. The CLI flag is also plumbed through `services/logistics_etl/cron.py`.
- **Price importer:** Add `--dry-run` to every `python -m services.price_importer.import ...` invocation. The integration test described below enforces that no DML occurs when the switch is set.
- **Repricer service:** Include `"dry_run": true` in the JSON body sent to `/pricing/apply`. The Pydantic schema defaults the field to `false`, so callers must opt in explicitly.

## Logging and metrics
- Each component logs the command invocation, resolved configuration, and the number of rows/records it would change. Use structured logging (`extra={"dry_run": True}`) where available so Loki/Splunk dashboards can filter by the flag.
- Prometheus counters keep incrementing: e.g., `etl_runs_total` and `etl_duration_seconds` emit even
  when no rows are persisted. This lets us compare dry-run vs. live latency.
- The repricer microservice includes `"changed": bool` per ASIN to prove that decisions still execute during rehearsal.
- Backup/restore jobs upload the same artifacts as a live run (`pgbackrest.log`, `system.txt`, `compose-logs.txt`) so reviewers can trace every command without rerunning it.

## Validation
- **Local:** run `pytest -q tests/integration/price_importer/test_price_importer_cli.py -m integration` after moving the SQLite-backed dry-run test into the integration suite. For services, invoke the commands above with `--dry-run` and verify that timestamps change while database counts remain constant.
- **CI:** the integration job spins up Postgres/Redis via docker-compose and executes the dry-run price importer test automatically. The backup workflow publishes every restore-check command in its job summary, and logistics ETL cron runs emit `dry_run=true` structured logs that land in `mirror-logs/<scope>/latest/etl/*.log`.

## See also
- [Agents](agents.md)
- [Testing](TESTING.md)
- [Restore runbook](runbooks/restore.md)
- [CI Debug](CI_debug.md)
