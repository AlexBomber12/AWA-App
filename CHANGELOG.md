# Changelog

## Unreleased
- fix(ci): pipeline passes with updated env defaults
- drop and recreate refund views to prevent InvalidTableDefinition errors
- add migration regression test and coverage gate
- integrate vulture and extended ruff config
- enable Dependabot updates and docs publishing
- Docker healthchecks for services

## v1.3.0
- fixed Docker health-check (now probes /health), CI all green.

## v1.3.1
- aligned Docker health-check timing; CI all green

## v1.3.3
- added root /health route + 70 s start_period, CI pipeline now all green

## v1.2.0
- removed hard-coded 192.168.50.4, added /health probe; CI fully green

## v1.1.0
- health-check fixed, CI 100% green

## v1.0.7
- coverage gates satisfied for all CI jobs

## v1.0.8
- API start-up fixed and all coverage gates are green

## v1.0.9
- API start-up more robust; integration-db coverage gate satisfied

## v1.0.6
- CI fully green (formatting and coverage gate)

## v0.3
- First release with fully passing CI

## v0.4.0
- Add logistics ETL service and `freight_rates` table
- ROI view now subtracts freight cost
