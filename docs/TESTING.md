# Testing

The monorepo splits tests into three execution groups so contributors can move quickly without skipping safety checks. All suites use `pytest` with strict markers, and CI mirrors the commands documented below.

## Test groups
### Unit
- **Scope:** Pure Python logic, FastAPI routes with mocked dependencies, and helpers that do not require Docker services.
- **Command:** `pytest -q -m "not integration and not live"`
- **Expectations:** Deterministic, hermetic, no external I/O (network, SMTP, or databases). Use the fixtures from `tests/conftest.py` (`faker_seed`, `env_overrides`, `http_mock`, `smtp_mock`, `now_utc`, etc.) to stub side effects.
- **CI:** Runs in the `unit` job (`make qa` delegates to the same subset) and collects coverage.

### Integration
- **Scope:** Modules that need Postgres, Redis, or docker-compose orchestration (e.g., price importer CLI, Alembic migrations, API-to-DB flows).
- **Command:** `docker compose up -d --wait db redis api worker` followed by `pytest -q -m integration`
- **Expectations:** Real services backed by the compose stack, but still idempotent. Tests may seed fixture data through SQLAlchemy or the exposed APIs. Use the `tests/integration/**` layout to group service-specific suites (e.g., `tests/integration/price_importer/`).
- **CI:** Runs in the `integration` workflow after the stack is built. Coverage is *not* collected here; only the unit job contributes to the coverage gate.

### Live
- **Scope:** Rare tests that hit real third-party APIs or production-like tunnels. They are skipped by default and run only on demand by operators.
- **Command:** `pytest -q -m live --runlive` once the necessary credentials are exported.
- **Expectations:** Document the required environment variables inline. Never enable this marker in automated CI.

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
   pytest -q -m "not integration and not live"
   ```
3. **Integration slice**
   ```bash
   docker compose up -d --wait db redis api worker
   pytest -q -m integration
   ```
4. **Selective targets** — run any path directly (`pytest -q tests/unit/services/price_importer/test_parser.py`) when iterating on a single module.

## Coverage policy
- Coverage thresholds live in `pytest.ini`/`coverage.xml` and are enforced by the unit job only.
- Integration tests skip coverage to keep the run fast and reduce noise from transient infrastructure.
- Generate a local report with `pytest -q --cov --cov-report=term-missing` when you need detailed file-by-file deltas.

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
