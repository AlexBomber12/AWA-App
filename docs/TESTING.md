# Testing

The monorepo splits tests into three execution groups so contributors can move quickly without skipping safety checks. All suites use `pytest` with strict markers, and CI mirrors the commands documented below.

## Test groups
CI has three logical test groups plus an e2e smoke check that rides on top of integration readiness.

### Unit
- **Scope:** Pure Python logic, FastAPI routes with mocked dependencies, and helpers that do not require Docker services.
- **Command:** `./scripts/ci/run_unit.sh` (wraps `pytest -q -m "not integration and not live"` with coverage enabled)
- **Speed tips:** Use `NO_COV=1 make unit` to skip coverage in local loops, or `make unit-fast` (auto-disables third-party plugins and falls back when `xdist` is missing) for a minimal pytest run. Pair with `-m "not slow"` to keep the suite snappy.
- **Expectations:** Deterministic, hermetic, no external I/O (network, SMTP, or databases). Use the fixtures from `tests/conftest.py` (`faker_seed`, `env_overrides`, `http_mock`, `smtp_mock`, `now_utc`, etc.) to stub side effects.
- **CI:** Runs in the `unit` job (`make qa` delegates to the same subset) and collects coverage.

### Integration
- **Scope:** Modules that need Postgres, Redis, or docker-compose orchestration (e.g., price importer CLI, Alembic migrations, API-to-DB flows).
- **Command (one-liner):** `docker compose -f docker-compose.ci.yml up -d --wait db redis && pytest -q -m integration tests/integration`
- **Expectations:** Real services backed by the compose stack, but still idempotent. Tests may seed fixture data through SQLAlchemy or the exposed APIs. Use the `tests/integration/**` layout to group service-specific suites (e.g., `tests/integration/price_importer/`).
- **CI:** `decide_integration_needed` runs `scripts/ci/should_run_integration.sh` to diff the current branch against `main`. Any DB/ETL-sensitive changes (migrations, API routes/schemas/security, `packages/awa_common/{metrics,logging,security,dsn,settings}`, `*.sql`, `docker-compose*.yml`, `alembic.ini`, etc.) trigger the full `pytest -q -m integration tests/integration` suite—no more `-k api_audit_rate_limit` filter. You can force the run via the `run-integration` PR label or the `force_full_integration` workflow_dispatch input.
- **Coverage:** We still gate coverage on the unit job, but integration uploads junit + coverage XML so you can diff regressions when needed.

### Live
- **Scope:** Rare tests that hit real third-party APIs or production-like tunnels. They are skipped by default and run only on demand by operators.
- **Command:** `pytest -q -m live --runlive` once the necessary credentials are exported.
- **Expectations:** Document the required environment variables inline. Never enable this marker in automated CI.

### E2E smoke
- **Scope:** Lightweight readiness probe that uses the dockerized API image and curls `/ready` until it succeeds (max ~150 seconds). It validates that dependencies (DB, Alembic, logging) come up cleanly before merging.
- **Command:** The CI job builds the API image with Buildx, runs Postgres + API in docker, and loops on `curl -fsS http://localhost:8000/ready`.
- **CI:** Triggered only when integration ran and passed (either automatically via the diff or by a forced run).

## How to run tests locally
1. **Bootstrap tooling**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt -c constraints.txt
   pre-commit install
   ```
2. **Unit slice (fast feedback)**
   ```bash
   ./scripts/ci/run_unit.sh
   ```
3. **Integration slice**
   ```bash
   docker compose -f docker-compose.ci.yml up -d --wait db redis
   pytest -q -m integration tests/integration
   ```
4. **Selective targets** — run any path directly (`pytest -q tests/unit/services/price_importer/test_parser.py`) when iterating on a single module.

## Coverage policy
- Backend gates run via `scripts/ci/check_coverage_thresholds.py` (api.routes, worker, etl, awa_common.etl) after `./scripts/ci/run_unit.sh` emits `coverage.xml`. Integration tests still upload coverage XML for diffing but do not gate merges.
- Frontend coverage uses path-specific Jest thresholds for dashboard/ROI/SKU/ingest/returns/inbox and `lib/tableState`; run `npm run test:coverage` from `webapp/` to validate locally.
- Generate a local report with `pytest -q --cov --cov-report=term-missing` when you need detailed file-by-file deltas.

## CI stages overview
1. **lint** — Pre-commit, ruff/mypy/actionlint/yamllint; blocks all other jobs.
2. **unit** — Executes `scripts/ci/run_unit.sh`, uploads coverage, and enforces diff-cover ≥80%.
3. **decide_integration_needed** — Runs `scripts/ci/should_run_integration.sh` to decide whether DB/ETL changes require the heavy jobs and exposes `run_integration=true|false` to downstream jobs.
4. **integration** — Spins up Postgres + Redis + MinIO as services, runs `alembic upgrade head`, then `pytest -q -m integration tests/integration` with junit + coverage artifacts. Produces a `mirrorlogs` bundle on failure.
5. **e2e-smoke** — Builds the API image with Buildx cache, launches a temp stack, and curls `/ready` until success. Logs are uploaded and mirrored if the job fails.
6. **webapp-qa** — Node 20 job that installs `webapp/` deps, runs lint + Jest coverage, builds Storybook, executes Playwright e2e + Lighthouse, and finishes with a production `next build`.
7. **secret-scan** — Runs gitleaks when the trigger is a PR.
8. **mirror-logs** — Collects artifacts from every job and posts a PR summary comment, keeping a consistent triage surface even when some jobs were skipped.

## Layout & naming
- Unit tests live under `tests/unit/<service>/test_*.py`; service-specific helpers belong next to their subjects.
- Integration suites live under `tests/integration/<area>/` (for example `tests/integration/price_importer/` now houses the dry-run CLI test).
- Top-level `tests/test_*.py` files cover repo-wide behaviours (CLI entry points, ETL flows, etc.).

## Shared fixtures & helpers
`tests/conftest.py` centralizes utilities for fast tests:
- `faker_seed()` seeds `random`, `numpy.random`, and Faker deterministically.
- `env_overrides(**env)` temporarily overrides environment variables.
- `dummy_user_ctx()` + `fastapi_dep_overrides()` build authenticated FastAPI requests without touching Keycloak.
- `http_mock()` (based on `httpx.MockTransport`) asserts outgoing HTTP calls.
- `smtp_mock()` captures SMTP interactions in memory.
- `now_utc()` freezes monotonic timestamps without external libraries.
- `tmp_path_helpers` copies deterministic fixtures (CSV/JSON) into temporary directories.

## Migration guard
- `pytest -q tests/alembic/test_migration_current.py` provisions a disposable Postgres instance, runs `alembic upgrade head`, autogenerates a throwaway revision, and fails if either `upgrade()` or `downgrade()` contains real operations. Run it whenever you touch models or migrations.

## Live data hygiene
- Never hit production data from unit or integration suites.
- When a test must call a third-party API, add the `@pytest.mark.live` marker, document the secrets it needs, and guard the code with `pytest.skip` unless `--runlive` is provided.

## See also
- [Agents](agents.md)
- [Dry-run](dry_run.md)
- [CI Debug](CI_debug.md)
