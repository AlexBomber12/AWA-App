import { fetchFromApi } from "@/lib/api/fetchFromApi";

import type { components } from "./types.generated";

type RoiListResponse = components["schemas"]["RoiListResponse"];
type RoiApprovalResponse = components["schemas"]["RoiApprovalResponse"];

export type RoiListParams = {
  page?: number;
  pageSize?: number;
  sort?: string | null;
  roiMin?: number | null;
  roiMax?: number | null;
  vendor?: number | string | null;
  category?: string | null;
  search?: string | null;
};

export type RoiBulkApprovePayload = {
  asins: string[];
};

const buildQueryString = (params: RoiListParams): string => {
  const query = new URLSearchParams();
  if (typeof params.page === "number" && Number.isFinite(params.page) && params.page > 0) {
    query.set("page", String(Math.floor(params.page)));
  }
  if (typeof params.pageSize === "number" && Number.isFinite(params.pageSize) && params.pageSize > 0) {
    query.set("page_size", String(Math.floor(params.pageSize)));
  }
  if (params.sort) {
    query.set("sort", params.sort);
  }
  if (typeof params.roiMin === "number" && Number.isFinite(params.roiMin)) {
    query.set("roi_min", String(params.roiMin));
  }
  if (typeof params.roiMax === "number" && Number.isFinite(params.roiMax)) {
    query.set("roi_max", String(params.roiMax));
  }
  if (params.vendor !== undefined && params.vendor !== null && params.vendor !== "") {
    query.set("vendor", String(params.vendor));
  }
  if (params.category) {
    query.set("category", params.category);
  }
  if (params.search) {
    query.set("search", params.search);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
};

async function listRoiRows(params: RoiListParams = {}): Promise<RoiListResponse> {
  const query = buildQueryString(params);
  return fetchFromApi<RoiListResponse>(`/roi${query}`);
}

async function bulkApproveRoi(payload: RoiBulkApprovePayload): Promise<RoiApprovalResponse> {
  return fetchFromApi<RoiApprovalResponse>("/roi-review/approve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export const roiClient = {
  listRoiRows,
  bulkApproveRoi,
};
