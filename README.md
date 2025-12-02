# AWA App
[![CI](https://github.com/your-org/AWA-App/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/AWA-App/actions/workflows/ci.yml)
[![coverage](https://codecov.io/gh/your-org/AWA-App/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/AWA-App)

The AWA App monorepo powers wholesale automation: ETL agents ingest marketplace data, FastAPI and worker services expose it, and operational runbooks keep the stack healthy across local, staging, and production deployments. This repository contains everything needed to bootstrap the platform locally, contribute code, and ship new agents.

## Quick start
1. **Prerequisites** — Docker + Docker Compose plugin, GNU Make, Python 3.12, Node.js 20, and `npm`.
2. **Environment**  
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt -c constraints.txt
   pre-commit install
   cp .env.example .env.local
   cp .env.postgres.example .env.postgres
   # Optional: copy .env.sample when bootstrapping the alert/notification stack
   # and append its knobs to your .env.local (it documents Telegram + alert bot toggles).
   ```
3. **Run the core stack**  
   ```bash
   make up              # wraps: docker compose up -d --wait db redis api worker
   alembic -c services/api/alembic.ini upgrade head
   ```
4. **Developer checks**
   ```bash
   make qa              # lint + type check + unit tests
   pytest -q            # run the default suite (see docs/TESTING.md for markers)
   ```
5. **Webapp (optional)**  
   ```bash
   cd webapp && npm install && npm run dev
   ```

## Configuration
- `packages/awa_common/settings.py` is the single source of truth for service configuration. Import `from awa_common.settings import settings` (or instantiate `Settings()` when a fresh read is required) instead of calling `os.getenv` inside services.
- Shared parsing helpers live in `awa_common.utils.env`. Use `env_int`, `env_float`, or `env_bool` when a module must read a raw environment variable (for example inside CLI glue code) so that bounds and defaults stay consistent.
- Database DSNs must come from `awa_common.dsn.build_dsn`. Ad-hoc DSN builders under `services/**` were removed in favour of the shared helper to keep aliases such as `PG_ASYNC_DSN` and `DATABASE_URL` aligned.
- New knobs such as `HTTP_MAX_CONNECTIONS`, `LOGISTICS_TIMEOUT_S`, `FREIGHT_API_URL`, and `ALERT_DB_POOL_MAX_SIZE` are documented in `.env.example`. Copy the sample file when bootstrapping a new environment and add overrides there instead of sprinkling new env lookups through the codebase.

## Documentation
- [Architecture Blueprint](docs/blueprint.md) — system map, deployment targets, and workflow for rolling out changes.
- [Agents](docs/agents.md) — fleet overview, lifecycle, and log-driven debugging contract.
- [Testing](docs/TESTING.md) — unit vs. integration responsibilities, commands, and coverage policy.
- [Dry-run Spec](docs/dry_run.md) — shared safety contract for restore checks, logistics ETL, price importer, and repricer service.
- [Local HTTPS](docs/local_https.md) — mkcert workflow plus proxy wiring for trusted dev certs.
- [CI Debug](docs/CI_debug.md) — mirror log recipe, artifact locations, and triage checklist.

The docs site is built with MkDocs Material (`mkdocs serve` for local preview, `mkdocs build` in CI). Start at [docs/index.md](docs/index.md) for a curated list of topics, or browse the new sections above directly from GitHub.

After merging docs changes that touch the deployment workflow, go to **Settings -> Pages -> Build and deployment -> Source** and select **GitHub Actions** so the Pages environment follows the new pipeline (GitHub only needs this confirmation once per repo).
