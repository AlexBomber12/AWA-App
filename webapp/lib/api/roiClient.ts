import { fetchFromApi } from "@/lib/api/fetchFromApi";

import type { components } from "./types.generated";

type RoiRow = components["schemas"]["RoiRow"];
type RoiApprovalResponse = components["schemas"]["RoiApprovalResponse"];

export type RoiListParams = {
  roiMin?: number | null;
  vendor?: number | string | null;
  category?: string | null;
};

export type RoiBulkApprovePayload = {
  asins: string[];
};

const buildQueryString = (params: RoiListParams): string => {
  const query = new URLSearchParams();
  if (typeof params.roiMin === "number" && Number.isFinite(params.roiMin)) {
    query.set("roi_min", String(params.roiMin));
  }
  if (params.vendor !== undefined && params.vendor !== null && params.vendor !== "") {
    query.set("vendor", String(params.vendor));
  }
  if (params.category) {
    query.set("category", params.category);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
};

async function listRoiRows(params: RoiListParams = {}): Promise<RoiRow[]> {
  const query = buildQueryString(params);
  return fetchFromApi<RoiRow[]>(`/roi${query}`);
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
