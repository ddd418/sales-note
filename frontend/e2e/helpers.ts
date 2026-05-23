import { expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export type E2ERole = 'salesman' | 'manager' | 'admin';

type E2ESeed = {
  basePassword: string;
  users: Record<E2ERole, {
    username: string;
    password: string;
    id: number;
    displayName: string;
  }>;
  ids: Record<string, number>;
  paths: Record<string, string>;
  labels: Record<string, string>;
};

let cachedSeed: E2ESeed | null = null;

export function getSeed(): E2ESeed {
  if (!cachedSeed) {
    const seedPath = fileURLToPath(new URL('../../output/e2e/seed.json', import.meta.url));
    cachedSeed = JSON.parse(readFileSync(seedPath, 'utf-8')) as E2ESeed;
  }
  return cachedSeed;
}

export async function loginAs(page: Page, role: E2ERole): Promise<void> {
  const seed = getSeed();
  const user = seed.users[role];
  const djangoBaseURL = process.env.E2E_DJANGO_BASE_URL || 'http://127.0.0.1:8013';
  await page.goto(`${djangoBaseURL}/reporting/login/`);
  await page.getByLabel('사용자 ID').fill(user.username);
  await page.getByLabel('비밀번호').fill(user.password);
  await Promise.all([
    page.waitForURL((url) => !url.pathname.startsWith('/reporting/login'), { timeout: 30_000 }),
    page.getByRole('button', { name: /로그인/ }).click(),
  ]);
  await expect(page.locator('#id_username')).toHaveCount(0);
}

export async function gotoCrmPage(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
  await expect(page.locator('.dashboard-loading')).toHaveCount(0, { timeout: 20_000 });
  await expect(page.getByText(/API에 연결되지 않았습니다/)).toHaveCount(0);
  await expect(page.getByText('로그인이 필요합니다.')).toHaveCount(0);
}

export function accountRow(page: Page, accountLabel: string) {
  return page.locator('tr').filter({ hasText: accountLabel }).first();
}
