import { assertSuccessfulJsonPayload, csrfHeaders, fetchJson, normalizeCoreCrmHref } from './shared';

export type ReceivableStatus = 'open' | 'all' | 'settled' | 'card' | string;
export type ReceivableSort = 'outstanding' | 'customer' | 'date' | 'amount' | string;
export type ReceivableOrder = 'asc' | 'desc' | string;

export type ReceivableOption = {
  value: string;
  label: string;
};

export type ReceivableCustomer = {
  key: string;
  id: number | null;
  type: string;
  label: string;
  companyName: string;
  departmentName: string;
  customerName: string;
  ownerNames: string[];
  itemCount: number;
  openItemCount: number;
  settledItemCount: number;
  cardItemCount: number;
  totalAmount: number;
  outstandingAmount: number;
  lastDeliveryDate: string;
  href: string;
};

export type ReceivableItem = {
  id: number;
  itemName: string;
  quantity: number;
  unit: string;
  unitPrice: number | null;
  totalPrice: number;
  outstandingAmount: number;
  taxInvoiceIssued: boolean;
  cardPaymentReceived: boolean;
  receivableSettled: boolean;
  receivableSettledAt: string | null;
  receivableSettledBy: string;
  statusLabel: string;
  deliveryDate: string | null;
  scheduleId: number | null;
  scheduleHref: string;
  djangoScheduleHref: string;
  historyId: number | null;
  historyHref: string;
  accountKey: string;
  accountId: number | null;
  accountType: string;
  accountLabel: string;
  companyName: string;
  departmentName: string;
  customerName: string;
  ownerName: string;
  canEdit: boolean;
  links: {
    update: string;
    schedule: string;
    history: string;
  };
};

export type ReceivablesData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  summary: {
    totalOutstanding: number;
    totalCreditAmount: number;
    settledAmount: number;
    customerCount: number;
    itemCount: number;
    openItemCount: number;
  };
  filters: {
    status: string;
    query: string;
    sort: string;
    order: string;
    statuses: ReceivableOption[];
    sorts: ReceivableOption[];
  };
  customers: ReceivableCustomer[];
  items: ReceivableItem[];
  links: {
    self: string;
  };
};

export type ReceivableItemStatusPayload = {
  taxInvoiceIssued?: boolean;
  cardPaymentReceived?: boolean;
  receivableSettled?: boolean;
};

export type ReceivableItemStatusResponse = {
  success?: boolean;
  source?: 'django' | string;
  generatedAt?: string;
  message?: string;
  error?: string;
  item: ReceivableItem;
};

const emptyReceivablesData: ReceivablesData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  summary: {
    totalOutstanding: 0,
    totalCreditAmount: 0,
    settledAmount: 0,
    customerCount: 0,
    itemCount: 0,
    openItemCount: 0,
  },
  filters: {
    status: 'open',
    query: '',
    sort: 'outstanding',
    order: 'desc',
    statuses: [],
    sorts: [],
  },
  customers: [],
  items: [],
  links: {
    self: '/reporting/api/receivables/',
  },
};

function normalizeReceivableItem(item: ReceivableItem): ReceivableItem {
  const links = item.links ?? { update: '', schedule: '', history: '' };
  return {
    ...item,
    scheduleHref: normalizeCoreCrmHref(item.scheduleHref),
    djangoScheduleHref: item.djangoScheduleHref || '',
    historyHref: normalizeCoreCrmHref(item.historyHref),
    links: {
      update: links.update || '',
      schedule: normalizeCoreCrmHref(links.schedule || item.scheduleHref),
      history: normalizeCoreCrmHref(links.history || item.historyHref),
    },
  };
}

export async function loadReceivablesData(params: {
  status?: ReceivableStatus;
  query?: string;
  sort?: ReceivableSort;
  order?: ReceivableOrder;
} = {}): Promise<ReceivablesData> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.query?.trim()) query.set('q', params.query.trim());
  if (params.sort) query.set('sort', params.sort);
  if (params.order) query.set('order', params.order);
  const href = `/reporting/api/receivables/${query.toString() ? `?${query.toString()}` : ''}`;
  const { response, payload } = await fetchJson<ReceivablesData>(href, {}, 'Receivables API unavailable');
  assertSuccessfulJsonPayload(response, payload, 'Receivables API unavailable', { requireDjangoSource: true });
  return {
    ...emptyReceivablesData,
    ...payload,
    summary: {
      ...emptyReceivablesData.summary,
      ...(payload.summary ?? {}),
    },
    filters: {
      ...emptyReceivablesData.filters,
      ...(payload.filters ?? {}),
      statuses: payload.filters?.statuses ?? [],
      sorts: payload.filters?.sorts ?? [],
    },
    customers: payload.customers ?? [],
    items: (payload.items ?? []).map(normalizeReceivableItem),
    links: {
      ...emptyReceivablesData.links,
      ...(payload.links ?? {}),
    },
  };
}

export async function updateReceivableItemStatus(
  item: ReceivableItem,
  payload: ReceivableItemStatusPayload,
): Promise<ReceivableItemStatusResponse> {
  const updateHref = item.links.update;
  if (!updateHref) {
    throw new Error('외상 상태를 변경할 권한이 없습니다.');
  }
  const { response, payload: result } = await fetchJson<ReceivableItemStatusResponse>(
    updateHref,
    {
      method: 'POST',
      headers: csrfHeaders({
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(payload),
    },
    'Receivable item update unavailable',
  );
  assertSuccessfulJsonPayload(response, result, '외상 상태 저장에 실패했습니다.');
  return {
    ...result,
    item: normalizeReceivableItem(result.item),
  };
}
