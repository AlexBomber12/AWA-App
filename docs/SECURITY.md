# Security Guide

The AWA platform authenticates with Keycloak, enforces FastAPI role guards, and hardens every request
path with rate limits, strict CORS, body limits, and Sentry scrubbing. This document captures the
single source of truth reflected in the codebase.

## OIDC and Token Validation

- **Realm / Client:** Keycloak realm `awa` with confidential client `awa-webapp`.
- The API reads issuer and audience from `OIDC_ISSUER` and `OIDC_AUDIENCE` (defaults in
  `.env.example`). Discovery happens at `${OIDC_ISSUER}/.well-known/openid-configuration`.
- `packages/awa_common/security/oidc.py` pulls JWKS via Authlib. Cache lifetime is controlled by
  `OIDC_JWKS_TTL_SECONDS` (default 900 s). `OIDC_JWKS_URL` can override discovery.
- Validation requires: a signed token (RS/PS algorithms), `iss` equal to `OIDC_ISSUER`, `aud`
  containing `OIDC_AUDIENCE`, an `exp` in the future, an `iat` within 24 h, and a non-empty `sub`.
- Email is read from `email` or `preferred_username`. Roles prefer the top-level `roles` claim but
  fall back to `realm_access.roles` or `resource_access[OIDC_AUDIENCE].roles`.
- `services/api/security.current_user` invokes `validate_access_token`, stores the resulting
  `UserCtx` on `request.state.user`, and binds `user_sub` into the logging context for observability.

## Role-Based Access Control

- Recognised roles live in `packages/awa_common/security/models.py`: `viewer`, `ops`, `admin`.
- Guards in `services/api/security.py` expose dependencies such as `require_ops` and `require_admin`,
  while rate-limit dependencies (`limit_ops`, `limit_admin`) wrap the same role inference.
- Example: `services/api/routes/ingest.submit_ingest` requires `ops` access and applies the ops rate
  limiter; `/jobs/{task_id}` allows any `viewer` or higher.
- When a token is missing or role checks fail, the API responds with 401/403 and logs
  `auth_missing_credentials`/`auth_forbidden` events via structlog.

## CORS Policy

- `services/api/main.resolve_cors_origins` inspects `APP_ENV` and `CORS_ORIGINS`.
  - `APP_ENV=dev` defaults to `http://localhost:3000` when `CORS_ORIGINS` is unset.
  - `APP_ENV` in `{"stage","staging","prod","production"}` **requires** `CORS_ORIGINS`; startup raises
    if it is missing or contains `"*"`.
- Requests inherit `allow_credentials=True`, full CRUD methods, wildcard headers, and `max_age=600`.
- Configure the origins in the environment (e.g. `.env.local`, GitHub secrets) so both the API and the
  Next.js webapp agree on allowed domains.

## HTTP Hardening

- `packages/awa_common/security/headers.install_security_headers` installs middleware that sets:
  - `X-Content-Type-Options: nosniff` (`SECURITY_X_CONTENT_TYPE_OPTIONS`).
  - `X-Frame-Options: DENY` (`SECURITY_FRAME_OPTIONS`).
  - `Referrer-Policy: strict-origin-when-cross-origin`
    (`SECURITY_REFERRER_POLICY`).
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
    when `SECURITY_HSTS_ENABLED=1` **and** `ENV` is `stage` or `prod`.
- Routes may override headers explicitly; the middleware respects existing values.
- Example response:
  ```
  $ curl -i http://localhost:8000/ready
  HTTP/1.1 200 OK
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  ```

## Environment

- Stage and production deployments must set `SECURITY_HSTS_ENABLED=true` to enforce HSTS middleware.
- Stage and production deployments must configure `CORS_ORIGINS` with the allowed frontend domains.

## Rate Limits

- Role-aware throttling uses Redis via `packages/awa_common/security/ratelimit.RoleBasedRateLimiter`.
- Defaults from `packages/awa_common/settings.Settings`:
  - `RATE_LIMIT_VIEWER=30/minute`
  - `RATE_LIMIT_OPS=120/minute`
  - `RATE_LIMIT_ADMIN=240/minute`
- Limits accept strings like `45/sec`. `FastAPILimiter` initialises during startup; in `stage/prod` a
  missing Redis connection raises HTTP 503 to avoid running unprotected.
- Requests exempt from rate limits (`/ready`, `/health`, `/metrics`) use the provided `@no_rate_limit`
  decorator.

## Request Size & Timeout Guards

- `packages/awa_common/security/request_limits.BodySizeLimitMiddleware` rejects bodies exceeding
  `MAX_REQUEST_BYTES` (1 048 576 bytes by default) with HTTP 413. Chunked uploads stop reading once the
  limit is crossed.
- ETL agents use the shared HTTP client (`packages/awa_common/etl/http.request/download`) with:
  - Connect timeout `ETL_CONNECT_TIMEOUT_S=5.0`
  - Read timeout `ETL_READ_TIMEOUT_S=30.0`
  - Total timeout `ETL_TOTAL_TIMEOUT_S=60.0`
  - Up to `ETL_MAX_RETRIES=5` attempts, exponential backoff (`ETL_BACKOFF_BASE_S=0.5`,
    `ETL_BACKOFF_MAX_S=30.0`), and retry-on-status for `ETL_RETRY_STATUS_CODES=[429,500,502,503,504]`.
- Retries log `etl_http_retry` events with `attempt`, `sleep`, and `status_code`, and increment
  `etl_retry_total{source,code}` in Prometheus.

## Sentry Telemetry

- `services/api/sentry_config.py` initialises Sentry when `SENTRY_DSN` is set. Telemetry is optional;
  invalid DSNs are ignored gracefully.
- PII scrubbing lives in `packages/awa_common/security/pii.py`:
  - Headers like `Authorization`, `Cookie`, `X-API-Key` are replaced with `***`.
  - Emails and phone numbers are redacted from messages, payloads, extras, contexts, and breadcrumbs.
  - The current request id is attached as `tags.request_id`.
- The integration disables default PII (`send_default_pii=False`) and registers FastAPI, SQLAlchemy,
  Celery, and logging integrations.
- `services/api/tests/test_sentry_event.py` verifies the scrubbers and `request_id` tagging.

## Secrets and Configuration

- Environment variables are the source of truth. Do **not** commit secrets; use `.env.local` for local
  overrides and GitHub/infra secrets in CI.
- Encrypted materials live under `ops/secrets/` managed by SOPS/age (see `docs/runbooks/secrets.md`).
  Helper targets `make secrets.encrypt` / `make secrets.decrypt` wrap the workflow.
- Rotate credentials by updating the secret manager and re-encrypting artefacts; never store plaintext
  or private keys inside the repository.

## Release Checklist

- ✅ Keycloak tokens tested end-to-end (issuer, audience, role claims) against the target realm.
- ✅ Production/staging `CORS_ORIGINS` set explicitly—no wildcard origins.
- ✅ `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy`
  verified via `curl -I` or smoke tests.
- ✅ Redis-backed rate limiter healthy (`/ready` returns 200, no `rate_limiter_not_initialized` logs).
- ✅ Sentry DSN configured (if required) and scrubbers exercised in staging.
- ✅ Secrets rotated or re-validated; no new plaintext secrets added to Git.
