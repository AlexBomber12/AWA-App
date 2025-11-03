# Testing

## Fast feedback loop
- Run `pytest -q` from the repo root for the default unit-test slice (`-m "not integration and not live"` is applied in `pytest.ini`).
- Unit tests must remain deterministic: seed random generators, keep fixtures tiny, and avoid shared state across tests.
- Never hit real network, SMTP, or databases in the unit suite—these belong in the integration slice.

## Shared fixtures & helpers
The root `tests/conftest.py` provides lightweight building blocks for pure unit tests:
- `faker_seed()` seeds `random`, `numpy.random`, and `faker` (when installed) with a deterministic default. Call it with a different seed if a test needs new data.
- `env_overrides(**env)` is a context manager that temporarily sets/clears environment variables while automatically restoring the previous state.
- `dummy_user_ctx(roles=[...])` returns a ready-to-use `Principal` for API tests. Combine it with `fastapi_dep_overrides` to stub authentication.
- `fastapi_dep_overrides(app, get_principal=...)` patches `app.dependency_overrides` inside a `with` block and restores the original wiring afterwards.
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
  - `logistics_etl/sample.json`
- Copy these into temp space with `tmp_path_helpers.copy_fixture(...)` rather than writing into the repository.
- When adding new fixtures, prefer a handful of rows with clearly labeled invalid cases so they remain readable in reviews.

## Integration & live suites
- `pytest -m integration` runs the Postgres-backed tests (ensure `TESTING=1` and supporting services are available).
- `pytest -m live` is reserved for explicit, real external calls; keep it opt-in.

## Coverage
- Coverage settings live in `.github/coverage.ini` (`source = packages, services`). CI already passes `--cov-config` so local and remote runs stay aligned.
- Generate a local report with `pytest -q --cov --cov-report=term-missing` if you need to inspect coverage deltas.
- When editing GitHub workflows, run `pre-commit run --all-files` or `make ci-validate` to catch actionlint/yamllint issues before pushing.
