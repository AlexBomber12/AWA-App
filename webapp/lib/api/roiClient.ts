import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";
import {
  ROI_TABLE_DEFAULTS,
  serializeRoiSearchParams,
  type RoiSort,
  type RoiTableFilters,
  type RoiTableState,
} from "@/lib/tableState/roi";

import type { components } from "./types.generated";

export type RoiRow = components["schemas"]["RoiRow"];

export type RoiTableResponse = {
  items: RoiRow[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
};

export type RoiListParams = {
  page: number;
  pageSize: number;
  sort?: RoiSort;
  filters?: RoiTableFilters;
};

const ROI_BFF_ENDPOINT = "/api/bff/roi";

const buildBffListQuery = (params: RoiListParams): string => {
  const state: RoiTableState = {
    page: params.page,
    pageSize: params.pageSize,
    sort: params.sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc",
    filters: params.filters ?? ROI_TABLE_DEFAULTS.filters ?? {},
  };
  return serializeRoiSearchParams(state).toString();
};

async function getRoiList(params: RoiListParams): Promise<RoiTableResponse> {
  const query = buildBffListQuery(params);
  const path = query ? `${ROI_BFF_ENDPOINT}?${query}` : ROI_BFF_ENDPOINT;
  return fetchFromBff<RoiTableResponse>(path);
}

export const getRoiListQueryKey = (params: RoiListParams) =>
  ["roi", buildBffListQuery(params)] as const;

type UseRoiListQueryOptions = Omit<
  UseApiQueryOptions<RoiTableResponse, ApiError, RoiTableResponse, ReturnType<typeof getRoiListQueryKey>>,
  "queryKey" | "queryFn"
>;

function useRoiListQuery(params: RoiListParams, options?: UseRoiListQueryOptions) {
  return useApiQuery<RoiTableResponse, ApiError, RoiTableResponse, ReturnType<typeof getRoiListQueryKey>>({
    queryKey: getRoiListQueryKey(params),
    queryFn: () => getRoiList(params),
    ...options,
  });
}

export const roiClient = {
  getRoiList,
  getRoiListQueryKey,
  useRoiListQuery,
};
