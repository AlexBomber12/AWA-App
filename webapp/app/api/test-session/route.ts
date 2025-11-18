import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { KNOWN_ROLES, type Role } from "@/lib/permissions/server";

const COOKIE_NAME = "webapp-test-session";

const normalizeRoles = (input: unknown): Role[] => {
  if (Array.isArray(input)) {
    return input
      .map((role) => (typeof role === "string" ? role.trim() : ""))
      .filter((role): role is Role => KNOWN_ROLES.includes(role as Role));
  }

  if (typeof input === "string") {
    return normalizeRoles(
      input
        .split(",")
        .map((role) => role.trim())
        .filter(Boolean)
    );
  }

  return [];
};

const isTestSessionEnabled = () => process.env.NODE_ENV !== "production";

export async function POST(request: NextRequest) {
  if (!isTestSessionEnabled()) {
    return NextResponse.json(
      { code: "NOT_FOUND", message: "Test sessions are disabled in production." },
      { status: 404 }
    );
  }

  const body = await request.json().catch(() => ({}));
  const roles = normalizeRoles(body.roles) ?? [];
  const fallbackRoles: Role[] = ["admin", "ops", "viewer"];
  const safeRoles = roles.length ? roles : fallbackRoles;

  cookies().set({
    name: COOKIE_NAME,
    value: JSON.stringify({ roles: safeRoles }),
    sameSite: "lax",
    httpOnly: true,
    secure: process.env.NODE_ENV !== "development",
    path: "/",
  });

  return NextResponse.json({ ok: true, roles: safeRoles });
}

export async function DELETE() {
  if (!isTestSessionEnabled()) {
    return NextResponse.json({ ok: true });
  }
  cookies().delete(COOKIE_NAME);
  return NextResponse.json({ ok: true });
}

const methodNotAllowed = () =>
  NextResponse.json(
    { code: "METHOD_NOT_ALLOWED", message: "Only POST and DELETE are supported." },
    {
      status: 405,
      headers: {
        Allow: "POST, DELETE",
      },
    }
  );

export const GET = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
