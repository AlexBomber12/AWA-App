# Testing

## Fast feedback loop
- Run `pytest -q` from the repo root for the default unit-test slice (`-m "not integration and not live"` is applied in `pytest.ini`).
- Unit tests must remain deterministic: seed random generators, keep fixtures tiny, and avoid shared state across tests.
- Never hit real network, SMTP, or databases in the unit suite—these belong in the integration slice.

## Shared fixtures & helpers
The root `tests/conftest.py` provides lightweight building blocks for pure unit tests:
- `faker_seed()` seeds `random`, `numpy.random`, and `faker` (when installed) with a deterministic default. Call it with a different seed if a test needs new data.
- `env_overrides(**env)` is a context manager that temporarily sets/clears environment variables while automatically restoring the previous state.
- `dummy_user_ctx(roles=[...])` returns a ready-to-use `UserCtx` for API tests. Combine it with `fastapi_dep_overrides` to stub authentication.
- `fastapi_dep_overrides(app, current_user=...)` patches `app.dependency_overrides` inside a `with` block and restores the original wiring afterwards.
- `http_mock()` queues canned HTTP responses using `httpx.MockTransport`. Register expectations with `mock.add("GET", "https://...", status_code=200, json={...})` and use `with mock.use(): ...` around code that instantiates `httpx` clients.
- `smtp_mock()` captures calls to `smtplib.SMTP`/`SMTP_SSL` and yields an in-memory list of sent messages so tests can assert email payloads without opening sockets.
- `now_utc(target="module.time_fn", value="2024-01-01T00:00:00Z")` patches a time provider to return a fixed UTC timestamp—no `freezegun` required.
- `tmp_path_helpers` creates scratch directories/files outside the repo tree and can copy fixtures with `helpers.copy_fixture("fees_h10/sample.csv")`.

All helpers rely solely on the standard library and `httpx`, so no additional test dependencies are required.

## Layout & naming
- Unit tests live under `tests/unit/<service>/test_*.py`. Use descriptive module names and keep fixtures local to the service unless they belong in the shared `conftest.py`.
- Integration tests continue to live alongside the existing suites; opt into them with `pytest -m integration`.

## Fixture data
- Deterministic CSV/JSON fixtures live under `tests/fixtures/`. Recent additions include:
  - `fees_h10/sample.csv`
  - `price_importer/sample.csv`
  - `email/body_template.txt`
  - `logistics_etl/sample.json`
  - `logistics_etl/rates_sample.csv`
  - `etl/returns_sample.csv`
- Copy these into temp space with `tmp_path_helpers.copy_fixture(...)` rather than writing into the repository.
- When adding new fixtures, prefer a handful of rows with clearly labeled invalid cases so they remain readable in reviews.

## Service-focused unit slices
- Targeted coverage suites live under `tests/unit/services/<service>/`. For example:
  - `pytest -q tests/unit/services/alert_bot`
  - `pytest -q tests/unit/services/emailer`
  - `pytest -q tests/unit/services/fees_h10`
  - `pytest -q tests/unit/services/price_importer`
- Core coverage additions:
  - `pytest -q tests/unit/services/api/test_security_oidc.py` exercises JWKS discovery/caching and token validation paths.
  - `pytest -q tests/unit/services/api/test_rate_limit_roles.py` ensures per-route rate limit dependencies stay wired.
  - `pytest -q tests/unit/services/db/test_views_utils.py` validates the Alembic view helpers, quoting behaviour, and that `replace_view` issues drop/create statements atomically.
  - `pytest -q tests/unit/services/etl/test_idempotency_retry.py` covers CSV ingestion idempotency (including `force=True` overrides) and the ETL healthcheck retry helper.
  - `pytest -q tests/unit/services/logistics_etl/test_http_and_parse.py` mocks the logistics HTTP downloader, retry/backoff branches, CSV parsing, and `fetch_rates` post-processing.
  - `pytest -q tests/unit/packages/awa_common/test_settings_metrics.py` verifies settings precedence, structured logging context, and the API metrics middleware.
- Use the shared helpers from `tests/conftest.py` (`smtp_mock`, `http_mock`, `env_overrides`, `now_utc`) to isolate SMTP/HTTP/DB/time behaviour without hitting real services.
- Unit fakes (see `tests/utils/strict_spy.py` and `tests/fakes/rate_limiter.py`) validate audit/rate-limit payloads—bad data raises immediately rather than being masked.
- Declare `pytest_plugins` only in the root `tests/conftest.py`; pytest no longer supports defining them in nested `conftest.py` files.

## Integration & live suites
- `pytest -m integration` runs the Postgres-backed tests (ensure `TESTING=1` and supporting services are available).
- `pytest -m live` is reserved for explicit, real external calls; keep it opt-in.
- GitHub Actions applies Alembic migrations inside the integration job before running tests, then captures `alembic-current.txt` and `integration.log` as artifacts. Local runs should mimic this order (`alembic -c services/api/alembic.ini upgrade head`) before invoking integration tests.

## Unit vs integration layers
- `pytest -m unit` runs hermetic tests with strict fakes—no Postgres, Redis, or real sleeps/timeouts.
- `pytest -m integration` expects real Postgres + Redis and validates audit persistence plus rate-limit enforcement (mirroring CI’s short limiter window).
- Keep all `pytest_plugins` declarations centralised in `tests/conftest.py` so pytest loads plugins deterministically.

## Coverage
- Coverage settings live in `.github/coverage.ini` (`source = packages, services`). CI already passes `--cov-config` so local and remote runs stay aligned.
- Generate a local report with `pytest -q --cov --cov-report=term-missing` if you need to inspect coverage deltas.
- When editing GitHub workflows, run `pre-commit run --all-files` or `make ci-validate` to catch actionlint/yamllint issues before pushing.
