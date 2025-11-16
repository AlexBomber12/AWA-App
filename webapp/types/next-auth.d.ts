import "next-auth";
import "next-auth/jwt";

import type { DefaultSession } from "next-auth";

import type { Role } from "@/lib/permissions";

declare module "next-auth" {
  interface Session {
    user: {
      roles: Role[];
    } & DefaultSession["user"];
    accessToken?: string;
    error?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    roles?: Role[];
    accessToken?: string;
  }
}
