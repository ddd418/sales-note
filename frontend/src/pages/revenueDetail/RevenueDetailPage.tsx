import { AlertTriangle, CircleDollarSign, Loader2, RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { loadRevenueDetail, type RevenueDetailData, type RevenuePeriod } from '../../api/revenueDetail';

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
  return new Intl.DateTimeFormat('ko-KR', { month: '2-digit', day: '2-digit' }).format(date);
};

function normalizePeriod(value: string | null): RevenuePeriod {
  if (value === 'quarter' || value === 'month') {
    return value;
  }
  return 'year';
}

export function RevenueDetailPage() {
  const [period, setPeriod] = useState<RevenuePeriod>(() =>
    normalizePeriod(new URLSearchParams(window.location.search).get('period')),
  );
  const [data, setData] = useState<RevenueDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const nextData = await loadRevenueDetail(period);
      setData(nextData);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : '매출 내역을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (period !== 'year') params.set('period', period);
    const queryString = params.toString();
    window.history.replaceState(null, '', `/revenue/${queryString ? `?${queryString}` : ''}`);
  }, [period]);

  const summary = data?.summary;

  return (
    <section className="revenue-detail-page">
      <div className="revenue-detail-controls">
        <div className="revenue-detail-tabs">
          <button
            className={`revenue-detail-tab${period === 'year' ? ' active' : ''}`}
            onClick={() => setPeriod('year')}
            type="button"
          >
            당해년도
          </button>
          <button
            className={`revenue-detail-tab${period === 'quarter' ? ' active' : ''}`}
            onClick={() => setPeriod('quarter')}
            type="button"
          >
            현재 분기
          </button>
          <button
            className={`revenue-detail-tab${period === 'month' ? ' active' : ''}`}
            onClick={() => setPeriod('month')}
            type="button"
          >
            이번 달
          </button>
        </div>
        <span className="revenue-detail-period-label">
          {data ? `${data.period.label} (${formatDateLabel(data.period.start)} ~ ${formatDateLabel(data.period.end)})` : ''}
        </span>
        <span className="revenue-detail-scope">{data?.scope.label}</span>
        <button className="route-secondary-action" disabled={loading} onClick={() => void refresh()} type="button">
          {loading ? <Loader2 className="spin-icon" size={15} /> : <RefreshCw size={15} />}
          새로고침
        </button>
      </div>

      {error ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="revenue-detail-summary-strip">
        <div>
          <span>완료 기준 실제 매출</span>
          <strong>{formatWon(summary?.total)}</strong>
        </div>
        <div>
          <span>납품 매출</span>
          <strong>{formatWon(summary?.deliveryTotal)}</strong>
        </div>
        <div>
          <span>내역 건수</span>
          <strong>{formatNumber(summary?.itemCount)}건</strong>
        </div>
      </div>

      <div className="revenue-detail-table-wrap">
        <table className="revenue-detail-table">
          <thead>
            <tr>
              <th>날짜</th>
              <th>구분</th>
              <th>계정</th>
              <th>내역</th>
              <th>담당자</th>
              <th>금액</th>
            </tr>
          </thead>
          <tbody>
            {loading && !data ? (
              <tr>
                <td colSpan={6}>
                  <Loader2 className="spin-icon" size={18} /> 데이터를 불러오는 중입니다
                </td>
              </tr>
            ) : data?.items.length ? (
              data.items.map((item, index) => (
                <tr key={`${item.kind}-${item.href}-${index}`}>
                  <td>{formatDateLabel(item.date)}</td>
                  <td>
                    <span className={`revenue-detail-kind ${item.kind}`}>납품</span>
                  </td>
                  <td>{item.accountLabel}</td>
                  <td>
                    <a href={item.href}>{item.itemName}</a>
                    {item.quantity ? <small>{formatNumber(item.quantity)}개</small> : null}
                  </td>
                  <td>{item.owner}</td>
                  <td className="revenue-detail-amount">{formatWon(item.amount)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6}>이 기간에 완료된 매출이 없습니다</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="revenue-detail-footnote">
        <CircleDollarSign size={14} />
        완료(completed)된 납품만 실제 매출로 집계합니다. 예정된 납품은 아직 실제로 일어나지 않았으므로 포함하지
        않습니다. 선결제는 받아둔 돈일 뿐이라 그 자체로는 매출이 아니며, 그 돈으로 실제 납품이 나갈 때 위 납품
        매출로 잡힙니다.
      </p>
    </section>
  );
}
