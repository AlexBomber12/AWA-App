import type { TableState, TableStateDefaults } from "@/lib/tableState";

export const ROI_SORT_OPTIONS = [
  "roi_pct_desc",
  "roi_pct_asc",
  "asin_asc",
  "asin_desc",
  "margin_desc",
  "margin_asc",
  "vendor_asc",
  "vendor_desc",
] as const;

export type RoiSort = (typeof ROI_SORT_OPTIONS)[number];

export type RoiTableFilters = {
  roiMin?: number | null;
  vendor?: string;
  category?: string;
  search?: string;
  observeOnly?: boolean;
};

export type RoiTableState = TableState<RoiSort, RoiTableFilters>;

const DEFAULT_FILTERS: RoiTableFilters = {
  roiMin: 0,
  vendor: "",
  category: "",
  search: "",
  observeOnly: false,
};

export const ROI_TABLE_DEFAULTS: TableStateDefaults<RoiSort, RoiTableFilters> = {
  page: 1,
  pageSize: 50,
  sort: "roi_pct_desc",
  filters: DEFAULT_FILTERS,
};

const parseNumber = (value: string | null): number | undefined => {
  if (!value) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseBoolean = (value: string | null): boolean | undefined => {
  if (!value) {
    return undefined;
  }
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return undefined;
};

const parseSort = (value: string | null): RoiSort | undefined => {
  if (value && ROI_SORT_OPTIONS.includes(value as RoiSort)) {
    return value as RoiSort;
  }
  return undefined;
};

export const parseRoiSearchParams = (params: URLSearchParams): Partial<RoiTableState> => {
  const page = parseNumber(params.get("page"));
  const pageSize = parseNumber(params.get("page_size"));
  const sort = parseSort(params.get("sort"));

  const filters: Partial<RoiTableFilters> = {};

  const roiMin = parseNumber(params.get("filter[roi_min]"));
  if (roiMin !== undefined) {
    filters.roiMin = roiMin;
  }

  const vendor = params.get("filter[vendor]");
  if (vendor) {
    filters.vendor = vendor;
  }

  const category = params.get("filter[category]");
  if (category) {
    filters.category = category;
  }

  const search = params.get("filter[search]");
  if (search) {
    filters.search = search;
  }

  const observeOnly = parseBoolean(params.get("filter[observe_only]"));
  if (observeOnly !== undefined) {
    filters.observeOnly = observeOnly;
  }

  return {
    page,
    pageSize,
    sort,
    filters: Object.keys(filters).length ? (filters as RoiTableFilters) : undefined,
  };
};

export const serializeRoiSearchParams = (state: RoiTableState): URLSearchParams => {
  const params = new URLSearchParams();
  params.set("page", String(state.page));
  params.set("page_size", String(state.pageSize));

  if (state.sort) {
    params.set("sort", state.sort);
  }

  const filters = state.filters ?? DEFAULT_FILTERS;

  if (typeof filters.roiMin === "number" && Number.isFinite(filters.roiMin)) {
    params.set("filter[roi_min]", String(filters.roiMin));
  }

  if (filters.vendor) {
    params.set("filter[vendor]", filters.vendor);
  }

  if (filters.category) {
    params.set("filter[category]", filters.category);
  }

  if (filters.search) {
    params.set("filter[search]", filters.search);
  }

  if (filters.observeOnly) {
    params.set("filter[observe_only]", "true");
  }

  return params;
};

export const mergeRoiTableStateWithDefaults = (
  partial?: Partial<RoiTableState>
): RoiTableState => {
  const normalizePositive = (value: number | undefined, fallback: number) => {
    if (!value || !Number.isFinite(value)) {
      return fallback;
    }
    const rounded = Math.floor(value);
    return rounded > 0 ? rounded : fallback;
  };

  return {
    page: normalizePositive(partial?.page, ROI_TABLE_DEFAULTS.page),
    pageSize: normalizePositive(partial?.pageSize, ROI_TABLE_DEFAULTS.pageSize),
    sort: partial?.sort ?? ROI_TABLE_DEFAULTS.sort,
    filters: {
      ...DEFAULT_FILTERS,
      ...(partial?.filters ?? {}),
    },
  };
};
