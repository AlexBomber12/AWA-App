# Overview
The agents layer orchestrates scheduled and event-driven tasks for data and pricing workflows.

# Table of Agents
| Agent | Container / Schedule | Triggers | Outputs |
|---|---|---|---|
| keepa_ingestor | etl container, nightly | daily cron | ASIN list in object storage and log table |
| helium_fees_ingestor | etl container, weekly | Monday cron | helium fees in database |
| sp_fees_ingestor | etl container, on demand | CLI or API | fees_raw table rows |
| sku_scoring_engine | scoring container, daily | new offers | sku_scores table |
| repricer_service | repricer container hourly | price changes | repricer_log records |
| restock_planner | planner container weekly | inventory signals | restock plan export |

# Lifecycle
Agents run in DEV via docker-compose. Successful jobs move to STAGING with cron. CI then deploys them to PROD.

# How to add a new agent
- create a prompt describing the task
- use Codex to generate code
- write tests and ensure they pass
- open a PR so CI deploys the agent
- add the agent to compose and schedule
