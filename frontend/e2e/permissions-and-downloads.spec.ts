import { expect, test } from '@playwright/test';
import { getSeed, gotoCrmPage, loginAs } from './helpers';

test.describe('Role permissions and Excel downloads', () => {
  test('salesman cannot see or fetch the reports Excel export', async ({ page }) => {
    const seed = getSeed();

    await loginAs(page, 'salesman');
    await gotoCrmPage(page, seed.paths.reports);
    await expect(page.getByRole('link', { name: /현황 엑셀/ })).toHaveCount(0);

    const response = await page.context().request.get(seed.paths.reportsExcel);
    expect(response.status()).toBe(403);
    await expect(response).not.toBeOK();
  });

  test('manager can filter reports and download the visible Excel range', async ({ page }) => {
    const seed = getSeed();

    await loginAs(page, 'manager');
    await gotoCrmPage(page, seed.paths.reports);
    await expect(page.getByRole('link', { name: /현황 엑셀/ })).toBeVisible();
    const userFilter = page.locator('.reports-filter-bar label').filter({ hasText: /^담당자/ }).locator('select').first();
    const exportScope = page.locator('.reports-filter-bar label').filter({ hasText: /^엑셀 범위/ }).locator('select').first();
    await expect(userFilter).toBeVisible();
    await expect(exportScope).toBeVisible();
    await exportScope.selectOption('prepayment_balance');

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: /현황 엑셀/ }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
  });

  test('admin can access reports Excel directly', async ({ page }) => {
    const seed = getSeed();

    await loginAs(page, 'admin');
    await gotoCrmPage(page, seed.paths.reports);
    await expect(page.getByRole('link', { name: /현황 엑셀/ })).toBeVisible();
    const userFilter = page.locator('.reports-filter-bar label').filter({ hasText: /^담당자/ }).locator('select').first();
    await expect(userFilter).toBeVisible();

    const response = await page.context().request.get(seed.paths.reportsExcel);
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('spreadsheetml.sheet');
    expect((await response.body()).length).toBeGreaterThan(1000);
  });
});
