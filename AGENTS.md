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

Agent operating mode: log-driven debugging

Goal
Use the repository’s persisted CI logs to identify failing errors first, then implement the smallest safe code change to fix them.

Primary inputs
1) Directory ci-logs/latest containing unzipped logs from the most recent workflow run.
2) If ci-logs/latest is missing, scan ci-logs for the most recently modified subfolder and use that instead.
3) Treat any files with extensions .log, .txt, .out, .err, .json, .xml, .junit, .tap as logs. Ignore archives because the workflow already unpacks artifacts.

What to extract from logs
1) The first hard failure that stops the pipeline. Prefer explicit error markers like Traceback, Exception, ERROR, FATAL, npm ERR!, TypeError, ReferenceError, Cannot find module, undefined reference, segmentation fault, AssertionError, test failures from pytest/jest/go test/maven/gradle.
2) For that failure collect a minimal excerpt: up to 200 lines ending at the failure plus up to 100 lines of preceding context.
3) Paths and line numbers of implicated source files, failing test names, command that failed, exit code.
4) If multiple independent failures exist, handle them one by one in chronological order of appearance in the logs.

Procedure
1) Locate logs: read ci-logs/latest. If empty or missing, report this and stop.
2) Parse logs and write a short triage summary in memory with keys: failure_kind, primary_file, line, failing_command, shortest_repro, stack_excerpt.
3) Open the implicated source file(s) and reason about the smallest change that fixes the root cause without weakening tests.
4) Implement the change. Do not change tests unless the test is objectively incorrect or contradicts the documented behavior.
5) If a deterministic quick check is available from the logs (for example a unit test command), run that command locally when permitted; otherwise, include exact commands for maintainers to run.
6) Update any related docs or configuration if the root cause is configuration or missing dependency.
7) Prepare a commit with a clear message and a concise PR body.

Constraints
1) Never delete or rewrite logs; do not commit changes under ci-logs.
2) Keep changes minimal and focused on the identified failure.
3) Preserve code style and lint rules already used in the repo.
4) Do not introduce secrets or modify CI triggers.
5) Do not add [skip ci] to fix commits; it is only used by the log-publishing workflow.

Deliverables
1) A single focused commit or PR that fixes the failure.
2) PR body sections:
   Summary: one paragraph describing the user-visible issue.
   Root cause: one paragraph referencing files/lines.
   Fix: bullet list of code changes.
   Repro steps: exact commands reproduced from logs to validate.
   Risk: potential side effects and why they are acceptable.
   Links: paths to the log files used, for example ci-logs/latest/build.log.
3) Add a triage note file at docs/ci-triage.md if the repo uses such docs; otherwise include the triage content in the PR body.

Success criteria
1) The specific failing error from ci-logs/latest is no longer present in the next CI run.
2) All previously passing tests remain green.
3) The PR body references the exact log filenames and contains a minimal excerpt of the failure.
4) The fix is the smallest reasonable change and adheres to the project’s style.
5) No files under ci-logs are modified by the fix.

Optional heuristics
1) Prefer the newest timestamped log if multiple versions of the same tool exist.
2) For test suites, extract the first failing test case name and only address that failure initially.
3) For compiler or linter errors, jump to the highest-level message that points to a source file and line; ignore cascading duplicates.

## Cloud-only workflow
- edit in Cursor/Codex, push, open PR.
- Python 3.12 and Node LTS.
- CI runs unit then integration; Docker/Compose runs only in CI.
- integration marker policy: tests needing DB or external services use `@pytest.mark.integration`.
- On failure read the PR failure comment and Run Summary; download artifact `ci-logs-<run_id>` if deeper inspection is needed.
- Never lower coverage thresholds; add tests first.
- Codex reviewers: read the PR failure comment, then propose the minimal patch.

### CI commands
- Unit: `pytest -q -m "not integration"`
- Web: `npm test` (web)
- Webapp: `npm run build` (webapp)
- Integration: docker compose up + `pytest -q -m integration`
