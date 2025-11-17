import type { components } from "@/lib/api/types.generated";

export type RoiRow = components["schemas"]["RoiRow"];
export type RoiApprovalResponse = components["schemas"]["RoiApprovalResponse"];

export type RoiListResponse = {
  items: RoiRow[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
};
