import { expect, test } from "@playwright/test";

const NAV_ITEMS = ["Dashboard", "ROI", "SKU", "Ingest", "Returns", "Inbox", "Decision", "Settings"];

test("renders sidebar navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/AWA Operator Console/);

  for (const label of NAV_ITEMS) {
    const locator = page.getByRole("link", { name: label }).first();
    await expect(locator).toBeVisible();
  }

  await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible();
});
