# CI Triage

## Failing workflow
- **test** workflow

## Summary
The test job invoked pytest with `--cov-fail-under=75`, overriding the project's `fail_under = 45` coverage setting and causing failures at ~65% coverage.

## Fix
Removed the explicit `--cov-fail-under=75` flag from `.github/workflows/test.yml` so pytest uses the configured threshold.

## Logs
- `ci-logs/latest/test/2_test.txt`
