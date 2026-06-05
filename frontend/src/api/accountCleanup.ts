import type { ReportsDataQualityContact } from './reports';
import {
  assertSuccessfulJsonPayload,
  csrfHeaders,
  fetchJson,
  normalizeCoreCrmHref,
  normalizeHrefFields,
} from './shared';

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

const emptyAccountCleanupSearchResult = {
  results: [] as AccountCleanupSearchResult[],
};

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
