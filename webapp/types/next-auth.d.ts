import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: DefaultSession["user"] & {
      roles: string[];
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    roles?: string[];
    realm_access?: {
      roles?: string[];
    };
    resource_access?: Record<string, { roles?: string[] } | null | undefined>;
  }
}
