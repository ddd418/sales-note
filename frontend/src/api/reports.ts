import { assertSuccessfulJsonPayload, fetchJson, normalizeCoreCrmHref, normalizeHrefFields } from './shared';

export type ReportsCustomerRecentDelivery = {
  id?: number | null;
  date: string | null;
  label: string;
  amount: number;
  paymentSource: 'normal' | 'prepayment' | string;
  paymentSourceLabel: string;
  paymentStatus?: string;
  paymentStatusLabel?: string;
  href?: string;
};

export type ReportsOperationDrilldownContact = {
  id: number;
  name: string;
  manager: string;
  role: string;
  roleLabel: string;
  email: string;
  phone: string;
  ownerName: string;
  href: string;
};

export type ReportsOperationDrilldownRecord = {
  id: number;
  date: string | null;
  label: string;
  amount?: number;
  balance?: number;
  customerName?: string;
  ownerName?: string;
  paymentSource?: string;
  paymentSourceLabel?: string;
  paymentStatusLabel?: string;
  statusLabel?: string;
  href: string;
};

export type ReportsCustomerOperationRow = {
  accountKey: string;
  id: number;
  accountId?: number | null;
  representativeCustomerId?: number;
  customer: string;
  company: string;
  department: string;
  manager: string;
  contactCount?: number;
  contactPreview?: string[];
  owner: string;
  status: string;
  statusLabel: string;
  priority: string;
  priorityLabel: string;
  pipelineStage: string;
  pipelineStageLabel: string;
  deliveryCount: number;
  deliveryAmount: number;
  normalDeliveryCount: number;
  normalDeliveryAmount: number;
  prepaymentDeliveryCount: number;
  prepaymentDeliveryAmount: number;
  prepaymentUsedAmount: number;
  lastDeliveryDate: string | null;
  quoteCount: number;
  quoteAmount: number;
  lastQuoteDate: string | null;
  serviceCount: number;
  openServiceCount: number;
  lastServiceDate: string | null;
  prepaymentCount: number;
  prepaymentAmount: number;
  prepaymentBalance: number;
  prepaymentUsedTotal: number;
  lastPrepaymentDate: string | null;
  lastActivityDate: string | null;
  recentDeliveryItems: ReportsCustomerRecentDelivery[];
  cleanupCandidateCount: number;
  cleanupRiskLabel: string;
  cleanupTypes: string[];
  cleanupPreviewHref: string;
  links: {
    account: string;
    prepayments: string;
    cleanupPreview: string;
    customer: string;
  };
  drilldown: {
    contacts: ReportsOperationDrilldownContact[];
    deliveries: ReportsOperationDrilldownRecord[];
    quotes: ReportsOperationDrilldownRecord[];
    prepayments: ReportsOperationDrilldownRecord[];
    services: ReportsOperationDrilldownRecord[];
  };
  href: string;
  customerHref?: string;
  djangoHref: string;
};

export type ReportsCustomerOperations = {
  metrics: {
    totalCustomers: number;
    customersWithDeliveries: number;
    deliveryCount: number;
    deliveryAmount: number;
    normalDeliveryCount: number;
    normalDeliveryAmount: number;
    prepaymentDeliveryCount: number;
    prepaymentDeliveryAmount: number;
    prepaymentUsedAmount: number;
    quoteCount: number;
    quoteAmount: number;
    serviceCount: number;
    openServiceCount: number;
    prepaymentCount: number;
    prepaymentAmount: number;
    prepaymentBalance: number;
    prepaymentUsedTotal: number;
  };
  rows: ReportsCustomerOperationRow[];
};

export type ReportsCustomerOperationsComparison = {
  dateFrom: string;
  dateTo: string;
  metrics: Partial<ReportsCustomerOperations['metrics']>;
  deltas: Partial<ReportsCustomerOperations['metrics']>;
  changeRates: Record<string, number | null>;
};

export type ReportsDataQualityContact = {
  id: number;
  name: string;
  manager: string;
  email: string;
  phone: string;
  companyName: string;
  departmentName: string;
  departmentId: number | null;
  ownerName: string;
  scheduleCount: number;
  historyCount: number;
  quoteCount: number;
  prepaymentCount: number;
  recordCount: number;
  recordSummary: string;
  href: string;
  accountHref: string;
  candidateType?: string;
  candidateKey?: string;
  decisionUrl?: string;
  reviewStatus?: string;
  reviewStatusLabel?: string;
  decisionReason?: string;
  decisionUpdatedAt?: string | null;
  decisionUpdatedBy?: string;
  sourceFollowupId?: number | null;
};

export type ReportsDataQualityDepartment = {
  id: number;
  name: string;
  companyName: string;
  accountHref: string;
  cleanupPreviewHref: string;
  contactCount: number;
  recordCount: number;
  scheduleCount: number;
  historyCount: number;
  quoteCount: number;
  prepaymentCount: number;
  contacts: ReportsDataQualityContact[];
};

export type ReportsDuplicateAccountGroup = {
  candidateType?: string;
  candidateKey?: string;
  decisionUrl?: string;
  reviewStatus?: string;
  reviewStatusLabel?: string;
  decisionReason?: string;
  decisionUpdatedAt?: string | null;
  decisionUpdatedBy?: string;
  sourceDepartmentId?: number | null;
  targetDepartmentId?: number | null;
  companyName: string;
  normalizedDepartmentName: string;
  departmentNames: string[];
  departmentIds: number[];
  cleanupPreviewHref: string;
  contactCount: number;
  recordCount: number;
  riskLevel: string;
  riskLabel: string;
  suggestedAction: string;
  departments: ReportsDataQualityDepartment[];
  contacts: ReportsDataQualityContact[];
};

export type ReportsDuplicateContactGroup = {
  candidateType?: string;
  candidateKey?: string;
  decisionUrl?: string;
  reviewStatus?: string;
  reviewStatusLabel?: string;
  decisionReason?: string;
  decisionUpdatedAt?: string | null;
  decisionUpdatedBy?: string;
  sourceFollowupId?: number | null;
  targetFollowupId?: number | null;
  companyName: string;
  departmentName: string;
  identity: string;
  contactCount: number;
  recordCount: number;
  contactIds: number[];
  riskLevel: string;
  riskLabel: string;
  suggestedAction: string;
  contacts: ReportsDataQualityContact[];
};

export type ReportsDataQualityHistoryItem = {
  id: string;
  kind: 'audit' | 'decision' | string;
  title: string;
  statusLabel: string;
  detail: string;
  actorName: string;
  createdAt: string | null;
  candidateKey?: string;
  candidateType?: string;
  decision?: string;
  decisionUrl?: string;
  reason?: string;
  sourceDepartmentId?: number | null;
  targetDepartmentId?: number | null;
  sourceFollowupId?: number | null;
  targetFollowupId?: number | null;
};

export type ReportsDataQuality = {
  metrics: {
    duplicateAccountGroups: number;
    duplicateContactGroups: number;
    contactsWithoutDepartment: number;
    contactsWithoutCompany: number;
    cleanupCandidateCount: number;
    heldCandidateCount?: number;
    dismissedCandidateCount?: number;
  };
  normalizationRule: string;
  duplicateAccounts: ReportsDuplicateAccountGroup[];
  duplicateContacts: ReportsDuplicateContactGroup[];
  contactsWithoutDepartment: ReportsDataQualityContact[];
  contactsWithoutCompany: ReportsDataQualityContact[];
  history: ReportsDataQualityHistoryItem[];
};

export type ReportsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  filters: {
    dateFrom: string;
    dateTo: string;
    selectedUserId: number | null;
    query: string;
    companyId: number | null;
    departmentId: number | null;
    deliveryFilter: string;
    prepaymentBalanceFilter: string;
    exportScope: string;
  };
  scope: {
    canFilterUsers: boolean;
    canExport: boolean;
    label: string;
    salespeople: Array<{ id: number; name: string; username: string }>;
    companies: Array<{ id: number; name: string }>;
    departments: Array<{ id: number; name: string; companyId: number | null; companyName: string }>;
  };
  metrics: {
    totalHistories: number;
    completedFollowups: number;
    overdueFollowups: number;
    upcomingFollowups: number;
    activePipeline: number;
    totalAssets: number;
    activeAssets: number;
    openServiceAssets: number;
    overdueServiceAssets: number;
    dueCalibrationAssets: number;
    overdueCalibrationAssets: number;
  };
  activityReport: Array<{
    user: { id: number; name: string; username: string };
    historyCount: number;
    followupCount: number;
    overdueCount: number;
    lastActivityAt: string | null;
  }>;
  customerReport: Array<{
    id: number;
    customer: string;
    company: string;
    department: string;
    owner: string;
    pipelineStage: string;
    pipelineStageLabel: string;
    lastActivityAt: string | null;
    nextActionDate: string | null;
    href: string;
    djangoHref: string;
  }>;
  customerOperations: ReportsCustomerOperations;
  comparison: {
    customerOperations: ReportsCustomerOperationsComparison;
  };
  dataQuality: ReportsDataQuality;
  pipelineSummary: Array<{ stage: string; label: string; count: number }>;
  links: {
    activityCsv: string;
    pipelineCsv: string;
    activityXlsx: string;
    pipelineXlsx: string;
    customerOperationsXlsx: string;
    assets: string;
    legacy: string;
  };
};

const emptyReportsData: ReportsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  filters: {
    dateFrom: '',
    dateTo: '',
    selectedUserId: null,
    query: '',
    companyId: null,
    departmentId: null,
    deliveryFilter: 'any',
    prepaymentBalanceFilter: 'any',
    exportScope: 'filtered',
  },
  scope: {
    canFilterUsers: false,
    canExport: false,
    label: '',
    salespeople: [],
    companies: [],
    departments: [],
  },
  metrics: {
    totalHistories: 0,
    completedFollowups: 0,
    overdueFollowups: 0,
    upcomingFollowups: 0,
    activePipeline: 0,
    totalAssets: 0,
    activeAssets: 0,
    openServiceAssets: 0,
    overdueServiceAssets: 0,
    dueCalibrationAssets: 0,
    overdueCalibrationAssets: 0,
  },
  activityReport: [],
  customerReport: [],
  customerOperations: {
    metrics: {
      totalCustomers: 0,
      customersWithDeliveries: 0,
      deliveryCount: 0,
      deliveryAmount: 0,
      normalDeliveryCount: 0,
      normalDeliveryAmount: 0,
      prepaymentDeliveryCount: 0,
      prepaymentDeliveryAmount: 0,
      prepaymentUsedAmount: 0,
      quoteCount: 0,
      quoteAmount: 0,
      serviceCount: 0,
      openServiceCount: 0,
      prepaymentCount: 0,
      prepaymentAmount: 0,
      prepaymentBalance: 0,
      prepaymentUsedTotal: 0,
    },
    rows: [],
  },
  comparison: {
    customerOperations: {
      dateFrom: '',
      dateTo: '',
      metrics: {},
      deltas: {},
      changeRates: {},
    },
  },
  dataQuality: {
    metrics: {
      duplicateAccountGroups: 0,
      duplicateContactGroups: 0,
      contactsWithoutDepartment: 0,
      contactsWithoutCompany: 0,
      cleanupCandidateCount: 0,
    },
    normalizationRule: '',
    duplicateAccounts: [],
    duplicateContacts: [],
    contactsWithoutDepartment: [],
    contactsWithoutCompany: [],
    history: [],
  },
  pipelineSummary: [],
  links: {
    activityCsv: '/reporting/analytics/export/activity.csv',
    pipelineCsv: '/reporting/analytics/export/pipeline.csv',
    activityXlsx: '/reporting/analytics/export/activity.xlsx',
    pipelineXlsx: '/reporting/analytics/export/pipeline.xlsx',
    customerOperationsXlsx: '/reporting/api/reports/customer-operations.xlsx',
    assets: '/assets/',
    legacy: '/reporting/analytics/',
  },
};

export async function loadReportsData(params: {
  companyId?: string;
  dateFrom?: string;
  dateTo?: string;
  deliveryFilter?: string;
  departmentId?: string;
  exportScope?: string;
  prepaymentBalanceFilter?: string;
  query?: string;
  cleanupLimit?: number;
  cleanupHistoryLimit?: number;
  userId?: string;
} = {}): Promise<ReportsData> {
  const query = new URLSearchParams();
  if (params.companyId) query.set('company_id', params.companyId);
  if (params.dateFrom) query.set('date_from', params.dateFrom);
  if (params.dateTo) query.set('date_to', params.dateTo);
  if (params.deliveryFilter && params.deliveryFilter !== 'any') query.set('delivery_filter', params.deliveryFilter);
  if (params.departmentId) query.set('department_id', params.departmentId);
  if (params.exportScope && params.exportScope !== 'filtered') query.set('export_scope', params.exportScope);
  if (params.prepaymentBalanceFilter && params.prepaymentBalanceFilter !== 'any') query.set('prepayment_balance_filter', params.prepaymentBalanceFilter);
  if (params.query) query.set('q', params.query);
  if (params.cleanupLimit) query.set('cleanup_limit', String(params.cleanupLimit));
  if (params.cleanupHistoryLimit) query.set('cleanup_history_limit', String(params.cleanupHistoryLimit));
  if (params.userId) query.set('user_id', params.userId);

  try {
    const { response, payload } = await fetchJson<Partial<ReportsData>>(
      `/reporting/api/reports/${query.toString() ? `?${query.toString()}` : ''}`,
      {},
      'Reports API unavailable',
    );
    assertSuccessfulJsonPayload(response, payload, 'Reports API unavailable', { requireDjangoSource: true });
    return {
      ...emptyReportsData,
      ...payload,
      filters: {
        ...emptyReportsData.filters,
        ...(payload.filters ?? {}),
      },
      scope: {
        ...emptyReportsData.scope,
        ...(payload.scope ?? {}),
        salespeople: payload.scope?.salespeople ?? emptyReportsData.scope.salespeople,
        companies: payload.scope?.companies ?? emptyReportsData.scope.companies,
        departments: payload.scope?.departments ?? emptyReportsData.scope.departments,
      },
      metrics: {
        ...emptyReportsData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyReportsData.links,
        ...(payload.links ?? {}),
      },
      activityReport: payload.activityReport ?? emptyReportsData.activityReport,
      customerReport: (payload.customerReport ?? emptyReportsData.customerReport).map((customer) => (
        normalizeHrefFields(customer, ['href', 'djangoHref'])
      )),
      customerOperations: {
        ...emptyReportsData.customerOperations,
        ...(payload.customerOperations ?? {}),
        metrics: {
          ...emptyReportsData.customerOperations.metrics,
          ...(payload.customerOperations?.metrics ?? {}),
        },
        rows: (payload.customerOperations?.rows ?? emptyReportsData.customerOperations.rows).map((customer) => {
          const normalized = normalizeHrefFields(customer, ['href', 'customerHref', 'djangoHref', 'cleanupPreviewHref']);
          return {
            ...normalized,
            accountKey: customer.accountKey ?? (customer.accountId ? `department:${customer.accountId}` : `followup:${customer.representativeCustomerId ?? normalized.id}`),
            links: {
              account: normalizeCoreCrmHref(customer.links?.account ?? normalized.href),
              prepayments: normalizeCoreCrmHref(customer.links?.prepayments ?? ''),
              cleanupPreview: normalizeCoreCrmHref(customer.links?.cleanupPreview ?? customer.cleanupPreviewHref ?? ''),
              customer: normalizeCoreCrmHref(customer.links?.customer ?? customer.customerHref ?? ''),
            },
            drilldown: {
              contacts: (customer.drilldown?.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href'])),
              deliveries: (customer.drilldown?.deliveries ?? []).map((record) => normalizeHrefFields(record, ['href'])),
              quotes: (customer.drilldown?.quotes ?? []).map((record) => normalizeHrefFields(record, ['href'])),
              prepayments: (customer.drilldown?.prepayments ?? []).map((record) => normalizeHrefFields(record, ['href'])),
              services: (customer.drilldown?.services ?? []).map((record) => normalizeHrefFields(record, ['href'])),
            },
            recentDeliveryItems: (customer.recentDeliveryItems ?? []).map((item) => ({
              ...item,
              href: normalizeCoreCrmHref(item.href ?? ''),
            })),
          };
        }),
      },
      comparison: {
        ...emptyReportsData.comparison,
        ...(payload.comparison ?? {}),
        customerOperations: {
          ...emptyReportsData.comparison.customerOperations,
          ...(payload.comparison?.customerOperations ?? {}),
          metrics: {
            ...emptyReportsData.comparison.customerOperations.metrics,
            ...(payload.comparison?.customerOperations?.metrics ?? {}),
          },
          deltas: {
            ...emptyReportsData.comparison.customerOperations.deltas,
            ...(payload.comparison?.customerOperations?.deltas ?? {}),
          },
          changeRates: {
            ...emptyReportsData.comparison.customerOperations.changeRates,
            ...(payload.comparison?.customerOperations?.changeRates ?? {}),
          },
        },
      },
      dataQuality: {
        ...emptyReportsData.dataQuality,
        ...(payload.dataQuality ?? {}),
        metrics: {
          ...emptyReportsData.dataQuality.metrics,
          ...(payload.dataQuality?.metrics ?? {}),
        },
        duplicateAccounts: (payload.dataQuality?.duplicateAccounts ?? emptyReportsData.dataQuality.duplicateAccounts).map((group) => ({
          ...group,
          cleanupPreviewHref: normalizeCoreCrmHref(group.cleanupPreviewHref),
          decisionUrl: normalizeCoreCrmHref(group.decisionUrl ?? ''),
          departments: (group.departments ?? []).map((department) => ({
            ...department,
            accountHref: normalizeCoreCrmHref(department.accountHref),
            cleanupPreviewHref: normalizeCoreCrmHref(department.cleanupPreviewHref),
            contacts: (department.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
          })),
          contacts: (group.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
        })),
        duplicateContacts: (payload.dataQuality?.duplicateContacts ?? emptyReportsData.dataQuality.duplicateContacts).map((group) => ({
          ...group,
          decisionUrl: normalizeCoreCrmHref(group.decisionUrl ?? ''),
          contacts: (group.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
        })),
        contactsWithoutDepartment: (
          payload.dataQuality?.contactsWithoutDepartment ?? emptyReportsData.dataQuality.contactsWithoutDepartment
        ).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref', 'decisionUrl'])),
        contactsWithoutCompany: (
          payload.dataQuality?.contactsWithoutCompany ?? emptyReportsData.dataQuality.contactsWithoutCompany
        ).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref', 'decisionUrl'])),
        history: (payload.dataQuality?.history ?? emptyReportsData.dataQuality.history).map((item) => ({
          ...item,
          decisionUrl: normalizeCoreCrmHref(item.decisionUrl ?? ''),
        })),
      },
      pipelineSummary: payload.pipelineSummary ?? emptyReportsData.pipelineSummary,
    };
  } catch (error) {
    return {
      ...emptyReportsData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Reports API unavailable',
    };
  }
}
