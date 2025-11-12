# Agents

The agents layer automates scheduled data collection and operational tasks across the AWA platform. Each agent runs as a containerized service with environment variables that configure API access and database credentials. The table below summarizes the current fleet and their cron cadence.

## Fleet overview
| Agent | Container / Schedule | Triggers | Outputs |
| ----- | -------------------- | -------- | ------- |
| `keepa_ingestor` | etl container / daily cron | new Keepa data | MinIO CSV file, Postgres log |
| `fba_fee_ingestor` | etl container / daily cron | new Helium10 fees | Postgres `fees_raw` table |
| `sp_fees_ingestor` | etl container / hourly cron | Amazon SP API data | Postgres `fees_raw` table |
| `sku_scoring_engine` | scoring container / nightly cron | updated SKU list | Postgres `scores` table |
| `repricer_service` | repricer container / 15 min cron | pricing signals | `repricer_log` entries |
| `restock_planner` | planner container / weekly cron | inventory changes | restock plan CSV |

## Agent descriptions
### keepa_ingestor
Fetches product metrics from the Keepa API. Results are written to a CSV object in MinIO and a brief summary is logged to Postgres. The agent requires `KEEPA_KEY`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and `DATABASE_URL`.

### fba_fee_ingestor
Downloads FBA fee data from Helium10. It reads `HELIUM_API_KEY` and `DATABASE_URL` to populate the `fees_raw` table. When run with `ENABLE_LIVE=1` it queries the live API, otherwise it loads fixture data for tests.

### sp_fees_ingestor
Retrieves fee estimates from Amazon’s Selling Partner API for a list of SKUs. Required variables are `SP_REFRESH_TOKEN`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `REGION`, and `DATABASE_URL`.

### sku_scoring_engine
Processes SKU information each night and updates the `scores` table with performance indicators used by other services.

### repricer_service
Exposes a FastAPI service that computes optimal prices. It is invoked every 15 minutes by a cron job and stores results in `repricer_log`. See the dry-run controls in [docs/dry_run.md](dry_run.md) before toggling write mode.

### restock_planner
Generates a weekly CSV file containing recommended restock quantities. This agent monitors inventory levels and sales velocity to plan replenishment.

## Large report streaming
- `etl.load_csv.import_file` accepts `streaming=True` plus an optional `chunk_size` to stream CSV or XLSX uploads through `copy_df_via_temp`. Leave the flag unset to preserve the legacy in-memory behaviour.
- Use `etl.load_csv.load_large_csv(path, chunk_size=...)` when other workflows need the chunked iterator used by the agents.
- Tune chunk sizing via `INGEST_STREAMING_CHUNK_SIZE` (default `50_000` rows) when deploying agents that process 100 MB+ datasets.
- Run `python tests/performance/streaming_benchmark.py --size-mb 120` to verify peak RSS stays below a few hundred megabytes before enabling streaming mode in production.

## Lifecycle
Agents are first added to the local docker-compose environment for development. Once verified they move to the STAGING stack where a cron schedule triggers them automatically. After tests pass in CI, the agent configuration is deployed to production.

## Adding a new agent
1. Create a prompt and initial implementation in a new module under `services/`.
2. Open a Codex PR describing the purpose of the agent.
3. Add tests covering the expected behavior and ensure `pre-commit` and `pytest` succeed.
4. Update CI and docker-compose files so the agent runs in each environment.

## Alert bot
The alert bot now fans out rule evaluations and Telegram sends in parallel with two layers of throttling (evaluation via `ALERT_EVAL_CONCURRENCY`, delivery via `ALERT_SEND_CONCURRENCY` plus token buckets). A single Celery beat entry (`alertbot.run`) executes on the cadence defined by `ALERT_SCHEDULE_CRON` (defaults to every minute) and the in-process scheduler honours per-rule `schedule` values (cron expressions or `@every 5m` style intervals).

### Rule configuration
- Source file: `services/alert_bot/config.yaml` (override with `ALERT_RULES_PATH`). The document contains `version`, `defaults` (chat list, parse mode, enabled flag), and a `rules[]` list.
- Each rule has `id`, `type` (`roi_drop`, `buybox_loss`, `returns_spike`, `price_outdated`, or `custom` plus legacy aliases), `schedule`, `chat_id` (string or list), `params`, and a Jinja-compatible `template`.
- The parser validates unique IDs, enforces chat targets, and supports runtime toggles through `ALERT_RULES_OVERRIDE=rule1:off,rule2:on`.
- File reloads happen on SIGHUP or at 60s intervals when `ALERT_RULES_WATCH=1`.

### Metrics & observability
- Rule execution: `alertbot_rules_evaluated_total{rule,outcome}`, `alertbot_rule_eval_duration_seconds{rule}`.
- Event and send pipeline: `alertbot_events_emitted_total{rule}`, `alertbot_messages_sent_total{rule,status}`, `alertbot_send_latency_seconds`, `alertbot_batch_duration_seconds`, and `alertbot_inflight_sends`.
- Telegram errors: `alertbot_telegram_errors_total{error_code}`.
- Health: `alertbot_startup_validation_ok` gauges whether token/chat validation passed. When the gauge is `0`, sending is skipped but rule evaluations continue.

### Troubleshooting
- Invalid tokens or chat IDs log `alertbot.validation.failed` entries with the problematic ID; update `TELEGRAM_TOKEN` / `TELEGRAM_DEFAULT_CHAT_ID` and rerun `alertbot.run`.
- Ensure `ALERT_RULES_PATH` points to a readable file; if the bot falls back to legacy rules it logs `alertbot.no_rules`.
- For test environments set `TELEGRAM_API_BASE` to a stub endpoint so CI never calls production Telegram servers.

## Log-driven debugging contract
Agent fixes follow the mirror-log process outlined below.

**Goal** — Use the repository’s mirrored CI logs (the `ci-logs` branch replicates outputs under `mirror-logs/<scope>/latest`, and failing workflows also expose a `ci-logs-<run_id>` artifact) to identify failing errors first, then implement the smallest safe code change to fix them.

**Primary inputs**
1. The mirrored log tree under `mirror-logs/<pr-or-branch>/latest` (fetch the `ci-logs` branch or use a workspace that already contains the mirror). These directories match the layout published by the CI mirror job.
2. When the mirror directory is absent, download the `ci-logs-<run_id>` artifact referenced in the workflow summary and unpack it locally.
3. Treat `.log`, `.txt`, `.out`, `.err`, `.json`, `.xml`, `.junit`, and `.tap` files as logs. Ignore archives because the workflow already unpacks artifacts.

**What to extract from logs**
1. The first hard failure that stops the pipeline. Prefer explicit error markers like `Traceback`, `Exception`, `ERROR`, `FATAL`, `npm ERR!`, `TypeError`, `ReferenceError`, `Cannot find module`, `undefined reference`, `segmentation fault`, `AssertionError`, or pytest/jest/go test/maven/gradle failures.
2. For that failure collect a minimal excerpt: up to 200 lines ending at the failure plus up to 100 lines of preceding context.
3. Paths and line numbers of implicated source files, failing test names, command that failed, exit code.
4. If multiple independent failures exist, handle them one by one in chronological order of appearance in the logs.

**Procedure**
1. Locate logs: inspect `mirror-logs/*/latest` (from the `ci-logs` branch) or the freshly downloaded artifact. If no logs are available anywhere, report that explicitly and stop.
2. Parse logs and write a short triage summary in memory with keys: `failure_kind`, `primary_file`, `line`, `failing_command`, `shortest_repro`, `stack_excerpt`.
3. Open the implicated source file(s) and reason about the smallest change that fixes the root cause without weakening tests.
4. Implement the change. Do not change tests unless the test is objectively incorrect or contradicts the documented behavior.
5. If a deterministic quick check is available from the logs (for example a unit test command), run that command locally when permitted; otherwise include exact commands for maintainers to run.
6. Update any related docs or configuration if the root cause is configuration or missing dependency.
7. Prepare a commit with a clear message and a concise PR body.

**Constraints**
1. Never delete or rewrite logs; do not commit changes under mirrored log folders (`mirror-logs/**`) or extracted artifacts.
2. Keep changes minimal and focused on the identified failure.
3. Preserve code style and lint rules already used in the repo.
4. Do not introduce secrets or modify CI triggers.
5. Do not add `[skip ci]` to fix commits; it is only used by the log-publishing workflow.

**Migration guard**
- Run `pytest -q tests/alembic/test_migration_current.py` before submitting schema or API changes to ensure Alembic has no pending autogeneration output. The helper deletes the throwaway revision automatically; only genuine schema drifts should cause failures.

**Deliverables**
1. A single focused commit or PR that fixes the failure.
2. PR body sections:
   - **Summary** — one paragraph describing the user-visible issue.
   - **Root cause** — one paragraph referencing files/lines.
   - **Fix** — bullet list of code changes.
   - **Repro steps** — exact commands reproduced from logs to validate.
   - **Risk** — potential side effects and why they are acceptable.
   - **Links** — paths to the log files used, for example `mirror-logs/pr-123/latest/unit/unit.log` or the extracted artifact path.
3. Add a triage note file at `docs/ci-triage.md` if the repo uses such docs; otherwise include the triage content in the PR body.

**Success criteria**
1. The specific failing error from the mirrored logs is no longer present in the next CI run.
2. All previously passing tests remain green.
3. The PR body references the exact log filenames and contains a minimal excerpt of the failure.
4. The fix is the smallest reasonable change and adheres to the project’s style.
5. No mirrored log files (`mirror-logs/**`) are modified by the fix.

**Optional heuristics**
1. Prefer the newest timestamped log if multiple versions of the same tool exist.
2. For test suites, extract the first failing test case name and only address that failure initially.
3. For compiler or linter errors, jump to the highest-level message that points to a source file and line; ignore cascading duplicates.

## See also
- [Blueprint](blueprint.md)
- [Testing](TESTING.md)
- [Dry-run](dry_run.md)
- [CI Debug](CI_debug.md)
