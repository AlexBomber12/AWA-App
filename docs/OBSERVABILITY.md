# Observability Guide

The AWA observability stack standardises logging, tracing, and metrics across the API, Celery workers,
and ETL agents. Use this document to understand what data is emitted, how to consume it, and how to
debug incidents.

## Logging

- `packages/awa_common/logging.configure_logging` configures structlog to emit JSON with consistent
  fields. Static context (`service`, `env`, `version`) is injected once; request-scoped context adds
  `request_id`, `trace_id`, and `user_sub`.
- The FastAPI stack installs both `awa_common.logging.RequestIdMiddleware` and
  `services/api.security.RequestContextMiddleware`. Incoming requests without `X-Request-ID` receive a
  generated UUID, which is echoed on the response headers and made available to downstream services.
- Celery workers call `awa_common.logging.bind_celery_task()` from `services/worker/celery_app.py` so
  task logs include `task_id`.
- Example payload (captured in `tests/unit/packages/awa_common/test_logging_json.py`):
  ```json
  {
    "timestamp": "2025-11-06T00:00:00.000000Z",
    "level": "info",
    "event": "sample_event",
    "service": "api",
    "env": "local",
    "version": "0.0.0",
    "request_id": "req-1",
    "trace_id": "trace-xyz",
    "user_sub": "u-123",
    "status": "ok"
  }
  ```
- Logs always include enough context to correlate API calls, Celery retries, and ETL runs—use
  `request_id` to pivot between systems.

## Metrics

### HTTP (API)

- `packages/awa_common/metrics.MetricsMiddleware` records:
  - `http_requests_total{method,path_template,status,service,env,version}`
  - `http_request_duration_seconds_bucket` and the derived histogram quantiles.
- Labels always include `(service, env, version)` as a base.

### Workers & Celery

- `task_runs_total{task_name,outcome,service,env,version}`
- `task_duration_seconds{task_name,service,env,version}`
- `task_failures_total{task_name,exc_type,service,env,version}`
- `queue_backlog{queue,service,env,version}` gauges (requires Redis broker and `QUEUE_NAMES`).
- The worker process enables these by calling `enable_celery_metrics` inside
  `services/worker/celery_app.py`. Set `WORKER_METRICS_HTTP=1` to expose a scrape port.

### ETL

- `etl_runs_total{source,status,service,env,version}`
- `etl_failures_total{source,reason,service,env,version}`
- `etl_duration_seconds{source,service,env,version}` histogram
- `etl_retry_total{source,code,service,env,version}` counter
- Domain-specific ETL modules may also export summaries such as
  `services/logistics_etl/metrics.py::etl_latency_seconds` (Summary over `source`).
- Wrap new pipelines with `awa_common.metrics.record_etl_run/record_etl_skip` and the HTTP client in
  `packages/awa_common/etl/http.py` to populate these metrics automatically.

## Metrics Endpoints

- The API exposes `/metrics` via `packages/awa_common/metrics.register_metrics_endpoint`. Uvicorn
  workers share a Prometheus registry (`PROMETHEUS_MULTIPROC_DIR` is respected when using Gunicorn).
- Celery workers start a sidecar HTTP exporter when `WORKER_METRICS_HTTP=1`; the port defaults to
  `WORKER_METRICS_PORT=9108` and is mapped in `docker-compose.yml`.
- When running locally, `docker compose up -d --build --wait db redis api worker` makes the API
  endpoint available on `http://localhost:8000/metrics` and worker metrics on `http://localhost:9108`.

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
