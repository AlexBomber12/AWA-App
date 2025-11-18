import type { Session } from "next-auth";

export type Role = "viewer" | "ops" | "admin";
export type Resource =
  | "dashboard"
  | "roi"
  | "sku"
  | "ingest"
  | "returns"
  | "inbox"
  | "decision"
  | "settings";
export type Action = "view" | "edit" | "approve" | "ingest" | "configure";

export const KNOWN_ROLES: Role[] = ["viewer", "ops", "admin"];

type ResourceAcl = Partial<Record<Action, Role[]>>;

const ACL: Record<Resource, ResourceAcl> = {
  dashboard: {
    view: ["viewer", "ops", "admin"],
  },
  roi: {
    view: ["viewer", "ops", "admin"],
    edit: ["ops", "admin"],
    approve: ["ops", "admin"],
  },
  sku: {
    view: ["viewer", "ops", "admin"],
    edit: ["ops", "admin"],
  },
  ingest: {
    view: ["ops", "admin"],
    ingest: ["ops", "admin"],
  },
  returns: {
    view: ["viewer", "ops", "admin"],
  },
  inbox: {
    view: ["ops", "admin"],
    configure: ["ops", "admin"],
  },
  decision: {
    view: ["admin"],
    configure: ["admin"],
  },
  settings: {
    view: ["ops", "admin"],
    configure: ["admin"],
  },
};

type CanCheck = {
  resource: Resource;
  action: Action;
  roles: Role[];
};

const filterRoles = (roles: string[]): Role[] => {
  const unique = new Set<Role>();
  roles.forEach((role) => {
    if (KNOWN_ROLES.includes(role as Role)) {
      unique.add(role as Role);
    }
  });
  return Array.from(unique);
};

export function getUserRolesFromSession(session: Session | null): Role[] {
  if (!session?.user?.roles) {
    return [];
  }

  return filterRoles(session.user.roles);
}

export function hasRole(role: Role, roles: Role[]): boolean {
  return roles.includes(role);
}

export function can({ resource, action, roles }: CanCheck): boolean {
  const allowedRoles = ACL[resource]?.[action];
  if (!allowedRoles) {
    return false;
  }

  return roles.some((role) => allowedRoles.includes(role));
}
