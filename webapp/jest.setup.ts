import "@testing-library/jest-dom";

process.env.NEXT_PUBLIC_API_URL ??= "http://localhost:8000";
process.env.NEXT_PUBLIC_APP_ENV ??= "test";
process.env.KEYCLOAK_ISSUER ??= "http://localhost:8080/realms/awa";
process.env.KEYCLOAK_CLIENT_ID ??= "awa-webapp";
process.env.KEYCLOAK_CLIENT_SECRET ??= "jest-secret";
process.env.NEXTAUTH_URL ??= "http://localhost:3000";
process.env.NEXTAUTH_SECRET ??= "jest-nextauth-secret";
