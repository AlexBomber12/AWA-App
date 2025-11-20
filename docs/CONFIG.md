# Configuration Guide

The AWA monorepo uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to provide type-safe configuration for every service. All configuration lives in `awa_common.settings`; importing `settings` gives access to strongly typed groups that mirror the major concerns in the system.

```python
from awa_common.settings import settings

if settings.app.testing:
    ...
engine = create_engine(settings.db.url)
minio = aioboto3.Session().client("s3", **settings.s3.client_kwargs())
```

Configuration sources are applied in this order:

1. Explicit environment variables (CI, containers, docker-compose)
2. `.env.*` files (loaded automatically based on `ENV`)
3. Hard-coded defaults inside `awa_common.settings`

## Application (`settings.app`)

| Variable | Description |
| --- | --- |
| `ENV`, `APP_ENV` | Deployment stage (`local`, `dev`, `stage`, `prod`) |
| `APP_NAME`, `SERVICE_NAME` | Identifiers for logs and metrics |
| `ALEMBIC_CONFIG` | Path to Alembic configuration file |
| `WAIT_FOR_DB_MAX_ATTEMPTS`, `WAIT_FOR_DB_DELAY_S` | Retry strategy for startup DB checks |

## Database (`settings.db`)

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Primary SQLAlchemy DSN (sync) |
| `PG_ASYNC_DSN` | Optional async-friendly DSN override |
| `ALERT_DB_POOL_*` | Pool sizes and timeouts for the alert-bot asyncpg pool |

Use `settings.db.url` for SQLAlchemy engines and `settings.db.async_dsn` for asyncpg/SQLModel contexts.

## Redis & Celery (`settings.redis`, `settings.celery`)

| Variable | Description |
| --- | --- |
| `REDIS_URL` | Primary Redis (cache + broker) |
| `CACHE_REDIS_URL` | Override for the shared cache backend (defaults to `REDIS_URL`) |
| `CACHE_NAMESPACE`, `CACHE_DEFAULT_TTL_S` | Cache key prefix + default TTL for helpers |
| `BROKER_URL` | Optional Celery broker override |
| `QUEUE_NAMES` | Comma-separated queue list for metrics |
| `CELERY_*` (`CELERY_WORKER_PREFETCH_MULTIPLIER`, `CELERY_TASK_TIME_LIMIT`, `CELERY_TASK_ALWAYS_EAGER`, etc.) | Worker tunables |
| `BACKLOG_PROBE_SECONDS`, `SCHEDULE_*` | Metrics probe interval and scheduler toggles |

`settings.celery` exposes typed helpers (`prefetch_multiplier`, `logistics_cron`, `alerts_schedule_cron`, etc.).

## S3 / MinIO (`settings.s3`)

| Variable | Description |
| --- | --- |
| `MINIO_ENDPOINT`, `MINIO_SECURE` | Host and TLS toggle |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Credentials |
| `MINIO_BUCKET`, `AWS_REGION` | Default bucket name + region |
| `INGEST_*` | Chunk sizes, streaming controls, idempotency |

Call `settings.s3.client_kwargs()` when constructing boto3/aioboto3 clients.

## Security & API (`settings.security`)

| Variable | Description |
| --- | --- |
| `CORS_ORIGINS` | Comma-separated origin list |
| `MAX_REQUEST_BYTES` | Request body limit |
| `OIDC_*` | Keycloak / OIDC validation configuration |
| `RATE_LIMIT_*` | Role-based rate limits |

## Observability (`settings.observability`)

| Variable | Description |
| --- | --- |
| `LOG_LEVEL`, `SENTRY_DSN` | Logging + tracing |
| `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_PROFILES_SAMPLE_RATE` | Sentry sampling |
| `PROMETHEUS_MULTIPROC_DIR`, `ENABLE_METRICS` | Metrics exporters |
| `WORKER_METRICS_HTTP`, `WORKER_METRICS_PORT` | Dedicated worker exporter |

## ROI (`settings.roi`)

| Variable | Description |
| --- | --- |
| `ROI_VIEW_NAME` | View backing ROI listings, stats, and score APIs (allowed: `v_roi_full` default, `roi_view`, `mat_v_roi_full`, `test_roi_view`) |
| `ROI_MATERIALIZED_VIEW_NAME` | Materialized ROI view refreshed by maintenance jobs |

`ROI_VIEW_NAME` (or a nested `settings.roi.view_name` entry) is resolved via `awa_common.roi_views.current_roi_view`. Invalid values raise `InvalidROIViewError` instead of silently falling back so misconfigurations fail fast.

## LLM (`settings.llm`)

| Variable | Description |
| --- | --- |
| `LLM_PROVIDER`, `LLM_PROVIDER_FALLBACK` | Provider chain (`lan`, `local`, `openai`, `stub`) |
| `LLM_URL`, `LLM_BASE_URL`, `LAN_BASE` | Local and LAN inference endpoints |
| `LLM_API_KEY`, `OPENAI_API_KEY`, `OPENAI_MODEL` | Credential material |
| `LLM_REQUEST_TIMEOUT_S`, `LLM_LAN_HEALTH_TIMEOUT_S` | Request + LAN readiness timeouts |

`settings.llm` centralises the provider order and timeouts used by the API and price importer services.

## ETL (`settings.etl`)

| Variable | Description |
| --- | --- |
| `ENABLE_LIVE` | Run ETL in live mode |
| `TASK_ID` | External task identifier for Keepa/Helium ETLs |
| `KEEPA_KEY`, `HELIUM_API_KEY` | Third-party keys |
| `REGION`, `SP_REFRESH_TOKEN`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `SP_FEES_DATE`, `SP_API_BASE_URL` | SP API credentials and base URL |
| `HTTP_*` (`HTTP_CONNECT_TIMEOUT_S`, `HTTP_MAX_CONNECTIONS`, etc.) | Shared HTTP client tuning (legacy `ETL_*` aliases still work) |

## Health checks

| Variable | Description |
| --- | --- |
| `HEALTHCHECK_DB_TIMEOUT_S`, `HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S`, `HEALTHCHECK_HTTP_TIMEOUT_S` | Probe timeouts for DB, Redis, and MinIO |
| `HEALTHCHECK_CELERY_TIMEOUT_S`, `HEALTHCHECK_INSPECT_TIMEOUT_S` | Celery ping and inspect timeouts |
| `HEALTHCHECK_RETRY_ATTEMPTS`, `HEALTHCHECK_RETRY_DELAY_S` | Retry budget for CLI health checks |

## Alerts (`settings.alerts`)

| Variable | Description |
| --- | --- |
| `TELEGRAM_TOKEN`, `TELEGRAM_DEFAULT_CHAT_ID` | Telegram credentials |
| `ALERTS_ENABLED`, `ALERT_RULES_SOURCE`, `ALERTS_EVALUATION_INTERVAL_CRON`, `ALERT_SCHEDULE_CRON` | Rule loading and cadence |
| `ALERT_EVAL_CONCURRENCY`, `ALERT_SEND_CONCURRENCY` | Worker throughput knobs |

## Email (`settings.email`)

| Variable | Description |
| --- | --- |
| `IMAP_HOST`, `IMAP_USER`, `IMAP_PASS` | Marketplace ingestion mailbox credentials |

## Repricer (`settings.repricer`)

| Variable | Description |
| --- | --- |
| `REPRICER_MIN_ROI`, `REPRICER_BUYBOX_GAP`, `REPRICER_ROUND` | Strategy thresholds |

## Sample `.env`

See `.env.sample` for a curated list of supported environment variables grouped by concern. This file is meant for local development (copy to `.env.local` or `.env`).
