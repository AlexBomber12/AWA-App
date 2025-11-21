import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";
import {
  RETURNS_SORT_OPTIONS,
  RETURNS_TABLE_DEFAULTS,
  serializeReturnsSearchParams,
  type ReturnsSort,
  type ReturnsTableFilters,
  type ReturnsTableState,
} from "@/lib/tableState/returns";

const RETURNS_BFF_ENDPOINT = "/api/bff/returns";

export type ReturnsFilters = ReturnsTableFilters;

export type ReturnsRow = {
  asin: string;
  qty: number;
  refundAmount: number;
  avgRefundPerUnit: number;
};

export type ReturnsListResponse = {
  items: ReturnsRow[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
};

export type ReturnsSummary = {
  totalAsins: number;
  totalUnits: number;
  totalRefundAmount: number;
  avgRefundPerUnit: number;
  topAsin?: string | null;
  topAsinRefundAmount?: number | null;
};

export type ReturnsListParams = {
  page: number;
  pageSize: number;
  sort?: ReturnsSort;
  filters?: ReturnsFilters;
};

export type { ReturnsSort };

const buildListQuery = (params: ReturnsListParams): string => {
  const sort = params.sort && RETURNS_SORT_OPTIONS.includes(params.sort)
    ? params.sort
    : RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc";

  const state: ReturnsTableState = {
    page: params.page,
    pageSize: params.pageSize,
    sort,
    filters: params.filters ?? RETURNS_TABLE_DEFAULTS.filters ?? {},
  };

  const query = serializeReturnsSearchParams(state);
  query.set("resource", "list");
  return query.toString();
};

const buildStatsQuery = (filters?: ReturnsFilters): string => {
  const state: ReturnsTableState = {
    page: 1,
    pageSize: 1,
    sort: RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc",
    filters: filters ?? RETURNS_TABLE_DEFAULTS.filters ?? {},
  };
  const query = serializeReturnsSearchParams(state);
  query.set("resource", "stats");
  return query.toString();
};

export async function getReturnsList(params: ReturnsListParams): Promise<ReturnsListResponse> {
  const query = buildListQuery(params);
  const response = await fetchFromBff<ReturnsListResponse>(`${RETURNS_BFF_ENDPOINT}?${query}`);
  return response;
}

export async function getReturnsStats(filters?: ReturnsFilters): Promise<ReturnsSummary> {
  const query = buildStatsQuery(filters);
  return fetchFromBff<ReturnsSummary>(`${RETURNS_BFF_ENDPOINT}?${query}`);
}

export const getReturnsListQueryKey = (params: ReturnsListParams) =>
  ["returns", "list", buildListQuery(params)] as const;

export const getReturnsStatsQueryKey = (filters?: ReturnsFilters) =>
  ["returns", "stats", buildStatsQuery(filters)] as const;

type UseReturnsListQueryOptions = Omit<
  UseApiQueryOptions<ReturnsListResponse, ApiError, ReturnsListResponse, ReturnType<typeof getReturnsListQueryKey>>,
  "queryKey" | "queryFn"
>;

type UseReturnsStatsQueryOptions = Omit<
  UseApiQueryOptions<ReturnsSummary, ApiError, ReturnsSummary, ReturnType<typeof getReturnsStatsQueryKey>>,
  "queryKey" | "queryFn"
>;

export function useReturnsListQuery(params: ReturnsListParams, options?: UseReturnsListQueryOptions) {
  return useApiQuery<ReturnsListResponse, ApiError, ReturnsListResponse, ReturnType<typeof getReturnsListQueryKey>>({
    queryKey: getReturnsListQueryKey(params),
    queryFn: () => getReturnsList(params),
    ...options,
  });
}

export function useReturnsStatsQuery(filters?: ReturnsFilters, options?: UseReturnsStatsQueryOptions) {
  return useApiQuery<ReturnsSummary, ApiError, ReturnsSummary, ReturnType<typeof getReturnsStatsQueryKey>>({
    queryKey: getReturnsStatsQueryKey(filters),
    queryFn: () => getReturnsStats(filters),
    ...options,
  });
}
