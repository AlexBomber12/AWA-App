# AWA Webapp

This directory contains the Next.js frontend for the AWA platform. The app uses NextAuth with the
Keycloak provider and exposes a minimal console with login, logout, and profile pages.

## Getting started

1. Duplicate `.env.local.template` and rename it to `.env.local`.
2. Fill in the Keycloak client values and `NEXTAUTH_SECRET`. For local experimentation you can use
   values from a development realm.
3. Install dependencies and run the development server:

   ```bash
   npm install
   npm run dev
   ```

The app listens on `http://localhost:3000`. It expects the FastAPI backend to run on
`http://localhost:8000`.

## Build

To create a production build:

```bash
npm run build
npm run start
```

## Auth flow

Users authenticate against Keycloak via NextAuth. The JWT roles claim (or Keycloak
`realm_access.roles`) is mapped into the NextAuth session so components can check permissions.

