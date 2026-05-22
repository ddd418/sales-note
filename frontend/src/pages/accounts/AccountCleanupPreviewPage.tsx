import { AlertTriangle, ArrowRightLeft, CheckCircle2, Download, FileSpreadsheet, Loader2, ShieldCheck, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { AccountCleanupMergeReadiness, AccountCleanupPreviewData, AccountCleanupSearchResult } from '../../api';
import { searchAccountCleanupTargets } from '../../api';
import { DashboardEmpty } from '../../components/shared/DashboardEmpty';
import { formatNumber, formatWon } from '../../components/shared/formatters';

export function AccountCleanupPreviewPage({
  data,
  loading,
  targetDepartmentId,
  onTargetDepartmentChange,
}: {
  data: AccountCleanupPreviewData | null;
  loading: boolean;
  targetDepartmentId: string;
  onTargetDepartmentChange: (value: string) => void;
}) {
  const [targetQuery, setTargetQuery] = useState('');
  const [targetResults, setTargetResults] = useState<AccountCleanupSearchResult[]>([]);
  const [targetSearchLoading, setTargetSearchLoading] = useState(false);

  useEffect(() => {
    if (!data?.sourceAccount?.id) {
      return;
    }
    const query = targetQuery.trim();
    if (!query) {
      setTargetResults([]);
      setTargetSearchLoading(false);
      return;
    }
    let alive = true;
    setTargetSearchLoading(true);
    const timer = window.setTimeout(() => {
      searchAccountCleanupTargets(query, data.sourceAccount.id).then((results) => {
        if (!alive) {
          return;
        }
        setTargetResults(results);
        setTargetSearchLoading(false);
      });
    }, 220);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [data?.sourceAccount?.id, targetQuery]);

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>계정 정리 영향 범위를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const source = data.sourceAccount;
  const target = data.targetAccount;
  const combined = data.combined.metrics;
  const accountTitle = (account: typeof source | null) => (
    account ? [account.companyName, account.name].filter(Boolean).join(' · ') || '계정명 없음' : '계정 없음'
  );
  const handleSelectTarget = (result: AccountCleanupSearchResult) => {
    setTargetQuery(result.label);
    setTargetResults([]);
    onTargetDepartmentChange(String(result.id));
  };
  const combinedCards = [
    { label: '담당자', value: `${formatNumber(combined.contactCount)}명`, detail: 'FollowUp 담당자' },
    { label: '운영 기록', value: `${formatNumber(combined.recordCount)}건`, detail: '담당자 제외 영향 기록' },
    { label: '납품/일정', value: `${formatNumber(combined.scheduleCount)}건`, detail: `납품 ${formatNumber(combined.deliveryCount)}건` },
    { label: '견적', value: `${formatNumber(combined.quoteCount)}건`, detail: formatWon(combined.quoteAmount) },
    { label: '선결제 잔액', value: formatWon(combined.prepaymentBalance), detail: `${formatNumber(combined.prepaymentCount)}건` },
    { label: '장비/A/S', value: `${formatNumber(combined.assetCount)}대`, detail: `A/S ${formatNumber(combined.serviceCaseCount)}건` },
  ];

  return (
    <section className="customers-page account-cleanup-preview-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>계정 정리 영향 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Cleanup preview</span>
          <h2>계정 정리 영향 미리보기</h2>
          <p>{accountTitle(source)} · 읽기 전용 검수 화면</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={source.href || data.links.sourceAccount}>계정 상세</a>
          <a className="route-secondary-action" href={data.links.reports || '/reports/'}>리포트</a>
        </div>
      </div>

      <section className="dashboard-panel account-cleanup-control-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Compare</span>
            <h2>대상 계정 검색</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <ArrowRightLeft size={18} />}
        </div>
        <div className="account-cleanup-target-form">
          <label>
            <span>업체, 부서/연구실, PI/책임자, 담당자, 이메일</span>
            <input
              onChange={(event) => setTargetQuery(event.target.value)}
              placeholder="예: 서울대 김PI, 한은영, 줄기세포 연구실"
              value={targetQuery}
            />
          </label>
          {targetDepartmentId ? (
            <button
              className="route-secondary-action"
              onClick={() => {
                setTargetQuery('');
                setTargetResults([]);
                onTargetDepartmentChange('');
              }}
              type="button"
            >
              비교 해제
            </button>
          ) : null}
        </div>
        {target ? (
          <div className="account-cleanup-selected-target">
            <CheckCircle2 size={16} />
            <span>비교 중: {accountTitle(target)}</span>
          </div>
        ) : null}
        <div className="account-cleanup-search-results">
          {targetSearchLoading ? (
            <span className="account-cleanup-search-status"><Loader2 className="spin-icon" size={15} />검색 중</span>
          ) : null}
          {!targetSearchLoading && targetQuery.trim() && targetResults.length === 0 ? (
            <span className="account-cleanup-search-status">검색 결과가 없습니다</span>
          ) : null}
          {targetResults.map((result) => (
            <button key={result.id} onClick={() => handleSelectTarget(result)} type="button">
              <strong>{result.label}</strong>
              <span>{result.meta || [result.companyName, result.departmentName].filter(Boolean).join(' · ')}</span>
            </button>
          ))}
        </div>
        <p className="account-cleanup-note">이 화면은 실제 병합/이관을 실행하지 않고, 영향을 받는 기록 수와 범위만 확인합니다.</p>
      </section>

      {data.warnings.length > 0 ? (
        <div className="account-cleanup-warning-list">
          {data.warnings.map((warning) => (
            <span key={warning}><AlertTriangle size={15} />{warning}</span>
          ))}
        </div>
      ) : null}

      <AccountCleanupChecklistPanel
        readiness={data.mergeReadiness}
        reportsHref={data.links.reports || '/reports/'}
      />

      <section className="dashboard-metric-grid customers-metric-grid reports-metric-grid" aria-label="계정 정리 영향 합산 지표">
        {combinedCards.map((card) => (
          <article className="dashboard-metric-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.detail}</small>
          </article>
        ))}
      </section>

      <div className="account-cleanup-preview-grid">
        <section className="dashboard-panel account-cleanup-account-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Source</span>
              <h2>{accountTitle(source)}</h2>
            </div>
            <Users size={18} />
          </div>
          <AccountCleanupImpactTable account={source} />
        </section>

        {target ? (
          <section className="dashboard-panel account-cleanup-account-panel">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Target</span>
                <h2>{accountTitle(target)}</h2>
              </div>
              <ArrowRightLeft size={18} />
            </div>
            <AccountCleanupImpactTable account={target} />
          </section>
        ) : null}
      </div>
    </section>
  );
}

function AccountCleanupChecklistPanel({
  readiness,
  reportsHref,
}: {
  readiness: AccountCleanupMergeReadiness;
  reportsHref: string;
}) {
  const statusClass = readiness.status === 'ready' ? 'ready' : readiness.status === 'review' ? 'review' : 'blocked';
  const exportHref = readiness.exportHref || '';
  return (
    <section className={`dashboard-panel account-cleanup-checklist-panel ${statusClass}`}>
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Pre-merge checklist</span>
          <h2>병합 전 확인 체크리스트</h2>
        </div>
        <ShieldCheck size={18} />
      </div>
      <div className="account-cleanup-readiness-summary">
        <div>
          <strong>{readiness.statusLabel || '병합 실행 불가'}</strong>
          <span>{readiness.summary || '실제 병합/이관 버튼은 아직 제공하지 않습니다.'}</span>
        </div>
        <div className="account-cleanup-readiness-counts">
          <span>통과 <strong>{formatNumber(readiness.counts.pass)}</strong></span>
          <span>확인 <strong>{formatNumber(readiness.counts.review)}</strong></span>
          <span>차단 <strong>{formatNumber(readiness.counts.blocked)}</strong></span>
        </div>
      </div>
      <div className="account-cleanup-safety-actions">
        {exportHref ? (
          <a className="route-secondary-action" href={exportHref}>
            <Download size={15} />
            미리보기 JSON export
          </a>
        ) : null}
        <a className="route-secondary-action" href={reportsHref}>
          <FileSpreadsheet size={15} />
          리포트로 돌아가기
        </a>
      </div>
      <div className="account-cleanup-checklist-grid">
        {readiness.items.map((item) => (
          <article className={`account-cleanup-checklist-item ${item.status}`} key={item.key}>
            <div>
              {item.status === 'pass' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <strong>{item.label}</strong>
              <span>{item.status === 'pass' ? '통과' : item.status === 'blocked' ? '차단' : '확인 필요'}</span>
            </div>
            <p>{item.detail}</p>
            {(item.count || item.amount) ? (
              <small>
                {item.count ? `건수 ${formatNumber(item.count)}` : ''}
                {item.count && item.amount ? ' · ' : ''}
                {item.amount ? `금액 ${formatWon(item.amount)}` : ''}
              </small>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function AccountCleanupImpactTable({ account }: { account: AccountCleanupPreviewData['sourceAccount'] }) {
  return (
    <>
      <div className="account-cleanup-contact-strip">
        <strong>담당자 {formatNumber(account.metrics.contactCount)}명</strong>
        <span>영향 기록 {formatNumber(account.metrics.recordCount)}건</span>
        <a href={account.href}>계정 상세</a>
      </div>
      <div className="customers-table-wrap account-cleanup-table-wrap">
        <table className="customers-table account-cleanup-table">
          <thead>
            <tr>
              <th>구분</th>
              <th>건수</th>
              <th>금액</th>
              <th>상세</th>
            </tr>
          </thead>
          <tbody>
            {account.affectedRecords.map((record) => (
              <tr key={record.key}>
                <td><strong>{record.label}</strong></td>
                <td>{formatNumber(record.count)}</td>
                <td>{record.amount ? formatWon(record.amount) : '-'}</td>
                <td>{record.detail || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="account-cleanup-contact-list">
        {account.contacts.length > 0 ? account.contacts.map((contact) => (
          <a href={contact.href} key={contact.id}>
            <strong>{contact.name}</strong>
            <span>{contact.recordSummary}</span>
          </a>
        )) : <DashboardEmpty label="표시할 담당자가 없습니다" />}
      </div>
    </>
  );
}