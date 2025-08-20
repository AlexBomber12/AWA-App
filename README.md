# AWA App
[![CI](https://github.com/your-org/AWA-App/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/AWA-App/actions/workflows/ci.yml)
[![coverage](https://codecov.io/gh/your-org/AWA-App/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/AWA-App)
[![docker](https://img.shields.io/badge/docker-build-blue)](https://hub.docker.com/r/your-org/awa-app)
[![docs](https://img.shields.io/badge/docs-latest-blue)](https://your-org.github.io/AWA-App/)

## Quick Start
Repricer API → http://localhost:8100/health
The API exposes `/health` for readiness checks.

## API documentation
The generated API reference lives at <https://your-org.github.io/AWA-App/>.
Regenerate it locally with Python 3.11+ and `pydoc-markdown`:

```bash
pip install pydoc-markdown
pydoc-markdown
```

Markdown files are written to `docs/api` and published on pushes to `main`.

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
curl -f http://localhost:8000/health
```

The stack uses Postgres for all services. Copy `.env.example` to `.env.postgres`
and run docker compose to start the database and API containers.

### Default credentials

The docker-compose files provide fallback values for MinIO and IMAP credentials
so the stack starts without extra configuration. Adjust `.env.postgres` if you
need different accounts.

### Database config – env matrix

`build_dsn(sync=True|False)` reads `PG_SYNC_DSN`, `PG_ASYNC_DSN` or
`DATABASE_URL` directly. CI exports both a synchronous URL and an
async-friendly variant:

```
PG_SYNC_DSN=postgresql+psycopg://postgres:pass@localhost:5432/awa  # pragma: allowlist secret
PG_ASYNC_DSN=postgresql+asyncpg://postgres:pass@localhost:5432/awa  # pragma: allowlist secret
DATABASE_URL=$PG_ASYNC_DSN  # pragma: allowlist secret
```
Services and tests read these values automatically.

### Continuous Integration

The GitHub Actions test workflow uses a Postgres service container. It waits
for the database to become healthy, runs Alembic migrations and executes the
tests. No `docker compose` commands are required in CI.
The workflow validates the Dependabot configuration using
`marocchino/validate-dependabot` to avoid broken update PRs.
Pytest enforces a minimum of 45% total coverage.
Docker builds use BuildKit. In CI the stack is built with
`TZ_CACHE_BUST=${GITHUB_SHA}` and started with `--pull never` so tests run
against the freshly-built containers instead of any cached `:latest` image.

### Database commands

Common migration tasks are available via the Makefile:

```bash
make db-upgrade    # apply migrations
make db-downgrade  # roll back to base
make db-reset      # rebuild schema from scratch
```

CI and local development both connect to Postgres at `localhost:5432` using a
synchronous DSN for Alembic and an async variant for the application layer.


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
Set `LLM_PROVIDER` to `lan` (default), `openai`, or `local`.
For `lan` configure `LLM_BASE_URL` and optional `LLM_API_KEY`.
For `openai`, provide `OPENAI_API_KEY` and optionally `OPENAI_MODEL`.

## Manual CSV types

The ingestion CLI auto-detects certain Amazon reports and stores them in
dedicated tables.

| Report type           | Target table        |
| --------------------- | ------------------- |
| `returns_report`      | `returns_raw`       |
| `reimbursements_report` | `reimbursements_raw` |
| `fee_preview_report` | `fee_preview_raw` |
| `inventory_ledger_report` | `inventory_ledger_raw` |
| `ads_sp_cost_daily_report` | `ads_sp_cost_daily_raw` |
| `settlements_txn_report` | `settlements_txn_raw` |

### Dependency pinning
Run `./scripts/pin_constraints.sh` whenever you update service requirements to refresh an optional `constraints.txt` for reproducible installs.

### Health checks
Services with an HTTP API expose `/health` and use `curl -f` in their Dockerfiles. Worker containers without an API use `HEALTHCHECK CMD ["true"]` so Compose marks them as healthy as soon as the process starts.

## Local QA checklist

* Run `make test-cov` and ensure coverage badge shows **≥55 %**.
* Start the stack with `make compose-dev` and verify `curl -f localhost:8000/ready` returns `200`.
