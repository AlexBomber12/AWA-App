# AWA Webapp

This package hosts the Amazon Wholesale Analytics operator console. It is a
Next.js 14 App Router project with Tailwind CSS + shadcn/ui, Jest + React Testing
Library, and Playwright smoke tests.

## Getting started
1. Install dependencies (`npm install`). npm is the supported package manager
   (`package-lock.json` is checked in).
2. Run `npm run dev` to start the dev server on `http://localhost:3000`.
3. Set `NEXT_PUBLIC_API_URL` in `.env.local` if you need to point at a different
   FastAPI endpoint. `NEXT_PUBLIC_APP_ENV` controls the header badge shown in the
   AppShell.

## Scripts
- `npm run lint`: ESLint with the Next.js recommended + TypeScript rules.
- `npm run format` / `format:write`: Prettier check or write.
- `npm run test:unit`: Jest + React Testing Library smoke test for the AppShell.
- `npm run test:e2e`: Playwright smoke test that exercises the sidebar nav.
- `npm run build`: Production build used by Docker/CI, automatically run by the
  docker-compose service and GitHub Actions.

## Docker
Use `make webapp-up` (repo root) to build and start the docker-compose service
that exposes the production build on `http://localhost:3000`. The Dockerfile uses
multi-stage builds so CI and local workflows share the same pipeline.

## Roadmap
PR-UI-1A only ships the skeleton and base conventions. NextAuth + Keycloak, BFF
routes, and real ROI/Decision Engine features arrive in PR-UI-1B and later PRs
per `docs/FRONTEND.md`.
