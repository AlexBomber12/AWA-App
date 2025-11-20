import { RETURNS_SORT_OPTIONS, type ReturnsFilters, type ReturnsSort } from "@/lib/api/returnsClient";
import { parsePositiveInt, parseSort, parseString } from "@/lib/parsers";
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

const parseFilters = (params: URLSearchParams): ReturnsTableFilters | undefined => {
  const entries: ReturnsTableFilters = {};
  const dateFrom = parseString(params.get("filter[date_from]"));
  if (dateFrom !== undefined) {
    entries.dateFrom = dateFrom;
  }
  const dateTo = parseString(params.get("filter[date_to]"));
  if (dateTo !== undefined) {
    entries.dateTo = dateTo;
  }
  const vendor = parseString(params.get("filter[vendor]"));
  if (vendor !== undefined) {
    entries.vendor = vendor;
  }
  const asin = parseString(params.get("filter[asin]"));
  if (asin !== undefined) {
    entries.asin = asin;
  }
  return Object.keys(entries).length ? entries : undefined;
};

export const parseReturnsSearchParams = (
  params: URLSearchParams
): Partial<TableState<ReturnsSort, ReturnsTableFilters>> => {
  const page = parsePositiveInt(params.get("page"), RETURNS_TABLE_DEFAULTS.page);
  const pageSize = parsePositiveInt(params.get("page_size"), RETURNS_TABLE_DEFAULTS.pageSize);
  const sort = parseSort(params.get("sort"), RETURNS_SORT_OPTIONS, RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc");
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
