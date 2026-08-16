import { assertSuccessfulJsonPayload, fetchJson } from './shared';

export type RevenuePeriod = 'year' | 'quarter' | 'month';

export type RevenueDetailItem = {
  // 선결제는 매출이 아니라 여기 오지 않는다 — 매출은 실제 납품될 때만 잡힌다.
  kind: 'delivery';
  date: string | null;
  accountLabel: string;
  itemName: string;
  quantity: number | null;
  amount: number;
  owner: string;
  href: string;
};

export type RevenueDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  period: {
    value: RevenuePeriod;
    label: string;
    start: string;
    end: string;
  };
  scope: { label: string };
  summary: {
    total: number;
    deliveryTotal: number;
    itemCount: number;
  };
  items: RevenueDetailItem[];
};

const emptyRevenueDetailData: RevenueDetailData = {
  success: false,
  source: 'unavailable',
  period: { value: 'year', label: '', start: '', end: '' },
  scope: { label: '' },
  summary: { total: 0, deliveryTotal: 0, itemCount: 0 },
  items: [],
};

export async function loadRevenueDetail(period: RevenuePeriod = 'year'): Promise<RevenueDetailData> {
  const query = new URLSearchParams();
  if (period) query.set('period', period);
  const href = `/reporting/api/revenue-detail/${query.toString() ? `?${query.toString()}` : ''}`;
  const { response, payload } = await fetchJson<RevenueDetailData>(href, {}, '매출 내역 API unavailable');
  assertSuccessfulJsonPayload(response, payload, '매출 내역 API unavailable', { requireDjangoSource: true });
  return {
    ...emptyRevenueDetailData,
    ...payload,
    items: payload.items ?? [],
  };
}
