import {
  getReturnsList,
  getReturnsListQueryKey,
  getReturnsStats,
  getReturnsStatsQueryKey,
} from "@/lib/api/returnsClient";
import { fetchFromBff } from "@/lib/api/fetchFromBff";

jest.mock("@/lib/api/fetchFromBff", () => ({
  fetchFromBff: jest.fn(),
}));

const mockFetch = fetchFromBff as jest.MockedFunction<typeof fetchFromBff>;

describe("returnsClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("constructs list queries with filters and defaults", async () => {
    mockFetch.mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
    });

    await getReturnsList({
      page: 2,
      pageSize: 10,
      sort: "qty_desc",
      filters: { vendor: "42", asin: "B00-TEST-ROI", dateFrom: "2024-01-01", dateTo: "2024-01-31" },
    });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    expect(calledUrl.startsWith("/api/bff/returns?")).toBe(true);
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("resource")).toBe("list");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("10");
    expect(params.get("sort")).toBe("qty_desc");
    expect(params.get("filter[vendor]")).toBe("42");
    expect(params.get("filter[asin]")).toBe("B00-TEST-ROI");
    expect(params.get("filter[date_from]")).toBe("2024-01-01");
    expect(params.get("filter[date_to]")).toBe("2024-01-31");
  });

  it("applies defaults when filters are empty and keeps stable query keys", async () => {
    mockFetch.mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
    });

    const params = { page: 1, pageSize: 25 };
    await getReturnsList(params);

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    const paramsObj = new URL(calledUrl, "http://placeholder").searchParams;
    expect(paramsObj.get("sort")).toBe("refund_desc");
    expect(paramsObj.get("page_size")).toBe("25");
    expect(getReturnsListQueryKey(params)).toEqual(["returns", "list", expect.any(String)]);
  });

  it("builds stats query with provided filters", async () => {
    mockFetch.mockResolvedValue({
      data: {
        totalAsins: 1,
        totalUnits: 2,
        totalRefundAmount: 3,
        avgRefundPerUnit: 1.5,
      },
    });

    await getReturnsStats({ vendor: "99", asin: "B00-STATS" });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("resource")).toBe("stats");
    expect(params.get("filter[vendor]")).toBe("99");
    expect(params.get("filter[asin]")).toBe("B00-STATS");
    expect(params.get("page")).toBe("1");
    expect(params.get("page_size")).toBe("1");
    expect(getReturnsStatsQueryKey({ vendor: "99", asin: "B00-STATS" })).toEqual([
      "returns",
      "stats",
      expect.any(String),
    ]);
  });
});
