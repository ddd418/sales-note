import {
  Activity,
  AlertTriangle,
  Bell,
  Building2,
  CalendarDays,
  CheckCircle2,
  Check,
  ChevronDown,
  ChevronRight,
  CircleDollarSign,
  Clock,
  Columns3,
  Copy,
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
import { type FormEvent, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  DashboardData,
  DashboardHistoryItem,
  DashboardScheduleItem,
  CustomersData,
  CustomerItem,
  NotesData,
  NoteItem,
  SchedulesData,
  ScheduleItem,
  AIWorkspaceData,
  AIWorkspaceDepartment,
  AIWorkspaceFollowupTarget,
  AIWorkspacePainpoint,
  AIWorkspacePromptTarget,
  NoteCreatePayload,
  createNote as createSalesNote,
  loadDashboardData,
  loadCustomersData,
  loadNotesData,
  loadSchedulesData,
  loadAIWorkspaceData,
  loadPipelineData,
  moveDealStage,
  toggleNoteReviewed,
} from './api';
import { Deal, mockPipelineData, PipelineData, PipelineStage, PriorityTask, StageSummary } from './mockData';

const navItems = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

const scheduleCalendarUrl = '/reporting/schedules/calendar/';

type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';
type MainView = 'dashboard' | 'customers' | 'pipeline' | 'notes' | 'schedules' | 'ai';

type RouteAction = {
  label: string;
  href: string;
  primary?: boolean;
};

type NoteCreateFormState = {
  actionType: string;
  activityDate: string;
  content: string;
  followupId: string;
  nextAction: string;
  nextActionDate: string;
};

const localDateInputValue = (date = new Date()) => {
  const localTime = date.getTime() - date.getTimezoneOffset() * 60_000;
  return new Date(localTime).toISOString().slice(0, 10);
};

const makeEmptyNoteCreateForm = (): NoteCreateFormState => ({
  actionType: 'customer_meeting',
  activityDate: localDateInputValue(),
  content: '',
  followupId: '',
  nextAction: '',
  nextActionDate: '',
});

const shouldOpenCreateNote = () => new URLSearchParams(window.location.search).get('create') === '1';

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
    primaryHref: '/dashboard/',
    primaryLabel: '프론트 대시보드 보기',
    actions: [
      { label: '영업노트 작성', href: '/notes/?create=1', primary: true },
      { label: '미검토 노트', href: '/notes/' },
      { label: '고객 리포트', href: '/reporting/customer-report/' },
    ],
  },
  customers: {
    eyebrow: 'Sales CRM / Customers',
    title: '고객',
    summary: '고객, 업체, 팔로우업, 고객 리포트를 하나의 고객 업무 흐름으로 묶습니다.',
    primaryHref: '/customers/',
    primaryLabel: '프론트 고객 보기',
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
    primaryHref: '/notes/',
    primaryLabel: '프론트 영업노트 보기',
    actions: [
      { label: '노트 작성', href: '/notes/?create=1', primary: true },
      { label: '미검토 노트', href: '/notes/' },
      { label: '주간보고', href: '/reporting/weekly-reports/' },
    ],
  },
  schedules: {
    eyebrow: 'Sales CRM / Schedule',
    title: '일정',
    summary: '방문, 견적, 납품, 후속 연락 일정을 캘린더 중심으로 관리합니다.',
    primaryHref: scheduleCalendarUrl,
    primaryLabel: '일정 캘린더 열기',
    actions: [
      { label: '일정 캘린더', href: scheduleCalendarUrl, primary: true },
      { label: '새 일정 등록', href: '/reporting/schedules/create/' },
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
  { id: 'managerReview', label: '매니저 검토' },
];

const formatWon = (value: number) =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const formatSignedWon = (value: number) => {
  if (value > 0) return `+${formatWon(value)}`;
  if (value < 0) return `-${formatWon(Math.abs(value))}`;
  return formatWon(0);
};

const formatSignedPercent = (value: number) => `${value > 0 ? '+' : ''}${value}%`;

const formatNumber = (value: number) => new Intl.NumberFormat('ko-KR').format(value);

const formatDateLabel = (value?: string | null) => {
  if (!value) return '';
  const [year, month, day] = value.split('-');
  if (!year || !month || !day) return value;
  return `${Number(month)}월 ${Number(day)}일`;
};

const formatDateTimeLabel = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

const sortScheduleItems = (items: DashboardScheduleItem[]) =>
  [...items].sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

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
          <strong>프론트가 메인 화면</strong>
          <p>조회와 이동은 프론트에서 시작하고, 작성/상세/관리는 필요한 때만 Django 화면을 엽니다.</p>
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
        <a className="icon-button" aria-label="영업노트" href="/notes/">
          <Bell size={18} />
        </a>
        <a className="primary-button" href="/notes/?create=1">
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

function DashboardMetricCard({
  detail,
  href,
  icon: Icon,
  label,
  tone,
  value,
}: {
  detail: string;
  href?: string;
  icon: typeof LayoutDashboard;
  label: string;
  tone: 'blue' | 'green' | 'amber' | 'red' | 'teal';
  value: string;
}) {
  const content = (
    <>
      <div className="dashboard-metric-icon">
        <Icon size={19} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </>
  );

  if (href) {
    return (
      <a className={`dashboard-metric-card ${tone}`} href={href}>
        {content}
      </a>
    );
  }

  return <article className={`dashboard-metric-card ${tone}`}>{content}</article>;
}

function DashboardEmpty({ label }: { label: string }) {
  return <div className="dashboard-empty">{label}</div>;
}

function DashboardScheduleList({ items }: { items: DashboardScheduleItem[] }) {
  if (items.length === 0) {
    return <DashboardEmpty label="표시할 일정이 없습니다" />;
  }

  return (
    <div className="dashboard-list">
      {sortScheduleItems(items).map((item) => (
        <a className="dashboard-list-row" href={item.href} key={`${item.type}-${item.id}`}>
          <div className="dashboard-row-icon">
            {item.type === 'personal' ? <Clock size={17} /> : <CalendarDays size={17} />}
          </div>
          <div className="dashboard-row-main">
            <strong>{item.customer}</strong>
            <span>
              {[item.company, item.department, item.activityLabel].filter(Boolean).join(' · ')}
            </span>
            {item.notes ? <small>{item.notes}</small> : null}
          </div>
          <time>
            {formatDateLabel(item.date)}
            {item.time ? ` ${item.time}` : ''}
          </time>
        </a>
      ))}
    </div>
  );
}

function DashboardHistoryList({
  emptyLabel,
  items,
  urgent,
}: {
  emptyLabel: string;
  items: DashboardHistoryItem[];
  urgent?: boolean;
}) {
  if (items.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="dashboard-list">
      {items.map((item) => (
        <a className={`dashboard-list-row ${urgent ? 'urgent' : ''}`} href={item.href} key={item.id}>
          <div className="dashboard-row-icon">
            {urgent ? <AlertTriangle size={17} /> : <FileText size={17} />}
          </div>
          <div className="dashboard-row-main">
            <strong>{item.customer}</strong>
            <span>
              {[item.company, item.actionLabel, item.owner].filter(Boolean).join(' · ')}
            </span>
            <small>{item.nextAction || item.summary || '내용 없음'}</small>
          </div>
          <time>{item.nextActionDate ? formatDateLabel(item.nextActionDate) : formatDateTimeLabel(item.createdAt)}</time>
        </a>
      ))}
    </div>
  );
}

function DashboardCustomerList({ items }: { items: DashboardData['priorityCustomers'] }) {
  if (items.length === 0) {
    return <DashboardEmpty label="표시할 우선 고객이 없습니다" />;
  }

  return (
    <div className="dashboard-customer-list">
      {items.map((item) => (
        <a className={`dashboard-customer-row ${item.overdue ? 'overdue' : ''}`} href={item.href} key={item.id}>
          <div>
            <strong>{item.company || item.customer}</strong>
            <span>
              {[item.customer, item.department, item.owner].filter(Boolean).join(' · ')}
            </span>
            {item.nextAction ? <small>{item.nextAction}</small> : null}
          </div>
          <div className="dashboard-customer-meta">
            <span>{item.priorityLabel}</span>
            <strong>{Math.round(item.score)}</strong>
          </div>
        </a>
      ))}
    </div>
  );
}

function DashboardPipelineSummary({ data }: { data: DashboardData['pipelineSummary'] }) {
  const maxCount = Math.max(...data.map((item) => item.count), 1);
  return (
    <div className="dashboard-pipeline-summary">
      {data.map((item) => (
        <a className="dashboard-pipeline-row" href={`/reporting/followups/?pipeline_stage=${item.stage}`} key={item.stage}>
          <div>
            <span>{item.label}</span>
            <strong>{formatNumber(item.count)}건</strong>
          </div>
          <div className="dashboard-pipeline-bar">
            <div style={{ width: `${(item.count / maxCount) * 100}%` }} />
          </div>
        </a>
      ))}
    </div>
  );
}

function DashboardTeamActivity({ data }: { data: DashboardData['teamActivity'] }) {
  if (data.length === 0) {
    return null;
  }

  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Team</span>
          <h2>팀 활동 현황</h2>
        </div>
        <Users size={18} />
      </div>
      <div className="dashboard-team-grid">
        {data.map((item) => (
          <article className="dashboard-team-row" key={item.userId}>
            <strong>{item.name}</strong>
            <span>최근 30일 {formatNumber(item.recentCount)}건</span>
            <small>지연 {formatNumber(item.overdueCount)}건</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function CustomerStatusBadge({ customer }: { customer: CustomerItem }) {
  return (
    <div className="customer-badge-row">
      <span className={`customer-priority ${customer.priority}`}>{customer.priorityLabel}</span>
      <span>{customer.pipelineLabel}</span>
      {customer.grade ? <span>{customer.grade}</span> : null}
    </div>
  );
}

function CustomersPriorityList({ customers }: { customers: CustomerItem[] }) {
  if (customers.length === 0) {
    return <DashboardEmpty label="우선 고객이 없습니다" />;
  }

  return (
    <div className="customers-priority-list">
      {customers.map((customer) => (
        <a className={`customers-priority-row ${customer.overdue ? 'overdue' : ''}`} href={customer.href} key={customer.id}>
          <div>
            <strong>{customer.company || customer.customer}</strong>
            <span>{[customer.customer, customer.owner].filter(Boolean).join(' · ')}</span>
            {customer.nextAction ? <small>{customer.nextAction}</small> : null}
            {customer.upcomingSchedule ? (
              <small>
                {formatDateLabel(customer.upcomingSchedule.date)} {customer.upcomingSchedule.time} · {customer.upcomingSchedule.activityLabel}
              </small>
            ) : null}
            {customer.overdueActionCount > 0 ? (
              <small className="customer-priority-warning">지연 후속 {formatNumber(customer.overdueActionCount)}건</small>
            ) : null}
          </div>
          <div className="customer-priority-meta">
            <strong className="customer-score">{Math.round(customer.score)}</strong>
            <span>활동 {formatNumber(customer.activityCount)}</span>
          </div>
        </a>
      ))}
    </div>
  );
}

function CustomersTable({ customers }: { customers: CustomerItem[] }) {
  if (customers.length === 0) {
    return <DashboardEmpty label="조건에 맞는 고객이 없습니다" />;
  }

  return (
    <div className="customers-table-wrap">
      <table className="customers-table">
        <thead>
          <tr>
            <th>고객</th>
            <th>상태</th>
            <th>후속</th>
            <th>예정 일정</th>
            <th>활동</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={customer.id}>
              <td>
                <a className="customer-name-link" href={customer.href}>
                  <strong>{customer.company || customer.customer}</strong>
                  <span>{[customer.customer, customer.department].filter(Boolean).join(' · ')}</span>
                  {customer.contactSummary ? <small className="customer-contact-line">{customer.contactSummary}</small> : null}
                  {!customer.contactSummary && customer.notes ? <small className="customer-contact-line">{customer.notes}</small> : null}
                </a>
              </td>
              <td>
                <CustomerStatusBadge customer={customer} />
              </td>
              <td>
                <span className={customer.overdue ? 'customer-overdue-text' : ''}>
                  {customer.nextAction || '다음 액션 없음'}
                </span>
                {customer.nextActionDate ? <small>{formatDateLabel(customer.nextActionDate)}</small> : null}
                {customer.overdueActionCount > 0 ? (
                  <small className="customer-overdue-text">지연 후속 {formatNumber(customer.overdueActionCount)}건</small>
                ) : null}
              </td>
              <td>
                {customer.upcomingSchedule ? (
                  <a className="customer-schedule-link" href={customer.upcomingSchedule.href}>
                    <strong>
                      {formatDateLabel(customer.upcomingSchedule.date)}
                      {customer.upcomingSchedule.time ? ` ${customer.upcomingSchedule.time}` : ''}
                    </strong>
                    <span>
                      {[customer.upcomingSchedule.activityLabel, customer.upcomingSchedule.location].filter(Boolean).join(' · ')}
                    </span>
                  </a>
                ) : (
                  <span className="customer-muted-cell">예정 일정 없음</span>
                )}
              </td>
              <td>
                <div className="customer-count-grid">
                  <span>활동 <strong>{formatNumber(customer.activityCount)}</strong></span>
                  <span>일정 <strong>{formatNumber(customer.scheduleCount)}</strong></span>
                </div>
                <small>{customer.lastActivityLabel || '최근 활동 없음'}</small>
                {customer.lastActivityAt ? <small>{formatDateTimeLabel(customer.lastActivityAt)}</small> : null}
              </td>
              <td>
                <span>{customer.owner}</span>
                <div className="customer-row-actions">
                  <a className="customer-row-action" href={customer.createScheduleHref}>일정</a>
                  {customer.upcomingSchedule ? (
                    <a className="customer-row-action" href={customer.upcomingSchedule.createHistoryHref}>보고</a>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CustomersPage({
  data,
  loading,
  owner,
  priority,
  query,
  stage,
  onOwnerChange,
  onPriorityChange,
  onQueryChange,
  onStageChange,
}: {
  data: CustomersData | null;
  loading: boolean;
  owner: string;
  priority: string;
  query: string;
  stage: string;
  onOwnerChange: (value: string) => void;
  onPriorityChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onStageChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 고객', value: `${formatNumber(data.metrics.totalCustomers)}건`, detail: data.scope.label, icon: Users, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(data.metrics.filteredCustomers)}건`, detail: '현재 필터', icon: Search, tone: 'teal' as const },
    { label: '예정 일정 고객', value: `${formatNumber(data.metrics.scheduledCustomers)}건`, detail: '미래 일정 보유', icon: CalendarDays, tone: 'green' as const },
    { label: '지연 후속', value: `${formatNumber(data.metrics.overdueCustomers)}건`, detail: '다음 액션 경과', icon: AlertTriangle, tone: 'red' as const },
  ];

  return (
    <section className="customers-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>고객 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Customers</span>
          <h2>{data.scope.label || '고객 관리'}</h2>
          <p>검색, 담당자, 우선순위 기준으로 고객과 후속조치를 확인합니다.</p>
        </div>
        <a className="route-primary-action" href={data.links.createCustomer}>
          새 고객 등록
          <Plus size={16} />
        </a>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객 핵심 지표">
        {metrics.map((metric) => (
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

      <div className="customers-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 회사, 연구실, 연락처 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onPriorityChange(event.target.value)} value={priority}>
          <option value="">우선순위 전체</option>
          {data.options.priorities.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onStageChange(event.target.value)} value={stage}>
          <option value="">파이프라인 전체</option>
          {data.options.stages.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="customers-layout">
        <section className="dashboard-panel customers-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customer list</span>
              <h2>고객 목록</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
          </div>
          <CustomersTable customers={data.customers} />
        </section>

        <aside className="dashboard-panel customers-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Priority</span>
              <h2>우선 고객</h2>
            </div>
            <Bell size={18} />
          </div>
          <CustomersPriorityList customers={data.priorityCustomers} />
          <div className="customers-side-actions">
            <a href={data.links.customerReport}>고객 리포트</a>
            <a href={data.links.companies}>고객사 관리</a>
          </div>
        </aside>
      </div>
    </section>
  );
}

function NoteStatusBadge({ note }: { note: NoteItem }) {
  const reviewLabel = note.reviewed ? '검토 완료' : note.reviewRequired ? '미검토' : '검토 불필요';
  return (
    <div className="customer-badge-row notes-badge-row">
      <span className={`note-action ${note.actionType}`}>{note.actionLabel}</span>
      <span className={note.reviewed ? 'note-reviewed' : note.reviewRequired ? 'note-unreviewed' : ''}>
        {reviewLabel}
      </span>
      {note.overdue ? <span className="note-overdue">지연</span> : null}
      {note.serviceStatusLabel ? <span>{note.serviceStatusLabel}</span> : null}
    </div>
  );
}

function NotesActionCounts({ data }: { data: NotesData }) {
  const maxCount = Math.max(...data.actionCounts.map((item) => item.count), 1);
  return (
    <div className="notes-action-counts">
      {data.actionCounts.map((item) => (
        <div className="notes-action-count-row" key={item.value}>
          <div>
            <span>{item.label}</span>
            <strong>{formatNumber(item.count)}건</strong>
          </div>
          <div className="notes-count-bar">
            <div style={{ width: `${(item.count / maxCount) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function NotesTable({
  canReview,
  notes,
  onToggleReview,
  reviewingNoteId,
}: {
  canReview: boolean;
  notes: NoteItem[];
  onToggleReview: (note: NoteItem) => void;
  reviewingNoteId: number | null;
}) {
  if (notes.length === 0) {
    return <DashboardEmpty label="조건에 맞는 영업노트가 없습니다" />;
  }

  return (
    <div className="customers-table-wrap notes-table-wrap">
      <table className="customers-table notes-table">
        <thead>
          <tr>
            <th>영업노트</th>
            <th>다음 액션</th>
            <th>상태</th>
            <th>연결</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {notes.map((note) => (
            <tr key={note.id}>
              <td>
                <a className="customer-name-link" href={note.href}>
                  <strong>{note.company || note.customer}</strong>
                  <span>{[note.customer, note.department, note.actionLabel].filter(Boolean).join(' · ')}</span>
                  {note.summary ? <small>{note.summary}</small> : null}
                  {note.fileCount > 0 || note.replyCount > 0 ? (
                    <div className="note-meta-row">
                      {note.fileCount > 0 ? <span>첨부 {formatNumber(note.fileCount)}</span> : null}
                      {note.replyCount > 0 ? <span>댓글 {formatNumber(note.replyCount)}</span> : null}
                    </div>
                  ) : null}
                </a>
              </td>
              <td>
                <span className={note.overdue ? 'customer-overdue-text' : ''}>
                  {note.nextAction || '다음 액션 없음'}
                </span>
                {note.nextActionDate ? <small>{formatDateLabel(note.nextActionDate)}</small> : null}
              </td>
              <td>
                <NoteStatusBadge note={note} />
                {note.reviewedAt ? (
                  <small>{[note.reviewer, formatDateTimeLabel(note.reviewedAt)].filter(Boolean).join(' · ')}</small>
                ) : null}
              </td>
              <td>
                <div className="notes-row-actions">
                  <a className="customer-row-action" href={note.href}>상세</a>
                  {note.customerHref ? <a className="customer-row-action" href={note.customerHref}>고객</a> : null}
                  {note.scheduleHref ? <a className="customer-row-action" href={note.scheduleHref}>일정</a> : null}
                  {canReview && note.canReview && note.reviewToggleHref ? (
                    <button
                      className="customer-row-action note-review-action"
                      disabled={reviewingNoteId === note.id}
                      onClick={() => onToggleReview(note)}
                      type="button"
                    >
                      {reviewingNoteId === note.id ? <Loader2 className="spin-icon" size={12} /> : <CheckCircle2 size={12} />}
                      {note.reviewed ? '검토 해제' : '검토 완료'}
                    </button>
                  ) : null}
                </div>
              </td>
              <td>
                <span>{note.owner}</span>
                <small>{note.activityDate ? formatDateLabel(note.activityDate) : formatDateTimeLabel(note.createdAt)}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NotesPage({
  actionType,
  createError,
  createForm,
  createMessage,
  createOpen,
  creating,
  data,
  loading,
  nextAction,
  owner,
  query,
  reviewError,
  reviewMessage,
  reviewingNoteId,
  review,
  onActionTypeChange,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onNextActionChange,
  onOwnerChange,
  onQueryChange,
  onReviewChange,
  onToggleReview,
}: {
  actionType: string;
  createError: string;
  createForm: NoteCreateFormState;
  createMessage: string;
  createOpen: boolean;
  creating: boolean;
  data: NotesData | null;
  loading: boolean;
  nextAction: string;
  owner: string;
  query: string;
  reviewError: string;
  reviewMessage: string;
  reviewingNoteId: number | null;
  review: string;
  onActionTypeChange: (value: string) => void;
  onCreateFormChange: (field: keyof NoteCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onNextActionChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onReviewChange: (value: string) => void;
  onToggleReview: (note: NoteItem) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>영업노트 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 노트', value: `${formatNumber(data.metrics.totalNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(data.metrics.filteredNotes)}건`, detail: '현재 필터', icon: Search, tone: 'teal' as const },
    { label: '미검토', value: `${formatNumber(data.metrics.unreviewedNotes)}건`, detail: '검토 필요', icon: CheckCircle2, tone: 'amber' as const },
    { label: '지연 후속', value: `${formatNumber(data.metrics.overdueActions)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: 'red' as const },
    { label: '7일 이내', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '다가오는 액션', icon: Clock, tone: 'green' as const },
  ];
  const createConfig = data.create;
  const canCreateNotes = createConfig.canCreate;
  const createCustomers = createConfig.customers;
  const createActionTypes = createConfig.actionTypes;

  return (
    <section className="notes-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>영업노트 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Notes</span>
          <h2>{data.scope.label || '영업노트'}</h2>
          <p>활동 기록, 검토 상태, 다음 액션을 같은 목록에서 확인합니다.</p>
        </div>
        <button
          className={canCreateNotes ? 'route-primary-action' : 'route-secondary-action'}
          onClick={() => onCreateOpenChange(!createOpen)}
          type="button"
        >
          {canCreateNotes ? '노트 작성' : '작성 권한 없음'}
          <Plus size={16} />
        </button>
      </div>

      <section className="dashboard-metric-grid" aria-label="영업노트 핵심 지표">
        {metrics.map((metric) => (
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

      {createOpen ? (
        <section className="dashboard-panel notes-create-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Quick note</span>
              <h2>영업노트 빠른 작성</h2>
            </div>
            {creating ? <Loader2 className="spin-icon" size={18} /> : <MessageSquareText size={18} />}
          </div>
          {createMessage ? <div className="notes-action-feedback success">{createMessage}</div> : null}
          {createError ? <div className="notes-action-feedback error">{createError}</div> : null}
          {!canCreateNotes ? (
            <DashboardEmpty label={createConfig.message || '작성 권한이 없습니다'} />
          ) : createCustomers.length === 0 ? (
            <DashboardEmpty label="작성 가능한 담당 고객이 없습니다" />
          ) : createActionTypes.length === 0 ? (
            <DashboardEmpty label="작성 가능한 활동 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid">
                <label>
                  <span>고객</span>
                  <select
                    onChange={(event) => onCreateFormChange('followupId', event.target.value)}
                    required
                    value={createForm.followupId}
                  >
                    <option value="">고객 선택</option>
                    {createCustomers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => onCreateFormChange('actionType', event.target.value)}
                    required
                    value={createForm.actionType}
                  >
                    {createActionTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동일</span>
                  <input
                    onChange={(event) => onCreateFormChange('activityDate', event.target.value)}
                    type="date"
                    value={createForm.activityDate}
                  />
                </label>
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => onCreateFormChange('nextActionDate', event.target.value)}
                    type="date"
                    value={createForm.nextActionDate}
                  />
                </label>
              </div>
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => onCreateFormChange('content', event.target.value)}
                  placeholder="방문/통화/견적 진행 내용"
                  required
                  rows={4}
                  value={createForm.content}
                />
              </label>
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => onCreateFormChange('nextAction', event.target.value)}
                  placeholder="후속 연락, 견적 발송, 샘플 준비 등"
                  rows={2}
                  value={createForm.nextAction}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href="/reporting/dashboard/#dashboardNoteModal">
                  상세 작성
                  <MoveUpRight size={15} />
                </a>
                <button className="route-primary-action" disabled={creating} type="submit">
                  {creating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          )}
        </section>
      ) : null}

      <div className="notes-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 회사, 노트 내용, 다음 액션 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onActionTypeChange(event.target.value)} value={actionType}>
          <option value="">활동 유형 전체</option>
          {data.options.actionTypes.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onReviewChange(event.target.value)} value={review}>
          <option value="">검토 상태 전체</option>
          {data.options.reviewStates.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onNextActionChange(event.target.value)} value={nextAction}>
          <option value="">다음 액션 전체</option>
          {data.options.nextActionStates.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="notes-layout">
        <section className="dashboard-panel notes-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Note list</span>
              <h2>영업노트 목록</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <MessageSquareText size={18} />}
          </div>
          {reviewMessage ? <div className="notes-action-feedback success">{reviewMessage}</div> : null}
          {reviewError ? <div className="notes-action-feedback error">{reviewError}</div> : null}
          <NotesTable
            canReview={data.scope.canReview}
            notes={data.notes}
            onToggleReview={onToggleReview}
            reviewingNoteId={reviewingNoteId}
          />
        </section>

        <aside className="dashboard-panel notes-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Activity type</span>
              <h2>유형별 현황</h2>
            </div>
            <Filter size={18} />
          </div>
          <NotesActionCounts data={data} />
          <div className="customers-side-actions">
            <a href={data.links.notes}>Django 영업노트</a>
            <a href={data.links.unreviewed}>미검토 노트</a>
            <a href={data.links.weeklyReports}>주간보고</a>
          </div>
        </aside>
      </div>
    </section>
  );
}

function ScheduleStatusBadge({ schedule }: { schedule: ScheduleItem }) {
  return (
    <div className="customer-badge-row schedules-badge-row">
      <span className={`schedule-status ${schedule.status}`}>{schedule.statusLabel}</span>
      <span>{schedule.activityLabel}</span>
      {schedule.priorityLabel ? <span>{schedule.priorityLabel}</span> : null}
      {schedule.overdue ? <span className="schedule-overdue">지연</span> : null}
    </div>
  );
}

function SchedulesCompactList({
  emptyLabel,
  items,
  urgent,
}: {
  emptyLabel: string;
  items: ScheduleItem[];
  urgent?: boolean;
}) {
  if (items.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="schedules-compact-list">
      {items.map((item) => (
        <a className={`schedules-compact-row ${urgent || item.overdue ? 'urgent' : ''}`} href={item.href} key={`${item.type}-${item.id}`}>
          <div>
            <strong>{item.company || item.title || item.customer}</strong>
            <span>{[item.customer, item.activityLabel, item.owner].filter(Boolean).join(' · ')}</span>
            {item.notes ? <small>{item.notes}</small> : null}
          </div>
          <time>
            {item.date ? formatDateLabel(item.date) : ''}
            {item.time ? ` ${item.time}` : ''}
          </time>
        </a>
      ))}
    </div>
  );
}

function SchedulesCountRows({ data }: { data: SchedulesData }) {
  const maxCount = Math.max(...data.statusCounts.map((item) => item.count), 1);
  return (
    <div className="notes-action-counts">
      {data.statusCounts.map((item) => (
        <div className="notes-action-count-row" key={item.value}>
          <div>
            <span>{item.label}</span>
            <strong>{formatNumber(item.count)}건</strong>
          </div>
          <div className="notes-count-bar">
            <div style={{ width: `${(item.count / maxCount) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function SchedulesTable({ schedules }: { schedules: ScheduleItem[] }) {
  if (schedules.length === 0) {
    return <DashboardEmpty label="조건에 맞는 일정이 없습니다" />;
  }

  return (
    <div className="customers-table-wrap schedules-table-wrap">
      <table className="customers-table schedules-table">
        <thead>
          <tr>
            <th>일정</th>
            <th>일시</th>
            <th>상태</th>
            <th>금액/보고</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {schedules.map((schedule) => (
            <tr key={`${schedule.type}-${schedule.id}`}>
              <td>
                <a className="customer-name-link" href={schedule.href}>
                  <strong>{schedule.company || schedule.title || schedule.customer}</strong>
                  <span>{[schedule.customer, schedule.department, schedule.location].filter(Boolean).join(' · ')}</span>
                  {schedule.notes ? <small>{schedule.notes}</small> : null}
                </a>
              </td>
              <td>
                <span className={schedule.overdue ? 'customer-overdue-text' : ''}>
                  {schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}
                </span>
                {schedule.time ? <small>{schedule.time}</small> : null}
              </td>
              <td>
                <ScheduleStatusBadge schedule={schedule} />
              </td>
              <td>
                {schedule.expectedRevenue > 0 ? <span>{formatWon(schedule.expectedRevenue)}</span> : <span>예상 매출 없음</span>}
                <small>보고 {formatNumber(schedule.historyCount)}건</small>
                <div className="notes-row-actions">
                  {schedule.createHistoryHref ? <a className="customer-row-action" href={schedule.createHistoryHref}>보고</a> : null}
                  {schedule.customerHref ? <a className="customer-row-action" href={schedule.customerHref}>고객</a> : null}
                </div>
              </td>
              <td>
                <span>{schedule.owner}</span>
                <a className="customer-row-action" href={schedule.href}>상세</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SchedulesPage({
  activityType,
  data,
  loading,
  owner,
  query,
  range,
  status,
  onActivityTypeChange,
  onOwnerChange,
  onQueryChange,
  onRangeChange,
  onStatusChange,
}: {
  activityType: string;
  data: SchedulesData | null;
  loading: boolean;
  owner: string;
  query: string;
  range: string;
  status: string;
  onActivityTypeChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRangeChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 일정', value: `${formatNumber(data.metrics.totalSchedules)}건`, detail: data.scope.label, icon: CalendarDays, tone: 'blue' as const },
    { label: '오늘 일정', value: `${formatNumber(data.metrics.todaySchedules)}건`, detail: '금일 업무', icon: Clock, tone: 'green' as const },
    { label: '7일 이내', value: `${formatNumber(data.metrics.weekSchedules)}건`, detail: '다가오는 일정', icon: Bell, tone: 'teal' as const },
    { label: '지연 일정', value: `${formatNumber(data.metrics.overdueSchedules)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: 'red' as const },
    { label: '완료 일정', value: `${formatNumber(data.metrics.completedSchedules)}건`, detail: '고객 일정 기준', icon: CheckCircle2, tone: 'amber' as const },
  ];

  return (
    <section className="schedules-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>일정 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Schedules</span>
          <h2>{data.scope.label || '일정'}</h2>
          <p>고객 일정과 개인 일정을 함께 보고 후속 보고 작성으로 연결합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.createPersonalSchedule}>
            개인 일정
          </a>
          <a className="route-primary-action" href={data.links.createSchedule}>
            일정 등록
            <Plus size={16} />
          </a>
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="일정 핵심 지표">
        {metrics.map((metric) => (
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

      <div className="schedules-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 회사, 장소, 메모 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onActivityTypeChange(event.target.value)} value={activityType}>
          <option value="">활동 유형 전체</option>
          {data.options.activityTypes.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onRangeChange(event.target.value)} value={range}>
          <option value="">기간 전체</option>
          {data.options.ranges.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="schedules-layout">
        <section className="dashboard-panel schedules-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Schedule list</span>
              <h2>일정 목록</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          <SchedulesTable schedules={data.schedules} />
        </section>

        <aside className="dashboard-panel schedules-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Today</span>
              <h2>오늘 일정</h2>
            </div>
            <Clock size={18} />
          </div>
          <SchedulesCompactList emptyLabel="오늘 일정이 없습니다" items={data.today} />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Overdue</span>
              <h2>지연 일정</h2>
            </div>
            <AlertTriangle size={18} />
          </div>
          <SchedulesCompactList emptyLabel="지연 일정이 없습니다" items={data.overdue} urgent />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Status</span>
              <h2>상태별 현황</h2>
            </div>
            <Filter size={18} />
          </div>
          <SchedulesCountRows data={data} />
          <div className="customers-side-actions">
            <a href={data.links.calendar}>일정 캘린더</a>
            <a href={data.links.schedules}>Django 일정 목록</a>
            <a href={data.links.weeklyReports}>주간보고</a>
          </div>
        </aside>
      </div>
    </section>
  );
}

function AIWorkspaceDepartmentList({ departments }: { departments: AIWorkspaceDepartment[] }) {
  if (departments.length === 0) {
    return <DashboardEmpty label="AI 분석 대상 부서가 없습니다" />;
  }

  return (
    <div className="ai-department-list">
      {departments.map((department) => (
        <a className={`ai-department-row ${department.hasAnalysis ? 'ready' : ''}`} href={department.hubHref} key={department.id}>
          <div>
            <strong>{department.company || department.name}</strong>
            <span>{[department.name, `${formatNumber(department.customerCount)}명`].filter(Boolean).join(' · ')}</span>
            {department.summary ? <small>{department.summary}</small> : null}
            {!department.summary && department.customerPreview.length > 0 ? (
              <small>{department.customerPreview.join(', ')}</small>
            ) : null}
          </div>
          <div className="ai-row-meta">
            <span>{department.hasAnalysis ? '분석 완료' : '분석 필요'}</span>
            <strong>{formatNumber(department.unverifiedPainpointCount)}</strong>
          </div>
        </a>
      ))}
    </div>
  );
}

function AIWorkspacePainpointList({ painpoints }: { painpoints: AIWorkspacePainpoint[] }) {
  if (painpoints.length === 0) {
    return <DashboardEmpty label="미검증 PainPoint가 없습니다" />;
  }

  return (
    <div className="ai-painpoint-list">
      {painpoints.map((painpoint) => (
        <a className="ai-painpoint-row" href={painpoint.href} key={painpoint.id}>
          <div>
            <strong>{painpoint.hypothesis}</strong>
            <span>{[painpoint.company, painpoint.department, painpoint.categoryLabel].filter(Boolean).join(' · ')}</span>
            {painpoint.question ? <small>{painpoint.question}</small> : null}
          </div>
          <div className="ai-confidence">
            <span>{painpoint.confidenceLabel}</span>
            <strong>{painpoint.confidenceScore}</strong>
          </div>
        </a>
      ))}
    </div>
  );
}

function AIWorkspaceFollowupTargets({ targets }: { targets: AIWorkspaceFollowupTarget[] }) {
  if (targets.length === 0) {
    return <DashboardEmpty label="AI 고객 분석 대상이 없습니다" />;
  }

  return (
    <div className="ai-followup-grid">
      {targets.map((target) => (
        <article className="ai-followup-card" key={target.id}>
          <div>
            <strong>{target.company || target.customer}</strong>
            <span>{[target.customer, target.department, target.priorityLabel].filter(Boolean).join(' · ')}</span>
            {target.analysisSummary ? <small>{target.analysisSummary}</small> : null}
          </div>
          <div className="ai-followup-card-footer">
            <strong>{Math.round(target.score)}</strong>
            <div>
              <a href={target.href}>{target.hasAnalysis ? '분석 보기' : '분석 시작'}</a>
              <a href={target.customerHref}>고객</a>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function AIWorkspacePromptQueue({
  copiedPromptId,
  onCopyPrompt,
  targets,
}: {
  copiedPromptId: string;
  onCopyPrompt: (target: AIWorkspacePromptTarget) => void;
  targets: AIWorkspacePromptTarget[];
}) {
  if (targets.length === 0) {
    return <DashboardEmpty label="AI 작업 프롬프트 대상이 없습니다" />;
  }

  return (
    <div className="ai-prompt-grid">
      {targets.map((target) => (
        <article className={`ai-prompt-card ${target.type}`} key={target.id}>
          <div className="ai-prompt-card-head">
            <div>
              <span>{target.typeLabel}</span>
              <strong>{target.title}</strong>
              {target.subtitle ? <small>{target.subtitle}</small> : null}
            </div>
            <em>{target.priority}</em>
          </div>
          {target.context.length > 0 ? (
            <div className="ai-prompt-context">
              {target.context.slice(0, 4).map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          ) : null}
          <pre>{target.prompt}</pre>
          <div className="ai-prompt-actions">
            <button onClick={() => onCopyPrompt(target)} type="button">
              {copiedPromptId === target.id ? <Check size={14} /> : <Copy size={14} />}
              {copiedPromptId === target.id ? '복사됨' : '복사'}
            </button>
            <a href={target.href}>열기</a>
          </div>
        </article>
      ))}
    </div>
  );
}

function AIWorkspacePage({ data, loading }: { data: AIWorkspaceData | null; loading: boolean }) {
  const [copiedPromptId, setCopiedPromptId] = useState('');

  const handleCopyPrompt = async (target: AIWorkspacePromptTarget) => {
    try {
      await navigator.clipboard.writeText(target.prompt);
      setCopiedPromptId(target.id);
      window.setTimeout(() => setCopiedPromptId(''), 1600);
    } catch {
      setCopiedPromptId('');
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>AI 업무 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '분석 대상 부서', value: `${formatNumber(data.metrics.departmentsWithCustomers)}개`, detail: data.currentUser.name || '현재 사용자', icon: Building2, tone: 'blue' as const },
    { label: '분석 완료', value: `${formatNumber(data.metrics.analyzedDepartments)}개`, detail: '부서 분석', icon: Sparkles, tone: 'teal' as const },
    { label: '미검증 PainPoint', value: `${formatNumber(data.metrics.unverifiedPainpoints)}건`, detail: '확인 필요', icon: AlertTriangle, tone: 'red' as const },
    { label: '고객 분석', value: `${formatNumber(data.metrics.followupAnalyses)}건`, detail: '개별 고객', icon: Target, tone: 'amber' as const },
    { label: '이번 달 보고', value: `${formatNumber(data.metrics.weeklyReportsThisMonth)}건`, detail: '주간보고', icon: FileText, tone: 'green' as const },
  ];

  return (
    <section className="ai-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>AI workspace API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      {!data.permission.canUseAi ? (
        <div className="dashboard-api-alert ai-permission-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>AI 기능 권한이 없습니다</strong>
            <span>{data.permission.message || '관리자에게 AI 기능 권한을 요청해야 합니다.'}</span>
          </div>
          <a href={data.links.dashboard}>대시보드</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">AI Workspace</span>
          <h2>{data.currentUser.company || 'AI 업무도구'}</h2>
          <p>부서 분석, 고객 분석, PainPoint 검증, 주간보고 초안을 한 흐름에서 확인합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.weeklyReportCreate}>
            주간보고
          </a>
          <a className="route-primary-action" href={data.links.aiHub}>
            AI 허브
            <MoveUpRight size={16} />
          </a>
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="AI 업무 핵심 지표">
        {metrics.map((metric) => (
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

      {data.permission.canUseAi ? (
        <section className="dashboard-panel ai-prompt-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Prompt queue</span>
              <h2>AI 작업 큐</h2>
            </div>
            <Copy size={18} />
          </div>
          <AIWorkspacePromptQueue
            copiedPromptId={copiedPromptId}
            onCopyPrompt={handleCopyPrompt}
            targets={data.promptTargets || []}
          />
        </section>
      ) : null}

      <div className="ai-layout">
        <section className="dashboard-panel ai-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Department analysis</span>
              <h2>부서 분석 대상</h2>
            </div>
            <Sparkles size={18} />
          </div>
          <AIWorkspaceDepartmentList departments={data.departments} />
        </section>

        <aside className="dashboard-panel ai-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Action</span>
              <h2>바로 실행</h2>
            </div>
            <MoveUpRight size={18} />
          </div>
          <div className="ai-tool-list">
            <a href={data.links.aiHub}>
              <Sparkles size={17} />
              <span>부서 분석/프롬프트</span>
            </a>
            <a href={data.links.weeklyAiDraft}>
              <FileText size={17} />
              <span>이번 주 AI 초안</span>
            </a>
            <a href={data.links.customers}>
              <Users size={17} />
              <span>고객 목록</span>
            </a>
            <a href={data.links.notes}>
              <MessageSquareText size={17} />
              <span>영업노트</span>
            </a>
          </div>

          <div className="dashboard-panel-heading ai-side-heading">
            <div>
              <span className="eyebrow">PainPoint</span>
              <h2>검증 대기</h2>
            </div>
            <AlertTriangle size={18} />
          </div>
          <AIWorkspacePainpointList painpoints={data.painpoints} />
        </aside>
      </div>

      <section className="dashboard-panel ai-followup-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Account AI</span>
            <h2>고객 분석 대상</h2>
          </div>
          <Target size={18} />
        </div>
        <AIWorkspaceFollowupTargets targets={data.followupTargets} />
      </section>

      {data.recommendedGoals.length > 0 ? (
        <section className="dashboard-panel ai-goal-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Prompt goals</span>
              <h2>추천 목표</h2>
            </div>
            <CheckCircle2 size={18} />
          </div>
          <div className="ai-goal-grid">
            {data.recommendedGoals.map((goal) => (
              <article className="ai-goal-card" key={goal.title}>
                <strong>{goal.title}</strong>
                <span>{goal.description}</span>
                {goal.reason ? <small>{goal.reason}</small> : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

function DashboardPage({ data, loading }: { data: DashboardData | null; loading: boolean }) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>대시보드 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metricCards = [
    {
      label: '활성 고객',
      value: `${formatNumber(data.metrics.activeCustomers)}건`,
      detail: `전체 ${formatNumber(data.metrics.totalCustomers)}건`,
      icon: Users,
      tone: 'blue' as const,
      href: data.links.customers,
    },
    {
      label: '오늘 일정',
      value: `${formatNumber(data.metrics.todaySchedules)}건`,
      detail: `이번 주 ${formatNumber(data.metrics.weeklySchedules)}건`,
      icon: CalendarDays,
      tone: 'green' as const,
      href: data.links.calendar,
    },
    {
      label: '지연 후속',
      value: `${formatNumber(data.metrics.overdueActions)}건`,
      detail: `오늘 예정 ${formatNumber(data.metrics.dueTodayActions)}건`,
      icon: AlertTriangle,
      tone: 'red' as const,
      href: data.links.notes,
    },
    {
      label: '이번 달 활동',
      value: `${formatNumber(data.metrics.monthlyActivity)}건`,
      detail: data.scope.label || data.currentUser.name || '현재 범위',
      icon: Activity,
      tone: 'teal' as const,
      href: data.links.notes,
    },
    {
      label: '이번 달 매출',
      value: formatWon(data.metrics.monthlyRevenue),
      detail: '납품 일정 기준',
      icon: CircleDollarSign,
      tone: 'amber' as const,
      href: data.links.operationalDashboard,
    },
  ];

  if (data.scope.canViewAll) {
    metricCards.push({
      label: '미검토 노트',
      value: `${formatNumber(data.metrics.pendingReviews)}건`,
      detail: '매니저 검토 대기',
      icon: CheckCircle2,
      tone: 'blue' as const,
      href: data.links.pendingReviews,
    });
  }

  const quickActions = [
    { label: '영업노트 작성', href: data.links.createNote, icon: Plus, primary: true },
    { label: '고객 목록', href: data.links.customers, icon: Users },
    { label: '일정 캘린더', href: data.links.calendar, icon: CalendarDays },
    { label: '운영 대시보드', href: data.links.operationalDashboard, icon: MoveUpRight },
  ];

  return (
    <section className="dashboard-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>대시보드 API에 연결되지 않았습니다</strong>
            <span>{data.error || '로그인 상태나 Django API 응답을 확인해야 합니다.'}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Live dashboard</span>
          <h2>{data.scope.label || '내 영업 현황'}</h2>
          <p>
            {data.currentUser.company ? `${data.currentUser.company} · ` : ''}
            {data.currentUser.roleLabel}
          </p>
        </div>
        <div className={`source-badge ${data.source === 'django' ? 'django' : 'mock'}`}>
          {data.source === 'django' ? 'Django API 연결됨' : '연결 필요'}
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="대시보드 핵심 지표">
        {metricCards.map((metric) => (
          <DashboardMetricCard
            detail={metric.detail}
            href={metric.href}
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      <div className="dashboard-action-strip">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <a className={action.primary ? 'primary' : ''} href={action.href} key={action.label}>
              <Icon size={17} />
              {action.label}
            </a>
          );
        })}
      </div>

      <div className="dashboard-layout">
        <section className="dashboard-panel dashboard-panel-large">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Today</span>
              <h2>오늘 일정</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          <DashboardScheduleList items={data.today.items} />
        </section>

        <section className="dashboard-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Follow-up</span>
              <h2>지연 후속조치</h2>
            </div>
            <Bell size={18} />
          </div>
          <DashboardHistoryList emptyLabel="지연된 후속조치가 없습니다" items={data.overdueActions} urgent />
        </section>

        <section className="dashboard-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customers</span>
              <h2>우선 고객</h2>
            </div>
            <Building2 size={18} />
          </div>
          <DashboardCustomerList items={data.priorityCustomers} />
        </section>

        <section className="dashboard-panel dashboard-panel-large">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Recent notes</span>
              <h2>최근 영업노트</h2>
            </div>
            <FileText size={18} />
          </div>
          <DashboardHistoryList emptyLabel="최근 영업노트가 없습니다" items={data.recentActivities} />
        </section>

        <section className="dashboard-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">This week</span>
              <h2>이번 주 예정</h2>
            </div>
            <Clock size={18} />
          </div>
          <DashboardScheduleList items={data.upcomingSchedules} />
        </section>

        <section className="dashboard-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Pipeline</span>
              <h2>파이프라인 현황</h2>
            </div>
            <Target size={18} />
          </div>
          <DashboardPipelineSummary data={data.pipelineSummary} />
        </section>
      </div>

      <DashboardTeamActivity data={data.teamActivity} />
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
      {deal.quoteComparison ? (
        <div className={`quote-delta ${deal.quoteComparison.status}`}>
          <span>견적 대비</span>
          <strong>
            {formatSignedWon(deal.quoteComparison.deltaAmount)}
            <small>{formatSignedPercent(deal.quoteComparison.deltaRate)}</small>
          </strong>
        </div>
      ) : null}
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
            <th>대표 금액</th>
            <th>견적 대비</th>
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
              <td>
                {deal.quoteComparison ? (
                  <>
                    <strong>{formatSignedWon(deal.quoteComparison.deltaAmount)}</strong>
                    <span>{deal.quoteComparison.statusLabel}</span>
                  </>
                ) : (
                  '-'
                )}
              </td>
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
        <span>{deal.latestQuote?.basisType === 'delivery' ? '실제 납품 매출' : '예상 매출'}</span>
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
          <div className="section-title">{deal.latestQuote.source || '가격 기준 견적'}</div>
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
      {deal.quoteComparison ? (
        <div className={`detail-box quote-comparison ${deal.quoteComparison.status}`}>
          <div className="section-title">견적 대비 실제 납품</div>
          <div className="comparison-grid">
            <span>기준 견적</span>
            <strong>{formatWon(deal.quoteComparison.quotedAmount)}</strong>
            <span>실제 납품</span>
            <strong>{formatWon(deal.quoteComparison.actualAmount)}</strong>
          </div>
          <div className="comparison-delta">
            <span>{deal.quoteComparison.statusLabel}</span>
            <strong>{formatSignedWon(deal.quoteComparison.deltaAmount)}</strong>
            <small>{formatSignedPercent(deal.quoteComparison.deltaRate)}</small>
          </div>
          <small>
            {deal.quoteComparison.source}
            {deal.quoteComparison.number ? ` · ${deal.quoteComparison.number}` : ''}
          </small>
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
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(currentView === 'dashboard');
  const [customersData, setCustomersData] = useState<CustomersData | null>(null);
  const [customersLoading, setCustomersLoading] = useState(currentView === 'customers');
  const [customerQuery, setCustomerQuery] = useState('');
  const [customerOwner, setCustomerOwner] = useState('');
  const [customerPriority, setCustomerPriority] = useState('');
  const [customerStage, setCustomerStage] = useState('');
  const [notesData, setNotesData] = useState<NotesData | null>(null);
  const [notesLoading, setNotesLoading] = useState(currentView === 'notes');
  const [noteQuery, setNoteQuery] = useState('');
  const [noteOwner, setNoteOwner] = useState('');
  const [noteActionType, setNoteActionType] = useState('');
  const [noteReview, setNoteReview] = useState('');
  const [noteNextAction, setNoteNextAction] = useState('');
  const [noteReviewingId, setNoteReviewingId] = useState<number | null>(null);
  const [noteReviewError, setNoteReviewError] = useState('');
  const [noteReviewMessage, setNoteReviewMessage] = useState('');
  const [noteCreateOpen, setNoteCreateOpen] = useState(currentView === 'notes' && shouldOpenCreateNote());
  const [noteCreateForm, setNoteCreateForm] = useState<NoteCreateFormState>(() => makeEmptyNoteCreateForm());
  const [noteCreating, setNoteCreating] = useState(false);
  const [noteCreateError, setNoteCreateError] = useState('');
  const [noteCreateMessage, setNoteCreateMessage] = useState('');
  const [schedulesData, setSchedulesData] = useState<SchedulesData | null>(null);
  const [schedulesLoading, setSchedulesLoading] = useState(currentView === 'schedules');
  const [scheduleQuery, setScheduleQuery] = useState('');
  const [scheduleOwner, setScheduleOwner] = useState('');
  const [scheduleStatus, setScheduleStatus] = useState('');
  const [scheduleActivityType, setScheduleActivityType] = useState('');
  const [scheduleRange, setScheduleRange] = useState('');
  const [aiWorkspaceData, setAiWorkspaceData] = useState<AIWorkspaceData | null>(null);
  const [aiWorkspaceLoading, setAiWorkspaceLoading] = useState(currentView === 'ai');
  const [selectedDealId, setSelectedDealId] = useState<number | null>(mockPipelineData.deals[0]?.id ?? null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<SavedView>('priority');
  const [movingDealId, setMovingDealId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState('');
  const [moveMessage, setMoveMessage] = useState('');

  useEffect(() => {
    if (currentView === 'schedules') {
      window.location.replace(scheduleCalendarUrl);
    }
  }, [currentView]);

  useEffect(() => {
    if (currentView === 'dashboard') {
      return;
    }
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
  }, [currentView]);

  useEffect(() => {
    if (currentView !== 'dashboard') {
      return;
    }
    let alive = true;
    setDashboardLoading(true);
    loadDashboardData().then((data) => {
      if (!alive) {
        return;
      }
      setDashboardData(data);
      setDashboardLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView]);

  useEffect(() => {
    if (currentView !== 'customers') {
      return;
    }
    let alive = true;
    setCustomersLoading(true);
    loadCustomersData({
      q: customerQuery,
      owner: customerOwner,
      priority: customerPriority,
      stage: customerStage,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setCustomersData(data);
      setCustomersLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, customerOwner, customerPriority, customerQuery, customerStage]);

  useEffect(() => {
    if (currentView !== 'notes') {
      return;
    }
    let alive = true;
    setNotesLoading(true);
    setNoteReviewError('');
    setNoteReviewMessage('');
    setNoteCreateError('');
    loadNotesData({
      q: noteQuery,
      owner: noteOwner,
      actionType: noteActionType,
      review: noteReview,
      nextAction: noteNextAction,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setNotesData(data);
      setNotesLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, noteActionType, noteNextAction, noteOwner, noteQuery, noteReview]);

  useEffect(() => {
    if (currentView !== 'notes' || !notesData?.create.canCreate) {
      return;
    }
    const firstCustomerId = notesData.create.customers[0]?.id;
    const firstActionType = notesData.create.actionTypes[0]?.value || 'customer_meeting';
    setNoteCreateForm((previous) => ({
      ...previous,
      actionType: previous.actionType || firstActionType,
      followupId: previous.followupId || (firstCustomerId ? String(firstCustomerId) : ''),
    }));
  }, [currentView, notesData]);

  useEffect(() => {
    if (currentView !== 'schedules') {
      return;
    }
    setSchedulesLoading(false);
  }, [currentView]);

  useEffect(() => {
    if (currentView !== 'ai') {
      return;
    }
    let alive = true;
    setAiWorkspaceLoading(true);
    loadAIWorkspaceData().then((data) => {
      if (!alive) {
        return;
      }
      setAiWorkspaceData(data);
      setAiWorkspaceLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView]);

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
  const refreshNotesData = async () => {
    const data = await loadNotesData({
      q: noteQuery,
      owner: noteOwner,
      actionType: noteActionType,
      review: noteReview,
      nextAction: noteNextAction,
    });
    setNotesData(data);
  };
  const handleToggleNoteReview = async (note: NoteItem) => {
    if (!note.reviewToggleHref || noteReviewingId) {
      return;
    }
    setNoteReviewingId(note.id);
    setNoteReviewError('');
    setNoteReviewMessage('');
    try {
      await toggleNoteReviewed(note.reviewToggleHref);
      await refreshNotesData();
      setNoteReviewMessage(note.reviewed ? '검토 상태를 해제했습니다.' : '검토 완료로 처리했습니다.');
    } catch (error) {
      setNoteReviewError(error instanceof Error ? error.message : '검토 상태 변경에 실패했습니다.');
    } finally {
      setNoteReviewingId(null);
    }
  };
  const handleNoteCreateOpenChange = (open: boolean) => {
    setNoteCreateOpen(open);
    setNoteCreateError('');
    if (open) {
      setNoteCreateMessage('');
    }
  };
  const handleNoteCreateFormChange = (field: keyof NoteCreateFormState, value: string) => {
    setNoteCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setNoteCreateError('');
  };
  const resetNoteCreateForm = (data: NotesData | null) => {
    const nextForm = makeEmptyNoteCreateForm();
    nextForm.actionType = data?.create.actionTypes[0]?.value || nextForm.actionType;
    nextForm.followupId = data?.create.customers[0]?.id ? String(data.create.customers[0].id) : '';
    setNoteCreateForm(nextForm);
  };
  const handleCreateNoteSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!notesData || noteCreating) {
      return;
    }
    if (!notesData.create.canCreate) {
      setNoteCreateError(notesData.create.message || '작성 권한이 없습니다.');
      return;
    }
    const followupId = Number(noteCreateForm.followupId);
    if (!followupId) {
      setNoteCreateError('고객을 선택하세요.');
      return;
    }
    if (!noteCreateForm.actionType) {
      setNoteCreateError('활동 유형을 선택하세요.');
      return;
    }
    if (!noteCreateForm.content.trim()) {
      setNoteCreateError('활동 내용을 입력하세요.');
      return;
    }

    const payload: NoteCreatePayload = {
      actionType: noteCreateForm.actionType,
      activityDate: noteCreateForm.activityDate || undefined,
      content: noteCreateForm.content.trim(),
      followupId,
      nextAction: noteCreateForm.nextAction.trim() || undefined,
      nextActionDate: noteCreateForm.nextActionDate || undefined,
    };

    setNoteCreating(true);
    setNoteCreateError('');
    setNoteCreateMessage('');
    try {
      await createSalesNote(payload, notesData.create.submitUrl);
      const refreshedData = await loadNotesData({
        q: noteQuery,
        owner: noteOwner,
        actionType: noteActionType,
        review: noteReview,
        nextAction: noteNextAction,
      });
      setNotesData(refreshedData);
      resetNoteCreateForm(refreshedData);
      setNoteCreateMessage('영업노트를 저장했습니다.');
    } catch (error) {
      setNoteCreateError(error instanceof Error ? error.message : '영업노트 저장에 실패했습니다.');
    } finally {
      setNoteCreating(false);
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

  if (currentView === 'dashboard') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <DashboardPage data={dashboardData} loading={dashboardLoading} />
      </AppShell>
    );
  }

  if (currentView === 'customers') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <CustomersPage
          data={customersData}
          loading={customersLoading}
          owner={customerOwner}
          priority={customerPriority}
          query={customerQuery}
          stage={customerStage}
          onOwnerChange={setCustomerOwner}
          onPriorityChange={setCustomerPriority}
          onQueryChange={setCustomerQuery}
          onStageChange={setCustomerStage}
        />
      </AppShell>
    );
  }

  if (currentView === 'notes') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <NotesPage
          actionType={noteActionType}
          createError={noteCreateError}
          createForm={noteCreateForm}
          createMessage={noteCreateMessage}
          createOpen={noteCreateOpen}
          creating={noteCreating}
          data={notesData}
          loading={notesLoading}
          nextAction={noteNextAction}
          owner={noteOwner}
          query={noteQuery}
          reviewError={noteReviewError}
          reviewMessage={noteReviewMessage}
          reviewingNoteId={noteReviewingId}
          review={noteReview}
          onActionTypeChange={setNoteActionType}
          onCreateFormChange={handleNoteCreateFormChange}
          onCreateOpenChange={handleNoteCreateOpenChange}
          onCreateSubmit={handleCreateNoteSubmit}
          onNextActionChange={setNoteNextAction}
          onOwnerChange={setNoteOwner}
          onQueryChange={setNoteQuery}
          onReviewChange={setNoteReview}
          onToggleReview={handleToggleNoteReview}
        />
      </AppShell>
    );
  }

  if (currentView === 'schedules') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <section className="dashboard-loading">
          <Loader2 className="spin-icon" size={24} />
          <span>일정 캘린더로 이동 중입니다</span>
        </section>
      </AppShell>
    );
  }

  if (currentView === 'ai') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <AIWorkspacePage data={aiWorkspaceData} loading={aiWorkspaceLoading} />
      </AppShell>
    );
  }

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
