# CI Triage

## Failing workflows
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
