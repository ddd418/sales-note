import { lazy } from 'react';

export const AccountCleanupPreviewPage = lazy(() =>
  import('./accounts/AccountCleanupPreviewPage').then((module) => ({ default: module.AccountCleanupPreviewPage })),
);

export const CompanyManagementPage = lazy(() =>
  import('./companies/CompanyManagementPage').then((module) => ({ default: module.CompanyManagementPage })),
);

export const DataCleanupPage = lazy(() =>
  import('./data-cleanup/DataCleanupPage').then((module) => ({ default: module.DataCleanupPage })),
);

export const DownloadsPage = lazy(() =>
  import('./downloads/DownloadsPage').then((module) => ({ default: module.DownloadsPage })),
);

export const ReportsPage = lazy(() =>
  import('./reports/ReportsPage').then((module) => ({ default: module.ReportsPage })),
);
