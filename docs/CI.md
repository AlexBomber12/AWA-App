# Continuous Integration

The `CI` workflow keeps feedback fast by splitting validation into focused jobs:

- **lint** — repository-wide `pre-commit`, `ruff`, `mypy`, yamllint, and actionlint.
- **tests-backend** — `./scripts/ci/run_unit.sh` with diff-cover and per-package coverage gates (`scripts/ci/check_coverage_thresholds.py`).
- **decide_integration_needed** — determines whether DB/ETL-sensitive changes require the heavy integration suite.
- **integration** — Postgres+Redis+MinIO services plus `pytest -q -m integration tests/integration` when `run_integration=true`.
- **api-e2e-smoke** — dockerised API image built with Buildx and probed via `/ready` (runs only after a successful integration job).
- **tests-frontend** — Node 20 job running `npm ci`, `npm run lint`, `npm run test:coverage`, `npm run storybook:build`, `npm run build`, and a best-effort `npm run lighthouse`.
- **e2e-ui** — Playwright journey (test login → Dashboard → ROI → SKU → Ingest → Returns → Inbox) with traces/screenshots on failure.
- **secret-scan** — gitleaks on PRs.
- **mirror-logs** — aggregates `logs-*` and coverage artifacts from every job and mirrors them into the `ci-logs` branch for triage.

All jobs inherit BuildKit defaults (`DOCKER_BUILDKIT=1`, `COMPOSE_DOCKER_CLI_BUILD=1`) and use `actions/setup-python@v5` with pip caching keyed on `constraints.txt` plus each service's `requirements*.txt`. Caching keeps dependency installs fast while still respecting the global constraints lockfile. Frontend jobs use `actions/setup-node@v6` with npm caching keyed on `webapp/package-lock.json` and cache Playwright browsers via `~/.cache/ms-playwright`.

Python jobs (lint/tests-backend/integration/api-e2e) emit `debug-bundle-<job>.tar.gz` artifacts capturing:

- `python --version` and `pip freeze` for the executed environment
- Docker state (`docker ps`, `docker compose ps/logs`) when available
- Alembic state via `alembic current -v` and recent history
- HTTP dumps of `http://localhost:8000/ready` and `/metrics` when reachable
- Collected CI log files from the workspace

Download the bundle from the workflow run page, extract it locally, and inspect the captured commands (each file includes the executed command and exit code). This consistent artifact makes reproducing failures offline straightforward, even when a job fails before emitting normal logs.

## Docs deployment

MkDocs builds now run in `.github/workflows/docs.yml` with a strict build, Pages artifact upload, and a gated deploy job that only runs on `main` pushes and manual dispatches. After merging updates to this workflow, open the repository **Settings -> Pages -> Build and deployment** panel and set **Source** to **GitHub Actions** so GitHub Pages is allowed to serve the published artifact (GitHub only requires the toggle once per repository).
