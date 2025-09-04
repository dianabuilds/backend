import { test, expect } from "@playwright/test";

test.skip("moderation inbox loads", async ({ page }) => {
  await page.goto("/moderation");
  await expect(page).toHaveTitle(/Moderation/);
});
