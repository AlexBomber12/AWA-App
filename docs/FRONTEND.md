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
- `webapp/components/layout/AppShell.tsx` defines the sidebar, header, and responsive layout.
- `webapp/components/ui/` contains shadcn/ui primitives (currently only `Button`). Expand this folder
  instead of inlining ad-hoc components.
- `webapp/lib/` collects shared helpers (`utils.ts` currently exports `cn`). Future API clients,
  hooks, and formatting utilities should be colocated here.
- `webapp/tests/unit` and `webapp/tests/e2e` host Jest + React Testing Library unit tests and
  Playwright smoke tests.

Tailwind CSS provides the design tokens. Update `tailwind.config.ts` and `app/globals.css` when
adding new semantic colors or radii so the entire UI stays consistent.

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
