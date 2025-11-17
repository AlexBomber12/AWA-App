import { expect, test, type Page } from "@playwright/test";

const registerApiStubs = async (page: Page) => {
  await page.route("**/api/bff/stats", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        kpi: { roi_avg: 42.5, products: 128, vendors: 14 },
        roiTrend: {
          points: [
            { month: "2024-01-01", roi_avg: 35, items: 30 },
            { month: "2024-02-01", roi_avg: 42, items: 34 },
            { month: "2024-03-01", roi_avg: 44, items: 38 },
          ],
        },
      }),
    });
  });

  await page.route("**/api/bff/roi**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            asin: "B00-NAV-001",
            title: "Navigation Test SKU",
            vendor_id: 12,
            category: "Outdoors",
            cost: 14.5,
            freight: 2.5,
            fees: 1.2,
            roi_pct: 32.1,
          },
          {
            asin: "B00-NAV-002",
            title: "Navigation Fallback SKU",
            vendor_id: 44,
            category: "Beauty",
            cost: 18.2,
            freight: 2.1,
            fees: 1.1,
            roi_pct: 25.6,
          },
        ],
        pagination: {
          page: 1,
          pageSize: 50,
          total: 2,
          totalPages: 1,
        },
      }),
    });
  });

  await page.route("**/api/bff/sku**", async (route) => {
    const asin = new URL(route.request().url()).searchParams.get("asin") ?? "B00-NAV-001";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        asin,
        title: `Detail for ${asin}`,
        roi: 41.2,
        fees: 7.4,
        chartData: [
          { date: "2024-03-01", price: 23.4 },
          { date: "2024-03-02", price: 24.1 },
          { date: "2024-03-03", price: 22.9 },
        ],
      }),
    });
  });

  await page.route("**/api/bff/returns**", async (route) => {
    const resource = new URL(route.request().url()).searchParams.get("resource");
    if (resource === "stats") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totalAsins: 2,
          totalUnits: 42,
          totalRefundAmount: 1240.5,
          avgRefundPerUnit: 29.5,
          topAsin: "RET-001",
          topAsinRefundAmount: 640.5,
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          { asin: "RET-001", qty: 21, refundAmount: 640.5, avgRefundPerUnit: 30.5 },
          { asin: "RET-002", qty: 12, refundAmount: 300, avgRefundPerUnit: 25 },
        ],
        pagination: {
          page: 1,
          pageSize: 25,
          total: 2,
          totalPages: 1,
        },
      }),
    });
  });

  await page.route("**/api/bff/inbox", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "task-nav-1",
            source: "decision_engine",
            entity: { type: "sku", id: "B00-NAV-001", asin: "B00-NAV-001", label: "Navigation SKU" },
            summary: "Review ROI thresholds",
            assignee: "Jordan Ops",
            due: new Date().toISOString(),
            state: "open",
            decision: {
              decision: "update_price",
              priority: "high",
              deadlineAt: new Date(Date.now() + 86400000).toISOString(),
              defaultAction: "Increase price by 2%",
              why: ["Competitive pressure rising"],
              alternatives: ["Delay decision"],
            },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        ],
        total: 1,
      }),
    });
  });
};

test("navigates through the primary operator surfaces", async ({ page }) => {
  await registerApiStubs(page);

  await page.goto("/test-login");
  await expect(page.getByTestId("test-login-panel")).toBeVisible();
  await page.getByTestId("test-login-admin").click();

  await expect(page.getByTestId("page-header-dashboard")).toBeVisible();

  await page.getByTestId("nav-roi").click();
  await expect(page.getByTestId("page-header-roi-review")).toBeVisible();
  await expect(page.getByRole("button", { name: "B00-NAV-001" })).toBeVisible();

  await page.getByRole("button", { name: "B00-NAV-001" }).click();
  await expect(page.getByTestId("page-header-sku-b00-nav-001")).toBeVisible();

  await page.goBack();
  await expect(page.getByTestId("page-header-roi-review")).toBeVisible();

  await page.getByTestId("nav-ingest").click();
  await expect(page.getByTestId("page-header-ingest")).toBeVisible();

  await page.getByTestId("nav-returns").click();
  await expect(page.getByTestId("page-header-returns")).toBeVisible();

  await page.getByTestId("nav-inbox").click();
  await expect(page.getByTestId("page-header-inbox")).toBeVisible();
  await expect(page.getByText(/Review ROI thresholds/)).toBeVisible();

  await page.goto("/test-login");
  await page.getByTestId("test-logout").click();
  await expect(page.getByTestId("test-login-panel")).toBeVisible();
});
