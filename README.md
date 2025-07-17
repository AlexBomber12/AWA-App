# AWA App
[![CI](https://github.com/your-org/AWA-App/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/AWA-App/actions/workflows/ci.yml)
[![coverage](https://codecov.io/gh/your-org/AWA-App/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/AWA-App)
[![docker](https://img.shields.io/badge/docker-build-blue)](https://hub.docker.com/r/your-org/awa-app)

## Quick Start
Repricer API → http://localhost:8100/health

## Development setup

### Code style
```bash
pip install pre-commit
pre-commit install
```
Black auto-formats every commit; CI enforces `git diff --exit-code`.

### Database configuration

The ETL and API services read Postgres credentials from environment variables.
Copy `.env.example` to `.env.postgres` and spin up the stack:

```bash
cp .env.example .env.postgres
docker compose up -d --wait
curl http://localhost:8000/health
```

The stack uses Postgres for all services. Copy `.env.example` to `.env.postgres`
and run docker compose to start the database and API containers.

### Database config – env matrix

`build_dsn(sync=True|False)` derives a DSN from `DATABASE_URL` or the `PG_*`
variables.  CI exports both a synchronous URL and an async-friendly variant:

```
DATABASE_URL=postgresql+psycopg://postgres:pass@localhost:5432/awa  # pragma: allowlist secret
PG_ASYNC_DSN=postgresql://postgres:pass@localhost:5432/awa  # pragma: allowlist secret
```
Services and tests read these values automatically.

### Continuous Integration

The GitHub Actions test workflow uses a Postgres service container. It waits
for the database to become healthy, runs Alembic migrations and executes the
tests. No `docker compose` commands are required in CI.


## Importing supplier prices
Use the price importer to load vendor spreadsheets into the database:
```bash
python -m price_importer.import tests/fixtures/sample_prices.csv --vendor "ACME GmbH"
```
This updates `vendor_prices` and recomputes ROI via the `v_roi_full` view.

## Helium10 fee cron
Add your Helium10 API key to `.env.postgres` and run the fee cron container:

```yaml
fees_h10:
  build: services/fees_h10
  command: ["celery", "-A", "services.fees_h10.worker", "beat", "-l", "info"]
  env_file: .env.postgres
  depends_on:
    postgres:
      condition: service_healthy
```

`docker compose up fees_h10` fetches daily FBA fees into `fees_raw`.

## Logistics costs
Daily freight rates populate the `freight_rates` table:

```yaml
logistics_etl:
  build: services/logistics_etl
  env_file: .env.postgres
  command: ["python", "-m", "logistics_etl"]
  depends_on:
    postgres:
      condition: service_healthy
```

Run `docker compose up logistics_etl` to insert rates and update ROI.

## ROI Review demo

Browse high-margin SKUs with basic auth:

```bash
curl -u admin:pass "http://localhost:8000/roi-review?roi_min=15"
```

## LLM provider

The emailer and future services call a configurable language model.
Set `LLM_PROVIDER` to `local` (default) or `openai`. When using
`openai`, provide `OPENAI_API_KEY` and optionally `OPENAI_MODEL`.

## Manual CSV types

The ingestion CLI auto-detects certain Amazon reports and stores them in
dedicated tables.

| Report type           | Target table        |
| --------------------- | ------------------- |
| `returns_report`      | `returns_raw`       |
| `reimbursements_report` | `reimbursements_raw` |
