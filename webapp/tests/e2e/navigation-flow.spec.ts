import { expect, test, type Page } from "@playwright/test";

const seededFixtures = {
  stats: {
    kpi: { roi_avg: 42.5, products: 128, vendors: 14 },
    roiTrend: {
      points: [
        { month: "2024-01-01", roi_avg: 35, items: 30 },
        { month: "2024-02-01", roi_avg: 42, items: 34 },
        { month: "2024-03-01", roi_avg: 44, items: 38 },
      ],
    },
  },
  roi: [
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
  sku: {
    roi: 41.2,
    fees: 7.4,
    chartData: [
      { date: "2024-03-01", price: 23.4 },
      { date: "2024-03-02", price: 24.1 },
      { date: "2024-03-03", price: 22.9 },
    ],
  },
  returns: {
    stats: {
      totalAsins: 2,
      totalUnits: 42,
      totalRefundAmount: 1240.5,
      avgRefundPerUnit: 29.5,
      topAsin: "RET-001",
      topAsinRefundAmount: 640.5,
    },
    rows: [
      {
        returnId: "ret-001",
        asin: "RET-001",
        sku: "RET-001",
        title: "Return navigation primary",
        reason: "Damaged packaging",
        quantity: 21,
        reimbursementAmount: 640.5,
        currency: "EUR",
        status: "approved",
        createdAt: "2024-05-02T00:00:00Z",
        updatedAt: "2024-05-03T00:00:00Z",
        vendor: "Navigation Vendor",
        avgRefundPerUnit: 30.5,
      },
      {
        returnId: "ret-002",
        asin: "RET-002",
        sku: "RET-002",
        title: "Return navigation secondary",
        reason: "Customer remorse",
        quantity: 12,
        reimbursementAmount: 300,
        currency: "EUR",
        status: "pending",
        createdAt: "2024-04-22T00:00:00Z",
        updatedAt: "2024-04-23T00:00:00Z",
        vendor: "Secondary Vendor",
        avgRefundPerUnit: 25,
      },
    ],
  },
  inbox: [
    {
      id: "task-nav-1",
      source: "decision_engine",
      entity: { type: "sku_vendor", asin: "B00-NAV-001", vendorId: "12", label: "Navigation SKU" },
      summary: "Review ROI thresholds",
      assignee: "Jordan Ops",
      state: "open",
      decision: {
        decision: "update_price",
        priority: 90,
        deadlineAt: "2024-07-01T12:00:00Z",
        defaultAction: "Increase price by 2%",
        why: ["Competitive pressure rising"],
        alternatives: [{ decision: "wait_until", label: "Delay decision" }],
      },
      priority: 90,
      deadlineAt: "2024-07-01T12:00:00Z",
      createdAt: "2024-06-01T00:00:00Z",
      updatedAt: "2024-06-02T00:00:00Z",
    },
  ],
};

const registerApiStubs = async (page: Page) => {
  await page.route("**/api/bff/stats", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(seededFixtures.stats),
    });
  });

  await page.route("**/api/bff/roi**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: seededFixtures.roi,
        pagination: {
          page: 1,
          pageSize: 50,
          total: seededFixtures.roi.length,
          totalPages: 1,
        },
      }),
    });
  });

  await page.route("**/api/bff/sku**", async (route) => {
    const asin = new URL(route.request().url()).searchParams.get("asin") ?? seededFixtures.roi[0].asin;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        asin,
        title: `Detail for ${asin}`,
        ...seededFixtures.sku,
      }),
    });
  });

  await page.route("**/api/bff/returns**", async (route) => {
    const resource = new URL(route.request().url()).searchParams.get("resource");
    if (resource === "stats") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(seededFixtures.returns.stats),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        data: seededFixtures.returns.rows,
        items: seededFixtures.returns.rows,
        pagination: {
          page: 1,
          pageSize: 25,
          total: seededFixtures.returns.rows.length,
          totalPages: 1,
        },
      }),
    });
  });

  await page.route("**/api/bff/inbox**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: seededFixtures.inbox,
        pagination: {
          page: 1,
          pageSize: 25,
          total: seededFixtures.inbox.length,
          totalPages: 1,
        },
        summary: {
          open: seededFixtures.inbox.length,
          inProgress: 0,
          blocked: 0,
        },
      }),
    });
  });
};

test.beforeEach(async ({ page }) => {
  await registerApiStubs(page);
});

test("navigates through the primary operator surfaces", async ({ page }) => {
  await page.goto("/test-login");
  await expect(page.getByTestId("test-login-panel")).toBeVisible();
  await page.getByTestId("test-login-admin").click();

  await expect(page.getByTestId("page-header-dashboard")).toBeVisible();

  await page.getByTestId("nav-roi").first().click();
  await expect(page.getByTestId("page-header-roi-review")).toBeVisible();
  await expect(page.getByTestId("roi-row-B00-NAV-001")).toBeVisible();

  await page.getByTestId("roi-row-B00-NAV-001").click();
  await expect(page.getByTestId("page-header-sku-b00-nav-001")).toBeVisible();

  await page.getByTestId("nav-ingest").first().click();
  await expect(page.getByTestId("page-header-ingest")).toBeVisible();

  await page.getByTestId("nav-returns").first().click();
  await expect(page.getByTestId("page-header-returns")).toBeVisible();

  await page.getByTestId("nav-inbox").first().click();
  await expect(page.getByTestId("page-header-inbox")).toBeVisible();
  await expect(page.getByText(/Review ROI thresholds/)).toBeVisible();

  await page.goto("/test-login");
  await page.getByTestId("test-logout").click();
  await expect(page.getByTestId("test-login-panel")).toBeVisible();
});
