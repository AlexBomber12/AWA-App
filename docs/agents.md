# Agents

The agents layer automates scheduled data collection and operational tasks across the AWA platform. Each agent runs as a containerized service with environment variables that configure API access and database credentials. The table below summarizes the current fleet and their cron cadence.

## Fleet overview
| Agent | Container / Schedule | Triggers | Outputs |
| ----- | -------------------- | -------- | ------- |
| `fees_h10` | fees_h10 worker / daily Celery beat (`fees.refresh`) | active ASIN list from DB | Postgres `fees_raw` table |
| `sku_scoring_engine` | scoring container / nightly cron | updated SKU list | Postgres `scores` table |
| `repricer_service` | repricer container / 15 min cron | pricing signals | `repricer_log` entries |
| `restock_planner` | planner container / weekly cron | inventory changes | restock plan CSV |

## Agent descriptions
### fees_h10
Refreshes Helium10 FBA fee data for active ASINs using the shared async HTTP client. The Celery beat
task `fees.refresh` reads `HELIUM10_KEY` (or `etl.helium10_key`), honours `HELIUM10_BASE_URL`,
`HELIUM10_TIMEOUT_S`, and `HELIUM10_MAX_RETRIES`, and upserts rows into `fees_raw`. Concurrency is
limited by `H10_MAX_CONCURRENCY`.

### sku_scoring_engine
Processes SKU information each night and updates the `scores` table with performance indicators used by other services.

### repricer_service
Exposes a FastAPI service that computes optimal prices. It is invoked every 15 minutes by a cron job and stores results in `repricer_log`. See the dry-run controls in [docs/dry_run.md](dry_run.md) before toggling write mode.

### restock_planner
Generates a weekly CSV file containing recommended restock quantities. This agent monitors inventory levels and sales velocity to plan replenishment.

### Legacy ETL samples
The retired ingestors (`keepa_ingestor`, `fba_fee_ingestor`, `sp_fees_ingestor`) are archived under
`docs/legacy_samples/etl/` and described in `docs/legacy_samples/ETL_LEGACY_NOTES.md`; they are no
longer part of the supported fleet.

## Large report streaming
- `etl.load_csv.import_file` accepts `streaming=True` plus an optional `chunk_size` to stream CSV or XLSX uploads through `copy_df_via_temp`. Leave the flag unset to preserve the legacy in-memory behaviour.
- Use `etl.load_csv.load_large_csv(path, chunk_size=...)` when other workflows need the chunked iterator used by the agents.
- Tune chunk sizing via `INGEST_STREAMING_CHUNK_SIZE` (default `50_000` rows) when deploying agents that process 100 MB+ datasets, or set `INGEST_STREAMING_CHUNK_SIZE_MB` alongside `INGEST_STREAMING_THRESHOLD_MB` to opt into the new size-aware streaming defaults without changing the code paths.
- Run `python tests/performance/streaming_benchmark.py --size-mb 120` to verify peak RSS stays below a few hundred megabytes before enabling streaming mode in production.

## Lifecycle
Agents are first added to the local docker-compose environment for development. Once verified they move to the STAGING stack where a cron schedule triggers them automatically. After tests pass in CI, the agent configuration is deployed to production.

## Adding a new agent
1. Create a prompt and initial implementation in a new module under `services/`.
2. Open a Codex PR describing the purpose of the agent.
3. Add tests covering the expected behavior and ensure `pre-commit` and `pytest` succeed.
4. Update CI and docker-compose files so the agent runs in each environment.

## Alert bot
The alert bot now fans out rule evaluations and Telegram sends in parallel with two layers of throttling (evaluation via `ALERT_EVAL_CONCURRENCY`, delivery via `ALERT_SEND_CONCURRENCY` plus token buckets). A single Celery beat entry (`alertbot.run`) executes on the cadence defined by the validated cron settings (`ALERTS_EVALUATION_INTERVAL_CRON` / `ALERT_SCHEDULE_CRON`), while each rule’s `schedule` string is validated through the shared cron helpers and simply filters rules that are not due on a given tick. All outbound Telegram calls run through the shared HTTP client so retries, timeouts, structured logs, and metrics match the rest of the platform.

### Required settings
- `TELEGRAM_TOKEN` and `TELEGRAM_DEFAULT_CHAT_ID` are loaded via `AlertBotSettings`. Tokens that are empty, placeholders, or malformed trigger `alertbot.validation.failed`, flip `alertbot_startup_validation_ok` back to `0`, and increment `alert_errors_total{type="config_error"}` so misconfiguration can’t hide silently.
- `ALERTS_ENABLED`, `ALERT_EVAL_CONCURRENCY`, `ALERT_SEND_CONCURRENCY`, and `ALERT_RULE_TIMEOUT_S` also live in `AlertBotSettings`, making env files / Helm values the single source of truth for feature flags and concurrency knobs.
- Per-rule schedules and the global cadence share the same cron validation logic from `awa_common.cron_config`, keeping CI/production parity.

### Rule configuration
- Source file: `services/alert_bot/config.yaml` (override with `ALERT_RULES_PATH`). The document contains `version`, `defaults` (chat list, parse mode, enabled flag), and a `rules[]` list.
- Each rule has `id`, `type` (`roi_drop`, `buybox_loss`, `returns_spike`, `price_outdated`, or `custom` plus legacy aliases), `schedule`, `chat_id` (string or list), `params`, and a Jinja-compatible `template`.
- The parser validates unique IDs, enforces chat targets, and supports runtime toggles through `ALERT_RULES_OVERRIDE=rule1:off,rule2:on`.
- File reloads happen on SIGHUP or at 60s intervals when `ALERT_RULES_WATCH=1`.

### Metrics & observability
- Rule execution: `alertbot_rules_evaluated_total{rule,outcome}`, `alertbot_rule_eval_duration_seconds{rule}`.
- Event and send pipeline: `alertbot_events_emitted_total{rule}`, `alertbot_messages_sent_total{rule,status}`, `alertbot_send_latency_seconds`, `alertbot_batch_duration_seconds`, and `alertbot_inflight_sends`.
- Transport: `alerts_sent_total{rule,severity,channel,status}` shows whether Telegram sends succeed, `alert_rule_skipped_total{rule,reason}` highlights disabled/filtered/invalid-config rules, and `alert_errors_total{rule,type}` captures HTTP/API/config errors emitted by the new transport layer.
- Health: `alertbot_startup_validation_ok` gauges whether token/chat validation passed. When the gauge is `0`, sending is skipped but rule evaluations continue and the counters above will show skipped sends.

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
