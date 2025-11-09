# CI Debug

CI publishes the exact logs you need to triage failures without kicking off extra runs. Use this recipe whenever a unit, integration, e2e, or docker-compose step goes red.

## When full integration runs
- `decide_integration_needed` runs `scripts/ci/should_run_integration.sh`, diffs the branch against the default branch, and flags DB/ETL-sensitive paths such as `services/**/migrations/`, `services/api/{routes,schemas,security,main}`, `packages/awa_common/{metrics,logging,security,dsn,settings}`, any `*.sql`, `docker-compose*.yml`, or `alembic.ini` edits.
- If the script prints `run_integration=true`, CI automatically executes the Postgres+Redis+MinIO backed integration suite and then the e2e smoke job.
- You can force the suite even for docs/UI-only changes by either triggering `workflow_dispatch` with `force_full_integration=true` or adding the `run-integration` PR label.
- PRs without matching changes keep the heavy jobs skipped, which shortens wall-clock time without losing the ability to opt-in.

## Where logs live
| Source | Path | Notes |
| ------ | ---- | ----- |
| Mirror branch | `mirror-logs/<scope>/latest/...` in the `ci-logs` branch | Updated on every run targeting `main` or a PR. Each directory mirrors the workflow layout (`unit/unit.log`, `integration/integration.log`, etc.). |
| Artifacts | `debug-bundle-<stage>-<run_id>-<attempt>.tar.gz` | Uploaded per job. Contains sanitized environment info, compose logs, Alembic summaries, and every `*.log` file streamed via `tee`. |
| Job summary | GitHub Actions run page | Shows the command that failed and links to the artifact + mirror tree. |
| Mirrorlogs bundle | `mirrorlogs` artifact with `mirrorlogs-<job>.tar.zst` | Emitted on every unit/integration/e2e failure via `scripts/ci/mirrorlogs_bundle.sh`; includes junit XML, coverage, diff-cover output, `.pytest_cache` snippets, docker logs, and system info (`pip freeze`, `uname -a`, `git rev-parse`). |

## Hands-on triage flow
1. **Fetch mirror logs**
   ```bash
   git fetch origin ci-logs
   git checkout ci-logs
   ls mirror-logs/pr-123/latest/unit
   ```
   Copy the relevant directory into your workspace (never edit files in-place; they are treated as artifacts).
2. **Download bundles if needed**
   - Debug bundle (per job):
     ```bash
     gh run download <run-id> -n debug-bundle-unit-<run-id>-<attempt>
     tar -xf debug-bundle-unit-*.tar.gz
     less unit.log
     ```
   - Mirror logs: `scripts/ci/mirrorlogs_fetch.sh --repo awa-dev/AWA-App --run-id <run-id>` (requires `brew install gh` or `apt install gh` and `gh auth login`), or click the `mirrorlogs` artifact in the GitHub UI.
3. **Locate the first hard failure** — search for `Traceback`, `ERROR`, `npm ERR!`, or `FAILED tests` using `rg -n` or your editor. Capture ~50 lines of context before the failure and up to 200 lines including the failure itself.
4. **Record the metadata**
   - `failure_kind` (e.g., `pytest assertion`, `mypy`, `docker build`).
   - `primary_file` + line number.
   - `failing_command` exactly as logged.
   - `shortest_repro` (usually the pytest target, e2e curl, or npm script).
5. **Reproduce locally**
   - Unit: `./scripts/ci/run_unit.sh` or `pytest -q path/to/test.py -k failing_case`.
   - Integration: `docker compose -f docker-compose.ci.yml up -d --wait db redis` followed by `pytest -q -m integration tests/integration` (no `-k api_audit_rate_limit` filter anymore).
   - E2E smoke: `docker build -t awa-api:e2e . && docker run --rm -p 8000:8000 -e DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/awa awa-api:e2e` followed by repeated `curl -fsS http://localhost:8000/ready`.
6. **Sanitize excerpts** — before copying log snippets into PRs or docs, remove secrets/URLs. The mirror job already redacts known patterns, but double-check manually.
7. **Update docs/ci-triage.md when needed** — add a short note if you discovered a new failure mode or remediation.

## Known flaky areas & quick checklist
- **DB readiness:** Integration/e2e jobs boot Postgres via GitHub services or docker. If `pg_isready` fails, restart locally with `docker compose up -d db` and retry.
- **Alembic upgrade:** `Target database is not up to date` generally means the migration series is stale. Run `alembic -c services/api/alembic.ini upgrade head` before pushing another commit.
- **Redis rate-limit tests:** Failures usually indicate Redis was not healthy yet. Re-run locally with `pytest -q -m integration tests/integration/api/test_rate_limit.py` after ensuring `redis-cli ping` succeeds.
- **E2E readiness:** The smoke job curls `/ready` for ~150 seconds. If it times out, inspect `artifacts/e2e/api.log` or the `mirrorlogs-e2e.tar.zst` bundle to confirm whether the API started, then run `docker run --rm -p 8000:8000 awa-api:e2e` locally.

## Stage-by-stage hints
- **Unit job:** look for `pytest` exit codes and `FAILED` summaries at the bottom of `artifacts/unit.log`. Coverage and diff-cover reports live in the same bundle.
- **Integration job:** inspect `artifacts/integration.log` first (includes Alembic + pytest output) and cross-check junit/coverage files from the `integration-test-artifacts` upload.
- **E2E smoke:** focus on `artifacts/e2e/api.log` plus docker logs from the mirrorlogs bundle.
- **Mirror logs job:** consult `mirror_logs/mirror.log` when log publishing itself fails; permissions or missing scripts typically show up here.

## See also
- [Agents](agents.md)
- [Testing](TESTING.md)
- [docs/ci-triage.md](ci-triage.md)
