import { expect, test } from '@playwright/test';
import { accountRow, getSeed, gotoCrmPage, loginAs } from './helpers';

test.describe('CRM core E2E flows', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'salesman');
  });

  test('salesman can open customer and account detail ledgers', async ({ page }) => {
    const seed = getSeed();

    await gotoCrmPage(page, seed.paths.customerDetail);
    await expect(page.getByText(seed.labels.company).first()).toBeVisible();
    await expect(page.getByText(seed.labels.sourceDepartment).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: '부서/연구실 계정 정보' })).toBeVisible();
    await expect(page.getByText('원장 범위')).toBeVisible();
    await expect(page.getByText('선결제 차감 납품', { exact: true }).first()).toBeVisible();
    await expect(page.getByRole('link', { name: '정리 영향' })).toBeVisible();

    await gotoCrmPage(page, seed.paths.accountDetail);
    await expect(page.getByText(seed.labels.sourceDepartment).first()).toBeVisible();
    await expect(page.getByText('공유 담당자')).toBeVisible();
    await expect(page.getByText(seed.labels.primaryContact, { exact: true }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: '선결제 기록' })).toBeVisible();
  });

  test('salesman can use reports account drilldown and data cleanup links', async ({ page }) => {
    const seed = getSeed();

    await gotoCrmPage(page, seed.paths.reports);
    await expect(page.getByRole('heading', { name: '부서/연구실 계정별 납품/견적 현황' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '계정별 운영 현황표' })).toBeVisible();
    await expect(page.getByRole('link', { name: /현황 엑셀/ })).toHaveCount(0);

    const row = accountRow(page, seed.labels.sourceDepartment);
    await expect(row).toBeVisible();
    await row.getByRole('button', { name: /드릴다운/ }).click();
    const drilldown = page.locator('.reports-drilldown-row').first();
    await expect(drilldown).toContainText(seed.labels.primaryContact);
    await expect(drilldown).toContainText('납품');
    await expect(drilldown).toContainText('선결제');

    await expect(page.getByRole('heading', { name: '데이터 정리 후보' })).toBeVisible();
    await expect(page.getByRole('link', { name: /정리 후보|정리 영향/ }).first()).toBeVisible();
  });

  test('salesman can drill into account prepayments', async ({ page }) => {
    const seed = getSeed();

    await gotoCrmPage(page, seed.paths.accountPrepayments);
    await expect(page.getByText('부서/연구실 계정 기준')).toBeVisible();
    await expect(page.getByRole('heading', { name: '선결제 내역' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '계정 잔액' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '납품 차감 내역' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '조정/이관/취소 기록' })).toBeVisible();
    await expect(page.getByText(seed.labels.prepaymentPayer).first()).toBeVisible();
    await expect(page.getByText(seed.labels.prepaymentItem).first()).toBeVisible();
    await expect(page.getByRole('link', { name: '엑셀' })).toBeVisible();
  });

  test('salesman can preview account cleanup impact with target search', async ({ page }) => {
    const seed = getSeed();

    await gotoCrmPage(page, seed.paths.cleanupPreview);
    await expect(page.getByRole('heading', { name: '계정 정리 영향 미리보기' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '대상 계정 검색' })).toBeVisible();
    await expect(page.getByText('선결제 잔액', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('장비/A/S').first()).toBeVisible();

    await page.getByPlaceholder('예: 서울대 김PI, 한은영, 줄기세포 연구실').fill('Lab');
    const targetButton = page.getByRole('button', { name: new RegExp(seed.labels.targetDepartment) });
    await expect(targetButton).toBeVisible({ timeout: 10_000 });
    await targetButton.click();
    await expect(page.getByText(/비교 중:/)).toContainText(seed.labels.targetDepartment);
  });
});
