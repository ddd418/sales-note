import { Loader2, Printer, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { loadService, type ServiceDetail } from '../../api/services';
import { formatWon } from '../../components/shared/formatters';
import './serviceReport.css';

/** 수리완료보고서 — 셸 없이 A4 한 장. 브라우저 인쇄(또는 PDF 로 저장)로 뽑는다. */

function reportId(): number | null {
  const match = window.location.pathname.match(/^\/services\/(\d+)\/report\/?$/);
  return match ? Number(match[1]) : null;
}

const ISSUE_DATE = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
};

// 공식 문서라 연도까지 적는다
function fullDate(value: string | null | undefined) {
  if (!value) return '-';
  const [y, m, d] = value.slice(0, 10).split('-').map(Number);
  return y && m && d ? `${y}년 ${m}월 ${d}일` : value;
}

function Text({ value }: { value: string }) {
  return value ? <p className="rpt-text">{value}</p> : <p className="rpt-text rpt-empty">-</p>;
}

export function ServiceReportPage() {
  const [item, setItem] = useState<ServiceDetail | null>(null);
  const [error, setError] = useState('');
  const id = reportId();

  useEffect(() => {
    if (id === null) {
      setError('보고서 주소가 올바르지 않습니다.');
      return;
    }
    loadService(id)
      .then((payload) => {
        setItem(payload.item);
        document.title = `수리완료보고서 - ${payload.item.institution || payload.item.title}`;
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : '서비스 기록을 불러오지 못했습니다.'));
  }, [id]);

  if (!item) {
    return (
      <main className="rpt-shell">
        <p className="rpt-status">{error || <><Loader2 className="spin-icon" size={16} /> 불러오는 중</>}</p>
      </main>
    );
  }

  const customer = item.customer;
  const requester = item.requester;
  const year = (item.date ?? ISSUE_DATE()).slice(0, 4);
  const docNumber = `SR-${year}-${String(item.id).padStart(4, '0')}`;
  const equipments = item.equipments;
  const single = equipments.length <= 1 ? equipments[0] : undefined;
  const chargeText = item.chargeType === 'paid'
    ? `유상${item.chargeAmount !== null ? ` · ${formatWon(item.chargeAmount)} (청구 금액)` : ''}`
    : '무상';

  return (
    <main className="rpt-shell">
      <div className="rpt-toolbar">
        <button onClick={() => window.print()} type="button"><Printer size={15} />인쇄 / PDF 저장</button>
        <button onClick={() => window.close()} type="button"><X size={15} />닫기</button>
        <span>인쇄 창에서 대상을 "PDF로 저장"으로 고르면 파일로 저장됩니다.</span>
      </div>

      <article className="rpt-page">
        <header className="rpt-head">
          <div>
            <p className="rpt-company">{item.reportCompany}</p>
            <h1>수리완료보고서</h1>
          </div>
          <dl className="rpt-meta">
            <dt>문서번호</dt><dd>{docNumber}</dd>
            <dt>작성일</dt><dd>{fullDate(ISSUE_DATE())}</dd>
          </dl>
        </header>

        <table className="rpt-grid">
          <tbody>
            {requester ? (
              <tr>
                <th>의뢰처</th>
                <td colSpan={3}>
                  {[requester.name || requester.customer?.company, requester.customer?.name, requester.contact].filter(Boolean).join(' · ')}
                </td>
              </tr>
            ) : null}
            <tr>
              <th>{requester ? '사용처' : '고객'}</th>
              <td colSpan={3}>
                {[item.institution, customer?.department, customer?.name].filter(Boolean).join(' · ') || '-'}
              </td>
            </tr>
            <tr>
              <th>연락처</th>
              <td colSpan={3}>{[customer?.phone, customer?.email].filter(Boolean).join(' · ') || '-'}</td>
            </tr>
            {equipments.length <= 1 ? (
              <>
                <tr>
                  <th>브랜드</th><td>{single?.brand || '-'}</td>
                  <th>장비</th><td>{single?.name || '-'}</td>
                </tr>
                <tr>
                  <th>시리얼</th><td>{single?.serialNumber || '-'}{single?.note ? ` (${single.note})` : ''}</td>
                  <th>구분</th><td>{item.typeLabel}</td>
                </tr>
              </>
            ) : (
              <tr>
                <th>장비</th><td>아래 {equipments.length}대</td>
                <th>구분</th><td>{item.typeLabel}</td>
              </tr>
            )}
            <tr>
              <th>서비스일</th><td>{fullDate(item.date)}</td>
              <th>완료일</th><td>{item.completedDate ? fullDate(item.completedDate) : '진행 중'}</td>
            </tr>
            <tr>
              <th>담당</th><td>{item.owner || '-'}</td>
              <th>비용</th><td>{chargeText}</td>
            </tr>
          </tbody>
        </table>

        {equipments.length > 1 ? (
          <table className="rpt-parts rpt-equip">
            <thead><tr><th>No.</th><th>브랜드</th><th>장비명</th><th>시리얼</th><th>비고</th></tr></thead>
            <tbody>
              {equipments.map((equipment, index) => (
                <tr key={equipment.id ?? index}>
                  <td>{index + 1}</td>
                  <td>{equipment.brand || '-'}</td>
                  <td>{equipment.name || '-'}</td>
                  <td>{equipment.serialNumber || '-'}</td>
                  <td>{equipment.note || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}

        <section className="rpt-section"><h2>1. 증상 및 요청 사항</h2><Text value={item.symptom} /></section>
        <section className="rpt-section"><h2>2. 점검 결과</h2><Text value={item.diagnosis} /></section>
        <section className="rpt-section"><h2>3. 조치 내용</h2><Text value={item.resolution || item.rawTitle} /></section>

        <section className="rpt-section">
          <h2>4. 교체 부품 <small className="rpt-note">(단가·금액은 부가세 별도)</small></h2>
          {item.parts.length ? (
            <table className="rpt-parts">
              <thead><tr><th>No.</th><th>부품명</th><th>품번</th><th>수량</th><th>단가</th><th>금액</th></tr></thead>
              <tbody>
                {item.parts.map((part, index) => (
                  <tr key={part.id ?? index}>
                    <td>{index + 1}</td>
                    <td>{part.name}</td>
                    <td>{part.partNumber || '-'}</td>
                    <td className="rpt-num">{part.quantity}</td>
                    <td className="rpt-num">{part.unitPrice !== null ? formatWon(part.unitPrice) : '-'}</td>
                    <td className="rpt-num">{part.amount !== null && part.amount !== undefined ? formatWon(part.amount) : '-'}</td>
                  </tr>
                ))}
              </tbody>
              {item.partsAmount ? (
                <tfoot>
                  <tr><td colSpan={5}>공급가 합계</td><td className="rpt-num">{formatWon(item.partsAmount)}</td></tr>
                  <tr><td colSpan={5}>부가세 (10%)</td><td className="rpt-num">{formatWon(item.partsVat)}</td></tr>
                  <tr><td colSpan={5}>합계 (부가세 포함)</td><td className="rpt-num"><strong>{formatWon(item.partsTotal)}</strong></td></tr>
                </tfoot>
              ) : null}
            </table>
          ) : <p className="rpt-text rpt-empty">교체 부품 없음</p>}
        </section>

        <p className="rpt-closing">위와 같이 서비스를 완료하였음을 보고합니다.</p>

        <footer className="rpt-sign">
          <div><span>서비스 담당</span><strong>{item.owner}</strong><i>(서명)</i></div>
          <div><span>고객 확인</span><strong>{customer?.name ?? ''}</strong><i>(서명)</i></div>
        </footer>
      </article>
    </main>
  );
}
