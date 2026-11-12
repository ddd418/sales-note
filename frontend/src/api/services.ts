import { assertSuccessfulJsonPayload, csrfHeaders, fetchJson } from './shared';

const API = '/reporting/api/services/';

export type ServiceCustomer = {
  id: number;
  name: string;
  company: string;
  department: string;
  phone: string;
  email: string;
  href: string;
};

export type ServiceRequester = {
  name: string;
  contact: string;
  customer: ServiceCustomer | null;
};

export type ServiceSummaryItem = {
  id: number;
  date: string | null;
  completedDate: string | null;
  status: string;
  statusLabel: string;
  type: string;
  typeLabel: string;
  title: string;
  institution: string;
  customer: ServiceCustomer | null;
  requester: ServiceRequester | null;
  equipment: string;
  equipmentCount: number;
  serialNumber: string;
  serialNumbers: string[];
  ownerId: number | null;
  owner: string;
  chargeType: 'free' | 'paid';
  chargeLabel: string;
  chargeAmount: number | null;
  partsCount: number;
  partNames: string[];
  canEdit: boolean;
  href: string;
};

export type ServiceEquipment = {
  id?: number | null;
  name: string;
  modelName: string;
  serialNumber: string;
  note: string;
};

export type ServicePart = {
  id?: number;
  productId?: number | null;
  name: string;
  partNumber: string;
  quantity: number;
  unitPrice: number | null;
  amount?: number | null;
};

export type ServiceRelated = {
  basis: '' | 'serial' | 'customer' | 'institution';
  items: {
    id: number;
    date: string | null;
    typeLabel: string;
    statusLabel: string;
    title: string;
    diagnosis: string;
    href: string;
  }[];
};

export type ServiceDetail = ServiceSummaryItem & {
  rawTitle: string;
  equipments: ServiceEquipment[];
  equipmentName: string;
  modelName: string;
  symptom: string;
  diagnosis: string;
  resolution: string;
  dueDate: string | null;
  parts: ServicePart[];
  partsAmount: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  reportCompany: string;
  related: ServiceRelated;
};

export type ServiceProduct = {
  id: number;
  code: string;
  name: string;
  specification: string;
  unit: string;
  price: number;
};

export type ServiceOption = { value: string; label: string };

export type ServiceFormOptions = {
  types: ServiceOption[];
  statuses: ServiceOption[];
  charges: ServiceOption[];
  owners: { id: number; name: string }[];
};

export type ServiceYearSummary = {
  year: number;
  total: number;
  completed: number;
  open: number;
  paidCount: number;
  paidAmount: number;
  partsCount: number;
  byMonth: number[];
  byType: { type: string; label: string; count: number }[];
  topInstitutions: { name: string; count: number }[];
  repeatSerials: { serialNumber: string; equipment: string; count: number }[];
};

export type ServiceListData = {
  year: number;
  years: number[];
  summary: ServiceYearSummary;
  items: ServiceSummaryItem[];
  truncated: boolean;
  form: ServiceFormOptions;
};

export type ServiceListFilters = {
  year: number;
  status: string;
  type: string;
  q: string;
};

export type ServicePayload = {
  customerId: number | null;
  institution: string;
  requesterId: number | null;
  requesterName: string;
  requesterContact: string;
  type: string;
  status: string;
  date: string;
  completedDate: string;
  ownerId: number | null;
  title: string;
  symptom: string;
  diagnosis: string;
  resolution: string;
  equipments: Omit<ServiceEquipment, 'id'>[];
  chargeType: string;
  chargeAmount: string;
  parts: { productId: number | null; name: string; partNumber: string; quantity: number; unitPrice: string }[];
};

async function getJson<T>(href: string, label: string): Promise<T> {
  const { response, payload } = await fetchJson<T & { success?: boolean }>(href, {}, label);
  assertSuccessfulJsonPayload(response, payload, label);
  return payload;
}

async function postJson<T>(href: string, body: unknown, label: string): Promise<T> {
  const { response, payload } = await fetchJson<T & { success?: boolean }>(
    href,
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body ?? {}),
    },
    label,
  );
  assertSuccessfulJsonPayload(response, payload, label);
  return payload;
}

export function loadServices(filters: ServiceListFilters): Promise<ServiceListData> {
  const params = new URLSearchParams({ year: String(filters.year) });
  if (filters.status) params.set('status', filters.status);
  if (filters.type) params.set('type', filters.type);
  if (filters.q.trim()) params.set('q', filters.q.trim());
  return getJson<ServiceListData>(`${API}?${params.toString()}`, '서비스 목록을 불러오지 못했습니다.');
}

export async function loadService(id: number): Promise<{ item: ServiceDetail; form: ServiceFormOptions }> {
  return getJson(`${API}${id}/`, '서비스 기록을 불러오지 못했습니다.');
}

export async function loadServiceForm(): Promise<{ form: ServiceFormOptions; viewerId: number }> {
  return getJson(`${API}form/`, '입력 항목을 불러오지 못했습니다.');
}

export async function searchServiceCustomers(q: string): Promise<ServiceCustomer[]> {
  const data = await getJson<{ items: ServiceCustomer[] }>(
    `${API}customers/?q=${encodeURIComponent(q)}`,
    '고객을 찾지 못했습니다.',
  );
  return data.items;
}

export async function searchServiceProducts(q: string): Promise<ServiceProduct[]> {
  const data = await getJson<{ items: ServiceProduct[] }>(
    `${API}products/?q=${encodeURIComponent(q)}`,
    '제품을 찾지 못했습니다.',
  );
  return data.items;
}

export async function createService(body: ServicePayload): Promise<ServiceDetail> {
  const result = await postJson<{ item: ServiceDetail }>(`${API}create/`, body, '서비스 기록을 저장하지 못했습니다.');
  return result.item;
}

export async function updateService(id: number, body: ServicePayload): Promise<ServiceDetail> {
  const result = await postJson<{ item: ServiceDetail }>(`${API}${id}/update/`, body, '서비스 기록을 저장하지 못했습니다.');
  return result.item;
}

export async function deleteService(id: number): Promise<void> {
  await postJson(`${API}${id}/delete/`, {}, '서비스 기록을 삭제하지 못했습니다.');
}
