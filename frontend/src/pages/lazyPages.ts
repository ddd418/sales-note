import { lazy } from 'react';

export const CompanyManagementPage = lazy(() =>
  import('./companies/CompanyManagementPage').then((module) => ({ default: module.CompanyManagementPage })),
);

export const ReceivablesPage = lazy(() =>
  import('./receivables/ReceivablesPage').then((module) => ({ default: module.ReceivablesPage })),
);

export const PipelineSheetPage = lazy(() =>
  import('./pipelineSheet/PipelineSheetPage').then((module) => ({ default: module.PipelineSheetPage })),
);
