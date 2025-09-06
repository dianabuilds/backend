import { expect,test } from "@playwright/test";

test("shows warning banner when override response includes warning_banner", async ({ page }) => {
  await page.route("**/users/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ default_account_id: "ws1" }),
    }),
  );

  await page.route("**/admin/accounts", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([{ id: "ws1", type: "global", slug: "global" }]),
    }),
  );

  await page.route("**/admin/menu", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    }),
  );

  await page.route("**/admin/accounts/ws1/nodes", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, warning_banner: "Override active" }),
    }),
  );

  await page.goto("/nodes/article/new");
  await page.getByTestId("override-toggle").check();
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Override active")).toBeVisible();
});
