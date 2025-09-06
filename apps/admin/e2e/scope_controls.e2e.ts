import { expect, test } from "@playwright/test";

test("scope controls switch modes and send override headers", async ({ page }) => {
  let lastHeaders: Record<string, string> = {};
  let lastUrl = "";

  await page.route("**/users/me", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ default_workspace_id: "ws1" }),
    }),
  );

  await page.route("**/admin/menu", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    }),
  );

  await page.route("**/admin/accounts", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([{ id: "ws1", name: "One" }]),
    }),
  );

  await page.route("**/admin/accounts/ws1/nodes**", (route) => {
    lastHeaders = route.request().headers();
    lastUrl = route.request().url();
    route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });

  await page.goto("/nodes");
  await page.getByTestId("override-toggle").check();
  await page.getByTestId("override-reason").fill("test");
  await page.getByTestId("scope-mode-select").selectOption("global");

  expect(lastUrl).toContain("scope_mode=global");
  expect(lastHeaders["x-admin-override"]).toBe("on");
  expect(lastHeaders["x-override-reason"]).toBe("test");
});

