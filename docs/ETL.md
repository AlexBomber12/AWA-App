# ETL Playbook

AWA’s ETL agents share a reliability layer for idempotency, retries, and observability. Use the
components in `packages/awa_common` to deliver repeatable pipelines that survive restarts and replay.

## Idempotency via `load_log`

- The schema defined in `services/api/migrations/versions/0032_etl_reliability.py` creates
  `load_log` with a unique constraint on `(source, idempotency_key)`. Columns:
- `source` (≤128 chars) – logical agent name (`fees_h10`, `ingest.import_file`, …).
  - `idempotency_key` (64-char BLAKE2 digest) computed in `packages/awa_common/etl/idempotency.py`.
  - `status` in `{pending, success, skipped, failed}`; constants live in
    `packages/awa_common/db/load_log.py`.
  - `payload_meta` JSONB storing fingerprints, sizes, hashes, and optional extras.
  - `processed_by`, `task_id`, `duration_ms`, `error_message`, `created_at`, `updated_at`.
- Populate `payload_meta` with enough breadcrumbs to debug a run without reprocessing: include
  `source_uri` (or URI list), `target_table`, `dialect/report_type`, `rows`, a file hash, and any
  run flags such as `streaming`/`force`. Using `on_duplicate="update_meta"` with `process_once`
  will mark the row as `skipped` on duplicates while refreshing that metadata.
- `compute_idempotency_key` and `build_payload_meta` prefer stable remote metadata (`etag`,
  `last_modified`, `content_length`, `content_md5`), fall back to local file stats, then the raw
  payload (`blake2b` hash). Persisting these values guarantees we can prove what was loaded.
- Duplicate work is detected at insert time; the guard can either skip (`status='skipped'`) or update
  metadata for auditing.

## HTTP Policy

- Always call `awa_common.http_client.HTTPClient` / `AsyncHTTPClient` for outbound requests; the
  deprecated `packages/awa_common/etl/http` shims remain only for legacy tests and the old
  `services.etl.http_client` module has been removed entirely.
- Defaults come from `settings.HTTP_*`: connect 5 s, read 30 s, total 60 s with `HTTP_MAX_RETRIES`
  exponential backoff (`HTTP_BACKOFF_BASE_S`/`HTTP_BACKOFF_MAX_S`/`HTTP_BACKOFF_JITTER_S`) and
  retryable status codes in `HTTP_RETRY_STATUS_CODES` (honours `Retry-After`).
- Integration-specific knobs live in settings and stay env-driven: `HELIUM10_BASE_URL`,
  `HELIUM10_TIMEOUT_S`, `HELIUM10_MAX_RETRIES`, `LOGISTICS_TIMEOUT_S`/`LOGISTICS_RETRIES`/retry
  backoff, LLM timeouts (`LLM_REQUEST_TIMEOUT_S`), plus `S3_CONNECT_TIMEOUT_S` /
  `S3_READ_TIMEOUT_S` / `S3_ADDRESSING_STYLE` for storage clients.
- Every attempt emits `external_http_requests_total`, latency histograms, and `external_http_retries_total`
  with the `integration` label so backoff/throttling is visible alongside structured
  `external_http.retry` logs. Use `allowed_statuses={...}` when cacheable responses (e.g. JWKS 304)
  should be treated as success without incrementing failures.

## Object storage

- Build S3/MinIO clients with `awa_common.minio.get_s3_client_kwargs()` and
  `get_s3_client_config()` so endpoint, credentials, pool sizing, and connect/read timeouts stay
  centralised. Avoid ad-hoc boto3/aioboto3 kwargs in API/worker routes.

## Streaming ingest

- Celery `ingest.import_file` switches to streaming mode when `INGEST_STREAMING_ENABLED=1` and the
  resolved payload size strictly exceeds `INGEST_STREAMING_THRESHOLD_MB`. Smaller files continue down
  the legacy in-memory path.
- Streaming chunk sizing defaults to `INGEST_STREAMING_CHUNK_SIZE` rows. `INGEST_STREAMING_CHUNK_SIZE_MB`
  remains available as a size-based hint and is converted to rows when the row override is not set.
- API uploads (`/ingest` or `/upload`) always enqueue the Celery task; the legacy worker-side
  `ingest_router` HTTP shim has been removed in favour of the unified API entrypoints.

## Shared validation & retry helpers

- Ingest endpoints now return a structured `ErrorResponse` (defined in `services/api/schemas.py`) with machine
  readable codes (`unsupported_file_format`, `bad_request`, `unprocessable_entity`, `validation_error`)
  and the `X-Request-ID` echoed back to the caller. The FastAPI layer increments
  `api_ingest_4xx_total{code}`/`api_ingest_5xx_total` and logs the user sub, route, and error code so
  dashboards can separate unsupported files from schema failures.
- CSV/XLSX scrubbing logic lives in `packages/awa_common/vendor`. Functions such as
  `normalize_currency`, `parse_decimal`, and `parse_date` are shared by the price importer and
  logistics ETL so we only maintain one set of validators. Normalization and schema errors feed the
  new Prometheus counters `etl_row_normalized_total{job}` and `etl_normalize_errors_total{job,reason}`.
- Long lived retry policies now funnel through `packages/awa_common/retries`. Supply a `RetryConfig`
  and use `@retry`/`@aretry` instead of hand rolling Tenacity loops; the helper logs every retry with
  the current request id and emits `awa_retry_attempts_total{operation}` plus
  `awa_retry_sleep_seconds{operation}` so queuing delays are visible.
- Vendor pricing tables are defined once in `packages/awa_common/models_vendor.py`; price importer and
  related ETL tasks re-use these ORM models directly to avoid drift.
- Typed ETL rows live in `packages/awa_common/types`. `RateRowModel` and `PriceRowModel` validate
  Decimal/date fields at runtime while the corresponding `TypedDict` definitions feed mypy so that
  price importer and logistics ETL hand off consistent structures before writing to Postgres.

## Task Lifecycle

- Wrap mutable sections with `packages/awa_common/etl/guard.process_once`:
  ```python
  from awa_common.etl.guard import process_once
  from awa_common.etl.idempotency import compute_idempotency_key, build_payload_meta
  from awa_common.metrics import record_etl_run, record_etl_skip

  payload_meta = build_payload_meta(path=source_path, remote_meta=remote_headers)
  key = compute_idempotency_key(path=source_path, remote_meta=remote_headers)

  with process_once(
      SessionLocal,
      source="fees_h10",
      payload_meta=payload_meta,
      idempotency_key=key,
  ) as handle:
      if handle is None:
          record_etl_skip("fees_h10")
          return
      with record_etl_run("fees_h10"):
      # use handle.session for transactional work
      ingest_rows(handle.session, payload_meta)
  ```
- On entry the guard inserts a `pending` row, commits, and returns a `ProcessHandle`. Exiting with no
  exception marks the row `success` and records `duration_ms`; raising an exception rolls back and
  marks `failed` with the truncated message (max 1024 chars).
- When a manual `--force` or replay run is necessary, generate a new idempotency key (append a
  timestamp or hash of the override parameters) so the guard does not skip the attempt; otherwise
  duplicates default to `status='skipped'`.
- Celery schedules live in `services/worker/celery_app.py`. Environment switches such as
  `SCHEDULE_MV_REFRESH`, `MV_REFRESH_CRON`, and `SCHEDULE_LOGISTICS_ETL` control when pipelines run
  and are validated through `awa_common.cron_config.CronSchedule`. Invalid cron strings are logged
  and block the worker from starting, so rely on those toggles rather than bespoke crontabs.

## Backfill & Replay

- Re-run a job by supplying the same source and idempotency key. The guard returns `None`, letting you
  skip work safely. Pass `on_duplicate="update_meta"` when you want to refresh metadata while keeping
  the result marked as `skipped`.
- To replay a period:
  1. Compute idempotency keys for the target artefacts (e.g. one per day) with
     `compute_idempotency_key`.
  2. Delete or set `status='failed'` for the relevant rows if you intend to recompute; otherwise rely on
     the guard to skip duplicates.
  3. Trigger the Celery task (`services.worker.tasks`) or CLI entry point with `force=True` if the agent
     supports it (see `services/api/routes/ingest.submit_ingest`).
- Because writes happen in a single transaction inside `process_once`, reruns are atomic—either the
  run completes and marks `success` or nothing is committed.

## Supported pipelines

- **CSV/XLSX ingest (`etl.load_csv`)** – entrypoints: `python -m etl.load_csv --source ... --table auto` and
  the Celery task `ingest.import_file`. Worker containers no longer expose any HTTP ingest route; use the
  API `/ingest` or `/upload` endpoints (which trigger the same Celery task) or call the task internally.
  Idempotency key comes from the uploaded file hash/dialect (or the API-provided key) and `payload_meta`
  records `source_uri`, `target_table`, `dialect`, `rows`, `file_sha256`, and flags such as
  `streaming`/`force`. Returns are handled through the `returns_report` dialect; the legacy
  `services/returns_etl` CLI was retired (see `docs/legacy_samples/returns_loader.md`).
- **Helium10 fees (`services.fees_h10.worker.refresh_fees`)** – keyed on the sorted ASIN list with metadata
  for `asin_count` and source URL; duplicate keys set `status='skipped'` before any API calls.
- **Logistics ETL (`services.logistics_etl.flow.run_once_with_guard` via Celery `logistics.etl.full`)** –
  fingerprints each snapshot by `seqno`/SHA256 and records `rows_in`/`rows_upserted` in `payload_meta`.
  Repeat runs with the same fingerprint are skipped; the historical `logistics_loadlog` table remains for
  analytics but idempotency is enforced via `load_log`.
- **Price importer (`services.price_importer.import`)** – keyed on vendor and input file stats; run with
  `python -m services.price_importer.import --file ... --vendor ...`. `payload_meta` is updated with vendor
  and batch counters, and duplicate files are skipped unless a new idempotency key is supplied.

## Legacy pipelines

- Archived ingestors (`docs/legacy_samples/etl/keepa_ingestor.py`, `docs/legacy_samples/etl/fba_fee_ingestor.py`,
  `docs/legacy_samples/etl/sp_fees.py`, etc.) are retained as references only and are no longer importable from
  `services.etl.*`. Avoid wiring them into Celery or API codepaths; use `services.fees_h10` for Helium10 fees.

## Adding a Connector (Checklist)

1. Decide on a stable `source` name and include it in alerts/metrics.
2. Fetch data with `awa_common.http_client.HTTPClient` / `AsyncHTTPClient`; avoid raw `httpx` calls.
3. Build deterministic idempotency keys and metadata with `compute_idempotency_key` /
   `build_payload_meta`.
4. Wrap database writes in `process_once` and emit `record_etl_run`, `record_etl_batch`, and
   `record_etl_retry` as appropriate (the helpers feed `etl_runs_total`, `etl_processed_records_total`,
   and `etl_retry_total` respectively).
5. Extend tests (see `tests/unit/packages/awa_common/etl/test_guard_logic.py`,
   `tests/integration/etl/test_load_log_migration.py`) to cover idempotency and schema expectations.
6. Document the connector schedule and operational notes in this file or a dedicated runbook.

## Operational Guide

- Inspect recent runs:
  ```sql
  SELECT source, status, processed_by, duration_ms, error_message, updated_at
  FROM load_log
  ORDER BY updated_at DESC
  LIMIT 20;
  ```
- Dashboard metrics: `task_runs_total{status="error"}` for failures, `etl_duration_seconds` for long
  runs, `etl_processed_records_total` for throughput, and `etl_retry_total{reason=...}` for flaky
  upstreams. Correlate with structured logs (`etl_http_retry`, `source="..."`).
- When alerts fire:
  1. Confirm the failing source in Prometheus or Grafana.
  2. Query `load_log` for stuck `pending` entries and inspect `error_message`.
  3. Check the agent logs (Celery worker or dedicated container) for stack traces.
  4. If a migration is involved, refer to `docs/runbooks/restore.md`; for secrets (API keys, etc.)
     follow `docs/runbooks/secrets.md`.
- Capture a diagnostic bundle with `scripts/ci/make_debug_bundle.sh` when escalations are needed; the
  archive includes docker logs and environment context for post-mortems.

Using the shared guard, HTTP client, and metrics ensures ETL behaviour is predictable and observable in
all environments.

## ROI / Returns Materialized Views

- Returns imports now rely on the shared ingest path (`etl.load_csv` with `returns_report`); the retired
  `services/returns_etl` helper lives only as a reference in `docs/legacy_samples/returns_loader.md`.
- The stats APIs (`/stats/*` and `/score`) query the ROI view configured via `ROI_VIEW_NAME`. Point it
  at `mat_v_roi_full` in production so requests hit the materialized view refreshed by the
  `db.refresh_roi_mvs` Celery task (defined in `services/worker/maintenance.py`). The task runs after
  every bulk ROI import and during nightly maintenance, keeping `mat_v_roi_full` and
  `mat_fees_expanded` current.
- Returns aggregations default to the live table, but you can switch them to a lightweight view such
  as `mat_returns_agg` by setting `RETURNS_STATS_VIEW_NAME`. The async routes will prefer that view
  while preserving parameterised filters.
- The optional monthly partitioning scaffold for `returns_raw` ships disabled; enable
  `RETURNS_PARTITION_SCAFFOLD=1` during a maintenance window and follow
  `docs/runbooks/returns_partitioning.md` for the copy/attach/rename workflow.
- ROI view selection is resolved and cached centrally in `awa_common.roi_views.current_roi_view`
  using `ROI_VIEW_NAME` (or `settings.roi.view_name`). Allowed values are
  `v_roi_full` (default), `roi_view`, `mat_v_roi_full`, and `test_roi_view`; other names raise
  `InvalidROIViewError` so misconfiguration is obvious during startup.
- The “does `returns_raw` have a `vendor` column?” check lives in `services.api.roi_views` and is
  cached per `schema.table` key. Override `ROI_CACHE_TTL_SECONDS` to refresh the discovery more
  frequently—for example during migrations that add the column.
- `/stats/returns` enforces a bounded date range via `STATS_MAX_DAYS` (default 365). When
  `REQUIRE_CLAMP=false` the API clamps `date_from` to stay within the window; when set to `true` it
  returns HTTP 422 so callers must adjust the request client-side.
- Redis read-through caching relies on the shared cache backend configured through
  `CACHE_REDIS_URL` (defaults to `REDIS_URL`) and `CACHE_NAMESPACE`. Enable stats caching with
  `STATS_ENABLE_CACHE=true`; those keys live under `STATS_CACHE_NAMESPACE` (default `stats:`), expire
  after `STATS_CACHE_TTL_S` seconds, and are automatically invalidated after the MV refresh task
  completes.
