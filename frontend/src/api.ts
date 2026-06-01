// Backward-compatible API barrel.
//
// New React code should prefer the domain modules under ./api/* directly.
// This file stays as a compatibility layer for older imports during the
// React CRM migration.

export * from './api/accounts';
export * from './api/assets';
export * from './api/prepayments';
export * from './api/ai';
export * from './api/reports';
export * from './api/accountCleanup';
export * from './api/receivables';
export * from './api/demos';
export * from './api/legacy';
