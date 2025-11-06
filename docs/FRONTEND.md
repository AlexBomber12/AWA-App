# Frontend Overview

The `webapp/` directory contains the Next.js console for AWA. The application authenticates users
through Keycloak via NextAuth, shares the resulting roles with the API, and enforces strict
environment-aware CORS settings.

## Auth flow

1. A user navigates to `webapp/` and chooses **Login**.
2. NextAuth redirects the browser to the configured Keycloak realm.
3. After successful authentication, NextAuth receives the ID/Access tokens, extracts the `roles`
   (or `realm_access.roles`) claim, and persists them in the session (`session.user.roles`).
4. Subsequent requests from the webapp to the FastAPI backend include credentials (cookies)
   protected by the CORS policy defined in the API.
5. The API uses the same Keycloak roles to authorize endpoints, keeping the session and backend
   in sync.

## Environment variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `NEXTAUTH_URL` | Public URL the webapp uses for callbacks. Must match load balancer or dev URL. | `http://localhost:3000` (dev template only) |
| `KEYCLOAK_ISSUER` | OpenID Connect issuer URL for the AWA Keycloak realm. | `https://keycloak.example.com/realms/awa` |
| `KEYCLOAK_CLIENT_ID` | Keycloak client configured for the webapp. | _(required)_ |
| `KEYCLOAK_SECRET` | Client secret matching `KEYCLOAK_CLIENT_ID`. | _(required)_ |
| `NEXTAUTH_SECRET` | Random secret for NextAuth session encryption. | _(required)_ |
| `APP_ENV` | Runtime profile controlling CORS defaults. One of `dev`, `stage`, `prod`. | `dev` |
| `CORS_ORIGINS` | Comma-separated list of trusted origins for the API. | Empty (defaults to `http://localhost:3000` when `APP_ENV=dev`) |

## Role mapping

Keycloak issues roles either in a top-level `roles` claim or within
`realm_access.roles`. The helper in `webapp/lib/auth.ts` normalises both sources and attaches the
resulting list of roles to `session.user.roles`. Typical roles are:

- `viewer` — read-only dashboards.
- `ops` — trigger ingestions and manage SKUs.
- `admin` — elevated access for configuration changes.

Back-end guards expect the same set of roles. Providing consistent mapping ensures canaries and API
tests can rely on the session for authorisation state.

Example Keycloak token snippet:

```json
{
  "sub": "7415f93a-b4e3-45ee-9c61-f38d3b1d1fc7",
  "email": "ops@example.com",
  "realm_access": {
    "roles": ["ops", "viewer"]
  }
}
```

## CORS policy

- **dev**: If `CORS_ORIGINS` is unset, the API defaults to `http://localhost:3000`. Extra origins can
  be added by setting the environment variable.
- **stage / prod**: `CORS_ORIGINS` must be provided and may *not* include a wildcard (`*`). API
  startup fails fast if the variable is missing, guaranteeing that only explicit origins gain access.

All environments use:

- `allow_credentials=True`
- Methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`
- Headers: `*`
- `max_age=600`

## Local development checklist

1. Copy `webapp/.env.local.template` to `webapp/.env.local` and fill in Keycloak credentials plus
   `NEXTAUTH_SECRET`.
2. Start the API (e.g. `docker compose -f docker-compose.dev.yml up api postgres`).
3. In another terminal, run `npm install` then `npm run dev` inside `webapp/`.
   - Alternatively, `docker compose -f docker-compose.dev.yml --profile webapp up webapp` will start
     the Next.js dev server against the running API.
4. Visit `http://localhost:3000`, log in, and navigate to `/profile` to confirm roles are visible.

