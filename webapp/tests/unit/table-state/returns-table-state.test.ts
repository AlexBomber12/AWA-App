import {
  RETURNS_MAX_PAGE_SIZE,
  RETURNS_TABLE_DEFAULTS,
  mergeReturnsTableStateWithDefaults,
  parseReturnsSearchParams,
  serializeReturnsSearchParams,
} from "@/lib/tableState/returns";

describe("Returns table state helpers", () => {
  it("parses query params and clamps page size", () => {
    const params = new URLSearchParams(
      "page=3&page_size=999&sort=asin_desc&filter%5Bvendor%5D=55&filter%5Basin%5D=B00-RET-123&filter%5Bdate_from%5D=2024-02-01&filter%5Bdate_to%5D=2024-02-29"
    );

    const parsed = parseReturnsSearchParams(params);

    expect(parsed.page).toBe(3);
    expect(parsed.pageSize).toBe(RETURNS_MAX_PAGE_SIZE);
    expect(parsed.sort).toBe("asin_desc");
    expect(parsed.filters).toEqual({
      vendor: "55",
      asin: "B00-RET-123",
      dateFrom: "2024-02-01",
      dateTo: "2024-02-29",
    });
  });

  it("serializes filters, omitting blanks", () => {
    const query = serializeReturnsSearchParams({
      page: 1,
      pageSize: 10,
      sort: "refund_asc",
      filters: { vendor: "  ", asin: "", dateFrom: "2024-01-01", dateTo: undefined },
    });

    expect(query.get("page_size")).toBe("10");
    expect(query.get("sort")).toBe("refund_asc");
    expect(query.get("filter[vendor]")).toBeNull();
    expect(query.get("filter[date_from]")).toBe("2024-01-01");
  });

  it("merges defaults when values are missing", () => {
    const merged = mergeReturnsTableStateWithDefaults({
      page: -1,
      pageSize: 0,
      sort: undefined,
    });

    expect(merged.page).toBe(RETURNS_TABLE_DEFAULTS.page);
    expect(merged.pageSize).toBe(RETURNS_TABLE_DEFAULTS.pageSize);
    expect(merged.sort).toBe(RETURNS_TABLE_DEFAULTS.sort);
    expect(merged.filters.vendor).toBe("");
  });
});
