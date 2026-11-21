import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  GripVertical,
  Loader2,
  Maximize2,
  Moon,
  Pencil,
  Plus,
  Sun,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent, type FormEvent } from 'react';
import {
  createMeetingAction,
  deleteMeetingAction,
  dismissMeetingNextAction,
  loadPipelineMeeting,
  reorderMeetingServices,
  restoreMeetingNextAction,
  setMeetingMovement,
  toggleMeetingAction,
  updateMeetingAction,
  type MeetingActionItem,
  type MeetingMovementGroup,
  type MeetingMovementItem,
  type MeetingMovementKey,
  type MeetingNextAction,
  type MeetingServiceRecord,
  type PipelineMeetingData,
} from '../../api/pipelineMeeting';
import { humanizeApiError } from '../../components/shared/FeedbackStates';
import { formatNumber, formatWon } from '../../components/shared/formatters';
import { SearchableSelect } from '../shared/appShared';
import './pipelineMeeting.css';

const SCENES = ['요약', '서비스', '활동', '약속', '이번 주 계획'] as const;

const shortDate = (iso: string | null | undefined) => {
  if (!iso) return '';
  const [, month, day] = iso.split('-');
  return `${Number(month)}/${Number(day)}`;
};

// 기본 기준 주(지난주)면 말로 부르고, 다른 주를 고르면 날짜로 부른다.
const weekNameOf = (weekStart: string) => {
  const today = new Date();
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - ((today.getDay() + 6) % 7) - 7);
  const lastWeek = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, '0')}-${String(monday.getDate()).padStart(2, '0')}`;
  return weekStart === lastWeek ? '지난주' : `${shortDate(weekStart)} 주`;
};

// 보고 기한 기본값: 다음 주 월요일(주간 회의 기준)
const nextMondayIso = () => {
  const today = new Date();
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (7 - ((today.getDay() + 6) % 7)));
  return `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, '0')}-${String(monday.getDate()).padStart(2, '0')}`;
};

const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function useCountUp(target: number, duration = 1100) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (prefersReducedMotion()) {
      setValue(target);
      return undefined;
    }
    let frame = 0;
    const started = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - started) / duration, 1);
      setValue(Math.round(target * (1 - (1 - progress) ** 3)));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);
  return value;
}

function WinBurst() {
  const pieces = useMemo(
    () => Array.from({ length: 36 }, (_, index) => ({
      left: `${(index * 97) % 100}%`,
      delay: `${((index * 53) % 60) / 100}s`,
      duration: `${1.8 + ((index * 31) % 12) / 10}s`,
      rotate: `${(index * 71) % 360}deg`,
    })),
    [],
  );
  return (
    <div aria-hidden="true" className="meeting-burst">
      {pieces.map((piece, index) => (
        <i
          key={index}
          style={{ left: piece.left, animationDelay: piece.delay, animationDuration: piece.duration, rotate: piece.rotate }}
        />
      ))}
    </div>
  );
}

function SummaryScene({ data }: { data: PipelineMeetingData }) {
  const { summary } = data;
  const weekRevenue = useCountUp(summary.weekRevenue);
  const yearRevenue = useCountUp(summary.yearRevenue, 1500);
  const up = summary.weekDelta >= 0;
  const ratio = summary.lastYearRevenue > 0 ? summary.yearRevenue / summary.lastYearRevenue : null;
  return (
    <div className="meeting-summary">
      <section className="meeting-hero">
        <span className="meeting-label">{weekNameOf(data.week.start)} 매출</span>
        <strong className="meeting-hero-number">{formatWon(weekRevenue)}</strong>
        <span className={`meeting-delta ${up ? 'up' : 'down'}`}>
          {up ? <TrendingUp size={22} /> : <TrendingDown size={22} />}
          전주 대비 {up ? '+' : '-'}{formatWon(Math.abs(summary.weekDelta))}
        </span>
      </section>
      <section className="meeting-year">
        <span className="meeting-label">올해 누적 매출</span>
        <strong>{formatWon(yearRevenue)}</strong>
        {ratio !== null ? (
          <>
            <div className="meeting-gauge">
              <div style={{ width: `${Math.min(ratio, 1) * 100}%` }} />
            </div>
            <small>
              작년 전체 매출 {formatWon(summary.lastYearRevenue)}의 {Math.round(ratio * 100)}%
            </small>
          </>
        ) : null}
      </section>
      <section className="meeting-stats">
        {/* 활동 장면 "수주" 칸과 같은 숫자(발주 접수 + 수주로 바뀐 건, 손 보정 포함). 매출은 납품 완료 기준 */}
        <div>
          <span>수주</span>
          <strong>{formatNumber(data.movement.won.count)}건{data.movement.won.amount > 0 ? ` · ${formatWon(data.movement.won.amount)}` : ''}</strong>
        </div>
        <div><span>납품 완료</span><strong>{formatNumber(summary.deliveryCount)}건</strong></div>
        <div><span>견적 금액</span><strong>{formatWon(summary.quoteAmount)}</strong></div>
        <div><span>실주 금액</span><strong>{summary.lostAmount === null ? '기록 없음' : formatWon(summary.lostAmount)}</strong></div>
        <div><span>활동한 계정</span><strong>{formatNumber(summary.activeAccounts)}곳</strong></div>
        {data.services.length > 0 ? <div><span>서비스</span><strong>{formatNumber(data.services.length)}건</strong></div> : null}
      </section>
    </div>
  );
}

const MOVE_LABELS: Record<MeetingMovementKey, string> = {
  won: '수주', advanced: '전진', regressed: '후퇴', lost: '실주', created: '신규',
};
const MOVE_KEYS = Object.keys(MOVE_LABELS) as MeetingMovementKey[];
type MoveChange = (followupId: number, group: MeetingMovementKey | 'hidden' | '', card?: '' | 'quote') => void;

function MovementCard({ item, index, busy, onChange }: {
  item: MeetingMovementItem;
  index: number;
  busy: boolean;
  onChange: MoveChange;
}) {
  return (
    <div
      className={`meeting-move-card${item.adjusted ? ' adjusted' : ''}`}
      draggable={!busy}
      onDragStart={(event) => {
        event.dataTransfer.setData('text/meeting-move', item.key);
        event.dataTransfer.effectAllowed = 'move';
      }}
      style={{ animationDelay: `${index * 70}ms` }}
    >
      <a href={item.href}>
        <b>{item.company || item.customer}</b>
        <small>{item.company ? item.customer : ''} · {item.owner}</small>
      </a>
      <span className="meeting-move-flow">
        <em>{item.fromLabel}</em><ArrowRight size={14} /><em className="to">{item.toLabel}</em>
        {item.amount > 0 ? <strong>{formatWon(item.amount)}</strong> : null}
      </span>
      <div className="meeting-move-tools">
        <select
          aria-label={`${item.company || item.customer} 칸 옮기기`}
          disabled={busy}
          onChange={(event) => onChange(item.followupId, event.target.value as MeetingMovementKey, item.card)}
          value={item.group}
        >
          {MOVE_KEYS.map((key) => <option key={key} value={key}>{MOVE_LABELS[key]}</option>)}
        </select>
        {item.adjusted && !item.manual ? (
          <button disabled={busy} onClick={() => onChange(item.followupId, '', item.card)} title="자동 분류로 되돌리기" type="button">원래대로</button>
        ) : null}
        {item.manual ? <span className="meeting-move-tag">직접 추가</span> : null}
        <button
          aria-label={`${item.company || item.customer} 지우기`}
          className="meeting-move-delete"
          disabled={busy}
          onClick={() => onChange(item.followupId, 'hidden', item.card)}
          title="이 회의 화면에서 지우기(고객 단계는 그대로)"
          type="button"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}

function MovementColumn({ title, tone, group, groups, startIndex, busy, customers, onChange }: {
  title: string;
  tone: string;
  group: MeetingMovementGroup;
  /** 이 칸에 넣을 수 있는 분류(후퇴·실주 칸은 둘) */
  groups: MeetingMovementKey[];
  startIndex: number;
  busy: boolean;
  customers: { value: string; label: string }[];
  onChange: MoveChange;
}) {
  const [adding, setAdding] = useState(false);
  const [customer, setCustomer] = useState('');
  const [target, setTarget] = useState<MeetingMovementKey>(groups[0]);
  const [over, setOver] = useState(false);

  const onDrop = (event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    setOver(false);
    const key = event.dataTransfer.getData('text/meeting-move');
    const [rawId, card = ''] = key.split(':');
    const id = Number(rawId);
    if (!id) return;
    const current = group.items.find((item) => item.key === key);
    if (!current) onChange(id, groups[0], card === 'quote' ? 'quote' : '');
  };

  return (
    <section
      className={`meeting-column ${tone}${over ? ' drop-over' : ''}`}
      onDragLeave={() => setOver(false)}
      onDragOver={(event) => {
        if (busy) return;
        event.preventDefault();
        setOver(true);
      }}
      onDrop={onDrop}
    >
      <header>
        <h3>{title}</h3>
        <span className="meeting-column-head-tools">
          <button aria-label={`${title}에 직접 추가`} disabled={busy} onClick={() => setAdding((value) => !value)} title="직접 추가" type="button">
            {adding ? <X size={15} /> : <Plus size={15} />}
          </button>
          <strong>{group.count}</strong>
        </span>
      </header>
      <div className="meeting-column-body">
        {adding ? (
          <form
            className="meeting-move-add"
            onSubmit={(event) => {
              event.preventDefault();
              if (!customer) return;
              onChange(Number(customer), target);
              setCustomer('');
              setAdding(false);
            }}
          >
            <SearchableSelect ariaLabel={`${title}에 넣을 고객`} onChange={setCustomer} options={customers} placeholder="고객 검색" value={customer} />
            {groups.length > 1 ? (
              <select aria-label="분류" onChange={(event) => setTarget(event.target.value as MeetingMovementKey)} value={target}>
                {groups.map((key) => <option key={key} value={key}>{MOVE_LABELS[key]}</option>)}
              </select>
            ) : null}
            <button disabled={busy || !customer} type="submit">추가</button>
          </form>
        ) : null}
        {group.items.length === 0 && !adding ? <p className="meeting-empty">없음</p> : null}
        {group.items.map((item: MeetingMovementItem, index) => (
          <MovementCard busy={busy} index={startIndex + index} item={item} key={item.key ?? item.followupId} onChange={onChange} />
        ))}
      </div>
    </section>
  );
}

function MovementScene({ data, onChanged }: {
  data: PipelineMeetingData;
  onChanged: (movement: PipelineMeetingData['movement'], lostAmount: number | null) => void;
}) {
  const { movement } = data;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [manual, setManual] = useState(false);
  const [showHidden, setShowHidden] = useState(false);
  const customers = useMemo(
    () => (data.form.movementCustomers ?? data.form.customers).map((row) => ({ value: String(row.id), label: row.label })),
    [data.form.movementCustomers, data.form.customers],
  );

  const change: MoveChange = (followupId, group, card = '') => {
    setBusy(true);
    setError('');
    setMeetingMovement({ week: data.week.start, followupId, group, card })
      .then((result) => onChanged(result.movement, result.lostAmount))
      .catch((caught) => setError(humanizeApiError(caught instanceof Error ? caught.message : '') || '활동을 고치지 못했습니다.'))
      .finally(() => setBusy(false));
  };

  if (!movement.tracked && !manual) {
    return (
      <div className="meeting-notice">
        <h2>이 주의 단계 변경 기록이 없습니다</h2>
        <p>
          단계 변경은 {movement.trackingSince ? `${shortDate(movement.trackingSince)}부터` : '이번 배포부터'} 기록하고 있습니다.
          기록이 시작된 다음 회의부터 이 장면이 채워집니다.
        </p>
        <p><button className="meeting-move-manual" onClick={() => setManual(true)} type="button"><Plus size={14} />직접 채우기</button></p>
      </div>
    );
  }
  const common = { busy, customers, onChange: change };
  return (
    <div className="meeting-movement-wrap">
      <div className="meeting-movement">
        {movement.won.count > 0 ? <WinBurst /> : null}
        <MovementColumn {...common} group={movement.won} groups={['won']} startIndex={0} title="수주" tone="won" />
        <MovementColumn {...common} group={movement.advanced} groups={['advanced']} startIndex={2} title="전진" tone="advanced" />
        <MovementColumn
          {...common}
          group={{
            count: movement.regressed.count + movement.lost.count,
            amount: movement.regressed.amount + movement.lost.amount,
            items: [...movement.regressed.items, ...movement.lost.items],
          }}
          groups={['regressed', 'lost']}
          startIndex={4}
          title="후퇴 · 실주"
          tone="regressed"
        />
        <MovementColumn {...common} group={movement.created} groups={['created']} startIndex={6} title="신규" tone="created" />
      </div>
      <footer className="meeting-move-foot">
        {busy ? <span><Loader2 className="spin-icon" size={14} /> 저장 중</span> : null}
        {error ? <span className="meeting-move-error">{error}</span> : null}
        <span className="meeting-move-hint">카드를 다른 칸으로 끌거나 카드의 칸 선택으로 옮깁니다 · + 로 직접 추가, 휴지통으로 지우기 · 여기서 고친 것은 회의 화면에만 적용되고 고객 단계는 바뀌지 않습니다</span>
        {(movement.hidden ?? []).length ? (
          <button onClick={() => setShowHidden((value) => !value)} type="button">지운 건 {movement.hidden.length}</button>
        ) : null}
      </footer>
      {showHidden && (movement.hidden ?? []).length ? (
        <ul className="meeting-move-hidden">
          {movement.hidden.map((item) => (
            <li key={item.key ?? item.followupId}>
              <span>{item.company || item.customer} · {item.fromLabel} → {item.toLabel}</span>
              <button disabled={busy} onClick={() => change(item.followupId, '', item.card)} type="button">되살리기</button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

type ActionDraft = { title: string; ownerId: string; dueDate: string; followupId: string };

function PromisesScene({ data, draft, onDraftChange, onCreated, onChanged, onRemoved, onNextActionsChange }: {
  data: PipelineMeetingData;
  draft: ActionDraft;
  onDraftChange: (draft: ActionDraft) => void;
  onCreated: (item: MeetingActionItem) => void;
  onChanged: (item: MeetingActionItem) => void;
  onRemoved: (id: number) => void;
  onNextActionsChange: (rows: MeetingNextAction[]) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [lastDismissed, setLastDismissed] = useState<MeetingNextAction | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [reportDue, setReportDue] = useState(nextMondayIso);
  const [error, setError] = useState('');
  const titleRef = useRef<HTMLInputElement>(null);
  const { actionItems, nextActions } = data.promises;
  const promises = actionItems.filter((item) => item.kind !== 'report');
  // 기한이 된 보고를 맨 위로, 그다음 가까운 기한 순
  const reports = actionItems
    .filter((item) => item.kind === 'report')
    .sort((a, b) => Number(b.dueReached) - Number(a.dueReached) || (a.dueDate ?? '').localeCompare(b.dueDate ?? ''));
  const customerOptions = useMemo(
    () => data.form.customers.map((customer) => ({ value: String(customer.id), label: customer.label })),
    [data.form.customers],
  );

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft.title.trim()) {
      setError('약속 내용을 입력하세요.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      onCreated(await createMeetingAction({
        title: draft.title.trim(),
        ownerId: Number(draft.ownerId),
        dueDate: draft.dueDate || undefined,
        followupId: draft.followupId ? Number(draft.followupId) : undefined,
      }));
      onDraftChange({ ...draft, title: '', followupId: '' });
      titleRef.current?.focus();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '약속을 저장하지 못했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const saveTitle = async () => {
    if (editingId === null) return;
    if (!editingTitle.trim()) {
      setError('내용을 입력하세요.');
      return;
    }
    await run(async () => {
      onChanged(await updateMeetingAction(editingId, editingTitle.trim()));
      setEditingId(null);
    });
  };

  const titleCell = (item: MeetingActionItem) => (editingId === item.id ? (
    <input
      aria-label="내용 수정"
      autoFocus
      className="meeting-inline-edit"
      maxLength={200}
      onChange={(event) => setEditingTitle(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === 'Enter') void saveTitle();
        if (event.key === 'Escape') setEditingId(null);
      }}
      value={editingTitle}
    />
  ) : <b>{item.title}</b>);

  const editButtons = (item: MeetingActionItem) => (editingId === item.id ? (
    <>
      <button aria-label="저장" className="meeting-icon" onClick={saveTitle} type="button"><Check size={15} /></button>
      <button aria-label="수정 취소" className="meeting-icon" onClick={() => setEditingId(null)} type="button"><X size={15} /></button>
    </>
  ) : (
    <button
      aria-label="내용 수정"
      className="meeting-icon"
      onClick={() => {
        setEditingId(item.id);
        setEditingTitle(item.title);
        setError('');
      }}
      type="button"
    >
      <Pencil size={15} />
    </button>
  ));

  const submitReport = async (event: FormEvent) => {
    event.preventDefault();
    if (!reportTitle.trim()) {
      setError('보고할 내용을 입력하세요.');
      return;
    }
    if (!reportDue) {
      setError('보고 기한을 선택하세요.');
      return;
    }
    setError('');
    try {
      onCreated(await createMeetingAction({ kind: 'report', title: reportTitle.trim(), dueDate: reportDue }));
      setReportTitle('');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '보고 내용을 저장하지 못했습니다.');
    }
  };

  const run = async (action: () => Promise<void>) => {
    setError('');
    try {
      await action();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '약속을 변경하지 못했습니다.');
    }
  };

  return (
    <div className="meeting-promises">
      <section className="meeting-panel">
        <header><h3>회의 약속</h3><small>끝낼 때까지 다음 회의로 넘어옵니다</small></header>
        <div className="meeting-scroll">
          {promises.length === 0 ? <p className="meeting-empty">아직 약속이 없습니다. 아래에서 오늘 정한 일을 적어 주세요.</p> : null}
          {promises.map((item) => (
            <div className={`meeting-action ${item.status}`} key={item.id}>
              <button
                aria-label={item.status === 'done' ? '완료 취소' : '완료 처리'}
                className="meeting-check"
                disabled={!item.canEdit}
                onClick={() => run(async () => onChanged(await toggleMeetingAction(item.id)))}
                type="button"
              >
                {item.status === 'done' ? <Check size={16} /> : null}
              </button>
              <div>
                {titleCell(item)}
                <small>
                  {item.owner}
                  {item.customer ? ` · ${item.company ? `${item.company} ` : ''}${item.customer}` : ''}
                </small>
              </div>
              {item.carriedWeeks > 0 && item.status === 'open' ? <em className="meeting-tag warn">{item.carriedWeeks}주째</em> : null}
              {item.dueDate ? <em className={`meeting-tag ${item.overdue ? 'danger' : ''}`}>{shortDate(item.dueDate)}까지</em> : null}
              {item.canEdit ? editButtons(item) : null}
              {item.canEdit && editingId !== item.id ? (
                <button
                  aria-label="약속 삭제"
                  className="meeting-icon"
                  onClick={() => run(async () => {
                    await deleteMeetingAction(item.id);
                    onRemoved(item.id);
                  })}
                  type="button"
                >
                  <Trash2 size={15} />
                </button>
              ) : null}
            </div>
          ))}
        </div>
        <form className="meeting-action-form" onSubmit={submit}>
          <input
            aria-label="약속 내용"
            maxLength={200}
            onChange={(event) => onDraftChange({ ...draft, title: event.target.value })}
            placeholder="무엇을 하기로 했나요"
            ref={titleRef}
            value={draft.title}
          />
          <select aria-label="담당자" onChange={(event) => onDraftChange({ ...draft, ownerId: event.target.value })} value={draft.ownerId}>
            {data.form.owners.map((owner) => <option key={owner.id} value={owner.id}>{owner.name}</option>)}
          </select>
          <input aria-label="기한" onChange={(event) => onDraftChange({ ...draft, dueDate: event.target.value })} type="date" value={draft.dueDate} />
          <SearchableSelect
            allowEmpty
            ariaLabel="관련 고객"
            emptyLabel="고객 선택 안 함"
            onChange={(value) => onDraftChange({ ...draft, followupId: value })}
            options={customerOptions}
            placeholder="고객 검색"
            value={draft.followupId}
          />
          <button disabled={saving} type="submit">
            {saving ? <Loader2 className="spin-icon" size={16} /> : <Plus size={16} />}추가
          </button>
        </form>
        {error ? <p className="meeting-error">{error}</p> : null}
      </section>
      <section className="meeting-panel">
        <header>
          <h3>다음 액션</h3>
          <small>
            후속 기록 있음 {nextActions.filter((row) => row.followedUp).length} · 없음 {nextActions.filter((row) => !row.followedUp).length}
            {lastDismissed ? (
              <button
                className="meeting-undo"
                onClick={() => run(async () => {
                  await restoreMeetingNextAction(lastDismissed.id);
                  onNextActionsChange([...nextActions, lastDismissed]);
                  setLastDismissed(null);
                })}
                type="button"
              >
                되돌리기
              </button>
            ) : null}
          </small>
        </header>
        <div className="meeting-scroll">
          {reports.length === 0 && nextActions.length === 0 ? <p className="meeting-empty">이 주가 기한인 다음 액션이 없습니다.</p> : null}
          {reports.map((item) => (
            <div className={`meeting-action meeting-report ${item.status} ${item.dueReached ? 'due' : ''}`} key={item.id}>
              <button
                aria-label={item.status === 'done' ? '완료 취소' : '보고 완료'}
                className="meeting-check"
                disabled={!item.canEdit}
                onClick={() => run(async () => onChanged(await toggleMeetingAction(item.id)))}
                type="button"
              >
                {item.status === 'done' ? <Check size={16} /> : null}
              </button>
              <div>
                {titleCell(item)}
                <small>{item.owner}</small>
              </div>
              <em className={`meeting-tag ${item.overdue ? 'danger' : item.dueReached ? 'warn' : ''}`}>
                {item.overdue ? `${shortDate(item.dueDate)} 기한 지남` : item.dueReached ? '오늘 보고' : `${shortDate(item.dueDate)} 보고`}
              </em>
              {item.canEdit ? editButtons(item) : null}
              {item.canEdit && editingId !== item.id ? (
                <button
                  aria-label="보고 삭제"
                  className="meeting-icon"
                  onClick={() => run(async () => {
                    await deleteMeetingAction(item.id);
                    onRemoved(item.id);
                  })}
                  type="button"
                >
                  <Trash2 size={15} />
                </button>
              ) : null}
            </div>
          ))}
          {nextActions.map((row) => (
            <div className="meeting-next" key={row.id}>
              {row.followedUp ? (
                <i className="ok"><Check size={14} /></i>
              ) : (
                <button
                  aria-label="아침회의 목록에서 숨기기"
                  className="meeting-next-dismiss"
                  onClick={() => run(async () => {
                    await dismissMeetingNextAction(row.id);
                    onNextActionsChange(nextActions.filter((other) => other.id !== row.id));
                    setLastDismissed(row);
                  })}
                  title="아침회의 목록에서만 숨깁니다. 노트 기록은 그대로입니다."
                  type="button"
                >
                  <X size={14} />
                </button>
              )}
              <a href={row.href}>
                <b>{row.text}</b>
                <small>{row.company} {row.customer} · {row.owner} · {shortDate(row.dueDate)}</small>
              </a>
            </div>
          ))}
        </div>
        <form className="meeting-report-form" onSubmit={submitReport}>
          <input
            aria-label="회의 때 보고할 내용"
            maxLength={200}
            onChange={(event) => setReportTitle(event.target.value)}
            placeholder="회의 때 보고할 내용"
            value={reportTitle}
          />
          <input aria-label="보고 기한" onChange={(event) => setReportDue(event.target.value)} type="date" value={reportDue} />
          <button type="submit"><Plus size={16} />추가</button>
        </form>
      </section>
    </div>
  );
}

type ServiceGroup = [string, MeetingServiceRecord[]];
type ServiceDrag = { kind: 'item'; id: number; institution: string } | { kind: 'group'; institution: string };
type ServiceDrop = { key: string; after: boolean };

const moveEntry = <T,>(list: T[], from: number, to: number, after: boolean) => {
  const next = [...list];
  const [moved] = next.splice(from, 1);
  const target = from < to ? to - 1 : to;
  next.splice(after ? target + 1 : target, 0, moved);
  return next;
};

const dropsAfter = (event: DragEvent<HTMLElement>) => {
  const rect = event.currentTarget.getBoundingClientRect();
  return event.clientY > rect.top + rect.height / 2;
};

function ServiceScene({ data, onReordered }: {
  data: PipelineMeetingData;
  onReordered: (records: MeetingServiceRecord[]) => void;
}) {
  // 회의에서는 보기만 한다(기관별 장비 목록). 입력·수정은 서비스 메뉴에서.
  const [error, setError] = useState('');
  const [drag, setDrag] = useState<ServiceDrag | null>(null);
  const [drop, setDrop] = useState<ServiceDrop | null>(null);

  const groups = useMemo<ServiceGroup[]>(() => {
    const byInstitution = new Map<string, MeetingServiceRecord[]>();
    data.services.forEach((record) => {
      byInstitution.set(record.institution, [...(byInstitution.get(record.institution) ?? []), record]);
    });
    return [...byInstitution.entries()];
  }, [data.services]);

  const applyOrder = async (nextGroups: ServiceGroup[]) => {
    const records = nextGroups.flatMap(([, rows]) => rows);
    const previous = data.services;
    onReordered(records);
    try {
      await reorderMeetingServices(data.week.start, records.map((record) => record.id));
    } catch (caught) {
      onReordered(previous);
      setError(caught instanceof Error ? caught.message : '순서를 저장하지 못했습니다.');
    }
  };

  const endDrag = () => {
    setDrag(null);
    setDrop(null);
  };

  const dropOnGroup = (event: DragEvent<HTMLElement>, name: string) => {
    event.preventDefault();
    event.stopPropagation();
    const current = drag;
    const after = dropsAfter(event);
    endDrag();
    if (!current || current.institution === name) return;
    const from = groups.findIndex(([group]) => group === current.institution);
    const to = groups.findIndex(([group]) => group === name);
    void applyOrder(moveEntry(groups, from, to, after));
  };

  const dropOnItem = (event: DragEvent<HTMLElement>, target: MeetingServiceRecord) => {
    const current = drag;
    // 다른 기관 위에 놓으면 기관 순서를 바꾼다 — 바깥 섹션의 dropOnGroup 이 처리하도록 넘긴다.
    if (current?.kind !== 'item' || current.institution !== target.institution) return;
    event.preventDefault();
    event.stopPropagation();
    const after = dropsAfter(event);
    endDrag();
    if (current.id === target.id) return;
    void applyOrder(groups.map(([name, rows]) => {
      if (name !== target.institution) return [name, rows] as ServiceGroup;
      const from = rows.findIndex((row) => row.id === current.id);
      const to = rows.findIndex((row) => row.id === target.id);
      return [name, moveEntry(rows, from, to, after)] as ServiceGroup;
    }));
  };

  const hover = (event: DragEvent<HTMLElement>, key: string, allowed: boolean) => {
    if (!allowed) return;
    event.preventDefault();
    event.stopPropagation();
    const after = dropsAfter(event);
    setDrop((current) => (current?.key === key && current.after === after ? current : { key, after }));
  };

  const dropClass = (key: string) => (drop?.key === key ? (drop.after ? ' drop-after' : ' drop-before') : '');

  return (
    <section className="meeting-panel meeting-service">
      <header>
        <h3>서비스 기록</h3>
        <small>
          끌어서 순서를 바꿀 수 있습니다 · <a href="/services/new/" rel="noreferrer" target="_blank">서비스 기록 추가</a>
        </small>
      </header>
      <div className="meeting-scroll">
        {groups.length === 0 ? <p className="meeting-empty">이 주의 서비스 기록이 없습니다. 서비스 메뉴에서 기록하면 여기에 보입니다.</p> : null}
        {groups.map(([name, records]) => (
          <section
            className={`meeting-service-group${dropClass(`group:${name}`)}${drag?.kind === 'group' && drag.institution === name ? ' dragging' : ''}`}
            key={name}
            onDragOver={(event) => hover(event, `group:${name}`, drag !== null && drag.institution !== name)}
            onDrop={(event) => dropOnGroup(event, name)}
          >
            <h4
              draggable
              onDragEnd={endDrag}
              onDragStart={(event) => {
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', name);
                setDrag({ kind: 'group', institution: name });
              }}
            >
              <GripVertical size={15} />{name}
            </h4>
            {records.map((record) => (
              <article
                className={`meeting-service-item${dropClass(`item:${record.id}`)}${drag?.kind === 'item' && drag.id === record.id ? ' dragging' : ''}`}
                draggable
                key={record.id}
                onDragEnd={endDrag}
                onDragOver={(event) => hover(event, `item:${record.id}`, drag?.kind === 'item' && drag.id !== record.id && drag.institution === record.institution)}
                onDragStart={(event) => {
                  event.stopPropagation();
                  event.dataTransfer.effectAllowed = 'move';
                  event.dataTransfer.setData('text/plain', String(record.id));
                  setDrag({ kind: 'item', id: record.id, institution: record.institution });
                }}
                onDrop={(event) => dropOnItem(event, record)}
              >
                <div className="meeting-service-text">
                  {record.equipments.length ? (
                    <ul className="meeting-equipments">
                      {record.equipments.map((equipment, index) => (
                        <li key={equipment.id ?? index}>
                          <strong>{[equipment.brand, equipment.name].filter(Boolean).join(' ') || '장비'}</strong>
                          {equipment.serialNumber ? <span>S/N {equipment.serialNumber}</span> : null}
                        </li>
                      ))}
                    </ul>
                  ) : <p className="meeting-muted">장비 미입력</p>}
                  <small>
                    {record.open ? (
                      <span className="meeting-service-open">
                        {record.statusLabel}{record.date ? ` · ${shortDate(record.date)} 접수` : ''}
                      </span>
                    ) : null}
                    {record.customer ? `${record.customer} · ` : ''}
                    <a href={record.href} rel="noreferrer" target="_blank">서비스 상세</a>
                  </small>
                </div>
              </article>
            ))}
          </section>
        ))}
      </div>
      {error ? <p className="meeting-error">{error}</p> : null}
    </section>
  );
}

function PlanScene({ data }: { data: PipelineMeetingData }) {
  const { plan } = data;
  if (plan.total === 0) {
    return (
      <div className="meeting-notice">
        <h2>{shortDate(plan.start)} 주에 잡힌 일정이 없습니다</h2>
        <p>오늘 회의에서 이번 주 일정을 잡아 주세요.</p>
      </div>
    );
  }
  return (
    <div className="meeting-plan">
      {plan.byOwner.map((owner, ownerIndex) => (
        <section className="meeting-column" key={owner.ownerId} style={{ animationDelay: `${ownerIndex * 100}ms` }}>
          <header><h3>{owner.owner}</h3><strong>{owner.items.length}</strong></header>
          <div className="meeting-column-body">
            {owner.items.map((item) => (
              <a className="meeting-plan-item" href={item.href} key={item.id}>
                <time>{item.weekday} {shortDate(item.date)}<small>{item.time}</small></time>
                <div>
                  <b>{item.company || item.customer}</b>
                  <small>{item.typeLabel}{item.company ? ` · ${item.customer}` : ''}</small>
                </div>
                {item.amount > 0 ? <strong>{formatWon(item.amount)}</strong> : null}
              </a>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function PipelineMeetingPage() {
  const [data, setData] = useState<PipelineMeetingData | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [week, setWeek] = useState('');
  const [user, setUser] = useState<number | null>(null);
  const [users, setUsers] = useState<{ id: number; name: string }[]>([]);
  const [scene, setScene] = useState(0);
  const [light, setLight] = useState(false);
  const [draft, setDraft] = useState<ActionDraft>({ title: '', ownerId: '', dueDate: '', followupId: '' });

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError('');
    loadPipelineMeeting({ week, user })
      .then((payload) => {
        if (!alive) return;
        setData(payload);
        // 담당자를 고르면 응답의 목록이 한 명으로 줄어드므로 처음 받은 전체 목록을 유지한다
        setUsers((current) => (payload.scope.users.length > current.length ? payload.scope.users : current));
        const friday = new Date(`${payload.plan.start}T00:00:00`);
        friday.setDate(friday.getDate() + 4);
        const due = `${friday.getFullYear()}-${String(friday.getMonth() + 1).padStart(2, '0')}-${String(friday.getDate()).padStart(2, '0')}`;
        setDraft((current) => ({
          ...current,
          ownerId: payload.form.owners.some((owner) => String(owner.id) === current.ownerId)
            ? current.ownerId
            : String(payload.form.owners[0]?.id ?? ''),
          dueDate: due,
        }));
      })
      .catch((caught) => {
        if (alive) setError(caught instanceof Error ? caught.message : '');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [week, user]);

  const go = useCallback((next: number) => {
    setScene(Math.max(0, Math.min(SCENES.length - 1, next)));
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void document.documentElement.requestFullscreen();
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(target.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
      // 버튼에 포커스가 있으면 스페이스는 그 버튼을 누르는 키다(장면까지 넘기면 두 동작이 겹친다)
      if (event.key === ' ' && target.tagName === 'BUTTON') return;
      if (['ArrowRight', 'PageDown', ' '].includes(event.key)) {
        event.preventDefault();
        setScene((current) => Math.min(SCENES.length - 1, current + 1));
      } else if (['ArrowLeft', 'PageUp'].includes(event.key)) {
        event.preventDefault();
        setScene((current) => Math.max(0, current - 1));
      } else if (/^[1-5]$/.test(event.key)) {
        setScene(Number(event.key) - 1);
      } else if (event.key === 'f') {
        toggleFullscreen();
      } else if (event.key === 't') {
        setLight((current) => !current);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [toggleFullscreen]);

  const dueReports = data?.promises.actionItems.filter((item) => item.kind === 'report' && item.dueReached).length ?? 0;

  const updateActions = (update: (items: MeetingActionItem[]) => MeetingActionItem[]) => {
    setData((current) => (current
      ? { ...current, promises: { ...current.promises, actionItems: update(current.promises.actionItems) } }
      : current));
  };

  return (
    <div className={`meeting-root ${light ? 'light' : ''}`}>
      <header className="meeting-top">
        <div className="meeting-title">
          <h1>아침회의</h1>
          {data ? <span>{shortDate(data.week.start)} – {shortDate(data.week.end)} 회고 · {data.scope.label}</span> : null}
        </div>
        <div className="meeting-controls">
          {data ? (
            <select aria-label="기준 주" onChange={(event) => setWeek(event.target.value)} value={data.week.start}>
              {data.weekOptions.map((option) => <option key={option.value} value={option.weekStart}>{option.label}</option>)}
            </select>
          ) : null}
          {users.length > 0 ? (
            <select aria-label="담당자" onChange={(event) => setUser(event.target.value ? Number(event.target.value) : null)} value={user ?? ''}>
              <option value="">전체</option>
              {users.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}
            </select>
          ) : null}
          <button aria-label="밝기 전환" onClick={() => setLight((current) => !current)} type="button">
            {light ? <Moon size={17} /> : <Sun size={17} />}
          </button>
          <button aria-label="전체화면" onClick={toggleFullscreen} type="button"><Maximize2 size={17} /></button>
          <a aria-label="나가기" href="/pipeline-sheet/"><X size={18} /></a>
        </div>
      </header>

      <main className="meeting-stage">
        {error ? (
          <div className="meeting-notice">
            <h2>회의 자료를 불러오지 못했습니다</h2>
            <p>{humanizeApiError(error)}</p>
          </div>
        ) : null}
        {!error && !data ? (
          <div className="meeting-notice"><Loader2 className="spin-icon" size={32} /></div>
        ) : null}
        {!error && data ? (
          <div className={`meeting-scene ${loading ? 'dim' : ''}`} key={`${scene}-${data.week.start}-${data.scope.selectedUserId ?? 'all'}`}>
            <h2 className="meeting-scene-title">
              {scene === 4 && weekNameOf(data.week.start) !== '지난주' ? `${shortDate(data.plan.start)} 주 계획` : SCENES[scene]}
              {scene === 4 ? <small>{shortDate(data.plan.start)} – {shortDate(data.plan.end)}</small> : null}
              {scene === 2 && data.movement.restored ? <small>일정 기록으로 복원한 주입니다 · 보드에서 직접 옮긴 건은 빠져 있을 수 있습니다</small> : null}
            </h2>
            {scene === 0 ? <SummaryScene data={data} /> : null}
            {scene === 1 ? (
              <ServiceScene
                data={data}
                onReordered={(records) => setData((current) => (current ? { ...current, services: records } : current))}
              />
            ) : null}
            {scene === 2 ? (
              <MovementScene
                data={data}
                onChanged={(movement, lostAmount) => setData((current) => (current
                  ? { ...current, movement, summary: { ...current.summary, lostAmount } }
                  : current))}
              />
            ) : null}
            {scene === 3 ? (
              <PromisesScene
                data={data}
                draft={draft}
                onChanged={(item) => updateActions((items) => items.map((row) => (row.id === item.id ? item : row)))}
                onCreated={(item) => updateActions((items) => [...items, item])}
                onDraftChange={setDraft}
                onNextActionsChange={(rows) => setData((current) => (current
                  ? { ...current, promises: { ...current.promises, nextActions: rows } }
                  : current))}
                onRemoved={(id) => updateActions((items) => items.filter((row) => row.id !== id))}
              />
            ) : null}
            {scene === 4 ? <PlanScene data={data} /> : null}
          </div>
        ) : null}
      </main>

      <footer className="meeting-nav">
        <button aria-label="이전" disabled={scene === 0} onClick={() => go(scene - 1)} type="button"><ChevronLeft size={20} /></button>
        <ol>
          {SCENES.map((label, index) => (
            <li key={label}>
              <button className={index === scene ? 'active' : ''} onClick={() => go(index)} type="button">
                <span>{index + 1}</span>{label}
                {label === '약속' && dueReports > 0 ? <em className="meeting-nav-badge">{dueReports}</em> : null}
              </button>
            </li>
          ))}
        </ol>
        <button aria-label="다음" disabled={scene === SCENES.length - 1} onClick={() => go(scene + 1)} type="button"><ChevronRight size={20} /></button>
      </footer>
    </div>
  );
}
