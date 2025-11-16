import { getServerSession, type NextAuthOptions } from "next-auth";
import type { Account } from "next-auth";
import KeycloakProvider, { type KeycloakProfile } from "next-auth/providers/keycloak";
import type { JWT } from "next-auth/jwt";

import { KNOWN_ROLES, type Role } from "@/lib/permissions";

type KeycloakAccessProfile = KeycloakProfile & {
  roles?: string[];
  realm_access?: { roles?: string[] };
  resource_access?: Record<string, { roles?: string[] }>;
};

type AuthEnvironment = {
  issuer: string;
  clientId: string;
  clientSecret: string;
  nextAuthSecret: string;
};

type TokenWithKeycloak = JWT & {
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number;
  tokenRefreshError?: string;
};

type KeycloakRefreshResponse = {
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  refresh_expires_in?: number;
  error?: string;
  error_description?: string;
};

const ACCESS_TOKEN_EXPIRY_BUFFER_MS = 60_000;

let cachedAuthOptions: NextAuthOptions | null = null;

const toRole = (value: string): value is Role => KNOWN_ROLES.includes(value as Role);

const normalizeRoles = (roles: string[] | undefined): Role[] => {
  if (!Array.isArray(roles)) {
    return [];
  }
  return roles.filter(toRole);
};

const extractRoles = (profile: KeycloakAccessProfile, clientId: string): Role[] => {
  const collected = new Set<string>();

  normalizeRoles(profile.roles).forEach((role) => collected.add(role));

  if (profile.realm_access?.roles) {
    normalizeRoles(profile.realm_access.roles).forEach((role) => collected.add(role));
  }

  const resourceRoles = profile.resource_access?.[clientId]?.roles;
  if (resourceRoles) {
    normalizeRoles(resourceRoles).forEach((role) => collected.add(role));
  }

  return Array.from(collected).filter(toRole);
};

const resolveAuthEnvironment = (): AuthEnvironment | null => {
  const issuer = process.env.KEYCLOAK_ISSUER;
  const clientId = process.env.KEYCLOAK_CLIENT_ID;
  const clientSecret = process.env.KEYCLOAK_CLIENT_SECRET;
  const nextAuthSecret = process.env.NEXTAUTH_SECRET ?? process.env.SECRET;

  if (!issuer || !clientId || !clientSecret || !nextAuthSecret) {
    return null;
  }

  return {
    issuer,
    clientId,
    clientSecret,
    nextAuthSecret,
  };
};

const buildAuthOptions = (env: AuthEnvironment): NextAuthOptions => ({
  session: {
    strategy: "jwt",
  },
  providers: [
    KeycloakProvider({
      issuer: env.issuer,
      clientId: env.clientId,
      clientSecret: env.clientSecret,
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
      const typedToken = token as TokenWithKeycloak;

      if (profile) {
        typedToken.roles = extractRoles(profile as KeycloakAccessProfile, env.clientId);
      }

      if (account) {
        typedToken.accessToken = account.access_token ?? typedToken.accessToken;
        typedToken.refreshToken = account.refresh_token ?? typedToken.refreshToken;
        typedToken.accessTokenExpires = resolveAccessTokenExpiry(account);
        typedToken.tokenRefreshError = undefined;
        return typedToken;
      }

      if (!shouldRefreshToken(typedToken)) {
        return typedToken;
      }

      if (!typedToken.refreshToken) {
        typedToken.accessToken = undefined;
        return typedToken;
      }

      return refreshAccessToken(typedToken, env);
    },
    async session({ session, token }) {
      const typedToken = token as TokenWithKeycloak;

      if (session.user) {
        session.user.roles = Array.isArray(typedToken.roles) ? normalizeRoles(typedToken.roles) : [];
      }

      if (typeof typedToken.accessToken === "string") {
        session.accessToken = typedToken.accessToken;
      }

      if (typedToken.tokenRefreshError) {
        session.error = typedToken.tokenRefreshError;
      }

      return session;
    },
  },
  secret: env.nextAuthSecret,
});

const resolveAccessTokenExpiry = (account: Account): number | undefined => {
  if (typeof account.expires_at === "number") {
    return account.expires_at * 1000;
  }
  if (typeof account.expires_in === "number") {
    return Date.now() + account.expires_in * 1000;
  }
  return undefined;
};

const shouldRefreshToken = (token: TokenWithKeycloak): boolean => {
  if (!token.accessTokenExpires) {
    return true;
  }
  return Date.now() + ACCESS_TOKEN_EXPIRY_BUFFER_MS >= token.accessTokenExpires;
};

const refreshAccessToken = async (token: TokenWithKeycloak, env: AuthEnvironment): Promise<TokenWithKeycloak> => {
  try {
    const response = await fetch(`${env.issuer}/protocol/openid-connect/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: env.clientId,
        client_secret: env.clientSecret,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken ?? "",
      }),
    });

    const tokens = (await response.json()) as KeycloakRefreshResponse;

    if (!response.ok) {
      throw new Error(tokens.error_description ?? tokens.error ?? "Failed to refresh access token.");
    }

    return {
      ...token,
      accessToken: tokens.access_token ?? token.accessToken,
      accessTokenExpires: tokens.expires_in ? Date.now() + tokens.expires_in * 1000 : token.accessTokenExpires,
      refreshToken: tokens.refresh_token ?? token.refreshToken,
      tokenRefreshError: undefined,
    };
  } catch (error) {
    console.error("Failed to refresh Keycloak access token", error);
    return {
      ...token,
      accessToken: undefined,
      tokenRefreshError: "RefreshAccessTokenError",
    };
  }
};

export const getAuthOptions = (): NextAuthOptions | null => {
  if (cachedAuthOptions) {
    return cachedAuthOptions;
  }

  const env = resolveAuthEnvironment();
  if (!env) {
    return null;
  }

  cachedAuthOptions = buildAuthOptions(env);
  return cachedAuthOptions;
};

export const getServerAuthSession = async () => {
  const options = getAuthOptions();
  if (!options) {
    return null;
  }
  return getServerSession(options);
};
