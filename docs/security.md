# API Authentication & RBAC

The API supports pluggable authentication so that environments can opt-in to protection without breaking existing public endpoints. By default (`AUTH_MODE=disabled`) no authentication is enforced and the service behaves exactly as before.

## Modes

- `AUTH_MODE=oidc` – validate incoming `Authorization: Bearer <JWT>` headers using an OIDC provider (Keycloak, Okta, Azure AD, etc.).
- `AUTH_MODE=forward-auth` – trust identity headers added by a reverse proxy (Traefik, NGINX, Envoy). No token parsing happens inside the API.
- `AUTH_MODE=disabled` – authentication and RBAC are bypassed. This is the default to keep current flows intact.

## Environment variables

| Variable | Description |
| -------- | ----------- |
| `AUTH_MODE` | `disabled`, `oidc`, or `forward-auth`. |
| `OIDC_ISSUER` | Required when using the OIDC mode (e.g., `https://idp.example.com/realms/awa`). |
| `OIDC_AUDIENCE` | Optional audience check for access tokens. |
| `OIDC_CLIENT_ID` | Optional additional audience (useful when tokens include `client_id`). |
| `OIDC_JWKS_URL` | Optional override for the JWKS URL. Falls back to issuer discovery. |
| `OIDC_ALGS` | Comma separated list of accepted algorithms (`RS256` by default). |
| `FA_USER_HEADER` | Forward-auth header containing the username (`X-Forwarded-User`). |
| `FA_EMAIL_HEADER` | Forward-auth header containing the email (`X-Forwarded-Email`). |
| `FA_GROUPS_HEADER` | Forward-auth header listing groups/roles (`X-Forwarded-Groups`). |
| `ROLE_MAP_JSON` | Mapping from internal roles to IdP/proxy groups, e.g. `{"admin":["admin","realm:admin"],"ops":["ops","devops"],"viewer":["viewer"]}`. |
| `AUTH_REQUIRED_ROUTES_REGEX` | Optional regex to restrict RBAC enforcement to matching paths. Leave empty to protect all guarded endpoints. |

## Role mapping

Use `ROLE_MAP_JSON` to translate provider-specific groups to the internal roles that the API understands (`viewer`, `ops`, `admin` by convention). You may extend or replace the mapping to introduce new roles.

Example:

```json
{"admin":["admin","realm:admin"],"ops":["ops","devops"],"viewer":["viewer","readonly"]}
```

## Forward-auth example (Traefik)

Configure a forward-auth service that injects user headers:

```toml
[http.middlewares.forward-auth.forwardAuth]
  address = "https://auth-proxy.internal/verify"
  trustForwardHeader = true
  authResponseHeaders = ["X-Forwarded-User","X-Forwarded-Email","X-Forwarded-Groups"]
```

Set in the API container:

```
AUTH_MODE=forward-auth
FA_USER_HEADER=X-Forwarded-User
FA_EMAIL_HEADER=X-Forwarded-Email
FA_GROUPS_HEADER=X-Forwarded-Groups
ROLE_MAP_JSON={"admin":["admin"],"ops":["ops"],"viewer":["viewer"]}
```

## OIDC example

```
AUTH_MODE=oidc
OIDC_ISSUER=https://keycloak.example.com/realms/awa
OIDC_JWKS_URL=https://keycloak.example.com/realms/awa/protocol/openid-connect/certs
OIDC_AUDIENCE=awa
ROLE_MAP_JSON={"admin":["admin","realm:admin"],"ops":["ops","devops"],"viewer":["viewer"]}
```

Tokens must include `sub`, must be signed with an accepted algorithm, and should contain one of the mapped groups so that roles resolve correctly.

## Protecting routes

Apply the provided FastAPI dependencies to guard endpoints:

```python
from services.api.security import require_admin, require_ops, require_viewer


@router.post("/admin/task", dependencies=[Depends(require_admin)])
async def run_admin_task(): ...
```

Set `AUTH_REQUIRED_ROUTES_REGEX` when only a subset of routes should be enforced (for example `^/(ingest|score|roi)`).

## Audit trail

When authentication is enabled the API writes request metadata to the `audit_log` table, including user id, email, roles, route template, status code, latency, IP, and request id. Failures to record the audit entry never affect the HTTP response. To disable auditing, keep `AUTH_MODE=disabled`.
