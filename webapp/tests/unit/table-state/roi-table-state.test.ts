import {
  ROI_MAX_PAGE_SIZE,
  ROI_TABLE_DEFAULTS,
  mergeRoiTableStateWithDefaults,
  parseRoiSearchParams,
  serializeRoiSearchParams,
} from "@/lib/tableState/roi";

describe("ROI table state helpers", () => {
  it("parses ROI search params into a table state shape", () => {
    const params = new URLSearchParams(
      "page=2&page_size=500&sort=vendor_desc&filter%5Broi_min%5D=15&filter%5Bvendor%5D=7&filter%5Bcategory%5D=Outdoors&filter%5Bsearch%5D=camp&filter%5Bobserve_only%5D=true"
    );

    const parsed = parseRoiSearchParams(params);

    expect(parsed.page).toBe(2);
    expect(parsed.pageSize).toBe(ROI_MAX_PAGE_SIZE);
    expect(parsed.sort).toBe("vendor_desc");
    expect(parsed.filters).toEqual({
      roiMin: 15,
      vendor: "7",
      category: "Outdoors",
      search: "camp",
      observeOnly: true,
    });
  });

  it("serializes table state, omitting empty filters", () => {
    const query = serializeRoiSearchParams({
      page: 1,
      pageSize: ROI_TABLE_DEFAULTS.pageSize,
      sort: "roi_pct_desc",
      filters: { roiMin: null, vendor: "", category: "", search: "", observeOnly: false },
    });

    expect(query.get("page")).toBe("1");
    expect(query.get("page_size")).toBe(String(ROI_TABLE_DEFAULTS.pageSize));
    expect(query.get("sort")).toBe("roi_pct_desc");
    expect(query.get("filter[roi_min]")).toBeNull();
    expect(query.get("filter[vendor]")).toBeNull();
  });

  it("merges partial state with defaults and clamps values", () => {
    const merged = mergeRoiTableStateWithDefaults({
      page: -4,
      pageSize: 999,
      filters: { roiMin: 5 },
    });

    expect(merged.page).toBe(ROI_TABLE_DEFAULTS.page);
    expect(merged.pageSize).toBe(ROI_MAX_PAGE_SIZE);
    expect(merged.sort).toBe(ROI_TABLE_DEFAULTS.sort);
    expect(merged.filters.search).toBe("");
    expect(merged.filters.roiMin).toBe(5);
  });
});
