import { defineConfig, devices } from '@playwright/test';

const isCi = Boolean(process.env.CI);
const djangoBaseURL = process.env.E2E_DJANGO_BASE_URL || 'http://127.0.0.1:8013';
const frontendBaseURL = process.env.E2E_FRONTEND_BASE_URL || 'http://127.0.0.1:5183';
const djangoPort = new URL(djangoBaseURL).port || '8013';
const frontendPort = new URL(frontendBaseURL).port || '5183';
const e2eDatabase = process.env.E2E_SQLITE_DATABASE || 'output/e2e/e2e.sqlite3';

process.env.E2E_DJANGO_BASE_URL = djangoBaseURL;
process.env.E2E_SQLITE_DATABASE = e2eDatabase;

export default defineConfig({
  testDir: './e2e',
  outputDir: '../output/e2e/playwright-results',
  fullyParallel: false,
  workers: 1,
  retries: isCi ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../output/e2e/playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: frontendBaseURL,
    acceptDownloads: true,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: `cd .. && python manage.py migrate --noinput && python manage.py seed_e2e_data --output output/e2e/seed.json && python manage.py runserver --noreload 127.0.0.1:${djangoPort}`,
      url: `${djangoBaseURL}/reporting/login/`,
      env: {
        ...process.env,
        E2E_SQLITE_DATABASE: e2eDatabase,
        FRONTEND_PIPELINE_URL: `${frontendBaseURL}/`,
        PYTHONIOENCODING: 'utf-8',
      },
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: `${frontendBaseURL}/`,
      env: {
        ...process.env,
        DJANGO_BASE_URL: djangoBaseURL,
      },
      timeout: 120_000,
      reuseExistingServer: false,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
