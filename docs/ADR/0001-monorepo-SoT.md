# ADR 0001 — Monorepo Single Source of Truth

- Status: Accepted
- Date: 2025-11-06

## Context

The early AWA stacks accumulated duplicate configuration: multiple `alembic.ini` files, hand-copied
`env.py` helpers, service-specific dependency pins, and ad-hoc CORS or auth middleware. Local setups
often diverged from CI because developers edited whichever file was closest at hand, so migrations
ran against different heads, HTTP timeouts drifted, and the webapp shipped with broader CORS than the
API enforced. The platform now standardises on one set of artefacts and expects every surface (local,
staging, CI, production) to consume that same source of truth.

## Decision

- Database migrations live in `services/api/migrations`, driven exclusively by
  `services/api/alembic.ini`. Every migration job (for example `scripts/ci/migrations.sh`) shells out
  with `-c services/api/alembic.ini`, and new revisions must be added to that directory.
- Python dependencies are pinned via the root `constraints.txt`. Service manifests (for example
  `services/api/requirements.txt`, `services/worker/requirements.txt`, `packages/awa_common/pyproject.toml`)
  include the constraint file so local installs and CI resolve identical versions.
- Runtime configuration is imported through `packages/awa_common/settings.py`. All services read env
  variables via `awa_common.settings.settings`, which exposes the canonical names such as `ENV`,
  `APP_ENV`, `DATABASE_URL`, `CORS_ORIGINS`, `OIDC_ISSUER`, rate-limit knobs, and ETL timeouts.
- Structured logging is provided by `packages/awa_common/logging.py` using structlog JSON renderers.
  Middleware (`awa_common.logging.RequestIdMiddleware` and `services/api.security.RequestContextMiddleware`)
  binds `timestamp`, `level`, `service`, `env`, `version`, `request_id`, `trace_id`, and `user_sub` so the
  API, workers, and ETL jobs emit identical payloads.
- Metrics are defined in `packages/awa_common/metrics.py`, which registers shared Prometheus series such as
  `http_requests_total`, `http_request_duration_seconds`, `task_runs_total`, `task_failures_total`,
  `etl_runs_total`, `etl_duration_seconds`, `etl_failures_total`, `etl_retry_total`, and `queue_backlog`
  with the common `(service, env, version)` label set. The API exposes `/metrics` via the same module.
- Security is enforced through Keycloak OIDC validation in
  `packages/awa_common/security/oidc.py` and FastAPI guards in `services/api/security.py`. Tokens must
  include `sub`, `email`, and role claims (`roles` array preferred, `realm_access.roles` fallback). RBAC
  recognises the shared `viewer`, `ops`, and `admin` roles, and rate limits run through
  `packages/awa_common/security/ratelimit.py`.
- ETL reliability uses the shared HTTP client (`packages/awa_common/etl/http.py`) with unified
  httpx + tenacity retries, and the transactional idempotency guard backed by the `load_log` table
  (`packages/awa_common/db/load_log.py`, migration `services/api/migrations/versions/0032_etl_reliability.py`).
  Metrics flow through `awa_common.metrics.record_etl_run/skip/retry`.
- The customer-facing web experience lives under `webapp/` (Next.js 14 + NextAuth Keycloak provider).
  It reads the API base URL via `NEXT_PUBLIC_API_URL` and relies on the API’s CORS defaults discussed
  in `services/api/main.py::resolve_cors_origins`.
- Continuous integration reuses the same artefacts: `docker-compose.yml` for services, `scripts/ci/*.sh`
  for migrations/tests, and `Makefile` targets (`make qa`, `make migrations-local`) that enforce the
  constraints file and Require migrations to round-trip locally before PRs merge.
- Repository ownership is codified in the root `CODEOWNERS`. Branch protection on `main` requires a
  CODEOWNERS approval before merge; changes to the artefacts listed here must be reviewed by the
  designated owner.

## Consequences

Centralising these contracts removes the drift between local machines, CI, and production: everyone
migrates the same schema, installs the same wheels, and adheres to consistent logging, security, and
metric formats. The trade-off is tighter change control—updating any source-of-truth artefact requires
touching the canonical file and landing a CODEOWNERS-reviewed PR—but the benefit is deterministic
rollouts and simpler incident response (logs, metrics, and configs line up across environments). Teams
must update this ADR when introducing new single-source components so future maintainers know where to
look.

## Status update

The only active migration root is `services/api/migrations`, and `services/returns_etl/migrations/env.py`
has been removed to enforce that single source of truth.

## Links

- [Repository README](https://github.com/your-org/AWA-App/blob/main/README.md)
- [Documentation index](../index.md)
- [Security guide](../SECURITY.md)
- [Observability guide](../OBSERVABILITY.md)
- [ETL playbook](../ETL.md)
- [Frontend guide](../FRONTEND.md)
- CI scripts: `scripts/ci`
- Alembic configuration: `services/api/alembic.ini`
- Alembic migrations: `services/api/migrations`
