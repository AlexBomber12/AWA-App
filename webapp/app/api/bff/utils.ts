import { NextResponse } from "next/server";

import { isApiError } from "@/lib/api/fetchFromApi";
import { getServerAuthSession } from "@/lib/auth";
import type { PaginationMeta, SortMeta } from "@/lib/api/bffTypes";
import { can, getUserRolesFromSession, type Action, type Resource, type Role } from "@/lib/permissions/server";

type PermissionResult =
  | { ok: true; roles: Role[] }
  | { ok: false; response: NextResponse };

export const errorResponse = (status: number, code: string, message: string, details?: unknown) =>
  NextResponse.json(
    { error: { code, message, status, details } },
    { status }
  );

export const handleApiError = (error: unknown, defaultMessage: string) => {
  if (isApiError(error)) {
    return errorResponse(error.status, error.code, error.message, error.details);
  }

  console.error(defaultMessage, error);
  return errorResponse(500, "BFF_ERROR", defaultMessage);
};

export async function requirePermission(resource: Resource, action: Action): Promise<PermissionResult> {
  const session = await getServerAuthSession();
  if (!session) {
    return {
      ok: false,
      response: errorResponse(401, "UNAUTHORIZED", "Authentication required."),
    };
  }

  const roles = getUserRolesFromSession(session);
  if (!can({ resource, action, roles })) {
    return {
      ok: false,
      response: errorResponse(403, "FORBIDDEN", "You are not allowed to access this resource."),
    };
  }

  return { ok: true, roles };
}

export const buildPaginationMeta = (page: number, pageSize: number, total: number): PaginationMeta => {
  const safePage = Number.isFinite(page) && page > 0 ? Math.floor(page) : 1;
  const safePageSize = Number.isFinite(pageSize) && pageSize > 0 ? Math.floor(pageSize) : 25;
  const safeTotal = Number.isFinite(total) && total >= 0 ? Math.floor(total) : 0;
  const totalPages = Math.max(1, Math.ceil(safeTotal / safePageSize || 1));

  return {
    page: safePage,
    pageSize: safePageSize,
    total: safeTotal,
    totalPages,
  };
};

export const parseSortMeta = (rawSort?: string | null): SortMeta => {
  if (!rawSort) {
    return {};
  }

  const segments = rawSort.split("_");
  if (segments.length < 2) {
    return { sortBy: rawSort, sortDir: "asc" };
  }

  const dirCandidate = segments.pop();
  const sortDir = dirCandidate === "desc" ? "desc" : dirCandidate === "asc" ? "asc" : undefined;
  const sortBy = segments.join("_") || undefined;

  return { sortBy, sortDir };
};
