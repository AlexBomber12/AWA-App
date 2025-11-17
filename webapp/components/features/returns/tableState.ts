import { RETURNS_SORT_OPTIONS, type ReturnsFilters, type ReturnsSort } from "@/lib/api/returnsClient";
import type { TableState, TableStateDefaults } from "@/lib/tableState";

export type ReturnsTableFilters = ReturnsFilters;
export type ReturnsTableState = TableState<ReturnsSort, ReturnsTableFilters>;

const DEFAULT_FILTERS: ReturnsTableFilters = {
  dateFrom: "",
  dateTo: "",
  vendor: "",
  asin: "",
};

export const RETURNS_TABLE_DEFAULTS: TableStateDefaults<ReturnsSort, ReturnsTableFilters> = {
  page: 1,
  pageSize: 25,
  sort: "refund_desc",
  filters: DEFAULT_FILTERS,
};

const parseNumber = (value: string | null): number | undefined => {
  if (!value) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseSort = (value: string | null): ReturnsSort | undefined => {
  if (value && RETURNS_SORT_OPTIONS.includes(value as ReturnsSort)) {
    return value as ReturnsSort;
  }
  return undefined;
};

const parseFilters = (params: URLSearchParams): ReturnsTableFilters | undefined => {
  const entries: ReturnsTableFilters = {};
  const dateFrom = params.get("filter[date_from]");
  if (dateFrom) {
    entries.dateFrom = dateFrom;
  }
  const dateTo = params.get("filter[date_to]");
  if (dateTo) {
    entries.dateTo = dateTo;
  }
  const vendor = params.get("filter[vendor]");
  if (vendor) {
    entries.vendor = vendor;
  }
  const asin = params.get("filter[asin]");
  if (asin) {
    entries.asin = asin;
  }
  return Object.keys(entries).length ? entries : undefined;
};

export const parseReturnsSearchParams = (
  params: URLSearchParams
): Partial<TableState<ReturnsSort, ReturnsTableFilters>> => {
  const page = parseNumber(params.get("page"));
  const pageSize = parseNumber(params.get("page_size"));
  const sort = parseSort(params.get("sort"));
  const filters = parseFilters(params);

  return {
    page,
    pageSize,
    sort,
    filters,
  };
};

const normalizeFilterValue = (value?: string | null) => {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

export const serializeReturnsSearchParams = (state: ReturnsTableState): URLSearchParams => {
  const params = new URLSearchParams();
  params.set("page", String(state.page));
  params.set("page_size", String(state.pageSize));
  if (state.sort) {
    params.set("sort", state.sort);
  }

  const filters = state.filters ?? DEFAULT_FILTERS;
  const dateFrom = normalizeFilterValue(filters.dateFrom);
  const dateTo = normalizeFilterValue(filters.dateTo);
  const vendor = normalizeFilterValue(filters.vendor);
  const asin = normalizeFilterValue(filters.asin);

  if (dateFrom) {
    params.set("filter[date_from]", dateFrom);
  }
  if (dateTo) {
    params.set("filter[date_to]", dateTo);
  }
  if (vendor) {
    params.set("filter[vendor]", vendor);
  }
  if (asin) {
    params.set("filter[asin]", asin);
  }

  return params;
};
