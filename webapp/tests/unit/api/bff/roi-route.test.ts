import { NextRequest } from "next/server";

jest.mock("@/lib/api/roiClient", () => ({
  roiClient: {
    listRoiRows: jest.fn(),
  },
}));
jest.mock("@/lib/api/fetchFromApi", () => ({
  isApiError: () => false,
}));

const mockedModule = jest.requireMock("@/lib/api/roiClient") as {
  roiClient: {
    listRoiRows: jest.Mock;
  };
};

let handler: typeof import("@/app/api/bff/roi/route");

beforeAll(async () => {
  handler = await import("@/app/api/bff/roi/route");
});

const buildRequest = (query: string) => {
  const url = new URL(`http://localhost/api/bff/roi${query ? `?${query}` : ""}`);
  return new NextRequest(url);
};

describe("ROI BFF route", () => {
  beforeEach(() => {
    mockedModule.roiClient.listRoiRows.mockReset();
  });

  it("forwards pagination, sorting, and filters to the backend", async () => {
    mockedModule.roiClient.listRoiRows.mockResolvedValue({
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
    expect(mockedModule.roiClient.listRoiRows).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 2,
        pageSize: 25,
        sort: "asin_asc",
        roiMin: 5,
        roiMax: 20,
        vendor: 42,
        search: "headphones",
      })
    );

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
