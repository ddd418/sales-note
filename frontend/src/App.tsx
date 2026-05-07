import {
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleDollarSign,
  Columns3,
  FileText,
  Filter,
  LayoutDashboard,
  ListChecks,
  Loader2,
  MessageSquareText,
  MoveUpRight,
  ArrowRightLeft,
  PanelRight,
  Plus,
  Search,
  Sparkles,
  Target,
  Users,
} from 'lucide-react';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { loadPipelineData, moveDealStage } from './api';
import { Deal, mockPipelineData, PipelineData, PipelineStage, PriorityTask, StageSummary } from './mockData';

const navItems = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';
type MainView = 'dashboard' | 'customers' | 'pipeline' | 'notes' | 'schedules' | 'ai';

type RouteAction = {
  label: string;
  href: string;
  primary?: boolean;
};

const routeMeta: Record<
  MainView,
  {
    eyebrow: string;
    title: string;
    summary: string;
    primaryHref: string;
    primaryLabel: string;
    actions: RouteAction[];
  }
> = {
  dashboard: {
    eyebrow: 'Sales CRM / Dashboard',
    title: '대시보드',
    summary: '영업 현황, 지연 후속, 이번 주 접촉을 한 화면에서 확인합니다.',
    primaryHref: '/reporting/dashboard/',
    primaryLabel: '운영 대시보드 열기',
    actions: [
      { label: '영업노트 작성', href: '/reporting/dashboard/#dashboardNoteModal', primary: true },
      { label: '미검토 노트', href: '/reporting/histories/?review_filter=unreviewed' },
      { label: '고객 리포트', href: '/reporting/customer-report/' },
    ],
  },
  customers: {
    eyebrow: 'Sales CRM / Customers',
    title: '고객',
    summary: '고객, 업체, 팔로우업, 고객 리포트를 하나의 고객 업무 흐름으로 묶습니다.',
    primaryHref: '/reporting/followups/',
    primaryLabel: '고객/팔로우업 열기',
    actions: [
      { label: '새 고객 등록', href: '/reporting/followups/create/', primary: true },
      { label: '고객사 관리', href: '/reporting/companies/' },
      { label: '고객 리포트', href: '/reporting/customer-report/' },
    ],
  },
  pipeline: {
    eyebrow: 'Sales CRM / Pipeline',
    title: '파이프라인 관리',
    summary: '견적, 협상, 수주 가능성을 중심으로 이번 주 우선 영업 건을 관리합니다.',
    primaryHref: '/',
    primaryLabel: '파이프라인 보기',
    actions: [
      { label: 'Django 파이프라인 리스트', href: '/reporting/funnel/' },
      { label: 'Django 파이프라인 보드', href: '/reporting/funnel/pipeline/' },
    ],
  },
  notes: {
    eyebrow: 'Sales CRM / Notes',
    title: '영업노트',
    summary: '영업 활동 기록, 검토 상태, 고객별 히스토리를 빠르게 확인합니다.',
    primaryHref: '/reporting/histories/',
    primaryLabel: '영업노트 목록 열기',
    actions: [
      { label: '대시보드 노트 작성', href: '/reporting/dashboard/#dashboardNoteModal', primary: true },
      { label: '미검토 노트', href: '/reporting/histories/?review_filter=unreviewed' },
      { label: '주간보고', href: '/reporting/weekly-reports/' },
    ],
  },
  schedules: {
    eyebrow: 'Sales CRM / Schedule',
    title: '일정',
    summary: '방문, 견적, 납품, 후속 연락 일정을 한 흐름에서 관리합니다.',
    primaryHref: '/reporting/schedules/',
    primaryLabel: '일정 목록 열기',
    actions: [
      { label: '새 일정 등록', href: '/reporting/schedules/create/', primary: true },
      { label: '일정 캘린더', href: '/reporting/schedules/calendar/' },
      { label: '이번 주 보고', href: '/reporting/weekly-reports/' },
    ],
  },
  ai: {
    eyebrow: 'Sales CRM / AI',
    title: 'AI 업무도구',
    summary: '부서 분석 결과와 목표를 조합해 외부 AI용 업무 프롬프트를 생성합니다.',
    primaryHref: '/ai/',
    primaryLabel: 'AI 분석/프롬프트 열기',
    actions: [
      { label: 'AI 허브 열기', href: '/ai/', primary: true },
      { label: '고객 리포트', href: '/reporting/customer-report/' },
      { label: '영업노트', href: '/reporting/histories/' },
    ],
  },
};

function getCurrentView(): MainView {
  const pathname = window.location.pathname.replace(/\/+$/, '/') || '/';
  if (pathname.startsWith('/dashboard/')) return 'dashboard';
  if (pathname.startsWith('/customers/')) return 'customers';
  if (pathname.startsWith('/notes/')) return 'notes';
  if (pathname.startsWith('/schedules/')) return 'schedules';
  if (pathname.startsWith('/ai-workspace/')) return 'ai';
  return 'pipeline';
}

const savedViews: Array<{ id: SavedView; label: string }> = [
  { id: 'priority', label: '내 담당 우선' },
  { id: 'thisWeek', label: '이번 주 마감' },
  { id: 'quoteDelay', label: '견적 제출 후 지연' },
  { id: 'managerReview', label: '관리자 검토' },
];

const formatWon = (value: number) =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const riskLabel: Record<Deal['risk'], string> = {
  low: '정상',
  medium: '확인',
  high: '지연',
};

function AppShell({ activeView, children }: { activeView: MainView; children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SN</div>
          <div>
            <strong>영업 보고 시스템</strong>
            <span>CRM Workspace</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="CRM navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <a className={`nav-item ${item.id === activeView ? 'active' : ''}`} href={item.href} key={item.label}>
                <Icon size={18} />
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>
        <div className="sidebar-note">
          <span>운영 기준</span>
          <strong>React Shell + Django API</strong>
          <p>핵심 메뉴는 프론트에서 시작하고, 저장/상세 작업은 검증된 Django 화면과 연결합니다.</p>
        </div>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}

function TopBar({
  activeView,
  searchQuery,
  onSearchChange,
}: {
  activeView: MainView;
  searchQuery: string;
  onSearchChange: (value: string) => void;
}) {
  const meta = routeMeta[activeView];
  const showSearch = activeView === 'pipeline';
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">{meta.eyebrow}</div>
        <h1>{meta.title}</h1>
      </div>
      <div className="topbar-actions">
        {showSearch ? (
          <label className="search-box">
            <Search size={17} />
            <input
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="고객, 담당자, 품목, 다음 액션 검색"
              value={searchQuery}
            />
          </label>
        ) : null}
        <a className="icon-button" aria-label="알림" href="/reporting/dashboard/">
          <Bell size={18} />
        </a>
        <a className="primary-button" href="/reporting/dashboard/#dashboardNoteModal">
          <Plus size={17} />
          새 영업노트
        </a>
      </div>
    </header>
  );
}

function WorkspaceRoutePage({ data, view }: { data: PipelineData; view: MainView }) {
  const meta = routeMeta[view];
  const urgentDeals = data.deals
    .filter((deal) => deal.risk === 'high' || deal.stage === 'quote' || deal.stage === 'negotiation')
    .slice(0, 5);
  const routeStats = [
    {
      label: '활성 고객',
      value: `${data.metrics.activeCount}건`,
      detail: '파이프라인 기준',
    },
    {
      label: '지연 후속',
      value: `${data.metrics.overdueCount}건`,
      detail: '우선 대응',
    },
    {
      label: '예상 매출',
      value: formatWon(data.metrics.weightedPipelineValue),
      detail: '확률 가중',
    },
  ];

  return (
    <section className="workspace-route-page">
      <div className="route-hero">
        <div>
          <span className="eyebrow">{meta.eyebrow}</span>
          <h2>{meta.title}</h2>
          <p>{meta.summary}</p>
        </div>
        <a className="route-primary-action" href={meta.primaryHref}>
          {meta.primaryLabel}
          <MoveUpRight size={16} />
        </a>
      </div>

      <div className="route-stat-grid">
        {routeStats.map((stat) => (
          <article className="route-stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.detail}</small>
          </article>
        ))}
      </div>

      <div className="route-content-grid">
        <article className="route-card">
          <div className="panel-heading">
            <span>주요 작업</span>
            <ArrowRightLeft size={15} />
          </div>
          <div className="route-action-list">
            {meta.actions.map((action) => (
              <a className={action.primary ? 'primary' : ''} href={action.href} key={action.label}>
                {action.label}
                <ChevronRight size={15} />
              </a>
            ))}
          </div>
        </article>

        <article className="route-card">
          <div className="panel-heading">
            <span>우선 확인 고객</span>
            <Users size={15} />
          </div>
          <div className="route-deal-list">
            {urgentDeals.map((deal) => (
              <a href={deal.detailUrl || '/reporting/followups/'} key={deal.id}>
                <div>
                  <strong>{deal.company}</strong>
                  <span>{deal.contact} · {deal.owner}</span>
                </div>
                <small className={`risk-badge ${deal.risk}`}>{riskLabel[deal.risk]}</small>
              </a>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}

function MetricStrip({ data }: { data: PipelineData }) {
  const metrics = [
    {
      label: '총 파이프라인',
      value: formatWon(data.metrics.totalPipelineValue),
      detail: `활성 ${data.metrics.activeCount}건`,
      icon: CircleDollarSign,
    },
    {
      label: '예상 매출',
      value: formatWon(data.metrics.weightedPipelineValue),
      detail: '확률 가중',
      icon: Target,
    },
    {
      label: '지연 후속',
      value: `${data.metrics.overdueCount}건`,
      detail: '오늘 우선 처리',
      icon: Bell,
      alert: data.metrics.overdueCount > 0,
    },
    {
      label: '접촉/미팅',
      value: `${data.metrics.contactCount}건`,
      detail: '이번 주 일정',
      icon: MessageSquareText,
    },
  ];

  return (
    <section className="metric-strip" aria-label="핵심 파이프라인 지표">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <article className={`metric-card ${metric.alert ? 'alert' : ''}`} key={metric.label}>
            <div className="metric-icon">
              <Icon size={19} />
            </div>
            <div>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.detail}</small>
            </div>
          </article>
        );
      })}
    </section>
  );
}

function FilterRail({
  onViewChange,
  selectedView,
  source,
  tasks,
}: {
  onViewChange: (view: SavedView) => void;
  selectedView: SavedView;
  source: PipelineData['source'];
  tasks: PriorityTask[];
}) {
  return (
    <aside className="filter-rail">
      <div className="rail-section">
        <div className="rail-heading">
          <span>데이터</span>
        </div>
        <div className={`source-badge ${source}`}>
          {source === 'django' ? 'Django API 연결됨' : 'Mock data fallback'}
        </div>
      </div>
      <div className="rail-section">
        <div className="rail-heading">
          <span>저장된 뷰</span>
          <ChevronDown size={16} />
        </div>
        {savedViews.map((view) => (
          <button
            className={`view-chip ${selectedView === view.id ? 'selected' : ''}`}
            key={view.id}
            onClick={() => onViewChange(view.id)}
            type="button"
          >
            {view.label}
          </button>
        ))}
      </div>
      <div className="rail-section">
        <div className="rail-heading">
          <span>우선 대응</span>
        </div>
        {tasks.map((task) => (
          <div className={`task-chip ${task.tone}`} key={task.title}>
            <span>{task.title}</span>
            <strong>{task.count}</strong>
          </div>
        ))}
      </div>
      <div className="rail-section">
        <div className="rail-heading">
          <span>필터</span>
        </div>
        <button className="filter-button">
          <Filter size={16} />
          담당자: 전체
        </button>
        <button className="filter-button">
          <CalendarDays size={16} />
          마감: 30일
        </button>
      </div>
    </aside>
  );
}

function DealCard({ deal, selected, onSelect }: { deal: Deal; selected: boolean; onSelect: () => void }) {
  return (
    <button className={`deal-card ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <div className="deal-card-top">
        <strong>{deal.company}</strong>
        <span className={`risk-badge ${deal.risk}`}>{riskLabel[deal.risk]}</span>
      </div>
      <span className="deal-contact">{deal.contact}</span>
      <div className="deal-value">
        <span>{formatWon(deal.value)}</span>
        <small>{deal.probability}%</small>
      </div>
      <p>{deal.nextAction}</p>
      {deal.attentionReason ? <small className="attention-reason">{deal.attentionReason}</small> : null}
      <div className="deal-meta">
        <span>{deal.owner}</span>
        <span>{deal.due}</span>
      </div>
    </button>
  );
}

function PipelineBoard({
  selectedDeal,
  onSelect,
  stages,
  deals,
}: {
  selectedDeal?: Deal;
  onSelect: (deal: Deal) => void;
  stages: StageSummary[];
  deals: Deal[];
}) {
  const [collapsedStages, setCollapsedStages] = useState<Record<string, boolean>>({ potential: true });
  const dealsByStage = useMemo(() => {
    return stages.reduce<Record<PipelineStage, Deal[]>>((acc, stage) => {
      acc[stage.id] = deals.filter((deal) => deal.stage === stage.id);
      return acc;
    }, {} as Record<PipelineStage, Deal[]>);
  }, [deals, stages]);
  const topScrollRef = useRef<HTMLDivElement>(null);
  const boardScrollRef = useRef<HTMLElement>(null);
  const [scrollWidth, setScrollWidth] = useState(0);

  useLayoutEffect(() => {
    const updateScrollWidth = () => {
      setScrollWidth(boardScrollRef.current?.scrollWidth ?? 0);
    };
    updateScrollWidth();
    window.addEventListener('resize', updateScrollWidth);
    return () => window.removeEventListener('resize', updateScrollWidth);
  }, [deals, stages]);

  const syncScroll = (source: 'top' | 'board') => {
    const top = topScrollRef.current;
    const board = boardScrollRef.current;
    if (!top || !board) {
      return;
    }
    if (source === 'top' && board.scrollLeft !== top.scrollLeft) {
      board.scrollLeft = top.scrollLeft;
    }
    if (source === 'board' && top.scrollLeft !== board.scrollLeft) {
      top.scrollLeft = board.scrollLeft;
    }
  };

  return (
    <div className="pipeline-scroll-wrap">
      <div
        className="pipeline-scroll-top"
        ref={topScrollRef}
        onScroll={() => syncScroll('top')}
        aria-hidden="true"
      >
        <div style={{ width: scrollWidth }} />
      </div>
      <section
        className="pipeline-board"
        ref={boardScrollRef}
        onScroll={() => syncScroll('board')}
        aria-label="파이프라인 보드"
      >
        {stages.map((stage) => {
          const allStageDeals = dealsByStage[stage.id] || [];
          const visibleStageDeals =
            stage.id === 'potential'
              ? allStageDeals.filter((deal) => !deal.isPotentialOverflow)
              : allStageDeals;
          const stageDeals = visibleStageDeals;
          const total = stage.totalValue ?? stageDeals.reduce((sum, deal) => sum + deal.value, 0);
          const isCollapsed = Boolean(collapsedStages[stage.id]);
          const hiddenCount =
            stage.id === 'potential'
              ? allStageDeals.filter((deal) => deal.isPotentialOverflow).length
              : 0;
          const topPotential = stage.id === 'potential' ? stageDeals.slice(0, 3) : [];
          return (
            <div className={`stage-column ${isCollapsed ? 'collapsed' : ''}`} key={stage.id}>
              <div className="stage-header">
                <div>
                  <strong>{stage.label}</strong>
                  <span>{stage.caption}</span>
                </div>
                <div className="stage-header-actions">
                  <small>{stage.count ?? allStageDeals.length}</small>
                  {stage.id === 'potential' ? (
                    <button
                      className="stage-collapse-button"
                      onClick={() =>
                        setCollapsedStages((current) => ({
                          ...current,
                          [stage.id]: !current[stage.id],
                        }))
                      }
                      aria-label={isCollapsed ? '잠재 컬럼 펼치기' : '잠재 컬럼 접기'}
                    >
                      {isCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                    </button>
                  ) : null}
                </div>
              </div>
              <div className="stage-total">{formatWon(total)}</div>
              {isCollapsed && stage.id === 'potential' ? (
                <div className="collapsed-stage-summary">
                  <strong>우선 잠재 고객 {stageDeals.length}건</strong>
                  <span>전체 {allStageDeals.length}건 중 점수 높은 고객만 먼저 관리합니다.</span>
                  <div className="mini-deal-list">
                    {topPotential.map((deal) => (
                      <button key={deal.id} onClick={() => onSelect(deal)}>
                        <span>{deal.company}</span>
                        <strong>{deal.attentionScore ?? 0}</strong>
                      </button>
                    ))}
                  </div>
                  <button
                    className="show-stage-button"
                    onClick={() =>
                      setCollapsedStages((current) => ({
                        ...current,
                        [stage.id]: false,
                      }))
                    }
                  >
                    TOP 10 펼치기
                  </button>
                  {hiddenCount > 0 ? <small>나머지 {hiddenCount}건은 리스트 보기에서 확인</small> : null}
                </div>
              ) : (
                <div className="stage-deals">
                  {stageDeals.map((deal) => (
                    <DealCard
                      deal={deal}
                      key={deal.id}
                      selected={deal.id === selectedDeal?.id}
                      onSelect={() => onSelect(deal)}
                    />
                  ))}
                  {hiddenCount > 0 ? (
                    <div className="stage-overflow-note">
                      추가 잠재 고객 {hiddenCount}건은 리스트 보기에서 확인할 수 있습니다.
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}

function PipelineList({
  onSelect,
  stages,
  deals,
}: {
  onSelect: (deal: Deal) => void;
  stages: StageSummary[];
  deals: Deal[];
}) {
  return (
    <section className="list-panel" aria-label="파이프라인 리스트">
      <table>
        <thead>
          <tr>
            <th>고객</th>
            <th>단계</th>
            <th>예상 매출</th>
            <th>확률</th>
            <th>다음 액션</th>
            <th>담당</th>
          </tr>
        </thead>
        <tbody>
          {deals.map((deal) => (
            <tr key={deal.id} onClick={() => onSelect(deal)}>
              <td>
                <strong>{deal.company}</strong>
                <span>{deal.contact}</span>
              </td>
              <td>{stages.find((stage) => stage.id === deal.stage)?.label}</td>
              <td>{formatWon(deal.value)}</td>
              <td>{deal.probability}%</td>
              <td>{deal.nextAction}</td>
              <td>{deal.owner}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function DetailPanel({
  deal,
  stages,
  canMove,
  moving,
  moveError,
  moveMessage,
  onMoveStage,
}: {
  deal?: Deal;
  stages: StageSummary[];
  canMove: boolean;
  moving: boolean;
  moveError: string;
  moveMessage: string;
  onMoveStage: (deal: Deal, stage: PipelineStage) => void;
}) {
  if (!deal) {
    return (
      <aside className="detail-panel empty">
        <div className="panel-heading">
          <span>선택 고객</span>
          <PanelRight size={18} />
        </div>
        <h2>표시할 고객이 없습니다</h2>
        <p className="muted">Django API에 접근 가능한 파이프라인 데이터가 없으면 여기에 빈 상태가 표시됩니다.</p>
      </aside>
    );
  }

  return (
    <aside className="detail-panel">
      <div className="panel-heading">
        <span>선택 고객</span>
        <PanelRight size={18} />
      </div>
      <div className="detail-title-row">
        <div>
          <h2>{deal.company}</h2>
          <p className="muted">{deal.contact} · {deal.owner}</p>
        </div>
        {deal.detailUrl ? (
          <a className="detail-link" href={deal.detailUrl}>
            <MoveUpRight size={16} />
          </a>
        ) : null}
      </div>
      <div className="detail-status-row">
        <span>{deal.stageLabel ?? deal.stage}</span>
        <span className={`risk-badge ${deal.risk}`}>{riskLabel[deal.risk]}</span>
      </div>
      <div className="stage-move-box">
        <div className="stage-move-heading">
          <span>단계 변경</span>
          {moving ? <Loader2 className="spin-icon" size={15} /> : <ArrowRightLeft size={15} />}
        </div>
        <div className="stage-button-grid">
          {stages.map((stage) => (
            <button
              className={stage.id === deal.stage ? 'active' : ''}
              disabled={!canMove || moving || stage.id === deal.stage}
              key={stage.id}
              onClick={() => onMoveStage(deal, stage.id)}
              type="button"
            >
              {stage.label}
            </button>
          ))}
        </div>
        {!canMove ? <small className="move-help">Django API 연결 상태에서만 단계 변경이 가능합니다.</small> : null}
        {moveMessage ? <small className="move-status success">{moveMessage}</small> : null}
        {moveError ? <small className="move-status error">{moveError}</small> : null}
      </div>
      <div className="detail-value">
        <span>예상 매출</span>
        <strong>{formatWon(deal.value)}</strong>
      </div>
      <div className="progress-wrap">
        <div className="progress-label">
          <span>수주 가능성</span>
          <strong>{deal.probability}%</strong>
        </div>
        <div className="progress-track">
          <div style={{ width: `${deal.probability}%` }} />
        </div>
      </div>
      <div className="next-action">
        <span>다음 액션</span>
        <strong>{deal.nextAction}</strong>
        <small>{deal.due}</small>
      </div>
      {deal.nextSchedule ? (
        <div className="detail-box">
          <div className="section-title">다음 일정</div>
          <strong>{deal.nextSchedule.type}</strong>
          <span>
            {deal.nextSchedule.date} {deal.nextSchedule.time}
            {deal.nextSchedule.location ? ` · ${deal.nextSchedule.location}` : ''}
          </span>
        </div>
      ) : null}
      {deal.latestQuote ? (
        <div className="detail-box quote">
          <div className="section-title">최근 견적</div>
          <div className="quote-line">
            <strong>{deal.latestQuote.number}</strong>
            <span>{deal.latestQuote.stage}</span>
          </div>
          <div className="quote-line">
            <strong>{formatWon(deal.latestQuote.amount)}</strong>
            <span>{deal.latestQuote.probability}%</span>
          </div>
          {deal.latestQuote.validUntil ? <small>유효기한 {deal.latestQuote.validUntil}</small> : null}
        </div>
      ) : null}
      <div className="tag-row">
        {deal.tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
      <div className="activity-list">
        <div className="section-title">최근 활동</div>
        {(deal.recentActivities?.length ? deal.recentActivities : [{ type: '활동', date: '', summary: deal.lastActivity }]).map((activity) => (
          <div className="activity-item" key={`${activity.type}-${activity.date}-${activity.summary}`}>
            <CheckCircle2 size={16} />
            <span>
              <strong>{activity.type}</strong>
              {activity.date ? ` · ${activity.date}` : ''} {activity.summary}
            </span>
          </div>
        ))}
      </div>
      {deal.detailUrl ? (
        <a className="detail-primary-link" href={deal.detailUrl}>
          Django 고객 상세 열기
          <MoveUpRight size={16} />
        </a>
      ) : null}
    </aside>
  );
}

export function App() {
  const currentView = getCurrentView();
  const [mode, setMode] = useState<'board' | 'list'>('board');
  const [pipelineData, setPipelineData] = useState(mockPipelineData);
  const [selectedDealId, setSelectedDealId] = useState<number | null>(mockPipelineData.deals[0]?.id ?? null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<SavedView>('priority');
  const [movingDealId, setMovingDealId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState('');
  const [moveMessage, setMoveMessage] = useState('');

  useEffect(() => {
    let alive = true;
    loadPipelineData().then((data) => {
      if (!alive) {
        return;
      }
      setPipelineData(data);
      setSelectedDealId(data.deals[0]?.id ?? null);
    });
    return () => {
      alive = false;
    };
  }, []);

  const selectDeal = (deal: Deal) => {
    setSelectedDealId(deal.id);
    setMoveError('');
    setMoveMessage('');
  };
  const handleMoveStage = async (deal: Deal, stage: PipelineStage) => {
    if (pipelineData.source !== 'django' || deal.stage === stage) {
      return;
    }
    setMovingDealId(deal.id);
    setMoveError('');
    setMoveMessage('');
    try {
      await moveDealStage(deal.id, stage);
      const data = await loadPipelineData();
      setPipelineData(data);
      setSelectedDealId(data.deals.some((item) => item.id === deal.id) ? deal.id : data.deals[0]?.id ?? null);
      setMoveMessage('단계가 변경되었습니다.');
    } catch (error) {
      setMoveError(error instanceof Error ? error.message : '단계 변경에 실패했습니다.');
    } finally {
      setMovingDealId(null);
    }
  };
  const visibleDeals = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return pipelineData.deals.filter((deal) => {
      const matchesQuery =
        !normalizedQuery ||
        [
          deal.company,
          deal.contact,
          deal.department || '',
          deal.owner,
          deal.nextAction,
          deal.lastActivity,
          ...deal.tags,
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalizedQuery);
      if (!matchesQuery) {
        return false;
      }
      if (selectedView === 'thisWeek') {
        const dueText = deal.due || '';
        return (
          dueText.includes('오늘') ||
          dueText.includes('내일') ||
          dueText.includes('금요일') ||
          dueText.includes('이번 주') ||
          dueText.includes('일 후')
        );
      }
      if (selectedView === 'quoteDelay') {
        return deal.stage === 'quote' && deal.risk === 'high';
      }
      if (selectedView === 'managerReview') {
        return deal.tags.some((tag) => tag.includes('관리자')) || deal.stage === 'negotiation';
      }
      return true;
    });
  }, [pipelineData.deals, searchQuery, selectedView]);
  const visibleSelectedDeal = visibleDeals.find((deal) => deal.id === selectedDealId) ?? visibleDeals[0];

  if (currentView !== 'pipeline') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <WorkspaceRoutePage data={pipelineData} view={currentView} />
      </AppShell>
    );
  }

  return (
    <AppShell activeView={currentView}>
      <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
      <MetricStrip data={pipelineData} />
      <div className="content-grid">
        <FilterRail
          onViewChange={setSelectedView}
          selectedView={selectedView}
          tasks={pipelineData.priorityTasks}
          source={pipelineData.source}
        />
        <section className="center-panel">
          <div className="panel-toolbar">
            <div>
              <span className="eyebrow">Active pipeline</span>
              <h2>이번 주 우선 영업 건</h2>
            </div>
            <div className="segmented-control" role="tablist" aria-label="보기 방식">
              <button className={mode === 'board' ? 'active' : ''} onClick={() => setMode('board')}>
                <Columns3 size={16} />
                보드
              </button>
              <button className={mode === 'list' ? 'active' : ''} onClick={() => setMode('list')}>
                <ListChecks size={16} />
                리스트
              </button>
            </div>
          </div>
          {visibleDeals.length === 0 ? (
            <div className="empty-state">
              <strong>조건에 맞는 파이프라인이 없습니다</strong>
              <span>검색어를 지우거나 저장된 뷰를 변경해보세요.</span>
            </div>
          ) : mode === 'board' ? (
            <PipelineBoard
              selectedDeal={visibleSelectedDeal}
              onSelect={selectDeal}
              stages={pipelineData.stages}
              deals={visibleDeals}
            />
          ) : (
            <PipelineList onSelect={selectDeal} stages={pipelineData.stages} deals={visibleDeals} />
          )}
        </section>
        <DetailPanel
          deal={visibleSelectedDeal}
          stages={pipelineData.stages}
          canMove={pipelineData.source === 'django'}
          moving={Boolean(visibleSelectedDeal && movingDealId === visibleSelectedDeal.id)}
          moveError={moveError}
          moveMessage={moveMessage}
          onMoveStage={handleMoveStage}
        />
      </div>
    </AppShell>
  );
}
