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

## Detail page pattern: SKU example

Use `SkuPage` as the reference implementation for every future "detail" surface. The flow is:

- `app/api/bff/sku/route.ts` proxies FastAPI with `fetchFromApi`, merges summary + history data, and
  translates backend failures into `ApiError` payloads.
- `lib/api/skuClient.ts` exposes a strongly typed `getSkuDetail()` + `useSkuDetailQuery()` pair. All
  client components call the BFF through this client (never FastAPI directly) so React Query caches
  stay consistent.
- `app/sku/[asin]/page.tsx` is the server entry point. It composes `PageHeader`/`PageBody`, enforces
  RBAC via `getServerAuthSession()` + `can({ resource: "sku", action: "view" })`, and renders the
  client-side feature component.
- Feature UI lives in `components/features/sku/*` with a top-level orchestrator (`SkuPage`) that
  loads data via `useSkuDetailQuery` and composes presentational leaves (`SkuCard`,
  `SkuPriceHistoryChart`). Contextual navigation (e.g., "Back to ROI") is handled here.
- Every detail slice ships with Storybook coverage (`stories/features/sku/SkuPage.stories.tsx`) that
  feeds the feature mock data, plus dedicated Jest/RTL tests (see `tests/unit/sku-page.test.tsx` and
  `tests/unit/sku-client.test.ts`).

Future detail-heavy screens (returns detail, vendor detail, etc.) should follow the same layering:
App Router page → BFF route → typed client + query hook → feature slice → story + tests. This keeps
the UX consistent and gives Codex prompts an obvious blueprint to extend.

## Table patterns: large vs. mid-size grids

- **ROI review (large + virtualized).** `components/features/roi/RoiTableContainer.tsx` pairs
  `useTableState` with `components/data/VirtualizedTable` so the ROI surface can handle thousands of
  rows without jank. The flow is `/roi` page → `app/api/bff/roi/route.ts` → `fetchFromApi("/roi")`
  with client-side sorting, selection, and virtualization. Copy this pattern whenever a table needs
  bulk actions, virtual scrolling, or hundreds of visible rows.
- **Returns (mid-size + standard DataTable).** PR-UI-7 turns `/returns` into the canonical
  server-driven “mid-size table” example: `app/api/bff/returns/route.ts` proxies FastAPI
  `/stats/returns` for both summary + paginated list responses, `lib/api/returnsClient.ts` exposes
  `useReturnsListQuery`/`useReturnsStatsQuery`, and `components/features/returns/*` composes the
  summary cards, filters (`FilterBar`), and `components/data/DataTable`. Both ROI and Returns reuse
  `lib/tableState/useTableState`, so pagination, sort, and filters stay synced to the URL regardless
  of table size. Future mid-size tables should mirror the Returns slice: add a BFF route, typed
  client hook, feature components under `components/features/<feature>`, a Storybook story (see
  `stories/features/returns/ReturnsPage.stories.tsx`), and Jest coverage
  (`tests/unit/returns/returns-page.test.tsx`).

Use the shared states as starting points:

- For new tables, copy the TanStack scaffolding in `components/data/DataTable` and pair it with
  `PaginationControls` (and `FilterBar` for filters).
- For new filter toolbars, drop in `components/data/FilterBar` and pass your filter inputs as
  children; the component already renders apply/reset actions.
- For new forms, `components/forms/Form` + Zod typed schemas keep validation and `ApiError` handling
  consistent. Map server validation problems to field-level errors or a global `FormMessage`
  instead of bespoke alerts.

## API & React Query pattern

Dashboard is the reference implementation for typed data access. The flow is:

`app/dashboard/page.tsx` (server) → `app/api/bff/stats` (Next.js BFF) → FastAPI `/stats/kpi` +
`/stats/roi_trend` → typed client in `lib/api/statsClient.ts` → `useApiQuery` → feature components.

**Type generation.** The FastAPI OpenAPI schema drives type safety. Run `npm run webapp:generate-api`
from `webapp/` (or `pnpm webapp:generate-api`) with the API service running. The script uses
`OPENAPI_SCHEMA_URL` (default `http://localhost:8000/openapi.json`) and writes the result to
`lib/api/types.generated.ts`. Do not edit this file manually—regenerate it when backend schemas
change.

**Typed clients.** Clients live under `lib/api/*Client.ts` and import the generated types. Follow the
stats client pattern:

1. Import the relevant `paths["/resource"]["get"]["responses"]` type aliases.
2. Call BFF routes via `fetchFromBff`, which surfaces the shared `ApiError` shape.
3. Export narrow helpers (`getKpi`, `getRoiTrend`, `getDashboardStats`) so server components, hooks,
   and tests share the same contract.

**React Query helpers.** `useApiQuery` and `useApiMutation` wrap TanStack React Query with the
standard `ApiError` type, default stale times/retries, and centralized logging. Always pass a stable
`queryKey`, call the typed client inside `queryFn`, and handle loading/error/success states just as
`DashboardPageClient` does. For mutations, provide the typed mutation function and hook the usual
`onSuccess`/`onError` callbacks.

When adding a new feature:

1. Generate or refresh `types.generated.ts`.
2. Create the BFF route that calls FastAPI via `fetchFromApi` and returns `ApiError` structures on
   failures.
3. Build a typed client that calls the BFF route with `fetchFromBff`.
4. Use `useApiQuery`/`useApiMutation` inside the client component, render loading skeletons, wire
   `ErrorState` for failures, and pass data into presentational components (cards, charts, tables,
   etc.).

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

## QA and testing for webapp
- **Unit + integration tests:** Live in `webapp/tests/unit/**`. They exercise RBAC helpers, API abstractions, table state syncing, ROI containers, and the feature pages themselves. Run them locally with `npm run test:unit` or `npm run test:coverage` (which enables Jest coverage for `app/`, `components/`, and `lib/` with thresholds at ~60% lines/branches).
- **Storybook:** Component sandboxes are under `webapp/stories/**`, covering layout primitives plus feature slices such as ROI, SKU, Returns, Inbox, and Ingest. Use `npm run storybook` for interactive development and `npm run storybook:build` in CI to ensure new stories compile.
- **E2E:** Playwright specs live in `webapp/tests/e2e`. The `navigation-flow.spec.ts` script logs in via `/test-login`, walks Dashboard → ROI → SKU → Ingest → Returns → Inbox, and verifies logout. Run `npm run test:e2e`; the Playwright config launches the Next.js dev server automatically.
- **Lighthouse + accessibility:** `npm run lighthouse` executes `scripts/run-lighthouse.mjs`, optionally bootstrapping a local dev server (`LIGHTHOUSE_SKIP_SERVER=1` skips startup) and failing when the dashboard performance drops below 0.6 or accessibility below 0.8.
- **Combined QA loop:** `npm run qa` chains linting, unit tests with coverage, Storybook build, Playwright, and Lighthouse so feature PRs can reproduce CI locally.

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
