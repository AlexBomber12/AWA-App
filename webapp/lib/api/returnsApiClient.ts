import { fetchFromApi } from "@/lib/api/fetchFromApi";
import {
  RETURNS_TABLE_DEFAULTS,
  RETURNS_SORT_OPTIONS,
  mergeReturnsTableStateWithDefaults,
  type ReturnsSort,
  type ReturnsTableFilters,
} from "@/lib/tableState/returns";

import type { paths } from "./types.generated";

type ReturnsStatsResponse = paths["/stats/returns"]["get"]["responses"]["200"]["content"]["application/json"];

export type ReturnsApiParams = {
  page?: number;
  pageSize?: number;
  sort?: ReturnsSort;
  filters?: ReturnsTableFilters;
};

const appendFilters = (filters: ReturnsTableFilters | undefined, query: URLSearchParams) => {
  if (!filters) {
    return;
  }

  const trim = (value?: string | null) => value?.trim();

  const dateFrom = trim(filters.dateFrom);
  const dateTo = trim(filters.dateTo);
  const vendor = trim(filters.vendor);
  const asin = trim(filters.asin);

  if (dateFrom) {
    query.set("date_from", dateFrom);
  }
  if (dateTo) {
    query.set("date_to", dateTo);
  }
  if (vendor) {
    query.set("vendor", vendor);
  }
  if (asin) {
    query.set("asin", asin);
  }
};

const buildQuery = (params: ReturnsApiParams): string => {
  const state = mergeReturnsTableStateWithDefaults({
    page: params.page ?? RETURNS_TABLE_DEFAULTS.page,
    pageSize: params.pageSize ?? RETURNS_TABLE_DEFAULTS.pageSize,
    sort: params.sort ?? RETURNS_TABLE_DEFAULTS.sort,
    filters: params.filters,
  });

  const query = new URLSearchParams();
  query.set("page", String(state.page));
  query.set("page_size", String(state.pageSize));

  if (state.sort && RETURNS_SORT_OPTIONS.includes(state.sort)) {
    query.set("sort", state.sort);
  }

  appendFilters(state.filters, query);

  return query.toString();
};

const buildPath = (params: ReturnsApiParams): string => {
  const query = buildQuery(params);
  return query ? `/stats/returns?${query}` : "/stats/returns";
};

export const returnsApiClient = {
  async fetchStats(params: ReturnsApiParams): Promise<ReturnsStatsResponse> {
    const path = buildPath(params);
    return fetchFromApi<ReturnsStatsResponse>(path);
  },
};
