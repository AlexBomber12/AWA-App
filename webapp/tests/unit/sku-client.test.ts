import { rest } from "msw";
import { setupServer } from "msw/node";

import { getSkuDetail } from "@/lib/api/skuClient";

const apiServer = setupServer();

beforeAll(() => apiServer.listen());
afterEach(() => apiServer.resetHandlers());
afterAll(() => apiServer.close());

const mockDetail = {
  title: "MSW Prime Test",
  roi: 37.5,
  fees: 12.8,
  chartData: [
    { date: "2025-02-10T00:00:00Z", price: 32.1 },
    { date: "2025-02-11T00:00:00Z", price: 35.6 },
  ],
};

describe("skuClient", () => {
  it("fetches SKU detail via the BFF endpoint", async () => {
    let requestedUrl: URL | null = null;
    apiServer.use(
      rest.get("http://localhost:3000/api/bff/sku", (req, res, ctx) => {
        requestedUrl = new URL(req.url.toString());
        return res(ctx.json(mockDetail));
      })
    );

    const result = await getSkuDetail("B00-TEST-1");

    expect(requestedUrl?.searchParams.get("asin")).toBe("B00-TEST-1");
    expect(result).toEqual({ ...mockDetail, asin: "B00-TEST-1" });
  });

  it("surfaces ApiErrors when the BFF responds with an error", async () => {
    apiServer.use(
      rest.get("http://localhost:3000/api/bff/sku", (_req, res, ctx) =>
        res(ctx.status(502), ctx.json({ code: "SKU_UPSTREAM", message: "boom", status: 502 }))
      )
    );

    await expect(getSkuDetail("B00-ERR"))
      .rejects.toMatchObject({ code: "SKU_UPSTREAM", message: "boom", status: 502 });
  });
});
