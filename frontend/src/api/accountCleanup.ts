import type { ReportsDataQualityContact } from './reports';
import {
  assertSuccessfulJsonPayload,
  csrfHeaders,
  fetchJson,
  normalizeCoreCrmHref,
  normalizeHrefFields,
} from './shared';

export type AccountCleanupAffectedRecord = {
  key: string;
  label: string;
  count: number;
  amount: number;
  detail: string;
};

export type AccountCleanupPreviewAccount = {
  id: number | null;
  name: string;
  companyId: number | null;
  companyName: string;
  href: string;
  djangoHref: string;
  metrics: {
    contactCount: number;
    recordCount: number;
    scheduleCount: number;
    deliveryCount: number;
    quoteCount: number;
    quoteAmount: number;
    historyCount: number;
    prepaymentCount: number;
    prepaymentAmount: number;
    prepaymentBalance: number;
    prepaymentUsageCount: number;
    prepaymentUsedAmount: number;
    assetCount: number;
    serviceCaseCount: number;
    calibrationCount: number;
  };
  affectedRecords: AccountCleanupAffectedRecord[];
  contacts: ReportsDataQualityContact[];
};

export type AccountCleanupChecklistItem = {
  key: string;
  label: string;
  status: 'pass' | 'review' | 'blocked' | string;
  severity: 'success' | 'warning' | 'danger' | 'info' | string;
  detail: string;
  count: number;
  amount: number;
};

export type AccountCleanupMergeReadiness = {
  status: 'ready' | 'review' | 'blocked' | string;
  statusLabel: string;
  canMerge: boolean;
  summary: string;
  counts: {
    pass: number;
    review: number;
    blocked: number;
  };
  recommendedSurvivingAccount: AccountCleanupPreviewAccount | null;
  exportHref: string;
  items: AccountCleanupChecklistItem[];
};

export type AccountCleanupPreviewData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  mode: 'source' | 'compare' | string;
  sourceAccount: AccountCleanupPreviewAccount;
  targetAccount: AccountCleanupPreviewAccount | null;
  combined: {
    metrics: AccountCleanupPreviewAccount['metrics'];
    description: string;
  };
  mergeReadiness: AccountCleanupMergeReadiness;
  warnings: string[];
  links: {
    sourceAccount: string;
    reports: string;
    previewExportJson: string;
  };
};

export type AccountCleanupSearchResult = {
  id: number;
  label: string;
  companyName: string;
  departmentName: string;
  contactPreview: string[];
  piPreview: string[];
  emailPreview: string[];
  meta: string;
  searchText: string;
  href: string;
  previewHref: string;
};

export type AccountCleanupDecisionPayload = {
  candidateType: string;
  candidateKey: string;
  decision: 'hold' | 'dismissed' | 'active' | 'restore' | string;
  label?: string;
  reason?: string;
  sourceDepartmentId?: number | null;
  targetDepartmentId?: number | null;
  sourceFollowupId?: number | null;
  targetFollowupId?: number | null;
  decisionUrl?: string;
};

export type AccountCleanupDecisionResponse = {
  success?: boolean;
  message?: string;
  error?: string;
  candidateKey?: string;
  candidateType?: string;
  decision?: string;
  reviewStatusLabel?: string;
  restored?: boolean;
};

export type DataQualityContactAssignResponse = {
  success?: boolean;
  message?: string;
  error?: string;
  auditLogId?: number;
  contact?: ReportsDataQualityContact;
};

export type AccountCleanupMergeTransfer = {
  key: string;
  label: string;
  count: number;
  sampleIds: number[];
  sampleLimit: number;
  truncated: boolean;
  detail: string;
};

export type AccountCleanupMergePlan = {
  actionType: 'department_merge' | 'contact_merge' | string;
  sourceAccount?: {
    id: number;
    name: string;
    companyId: number | null;
    companyName: string;
    href: string;
  };
  targetAccount?: {
    id: number;
    name: string;
    companyId: number | null;
    companyName: string;
    href: string;
  };
  sourceContact?: {
    id: number;
    customerName: string;
    manager: string;
    email: string;
    status: string;
    companyId: number | null;
    companyName: string;
    departmentId: number | null;
    departmentName: string;
    href: string;
  };
  targetContact?: {
    id: number;
    customerName: string;
    manager: string;
    email: string;
    status: string;
    companyId: number | null;
    companyName: string;
    departmentId: number | null;
    departmentName: string;
    href: string;
  };
  transfers: AccountCleanupMergeTransfer[];
  counts: {
    transferCount: number;
    groups: number;
  };
};

export type AccountCleanupMergeResponse = {
  success?: boolean;
  source?: 'django' | string;
  generatedAt?: string;
  error?: string;
  message?: string;
  actionType: 'department_merge' | 'contact_merge' | string;
  mode: 'dry_run' | 'execute' | string;
  dryRun: boolean;
  executed: boolean;
  canExecute: boolean;
  requiredConfirmationText: string;
  plan: AccountCleanupMergePlan;
  warnings: string[];
  auditLogId: number | null;
  result?: Record<string, unknown>;
  after?: Record<string, unknown>;
};

export type AccountCleanupMergePayload = {
  mode?: 'dry_run' | 'execute';
  targetDepartmentId?: number | null;
  targetFollowupId?: number | null;
  confirmationText?: string;
};

const emptyAccountCleanupPreviewAccount: AccountCleanupPreviewAccount = {
  id: null,
  name: '',
  companyId: null,
  companyName: '',
  href: '',
  djangoHref: '',
  metrics: {
    contactCount: 0,
    recordCount: 0,
    scheduleCount: 0,
    deliveryCount: 0,
    quoteCount: 0,
    quoteAmount: 0,
    historyCount: 0,
    prepaymentCount: 0,
    prepaymentAmount: 0,
    prepaymentBalance: 0,
    prepaymentUsageCount: 0,
    prepaymentUsedAmount: 0,
    assetCount: 0,
    serviceCaseCount: 0,
    calibrationCount: 0,
  },
  affectedRecords: [],
  contacts: [],
};

const emptyAccountCleanupPreviewData: AccountCleanupPreviewData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  mode: 'source',
  sourceAccount: emptyAccountCleanupPreviewAccount,
  targetAccount: null,
  combined: {
    metrics: emptyAccountCleanupPreviewAccount.metrics,
    description: '',
  },
  mergeReadiness: {
    status: 'blocked',
    statusLabel: '병합 실행 불가',
    canMerge: false,
    summary: '',
    counts: {
      pass: 0,
      review: 0,
      blocked: 0,
    },
    recommendedSurvivingAccount: null,
    exportHref: '',
    items: [],
  },
  warnings: [],
  links: {
    sourceAccount: '',
    reports: '/reports/',
    previewExportJson: '',
  },
};

const emptyAccountCleanupSearchResult = {
  results: [] as AccountCleanupSearchResult[],
};

function normalizeAccountCleanupPreviewAccount(
  account?: Partial<AccountCleanupPreviewAccount> | null,
): AccountCleanupPreviewAccount | null {
  if (!account) {
    return null;
  }
  return {
    ...emptyAccountCleanupPreviewAccount,
    ...account,
    href: normalizeCoreCrmHref(account.href ?? emptyAccountCleanupPreviewAccount.href),
    djangoHref: normalizeCoreCrmHref(account.djangoHref ?? emptyAccountCleanupPreviewAccount.djangoHref),
    metrics: {
      ...emptyAccountCleanupPreviewAccount.metrics,
      ...(account.metrics ?? {}),
    },
    affectedRecords: account.affectedRecords ?? emptyAccountCleanupPreviewAccount.affectedRecords,
    contacts: (account.contacts ?? emptyAccountCleanupPreviewAccount.contacts).map((contact) => (
      normalizeHrefFields(contact, ['href', 'accountHref'])
    )),
  };
}

export async function loadAccountCleanupPreviewData(
  departmentId: number,
  targetDepartmentId?: string,
): Promise<AccountCleanupPreviewData> {
  const query = new URLSearchParams();
  if (targetDepartmentId) {
    query.set('target', targetDepartmentId);
  }

  try {
    const { response, payload } = await fetchJson<Partial<AccountCleanupPreviewData>>(
      `/reporting/api/accounts/${departmentId}/cleanup-preview/${query.toString() ? `?${query.toString()}` : ''}`,
      {},
      'Account cleanup preview API unavailable',
    );
    assertSuccessfulJsonPayload(response, payload, 'Account cleanup preview API unavailable', { requireDjangoSource: true });
    const sourceAccount = normalizeAccountCleanupPreviewAccount(payload.sourceAccount) ?? emptyAccountCleanupPreviewAccount;
    const targetAccount = normalizeAccountCleanupPreviewAccount(payload.targetAccount);
    return {
      ...emptyAccountCleanupPreviewData,
      ...payload,
      sourceAccount,
      targetAccount,
      combined: {
        ...emptyAccountCleanupPreviewData.combined,
        ...(payload.combined ?? {}),
        metrics: {
          ...emptyAccountCleanupPreviewData.combined.metrics,
          ...(payload.combined?.metrics ?? {}),
        },
      },
      mergeReadiness: {
        ...emptyAccountCleanupPreviewData.mergeReadiness,
        ...(payload.mergeReadiness ?? {}),
        counts: {
          ...emptyAccountCleanupPreviewData.mergeReadiness.counts,
          ...(payload.mergeReadiness?.counts ?? {}),
        },
        recommendedSurvivingAccount: (
          normalizeAccountCleanupPreviewAccount(payload.mergeReadiness?.recommendedSurvivingAccount)
        ),
        exportHref: normalizeCoreCrmHref(payload.mergeReadiness?.exportHref ?? payload.links?.previewExportJson ?? ''),
        items: payload.mergeReadiness?.items ?? emptyAccountCleanupPreviewData.mergeReadiness.items,
      },
      warnings: payload.warnings ?? emptyAccountCleanupPreviewData.warnings,
      links: {
        ...emptyAccountCleanupPreviewData.links,
        ...(payload.links ?? {}),
        sourceAccount: normalizeCoreCrmHref(payload.links?.sourceAccount ?? sourceAccount.href),
        reports: normalizeCoreCrmHref(payload.links?.reports ?? emptyAccountCleanupPreviewData.links.reports),
        previewExportJson: normalizeCoreCrmHref(payload.links?.previewExportJson ?? payload.mergeReadiness?.exportHref ?? ''),
      },
    };
  } catch (error) {
    return {
      ...emptyAccountCleanupPreviewData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Account cleanup preview API unavailable',
    };
  }
}

export async function searchAccountCleanupTargets(
  query: string,
  sourceDepartmentId?: number | null,
): Promise<AccountCleanupSearchResult[]> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('q', query.trim());
  }
  if (sourceDepartmentId) {
    params.set('source', String(sourceDepartmentId));
  }

  try {
    const { response, payload } = await fetchJson<{
      success?: boolean;
      source?: string;
      error?: string;
      message?: string;
      results?: AccountCleanupSearchResult[];
    }>(
      `/reporting/api/accounts/search/${params.toString() ? `?${params.toString()}` : ''}`,
      {},
      'Account search API unavailable',
    );
    assertSuccessfulJsonPayload(response, payload, 'Account search API unavailable', { requireDjangoSource: true });
    return (payload.results ?? emptyAccountCleanupSearchResult.results).map((result) => ({
      ...result,
      href: normalizeCoreCrmHref(result.href),
      previewHref: normalizeCoreCrmHref(result.previewHref),
      contactPreview: result.contactPreview ?? [],
      piPreview: result.piPreview ?? [],
      emailPreview: result.emailPreview ?? [],
      meta: result.meta ?? '',
      searchText: result.searchText ?? '',
    }));
  } catch {
    return emptyAccountCleanupSearchResult.results;
  }
}

export async function saveAccountCleanupDecision(
  payload: AccountCleanupDecisionPayload,
): Promise<AccountCleanupDecisionResponse> {
  const { response, payload: data } = await fetchJson<AccountCleanupDecisionResponse>(
    payload.decisionUrl || '/reporting/api/accounts/cleanup-decision/',
    {
      method: 'POST',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Cleanup decision API unavailable',
  );
  assertSuccessfulJsonPayload(response, data, 'Cleanup decision failed');
  return data;
}

async function postAccountCleanupMerge(
  url: string,
  payload: AccountCleanupMergePayload,
): Promise<AccountCleanupMergeResponse> {
  const { response, payload: data } = await fetchJson<AccountCleanupMergeResponse>(
    url,
    {
      method: 'POST',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Cleanup merge API unavailable',
  );
  assertSuccessfulJsonPayload(response, data, 'Cleanup merge failed');
  return {
    ...data,
    warnings: data.warnings ?? [],
    plan: {
      ...(data.plan ?? {}),
      transfers: data.plan?.transfers ?? [],
      counts: {
        transferCount: data.plan?.counts?.transferCount ?? 0,
        groups: data.plan?.counts?.groups ?? 0,
      },
    },
  };
}

export function runDepartmentCleanupMerge(
  sourceDepartmentId: number,
  payload: AccountCleanupMergePayload,
): Promise<AccountCleanupMergeResponse> {
  return postAccountCleanupMerge(`/reporting/api/accounts/${sourceDepartmentId}/cleanup-merge/`, payload);
}

export function runContactCleanupMerge(
  sourceFollowupId: number,
  payload: AccountCleanupMergePayload,
): Promise<AccountCleanupMergeResponse> {
  return postAccountCleanupMerge(`/reporting/api/customers/${sourceFollowupId}/cleanup-merge/`, payload);
}

export async function assignDataQualityContactAccount(
  followupId: number,
  departmentId: number,
): Promise<DataQualityContactAssignResponse> {
  const { response, payload: data } = await fetchJson<DataQualityContactAssignResponse>(
    `/reporting/api/data-quality/contacts/${followupId}/assign-account/`,
    {
      method: 'POST',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify({ departmentId }),
    },
    'Data quality assign API unavailable',
  );
  assertSuccessfulJsonPayload(response, data, 'Data quality assign failed');
  return {
    ...data,
    contact: data.contact ? normalizeHrefFields(data.contact, ['href', 'accountHref']) : undefined,
  };
}
