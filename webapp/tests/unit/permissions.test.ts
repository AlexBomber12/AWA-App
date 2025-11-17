import type { Session } from "next-auth";

import { can, getUserRolesFromSession } from "@/lib/permissions";

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
    const session = buildSession(["viewer", "invalid", "admin"]);

    expect(getUserRolesFromSession(session)).toEqual(["viewer", "admin"]);
  });

  it("returns empty roles when the session is missing", () => {
    expect(getUserRolesFromSession(null)).toEqual([]);
  });

  it("evaluates ACL via can()", () => {
    expect(can({ resource: "dashboard", action: "view", roles: ["viewer"] })).toBe(true);
    expect(can({ resource: "inbox", action: "view", roles: ["ops"] })).toBe(true);
    expect(can({ resource: "decision", action: "configure", roles: ["admin"] })).toBe(true);
  });
});
