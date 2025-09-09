import { expect, test } from '@playwright/test';

test('node editor shows access controls', async ({ page }) => {
  await page.goto('/nodes/article/new');
  await expect(page.getByTestId('context-switcher')).toBeVisible();
  await expect(page.getByTestId('space-selector')).toBeVisible();
  await expect(page.getByTestId('role-reader')).toBeVisible();
  await expect(page.getByTestId('override-toggle')).toBeVisible();
});
