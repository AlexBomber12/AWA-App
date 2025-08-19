# Testing

## Quick start
```bash
pytest
```

By default, only unit tests run (integration and live are excluded to keep CI fast).

## Markers

unit — fast, pure unit tests (default).

integration — require services (Postgres/Redis/S3/etc.). Run with:

```bash
pytest -m integration
```

live — talk to real external services. Run explicitly:

```bash
pytest -m live
```

future — tests that pin the future API/behavior, may be xfail.

slow — long-running / large datasets.

## Coverage

Coverage is enforced at 65% with --cov=services --cov-report=xml.
CI uploads coverage.xml for external tooling.

### Ingest/ETL integration tests
These tests are marked `@pytest.mark.integration` and rely on Postgres.

Run them locally:
```bash
export TESTING=1
pytest -m integration tests/etl
```

The test_generic dialect and test_generic_raw table are for tests only and are enabled when TESTING=1.

### API integration tests for ROI and /score
To run locally:
```bash
export TESTING=1
export API_BASIC_USER=u
export API_BASIC_PASS=p
export ROI_VIEW_NAME=test_roi_view
pytest -m integration services/api/tests
```

The tests create a local test_roi_view table and point queries to it via ROI_VIEW_NAME, leaving production views untouched.

### Fees integrators (Helium10 / SP) — integration tests
These tests use a dedicated table under `FEES_RAW_TABLE` to avoid touching production tables.

Run locally:
```bash
export TESTING=1
export FEES_RAW_TABLE=test_fees_raw
pytest -m integration tests/fees
```

The repository performs two-phase writes (INSERT .. DO NOTHING + UPDATE with IS DISTINCT FROM) so unchanged rows are not updated.
