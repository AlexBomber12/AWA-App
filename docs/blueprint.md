# Architecture Blueprint

The AWA App orchestrates marketplace analytics, pricing, and replenishment flows through a mix of Python services, cron-triggered agents, and a small LLM microservice. This blueprint explains how those parts fit together and what each environment expects.

## System view
```
Amazon APIs / Keepa / Helium10
        │
        ▼
ETL containers (agents) ──► Postgres + MinIO ◄── FastAPI API
        │                         │
        ├──► Metrics & logs ◄─────┘
        │
        └──► Repricer + SKU scoring + Restock planner
                            │
                            ▼
                        Web / worker clients
```

The database (Postgres 16) and object storage (MinIO) act as the single source of truth. Agents ingest raw data, normalize it into staging tables, and publish derived artifacts. The API and worker processes expose that data to downstream services and user interfaces.

## Core modules
- **`services/api`** — FastAPI application that serves HTTP routes, webhooks, and health checks. It depends on Postgres, Redis, and shared settings from `packages/awa_common`.
- **`services/worker`** — Background jobs (Celery and standalone cron helpers) that process queues, notifications, and repricing workflows.
- **`services/price_importer`** — CLI entry point that loads vendor spreadsheets, enforces schema validation, and upserts into `vendor_prices`.
- **`services/logistics_etl`** — Async ingestion job that hydrates freight-rate tables and publishes metrics for alerting.
- **`services/llm_server`** — Lightweight FastAPI wrapper around a llama.cpp binary; used for templating outbound communications when `LLM_PROVIDER=lan`.
- **Agents** — Containerized ETL/scoring/repricing workloads scheduled via cron (see [Agents](agents.md) for cadence and configuration).

## Data & messaging layers
- **Postgres** holds operational tables (`fees_raw`, `vendor_prices`, `scores`, `repricer_log`, etc.). Alembic migrations live under `services/api/migrations`.
- **Redis** powers short-lived queues, cache, and rate-limit tokens consumed by API/worker processes.
- **MinIO** stores large CSV objects (Keepa exports, restock plans, pgBackRest backups).
- **Metrics/Logs** flow to Prometheus and Loki via sidecar exporters. Each agent emits `*_runs_total`, latency histograms, and structured JSON logs to simplify triage.

## Deployment targets
1. **Local compose (`docker-compose.yml`)** — Developer default; run `docker compose up -d --wait db redis api worker`.
2. **Staging** — Mirrors compose topology in a longer-lived cluster. Agents are promoted here first, using temporary schedules and verbose logging.
3. **Production** — Cron-managed schedules and tightened environment variables/secrets. Deployments happen after CI + staging sign-off.

## Change flow
1. Prototype locally, gated by unit + integration tests. Dry-run sensitive commands before enabling writes.
2. Raise a Codex PR, capture CI mirror-log links for any fixes, and document roll-out steps.
3. Once merged, the docker images are rebuilt, migrations apply automatically, and cron entries update via infrastructure-as-code.

## See also
- [Agents](agents.md)
- [Testing](TESTING.md)
- [Dry-run](dry_run.md)
- [LLM microservice](llm_microservice.md)
