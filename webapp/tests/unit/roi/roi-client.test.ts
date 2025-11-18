import { roiClient } from "@/lib/api/roiClient";
import { fetchFromApi } from "@/lib/api/fetchFromApi";

jest.mock("@/lib/api/fetchFromApi", () => ({
  fetchFromApi: jest.fn(),
}));

const mockFetch = fetchFromApi as jest.MockedFunction<typeof fetchFromApi>;

describe("roiClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetches ROI rows with the provided query params", async () => {
    mockFetch.mockResolvedValueOnce([]);

    await roiClient.listRoiRows({ roiMin: 15, vendor: "42", category: "Beauty" });

    expect(mockFetch).toHaveBeenCalledWith("/roi?roi_min=15&vendor=42&category=Beauty");
  });

  it("omits empty params from the query string", async () => {
    mockFetch.mockResolvedValueOnce([]);

    await roiClient.listRoiRows({ roiMin: null, vendor: "", category: undefined });

    expect(mockFetch).toHaveBeenCalledWith("/roi");
  });

  it("calls the bulk approve endpoint with the payload", async () => {
    mockFetch.mockResolvedValueOnce({ updated: 1, approved_ids: ["ASIN-123"] });

    const payload = { asins: ["ASIN-123"] };
    await roiClient.bulkApproveRoi(payload);

    expect(mockFetch).toHaveBeenCalledWith("/roi-review/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  });
});
