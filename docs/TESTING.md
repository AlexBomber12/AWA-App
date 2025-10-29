# Testing

## Quick start
```bash
pytest
```

By default only unit tests run (integration and live are excluded to keep CI fast).

## Dependencies

All services share the root `constraints.txt`. Each `services/**/requirements.txt`
includes a `-c ../../constraints.txt` header so installing from the repository root
is reproducible:

```bash
pip install -r services/api/requirements.txt
```

If you prefer to install from another directory, pass the constraint explicitly:

```bash
pip install -r services/api/requirements.txt -c constraints.txt
```

The CI job runs `scripts/ci/check_constraints.py` to ensure no additional
`constraints*.txt` files are introduced and that service requirements remain
unpinned.

Markers

unit — fast, pure unit tests (default).

integration — require services (Postgres/MinIO/etc.). Run explicitly:

pytest -m integration


live — real external calls; always opt-in:

pytest -m live


future — pins future behavior; often xfail.

slow — long-running or large datasets.

Coverage policy

Coverage is measured on the services package and enforced via the configuration in
`pyproject.toml` (default 45%):

pytest -q --cov=services --cov-report=xml


CI publishes coverage.xml for external tooling.

Ingest / ETL integration tests

Require Postgres and TESTING=1.

export TESTING=1
pytest -m integration tests/etl -q


Tests use a test-only dialect test_generic; production data is untouched.

API integration tests (ROI filters and /score)

Point the API to a test ROI view/table via env.

export TESTING=1
export API_BASIC_USER=u
export API_BASIC_PASS=p
export ROI_VIEW_NAME=test_roi_view
pytest -m integration services/api/tests/test_roi_filters.py -q
pytest -m integration services/api/tests/test_score.py -q

/stats in SQL mode

Enable real aggregates with STATS_USE_SQL=1.

export TESTING=1
export STATS_USE_SQL=1
export ROI_VIEW_NAME=test_roi_view
export API_BASIC_USER=u
export API_BASIC_PASS=p
pytest -m integration services/api/tests/test_stats_sql.py -q


With STATS_USE_SQL unset/0, /stats returns the stable placeholder contracts.

Fees integrators (Helium10 / SP)

Write to a dedicated test table via FEES_RAW_TABLE.

export TESTING=1
export FEES_RAW_TABLE=test_fees_raw
pytest -m integration tests/fees -q

Logistics ETL

Generic upsert helper exists only when TESTING=1.

export TESTING=1
pytest -m integration tests/logistics -q

LLM module tests and defaults

Provider is selected at call time via LLM_PROVIDER; default is lan. Useful envs:

LLM_PROVIDER — lan | local | openai | stub (default: lan)

LLM_TIMEOUT_SECS — request timeout (seconds), default 60

LLM_REMOTE_URL — override remote HTTP endpoint in tests

Run:

pytest tests/llm -q
