# Frontend Guide

The web console lives under `webapp/` and is built with Next.js 14 (App Router) and NextAuth’s
Keycloak provider. This section documents the required configuration and how it integrates with the
API’s security model.

## Structure

- `webapp/app/` contains the App Router pages (`page.tsx`, `(auth)/login`, profile routes).
- `webapp/lib/auth.ts` exports the canonical `authOptions` used by NextAuth, along with helpers to
  decode Keycloak tokens and normalise roles.
- Tooling is managed via `webapp/package.json` and `webapp/tsconfig.json`; the repo ships with
  `package-lock.json`, so use `npm install` for deterministic installs.

## Authentication Flow

1. A user visits the console and triggers **Sign in**.
2. NextAuth redirects to the Keycloak realm configured by `KEYCLOAK_ISSUER`.
3. After the user authenticates, NextAuth receives the tokens, calls
   `rolesFromToken` (`webapp/lib/auth.ts`) to collect roles from the top-level `roles` claim,
   `realm_access.roles`, or resource access entries, and stores them on `session.user.roles`.
4. Subsequent API requests include session cookies; the FastAPI backend reads the same roles (see
   `docs/SECURITY.md`) so RBAC stays aligned end-to-end.

## Environment Variables

| Variable | Description |
| -------- | ----------- |
| `NEXTAUTH_URL` | Public base URL for callbacks (e.g. `http://localhost:3000` in dev). |
| `NEXTAUTH_SECRET` | Random 32+ byte secret for NextAuth session encryption. |
| `KEYCLOAK_ISSUER` | Keycloak issuer, typically `https://<host>/realms/awa`. |
| `KEYCLOAK_CLIENT_ID` | Keycloak client identifier for the webapp (`awa-webapp`). |
| `KEYCLOAK_SECRET` | Client secret registered with the Keycloak client. |
| `NEXT_PUBLIC_API_URL` | Base URL for API requests; defaults to `http://localhost:8000`. |

The API derives its own CORS origins from `CORS_ORIGINS` / `APP_ENV` (see `services/api/main.py`), so
ensure the values above match the allowed origins in your deployment.

## CORS and API Interaction

- Development (`APP_ENV=dev`): if `CORS_ORIGINS` is unset the API automatically allows
  `http://localhost:3000`, which matches the Next.js dev server.
- Stage/Prod: set `CORS_ORIGINS` explicitly (comma-separated list) and avoid wildcards. Startup fails
  if the list is empty or contains `"*"`.
- The webapp reads `NEXT_PUBLIC_API_URL` to call backend routes; keep this aligned with the API host
  exposed to browsers.

## Local Development

1. Start the backend stack:
   ```bash
   docker compose up -d --build --wait db redis api worker
   ```
   or `make up` which wraps the same command.
2. Create `webapp/.env.local` with the required variables, for example:
   ```ini
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=replace-with-generated-secret
   KEYCLOAK_ISSUER=https://keycloak.local/realms/awa
   KEYCLOAK_CLIENT_ID=awa-webapp
   KEYCLOAK_SECRET=replace-with-dev-secret
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Install dependencies and run the dev server:
   ```bash
   cd webapp
   npm install
   npm run dev
   ```
4. Navigate to `http://localhost:3000`. The profile page (`/profile`) shows the decoded roles and
   helps verify Keycloak claims during setup.
5. Confirm the API is reachable (`curl http://localhost:8000/ready`) before testing UI flows.

## Role-Based UI Hints

Components can inspect `session.user.roles` to conditionally render features. Align role names with
those documented in `docs/SECURITY.md` (`viewer`, `ops`, `admin`) so backend enforcement and UI hints
stay in sync. When adding new protected sections, guard both the API route and the React component.
