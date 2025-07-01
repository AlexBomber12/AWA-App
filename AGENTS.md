# Overview
The agents layer automates data retrieval and operations across the platform.

# Table of Agents
| Agent | Container / Schedule | Triggers | Outputs |
| ----- | -------------------- | -------- | ------- |
| keepa_ingestor | etl container / daily cron | new keepa data | minio csv, postgres log |
| helium_fees_ingestor | etl container / daily cron | new helium fees | postgres table |
| sp_fees_ingestor | etl container / hourly cron | Amazon SP API data | postgres fees_raw |
| sku_scoring_engine | scoring container / nightly cron | updated sku list | postgres scores |
| repricer_service | repricer container / 15 min cron | pricing signals | repricer_log entries |
| restock_planner | planner container / weekly cron | inventory changes | restock plan csv |

# Lifecycle
Agents start in DEV docker-compose, then move to STAGING with scheduled cron jobs and are finally deployed to PROD through CI after tests pass.

# How to add a new agent
- create a new prompt and implementation
- open a Codex PR
- add tests and ensure they pass
- update CI and compose files
