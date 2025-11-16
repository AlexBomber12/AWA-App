# Frontend Guide

This guide is the single source of truth for all AWA web UI work. Every new frontend change **must**
follow the conventions below.

## Architecture blueprint
1. **Browser → Next.js webapp (App Router).** The web console lives under `webapp/` and uses
   Next.js 14+ with the App Router and TypeScript-only modules. Component code renders on the
   server by default and opt into client interactivity when needed in `/components`.
2. **Next.js BFF routes (`app/api/bff/*`).** Back-end-for-frontend (BFF) handlers will be added in
   PR-UI-1B. They sit next to the App Router pages, proxy authenticated calls, and apply any UI
   specific shaping before forwarding to the API.
3. **FastAPI backend (`services/api`).** Remains the system of record for auth, RBAC, business
   workflows, and event ingestion. UI calls it via `NEXT_PUBLIC_API_URL` through the upcoming BFF
   layer or directly for simple read-only endpoints.

## Project layout
- `webapp/app/`
  - `layout.tsx` wires the global `<AppShell />`, fonts, and providers.
  - `page.tsx` redirects to `/dashboard`.
  - `app/dashboard|roi|sku|ingest|returns|inbox|decision|settings/page.tsx` are presentational stub
    routes so navigation can be validated visually.
  - `app/api/bff/*` will host API handlers that terminate in FastAPI once PR-UI-1B lands.
- `webapp/components/layout/` hosts the shell primitives shared by every route:
  - `AppShell` wires auth + permissions and renders the sidebar/header.
  - `PageHeader`, `PageBody`, and `Breadcrumbs` provide consistent page structure.
- `webapp/components/ui/` exports the wrapped shadcn primitives (`Button`, `Input`, `Select`, `Tabs`,
  `Dialog`, `Drawer`, `Tooltip`, etc.) via `index.ts`. Feature code should never import
  `@radix-ui/*` or `shadcn/ui` directly—use these wrappers so tokens stay centralized.
- `webapp/components/data/` contains reusable table scaffolding (`DataTable`, `FilterBar`,
  `PaginationControls`, `EmptyState`, `ErrorState`, `SkeletonTable`). These components are generic
  and should be reused by ROI, Returns, and future screens for standard grid patterns.
- `webapp/components/forms/` hosts the React Hook Form + Zod glue (`Form`, `FormField`, `FormItem`,
  etc.). Forms should always be typed by a Zod schema and surface API errors via the shared
  `ApiError` type.
- `webapp/components/features/*` is the only place for feature-specific UI. Keep leaf components
  close to their routes so Codex prompts can reason about the feature slice without touching shared
  primitives.
- `webapp/lib/` collects shared helpers (`utils.ts` currently exports `cn`). Future API clients,
  hooks, and formatting utilities should be colocated here.
- `webapp/tests/unit` and `webapp/tests/e2e` host Jest + React Testing Library unit tests and
  Playwright smoke tests.

Tailwind CSS provides the design tokens. Update `tailwind.config.ts` and `app/globals.css` when
adding new semantic colors or radii so the entire UI stays consistent.

## Feature slice golden path

Every new feature should follow the same slice blueprint so layout/ui/data/forms primitives stay
consistent and Codex prompts can reason about the codebase by name.

Example structure for a hypothetical feature named `foo`:

- `app/foo/page.tsx` — App Router entry point. Compose `PageHeader`, `PageBody`, and feature
  components (the `AppShell` wrapper already lives in `app/layout.tsx`).
- `app/api/bff/foo/route.ts` — BFF route that calls FastAPI via `fetchFromApi`. Translate backend
  errors into `ApiError` before returning a response.
- `lib/api/fooClient.ts` — Typed client that wraps `fetchFromApi("/foo")` and exposes Zod or
  OpenAPI-derived types.
- `components/features/foo/*` — Feature-specific UI composed from the shared layers in
  `components/ui`, `components/data`, and `components/forms`.

### New feature checklist

1. Create `app/foo/page.tsx` with `PageHeader`/`PageBody` inside the global `AppShell`.
2. Add BFF route(s) under `app/api/bff/foo/route.ts` that call FastAPI via `fetchFromApi`.
3. Create a typed API client in `lib/api/fooClient.ts` so server and client components share the
   same contract.
4. Build UI under `components/features/foo/`, always reusing:
   - `components/ui` wrappers (never import shadcn/ui primitives directly),
   - `components/data/DataTable`, `PaginationControls`, and `FilterBar` for tabular work,
   - `components/forms/Form` + Zod schemas for inputs and mutations.
5. Add at least one Storybook story for the primary feature component so UI regressions can be
   caught visually (`npm run storybook`).
6. Add or update unit tests that cover critical primitives (tables, permissions, etc.) under
   `webapp/tests/unit`.

Use the shared states as starting points:

- For new tables, copy the TanStack scaffolding in `components/data/DataTable` and pair it with
  `PaginationControls` (and `FilterBar` for filters).
- For new filter toolbars, drop in `components/data/FilterBar` and pass your filter inputs as
  children; the component already renders apply/reset actions.
- For new forms, `components/forms/Form` + Zod typed schemas keep validation and `ApiError` handling
  consistent. Map server validation problems to field-level errors or a global `FormMessage`
  instead of bespoke alerts.

## Auth & RBAC
- **Flow:** Browser → NextAuth (App Router) → Next.js BFF → FastAPI. Keycloak runs in confidential
  client mode using `KEYCLOAK_ISSUER`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`,
  `NEXTAUTH_URL`, and `NEXTAUTH_SECRET`. Tokens stay on the server; the BFF layer forwards them as
  `Authorization: Bearer <token>` to FastAPI.
- **Session helper:** `lib/auth.ts` centralises `authOptions` plus `getServerAuthSession()` so server
  components, layouts, and API routes reuse the same wiring. Sessions include `session.accessToken`
  and `session.user.roles` derived from Keycloak's `roles`, `realm_access`, or `resource_access`.
- **BFF helper:** `lib/api/fetchFromApi.ts` enforces the "one way into FastAPI" rule. It loads the
  session, applies the bearer token, builds URLs from `NEXT_PUBLIC_API_URL`, and maps API errors into
  `{ code, message, status, details }`. BFF routes (e.g. `app/api/bff/stats/route.ts`) should call
  `fetchFromApi("/stats/kpi")` and translate `ApiError`s into `NextResponse`.
- **Permissions source of truth:** `lib/permissions.ts` defines `Role`, `Resource`, `Action`, and the
  ACL that matches `docs/SECURITY.md` (viewer, ops, admin). Use:
  - `getUserRolesFromSession(session)` when you already have a server session.
  - `usePermissions()` in client components to read `{ roles, can, hasRole }`.
  - `PermissionGuard` (`// Pattern: wrap protected buttons/sections...`) to hide sections or buttons.
- **Sidebar & guards:** `AppShell` uses `usePermissions()` so Inbox/Decision Engine/Settings only
  render for the correct roles. Page sections (ROI bulk approve, inbox actions) should wrap their UI
  in `PermissionGuard` or a hook call, and any future middleware must rely on
  `getServerAuthSession()` so RBAC stays in sync across the stack.

## Tooling & commands
The repo uses **npm** (see `package-lock.json`). Run these from `webapp/`:

| Command | Purpose |
| ------- | ------- |
| `npm install` | Install dependencies. |
| `npm run dev` | Start the Next.js dev server with the App Router. |
| `npm run lint` | ESLint with Next.js + TypeScript rules. |
| `npm run format` / `format:write` | Prettier in check or write mode. |
| `npm run test:unit` | Jest + React Testing Library smoke tests. |
| `npm run test:e2e` | Playwright sidebar/navigation smoke covering the AppShell. |
| `npm run storybook` | Start the component library sandbox with layout/ui/data/forms stories. |
| `npm run build` | Production build used by docker-compose and CI. |

CI executes `lint`, `test:unit`, `test:e2e`, and `build` in the `webapp-build` job. Local docker
runs use `make webapp-up` which builds the Next.js image and exposes it on port `3000`.

## Roadmap & scope guardrails
- **PR-UI-1A (this change):** Bootstrap App Router, Tailwind design tokens, shadcn/ui wiring,
  navigation stubs, Jest + Playwright smoke coverage, docker + docs integration.
- **PR-UI-1B:** Add NextAuth with Keycloak, BFF routes under `app/api/bff`, and Settings controls
  for environment + RBAC toggles.
- **Later milestones:** Fill in ROI, SKU, Ingest, Returns, Inbox, and Decision Engine workflows as
  described in the ROI and Virtual Buyer specifications.

Until PR-UI-1B lands:
- **Do not** ship Keycloak/NextAuth wiring, API mutations, or RBAC switches. Keep routes stubbed.
- **Do not** add bespoke layout shells. Extend `AppShell` instead so navigation stays uniform.
- **Do** keep all new code in TypeScript (`.ts`/`.tsx`) and follow the Tailwind tokens defined in
  `globals.css`.
