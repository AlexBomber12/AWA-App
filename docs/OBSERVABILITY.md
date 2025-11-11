# Observability Guide

The AWA observability stack standardises logging, tracing, and metrics across the API, Celery workers,
and ETL agents. Use this document to understand what data is emitted, how to consume it, and how to
debug incidents.

## Logging

- `packages/awa_common/logging.configure_logging(service, level=None)` applies the structlog JSON
  pipeline and reads `service`, `env`, and `version` directly from `awa_common.settings`. Every log
  record includes the keys `ts`, `level`, `service`, `env`, `version`, `request_id`, `trace_id`,
  `task`, `component`, and `msg`, so downstream processors never have to guess.
- Request-scoped helpers `set_request_context` / `clear_request_context` store correlation IDs via
  contextvars. The FastAPI stack still mounts `RequestIdMiddleware`, which pulls `X-Request-ID`
  (or generates one), binds it to structlog, and echoes the ID plus `X-Trace-ID` on responses.
- Background workers call `bind_celery_task()` during the `task_prerun` signal so task IDs populate
  the `task` field and, when no HTTP request exists, become the default `request_id`.
- Example payload (`tests/unit/observability/test_structlog_context.py`):
  ```json
  {
    "ts": "2025-11-06T00:00:00.000000Z",
    "level": "info",
    "service": "api",
    "env": "local",
    "version": "0.0.0",
    "request_id": "req-1",
    "trace_id": "trace-xyz",
    "task": null,
    "component": "price_importer",
    "msg": "price_import.batch_completed"
  }
  ```
- Use `set_request_context` whenever an async boundary would otherwise drop correlation IDs (custom
  clients, background threads, etc.).

## Database Access

- `packages/awa_common/db/async_session` owns the global `AsyncEngine` and FastAPI dependency `get_async_session()`. Engines are initialised during app lifespan and disposed on shutdown so middlewares (audit, rate-limit) and routers share a single asyncpg pool.
- ROI-facing routes resolve view names exclusively through `packages/awa_common/roi_views.current_roi_view()`, which enforces the whitelist and caches the configured name for 30 seconds to avoid per-request environment lookups.

## Metrics

### HTTP (API)

- `packages/awa_common/metrics.MetricsMiddleware` records:
  - `http_requests_total{method,path_template,status,service,env,version}`
  - `http_request_duration_seconds_bucket` and the derived histogram quantiles.
- Labels always include `(service, env, version)` as a base.

### Workers & Celery

- `task_runs_total{task,status,service,env,version}` counts successes vs. errors.
- `task_duration_seconds_bucket{task,service,env,version}` histograms runtimes.
- `task_errors_total{task,error_type,service,env,version}` captures exception class.
- `queue_backlog{queue,service,env,version}` gauges Redis queue depth when the worker enables
  `enable_celery_metrics`.
- Decorate Celery functions (or cron jobs) with `@metrics.instrument_task("task_name")` to emit
  the counters automatically. Signals registered in `services/worker/celery_app.py` provide a
  drop-in for legacy tasks that have not yet been decorated.

### ETL

- `etl_runs_total{job,service,env,version}` increments every time a pipeline processes an input.
- `etl_processed_records_total{job,service,env,version}` tracks batch throughput.
- `etl_duration_seconds{job,service,env,version}` records both job-level and per-snapshot durations,
  depending on whether you call `record_etl_run` or `record_etl_batch`.
- `etl_retry_total{job,reason,service,env,version}` captures retries, parse failures, and skips
  with a bounded `reason` label (e.g., `429`, `timeout`, `exception`, `skipped`).
- Convenience helpers:
  - `with record_etl_run("job"):` wraps an entire pipeline invocation.
  - `record_etl_batch(job="logistics", processed=rows, errors=failures, duration_s=seconds)` records
    per-file progress.
  - `record_etl_retry(job, reason)` is used by the HTTP clients and ETL modules to tag retries.
- HTTP clients (`packages/awa_common/etl/http.py` and `services/etl/http_client.py`) now report
  their own metrics:
  - `http_client_requests_total{target,method,status_class,service,env,version}`
- `http_client_request_duration_seconds_bucket{target,method,service,env,version}`

### Stats Aggregates

- `stats_cache_hits_total{endpoint,service,env,version}` and `stats_cache_miss_total{...}` measure
  Redis effectiveness for `/stats/kpi`, `/stats/returns`, and `/stats/roi_trend`.
- `stats_query_duration_seconds_bucket{endpoint,service,env,version}` captures the DB runtime for
  the same aggregate queries so you can correlate cache hit-rates with database load.
- Cache operations log `stats_cache_hit`, `stats_cache_miss`, and `stats_cache_store_failed`
  messages that include only the hashed cache key and endpoint. Payloads are intentionally excluded
  so Sentry breadcrumbs never contain PII.

### Metrics Endpoints

- The API exposes `/metrics` via `packages/awa_common/metrics.register_metrics_endpoint`. Uvicorn
  workers share a Prometheus registry (`PROMETHEUS_MULTIPROC_DIR` is respected when using Gunicorn).
- Celery workers start a sidecar HTTP exporter when `WORKER_METRICS_HTTP=1`; the port defaults to
  `WORKER_METRICS_PORT=9108` and is mapped in `docker-compose.yml`.
- Any non-HTTP process (ETL scripts, cron workers, CLI tools) can set
  `METRICS_TEXTFILE_DIR=/var/lib/node_exporter/textfile` and optionally
  `METRICS_FLUSH_INTERVAL_S` to enable the node-exporter textfile collector. Call
  `metrics.flush_textfile("service")` before exit to guarantee a fresh snapshot.
- When running locally, `docker compose up -d --build --wait db redis api worker` makes the API
  endpoint available on `http://localhost:8000/metrics` and worker metrics on `http://localhost:9108`.

## Sentry

- `packages/awa_common/sentry.init_sentry(service)` centralises DSN handling, scrubbers, and default
  integrations (Celery, FastAPI, SQLAlchemy, stdlib logging). The initializer never raises: empty or
  invalid DSNs are logged and the application continues.
- `before_send` / `before_breadcrumb` are shared so both API and workers scrub secrets the same way.
- API, worker, fees worker, and price-importer all call `init_sentry(...)` on startup; the helpers
  guard against double-initialisation.

## SLO & SLI Targets

- Availability ≥ 99.9 % over 30 days (derived from `http_requests_total` 5xx share).
- HTTP latency p95 ≤ 400 ms and p99 ≤ 800 ms (1 min windows over `http_request_duration_seconds`).
- HTTP 5xx rate ≤ 0.5 % of total requests (excluding 401/403).
- Celery task success ≥ 99 % on rolling 24 h (`task_runs_total`).
- ETL hourly lag ≤ 15 minutes; nightly pipelines complete by T+1 07:00 local (`etl_runs_total`,
  domain-specific latency summaries).
- Queue backlog p95 ≤ 30 seconds equivalent; sustained backlog > 100 items triggers intervention.

## Alerting & Debug Bundles

- Suggested Prometheus rules:
  - **WARN** API latency: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.4`
  - **CRIT** API latency: same expression with threshold `0.8`.
  - **WARN** 5xx: `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.005`.
  - **WARN** Celery failures: `1 - (sum(rate(task_runs_total{outcome="success"}[5m])) / sum(rate(task_runs_total[5m]))) > 0.01`.
  - **WARN** ETL retries: `sum(rate(etl_retry_total[5m])) by (source)` spikes indicate upstream instability.
- Capture diagnostics with `scripts/ci/make_debug_bundle.sh <output.tar.gz>`; the script snapshots logs,
  docker status, and environment (with sensitive values redacted).

## Runbooks & Triage

- Primary references:
  - `docs/runbooks/restore.md` — database backup/restore procedures.
  - `docs/runbooks/secrets.md` — secret handling and rotations.
  - `docs/ci-triage.md` — catalog of past CI failures and mitigations.
- Triage flow for failed migrations or ETL:
  1. Inspect `ci-logs/latest/*` (or run `scripts/ci/make_debug_bundle.sh`) to confirm the first failing
     step and capture command output.
  2. For migrations, check `services/api/migrations` and rerun
     `alembic -c services/api/alembic.ini upgrade head` locally; consult `docs/runbooks/restore.md` if
     the database requires recovery.
  3. For ETL, query `load_log` (see `packages/awa_common/db/load_log.py`) for stuck `status='pending'`
     rows, review `etl_runs_total` / `etl_failures_total`, and resubmit work via the relevant Celery
     task or agent.
  4. Document findings in `docs/ci-triage.md` when new failure modes arise so future responders can
     reuse the investigation.

Consistent logging and metric labelling eliminate guesswork; always start with the shared artefacts in
`packages/awa_common/` when instrumenting new code.
