import { parseBoolean, parseNumber, parsePositiveInt, parseSort, parseString } from "@/lib/parsers";
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

export const parseRoiSearchParams = (params: URLSearchParams): Partial<RoiTableState> => {
  const page = parsePositiveInt(params.get("page"), ROI_TABLE_DEFAULTS.page);
  const pageSize = parsePositiveInt(params.get("page_size"), ROI_TABLE_DEFAULTS.pageSize);
  const sort = parseSort(params.get("sort"), ROI_SORT_OPTIONS, ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc");

  const filters: Partial<RoiTableFilters> = {};

  const roiMinRaw = params.get("filter[roi_min]");
  if (roiMinRaw !== null) {
    const roiMin = parseNumber(roiMinRaw, Number.NaN);
    if (!Number.isNaN(roiMin)) {
      filters.roiMin = roiMin;
    }
  }

  const vendor = parseString(params.get("filter[vendor]"));
  if (vendor !== undefined) {
    filters.vendor = vendor;
  }

  const category = parseString(params.get("filter[category]"));
  if (category !== undefined) {
    filters.category = category;
  }

  const search = parseString(params.get("filter[search]"));
  if (search !== undefined) {
    filters.search = search;
  }

  const observeOnlyRaw = params.get("filter[observe_only]");
  if (observeOnlyRaw !== null) {
    const trueFallback = parseBoolean(observeOnlyRaw, true);
    const falseFallback = parseBoolean(observeOnlyRaw, false);
    if (trueFallback === falseFallback) {
      filters.observeOnly = trueFallback;
    }
  }

  if (Object.keys(filters).length === 0) {
    return {
      page,
      pageSize,
      sort,
    };
  }

  return {
    page,
    pageSize,
    sort,
    filters: filters as RoiTableFilters,
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
