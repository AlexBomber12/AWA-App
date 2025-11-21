# ETL Playbook

AWA’s ETL agents share a reliability layer for idempotency, retries, and observability. Use the
components in `packages/awa_common` to deliver repeatable pipelines that survive restarts and replay.

## Idempotency via `load_log`

- The schema defined in `services/api/migrations/versions/0032_etl_reliability.py` creates
  `load_log` with a unique constraint on `(source, idempotency_key)`. Columns:
  - `source` (≤128 chars) – logical agent name (`keepa_ingestor`, `fba_fee_ingestor`, …).
  - `idempotency_key` (64-char BLAKE2 digest) computed in `packages/awa_common/etl/idempotency.py`.
  - `status` in `{pending, success, skipped, failed}`; constants live in
    `packages/awa_common/db/load_log.py`.
  - `payload_meta` JSONB storing fingerprints, sizes, hashes, and optional extras.
  - `processed_by`, `task_id`, `duration_ms`, `error_message`, `created_at`, `updated_at`.
- `compute_idempotency_key` and `build_payload_meta` prefer stable remote metadata (`etag`,
  `last_modified`, `content_length`, `content_md5`), fall back to local file stats, then the raw
  payload (`blake2b` hash). Persisting these values guarantees we can prove what was loaded.
- Duplicate work is detected at insert time; the guard can either skip (`status='skipped'`) or update
  metadata for auditing.

## HTTP Policy

- Always call `packages/awa_common/etl/http.request` or `.download`. Defaults from
  `packages/awa_common/settings.Settings`:
  - Connect timeout 5 s, read timeout 30 s, total budget 60 s.
  - Up to 5 attempts with exponential backoff (0.5 s base, 30 s cap) shared between retries.
  - Retries on httpx transport errors and status codes `{429,500,502,503,504}`. `Retry-After` headers
    are honoured for `429` or any response providing the header.
- Each retry logs `etl_http_retry` with `attempt`, `sleep`, `source`, `task_id`, and increments
  `etl_retry_total{job,reason}` (reason in `{429, timeout, 5xx, exception}`) so operations can see
  churn without exploding cardinality.

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
      source="keepa_ingestor",
      payload_meta=payload_meta,
      idempotency_key=key,
  ) as handle:
      if handle is None:
          record_etl_skip("keepa_ingestor")
          return
      with record_etl_run("keepa_ingestor"):
          # use handle.session for transactional work
          ingest_rows(handle.session, payload_meta)
  ```
- On entry the guard inserts a `pending` row, commits, and returns a `ProcessHandle`. Exiting with no
  exception marks the row `success` and records `duration_ms`; raising an exception rolls back and
  marks `failed` with the truncated message (max 1024 chars).
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
