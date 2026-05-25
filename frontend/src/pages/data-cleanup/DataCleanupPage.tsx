import {
  AlertTriangle,
  ArrowRightLeft,
  Check,
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
  MoveUpRight,
  RefreshCw,
  Search,
  ShieldCheck,
  Undo2,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import type {
  AccountCleanupDecisionPayload,
  AccountCleanupMergeResponse,
  AccountCleanupSearchResult,
  ReportsData,
  ReportsDataQualityContact,
  ReportsDuplicateAccountGroup,
  ReportsDuplicateContactGroup,
} from '../../api';
import {
  assignDataQualityContactAccount,
  runContactCleanupMerge,
  runDepartmentCleanupMerge,
  saveAccountCleanupDecision,
  searchAccountCleanupTargets,
} from '../../api';
import { DashboardEmpty } from '../../components/shared/DashboardEmpty';
import { formatDateTimeLabel, formatNumber } from '../../components/shared/formatters';

type CleanupCandidate = Partial<AccountCleanupDecisionPayload> & {
  reviewStatus?: string;
  reviewStatusLabel?: string;
};

type MergeSelection = {
  type: 'department' | 'contact';
  title: string;
  sourceId: number;
  targetId: number;
};

export function DataCleanupPage({
  data,
  loading,
  onRefresh,
}: {
  data: ReportsData | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const [actionMessage, setActionMessage] = useState('');
  const [decisionLoadingKey, setDecisionLoadingKey] = useState('');
  const [mergeSelection, setMergeSelection] = useState<MergeSelection | null>(null);
  const [mergeResult, setMergeResult] = useState<AccountCleanupMergeResponse | null>(null);
  const [mergeLoading, setMergeLoading] = useState(false);
  const [mergeError, setMergeError] = useState('');
  const [confirmationText, setConfirmationText] = useState('');
  const [quickFixContactId, setQuickFixContactId] = useState('');
  const [quickFixQuery, setQuickFixQuery] = useState('');
  const [quickFixResults, setQuickFixResults] = useState<AccountCleanupSearchResult[]>([]);
  const [quickFixTarget, setQuickFixTarget] = useState<AccountCleanupSearchResult | null>(null);
  const [quickFixLoading, setQuickFixLoading] = useState(false);
  const [quickFixSubmitting, setQuickFixSubmitting] = useState(false);

  const dataQuality = data?.dataQuality;
  const unassignedContacts = useMemo<ReportsDataQualityContact[]>(() => {
    if (!dataQuality) return [];
    return [
      ...dataQuality.contactsWithoutDepartment,
      ...dataQuality.contactsWithoutCompany.filter((contact) => (
        !dataQuality.contactsWithoutDepartment.some((item) => item.id === contact.id)
      )),
    ];
  }, [dataQuality]);
  const selectedQuickFixContact = unassignedContacts.find((contact) => String(contact.id) === quickFixContactId) ?? unassignedContacts[0] ?? null;

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>데이터 정리 후보를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !dataQuality) {
    return null;
  }

  const metrics = dataQuality.metrics;
  const candidateCount = metrics.cleanupCandidateCount || 0;
  const heldCount = metrics.heldCandidateCount || 0;
  const dismissedCount = metrics.dismissedCandidateCount || 0;

  const buildDecisionPayload = (
    candidate: CleanupCandidate,
    decision: AccountCleanupDecisionPayload['decision'],
    label: string,
  ): AccountCleanupDecisionPayload | null => {
    if (!candidate.candidateType || !candidate.candidateKey) return null;
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

  const handleDecision = async (
    candidate: CleanupCandidate,
    decision: AccountCleanupDecisionPayload['decision'],
    label: string,
  ) => {
    const payload = buildDecisionPayload(candidate, decision, label);
    if (!payload) {
      setActionMessage('후보 키가 없어 처리할 수 없습니다.');
      return;
    }
    setDecisionLoadingKey(`${payload.candidateKey}:${decision}`);
    setActionMessage('');
    try {
      const result = await saveAccountCleanupDecision(payload);
      setActionMessage(result.message || '정리 후보 판단을 저장했습니다.');
      onRefresh();
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : '정리 후보 판단 저장에 실패했습니다.');
    } finally {
      setDecisionLoadingKey('');
    }
  };

  const runMerge = async (selection: MergeSelection, mode: 'dry_run' | 'execute', confirmation = '') => {
    setMergeSelection(selection);
    setMergeLoading(true);
    setMergeError('');
    setActionMessage('');
    try {
      const result = selection.type === 'department'
        ? await runDepartmentCleanupMerge(selection.sourceId, {
          mode,
          targetDepartmentId: selection.targetId,
          confirmationText: confirmation,
        })
        : await runContactCleanupMerge(selection.sourceId, {
          mode,
          targetFollowupId: selection.targetId,
          confirmationText: confirmation,
        });
      setMergeResult(result);
      setConfirmationText('');
      if (result.executed) {
        setActionMessage(`정리 실행 완료: AuditLog #${result.auditLogId}`);
        onRefresh();
      }
    } catch (error) {
      setMergeError(error instanceof Error ? error.message : '정리 dry-run/실행 요청에 실패했습니다.');
    } finally {
      setMergeLoading(false);
    }
  };

  const handleQuickFixSearch = async () => {
    if (!quickFixQuery.trim()) {
      setQuickFixResults([]);
      setQuickFixTarget(null);
      return;
    }
    setQuickFixLoading(true);
    setActionMessage('');
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
      setActionMessage('담당자와 대상 계정을 선택해주세요.');
      return;
    }
    setQuickFixSubmitting(true);
    setActionMessage('');
    try {
      const result = await assignDataQualityContactAccount(contact.id, quickFixTarget.id);
      setActionMessage(result.message || '담당자를 계정에 연결했습니다.');
      setQuickFixContactId('');
      setQuickFixQuery('');
      setQuickFixResults([]);
      setQuickFixTarget(null);
      onRefresh();
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : '계정 연결에 실패했습니다.');
    } finally {
      setQuickFixSubmitting(false);
    }
  };

  const renderDecisionActions = (candidate: CleanupCandidate, label: string) => {
    if (!candidate.candidateType || !candidate.candidateKey) return null;
    const loadingPrefix = `${candidate.candidateKey}:`;
    return (
      <div className="data-cleanup-actions">
        {candidate.reviewStatusLabel ? <span>{candidate.reviewStatusLabel}</span> : null}
        <button
          disabled={decisionLoadingKey.startsWith(loadingPrefix)}
          onClick={() => handleDecision(candidate, candidate.reviewStatus === 'hold' ? 'active' : 'hold', label)}
          type="button"
        >
          {candidate.reviewStatus === 'hold' ? '다시 검토' : '보류'}
        </button>
        <button
          className="danger"
          disabled={decisionLoadingKey.startsWith(loadingPrefix)}
          onClick={() => handleDecision(candidate, 'dismissed', label)}
          type="button"
        >
          제외
        </button>
      </div>
    );
  };

  return (
    <section className="data-cleanup-page">
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Data cleanup</span>
          <h2>데이터 품질/정리 도구</h2>
          <p>후보 검수, dry-run, 관리자 확인 실행, 보류/제외, audit log를 한 화면에서 처리합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <button className="route-secondary-action" disabled={loading} onClick={onRefresh} type="button">
            {loading ? <Loader2 className="spin-icon" size={15} /> : <RefreshCw size={15} />}
            새로고침
          </button>
          <a className="route-secondary-action" href="/reports/?export_scope=cleanup_candidates">
            <FileSpreadsheet size={15} />
            현황표
          </a>
        </div>
      </div>

      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>데이터 정리 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <section className="data-cleanup-metrics" aria-label="데이터 정리 지표">
        <CleanupMetric label="전체 후보" value={`${formatNumber(candidateCount)}건`} detail={`보류 ${formatNumber(heldCount)} · 제외 ${formatNumber(dismissedCount)}`} />
        <CleanupMetric label="계정명 유사" value={`${formatNumber(metrics.duplicateAccountGroups)}그룹`} detail="Department 병합 후보" />
        <CleanupMetric label="담당자 중복" value={`${formatNumber(metrics.duplicateContactGroups)}그룹`} detail="FollowUp 병합 후보" />
        <CleanupMetric label="미지정" value={`${formatNumber(metrics.contactsWithoutDepartment + metrics.contactsWithoutCompany)}건`} detail="빠른 계정 연결 대상" />
      </section>

      {actionMessage ? <div className="reports-quality-action-message">{actionMessage}</div> : null}

      <div className="data-cleanup-layout">
        <div className="data-cleanup-main">
          <section className="dashboard-panel data-cleanup-panel">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Candidates</span>
                <h2>계정 정리 후보 목록</h2>
              </div>
              <AlertTriangle size={18} />
            </div>
            <p className="reports-quality-rule">{dataQuality.normalizationRule || '정규화 규칙으로 중복/누락 후보를 찾습니다.'}</p>
            <DuplicateAccountList
              groups={dataQuality.duplicateAccounts}
              onDecision={renderDecisionActions}
              onDryRun={(group) => {
                if (group.sourceDepartmentId && group.targetDepartmentId) {
                  void runMerge({
                    type: 'department',
                    title: `${group.companyName || '업체 미지정'} · ${group.departmentNames.join(', ')}`,
                    sourceId: group.sourceDepartmentId,
                    targetId: group.targetDepartmentId,
                  }, 'dry_run');
                }
              }}
            />
            <DuplicateContactList
              groups={dataQuality.duplicateContacts}
              onDecision={renderDecisionActions}
              onDryRun={(group) => {
                if (group.sourceFollowupId && group.targetFollowupId) {
                  void runMerge({
                    type: 'contact',
                    title: `${group.identity} · ${[group.companyName, group.departmentName].filter(Boolean).join(' · ')}`,
                    sourceId: group.sourceFollowupId,
                    targetId: group.targetFollowupId,
                  }, 'dry_run');
                }
              }}
            />
          </section>

          <QuickAssignPanel
            contacts={unassignedContacts}
            loading={quickFixLoading}
            query={quickFixQuery}
            results={quickFixResults}
            selectedContact={selectedQuickFixContact}
            selectedContactId={quickFixContactId}
            selectedTarget={quickFixTarget}
            submitting={quickFixSubmitting}
            onAssign={handleQuickFixAssign}
            onContactChange={setQuickFixContactId}
            onQueryChange={setQuickFixQuery}
            onSearch={handleQuickFixSearch}
            onTargetChange={setQuickFixTarget}
          />

          <AuditHistoryPanel
            history={dataQuality.history}
            loadingKey={decisionLoadingKey}
            onRestore={(item) => handleDecision(item, 'active', item.detail || item.title)}
          />
        </div>

        <MergePlanPanel
          confirmationText={confirmationText}
          error={mergeError}
          loading={mergeLoading}
          result={mergeResult}
          selection={mergeSelection}
          onConfirmationChange={setConfirmationText}
          onExecute={() => {
            if (mergeSelection && mergeResult) {
              void runMerge(mergeSelection, 'execute', confirmationText);
            }
          }}
        />
      </div>
    </section>
  );
}

function CleanupMetric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <article className="dashboard-metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function DuplicateAccountList({
  groups,
  onDecision,
  onDryRun,
}: {
  groups: ReportsDuplicateAccountGroup[];
  onDecision: (candidate: CleanupCandidate, label: string) => JSX.Element | null;
  onDryRun: (group: ReportsDuplicateAccountGroup) => void;
}) {
  return (
    <section className="data-cleanup-list-section">
      <h3>계정명 유사 후보</h3>
      {groups.length ? (
        <div className="data-cleanup-card-list">
          {groups.map((group) => (
            <article key={group.candidateKey || `${group.companyName}-${group.normalizedDepartmentName}`}>
              <div className="reports-quality-card-head">
                <strong>{group.companyName || '업체 미지정'}</strong>
                <span>{group.riskLabel || '검토 필요'}</span>
              </div>
              <p>{group.departmentNames.join(', ') || '부서명 없음'} · 담당자 {formatNumber(group.contactCount)}명 · 기록 {formatNumber(group.recordCount)}건</p>
              <small>{group.suggestedAction}</small>
              <div className="data-cleanup-card-actions">
                {group.cleanupPreviewHref ? (
                  <a className="route-secondary-action" href={group.cleanupPreviewHref}>
                    <MoveUpRight size={14} />
                    preview
                  </a>
                ) : null}
                <button disabled={!group.sourceDepartmentId || !group.targetDepartmentId} onClick={() => onDryRun(group)} type="button">
                  <ArrowRightLeft size={14} />
                  Department dry-run
                </button>
              </div>
              {onDecision(group, `${group.companyName || '업체 미지정'} · ${group.departmentNames.join(', ')}`)}
              <div className="reports-quality-detail-list">
                {group.departments.map((department) => (
                  <a href={department.cleanupPreviewHref || department.accountHref} key={department.id}>
                    <strong>{department.name}</strong>
                    <small>담당자 {formatNumber(department.contactCount)}명 · 기록 {formatNumber(department.recordCount)}건</small>
                  </a>
                ))}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <DashboardEmpty label="계정명 유사 후보 없음" />
      )}
    </section>
  );
}

function DuplicateContactList({
  groups,
  onDecision,
  onDryRun,
}: {
  groups: ReportsDuplicateContactGroup[];
  onDecision: (candidate: CleanupCandidate, label: string) => JSX.Element | null;
  onDryRun: (group: ReportsDuplicateContactGroup) => void;
}) {
  return (
    <section className="data-cleanup-list-section">
      <h3>담당자 중복 후보</h3>
      {groups.length ? (
        <div className="data-cleanup-card-list">
          {groups.map((group) => (
            <article key={group.candidateKey || `${group.companyName}-${group.departmentName}-${group.identity}`}>
              <div className="reports-quality-card-head">
                <strong>{group.identity}</strong>
                <span>{group.riskLabel || '검토 필요'}</span>
              </div>
              <p>{[group.companyName, group.departmentName].filter(Boolean).join(' · ') || '계정 미지정'} · 담당자 {formatNumber(group.contactCount)}명 · 기록 {formatNumber(group.recordCount)}건</p>
              <small>{group.suggestedAction}</small>
              <div className="data-cleanup-card-actions">
                <button disabled={!group.sourceFollowupId || !group.targetFollowupId} onClick={() => onDryRun(group)} type="button">
                  <ArrowRightLeft size={14} />
                  Contact dry-run
                </button>
              </div>
              {onDecision(group, `${group.identity} · ${group.companyName || ''} ${group.departmentName || ''}`)}
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
  );
}

function QuickAssignPanel({
  contacts,
  loading,
  query,
  results,
  selectedContact,
  selectedContactId,
  selectedTarget,
  submitting,
  onAssign,
  onContactChange,
  onQueryChange,
  onSearch,
  onTargetChange,
}: {
  contacts: ReportsDataQualityContact[];
  loading: boolean;
  query: string;
  results: AccountCleanupSearchResult[];
  selectedContact: ReportsDataQualityContact | null;
  selectedContactId: string;
  selectedTarget: AccountCleanupSearchResult | null;
  submitting: boolean;
  onAssign: () => void;
  onContactChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  onTargetChange: (value: AccountCleanupSearchResult) => void;
}) {
  return (
    <section className="dashboard-panel data-cleanup-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Quick fix</span>
          <h2>미지정 담당자 계정 연결</h2>
        </div>
        <Search size={18} />
      </div>
      {contacts.length ? (
        <div className="reports-quality-quickfix">
          <label>
            <span>담당자</span>
            <select value={selectedContactId || (selectedContact ? String(selectedContact.id) : '')} onChange={(event) => onContactChange(event.target.value)}>
              {contacts.map((contact) => (
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
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault();
                    onSearch();
                  }
                }}
                placeholder="업체, 부서, 담당자 검색"
              />
              <button disabled={loading} onClick={onSearch} type="button">
                {loading ? <Loader2 className="spin-icon" size={14} /> : <Search size={14} />}
                검색
              </button>
            </div>
          </label>
          {results.length ? (
            <div className="reports-quality-target-results">
              {results.slice(0, 6).map((result) => (
                <button
                  className={selectedTarget?.id === result.id ? 'selected' : ''}
                  key={result.id}
                  onClick={() => onTargetChange(result)}
                  type="button"
                >
                  <strong>{result.companyName} · {result.departmentName}</strong>
                  <span>{result.meta || result.contactPreview.join(', ')}</span>
                </button>
              ))}
            </div>
          ) : null}
          <button className="route-secondary-action" disabled={!selectedContact || !selectedTarget || submitting} onClick={onAssign} type="button">
            {submitting ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
            계정 연결
          </button>
        </div>
      ) : (
        <DashboardEmpty label="미지정 담당자가 없습니다" />
      )}
    </section>
  );
}

function MergePlanPanel({
  confirmationText,
  error,
  loading,
  result,
  selection,
  onConfirmationChange,
  onExecute,
}: {
  confirmationText: string;
  error: string;
  loading: boolean;
  result: AccountCleanupMergeResponse | null;
  selection: MergeSelection | null;
  onConfirmationChange: (value: string) => void;
  onExecute: () => void;
}) {
  return (
    <aside className="dashboard-panel data-cleanup-merge-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Dry-run / approval</span>
          <h2>병합 실행 전 검수</h2>
        </div>
        {loading ? <Loader2 className="spin-icon" size={18} /> : <ShieldCheck size={18} />}
      </div>
      {!selection ? (
        <DashboardEmpty label="후보에서 dry-run을 실행하세요" />
      ) : (
        <>
          <div className="data-cleanup-selected-merge">
            <strong>{selection.title}</strong>
            <span>{selection.type === 'department' ? 'Department merge' : 'FollowUp/contact merge'}</span>
          </div>
          {error ? <div className="form-error-message">{error}</div> : null}
          {result ? (
            <>
              <div className="data-cleanup-plan-summary">
                <span>이관 그룹 <strong>{formatNumber(result.plan.counts.groups)}</strong></span>
                <span>영향 건수 <strong>{formatNumber(result.plan.counts.transferCount)}</strong></span>
                <span>{result.canExecute ? '관리자 실행 가능' : '관리자 승인 필요'}</span>
              </div>
              {result.warnings.length ? (
                <div className="account-cleanup-warning-list">
                  {result.warnings.map((warning) => (
                    <span key={warning}><AlertTriangle size={15} />{warning}</span>
                  ))}
                </div>
              ) : null}
              <div className="customers-table-wrap data-cleanup-plan-table-wrap">
                <table className="customers-table data-cleanup-plan-table">
                  <thead>
                    <tr>
                      <th>이관 대상</th>
                      <th>건수</th>
                      <th>상세</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.plan.transfers.map((transfer) => (
                      <tr key={transfer.key}>
                        <td><strong>{transfer.label}</strong></td>
                        <td>{formatNumber(transfer.count)}</td>
                        <td>{transfer.detail}{transfer.truncated ? ` · 샘플 ${formatNumber(transfer.sampleLimit)}건만 표시` : ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {result.executed ? (
                <div className="form-success-message">
                  AuditLog #{result.auditLogId} 실행이 기록되었습니다.
                </div>
              ) : result.canExecute ? (
                <div className="data-cleanup-approval-box">
                  <strong>관리자 승인 실행</strong>
                  <span>아래 확인 문구를 그대로 입력해야 execute API가 실행됩니다.</span>
                  <code>{result.requiredConfirmationText}</code>
                  <input value={confirmationText} onChange={(event) => onConfirmationChange(event.target.value)} />
                  <button className="primary-button" disabled={confirmationText !== result.requiredConfirmationText || loading} onClick={onExecute} type="button">
                    {loading ? <Loader2 className="spin-icon" size={15} /> : <ShieldCheck size={15} />}
                    승인 후 실행
                  </button>
                </div>
              ) : (
                <div className="data-cleanup-approval-box readonly">
                  <strong>관리자 승인 필요</strong>
                  <span>실행은 admin 계정에서 같은 후보 dry-run 검토 후 확인 문구 입력으로만 가능합니다.</span>
                  <code>{result.requiredConfirmationText}</code>
                </div>
              )}
            </>
          ) : null}
        </>
      )}
    </aside>
  );
}

function AuditHistoryPanel({
  history,
  loadingKey,
  onRestore,
}: {
  history: ReportsData['dataQuality']['history'];
  loadingKey: string;
  onRestore: (item: ReportsData['dataQuality']['history'][number]) => void;
}) {
  return (
    <section className="dashboard-panel data-cleanup-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Audit log</span>
          <h2>정리 작업 이력</h2>
        </div>
        <CheckCircle2 size={18} />
      </div>
      {history.length ? (
        <div className="data-cleanup-history-list">
          {history.map((item) => (
            <article key={item.id}>
              <div>
                <strong>{item.title}</strong>
                <span>{item.statusLabel}</span>
              </div>
              <small>{[item.detail, item.actorName, item.createdAt ? formatDateTimeLabel(item.createdAt) : ''].filter(Boolean).join(' · ')}</small>
              {item.kind === 'decision' && item.candidateType && item.candidateKey ? (
                <button disabled={loadingKey.startsWith(`${item.candidateKey}:`)} onClick={() => onRestore(item)} type="button">
                  <Undo2 size={14} />
                  복구
                </button>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <DashboardEmpty label="정리 이력이 없습니다" />
      )}
    </section>
  );
}
