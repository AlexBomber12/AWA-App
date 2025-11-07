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

## Documentation
- [Architecture Blueprint](docs/blueprint.md) — system map, deployment targets, and workflow for rolling out changes.
- [Agents](docs/agents.md) — fleet overview, lifecycle, and log-driven debugging contract.
- [Testing](docs/TESTING.md) — unit vs. integration responsibilities, commands, and coverage policy.
- [Dry-run Spec](docs/dry_run.md) — shared safety contract for restore checks, logistics ETL, price importer, and repricer service.
- [Local HTTPS](docs/local_https.md) — mkcert workflow plus proxy wiring for trusted dev certs.
- [CI Debug](docs/CI_debug.md) — mirror log recipe, artifact locations, and triage checklist.

The docs site is built with MkDocs Material (`mkdocs serve` for local preview, `mkdocs build` in CI). Start at [docs/index.md](docs/index.md) for a curated list of topics, or browse the new sections above directly from GitHub.
