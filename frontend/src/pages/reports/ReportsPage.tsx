import {
  AlertTriangle,
  ArrowRightLeft,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Loader2,
  MoveUpRight,
  RefreshCw,
  Search,
  Users,
  Wrench,
} from 'lucide-react';
import { Fragment, useState } from 'react';
import type { AccountCleanupDecisionPayload, AccountCleanupSearchResult, ReportsData, ReportsDataQualityContact } from '../../api';
import { assignDataQualityContactAccount, saveAccountCleanupDecision, searchAccountCleanupTargets } from '../../api';
import { DashboardEmpty } from '../../components/shared/DashboardEmpty';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { formatDateLabel, formatDateTimeLabel, formatNumber, formatSignedNumber, formatSignedWon, formatWon } from '../../components/shared/formatters';

export function ReportsPage({
  companyId,
  data,
  dateFrom,
  dateTo,
  deliveryFilter,
  departmentId,
  exportScope,
  loading,
  prepaymentBalanceFilter,
  query,
  userId,
  onDateFromChange,
  onDateToChange,
  onDeliveryFilterChange,
  onDepartmentChange,
  onExportScopeChange,
  onCompanyChange,
  onPrepaymentBalanceFilterChange,
  onQueryChange,
  onRefresh,
  onUserChange,
}: {
  companyId: string;
  data: ReportsData | null;
  dateFrom: string;
  dateTo: string;
  deliveryFilter: string;
  departmentId: string;
  exportScope: string;
  loading: boolean;
  prepaymentBalanceFilter: string;
  query: string;
  userId: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onDeliveryFilterChange: (value: string) => void;
  onDepartmentChange: (value: string) => void;
  onExportScopeChange: (value: string) => void;
  onCompanyChange: (value: string) => void;
  onPrepaymentBalanceFilterChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRefresh: () => void;
  onUserChange: (value: string) => void;
}) {
  const [expandedAccountKey, setExpandedAccountKey] = useState<string | null>(null);
  const [cleanupActionLoadingKey, setCleanupActionLoadingKey] = useState('');
  const [cleanupActionMessage, setCleanupActionMessage] = useState('');
  const [quickFixContactId, setQuickFixContactId] = useState('');
  const [quickFixQuery, setQuickFixQuery] = useState('');
  const [quickFixResults, setQuickFixResults] = useState<AccountCleanupSearchResult[]>([]);
  const [quickFixTarget, setQuickFixTarget] = useState<AccountCleanupSearchResult | null>(null);
  const [quickFixLoading, setQuickFixLoading] = useState(false);
  const [quickFixSubmitting, setQuickFixSubmitting] = useState(false);

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객 운영 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const operations = data.customerOperations;
  const dataQuality = data.dataQuality;
  const rows = operations.rows;
  const metrics = operations.metrics;
  const customersWithRecords = rows.filter((row) => (
    row.deliveryCount > 0 ||
    row.quoteCount > 0 ||
    row.serviceCount > 0 ||
    row.prepaymentCount > 0
  )).length;
  const metricCards = [
    { label: '계정', value: `${formatNumber(metrics.totalCustomers)}개`, detail: `기록 보유 ${formatNumber(customersWithRecords)}개`, icon: Users, tone: 'blue' as const },
    { label: '납품', value: `${formatNumber(metrics.deliveryCount)}건`, detail: formatWon(metrics.deliveryAmount), icon: CalendarDays, tone: 'green' as const },
    { label: '견적', value: `${formatNumber(metrics.quoteCount)}건`, detail: formatWon(metrics.quoteAmount), icon: FileText, tone: 'teal' as const },
    { label: '선결제 차감', value: `${formatNumber(metrics.prepaymentDeliveryCount)}건`, detail: formatWon(metrics.prepaymentUsedAmount), icon: CircleDollarSign, tone: metrics.prepaymentDeliveryCount > 0 ? 'amber' as const : 'blue' as const },
    { label: '선결제 잔액', value: formatWon(metrics.prepaymentBalance), detail: `${formatNumber(metrics.prepaymentCount)}건`, icon: CheckCircle2, tone: 'green' as const },
    { label: '서비스', value: `${formatNumber(metrics.serviceCount)}건`, detail: `진행 ${formatNumber(metrics.openServiceCount)}건`, icon: Wrench, tone: metrics.openServiceCount > 0 ? 'amber' as const : 'blue' as const },
  ];
  const dateRangeLabel = `${formatDateLabel(data.filters.dateFrom) || data.filters.dateFrom} - ${formatDateLabel(data.filters.dateTo) || data.filters.dateTo}`;
  const generatedLabel = data.generatedAt ? formatDateTimeLabel(data.generatedAt) : '';
  const cleanupMetrics = dataQuality.metrics;
  const cleanupCards = [
    { label: '계정명 유사', value: `${formatNumber(cleanupMetrics.duplicateAccountGroups)}그룹` },
    { label: '담당자 중복', value: `${formatNumber(cleanupMetrics.duplicateContactGroups)}그룹` },
    { label: '부서 미지정', value: `${formatNumber(cleanupMetrics.contactsWithoutDepartment)}명` },
    { label: '업체 미지정', value: `${formatNumber(cleanupMetrics.contactsWithoutCompany)}명` },
  ];
  const hasCleanupCandidates = cleanupMetrics.cleanupCandidateCount > 0;
  const unassignedContacts: ReportsDataQualityContact[] = [
    ...dataQuality.contactsWithoutDepartment,
    ...dataQuality.contactsWithoutCompany.filter((contact) => (
      !dataQuality.contactsWithoutDepartment.some((item) => item.id === contact.id)
    )),
  ];
  const selectedQuickFixContact = unassignedContacts.find((contact) => String(contact.id) === quickFixContactId) ?? unassignedContacts[0] ?? null;
  const buildCleanupDecisionPayload = (
    candidate: Partial<AccountCleanupDecisionPayload>,
    decision: AccountCleanupDecisionPayload['decision'],
    label: string,
  ): AccountCleanupDecisionPayload | null => {
    if (!candidate.candidateType || !candidate.candidateKey) {
      return null;
    }
    return {
      candidateType: candidate.candidateType,
      candidateKey: candidate.candidateKey,
      decision,
      label,
      decisionUrl: candidate.decisionUrl,
      sourceDepartmentId: candidate.sourceDepartmentId ?? null,
      targetDepartmentId: candidate.targetDepartmentId ?? null,
      sourceFollowupId: candidate.sourceFollowupId ?? null,
      targetFollowupId: candidate.targetFollowupId ?? null,
    };
  };
  const handleCleanupDecision = async (
    candidate: Partial<AccountCleanupDecisionPayload>,
    decision: AccountCleanupDecisionPayload['decision'],
    label: string,
  ) => {
    const payload = buildCleanupDecisionPayload(candidate, decision, label);
    if (!payload) {
      setCleanupActionMessage('후보 키가 없어 처리할 수 없습니다.');
      return;
    }
    setCleanupActionLoadingKey(`${payload.candidateKey}:${decision}`);
    setCleanupActionMessage('');
    try {
      const result = await saveAccountCleanupDecision(payload);
      setCleanupActionMessage(result.message || '정리 후보 판단을 저장했습니다.');
      onRefresh();
    } catch (error) {
      setCleanupActionMessage(error instanceof Error ? error.message : '정리 후보 판단 저장에 실패했습니다.');
    } finally {
      setCleanupActionLoadingKey('');
    }
  };
  const handleQuickFixSearch = async () => {
    if (!quickFixQuery.trim()) {
      setQuickFixResults([]);
      setQuickFixTarget(null);
      return;
    }
    setQuickFixLoading(true);
    setCleanupActionMessage('');
    try {
      const results = await searchAccountCleanupTargets(quickFixQuery.trim());
      setQuickFixResults(results);
      setQuickFixTarget(results[0] ?? null);
    } finally {
      setQuickFixLoading(false);
    }
  };
  const handleQuickFixAssign = async () => {
    const contact = selectedQuickFixContact;
    if (!contact || !quickFixTarget) {
      setCleanupActionMessage('담당자와 대상 계정을 선택해주세요.');
      return;
    }
    setQuickFixSubmitting(true);
    setCleanupActionMessage('');
    try {
      const result = await assignDataQualityContactAccount(contact.id, quickFixTarget.id);
      setCleanupActionMessage(result.message || '담당자를 계정에 연결했습니다.');
      setQuickFixContactId('');
      setQuickFixQuery('');
      setQuickFixResults([]);
      setQuickFixTarget(null);
      onRefresh();
    } catch (error) {
      setCleanupActionMessage(error instanceof Error ? error.message : '계정 연결에 실패했습니다.');
    } finally {
      setQuickFixSubmitting(false);
    }
  };
  const renderCleanupDecisionActions = (
    candidate: Partial<AccountCleanupDecisionPayload> & { reviewStatus?: string; reviewStatusLabel?: string },
    label: string,
  ) => {
    if (!candidate.candidateType || !candidate.candidateKey) {
      return null;
    }
    const loadingPrefix = `${candidate.candidateKey}:`;
    return (
      <div className="reports-quality-decision-actions">
        {candidate.reviewStatusLabel ? <span>{candidate.reviewStatusLabel}</span> : null}
        <button
          className="reports-quality-decision-button"
          disabled={cleanupActionLoadingKey.startsWith(loadingPrefix)}
          onClick={() => handleCleanupDecision(candidate, candidate.reviewStatus === 'hold' ? 'active' : 'hold', label)}
          type="button"
        >
          {candidate.reviewStatus === 'hold' ? '다시 검토' : '보류'}
        </button>
        <button
          className="reports-quality-decision-button danger"
          disabled={cleanupActionLoadingKey.startsWith(loadingPrefix)}
          onClick={() => handleCleanupDecision(candidate, 'dismissed', label)}
          type="button"
        >
          제외
        </button>
      </div>
    );
  };
  const selectedCompanyId = companyId || (data.filters.companyId ? String(data.filters.companyId) : '');
  const selectedDepartmentId = departmentId || (data.filters.departmentId ? String(data.filters.departmentId) : '');
  const selectedDeliveryFilter = deliveryFilter || data.filters.deliveryFilter || 'any';
  const selectedPrepaymentBalanceFilter = prepaymentBalanceFilter || data.filters.prepaymentBalanceFilter || 'any';
  const selectedExportScope = exportScope || data.filters.exportScope || 'filtered';
  const selectedQuery = query || data.filters.query || '';
  const departmentOptions = selectedCompanyId
    ? data.scope.departments.filter((department) => String(department.companyId ?? '') === selectedCompanyId)
    : data.scope.departments;
  const excelHref = (() => {
    const [path, existingQuery = ''] = data.links.customerOperationsXlsx.split('?');
    const params = new URLSearchParams(existingQuery);
    if (selectedExportScope && selectedExportScope !== 'filtered') {
      params.set('export_scope', selectedExportScope);
    } else {
      params.delete('export_scope');
    }
    return `${path}${params.toString() ? `?${params.toString()}` : ''}`;
  })();
  const comparison = data.comparison.customerOperations;
  const previousDateRangeLabel = comparison.dateFrom && comparison.dateTo
    ? `${formatDateLabel(comparison.dateFrom) || comparison.dateFrom} - ${formatDateLabel(comparison.dateTo) || comparison.dateTo}`
    : '';
  const comparisonCards = [
    { label: '납품 증감', value: `${formatSignedNumber(comparison.deltas.deliveryCount ?? 0)}건`, detail: `${formatSignedWon(comparison.deltas.deliveryAmount ?? 0)} · 이전 ${formatNumber(comparison.metrics.deliveryCount ?? 0)}건` },
    { label: '견적 증감', value: `${formatSignedNumber(comparison.deltas.quoteCount ?? 0)}건`, detail: `${formatSignedWon(comparison.deltas.quoteAmount ?? 0)} · 이전 ${formatNumber(comparison.metrics.quoteCount ?? 0)}건` },
    { label: '선결제 차감 증감', value: `${formatSignedNumber(comparison.deltas.prepaymentDeliveryCount ?? 0)}건`, detail: `${formatSignedWon(comparison.deltas.prepaymentUsedAmount ?? 0)} · 이전 ${formatNumber(comparison.metrics.prepaymentDeliveryCount ?? 0)}건` },
    { label: '서비스 증감', value: `${formatSignedNumber(comparison.deltas.serviceCount ?? 0)}건`, detail: `진행 ${formatSignedNumber(comparison.deltas.openServiceCount ?? 0)}건` },
  ];

  const lastDateLabel = (value: string | null) => formatDateLabel(value) || '-';

  return (
    <section className="reports-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>리포트 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Reports</span>
          <h2>부서/연구실 계정별 납품/견적 현황</h2>
          <p>{data.scope.label || '현재 범위'} · {dateRangeLabel} · 선결제 잔액은 현재 기준</p>
        </div>
        <div className="reports-actions">
          {data.scope.canExport ? (
            <a className="route-secondary-action" href={excelHref}>
              <Download size={15} />
              현황 엑셀
            </a>
          ) : null}
          <a className="route-secondary-action" href="/customers/"><Users size={15} />고객 목록</a>
          <button className="icon-button" onClick={onRefresh} type="button" aria-label="리포트 새로고침">
            <RefreshCw size={17} />
          </button>
        </div>
      </div>

      <div className="reports-control-band">
        <div className="reports-filter-bar">
          <label className="reports-filter-wide">
            <span>업체/부서/담당자</span>
            <input
              type="search"
              value={selectedQuery}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="계정, 업체, 담당자 검색"
            />
          </label>
          <label>
            <span>업체</span>
            <select value={selectedCompanyId} onChange={(event) => onCompanyChange(event.target.value)}>
              <option value="">전체</option>
              {data.scope.companies.map((company) => (
                <option key={company.id} value={company.id}>{company.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>부서/연구실</span>
            <select value={selectedDepartmentId} onChange={(event) => onDepartmentChange(event.target.value)}>
              <option value="">전체</option>
              {departmentOptions.map((department) => (
                <option key={department.id} value={department.id}>
                  {selectedCompanyId ? department.name : `${department.companyName} · ${department.name}`}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>시작일</span>
            <input type="date" value={dateFrom || data.filters.dateFrom} onChange={(event) => onDateFromChange(event.target.value)} />
          </label>
          <label>
            <span>종료일</span>
            <input type="date" value={dateTo || data.filters.dateTo} onChange={(event) => onDateToChange(event.target.value)} />
          </label>
          {data.scope.canFilterUsers ? (
            <label>
              <span>담당자</span>
              <select value={userId} onChange={(event) => onUserChange(event.target.value)}>
                <option value="">전체</option>
                {data.scope.salespeople.map((user) => (
                  <option key={user.id} value={user.id}>{user.name}</option>
                ))}
              </select>
            </label>
          ) : null}
          <label>
            <span>납품</span>
            <select value={selectedDeliveryFilter} onChange={(event) => onDeliveryFilterChange(event.target.value)}>
              <option value="any">전체</option>
              <option value="with">납품 있음</option>
              <option value="without">납품 없음</option>
            </select>
          </label>
          <label>
            <span>선결제 잔액</span>
            <select value={selectedPrepaymentBalanceFilter} onChange={(event) => onPrepaymentBalanceFilterChange(event.target.value)}>
              <option value="any">전체</option>
              <option value="with">잔액 있음</option>
              <option value="without">잔액 없음</option>
            </select>
          </label>
          {data.scope.canExport ? (
            <label>
              <span>엑셀 범위</span>
              <select value={selectedExportScope} onChange={(event) => onExportScopeChange(event.target.value)}>
                <option value="filtered">현재 필터</option>
                <option value="all">전체 계정</option>
                <option value="deliveries">납품 있는 계정</option>
                <option value="prepayment_balance">선결제 잔액 계정</option>
                <option value="cleanup_candidates">정리 후보 계정</option>
              </select>
            </label>
          ) : null}
        </div>
        <div className="reports-signal-strip">
          <div>
            <Users size={16} />
            <span>표시 계정</span>
            <strong>{formatNumber(metrics.totalCustomers)}개</strong>
          </div>
          <div className={metrics.prepaymentDeliveryCount > 0 ? 'stable' : ''}>
            <CircleDollarSign size={16} />
            <span>선결제 차감 납품</span>
            <strong>{formatNumber(metrics.prepaymentDeliveryCount)}건</strong>
          </div>
          <div>
            <CalendarDays size={16} />
            <span>일반 납품</span>
            <strong>{formatNumber(metrics.normalDeliveryCount)}건</strong>
          </div>
          <div>
            <Clock size={16} />
            <span>갱신</span>
            <strong>{generatedLabel || '방금'}</strong>
          </div>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid reports-metric-grid" aria-label="고객 운영 핵심 지표">
        {metricCards.map((metric) => (
          <DashboardMetricCard
            detail={metric.detail}
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      <section className="dashboard-panel reports-comparison-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Period comparison</span>
            <h2>직전 기간 비교</h2>
          </div>
          <ArrowRightLeft size={18} />
        </div>
        <p className="reports-quality-rule">
          현재 선택 기간과 동일한 길이의 직전 기간을 비교합니다{previousDateRangeLabel ? `: ${previousDateRangeLabel}` : ''}.
        </p>
        <div className="reports-comparison-grid">
          {comparisonCards.map((card) => (
            <span key={card.label}>
              {card.label}
              <strong className={(card.value.startsWith('+') ? 'positive' : card.value.startsWith('-') ? 'negative' : '')}>{card.value}</strong>
              <small>{card.detail}</small>
            </span>
          ))}
        </div>
      </section>

      <section className="dashboard-panel reports-quality-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Data cleanup</span>
            <h2>데이터 정리 후보</h2>
          </div>
          <AlertTriangle size={18} />
        </div>
        <div className="reports-quality-metrics">
          {cleanupCards.map((card) => (
            <span key={card.label}>
              {card.label}
              <strong>{card.value}</strong>
            </span>
          ))}
        </div>
        {cleanupActionMessage ? (
          <div className="reports-quality-action-message">{cleanupActionMessage}</div>
        ) : null}
        {hasCleanupCandidates ? (
          <>
            <p className="reports-quality-rule">{dataQuality.normalizationRule || '중복/누락 후보를 읽기 전용으로 표시합니다.'}</p>
            {unassignedContacts.length > 0 ? (
              <div className="reports-quality-quickfix">
                <div>
                  <strong>미지정 담당자 빠른 수정</strong>
                  <span>{formatNumber(unassignedContacts.length)}명 대기</span>
                </div>
                <label>
                  <span>담당자</span>
                  <select
                    value={quickFixContactId || (selectedQuickFixContact ? String(selectedQuickFixContact.id) : '')}
                    onChange={(event) => setQuickFixContactId(event.target.value)}
                  >
                    {unassignedContacts.map((contact) => (
                      <option key={contact.id} value={contact.id}>
                        {contact.name} · {contact.companyName || '업체 미지정'} · {contact.departmentName || '부서 미지정'}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>대상 계정</span>
                  <div className="reports-quality-search-row">
                    <input
                      type="search"
                      value={quickFixQuery}
                      onChange={(event) => setQuickFixQuery(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter') {
                          event.preventDefault();
                          handleQuickFixSearch();
                        }
                      }}
                      placeholder="업체, 부서, 담당자 검색"
                    />
                    <button disabled={quickFixLoading} onClick={handleQuickFixSearch} type="button">
                      {quickFixLoading ? <Loader2 className="spin-icon" size={14} /> : <Search size={14} />}
                      검색
                    </button>
                  </div>
                </label>
                {quickFixResults.length > 0 ? (
                  <div className="reports-quality-target-results">
                    {quickFixResults.slice(0, 5).map((result) => (
                      <button
                        className={quickFixTarget?.id === result.id ? 'selected' : ''}
                        key={result.id}
                        onClick={() => setQuickFixTarget(result)}
                        type="button"
                      >
                        <strong>{result.companyName} · {result.departmentName}</strong>
                        <span>{result.meta || result.contactPreview.join(', ')}</span>
                      </button>
                    ))}
                  </div>
                ) : null}
                <button
                  className="route-secondary-action"
                  disabled={!selectedQuickFixContact || !quickFixTarget || quickFixSubmitting}
                  onClick={handleQuickFixAssign}
                  type="button"
                >
                  {quickFixSubmitting ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
                  계정 연결
                </button>
              </div>
            ) : null}
            <div className="reports-quality-grid">
              <section>
                <h3>계정명 유사 후보</h3>
                {dataQuality.duplicateAccounts.length > 0 ? (
                  <div className="reports-quality-list">
                    {dataQuality.duplicateAccounts.map((group) => (
                      <article key={`${group.companyName}-${group.normalizedDepartmentName}`}>
                        <div className="reports-quality-card-head">
                          <strong>{group.companyName || '업체 미지정'}</strong>
                          <span>{group.riskLabel || '검토 필요'}</span>
                        </div>
                        {group.cleanupPreviewHref ? (
                          <div className="reports-quality-actions">
                            <a className="reports-quality-preview-link" href={group.cleanupPreviewHref}>
                              <MoveUpRight size={14} />
                              정리 영향 미리보기
                            </a>
                          </div>
                        ) : null}
                        {renderCleanupDecisionActions(group, `${group.companyName || '업체 미지정'} · ${group.departmentNames.join(', ')}`)}
                        <span>{group.departmentNames.join(', ') || '부서명 없음'} · 담당자 {formatNumber(group.contactCount)}명 · 기록 {formatNumber(group.recordCount)}건</span>
                        <small>{group.suggestedAction}</small>
                        {group.departments.length > 0 ? (
                          <div className="reports-quality-detail-list">
                            {group.departments.map((department) => (
                              <div className="reports-quality-detail-row" key={department.id}>
                                <a href={department.accountHref}>
                                  <strong>{department.name}</strong>
                                  <small>담당자 {formatNumber(department.contactCount)}명 · 기록 {formatNumber(department.recordCount)}건</small>
                                </a>
                                {department.cleanupPreviewHref ? (
                                  <a className="reports-quality-mini-action" href={department.cleanupPreviewHref}>
                                    미리보기
                                  </a>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <small>부서 ID {group.departmentIds.join(', ')}</small>
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <DashboardEmpty label="계정명 유사 후보 없음" />
                )}
              </section>
              <section>
                <h3>담당자 중복 후보</h3>
                {dataQuality.duplicateContacts.length > 0 ? (
                  <div className="reports-quality-list">
                    {dataQuality.duplicateContacts.map((group) => (
                      <article key={`${group.companyName}-${group.departmentName}-${group.identity}`}>
                        <div className="reports-quality-card-head">
                          <strong>{group.identity}</strong>
                          <span>{group.riskLabel || '검토 필요'}</span>
                        </div>
                        {renderCleanupDecisionActions(group, `${group.identity} · ${group.companyName || ''} ${group.departmentName || ''}`)}
                        <span>{[group.companyName, group.departmentName].filter(Boolean).join(' · ') || '계정 미지정'} · 담당자 {formatNumber(group.contactCount)}명 · 기록 {formatNumber(group.recordCount)}건</span>
                        <small>{group.suggestedAction}</small>
                        <div className="reports-quality-detail-list">
                          {group.contacts.map((contact) => (
                            <a href={contact.href} key={contact.id}>
                              <strong>{contact.name}</strong>
                              <small>{contact.recordSummary}</small>
                            </a>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <DashboardEmpty label="담당자 중복 후보 없음" />
                )}
              </section>
              <section>
                <h3>부서 미지정 담당자</h3>
                {dataQuality.contactsWithoutDepartment.length > 0 ? (
                  <div className="reports-quality-list">
                    {dataQuality.contactsWithoutDepartment.map((contact) => (
                      <article key={contact.id}>
                        <a href={contact.href}><strong>{contact.name}</strong></a>
                        {renderCleanupDecisionActions(contact, `${contact.name} · 부서 미지정`)}
                        <span>{contact.companyName || '업체 미지정'} · 기록 {formatNumber(contact.recordCount)}건</span>
                        <small>{[contact.email, contact.phone, contact.ownerName].filter(Boolean).join(' · ') || '연락처 없음'}</small>
                      </article>
                    ))}
                  </div>
                ) : (
                  <DashboardEmpty label="부서 미지정 담당자 없음" />
                )}
              </section>
              <section>
                <h3>업체 미지정 담당자</h3>
                {dataQuality.contactsWithoutCompany.length > 0 ? (
                  <div className="reports-quality-list">
                    {dataQuality.contactsWithoutCompany.map((contact) => (
                      <article key={contact.id}>
                        <a href={contact.href}><strong>{contact.name}</strong></a>
                        {renderCleanupDecisionActions(contact, `${contact.name} · 업체 미지정`)}
                        <span>{contact.departmentName || '부서 미지정'} · 기록 {formatNumber(contact.recordCount)}건</span>
                        <small>{[contact.email, contact.phone, contact.ownerName].filter(Boolean).join(' · ') || '연락처 없음'}</small>
                      </article>
                    ))}
                  </div>
                ) : (
                  <DashboardEmpty label="업체 미지정 담당자 없음" />
                )}
              </section>
            </div>
            {dataQuality.history.length > 0 ? (
              <section className="reports-quality-history">
                <h3>최근 정리 이력</h3>
                <div>
                  {dataQuality.history.map((item) => (
                    <article key={item.id}>
                      <div>
                        <strong>{item.title}</strong>
                        <span>{item.statusLabel}</span>
                      </div>
                      <small>{[item.detail, item.actorName, item.createdAt ? formatDateTimeLabel(item.createdAt) : ''].filter(Boolean).join(' · ')}</small>
                      {item.kind === 'decision' && item.candidateType && item.candidateKey ? (
                        <button
                          className="reports-quality-decision-button"
                          disabled={cleanupActionLoadingKey.startsWith(`${item.candidateKey}:`)}
                          onClick={() => handleCleanupDecision(item, 'active', item.detail || item.title)}
                          type="button"
                        >
                          복구
                        </button>
                      ) : null}
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
          </>
        ) : (
          <div className="reports-quality-empty-state">
            <CheckCircle2 size={19} />
            <div>
              <strong>현재 범위 데이터 정리 후보 없음</strong>
              <span>납품, 견적, 선결제 현황은 위 계정별 운영 현황표 기준으로 확인하세요.</span>
            </div>
          </div>
        )}
      </section>

      <section className="dashboard-panel reports-customer-panel reports-operations-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Operations</span>
            <h2>계정별 운영 현황표</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <FileSpreadsheet size={18} />}
        </div>
        <div className="customers-table-wrap reports-operations-table-wrap">
          <table className="customers-table reports-operations-table">
            <thead>
              <tr>
                <th>계정</th>
                <th>담당/상태</th>
                <th>납품</th>
                <th>선결제 차감</th>
                <th>일반 납품</th>
                <th>견적</th>
                <th>선결제</th>
                <th>서비스</th>
                <th>최근 납품 품목</th>
                <th>최근일</th>
              </tr>
            </thead>
            <tbody>
              {rows.length > 0 ? rows.map((customer) => (
                <Fragment key={customer.accountKey || customer.id}>
                <tr>
                  <td className="reports-account-cell">
                    <a href={customer.href}>
                      <strong>{customer.customer || customer.company}</strong>
                      <span>{[customer.company, customer.department].filter(Boolean).join(' · ') || '업체/부서 미지정'}</span>
                    </a>
                    {customer.contactPreview?.length ? <small>담당자 {customer.contactPreview.join(', ')}{(customer.contactCount || 0) > customer.contactPreview.length ? ` 외 ${(customer.contactCount || 0) - customer.contactPreview.length}명` : ''}</small> : null}
                    {customer.cleanupCandidateCount > 0 ? (
                      <a className="reports-cleanup-badge" href={customer.cleanupPreviewHref || customer.href}>
                        <AlertTriangle size={13} />
                        {customer.cleanupRiskLabel || '정리 후보'} {formatNumber(customer.cleanupCandidateCount)}
                      </a>
                    ) : null}
                  </td>
                  <td className="reports-stack-cell">
                    <strong>{customer.owner}</strong>
                    <span className="status-pill neutral">{customer.pipelineStageLabel}</span>
                    <small>{customer.statusLabel} · {customer.priorityLabel}</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatNumber(customer.deliveryCount)}건</strong>
                    <span>{formatWon(customer.deliveryAmount)}</span>
                    <small>최근 {lastDateLabel(customer.lastDeliveryDate)}</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatNumber(customer.prepaymentDeliveryCount)}건</strong>
                    <span>{formatWon(customer.prepaymentUsedAmount)}</span>
                    <small>선결제 차감 납품</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatNumber(customer.normalDeliveryCount)}건</strong>
                    <span>{formatWon(customer.normalDeliveryAmount)}</span>
                    <small>선결제 사용 기록 없음</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatNumber(customer.quoteCount)}건</strong>
                    <span>{formatWon(customer.quoteAmount)}</span>
                    <small>최근 {lastDateLabel(customer.lastQuoteDate)}</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatWon(customer.prepaymentAmount)}</strong>
                    <span>잔액 {formatWon(customer.prepaymentBalance)}</span>
                    <small>{formatNumber(customer.prepaymentCount)}건 · 사용 {formatWon(customer.prepaymentUsedTotal)}</small>
                  </td>
                  <td className="reports-money-cell">
                    <strong>{formatNumber(customer.serviceCount)}건</strong>
                    <span>진행 {formatNumber(customer.openServiceCount)}건</span>
                    <small>최근 {lastDateLabel(customer.lastServiceDate)}</small>
                  </td>
                  <td className="reports-delivery-items-cell">
                    {customer.recentDeliveryItems.length > 0 ? (
                      <div className="reports-delivery-chip-list">
                        {customer.recentDeliveryItems.map((item, index) => (
                          <a className={item.paymentSource === 'prepayment' ? 'prepayment' : ''} href={item.href || customer.href} key={`${customer.id}-${item.date || index}-${index}`}>
                            <strong>{item.label}</strong>
                            <small>{[lastDateLabel(item.date), item.paymentSourceLabel, item.amount ? formatWon(item.amount) : ''].filter(Boolean).join(' · ')}</small>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <span className="reports-empty-cell">납품 없음</span>
                    )}
                  </td>
                  <td className="reports-stack-cell">
                    <strong>{lastDateLabel(customer.lastActivityDate)}</strong>
                    <a className="customer-row-action" href={customer.href}>
                      상세보기 <MoveUpRight size={13} />
                    </a>
                    <button
                      className="customer-row-action reports-row-toggle"
                      onClick={() => setExpandedAccountKey((current) => (current === customer.accountKey ? null : customer.accountKey))}
                      type="button"
                    >
                      {expandedAccountKey === customer.accountKey ? '접기' : '드릴다운'} <Eye size={13} />
                    </button>
                  </td>
                </tr>
                {expandedAccountKey === customer.accountKey ? (
                  <tr className="reports-drilldown-row">
                    <td colSpan={10}>
                      <ReportsAccountDrilldown customer={customer} />
                    </td>
                  </tr>
                ) : null}
                </Fragment>
              )) : (
                <tr><td colSpan={10}>표시할 고객 운영 기록이 없습니다.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

function ReportsAccountDrilldown({ customer }: { customer: ReportsData['customerOperations']['rows'][number] }) {
  const renderRecords = (
    records: ReportsData['customerOperations']['rows'][number]['drilldown']['deliveries'],
    emptyLabel: string,
    amountLabel = '금액',
  ) => (
    records.length > 0 ? (
      <div className="reports-drilldown-list">
        {records.map((record, index) => (
          <a href={record.href || customer.href} key={`${record.id}-${index}`}>
            <strong>{record.label || '기록'}</strong>
            <span>{[lastDateForReport(record.date), record.customerName, record.statusLabel || record.paymentStatusLabel].filter(Boolean).join(' · ')}</span>
            <small>
              {[
                typeof record.amount === 'number' ? `${amountLabel} ${formatWon(record.amount)}` : '',
                typeof record.balance === 'number' ? `잔액 ${formatWon(record.balance)}` : '',
                record.ownerName,
              ].filter(Boolean).join(' · ')}
            </small>
          </a>
        ))}
      </div>
    ) : <DashboardEmpty label={emptyLabel} />
  );

  return (
    <div className="reports-drilldown-grid">
      <section>
        <h3>담당자</h3>
        {customer.drilldown.contacts.length > 0 ? (
          <div className="reports-drilldown-list compact">
            {customer.drilldown.contacts.map((contact) => (
              <a href={contact.href} key={contact.id}>
                <strong>{contact.name}</strong>
                <span>{[contact.roleLabel, contact.manager, contact.ownerName].filter(Boolean).join(' · ')}</span>
                <small>{[contact.email, contact.phone].filter(Boolean).join(' · ') || '연락처 없음'}</small>
              </a>
            ))}
          </div>
        ) : <DashboardEmpty label="담당자가 없습니다" />}
      </section>
      <section>
        <h3>납품</h3>
        {renderRecords(customer.drilldown.deliveries, '납품 기록 없음')}
      </section>
      <section>
        <h3>견적</h3>
        {renderRecords(customer.drilldown.quotes, '견적 기록 없음')}
      </section>
      <section>
        <h3>선결제</h3>
        {renderRecords(customer.drilldown.prepayments, '선결제 기록 없음', '입금')}
      </section>
      <section>
        <h3>서비스</h3>
        {renderRecords(customer.drilldown.services, '서비스 기록 없음')}
      </section>
      <section>
        <h3>연결</h3>
        <div className="reports-drilldown-actions">
          <a href={customer.links.account || customer.href}>계정 상세</a>
          {customer.links.prepayments ? <a href={customer.links.prepayments}>선결제 현황</a> : null}
          {customer.links.cleanupPreview ? <a href={customer.links.cleanupPreview}>정리 영향</a> : null}
          {customer.links.customer ? <a href={customer.links.customer}>대표 담당자</a> : null}
        </div>
      </section>
    </div>
  );
}

function lastDateForReport(value?: string | null) {
  return formatDateLabel(value) || '';
}
