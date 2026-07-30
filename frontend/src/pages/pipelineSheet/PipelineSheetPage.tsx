import {
  AlertTriangle,
  CalendarRange,
  ChevronDown,
  ChevronRight,
  Download,
  Loader2,
  RefreshCw,
  Search,
  Target,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  loadPipelineSheetQuotes,
  loadPipelineSheetWeekly,
  pipelineSheetExportHref,
  updatePipelineSheetActivity,
  type PipelineSheetActivity,
  type PipelineSheetActivityPatch,
  type PipelineSheetQuoteRow,
  type PipelineSheetQuotesData,
  type PipelineSheetWeeklyData,
  type PipelineSheetWeeklyRow,
} from '../../api/pipelineSheet';

type SheetTab = 'weekly' | 'quotes';

/** `nextAction`은 텍스트+예정일을 한 단위로 묶어 같이 편집한다. */
type EditableField = 'body' | 'obstacle' | 'nextAction';

type EditingCell = {
  activityId: number;
  kind: 'history' | 'schedule';
  field: EditableField;
};

type ActivityEditBundle = {
  editing: EditingCell | null;
  text: string;
  date: string;
  savingKey: string | null;
  onStart: (activity: PipelineSheetActivity, field: EditableField) => void;
  onChangeText: (value: string) => void;
  onChangeDate: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
};

const QUOTE_FILTERS: { value: string; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'pending', label: '미결 있음' },
  { value: 'zero', label: '전환 0%' },
  { value: 'dead', label: '만료/거절 있음' },
];

const formatNumber = (value: number | null | undefined) => new Intl.NumberFormat('ko-KR').format(Number(value || 0));

/** 금액은 만원 단위로 줄여 쓴다 — 한 줄에 계정이 다 들어와야 읽힌다. */
const formatMoney = (value: number | null | undefined) => {
  const amount = Number(value || 0);
  if (!amount) {
    return '-';
  }
  if (Math.abs(amount) >= 10000) {
    return `${formatNumber(Math.round(amount / 10000))}만`;
  }
  return formatNumber(amount);
};

const formatDayLabel = (value: string | null | undefined) => {
  if (!value) {
    return '-';
  }
  const parts = value.split('-');
  return parts.length === 3 ? `${parts[1]}/${parts[2]}` : value;
};

const accountLabel = (row: { company: string; department: string }) =>
  [row.company, row.department].filter(Boolean).join(' · ') || '계정 미지정';

function normalizeTab(value: string | null): SheetTab {
  return value === 'quotes' ? 'quotes' : 'weekly';
}

function activityCellKey(kind: string, id: number, field: EditableField): string {
  return `${kind}-${id}-${field}`;
}

type ActivityCellProps = {
  activity: PipelineSheetActivity;
  field: EditableField;
  edit: ActivityEditBundle;
  display: ReactNode;
  placeholder: string;
};

function ActivityCell({ activity, field, edit, display, placeholder }: ActivityCellProps) {
  // Schedule에는 장애물/다음액션 필드가 없다 — 본문(body)만 편집 가능하다.
  const editable = activity.editable && (activity.kind === 'history' || field === 'body');
  if (!editable) {
    return <>{display}</>;
  }

  const isEditing =
    edit.editing?.activityId === activity.id && edit.editing.kind === activity.kind && edit.editing.field === field;
  const saving = edit.savingKey === activityCellKey(activity.kind, activity.id, field);

  if (!isEditing) {
    return (
      <button className="pipeline-sheet-editable" onClick={() => edit.onStart(activity, field)} type="button">
        {display}
      </button>
    );
  }

  return (
    <div className="pipeline-sheet-edit-box">
      <textarea
        autoFocus
        onChange={(event) => edit.onChangeText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            edit.onSave();
          } else if (event.key === 'Escape') {
            edit.onCancel();
          }
        }}
        placeholder={placeholder}
        rows={field === 'body' ? 4 : 2}
        value={edit.text}
      />
      {field === 'nextAction' ? (
        <input onChange={(event) => edit.onChangeDate(event.target.value)} type="date" value={edit.date} />
      ) : null}
      <div className="pipeline-sheet-edit-actions">
        <button disabled={saving} onClick={edit.onSave} type="button">
          {saving ? '저장중' : '저장'}
        </button>
        <button disabled={saving} onClick={edit.onCancel} type="button">
          취소
        </button>
      </div>
    </div>
  );
}

type WeeklyAccountBlockProps = {
  row: PipelineSheetWeeklyRow;
  edit: ActivityEditBundle;
};

function WeeklyAccountBlock({ row, edit }: WeeklyAccountBlockProps) {
  return (
    <tbody className="pipeline-sheet-account">
      <tr className="pipeline-sheet-account-head">
        <th colSpan={6}>
          <a href={row.href}>{accountLabel(row)}</a>
          <span className="pipeline-sheet-stage">{row.stageLabel}</span>
          <span className="pipeline-sheet-meta">
            {[row.contact, row.owner, row.amount ? `${formatMoney(row.amount)}원` : '']
              .filter(Boolean)
              .join(' · ')}
          </span>
          <span className="pipeline-sheet-count">활동 {formatNumber(row.activityCount)}건</span>
        </th>
      </tr>
      {row.activities.map((activity) => (
        <tr key={`${activity.kind}-${activity.id}`}>
          <td className="pipeline-sheet-date">
            <a href={activity.href}>{formatDayLabel(activity.date)}</a>
            <small>{activity.weekday}</small>
          </td>
          <td className="pipeline-sheet-type">{activity.type}</td>
          <td className="pipeline-sheet-body">
            <ActivityCell
              activity={activity}
              display={activity.body || <span className="muted">내용 없음</span>}
              edit={edit}
              field="body"
              placeholder="상황 / 내용"
            />
          </td>
          <td className="pipeline-sheet-obstacle">
            <ActivityCell activity={activity} display={activity.obstacle || '-'} edit={edit} field="obstacle" placeholder="장애물" />
          </td>
          <td className="pipeline-sheet-next">
            <ActivityCell
              activity={activity}
              display={
                <>
                  {activity.nextAction || '-'}
                  {activity.nextActionDate ? <small>{formatDayLabel(activity.nextActionDate)}</small> : null}
                </>
              }
              edit={edit}
              field="nextAction"
              placeholder="다음 액션"
            />
          </td>
          <td className="pipeline-sheet-amount">{activity.amount ? `${formatMoney(activity.amount)}원` : '-'}</td>
        </tr>
      ))}
    </tbody>
  );
}

type QuoteRowProps = {
  row: PipelineSheetQuoteRow;
  expanded: boolean;
  onToggle: () => void;
};

function QuoteAccountRows({ row, expanded, onToggle }: QuoteRowProps) {
  return (
    <>
      <tr className="pipeline-sheet-quote-row">
        <td className="pipeline-sheet-account-cell">
          <button className="pipeline-sheet-expand" onClick={onToggle} type="button">
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
          <a href={row.href}>{accountLabel(row)}</a>
          <small>{[row.contact, row.owner].filter(Boolean).join(' · ')}</small>
        </td>
        <td>{formatNumber(row.quoteCount)}</td>
        <td>{formatMoney(row.quoteAmount)}</td>
        <td>{formatNumber(row.convertedCount)}</td>
        <td>{formatMoney(row.convertedAmount)}</td>
        <td>
          <span className={`pipeline-sheet-rate${row.conversionRate === 0 ? ' zero' : ''}`}>
            {row.conversionRate}%
          </span>
        </td>
        <td>{row.conversionAmountRate}%</td>
        <td>{formatNumber(row.pendingCount)}</td>
        <td>{formatMoney(row.pendingAmount)}</td>
        <td>{formatNumber(row.deadCount)}</td>
        <td>
          {formatDayLabel(row.latestQuoteDate)}
          {row.latestQuoteAgeDays !== null ? <small>{row.latestQuoteAgeDays}일 경과</small> : null}
        </td>
      </tr>
      {expanded
        ? row.quotes.map((quote) => (
            <tr className="pipeline-sheet-quote-detail" key={`${quote.recordType}-${quote.id}`}>
              <td className="pipeline-sheet-account-cell">
                {quote.href ? <a href={quote.href}>{quote.number || '견적'}</a> : (quote.number || '견적')}
                <small>{formatDayLabel(quote.date)}</small>
              </td>
              <td colSpan={4}>{quote.statusLabel || quote.status || '-'}</td>
              <td colSpan={2}>{quote.converted ? '납품 전환' : '미전환'}</td>
              <td colSpan={3}>{formatMoney(quote.amount)}</td>
              <td>{quote.ageDays !== null ? `${quote.ageDays}일` : '-'}</td>
            </tr>
          ))
        : null}
    </>
  );
}

export function PipelineSheetPage() {
  const initialParams = useMemo(() => new URLSearchParams(window.location.search), []);
  const [tab, setTab] = useState<SheetTab>(() => normalizeTab(initialParams.get('tab')));
  const [week, setWeek] = useState(() => initialParams.get('week') || '');
  const [ownerId, setOwnerId] = useState<number | null>(() => {
    const raw = Number(initialParams.get('user'));
    return Number.isFinite(raw) && raw > 0 ? raw : null;
  });
  const [quoteFilter, setQuoteFilter] = useState(() => initialParams.get('filter') || 'all');
  const [quoteSort, setQuoteSort] = useState(() => initialParams.get('sort') || 'conversion');
  const [quoteQuery, setQuoteQuery] = useState(() => initialParams.get('q') || '');

  const [weekly, setWeekly] = useState<PipelineSheetWeeklyData | null>(null);
  const [quotes, setQuotes] = useState<PipelineSheetQuotesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedAccount, setExpandedAccount] = useState<string | null>(null);

  const [editing, setEditing] = useState<EditingCell | null>(null);
  const [editText, setEditText] = useState('');
  const [editDate, setEditDate] = useState('');
  const [savingKey, setSavingKey] = useState<string | null>(null);

  const refreshWeekly = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await loadPipelineSheetWeekly({ week: week || undefined, user: ownerId });
      setWeekly(data);
      if (!week) {
        setWeek(data.week.start);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '주간 활동을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [ownerId, week]);

  const refreshQuotes = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await loadPipelineSheetQuotes({
        filter: quoteFilter,
        sort: quoteSort,
        query: quoteQuery,
        user: ownerId,
      });
      setQuotes(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '견적 전환을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, [ownerId, quoteFilter, quoteQuery, quoteSort]);

  useEffect(() => {
    if (tab === 'weekly') {
      void refreshWeekly();
    } else {
      void refreshQuotes();
    }
  }, [refreshQuotes, refreshWeekly, tab]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (tab !== 'weekly') params.set('tab', tab);
    if (ownerId) params.set('user', String(ownerId));
    if (tab === 'weekly') {
      if (week) params.set('week', week);
    } else {
      if (quoteFilter && quoteFilter !== 'all') params.set('filter', quoteFilter);
      if (quoteSort && quoteSort !== 'conversion') params.set('sort', quoteSort);
      if (quoteQuery.trim()) params.set('q', quoteQuery.trim());
    }
    const queryString = params.toString();
    window.history.replaceState(null, '', `/pipeline-sheet/${queryString ? `?${queryString}` : ''}`);
  }, [ownerId, quoteFilter, quoteQuery, quoteSort, tab, week]);

  const scope = tab === 'weekly' ? weekly?.scope : quotes?.scope;
  const exportHref = pipelineSheetExportHref(
    { week: week || undefined, user: ownerId },
    { filter: quoteFilter, sort: quoteSort, query: quoteQuery, user: ownerId },
  );
  // 최근 8주 밖의 주를 URL로 직접 열었을 때도 선택 상태가 비지 않도록 끼워 넣는다.
  const weekOptions = useMemo(() => {
    const options = weekly?.weekOptions ?? [];
    if (!weekly || options.some((option) => option.value === weekly.week.start)) {
      return options;
    }
    return [
      {
        value: weekly.week.start,
        label: `${weekly.week.start} ~ ${weekly.week.end}`,
        weekStart: weekly.week.start,
        weekEnd: weekly.week.end,
      },
      ...options,
    ];
  }, [weekly]);
  const weeklyMetrics = weekly?.metrics;
  const quoteMetrics = quotes?.metrics;
  const refreshCurrent = tab === 'weekly' ? refreshWeekly : refreshQuotes;

  const startEdit = useCallback((activity: PipelineSheetActivity, field: EditableField) => {
    setEditing({ activityId: activity.id, kind: activity.kind, field });
    setEditText(field === 'nextAction' ? activity.nextAction : field === 'obstacle' ? activity.obstacle : activity.body);
    setEditDate(activity.nextActionDate || '');
  }, []);

  const cancelEdit = useCallback(() => {
    setEditing(null);
    setEditText('');
    setEditDate('');
  }, []);

  const saveEdit = useCallback(async () => {
    if (!editing) {
      return;
    }
    const key = activityCellKey(editing.kind, editing.activityId, editing.field);
    setSavingKey(key);
    setError('');
    try {
      const patch: PipelineSheetActivityPatch =
        editing.field === 'nextAction'
          ? { nextAction: editText, nextActionDate: editDate }
          : editing.field === 'obstacle'
            ? { obstacle: editText }
            : { body: editText };
      await updatePipelineSheetActivity(editing.kind, editing.activityId, patch);
      setEditing(null);
      setEditText('');
      setEditDate('');
      await refreshWeekly();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : '저장하지 못했습니다.');
    } finally {
      setSavingKey(null);
    }
  }, [editDate, editText, editing, refreshWeekly]);

  const activityEdit: ActivityEditBundle = {
    editing,
    text: editText,
    date: editDate,
    savingKey,
    onStart: startEdit,
    onChangeText: setEditText,
    onChangeDate: setEditDate,
    onSave: () => void saveEdit(),
    onCancel: cancelEdit,
  };

  return (
    <section className="pipeline-sheet-page">
      <div className="pipeline-sheet-tabs">
        <button
          className={`pipeline-sheet-tab${tab === 'weekly' ? ' active' : ''}`}
          onClick={() => setTab('weekly')}
          type="button"
        >
          <CalendarRange size={15} />
          주간 활동
        </button>
        <button
          className={`pipeline-sheet-tab${tab === 'quotes' ? ' active' : ''}`}
          onClick={() => setTab('quotes')}
          type="button"
        >
          <Target size={15} />
          견적 전환
        </button>
        <div className="pipeline-sheet-tab-actions">
          {scope?.canSelectUser ? (
            <select
              onChange={(event) => setOwnerId(event.target.value ? Number(event.target.value) : null)}
              value={ownerId ?? ''}
            >
              <option value="">전체 담당</option>
              {scope.users.map((user) => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
            </select>
          ) : null}
          <button className="route-secondary-action" disabled={loading} onClick={() => void refreshCurrent()} type="button">
            {loading ? <Loader2 className="spin-icon" size={15} /> : <RefreshCw size={15} />}
            새로고침
          </button>
          <a className="route-secondary-action" href={exportHref}>
            <Download size={15} />
            엑셀 다운로드
          </a>
        </div>
      </div>

      {error ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      ) : null}

      {tab === 'weekly' ? (
        <>
          <div className="pipeline-sheet-controls">
            <select onChange={(event) => setWeek(event.target.value)} value={week}>
              {weekOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <span className="pipeline-sheet-range">
              {weekly ? `${weekly.week.start} ~ ${weekly.week.end}` : ''}
            </span>
            <span className="pipeline-sheet-scope">{scope?.label}</span>
          </div>

          <div className="pipeline-sheet-metrics">
            <div>
              <span>활동한 계정</span>
              <strong>{formatNumber(weeklyMetrics?.activeAccounts)}곳</strong>
            </div>
            <div>
              <span>총 활동</span>
              <strong>{formatNumber(weeklyMetrics?.totalActivities)}건</strong>
            </div>
            <div>
              <span>미접촉 계정</span>
              <strong>{formatNumber(weeklyMetrics?.untouchedCount)}곳</strong>
            </div>
            <div>
              <span>미접촉 금액</span>
              <strong>{formatMoney(weeklyMetrics?.untouchedAmount)}원</strong>
            </div>
          </div>

          {weekly?.untouchedAccounts.length ? (
            <div className="pipeline-sheet-untouched">
              <strong>이번 주 손대지 못한 주요 계정</strong>
              <div>
                {weekly.untouchedAccounts.map((account) => (
                  <a href={account.href} key={account.accountKey}>
                    {accountLabel(account)}
                    <span>{account.stageLabel} · {formatMoney(account.amount)}원</span>
                  </a>
                ))}
              </div>
            </div>
          ) : null}

          <div className="pipeline-sheet-table-wrap">
            <table className="pipeline-sheet-table">
              <thead>
                <tr>
                  <th>날짜</th>
                  <th>활동</th>
                  <th>상황 / 내용</th>
                  <th>장애물</th>
                  <th>다음 액션</th>
                  <th>금액</th>
                </tr>
              </thead>
              {loading && !weekly ? (
                <tbody>
                  <tr>
                    <td colSpan={6}>
                      <Loader2 className="spin-icon" size={18} /> 데이터를 불러오는 중입니다
                    </td>
                  </tr>
                </tbody>
              ) : weekly?.rows.length ? (
                weekly.rows.map((row) => <WeeklyAccountBlock edit={activityEdit} key={row.accountKey} row={row} />)
              ) : (
                <tbody>
                  <tr>
                    <td colSpan={6}>이 주에 기록된 활동이 없습니다</td>
                  </tr>
                </tbody>
              )}
            </table>
          </div>
        </>
      ) : (
        <>
          <div className="pipeline-sheet-controls">
            <label className="customers-search">
              <Search size={16} />
              <input
                onChange={(event) => setQuoteQuery(event.target.value)}
                placeholder="업체, 부서, 담당자 검색"
                value={quoteQuery}
              />
            </label>
            <div className="pipeline-sheet-filters">
              {QUOTE_FILTERS.map((option) => (
                <button
                  className={`pipeline-sheet-chip${quoteFilter === option.value ? ' active' : ''}`}
                  key={option.value}
                  onClick={() => setQuoteFilter(option.value)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>
            <select onChange={(event) => setQuoteSort(event.target.value)} value={quoteSort}>
              {(quotes?.sortOptions ?? []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <span className="pipeline-sheet-scope">{scope?.label}</span>
          </div>

          <div className="pipeline-sheet-metrics">
            <div>
              <span>견적 계정</span>
              <strong>{formatNumber(quoteMetrics?.accounts)}곳</strong>
            </div>
            <div>
              <span>누적 견적</span>
              <strong>{formatMoney(quoteMetrics?.quoteAmount)}원</strong>
            </div>
            <div>
              <span>납품 전환</span>
              <strong>{formatMoney(quoteMetrics?.convertedAmount)}원</strong>
            </div>
            <div>
              <span>전환율</span>
              <strong>{quoteMetrics?.conversionRate ?? 0}% / {quoteMetrics?.conversionAmountRate ?? 0}%</strong>
            </div>
          </div>

          <div className="pipeline-sheet-table-wrap">
            <table className="pipeline-sheet-table pipeline-sheet-quotes-table">
              <thead>
                <tr>
                  <th>계정</th>
                  <th>견적</th>
                  <th>견적금액</th>
                  <th>전환</th>
                  <th>전환금액</th>
                  <th>전환율</th>
                  <th>금액전환율</th>
                  <th>미결</th>
                  <th>미결금액</th>
                  <th>종료</th>
                  <th>최근 견적</th>
                </tr>
              </thead>
              <tbody>
                {loading && !quotes ? (
                  <tr>
                    <td colSpan={11}>
                      <Loader2 className="spin-icon" size={18} /> 데이터를 불러오는 중입니다
                    </td>
                  </tr>
                ) : quotes?.rows.length ? (
                  quotes.rows.map((row) => (
                    <QuoteAccountRows
                      expanded={expandedAccount === row.accountKey}
                      key={row.accountKey}
                      onToggle={() =>
                        setExpandedAccount((current) => (current === row.accountKey ? null : row.accountKey))
                      }
                      row={row}
                    />
                  ))
                ) : (
                  <tr>
                    <td colSpan={11}>조건에 맞는 견적이 없습니다</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
