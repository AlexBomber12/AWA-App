# CI Debug

CI publishes the exact logs you need to triage failures without kicking off extra runs. Use this recipe whenever a unit, integration, or docker-compose step goes red.

## Where logs live
| Source | Path | Notes |
| ------ | ---- | ----- |
| Mirror branch | `mirror-logs/<scope>/latest/...` in the `ci-logs` branch | Updated on every run targeting `main` or a PR. Each directory mirrors the workflow layout (`unit/unit.log`, `integration/docker-compose.log`, etc.). |
| Artifacts | `debug-bundle-<stage>-<run_id>-<attempt>.tar.gz` | Uploaded per job. Contains sanitized environment info, compose logs, Alembic summaries, and every `*.log` file streamed via `tee`. |
| Job summary | GitHub Actions run page | Shows the command that failed and links to the artifact + mirror tree. |

## Hands-on triage flow
1. **Fetch mirror logs**
   ```bash
   git fetch origin ci-logs
   git checkout ci-logs
   ls mirror-logs/pr-123/latest/unit
   ```
   Copy the relevant directory into your workspace (never edit files in-place; they are treated as artifacts).
2. **Locate the first hard failure** — search for `Traceback`, `ERROR`, `npm ERR!`, or `FAILED tests` using `rg -n` or your editor. Capture ~50 lines of context before the failure and up to 200 lines including the failure itself.
3. **Record the metadata**
   - `failure_kind` (e.g., `pytest assertion`, `mypy`, `docker build`).
   - `primary_file` + line number.
   - `failing_command` exactly as logged.
   - `shortest_repro` (usually the pytest module or npm script).
4. **Reproduce locally**
   - For unit failures: `pytest -q path/to/test.py -k failing_case`.
   - For integration failures: run `docker compose up -d --wait ...` then the same `pytest -q -m integration` command shown in CI.
   - For docker build issues: reuse the `docker build` command printed inside the log bundle.
5. **Sanitize excerpts** — before copying log snippets into PRs or docs, remove secrets/URLs. The mirror job already redacts known patterns, but double-check manually.
6. **Update docs/ci-triage.md when needed** — add a short note if you discovered a new failure mode or remediation.

## Downloading artifacts directly
If the mirror branch has not updated yet (fork PRs or temporary outages), download the debug bundle:
```bash
gh run download <run-id> -n debug-bundle-unit-<run-id>-<attempt>
tar -xf debug-bundle-unit-*.tar.gz
less unit.log
```

## Stage-by-stage hints
- **Unit job:** look for `pytest` exit codes and `FAILED` summaries at the bottom of `unit/unit.log`.
- **Integration job:** inspect `integration/docker-compose.log` first (services might be unhealthy) before jumping into `integration/pytest.log`.
- **Mirror logs job:** consult `mirror_logs/mirror.log` when log publishing itself fails; permissions or missing scripts typically show up here.

## See also
- [Agents](agents.md)
- [Testing](TESTING.md)
- [docs/ci-triage.md](ci-triage.md)
