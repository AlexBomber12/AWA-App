"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, type ReactNode } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

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
  resource?: Resource;
  action?: Action;
  requiredRoles?: Role[];
  fallback?: ReactNode;
  redirectTo?: string;
  children: ReactNode;
};

export function PermissionGuard({ resource, action, requiredRoles, fallback = null, redirectTo, children }: PermissionGuardProps) {
  const { can, hasRole, roles } = usePermissions();
  const router = useRouter();

  const hasRequiredRole = requiredRoles?.length
    ? requiredRoles.some((role) => hasRole(role))
    : true;
  const canAccess = resource && action ? can({ resource, action }) : true;
  const isAllowed = hasRequiredRole && canAccess;

  useEffect(() => {
    if (!isAllowed && redirectTo) {
      router.replace(redirectTo);
    }
  }, [isAllowed, redirectTo, router]);

  return (isAllowed ? children : fallback) ?? null;
}

export const useHasPermission = (params: { resource?: Resource; action?: Action; requiredRoles?: Role[] }) => {
  const { can, hasRole } = usePermissions();
  const meetsRole = params.requiredRoles?.length ? params.requiredRoles.some((role) => hasRole(role)) : true;
  const meetsPermission = params.resource && params.action ? can({ resource: params.resource, action: params.action }) : true;
  return meetsRole && meetsPermission;
};

export type { Role, Resource, Action } from "./server";
export { can, getUserRolesFromSession, hasRole, KNOWN_ROLES } from "./server";
