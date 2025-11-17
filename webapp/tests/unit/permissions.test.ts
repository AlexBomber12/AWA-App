import type { Session } from "next-auth";

import { can, getUserRolesFromSession, hasRole } from "@/lib/permissions";

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Test User",
    email: "test@example.com",
    roles,
  },
  expires: "",
});

describe("permissions helpers", () => {
  it("extracts only recognised roles from the session", () => {
    const session = buildSession(["viewer", "invalid", "admin", "viewer"]);

    expect(getUserRolesFromSession(session)).toEqual(["viewer", "admin"]);
  });

  it("returns empty roles when the session is missing", () => {
    expect(getUserRolesFromSession(null)).toEqual([]);
  });

  it.each([
    { resource: "dashboard", action: "view", roles: ["viewer"], expected: true },
    { resource: "roi", action: "approve", roles: ["ops"], expected: true },
    { resource: "roi", action: "approve", roles: ["viewer"], expected: false },
    { resource: "sku", action: "edit", roles: ["ops"], expected: true },
    { resource: "ingest", action: "ingest", roles: ["admin"], expected: true },
    { resource: "ingest", action: "view", roles: ["viewer"], expected: false },
    { resource: "returns", action: "view", roles: ["viewer"], expected: true },
    { resource: "inbox", action: "view", roles: ["viewer"], expected: false },
    { resource: "decision", action: "configure", roles: ["ops"], expected: false },
    { resource: "settings", action: "configure", roles: ["admin"], expected: true },
  ])("evaluates ACL for %s:%s", ({ expected, ...params }) => {
    expect(can(params as Parameters<typeof can>[0])).toBe(expected);
  });

  it("evaluates hasRole helper", () => {
    expect(hasRole("viewer", ["viewer", "ops"])).toBe(true);
    expect(hasRole("admin", ["viewer", "ops"])).toBe(false);
  });
});
