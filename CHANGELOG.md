# Changelog

## Unreleased
- fix(ci): pipeline passes with updated env defaults
- drop and recreate refund views to prevent InvalidTableDefinition errors
- add migration regression test and coverage gate
- integrate vulture and extended ruff config
- enable Dependabot updates and docs publishing
- Docker healthchecks for services

## v1.0.7
- coverage gates satisfied for all CI jobs

## v1.0.8
- all coverage gates satisfied across integration-db and service jobs

## v1.0.6
- CI fully green (formatting and coverage gate)

## v0.3
- First release with fully passing CI

## v0.4.0
- Add logistics ETL service and `freight_rates` table
- ROI view now subtracts freight cost
