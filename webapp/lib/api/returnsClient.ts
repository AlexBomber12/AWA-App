import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";

const RETURNS_BFF_ENDPOINT = "/api/bff/returns";

export const RETURNS_SORT_OPTIONS = [
  "refund_desc",
  "refund_asc",
  "qty_desc",
  "qty_asc",
  "asin_asc",
  "asin_desc",
] as const;
export type ReturnsSort = (typeof RETURNS_SORT_OPTIONS)[number];

export type ReturnsFilters = {
  dateFrom?: string | null;
  dateTo?: string | null;
  vendor?: string | null;
  asin?: string | null;
};

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

const appendFilters = (filters: ReturnsFilters | undefined, query: URLSearchParams) => {
  if (!filters) {
    return;
  }
  const safeTrim = (value: string | null | undefined) => value?.trim();
  const dateFrom = safeTrim(filters.dateFrom ?? undefined);
  const dateTo = safeTrim(filters.dateTo ?? undefined);
  const vendor = safeTrim(filters.vendor ?? undefined);
  const asin = safeTrim(filters.asin ?? undefined);

  if (dateFrom) {
    query.set("filter[date_from]", dateFrom);
  }
  if (dateTo) {
    query.set("filter[date_to]", dateTo);
  }
  if (vendor) {
    query.set("filter[vendor]", vendor);
  }
  if (asin) {
    query.set("filter[asin]", asin);
  }
};

const buildListQuery = (params: ReturnsListParams): string => {
  const query = new URLSearchParams();
  query.set("resource", "list");
  query.set("page", String(params.page));
  query.set("page_size", String(params.pageSize));
  if (params.sort && RETURNS_SORT_OPTIONS.includes(params.sort)) {
    query.set("sort", params.sort);
  }
  appendFilters(params.filters, query);
  return query.toString();
};

const buildStatsQuery = (filters?: ReturnsFilters): string => {
  const query = new URLSearchParams();
  query.set("resource", "stats");
  appendFilters(filters, query);
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
