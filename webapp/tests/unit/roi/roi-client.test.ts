import { roiApiClient } from "@/lib/api/roiApiClient";
import { fetchFromApi } from "@/lib/api/fetchFromApi";

jest.mock("@/lib/api/fetchFromApi", () => ({
  fetchFromApi: jest.fn(),
}));

const mockFetch = fetchFromApi as jest.MockedFunction<typeof fetchFromApi>;

describe("roiApiClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetches ROI rows with the provided query params", async () => {
    mockFetch.mockResolvedValueOnce({ items: [], pagination: { page: 1, page_size: 50, total: 0, total_pages: 1 } });

    await roiApiClient.listRoiRows({
      page: 2,
      pageSize: 25,
      sort: "asin_asc",
      roiMax: 20,
      filters: {
        roiMin: 15,
        vendor: "42",
        category: "Beauty",
        search: "headphones",
      },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/roi?page=2&page_size=25&sort=asin_asc&roi_min=15&roi_max=20&vendor=42&category=Beauty&search=headphones"
    );
  });

  it("omits empty params from the query string", async () => {
    mockFetch.mockResolvedValueOnce({ items: [], pagination: { page: 1, page_size: 50, total: 0, total_pages: 1 } });

    await roiApiClient.listRoiRows({ filters: { roiMin: null, vendor: "", category: undefined } });

    expect(mockFetch).toHaveBeenCalledWith("/roi?page=1&page_size=50&sort=roi_pct_desc");
  });

  it("calls the bulk approve endpoint with the payload", async () => {
    mockFetch.mockResolvedValueOnce({ updated: 1, approved_ids: ["ASIN-123"] });

    const payload = { asins: ["ASIN-123"] };
    await roiApiClient.bulkApproveRoi(payload);

    expect(mockFetch).toHaveBeenCalledWith("/roi-review/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });
});
