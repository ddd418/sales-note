import { lazy } from 'react';

export const CompanyManagementPage = lazy(() =>
  import('./companies/CompanyManagementPage').then((module) => ({ default: module.CompanyManagementPage })),
);

export const ReportsPage = lazy(() =>
  import('./reports/ReportsPage').then((module) => ({ default: module.ReportsPage })),
);

export const ReceivablesPage = lazy(() =>
  import('./receivables/ReceivablesPage').then((module) => ({ default: module.ReceivablesPage })),
);
