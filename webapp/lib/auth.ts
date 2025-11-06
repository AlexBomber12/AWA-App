import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import KeycloakProvider from "next-auth/providers/keycloak";

type KeycloakRoleSource = {
  roles?: unknown;
  realm_access?: {
    roles?: unknown;
  };
  resource_access?: Record<string, { roles?: unknown } | null | undefined>;
};

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];

const collectRoles = (source?: KeycloakRoleSource | null): string[] => {
  if (!source) {
    return [];
  }
  const roleSet = new Set<string>();
  toStringArray(source.roles).forEach((role) => roleSet.add(role));
  toStringArray(source.realm_access?.roles).forEach((role) => roleSet.add(role));
  if (source.resource_access) {
    Object.values(source.resource_access).forEach((entry) => {
      toStringArray(entry?.roles).forEach((role) => roleSet.add(role));
    });
  }
  return Array.from(roleSet);
};

const decodeSegment = (segment: string) => {
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padding = normalized.length % 4 === 0 ? "" : "=".repeat(4 - (normalized.length % 4));
  return Buffer.from(normalized + padding, "base64").toString("utf8");
};

export const decodeKeycloakToken = (token: string | undefined): KeycloakRoleSource | null => {
  if (!token) {
    return null;
  }

  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const payload = decodeSegment(parts[1]);
    return JSON.parse(payload) as KeycloakRoleSource;
  } catch (error) {
    console.warn("Failed to decode Keycloak token payload", error);
    return null;
  }
};

export const rolesFromToken = (
  token: Partial<JWT> & Partial<KeycloakRoleSource>
): string[] => collectRoles(token);

const envOrFallback = (name: string, fallback: string): string => {
  const value = process.env[name];
  return value && value.trim().length > 0 ? value : fallback;
};

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
  },
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    KeycloakProvider({
      issuer: envOrFallback("KEYCLOAK_ISSUER", "https://keycloak.example.com/realms/awa"),
      clientId: envOrFallback("KEYCLOAK_CLIENT_ID", "__CHANGE_ME__"),
      clientSecret: envOrFallback("KEYCLOAK_SECRET", "__CHANGE_ME__"),
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.id_token) {
        const decoded = decodeKeycloakToken(account.id_token);
        if (decoded) {
          const derived = collectRoles(decoded);
          if (derived.length > 0) {
            token.roles = derived;
          }
        }
      }

      const derived = collectRoles(token as KeycloakRoleSource);
      token.roles = derived;

      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.roles = collectRoles(token as KeycloakRoleSource);
        if (!session.user.email && typeof token.email === "string") {
          session.user.email = token.email;
        }
        if (!session.user.name && typeof token.name === "string") {
          session.user.name = token.name;
        }
      }

      return session;
    },
  },
};
