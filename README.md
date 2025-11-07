# AWA App
[![CI](https://github.com/your-org/AWA-App/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/AWA-App/actions/workflows/ci.yml)
[![coverage](https://codecov.io/gh/your-org/AWA-App/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/AWA-App)
[![docker](https://img.shields.io/badge/docker-build-blue)](https://hub.docker.com/r/your-org/awa-app)
[![docs](https://img.shields.io/badge/docs-latest-blue)](https://your-org.github.io/AWA-App/)

## Documentation index
- [docs/README.md](docs/README.md) – curated index
- [ADR 0001 — Monorepo Single Source of Truth](docs/ADR/0001-monorepo-SoT.md)
- [Security guide](docs/SECURITY.md)
- [Observability guide](docs/OBSERVABILITY.md)
- [ETL playbook](docs/ETL.md)
- [Frontend guide](docs/FRONTEND.md)

## Getting Started
1. **Prerequisites:** Docker + Docker Compose plugin, GNU Make, Python 3.12, Node.js 20, and `npm`.
2. **Python environment:**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt -c constraints.txt
   pre-commit install
   ```
3. **Environment files:** copy the tracked templates and edit as needed.
   ```bash
   cp .env.example .env.local
   cp .env.postgres.example .env.postgres  # optional: used by docker-compose.dev.yml and workflows
   ```
4. **Start core services** (Postgres, Redis, API, worker):
   ```bash
   docker compose up -d --build --wait db redis api worker
   # or: make up
   ```
5. **Apply migrations:** `alembic -c services/api/alembic.ini upgrade head`
6. **Run quality checks:** `make qa` (wraps lint, mypy, unit tests) or `pytest -q -m "not integration"`
7. **Smoke test:** `curl -f http://localhost:8000/ready`
8. **Webapp (optional):**
   ```bash
   cd webapp
   npm install
   npm run dev
   ```
   Ensure `webapp/.env.local` contains `NEXTAUTH_SECRET`, Keycloak client credentials, and
   `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## API documentation
The generated API reference lives at <https://your-org.github.io/AWA-App/>.
Regenerate it locally with Python 3.12+ and `pydoc-markdown`:

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

Runtime settings are centralised in `packages/awa_common/settings.py`. For a clean local stack:

```bash
cp .env.example .env.local
cp .env.postgres.example .env.postgres  # optional; used by docker-compose.dev.yml
docker compose up -d --build --wait db redis api worker
alembic -c services/api/alembic.ini upgrade head
curl -f http://localhost:8000/ready
```

`docker-compose.yml` wires the API and worker to Postgres (`db`) and Redis (`redis`) using the values
from `.env.local`. `.env.postgres` provides overrides for the auxiliary compose files.

### Default credentials

The compose files provide fallback values for MinIO and IMAP credentials so the stack starts without
extra configuration. Update `.env.local` (and `.env.postgres` when using the dev override file) if you
need different accounts.

### Database config – env matrix

`build_dsn(sync=True|False)` reads `PG_SYNC_DSN`, `PG_ASYNC_DSN` or
`DATABASE_URL` directly. CI exports both a synchronous URL and an
async-friendly variant:

```
PG_SYNC_DSN=postgresql+psycopg://postgres:pass@postgres:5432/awa  # pragma: allowlist secret
PG_ASYNC_DSN=postgresql+asyncpg://postgres:pass@postgres:5432/awa  # pragma: allowlist secret
DATABASE_URL=$PG_ASYNC_DSN  # pragma: allowlist secret
```
Services and tests read these values automatically.

The `.env.example` file also defines `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`,
`PG_HOST` and `PG_PORT`. These mirror the `POSTGRES_*` variables and are
exported by `docker-compose.yml` so a valid DSN can be constructed even when
`PG_SYNC_DSN` or `PG_ASYNC_DSN` are not provided. Containers address each
other by service name (`postgres:5432`, `redis:6379`, `minio:9000`,
`api:8000`) rather than `localhost`.

### Running tests

Start the stack and wait for services to become healthy before running tests:

```bash
docker compose up -d --build --wait db redis api worker
make qa              # lint + mypy + unit tests
# or run subsets:
pytest -q -m "not integration"
pytest -q -m integration         # requires Postgres/Redis running
```

#### Migration currency guard

Run `pytest -q tests/alembic/test_migration_current.py` before pushing schema
changes. The test provisions a throwaway Postgres database, runs `alembic
upgrade head`, captures `alembic history --verbose`, and autogenerates a
temporary revision. If Alembic detects any pending operations the test fails,
indicating that a new migration must accompany the code changes. The temporary
revision file is deleted automatically.

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
Changes under `.codex/**` are ignored by CI to avoid noisy runs.

### Database commands

Common migration tasks are available via the Makefile:

```bash
make db-upgrade    # apply migrations
make db-downgrade  # roll back to base
make db-reset      # rebuild schema from scratch
```

CI and local development connect to Postgres at `postgres:5432` using a
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

### Refund views
`v_refunds_txn` combines rows from `returns_raw` and `reimbursements_raw` into a
single refund model. The companion `v_refunds_summary` view aggregates those
refund amounts by ASIN and day for simplified analysis.

### Dependency pinning
All Python pins live in the root `./constraints.txt`. Every service `requirements.txt`
starts with a relative `-c ../../constraints.txt` include so that running

```bash
pip install -r services/api/requirements.txt
```

from the repository root will resolve the exact versions recorded in the
constraints file. If you are installing from a different working directory,
pass the constraint path explicitly:

```bash
pip install -r services/api/requirements.txt -c constraints.txt
```

The `scripts/ci/check_constraints.py` guard runs in CI and will fail if new
`constraints*.txt` files appear or if `services/**/requirements.txt` reintroduce
version pins. Run `./scripts/pin_constraints.sh` whenever you intentionally
change dependencies to regenerate `constraints.txt`.

### Health checks
Each container exposes a simple probe:

- `api` – HTTP `GET /health`.
- `etl` – connects to Postgres and optionally `MINIO_ENDPOINT`.
- `celery_worker` – connects to Redis and Postgres and pings active workers.
- `celery_beat` – connects to Redis and Postgres and ensures a beat schedule is loaded.

Start the stack and inspect status:

```bash
docker compose up -d --wait
docker compose ps
```

All services should show `healthy`. The checks can be run directly:

```bash
docker compose exec etl python -m services.etl.healthcheck
docker compose exec celery_worker python -m services.ingest.healthcheck worker
docker compose exec celery_beat python -m services.ingest.healthcheck beat
```

## Local QA checklist

* Run `make qa` and review `./.local-artifacts/` for lint, type, and test logs.
* Start the stack with `make up` (or `docker compose up -d --build --wait db redis api worker`) and
  verify `curl -f http://localhost:8000/ready`.
