import { rest } from "msw";
import { setupServer } from "msw/node";

import { statsClient } from "@/lib/api/statsClient";

const apiServer = setupServer();

beforeAll(() => apiServer.listen());
afterEach(() => apiServer.resetHandlers());
afterAll(() => apiServer.close());

const mockResponse = {
  kpi: { roi_avg: 42.2, products: 120, vendors: 8 },
  roiTrend: {
    points: [
      { month: "2024-01-01", roi_avg: 40.5, items: 48 },
      { month: "2024-02-01", roi_avg: 43.1, items: 51 },
    ],
  },
};

describe("statsClient", () => {
  it("fetches KPI and ROI trend using a single BFF request", async () => {
    let requestCount = 0;
    apiServer.use(
      rest.get("http://localhost:3000/api/bff/stats", (_req, res, ctx) => {
        requestCount += 1;
        return res(ctx.json(mockResponse));
      })
    );

    const [kpi, roiTrend] = await Promise.all([statsClient.getKpi(), statsClient.getRoiTrend()]);

    expect(kpi).toEqual(mockResponse.kpi);
    expect(roiTrend).toEqual(mockResponse.roiTrend);
    expect(requestCount).toBe(1);
  });

  it("surfaces ApiErrors when the BFF returns an error payload", async () => {
    apiServer.use(
      rest.get("http://localhost:3000/api/bff/stats", (_req, res, ctx) =>
        res(ctx.status(500), ctx.json({ code: "STATS_ERROR", message: "boom", status: 500 }))
      )
    );

    await expect(statsClient.getKpi()).rejects.toMatchObject({
      code: "STATS_ERROR",
      message: "boom",
      status: 500,
    });
  });
});
