import { NextRequest } from "next/server";

import { GET } from "@/app/api/bff/returns/route";
import { returnsApiClient } from "@/lib/api/returnsApiClient";

jest.mock("@/lib/api/fetchFromApi", () => ({
  isApiError: () => false,
}));
jest.mock("@/lib/api/returnsApiClient", () => ({
  returnsApiClient: {
    fetchStats: jest.fn(),
  },
}));

const mockedFetch = returnsApiClient.fetchStats as jest.MockedFunction<typeof returnsApiClient.fetchStats>;

const buildRequest = (query: string) => {
  const url = new URL(`http://localhost/api/bff/returns${query ? `?${query}` : ""}`);
  return new NextRequest(url);
};

describe("Returns BFF route", () => {
  beforeEach(() => {
    mockedFetch.mockReset();
  });

  it("builds list responses using backend pagination", async () => {
    mockedFetch.mockResolvedValueOnce({
      items: [
        { asin: "A1", qty: 5, refund_amount: 10 },
        { asin: "A2", qty: 3, refund_amount: 6 },
      ],
      total_returns: 50,
      pagination: { page: 3, page_size: 50, total: 50, total_pages: 1 },
      summary: {
        total_asins: 50,
        total_units: 8,
        total_refund_amount: 16,
        avg_refund_per_unit: 2,
        top_asin: "A1",
        top_refund_amount: 10,
      },
    } as never);

    const request = buildRequest("resource=list&page=3&page_size=50&sort=qty_desc&filter[asin]=A1");
    const response = await GET(request);
    expect(mockedFetch).toHaveBeenCalledWith({
      page: 3,
      pageSize: 50,
      sort: "qty_desc",
      filters: expect.objectContaining({ asin: "A1" }),
    });
    const payload = await response.json();
    expect(payload.pagination).toEqual({ page: 3, pageSize: 50, total: 50, totalPages: 1 });
    expect(payload.items[0]).toMatchObject({ asin: "A1", avgRefundPerUnit: 2 });
  });

  it("returns summary payload using backend summary", async () => {
    mockedFetch.mockResolvedValueOnce({
      items: [],
      total_returns: 10,
      pagination: { page: 1, page_size: 1, total: 10, total_pages: 10 },
      summary: {
        total_asins: 10,
        total_units: 25,
        total_refund_amount: 100,
        avg_refund_per_unit: 4,
        top_asin: "A1",
        top_refund_amount: 40,
      },
    } as never);

    const request = buildRequest("resource=stats&filter[vendor]=ACME");
    const response = await GET(request);
    expect(mockedFetch).toHaveBeenCalledWith({
      page: 1,
      pageSize: 1,
      sort: "refund_desc",
      filters: expect.objectContaining({ vendor: "ACME" }),
    });
    const payload = await response.json();
    expect(payload).toEqual({
      totalAsins: 10,
      totalUnits: 25,
      totalRefundAmount: 100,
      avgRefundPerUnit: 4,
      topAsin: "A1",
      topAsinRefundAmount: 40,
    });
  });
});
