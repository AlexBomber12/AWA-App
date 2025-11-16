import { expect, test } from "@playwright/test";

const VISIBLE_TO_VIEWER = ["Dashboard", "ROI", "SKU", "Returns"];
const HIDDEN_FROM_VIEWER = ["Ingest", "Inbox", "Decision", "Settings"];

test("renders sidebar navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/AWA Operator Console/);

  for (const label of VISIBLE_TO_VIEWER) {
    const locator = page.getByRole("link", { name: label }).first();
    await expect(locator).toBeVisible();
  }

  for (const label of HIDDEN_FROM_VIEWER) {
    const locator = page.getByRole("link", { name: label });
    await expect(locator).toHaveCount(0);
  }

  await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible();
});
