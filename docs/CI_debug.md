# CI Debug

CI publishes the exact logs you need to triage failures without kicking off extra runs. Use this recipe whenever a lint, unit, integration, frontend, or e2e step goes red.

## Workflow layout
- **lint** — pre-commit + ruff/mypy/yamllint/actionlint. Repro: `python -m pip install -U pip wheel` then `python -m pip install -c constraints.txt -r requirements-dev.txt -e packages/awa_common` and `pre-commit run --all-files`, `mypy --install-types --non-interactive .`.
- **tests-backend** — python unit slice via `./scripts/ci/run_unit.sh` with diff-cover and per-package coverage gates enforced by `scripts/ci/check_coverage_thresholds.py`.
- **decide_integration_needed** — runs `scripts/ci/should_run_integration.sh` to determine if DB/ETL changes require the heavy jobs.
- **integration** — Postgres+Redis+MinIO services plus `pytest -q -m integration tests/integration`. Runs only when `run_integration=true` or forced via label/dispatch input.
- **api-e2e-smoke** — dockerised API readiness probe hitting `/ready` after integration succeeds.
- **tests-frontend** — Node 20 job running `npm ci`, `npm run lint`, `npm run test:coverage`, `npm run storybook:build`, `npm run build`, and `npm run lighthouse` (best-effort). Repro locally from `webapp/`: `npm ci && npm run lint && npm run test:coverage && npm run storybook:build && npm run build && npm run lighthouse`.
- **e2e-ui** — Playwright flow that logs in via `/test-login`, walks Dashboard → ROI → SKU detail → Ingest → Returns → Inbox, and captures traces/screenshots on failure (`webapp/test-results`, `webapp/playwright-report`). Repro: `npm run test:e2e` from `webapp/` (uses local dev server unless `PLAYWRIGHT_BASE_URL` is set).
- **secret-scan** — gitleaks on PRs.
- **mirror-logs** — pulls log + coverage artifacts from every job (unit, integration, api-e2e, frontend, ui-e2e, secret-scan) and posts the PR summary. Artifacts from `logs-*` and coverage bundles are mirrored into the `ci-logs` branch.

## When full integration runs
- `decide_integration_needed` still drives the heavy jobs by diffing against the default branch for DB/ETL-sensitive paths (migrations, FastAPI routes/security/schemas, `packages/awa_common/{metrics,logging,security,dsn,settings}`, `*.sql`, `docker-compose*.yml`, `alembic.ini`).
- If it prints `run_integration=true`, CI executes the integration suite and the `api-e2e-smoke` docker readiness check.
- Force the suite for UI-only changes via `workflow_dispatch` (`force_full_integration=true`) or the `run-integration` PR label.

## Where logs live
| Source | Path | Notes |
| ------ | ---- | ----- |
| Mirror branch | `mirror-logs/<scope>/latest/...` in the `ci-logs` branch | Updated on every run targeting `main` or a PR. Directories mirror the workflow layout (`tests-backend/unit.log`, `integration/integration.log`, `tests-frontend/storybook.log`, `e2e-ui/e2e-ui.log`, etc.). |
| Artifacts | `debug-bundle-<stage>-<run_id>-<attempt>.tar.gz` | Uploaded per job. Contains sanitized environment info, compose logs, Alembic summaries, and every `*.log` file streamed via `tee`. |
| Job summary | GitHub Actions run page | Shows the command that failed and links to the artifact + mirror tree. |
| Mirrorlogs bundle | `mirrorlogs` artifact with `mirrorlogs-<job>.tar.zst` | Emitted on unit/integration/api-e2e failures via `scripts/ci/mirrorlogs_bundle.sh`; includes junit XML, coverage, diff-cover output, `.pytest_cache` snippets, docker logs, and system info (`pip freeze`, `uname -a`, `git rev-parse`). Playwright traces/snapshots live under `webapp/test-results` + `webapp/playwright-report` (uploaded as `logs-e2e-ui`). |

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
     gh run download <run-id> -n debug-bundle-tests-backend-<run-id>-<attempt>
     tar -xf debug-bundle-tests-backend-*.tar.gz
     less tests-backend.log
     ```
   - Mirror logs: `scripts/ci/mirrorlogs_fetch.sh --repo awa-dev/AWA-App --run-id <run-id>` (requires `gh auth login`), or click the `mirrorlogs` artifact in the GitHub UI.
3. **Locate the first hard failure** — search for `Traceback`, `ERROR`, `npm ERR!`, `FAILED tests`, or Playwright errors using `rg -n` or your editor. Capture ~50 lines of context before the failure and up to 200 lines including the failure itself.
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
- **tests-backend:** look for `pytest` exit codes and `FAILED` summaries at the bottom of `artifacts/unit.log`. Coverage and diff-cover reports live in the same bundle. Per-package coverage gates are enforced via `scripts/ci/check_coverage_thresholds.py`.
- **integration:** inspect `artifacts/integration.log` first (includes Alembic + pytest output) and cross-check junit/coverage files from the `integration-test-artifacts` upload.
- **api-e2e-smoke:** focus on `artifacts/e2e/api.log` plus docker logs from the mirrorlogs bundle.
- **tests-frontend:** `artifacts/frontend-tests.log`, `storybook.log`, and `webapp-build.log` capture lint/test/build/Storybook output. Lighthouse is best-effort and logs to `lighthouse.log` when present.
- **e2e-ui:** Playwright traces and screenshots sit under `webapp/test-results` and `webapp/playwright-report`; the console log for the run is `artifacts/e2e-ui.log`.
- **Mirror logs job:** consult `mirror_logs/mirror.log` when log publishing itself fails; permissions or missing scripts typically show up here.

## See also
- [Agents](agents.md)
- [Testing](TESTING.md)
- [docs/ci-triage.md](ci-triage.md)
