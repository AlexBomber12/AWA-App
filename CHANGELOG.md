# Changelog

## Unreleased
- fix(ci): pipeline passes with updated env defaults
- drop and recreate refund views to prevent InvalidTableDefinition errors
- add migration regression test and coverage gate
- integrate vulture and extended ruff config
- enable Dependabot updates and docs publishing
- Docker healthchecks for services

## v0.3
- First release with fully passing CI

## v0.4.0
- Add logistics ETL service and `freight_rates` table
- ROI view now subtracts freight cost
