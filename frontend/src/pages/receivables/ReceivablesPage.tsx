import { AlertTriangle, Check, CheckCircle2, CircleDollarSign, Loader2, RefreshCw, Search } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  loadReceivablesData,
  updateReceivableItemStatus,
  type ReceivableItem,
  type ReceivableOrder,
  type ReceivableSort,
  type ReceivableStatus,
  type ReceivablesData,
} from '../../api/receivables';

const formatNumber = (value: number | null | undefined) => new Intl.NumberFormat('ko-KR').format(Number(value || 0));
const formatWon = (value: number | null | undefined) => `${formatNumber(value)}원`;

const formatDateLabel = (value: string | null | undefined) => {
  if (!value) {
    return '-';
  }
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('ko-KR', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
};

const receivableItemStateClass = (item: ReceivableItem) => {
  if (item.cardPaymentReceived) return 'card';
  if (item.receivableSettled) return 'settled';
  if (item.taxInvoiceIssued) return 'open';
  return 'unregistered';
};

type ReceivableCheckboxProps = {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: (checked: boolean) => void;
};

function ReceivableCheckbox({ checked, disabled, label, onChange }: ReceivableCheckboxProps) {
  return (
    <label className="receivable-check">
      <input
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      <span>{label}</span>
    </label>
  );
}

export function ReceivablesPage() {
  const initialParams = useMemo(() => new URLSearchParams(window.location.search), []);
  const [data, setData] = useState<ReceivablesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(() => initialParams.get('q') || '');
  const [status, setStatus] = useState<ReceivableStatus>(() => initialParams.get('status') || 'open');
  const [sort, setSort] = useState<ReceivableSort>(() => initialParams.get('sort') || 'outstanding');
  const [order, setOrder] = useState<ReceivableOrder>(() => initialParams.get('order') || 'desc');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const refreshData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const nextData = await loadReceivablesData({ status, query, sort, order });
      setData(nextData);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : '외상고객 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [order, query, sort, status]);

  useEffect(() => {
    void refreshData();
  }, [refreshData]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    if (status && status !== 'open') params.set('status', status);
    if (sort && sort !== 'outstanding') params.set('sort', sort);
    if (order && order !== 'desc') params.set('order', order);
    const queryString = params.toString();
    window.history.replaceState(null, '', `/receivables/${queryString ? `?${queryString}` : ''}`);
  }, [order, query, sort, status]);

  const handleUpdate = async (item: ReceivableItem, payload: {
    taxInvoiceIssued?: boolean;
    cardPaymentReceived?: boolean;
    receivableSettled?: boolean;
  }) => {
    if (updatingId) {
      return;
    }
    setUpdatingId(item.id);
    setError('');
    setMessage('');
    try {
      const result = await updateReceivableItemStatus(item, payload);
      setMessage(result.message || '외상 상태를 저장했습니다.');
      await refreshData();
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : '외상 상태 저장에 실패했습니다.');
    } finally {
      setUpdatingId(null);
    }
  };

  const summary = data?.summary;

  return (
    <section className="receivables-page">
      <div className="receivables-summary-strip">
        <div>
          <span>총 외상</span>
          <strong>{formatWon(summary?.totalOutstanding)}</strong>
        </div>
        <div>
          <span>외상 고객</span>
          <strong>{formatNumber(summary?.customerCount)}곳</strong>
        </div>
        <div>
          <span>외상 품목</span>
          <strong>{formatNumber(summary?.openItemCount)}개</strong>
        </div>
        <div>
          <span>수금/카드</span>
          <strong>{formatWon(summary?.settledAmount)}</strong>
        </div>
      </div>

      <div className="customers-filter-bar receivables-filter-bar">
        <label className="customers-search">
          <Search size={16} />
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="고객, 품목, 담당자 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => setStatus(event.target.value)} value={status}>
          {(data?.filters.statuses.length ? data.filters.statuses : [
            { value: 'open', label: '외상 진행중' },
            { value: 'all', label: '전체 납품 품목' },
            { value: 'unregistered', label: '미등록' },
            { value: 'settled', label: '수금완료' },
            { value: 'card', label: '카드결제' },
          ]).map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => setSort(event.target.value)} value={sort}>
          {(data?.filters.sorts.length ? data.filters.sorts : [
            { value: 'outstanding', label: '외상금액' },
            { value: 'customer', label: '고객명' },
            { value: 'date', label: '납품일' },
            { value: 'amount', label: '품목금액' },
          ]).map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <button
          className="route-secondary-action"
          onClick={() => setOrder((current) => (current === 'desc' ? 'asc' : 'desc'))}
          type="button"
        >
          {order === 'desc' ? '내림차순' : '오름차순'}
        </button>
        <button className="route-secondary-action" disabled={loading} onClick={() => void refreshData()} type="button">
          {loading ? <Loader2 className="spin-icon" size={15} /> : <RefreshCw size={15} />}
          새로고침
        </button>
      </div>

      {error ? <div className="dashboard-api-alert"><AlertTriangle size={18} /><span>{error}</span></div> : null}
      {message ? <div className="dashboard-api-alert success"><CheckCircle2 size={18} /><span>{message}</span></div> : null}

      <div className="receivables-layout">
        <section className="dashboard-panel receivable-customers-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Credit Customers</span>
              <h2>외상 고객</h2>
            </div>
            <CircleDollarSign size={20} />
          </div>
          {loading && !data ? (
            <div className="dashboard-loading compact"><Loader2 className="spin-icon" size={20} /><span>불러오는 중입니다</span></div>
          ) : data?.customers.length ? (
            <div className="receivable-customer-list">
              {data.customers.map((customer) => (
                <div className="receivable-customer-row" key={customer.key}>
                  <div>
                    <strong>{customer.label || '고객 미지정'}</strong>
                    <span>{[
                      customer.companyName,
                      customer.ownerNames.join(', '),
                      customer.lastDeliveryDate ? `최근 ${formatDateLabel(customer.lastDeliveryDate)}` : '',
                    ].filter(Boolean).join(' · ')}</span>
                  </div>
                  <div>
                    <strong>{formatWon(customer.outstandingAmount)}</strong>
                    <span>{formatNumber(customer.openItemCount)} / {formatNumber(customer.itemCount)}개</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">표시할 외상 고객이 없습니다</div>
          )}
        </section>

        <section className="dashboard-panel receivable-items-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Delivery Items</span>
              <h2>납품 품목별 처리</h2>
            </div>
            <Check size={20} />
          </div>
          <div className="receivable-items-table-wrap">
            <table className="receivable-items-table">
              <thead>
                <tr>
                  <th>납품일</th>
                  <th>고객</th>
                  <th>품목</th>
                  <th>금액</th>
                  <th>상태</th>
                  <th>외상</th>
                  <th>카드</th>
                  <th>수금</th>
                </tr>
              </thead>
              <tbody>
                {loading && !data ? (
                  <tr><td colSpan={8}><Loader2 className="spin-icon" size={18} /> 데이터를 불러오는 중입니다</td></tr>
                ) : data?.items.length ? data.items.map((item) => {
                  const disabled = updatingId === item.id || !item.canEdit;
                  return (
                    <tr key={item.id}>
                      <td>{formatDateLabel(item.deliveryDate)}</td>
                      <td>
                        <a href={item.scheduleHref || item.historyHref || '#'}>{item.accountLabel || '고객 미지정'}</a>
                        <small>{item.ownerName}</small>
                      </td>
                      <td>
                        <strong>{item.itemName}</strong>
                        <small>{formatNumber(item.quantity)}{item.unit}</small>
                      </td>
                      <td>
                        <strong>{formatWon(item.totalPrice)}</strong>
                        {item.outstandingAmount ? <small>외상 {formatWon(item.outstandingAmount)}</small> : null}
                      </td>
                      <td><span className={`receivable-status ${receivableItemStateClass(item)}`}>{item.statusLabel}</span></td>
                      <td>
                        <ReceivableCheckbox
                          checked={item.taxInvoiceIssued}
                          disabled={disabled}
                          label={updatingId === item.id ? '저장중' : '외상'}
                          onChange={(checked) => void handleUpdate(item, { taxInvoiceIssued: checked })}
                        />
                      </td>
                      <td>
                        <ReceivableCheckbox
                          checked={item.cardPaymentReceived}
                          disabled={disabled}
                          label="카드"
                          onChange={(checked) => void handleUpdate(item, { cardPaymentReceived: checked })}
                        />
                      </td>
                      <td>
                        <ReceivableCheckbox
                          checked={item.receivableSettled}
                          disabled={disabled}
                          label="수금"
                          onChange={(checked) => void handleUpdate(item, { receivableSettled: checked })}
                        />
                      </td>
                    </tr>
                  );
                }) : (
                  <tr><td colSpan={8}>표시할 납품 품목이 없습니다</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>
  );
}
