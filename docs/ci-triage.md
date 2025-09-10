# CI Triage

## Failing workflows

---

- **CI** workflow (unit job)

## Summary
`alembic upgrade head` failed with `sqlalchemy.exc.OperationalError: (psycopg.OperationalError) [Errno -3] Temporary failure in name resolution` in the unit job. The Alembic env uses `services.common.dsn.build_dsn(sync=True)`, which preferred `PG_SYNC_DSN`. In CI, that DSN points at the Docker hostname `postgres`, while the services run outside Docker with `PG_HOST=localhost`, so the hostname could not be resolved.

## Fix
- Update `services/common/dsn.py` to honor `PG_HOST` as an override for any provided DSN (PG_SYNC_DSN/PG_ASYNC_DSN/DATABASE_URL) by replacing the DSN hostname with `PG_HOST` when they differ. This yields a localhost DSN during CI while remaining a no-op when already inside Docker.

## Logs
- `ci-logs/main/latest/00001047_ci/unit/10_Run migrations.txt`
- **CI** workflow (compose-health job)
- **test** workflow (health-checks job)

## Summary
Docker compose health checks failed because the Redis service exited immediately. The startup command attempted to run `sysctl -w vm.overcommit_memory=1`, which is not permitted in the execution environment, so `redis-server` never started and downstream services reported the container as unhealthy.

## Fix
- Updated `docker-compose.yml` to ignore failures from the `sysctl` command so the Redis server starts even when kernel parameters cannot be modified.

## Logs
- `ci-logs/latest/CI/compose-health/6_Run export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1.txt`
- `ci-logs/latest/test/health-checks/5_Run export COMPOSE_DOCKER_CLI_BUILD=1.txt`

---

## Failing workflows
- **test** workflow (health-checks job)

## Summary
`docker compose` reported `container awa-app-etl-1 is unhealthy`. The ETL image lacked the
`services.common` package and used an invalid `timeout` parameter in the healthcheck,
causing the script to crash.

## Fix
- Include the `services` package in the ETL image and set `PYTHONPATH`.
- Use `connect_timeout` when opening the database connection in `healthcheck.py`.

## Logs
- `ci-logs/latest/test/2_health-checks.txt`

---

## Failing workflows
- **test** workflow (health-checks job)

## Summary
`docker compose` reported `container awa-app-celery_worker-1 is unhealthy` because the ETL entrypoint always executed `keepa_ingestor.py`, ignoring the Celery command so the worker never started.

## Fix
- Allow `services/etl/entrypoint.sh` to execute the provided command after waiting for PostgreSQL, falling back to `keepa_ingestor.py` when none is supplied.

## Logs
- `ci-logs/latest/test/0_health-checks.txt`
- `ci-logs/latest/test/health-checks/5_Run export COMPOSE_DOCKER_CLI_BUILD=1.txt`

---

## Failing workflows
- **CI** workflow (compose-health job)

## Summary
The API container failed its health check because it was configured to reach PostgreSQL at `localhost`, which is inaccessible from within the container network.

## Fix
- Use the `postgres` service hostname for `DATABASE_URL` and `PG_HOST` in the compose-health job.

## Logs
- `ci-logs/latest/CI/3_compose-health.txt`

---

## Failing workflows
- **CI** workflow (compose-health job)

## Summary
`docker compose` reported `container awa-app-celery_worker-1 is unhealthy`. The
`services.ingest.healthcheck` module referenced `os` and `argparse` without
importing them, causing the health check process to exit before Celery could
report ready.

## Fix
- Import `os` and `argparse` in `services/ingest/healthcheck.py`.

## Logs
- `ci-logs/latest/CI/3_compose-health.txt`
---

## Failing workflows
- **CI** workflow (install-deps job)

## Summary
`pip install` failed because `constraints.txt` pinned versions that conflicted with `requirements-dev.txt` (`httpx==0.26.0`, `pandas==2.3.1`, `ruff==0.4.4`, `testcontainers==4.10.0`).

## Fix
- Update the pinned versions in `constraints.txt` to align with development requirements.

## Logs
- `ci-logs/latest/CI/install-deps.txt`

---

## Failing workflows
- **CI** workflow (compose-health job)
- **test** workflow (health-checks job)

## Summary
`docker compose` reported `container awa-app-celery_worker-1 is unhealthy` and `container awa-app-etl-1 is unhealthy`. The healthcheck scripts built a DSN that still pointed to `localhost`, preventing services from reaching the PostgreSQL container.

## Fix
- Expose `PG_HOST` and `PG_PORT` to services in `docker-compose.yml` so the DSN resolves to the `postgres` service.

## Logs
- `ci-logs/latest/CI/3_compose-health.txt`
- `ci-logs/latest/test/2_health-checks.txt`
---

## Failing workflows
- **CI** workflow (unit job)
- **test** workflow (test job)

## Summary
`alembic upgrade head` failed because two migrations shared the same parent revision, producing multiple heads (`0026_amazon_new_reports` and `0026_fix_refund_views`).

## Fix
- Add a merge migration `0027_merge_reports_and_refund_heads` to unify the heads.

## Logs
- `ci-logs/latest/CI/unit/10_Run migrations.txt`
- `ci-logs/latest/test/test/13_Run Alembic migrations.txt`
---

## Failing workflows
- **CI** workflow (migrations-check job)

## Summary
`alembic heads` failed with `ModuleNotFoundError: No module named 'services'` while loading migration `0023_add_storage_fee.py`. The revision imported project utilities without ensuring the repository root was on `sys.path`.

## Fix
- Append the repository root to `sys.path` in migrations before importing project modules.

## Logs
- `ci-logs/latest/CI/1_migrations-check.txt`
---
## Failing workflows
- **CI** workflow (unit job)

## Summary
`ruff check` reported an unsorted import block in `services/api/main.py`, causing the lint step to fail.

## Fix
- Consolidated the LLM imports into a single ordered line in `_check_llm`.

## Logs
- `ci-logs/latest/CI/unit/7_Check code formatting.txt`
---
## Failing workflows
- **test** workflow (health-checks job)

## Summary
`docker compose` reported `container awa-app-api-1 exited (1)` because the API image
lacked the shared database utilities and the `imapclient` package required by the
email watcher, preventing migrations from running during startup.

## Fix
- Copy `services/db` into the API image.
- Declare `imapclient` in API requirements and constraints.

## Logs
- `ci-logs/latest/test/1_health-checks.txt`
---
## Failing workflows
- **CI** workflow (unit job)

## Summary
`ruff format --check` reported misformatted code in `services/api/main.py`.

## Fix
- Reformat `services/api/main.py` with `ruff format`.

## Logs
- `ci-logs/latest/CI/0_unit.txt`

```text
Would reformat: services/api/main.py
1 file would be reformatted, 258 files already formatted
```

---

## Failing workflows
- **CI** workflow (compose-health job)

## Summary
`docker compose` reported `container awa-app-celery_worker-1 is unhealthy`. The
healthcheck scripts now retry failed probes, which can take longer than the
5 s timeout, causing Docker to mark the service unhealthy before the checks finish.

## Fix
- Widen healthcheck `timeout` to 25 s for ETL, Celery worker, and Celery beat so
  internal retries can complete.

## Logs
- `ci-logs/latest/CI/3_compose-health.txt`

---

## Failing workflows
- **logs-after-ci** workflow (gather-and-commit job)

## Summary
GitHub Actions reported `Invalid workflow file` because line 22 in `.github/workflows/logs-after-ci.yml` was outside the multi-line `if` block, leaving an orphaned `&&` expression.

## Fix
- Move the explanatory comment above the `if` block so the entire condition remains within the YAML scalar.

## Logs
- No log file was generated; the workflow failed before execution.

---

## Failing workflows
- **collect-logs** workflow (collect job)

## Summary
Python script in the "Download and unpack logs" step raised
`IndentationError: expected an indented block after function definition` on
line 9, preventing the job from fetching workflow logs.

## Fix
- Indent the helper functions and loop in the script so Python executes
  without syntax errors.

## Logs
- No log file was generated; the workflow failed before execution.

---

## Failing workflows
- **collect-logs** workflow (collect job)

## Summary
Python script in the "Wait for all workflows to finish for this SHA" step raised
`IndentationError: expected an indented block after function definition` on line
9, stopping the job before log collection could begin.

## Fix
- Indent the body of the `api` function and subsequent loop so the script runs
  without syntax errors.

## Logs
- No log file was generated; the workflow failed before execution.

---

## Failing workflows
- **collect-logs** workflow (collect job)

## Summary
The "Resolve targets" step invoked the deprecated `set-output` command,
which now errors out and stops the job before collecting logs.

## Fix
- Write the resolved target list to `$GITHUB_OUTPUT` instead of using the
  deprecated command.

## Logs
- No log file was generated; the workflow failed before execution.

## Failing workflows
- **collect-logs** workflow (collect job)

## Summary
The "Commit and push" step failed with `failed to push some refs` because the
remote branch contained new commits, making the push non-fast-forward.

## Fix
- Rebase onto the latest `$HEAD_BRANCH` before pushing to ensure the commit
  fast-forwards even when the branch moves.

## Logs
- No log file was generated; the workflow failed before execution.

---

## Failing workflows
- **collect-logs** workflow (collect job)

## Summary
The workflow referenced `inputs.sha` in the concurrency group and job environment.
On push events, the `inputs` context is unavailable, producing `Invalid workflow file`
errors before execution.

## Fix
- Use `github.event.inputs.sha` with a fallback to `github.sha` for the concurrency
  group and `HEAD_SHA` environment variable.

## Logs
- No log file was generated; the workflow failed before execution.

---

## Failing workflows
- **CI** workflow (compose-logs job)

## Summary
Starting the ETL container crashed with `ModuleNotFoundError: No module named 'sqlalchemy'` from `services/common/base.py`.

## Fix
- Add `sqlalchemy` to `services/etl/requirements.txt` so the ETL image includes SQLAlchemy.

## Logs
- `ci-logs/latest/CI/compose-logs.txt`

---

## Failing workflows
- **CI** workflow (unit job)

## Summary
`npm run build` in the webapp failed with `Error: <Html> should not be imported outside of pages/_document.` because the build ran with `NODE_ENV=development`, triggering Next.js development-only checks.

## Fix
- Force `NODE_ENV=production` for the webapp build step in `.github/workflows/ci.yml`.

## Logs
- `ci-logs/latest/CI/webapp-build.log`

---

## Failing workflows
- **CI** workflow (compose-logs job)

## Summary
`keepa_ingestor.py` crashed with `FileNotFoundError: [Errno 2] No such file or directory: 'tests/fixtures/keepa_sample.json'` when the ETL container started without the test fixtures present.

## Fix
- Copy `tests/fixtures/keepa_sample.json` into the ETL image so the default ingest command finds the sample data.

## Logs
- `ci-logs/latest/CI/compose-logs.txt`

---

## Failing workflows
- **CI** workflow (unit job)

## Summary
`tests/test_docker_build.py::test_api_image_builds` attempted to build a Docker image during the unit job, which stalled without a Docker daemon.

## Fix
- Marked `tests/test_docker_build.py` as integration-only so Docker image builds run only where Docker is available.

## Logs
- `ci-logs/latest/CI/unit/unit-pytest.log`

---

## Failing workflows
- **CI** workflow (compose-up job)

## Summary
The ETL container exited during `docker compose up` because `keepa_ingestor.py` could not import `pg_utils`.

## Fix
- Export `PYTHONPATH` in `services/etl/entrypoint.sh` so bundled modules like `pg_utils` are discoverable.

## Logs
- `.codex/last-run/compose-logs.txt`
