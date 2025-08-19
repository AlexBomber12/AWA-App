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
