import {
  Activity,
  AlertTriangle,
  Archive,
  Bell,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  Columns3,
  FileSpreadsheet,
  FileText,
  ImagePlus,
  LayoutDashboard,
  ListChecks,
  Loader2,
  LogOut,
  Mail,
  MoveUpRight,
  Plus,
  Sparkles,
  Target,
  Users,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { type ReactNode, useEffect, useState } from 'react';
import {
  type DashboardData,
  type DashboardHistoryItem,
  type DashboardScheduleItem,
  type NavigationData,
  type NavigationItem,
  loadDashboardData,
  loadNavigationData,
} from './api/dashboard';
import { formatDateLabel, formatDateTimeLabel, formatNumber, formatWon } from './components/shared/formatters';

type MainView = 'dashboard' | 'analytics' | 'customers' | 'assets' | 'services' | 'pipeline' | 'notes' | 'schedules' | 'tasks' | 'mail' | 'businessCards' | 'weeklyReports' | 'documents' | 'products' | 'prepayments' | 'profile' | 'ai';

const navItems = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'analytics', label: '현황', icon: Activity, href: '/reports/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'assets', label: '장비', icon: Wrench, href: '/assets/' },
  { id: 'services', label: '서비스', icon: Wrench, href: '/services/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/pipeline/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/calendar/' },
  { id: 'tasks', label: '업무', icon: CheckCircle2, href: '/tasks/' },
  { id: 'mail', label: '메일', icon: Mail, href: '/mailbox/' },
  { id: 'businessCards', label: '명함', icon: ImagePlus, href: '/mailbox/business-cards/' },
  { id: 'weeklyReports', label: '주간보고', icon: ListChecks, href: '/weekly-reports/' },
  { id: 'documents', label: '서류', icon: FileSpreadsheet, href: '/documents/' },
  { id: 'products', label: '제품', icon: Archive, href: '/products/' },
  { id: 'prepayments', label: '선결제', icon: CircleDollarSign, href: '/prepayments/' },
  { id: 'profile', label: '프로필', icon: Users, href: '/profile/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

const navIconMap: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  analytics: Activity,
  customers: Users,
  assets: Wrench,
  services: Wrench,
  pipeline: Columns3,
  notes: FileText,
  schedules: CalendarDays,
  tasks: CheckCircle2,
  tasksManager: Users,
  mail: Mail,
  businessCards: ImagePlus,
  weeklyReports: ListChecks,
  documents: FileSpreadsheet,
  products: Archive,
  prepayments: CircleDollarSign,
  profile: Users,
  ai: Sparkles,
};

const routeMeta: Record<MainView, { eyebrow: string; title: string }> = {
  dashboard: { eyebrow: 'Sales CRM / Dashboard', title: '대시보드' },
  analytics: { eyebrow: 'Sales CRM / Reports', title: '현황' },
  customers: { eyebrow: 'Sales CRM / Customers', title: '고객' },
  assets: { eyebrow: 'Sales CRM / Assets', title: '장비' },
  services: { eyebrow: 'Sales CRM / Service', title: '서비스' },
  pipeline: { eyebrow: 'Sales CRM / Pipeline', title: '파이프라인' },
  notes: { eyebrow: 'Sales CRM / Notes', title: '영업노트' },
  schedules: { eyebrow: 'Sales CRM / Schedule', title: '일정' },
  tasks: { eyebrow: 'Sales CRM / Tasks', title: '업무' },
  mail: { eyebrow: 'Sales CRM / Mail', title: '메일' },
  businessCards: { eyebrow: 'Sales CRM / Signature', title: '명함' },
  weeklyReports: { eyebrow: 'Sales CRM / Weekly', title: '주간보고' },
  documents: { eyebrow: 'Sales CRM / Documents', title: '서류' },
  products: { eyebrow: 'Sales CRM / Products', title: '제품' },
  prepayments: { eyebrow: 'Sales CRM / Prepayment', title: '선결제' },
  profile: { eyebrow: 'Sales CRM / Profile', title: '프로필' },
  ai: { eyebrow: 'Sales CRM / AI', title: 'AI 업무도구' },
};

function readCookie(name: string): string {
  const cookie = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`));
  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : '';
}

async function handleLogout() {
  const csrfToken = readCookie('csrftoken');
  try {
    await fetch('/reporting/logout/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
    });
  } catch (error) {
    console.error('Logout request failed', error);
  } finally {
    window.location.href = '/reporting/login/';
  }
}

const sortScheduleItems = (items: DashboardScheduleItem[]) =>
  [...items].sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

function AppShell({ activeView, children }: { activeView: MainView; children: ReactNode }) {
  const [navigation, setNavigation] = useState<NavigationData | null>(null);

  useEffect(() => {
    let mounted = true;
    loadNavigationData().then((data) => {
      if (mounted) setNavigation(data);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const dynamicItems = navigation?.items?.length ? navigation.items : null;
  const items: Array<NavigationItem & { icon?: LucideIcon }> = dynamicItems
    ? dynamicItems.map((item) => ({ ...item, icon: navIconMap[item.id] || LayoutDashboard }))
    : navItems;
  const pathname = window.location.pathname;
  const isActiveNavItem = (item: NavigationItem) => {
    if (activeView !== 'tasks') return item.id === activeView;
    if (pathname.startsWith('/tasks/manager/')) return item.id === 'tasksManager';
    return item.id === 'tasks';
  };

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
          {items.map((item) => {
            const Icon = item.icon || navIconMap[item.id] || LayoutDashboard;
            return (
              <a className={`nav-item ${isActiveNavItem(item) ? 'active' : ''}`} href={item.href} key={`${item.id}-${item.href}`}>
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

function TopBar({ activeView }: { activeView: MainView }) {
  const meta = routeMeta[activeView];
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">{meta.eyebrow}</div>
        <h1>{meta.title}</h1>
      </div>
      <div className="topbar-actions">
        <a className="icon-button" aria-label="영업노트" href="/notes/">
          <Bell size={18} />
        </a>
        <a className="primary-button" href="/notes/?create=1">
          <Plus size={17} />
          새 영업노트
        </a>
        <button className="logout-button" onClick={handleLogout} type="button">
          <LogOut size={17} />
          로그아웃
        </button>
      </div>
    </header>
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
  icon: LucideIcon;
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
        <a className="dashboard-pipeline-row" href="/pipeline/" key={item.stage}>
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

  const revenueYear = data.revenuePeriod.year || new Date().getFullYear();
  const revenueQuarter = data.revenuePeriod.quarter || Math.floor(new Date().getMonth() / 3) + 1;
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
      label: '당해년도 전체 매출',
      value: formatWon(data.metrics.yearRevenue),
      detail: `${revenueYear}년 납품 일정 기준`,
      icon: CircleDollarSign,
      tone: 'amber' as const,
      href: data.links.schedules,
    },
    {
      label: '현재 분기 매출',
      value: formatWon(data.metrics.quarterRevenue),
      detail: `${revenueYear}년 ${revenueQuarter}분기`,
      icon: Target,
      tone: 'green' as const,
      href: data.links.schedules,
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
      href: data.links.schedules,
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
    { label: '파이프라인', href: data.links.pipeline, icon: MoveUpRight },
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

export function DashboardApp() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);

  useEffect(() => {
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
  }, []);

  return (
    <AppShell activeView="dashboard">
      <TopBar activeView="dashboard" />
      <DashboardPage data={dashboardData} loading={dashboardLoading} />
    </AppShell>
  );
}
