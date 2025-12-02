import { roiClient } from "@/lib/api/roiClient";
import { fetchFromBff } from "@/lib/api/fetchFromBff";

jest.mock("@/lib/api/fetchFromBff", () => ({
  fetchFromBff: jest.fn(),
}));

const mockFetch = fetchFromBff as jest.MockedFunction<typeof fetchFromBff>;

describe("roiClient (BFF)", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("serializes ROI table params into query string", async () => {
    mockFetch.mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 50, total: 0, totalPages: 1 },
    });

    await roiClient.getRoiPage({
      page: 3,
      pageSize: 25,
      sort: "asin_desc",
      filters: { roiMin: 10, vendor: "12", category: "Beauty", search: "yoga", observeOnly: true },
    });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    expect(calledUrl.startsWith("/api/bff/roi?")).toBe(true);
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("page")).toBe("3");
    expect(params.get("page_size")).toBe("25");
    expect(params.get("sort")).toBe("asin_desc");
    expect(params.get("filter[roi_min]")).toBe("10");
    expect(params.get("filter[vendor]")).toBe("12");
    expect(params.get("filter[category]")).toBe("Beauty");
    expect(params.get("filter[search]")).toBe("yoga");
    expect(params.get("filter[observe_only]")).toBe("true");
  });

  it("falls back to defaults when params are missing", async () => {
    mockFetch.mockResolvedValue({
      data: [],
      pagination: { page: 1, pageSize: 50, total: 0, totalPages: 1 },
    });

    await roiClient.getRoiPage({ page: 1, pageSize: 50 });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("page")).toBe("1");
    expect(params.get("page_size")).toBe("50");
    expect(params.get("sort")).toBe("roi_pct_desc");
    expect(roiClient.getRoiListQueryKey({ page: 1, pageSize: 50 })).toEqual(["roi", expect.any(String)]);
  });
});
