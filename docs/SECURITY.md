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
| `RATE_LIMIT_VIEWER_TIMES` / `RATE_LIMIT_VIEWER_SECONDS` | `60` / `60` | Rate limit for viewer endpoints. |
| `RATE_LIMIT_OPS_TIMES` / `RATE_LIMIT_OPS_SECONDS` | `120` / `60` | Rate limit for ops endpoints. |
| `RATE_LIMIT_ADMIN_TIMES` / `RATE_LIMIT_ADMIN_SECONDS` | `180` / `60` | Rate limit for admin endpoints. |
| `SECURITY_ENABLE_AUDIT` | `true` | Toggle audit-log persistence. |

The Redis URL (`REDIS_URL`) must be reachable so the per-role rate limiters can
store counters.

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
