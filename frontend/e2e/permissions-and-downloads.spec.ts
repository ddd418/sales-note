import { expect, test } from '@playwright/test';
import { getSeed, gotoCrmPage, loginAs, type E2ERole } from './helpers';

type NavigationPayload = {
  currentUser: {
    role: E2ERole;
    canUseAi: boolean;
  };
  capabilities: {
    canManageTasks: boolean;
    canManageEmployees: boolean;
    canManageUsers: boolean;
    canManageCompanies: boolean;
    canUseAi: boolean;
    canUseMailbox: boolean;
    canViewAllUsers: boolean;
  };
  items: Array<{
    id: string;
    href: string;
    label: string;
  }>;
};

async function loadNavigation(page: Parameters<typeof loginAs>[0]): Promise<NavigationPayload> {
  const response = await page.context().request.get('/reporting/api/navigation/');
  expect(response.status()).toBe(200);
  const payload = await response.json();
  expect(payload.success).toBe(true);
  return payload as NavigationPayload;
}

test.describe('Role permissions and Excel downloads', () => {
  const roleCases: Array<{
    role: E2ERole;
    expectedItems: string[];
    hiddenItems: string[];
    capabilities: Partial<NavigationPayload['capabilities']>;
  }> = [
    {
      role: 'salesman',
      expectedItems: ['dashboard', 'analytics', 'dataCleanup', 'downloads', 'customers', 'mail', 'prepayments'],
      hiddenItems: ['tasksManager', 'employees', 'userAdmin', 'ai'],
      capabilities: {
        canManageTasks: false,
        canManageEmployees: false,
        canManageUsers: false,
        canManageCompanies: true,
        canUseAi: false,
        canUseMailbox: true,
        canViewAllUsers: false,
      },
    },
    {
      role: 'manager',
      expectedItems: ['dashboard', 'analytics', 'dataCleanup', 'downloads', 'customers', 'tasksManager', 'employees', 'ai', 'prepayments'],
      hiddenItems: ['mail', 'userAdmin'],
      capabilities: {
        canManageTasks: true,
        canManageEmployees: true,
        canManageUsers: false,
        canManageCompanies: false,
        canUseAi: true,
        canUseMailbox: false,
        canViewAllUsers: true,
      },
    },
    {
      role: 'admin',
      expectedItems: ['dashboard', 'analytics', 'dataCleanup', 'downloads', 'customers', 'userAdmin', 'mail', 'ai', 'prepayments'],
      hiddenItems: ['tasksManager', 'employees'],
      capabilities: {
        canManageTasks: false,
        canManageEmployees: true,
        canManageUsers: true,
        canManageCompanies: true,
        canUseAi: true,
        canUseMailbox: true,
        canViewAllUsers: true,
      },
    },
  ];

  for (const roleCase of roleCases) {
    test(`${roleCase.role} navigation exposes the expected CRM permission surface`, async ({ page }) => {
      await loginAs(page, roleCase.role);
      const navigation = await loadNavigation(page);
      const itemIds = new Set(navigation.items.map((item) => item.id));

      expect(navigation.currentUser.role).toBe(roleCase.role);
      for (const itemId of roleCase.expectedItems) {
        expect(itemIds.has(itemId), `${roleCase.role} should see ${itemId}`).toBe(true);
      }
      for (const itemId of roleCase.hiddenItems) {
        expect(itemIds.has(itemId), `${roleCase.role} should not see ${itemId}`).toBe(false);
      }
      for (const [capability, expected] of Object.entries(roleCase.capabilities)) {
        expect(navigation.capabilities[capability as keyof NavigationPayload['capabilities']], `${roleCase.role} ${capability}`).toBe(expected);
      }
    });
  }

  test('employee management API allows manager and admin but blocks salesman', async ({ page }) => {
    await loginAs(page, 'salesman');
    let response = await page.context().request.get('/reporting/api/employees/');
    expect(response.status()).toBe(403);

    await page.context().clearCookies();
    await loginAs(page, 'manager');
    response = await page.context().request.get('/reporting/api/employees/');
    expect(response.status()).toBe(200);
    let payload = await response.json();
    expect(payload.scope.mode).toBe('manager');

    await page.context().clearCookies();
    await loginAs(page, 'admin');
    response = await page.context().request.get('/reporting/api/employees/');
    expect(response.status()).toBe(200);
    payload = await response.json();
    expect(payload.scope.mode).toBe('admin');
  });

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
