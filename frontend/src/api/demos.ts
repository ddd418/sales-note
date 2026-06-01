import type { ProductOption } from './legacy';
import {
  assertSuccessfulJsonPayload,
  csrfHeaders,
  fetchJson,
  normalizeHrefFields,
} from './shared';

export type DemoStatusOption = {
  value: string;
  label: string;
};

export type DemoAccountContactOption = {
  id: number;
  name: string;
  ownerName: string;
};

export type DemoAccountOption = {
  departmentId: number;
  departmentName: string;
  companyId: number | null;
  companyName: string;
  label: string;
  contactCount: number;
  contacts: DemoAccountContactOption[];
  searchText: string;
};

export type DemoRecordItem = {
  id: number;
  companyId: number | null;
  companyName: string;
  departmentId: number | null;
  departmentName: string;
  customerId: number | null;
  customerName: string;
  customerHref: string;
  accountHref: string;
  productId: number | null;
  productCode: string;
  productName: string;
  serialNumber: string;
  quantity: number;
  status: string;
  statusLabel: string;
  startDate: string;
  expectedReturnDate: string;
  returnedDate: string;
  ownerId: number | null;
  ownerName: string;
  notes: string;
  createdByName: string;
  createdAt: string;
  updatedAt: string;
  canManage: boolean;
};

export type DemoRecordsSummary = {
  total: number;
  scheduled: number;
  active: number;
  returned: number;
  converted: number;
  cancelled: number;
  overdue: number;
};

export type CustomerDemoSummary = {
  canManage: boolean;
  message: string;
  metrics: DemoRecordsSummary;
  links: {
    demos: string;
    createDemo: string;
  };
  options: {
    statuses: DemoStatusOption[];
  };
  demos: DemoRecordItem[];
};

export type DemoRecordsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
  };
  summary: DemoRecordsSummary;
  demos: DemoRecordItem[];
  options: {
    accounts: DemoAccountOption[];
    products: ProductOption[];
    owners: Array<{ id: number; name: string; username: string }>;
    statuses: DemoStatusOption[];
  };
  links: {
    self: string;
    create: string;
  };
  permissions: {
    canCreate: boolean;
    readOnlyMessage: string;
  };
};

export type DemoRecordPayload = {
  departmentId: number;
  customerId?: number | null;
  productId?: number | null;
  productName?: string;
  serialNumber?: string;
  quantity: number;
  status: string;
  startDate?: string;
  expectedReturnDate?: string;
  returnedDate?: string;
  ownerId?: number | null;
  notes?: string;
};

type DemoRecordMutationResponse = {
  success?: boolean;
  source?: string;
  message?: string;
  error?: string;
  demo?: DemoRecordItem;
};

const emptyDemoSummary: DemoRecordsSummary = {
  total: 0,
  scheduled: 0,
  active: 0,
  returned: 0,
  converted: 0,
  cancelled: 0,
  overdue: 0,
};

export const emptyCustomerDemoSummary: CustomerDemoSummary = {
  canManage: false,
  message: '',
  metrics: emptyDemoSummary,
  links: {
    demos: '/demos/',
    createDemo: '',
  },
  options: {
    statuses: [],
  },
  demos: [],
};

const emptyDemoRecordsData: DemoRecordsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  summary: emptyDemoSummary,
  demos: [],
  options: {
    accounts: [],
    products: [],
    owners: [],
    statuses: [],
  },
  links: {
    self: '/reporting/api/demos/',
    create: '/reporting/api/demos/create/',
  },
  permissions: {
    canCreate: false,
    readOnlyMessage: '',
  },
};

function normalizeDemoRecord(record: DemoRecordItem): DemoRecordItem {
  return normalizeHrefFields(record, ['customerHref', 'accountHref']);
}

export function normalizeCustomerDemoSummary(summary?: Partial<CustomerDemoSummary> | null): CustomerDemoSummary {
  return {
    ...emptyCustomerDemoSummary,
    ...(summary ?? {}),
    metrics: {
      ...emptyCustomerDemoSummary.metrics,
      ...(summary?.metrics ?? {}),
    },
    links: normalizeHrefFields({
      ...emptyCustomerDemoSummary.links,
      ...(summary?.links ?? {}),
    }, ['demos', 'createDemo']),
    options: {
      ...emptyCustomerDemoSummary.options,
      ...(summary?.options ?? {}),
    },
    demos: (summary?.demos ?? emptyCustomerDemoSummary.demos).map(normalizeDemoRecord),
  };
}

export async function loadDemoRecordsData(filters: Record<string, string | number | null | undefined> = {}): Promise<DemoRecordsData> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && String(value).trim()) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  const { response, payload } = await fetchJson<DemoRecordsData>(
    `/reporting/api/demos/${query ? `?${query}` : ''}`,
    {},
    'Demo records API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'Demo records API unavailable', { requireDjangoSource: true });
  return {
    ...emptyDemoRecordsData,
    ...payload,
    summary: {
      ...emptyDemoRecordsData.summary,
      ...(payload.summary ?? {}),
    },
    options: {
      ...emptyDemoRecordsData.options,
      ...(payload.options ?? {}),
    },
    links: {
      ...emptyDemoRecordsData.links,
      ...(payload.links ?? {}),
    },
    permissions: {
      ...emptyDemoRecordsData.permissions,
      ...(payload.permissions ?? {}),
    },
    demos: (payload.demos ?? []).map(normalizeDemoRecord),
  };
}

async function postDemoRecord(url: string, payload: DemoRecordPayload | Record<string, never>, label: string): Promise<DemoRecordMutationResponse> {
  const { response, payload: data } = await fetchJson<DemoRecordMutationResponse>(
    url,
    {
      method: 'POST',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    label,
  );
  assertSuccessfulJsonPayload(response, data, label);
  return data;
}

export async function createDemoRecord(payload: DemoRecordPayload): Promise<DemoRecordItem> {
  const data = await postDemoRecord('/reporting/api/demos/create/', payload, 'Demo record create unavailable');
  if (!data.demo) {
    throw new Error(data.message || '데모 기록 응답을 확인하세요.');
  }
  return normalizeDemoRecord(data.demo);
}

export async function updateDemoRecord(demoId: number, payload: DemoRecordPayload): Promise<DemoRecordItem> {
  const data = await postDemoRecord(`/reporting/api/demos/${demoId}/update/`, payload, 'Demo record update unavailable');
  if (!data.demo) {
    throw new Error(data.message || '데모 기록 응답을 확인하세요.');
  }
  return normalizeDemoRecord(data.demo);
}

export async function deleteDemoRecord(demoId: number): Promise<void> {
  await postDemoRecord(`/reporting/api/demos/${demoId}/delete/`, {}, 'Demo record delete unavailable');
}
