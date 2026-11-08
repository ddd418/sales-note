import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Maximize2,
  Moon,
  Plus,
  Sun,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
  createMeetingAction,
  deleteMeetingAction,
  loadMeetingBriefs,
  loadPipelineMeeting,
  toggleMeetingAction,
  type MeetingActionItem,
  type MeetingBlockedItem,
  type MeetingBrief,
  type MeetingMovementGroup,
  type MeetingMovementItem,
  type PipelineMeetingData,
} from '../../api/pipelineMeeting';
import { humanizeApiError } from '../../components/shared/FeedbackStates';
import { formatNumber, formatWon } from '../../components/shared/formatters';
import './pipelineMeeting.css';

const SCENES = ['요약', '활동', '약속', '장애물', '이번 주 계획'] as const;
const PROMISES_SCENE = 2;

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
        <div><span>납품 완료</span><strong>{formatNumber(summary.deliveryCount)}건</strong></div>
        <div><span>견적 금액</span><strong>{formatWon(summary.quoteAmount)}</strong></div>
        <div><span>활동한 계정</span><strong>{formatNumber(summary.activeAccounts)}곳</strong></div>
        <div><span>총 활동</span><strong>{formatNumber(summary.totalActivities)}건</strong></div>
      </section>
    </div>
  );
}

function MovementColumn({ title, tone, group, startIndex }: {
  title: string;
  tone: string;
  group: MeetingMovementGroup;
  startIndex: number;
}) {
  return (
    <section className={`meeting-column ${tone}`}>
      <header><h3>{title}</h3><strong>{group.count}</strong></header>
      <div className="meeting-column-body">
        {group.items.length === 0 ? <p className="meeting-empty">없음</p> : null}
        {group.items.map((item: MeetingMovementItem, index) => (
          <a
            className="meeting-move-card"
            href={item.href}
            key={item.followupId}
            style={{ animationDelay: `${(startIndex + index) * 70}ms` }}
          >
            <b>{item.company || item.customer}</b>
            <small>{item.company ? item.customer : ''} · {item.owner}</small>
            <span className="meeting-move-flow">
              <em>{item.fromLabel}</em><ArrowRight size={14} /><em className="to">{item.toLabel}</em>
              {item.amount > 0 ? <strong>{formatWon(item.amount)}</strong> : null}
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}

function MovementScene({ data }: { data: PipelineMeetingData }) {
  const { movement } = data;
  if (!movement.tracked) {
    return (
      <div className="meeting-notice">
        <h2>이 주의 단계 변경 기록이 없습니다</h2>
        <p>
          단계 변경은 {movement.trackingSince ? `${shortDate(movement.trackingSince)}부터` : '이번 배포부터'} 기록하고 있습니다.
          기록이 시작된 다음 회의부터 이 장면이 채워집니다.
        </p>
      </div>
    );
  }
  return (
    <div className="meeting-movement">
      {movement.won.count > 0 ? <WinBurst /> : null}
      <MovementColumn group={movement.won} startIndex={0} title="수주" tone="won" />
      <MovementColumn group={movement.advanced} startIndex={2} title="전진" tone="advanced" />
      <MovementColumn
        group={{
          count: movement.regressed.count + movement.lost.count,
          items: [...movement.regressed.items, ...movement.lost.items],
        }}
        startIndex={4}
        title="후퇴 · 실주"
        tone="regressed"
      />
      <MovementColumn group={movement.created} startIndex={6} title="신규" tone="created" />
    </div>
  );
}

type ActionDraft = { title: string; ownerId: string; dueDate: string; followupId: string };

function PromisesScene({ data, draft, onDraftChange, onCreated, onChanged, onRemoved }: {
  data: PipelineMeetingData;
  draft: ActionDraft;
  onDraftChange: (draft: ActionDraft) => void;
  onCreated: (item: MeetingActionItem) => void;
  onChanged: (item: MeetingActionItem) => void;
  onRemoved: (id: number) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const titleRef = useRef<HTMLInputElement>(null);
  const { actionItems, nextActions } = data.promises;

  useEffect(() => {
    if (draft.followupId) titleRef.current?.focus();
  }, [draft.followupId]);

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
          {actionItems.length === 0 ? <p className="meeting-empty">아직 약속이 없습니다. 아래에서 오늘 정한 일을 적어 주세요.</p> : null}
          {actionItems.map((item) => (
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
                <b>{item.title}</b>
                <small>
                  {item.owner}
                  {item.customer ? ` · ${item.company ? `${item.company} ` : ''}${item.customer}` : ''}
                </small>
              </div>
              {item.carriedWeeks > 0 && item.status === 'open' ? <em className="meeting-tag warn">{item.carriedWeeks}주째</em> : null}
              {item.dueDate ? <em className={`meeting-tag ${item.overdue ? 'danger' : ''}`}>{shortDate(item.dueDate)}까지</em> : null}
              {item.canEdit ? (
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
          <select aria-label="관련 고객" onChange={(event) => onDraftChange({ ...draft, followupId: event.target.value })} value={draft.followupId}>
            <option value="">고객 선택 안 함</option>
            {data.form.customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.label}</option>)}
          </select>
          <button disabled={saving} type="submit">
            {saving ? <Loader2 className="spin-icon" size={16} /> : <Plus size={16} />}추가
          </button>
        </form>
        {error ? <p className="meeting-error">{error}</p> : null}
      </section>
      <section className="meeting-panel">
        <header>
          <h3>{weekNameOf(data.week.start)} 다음 액션</h3>
          <small>
            후속 기록 있음 {nextActions.filter((row) => row.followedUp).length} · 없음 {nextActions.filter((row) => !row.followedUp).length}
          </small>
        </header>
        <div className="meeting-scroll">
          {nextActions.length === 0 ? <p className="meeting-empty">이 주가 기한인 다음 액션이 없습니다.</p> : null}
          {nextActions.map((row) => (
            <a className="meeting-next" href={row.href} key={row.id}>
              <i className={row.followedUp ? 'ok' : 'miss'}>{row.followedUp ? <Check size={14} /> : <X size={14} />}</i>
              <div>
                <b>{row.text}</b>
                <small>{row.company} {row.customer} · {row.owner} · {shortDate(row.dueDate)}</small>
              </div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

function BlockedScene({ data, briefs, briefsLoading, onPromise }: {
  data: PipelineMeetingData;
  briefs: Record<string, MeetingBrief>;
  briefsLoading: boolean;
  onPromise: (item: MeetingBlockedItem) => void;
}) {
  const { blocked } = data;
  if (blocked.items.length === 0) {
    return (
      <div className="meeting-notice">
        <h2>장애물이 없습니다</h2>
        <p>최근 장애물이 기록되었거나 {`2주 이상`} 조용한 진행 건이 없습니다.</p>
      </div>
    );
  }
  return (
    <div className="meeting-blocked">
      {blocked.items.map((item, index) => {
        const brief = item.noteId ? briefs[String(item.noteId)] : undefined;
        return (
          <article className="meeting-blocked-card" key={item.followupId} style={{ animationDelay: `${index * 120}ms` }}>
            <header>
              <span>{item.stageLabel}</span>
              <strong>{item.amount > 0 ? formatWon(item.amount) : '금액 미정'}</strong>
            </header>
            <h3>{item.company || item.customer}</h3>
            <small>{item.company ? item.customer : ''} · {item.owner}</small>
            {brief ? (
              <dl className="meeting-brief">
                {brief.situation ? <div><dt>상황</dt><dd>{brief.situation}</dd></div> : null}
                {brief.blocker ? <div><dt>장애물</dt><dd>{brief.blocker}</dd></div> : null}
                {brief.nextStep ? <div><dt>다음 할 일</dt><dd>{brief.nextStep}</dd></div> : null}
              </dl>
            ) : (
              <p className="meeting-reason">{item.obstacle || (briefsLoading ? '노트를 요약하는 중입니다' : '최근 노트에 장애물 기록이 없습니다')}</p>
            )}
            <footer>
              <em className={item.idleDays >= 14 ? 'danger' : ''}>
                {item.idleDays === 0 ? '오늘 활동 있음' : `마지막 활동 ${item.idleDays}일 전`}{item.hasNextStep ? '' : ' · 다음 일정 없음'}
              </em>
              <button onClick={() => onPromise(item)} type="button">약속으로 남기기</button>
            </footer>
          </article>
        );
      })}
      {blocked.total > blocked.items.length ? <p className="meeting-more">금액이 큰 순으로 {blocked.items.length}건만 표시했습니다 (전체 {blocked.total}건)</p> : null}
    </div>
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
  const [briefs, setBriefs] = useState<Record<string, MeetingBrief>>({});
  const [briefsLoading, setBriefsLoading] = useState(false);
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

  useEffect(() => {
    if (!data?.canUseAi) return undefined;
    const noteIds = data.blocked.items.map((item) => item.noteId).filter((id): id is number => Boolean(id));
    if (noteIds.length === 0) return undefined;
    let alive = true;
    setBriefsLoading(true);
    loadMeetingBriefs(noteIds)
      .then((result) => {
        if (alive) setBriefs((current) => ({ ...current, ...result }));
      })
      // 요약이 없어도 회의는 진행돼야 한다 — 카드는 장애물 원문을 보여 준다
      .catch(() => undefined)
      .finally(() => {
        if (alive) setBriefsLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [data?.canUseAi, data?.blocked.items]);

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

  const updateActions = (update: (items: MeetingActionItem[]) => MeetingActionItem[]) => {
    setData((current) => (current
      ? { ...current, promises: { ...current.promises, actionItems: update(current.promises.actionItems) } }
      : current));
  };

  const promiseFromBlocked = (item: MeetingBlockedItem) => {
    setDraft((current) => ({
      ...current,
      followupId: String(item.followupId),
      ownerId: String(item.ownerId),
      title: '',
    }));
    go(PROMISES_SCENE);
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
            </h2>
            {scene === 0 ? <SummaryScene data={data} /> : null}
            {scene === 1 ? <MovementScene data={data} /> : null}
            {scene === 2 ? (
              <PromisesScene
                data={data}
                draft={draft}
                onChanged={(item) => updateActions((items) => items.map((row) => (row.id === item.id ? item : row)))}
                onCreated={(item) => updateActions((items) => [...items, item])}
                onDraftChange={setDraft}
                onRemoved={(id) => updateActions((items) => items.filter((row) => row.id !== id))}
              />
            ) : null}
            {scene === 3 ? <BlockedScene briefs={briefs} briefsLoading={briefsLoading} data={data} onPromise={promiseFromBlocked} /> : null}
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
              </button>
            </li>
          ))}
        </ol>
        <button aria-label="다음" disabled={scene === SCENES.length - 1} onClick={() => go(scene + 1)} type="button"><ChevronRight size={20} /></button>
      </footer>
    </div>
  );
}
