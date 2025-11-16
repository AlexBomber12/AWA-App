import { getServerSession, type NextAuthOptions } from "next-auth";
import KeycloakProvider, { type KeycloakProfile } from "next-auth/providers/keycloak";

import { KNOWN_ROLES, type Role } from "@/lib/permissions";

type KeycloakAccessProfile = KeycloakProfile & {
  roles?: string[];
  realm_access?: { roles?: string[] };
  resource_access?: Record<string, { roles?: string[] }>;
};

const keycloakIssuer = requireEnv("KEYCLOAK_ISSUER");
const keycloakClientId = requireEnv("KEYCLOAK_CLIENT_ID");
const keycloakClientSecret = requireEnv("KEYCLOAK_CLIENT_SECRET");
const nextAuthSecret = requireEnv("NEXTAUTH_SECRET", process.env.SECRET);

const toRole = (value: string): value is Role => KNOWN_ROLES.includes(value as Role);

const normalizeRoles = (roles: string[] | undefined): Role[] => {
  if (!Array.isArray(roles)) {
    return [];
  }
  return roles.filter(toRole);
};

const extractRoles = (profile: KeycloakAccessProfile): Role[] => {
  const collected = new Set<string>();

  normalizeRoles(profile.roles).forEach((role) => collected.add(role));

  if (profile.realm_access?.roles) {
    normalizeRoles(profile.realm_access.roles).forEach((role) => collected.add(role));
  }

  const resourceRoles = profile.resource_access?.[keycloakClientId]?.roles;
  if (resourceRoles) {
    normalizeRoles(resourceRoles).forEach((role) => collected.add(role));
  }

  return Array.from(collected).filter(toRole);
};

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
  },
  providers: [
    KeycloakProvider({
      issuer: keycloakIssuer,
      clientId: keycloakClientId,
      clientSecret: keycloakClientSecret,
      profile(profile) {
        return {
          id: profile.sub ?? profile.id ?? profile.email ?? "",
          name: profile.preferred_username ?? profile.name ?? profile.email ?? undefined,
          email: profile.email ?? undefined,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }

      if (profile) {
        token.roles = extractRoles(profile as KeycloakAccessProfile);
      }

      token.roles = normalizeRoles(token.roles as string[] | undefined);
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.roles = Array.isArray(token.roles) ? normalizeRoles(token.roles) : [];
      }

      if (typeof token.accessToken === "string") {
        session.accessToken = token.accessToken;
      }

      return session;
    },
  },
  secret: nextAuthSecret,
};

export const getServerAuthSession = () => getServerSession(authOptions);

function requireEnv(name: string, fallback?: string) {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`Missing environment variable: ${name}`);
  }
  return value;
}
