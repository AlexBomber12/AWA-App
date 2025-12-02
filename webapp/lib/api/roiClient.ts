import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";
import type { BffListResponse, RoiItem } from "@/lib/api/bffTypes";
import {
  ROI_TABLE_DEFAULTS,
  serializeRoiSearchParams,
  type RoiSort,
  type RoiTableFilters,
  type RoiTableState,
} from "@/lib/tableState/roi";

export type RoiListParams = {
  page: number;
  pageSize: number;
  sort?: RoiSort;
  filters?: RoiTableFilters;
};

export type RoiPageResponse = BffListResponse<RoiItem>;
export type RoiRow = RoiItem;

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

export async function getRoiPage(params: RoiListParams): Promise<RoiPageResponse> {
  const query = buildBffListQuery(params);
  const path = query ? `${ROI_BFF_ENDPOINT}?${query}` : ROI_BFF_ENDPOINT;
  return fetchFromBff<RoiPageResponse>(path);
}

export const getRoiListQueryKey = (params: RoiListParams) =>
  ["roi", buildBffListQuery(params)] as const;

type UseRoiListQueryOptions = Omit<
  UseApiQueryOptions<RoiPageResponse, ApiError, RoiPageResponse, ReturnType<typeof getRoiListQueryKey>>,
  "queryKey" | "queryFn"
>;

function useRoiQuery(params: RoiListParams, options?: UseRoiListQueryOptions) {
  return useApiQuery<RoiPageResponse, ApiError, RoiPageResponse, ReturnType<typeof getRoiListQueryKey>>({
    queryKey: getRoiListQueryKey(params),
    queryFn: () => getRoiPage(params),
    ...options,
  });
}

export const roiClient = {
  getRoiPage,
  getRoiList: getRoiPage,
  getRoiListQueryKey,
  useRoiQuery,
  useRoiListQuery: useRoiQuery,
};
