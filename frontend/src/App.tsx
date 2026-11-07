import {
    ArrowRightLeft,
    CalendarDays,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    CircleDollarSign,
    Columns3,
    Copy,
    FileText,
    Filter,
    LayoutDashboard,
    ListChecks,
    Loader2,
    MessageSquareText,
    MoveUpRight,
    PanelRight,
    PanelRightClose,
    PanelRightOpen,
    Pencil,
    Target,
    Trash2
} from 'lucide-react';
import { useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
    changeProfilePassword,
    createSchedule as createCustomerSchedule,
    createDemoRecord,
    createNote as createSalesNote,
    deleteDemoRecord,
    DemoRecordItem,
    DemoRecordPayload,
    DemoRecordsData,
    DocumentTemplatesData,
    duplicateDealCard,
    EmployeesData,
    hideDealCard,
    loadDemoRecordsData,
    loadDocumentTemplatesData,
    loadEmployeesData,
    loadNoteDetailData,
    loadNotesData,
    loadPipelineData,
    loadProductManagementData,
    loadProfileData,
    loadScheduleCalendarData,
    loadScheduleDetailData,
    loadSchedulesData,
    moveDealStage,
    NoteCreatePayload,
    NoteDetailData,
    NoteItem,
    NotesData,
    ProductManagementData,
    ProfileData,
    ProfilePasswordPayload,
    ProfileUpdatePayload,
    ScheduleCalendarData,
    ScheduleCreatePayload,
    ScheduleDetailData,
    ScheduleItem,
    SchedulesData,
    toggleNoteReviewed,
    unhideDealCard,
    updateDealProbability,
    updateDemoRecord,
    updateProfile,
    updateScheduleStatus
} from './api';
import type {
    CustomerDetailData,
    CustomerRowMode,
    CustomersData
} from './api/accounts';
import {
    loadAccountDetailData,
    loadCustomerDetailData,
    loadCustomersData
} from './api/accounts';
import type {
    PrepaymentCreateData,
    PrepaymentCustomerData,
    PrepaymentDetailData,
    PrepaymentsData
} from './api/prepayments';
import {
    loadPrepaymentAccountData,
    loadPrepaymentCreateData,
    loadPrepaymentCustomerData,
    loadPrepaymentDetailData,
    loadPrepaymentsData
} from './api/prepayments';
import { AppShell, TopBar, type MainView } from './components/shared/CrmShell';
import {
    formatDateLabel,
    formatNumber,
    formatSignedWon,
    formatWon
} from './components/shared/formatters';
import { CRM_CLIENT_NAVIGATION_EVENT } from './navigationEvents';
import { lazyPage, LazyPageBoundary } from './pages/lazyPage';
import {
    CompanyManagementPage,
    PipelineSheetPage,
    ReceivablesPage,
    RevenueDetailPage,
} from './pages/lazyPages';
import { customersForDepartment, DemoRecordFormState, getCreateDateParam, getScheduleCalendarRange, isNoteActionAllowed, isQuoteProbabilityRequired, localDateInputValue, makeEmptyScheduleCreateForm, normalizeProbabilityInputValue, NoteCreateFormState, ProductSortField, ProductSortOrder, ProfileFormState, ProfilePasswordFormState, riskLabel, routeMeta, ScheduleCreateFormState, shouldOpenCreatePanel, WorkspaceRoutePage } from './pages/shared/appShared';
import { emptyPipelineData, type Deal, type HiddenDeal, type PipelineData, type PipelineStage, type PriorityTask, type StageSummary } from './pipelineTypes';
// 화면별 코드는 그 화면을 열 때만 내려받는다(pages/*). 공용 조각은 pages/shared/appShared.
const CustomersPage = lazyPage(() => import('./pages/customers/CustomerPages').then((module) => module.CustomersPage));
const NotesPage = lazyPage(() => import('./pages/notes/NotePages').then((module) => module.NotesPage));
const NoteDetailPage = lazyPage(() => import('./pages/notes/NotePages').then((module) => module.NoteDetailPage));
const SchedulesPage = lazyPage(() => import('./pages/schedules/SchedulePages').then((module) => module.SchedulesPage));
const ScheduleCalendarPage = lazyPage(() => import('./pages/schedules/SchedulePages').then((module) => module.ScheduleCalendarPage));
const ScheduleDetailPage = lazyPage(() => import('./pages/schedules/SchedulePages').then((module) => module.ScheduleDetailPage));
const PrepaymentsPage = lazyPage(() => import('./pages/prepayments/PrepaymentPages').then((module) => module.PrepaymentsPage));
const PrepaymentCustomerPage = lazyPage(() => import('./pages/prepayments/PrepaymentPages').then((module) => module.PrepaymentCustomerPage));
const PrepaymentCreatePage = lazyPage(() => import('./pages/prepayments/PrepaymentPages').then((module) => module.PrepaymentCreatePage));
const PrepaymentDetailPage = lazyPage(() => import('./pages/prepayments/PrepaymentPages').then((module) => module.PrepaymentDetailPage));
const DemoManagementPage = lazyPage(() => import('./pages/demos/DemoManagementPage').then((module) => module.DemoManagementPage));
const ProfileSettingsPage = lazyPage(() => import('./pages/profile/ProfileSettingsPage').then((module) => module.ProfileSettingsPage));
const EmployeesPage = lazyPage(() => import('./pages/employees/EmployeesPage').then((module) => module.EmployeesPage));
const DocumentsPage = lazyPage(() => import('./pages/documents/DocumentsPage').then((module) => module.DocumentsPage));
const ProductManagementPage = lazyPage(() => import('./pages/products/ProductManagementPage').then((module) => module.ProductManagementPage));
type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';
const shiftLocalDateByMonths = (date: Date, offset: number) => {
  const shifted = new Date(date);
  const day = shifted.getDate();
  shifted.setDate(1);
  shifted.setMonth(shifted.getMonth() + offset);
  const lastDay = new Date(shifted.getFullYear(), shifted.getMonth() + 1, 0).getDate();
  shifted.setDate(Math.min(day, lastDay));
  return shifted;
};

const defaultNotesDateFrom = () => localDateInputValue(shiftLocalDateByMonths(new Date(), -1));
const defaultNotesDateTo = () => localDateInputValue();

const getScheduleCalendarMonthParam = () => {
  const month = new URLSearchParams(window.location.search).get('month') || '';
  return /^\d{4}-\d{2}$/.test(month) ? month : localDateInputValue().slice(0, 7);
};
const getScheduleCalendarDataFilterParam = () => {
  const value = new URLSearchParams(window.location.search).get('data_filter') || '';
  return value === 'all' || value === 'user' ? value : 'me';
};
const getNoteReviewParam = () => {
  const value = new URLSearchParams(window.location.search).get('review') ||
    new URLSearchParams(window.location.search).get('review_filter') ||
    '';
  return value === 'unreviewed' || value === 'reviewed' ? value : '';
};
const makeEmptyNoteCreateForm = (): NoteCreateFormState => ({
  actionType: 'customer_meeting',
  activityDate: localDateInputValue(),
  content: '',
  departmentId: '',
  followupId: '',
  nextAction: '',
  nextActionDate: '',
  scheduleId: '',
});
const makeProfileForm = (data?: ProfileData | null): ProfileFormState => ({
  username: data?.user.username || '',
  firstName: data?.user.firstName || '',
  lastName: data?.user.lastName || '',
  email: data?.user.email || '',
});

const makeEmptyProfilePasswordForm = (): ProfilePasswordFormState => ({
  oldPassword: '',
  newPassword1: '',
  newPassword2: '',
});
const makeDemoRecordForm = (record?: DemoRecordItem | null, defaults: Partial<DemoRecordFormState> = {}): DemoRecordFormState => ({
  departmentId: defaults.departmentId ?? (record?.departmentId ? String(record.departmentId) : ''),
  customerId: defaults.customerId ?? (record?.customerId ? String(record.customerId) : ''),
  productId: defaults.productId ?? (record?.productId ? String(record.productId) : ''),
  productName: defaults.productName ?? (record?.productId ? '' : record?.productName ?? ''),
  serialNumber: defaults.serialNumber ?? (record?.serialNumber ?? ''),
  quantity: defaults.quantity ?? String(record?.quantity || 1),
  status: defaults.status ?? (record?.status || 'active'),
  startDate: defaults.startDate ?? (record?.startDate || localDateInputValue()),
  expectedReturnDate: defaults.expectedReturnDate ?? (record?.expectedReturnDate || ''),
  returnedDate: defaults.returnedDate ?? (record?.returnedDate || ''),
  ownerId: defaults.ownerId ?? (record?.ownerId ? String(record.ownerId) : ''),
  notes: defaults.notes ?? (record?.notes ?? ''),
});

const demoRecordFormToPayload = (form: DemoRecordFormState): { payload?: DemoRecordPayload; error?: string } => {
  const departmentId = Number(form.departmentId);
  if (!departmentId) {
    return { error: '부서/연구실 계정을 선택하세요.' };
  }
  const productId = Number(form.productId);
  const productName = form.productName.trim();
  if (!productId) {
    return { error: '제품을 선택하세요.' };
  }
  const quantity = Number(form.quantity);
  if (!Number.isFinite(quantity) || quantity < 1) {
    return { error: '수량은 1 이상으로 입력하세요.' };
  }
  if (!form.status) {
    return { error: '데모 상태를 선택하세요.' };
  }
  return {
    payload: {
      departmentId,
      customerId: form.customerId ? Number(form.customerId) : null,
      productId: productId || null,
      productName: productName || undefined,
      serialNumber: form.serialNumber.trim() || undefined,
      quantity,
      status: form.status,
      startDate: form.startDate || undefined,
      expectedReturnDate: form.expectedReturnDate || undefined,
      returnedDate: form.returnedDate || undefined,
      ownerId: form.ownerId ? Number(form.ownerId) : null,
      notes: form.notes.trim() || undefined,
    },
  };
};

function getCurrentView(): MainView {
  const pathname = window.location.pathname.replace(/\/+$/, '/') || '/';
  if (pathname.startsWith('/dashboard/')) return 'dashboard';
  if (pathname.startsWith('/data-cleanup/') || pathname.startsWith('/downloads/')) return 'notFound';
  if (/^\/accounts\/\d+\/cleanup-preview\/$/.test(pathname)) return 'notFound';
  if (pathname.startsWith('/companies/')) return 'companies';
  if (pathname.startsWith('/accounts/')) return 'customers';
  if (pathname.startsWith('/customers/')) return 'customers';
  if (pathname.startsWith('/demos/')) return 'demos';
  if (pathname.startsWith('/notes/')) return 'notes';
  if (pathname.startsWith('/schedules/')) return 'schedules';
  if (pathname.startsWith('/employees/')) return 'employees';
  if (pathname.startsWith('/documents/')) return 'documents';
  if (pathname.startsWith('/products/')) return 'products';
  if (pathname.startsWith('/receivables/')) return 'receivables';
  if (pathname.startsWith('/prepayments/')) return 'prepayments';
  if (pathname.startsWith('/profile/')) return 'profile';
  if (pathname.startsWith('/pipeline-sheet/')) return 'pipelineSheet';
  if (pathname.startsWith('/revenue/')) return 'revenue';
  if (pathname.startsWith('/pipeline/')) return 'pipeline';
  return 'pipeline';
}

function getCustomerDetailId(): number | null {
  const match = window.location.pathname.match(/^\/customers\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getAccountDetailId(): number | null {
  const match = window.location.pathname.match(/^\/accounts\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getCustomerRowModeParam(): CustomerRowMode {
  const value = new URLSearchParams(window.location.search).get('mode');
  return value === 'contact' ? 'contact' : 'account';
}

function getNoteDetailId(): number | null {
  const match = window.location.pathname.match(/^\/notes\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getScheduleDetailId(): number | null {
  const match = window.location.pathname.match(/^\/schedules\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function isScheduleCalendarRoute(): boolean {
  return /^\/schedules\/calendar\/?$/.test(window.location.pathname);
}

const productSortFields: ProductSortField[] = ['code', 'description', 'specification', 'unit', 'price', 'status', 'quoteCount', 'deliveryCount', 'updatedAt'];

function getProductSortParam(): ProductSortField {
  const value = new URLSearchParams(window.location.search).get('sort') || 'code';
  return productSortFields.includes(value as ProductSortField) ? value as ProductSortField : 'code';
}

function getProductOrderParam(): ProductSortOrder {
  return new URLSearchParams(window.location.search).get('order') === 'desc' ? 'desc' : 'asc';
}

function getPrepaymentDetailId(): number | null {
  const match = window.location.pathname.match(/^\/prepayments\/(\d+)\/(?:edit\/?)?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getPrepaymentCustomerId(): number | null {
  const match = window.location.pathname.match(/^\/prepayments\/customer\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getPrepaymentAccountId(): number | null {
  const match = window.location.pathname.match(/^\/prepayments\/account\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function isPrepaymentCreateRoute(): boolean {
  return /^\/prepayments\/new\/?$/.test(window.location.pathname);
}

function isPrepaymentEditRoute(): boolean {
  return /^\/prepayments\/\d+\/edit\/?$/.test(window.location.pathname);
}

function getCreateCustomerParam(): string {
  return new URLSearchParams(window.location.search).get('customer') || '';
}

function getCreateDepartmentParam(): string {
  const value = new URLSearchParams(window.location.search).get('department') || '';
  return /^\d+$/.test(value) ? value : '';
}

function getCreateScheduleParam(): string {
  const value = new URLSearchParams(window.location.search).get('schedule') || '';
  return /^\d+$/.test(value) ? value : '';
}

const savedViews: Array<{ id: SavedView; label: string }> = [
  { id: 'priority', label: '내 담당 우선' },
  { id: 'thisWeek', label: '이번 주 마감' },
  { id: 'quoteDelay', label: '견적 제출 후 지연' },
  { id: 'managerReview', label: '매니저 검토' },
];



const formatSignedPercent = (value: number) => `${value > 0 ? '+' : ''}${value}%`;
const pipelineQuoteDateLabel = (deal?: Deal | null) => {
  const quote = deal?.latestQuote;
  if (!quote?.quoteDate || quote.basisType === 'delivery') {
    return '';
  }
  return formatDateLabel(quote.quoteDate);
};

const formatDealProbability = (probability: number | null | undefined) => (
  probability === null || probability === undefined ? '미입력' : `${probability}%`
);

const dealProbabilityPercent = (probability: number | null | undefined) => (
  probability === null || probability === undefined ? 0 : probability
);
const legacyFallbackViews: MainView[] = [];
const pipelineDataViews: MainView[] = ['pipeline', 'documents', 'products'];

function routeUsesPipelineData(view: MainView): boolean {
  return pipelineDataViews.includes(view);
}

function useRouteChangeSignal() {
  const [, setRouteChangeSignal] = useState(0);

  useEffect(() => {
    const refreshRoute = () => setRouteChangeSignal((value) => value + 1);
    window.addEventListener('popstate', refreshRoute);
    window.addEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    return () => {
      window.removeEventListener('popstate', refreshRoute);
      window.removeEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    };
  }, []);
}

function LegacyFallbackRoutePage({ view }: { view: MainView }) {
  const meta = routeMeta[view];
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
        <article className="route-stat-card">
          <span>화면 상태</span>
          <strong>운영 연결</strong>
          <small>기존 업무 화면 유지</small>
        </article>
        <article className="route-stat-card">
          <span>접근 기준</span>
          <strong>로그인</strong>
          <small>기존 권한 흐름 유지</small>
        </article>
        <article className="route-stat-card">
          <span>이관 단계</span>
          <strong>대기</strong>
          <small>React 기능화 후보</small>
        </article>
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
            <span>관련 React 화면</span>
            <LayoutDashboard size={15} />
          </div>
          <div className="route-action-list">
            <a href="/dashboard/">대시보드<ChevronRight size={15} /></a>
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
          <article className="metric-card" key={metric.label}>
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
          {source === 'django' ? 'Django API 연결됨' : '데이터 연결 대기'}
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
  const quoteDateLabel = pipelineQuoteDateLabel(deal);

  return (
    <button className={`deal-card ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <div className="deal-card-top">
        <strong>{deal.company}</strong>
        <span className={`risk-badge ${deal.risk}`}>{riskLabel[deal.risk]}</span>
      </div>
      <span className="deal-contact">{deal.contact}</span>
      <div className="deal-value">
        <span>{formatWon(deal.value)}</span>
        <small>{formatDealProbability(deal.probability)}</small>
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
      {quoteDateLabel ? (
        <div className="pipeline-quote-date">
          <FileText size={13} />
          <span>견적일 {quoteDateLabel}</span>
        </div>
      ) : null}
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
          // 지금 선택된 카드는 어떤 경우에도 화면에서 사라지면 안 된다. 잠재 칸은
          // 기본이 "접힘 + 상위 10건만" 이라, '같은 담당자로 새 카드 만들기'로 만든
          // 카드(항상 잠재에서 시작)가 곧바로 숨어버려 복사가 실패한 것처럼 보였다.
          const visibleStageDeals =
            stage.id === 'potential'
              ? allStageDeals.filter(
                  (deal) => !deal.isPotentialOverflow || deal.id === selectedDeal?.id,
                )
              : allStageDeals;
          const stageDeals = visibleStageDeals;
          const total = stage.totalValue ?? stageDeals.reduce((sum, deal) => sum + deal.value, 0);
          // 선택된 카드가 이 칸에 있으면 접힌 상태를 풀어 그 카드를 보여준다.
          const isCollapsed =
            Boolean(collapsedStages[stage.id]) && selectedDeal?.stage !== stage.id;
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
                        <span>
                          {deal.company}
                          {deal.department ? <small>{deal.department}</small> : null}
                        </span>
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
          {deals.map((deal) => {
            const quoteDateLabel = pipelineQuoteDateLabel(deal);
            return (
              <tr key={deal.id} onClick={() => onSelect(deal)}>
                <td>
                  <strong>{deal.company}</strong>
                  <span>{deal.contact}</span>
                </td>
                <td>{stages.find((stage) => stage.id === deal.stage)?.label}</td>
                <td>
                  <strong>{formatWon(deal.value)}</strong>
                  {quoteDateLabel ? <span className="pipeline-list-submeta">견적일 {quoteDateLabel}</span> : null}
                </td>
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
                <td>{formatDealProbability(deal.probability)}</td>
                <td>{deal.nextAction}</td>
                <td>{deal.owner}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function HiddenCardsPanel({
  hidden,
  onRestore,
  restoringId,
  disabled,
}: {
  hidden: HiddenDeal[];
  onRestore: (dealId: number) => void;
  restoringId: number | null;
  disabled: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <section className="list-panel" aria-label="숨긴 파이프라인 카드" style={{ marginTop: 12 }}>
      <button type="button" className="show-stage-button" onClick={() => setOpen((value) => !value)}>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />} 숨긴 카드 {hidden.length}건
      </button>
      {open ? (
        <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0' }}>
          {hidden.map((item) => (
            <li
              key={item.id}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, padding: '6px 0' }}
            >
              <span>
                <strong>{item.company}</strong>
                {item.department ? <span className="muted"> · {item.department}</span> : null}
                {item.contact ? <span className="muted"> · {item.contact}</span> : null}
              </span>
              <button
                type="button"
                className="customer-row-action"
                disabled={disabled || restoringId === item.id}
                onClick={() => onRestore(item.id)}
              >
                복원
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function ProbabilityEditor({
  deal,
  canEdit,
  saving,
  error,
  message,
  onSave,
}: {
  deal: Deal;
  canEdit: boolean;
  saving: boolean;
  error: string;
  message: string;
  onSave: (deal: Deal, probability: number | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState('');
  const [inputError, setInputError] = useState('');

  const startEdit = () => {
    setValue(deal.probability !== null && deal.probability !== undefined ? String(deal.probability) : '');
    setInputError('');
    setEditing(true);
  };
  const cancelEdit = () => {
    setEditing(false);
    setInputError('');
  };
  const save = () => {
    const trimmed = value.trim();
    if (trimmed === '') {
      onSave(deal, null);
      setEditing(false);
      return;
    }
    const parsed = Number(trimmed);
    if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
      setInputError('0~100 사이의 숫자를 입력하세요.');
      return;
    }
    onSave(deal, Math.round(parsed));
    setEditing(false);
  };

  if (!canEdit) {
    return null;
  }

  if (!editing) {
    return (
      <div className="probability-edit-row">
        <button className="probability-edit-trigger" onClick={startEdit} type="button">
          <Pencil size={13} />
          확률 수정
        </button>
        {deal.probabilityOverridden ? (
          <button className="probability-reset" onClick={() => onSave(deal, null)} type="button">
            자동 계산으로 되돌리기
          </button>
        ) : null}
        {message ? <small className="move-status success">{message}</small> : null}
        {error ? <small className="move-status error">{error}</small> : null}
      </div>
    );
  }

  return (
    <div className="probability-edit-box">
      <input
        autoFocus
        max={100}
        min={0}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            save();
          } else if (event.key === 'Escape') {
            cancelEdit();
          }
        }}
        type="number"
        value={value}
      />
      <span>%</span>
      <button disabled={saving} onClick={save} type="button">
        {saving ? '저장중' : '저장'}
      </button>
      <button disabled={saving} onClick={cancelEdit} type="button">
        취소
      </button>
      {inputError ? <small className="move-status error">{inputError}</small> : null}
    </div>
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
  onRemoveDeal,
  removing,
  removeError,
  removeMessage,
  probabilitySaving,
  probabilityError,
  probabilityMessage,
  onUpdateProbability,
  duplicating,
  duplicateError,
  duplicateMessage,
  onDuplicateDeal,
}: {
  deal?: Deal;
  stages: StageSummary[];
  canMove: boolean;
  moving: boolean;
  moveError: string;
  moveMessage: string;
  onMoveStage: (deal: Deal, stage: PipelineStage) => void;
  onRemoveDeal: (deal: Deal) => void;
  removing: boolean;
  removeError: string;
  removeMessage: string;
  probabilitySaving: boolean;
  probabilityError: string;
  probabilityMessage: string;
  onUpdateProbability: (deal: Deal, probability: number | null) => void;
  duplicating: boolean;
  duplicateError: string;
  duplicateMessage: string;
  onDuplicateDeal: (deal: Deal) => void;
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

  const latestQuoteDateLabel = pipelineQuoteDateLabel(deal);
  const latestQuoteBasisDateLabel =
    deal.latestQuote?.basisDate && deal.latestQuote.basisDate !== deal.latestQuote.quoteDate
      ? formatDateLabel(deal.latestQuote.basisDate)
      : '';
  const sidebarQuote =
    deal.latestQuote && deal.latestQuote.basisType !== 'delivery'
      ? {
          number: deal.latestQuote.number || '견적 번호 없음',
          source: deal.latestQuote.source || '가격 기준 견적',
          amount: deal.latestQuote.amount,
          stage: deal.latestQuote.stage || `${deal.latestQuote.probability}%`,
          quoteDateLabel: latestQuoteDateLabel,
          basisDateLabel: latestQuoteBasisDateLabel,
          validUntilLabel: deal.latestQuote.validUntil ? formatDateLabel(deal.latestQuote.validUntil) : '',
          items: deal.latestQuote.items ?? [],
        }
      : deal.quoteComparison
        ? {
            number: deal.quoteComparison.number || '기준 견적',
            source: deal.quoteComparison.source || '기준 견적',
            amount: deal.quoteComparison.quotedAmount,
            stage: '기준 견적',
            quoteDateLabel: '',
            basisDateLabel: '',
            validUntilLabel: '',
            items: deal.quoteComparison.items ?? [],
          }
        : null;
  const hasSidebarQuoteMeta = Boolean(
    sidebarQuote?.quoteDateLabel || sidebarQuote?.basisDateLabel || sidebarQuote?.validUntilLabel,
  );
  const sidebarQuoteItems = sidebarQuote?.items ?? [];

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
      {canMove ? (
        <div className="stage-move-box">
          <button
            type="button"
            className="customer-row-action"
            disabled={duplicating}
            onClick={() => onDuplicateDeal(deal)}
          >
            {duplicating ? <Loader2 className="spin-icon" size={14} /> : <Copy size={14} />} 같은 담당자로 새 카드 만들기
          </button>
          <small className="move-help">
            {deal.contact} · {deal.company} 정보를 그대로 복사해 '잠재' 단계에 새 카드를 만듭니다.
            일정·노트·견적 기록은 이 카드로 옮겨오지 않습니다.
          </small>
          {duplicateMessage ? <small className="move-status success">{duplicateMessage}</small> : null}
          {duplicateError ? <small className="move-status error">{duplicateError}</small> : null}
        </div>
      ) : null}
      {canMove ? (
        <div className="stage-move-box">
          <button
            type="button"
            className="customer-row-action danger"
            disabled={removing}
            onClick={() => onRemoveDeal(deal)}
          >
            <Trash2 size={14} /> 보드에서 제거
          </button>
          <small className="move-help">고객·일정·노트·견적 기록은 보존되며 아래 "숨긴 카드"에서 복원할 수 있습니다.</small>
          {removeMessage ? <small className="move-status success">{removeMessage}</small> : null}
          {removeError ? <small className="move-status error">{removeError}</small> : null}
        </div>
      ) : null}
      <div className="detail-value">
        <span>{deal.latestQuote?.basisType === 'delivery' ? '실제 납품 매출' : '예상 매출'}</span>
        <strong>{formatWon(deal.value)}</strong>
      </div>
      <div className="progress-wrap">
        <div className="progress-label">
          <span>수주 가능성</span>
          <strong>{formatDealProbability(deal.probability)}</strong>
        </div>
        <div className="progress-track">
          <div style={{ width: `${dealProbabilityPercent(deal.probability)}%` }} />
        </div>
        <ProbabilityEditor
          canEdit={canMove}
          deal={deal}
          error={probabilityError}
          message={probabilityMessage}
          onSave={onUpdateProbability}
          saving={probabilitySaving}
        />
      </div>
      {sidebarQuote ? (
        <div className="detail-box quote pipeline-quote-summary">
          <div className="section-title">들어간 견적</div>
          <div className="quote-line">
            <strong>{sidebarQuote.number}</strong>
            <span>{sidebarQuote.source}</span>
          </div>
          <div className="quote-line quote-amount-line">
            <strong>{formatWon(sidebarQuote.amount)}</strong>
            <span>{sidebarQuote.stage}</span>
          </div>
          {hasSidebarQuoteMeta ? (
            <div className="quote-meta-grid">
              {sidebarQuote.quoteDateLabel ? (
                <>
                  <span>견적일</span>
                  <strong>{sidebarQuote.quoteDateLabel}</strong>
                </>
              ) : null}
              {sidebarQuote.basisDateLabel ? (
                <>
                  <span>기준일</span>
                  <strong>{sidebarQuote.basisDateLabel}</strong>
                </>
              ) : null}
              {sidebarQuote.validUntilLabel ? (
                <>
                  <span>유효기한</span>
                  <strong>{sidebarQuote.validUntilLabel}</strong>
                </>
              ) : null}
            </div>
          ) : null}
          {sidebarQuoteItems.length ? (
            <div className="pipeline-quote-items">
              <div className="quote-items-heading">
                <span>견적 품목</span>
                <strong>{formatNumber(sidebarQuoteItems.length)}개</strong>
              </div>
              {sidebarQuoteItems.slice(0, 8).map((item) => {
                const quantityLabel = `${formatNumber(item.quantity)}${item.unit || ''}`;
                const groupLabel = item.quoteGroupLabel && item.quoteGroupLabel !== '기본 견적서'
                  ? item.quoteGroupLabel
                  : '';
                return (
                  <div className="pipeline-quote-item" key={item.id}>
                    <div>
                      <strong>{groupLabel ? `[${groupLabel}] ${item.itemName}` : item.itemName}</strong>
                      <span>
                        {quantityLabel}
                        {item.unitPrice !== null && item.unitPrice !== undefined ? ` · 단가 ${formatWon(item.unitPrice)}` : ''}
                      </span>
                    </div>
                    {item.totalPrice !== undefined ? <em>{formatWon(item.totalPrice)}</em> : null}
                  </div>
                );
              })}
              {sidebarQuoteItems.length > 8 ? (
                <small>외 {formatNumber(sidebarQuoteItems.length - 8)}개 품목</small>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="detail-box quote pipeline-quote-summary empty">
          <div className="section-title">들어간 견적</div>
          <strong>등록된 견적 없음</strong>
          <span>견적 일정, 견적 활동, 또는 견적서가 등록되면 여기에 표시됩니다.</span>
        </div>
      )}
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
          고객 상세 열기
          <MoveUpRight size={16} />
        </a>
      ) : null}
    </aside>
  );
}

export function App() {
  useRouteChangeSignal();

  const currentView = getCurrentView();
  useEffect(() => {
    document.title = `${routeMeta[currentView].title} - 영업 보고 시스템`;
  }, [currentView]);

  const customerDetailId = currentView === 'customers' ? getCustomerDetailId() : null;
  const accountDetailId = currentView === 'customers' ? getAccountDetailId() : null;
  const noteDetailId = currentView === 'notes' ? getNoteDetailId() : null;
  const scheduleDetailId = currentView === 'schedules' ? getScheduleDetailId() : null;
  const scheduleCalendarRoute = currentView === 'schedules' && isScheduleCalendarRoute();
  const prepaymentCustomerId = currentView === 'prepayments' ? getPrepaymentCustomerId() : null;
  const prepaymentAccountId = currentView === 'prepayments' ? getPrepaymentAccountId() : null;
  const prepaymentDetailId = currentView === 'prepayments' ? getPrepaymentDetailId() : null;
  const prepaymentCreateRoute = currentView === 'prepayments' && isPrepaymentCreateRoute();
  const prepaymentEditRoute = currentView === 'prepayments' && isPrepaymentEditRoute();
  const [mode, setMode] = useState<'board' | 'list'>('board');
  const [pipelineDetailCollapsed, setPipelineDetailCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem('pipelineDetailCollapsed') === '1';
    } catch {
      return false;
    }
  });
  const [pipelineData, setPipelineData] = useState(emptyPipelineData);
  const [pipelineLoading, setPipelineLoading] = useState(routeUsesPipelineData(currentView));
  const [customersData, setCustomersData] = useState<CustomersData | null>(null);
  const [customersLoading, setCustomersLoading] = useState(currentView === 'customers');
  const [customerDetailData, setCustomerDetailData] = useState<CustomerDetailData | null>(null);
  const [customerDetailLoading, setCustomerDetailLoading] = useState(Boolean(customerDetailId || accountDetailId));
  const [customerQuery, setCustomerQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [customerOwner, setCustomerOwner] = useState(() => new URLSearchParams(window.location.search).get('owner') || '');
  const [customerStage, setCustomerStage] = useState(
    () => new URLSearchParams(window.location.search).get('stage') || new URLSearchParams(window.location.search).get('pipeline_stage') || '',
  );
  const [customerCompany, setCustomerCompany] = useState(
    () => new URLSearchParams(window.location.search).get('company') || new URLSearchParams(window.location.search).get('company_id') || '',
  );
  const [customerGrade, setCustomerGrade] = useState(() => new URLSearchParams(window.location.search).get('grade') || '');
  const [customerLevel, setCustomerLevel] = useState(
    () => new URLSearchParams(window.location.search).get('level') || new URLSearchParams(window.location.search).get('score_level') || '',
  );
  const [customerRowMode, setCustomerRowMode] = useState<CustomerRowMode>(() => getCustomerRowModeParam());
  const [customerPage, setCustomerPage] = useState(() => Math.max(Number(new URLSearchParams(window.location.search).get('page') || '1') || 1, 1));
  const customerPageSize = 20;
  const [demosData, setDemosData] = useState<DemoRecordsData | null>(null);
  const [demosLoading, setDemosLoading] = useState(currentView === 'demos');
  const [demoQuery, setDemoQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [demoStatus, setDemoStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || 'active');
  const [demoProduct, setDemoProduct] = useState(() => new URLSearchParams(window.location.search).get('product') || '');
  const [demoOwner, setDemoOwner] = useState(() => new URLSearchParams(window.location.search).get('owner') || '');
  const [demoCustomer] = useState(() => new URLSearchParams(window.location.search).get('customer') || '');
  const [demoDepartment] = useState(() => new URLSearchParams(window.location.search).get('department') || '');
  const [demoSort, setDemoSort] = useState(() => new URLSearchParams(window.location.search).get('sort') || 'updated');
  const [demoOrder, setDemoOrder] = useState(() => new URLSearchParams(window.location.search).get('order') || 'desc');
  const [demoCreateOpen, setDemoCreateOpen] = useState(currentView === 'demos' && shouldOpenCreatePanel());
  const [demoEditingId, setDemoEditingId] = useState<number | null>(null);
  const [demoForm, setDemoForm] = useState<DemoRecordFormState>(() => makeDemoRecordForm(null, {
    departmentId: new URLSearchParams(window.location.search).get('department') || '',
    customerId: new URLSearchParams(window.location.search).get('customer') || '',
  }));
  const [demoSaving, setDemoSaving] = useState(false);
  const [demoError, setDemoError] = useState('');
  const [demoMessage, setDemoMessage] = useState('');
  const [notesData, setNotesData] = useState<NotesData | null>(null);
  const [notesLoading, setNotesLoading] = useState(currentView === 'notes' && !noteDetailId);
  const [noteDetailData, setNoteDetailData] = useState<NoteDetailData | null>(null);
  const [noteDetailLoading, setNoteDetailLoading] = useState(Boolean(noteDetailId));
  const [noteQuery, setNoteQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [noteDateFrom, setNoteDateFrom] = useState(
    () => new URLSearchParams(window.location.search).get('date_from') || new URLSearchParams(window.location.search).get('dateFrom') || defaultNotesDateFrom(),
  );
  const [noteDateTo, setNoteDateTo] = useState(
    () => new URLSearchParams(window.location.search).get('date_to') || new URLSearchParams(window.location.search).get('dateTo') || defaultNotesDateTo(),
  );
  const [noteOwner, setNoteOwner] = useState(() => new URLSearchParams(window.location.search).get('owner') || '');
  const [noteActionType, setNoteActionType] = useState(
    () => new URLSearchParams(window.location.search).get('action_type') || new URLSearchParams(window.location.search).get('actionType') || '',
  );
  const [noteReview, setNoteReview] = useState(() => getNoteReviewParam());
  const [noteNextAction, setNoteNextAction] = useState(() => new URLSearchParams(window.location.search).get('next_action') || '');
  const [noteReviewingId, setNoteReviewingId] = useState<number | null>(null);
  const [noteReviewError, setNoteReviewError] = useState('');
  const [noteReviewMessage, setNoteReviewMessage] = useState('');
  const [noteCreateOpen, setNoteCreateOpen] = useState(currentView === 'notes' && shouldOpenCreatePanel());
  const [noteCreateForm, setNoteCreateForm] = useState<NoteCreateFormState>(() => makeEmptyNoteCreateForm());
  const [noteCreating, setNoteCreating] = useState(false);
  const [noteCreateError, setNoteCreateError] = useState('');
  const [noteCreateMessage, setNoteCreateMessage] = useState('');
  const [schedulesData, setSchedulesData] = useState<SchedulesData | null>(null);
  const [schedulesLoading, setSchedulesLoading] = useState(currentView === 'schedules' && !scheduleDetailId && !scheduleCalendarRoute);
  const [scheduleCreateOpen, setScheduleCreateOpen] = useState(currentView === 'schedules' && !scheduleDetailId && !scheduleCalendarRoute && shouldOpenCreatePanel());
  const [scheduleCreateForm, setScheduleCreateForm] = useState<ScheduleCreateFormState>(() => makeEmptyScheduleCreateForm(getCreateDateParam() || undefined));
  const [scheduleCreating, setScheduleCreating] = useState(false);
  const [scheduleCreateError, setScheduleCreateError] = useState('');
  const [scheduleCreateMessage, setScheduleCreateMessage] = useState('');
  const [scheduleCreatedDetailHref, setScheduleCreatedDetailHref] = useState('');
  const [scheduleDetailData, setScheduleDetailData] = useState<ScheduleDetailData | null>(null);
  const [scheduleDetailLoading, setScheduleDetailLoading] = useState(Boolean(scheduleDetailId));
  const [scheduleCalendarData, setScheduleCalendarData] = useState<ScheduleCalendarData | null>(null);
  const [scheduleCalendarLoading, setScheduleCalendarLoading] = useState(scheduleCalendarRoute);
  const [scheduleCalendarMonth, setScheduleCalendarMonth] = useState(getScheduleCalendarMonthParam);
  const [scheduleCalendarDataFilter, setScheduleCalendarDataFilter] = useState(getScheduleCalendarDataFilterParam);
  const [scheduleCalendarFilterUser, setScheduleCalendarFilterUser] = useState(() => new URLSearchParams(window.location.search).get('filter_user') || '');
  const [scheduleCalendarStatusUpdatingKey, setScheduleCalendarStatusUpdatingKey] = useState('');
  const [scheduleCalendarStatusError, setScheduleCalendarStatusError] = useState('');
  const [scheduleCalendarStatusMessage, setScheduleCalendarStatusMessage] = useState('');
  const [scheduleQuery, setScheduleQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [scheduleOwner, setScheduleOwner] = useState(() => new URLSearchParams(window.location.search).get('owner') || '');
  const [scheduleStatus, setScheduleStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || '');
  const [scheduleActivityType, setScheduleActivityType] = useState(
    () => new URLSearchParams(window.location.search).get('activity_type') || new URLSearchParams(window.location.search).get('activityType') || '',
  );
  const [scheduleRange, setScheduleRange] = useState(() => new URLSearchParams(window.location.search).get('range') || '');
  const [prepaymentsData, setPrepaymentsData] = useState<PrepaymentsData | null>(null);
  const [prepaymentsLoading, setPrepaymentsLoading] = useState(currentView === 'prepayments' && !prepaymentAccountId && !prepaymentCustomerId && !prepaymentDetailId && !prepaymentCreateRoute);
  const [prepaymentCustomerData, setPrepaymentCustomerData] = useState<PrepaymentCustomerData | null>(null);
  const [prepaymentCustomerLoading, setPrepaymentCustomerLoading] = useState(Boolean(prepaymentAccountId || prepaymentCustomerId));
  const [prepaymentCustomerUser, setPrepaymentCustomerUser] = useState('');
  const [prepaymentCreateData, setPrepaymentCreateData] = useState<PrepaymentCreateData | null>(null);
  const [prepaymentCreateLoading, setPrepaymentCreateLoading] = useState(prepaymentCreateRoute);
  const [prepaymentDetailData, setPrepaymentDetailData] = useState<PrepaymentDetailData | null>(null);
  const [prepaymentDetailLoading, setPrepaymentDetailLoading] = useState(Boolean(prepaymentDetailId));
  const [prepaymentQuery, setPrepaymentQuery] = useState(
    () => new URLSearchParams(window.location.search).get('q') || new URLSearchParams(window.location.search).get('search') || '',
  );
  const [prepaymentStatus, setPrepaymentStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || '');
  const [prepaymentDataFilter, setPrepaymentDataFilter] = useState(
    () => new URLSearchParams(window.location.search).get('data_filter') || new URLSearchParams(window.location.search).get('dataFilter') || '',
  );
  const [prepaymentFilterUser, setPrepaymentFilterUser] = useState(
    () => new URLSearchParams(window.location.search).get('filter_user') || new URLSearchParams(window.location.search).get('filterUser') || '',
  );
  const [documentsData, setDocumentsData] = useState<DocumentTemplatesData | null>(null);
  const [documentsLoading, setDocumentsLoading] = useState(currentView === 'documents');
  const [documentTypeFilter, setDocumentTypeFilter] = useState(() => new URLSearchParams(window.location.search).get('type') || '');
  const [productsData, setProductsData] = useState<ProductManagementData | null>(null);
  const [productsLoading, setProductsLoading] = useState(currentView === 'products');
  const [productQuery, setProductQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [productStatus, setProductStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || '');
  const [productSort, setProductSort] = useState<ProductSortField>(() => getProductSortParam());
  const [productOrder, setProductOrder] = useState<ProductSortOrder>(() => getProductOrderParam());
  const [productPage, setProductPage] = useState(() => Number(new URLSearchParams(window.location.search).get('page') || '1') || 1);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [profileLoading, setProfileLoading] = useState(currentView === 'profile');
  const [profileForm, setProfileForm] = useState<ProfileFormState>(() => makeProfileForm());
  const [profilePasswordForm, setProfilePasswordForm] = useState<ProfilePasswordFormState>(() => makeEmptyProfilePasswordForm());
  const [profileSaving, setProfileSaving] = useState(false);
  const [profilePasswordSaving, setProfilePasswordSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');
  const [profileError, setProfileError] = useState('');
  const [employeesData, setEmployeesData] = useState<EmployeesData | null>(null);
  const [employeesLoading, setEmployeesLoading] = useState(currentView === 'employees');
  const [employeeQuery, setEmployeeQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [employeeRole, setEmployeeRole] = useState(() => new URLSearchParams(window.location.search).get('role') || '');
  const [employeeStatus, setEmployeeStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || '');
  const [employeeCompany, setEmployeeCompany] = useState(() => new URLSearchParams(window.location.search).get('company') || '');
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<SavedView>('priority');
  const [movingDealId, setMovingDealId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState('');
  const [moveMessage, setMoveMessage] = useState('');
  const [removingDealId, setRemovingDealId] = useState<number | null>(null);
  const [removeError, setRemoveError] = useState('');
  const [removeMessage, setRemoveMessage] = useState('');
  const [restoringDealId, setRestoringDealId] = useState<number | null>(null);
  const [probabilityDealId, setProbabilityDealId] = useState<number | null>(null);
  const [probabilityError, setProbabilityError] = useState('');
  const [probabilityMessage, setProbabilityMessage] = useState('');
  const [duplicatingDealId, setDuplicatingDealId] = useState<number | null>(null);
  const [duplicateError, setDuplicateError] = useState('');
  const [duplicateMessage, setDuplicateMessage] = useState('');
  const scheduleCalendarRange = useMemo(() => getScheduleCalendarRange(scheduleCalendarMonth), [scheduleCalendarMonth]);

  useEffect(() => {
    try {
      window.localStorage.setItem('pipelineDetailCollapsed', pipelineDetailCollapsed ? '1' : '0');
    } catch {
      // Ignore storage failures so the toolbar toggle still works in restricted browsers.
    }
  }, [pipelineDetailCollapsed]);

  useEffect(() => {
    if (!routeUsesPipelineData(currentView)) {
      setPipelineLoading(false);
      return;
    }
    let alive = true;
    setPipelineLoading(true);
    loadPipelineData()
      .then((data) => {
        if (!alive) {
          return;
        }
        setPipelineData(data);
        setSelectedDealId(data.deals[0]?.id ?? null);
        setPipelineLoading(false);
      })
      .catch(() => {
        if (alive) {
          setPipelineLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, [currentView]);

  useEffect(() => {
    if (currentView !== 'employees') {
      return;
    }
    let alive = true;
    setEmployeesLoading(true);
    loadEmployeesData({
      company: employeeCompany,
      q: employeeQuery,
      role: employeeRole,
      status: employeeStatus,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setEmployeesData(data);
      setEmployeesLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, employeeCompany, employeeQuery, employeeRole, employeeStatus]);

  const refreshEmployeesData = async () => {
    setEmployeesLoading(true);
    const data = await loadEmployeesData({
      company: employeeCompany,
      q: employeeQuery,
      role: employeeRole,
      status: employeeStatus,
    });
    setEmployeesData(data);
    setEmployeesLoading(false);
  };

  useEffect(() => {
    if (currentView !== 'employees') {
      return;
    }
    const params = new URLSearchParams();
    if (employeeQuery.trim()) params.set('q', employeeQuery.trim());
    if (employeeRole) params.set('role', employeeRole);
    if (employeeStatus) params.set('status', employeeStatus);
    if (employeeCompany) params.set('company', employeeCompany);
    const queryString = params.toString();
    window.history.replaceState(null, '', `/employees/${queryString ? `?${queryString}` : ''}`);
  }, [currentView, employeeCompany, employeeQuery, employeeRole, employeeStatus]);

  useEffect(() => {
    if (currentView !== 'customers' || customerDetailId || accountDetailId) {
      return;
    }
    let alive = true;
    setCustomersLoading(true);
    loadCustomersData({
      q: customerQuery,
      owner: customerOwner,
      stage: customerStage,
      company: customerCompany,
      grade: customerGrade,
      level: customerLevel,
      mode: customerRowMode,
      page: customerPage,
      pageSize: customerPageSize,
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
  }, [
    accountDetailId,
    currentView,
    customerCompany,
    customerDetailId,
    customerGrade,
    customerLevel,
    customerOwner,
    customerPage,
    customerQuery,
    customerRowMode,
    customerStage,
  ]);

  useEffect(() => {
    if (currentView !== 'customers' || customerDetailId || accountDetailId) {
      return;
    }
    const params = new URLSearchParams();
    if (customerQuery.trim()) params.set('q', customerQuery.trim());
    if (customerCompany) params.set('company', customerCompany);
    if (customerOwner) params.set('owner', customerOwner);
    if (customerStage) params.set('stage', customerStage);
    if (customerGrade) params.set('grade', customerGrade);
    if (customerLevel) params.set('level', customerLevel);
    if (customerRowMode !== 'account') params.set('mode', customerRowMode);
    if (customerPage > 1) params.set('page', String(customerPage));
    const queryString = params.toString();
    window.history.replaceState(null, '', `/customers/${queryString ? `?${queryString}` : ''}`);
  }, [
    accountDetailId,
    currentView,
    customerCompany,
    customerDetailId,
    customerGrade,
    customerLevel,
    customerOwner,
    customerPage,
    customerQuery,
    customerRowMode,
    customerStage,
  ]);

  useEffect(() => {
    if (currentView !== 'demos') {
      return;
    }
    let alive = true;
    setDemosLoading(true);
    setDemoError('');
    loadDemoRecordsData({
      q: demoQuery,
      status: demoStatus,
      product: demoProduct,
      owner: demoOwner,
      customer: demoCustomer,
      department: demoDepartment,
      sort: demoSort,
      order: demoOrder,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setDemosData(data);
      setDemosLoading(false);
    }).catch((error: Error) => {
      if (!alive) {
        return;
      }
      setDemoError(error.message || '데모 목록을 불러오지 못했습니다.');
      setDemosLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, demoCustomer, demoDepartment, demoOrder, demoOwner, demoProduct, demoQuery, demoSort, demoStatus]);

  useEffect(() => {
    if (currentView !== 'demos') {
      return;
    }
    const params = new URLSearchParams();
    if (demoQuery.trim()) params.set('q', demoQuery.trim());
    if (demoStatus && demoStatus !== 'active') params.set('status', demoStatus);
    if (demoProduct) params.set('product', demoProduct);
    if (demoOwner) params.set('owner', demoOwner);
    if (demoCustomer) params.set('customer', demoCustomer);
    if (demoDepartment) params.set('department', demoDepartment);
    if (demoSort && demoSort !== 'updated') params.set('sort', demoSort);
    if (demoOrder && demoOrder !== 'desc') params.set('order', demoOrder);
    const queryString = params.toString();
    window.history.replaceState(null, '', `/demos/${queryString ? `?${queryString}` : ''}`);
  }, [currentView, demoCustomer, demoDepartment, demoOrder, demoOwner, demoProduct, demoQuery, demoSort, demoStatus]);

  useEffect(() => {
    if (currentView !== 'customers' || (!customerDetailId && !accountDetailId)) {
      setCustomerDetailData(null);
      setCustomerDetailLoading(false);
      return;
    }
    let alive = true;
    setCustomerDetailLoading(true);
    const detailRequest = accountDetailId
      ? loadAccountDetailData(accountDetailId)
      : loadCustomerDetailData(customerDetailId as number);
    detailRequest.then((data) => {
      if (!alive) {
        return;
      }
      setCustomerDetailData(data);
      setCustomerDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [accountDetailId, currentView, customerDetailId]);

  useEffect(() => {
    if (currentView !== 'notes' || noteDetailId) {
      return;
    }
    let alive = true;
    setNotesLoading(true);
    setNoteReviewError('');
    setNoteReviewMessage('');
    setNoteCreateError('');
    loadNotesData({
      q: noteQuery,
      dateFrom: noteDateFrom,
      dateTo: noteDateTo,
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
  }, [currentView, noteActionType, noteDateFrom, noteDateTo, noteDetailId, noteNextAction, noteOwner, noteQuery, noteReview]);

  useEffect(() => {
    if (currentView !== 'notes' || !noteDetailId) {
      setNoteDetailData(null);
      setNoteDetailLoading(false);
      return;
    }
    let alive = true;
    setNoteDetailLoading(true);
    loadNoteDetailData(noteDetailId).then((data) => {
      if (!alive) {
        return;
      }
      setNoteDetailData(data);
      setNoteDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, noteDetailId]);

  useEffect(() => {
    if (currentView !== 'notes' || noteDetailId || !notesData?.create.canCreate) {
      return;
    }
    const requestedCustomerId = getCreateCustomerParam();
    const requestedDepartmentId = getCreateDepartmentParam();
    const requestedCustomer = notesData.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const firstActionType = notesData.create.actionTypes[0]?.value || 'customer_meeting';
    const requestedScheduleId = getCreateScheduleParam();
    const requestedSchedule = notesData.create.schedules.find((schedule) => String(schedule.id) === requestedScheduleId);
    setNoteCreateForm((previous) => {
      const nextDepartmentId = requestedCustomer?.departmentId
        ? String(requestedCustomer.departmentId)
        : requestedSchedule?.departmentId
          ? String(requestedSchedule.departmentId)
          : requestedDepartmentId || previous.departmentId || (notesData.create.customers[0]?.departmentId ? String(notesData.create.customers[0].departmentId) : notesData.create.departments[0]?.id ? String(notesData.create.departments[0].id) : '');
      const departmentCustomers = customersForDepartment(notesData.create.customers, nextDepartmentId);
      const fallbackCustomerId = departmentCustomers[0]?.id ?? notesData.create.customers[0]?.id;
      const previousFollowupValid = departmentCustomers.some((customer) => String(customer.id) === previous.followupId);
      const nextFollowupId = requestedCustomer
        ? String(requestedCustomer.id)
        : requestedSchedule
          ? (requestedSchedule.followupId ? String(requestedSchedule.followupId) : '')
          : previousFollowupValid
            ? previous.followupId
            : fallbackCustomerId ? String(fallbackCustomerId) : '';
      const existingSchedule = notesData.create.schedules.find((schedule) => String(schedule.id) === previous.scheduleId);
      const scheduleStillValid = existingSchedule && (
        nextFollowupId
          ? String(existingSchedule.followupId) === nextFollowupId
          : String(existingSchedule.departmentId || '') === nextDepartmentId
      );
      const nextScheduleId = requestedSchedule
        ? String(requestedSchedule.id)
        : scheduleStillValid
          ? previous.scheduleId
          : '';
      const shouldApplyScheduleAction = requestedSchedule && previous.scheduleId !== String(requestedSchedule.id);
      const scheduleActionType = requestedSchedule?.suggestedActionType || '';
      const nextActionType = shouldApplyScheduleAction && isNoteActionAllowed(notesData.create.actionTypes, scheduleActionType)
        ? scheduleActionType
        : previous.actionType || firstActionType;
      return {
        ...previous,
        actionType: nextActionType,
        activityDate: requestedSchedule?.date || previous.activityDate,
        departmentId: nextDepartmentId,
        followupId: nextFollowupId,
        scheduleId: nextScheduleId,
      };
    });
  }, [currentView, noteDetailId, notesData]);

  useEffect(() => {
    if (currentView !== 'schedules' || scheduleDetailId || scheduleCalendarRoute) {
      return;
    }
    let alive = true;
    setSchedulesLoading(true);
    loadSchedulesData({
      q: scheduleQuery,
      owner: scheduleOwner,
      status: scheduleStatus,
      activityType: scheduleActivityType,
      range: scheduleRange,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setSchedulesData(data);
      setSchedulesLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, scheduleActivityType, scheduleCalendarRoute, scheduleDetailId, scheduleOwner, scheduleQuery, scheduleRange, scheduleStatus]);

  useEffect(() => {
    if (currentView !== 'schedules' || scheduleDetailId || scheduleCalendarRoute || !schedulesData?.create.canCreate) {
      return;
    }
    const requestedCustomerId = getCreateCustomerParam();
    const requestedDepartmentId = getCreateDepartmentParam();
    const requestedCustomer = schedulesData.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const firstDepartmentId = requestedCustomer?.departmentId ?? (requestedDepartmentId ? Number(requestedDepartmentId) : null) ?? schedulesData.create.customers[0]?.departmentId ?? schedulesData.create.departments[0]?.id;
    const departmentCustomers = customersForDepartment(schedulesData.create.customers, firstDepartmentId ? String(firstDepartmentId) : '');
    const firstCustomerId = requestedCustomer?.id ?? departmentCustomers[0]?.id;
    const firstActivityType = schedulesData.create.activityTypes[0]?.value || 'customer_meeting';
    setScheduleCreateForm((previous) => ({
      ...previous,
      activityType: previous.activityType || firstActivityType,
      departmentId: previous.departmentId || (firstDepartmentId ? String(firstDepartmentId) : ''),
      followupId: previous.followupId && departmentCustomers.some((customer) => String(customer.id) === previous.followupId)
        ? previous.followupId
        : firstCustomerId ? String(firstCustomerId) : '',
      visitDate: previous.visitDate || getCreateDateParam(),
    }));
  }, [currentView, scheduleCalendarRoute, scheduleDetailId, schedulesData]);

  useEffect(() => {
    if (currentView !== 'schedules' || !scheduleCalendarRoute) {
      setScheduleCalendarLoading(false);
      return;
    }
    let alive = true;
    setScheduleCalendarLoading(true);
    loadScheduleCalendarData({
      start: scheduleCalendarRange.start,
      end: scheduleCalendarRange.end,
      dataFilter: scheduleCalendarDataFilter,
      filterUser: scheduleCalendarDataFilter === 'user' ? scheduleCalendarFilterUser : '',
    }).then((data) => {
      if (!alive) {
        return;
      }
      setScheduleCalendarData(data);
      if (data.filters.dataFilter && data.filters.dataFilter !== scheduleCalendarDataFilter) {
        setScheduleCalendarDataFilter(data.filters.dataFilter);
      }
      if (data.filters.filterUser !== scheduleCalendarFilterUser) {
        setScheduleCalendarFilterUser(data.filters.filterUser);
      }
      setScheduleCalendarLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [
    currentView,
    scheduleCalendarDataFilter,
    scheduleCalendarFilterUser,
    scheduleCalendarRange.end,
    scheduleCalendarRange.start,
    scheduleCalendarRoute,
  ]);

  useEffect(() => {
    if (currentView !== 'schedules' || !scheduleDetailId) {
      setScheduleDetailData(null);
      setScheduleDetailLoading(false);
      return;
    }
    let alive = true;
    setScheduleDetailLoading(true);
    loadScheduleDetailData(scheduleDetailId).then((data) => {
      if (!alive) {
        return;
      }
      setScheduleDetailData(data);
      setScheduleDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, scheduleDetailId]);

  useEffect(() => {
    if (currentView !== 'prepayments' || prepaymentAccountId || prepaymentCustomerId || prepaymentDetailId || prepaymentCreateRoute) {
      return;
    }
    let alive = true;
    setPrepaymentsLoading(true);
    loadPrepaymentsData({
      search: prepaymentQuery,
      status: prepaymentStatus,
      dataFilter: prepaymentDataFilter,
      filterUser: prepaymentFilterUser,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setPrepaymentsData(data);
      setPrepaymentsLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, prepaymentAccountId, prepaymentCreateRoute, prepaymentCustomerId, prepaymentDataFilter, prepaymentDetailId, prepaymentFilterUser, prepaymentQuery, prepaymentStatus]);

  useEffect(() => {
    if (currentView !== 'prepayments' || (!prepaymentAccountId && !prepaymentCustomerId)) {
      setPrepaymentCustomerData(null);
      setPrepaymentCustomerLoading(false);
      return;
    }
    let alive = true;
    setPrepaymentCustomerLoading(true);
    const detailRequest = prepaymentAccountId
      ? loadPrepaymentAccountData(prepaymentAccountId, prepaymentCustomerUser)
      : loadPrepaymentCustomerData(prepaymentCustomerId as number, prepaymentCustomerUser);
    detailRequest.then((data) => {
      if (!alive) {
        return;
      }
      setPrepaymentCustomerData(data);
      setPrepaymentCustomerLoading(false);
      if (!prepaymentCustomerUser && data.scope.targetUserId) {
        setPrepaymentCustomerUser(String(data.scope.targetUserId));
      }
    });
    return () => {
      alive = false;
    };
  }, [currentView, prepaymentAccountId, prepaymentCustomerId, prepaymentCustomerUser]);

  useEffect(() => {
    if (currentView !== 'prepayments' || !prepaymentCreateRoute) {
      setPrepaymentCreateData(null);
      setPrepaymentCreateLoading(false);
      return;
    }
    let alive = true;
    setPrepaymentCreateLoading(true);
    loadPrepaymentCreateData().then((data) => {
      if (!alive) {
        return;
      }
      setPrepaymentCreateData(data);
      setPrepaymentCreateLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, prepaymentCreateRoute]);

  useEffect(() => {
    if (currentView !== 'prepayments' || !prepaymentDetailId) {
      setPrepaymentDetailData(null);
      setPrepaymentDetailLoading(false);
      return;
    }
    let alive = true;
    setPrepaymentDetailLoading(true);
    loadPrepaymentDetailData(prepaymentDetailId).then((data) => {
      if (!alive) {
        return;
      }
      setPrepaymentDetailData(data);
      setPrepaymentDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, prepaymentDetailId]);


  useEffect(() => {
    if (currentView !== 'documents') {
      setDocumentsLoading(false);
      return;
    }
    let alive = true;
    setDocumentsLoading(true);
    loadDocumentTemplatesData(documentTypeFilter).then((data) => {
      if (!alive) {
        return;
      }
      setDocumentsData(data);
      setDocumentsLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, documentTypeFilter]);

  useEffect(() => {
    if (currentView !== 'products') {
      setProductsLoading(false);
      return;
    }
    let alive = true;
    const currentParams = new URLSearchParams(window.location.search);
    const selectedProductId = Number(currentParams.get('product') || 0) || null;
    setProductsLoading(true);
    loadProductManagementData({
      order: productOrder,
      page: productPage,
      pageSize: 50,
      q: productQuery,
      selectedProductId,
      sort: productSort,
      status: productStatus,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setProductsData(data);
      setProductsLoading(false);
    });

    const params = new URLSearchParams();
    if (productQuery.trim()) params.set('q', productQuery.trim());
    if (productStatus) params.set('status', productStatus);
    if (productSort !== 'code') params.set('sort', productSort);
    if (productOrder !== 'asc') params.set('order', productOrder);
    if (productPage > 1) params.set('page', String(productPage));
    ['create', 'import', 'product', 'edit', 'delete'].forEach((key) => {
      const value = currentParams.get(key);
      if (value) {
        params.set(key, value);
      }
    });
    const queryString = params.toString();
    window.history.replaceState(null, '', `/products/${queryString ? `?${queryString}` : ''}`);

    return () => {
      alive = false;
    };
  }, [currentView, productOrder, productPage, productQuery, productSort, productStatus]);

  useEffect(() => {
    if (currentView !== 'profile') {
      setProfileLoading(false);
      return;
    }
    let alive = true;
    setProfileLoading(true);
    loadProfileData().then((data) => {
      if (!alive) {
        return;
      }
      setProfileData(data);
      setProfileForm(makeProfileForm(data));
      setProfileLoading(false);
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
  const refreshPipelineData = async (preferredDealId: number | null = selectedDealId) => {
    const data = await loadPipelineData();
    setPipelineData(data);
    setSelectedDealId(
      preferredDealId && data.deals.some((item) => item.id === preferredDealId)
        ? preferredDealId
        : data.deals[0]?.id ?? null,
    );
    return data;
  };
  const handleMoveStage = async (deal: Deal, stage: PipelineStage) => {
    if (pipelineData.source !== 'django' || deal.stage === stage) {
      return;
    }
    // 수주 카드를 다른 단계로 옮기면 이 건이 수주 목록에서 빠진다. 같은 담당자에게
    // 새 건이 생긴 경우라면 기존 수주 카드는 그대로 두고 "같은 담당자로 새 카드
    // 만들기"를 쓰는 게 맞다 — 그래야 수주 이력과 새 건이 각각 남는다.
    // (금액은 실제 납품 기준이라 카드를 옮겨도 올해 매출에서 빠지지 않는다.)
    if (
      deal.stage === 'won' &&
      !window.confirm(
        [
          '이 카드는 수주 건입니다.',
          '',
          '같은 담당자에게 새로 생긴 건이라면 이 카드를 옮기지 말고, 상세 패널의',
          '"같은 담당자로 새 카드 만들기"를 쓰세요. 그래야 수주 이력이 그대로 남습니다.',
          '',
          '(올해 매출 금액은 실제 납품 기준이라 카드를 옮겨도 줄지 않습니다.)',
          '',
          '그래도 이 카드를 옮기시겠습니까?',
        ].join('\n'),
      )
    ) {
      return;
    }
    setMovingDealId(deal.id);
    setMoveError('');
    setMoveMessage('');
    try {
      await moveDealStage(deal.id, stage);
      await refreshPipelineData(deal.id);
      setMoveMessage('단계가 변경되었습니다.');
    } catch (error) {
      setMoveError(error instanceof Error ? error.message : '단계 변경에 실패했습니다.');
    } finally {
      setMovingDealId(null);
    }
  };
  const handleUpdateProbability = async (deal: Deal, probability: number | null) => {
    if (pipelineData.source !== 'django') {
      return;
    }
    setProbabilityDealId(deal.id);
    setProbabilityError('');
    setProbabilityMessage('');
    try {
      await updateDealProbability(deal.id, probability);
      await refreshPipelineData(deal.id);
      setProbabilityMessage(probability === null ? '자동 계산 확률로 되돌렸습니다.' : '확률이 저장되었습니다.');
    } catch (error) {
      setProbabilityError(error instanceof Error ? error.message : '확률 저장에 실패했습니다.');
    } finally {
      setProbabilityDealId(null);
    }
  };
  const handleDuplicateDeal = async (deal: Deal) => {
    if (pipelineData.source !== 'django') {
      return;
    }
    setDuplicatingDealId(deal.id);
    setDuplicateError('');
    setDuplicateMessage('');
    try {
      const { followupId, message } = await duplicateDealCard(deal.id);
      await refreshPipelineData(followupId);
      setDuplicateMessage(message || '새 카드를 만들었습니다.');
    } catch (error) {
      setDuplicateError(error instanceof Error ? error.message : '새 카드를 만들지 못했습니다.');
    } finally {
      setDuplicatingDealId(null);
    }
  };
  const handleRemoveDeal = async (deal: Deal) => {
    if (pipelineData.source !== 'django') {
      return;
    }
    if (!window.confirm(
      `"${deal.company}" 카드를 파이프라인 보드에서 제거할까요?\n고객·일정·영업노트·견적 기록은 그대로 보존되며, 아래 "숨긴 카드"에서 다시 복원할 수 있습니다.`,
    )) {
      return;
    }
    setRemovingDealId(deal.id);
    setRemoveError('');
    setRemoveMessage('');
    try {
      await hideDealCard(deal.id);
      await refreshPipelineData(null);
      setRemoveMessage('카드를 보드에서 제거했습니다. (숨긴 카드에서 복원 가능)');
    } catch (error) {
      setRemoveError(error instanceof Error ? error.message : '카드 제거에 실패했습니다.');
    } finally {
      setRemovingDealId(null);
    }
  };
  const handleRestoreDeal = async (dealId: number) => {
    setRestoringDealId(dealId);
    setRemoveError('');
    setRemoveMessage('');
    try {
      await unhideDealCard(dealId);
      await refreshPipelineData(dealId);
      setRemoveMessage('카드를 보드에 복원했습니다.');
    } catch (error) {
      setRemoveError(error instanceof Error ? error.message : '카드 복원에 실패했습니다.');
    } finally {
      setRestoringDealId(null);
    }
  };
  const handleCustomerQueryChange = (value: string) => {
    setCustomerQuery(value);
    setCustomerPage(1);
  };
  const handleCustomerCompanyFilterChange = (value: string) => {
    setCustomerCompany(value);
    setCustomerPage(1);
  };
  const handleCustomerOwnerChange = (value: string) => {
    setCustomerOwner(value);
    setCustomerPage(1);
  };
  const handleCustomerStageChange = (value: string) => {
    setCustomerStage(value);
    setCustomerPage(1);
  };
  const handleCustomerGradeChange = (value: string) => {
    setCustomerGrade(value);
    setCustomerPage(1);
  };
  const handleCustomerLevelChange = (value: string) => {
    setCustomerLevel(value);
    setCustomerPage(1);
  };
  const handleCustomerRowModeChange = (value: CustomerRowMode) => {
    setCustomerRowMode(value);
    setCustomerPage(1);
  };
  const handleCustomerPageChange = (value: number) => {
    setCustomerPage(Math.max(1, value));
  };
  const refreshDemosData = async () => {
    const data = await loadDemoRecordsData({
      q: demoQuery,
      status: demoStatus,
      product: demoProduct,
      owner: demoOwner,
      customer: demoCustomer,
      department: demoDepartment,
      sort: demoSort,
      order: demoOrder,
    });
    setDemosData(data);
    return data;
  };
  const handleDemoCreateOpen = (defaults: Partial<DemoRecordFormState> = {}) => {
    setDemoEditingId(null);
    setDemoForm(makeDemoRecordForm(null, {
      departmentId: defaults.departmentId ?? demoDepartment,
      customerId: defaults.customerId ?? demoCustomer,
      ...defaults,
    }));
    setDemoCreateOpen(true);
    setDemoError('');
    setDemoMessage('');
  };
  const handleDemoEdit = (record: DemoRecordItem) => {
    setDemoEditingId(record.id);
    setDemoForm(makeDemoRecordForm(record));
    setDemoCreateOpen(true);
    setDemoError('');
    setDemoMessage('');
  };
  const handleDemoSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const { payload, error } = demoRecordFormToPayload(demoForm);
    if (error || !payload) {
      setDemoError(error || '데모 입력값을 확인하세요.');
      return;
    }
    setDemoSaving(true);
    setDemoError('');
    setDemoMessage('');
    try {
      if (demoEditingId) {
        await updateDemoRecord(demoEditingId, payload);
        setDemoMessage('데모 기록을 저장했습니다.');
      } else {
        await createDemoRecord(payload);
        setDemoMessage('데모 기록을 등록했습니다.');
      }
      setDemoCreateOpen(false);
      setDemoEditingId(null);
      await refreshDemosData();
      if (customerDetailData) {
        await refreshCustomerDetailData();
      }
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : '데모 기록 저장에 실패했습니다.');
    } finally {
      setDemoSaving(false);
    }
  };
  const handleDemoDelete = async (record: DemoRecordItem) => {
    if (!window.confirm(`${record.productName} 데모 기록을 삭제할까요?`)) {
      return;
    }
    setDemoSaving(true);
    setDemoError('');
    setDemoMessage('');
    try {
      await deleteDemoRecord(record.id);
      setDemoMessage('데모 기록을 삭제했습니다.');
      await refreshDemosData();
      if (customerDetailData) {
        await refreshCustomerDetailData();
      }
    } catch (error) {
      setDemoError(error instanceof Error ? error.message : '데모 기록 삭제에 실패했습니다.');
    } finally {
      setDemoSaving(false);
    }
  };
  const handleDemoSort = (key: string) => {
    setDemoSort((current) => {
      if (current === key) {
        setDemoOrder((order) => (order === 'asc' ? 'desc' : 'asc'));
        return current;
      }
      setDemoOrder(key === 'account' || key === 'product' ? 'asc' : 'desc');
      return key;
    });
  };
  const refreshCustomerDetailData = async () => {
    if (!customerDetailId && !accountDetailId) {
      return null;
    }
    const data = accountDetailId
      ? await loadAccountDetailData(accountDetailId)
      : await loadCustomerDetailData(customerDetailId as number);
    setCustomerDetailData(data);
    return data;
  };
  const refreshNotesData = async () => {
    const data = await loadNotesData({
      q: noteQuery,
      dateFrom: noteDateFrom,
      dateTo: noteDateTo,
      owner: noteOwner,
      actionType: noteActionType,
      review: noteReview,
      nextAction: noteNextAction,
    });
    setNotesData(data);
  };
  const refreshNoteDetailData = async () => {
    if (!noteDetailId) {
      return null;
    }
    const data = await loadNoteDetailData(noteDetailId);
    setNoteDetailData(data);
    return data;
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
    const requestedCustomerId = getCreateCustomerParam();
    const requestedDepartmentId = getCreateDepartmentParam();
    const requestedScheduleId = getCreateScheduleParam();
    const requestedCustomer = data?.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const requestedSchedule = data?.create.schedules.find((schedule) => String(schedule.id) === requestedScheduleId);
    const requestedDepartment = data?.create.departments.find((department) => String(department.id) === requestedDepartmentId);
    const fallbackDepartmentId = requestedCustomer?.departmentId
      ?? requestedSchedule?.departmentId
      ?? requestedDepartment?.id
      ?? data?.create.customers[0]?.departmentId
      ?? data?.create.departments[0]?.id;
    nextForm.departmentId = fallbackDepartmentId ? String(fallbackDepartmentId) : '';
    const departmentCustomers = data ? customersForDepartment(data.create.customers, nextForm.departmentId) : [];
    nextForm.followupId = requestedCustomer?.id
      ? String(requestedCustomer.id)
      : requestedSchedule?.followupId
        ? String(requestedSchedule.followupId)
      : departmentCustomers[0]?.id
        ? String(departmentCustomers[0].id)
        : '';
    nextForm.scheduleId = requestedSchedule ? String(requestedSchedule.id) : '';
    if (requestedSchedule?.date) {
      nextForm.activityDate = requestedSchedule.date;
    }
    if (
      requestedSchedule?.suggestedActionType &&
      data &&
      isNoteActionAllowed(data.create.actionTypes, requestedSchedule.suggestedActionType)
    ) {
      nextForm.actionType = requestedSchedule.suggestedActionType;
    }
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
    const departmentId = Number(noteCreateForm.departmentId);
    if (!followupId && !departmentId) {
      setNoteCreateError('고객 또는 부서/연구실을 선택하세요.');
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
      departmentId: departmentId || undefined,
      followupId: followupId || undefined,
      nextAction: noteCreateForm.nextAction.trim() || undefined,
      nextActionDate: noteCreateForm.nextActionDate || undefined,
      scheduleId: noteCreateForm.scheduleId ? Number(noteCreateForm.scheduleId) : undefined,
    };

    setNoteCreating(true);
    setNoteCreateError('');
    setNoteCreateMessage('');
    try {
      const result = await createSalesNote(payload, notesData.create.submitUrl);
      const refreshedData = await loadNotesData({
        q: noteQuery,
        dateFrom: noteDateFrom,
        dateTo: noteDateTo,
        owner: noteOwner,
        actionType: noteActionType,
        review: noteReview,
        nextAction: noteNextAction,
      });
      setNotesData(refreshedData);
      resetNoteCreateForm(refreshedData);
      setNoteCreateMessage(result.message || '영업노트를 저장했습니다.');
    } catch (error) {
      setNoteCreateError(error instanceof Error ? error.message : '영업노트 저장에 실패했습니다.');
    } finally {
      setNoteCreating(false);
    }
  };
  const refreshSchedulesData = async () => {
    const data = await loadSchedulesData({
      q: scheduleQuery,
      owner: scheduleOwner,
      status: scheduleStatus,
      activityType: scheduleActivityType,
      range: scheduleRange,
    });
    setSchedulesData(data);
    return data;
  };
  const refreshScheduleDetailData = async () => {
    if (!scheduleDetailId) {
      return null;
    }
    const data = await loadScheduleDetailData(scheduleDetailId);
    setScheduleDetailData(data);
    return data;
  };
  const refreshScheduleCalendarData = async () => {
    const data = await loadScheduleCalendarData({
      start: scheduleCalendarRange.start,
      end: scheduleCalendarRange.end,
      dataFilter: scheduleCalendarDataFilter,
      filterUser: scheduleCalendarDataFilter === 'user' ? scheduleCalendarFilterUser : '',
    });
    setScheduleCalendarData(data);
    return data;
  };
  const handleScheduleCalendarMonthChange = (value: string) => {
    setScheduleCalendarStatusError('');
    setScheduleCalendarStatusMessage('');
    setScheduleCalendarMonth(value);
  };
  const handleScheduleCalendarDataFilterChange = (value: string) => {
    setScheduleCalendarStatusError('');
    setScheduleCalendarStatusMessage('');
    setScheduleCalendarDataFilter(value);
    if (value !== 'user') {
      setScheduleCalendarFilterUser('');
    }
  };
  const handleScheduleCalendarFilterUserChange = (value: string) => {
    setScheduleCalendarStatusError('');
    setScheduleCalendarStatusMessage('');
    setScheduleCalendarFilterUser(value);
  };
  const handleScheduleCalendarStatusChange = async (schedule: ScheduleItem, status: string) => {
    if (status === schedule.status) {
      return;
    }
    if (!schedule.canEdit || !schedule.statusUpdateHref) {
      setScheduleCalendarStatusError('이 일정의 상태를 변경할 권한이 없습니다.');
      setScheduleCalendarStatusMessage('');
      return;
    }

    const itemKey = `${schedule.type}-${schedule.id}`;
    setScheduleCalendarStatusUpdatingKey(itemKey);
    setScheduleCalendarStatusError('');
    setScheduleCalendarStatusMessage('');
    try {
      const result = await updateScheduleStatus(schedule.statusUpdateHref, status);
      setScheduleCalendarLoading(true);
      await refreshScheduleCalendarData();
      setScheduleCalendarStatusMessage(result.message || '일정 상태를 변경했습니다.');
    } catch (error) {
      setScheduleCalendarStatusError(error instanceof Error ? error.message : '일정 상태 변경에 실패했습니다.');
    } finally {
      setScheduleCalendarStatusUpdatingKey('');
      setScheduleCalendarLoading(false);
    }
  };
  const handleScheduleCreateOpenChange = (open: boolean) => {
    setScheduleCreateOpen(open);
    setScheduleCreateError('');
    if (open) {
      setScheduleCreateMessage('');
      setScheduleCreatedDetailHref('');
    }
  };
  const handleScheduleCreateFormChange = (field: keyof ScheduleCreateFormState, value: string) => {
    setScheduleCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setScheduleCreateError('');
  };
  const resetScheduleCreateForm = (data: SchedulesData | null) => {
    const nextForm = makeEmptyScheduleCreateForm(getCreateDateParam() || undefined);
    nextForm.activityType = data?.create.activityTypes[0]?.value || nextForm.activityType;
    const firstCustomer = data?.create.customers[0];
    const firstDepartmentId = firstCustomer?.departmentId ?? data?.create.departments[0]?.id;
    nextForm.departmentId = firstDepartmentId ? String(firstDepartmentId) : '';
    nextForm.followupId = firstCustomer?.id ? String(firstCustomer.id) : '';
    setScheduleCreateForm(nextForm);
  };
  const handleCreateScheduleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!schedulesData || scheduleCreating) {
      return;
    }
    if (!schedulesData.create.canCreate) {
      setScheduleCreateError(schedulesData.create.message || '일정 등록 권한이 없습니다.');
      return;
    }
    const followupId = Number(scheduleCreateForm.followupId);
    const departmentId = Number(scheduleCreateForm.departmentId);
    if (!followupId && !departmentId) {
      setScheduleCreateError('고객 또는 부서/연구실을 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.activityType) {
      setScheduleCreateError('일정 유형을 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.visitDate) {
      setScheduleCreateError('일정 날짜를 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.visitTime) {
      setScheduleCreateError('일정 시간을 선택하세요.');
      return;
    }
    const probability = normalizeProbabilityInputValue(scheduleCreateForm.probability);
    if (isQuoteProbabilityRequired(scheduleCreateForm.activityType) && !probability) {
      setScheduleCreateError('견적 성공 확률은 필수입니다.');
      return;
    }

    const payload: ScheduleCreatePayload = {
      activityType: scheduleCreateForm.activityType,
      departmentId: departmentId || undefined,
      expectedRevenue: scheduleCreateForm.expectedRevenue.trim() || undefined,
      followupId: followupId || undefined,
      location: scheduleCreateForm.location.trim() || undefined,
      notes: scheduleCreateForm.notes.trim() || undefined,
      probability: probability || undefined,
      visitDate: scheduleCreateForm.visitDate,
      visitTime: scheduleCreateForm.visitTime,
    };

    setScheduleCreating(true);
    setScheduleCreateError('');
    setScheduleCreateMessage('');
    setScheduleCreatedDetailHref('');
    try {
      const createdSchedule = await createCustomerSchedule(payload, schedulesData.create.submitUrl);
      const refreshedData = await refreshSchedulesData();
      resetScheduleCreateForm(refreshedData);
      setScheduleCreateMessage('일정을 등록했습니다.');
      setScheduleCreatedDetailHref(createdSchedule.href || '');
    } catch (error) {
      setScheduleCreateError(error instanceof Error ? error.message : '일정 등록에 실패했습니다.');
    } finally {
      setScheduleCreating(false);
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
  const handlePrepaymentDataFilterChange = (value: string) => {
    setPrepaymentDataFilter(value);
    if (value !== 'user') {
      setPrepaymentFilterUser('');
      return;
    }
    if (!prepaymentFilterUser) {
      const firstOwner = prepaymentsData?.options.owners[0]?.id;
      if (firstOwner) {
        setPrepaymentFilterUser(String(firstOwner));
      }
    }
  };
  const refreshDocumentsData = async () => {
    const data = await loadDocumentTemplatesData(documentTypeFilter);
    setDocumentsData(data);
    return data;
  };
  const refreshProductManagementData = async () => {
    setProductsLoading(true);
    try {
      const data = await loadProductManagementData({
        order: productOrder,
        page: productPage,
        pageSize: 50,
        q: productQuery,
        sort: productSort,
        status: productStatus,
      });
      setProductsData(data);
      return data;
    } finally {
      setProductsLoading(false);
    }
  };
  const handleDocumentTypeFilterChange = (value: string) => {
    setDocumentTypeFilter(value);
    const params = new URLSearchParams(window.location.search);
    if (value) {
      params.set('type', value);
    } else {
      params.delete('type');
    }
    const query = params.toString();
    window.history.replaceState(null, '', `/documents/${query ? `?${query}` : ''}`);
  };
  const refreshPrepaymentDetailData = async () => {
    if (!prepaymentDetailId) {
      return null;
    }
    const data = await loadPrepaymentDetailData(prepaymentDetailId);
    setPrepaymentDetailData(data);
    return data;
  };
  const handleProfileFormChange = (field: keyof ProfileFormState, value: string) => {
    setProfileForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setProfileError('');
  };
  const handleProfilePasswordFormChange = (field: keyof ProfilePasswordFormState, value: string) => {
    setProfilePasswordForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setProfileError('');
  };
  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!profileData || profileSaving) {
      return;
    }
    if (!profileForm.username.trim()) {
      setProfileError('사용자명을 입력하세요.');
      return;
    }
    const payload: ProfileUpdatePayload = {
      username: profileForm.username.trim(),
      firstName: profileForm.firstName.trim(),
      lastName: profileForm.lastName.trim(),
      email: profileForm.email.trim(),
    };
    setProfileSaving(true);
    setProfileError('');
    setProfileMessage('');
    try {
      const data = await updateProfile(payload, profileData.links.update);
      setProfileData(data);
      setProfileForm(makeProfileForm(data));
      setProfileMessage(data.message || '프로필을 저장했습니다.');
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : '프로필 저장에 실패했습니다.');
    } finally {
      setProfileSaving(false);
    }
  };
  const handleProfilePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (profilePasswordSaving) {
      return;
    }
    const payload: ProfilePasswordPayload = {
      oldPassword: profilePasswordForm.oldPassword,
      newPassword1: profilePasswordForm.newPassword1,
      newPassword2: profilePasswordForm.newPassword2,
    };
    if (!payload.oldPassword || !payload.newPassword1 || !payload.newPassword2) {
      setProfileError('현재 비밀번호와 새 비밀번호를 입력하세요.');
      return;
    }
    if (payload.newPassword1 !== payload.newPassword2) {
      setProfileError('새 비밀번호 확인이 일치하지 않습니다.');
      return;
    }
    setProfilePasswordSaving(true);
    setProfileError('');
    setProfileMessage('');
    try {
      const result = await changeProfilePassword(payload, profileData?.links.password);
      setProfilePasswordForm(makeEmptyProfilePasswordForm());
      setProfileMessage(result.message || '비밀번호를 변경했습니다.');
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : '비밀번호 변경에 실패했습니다.');
    } finally {
      setProfilePasswordSaving(false);
    }
  };

  if (currentView === 'customers') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <CustomersPage
          data={customersData}
          detailData={customerDetailData}
          detailLoading={customerDetailLoading}
          company={customerCompany}
          grade={customerGrade}
          level={customerLevel}
          loading={customersLoading}
          owner={customerOwner}
          page={customerPage}
          query={customerQuery}
          rowMode={customerRowMode}
          selectedCustomerId={customerDetailId || accountDetailId}
          selectedDetailMode={accountDetailId ? 'account' : 'customer'}
          stage={customerStage}
          onDetailRefresh={refreshCustomerDetailData}
          onCompanyFilterChange={handleCustomerCompanyFilterChange}
          onGradeChange={handleCustomerGradeChange}
          onLevelChange={handleCustomerLevelChange}
          onOwnerChange={handleCustomerOwnerChange}
          onPageChange={handleCustomerPageChange}
          onQueryChange={handleCustomerQueryChange}
          onRowModeChange={handleCustomerRowModeChange}
          onStageChange={handleCustomerStageChange}
        />
      </AppShell>
    );
  }

  if (currentView === 'companies') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <LazyPageBoundary>
          <CompanyManagementPage />
        </LazyPageBoundary>
      </AppShell>
    );
  }

  if (currentView === 'demos') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <DemoManagementPage
          data={demosData}
          editingId={demoEditingId}
          error={demoError}
          form={demoForm}
          loading={demosLoading}
          message={demoMessage}
          open={demoCreateOpen}
          order={demoOrder}
          owner={demoOwner}
          product={demoProduct}
          query={demoQuery}
          saving={demoSaving}
          sort={demoSort}
          status={demoStatus}
          onCloseForm={() => {
            setDemoCreateOpen(false);
            setDemoEditingId(null);
            setDemoError('');
          }}
          onDelete={handleDemoDelete}
          onEdit={handleDemoEdit}
          onFormChange={(updater) => {
            setDemoForm(updater);
            setDemoError('');
          }}
          onOpenCreate={() => handleDemoCreateOpen()}
          onOwnerChange={setDemoOwner}
          onProductChange={setDemoProduct}
          onQueryChange={setDemoQuery}
          onSort={handleDemoSort}
          onStatusChange={setDemoStatus}
          onSubmit={handleDemoSubmit}
        />
      </AppShell>
    );
  }

  if (currentView === 'notes') {
    if (noteDetailId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <NoteDetailPage
            data={noteDetailData}
            loading={noteDetailLoading}
            onRefresh={refreshNoteDetailData}
          />
        </AppShell>
      );
    }

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
          dateFrom={noteDateFrom}
          dateTo={noteDateTo}
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
          onDateFromChange={setNoteDateFrom}
          onDateToChange={setNoteDateTo}
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
    if (scheduleCalendarRoute) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <ScheduleCalendarPage
            data={scheduleCalendarData}
            dataFilter={scheduleCalendarDataFilter}
            filterUser={scheduleCalendarFilterUser}
            loading={scheduleCalendarLoading}
            month={scheduleCalendarMonth}
            statusError={scheduleCalendarStatusError}
            statusMessage={scheduleCalendarStatusMessage}
            statusUpdatingKey={scheduleCalendarStatusUpdatingKey}
            onDataFilterChange={handleScheduleCalendarDataFilterChange}
            onFilterUserChange={handleScheduleCalendarFilterUserChange}
            onMonthChange={handleScheduleCalendarMonthChange}
            onRefresh={refreshScheduleCalendarData}
            onStatusChange={handleScheduleCalendarStatusChange}
          />
        </AppShell>
      );
    }

    if (scheduleDetailId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <ScheduleDetailPage
            data={scheduleDetailData}
            loading={scheduleDetailLoading}
            onRefresh={refreshScheduleDetailData}
          />
        </AppShell>
      );
    }

    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <SchedulesPage
          activityType={scheduleActivityType}
          createError={scheduleCreateError}
          createForm={scheduleCreateForm}
          createdDetailHref={scheduleCreatedDetailHref}
          createMessage={scheduleCreateMessage}
          createOpen={scheduleCreateOpen}
          creating={scheduleCreating}
          data={schedulesData}
          loading={schedulesLoading}
          owner={scheduleOwner}
          query={scheduleQuery}
          range={scheduleRange}
          status={scheduleStatus}
          onActivityTypeChange={setScheduleActivityType}
          onCreateFormChange={handleScheduleCreateFormChange}
          onCreateOpenChange={handleScheduleCreateOpenChange}
          onCreateSubmit={handleCreateScheduleSubmit}
          onOwnerChange={setScheduleOwner}
          onQueryChange={setScheduleQuery}
          onRangeChange={setScheduleRange}
          onStatusChange={setScheduleStatus}
        />
      </AppShell>
    );
  }

  if (currentView === 'employees') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <EmployeesPage
          company={employeeCompany}
          data={employeesData}
          loading={employeesLoading}
          query={employeeQuery}
          role={employeeRole}
          status={employeeStatus}
          onCompanyChange={setEmployeeCompany}
          onQueryChange={setEmployeeQuery}
          onRefresh={refreshEmployeesData}
          onRoleChange={setEmployeeRole}
          onStatusChange={setEmployeeStatus}
        />
      </AppShell>
    );
  }

  if (currentView === 'documents') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <DocumentsPage
          data={documentsData}
          loading={documentsLoading}
          onReload={refreshDocumentsData}
          onTypeChange={handleDocumentTypeFilterChange}
          routeData={pipelineData}
          selectedType={documentTypeFilter}
        />
      </AppShell>
    );
  }

  if (currentView === 'products') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <ProductManagementPage
          data={productsData}
          loading={productsLoading}
          onOrderChange={setProductOrder}
          onPageChange={setProductPage}
          onQueryChange={setProductQuery}
          onReload={refreshProductManagementData}
          onSortChange={setProductSort}
          onStatusChange={setProductStatus}
          order={productOrder}
          page={productPage}
          query={productQuery}
          routeData={pipelineData}
          sort={productSort}
          status={productStatus}
        />
      </AppShell>
    );
  }

  if (currentView === 'pipelineSheet') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <LazyPageBoundary>
          <PipelineSheetPage />
        </LazyPageBoundary>
      </AppShell>
    );
  }

  if (currentView === 'revenue') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <LazyPageBoundary>
          <RevenueDetailPage />
        </LazyPageBoundary>
      </AppShell>
    );
  }

  if (currentView === 'receivables') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <LazyPageBoundary>
          <ReceivablesPage />
        </LazyPageBoundary>
      </AppShell>
    );
  }

  if (currentView === 'prepayments') {
    if (prepaymentCreateRoute) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <PrepaymentCreatePage
            data={prepaymentCreateData}
            loading={prepaymentCreateLoading}
          />
        </AppShell>
      );
    }

    if (prepaymentAccountId || prepaymentCustomerId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <PrepaymentCustomerPage
            data={prepaymentCustomerData}
            loading={prepaymentCustomerLoading}
            selectedUser={prepaymentCustomerUser}
            onSelectedUserChange={setPrepaymentCustomerUser}
          />
        </AppShell>
      );
    }

    if (prepaymentDetailId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <PrepaymentDetailPage
            data={prepaymentDetailData}
            editRoute={prepaymentEditRoute}
            loading={prepaymentDetailLoading}
            onRefresh={refreshPrepaymentDetailData}
          />
        </AppShell>
      );
    }

    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <PrepaymentsPage
          data={prepaymentsData}
          dataFilter={prepaymentDataFilter}
          filterUser={prepaymentFilterUser}
          loading={prepaymentsLoading}
          query={prepaymentQuery}
          status={prepaymentStatus}
          onDataFilterChange={handlePrepaymentDataFilterChange}
          onFilterUserChange={setPrepaymentFilterUser}
          onQueryChange={setPrepaymentQuery}
          onStatusChange={setPrepaymentStatus}
        />
      </AppShell>
    );
  }

  if (currentView === 'profile') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <ProfileSettingsPage
          data={profileData}
          error={profileError}
          form={profileForm}
          loading={profileLoading}
          message={profileMessage}
          passwordForm={profilePasswordForm}
          passwordSaving={profilePasswordSaving}
          saving={profileSaving}
          onFormChange={handleProfileFormChange}
          onPasswordFormChange={handleProfilePasswordFormChange}
          onPasswordSubmit={handleProfilePasswordSubmit}
          onSubmit={handleProfileSubmit}
        />
      </AppShell>
    );
  }

  if (legacyFallbackViews.includes(currentView)) {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <LegacyFallbackRoutePage view={currentView} />
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

  if (pipelineLoading && pipelineData.source !== 'django') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <section className="dashboard-loading">
          <Loader2 className="spin-icon" size={24} />
          <span>파이프라인 데이터를 불러오는 중입니다</span>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell activeView={currentView}>
      <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
      <MetricStrip data={pipelineData} />
      <div className={`content-grid pipeline-content-grid ${pipelineDetailCollapsed ? 'detail-collapsed' : ''}`}>
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
            <div className="pipeline-toolbar-actions">
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
              <button
                aria-label={pipelineDetailCollapsed ? '선택 고객 패널 펼치기' : '선택 고객 패널 접기'}
                aria-pressed={pipelineDetailCollapsed}
                className="icon-button pipeline-detail-toggle"
                onClick={() => setPipelineDetailCollapsed((collapsed) => !collapsed)}
                title={pipelineDetailCollapsed ? '선택 고객 패널 펼치기' : '선택 고객 패널 접기'}
                type="button"
              >
                {pipelineDetailCollapsed ? <PanelRightOpen size={18} /> : <PanelRightClose size={18} />}
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
          {pipelineData.hiddenDeals && pipelineData.hiddenDeals.length > 0 ? (
            <HiddenCardsPanel
              hidden={pipelineData.hiddenDeals}
              onRestore={handleRestoreDeal}
              restoringId={restoringDealId}
              disabled={pipelineData.source !== 'django'}
            />
          ) : null}
        </section>
        {pipelineDetailCollapsed ? null : (
          <DetailPanel
            deal={visibleSelectedDeal}
            stages={pipelineData.stages}
            canMove={pipelineData.source === 'django'}
            moving={Boolean(visibleSelectedDeal && movingDealId === visibleSelectedDeal.id)}
            moveError={moveError}
            moveMessage={moveMessage}
            onMoveStage={handleMoveStage}
            onRemoveDeal={handleRemoveDeal}
            removing={Boolean(visibleSelectedDeal && removingDealId === visibleSelectedDeal.id)}
            removeError={removeError}
            removeMessage={removeMessage}
            probabilitySaving={Boolean(visibleSelectedDeal && probabilityDealId === visibleSelectedDeal.id)}
            probabilityError={probabilityError}
            probabilityMessage={probabilityMessage}
            onUpdateProbability={handleUpdateProbability}
            duplicating={Boolean(visibleSelectedDeal && duplicatingDealId === visibleSelectedDeal.id)}
            duplicateError={duplicateError}
            duplicateMessage={duplicateMessage}
            onDuplicateDeal={handleDuplicateDeal}
          />
        )}
      </div>
    </AppShell>
  );
}
