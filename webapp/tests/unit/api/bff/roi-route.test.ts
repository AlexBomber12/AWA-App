import { NextRequest } from "next/server";

jest.mock("@/lib/api/roiApiClient", () => ({
  roiApiClient: {
    listRoiRows: jest.fn(),
  },
}));
jest.mock("@/lib/api/fetchFromApi", () => ({
  isApiError: () => false,
}));

const mockedModule = jest.requireMock("@/lib/api/roiApiClient") as {
  roiApiClient: {
    listRoiRows: jest.Mock;
  };
};

let handler: typeof import("@/app/api/bff/roi/route");

beforeAll(async () => {
  handler = await import("@/app/api/bff/roi/route");
});

describe("ROI BFF route", () => {
  const buildRequest = (query: string) => {
    const url = new URL(`http://localhost/api/bff/roi${query ? `?${query}` : ""}`);
    return new NextRequest(url);
  };

  beforeEach(() => {
    mockedModule.roiApiClient.listRoiRows.mockReset();
  });

  it("forwards pagination, sorting, and filters to the backend", async () => {
    mockedModule.roiApiClient.listRoiRows.mockResolvedValue({
      items: [
        {
          asin: "A1",
          title: "Sample",
          category: "cat",
          vendor_id: 42,
          cost: 10,
          freight: 2,
          fees: 3,
          roi_pct: 25,
        },
      ],
      pagination: { page: 2, page_size: 25, total: 10, total_pages: 1 },
    } as never);

    const request = buildRequest(
      "page=2&page_size=25&sort=asin_asc&filter[vendor]=42&filter[search]= headphones &filter[roi_min]=5&filter[observe_only]=true"
    );

    const response = await handler.GET(request);
    expect(mockedModule.roiApiClient.listRoiRows).toHaveBeenCalledWith({
      page: 2,
      pageSize: 25,
      sort: "asin_asc",
      roiMax: 20,
      filters: expect.objectContaining({
        roiMin: 5,
        vendor: "42",
        search: "headphones",
      }),
    });

    const payload = await response.json();
    expect(payload.pagination).toEqual({
      page: 2,
      pageSize: 25,
      total: 10,
      totalPages: 1,
    });
    expect(payload.items[0].asin).toBe("A1");
  });
});
