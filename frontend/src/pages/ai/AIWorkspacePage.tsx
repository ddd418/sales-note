import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Link2,
  Loader2,
  Search,
  Send,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { type FormEvent, type KeyboardEvent, useEffect, useMemo, useState } from 'react';
import {
  askAIWorkspaceDepartmentQuestion,
  deleteAIWorkspaceQuestionLog,
  loadAIWorkspaceData,
  loadAIWorkspaceMemories,
  loadAIWorkspaceQuestionLogDetailData,
  saveAIWorkspaceMemory,
  submitAIWorkspaceQuestionFeedback,
  toggleAIWorkspaceMemory,
  updateAIWorkspaceMemory,
  type AIWorkspaceActionEvidence,
  type AIWorkspaceData,
  type AIWorkspaceDepartment,
  type AIWorkspaceDepartmentQuestionResponse,
  type AIWorkspaceLoadParams,
  type AIWorkspaceMemoriesData,
  type AIWorkspaceMemoryFilters,
  type AIWorkspaceMemoryItem,
  type AIWorkspaceMemoryType,
  type AIWorkspaceQuestionAnswer,
  type AIWorkspaceQuestionFeedbackRating,
  type AIWorkspaceQuestionLog,
  type AIWorkspaceQuestionLogDetailData,
  type AIWorkspaceQuestionModel,
  type AIWorkspaceQuestionScope,
} from '../../api/aiWorkspace';
import { AppShell, TopBar } from '../../components/shared/CrmShell';
import { DashboardApiAlert, DashboardEmpty, DashboardLoading } from '../../components/shared/FeedbackStates';
import { CRM_CLIENT_NAVIGATION_EVENT } from '../../navigationEvents';

type AIWorkspaceMemoryEditDraft = {
  title: string;
  content: string;
  memoryType: AIWorkspaceMemoryType;
  scopeType: AIWorkspaceQuestionScope;
  departmentId: number | null;
};

function formatNumber(value: number | null | undefined) {
  return new Intl.NumberFormat('ko-KR').format(Number(value || 0));
}

function formatDateLabel(value: string | null | undefined) {
  if (!value) return '';
  const date = new Date(value.includes('T') ? value : `${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' });
}

function formatDateTimeLabel(value: string | null | undefined) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getAIWorkspaceDepartmentIdParam(): number | null {
  const value = new URLSearchParams(window.location.search).get('department_id');
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function getAIWorkspaceQuestionScopeParam(): AIWorkspaceQuestionScope {
  return new URLSearchParams(window.location.search).get('question_scope') === 'all' ? 'all' : 'department';
}

function getAIWorkspaceQuestionLogId(): number | null {
  const match = window.location.pathname.match(/^\/ai-workspace\/questions\/(\d+)\/?$/);
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function pushAIWorkspaceUrl(departmentId: number | null, questionScope: AIWorkspaceQuestionScope) {
  const params = new URLSearchParams();
  if (departmentId) params.set('department_id', String(departmentId));
  if (questionScope === 'all') params.set('question_scope', 'all');
  const query = params.toString();
  window.history.replaceState(null, '', `/ai-workspace/${query ? `?${query}` : ''}`);
}

function evidenceKey(item: AIWorkspaceActionEvidence, index: number) {
  return `${item.label}-${item.value}-${item.href || index}`;
}

function AIEvidenceList({ items, limit = 8 }: { items: AIWorkspaceActionEvidence[]; limit?: number }) {
  const rows = items.slice(0, limit).filter((item) => item.label || item.value);
  if (!rows.length) return null;
  return (
    <div className="ai-evidence-list">
      {rows.map((item, index) => (
        <span className="ai-evidence-row" key={evidenceKey(item, index)}>
          <b>{item.label || '근거'}</b>
          {item.value}
          {item.href ? (
            <a className="ai-evidence-link" href={item.href}>
              <Link2 size={12} />
              {item.linkLabel || '열기'}
            </a>
          ) : null}
        </span>
      ))}
    </div>
  );
}

function normalizedAnswer(rawAnswer: unknown, fallback = ''): AIWorkspaceQuestionAnswer {
  const answer = rawAnswer && typeof rawAnswer === 'object' ? rawAnswer as Partial<AIWorkspaceQuestionAnswer> : {};
  return {
    summary: typeof answer.summary === 'string' ? answer.summary : fallback,
    bullets: Array.isArray(answer.bullets) ? answer.bullets.filter((item): item is string => typeof item === 'string') : [],
    evidence: Array.isArray(answer.evidence)
      ? answer.evidence.filter((item): item is AIWorkspaceActionEvidence => Boolean(item && typeof item === 'object'))
      : [],
    confidence: typeof answer.confidence === 'string' ? answer.confidence : '',
  };
}

function AIWorkspaceDepartmentList({
  departments,
  selectedDepartmentId,
  onSelect,
}: {
  departments: AIWorkspaceDepartment[];
  selectedDepartmentId: number | null;
  onSelect: (department: AIWorkspaceDepartment) => void;
}) {
  const [query, setQuery] = useState('');
  const normalizedQuery = query.trim().toLowerCase();
  const hasSearchQuery = normalizedQuery.length > 0;
  const filteredDepartments = useMemo(() => {
    if (!normalizedQuery) return [];
    return departments.filter((department) => {
      const searchableText = [
        department.company,
        department.name,
        department.summary,
        department.searchText || '',
        ...department.customerPreview,
      ].join(' ').toLowerCase();
      return searchableText.includes(normalizedQuery);
    });
  }, [departments, normalizedQuery]);
  const visibleDepartments = filteredDepartments.slice(0, 6);

  if (!departments.length) return <DashboardEmpty label="AI 브리핑 대상 부서가 없습니다" />;

  return (
    <div className="ai-department-block">
      <label className="ai-department-search">
        <Search size={16} />
        <input
          onChange={(event) => setQuery(event.target.value)}
          placeholder="회사, 부서, 고객, PI/담당자 검색"
          value={query}
        />
      </label>
      <div className="ai-department-list-meta">
        <span>
          전체 {formatNumber(departments.length)}개
          {hasSearchQuery ? ` · 검색 ${formatNumber(filteredDepartments.length)}개` : ''}
        </span>
        <strong>{hasSearchQuery ? '검색 결과' : '검색 후 표시'}</strong>
      </div>
      {!hasSearchQuery ? (
        <p className="ai-department-list-hint">
          기관명, 부서/연구실명, 고객명, PI/담당자 이름을 입력하면 해당 대상만 표시됩니다.
        </p>
      ) : visibleDepartments.length ? (
        <div className="ai-department-list">
          {visibleDepartments.map((department) => {
            const selected = department.id === selectedDepartmentId;
            return (
              <button
                className={`ai-department-row ${department.hasAnalysis ? 'ready' : ''} ${selected ? 'selected' : ''}`}
                key={department.id}
                onClick={() => onSelect(department)}
                type="button"
              >
                <div>
                  <strong>{department.company || department.name}</strong>
                  <span>{[department.name, `${formatNumber(department.customerCount)}명`].filter(Boolean).join(' · ')}</span>
                  {department.summary ? <small>{department.summary}</small> : null}
                  {!department.summary && department.customerPreview.length ? <small>{department.customerPreview.join(', ')}</small> : null}
                </div>
                <div className="ai-row-meta">
                  <strong>{selected ? '선택됨' : department.hasAnalysis ? '분석 있음' : 'CRM 기록'}</strong>
                  <small>미팅 {formatNumber(department.meetingCount)} · 견적 {formatNumber(department.quoteCount)} · 납품 {formatNumber(department.deliveryCount)}</small>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <DashboardEmpty label="검색 결과가 없습니다" />
      )}
      {hasSearchQuery && filteredDepartments.length > visibleDepartments.length ? (
        <p className="ai-department-list-hint">
          {formatNumber(filteredDepartments.length - visibleDepartments.length)}개가 더 있습니다. 검색어를 더 구체적으로 입력하세요.
        </p>
      ) : null}
    </div>
  );
}

function AIWorkspaceQuestionHistoryList({
  deletingHistoryId,
  history,
  onDelete,
  onPageChange,
}: {
  deletingHistoryId: number | null;
  history: AIWorkspaceData['questionHistory'];
  onDelete: (item: AIWorkspaceQuestionLog) => void;
  onPageChange: (page: number) => void;
}) {
  return (
    <section className="ai-question-history">
      <div className="ai-question-history-head">
        <div>
          <strong>최근 브리핑 기록</strong>
          <span>{history.scopeType === 'all' ? '전체 부서' : '선택 부서'} · {formatNumber(history.total)}건</span>
        </div>
        <div className="ai-question-history-pagination">
          <button disabled={!history.hasPrevious} onClick={() => onPageChange(history.page - 1)} type="button">
            <ChevronLeft size={14} />
          </button>
          <span>{formatNumber(history.page)} / {formatNumber(history.totalPages || 1)}</span>
          <button disabled={!history.hasNext} onClick={() => onPageChange(history.page + 1)} type="button">
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
      {history.items.length ? (
        <div className="ai-question-history-list">
          {history.items.map((item) => (
            <article className="ai-question-history-card" key={item.id}>
              <a className="ai-question-history-main" href={`/ai-workspace/questions/${item.id}/`}>
                <div className="ai-question-history-meta">
                  <span>{item.scopeType === 'all' ? '전체' : item.department ? `${item.department.company} · ${item.department.name}` : '부서'}</span>
                  <small>{formatDateTimeLabel(item.createdAt)} · {item.modelLabel || item.model}</small>
                </div>
                <strong>{item.question}</strong>
                <p>{item.answerSummary || normalizedAnswer(item.answer).summary || '저장된 요약 없음'}</p>
              </a>
              <button
                className="ai-question-history-delete"
                disabled={deletingHistoryId === item.id}
                onClick={() => onDelete(item)}
                type="button"
              >
                {deletingHistoryId === item.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
              </button>
            </article>
          ))}
        </div>
      ) : (
        <DashboardEmpty label={history.scopeType === 'all' ? '전체 부서 브리핑 기록이 없습니다' : '선택 부서의 브리핑 기록이 없습니다'} />
      )}
    </section>
  );
}

function AIWorkspaceQuestionPanel({
  data,
  deletingHistoryId,
  departmentId,
  onDeleteHistory,
  onHistoryPageChange,
  onRefresh,
  onScopeChange,
  questionScope,
}: {
  data: AIWorkspaceData;
  deletingHistoryId: number | null;
  departmentId: number | null;
  onDeleteHistory: (item: AIWorkspaceQuestionLog) => void;
  onHistoryPageChange: (page: number) => void;
  onRefresh: (params?: AIWorkspaceLoadParams) => Promise<AIWorkspaceData>;
  onScopeChange: (scope: AIWorkspaceQuestionScope) => void;
  questionScope: AIWorkspaceQuestionScope;
}) {
  const [question, setQuestion] = useState('');
  const [model, setModel] = useState<AIWorkspaceQuestionModel | string>(data.defaultQuestionModel || 'gpt-5.4-nano');
  const [result, setResult] = useState<AIWorkspaceDepartmentQuestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reviewSaving, setReviewSaving] = useState('');
  const [reviewMessage, setReviewMessage] = useState('');
  const [reviewError, setReviewError] = useState('');
  const [memoryTitle, setMemoryTitle] = useState('');
  const [memoryContent, setMemoryContent] = useState('');

  useEffect(() => {
    const choices = data.questionModelChoices || [];
    if (choices.length && !choices.some((choice) => choice.id === model)) {
      setModel(data.defaultQuestionModel || choices[0].id);
    }
  }, [data.defaultQuestionModel, data.questionModelChoices, model]);

  const selectedDepartmentLabel = [
    data.featuredDepartment?.companyName,
    data.feedbackHistory.scope.departmentName || data.featuredDepartment?.departmentName,
  ].filter(Boolean).join(' · ') || '선택 부서';
  const allScopeSelected = questionScope === 'all';
  const trimmedQuestion = question.trim();
  const canSubmit = (allScopeSelected || Boolean(departmentId)) && trimmedQuestion.length >= 2 && !loading;
  const answer = result?.answer;
  const history = data.questionHistory;
  const modelChoices = data.questionModelChoices.length ? data.questionModelChoices : [{ id: 'gpt-5.4-nano', label: 'GPT-5.4 nano' }];

  async function submitQuestion() {
    if (!canSubmit) return;
    setLoading(true);
    setError('');
    setReviewMessage('');
    setReviewError('');
    try {
      const questionDepartmentId = questionScope === 'department' ? departmentId : null;
      const nextResult = await askAIWorkspaceDepartmentQuestion(questionDepartmentId, trimmedQuestion, model, questionScope);
      setResult(nextResult);
      await onRefresh({ departmentId, questionPage: 1, questionScope });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'AI 브리핑 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }

  function handleQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      void submitQuestion();
    }
  }

  function handleQuestionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion();
  }

  async function submitReview(rating: AIWorkspaceQuestionFeedbackRating) {
    if (!result || reviewSaving) return;
    setReviewSaving(rating);
    setReviewMessage('');
    setReviewError('');
    try {
      const response = await submitAIWorkspaceQuestionFeedback({
        departmentId: questionScope === 'department' ? departmentId : null,
        scopeType: questionScope,
        question: result.question,
        answer: result.answer,
        source: result.source,
        rating,
      });
      setReviewMessage(response.message || 'AI 브리핑 검수를 저장했습니다.');
      await onRefresh({ departmentId, questionPage: history.page, questionScope });
    } catch (reviewSubmitError) {
      setReviewError(reviewSubmitError instanceof Error ? reviewSubmitError.message : 'AI 브리핑 검수 저장에 실패했습니다.');
    } finally {
      setReviewSaving('');
    }
  }

  async function saveMemory(memoryType: AIWorkspaceMemoryType) {
    if (!result || reviewSaving || memoryContent.trim().length < 2) return;
    setReviewSaving(memoryType);
    setReviewMessage('');
    setReviewError('');
    try {
      const response = await saveAIWorkspaceMemory({
        departmentId: questionScope === 'department' ? departmentId : null,
        scopeType: questionScope,
        questionLogId: result.questionLog?.id ?? null,
        memoryType,
        title: memoryTitle.trim(),
        content: memoryContent.trim(),
      });
      setReviewMessage(response.message || '검수 기억을 저장했습니다.');
      setMemoryTitle('');
      setMemoryContent('');
      await onRefresh({ departmentId, questionPage: history.page, questionScope });
    } catch (memoryError) {
      setReviewError(memoryError instanceof Error ? memoryError.message : '검수 기억 저장에 실패했습니다.');
    } finally {
      setReviewSaving('');
    }
  }

  return (
    <section className="dashboard-panel ai-department-question-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">CRM briefing</span>
          <h2>CRM 브리핑 질문</h2>
        </div>
        <Sparkles size={18} />
      </div>
      <div className="ai-department-question-scope">
        <span>{allScopeSelected ? '전체 부서 기준' : selectedDepartmentLabel}</span>
        <small>{allScopeSelected ? `부서 ${formatNumber(data.metrics.departmentsWithCustomers)}개` : `고객 ${formatNumber(data.featuredDepartment?.customerCount || 0)}명`}</small>
      </div>
      <div className="segmented-control ai-question-scope-toggle" aria-label="AI 브리핑 범위">
        <button
          className={questionScope === 'department' ? 'active' : ''}
          disabled={!departmentId}
          onClick={() => onScopeChange('department')}
          type="button"
        >
          선택 부서
        </button>
        <button className={questionScope === 'all' ? 'active' : ''} onClick={() => onScopeChange('all')} type="button">
          전체 부서
        </button>
      </div>
      <div className="segmented-control ai-question-model-toggle" aria-label="AI 브리핑 모델">
        {modelChoices.map((choice) => (
          <button
            className={model === choice.id ? 'active' : ''}
            key={choice.id}
            onClick={() => setModel(choice.id)}
            type="button"
          >
            {choice.label}
          </button>
        ))}
      </div>
      <form className="ai-department-question-form" onSubmit={handleQuestionSubmit}>
        <textarea
          maxLength={600}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleQuestionKeyDown}
          placeholder="예: 현재 내가 접촉을 진행중인 고객을 근거와 링크까지 리스트업해줘"
          rows={3}
          value={question}
        />
        <div>
          <span>{formatNumber(trimmedQuestion.length)} / 600 · Ctrl+Enter</span>
          <button disabled={!canSubmit} type="submit">
            {loading ? <Loader2 className="spin-icon" size={15} /> : <Send size={15} />}
            {loading ? '브리핑 중' : '브리핑'}
          </button>
        </div>
      </form>
      {questionScope === 'department' && !departmentId ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>질문할 부서를 먼저 선택하세요.</span>
        </div>
      ) : null}
      {error ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      ) : null}
      {answer ? (
        <div className="ai-department-question-answer">
          <div className="ai-department-question-answer-head">
            <div>
              <strong>브리핑</strong>
              <span>{result?.source === 'openai' ? `${result.modelLabel || 'AI'} 브리핑` : 'CRM 기반 브리핑'} · {answer.confidence}</span>
            </div>
            {result?.questionLog?.id ? (
              <a className="ai-evidence-link" href={`/ai-workspace/questions/${result.questionLog.id}/`}>
                <Link2 size={12} />
                기록 열기
              </a>
            ) : null}
          </div>
          {answer.summary ? <p>{answer.summary}</p> : null}
          {answer.bullets.length ? (
            <ul>
              {answer.bullets.map((line) => <li key={line}>{line}</li>)}
            </ul>
          ) : null}
          <AIEvidenceList items={answer.evidence || []} />
          <div className="ai-question-feedback-box">
            <div className="ai-question-feedback-head">
              <strong>검수</strong>
              <span>잘못된 답변은 기억으로 남겨 다음 브리핑에 반영합니다.</span>
            </div>
            <div className="ai-question-feedback-options">
              <button disabled={Boolean(reviewSaving)} onClick={() => submitReview('helpful')} type="button">도움됨</button>
              <button disabled={Boolean(reviewSaving)} onClick={() => submitReview('needs_style')} type="button">근거 부족</button>
              <button disabled={Boolean(reviewSaving)} onClick={() => submitReview('incorrect')} type="button">틀림</button>
            </div>
            <div className="ai-question-feedback-form">
              <input onChange={(event) => setMemoryTitle(event.target.value)} placeholder="기억 제목" value={memoryTitle} />
              <textarea onChange={(event) => setMemoryContent(event.target.value)} placeholder="정정할 사실 또는 선호하는 브리핑 기준" value={memoryContent} />
              <div>
                <span>정정/사실 기억은 활성 상태로 저장됩니다.</span>
                <button disabled={Boolean(reviewSaving) || memoryContent.trim().length < 2} onClick={() => saveMemory('correction')} type="button">
                  기억 저장
                </button>
              </div>
            </div>
            {reviewMessage ? <p className="ai-question-feedback-message success">{reviewMessage}</p> : null}
            {reviewError ? <p className="ai-question-feedback-message error">{reviewError}</p> : null}
          </div>
        </div>
      ) : null}
      <AIWorkspaceQuestionHistoryList
        deletingHistoryId={deletingHistoryId}
        history={history}
        onDelete={onDeleteHistory}
        onPageChange={onHistoryPageChange}
      />
    </section>
  );
}

function normalizeAIWorkspaceMemoryType(value: string | undefined): AIWorkspaceMemoryType {
  return value === 'correction' || value === 'preference' ? value : 'fact';
}

function normalizeAIWorkspaceMemoryScope(value: string | undefined): AIWorkspaceQuestionScope {
  return value === 'all' ? 'all' : 'department';
}

function AIWorkspaceMemoryPanel({
  activeDepartmentId,
  data,
}: {
  activeDepartmentId: number | null;
  data: AIWorkspaceData;
}) {
  const [memoryData, setMemoryData] = useState<AIWorkspaceMemoriesData | null>(null);
  const [filters, setFilters] = useState<AIWorkspaceMemoryFilters>({ status: 'active', scope: 'any', memoryType: '', q: '', page: 1 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [savingMemoryId, setSavingMemoryId] = useState<number | null>(null);
  const [editingMemoryId, setEditingMemoryId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<AIWorkspaceMemoryEditDraft>({
    title: '',
    content: '',
    memoryType: 'fact',
    scopeType: 'department',
    departmentId: null,
  });

  async function loadMemories(nextFilters: AIWorkspaceMemoryFilters = filters) {
    setLoading(true);
    setError('');
    try {
      const result = await loadAIWorkspaceMemories(nextFilters);
      setMemoryData(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '검수 기억을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!data.permission.canUseAi) return;
    const handle = window.setTimeout(() => {
      void loadMemories(filters);
    }, 250);
    return () => window.clearTimeout(handle);
  }, [data.permission.canUseAi, filters.status, filters.scope, filters.memoryType, filters.departmentId, filters.q, filters.page]);

  function changeFilters(nextFilters: Partial<AIWorkspaceMemoryFilters>) {
    setMessage('');
    setError('');
    setFilters((previous) => ({ ...previous, ...nextFilters, page: 1 }));
  }

  function startEdit(memory: AIWorkspaceMemoryItem) {
    const scopeType = normalizeAIWorkspaceMemoryScope(memory.scopeType);
    setEditingMemoryId(memory.id);
    setEditDraft({
      title: memory.title || '',
      content: memory.content || '',
      memoryType: normalizeAIWorkspaceMemoryType(memory.memoryType),
      scopeType,
      departmentId: scopeType === 'department' ? memory.department?.id || activeDepartmentId || data.selectedDepartmentId || null : null,
    });
  }

  function cancelEdit() {
    setEditingMemoryId(null);
    setEditDraft({
      title: '',
      content: '',
      memoryType: 'fact',
      scopeType: 'department',
      departmentId: null,
    });
  }

  async function saveEdit(memory: AIWorkspaceMemoryItem) {
    if (savingMemoryId || editDraft.content.trim().length < 2) return;
    setSavingMemoryId(memory.id);
    setError('');
    setMessage('');
    try {
      const result = await updateAIWorkspaceMemory(memory.id, {
        title: editDraft.title.trim(),
        content: editDraft.content.trim(),
        memoryType: editDraft.memoryType,
        scopeType: editDraft.scopeType,
        departmentId: editDraft.scopeType === 'department' ? editDraft.departmentId : null,
      });
      setMessage(result.message || 'AI 기억을 수정했습니다.');
      cancelEdit();
      await loadMemories(filters);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'AI 기억 수정에 실패했습니다.');
    } finally {
      setSavingMemoryId(null);
    }
  }

  async function toggleMemory(memory: AIWorkspaceMemoryItem) {
    if (savingMemoryId) return;
    setSavingMemoryId(memory.id);
    setError('');
    setMessage('');
    try {
      const result = await toggleAIWorkspaceMemory(memory.id, !memory.isActive);
      setMessage(result.message || 'AI 기억 상태를 변경했습니다.');
      await loadMemories(filters);
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : 'AI 기억 상태 변경에 실패했습니다.');
    } finally {
      setSavingMemoryId(null);
    }
  }

  return (
    <section className="dashboard-panel ai-memory-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Verified memories</span>
          <h2>검수 기억</h2>
        </div>
        {loading ? <Loader2 className="spin-icon" size={18} /> : <CheckCircle2 size={18} />}
      </div>
      <div className="ai-memory-toolbar">
        <label>
          <span>상태</span>
          <select onChange={(event) => changeFilters({ status: event.target.value as AIWorkspaceMemoryFilters['status'] })} value={filters.status}>
            <option value="active">활성</option>
            <option value="inactive">비활성</option>
            <option value="all">전체</option>
          </select>
        </label>
        <label>
          <span>범위</span>
          <select onChange={(event) => changeFilters({ scope: event.target.value as AIWorkspaceMemoryFilters['scope'] })} value={filters.scope}>
            <option value="any">전체</option>
            <option value="department">부서</option>
            <option value="all">전역</option>
          </select>
        </label>
        <label>
          <span>유형</span>
          <select onChange={(event) => changeFilters({ memoryType: event.target.value as AIWorkspaceMemoryFilters['memoryType'] })} value={filters.memoryType}>
            <option value="">전체</option>
            <option value="fact">사실</option>
            <option value="correction">정정</option>
            <option value="preference">선호</option>
          </select>
        </label>
        <label className="ai-memory-search">
          <span>검색</span>
          <Search size={15} />
          <input onChange={(event) => changeFilters({ q: event.target.value })} placeholder="기억 내용 검색" value={filters.q || ''} />
        </label>
      </div>
      {memoryData ? (
        <div className="ai-memory-counts">
          <span>활성 {formatNumber(memoryData.counts.active)}</span>
          <span>비활성 {formatNumber(memoryData.counts.inactive)}</span>
          <span>필터 {formatNumber(memoryData.counts.filtered)}</span>
        </div>
      ) : null}
      {message ? <p className="ai-question-feedback-message success">{message}</p> : null}
      {error ? <p className="ai-question-feedback-message error">{error}</p> : null}
      <div className="ai-memory-list">
        {memoryData?.memories.length ? memoryData.memories.map((memory) => (
          <article className={`ai-memory-card ${memory.isActive ? '' : 'inactive'}`} key={memory.id}>
            <div className="ai-memory-card-head">
              <div>
                <span>{memory.memoryTypeLabel}</span>
                <strong>{memory.title || '제목 없음'}</strong>
                <small>
                  {memory.department ? `${memory.department.company} · ${memory.department.name}` : '전체 부서'}
                  {memory.updatedAt ? ` · ${formatDateTimeLabel(memory.updatedAt)}` : ''}
                </small>
              </div>
              <em>{memory.isActive ? '활성' : '비활성'}</em>
            </div>
            {editingMemoryId === memory.id ? (
              <div className="ai-memory-edit-form">
                <div className="ai-memory-edit-grid">
                  <input onChange={(event) => setEditDraft((draft) => ({ ...draft, title: event.target.value }))} value={editDraft.title} />
                  <select onChange={(event) => setEditDraft((draft) => ({ ...draft, memoryType: event.target.value as AIWorkspaceMemoryType }))} value={editDraft.memoryType}>
                    <option value="fact">사실</option>
                    <option value="correction">정정</option>
                    <option value="preference">선호</option>
                  </select>
                  <select onChange={(event) => setEditDraft((draft) => ({ ...draft, scopeType: event.target.value as AIWorkspaceQuestionScope }))} value={editDraft.scopeType}>
                    <option value="department">부서</option>
                    <option value="all">전역</option>
                  </select>
                </div>
                <textarea onChange={(event) => setEditDraft((draft) => ({ ...draft, content: event.target.value }))} value={editDraft.content} />
                <div className="ai-memory-edit-actions">
                  <button disabled={savingMemoryId === memory.id} onClick={() => saveEdit(memory)} type="button">저장</button>
                  <button onClick={cancelEdit} type="button">취소</button>
                </div>
              </div>
            ) : (
              <>
                <p>{memory.content}</p>
                {memory.sourceQuestion ? <span className="ai-memory-source">출처 질문: {memory.sourceQuestion}</span> : null}
                <div className="ai-memory-card-actions">
                  <button onClick={() => startEdit(memory)} type="button">수정</button>
                  <button disabled={savingMemoryId === memory.id} onClick={() => toggleMemory(memory)} type="button">
                    {memory.isActive ? '비활성화' : '활성화'}
                  </button>
                </div>
              </>
            )}
          </article>
        )) : (!loading ? <DashboardEmpty label="검수 기억이 없습니다" /> : null)}
      </div>
    </section>
  );
}

function AIWorkspaceHomePage() {
  const [data, setData] = useState<AIWorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [departmentId, setDepartmentId] = useState<number | null>(() => getAIWorkspaceDepartmentIdParam());
  const [questionScope, setQuestionScope] = useState<AIWorkspaceQuestionScope>(() => getAIWorkspaceQuestionScopeParam());
  const [deletingHistoryId, setDeletingHistoryId] = useState<number | null>(null);
  const [deleteHistoryMessage, setDeleteHistoryMessage] = useState('');
  const [deleteHistoryError, setDeleteHistoryError] = useState('');

  async function refresh(params: AIWorkspaceLoadParams = {}) {
    const nextDepartmentId = params.departmentId !== undefined ? params.departmentId : departmentId;
    const nextQuestionScope = params.questionScope ?? questionScope;
    const nextData = await loadAIWorkspaceData({
      departmentId: nextDepartmentId,
      questionPage: params.questionPage,
      questionScope: nextQuestionScope,
    });
    setData(nextData);
    setDepartmentId(nextData.selectedDepartmentId ?? nextData.featuredDepartment?.departmentId ?? null);
    return nextData;
  }

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError('');
    loadAIWorkspaceData({ departmentId, questionScope }).then((nextData) => {
      if (!mounted) return;
      setData(nextData);
      setDepartmentId(nextData.selectedDepartmentId ?? nextData.featuredDepartment?.departmentId ?? null);
    }).catch((loadError) => {
      if (!mounted) return;
      setError(loadError instanceof Error ? loadError.message : 'AI 브리핑 데이터를 불러오지 못했습니다.');
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, []);

  async function handleDepartmentSelect(department: AIWorkspaceDepartment) {
    setDepartmentId(department.id);
    setQuestionScope('department');
    pushAIWorkspaceUrl(department.id, 'department');
    setLoading(true);
    setError('');
    try {
      await refresh({ departmentId: department.id, questionScope: 'department', questionPage: 1 });
    } catch (selectError) {
      setError(selectError instanceof Error ? selectError.message : '부서 브리핑 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }

  async function handleScopeChange(scope: AIWorkspaceQuestionScope) {
    setQuestionScope(scope);
    pushAIWorkspaceUrl(departmentId, scope);
    setLoading(true);
    setError('');
    try {
      await refresh({ departmentId, questionScope: scope, questionPage: 1 });
    } catch (scopeError) {
      setError(scopeError instanceof Error ? scopeError.message : '브리핑 범위를 변경하지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }

  async function handleHistoryPageChange(page: number) {
    if (page < 1) return;
    setLoading(true);
    try {
      await refresh({ departmentId, questionPage: page, questionScope });
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteHistory(item: AIWorkspaceQuestionLog) {
    if (deletingHistoryId) return;
    const confirmed = window.confirm('이 브리핑 기록을 삭제할까요? 삭제 후에는 복구할 수 없습니다.');
    if (!confirmed) return;
    setDeletingHistoryId(item.id);
    setDeleteHistoryMessage('');
    setDeleteHistoryError('');
    try {
      const result = await deleteAIWorkspaceQuestionLog(item.id);
      const currentHistory = data?.questionHistory;
      const currentPage = currentHistory?.page ?? 1;
      const nextPage = currentHistory && currentHistory.items.length <= 1 && currentPage > 1 ? currentPage - 1 : currentPage;
      await refresh({ departmentId, questionPage: nextPage, questionScope });
      setDeleteHistoryMessage(result.message || '브리핑 기록을 삭제했습니다.');
    } catch (deleteError) {
      setDeleteHistoryError(deleteError instanceof Error ? deleteError.message : '브리핑 기록 삭제에 실패했습니다.');
    } finally {
      setDeletingHistoryId(null);
    }
  }

  if (loading && !data) return <DashboardLoading label="AI 브리핑 데이터를 불러오는 중입니다" />;

  if (!data) {
    return (
      <section className="ai-page">
        <DashboardApiAlert
          actionHref="/reporting/login/"
          actionLabel="로그인"
          message={error || 'AI 브리핑 API에 연결되지 않았습니다.'}
          title="AI 브리핑 API에 연결되지 않았습니다"
        />
      </section>
    );
  }

  const activeDepartmentId = data.featuredDepartment?.departmentId ?? departmentId ?? data.selectedDepartmentId ?? null;

  return (
    <section className="ai-page">
      {error ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>AI 브리핑 데이터 갱신 실패</strong>
            <span>{error}</span>
          </div>
        </div>
      ) : null}
      {!data.permission.canUseAi ? (
        <DashboardApiAlert
          actionHref={data.links.dashboard}
          actionLabel="대시보드"
          message={data.permission.message || '관리자에게 AI 기능 권한을 요청해야 합니다.'}
          title="AI 기능 권한이 없습니다"
        />
      ) : null}
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">AI briefing</span>
          <h2>{data.currentUser.company || 'AI 브리핑'}</h2>
          <p>AI는 CRM 데이터 브리핑만 제공합니다. 창작, 전략, 메일/보고 초안은 만들지 않습니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.weeklyReportCreate}>주간보고</a>
          <button className="route-primary-action" disabled={loading} onClick={() => {
            setLoading(true);
            void refresh({ departmentId: activeDepartmentId, questionScope }).finally(() => setLoading(false));
          }} type="button">
            {loading ? <Loader2 className="spin-icon" size={16} /> : <Sparkles size={16} />}
            새로고침
          </button>
        </div>
      </div>
      {data.permission.canUseAi ? (
        <div className="ai-workspace-layout">
          <div className="ai-workspace-main">
            <section className="dashboard-panel ai-main-panel">
              <div className="dashboard-panel-heading">
                <div>
                  <span className="eyebrow">Department search</span>
                  <h2>부서 브리핑 대상</h2>
                </div>
                <Sparkles size={18} />
              </div>
              <AIWorkspaceDepartmentList
                departments={data.departments}
                selectedDepartmentId={activeDepartmentId}
                onSelect={handleDepartmentSelect}
              />
            </section>
            <AIWorkspaceQuestionPanel
              data={data}
              deletingHistoryId={deletingHistoryId}
              departmentId={activeDepartmentId}
              onDeleteHistory={handleDeleteHistory}
              onHistoryPageChange={handleHistoryPageChange}
              onRefresh={refresh}
              onScopeChange={handleScopeChange}
              questionScope={questionScope}
            />
            {deleteHistoryMessage ? <p className="ai-question-history-message success">{deleteHistoryMessage}</p> : null}
            {deleteHistoryError ? <p className="ai-question-history-message error">{deleteHistoryError}</p> : null}
            <AIWorkspaceMemoryPanel activeDepartmentId={activeDepartmentId} data={data} />
          </div>
        </div>
      ) : null}
    </section>
  );
}

type AIQuestionDetailLine = {
  text: string;
  href?: string;
  linkLabel?: string;
};

function makeAIQuestionDetailAnswer(log: AIWorkspaceQuestionLog): { lead: string; blocks: Array<{ title: string; lines: AIQuestionDetailLine[] }> } {
  const answer = normalizedAnswer(log.answer, log.answerSummary || '');
  const blocks: Array<{ title: string; lines: AIQuestionDetailLine[] }> = [];
  if (answer.bullets.length) {
    blocks.push({ title: '핵심 포인트', lines: answer.bullets.map((text) => ({ text })) });
  }
  if (answer.evidence.length) {
    blocks.push({
      title: '근거',
      lines: answer.evidence
        .filter((item) => item.value)
        .map((item) => ({
          text: `${item.label || '근거'}: ${item.value}`,
          href: item.href,
          linkLabel: item.linkLabel || '열기',
        })),
    });
  }
  if (answer.confidence) {
    blocks.push({ title: '신뢰도', lines: [{ text: answer.confidence }] });
  }
  return { lead: answer.summary || log.answerSummary || '', blocks };
}

function AIWorkspaceQuestionDetailRoute({ questionLogId }: { questionLogId: number }) {
  const [data, setData] = useState<AIWorkspaceQuestionLogDetailData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    loadAIWorkspaceQuestionLogDetailData(questionLogId).then((nextData) => {
      if (mounted) setData(nextData);
    }).catch((error) => {
      if (!mounted) return;
      setData({
        success: false,
        source: 'unavailable',
        generatedAt: new Date().toISOString(),
        questionLog: null,
        links: { aiWorkspace: '/ai-workspace/' },
        error: error instanceof Error ? error.message : 'AI question detail unavailable',
      });
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, [questionLogId]);

  if (loading && !data) return <DashboardLoading label="브리핑 기록을 불러오는 중입니다" />;

  if (!data || data.source !== 'django' || !data.questionLog) {
    return (
      <section className="ai-question-detail-page">
        <DashboardApiAlert
          actionHref="/ai-workspace/"
          actionLabel="AI 브리핑"
          message={data?.error || data?.message || '기록이 없거나 접근 권한이 없습니다.'}
          title="브리핑 기록을 불러오지 못했습니다"
        />
      </section>
    );
  }

  const log = data.questionLog;
  const answer = makeAIQuestionDetailAnswer(log);
  const departmentLabel = [
    log.department?.company,
    log.department?.name,
  ].filter(Boolean).join(' · ') || (log.scopeType === 'all' ? '전체 부서' : 'AI 브리핑');
  const meta = [
    log.createdAt ? formatDateTimeLabel(log.createdAt) : '',
    log.modelLabel,
    log.webSearchUsed ? '웹 검색 사용' : '',
  ].filter(Boolean).join(' · ');

  return (
    <section className="ai-question-detail-page">
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Brief detail</span>
          <h2>브리핑 기록</h2>
          <p>{departmentLabel}{meta ? ` · ${meta}` : ''}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.aiWorkspace}>
            <ChevronLeft size={16} />
            목록으로
          </a>
        </div>
      </div>
      <div className="ai-question-detail-chat">
        <article className="ai-question-detail-block">
          <span className="eyebrow">Request</span>
          <h3>요청</h3>
          <p>{log.question}</p>
        </article>
        <article className="ai-question-detail-block">
          <span className="eyebrow">Briefing</span>
          <h3>브리핑</h3>
          {answer.lead ? <p className="ai-question-detail-answer-lead">{answer.lead}</p> : <DashboardEmpty label="저장된 브리핑 내용이 없습니다" />}
          {answer.blocks.map((block) => (
            <section className="ai-question-detail-answer-section" key={block.title}>
              <strong>{block.title}</strong>
              <ul>
                {block.lines.map((line) => (
                  <li key={`${line.text}-${line.href || ''}`}>
                    {line.text}
                    {line.href ? (
                      <a className="ai-evidence-inline-link" href={line.href}>
                        <Link2 size={12} />
                        {line.linkLabel || '열기'}
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </article>
      </div>
    </section>
  );
}

export function AIWorkspaceApp() {
  const [routeSignal, setRouteSignal] = useState(0);

  useEffect(() => {
    const refreshRoute = () => setRouteSignal((value) => value + 1);
    window.addEventListener('popstate', refreshRoute);
    window.addEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    return () => {
      window.removeEventListener('popstate', refreshRoute);
      window.removeEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    };
  }, []);

  const questionLogId = useMemo(() => getAIWorkspaceQuestionLogId(), [routeSignal]);

  return (
    <AppShell activeView="ai">
      <TopBar activeView="ai" />
      {questionLogId ? <AIWorkspaceQuestionDetailRoute questionLogId={questionLogId} /> : <AIWorkspaceHomePage />}
    </AppShell>
  );
}
