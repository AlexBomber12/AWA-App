import NextAuth from "next-auth";
import { NextResponse } from "next/server";

import { getAuthOptions } from "@/lib/auth";

const handler = (req: Parameters<typeof NextAuth>[0], ctx: Parameters<typeof NextAuth>[1]) => {
  const options = getAuthOptions();
  if (!options) {
    return NextResponse.json(
      { code: "AUTH_CONFIG_MISSING", message: "Keycloak / NextAuth configuration is missing." },
      { status: 500 }
    );
  }
  return NextAuth(req, ctx, options);
};

export { handler as GET, handler as POST };
