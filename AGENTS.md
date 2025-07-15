# Overview
The agents layer automates scheduled data collection and operational tasks across the AWA platform. Each agent runs as a containerized service with environment variables that configure API access and database credentials.

## Table of Agents
| Agent | Container / Schedule | Triggers | Outputs |
| ----- | -------------------- | -------- | ------- |
| keepa_ingestor | etl container / daily cron | new keepa data | MinIO CSV file, Postgres log |
| fba_fee_ingestor | etl container / daily cron | new Helium10 fees | Postgres `fees_raw` table |
| sp_fees_ingestor | etl container / hourly cron | Amazon SP API data | Postgres `fees_raw` table |
| sku_scoring_engine | scoring container / nightly cron | updated SKU list | Postgres `scores` table |
| repricer_service | repricer container / 15 min cron | pricing signals | `repricer_log` entries |
| restock_planner | planner container / weekly cron | inventory changes | restock plan CSV |

## Agent Descriptions
### keepa_ingestor
Fetches product metrics from the Keepa API. Results are written to a CSV object in MinIO and a brief summary is logged to Postgres. The agent requires `KEEPA_KEY`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` and `DATABASE_URL`.

### fba_fee_ingestor
Downloads FBA fee data from Helium10. It reads `HELIUM_API_KEY` and `DATABASE_URL` to populate the `fees_raw` table. When run with `ENABLE_LIVE=1` it queries the live API, otherwise it loads fixture data for tests.

### sp_fees_ingestor
Retrieves fee estimates from Amazon’s Selling Partner API for a list of SKUs. Required variables are `SP_REFRESH_TOKEN`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `REGION` and `DATABASE_URL`.

### sku_scoring_engine
Processes SKU information each night and updates the `scores` table with performance indicators used by other services.

### repricer_service
Exposes a small FastAPI service that computes optimal prices. It is invoked every 15 minutes by a cron job and stores results in `repricer_log`.

### restock_planner
Generates a weekly CSV file containing recommended restock quantities. This agent monitors inventory levels and sales velocity to plan replenishment.

## Lifecycle
Agents are first added to the local docker-compose environment for development. Once verified they move to the STAGING stack where a cron schedule triggers them automatically. After tests pass in CI, the agent configuration is deployed to production.

## How to add a new agent
1. Create a prompt and initial implementation in a new module under `services/`.
2. Open a Codex PR describing the purpose of the agent.
3. Add tests covering the expected behaviour and ensure `pre-commit` and `pytest` succeed.
4. Update CI and docker-compose files so the agent runs in each environment.
