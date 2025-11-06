# ETL Reliability Layer

The ETL agents now share a common reliability layer that covers HTTP resiliency, idempotent processing, observability, and persistence of execution state. This document summarises the core concepts and the integration points available to new agents.

## Schedules & SLAs

| Agent | Schedule | Freshness expectation |
| ----- | -------- | -------------------- |
| `keepa_ingestor` | Daily | New Keepa snapshot available before 08:00 UTC |
| `fba_fee_ingestor` | Daily | Helium10 fees captured before business hours |
| `sp_fees_ingestor` | Hourly | Latest SP-API fees within 60 minutes |

## HTTP client defaults

All outbound calls should be made through `awa_common.etl.http.request`. The client wraps `httpx` with `tenacity` retries and structured logging.

- Connect timeout: **5s**
- Read timeout: **30s**
- Total request budget: **60s** (combined via `stop_after_delay`)
- Maximum attempts: **5**
- Backoff: exponential with jitter, base **0.5s**, capped at **30s**
- Retryable status codes: **429, 500, 502, 503, 504**
  - `429` honours `Retry-After` headers when provided
  - Network errors (DNS failures, resets, etc.) are retried automatically

Each retry emits a structured log (`etl_http_retry`) with `attempt`, `sleep`, `status_code`, `source`, `task_id`, and `request_id`, and increments the `etl_retry_total{source, code}` metric.

## Idempotency keys

Deterministic idempotency keys are computed via `awa_common.etl.idempotency.compute_idempotency_key` with the following precedence:

1. Stable remote metadata (`etag`, `last_modified`, `content_length`, `content_md5`) – hashed with BLAKE2.
2. Local file metadata (`name`, `size`, `mtime`) – hashed for repeatable offline runs.
3. Raw payload bytes fallback – e.g. hashing an in-memory JSON body.

Use `awa_common.etl.idempotency.build_payload_meta` to assemble a JSON payload that records the artefact the key was derived from (filenames, sizes, ETags, source URLs, etc.). This metadata is persisted alongside every `load_log` row.

## `load_log` table

Alembic revision `0032_etl_reliability` introduces a shared `load_log` table:

| Column | Description |
| ------ | ----------- |
| `id` | BIGSERIAL primary key |
| `source` | Agent identifier (≤128 chars) |
| `idempotency_key` | 64-char deterministic key |
| `status` | `pending`, `success`, `skipped`, `failed` |
| `payload_meta` | JSONB describing the artefact |
| `processed_by` | Service/worker name |
| `task_id` | Upstream task identifier (Celery, etc.) |
| `duration_ms` | Execution time |
| `error_message` | Truncated failure synopsis |
| `created_at` / `updated_at` | Timestamps (`updated_at` auto-populates via trigger) |

A unique index on `(source, idempotency_key)` enforces single processing per artefact. Duplicate attempts either skip immediately or soft-update metadata, depending on the guard configuration.

## Processing guard

Use `awa_common.etl.guard.process_once` to wrap agent work:

```python
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import compute_idempotency_key, build_payload_meta
from awa_common.metrics import record_etl_run, record_etl_skip

payload_meta = build_payload_meta(path=fixture_path, extra={"mode": "offline"})
idempotency_key = compute_idempotency_key(path=fixture_path)

with process_once(
    SessionLocal,
    source="my_agent",
    payload_meta=payload_meta,
    idempotency_key=idempotency_key,
) as handle:
    if handle is None:
        record_etl_skip("my_agent")
        return

    with record_etl_run("my_agent"):
        # Perform idempotent database writes using `handle.session`.
        ...
```

On entry the guard attempts to insert a `pending` row. If the `(source, idempotency_key)` tuple already exists, the guard returns `None`, allowing the caller to log and exit quickly. Within the context manager:

- Success updates the row to `status='success'`, records `duration_ms`, and commits the transaction.
- Exceptions roll back the session, mark the row `failed`, stash the error summary, and re-raise to surface the failure upstream.

## Metrics

New Prometheus series provide visibility into ETL health:

- `etl_runs_total{source, status}` – counts `success`, `failed`, `skipped`.
- `etl_failures_total{source, reason}` – groups failures by exception type.
- `etl_retry_total{source, code}` – increments on every retry attempt (HTTP status or exception class).
- `etl_duration_seconds{source}` – histogram of run durations.

Use `record_etl_run`, `record_etl_skip`, and the shared HTTP client to populate these metrics consistently.

## Extending an ingestor

1. Collect or derive a deterministic idempotency key and payload metadata.
2. Wrap the processing logic in `process_once` to guard against duplicates.
3. Execute writes within a single SQLAlchemy transaction, favouring `INSERT ... ON CONFLICT` or explicit unique constraints to guarantee idempotency at the data store.
4. Emit structured logs with `source`, `task_id`, `service`, and `request_id` for traceability.
5. Update `load_log` status via the guard and ensure metrics are emitted (`record_etl_run` / `record_etl_skip`).

Following this pattern keeps the agents safe to re-run, tolerant of transient API issues, and fully observable.
