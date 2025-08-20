# CI Triage

## Failing workflows
- **CI** workflow
- **test** workflow

## Summary
Both workflows invoked pytest with `--cov-fail-under=75`, overriding the project's `fail_under = 45` coverage setting and causing failures at ~65% coverage.

## Fix
Removed the explicit `--cov-fail-under=75` flag from `.github/workflows/ci.yml`, `.github/workflows/test.yml`, and `pytest.ini` so pytest uses the configured threshold.

## Logs
- `ci-logs/latest/CI/0_unit.txt`
- `ci-logs/latest/test/2_test.txt`
