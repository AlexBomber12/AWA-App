"use client";

import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { useSession } from "next-auth/react";

import {
  can,
  getUserRolesFromSession,
  hasRole,
  type Action,
  type Resource,
  type Role,
} from "./server";

type CanWithOptionalRoles = {
  resource: Resource;
  action: Action;
  roles?: Role[];
};

type UsePermissionsResult = {
  roles: Role[];
  can: (params: CanWithOptionalRoles) => boolean;
  hasRole: (role: Role, rolesOverride?: Role[]) => boolean;
};

const InitialRolesContext = createContext<Role[]>([]);

export const PermissionsProvider = ({
  roles,
  children,
}: {
  roles: Role[];
  children: ReactNode;
}) => (
  <InitialRolesContext.Provider value={roles}>{children}</InitialRolesContext.Provider>
);

export function usePermissions(): UsePermissionsResult {
  const { data: session } = useSession();
  const seedRoles = useContext(InitialRolesContext);

  const sessionRoles = useMemo(() => getUserRolesFromSession(session ?? null), [session]);
  const roles = sessionRoles.length > 0 ? sessionRoles : seedRoles;

  const canWithRoles = useCallback(
    ({ roles: overrideRoles, ...rest }: CanWithOptionalRoles) => {
      const targetRoles = overrideRoles ?? roles;
      return can({
        ...rest,
        roles: targetRoles,
      });
    },
    [roles]
  );

  const hasRoleWithOverride = useCallback(
    (role: Role, rolesOverride?: Role[]) => hasRole(role, rolesOverride ?? roles),
    [roles]
  );

  return {
    roles,
    can: canWithRoles,
    hasRole: hasRoleWithOverride,
  };
}

type PermissionGuardProps = {
  resource: Resource;
  action: Action;
  fallback?: ReactNode;
  children: ReactNode;
};

export function PermissionGuard({ resource, action, fallback = null, children }: PermissionGuardProps) {
  const { can } = usePermissions();
  const isAllowed = can({ resource, action });

  return (isAllowed ? children : fallback) ?? null;
}

export type { Role, Resource, Action } from "./server";
export { can, getUserRolesFromSession, hasRole, KNOWN_ROLES } from "./server";
