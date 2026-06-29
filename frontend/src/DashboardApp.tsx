import {
  Activity,
  AlertTriangle,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  FileText,
  MoveUpRight,
  Plus,
  Target,
  Users,
  type LucideIcon,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  type DashboardData,
  type DashboardHistoryItem,
  type DashboardScheduleItem,
  loadDashboardData,
} from './api/dashboard';
import { AppShell, TopBar, type MainView } from './components/shared/CrmShell';
import { DashboardApiAlert, DashboardEmpty, DashboardLoading } from './components/shared/FeedbackStates';
import { formatDateLabel, formatDateTimeLabel, formatNumber, formatWon } from './components/shared/formatters';

const sortScheduleItems = (items: DashboardScheduleItem[]) =>
  [...items].sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

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
    return <DashboardLoading label="대시보드 데이터를 불러오는 중입니다" />;
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
      detail: `${revenueYear}년 납품·선결제 기준`,
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
      detail: '납품·선결제 기준',
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
        <DashboardApiAlert
          title="대시보드 API에 연결되지 않았습니다"
          message={data.error || '로그인 상태나 Django API 응답을 확인해야 합니다.'}
        />
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
