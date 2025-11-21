import { fetchFromApi } from "@/lib/api/fetchFromApi";
import {
  ROI_MAX_PAGE_SIZE,
  ROI_SORT_OPTIONS,
  ROI_TABLE_DEFAULTS,
  mergeRoiTableStateWithDefaults,
  type RoiSort,
  type RoiTableFilters,
  type RoiTableState,
} from "@/lib/tableState/roi";

import type { paths } from "./types.generated";

export type RoiApiListResponse = paths["/roi"]["get"]["responses"]["200"]["content"]["application/json"];
export type RoiApprovalResponse = paths["/roi-review/approve"]["post"]["responses"]["200"]["content"]["application/json"];

export type RoiApiListParams = {
  page?: number;
  pageSize?: number;
  sort?: RoiSort | null;
  filters?: RoiTableFilters;
  roiMax?: number | null;
};

export type RoiBulkApprovePayload = {
  asins: string[];
};

const buildQueryString = (params: RoiApiListParams): string => {
  const state: RoiTableState = mergeRoiTableStateWithDefaults({
    page: params.page ?? ROI_TABLE_DEFAULTS.page,
    pageSize: params.pageSize ?? ROI_TABLE_DEFAULTS.pageSize,
    sort: params.sort ?? ROI_TABLE_DEFAULTS.sort,
    filters: params.filters,
  });

  const query = new URLSearchParams();
  query.set("page", String(state.page));
  query.set("page_size", String(Math.min(state.pageSize, ROI_MAX_PAGE_SIZE)));

  if (state.sort && ROI_SORT_OPTIONS.includes(state.sort)) {
    query.set("sort", state.sort);
  }

  const filters = state.filters ?? {};

  if (typeof filters.roiMin === "number" && Number.isFinite(filters.roiMin)) {
    query.set("roi_min", String(filters.roiMin));
  }

  if (typeof params.roiMax === "number" && Number.isFinite(params.roiMax)) {
    query.set("roi_max", String(params.roiMax));
  }

  const vendor = filters.vendor?.trim();
  if (vendor) {
    query.set("vendor", vendor);
  }

  if (filters.category) {
    query.set("category", filters.category);
  }

  if (filters.search) {
    query.set("search", filters.search);
  }

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
};

async function listRoiRows(params: RoiApiListParams = {}): Promise<RoiApiListResponse> {
  const query = buildQueryString(params);
  return fetchFromApi<RoiApiListResponse>(`/roi${query}`);
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

export const roiApiClient = {
  listRoiRows,
  bulkApproveRoi,
};
