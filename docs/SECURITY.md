# Security & Authentication

This service relies on Keycloak for OpenID Connect (OIDC) authentication and enforces
role-based access control (RBAC) together with request auditing and per-role
rate limiting. This document summarizes the required Keycloak configuration,
environment variables, and runtime behaviour.

## Keycloak Setup

* **Realm:** `awa`
* **Client:** `awa-webapp` (PKCE-enabled public client for the SPA).
* **Realm roles:** `viewer`, `ops`, `admin`.
* **Token mapper:** add a mapper that publishes the assigned realm roles in a
  `roles` claim (array of strings). The API will also accept Keycloak defaults:
  `realm_access.roles` and `resource_access["awa-webapp"].roles`.

Ensure that the realm issues tokens from:

* Issuer URL: `https://<keycloak-host>/realms/awa`
* Discovery document: `https://<keycloak-host>/realms/awa/.well-known/openid-configuration`

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `OIDC_ISSUER` | `https://keycloak.local/realms/awa` | Issuer URL used for token validation and discovery. |
| `OIDC_AUDIENCE` | `awa-webapp` | Expected audience (`aud`) claim. |
| `OIDC_JWKS_URL` | _(derived from discovery)_ | Optional override for the JWKS endpoint. |
| `OIDC_JWKS_TTL_SECONDS` | `900` | Cache duration for JWKS responses. |
| `SECURITY_HSTS_ENABLED` | `false` | Emit HSTS when `ENV` is `stage` or `prod`. |
| `SECURITY_REFERRER_POLICY` | `strict-origin-when-cross-origin` | Value for the `Referrer-Policy` response header. |
| `SECURITY_FRAME_OPTIONS` | `DENY` | Value for the `X-Frame-Options` header. |
| `SECURITY_X_CONTENT_TYPE_OPTIONS` | `nosniff` | Value for the `X-Content-Type-Options` header. |
| `RATE_LIMIT_VIEWER` | `30/minute` | Rate limit window for viewer role. |
| `RATE_LIMIT_OPS` | `120/minute` | Rate limit window for ops role. |
| `RATE_LIMIT_ADMIN` | `240/minute` | Rate limit window for admin role. |
| `MAX_REQUEST_BYTES` | `1048576` | Maximum allowed request body size in bytes. |
| `SECURITY_ENABLE_AUDIT` | `true` | Toggle audit-log persistence. |

## Response Security Headers

Every FastAPI response includes a standard set of defensive headers:

* `X-Content-Type-Options`: prevents MIME-sniffing (`SECURITY_X_CONTENT_TYPE_OPTIONS`).
* `X-Frame-Options`: clickjacking defence (`SECURITY_FRAME_OPTIONS`).
* `Referrer-Policy`: controls outbound referrers (`SECURITY_REFERRER_POLICY`).
* `Strict-Transport-Security`: enabled only when `SECURITY_HSTS_ENABLED=true`
  **and** `ENV` is `stage` or `prod`, enforcing HTTPS for one year with the
  `includeSubDomains; preload` directives.

Routes can override headers explicitly; the middleware preserves values that are
set within an endpoint.

## Rate Limiting

Role-aware throttling is enforced globally using Redis-backed counters. The
defaults are:

| Role | Default window |
| ---- | -------------- |
| `viewer` | `30/minute` |
| `ops` | `120/minute` |
| `admin` | `240/minute` |

Values are configured via `RATE_LIMIT_<ROLE>` in a `requests/second|minute`
string format, e.g. `45/sec` or `100/min`. When Redis is unavailable the limiter
returns HTTP 503 in stage/prod, and logs a warning while allowing traffic in
local/dev. The Redis URL (`REDIS_URL`) must therefore be reachable in deployed
environments.

The `@no_rate_limit` decorator exempts individual endpoints (for example
`/ready`, `/health`, and `/metrics`), and per-route overrides may still be
applied where tighter throttling is required.

## Request Size Limits

Incoming requests are capped by `MAX_REQUEST_BYTES` (default 1 MB). Requests
declaring a larger `Content-Length` are rejected immediately with HTTP 413, and
chunked uploads are streamed through a guard that stops reading once the limit
is exceeded. Update the environment variable to relax or tighten the boundary.

## Sentry PII Scrubbing

Sentry telemetry is initialised with `send_default_pii=False` and custom
scrubbers that:

* Mask sensitive headers (`Authorization`, `Cookie`, `Set-Cookie`,
  `X-API-Key`, `X-Amz-Security-Token`).
* Redact obvious PII patterns (email addresses, North American phone numbers)
  from event messages, request payloads, extras, contexts, and breadcrumbs.
* Preserve key names while replacing values with `***`.
* Attach the `request_id` tag when available from headers or correlation ID.

These transformations run for both events and breadcrumbs, ensuring that secrets
and user identifiers never reach Sentry.

## Token Validation

Tokens are validated with Authlib using the RSA/PS signature algorithms
published by the Keycloak JWKS endpoint. The following rules apply:

1. Signature matches a JWKS key (keys are cached for up to
   `OIDC_JWKS_TTL_SECONDS` seconds).
2. `iss` equals `OIDC_ISSUER`.
3. `aud` equals or contains `OIDC_AUDIENCE`.
4. `exp`, `nbf`, and `iat` claims are respected (`iat` must be within 24 hours
   of the current time).
5. The subject (`sub`) claim is required.

User metadata is extracted into a `UserCtx` object and attached to
`request.state.user`.

## Roles & Capabilities

| Role | Description |
| ---- | ----------- |
| `viewer` | Read-only access to analytics, SKUs, and monitoring APIs. |
| `ops` | Viewer privileges plus operational tasks such as ingest jobs, ROI approvals, uploads. |
| `admin` | Full control, including configuration-changing actions. |

Every protected endpoint declares both its required role dependency and an
appropriate rate limiter.

## Audit Trail

Authenticated requests (excluding `/health`, `/ready`, and `/metrics`) append a
row to the `audit_log` table containing the subject, email, roles, HTTP method,
path, status code, latency, IP, user agent, request id, and timestamp. Errors
while writing audit entries never block the response.

## Example Requests

```
# Missing or invalid token → 401
curl -i http://localhost:8000/sku/ABC123

# Viewer token succeeds on read-only route
curl -i http://localhost:8000/sku/ABC123 \
  -H "Authorization: Bearer $VIEWER_TOKEN"

# Ops-only endpoint rejects viewer
curl -i -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -d '{"uri":"s3://example"}'

# Same endpoint accepts ops token
curl -i -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $OPS_TOKEN" \
  -d '{"uri":"s3://example"}'

# Exceeding the per-role limit → 429
for i in $(seq 1 200); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $VIEWER_TOKEN" \
    http://localhost:8000/sku/ABC123
done
```

Replace `$VIEWER_TOKEN` and `$OPS_TOKEN` with Keycloak-issued access tokens for
the corresponding users.
