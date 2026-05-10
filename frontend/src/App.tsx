import {
  Activity,
  AlertTriangle,
  Archive,
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
  LogOut,
  Loader2,
  Inbox,
  Mail,
  MessageSquareText,
  MoveUpRight,
  ArrowRightLeft,
  PanelRight,
  Plus,
  RefreshCw,
  Reply,
  Search,
  Send,
  Sparkles,
  Star,
  Target,
  Trash2,
  Upload,
  Users,
  X,
} from 'lucide-react';
import { type ChangeEvent, type FormEvent, type KeyboardEvent, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  DashboardData,
  DashboardHistoryItem,
  DashboardScheduleItem,
  CustomerDetailData,
  CustomerAiDepartment,
  CustomerAiPainpoint,
  CustomerEditPayload,
  CustomerCreatePayload,
  CustomersData,
  CustomerItem,
  MailboxData,
  MailboxEmailItem,
  MailboxSendPayload,
  MailboxThreadData,
  MailboxType,
  NotesData,
  NoteDetailData,
  NoteDetailItem,
  NoteEditPayload,
  NoteFileItem,
  NoteItem,
  NoteReplyItem,
  PrepaymentCreateData,
  PrepaymentCustomerData,
  PrepaymentDetailData,
  PrepaymentFormPayload,
  PrepaymentsData,
  PrepaymentOption,
  ProductOption,
  SchedulesData,
  ScheduleDetailData,
  ScheduleDetailItem,
  ScheduleDeliveryItem,
  ScheduleDeliveryItemPayload,
  ScheduleFileItem,
  ScheduleEditPayload,
  ScheduleItem,
  AIWorkspaceData,
  AIWorkspaceDepartment,
  AIWorkspaceFollowupTarget,
  AIWorkspacePainpoint,
  AIWorkspacePromptTarget,
  WeeklyReportCreateData,
  WeeklyReportDetailData,
  WeeklyReportFormPayload,
  WeeklyReportsData,
  WeeklyReportSchedulesData,
  NoteCreatePayload,
  addNoteReply,
  cancelPrepayment as cancelCustomerPrepayment,
  createCompany as createCompanyRecord,
  createDepartment as createDepartmentRecord,
  createNote as createSalesNote,
  createPrepayment as createCustomerPrepayment,
  ScheduleCreatePayload,
  createCustomer as createCustomerRecord,
  deletePrepayment as deleteCustomerPrepayment,
  createSchedule as createCustomerSchedule,
  deleteNoteFile,
  deleteNoteReply,
  deleteScheduleFile,
  deleteWeeklyReport,
  generateWeeklyReportAiDraft,
  loadDashboardData,
  loadCustomerDetailData,
  loadCustomersData,
  loadMailboxData,
  loadMailboxThreadData,
  loadNoteDetailData,
  loadNotesData,
  loadPrepaymentCreateData,
  loadPrepaymentCustomerData,
  loadPrepaymentDetailData,
  loadPrepayments,
  loadPrepaymentsData,
  loadProducts,
  loadScheduleDetailData,
  loadSchedulesData,
  loadAIWorkspaceData,
  loadWeeklyReportCreateData,
  loadWeeklyReportDetailData,
  loadWeeklyReportsData,
  loadWeeklyReportSchedules,
  loadPipelineData,
  moveDealStage,
  runAiDepartmentAnalysis,
  runMailboxAction,
  runMailboxSync,
  sendMailboxEmail,
  toggleNoteReviewed,
  transferPrepayment as transferCustomerPrepayment,
  updateCustomer as updateCustomerRecord,
  updateNote as updateSalesNote,
  updatePrepayment as updateCustomerPrepayment,
  updateSchedule as updateCustomerSchedule,
  updateScheduleDeliveryItems,
  uploadNoteFiles,
  uploadScheduleFiles,
  verifyAiPainpoint,
  replyMailboxEmail,
  saveWeeklyReport,
  saveWeeklyReportManagerComment,
} from './api';
import { Deal, mockPipelineData, PipelineData, PipelineStage, PriorityTask, StageSummary } from './mockData';

const navItems = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/' },
  { id: 'mail', label: '메일', icon: Mail, href: '/mailbox/' },
  { id: 'weeklyReports', label: '주간보고', icon: ListChecks, href: '/weekly-reports/' },
  { id: 'prepayments', label: '선결제', icon: CircleDollarSign, href: '/prepayments/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

const scheduleCalendarUrl = '/reporting/schedules/calendar/';

type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';
type MainView = 'dashboard' | 'customers' | 'pipeline' | 'notes' | 'schedules' | 'mail' | 'weeklyReports' | 'prepayments' | 'ai';

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

type NoteEditFormState = NoteCreateFormState & {
  deliveryAmount: string;
  deliveryItems: string;
  meetingConfirmedFacts: string;
  meetingNextAction: string;
  meetingObstacles: string;
  meetingResearcherQuote: string;
  meetingSituation: string;
  serviceStatus: string;
};

type ScheduleCreateFormState = {
  activityType: string;
  expectedRevenue: string;
  followupId: string;
  location: string;
  notes: string;
  probability: string;
  visitDate: string;
  visitTime: string;
};

type ScheduleEditFormState = ScheduleCreateFormState & {
  expectedCloseDate: string;
  purchaseConfirmed: boolean;
  status: string;
  usePrepayment: boolean;
};

type SchedulePrepaymentEditRow = PrepaymentOption & {
  selected: boolean;
  amountInput: string;
};

type PrepaymentFormState = {
  amount: string;
  balance: string;
  customerId: string;
  memo: string;
  payerName: string;
  paymentDate: string;
  paymentMethod: string;
  status: string;
};

type ScheduleDeliveryEditRow = {
  rowId: string;
  id?: number;
  productId: string;
  productQuery: string;
  itemName: string;
  quantity: string;
  unit: string;
  unitPrice: string;
  taxInvoiceIssued: boolean;
  notes: string;
};

type ScheduleDeliveryEditField = 'productId' | 'productQuery' | 'itemName' | 'quantity' | 'unit' | 'unitPrice' | 'taxInvoiceIssued' | 'notes';

type MailComposeFormState = {
  bodyText: string;
  businessCardId: string;
  ccEmails: string;
  bccEmails: string;
  followupId: string;
  subject: string;
  toEmail: string;
};

type CustomerCreateFormState = {
  address: string;
  companyId: string;
  customerName: string;
  departmentId: string;
  email: string;
  manager: string;
  notes: string;
  phoneNumber: string;
  priority: string;
};

type CustomerEditFormState = {
  address: string;
  companyId: string;
  customerName: string;
  departmentId: string;
  email: string;
  manager: string;
  notes: string;
  phoneNumber: string;
  pipelineStage: string;
  priority: string;
  status: string;
};

type SearchableSelectOption = {
  value: string;
  label: string;
  meta?: string;
  searchText?: string;
};

type CustomerSelectSource = {
  id: number;
  label?: string;
  customer?: string;
  customerName?: string;
  company?: string;
  companyName?: string;
  department?: string;
  departmentName?: string;
  email?: string;
  ownerName?: string;
  priorityLabel?: string;
};

const localDateInputValue = (date = new Date()) => {
  const localTime = date.getTime() - date.getTimezoneOffset() * 60_000;
  return new Date(localTime).toISOString().slice(0, 10);
};

const shouldOpenCreatePanel = () => new URLSearchParams(window.location.search).get('create') === '1';

const makeEmptyWeeklyReportForm = (): WeeklyReportFormPayload => ({
  weekStart: '',
  weekEnd: '',
  title: '',
  activityNotes: '',
  quoteDeliveryNotes: '',
  otherNotes: '',
});

const makeEmptyNoteCreateForm = (): NoteCreateFormState => ({
  actionType: 'customer_meeting',
  activityDate: localDateInputValue(),
  content: '',
  followupId: '',
  nextAction: '',
  nextActionDate: '',
});

const makeNoteEditForm = (note: NoteDetailItem | null): NoteEditFormState => ({
  actionType: note?.actionType || 'customer_meeting',
  activityDate: note?.meetingDate || note?.deliveryDate || note?.activityDate || '',
  content: note?.content || '',
  deliveryAmount: note?.deliveryAmount ? String(note.deliveryAmount) : '',
  deliveryItems: note?.deliveryItems || '',
  followupId: note?.followupId ? String(note.followupId) : '',
  meetingConfirmedFacts: note?.meetingConfirmedFacts || '',
  meetingNextAction: note?.meetingNextAction || '',
  meetingObstacles: note?.meetingObstacles || '',
  meetingResearcherQuote: note?.meetingResearcherQuote || '',
  meetingSituation: note?.meetingSituation || '',
  nextAction: note?.nextAction || '',
  nextActionDate: note?.nextActionDate || '',
  serviceStatus: note?.serviceStatus || 'received',
});

const makeEmptyScheduleCreateForm = (): ScheduleCreateFormState => ({
  activityType: 'customer_meeting',
  expectedRevenue: '',
  followupId: '',
  location: '',
  notes: '',
  probability: '',
  visitDate: localDateInputValue(),
  visitTime: '09:00',
});

const makeScheduleEditForm = (schedule: ScheduleDetailItem | null): ScheduleEditFormState => ({
  activityType: schedule?.activityType || 'customer_meeting',
  expectedCloseDate: schedule?.expectedCloseDate || '',
  expectedRevenue: schedule?.expectedRevenue ? String(schedule.expectedRevenue) : '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  location: schedule?.location || '',
  notes: schedule?.notesFull || schedule?.notes || '',
  probability: schedule?.probability ? String(schedule.probability) : '',
  purchaseConfirmed: Boolean(schedule?.purchaseConfirmed),
  status: schedule?.status || 'scheduled',
  usePrepayment: Boolean(schedule?.usePrepayment),
  visitDate: schedule?.date || '',
  visitTime: schedule?.time || '09:00',
});

const makeSchedulePrepaymentRows = (options: PrepaymentOption[] = []): SchedulePrepaymentEditRow[] => (
  options.map((option) => ({
    ...option,
    selected: option.selectedAmount > 0,
    amountInput: option.selectedAmount > 0 ? String(option.selectedAmount) : '',
  }))
);

const makeEmptyPrepaymentForm = (): PrepaymentFormState => ({
  amount: '',
  balance: '',
  customerId: '',
  memo: '',
  payerName: '',
  paymentDate: localDateInputValue(),
  paymentMethod: 'transfer',
  status: 'active',
});

const makePrepaymentEditForm = (prepayment: PrepaymentDetailData['prepayment'] | null): PrepaymentFormState => ({
  amount: prepayment ? String(prepayment.amount) : '',
  balance: prepayment ? String(prepayment.balance) : '',
  customerId: prepayment?.customerId ? String(prepayment.customerId) : '',
  memo: prepayment?.memo || '',
  payerName: prepayment?.payerName || '',
  paymentDate: prepayment?.paymentDate || localDateInputValue(),
  paymentMethod: prepayment?.paymentMethod || 'transfer',
  status: prepayment?.status || 'active',
});

const makeScheduleDeliveryEditRow = (item?: ScheduleDeliveryItem, index = 0): ScheduleDeliveryEditRow => ({
  rowId: item ? `delivery-${item.id}` : `delivery-new-${Date.now()}-${index}`,
  id: item?.id,
  productId: item?.productId ? String(item.productId) : '',
  productQuery: item?.productCode || '',
  itemName: item?.itemName || '',
  quantity: item ? String(item.quantity) : '1',
  unit: item?.unit || 'EA',
  unitPrice: item && item.unitPrice !== undefined && item.unitPrice !== null ? String(item.unitPrice) : '',
  taxInvoiceIssued: Boolean(item?.taxInvoiceIssued),
  notes: item?.notes || '',
});

const makeScheduleDeliveryEditRows = (items: ScheduleDeliveryItem[] = []): ScheduleDeliveryEditRow[] => (
  items.length > 0
    ? items.map((item, index) => makeScheduleDeliveryEditRow(item, index))
    : [makeScheduleDeliveryEditRow(undefined, 0)]
);

const makeEmptyMailComposeForm = (): MailComposeFormState => ({
  bodyText: '',
  businessCardId: '',
  ccEmails: '',
  bccEmails: '',
  followupId: '',
  subject: '',
  toEmail: '',
});

const makeEmptyCustomerCreateForm = (): CustomerCreateFormState => ({
  address: '',
  companyId: '',
  customerName: '',
  departmentId: '',
  email: '',
  manager: '',
  notes: '',
  phoneNumber: '',
  priority: 'scheduled',
});

const makeCustomerEditForm = (customer: CustomerItem | null): CustomerEditFormState => ({
  address: customer?.address || '',
  companyId: customer?.companyId ? String(customer.companyId) : '',
  customerName: customer?.customer || '',
  departmentId: customer?.departmentId ? String(customer.departmentId) : '',
  email: customer?.email || '',
  manager: customer?.manager || '',
  notes: customer?.notesFull || customer?.notes || '',
  phoneNumber: customer?.phone || '',
  pipelineStage: customer?.pipelineStage || 'potential',
  priority: customer?.priority || 'scheduled',
  status: customer?.status || 'active',
});

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
      { label: '새 고객 등록', href: '/customers/?create=1', primary: true },
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
      { label: '주간보고', href: '/weekly-reports/' },
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
      { label: '이번 주 보고', href: '/weekly-reports/' },
    ],
  },
  mail: {
    eyebrow: 'Sales CRM / Mailbox',
    title: '메일',
    summary: '고객과 주고받은 메일을 고객 기록, AI 판단 근거와 함께 관리합니다.',
    primaryHref: '/mailbox/',
    primaryLabel: '프론트 메일함 보기',
    actions: [
      { label: '메일 작성', href: '/mailbox/?compose=1', primary: true },
      { label: '받은편지함', href: '/mailbox/?box=inbox' },
      { label: 'Django 메일함', href: '/reporting/mailbox/inbox/' },
    ],
  },
  weeklyReports: {
    eyebrow: 'Sales CRM / Weekly Reports',
    title: '주간보고',
    summary: '이번 주 영업활동, 견적/납품, 기타 메모를 보고서로 정리하고 검토합니다.',
    primaryHref: '/weekly-reports/new/',
    primaryLabel: '주간보고 작성',
    actions: [
      { label: '보고서 작성', href: '/weekly-reports/new/', primary: true },
      { label: 'Django 주간보고', href: '/reporting/weekly-reports/' },
      { label: '영업노트', href: '/notes/' },
    ],
  },
  prepayments: {
    eyebrow: 'Sales CRM / Prepayments',
    title: '선결제',
    summary: '고객별 선결제 입금, 잔액, 사용 현황을 React CRM에서 빠르게 확인합니다.',
    primaryHref: '/prepayments/',
    primaryLabel: '프론트 선결제 보기',
    actions: [
      { label: '선결제 등록', href: '/prepayments/new/', primary: true },
      { label: 'Django 선결제 관리', href: '/reporting/prepayment/' },
      { label: '엑셀 다운로드', href: '/reporting/prepayment/excel/' },
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
  if (pathname.startsWith('/mailbox/')) return 'mail';
  if (pathname.startsWith('/weekly-reports/')) return 'weeklyReports';
  if (pathname.startsWith('/prepayments/')) return 'prepayments';
  if (pathname.startsWith('/ai-workspace/')) return 'ai';
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

function getMailboxThreadId(): string {
  const match = window.location.pathname.match(/^\/mailbox\/thread\/(.+?)\/?$/);
  return match ? decodeURIComponent(match[1]) : '';
}

function getMailboxTypeParam(): MailboxType {
  const value = new URLSearchParams(window.location.search).get('box');
  if (value === 'sent' || value === 'starred' || value === 'archived' || value === 'trash') {
    return value;
  }
  return 'inbox';
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

function isPrepaymentCreateRoute(): boolean {
  return /^\/prepayments\/new\/?$/.test(window.location.pathname);
}

function isPrepaymentEditRoute(): boolean {
  return /^\/prepayments\/\d+\/edit\/?$/.test(window.location.pathname);
}

function getWeeklyReportDetailId(): number | null {
  const match = window.location.pathname.match(/^\/weekly-reports\/(\d+)\/(?:edit\/?)?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function isWeeklyReportCreateRoute(): boolean {
  return /^\/weekly-reports\/new\/?$/.test(window.location.pathname);
}

function isWeeklyReportEditRoute(): boolean {
  return /^\/weekly-reports\/\d+\/edit\/?$/.test(window.location.pathname);
}

function getCreateCustomerParam(): string {
  return new URLSearchParams(window.location.search).get('customer') || '';
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

const searchableOptionLimit = 80;

const joinOptionParts = (parts: Array<string | undefined>) => parts.filter(Boolean).join(' · ');

function normalizeOptionText(value: string): string {
  return value.trim().toLocaleLowerCase('ko-KR');
}

function makeCompanySelectOption(company: { id: number; name: string }): SearchableSelectOption {
  return {
    value: String(company.id),
    label: company.name,
    searchText: company.name,
  };
}

function makeDepartmentSelectOption(department: { id: number; name: string; companyName?: string }): SearchableSelectOption {
  const label = joinOptionParts([department.companyName, department.name]) || department.name;
  return {
    value: String(department.id),
    label,
    searchText: label,
  };
}

function makeCustomerSelectOption(customer: CustomerSelectSource): SearchableSelectOption {
  const label = customer.label || joinOptionParts([
    customer.company || customer.companyName,
    customer.department || customer.departmentName,
    customer.customer || customer.customerName,
  ]) || `고객 #${customer.id}`;
  const meta = joinOptionParts([customer.email, customer.ownerName, customer.priorityLabel]);
  return {
    value: String(customer.id),
    label,
    meta,
    searchText: [
      label,
      customer.company,
      customer.companyName,
      customer.department,
      customer.departmentName,
      customer.customer,
      customer.customerName,
      customer.email,
      customer.ownerName,
      customer.priorityLabel,
    ].filter(Boolean).join(' '),
  };
}

function SearchableSelect({
  allowEmpty = false,
  ariaLabel,
  className = '',
  disabled = false,
  emptyLabel = '선택 없음',
  onChange,
  options,
  placeholder = '검색해서 선택',
  value,
}: {
  allowEmpty?: boolean;
  ariaLabel: string;
  className?: string;
  disabled?: boolean;
  emptyLabel?: string;
  onChange: (value: string) => void;
  options: SearchableSelectOption[];
  placeholder?: string;
  value: string;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const selectedOption = options.find((option) => option.value === value);
  const allOptions = useMemo(
    () => (allowEmpty ? [{ value: '', label: emptyLabel, searchText: emptyLabel }, ...options] : options),
    [allowEmpty, emptyLabel, options],
  );
  const filteredOptions = useMemo(() => {
    const normalizedQuery = normalizeOptionText(query);
    const matches = normalizedQuery
      ? allOptions.filter((option) => normalizeOptionText(`${option.label} ${option.meta || ''} ${option.searchText || ''}`).includes(normalizedQuery))
      : allOptions;
    return matches.slice(0, searchableOptionLimit);
  }, [allOptions, query]);
  const inputValue = open ? query : selectedOption?.label || (!value && allowEmpty ? emptyLabel : '');

  useEffect(() => {
    setActiveIndex(0);
  }, [query, filteredOptions.length]);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!containerRef.current || containerRef.current.contains(event.target as Node)) {
        return;
      }
      setOpen(false);
      setQuery('');
    };
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  const handleSelect = (nextValue: string) => {
    onChange(nextValue);
    setOpen(false);
    setQuery('');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, Math.max(filteredOptions.length - 1, 0)));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.max(index - 1, 0));
      return;
    }
    if (event.key === 'Enter' && open) {
      event.preventDefault();
      const activeOption = filteredOptions[activeIndex];
      if (activeOption) {
        handleSelect(activeOption.value);
      }
      return;
    }
    if (event.key === 'Escape') {
      setOpen(false);
      setQuery('');
    }
  };

  return (
    <div
      className={`searchable-select ${open ? 'open' : ''} ${disabled ? 'disabled' : ''} ${className}`.trim()}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setOpen(false);
          setQuery('');
        }
      }}
      ref={containerRef}
    >
      <div aria-expanded={open} aria-haspopup="listbox" className="searchable-select-control" role="combobox">
        <Search size={15} />
        <input
          aria-autocomplete="list"
          aria-label={ariaLabel}
          className="searchable-select-input"
          disabled={disabled}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            setQuery('');
            setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          value={inputValue}
        />
        {allowEmpty && value ? (
          <button
            aria-label={`${ariaLabel} 선택 해제`}
            className="searchable-select-clear"
            disabled={disabled}
            onMouseDown={(event) => {
              event.preventDefault();
              handleSelect('');
            }}
            type="button"
          >
            <X size={14} />
          </button>
        ) : null}
        <button
          aria-label={`${ariaLabel} 목록 열기`}
          className="searchable-select-toggle"
          disabled={disabled}
          onMouseDown={(event) => {
            event.preventDefault();
            setOpen((current) => !current);
            setQuery('');
          }}
          type="button"
        >
          <ChevronDown size={15} />
        </button>
      </div>
      {open && !disabled ? (
        <div className="searchable-select-menu" role="listbox">
          {filteredOptions.length > 0 ? (
            filteredOptions.map((option, index) => (
              <button
                aria-selected={option.value === value}
                className={`searchable-select-option ${index === activeIndex ? 'active' : ''} ${option.value === value ? 'selected' : ''}`.trim()}
                key={`${option.value}-${option.label}`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  handleSelect(option.value);
                }}
                onMouseEnter={() => setActiveIndex(index)}
                role="option"
                type="button"
              >
                <span>{option.label}</span>
                {option.meta ? <small>{option.meta}</small> : null}
              </button>
            ))
          ) : (
            <div className="searchable-select-empty">검색 결과 없음</div>
          )}
        </div>
      ) : null}
    </div>
  );
}

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
        <button className="logout-button" onClick={handleLogout} type="button">
          <LogOut size={17} />
          로그아웃
        </button>
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
        <a className={`customers-priority-row ${customer.overdue ? 'overdue' : ''}`} href={`/customers/${customer.id}/`} key={customer.id}>
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
                <a className="customer-name-link" href={`/customers/${customer.id}/`}>
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

function CustomerDetailNoteList({
  emptyLabel,
  notes,
  urgent,
}: {
  emptyLabel: string;
  notes: NoteItem[];
  urgent?: boolean;
}) {
  if (notes.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="dashboard-list customer-detail-note-list">
      {notes.map((note) => (
        <a className={`dashboard-list-row ${urgent || note.overdue ? 'urgent' : ''}`} href={note.href} key={note.id}>
          <div className="dashboard-row-icon">
            {urgent || note.overdue ? <AlertTriangle size={17} /> : <FileText size={17} />}
          </div>
          <div className="dashboard-row-main">
            <strong>{note.actionLabel}</strong>
            <span>{[note.owner, note.serviceStatusLabel].filter(Boolean).join(' · ')}</span>
            <small>{note.nextAction || note.summary || '내용 없음'}</small>
          </div>
          <time>{note.nextActionDate ? formatDateLabel(note.nextActionDate) : formatDateTimeLabel(note.createdAt)}</time>
        </a>
      ))}
    </div>
  );
}

function CustomerAiResultPanel({
  aiDepartment,
  verificationNotes,
  verifyingId,
  onNoteChange,
  onVerify,
}: {
  aiDepartment: CustomerAiDepartment;
  verificationNotes: Record<number, string>;
  verifyingId: number | null;
  onNoteChange: (cardId: number, value: string) => void;
  onVerify: (card: CustomerAiPainpoint, status: 'confirmed' | 'denied') => void;
}) {
  const quoteDelivery = aiDepartment.quoteDelivery;
  const quoteInsights = aiDepartment.quoteInsights;
  const missingInfo = aiDepartment.missingInfo;
  const periodLabel = [aiDepartment.periodStart, aiDepartment.periodEnd]
    .filter(Boolean)
    .map((value) => formatDateLabel(value))
    .join(' - ');
  const quoteInsightItems = [
    { label: '전환율 분석', value: quoteInsights.conversionAnalysis },
    { label: '납품 주기', value: quoteInsights.deliveryCycle },
    { label: '제품 트렌드', value: quoteInsights.productTrends },
  ].filter((item) => item.value);
  const hasQuoteMetrics = quoteDelivery.totalQuotes > 0 || quoteDelivery.totalDeliveries > 0;

  return (
    <div className="customer-ai-result">
      <div className="customer-ai-result-meta">
        {periodLabel ? <span>{periodLabel}</span> : null}
        {aiDepartment.updatedAt ? <span>{formatDateTimeLabel(aiDepartment.updatedAt)}</span> : null}
        {aiDepartment.tokenUsage > 0 ? <span>토큰 {formatNumber(aiDepartment.tokenUsage)}</span> : null}
      </div>

      {aiDepartment.meetingInsights.length > 0 ? (
        <section className="customer-ai-section">
          <h4>미팅 인사이트</h4>
          <div className="customer-ai-insight-list">
            {aiDepartment.meetingInsights.map((insight) => (
              <article key={`${insight.theme}-${insight.frequency}`}>
                <strong>{insight.theme}</strong>
                {insight.details ? <p>{insight.details}</p> : null}
                {insight.frequency ? <small>{insight.frequency}</small> : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {hasQuoteMetrics || quoteInsightItems.length > 0 ? (
        <section className="customer-ai-section">
          <h4>견적/납품 분석</h4>
          {hasQuoteMetrics ? (
            <div className="customer-ai-quote-grid">
              <span>견적 <strong>{formatNumber(quoteDelivery.totalQuotes)}</strong></span>
              <span>전환 <strong>{formatNumber(quoteDelivery.convertedQuotes)}</strong></span>
              <span>전환율 <strong>{quoteDelivery.conversionRate}%</strong></span>
              <span>납품 <strong>{formatNumber(quoteDelivery.totalDeliveries)}</strong></span>
            </div>
          ) : null}
          {quoteInsightItems.length > 0 ? (
            <div className="customer-ai-text-list">
              {quoteInsightItems.map((item) => (
                <div key={item.label}>
                  <strong>{item.label}</strong>
                  <p>{item.value}</p>
                </div>
              ))}
            </div>
          ) : null}
          {quoteDelivery.productStats.length > 0 ? (
            <div className="customer-ai-product-list">
              {quoteDelivery.productStats.slice(0, 4).map((product) => (
                <div key={product.name}>
                  <strong>{product.name}</strong>
                  <span>견적 {formatNumber(product.quoted)}회 · 납품 {formatNumber(product.delivered)}회</span>
                  <small>{formatWon(product.quoteAmount)} / {formatWon(product.deliveryAmount)}</small>
                </div>
              ))}
            </div>
          ) : null}
          {quoteInsights.stalledQuotes.length > 0 ? (
            <div className="customer-ai-stalled-list">
              {quoteInsights.stalledQuotes.map((quote) => (
                <div key={`${quote.quoteInfo}-${quote.suggestion}`}>
                  <strong>{quote.quoteInfo}</strong>
                  {quote.possibleReason ? <span>원인: {quote.possibleReason}</span> : null}
                  {quote.suggestion ? <small>{quote.suggestion}</small> : null}
                </div>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {aiDepartment.verificationInsights.length > 0 ? (
        <section className="customer-ai-section">
          <h4>검증 기반 인사이트</h4>
          <div className="customer-ai-verification-list">
            {aiDepartment.verificationInsights.map((insight) => (
              <article
                className={insight.status || 'memory'}
                key={`${insight.hypothesis}-${insight.previousQuestion}-${insight.nextVerification}`}
              >
                <div className="customer-ai-verification-head">
                  <span>{insight.statusLabel || insight.status || '검증 메모리'}</span>
                  {insight.verifiedAt ? <small>{formatDateTimeLabel(insight.verifiedAt)}</small> : null}
                </div>
                <strong>{insight.insight || insight.hypothesis}</strong>
                {insight.impact ? <p>{insight.impact}</p> : null}
                {insight.previousQuestion ? <small>기존 질문: {insight.previousQuestion}</small> : null}
                {insight.nextVerification ? <small>다음 검증: {insight.nextVerification}</small> : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {aiDepartment.nextActions.length > 0 ? (
        <section className="customer-ai-section">
          <h4>추천 액션</h4>
          <div className="customer-ai-action-list">
            {aiDepartment.nextActions.map((action) => (
              <div key={`${action.action}-${action.reason}`}>
                <span className={`customer-ai-priority ${action.priority || 'low'}`}>{action.priority || 'low'}</span>
                <div>
                  <strong>{action.action}</strong>
                  {action.reason ? <small>{action.reason}</small> : null}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {missingInfo.items.length > 0 || missingInfo.questions.length > 0 ? (
        <section className="customer-ai-section">
          <h4>확인 필요</h4>
          <div className="customer-ai-check-list">
            {missingInfo.items.map((item) => (
              <span key={`item-${item}`}>{item}</span>
            ))}
            {missingInfo.questions.map((question) => (
              <span key={`question-${question}`}>{question}</span>
            ))}
          </div>
        </section>
      ) : null}

      <section className="customer-ai-section">
        <div className="customer-ai-section-heading">
          <h4>PainPoint 검증</h4>
          <span>미검증 {formatNumber(aiDepartment.unverifiedPainpointCount)}건</span>
        </div>
        {aiDepartment.painpoints.length === 0 ? (
          <DashboardEmpty label="PainPoint 카드가 없습니다" />
        ) : (
          <div className="customer-ai-painpoint-list">
            {aiDepartment.painpoints.map((card) => (
              <article className={`customer-ai-painpoint ${card.verificationStatus}`} key={card.id}>
                <div className="customer-ai-painpoint-head">
                  <span>{card.categoryLabel}</span>
                  <strong>{card.confidenceLabel} {card.confidenceScore}</strong>
                </div>
                <h5>{card.hypothesis}</h5>
                {card.evidence.length > 0 ? (
                  <div className="customer-ai-evidence-list">
                    {card.evidence.map((evidence) => (
                      <p key={`${card.id}-${evidence.text}-${evidence.sourceSection}`}>
                        <strong>{evidence.typeLabel}</strong>
                        {evidence.text}
                        {evidence.sourceSection ? <small>{evidence.sourceSection}</small> : null}
                      </p>
                    ))}
                  </div>
                ) : null}
                {card.verificationQuestion ? (
                  <div className="customer-ai-question">
                    <strong>검증 질문</strong>
                    <span>{card.verificationQuestion}</span>
                  </div>
                ) : null}
                <details className="customer-ai-response-detail">
                  <summary>대응 패키지</summary>
                  {card.actionIfYes ? <p><strong>맞으면</strong>{card.actionIfYes}</p> : null}
                  {card.actionIfNo ? <p><strong>아니면</strong>{card.actionIfNo}</p> : null}
                  {card.caution ? <p><strong>주의</strong>{card.caution}</p> : null}
                </details>
                {card.canVerify ? (
                  <div className="customer-ai-verify-box">
                    <textarea
                      onChange={(event) => onNoteChange(card.id, event.target.value)}
                      placeholder="검증 메모"
                      rows={2}
                      value={verificationNotes[card.id] || ''}
                    />
                    <div>
                      <button
                        className="route-secondary-action customer-ai-confirm-button"
                        disabled={Boolean(verifyingId)}
                        onClick={() => onVerify(card, 'confirmed')}
                        type="button"
                      >
                        {verifyingId === card.id ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
                        확인
                      </button>
                      <button
                        className="route-secondary-action customer-ai-deny-button"
                        disabled={Boolean(verifyingId)}
                        onClick={() => onVerify(card, 'denied')}
                        type="button"
                      >
                        {verifyingId === card.id ? <Loader2 className="spin-icon" size={14} /> : <X size={14} />}
                        부정
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className={`customer-ai-status ${card.verificationStatus}`}>
                    <strong>{card.verificationStatusLabel}</strong>
                    {card.verificationNote ? <span>{card.verificationNote}</span> : null}
                    {card.verifiedAt ? <small>{formatDateTimeLabel(card.verifiedAt)}</small> : null}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function CustomerDetailPage({
  data,
  loading,
  onRefresh,
}: {
  data: CustomerDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<CustomerDetailData | null>;
}) {
  const customer = data?.customer ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<CustomerEditFormState>(() => makeCustomerEditForm(customer));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [aiRunning, setAiRunning] = useState(false);
  const [aiError, setAiError] = useState('');
  const [aiMessage, setAiMessage] = useState('');
  const [aiResultOpen, setAiResultOpen] = useState(false);
  const [aiVerificationNotes, setAiVerificationNotes] = useState<Record<number, string>>({});
  const [aiVerifyingId, setAiVerifyingId] = useState<number | null>(null);

  useEffect(() => {
    setEditForm(makeCustomerEditForm(customer));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setAiRunning(false);
    setAiError('');
    setAiMessage('');
    setAiResultOpen(false);
    setAiVerificationNotes({});
    setAiVerifyingId(null);
  }, [customer?.id]);

  useEffect(() => {
    if (data?.aiDepartment?.hasAnalysis) {
      setAiResultOpen(true);
    }
  }, [customer?.id, data?.aiDepartment?.hasAnalysis]);

  const editConfig = data?.edit;
  const editCompanies = editConfig?.companies ?? [];
  const editDepartments = editForm.companyId
    ? (editConfig?.departments ?? []).filter((department) => String(department.companyId) === editForm.companyId)
    : editConfig?.departments ?? [];

  const handleEditFieldChange = (field: keyof CustomerEditFormState, value: string) => {
    setEditForm((previous) => {
      const next = {
        ...previous,
        [field]: value,
      };
      if (field === 'companyId') {
        const firstDepartment = (editConfig?.departments ?? []).find(
          (department) => String(department.companyId) === value,
        );
        next.departmentId = firstDepartment ? String(firstDepartment.id) : '';
      }
      return next;
    });
    setEditError('');
    setEditMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!customer || !editConfig || editSaving) {
      return;
    }
    if (!editConfig.canEdit) {
      setEditError(editConfig.message || '수정 권한이 없습니다.');
      return;
    }
    const companyId = Number(editForm.companyId);
    const departmentId = Number(editForm.departmentId);
    if (!companyId) {
      setEditError('업체/학교를 선택하세요.');
      return;
    }
    if (!departmentId) {
      setEditError('부서/연구실을 선택하세요.');
      return;
    }
    if (!editForm.customerName.trim()) {
      setEditError('고객명을 입력하세요.');
      return;
    }
    const payload: CustomerEditPayload = {
      address: editForm.address.trim() || undefined,
      companyId,
      customerName: editForm.customerName.trim(),
      departmentId,
      email: editForm.email.trim() || undefined,
      manager: editForm.manager.trim() || undefined,
      notes: editForm.notes.trim() || undefined,
      phoneNumber: editForm.phoneNumber.trim() || undefined,
      pipelineStage: editForm.pipelineStage,
      priority: editForm.priority,
      status: editForm.status,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateCustomerRecord(payload, editConfig.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '고객 정보를 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '고객 정보 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleAiDepartmentRun = async () => {
    const aiDepartment = data?.aiDepartment;
    if (!aiDepartment?.canAnalyze || !aiDepartment.runHref || aiRunning) {
      setAiError(aiDepartment?.message || 'AI 분석을 실행할 수 없습니다.');
      setAiMessage('');
      return;
    }

    setAiRunning(true);
    setAiError('');
    setAiMessage('');
    try {
      const result = await runAiDepartmentAnalysis(aiDepartment.runHref);
      await onRefresh();
      const cardCount = result.cards_created ?? result.cardsCreated ?? 0;
      setAiMessage(cardCount > 0 ? `AI 분석을 완료했습니다. PainPoint ${formatNumber(cardCount)}건` : 'AI 분석을 완료했습니다.');
      setAiResultOpen(true);
    } catch (error) {
      setAiError(error instanceof Error ? error.message : 'AI 분석 실행에 실패했습니다.');
    } finally {
      setAiRunning(false);
    }
  };

  const handleAiVerificationNoteChange = (cardId: number, value: string) => {
    setAiVerificationNotes((previous) => ({
      ...previous,
      [cardId]: value,
    }));
  };

  const handleAiPainpointVerify = async (card: CustomerAiPainpoint, status: 'confirmed' | 'denied') => {
    if (!card.canVerify || !card.verifyHref || aiVerifyingId) {
      return;
    }

    setAiVerifyingId(card.id);
    setAiError('');
    setAiMessage('');
    try {
      await verifyAiPainpoint(card.verifyHref, status, aiVerificationNotes[card.id] || '');
      await onRefresh();
      setAiMessage(status === 'confirmed' ? 'PainPoint를 확인 처리했습니다.' : 'PainPoint를 부정 처리했습니다.');
      setAiVerificationNotes((previous) => {
        const next = { ...previous };
        delete next[card.id];
        return next;
      });
      setAiResultOpen(true);
    } catch (error) {
      setAiError(error instanceof Error ? error.message : 'PainPoint 검증 저장에 실패했습니다.');
    } finally {
      setAiVerifyingId(null);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.customer) {
    return (
      <section className="customers-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>고객 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '고객 상세 API에 연결되지 않았습니다.'}</span>
          </div>
          <a href="/customers/">목록</a>
        </div>
      </section>
    );
  }

  const customerDetail = data.customer;
  const aiDepartment = data.aiDepartment;
  const prepaymentSummary = data.prepaymentSummary;
  const metrics = [
    { label: '최근 노트', value: `${formatNumber(data.metrics.recentNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '예정 일정', value: `${formatNumber(data.metrics.upcomingSchedules)}건`, detail: '진행 예정', icon: CalendarDays, tone: 'green' as const },
    { label: '지연 후속', value: `${formatNumber(data.metrics.overdueActions)}건`, detail: '확인 필요', icon: AlertTriangle, tone: 'red' as const },
    { label: '14일 내 후속', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '예정 액션', icon: Clock, tone: 'teal' as const },
  ];

  return (
    <section className="customers-page customer-detail-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>고객 상세 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Customer detail</span>
          <h2>{customerDetail.company || customerDetail.customer}</h2>
          <p>{[customerDetail.customer, customerDetail.department, customerDetail.owner].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/customers/">목록</a>
          <a className="route-secondary-action" href={data.links.djangoDetail}>Django 상세</a>
          {data.edit.canEdit ? (
            <button className="route-secondary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
            </button>
          ) : null}
          <a className="route-secondary-action" href={data.links.createNote}>
            노트 작성
            <FileText size={16} />
          </a>
          <a className="route-primary-action" href={data.links.createSchedule}>
            일정 등록
            <Plus size={16} />
          </a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객 상세 지표">
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

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel customer-edit-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit customer</span>
              <h2>고객 정보 수정</h2>
            </div>
            <Users size={18} />
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form customer-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid">
                <div className="form-field">
                  <span>업체/학교</span>
                  <SearchableSelect
                    ariaLabel="업체/학교 선택"
                    onChange={(nextValue) => handleEditFieldChange('companyId', nextValue)}
                    options={editCompanies.map(makeCompanySelectOption)}
                    placeholder="업체/학교 검색"
                    value={editForm.companyId}
                  />
                </div>
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    disabled={!editForm.companyId}
                    onChange={(nextValue) => handleEditFieldChange('departmentId', nextValue)}
                    options={editDepartments.map(makeDepartmentSelectOption)}
                    placeholder={editForm.companyId ? '부서/연구실 검색' : '업체를 먼저 선택'}
                    value={editForm.departmentId}
                  />
                </div>
                <label>
                  <span>고객명</span>
                  <input
                    onChange={(event) => handleEditFieldChange('customerName', event.target.value)}
                    required
                    value={editForm.customerName}
                  />
                </label>
                <label>
                  <span>책임자</span>
                  <input
                    onChange={(event) => handleEditFieldChange('manager', event.target.value)}
                    value={editForm.manager}
                  />
                </label>
                <label>
                  <span>우선순위</span>
                  <select
                    onChange={(event) => handleEditFieldChange('priority', event.target.value)}
                    required
                    value={editForm.priority}
                  >
                    {data.edit.priorities.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>상태</span>
                  <select
                    onChange={(event) => handleEditFieldChange('status', event.target.value)}
                    required
                    value={editForm.status}
                  >
                    {data.edit.statuses.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>파이프라인</span>
                  <select
                    onChange={(event) => handleEditFieldChange('pipelineStage', event.target.value)}
                    required
                    value={editForm.pipelineStage}
                  >
                    {data.edit.stages.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>연락처</span>
                  <input
                    onChange={(event) => handleEditFieldChange('phoneNumber', event.target.value)}
                    value={editForm.phoneNumber}
                  />
                </label>
                <label>
                  <span>이메일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('email', event.target.value)}
                    type="email"
                    value={editForm.email}
                  />
                </label>
                <label>
                  <span>상세주소</span>
                  <input
                    onChange={(event) => handleEditFieldChange('address', event.target.value)}
                    value={editForm.address}
                  />
                </label>
              </div>
              <label>
                <span>상세 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('notes', event.target.value)}
                  rows={3}
                  value={editForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={data.edit.djangoUrl || data.links.djangoEdit}>
                  Django 수정
                  <MoveUpRight size={15} />
                </a>
                <button className="route-primary-action" disabled={editSaving} type="submit">
                  {editSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      <div className="customer-detail-layout">
        <section className="dashboard-panel customer-detail-main">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Recent notes</span>
              <h2>최근 영업노트</h2>
            </div>
            <FileText size={18} />
          </div>
          <CustomerDetailNoteList emptyLabel="최근 영업노트가 없습니다" notes={data.recentNotes} />
        </section>

        <aside className="dashboard-panel customer-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customer</span>
              <h2>고객 요약</h2>
            </div>
            <Users size={18} />
          </div>
          <div className="customer-detail-summary">
            <CustomerStatusBadge customer={customerDetail} />
            <dl>
              <div>
                <dt>연락처</dt>
                <dd>{customerDetail.contactSummary || '연락처 없음'}</dd>
              </div>
              <div>
                <dt>다음 액션</dt>
                <dd className={customerDetail.overdue ? 'customer-overdue-text' : ''}>{customerDetail.nextAction || '다음 액션 없음'}</dd>
              </div>
              <div>
                <dt>최근 활동</dt>
                <dd>{customerDetail.lastActivityLabel || '최근 활동 없음'}</dd>
              </div>
            </dl>
          </div>

          <div className="customer-prepayment-card">
            <div className="customer-prepayment-heading">
              <div>
                <span className="eyebrow">Prepayment</span>
                <h3>선결제 요약</h3>
              </div>
              <CircleDollarSign size={18} />
            </div>
            <div className="customer-prepayment-metrics">
              <span>
                총액
                <strong>{formatWon(prepaymentSummary.metrics.totalAmount)}</strong>
              </span>
              <span>
                잔액
                <strong>{formatWon(prepaymentSummary.metrics.totalBalance)}</strong>
              </span>
              <span>
                사용
                <strong>{formatWon(prepaymentSummary.metrics.totalUsed)}</strong>
              </span>
              <span>
                건수
                <strong>{formatNumber(prepaymentSummary.metrics.totalCount)}건</strong>
              </span>
            </div>
            <div className="customer-prepayment-state">
              <span>활성 {formatNumber(prepaymentSummary.metrics.activeCount)}</span>
              <span>소진 {formatNumber(prepaymentSummary.metrics.depletedCount)}</span>
              <span>취소 {formatNumber(prepaymentSummary.metrics.cancelledCount)}</span>
            </div>
            {prepaymentSummary.recentPrepayments.length > 0 ? (
              <div className="customer-prepayment-list">
                {prepaymentSummary.recentPrepayments.map((prepayment) => (
                  <article key={prepayment.id}>
                    <div>
                      <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                      <small>{[prepayment.payerName || '입금자 미지정', prepayment.ownerName].filter(Boolean).join(' · ')}</small>
                    </div>
                    <div>
                      <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                        {formatWon(prepayment.balance)}
                      </strong>
                      <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
                    </div>
                    <a href={`/prepayments/${prepayment.id}/`}>상세</a>
                  </article>
                ))}
              </div>
            ) : (
              <DashboardEmpty label="이 고객의 선결제가 없습니다" />
            )}
            <div className="customer-prepayment-actions">
              <a className="route-secondary-action" href={prepaymentSummary.links.customerPrepayments || prepaymentSummary.links.djangoCustomerPrepayments}>
                고객별 선결제
                <MoveUpRight size={15} />
              </a>
              <a className="route-secondary-action" href={prepaymentSummary.links.prepayments}>
                선결제 목록
                <MoveUpRight size={15} />
              </a>
            </div>
          </div>

          <div className="customer-ai-card">
            <div className="customer-ai-card-heading">
              <div>
                <span className="eyebrow">Department AI</span>
                <h3>{aiDepartment.departmentName || '부서 AI 분석'}</h3>
              </div>
              <Sparkles size={18} />
            </div>
            {aiDepartment.hasAnalysis ? (
              <p>{aiDepartment.summary || '분석 요약 없음'}</p>
            ) : (
              <p>{aiDepartment.message || '아직 부서 AI 분석이 없습니다.'}</p>
            )}
            <div className="customer-ai-metrics">
              <span>미팅 <strong>{formatNumber(aiDepartment.meetingCount)}</strong></span>
              <span>견적 <strong>{formatNumber(aiDepartment.quoteCount)}</strong></span>
              <span>납품 <strong>{formatNumber(aiDepartment.deliveryCount)}</strong></span>
              <span>PainPoint <strong>{formatNumber(aiDepartment.painpointCount)}</strong></span>
            </div>
            {aiError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{aiError}</span></div> : null}
            {aiMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{aiMessage}</span></div> : null}
            <div className="customer-ai-actions">
              {aiDepartment.hasAnalysis ? (
                <button className="route-secondary-action" onClick={() => setAiResultOpen((open) => !open)} type="button">
                  {aiResultOpen ? '결과 닫기' : '결과 보기'}
                </button>
              ) : null}
              {aiDepartment.href ? (
                <a className="route-secondary-action" href={aiDepartment.href}>
                  Django 보기
                  <MoveUpRight size={15} />
                </a>
              ) : aiDepartment.hubHref ? (
                <a className="route-secondary-action" href={aiDepartment.hubHref}>
                  AI 허브
                  <MoveUpRight size={15} />
                </a>
              ) : null}
              <button
                className="route-primary-action customer-ai-run-button"
                disabled={!aiDepartment.canAnalyze || !aiDepartment.runHref || aiRunning}
                onClick={handleAiDepartmentRun}
                type="button"
              >
                {aiRunning ? <Loader2 className="spin-icon" size={15} /> : <Sparkles size={15} />}
                AI 분석 실행
              </button>
            </div>
            {aiDepartment.hasAnalysis && aiResultOpen ? (
              <CustomerAiResultPanel
                aiDepartment={aiDepartment}
                verificationNotes={aiVerificationNotes}
                verifyingId={aiVerifyingId}
                onNoteChange={handleAiVerificationNoteChange}
                onVerify={handleAiPainpointVerify}
              />
            ) : null}
          </div>

          <div className="dashboard-panel-heading customer-detail-section-heading">
            <div>
              <span className="eyebrow">Upcoming</span>
              <h2>예정 일정</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          <SchedulesCompactList emptyLabel="예정 일정이 없습니다" items={data.upcomingSchedules} />

          <div className="dashboard-panel-heading customer-detail-section-heading">
            <div>
              <span className="eyebrow">Overdue</span>
              <h2>지연 후속</h2>
            </div>
            <AlertTriangle size={18} />
          </div>
          <CustomerDetailNoteList emptyLabel="지연 후속이 없습니다" notes={data.overdueActions} urgent />
        </aside>
      </div>
    </section>
  );
}

function CustomersPage({
  companyCreateName,
  companyCreating,
  createDetailHref,
  createDepartmentName,
  createError,
  createForm,
  createMessage,
  createOpen,
  creating,
  data,
  departmentCreating,
  detailData,
  detailLoading,
  loading,
  owner,
  priority,
  query,
  selectedCustomerId,
  stage,
  onCompanyCreateNameChange,
  onCompanyCreateSubmit,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onDepartmentCreateNameChange,
  onDepartmentCreateSubmit,
  onDetailRefresh,
  onOwnerChange,
  onPriorityChange,
  onQueryChange,
  onStageChange,
}: {
  companyCreateName: string;
  companyCreating: boolean;
  createDetailHref: string;
  createDepartmentName: string;
  createError: string;
  createForm: CustomerCreateFormState;
  createMessage: string;
  createOpen: boolean;
  creating: boolean;
  data: CustomersData | null;
  departmentCreating: boolean;
  detailData: CustomerDetailData | null;
  detailLoading: boolean;
  loading: boolean;
  owner: string;
  priority: string;
  query: string;
  selectedCustomerId: number | null;
  stage: string;
  onCompanyCreateNameChange: (value: string) => void;
  onCompanyCreateSubmit: () => void;
  onCreateFormChange: (field: keyof CustomerCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDepartmentCreateNameChange: (value: string) => void;
  onDepartmentCreateSubmit: () => void;
  onDetailRefresh: () => Promise<CustomerDetailData | null>;
  onOwnerChange: (value: string) => void;
  onPriorityChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onStageChange: (value: string) => void;
}) {
  if (selectedCustomerId) {
    return <CustomerDetailPage data={detailData} loading={detailLoading} onRefresh={onDetailRefresh} />;
  }

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
  const createConfig = data.create;
  const canCreateCustomers = createConfig.canCreate;
  const createCompanies = createConfig.companies;
  const createPriorities = createConfig.priorities.length > 0 ? createConfig.priorities : data.options.priorities;
  const createDepartments = createForm.companyId
    ? createConfig.departments.filter((department) => String(department.companyId) === createForm.companyId)
    : createConfig.departments;
  const departmentCreateDisabled = !createForm.companyId || departmentCreating;

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
        <button
          className={canCreateCustomers ? 'route-primary-action' : 'route-secondary-action'}
          onClick={() => onCreateOpenChange(!createOpen)}
          type="button"
        >
          {canCreateCustomers ? '새 고객 등록' : '등록 권한 없음'}
          <Plus size={16} />
        </button>
      </div>

      {createOpen ? (
        <section className="dashboard-panel notes-create-panel customer-create-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Quick customer</span>
              <h2>고객 빠른 등록</h2>
            </div>
            {creating ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
          </div>
          {createMessage ? (
            <div className="notes-action-feedback success">
              <span>{createMessage}</span>
              {createDetailHref ? <a href={createDetailHref}>상세 열기</a> : null}
            </div>
          ) : null}
          {createError ? <div className="notes-action-feedback error">{createError}</div> : null}
          {!canCreateCustomers ? (
            <DashboardEmpty label={createConfig.message || '고객 등록 권한이 없습니다'} />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="customer-inline-create-grid">
                <label>
                  <span>새 업체/학교</span>
                  <div className="customer-inline-create-row">
                    <input
                      onChange={(event) => onCompanyCreateNameChange(event.target.value)}
                      placeholder="업체/학교명"
                      value={companyCreateName}
                    />
                    <button
                      className="route-secondary-action"
                      disabled={companyCreating || !companyCreateName.trim()}
                      onClick={onCompanyCreateSubmit}
                      type="button"
                    >
                      {companyCreating ? <Loader2 className="spin-icon" size={14} /> : <Plus size={14} />}
                      추가
                    </button>
                  </div>
                </label>
                <label>
                  <span>새 부서/연구실</span>
                  <div className="customer-inline-create-row">
                    <input
                      disabled={!createForm.companyId}
                      onChange={(event) => onDepartmentCreateNameChange(event.target.value)}
                      placeholder={createForm.companyId ? '부서/연구실명' : '업체를 먼저 선택'}
                      value={createDepartmentName}
                    />
                    <button
                      className="route-secondary-action"
                      disabled={departmentCreateDisabled || !createDepartmentName.trim()}
                      onClick={onDepartmentCreateSubmit}
                      type="button"
                    >
                      {departmentCreating ? <Loader2 className="spin-icon" size={14} /> : <Plus size={14} />}
                      추가
                    </button>
                  </div>
                </label>
              </div>
              <div className="notes-create-grid customer-create-grid">
                <div className="form-field">
                  <span>업체/학교</span>
                  <SearchableSelect
                    ariaLabel="업체/학교 선택"
                    onChange={(nextValue) => onCreateFormChange('companyId', nextValue)}
                    options={createCompanies.map(makeCompanySelectOption)}
                    placeholder="업체/학교 검색"
                    value={createForm.companyId}
                  />
                </div>
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    disabled={!createForm.companyId}
                    onChange={(nextValue) => onCreateFormChange('departmentId', nextValue)}
                    options={createDepartments.map(makeDepartmentSelectOption)}
                    placeholder={createForm.companyId ? '부서/연구실 검색' : '업체를 먼저 선택'}
                    value={createForm.departmentId}
                  />
                </div>
                <label>
                  <span>고객명</span>
                  <input
                    onChange={(event) => onCreateFormChange('customerName', event.target.value)}
                    placeholder="담당자명"
                    required
                    value={createForm.customerName}
                  />
                </label>
                <label>
                  <span>우선순위</span>
                  <select
                    onChange={(event) => onCreateFormChange('priority', event.target.value)}
                    required
                    value={createForm.priority}
                  >
                    {createPriorities.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>책임자</span>
                  <input
                    onChange={(event) => onCreateFormChange('manager', event.target.value)}
                    placeholder="책임자명"
                    value={createForm.manager}
                  />
                </label>
                <label>
                  <span>연락처</span>
                  <input
                    onChange={(event) => onCreateFormChange('phoneNumber', event.target.value)}
                    placeholder="010-0000-0000"
                    value={createForm.phoneNumber}
                  />
                </label>
                <label>
                  <span>이메일</span>
                  <input
                    onChange={(event) => onCreateFormChange('email', event.target.value)}
                    placeholder="name@example.com"
                    type="email"
                    value={createForm.email}
                  />
                </label>
                <label>
                  <span>상세주소</span>
                  <input
                    onChange={(event) => onCreateFormChange('address', event.target.value)}
                    placeholder="방문 주소"
                    value={createForm.address}
                  />
                </label>
              </div>
              <label>
                <span>상세 내용</span>
                <textarea
                  onChange={(event) => onCreateFormChange('notes', event.target.value)}
                  placeholder="관심 품목, 거래 맥락, 특이사항"
                  rows={3}
                  value={createForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={createConfig.advancedUrl}>
                  상세 등록
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

function NoteDetailPage({
  data,
  loading,
  onRefresh,
}: {
  data: NoteDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<NoteDetailData | null>;
}) {
  const currentNote = data?.note ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<NoteEditFormState>(() => makeNoteEditForm(currentNote));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const noteFileInputRef = useRef<HTMLInputElement | null>(null);
  const [noteFileUploading, setNoteFileUploading] = useState(false);
  const [noteFileDeletingId, setNoteFileDeletingId] = useState<number | null>(null);
  const [noteFileError, setNoteFileError] = useState('');
  const [noteFileMessage, setNoteFileMessage] = useState('');
  const [replyText, setReplyText] = useState('');
  const [replySaving, setReplySaving] = useState(false);
  const [replyDeletingId, setReplyDeletingId] = useState<number | null>(null);
  const [replyError, setReplyError] = useState('');
  const [replyMessage, setReplyMessage] = useState('');

  useEffect(() => {
    setEditForm(makeNoteEditForm(currentNote));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setNoteFileError('');
    setNoteFileMessage('');
    setNoteFileUploading(false);
    setNoteFileDeletingId(null);
    setReplyText('');
    setReplyError('');
    setReplyMessage('');
    setReplySaving(false);
    setReplyDeletingId(null);
    if (noteFileInputRef.current) {
      noteFileInputRef.current.value = '';
    }
  }, [currentNote?.id]);

  const editConfig = data?.edit;
  const activityDateVisible = editForm.actionType === 'customer_meeting' || editForm.actionType === 'delivery_schedule';

  const handleEditFieldChange = (field: keyof NoteEditFormState, value: string) => {
    setEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentNote || !editConfig || editSaving) {
      return;
    }
    if (!editConfig.canEdit) {
      setEditError(editConfig.message || '수정 권한이 없습니다.');
      return;
    }
    const followupId = Number(editForm.followupId);
    if (!followupId) {
      setEditError('고객을 선택하세요.');
      return;
    }
    if (!editForm.actionType) {
      setEditError('활동 유형을 선택하세요.');
      return;
    }
    if (editForm.actionType !== 'customer_meeting' && !editForm.content.trim()) {
      setEditError('활동 내용을 입력하세요.');
      return;
    }
    if (editForm.actionType === 'service' && !editForm.serviceStatus) {
      setEditError('서비스 상태를 선택하세요.');
      return;
    }

    const payload: NoteEditPayload = {
      actionType: editForm.actionType,
      activityDate: activityDateVisible ? editForm.activityDate || undefined : undefined,
      content: editForm.content.trim(),
      deliveryAmount: editForm.deliveryAmount.trim() || undefined,
      deliveryItems: editForm.deliveryItems.trim() || undefined,
      followupId,
      meetingConfirmedFacts: editForm.meetingConfirmedFacts.trim() || undefined,
      meetingNextAction: editForm.meetingNextAction.trim() || undefined,
      meetingObstacles: editForm.meetingObstacles.trim() || undefined,
      meetingResearcherQuote: editForm.meetingResearcherQuote.trim() || undefined,
      meetingSituation: editForm.meetingSituation.trim() || undefined,
      nextAction: editForm.nextAction.trim() || undefined,
      nextActionDate: editForm.nextActionDate || undefined,
      serviceStatus: editForm.actionType === 'service' ? editForm.serviceStatus : undefined,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateSalesNote(payload, editConfig.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '영업노트를 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '영업노트 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleToggleReview = async () => {
    if (!currentNote?.reviewToggleHref || reviewing) {
      return;
    }
    setReviewing(true);
    setEditError('');
    setEditMessage('');
    try {
      await toggleNoteReviewed(currentNote.reviewToggleHref);
      await onRefresh();
      setEditMessage(currentNote.reviewed ? '검토 상태를 해제했습니다.' : '검토 완료로 처리했습니다.');
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '검토 상태 변경에 실패했습니다.');
    } finally {
      setReviewing(false);
    }
  };

  const handleNoteFileUploadClick = () => {
    if (!currentNote?.canEdit || !data?.links.uploadFiles) {
      setNoteFileError('첨부파일 업로드 권한이 없습니다.');
      setNoteFileMessage('');
      return;
    }
    noteFileInputRef.current?.click();
  };

  const handleNoteFilesSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (!selectedFiles.length) {
      return;
    }

    if (!currentNote?.canEdit || !data?.links.uploadFiles) {
      setNoteFileError('첨부파일 업로드 권한이 없습니다.');
      setNoteFileMessage('');
      event.target.value = '';
      return;
    }

    if (currentNote.files.length + selectedFiles.length > 5) {
      setNoteFileError(`첨부파일은 최대 5개까지 등록할 수 있습니다. 현재 ${currentNote.files.length}개가 등록되어 있습니다.`);
      setNoteFileMessage('');
      event.target.value = '';
      return;
    }

    setNoteFileUploading(true);
    setNoteFileError('');
    setNoteFileMessage('');
    try {
      const result = await uploadNoteFiles(data.links.uploadFiles, selectedFiles);
      await onRefresh();
      setNoteFileMessage(result.message || `${selectedFiles.length}개 파일을 업로드했습니다.`);
    } catch (error) {
      setNoteFileError(error instanceof Error ? error.message : '첨부파일 업로드에 실패했습니다.');
    } finally {
      setNoteFileUploading(false);
      event.target.value = '';
    }
  };

  const handleNoteFileDelete = async (file: NoteFileItem) => {
    if (noteFileDeletingId !== null) {
      return;
    }
    if (!currentNote?.canEdit || !file.canDelete || !file.deleteHref) {
      setNoteFileError('첨부파일 삭제 권한이 없습니다.');
      setNoteFileMessage('');
      return;
    }
    if (!window.confirm(`"${file.filename}" 파일을 삭제할까요?`)) {
      return;
    }

    setNoteFileDeletingId(file.id);
    setNoteFileError('');
    setNoteFileMessage('');
    try {
      const result = await deleteNoteFile(file.deleteHref);
      await onRefresh();
      setNoteFileMessage(result.message || '첨부파일을 삭제했습니다.');
    } catch (error) {
      setNoteFileError(error instanceof Error ? error.message : '첨부파일 삭제에 실패했습니다.');
    } finally {
      setNoteFileDeletingId(null);
    }
  };

  const handleReplySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const memo = replyText.trim();
    if (!memo) {
      setReplyError('댓글 내용을 입력하세요.');
      setReplyMessage('');
      return;
    }
    if (!data?.comments.canCreate || !data.comments.submitUrl || replySaving) {
      setReplyError(data?.comments.message || '댓글 작성 권한이 없습니다.');
      setReplyMessage('');
      return;
    }

    setReplySaving(true);
    setReplyError('');
    setReplyMessage('');
    try {
      const result = await addNoteReply(data.comments.submitUrl, memo);
      await onRefresh();
      setReplyText('');
      setReplyMessage(result.message || '댓글을 추가했습니다.');
    } catch (error) {
      setReplyError(error instanceof Error ? error.message : '댓글 작성에 실패했습니다.');
    } finally {
      setReplySaving(false);
    }
  };

  const handleReplyDelete = async (reply: NoteReplyItem) => {
    if (replyDeletingId !== null) {
      return;
    }
    if (!reply.canDelete || !reply.deleteHref) {
      setReplyError('댓글 삭제 권한이 없습니다.');
      setReplyMessage('');
      return;
    }
    if (!window.confirm('이 댓글을 삭제할까요?')) {
      return;
    }

    setReplyDeletingId(reply.id);
    setReplyError('');
    setReplyMessage('');
    try {
      const result = await deleteNoteReply(reply.deleteHref);
      await onRefresh();
      setReplyMessage(result.message || '댓글을 삭제했습니다.');
    } catch (error) {
      setReplyError(error instanceof Error ? error.message : '댓글 삭제에 실패했습니다.');
    } finally {
      setReplyDeletingId(null);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>영업노트 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.note) {
    return (
      <section className="notes-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>영업노트 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '영업노트 상세 API에 연결되지 않았습니다.'}</span>
          </div>
          <a href="/notes/">목록</a>
        </div>
      </section>
    );
  }

  const note = data.note;
  const metrics = [
    { label: '활동 유형', value: note.actionLabel, detail: note.owner, icon: FileText, tone: 'blue' as const },
    { label: '검토 상태', value: note.reviewed ? '완료' : note.reviewRequired ? '미검토' : '불필요', detail: note.reviewer || data.scope.label, icon: CheckCircle2, tone: note.reviewed ? 'green' as const : 'amber' as const },
    { label: '다음 예정일', value: note.nextActionDate ? formatDateLabel(note.nextActionDate) : '없음', detail: note.overdue ? '지연' : '후속 액션', icon: Clock, tone: note.overdue ? 'red' as const : 'teal' as const },
    { label: '첨부/댓글', value: `${formatNumber(note.fileCount)} / ${formatNumber(note.replyCount)}`, detail: '파일 / 댓글', icon: MessageSquareText, tone: 'green' as const },
  ];

  return (
    <section className="notes-page note-detail-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>영업노트 상세 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Note detail</span>
          <h2>{note.company || note.customer || note.actionLabel}</h2>
          <p>{[note.customer, note.department, note.actionLabel, note.owner].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/notes/">목록</a>
          {data.links.customer ? <a className="route-secondary-action" href={data.links.customer}>고객</a> : null}
          <a className="route-secondary-action" href={data.links.djangoDetail}>Django 상세</a>
          {note.canReview && note.reviewToggleHref ? (
            <button className="route-secondary-action" disabled={reviewing} onClick={handleToggleReview} type="button">
              {reviewing ? <Loader2 className="spin-icon" size={15} /> : <CheckCircle2 size={15} />}
              {note.reviewed ? '검토 해제' : '검토 완료'}
            </button>
          ) : null}
          {data.edit.canEdit ? (
            <button className="route-primary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
              <Check size={16} />
            </button>
          ) : null}
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="영업노트 상세 지표">
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

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel note-edit-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit note</span>
              <h2>영업노트 수정</h2>
            </div>
            {editSaving ? <Loader2 className="spin-icon" size={18} /> : <FileText size={18} />}
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form note-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid">
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    ariaLabel="고객 선택"
                    onChange={(nextValue) => handleEditFieldChange('followupId', nextValue)}
                    options={data.edit.customers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={editForm.followupId}
                  />
                </div>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => handleEditFieldChange('actionType', event.target.value)}
                    required
                    value={editForm.actionType}
                  >
                    {data.edit.actionTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                {activityDateVisible ? (
                  <label>
                    <span>{editForm.actionType === 'delivery_schedule' ? '납품일' : '미팅일'}</span>
                    <input
                      onChange={(event) => handleEditFieldChange('activityDate', event.target.value)}
                      type="date"
                      value={editForm.activityDate}
                    />
                  </label>
                ) : null}
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('nextActionDate', event.target.value)}
                    type="date"
                    value={editForm.nextActionDate}
                  />
                </label>
                {editForm.actionType === 'service' ? (
                  <label>
                    <span>서비스 상태</span>
                    <select
                      onChange={(event) => handleEditFieldChange('serviceStatus', event.target.value)}
                      required
                      value={editForm.serviceStatus}
                    >
                      {data.edit.serviceStatuses.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </label>
                ) : null}
                {editForm.actionType === 'delivery_schedule' ? (
                  <label>
                    <span>납품 금액</span>
                    <input
                      min="0"
                      onChange={(event) => handleEditFieldChange('deliveryAmount', event.target.value)}
                      type="number"
                      value={editForm.deliveryAmount}
                    />
                  </label>
                ) : null}
              </div>
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('content', event.target.value)}
                  required={editForm.actionType !== 'customer_meeting'}
                  rows={4}
                  value={editForm.content}
                />
              </label>
              {editForm.actionType === 'customer_meeting' ? (
                <div className="note-edit-section-grid">
                  <label>
                    <span>오늘 상황</span>
                    <textarea onChange={(event) => handleEditFieldChange('meetingSituation', event.target.value)} rows={3} value={editForm.meetingSituation} />
                  </label>
                  <label>
                    <span>연구원 발언</span>
                    <textarea onChange={(event) => handleEditFieldChange('meetingResearcherQuote', event.target.value)} rows={3} value={editForm.meetingResearcherQuote} />
                  </label>
                  <label>
                    <span>확인한 사실</span>
                    <textarea onChange={(event) => handleEditFieldChange('meetingConfirmedFacts', event.target.value)} rows={3} value={editForm.meetingConfirmedFacts} />
                  </label>
                  <label>
                    <span>장애물/반대</span>
                    <textarea onChange={(event) => handleEditFieldChange('meetingObstacles', event.target.value)} rows={3} value={editForm.meetingObstacles} />
                  </label>
                  <label>
                    <span>미팅 다음 액션</span>
                    <textarea onChange={(event) => handleEditFieldChange('meetingNextAction', event.target.value)} rows={3} value={editForm.meetingNextAction} />
                  </label>
                </div>
              ) : null}
              {editForm.actionType === 'delivery_schedule' ? (
                <label>
                  <span>납품 품목</span>
                  <textarea
                    onChange={(event) => handleEditFieldChange('deliveryItems', event.target.value)}
                    rows={3}
                    value={editForm.deliveryItems}
                  />
                </label>
              ) : null}
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('nextAction', event.target.value)}
                  rows={2}
                  value={editForm.nextAction}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={data.edit.djangoUrl || data.links.djangoEdit}>
                  Django 수정
                  <MoveUpRight size={15} />
                </a>
                <button className="route-primary-action" disabled={editSaving} type="submit">
                  {editSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      <div className="note-detail-layout">
        <section className="dashboard-panel note-detail-main">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Activity</span>
              <h2>활동 내용</h2>
            </div>
            <NoteStatusBadge note={note} />
          </div>
          <div className="note-detail-content">
            {note.content ? <p>{note.content}</p> : <DashboardEmpty label="활동 내용이 없습니다" />}
          </div>
          {note.actionType === 'customer_meeting' ? (
            <div className="note-detail-field-grid">
              {[
                ['오늘 상황', note.meetingSituation],
                ['연구원 발언', note.meetingResearcherQuote],
                ['확인한 사실', note.meetingConfirmedFacts],
                ['장애물/반대', note.meetingObstacles],
                ['미팅 다음 액션', note.meetingNextAction],
              ].map(([label, value]) => (
                value ? (
                  <div className="note-detail-field" key={label}>
                    <span>{label}</span>
                    <p>{value}</p>
                  </div>
                ) : null
              ))}
            </div>
          ) : null}
          {note.actionType === 'delivery_schedule' ? (
            <div className="note-detail-field-grid">
              <div className="note-detail-field">
                <span>납품 금액</span>
                <p>{formatWon(note.deliveryAmount)}</p>
              </div>
              {note.deliveryItems ? (
                <div className="note-detail-field">
                  <span>납품 품목</span>
                  <p>{note.deliveryItems}</p>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>

        <aside className="dashboard-panel note-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Follow-up</span>
              <h2>연결 정보</h2>
            </div>
            <PanelRight size={18} />
          </div>
          <div className="customer-detail-summary">
            <dl>
              <div>
                <dt>고객</dt>
                <dd>{[note.company, note.department, note.customer].filter(Boolean).join(' · ') || '고객 없음'}</dd>
              </div>
              <div>
                <dt>담당자</dt>
                <dd>{note.owner}</dd>
              </div>
              <div>
                <dt>활동일</dt>
                <dd>{note.activityDate ? formatDateLabel(note.activityDate) : formatDateTimeLabel(note.createdAt)}</dd>
              </div>
              <div>
                <dt>다음 액션</dt>
                <dd className={note.overdue ? 'customer-overdue-text' : ''}>{note.nextAction || '다음 액션 없음'}</dd>
              </div>
            </dl>
          </div>
          <div className="customers-side-actions note-detail-actions">
            {data.links.customer ? <a href={data.links.customer}>React 고객 상세</a> : null}
            {data.links.djangoCustomer ? <a href={data.links.djangoCustomer}>Django 고객 상세</a> : null}
            {data.links.schedule ? <a href={data.links.schedule}>연결 일정</a> : null}
            <a href={data.links.createNote}>새 노트 작성</a>
          </div>
          <div className="schedule-file-heading">
            <h3 className="customer-detail-section-heading">첨부파일</h3>
            {note.canEdit && data.links.uploadFiles ? (
              <>
                <input
                  aria-label="영업노트 첨부파일 선택"
                  className="schedule-file-input"
                  multiple
                  onChange={handleNoteFilesSelected}
                  ref={noteFileInputRef}
                  type="file"
                />
                <button
                  className="customer-row-action schedule-file-upload-button"
                  disabled={noteFileUploading}
                  onClick={handleNoteFileUploadClick}
                  type="button"
                >
                  {noteFileUploading ? <Loader2 className="spin-icon" size={14} /> : <Upload size={14} />}
                  <span>{noteFileUploading ? '업로드 중' : '업로드'}</span>
                </button>
              </>
            ) : null}
          </div>
          {noteFileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{noteFileError}</span></div> : null}
          {noteFileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{noteFileMessage}</span></div> : null}
          {note.files.length === 0 ? (
            <DashboardEmpty label="첨부파일이 없습니다" />
          ) : (
            <div className="schedule-file-list">
              {note.files.map((file) => (
                <div className="schedule-file-row" key={file.id}>
                  <a className="schedule-file-download" href={file.downloadHref}>
                    <strong>{file.filename}</strong>
                    <span>{[file.size, file.uploadedAt ? formatDateTimeLabel(file.uploadedAt) : ''].filter(Boolean).join(' · ')}</span>
                  </a>
                  {file.canDelete && file.deleteHref ? (
                    <button
                      aria-label={`${file.filename} 삭제`}
                      className="customer-row-action schedule-file-delete-button"
                      disabled={noteFileDeletingId === file.id}
                      onClick={() => handleNoteFileDelete(file)}
                      type="button"
                    >
                      {noteFileDeletingId === file.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                      <span>삭제</span>
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
          <h3 className="customer-detail-section-heading">댓글</h3>
          {data.comments.canCreate ? (
            <form className="note-reply-compose" onSubmit={handleReplySubmit}>
              <textarea
                aria-label="댓글 내용"
                onChange={(event) => {
                  setReplyText(event.target.value);
                  setReplyError('');
                  setReplyMessage('');
                }}
                rows={3}
                value={replyText}
              />
              <button className="customer-row-action note-reply-submit-button" disabled={replySaving} type="submit">
                {replySaving ? <Loader2 className="spin-icon" size={14} /> : <MessageSquareText size={14} />}
                <span>추가</span>
              </button>
            </form>
          ) : null}
          {replyError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{replyError}</span></div> : null}
          {replyMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{replyMessage}</span></div> : null}
          {note.replies.length === 0 ? (
            <DashboardEmpty label="댓글이 없습니다" />
          ) : (
            <div className="note-reply-list">
              {note.replies.map((reply) => (
                <div className="note-reply-row" key={reply.id}>
                  <a className="note-reply-content" href={reply.djangoHref}>
                    <strong>{reply.author}</strong>
                    <span>{[reply.authorRole, reply.createdAt ? formatDateTimeLabel(reply.createdAt) : ''].filter(Boolean).join(' · ')}</span>
                    <p>{reply.content}</p>
                  </a>
                  {reply.canDelete && reply.deleteHref ? (
                    <button
                      aria-label={`${reply.author} 댓글 삭제`}
                      className="customer-row-action note-reply-delete-button"
                      disabled={replyDeletingId === reply.id}
                      onClick={() => handleReplyDelete(reply)}
                      type="button"
                    >
                      {replyDeletingId === reply.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                      <span>삭제</span>
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>

      <section className="dashboard-panel note-related-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Related notes</span>
            <h2>같은 고객의 최근 노트</h2>
          </div>
          <MessageSquareText size={18} />
        </div>
        <CustomerDetailNoteList emptyLabel="같은 고객의 다른 영업노트가 없습니다" notes={data.relatedNotes} />
      </section>
    </section>
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
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    ariaLabel="고객 선택"
                    onChange={(nextValue) => onCreateFormChange('followupId', nextValue)}
                    options={createCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={createForm.followupId}
                  />
                </div>
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

function ScheduleDetailPage({
  data,
  loading,
  onRefresh,
}: {
  data: ScheduleDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<ScheduleDetailData | null>;
}) {
  const currentSchedule = data?.schedule ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<ScheduleEditFormState>(() => makeScheduleEditForm(currentSchedule));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [fileUploading, setFileUploading] = useState(false);
  const [fileDeletingId, setFileDeletingId] = useState<number | null>(null);
  const [fileError, setFileError] = useState('');
  const [fileMessage, setFileMessage] = useState('');
  const [deliveryEditOpen, setDeliveryEditOpen] = useState(false);
  const [deliveryRows, setDeliveryRows] = useState<ScheduleDeliveryEditRow[]>(() => makeScheduleDeliveryEditRows(data?.deliveryItems ?? []));
  const [deliverySaving, setDeliverySaving] = useState(false);
  const [deliveryError, setDeliveryError] = useState('');
  const [deliveryMessage, setDeliveryMessage] = useState('');
  const [productOptions, setProductOptions] = useState<ProductOption[]>([]);
  const [productsLoaded, setProductsLoaded] = useState(false);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productError, setProductError] = useState('');
  const [prepaymentRows, setPrepaymentRows] = useState<SchedulePrepaymentEditRow[]>([]);
  const [prepaymentsLoading, setPrepaymentsLoading] = useState(false);
  const [prepaymentsError, setPrepaymentsError] = useState('');

  useEffect(() => {
    setEditForm(makeScheduleEditForm(currentSchedule));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setFileError('');
    setFileMessage('');
    setFileUploading(false);
    setFileDeletingId(null);
    setDeliveryEditOpen(false);
    setDeliveryRows(makeScheduleDeliveryEditRows(data?.deliveryItems ?? []));
    setDeliverySaving(false);
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
    setPrepaymentRows([]);
    setPrepaymentsLoading(false);
    setPrepaymentsError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [currentSchedule?.id]);

  useEffect(() => {
    if (
      !editOpen ||
      !currentSchedule?.canEdit ||
      editForm.activityType !== 'delivery' ||
      !editForm.followupId
    ) {
      setPrepaymentRows([]);
      setPrepaymentsLoading(false);
      setPrepaymentsError('');
      return undefined;
    }

    const followupId = Number(editForm.followupId);
    if (!followupId) {
      setPrepaymentRows([]);
      return undefined;
    }

    let active = true;
    setPrepaymentsLoading(true);
    setPrepaymentsError('');
    loadPrepayments(followupId, currentSchedule.id)
      .then((options) => {
        if (active) {
          setPrepaymentRows(makeSchedulePrepaymentRows(options));
        }
      })
      .catch((error) => {
        if (active) {
          setPrepaymentRows([]);
          setPrepaymentsError(error instanceof Error ? error.message : '선결제 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        if (active) {
          setPrepaymentsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [editOpen, editForm.activityType, editForm.followupId, currentSchedule?.canEdit, currentSchedule?.id]);

  const handleEditFieldChange = (field: keyof ScheduleEditFormState, value: string | boolean) => {
    setEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handlePrepaymentRowToggle = (id: number, selected: boolean) => {
    setPrepaymentRows((rows) => rows.map((row) => (
      row.id === id
        ? {
          ...row,
          selected,
          amountInput: selected && !row.amountInput && row.selectedAmount > 0 ? String(row.selectedAmount) : row.amountInput,
        }
        : row
    )));
    setEditError('');
    setEditMessage('');
  };

  const handlePrepaymentAmountChange = (id: number, amountInput: string) => {
    setPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput } : row
    )));
    setEditError('');
    setEditMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || !data?.edit || editSaving) {
      return;
    }
    if (!data.edit.canEdit) {
      setEditError(data.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const followupId = Number(editForm.followupId);
    if (!followupId) {
      setEditError('고객을 선택하세요.');
      return;
    }
    if (!editForm.activityType) {
      setEditError('활동 유형을 선택하세요.');
      return;
    }
    if (!editForm.status) {
      setEditError('일정 상태를 선택하세요.');
      return;
    }
    if (!editForm.visitDate) {
      setEditError('방문 날짜를 선택하세요.');
      return;
    }
    if (!editForm.visitTime) {
      setEditError('방문 시간을 선택하세요.');
      return;
    }

    const prepaymentSelections = prepaymentRows.filter((row) => row.selected);
    const usePrepayment = editForm.activityType === 'delivery' && editForm.usePrepayment;
    if (usePrepayment) {
      if (prepaymentsLoading) {
        setEditError('선결제 목록을 불러오는 중입니다.');
        return;
      }
      if (prepaymentsError) {
        setEditError(prepaymentsError);
        return;
      }
      if (!prepaymentSelections.length) {
        setEditError('사용할 선결제를 선택하세요.');
        return;
      }
      for (const [index, row] of prepaymentSelections.entries()) {
        const amount = Number(row.amountInput);
        if (!Number.isFinite(amount) || amount <= 0) {
          setEditError(`${index + 1}번째 선결제 차감 금액을 입력하세요.`);
          return;
        }
        if (amount > row.availableBalance) {
          setEditError(`${row.payerName} 선결제 잔액이 부족합니다.`);
          return;
        }
      }
    }

    const payload: ScheduleEditPayload = {
      activityType: editForm.activityType,
      expectedCloseDate: editForm.expectedCloseDate || undefined,
      expectedRevenue: editForm.expectedRevenue.trim() || undefined,
      followupId,
      location: editForm.location.trim() || undefined,
      notes: editForm.notes.trim() || undefined,
      probability: editForm.probability.trim() || undefined,
      prepayments: usePrepayment
        ? prepaymentSelections.map((row) => ({ id: row.id, amount: row.amountInput.trim() }))
        : [],
      purchaseConfirmed: editForm.purchaseConfirmed,
      status: editForm.status,
      usePrepayment,
      visitDate: editForm.visitDate,
      visitTime: editForm.visitTime,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateCustomerSchedule(payload, data.edit.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '일정을 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '일정 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleScheduleFileUploadClick = () => {
    if (!currentSchedule?.canEdit || !data?.links.uploadFiles) {
      setFileError('첨부파일 업로드 권한이 없습니다.');
      setFileMessage('');
      return;
    }
    fileInputRef.current?.click();
  };

  const handleScheduleFilesSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (!selectedFiles.length) {
      return;
    }

    if (!currentSchedule?.canEdit || !data?.links.uploadFiles) {
      setFileError('첨부파일 업로드 권한이 없습니다.');
      setFileMessage('');
      event.target.value = '';
      return;
    }

    if (currentSchedule.files.length + selectedFiles.length > 5) {
      setFileError(`첨부파일은 최대 5개까지 등록할 수 있습니다. 현재 ${currentSchedule.files.length}개가 등록되어 있습니다.`);
      setFileMessage('');
      event.target.value = '';
      return;
    }

    setFileUploading(true);
    setFileError('');
    setFileMessage('');
    try {
      const result = await uploadScheduleFiles(data.links.uploadFiles, selectedFiles);
      await onRefresh();
      setFileMessage(result.message || `${selectedFiles.length}개 파일을 업로드했습니다.`);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : '첨부파일 업로드에 실패했습니다.');
    } finally {
      setFileUploading(false);
      event.target.value = '';
    }
  };

  const handleScheduleFileDelete = async (file: ScheduleFileItem) => {
    if (fileDeletingId !== null) {
      return;
    }
    if (!currentSchedule?.canEdit || !file.canDelete || !file.deleteHref) {
      setFileError('첨부파일 삭제 권한이 없습니다.');
      setFileMessage('');
      return;
    }
    if (!window.confirm(`"${file.filename}" 파일을 삭제할까요?`)) {
      return;
    }

    setFileDeletingId(file.id);
    setFileError('');
    setFileMessage('');
    try {
      const result = await deleteScheduleFile(file.deleteHref);
      await onRefresh();
      setFileMessage(result.message || '첨부파일을 삭제했습니다.');
    } catch (error) {
      setFileError(error instanceof Error ? error.message : '첨부파일 삭제에 실패했습니다.');
    } finally {
      setFileDeletingId(null);
    }
  };

  const ensureProductsLoaded = async () => {
    if (productsLoaded || productsLoading) {
      return;
    }
    setProductsLoading(true);
    setProductError('');
    try {
      const products = await loadProducts();
      setProductOptions(products);
      setProductsLoaded(true);
    } catch (error) {
      setProductError(error instanceof Error ? error.message : '제품 목록을 불러오지 못했습니다.');
    } finally {
      setProductsLoading(false);
    }
  };

  const getDeliveryProductMatches = (query: string) => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return [];
    }
    return productOptions.filter((product) => (
      product.productCode.toLowerCase().includes(normalizedQuery) ||
      product.name.toLowerCase().includes(normalizedQuery) ||
      product.description.toLowerCase().includes(normalizedQuery) ||
      product.specification.toLowerCase().includes(normalizedQuery)
    )).slice(0, 6);
  };

  const handleDeliveryEditToggle = () => {
    if (!currentSchedule?.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }
    const willOpen = !deliveryEditOpen;
    setDeliveryRows(makeScheduleDeliveryEditRows(data.deliveryItems));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
    setDeliveryEditOpen((open) => !open);
    if (willOpen) {
      void ensureProductsLoaded();
    }
  };

  const handleDeliveryFieldChange = (rowId: string, field: ScheduleDeliveryEditField, value: string | boolean) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? { ...row, [field]: value } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryProductQueryChange = (rowId: string, value: string) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? { ...row, productId: '', productQuery: value } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryProductSelect = (rowId: string, product: ProductOption) => {
    const unitPrice = product.currentPrice || product.standardPrice || '';
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? {
        ...row,
        productId: String(product.id),
        productQuery: product.productCode,
        itemName: product.productCode,
        unit: product.unit || 'EA',
        unitPrice: unitPrice === '' ? '' : String(unitPrice),
      } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryProductClear = (rowId: string) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? { ...row, productId: '', productQuery: '' } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryAddRow = () => {
    setDeliveryRows((rows) => [...rows, makeScheduleDeliveryEditRow(undefined, rows.length)]);
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryRemoveRow = (rowId: string) => {
    setDeliveryRows((rows) => {
      const nextRows = rows.filter((row) => row.rowId !== rowId);
      return nextRows.length > 0 ? nextRows : [makeScheduleDeliveryEditRow(undefined, 0)];
    });
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliverySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || deliverySaving) {
      return;
    }
    if (!currentSchedule.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }

    const rowsWithInput = deliveryRows.filter((row) => (
      row.productId || row.itemName.trim() || row.quantity.trim() || row.unitPrice.trim() || row.notes.trim()
    ));
    if (!rowsWithInput.length) {
      setDeliveryError('품목명과 수량이 있는 납품 품목을 하나 이상 입력하세요.');
      return;
    }

    const payloadItems: ScheduleDeliveryItemPayload[] = [];
    for (const [index, row] of rowsWithInput.entries()) {
      const itemName = row.itemName.trim();
      if (!itemName) {
        setDeliveryError(`${index + 1}번째 품목명을 입력하세요.`);
        return;
      }
      const quantity = Number(row.quantity);
      if (!Number.isInteger(quantity) || quantity <= 0) {
        setDeliveryError(`${index + 1}번째 수량은 1 이상의 숫자로 입력하세요.`);
        return;
      }
      const unitPrice = row.unitPrice.trim();
      if (unitPrice && Number.isNaN(Number(unitPrice))) {
        setDeliveryError(`${index + 1}번째 단가는 숫자로 입력하세요.`);
        return;
      }
      if (unitPrice && Number(unitPrice) < 0) {
        setDeliveryError(`${index + 1}번째 단가는 0 이상이어야 합니다.`);
        return;
      }
      payloadItems.push({
        id: row.id,
        productId: row.productId ? Number(row.productId) : null,
        itemName,
        quantity,
        unit: row.unit.trim() || 'EA',
        unitPrice: unitPrice || null,
        taxInvoiceIssued: row.taxInvoiceIssued,
        notes: row.notes.trim(),
      });
    }

    setDeliverySaving(true);
    setDeliveryError('');
    setDeliveryMessage('');
    try {
      const updated = await updateScheduleDeliveryItems(data.links.updateDeliveryItems, payloadItems);
      const refreshed = await onRefresh();
      setDeliveryRows(makeScheduleDeliveryEditRows(refreshed?.deliveryItems ?? updated.deliveryItems ?? []));
      setDeliveryMessage(updated.message || '납품 품목을 저장했습니다.');
      setDeliveryEditOpen(false);
    } catch (error) {
      setDeliveryError(error instanceof Error ? error.message : '납품 품목 저장에 실패했습니다.');
    } finally {
      setDeliverySaving(false);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.schedule) {
    return (
      <section className="schedules-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>일정 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '일정 상세 API에 연결되지 않았습니다.'}</span>
          </div>
          <a href="/schedules/">목록</a>
        </div>
      </section>
    );
  }

  const schedule = data.schedule;
  const deliveryItems = data.deliveryItems;
  const prepaymentUsages = schedule.prepaymentUsages ?? [];
  const deliveryTotalAmount = deliveryItems.reduce((total, item) => total + (item.totalPrice || 0), 0);
  const prepaymentBaseAmount = deliveryTotalAmount > 0 ? deliveryTotalAmount : schedule.expectedRevenue;
  const selectedPrepaymentAmount = prepaymentRows.reduce((total, row) => {
    const amount = Number(row.amountInput);
    return row.selected && Number.isFinite(amount) && amount > 0 ? total + amount : total;
  }, 0);
  const payableAfterPrepayment = Math.max(prepaymentBaseAmount - selectedPrepaymentAmount, 0);
  const metrics = [
    { label: '일정 상태', value: schedule.statusLabel, detail: schedule.activityLabel, icon: CalendarDays, tone: schedule.overdue ? 'red' as const : 'blue' as const },
    { label: '방문 일시', value: schedule.date ? formatDateLabel(schedule.date) : '날짜 없음', detail: schedule.time || '시간 없음', icon: Clock, tone: 'green' as const },
    { label: '예상 매출', value: schedule.expectedRevenue > 0 ? formatWon(schedule.expectedRevenue) : '없음', detail: schedule.probability ? `${schedule.probability}%` : '확률 미입력', icon: CircleDollarSign, tone: 'amber' as const },
    { label: '보고/파일', value: `${formatNumber(schedule.historyCount)} / ${formatNumber(schedule.fileCount)}`, detail: '보고 / 첨부', icon: MessageSquareText, tone: 'teal' as const },
  ];

  return (
    <section className="schedules-page schedule-detail-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>일정 상세 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Schedule detail</span>
          <h2>{schedule.company || schedule.customer || schedule.activityLabel}</h2>
          <p>{[schedule.customer, schedule.department, schedule.activityLabel, schedule.owner].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/schedules/">목록</a>
          {data.links.customer ? <a className="route-secondary-action" href={data.links.customer}>고객</a> : null}
          <a className="route-secondary-action" href={data.links.djangoDetail}>Django 상세</a>
          {data.links.createNote ? <a className="route-secondary-action" href={data.links.createNote}>보고 작성</a> : null}
          {data.edit.canEdit ? (
            <button className="route-primary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
              <Check size={16} />
            </button>
          ) : null}
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="일정 상세 지표">
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

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel schedule-edit-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit schedule</span>
              <h2>일정 수정</h2>
            </div>
            {editSaving ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form schedule-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid schedules-create-grid">
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    ariaLabel="고객 선택"
                    onChange={(nextValue) => handleEditFieldChange('followupId', nextValue)}
                    options={data.edit.customers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={editForm.followupId}
                  />
                </div>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => handleEditFieldChange('activityType', event.target.value)}
                    required
                    value={editForm.activityType}
                  >
                    {data.edit.activityTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>상태</span>
                  <select
                    onChange={(event) => handleEditFieldChange('status', event.target.value)}
                    required
                    value={editForm.status}
                  >
                    {data.edit.statuses.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>방문 날짜</span>
                  <input
                    onChange={(event) => handleEditFieldChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={editForm.visitDate}
                  />
                </label>
                <label>
                  <span>방문 시간</span>
                  <input
                    onChange={(event) => handleEditFieldChange('visitTime', event.target.value)}
                    required
                    type="time"
                    value={editForm.visitTime}
                  />
                </label>
                <label>
                  <span>장소</span>
                  <input
                    onChange={(event) => handleEditFieldChange('location', event.target.value)}
                    value={editForm.location}
                  />
                </label>
                <label>
                  <span>예상 매출</span>
                  <input
                    inputMode="numeric"
                    min="0"
                    onChange={(event) => handleEditFieldChange('expectedRevenue', event.target.value)}
                    type="number"
                    value={editForm.expectedRevenue}
                  />
                </label>
                <label>
                  <span>성공 확률</span>
                  <input
                    inputMode="numeric"
                    max="100"
                    min="0"
                    onChange={(event) => handleEditFieldChange('probability', event.target.value)}
                    type="number"
                    value={editForm.probability}
                  />
                </label>
                <label>
                  <span>예상 종료일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('expectedCloseDate', event.target.value)}
                    type="date"
                    value={editForm.expectedCloseDate}
                  />
                </label>
              </div>
              <label className="schedule-edit-inline-check">
                <input
                  checked={editForm.purchaseConfirmed}
                  onChange={(event) => handleEditFieldChange('purchaseConfirmed', event.target.checked)}
                  type="checkbox"
                />
                <span>구매 확정</span>
              </label>
              {editForm.activityType === 'delivery' ? (
                <div className="schedule-prepayment-editor">
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={editForm.usePrepayment}
                      onChange={(event) => handleEditFieldChange('usePrepayment', event.target.checked)}
                      type="checkbox"
                    />
                    <span>선결제 사용</span>
                  </label>
                  {editForm.usePrepayment ? (
                    <div className="schedule-prepayment-body">
                      {prepaymentsError ? (
                        <div className="dashboard-api-alert compact">
                          <AlertTriangle size={16} />
                          <span>{prepaymentsError}</span>
                        </div>
                      ) : null}
                      {prepaymentsLoading ? (
                        <div className="schedule-prepayment-loading">
                          <Loader2 className="spin-icon" size={15} />
                          <span>선결제 조회 중</span>
                        </div>
                      ) : prepaymentRows.length > 0 ? (
                        <div className="schedule-prepayment-list">
                          {prepaymentRows.map((row) => (
                            <div className={row.selected ? 'schedule-prepayment-row selected' : 'schedule-prepayment-row'} key={row.id}>
                              <label className="schedule-prepayment-check">
                                <input
                                  checked={row.selected}
                                  onChange={(event) => handlePrepaymentRowToggle(row.id, event.target.checked)}
                                  type="checkbox"
                                />
                                <span>
                                  <strong>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '입금일 없음', row.payerName].filter(Boolean).join(' · ')}</strong>
                                  <small>{[row.customerName, `잔액 ${formatWon(row.balance)}`, `사용 가능 ${formatWon(row.availableBalance)}`].filter(Boolean).join(' · ')}</small>
                                </span>
                              </label>
                              <label className="schedule-prepayment-amount">
                                <span>차감</span>
                                <input
                                  disabled={!row.selected}
                                  inputMode="numeric"
                                  min="0"
                                  onChange={(event) => handlePrepaymentAmountChange(row.id, event.target.value)}
                                  type="number"
                                  value={row.amountInput}
                                />
                              </label>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <DashboardEmpty label="사용 가능한 선결제가 없습니다" />
                      )}
                      <div className="schedule-prepayment-totals">
                        <span>납품 합계 <strong>{formatWon(prepaymentBaseAmount)}</strong></span>
                        <span>차감 <strong>{formatWon(selectedPrepaymentAmount)}</strong></span>
                        <span>실결제 <strong>{formatWon(payableAfterPrepayment)}</strong></span>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <label>
                <span>메모</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('notes', event.target.value)}
                  rows={4}
                  value={editForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={data.edit.djangoUrl || data.links.djangoEdit}>
                  Django 수정
                  <MoveUpRight size={15} />
                </a>
                <button className="route-primary-action" disabled={editSaving} type="submit">
                  {editSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      <div className="note-detail-layout schedule-detail-layout">
        <section className="dashboard-panel note-detail-main schedule-detail-main">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Schedule</span>
              <h2>일정 내용</h2>
            </div>
            <ScheduleStatusBadge schedule={schedule} />
          </div>
          <div className="note-detail-content schedule-detail-content">
            {schedule.notesFull || schedule.notes ? <p>{schedule.notesFull || schedule.notes}</p> : <DashboardEmpty label="일정 메모가 없습니다" />}
          </div>
          <div className="note-detail-field-grid">
            <div className="note-detail-field">
              <span>장소</span>
              <p>{schedule.location || '장소 없음'}</p>
            </div>
            <div className="note-detail-field">
              <span>예상 종료일</span>
              <p>{schedule.expectedCloseDate ? formatDateLabel(schedule.expectedCloseDate) : '없음'}</p>
            </div>
            <div className="note-detail-field">
              <span>구매 확정</span>
              <p>{schedule.purchaseConfirmed ? '확정' : '미확정'}</p>
            </div>
            <div className="note-detail-field">
              <span>이메일 스레드</span>
              <p>{formatNumber(schedule.emailThreadCount)}건</p>
            </div>
          </div>
        </section>

        <aside className="dashboard-panel note-detail-side schedule-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Follow-up</span>
              <h2>연결 정보</h2>
            </div>
            <PanelRight size={18} />
          </div>
          <div className="customer-detail-summary">
            <dl>
              <div>
                <dt>고객</dt>
                <dd>{[schedule.company, schedule.department, schedule.customer].filter(Boolean).join(' · ') || '고객 없음'}</dd>
              </div>
              <div>
                <dt>담당자</dt>
                <dd>{schedule.owner}</dd>
              </div>
              <div>
                <dt>일정일</dt>
                <dd className={schedule.overdue ? 'customer-overdue-text' : ''}>
                  {[schedule.date ? formatDateLabel(schedule.date) : '', schedule.time].filter(Boolean).join(' ') || '일정 없음'}
                </dd>
              </div>
              <div>
                <dt>선결제</dt>
                <dd>{schedule.usePrepayment ? formatWon(schedule.prepaymentAmount) : '미사용'}</dd>
              </div>
            </dl>
            {prepaymentUsages.length > 0 ? (
              <div className="schedule-prepayment-usage-list">
                {prepaymentUsages.map((usage) => (
                  <div key={usage.id}>
                    <span>{[usage.paymentDate ? formatDateLabel(usage.paymentDate) : '', usage.payerName].filter(Boolean).join(' · ') || '선결제'}</span>
                    <strong>{formatWon(usage.amount)}</strong>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          <div className="customers-side-actions note-detail-actions">
            {data.links.customer ? <a href={data.links.customer}>React 고객 상세</a> : null}
            {data.links.djangoCustomer ? <a href={data.links.djangoCustomer}>Django 고객 상세</a> : null}
            {data.links.createNote ? <a href={data.links.createNote}>보고 작성</a> : null}
            <a href={data.links.calendar}>일정 캘린더</a>
          </div>
          <div className="schedule-file-heading schedule-delivery-heading">
            <h3 className="customer-detail-section-heading">납품 품목</h3>
            {schedule.canEdit && data.links.updateDeliveryItems ? (
              <button
                className="customer-row-action schedule-delivery-edit-toggle"
                disabled={deliverySaving}
                onClick={handleDeliveryEditToggle}
                type="button"
              >
                {deliveryEditOpen ? <ChevronDown size={14} /> : <ListChecks size={14} />}
                <span>{deliveryEditOpen ? '닫기' : '편집'}</span>
              </button>
            ) : null}
          </div>
          {deliveryError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{deliveryError}</span></div> : null}
          {deliveryMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{deliveryMessage}</span></div> : null}
          {deliveryEditOpen ? (
            <form className="schedule-delivery-edit-form" onSubmit={handleDeliverySubmit}>
              {productError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{productError}</span></div> : null}
              <div className="schedule-delivery-edit-list">
                {deliveryRows.map((row, index) => {
                  const productMatches = getDeliveryProductMatches(row.productQuery);
                  return (
                    <div className="schedule-delivery-edit-row" key={row.rowId}>
                      <label className="schedule-delivery-product-field">
                        <span>제품 검색</span>
                        <div className="schedule-delivery-product-control">
                          <Search size={14} />
                          <input
                            onChange={(event) => handleDeliveryProductQueryChange(row.rowId, event.target.value)}
                            onFocus={() => void ensureProductsLoaded()}
                            placeholder="품번/설명 검색"
                            value={row.productQuery}
                          />
                          {row.productId ? (
                            <button
                              aria-label={`${index + 1}번째 납품 품목 제품 선택 해제`}
                              className="schedule-delivery-product-clear"
                              disabled={deliverySaving}
                              onClick={() => handleDeliveryProductClear(row.rowId)}
                              type="button"
                            >
                              <X size={13} />
                            </button>
                          ) : null}
                        </div>
                        {row.productId ? <small>제품 마스터 연결됨</small> : null}
                        {row.productQuery.trim() && !row.productId ? (
                          <div className="schedule-delivery-product-results">
                            {productsLoading ? (
                              <span><Loader2 className="spin-icon" size={13} /> 제품 검색 중</span>
                            ) : productMatches.length > 0 ? (
                              productMatches.map((product) => (
                                <button
                                  key={product.id}
                                  onClick={() => handleDeliveryProductSelect(row.rowId, product)}
                                  type="button"
                                >
                                  <strong>{product.productCode}</strong>
                                  <span>{[product.description, product.specification, product.unit, formatWon(product.currentPrice)].filter(Boolean).join(' · ')}</span>
                                </button>
                              ))
                            ) : productsLoaded ? (
                              <span>검색 결과 없음</span>
                            ) : null}
                          </div>
                        ) : null}
                      </label>
                      <label className="schedule-delivery-name-field">
                        <span>품목명</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'itemName', event.target.value)}
                          required
                          value={row.itemName}
                        />
                      </label>
                      <label>
                        <span>수량</span>
                        <input
                          inputMode="numeric"
                          min="1"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'quantity', event.target.value)}
                          required
                          type="number"
                          value={row.quantity}
                        />
                      </label>
                      <label>
                        <span>단위</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'unit', event.target.value)}
                          value={row.unit}
                        />
                      </label>
                      <label>
                        <span>단가</span>
                        <input
                          inputMode="numeric"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'unitPrice', event.target.value)}
                          type="number"
                          value={row.unitPrice}
                        />
                      </label>
                      <label className="schedule-edit-inline-check schedule-delivery-tax-check">
                        <input
                          checked={row.taxInvoiceIssued}
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'taxInvoiceIssued', event.target.checked)}
                          type="checkbox"
                        />
                        <span>세금계산서</span>
                      </label>
                      <label className="schedule-delivery-notes-field">
                        <span>비고</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'notes', event.target.value)}
                          value={row.notes}
                        />
                      </label>
                      <button
                        aria-label={`${index + 1}번째 납품 품목 삭제`}
                        className="customer-row-action schedule-delivery-remove-button"
                        disabled={deliveryRows.length <= 1 || deliverySaving}
                        onClick={() => handleDeliveryRemoveRow(row.rowId)}
                        type="button"
                      >
                        <Trash2 size={14} />
                        <span>삭제</span>
                      </button>
                    </div>
                  );
                })}
              </div>
              <div className="notes-create-actions schedule-delivery-edit-actions">
                <button className="route-secondary-action" disabled={deliverySaving} onClick={handleDeliveryAddRow} type="button">
                  <Plus size={15} />
                  품목 추가
                </button>
                <button className="route-primary-action" disabled={deliverySaving} type="submit">
                  {deliverySaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : deliveryItems.length === 0 ? (
            <DashboardEmpty label="등록된 납품 품목이 없습니다" />
          ) : (
            <div className="schedule-delivery-list">
              {deliveryItems.map((item) => (
                <div key={item.id}>
                  <strong>{item.itemName}</strong>
                  <span>{[`${formatNumber(item.quantity)}${item.unit}`, item.totalPrice ? formatWon(item.totalPrice) : '', item.taxInvoiceIssued ? '세금계산서 발행' : '미발행'].filter(Boolean).join(' · ')}</span>
                  {item.notes ? <p>{item.notes}</p> : null}
                </div>
              ))}
            </div>
          )}
          <div className="schedule-file-heading">
            <h3 className="customer-detail-section-heading">첨부파일</h3>
            {schedule.canEdit && data.links.uploadFiles ? (
              <>
                <input
                  aria-label="일정 첨부파일 선택"
                  className="schedule-file-input"
                  multiple
                  onChange={handleScheduleFilesSelected}
                  ref={fileInputRef}
                  type="file"
                />
                <button
                  className="customer-row-action schedule-file-upload-button"
                  disabled={fileUploading}
                  onClick={handleScheduleFileUploadClick}
                  type="button"
                >
                  {fileUploading ? <Loader2 className="spin-icon" size={14} /> : <Upload size={14} />}
                  <span>{fileUploading ? '업로드 중' : '업로드'}</span>
                </button>
              </>
            ) : null}
          </div>
          {fileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{fileError}</span></div> : null}
          {fileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{fileMessage}</span></div> : null}
          {schedule.files.length === 0 ? (
            <DashboardEmpty label="첨부파일이 없습니다" />
          ) : (
            <div className="schedule-file-list">
              {schedule.files.map((file) => (
                <div className="schedule-file-row" key={file.id}>
                  <a className="schedule-file-download" href={file.downloadHref}>
                    <strong>{file.filename}</strong>
                    <span>{[file.size, file.uploadedAt ? formatDateTimeLabel(file.uploadedAt) : ''].filter(Boolean).join(' · ')}</span>
                  </a>
                  {file.canDelete && file.deleteHref ? (
                    <button
                      aria-label={`${file.filename} 삭제`}
                      className="customer-row-action schedule-file-delete-button"
                      disabled={fileDeletingId === file.id}
                      onClick={() => handleScheduleFileDelete(file)}
                      type="button"
                    >
                      {fileDeletingId === file.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                      <span>삭제</span>
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>

      <section className="dashboard-panel note-related-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Related notes</span>
            <h2>이 일정의 보고 기록</h2>
          </div>
          <MessageSquareText size={18} />
        </div>
        <CustomerDetailNoteList emptyLabel="이 일정에 연결된 영업노트가 없습니다" notes={data.relatedNotes} />
      </section>
    </section>
  );
}

function SchedulesPage({
  activityType,
  createError,
  createForm,
  createdDetailHref,
  createMessage,
  createOpen,
  creating,
  data,
  loading,
  owner,
  query,
  range,
  status,
  onActivityTypeChange,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onOwnerChange,
  onQueryChange,
  onRangeChange,
  onStatusChange,
}: {
  activityType: string;
  createError: string;
  createForm: ScheduleCreateFormState;
  createdDetailHref: string;
  createMessage: string;
  createOpen: boolean;
  creating: boolean;
  data: SchedulesData | null;
  loading: boolean;
  owner: string;
  query: string;
  range: string;
  status: string;
  onActivityTypeChange: (value: string) => void;
  onCreateFormChange: (field: keyof ScheduleCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
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
  const createConfig = data.create;
  const canCreateSchedules = createConfig.canCreate;
  const createCustomers = createConfig.customers;
  const createActivityTypes = createConfig.activityTypes;

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
          <button
            className={canCreateSchedules ? 'route-primary-action' : 'route-secondary-action'}
            onClick={() => onCreateOpenChange(!createOpen)}
            type="button"
          >
            {canCreateSchedules ? '일정 등록' : '등록 권한 없음'}
            <Plus size={16} />
          </button>
        </div>
      </div>

      {createOpen ? (
        <section className="dashboard-panel notes-create-panel schedules-create-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Quick schedule</span>
              <h2>고객 일정 빠른 등록</h2>
            </div>
            {creating ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          {createMessage ? (
            <div className="notes-action-feedback success">
              <span>{createMessage}</span>
              {createdDetailHref ? <a href={createdDetailHref}>상세 열기</a> : null}
            </div>
          ) : null}
          {createError ? <div className="notes-action-feedback error">{createError}</div> : null}
          {!canCreateSchedules ? (
            <DashboardEmpty label={createConfig.message || '일정 등록 권한이 없습니다'} />
          ) : createCustomers.length === 0 ? (
            <DashboardEmpty label="등록 가능한 담당 고객이 없습니다" />
          ) : createActivityTypes.length === 0 ? (
            <DashboardEmpty label="등록 가능한 활동 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid schedules-create-grid">
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    ariaLabel="고객 선택"
                    onChange={(nextValue) => onCreateFormChange('followupId', nextValue)}
                    options={createCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={createForm.followupId}
                  />
                </div>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => onCreateFormChange('activityType', event.target.value)}
                    required
                    value={createForm.activityType}
                  >
                    {createActivityTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>방문 날짜</span>
                  <input
                    onChange={(event) => onCreateFormChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={createForm.visitDate}
                  />
                </label>
                <label>
                  <span>방문 시간</span>
                  <input
                    onChange={(event) => onCreateFormChange('visitTime', event.target.value)}
                    required
                    type="time"
                    value={createForm.visitTime}
                  />
                </label>
                <label>
                  <span>장소</span>
                  <input
                    onChange={(event) => onCreateFormChange('location', event.target.value)}
                    placeholder="방문 장소"
                    value={createForm.location}
                  />
                </label>
                <label>
                  <span>예상 매출</span>
                  <input
                    inputMode="numeric"
                    min="0"
                    onChange={(event) => onCreateFormChange('expectedRevenue', event.target.value)}
                    placeholder="원"
                    type="number"
                    value={createForm.expectedRevenue}
                  />
                </label>
                <label>
                  <span>성공 확률</span>
                  <input
                    inputMode="numeric"
                    max="100"
                    min="0"
                    onChange={(event) => onCreateFormChange('probability', event.target.value)}
                    placeholder="0-100"
                    type="number"
                    value={createForm.probability}
                  />
                </label>
              </div>
              <label>
                <span>메모</span>
                <textarea
                  onChange={(event) => onCreateFormChange('notes', event.target.value)}
                  placeholder="일정 메모, 준비사항, 후속 확인 사항"
                  rows={3}
                  value={createForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={data.links.createSchedule}>
                  상세 등록
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

function PrepaymentStatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={`prepayment-status ${status || 'unknown'}`}>{label || status || '상태 없음'}</span>;
}

function PrepaymentsTable({ data }: { data: PrepaymentsData }) {
  if (data.prepayments.length === 0) {
    return <DashboardEmpty label="표시할 선결제가 없습니다" />;
  }

  return (
    <div className="customers-table-wrap prepayments-table-wrap">
      <table className="customers-table prepayments-table">
        <thead>
          <tr>
            <th>고객</th>
            <th>입금 정보</th>
            <th>금액</th>
            <th>잔액</th>
            <th>상태</th>
            <th>담당</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          {data.prepayments.map((prepayment) => (
            <tr key={prepayment.id}>
              <td>
                <a className="customer-name-link" href={prepayment.customerHref || prepayment.djangoCustomerHref}>
                  <strong>{prepayment.companyName || prepayment.customerName || '고객 미지정'}</strong>
                  <span>{[prepayment.departmentName, prepayment.customerName].filter(Boolean).join(' · ')}</span>
                </a>
                {prepayment.memo ? <small className="customer-muted-cell">{prepayment.memo}</small> : null}
              </td>
              <td>
                <div className="prepayment-info-cell">
                  <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                  <span>{[prepayment.payerName || '입금자 미지정', prepayment.paymentMethodLabel].filter(Boolean).join(' · ')}</span>
                  {prepayment.usageCount > 0 ? <small>사용 {formatNumber(prepayment.usageCount)}건</small> : null}
                </div>
              </td>
              <td>
                <strong>{formatWon(prepayment.amount)}</strong>
                <small className="customer-muted-cell">사용 {formatWon(prepayment.usedAmount)}</small>
              </td>
              <td>
                <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                  {formatWon(prepayment.balance)}
                </strong>
              </td>
              <td>
                <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
              </td>
              <td>
                <span className="customer-muted-cell">{prepayment.ownerName}</span>
              </td>
              <td>
                <div className="customer-row-actions">
                  <a className="customer-row-action" href={`/prepayments/${prepayment.id}/`}>상세</a>
                  {prepayment.canManage ? <a className="customer-row-action" href={`/prepayments/${prepayment.id}/edit/`}>수정</a> : null}
                  {prepayment.customerPrepaymentHref || prepayment.djangoCustomerPrepaymentHref ? (
                    <a className="customer-row-action" href={prepayment.customerPrepaymentHref || prepayment.djangoCustomerPrepaymentHref}>고객별</a>
                  ) : null}
                  <a className="customer-row-action" href={prepayment.href}>Django</a>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PrepaymentsPage({
  data,
  dataFilter,
  filterUser,
  loading,
  query,
  status,
  onDataFilterChange,
  onFilterUserChange,
  onQueryChange,
  onStatusChange,
}: {
  data: PrepaymentsData | null;
  dataFilter: string;
  filterUser: string;
  loading: boolean;
  query: string;
  status: string;
  onDataFilterChange: (value: string) => void;
  onFilterUserChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '총 선결제', value: formatWon(data.metrics.totalAmount), detail: `${formatNumber(data.metrics.filteredPrepayments)}건`, icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.totalBalance), detail: '사용 가능 잔액', icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.totalUsed), detail: '차감 누적', icon: Activity, tone: 'amber' as const },
    { label: '사용 가능', value: `${formatNumber(data.metrics.activeCount)}건`, detail: `소진 ${formatNumber(data.metrics.depletedCount)}건`, icon: CircleDollarSign, tone: 'teal' as const },
  ];
  const showOwnerSelect = dataFilter === 'user';

  return (
    <section className="prepayments-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>선결제 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Prepayments</span>
          <h2>{data.scope.label || '선결제 현황'}</h2>
          <p>입금액, 사용액, 잔액을 고객 단위로 확인하고 원본 Django 관리 화면으로 이어갑니다.</p>
        </div>
        <div className="schedules-summary-actions">
          {data.links.create ? (
            <a className="route-primary-action" href="/prepayments/new/">
              선결제 등록
              <Plus size={16} />
            </a>
          ) : null}
          <a className="route-secondary-action" href={data.links.djangoList}>Django 관리</a>
          <a className="route-secondary-action" href={data.links.excel}>엑셀</a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="선결제 핵심 지표">
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

      <div className="customers-filter-bar prepayments-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 업체, 부서, 입금자 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onDataFilterChange(event.target.value)} value={dataFilter}>
          {data.options.dataFilters.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select disabled={!showOwnerSelect} onChange={(event) => onFilterUserChange(event.target.value)} value={filterUser}>
          <option value="">직원 선택</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
      </div>

      {data.metrics.truncated ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>결과가 많아 최근 {formatNumber(data.metrics.returnedCount)}건만 표시합니다. 검색이나 상태 필터를 좁혀 확인하세요.</span>
        </div>
      ) : null}

      <section className="dashboard-panel prepayments-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Prepayment list</span>
            <h2>선결제 목록</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
        </div>
        <PrepaymentsTable data={data} />
      </section>
    </section>
  );
}

function PrepaymentCustomerPage({
  data,
  loading,
  selectedUser,
  onSelectedUserChange,
}: {
  data: PrepaymentCustomerData | null;
  loading: boolean;
  selectedUser: string;
  onSelectedUserChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객별 선결제 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '총 선결제', value: formatWon(data.metrics.totalAmount), detail: `${formatNumber(data.metrics.totalCount)}건`, icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.totalBalance), detail: `${data.scope.targetUserName || '담당'} 기준`, icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.totalUsed), detail: '차감 누적', icon: Activity, tone: 'amber' as const },
    { label: '사용 가능', value: `${formatNumber(data.metrics.activeCount)}건`, detail: `소진 ${formatNumber(data.metrics.depletedCount)}건 · 취소 ${formatNumber(data.metrics.cancelledCount)}건`, icon: ListChecks, tone: 'teal' as const },
  ];

  return (
    <section className="prepayments-page prepayment-customer-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>고객별 선결제 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Customer prepayments</span>
          <h2>{data.scope.name || data.customer.customerName || '고객별 선결제'}</h2>
          <p>
            {[
              data.scope.mode === 'department' ? '부서 전체 고객 기준' : '고객 기준',
              data.scope.targetUserName ? `${data.scope.targetUserName} 등록분` : '',
            ].filter(Boolean).join(' · ')}
          </p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.prepayments}>선결제 목록</a>
          <a className="route-secondary-action" href={data.links.djangoCustomer}>Django 고객별</a>
          <a className="route-secondary-action" href={data.links.djangoExcel}>엑셀</a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객별 선결제 지표">
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

      <div className="prepayment-customer-layout">
        <section className="dashboard-panel prepayments-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Department scope</span>
              <h2>선결제 내역</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
          </div>
          {data.scope.canSelectUser ? (
            <div className="prepayment-customer-filter">
              <label>
                <span>조회 사용자</span>
                <select onChange={(event) => onSelectedUserChange(event.target.value)} value={selectedUser || (data.scope.targetUserId ? String(data.scope.targetUserId) : '')}>
                  <option value="">현재 선택 사용자</option>
                  {data.options.owners.map((owner) => (
                    <option key={owner.id} value={owner.id}>{owner.name}</option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {data.prepayments.length === 0 ? (
            <DashboardEmpty label="표시할 선결제 내역이 없습니다" />
          ) : (
            <div className="customers-table-wrap prepayments-table-wrap">
              <table className="customers-table prepayments-table prepayment-customer-table">
                <thead>
                  <tr>
                    <th>고객</th>
                    <th>입금 정보</th>
                    <th>금액</th>
                    <th>잔액</th>
                    <th>상태</th>
                    <th>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {data.prepayments.map((prepayment) => (
                    <tr key={prepayment.id}>
                      <td>
                        <a className="customer-name-link" href={prepayment.customerHref || prepayment.djangoCustomerHref}>
                          <strong>{prepayment.customerName || data.customer.customerName || '고객 미정'}</strong>
                          <span>{[prepayment.companyName, prepayment.departmentName].filter(Boolean).join(' · ')}</span>
                        </a>
                      </td>
                      <td>
                        <div className="prepayment-info-cell">
                          <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                          <span>{[prepayment.payerName || '입금자 미지정', prepayment.paymentMethodLabel].filter(Boolean).join(' · ')}</span>
                          {prepayment.usageCount > 0 ? <small>사용 {formatNumber(prepayment.usageCount)}건</small> : null}
                        </div>
                      </td>
                      <td>
                        <strong>{formatWon(prepayment.amount)}</strong>
                        <small className="customer-muted-cell">사용 {formatWon(prepayment.usedAmount)}</small>
                      </td>
                      <td>
                        <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                          {formatWon(prepayment.balance)}
                        </strong>
                      </td>
                      <td>
                        <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
                      </td>
                      <td>
                        <div className="customer-row-actions">
                          <a className="customer-row-action" href={`/prepayments/${prepayment.id}/`}>상세</a>
                          {prepayment.canManage ? <a className="customer-row-action" href={`/prepayments/${prepayment.id}/edit/`}>수정</a> : null}
                          <a className="customer-row-action" href={prepayment.href}>Django</a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="dashboard-panel prepayment-customer-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customers</span>
              <h2>{data.scope.mode === 'department' ? '부서 고객' : '기준 고객'}</h2>
            </div>
            <Users size={18} />
          </div>
          <div className="prepayment-customer-list">
            {data.departmentCustomers.map((customer) => (
              <a className={customer.id === data.customer.id ? 'active' : ''} href={`/prepayments/customer/${customer.id}/`} key={customer.id}>
                <strong>{customer.customerName}</strong>
                <span>{customer.ownerName}</span>
              </a>
            ))}
          </div>
          <div className="customers-side-actions">
            <a href={data.links.customerDetail || data.links.djangoCustomerDetail}>고객 상세</a>
            <a href={data.links.djangoCustomerDetail}>Django 고객 상세</a>
            <a href={data.links.djangoCustomer}>Django 고객별 선결제</a>
          </div>
        </aside>
      </div>
    </section>
  );
}

function PrepaymentFormFields({
  form,
  options,
  saving,
  showStatus,
  submitLabel,
  onChange,
  onSubmit,
  secondaryActions,
}: {
  form: PrepaymentFormState;
  options: {
    customers: PrepaymentCreateData['create']['customers'];
    paymentMethods: PrepaymentCreateData['create']['paymentMethods'];
    statuses: PrepaymentCreateData['create']['statuses'];
  };
  saving: boolean;
  showStatus: boolean;
  submitLabel: string;
  onChange: (field: keyof PrepaymentFormState, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  secondaryActions?: React.ReactNode;
}) {
  return (
    <form className="notes-create-form prepayment-form" onSubmit={onSubmit}>
      <div className="notes-create-grid prepayment-form-grid">
        <div className="form-field">
          <span>고객</span>
          <SearchableSelect
            ariaLabel="고객 선택"
            onChange={(nextValue) => onChange('customerId', nextValue)}
            options={options.customers.map(makeCustomerSelectOption)}
            placeholder="고객, 회사, 부서 검색"
            value={form.customerId}
          />
        </div>
        <label>
          <span>입금일</span>
          <input
            onChange={(event) => onChange('paymentDate', event.target.value)}
            required
            type="date"
            value={form.paymentDate}
          />
        </label>
        <label>
          <span>선결제 금액</span>
          <input
            inputMode="numeric"
            min="1"
            onChange={(event) => onChange('amount', event.target.value)}
            placeholder="예: 250000"
            required
            type="number"
            value={form.amount}
          />
        </label>
        {showStatus ? (
          <label>
            <span>잔액</span>
            <input
              inputMode="numeric"
              min="0"
              onChange={(event) => onChange('balance', event.target.value)}
              required
              type="number"
              value={form.balance}
            />
          </label>
        ) : null}
        <label>
          <span>입금 방법</span>
          <select
            onChange={(event) => onChange('paymentMethod', event.target.value)}
            required
            value={form.paymentMethod}
          >
            {options.paymentMethods.map((method) => (
              <option key={method.value} value={method.value}>{method.label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>입금자명</span>
          <input
            onChange={(event) => onChange('payerName', event.target.value)}
            placeholder="실제 입금자"
            value={form.payerName}
          />
        </label>
        {showStatus ? (
          <label>
            <span>상태</span>
            <select
              onChange={(event) => onChange('status', event.target.value)}
              required
              value={form.status}
            >
              {options.statuses.map((statusOption) => (
                <option key={statusOption.value} value={statusOption.value}>{statusOption.label}</option>
              ))}
            </select>
          </label>
        ) : null}
      </div>
      <label>
        <span>메모</span>
        <textarea
          onChange={(event) => onChange('memo', event.target.value)}
          rows={4}
          value={form.memo}
        />
      </label>
      <div className="notes-create-actions">
        {secondaryActions}
        <button className="route-primary-action" disabled={saving} type="submit">
          {saving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

function PrepaymentCreatePage({
  data,
  loading,
}: {
  data: PrepaymentCreateData | null;
  loading: boolean;
}) {
  const [form, setForm] = useState<PrepaymentFormState>(() => makeEmptyPrepaymentForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [createdHref, setCreatedHref] = useState('');

  useEffect(() => {
    if (!data?.create.customers.length || form.customerId) {
      return;
    }
    setForm((previous) => ({
      ...previous,
      customerId: String(data.create.customers[0].id),
    }));
  }, [data?.create.customers, form.customerId]);

  const handleChange = (field: keyof PrepaymentFormState, value: string) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
      ...(field === 'amount' && !previous.balance ? { balance: value } : {}),
    }));
    setError('');
    setMessage('');
    setCreatedHref('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) {
      return;
    }
    if (!data.create.canCreate) {
      setError(data.create.message || '등록 권한이 없습니다.');
      return;
    }
    const customerId = Number(form.customerId);
    if (!customerId) {
      setError('고객을 선택하세요.');
      return;
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setError('선결제 금액을 입력하세요.');
      return;
    }
    if (!form.paymentDate) {
      setError('입금일을 선택하세요.');
      return;
    }

    const payload: PrepaymentFormPayload = {
      amount: form.amount,
      customerId,
      memo: form.memo.trim() || undefined,
      payerName: form.payerName.trim() || undefined,
      paymentDate: form.paymentDate,
      paymentMethod: form.paymentMethod,
    };

    setSaving(true);
    setError('');
    setMessage('');
    setCreatedHref('');
    try {
      const created = await createCustomerPrepayment(payload, data.create.submitUrl);
      setMessage(created.message || '선결제를 등록했습니다.');
      setCreatedHref(created.href || (created.prepaymentId ? `/prepayments/${created.prepaymentId}/` : ''));
      setForm((previous) => ({
        ...makeEmptyPrepaymentForm(),
        customerId: previous.customerId,
      }));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '선결제 등록에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 등록 정보를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const formOptions = {
    customers: data.create.customers,
    paymentMethods: data.create.paymentMethods,
    statuses: data.create.statuses,
  };

  return (
    <section className="prepayments-page prepayment-detail-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>선결제 등록 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">New prepayment</span>
          <h2>선결제 등록</h2>
          <p>고객별 입금액을 등록하고 납품 일정에서 차감할 수 있게 준비합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/prepayments/">목록</a>
          <a className="route-secondary-action" href={data.create.djangoUrl}>Django 등록</a>
        </div>
      </div>

      <section className="dashboard-panel notes-create-panel prepayment-editor-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Prepayment form</span>
            <h2>입금 정보</h2>
          </div>
          {saving ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
        </div>
        {message ? (
          <div className="notes-action-feedback success">
            <span>{message}</span>
            {createdHref ? <a href={createdHref}>상세 열기</a> : null}
          </div>
        ) : null}
        {error ? <div className="notes-action-feedback error">{error}</div> : null}
        {!data.create.canCreate ? (
          <DashboardEmpty label={data.create.message || '선결제 등록 권한이 없습니다'} />
        ) : (
          <PrepaymentFormFields
            form={form}
            options={formOptions}
            saving={saving}
            secondaryActions={<a className="route-secondary-action" href={data.links.djangoList}>Django 목록</a>}
            showStatus={false}
            submitLabel="등록"
            onChange={handleChange}
            onSubmit={handleSubmit}
          />
        )}
      </section>
    </section>
  );
}

function PrepaymentDetailPage({
  data,
  editRoute,
  loading,
  onRefresh,
}: {
  data: PrepaymentDetailData | null;
  editRoute: boolean;
  loading: boolean;
  onRefresh: () => Promise<PrepaymentDetailData | null>;
}) {
  const prepayment = data?.prepayment ?? null;
  const [form, setForm] = useState<PrepaymentFormState>(() => makePrepaymentEditForm(prepayment));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [transferUserId, setTransferUserId] = useState('');
  const [transferReason, setTransferReason] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [actionBusy, setActionBusy] = useState<'cancel' | 'delete' | 'transfer' | ''>('');
  const [actionError, setActionError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const transferUserIdsKey = data?.actions.transferUsers.map((user) => user.id).join(',') ?? '';

  useEffect(() => {
    setForm(makePrepaymentEditForm(prepayment));
    setError('');
    setMessage('');
    setSaving(false);
    setCancelReason('');
    setTransferReason('');
    setDeleteConfirm('');
    setActionBusy('');
    setActionError('');
    setActionMessage('');
  }, [prepayment?.id]);

  useEffect(() => {
    const transferUsers = data?.actions.transferUsers ?? [];
    const firstTransferUserId = transferUsers[0] ? String(transferUsers[0].id) : '';
    setTransferUserId((current) => {
      if (current && transferUsers.some((user) => String(user.id) === current)) {
        return current;
      }
      return firstTransferUserId;
    });
  }, [prepayment?.id, transferUserIdsKey]);

  const handleChange = (field: keyof PrepaymentFormState, value: string) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setError('');
    setMessage('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || saving) {
      return;
    }
    if (!data.edit.canEdit || !data.edit.submitUrl) {
      setError(data.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const customerId = Number(form.customerId);
    const amount = Number(form.amount);
    const balance = Number(form.balance);
    if (!customerId) {
      setError('고객을 선택하세요.');
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setError('선결제 금액을 입력하세요.');
      return;
    }
    if (!Number.isFinite(balance) || balance < 0) {
      setError('잔액은 0원 이상이어야 합니다.');
      return;
    }
    if (balance > amount) {
      setError('잔액은 선결제 금액보다 클 수 없습니다.');
      return;
    }

    const payload: PrepaymentFormPayload = {
      amount: form.amount,
      balance: form.balance,
      customerId,
      memo: form.memo.trim() || undefined,
      payerName: form.payerName.trim() || undefined,
      paymentDate: form.paymentDate,
      paymentMethod: form.paymentMethod,
      status: form.status,
    };

    setSaving(true);
    setError('');
    setMessage('');
    try {
      const updated = await updateCustomerPrepayment(payload, data.edit.submitUrl);
      await onRefresh();
      setMessage(updated.message || '선결제 정보를 수정했습니다.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '선결제 수정에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canCancel || !data.actions.cancelUrl) {
      setActionError('취소 권한이 없거나 이미 취소된 선결제입니다.');
      return;
    }

    setActionBusy('cancel');
    setActionError('');
    setActionMessage('');
    try {
      const cancelled = await cancelCustomerPrepayment(data.actions.cancelUrl, cancelReason);
      await onRefresh();
      setCancelReason('');
      setActionMessage(cancelled.message || '선결제를 취소했습니다.');
    } catch (cancelError) {
      setActionError(cancelError instanceof Error ? cancelError.message : '선결제 취소에 실패했습니다.');
    } finally {
      setActionBusy('');
    }
  };

  const handleTransfer = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canTransfer || !data.actions.transferUrl) {
      setActionError('이관 권한이 없습니다.');
      return;
    }
    const targetUserId = Number(transferUserId);
    if (!Number.isFinite(targetUserId) || targetUserId <= 0) {
      setActionError('이관 대상을 선택하세요.');
      return;
    }

    setActionBusy('transfer');
    setActionError('');
    setActionMessage('');
    try {
      const transferred = await transferCustomerPrepayment(data.actions.transferUrl, targetUserId, transferReason);
      await onRefresh();
      setTransferReason('');
      setActionMessage(transferred.message || '선결제를 이관했습니다.');
    } catch (transferError) {
      setActionError(transferError instanceof Error ? transferError.message : '선결제 이관에 실패했습니다.');
    } finally {
      setActionBusy('');
    }
  };

  const handleDelete = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canDelete || !data.actions.deleteUrl) {
      setActionError(data.actions.deleteMessage || '삭제할 수 없는 선결제입니다.');
      return;
    }
    if (deleteConfirm.trim() !== '삭제') {
      setActionError('확인 문구를 입력하세요.');
      return;
    }

    setActionBusy('delete');
    setActionError('');
    setActionMessage('');
    try {
      const deleted = await deleteCustomerPrepayment(data.actions.deleteUrl);
      window.location.href = deleted.href || '/prepayments/';
    } catch (deleteError) {
      setActionError(deleteError instanceof Error ? deleteError.message : '선결제 삭제에 실패했습니다.');
      setActionBusy('');
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !prepayment) {
    return (
      <section className="prepayments-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>선결제 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '선결제 상세 API에 연결되지 않았습니다.'}</span>
          </div>
          <a href="/prepayments/">목록</a>
        </div>
      </section>
    );
  }

  const metrics = [
    { label: '선결제 금액', value: formatWon(data.metrics.amount), detail: prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음', icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.balance), detail: `${data.metrics.balancePercent}% 남음`, icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.usedAmount), detail: `${data.metrics.usagePercent}% 사용`, icon: Activity, tone: 'amber' as const },
    { label: '사용 내역', value: `${formatNumber(data.metrics.usageCount)}건`, detail: prepayment.statusLabel, icon: ListChecks, tone: 'teal' as const },
  ];
  const formOptions = {
    customers: data.edit.customers,
    paymentMethods: data.edit.paymentMethods,
    statuses: data.edit.statuses,
  };
  const deleteConfirmed = deleteConfirm.trim() === '삭제';
  const actionDisabled = Boolean(actionBusy);

  return (
    <section className="prepayments-page prepayment-detail-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>선결제 상세 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Prepayment detail</span>
          <h2>{prepayment.companyName || prepayment.customerName || '선결제 상세'}</h2>
          <p>{[prepayment.departmentName, prepayment.customerName, prepayment.payerName || '입금자 미지정'].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/prepayments/">목록</a>
          <a className="route-secondary-action" href={data.links.djangoDetail}>Django 상세</a>
          {data.links.reactEdit && !editRoute ? <a className="route-primary-action" href={data.links.reactEdit}>수정</a> : null}
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="선결제 상세 지표">
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

      {editRoute ? (
        <section className="dashboard-panel notes-create-panel prepayment-editor-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit prepayment</span>
              <h2>선결제 수정</h2>
            </div>
            {saving ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
          </div>
          {message ? <div className="notes-action-feedback success">{message}</div> : null}
          {error ? <div className="notes-action-feedback error">{error}</div> : null}
          {!data.edit.canEdit ? (
            <DashboardEmpty label={data.edit.message || '수정 권한이 없습니다'} />
          ) : (
            <PrepaymentFormFields
              form={form}
              options={formOptions}
              saving={saving}
              secondaryActions={<a className="route-secondary-action" href={data.edit.djangoUrl || data.links.djangoEdit}>Django 수정</a>}
              showStatus
              submitLabel="저장"
              onChange={handleChange}
              onSubmit={handleSubmit}
            />
          )}
        </section>
      ) : null}

      <div className="prepayment-detail-layout">
        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Usage history</span>
              <h2>사용 내역</h2>
            </div>
            <ListChecks size={18} />
          </div>
          {data.usages.length === 0 ? (
            <DashboardEmpty label="아직 사용 내역이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.usages.map((usage) => (
                <article className="prepayment-usage-row" key={usage.id}>
                  <div>
                    <strong>{usage.productName || '사용 내역'}</strong>
                    <span>
                      {[usage.usedAt ? formatDateTimeLabel(usage.usedAt) : '', usage.scheduleDate ? `납품 ${formatDateLabel(usage.scheduleDate)}` : ''].filter(Boolean).join(' · ')}
                    </span>
                    {usage.deliveryItems.length > 0 ? (
                      <small>{usage.deliveryItems.map((item) => `${item.itemName} ${formatNumber(item.quantity)}${item.unit || ''}`).join(', ')}</small>
                    ) : usage.memo ? <small>{usage.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>-{formatWon(usage.amount)}</strong>
                    <span>잔액 {formatWon(usage.remainingBalance)}</span>
                    {usage.scheduleHref ? <a href={usage.scheduleHref}>일정</a> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="dashboard-panel prepayment-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Summary</span>
              <h2>기본 정보</h2>
            </div>
            <CircleDollarSign size={18} />
          </div>
          <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
          <dl className="prepayment-detail-list">
            <div>
              <dt>입금 방법</dt>
              <dd>{prepayment.paymentMethodLabel || '-'}</dd>
            </div>
            <div>
              <dt>등록자</dt>
              <dd>{prepayment.ownerName}</dd>
            </div>
            <div>
              <dt>등록일</dt>
              <dd>{prepayment.createdAt ? formatDateTimeLabel(prepayment.createdAt) : '-'}</dd>
            </div>
            <div>
              <dt>메모</dt>
              <dd>{prepayment.memo || '메모 없음'}</dd>
            </div>
          </dl>
          {actionMessage ? <div className="notes-action-feedback success">{actionMessage}</div> : null}
          {actionError ? <div className="notes-action-feedback error">{actionError}</div> : null}
          {!data.scope.canManage ? (
            <DashboardEmpty label="등록자만 취소/삭제/이관할 수 있습니다" />
          ) : (
            <div className="prepayment-action-panel">
              <form className="prepayment-action-block" onSubmit={handleCancel}>
                <div className="prepayment-action-heading">
                  <X size={15} />
                  <strong>취소</strong>
                </div>
                <textarea
                  disabled={!data.actions.canCancel || actionDisabled}
                  onChange={(event) => {
                    setCancelReason(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="취소 사유"
                  value={cancelReason}
                />
                <button className="route-secondary-action" disabled={!data.actions.canCancel || actionDisabled} type="submit">
                  {actionBusy === 'cancel' ? <Loader2 className="spin-icon" size={15} /> : <X size={15} />}
                  취소 처리
                </button>
              </form>

              <form className="prepayment-action-block" onSubmit={handleTransfer}>
                <div className="prepayment-action-heading">
                  <ArrowRightLeft size={15} />
                  <strong>이관</strong>
                </div>
                <select
                  disabled={!data.actions.canTransfer || actionDisabled || data.actions.transferUsers.length === 0}
                  onChange={(event) => {
                    setTransferUserId(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  value={transferUserId}
                >
                  {data.actions.transferUsers.length === 0 ? (
                    <option value="">대상 없음</option>
                  ) : (
                    data.actions.transferUsers.map((user) => (
                      <option key={user.id} value={user.id}>{user.name}</option>
                    ))
                  )}
                </select>
                <textarea
                  disabled={!data.actions.canTransfer || actionDisabled || data.actions.transferUsers.length === 0}
                  onChange={(event) => {
                    setTransferReason(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="이관 사유"
                  value={transferReason}
                />
                <button
                  className="route-secondary-action"
                  disabled={!data.actions.canTransfer || !transferUserId || data.actions.transferUsers.length === 0 || actionDisabled}
                  type="submit"
                >
                  {actionBusy === 'transfer' ? <Loader2 className="spin-icon" size={15} /> : <ArrowRightLeft size={15} />}
                  이관
                </button>
              </form>

              <form className="prepayment-action-block danger" onSubmit={handleDelete}>
                <div className="prepayment-action-heading">
                  <Trash2 size={15} />
                  <strong>삭제</strong>
                </div>
                {data.actions.deleteMessage ? <small>{data.actions.deleteMessage}</small> : null}
                <input
                  disabled={!data.actions.canDelete || actionDisabled}
                  onChange={(event) => {
                    setDeleteConfirm(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="삭제"
                  value={deleteConfirm}
                />
                <button className="prepayment-danger-button" disabled={!data.actions.canDelete || !deleteConfirmed || actionDisabled} type="submit">
                  {actionBusy === 'delete' ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
                  삭제
                </button>
              </form>
            </div>
          )}
          <div className="customers-side-actions">
            <a href={prepayment.customerHref || prepayment.djangoCustomerHref}>고객 상세</a>
            <a href={prepayment.customerPrepaymentHref || prepayment.djangoCustomerPrepaymentHref}>고객별 선결제</a>
            {prepayment.djangoCustomerPrepaymentHref ? <a href={prepayment.djangoCustomerPrepaymentHref}>Django 고객별</a> : null}
            {data.links.djangoTransfer ? <a href={data.links.djangoTransfer}>Django 이관</a> : null}
            {data.links.djangoDelete ? <a href={data.links.djangoDelete}>Django 삭제/취소</a> : null}
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

const mailboxTabs: Array<{ id: MailboxType; label: string; icon: typeof Inbox }> = [
  { id: 'inbox', label: '받은편지함', icon: Inbox },
  { id: 'sent', label: '보낸편지함', icon: Send },
  { id: 'starred', label: '중요편지함', icon: Star },
  { id: 'archived', label: '보관함', icon: Archive },
  { id: 'trash', label: '휴지통', icon: Trash2 },
];

function MailComposePanel({
  create,
  form,
  open,
  saving,
  error,
  message,
  submitLabel,
  onChange,
  onCustomerChange,
  onOpenChange,
  onSubmit,
}: {
  create: MailboxData['create'];
  form: MailComposeFormState;
  open: boolean;
  saving: boolean;
  error: string;
  message: string;
  submitLabel: string;
  onChange: (field: keyof MailComposeFormState, value: string) => void;
  onCustomerChange: (customerId: string) => void;
  onOpenChange: (open: boolean) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (!open) {
    return null;
  }

  return (
    <section className="mail-compose-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Compose</span>
          <h2>{submitLabel}</h2>
        </div>
        <button className="icon-button" type="button" onClick={() => onOpenChange(false)} aria-label="메일 작성 닫기">
          <X size={17} />
        </button>
      </div>
      <form className="mail-compose-form" onSubmit={onSubmit}>
        {create.customers.length > 0 ? (
          <div className="form-field">
            <span>연결 고객</span>
            <SearchableSelect
              allowEmpty
              ariaLabel="연결 고객 선택"
              emptyLabel="고객 선택 없음"
              onChange={onCustomerChange}
              options={create.customers.map(makeCustomerSelectOption)}
              placeholder="고객, 회사, 이메일 검색"
              value={form.followupId}
            />
          </div>
        ) : null}
        <label>
          <span>받는 사람</span>
          <input value={form.toEmail} onChange={(event) => onChange('toEmail', event.target.value)} placeholder="customer@example.com" />
        </label>
        <div className="mail-compose-grid">
          <label>
            <span>참조</span>
            <input value={form.ccEmails} onChange={(event) => onChange('ccEmails', event.target.value)} placeholder="쉼표로 구분" />
          </label>
          <label>
            <span>숨은참조</span>
            <input value={form.bccEmails} onChange={(event) => onChange('bccEmails', event.target.value)} placeholder="쉼표로 구분" />
          </label>
        </div>
        <label>
          <span>제목</span>
          <input value={form.subject} onChange={(event) => onChange('subject', event.target.value)} placeholder="메일 제목" />
        </label>
        <label>
          <span>본문</span>
          <textarea value={form.bodyText} onChange={(event) => onChange('bodyText', event.target.value)} rows={8} />
        </label>
        {create.businessCards.length > 0 ? (
          <label>
            <span>명함 서명</span>
            <select value={form.businessCardId} onChange={(event) => onChange('businessCardId', event.target.value)}>
              <option value="">사용 안 함</option>
              {create.businessCards.map((card) => (
                <option value={card.id} key={card.id}>
                  {card.name}{card.isDefault ? ' · 기본' : ''}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {error ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{error}</span></div> : null}
        {message ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{message}</span></div> : null}
        <div className="mail-compose-actions">
          <button className="route-secondary-action" type="button" onClick={() => onOpenChange(false)}>취소</button>
          <button className="route-primary-action" disabled={saving} type="submit">
            {saving ? <Loader2 className="spin-icon" size={16} /> : <Send size={16} />}
            {submitLabel}
          </button>
        </div>
      </form>
    </section>
  );
}

function MailboxPage({
  data,
  loading,
  selectedBox,
  query,
  composeOpen,
  composeForm,
  composing,
  composeError,
  composeMessage,
  syncing,
  actioningId,
  onAction,
  onBoxChange,
  onComposeCustomerChange,
  onComposeFormChange,
  onComposeOpenChange,
  onComposeSubmit,
  onQueryChange,
  onSync,
}: {
  data: MailboxData | null;
  loading: boolean;
  selectedBox: MailboxType;
  query: string;
  composeOpen: boolean;
  composeForm: MailComposeFormState;
  composing: boolean;
  composeError: string;
  composeMessage: string;
  syncing: boolean;
  actioningId: number | null;
  onAction: (email: MailboxEmailItem, action: 'star' | 'archive' | 'trash' | 'restore' | 'delete') => void;
  onBoxChange: (box: MailboxType) => void;
  onComposeCustomerChange: (customerId: string) => void;
  onComposeFormChange: (field: keyof MailComposeFormState, value: string) => void;
  onComposeOpenChange: (open: boolean) => void;
  onComposeSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onQueryChange: (value: string) => void;
  onSync: () => void;
}) {
  const mailbox = data ?? null;
  const counts = mailbox?.counts ?? { inbox: 0, sent: 0, starred: 0, archived: 0, trash: 0, unread: 0 };

  return (
    <section className="mailbox-page">
      {mailbox?.source !== 'django' && !loading ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>메일 API에 연결되지 않았습니다</strong>
            <span>{mailbox?.error || '로그인 상태나 Django API 응답을 확인해야 합니다.'}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="mailbox-summary-band">
        <div>
          <span className="eyebrow">Customer mailbox</span>
          <h2>{mailbox?.connection.address || '메일함'}</h2>
          <p>{mailbox?.connection.connected ? `${mailbox.connection.provider} 연결됨` : '메일 계정 연결이 필요합니다'}</p>
        </div>
        <div className="mailbox-summary-actions">
          <button className="route-secondary-action" disabled={syncing || !mailbox?.connection.gmailConnected} onClick={onSync} type="button">
            {syncing ? <Loader2 className="spin-icon" size={16} /> : <RefreshCw size={16} />}
            동기화
          </button>
          <button className="route-primary-action" onClick={() => onComposeOpenChange(true)} type="button">
            <Send size={16} />
            메일 작성
          </button>
        </div>
      </div>

      {!mailbox?.connection.connected ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>Gmail 또는 IMAP 계정을 연결하면 React 메일함에서 고객 메일을 관리할 수 있습니다.</span>
          <a href={mailbox?.connection.connectHref || '/reporting/gmail/connect/'}>Gmail 연결</a>
          <a href={mailbox?.connection.imapConnectHref || '/reporting/imap/connect/'}>IMAP 연결</a>
        </div>
      ) : null}

      <MailComposePanel
        create={mailbox?.create ?? {
          canSend: false,
          message: '',
          submitUrl: '/reporting/api/mailbox/send/',
          djangoUrl: '/reporting/gmail/send/mailbox/',
          customers: [],
          businessCards: [],
        }}
        error={composeError}
        form={composeForm}
        message={composeMessage}
        open={composeOpen}
        saving={composing}
        submitLabel="메일 발송"
        onChange={onComposeFormChange}
        onCustomerChange={onComposeCustomerChange}
        onOpenChange={onComposeOpenChange}
        onSubmit={onComposeSubmit}
      />

      <div className="mailbox-layout">
        <aside className="mailbox-rail">
          {mailboxTabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button className={selectedBox === tab.id ? 'active' : ''} key={tab.id} onClick={() => onBoxChange(tab.id)} type="button">
                <Icon size={16} />
                <span>{tab.label}</span>
                <strong>{formatNumber(counts[tab.id] || 0)}</strong>
              </button>
            );
          })}
          <a className="mailbox-legacy-link" href={mailbox?.links.djangoInbox || '/reporting/mailbox/inbox/'}>
            Django 메일함
            <MoveUpRight size={15} />
          </a>
        </aside>

        <section className="mailbox-list-panel">
          <div className="mailbox-toolbar">
            <label className="search-box mailbox-search">
              <Search size={17} />
              <input onChange={(event) => onQueryChange(event.target.value)} placeholder="제목, 고객, 본문 검색" value={query} />
            </label>
            <span>{formatNumber(mailbox?.pagination.totalCount || 0)}건</span>
          </div>
          {loading ? (
            <div className="loading-state"><Loader2 className="spin-icon" size={18} /> 메일을 불러오는 중입니다.</div>
          ) : mailbox?.emails.length ? (
            <div className="mail-row-list">
              {mailbox.emails.map((email) => (
                <article className={`mail-row ${email.type === 'received' && !email.isRead ? 'unread' : ''}`} key={email.id}>
                  <a className="mail-row-main" href={email.threadHref}>
                    <div>
                      <strong>{email.subject || '(제목 없음)'}</strong>
                      <span>{email.contact || email.senderEmail || email.recipientEmail}</span>
                    </div>
                    <p>{email.preview || '본문 미리보기가 없습니다.'}</p>
                    <small>
                      {email.followup.company ? `${email.followup.company} · ` : ''}
                      {email.followup.customer || email.followup.department || email.typeLabel}
                    </small>
                  </a>
                  <div className="mail-row-side">
                    <time>{formatDateTimeLabel(email.happenedAt)}</time>
                    <div className="mail-row-actions">
                      <button disabled={actioningId === email.id} onClick={() => onAction(email, 'star')} type="button" aria-label="중요 표시">
                        <Star size={15} className={email.isStarred ? 'filled-icon' : ''} />
                      </button>
                      {selectedBox === 'trash' ? (
                        <button disabled={actioningId === email.id} onClick={() => onAction(email, 'restore')} type="button" aria-label="복원">
                          <Archive size={15} />
                        </button>
                      ) : (
                        <button disabled={actioningId === email.id} onClick={() => onAction(email, 'archive')} type="button" aria-label="보관">
                          <Archive size={15} />
                        </button>
                      )}
                      <button disabled={actioningId === email.id} onClick={() => onAction(email, selectedBox === 'trash' ? 'delete' : 'trash')} type="button" aria-label="삭제">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <strong>표시할 메일이 없습니다</strong>
              <span>검색어를 지우거나 다른 메일함을 선택하세요.</span>
            </div>
          )}
          {mailbox?.pagination.totalPages && mailbox.pagination.totalPages > 1 ? (
            <div className="mailbox-pagination">
              <a className={!mailbox.pagination.hasPrevious ? 'disabled' : ''} href={`/mailbox/?box=${selectedBox}&page=${mailbox.pagination.previousPage || 1}${query ? `&q=${encodeURIComponent(query)}` : ''}`}>이전</a>
              <span>{mailbox.pagination.page} / {mailbox.pagination.totalPages}</span>
              <a className={!mailbox.pagination.hasNext ? 'disabled' : ''} href={`/mailbox/?box=${selectedBox}&page=${mailbox.pagination.nextPage || mailbox.pagination.page}${query ? `&q=${encodeURIComponent(query)}` : ''}`}>다음</a>
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );
}

function MailboxThreadPage({
  data,
  loading,
  replyForm,
  replyOpen,
  replySaving,
  replyError,
  replyMessage,
  actioningId,
  onAction,
  onReplyFormChange,
  onReplyOpenChange,
  onReplySubmit,
}: {
  data: MailboxThreadData | null;
  loading: boolean;
  replyForm: MailComposeFormState;
  replyOpen: boolean;
  replySaving: boolean;
  replyError: string;
  replyMessage: string;
  actioningId: number | null;
  onAction: (email: MailboxEmailItem, action: 'star' | 'archive' | 'trash' | 'restore' | 'delete') => void;
  onReplyFormChange: (field: keyof MailComposeFormState, value: string) => void;
  onReplyOpenChange: (open: boolean) => void;
  onReplySubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const thread = data ?? {
    success: false,
    source: 'unavailable' as const,
    error: '',
    thread: { id: '', subject: '', followup: null, messageCount: 0, lastReceivedEmailId: null },
    connection: {
      connected: false,
      provider: '',
      address: '',
      gmailConnected: false,
      imapConnected: false,
      lastSyncAt: null,
      connectHref: '/reporting/gmail/connect/',
      imapConnectHref: '/reporting/imap/connect/',
      profileHref: '/reporting/profile/',
    },
    links: { mailbox: '/mailbox/', djangoThread: '', reply: '' },
    create: { canSend: false, message: '', submitUrl: '', djangoUrl: '', customers: [], businessCards: [] },
    emails: [],
  };
  const lastEmail = thread.emails[thread.emails.length - 1];

  return (
    <section className="mail-thread-page">
      <div className="route-detail-header">
        <div>
          <a href="/mailbox/">메일함</a>
          <span>/</span>
          <strong>{thread.thread.subject || '메일 스레드'}</strong>
        </div>
        <div className="route-detail-actions">
          <a className="route-secondary-action" href={thread.links.djangoThread || `/reporting/mailbox/thread/${thread.thread.id}/`}>Django 보기</a>
          <button className="route-primary-action" disabled={!lastEmail} onClick={() => onReplyOpenChange(true)} type="button">
            <Reply size={16} />
            답장
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-state"><Loader2 className="spin-icon" size={18} /> 스레드를 불러오는 중입니다.</div>
      ) : thread.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>메일 스레드를 불러올 수 없습니다</strong>
            <span>{thread.error || '로그인 상태나 Django API 응답을 확인해야 합니다.'}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : (
        <>
          <div className="mail-thread-summary">
            <div>
              <span className="eyebrow">Thread</span>
              <h2>{thread.thread.subject || '(제목 없음)'}</h2>
              <p>
                {thread.thread.followup?.company ? `${thread.thread.followup.company} · ` : ''}
                {thread.thread.followup?.customer || thread.thread.followup?.department || `${thread.thread.messageCount}개 메시지`}
              </p>
            </div>
            {thread.thread.followup?.href ? <a className="route-secondary-action" href={thread.thread.followup.href}>고객 상세</a> : null}
          </div>

          <MailComposePanel
            create={thread.create}
            error={replyError}
            form={replyForm}
            message={replyMessage}
            open={replyOpen}
            saving={replySaving}
            submitLabel="답장 발송"
            onChange={onReplyFormChange}
            onCustomerChange={(customerId) => onReplyFormChange('followupId', customerId)}
            onOpenChange={onReplyOpenChange}
            onSubmit={onReplySubmit}
          />

          <div className="mail-thread-list">
            {thread.emails.map((email) => (
              <article className={`mail-message-card ${email.type}`} key={email.id}>
                <div className="mail-message-header">
                  <div>
                    <strong>{email.type === 'sent' ? email.recipientEmail : email.senderEmail}</strong>
                    <span>{email.typeLabel} · {formatDateTimeLabel(email.happenedAt)}</span>
                  </div>
                  <div className="mail-row-actions">
                    <button disabled={actioningId === email.id} onClick={() => onAction(email, 'star')} type="button" aria-label="중요 표시">
                      <Star size={15} className={email.isStarred ? 'filled-icon' : ''} />
                    </button>
                    <button disabled={actioningId === email.id} onClick={() => onAction(email, 'trash')} type="button" aria-label="휴지통">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
                <div className="mail-message-body">{email.bodyText || email.preview || '본문이 없습니다.'}</div>
                {email.followup.href ? (
                  <div className="mail-message-links">
                    <a href={email.followup.href}>{email.followup.company || '고객'} 상세</a>
                    {email.schedule.href ? <a href={email.schedule.href}>연결 일정</a> : null}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function weeklyDraftValue(draft: Record<string, unknown>, keys: string[]): string {
  for (const key of keys) {
    const value = draft[key];
    if (Array.isArray(value)) {
      return value.map((item) => String(item)).join('\n');
    }
    if (typeof value === 'string' && value.trim()) {
      return value.trim();
    }
  }
  return '';
}

function weeklyScheduleText(item: WeeklyReportSchedulesData['schedules'][number]): string {
  const lines = [
    `- ${item.date}${item.weekday ? `(${item.weekday})` : ''}: ${item.customer || '-'}${item.activity_type_display ? ` - ${item.activity_type_display}` : ''}`,
  ];
  const context = [item.company, item.department, item.manager].filter(Boolean).join(' · ');
  if (context) lines.push(`  고객/부서: ${context}`);
  if (item.notes) lines.push(`  메모: ${item.notes}`);
  if (item.amount && item.amount_label) lines.push(`  ${item.amount_label}: ${item.amount}`);
  (item.histories ?? []).forEach((history) => {
    if (history.snippet) lines.push(`  기록: ${history.snippet}`);
    if (history.amount) lines.push(`  기록 금액: ${history.amount}`);
  });
  (item.quotes ?? []).forEach((quote) => {
    const quoteParts = [quote.number, quote.stage, quote.amount, quote.probability ? `${quote.probability}%` : ''].filter(Boolean);
    if (quoteParts.length) lines.push(`  견적: ${quoteParts.join(' · ')}`);
  });
  return lines.join('\n');
}

function WeeklyReportsPage({
  data,
  loading,
  month,
  userId,
  year,
  onMonthChange,
  onUserChange,
  onYearChange,
  routeData,
}: {
  data: WeeklyReportsData | null;
  loading: boolean;
  month: string;
  routeData: PipelineData;
  userId: string;
  year: string;
  onMonthChange: (value: string) => void;
  onUserChange: (value: string) => void;
  onYearChange: (value: string) => void;
}) {
  const source = data;
  const metrics = source?.metrics;
  return (
    <div className="weekly-page">
      <WorkspaceRoutePage data={routeData} view="weeklyReports" />
      <section className="dashboard-metric-grid weekly-metrics">
        <DashboardMetricCard label="전체 보고" value={`${formatNumber(metrics?.filteredReports ?? 0)}건`} detail={source?.scope.label || '내 보고서'} icon={ListChecks} tone="blue" />
        <DashboardMetricCard label="검토 완료" value={`${formatNumber(metrics?.reviewedReports ?? 0)}건`} detail="관리자 코멘트 포함" icon={CheckCircle2} tone="green" />
        <DashboardMetricCard label="미검토" value={`${formatNumber(metrics?.pendingReports ?? 0)}건`} detail="검토 대기" icon={Clock} tone="amber" />
        <DashboardMetricCard label="이번 달" value={`${formatNumber(metrics?.thisMonthReports ?? 0)}건`} detail="작성된 주간보고" icon={CalendarDays} tone="teal" />
      </section>

      <section className="table-card weekly-list-card">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">Weekly Reports</p>
            <h2>주간보고 목록</h2>
          </div>
          <div className="route-actions">
            <a className="route-secondary-action primary" href="/weekly-reports/new/">
              <Plus size={16} />
              보고서 작성
            </a>
            <a className="route-secondary-action" href={source?.links.djangoList || '/reporting/weekly-reports/'}>
              Django
            </a>
          </div>
        </div>
        <div className="filter-row weekly-filter-row">
          <label>
            <span>연도</span>
            <select value={year} onChange={(event) => onYearChange(event.target.value)}>
              <option value="">전체</option>
              {(source?.options.years ?? [2024, 2025, 2026, 2027]).map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label>
            <span>월</span>
            <select value={month} onChange={(event) => onMonthChange(event.target.value)}>
              <option value="">전체</option>
              {(source?.options.months ?? Array.from({ length: 12 }, (_, index) => index + 1)).map((option) => (
                <option key={option} value={option}>{option}월</option>
              ))}
            </select>
          </label>
          {source?.scope.canViewAll ? (
            <label>
              <span>작성자</span>
              <select value={userId} onChange={(event) => onUserChange(event.target.value)}>
                <option value="">전체</option>
                {source.options.users.map((user) => (
                  <option key={user.id} value={user.id}>{user.name}</option>
                ))}
              </select>
            </label>
          ) : null}
        </div>

        {loading ? (
          <div className="empty-state">주간보고를 불러오는 중입니다.</div>
        ) : source?.error ? (
          <div className="empty-state error">{source.error}</div>
        ) : source?.reports.length ? (
          <div className="weekly-report-table">
            {source.reports.map((report) => (
              <a className="weekly-report-row" href={report.href} key={report.id}>
                <div>
                  <strong>{report.title}</strong>
                  <span>{formatDateLabel(report.weekStart)} - {formatDateLabel(report.weekEnd)}</span>
                </div>
                <div>
                  <span>{report.user.name}</span>
                  <small>{report.user.company || report.user.roleLabel}</small>
                </div>
                <span className={`status-pill ${report.reviewed ? 'done' : 'pending'}`}>
                  {report.reviewed ? '검토 완료' : '검토 대기'}
                </span>
                <MoveUpRight size={16} />
              </a>
            ))}
          </div>
        ) : (
          <div className="empty-state">조건에 맞는 주간보고가 없습니다.</div>
        )}
      </section>
    </div>
  );
}

function WeeklyReportDetailPage({
  data,
  loading,
  onRefresh,
  routeData,
}: {
  data: WeeklyReportDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<unknown>;
  routeData: PipelineData;
}) {
  const report = data?.report;
  const [comment, setComment] = useState('');
  const [savingComment, setSavingComment] = useState(false);
  const [actionError, setActionError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setComment(report?.managerComment || '');
    setActionError('');
    setActionMessage('');
  }, [report?.id, report?.managerComment]);

  const handleCommentSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!report?.managerCommentHref || savingComment) return;
    setSavingComment(true);
    setActionError('');
    setActionMessage('');
    try {
      await saveWeeklyReportManagerComment(report.managerCommentHref, comment);
      setActionMessage('검토 코멘트를 저장했습니다.');
      await onRefresh();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : '검토 저장에 실패했습니다.');
    } finally {
      setSavingComment(false);
    }
  };

  const handleDelete = async () => {
    if (!report?.deleteHref || deleting) return;
    if (!window.confirm('이 주간보고를 삭제할까요?')) return;
    setDeleting(true);
    setActionError('');
    try {
      const result = await deleteWeeklyReport(report.deleteHref);
      window.location.href = result.redirect || '/weekly-reports/';
    } catch (error) {
      setActionError(error instanceof Error ? error.message : '삭제에 실패했습니다.');
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="weekly-page"><div className="empty-state">주간보고를 불러오는 중입니다.</div></div>;
  }
  if (!report || data?.error) {
    return <div className="weekly-page"><div className="empty-state error">{data?.error || '주간보고를 찾을 수 없습니다.'}</div></div>;
  }

  return (
    <div className="weekly-page">
      <WorkspaceRoutePage data={routeData} view="weeklyReports" />
      <section className="weekly-detail-layout">
        <article className="weekly-report-document">
          <div className="weekly-document-header">
            <div>
              <p className="eyebrow">Weekly Report</p>
              <h2>{report.title}</h2>
              <p>{formatDateLabel(report.weekStart)} - {formatDateLabel(report.weekEnd)} · {report.user.name}</p>
            </div>
            <span className={`status-pill ${report.reviewed ? 'done' : 'pending'}`}>
              {report.reviewed ? '검토 완료' : '검토 대기'}
            </span>
          </div>
          <WeeklyReportHtmlSection title="영업 활동" html={report.activityNotesHtml} />
          <WeeklyReportHtmlSection title="견적/납품" html={report.quoteDeliveryNotesHtml} />
          <WeeklyReportHtmlSection title="기타" html={report.otherNotesHtml} />
          {report.managerComment ? (
            <section className="weekly-html-section manager">
              <h3>관리자 검토</h3>
              <p>{report.managerComment}</p>
              <small>{report.reviewedBy}{report.reviewedAt ? ` · ${formatDateTimeLabel(report.reviewedAt)}` : ''}</small>
            </section>
          ) : null}
        </article>

        <aside className="weekly-side-panel">
          <div className="side-card">
            <h3>작업</h3>
            <div className="button-stack">
              {report.canEdit ? <a className="route-secondary-action primary" href={report.editHref}>수정</a> : null}
              <button type="button" className="route-secondary-action" onClick={() => window.print()}>인쇄</button>
              <a className="route-secondary-action" href={report.djangoHref}>Django 보기</a>
              {report.canDelete ? (
                <button type="button" className="route-secondary-action danger" onClick={handleDelete} disabled={deleting}>
                  {deleting ? '삭제 중' : '삭제'}
                </button>
              ) : null}
            </div>
          </div>
          {report.canComment ? (
            <form className="side-card weekly-comment-form" onSubmit={handleCommentSubmit}>
              <h3>검토 코멘트</h3>
              <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={7} />
              {actionError ? <p className="form-error">{actionError}</p> : null}
              {actionMessage ? <p className="form-success">{actionMessage}</p> : null}
              <button type="submit" className="primary-button" disabled={savingComment}>
                {savingComment ? '저장 중' : '검토 저장'}
              </button>
            </form>
          ) : actionError ? (
            <div className="side-card"><p className="form-error">{actionError}</p></div>
          ) : null}
        </aside>
      </section>
    </div>
  );
}

function WeeklyReportHtmlSection({ title, html }: { title: string; html: string }) {
  return (
    <section className="weekly-html-section">
      <h3>{title}</h3>
      {html ? (
        <div className="weekly-html-content" dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <p className="muted-text">작성된 내용이 없습니다.</p>
      )}
    </section>
  );
}

function WeeklyReportEditorPage({
  createData,
  detailData,
  loading,
  mode,
  routeData,
}: {
  createData: WeeklyReportCreateData | null;
  detailData: WeeklyReportDetailData | null;
  loading: boolean;
  mode: 'create' | 'edit';
  routeData: PipelineData;
}) {
  const sourceForm = mode === 'create' ? createData?.form : detailData?.form;
  const report = detailData?.report;
  const links = mode === 'create' ? createData?.links : detailData?.links;
  const canUseAi = mode === 'create' ? Boolean(createData?.canUseAi) : Boolean(detailData?.canUseAi);
  const [form, setForm] = useState<WeeklyReportFormPayload>(() => makeEmptyWeeklyReportForm());
  const [saving, setSaving] = useState(false);
  const [loadingSchedules, setLoadingSchedules] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [schedules, setSchedules] = useState<WeeklyReportSchedulesData | null>(null);
  const [selectedScheduleIds, setSelectedScheduleIds] = useState<number[]>([]);
  const [formError, setFormError] = useState('');
  const [formMessage, setFormMessage] = useState('');

  useEffect(() => {
    if (!sourceForm) return;
    setForm({
      ...makeEmptyWeeklyReportForm(),
      ...sourceForm,
    });
    setSelectedScheduleIds([]);
  }, [sourceForm?.weekStart, sourceForm?.weekEnd, sourceForm?.title, mode]);

  const handleChange = (field: keyof WeeklyReportFormPayload, value: string) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setFormError('');
  };

  const handleLoadSchedules = async () => {
    if (!form.weekStart || !form.weekEnd || loadingSchedules) return;
    setLoadingSchedules(true);
    setFormError('');
    try {
      const result = await loadWeeklyReportSchedules(form.weekStart, form.weekEnd);
      setSchedules(result);
      setSelectedScheduleIds([]);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '일정 불러오기에 실패했습니다.');
    } finally {
      setLoadingSchedules(false);
    }
  };

  const selectedSchedules = [
    ...(schedules?.categorized.activity ?? []),
    ...(schedules?.categorized.quote_delivery ?? []),
  ].filter((item) => selectedScheduleIds.includes(item.id));

  const appendSelectedSchedules = (field: 'activityNotes' | 'quoteDeliveryNotes') => {
    if (!selectedSchedules.length) {
      setFormError('삽입할 일정을 선택하세요.');
      return;
    }
    const text = selectedSchedules.map(weeklyScheduleText).join('\n\n');
    setForm((previous) => ({
      ...previous,
      [field]: [previous[field], text].filter(Boolean).join('\n\n'),
    }));
    setFormMessage('선택한 일정을 본문에 삽입했습니다.');
    setFormError('');
  };

  const handleAiDraft = async () => {
    if (!form.weekStart || !form.weekEnd || aiLoading) return;
    setAiLoading(true);
    setFormError('');
    setFormMessage('');
    try {
      const draft = await generateWeeklyReportAiDraft(form.weekStart, form.weekEnd);
      const record = draft as Record<string, unknown>;
      setForm((previous) => ({
        ...previous,
        title: weeklyDraftValue(record, ['title']) || previous.title,
        activityNotes: weeklyDraftValue(record, ['activityNotes', 'activity_notes', 'activity', 'summary']) || previous.activityNotes,
        quoteDeliveryNotes: weeklyDraftValue(record, ['quoteDeliveryNotes', 'quote_delivery_notes', 'quoteDelivery']) || previous.quoteDeliveryNotes,
        otherNotes: weeklyDraftValue(record, ['otherNotes', 'other_notes', 'other']) || previous.otherNotes,
      }));
      setFormMessage('AI 초안을 적용했습니다.');
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'AI 초안 생성에 실패했습니다.');
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const submitUrl = mode === 'create' ? links?.createApi : report?.updateHref;
    if (!submitUrl || saving) return;
    if (!form.weekStart || !form.weekEnd) {
      setFormError('보고 기간을 선택하세요.');
      return;
    }
    setSaving(true);
    setFormError('');
    setFormMessage('');
    try {
      const result = await saveWeeklyReport(submitUrl, form);
      window.location.href = result.report?.href || '/weekly-reports/';
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="weekly-page"><div className="empty-state">주간보고 폼을 불러오는 중입니다.</div></div>;
  }
  if (!sourceForm || (mode === 'edit' && !report?.canEdit)) {
    return <div className="weekly-page"><div className="empty-state error">주간보고를 작성하거나 수정할 권한이 없습니다.</div></div>;
  }

  return (
    <div className="weekly-page">
      <WorkspaceRoutePage data={routeData} view="weeklyReports" />
      <section className="weekly-editor-layout">
        <form className="weekly-editor-form" onSubmit={handleSubmit}>
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">{mode === 'create' ? 'Create' : 'Edit'}</p>
              <h2>{mode === 'create' ? '주간보고 작성' : '주간보고 수정'}</h2>
            </div>
            <div className="route-actions">
              <a className="route-secondary-action" href={mode === 'edit' && report ? report.href : '/weekly-reports/'}>취소</a>
              {mode === 'edit' && report ? <a className="route-secondary-action" href={report.djangoEditHref}>Django 수정</a> : null}
            </div>
          </div>
          {mode === 'create' && createData?.existingReport ? (
            <div className="inline-alert">
              이번 주 보고서가 이미 있습니다.
              <a href={createData.existingReport.editHref}>기존 보고서 수정</a>
            </div>
          ) : null}
          <div className="form-grid two-columns">
            <label>
              <span>시작일</span>
              <input type="date" value={form.weekStart} onChange={(event) => handleChange('weekStart', event.target.value)} />
            </label>
            <label>
              <span>종료일</span>
              <input type="date" value={form.weekEnd} onChange={(event) => handleChange('weekEnd', event.target.value)} />
            </label>
          </div>
          <label className="form-field full">
            <span>제목</span>
            <input value={form.title} onChange={(event) => handleChange('title', event.target.value)} placeholder="주간보고 제목" />
          </label>
          <label className="form-field full">
            <span>영업 활동</span>
            <textarea value={form.activityNotes} onChange={(event) => handleChange('activityNotes', event.target.value)} rows={10} />
          </label>
          <label className="form-field full">
            <span>견적/납품</span>
            <textarea value={form.quoteDeliveryNotes} onChange={(event) => handleChange('quoteDeliveryNotes', event.target.value)} rows={9} />
          </label>
          <label className="form-field full">
            <span>기타</span>
            <textarea value={form.otherNotes} onChange={(event) => handleChange('otherNotes', event.target.value)} rows={6} />
          </label>
          {formError ? <p className="form-error">{formError}</p> : null}
          {formMessage ? <p className="form-success">{formMessage}</p> : null}
          <div className="form-actions">
            <button type="button" className="secondary-button" onClick={handleLoadSchedules} disabled={loadingSchedules || !form.weekStart || !form.weekEnd}>
              {loadingSchedules ? '불러오는 중' : '일정 불러오기'}
            </button>
            {canUseAi ? (
              <button type="button" className="secondary-button" onClick={handleAiDraft} disabled={aiLoading || !form.weekStart || !form.weekEnd}>
                {aiLoading ? 'AI 생성 중' : 'AI 초안'}
              </button>
            ) : null}
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? '저장 중' : '저장'}
            </button>
          </div>
        </form>

        <aside className="weekly-schedule-panel">
          <div className="section-heading-row compact">
            <div>
              <p className="eyebrow">Schedules</p>
              <h3>일정 불러오기</h3>
            </div>
            <span>{formatNumber(selectedScheduleIds.length)}개 선택</span>
          </div>
          <div className="weekly-insert-actions">
            <button type="button" onClick={() => appendSelectedSchedules('activityNotes')}>영업활동에 삽입</button>
            <button type="button" onClick={() => appendSelectedSchedules('quoteDeliveryNotes')}>견적/납품에 삽입</button>
          </div>
          <WeeklyScheduleGroup
            items={schedules?.categorized.activity ?? []}
            selectedIds={selectedScheduleIds}
            title="영업활동"
            onToggle={(id) => setSelectedScheduleIds((previous) => (
              previous.includes(id) ? previous.filter((value) => value !== id) : [...previous, id]
            ))}
          />
          <WeeklyScheduleGroup
            items={schedules?.categorized.quote_delivery ?? []}
            selectedIds={selectedScheduleIds}
            title="견적/납품"
            onToggle={(id) => setSelectedScheduleIds((previous) => (
              previous.includes(id) ? previous.filter((value) => value !== id) : [...previous, id]
            ))}
          />
        </aside>
      </section>
    </div>
  );
}

function WeeklyScheduleGroup({
  items,
  onToggle,
  selectedIds,
  title,
}: {
  items: WeeklyReportSchedulesData['schedules'];
  onToggle: (id: number) => void;
  selectedIds: number[];
  title: string;
}) {
  return (
    <section className="weekly-schedule-group">
      <h4>{title}</h4>
      {items.length ? items.map((item) => (
        <label className="weekly-schedule-card" key={item.id}>
          <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => onToggle(item.id)} />
          <div>
            <strong>{item.date}{item.weekday ? `(${item.weekday})` : ''} · {item.customer}</strong>
            <span>{[item.company, item.department, item.activity_type_display].filter(Boolean).join(' · ')}</span>
            {item.notes ? <p>{item.notes}</p> : null}
            {item.amount && item.amount_label ? <small>{item.amount_label}: {item.amount}</small> : null}
            {(item.histories?.length || item.quotes?.length) ? (
              <small>{formatNumber((item.histories?.length ?? 0) + (item.quotes?.length ?? 0))}개 연결 기록</small>
            ) : null}
          </div>
        </label>
      )) : (
        <div className="empty-state compact">불러온 일정이 없습니다.</div>
      )}
    </section>
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

  const aiDepartment = deal.aiDepartment;

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
      {aiDepartment ? (
        <div className="customer-ai-card pipeline-ai-card">
          <div className="customer-ai-card-heading">
            <div>
              <span className="eyebrow">Department AI</span>
              <h3>{aiDepartment.departmentName || '부서 AI 분석'}</h3>
            </div>
            <Sparkles size={18} />
          </div>
          {aiDepartment.hasAnalysis ? (
            <p>{aiDepartment.summary || '분석 요약 없음'}</p>
          ) : (
            <p>{aiDepartment.message || '아직 부서 AI 분석이 없습니다.'}</p>
          )}
          <div className="customer-ai-metrics">
            <span>미팅 <strong>{formatNumber(aiDepartment.meetingCount)}</strong></span>
            <span>견적 <strong>{formatNumber(aiDepartment.quoteCount)}</strong></span>
            <span>납품 <strong>{formatNumber(aiDepartment.deliveryCount)}</strong></span>
            <span>PainPoint <strong>{formatNumber(aiDepartment.painpointCount)}</strong></span>
          </div>
          {aiDepartment.unverifiedPainpointCount > 0 ? (
            <div className="pipeline-ai-alert">
              <AlertTriangle size={15} />
              <span>미검증 PainPoint {formatNumber(aiDepartment.unverifiedPainpointCount)}건</span>
            </div>
          ) : null}
          <div className="customer-ai-actions">
            {aiDepartment.href ? (
              <a className="route-secondary-action" href={aiDepartment.href}>
                AI 결과
                <MoveUpRight size={15} />
              </a>
            ) : aiDepartment.hubHref ? (
              <a className="route-secondary-action" href={aiDepartment.hubHref}>
                AI 허브
                <MoveUpRight size={15} />
              </a>
            ) : null}
            {deal.detailUrl ? (
              <a className="route-secondary-action" href={`/customers/${deal.id}/`}>
                고객 상세
                <MoveUpRight size={15} />
              </a>
            ) : null}
          </div>
        </div>
      ) : null}
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
  const customerDetailId = currentView === 'customers' ? getCustomerDetailId() : null;
  const noteDetailId = currentView === 'notes' ? getNoteDetailId() : null;
  const scheduleDetailId = currentView === 'schedules' ? getScheduleDetailId() : null;
  const mailboxThreadId = currentView === 'mail' ? getMailboxThreadId() : '';
  const initialMailboxBox = currentView === 'mail' ? getMailboxTypeParam() : 'inbox';
  const prepaymentCustomerId = currentView === 'prepayments' ? getPrepaymentCustomerId() : null;
  const prepaymentDetailId = currentView === 'prepayments' ? getPrepaymentDetailId() : null;
  const prepaymentCreateRoute = currentView === 'prepayments' && isPrepaymentCreateRoute();
  const prepaymentEditRoute = currentView === 'prepayments' && isPrepaymentEditRoute();
  const weeklyReportDetailId = currentView === 'weeklyReports' ? getWeeklyReportDetailId() : null;
  const weeklyReportCreateRoute = currentView === 'weeklyReports' && isWeeklyReportCreateRoute();
  const weeklyReportEditRoute = currentView === 'weeklyReports' && isWeeklyReportEditRoute();
  const [mode, setMode] = useState<'board' | 'list'>('board');
  const [pipelineData, setPipelineData] = useState(mockPipelineData);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(currentView === 'dashboard');
  const [customersData, setCustomersData] = useState<CustomersData | null>(null);
  const [customersLoading, setCustomersLoading] = useState(currentView === 'customers');
  const [customerDetailData, setCustomerDetailData] = useState<CustomerDetailData | null>(null);
  const [customerDetailLoading, setCustomerDetailLoading] = useState(Boolean(customerDetailId));
  const [customerQuery, setCustomerQuery] = useState('');
  const [customerOwner, setCustomerOwner] = useState('');
  const [customerPriority, setCustomerPriority] = useState('');
  const [customerStage, setCustomerStage] = useState('');
  const [customerCreateOpen, setCustomerCreateOpen] = useState(currentView === 'customers' && !customerDetailId && shouldOpenCreatePanel());
  const [customerCreateForm, setCustomerCreateForm] = useState<CustomerCreateFormState>(() => makeEmptyCustomerCreateForm());
  const [customerCreating, setCustomerCreating] = useState(false);
  const [customerCreateError, setCustomerCreateError] = useState('');
  const [customerCreateMessage, setCustomerCreateMessage] = useState('');
  const [customerCreatedDetailHref, setCustomerCreatedDetailHref] = useState('');
  const [customerCompanyCreateName, setCustomerCompanyCreateName] = useState('');
  const [customerDepartmentCreateName, setCustomerDepartmentCreateName] = useState('');
  const [customerCompanyCreating, setCustomerCompanyCreating] = useState(false);
  const [customerDepartmentCreating, setCustomerDepartmentCreating] = useState(false);
  const [notesData, setNotesData] = useState<NotesData | null>(null);
  const [notesLoading, setNotesLoading] = useState(currentView === 'notes' && !noteDetailId);
  const [noteDetailData, setNoteDetailData] = useState<NoteDetailData | null>(null);
  const [noteDetailLoading, setNoteDetailLoading] = useState(Boolean(noteDetailId));
  const [noteQuery, setNoteQuery] = useState('');
  const [noteOwner, setNoteOwner] = useState('');
  const [noteActionType, setNoteActionType] = useState('');
  const [noteReview, setNoteReview] = useState('');
  const [noteNextAction, setNoteNextAction] = useState('');
  const [noteReviewingId, setNoteReviewingId] = useState<number | null>(null);
  const [noteReviewError, setNoteReviewError] = useState('');
  const [noteReviewMessage, setNoteReviewMessage] = useState('');
  const [noteCreateOpen, setNoteCreateOpen] = useState(currentView === 'notes' && shouldOpenCreatePanel());
  const [noteCreateForm, setNoteCreateForm] = useState<NoteCreateFormState>(() => makeEmptyNoteCreateForm());
  const [noteCreating, setNoteCreating] = useState(false);
  const [noteCreateError, setNoteCreateError] = useState('');
  const [noteCreateMessage, setNoteCreateMessage] = useState('');
  const [schedulesData, setSchedulesData] = useState<SchedulesData | null>(null);
  const [schedulesLoading, setSchedulesLoading] = useState(currentView === 'schedules' && !scheduleDetailId);
  const [scheduleCreateOpen, setScheduleCreateOpen] = useState(currentView === 'schedules' && !scheduleDetailId && shouldOpenCreatePanel());
  const [scheduleCreateForm, setScheduleCreateForm] = useState<ScheduleCreateFormState>(() => makeEmptyScheduleCreateForm());
  const [scheduleCreating, setScheduleCreating] = useState(false);
  const [scheduleCreateError, setScheduleCreateError] = useState('');
  const [scheduleCreateMessage, setScheduleCreateMessage] = useState('');
  const [scheduleCreatedDetailHref, setScheduleCreatedDetailHref] = useState('');
  const [scheduleDetailData, setScheduleDetailData] = useState<ScheduleDetailData | null>(null);
  const [scheduleDetailLoading, setScheduleDetailLoading] = useState(Boolean(scheduleDetailId));
  const [scheduleQuery, setScheduleQuery] = useState('');
  const [scheduleOwner, setScheduleOwner] = useState('');
  const [scheduleStatus, setScheduleStatus] = useState('');
  const [scheduleActivityType, setScheduleActivityType] = useState('');
  const [scheduleRange, setScheduleRange] = useState('');
  const [prepaymentsData, setPrepaymentsData] = useState<PrepaymentsData | null>(null);
  const [prepaymentsLoading, setPrepaymentsLoading] = useState(currentView === 'prepayments' && !prepaymentCustomerId && !prepaymentDetailId && !prepaymentCreateRoute);
  const [prepaymentCustomerData, setPrepaymentCustomerData] = useState<PrepaymentCustomerData | null>(null);
  const [prepaymentCustomerLoading, setPrepaymentCustomerLoading] = useState(Boolean(prepaymentCustomerId));
  const [prepaymentCustomerUser, setPrepaymentCustomerUser] = useState('');
  const [prepaymentCreateData, setPrepaymentCreateData] = useState<PrepaymentCreateData | null>(null);
  const [prepaymentCreateLoading, setPrepaymentCreateLoading] = useState(prepaymentCreateRoute);
  const [prepaymentDetailData, setPrepaymentDetailData] = useState<PrepaymentDetailData | null>(null);
  const [prepaymentDetailLoading, setPrepaymentDetailLoading] = useState(Boolean(prepaymentDetailId));
  const [prepaymentQuery, setPrepaymentQuery] = useState('');
  const [prepaymentStatus, setPrepaymentStatus] = useState('');
  const [prepaymentDataFilter, setPrepaymentDataFilter] = useState('me');
  const [prepaymentFilterUser, setPrepaymentFilterUser] = useState('');
  const [weeklyReportsData, setWeeklyReportsData] = useState<WeeklyReportsData | null>(null);
  const [weeklyReportsLoading, setWeeklyReportsLoading] = useState(
    currentView === 'weeklyReports' && !weeklyReportDetailId && !weeklyReportCreateRoute,
  );
  const [weeklyReportCreateData, setWeeklyReportCreateData] = useState<WeeklyReportCreateData | null>(null);
  const [weeklyReportCreateLoading, setWeeklyReportCreateLoading] = useState(weeklyReportCreateRoute);
  const [weeklyReportDetailData, setWeeklyReportDetailData] = useState<WeeklyReportDetailData | null>(null);
  const [weeklyReportDetailLoading, setWeeklyReportDetailLoading] = useState(Boolean(weeklyReportDetailId));
  const [weeklyReportYear, setWeeklyReportYear] = useState(() => new URLSearchParams(window.location.search).get('year') || '');
  const [weeklyReportMonth, setWeeklyReportMonth] = useState(() => new URLSearchParams(window.location.search).get('month') || '');
  const [weeklyReportUser, setWeeklyReportUser] = useState(() => new URLSearchParams(window.location.search).get('user_id') || '');
  const [aiWorkspaceData, setAiWorkspaceData] = useState<AIWorkspaceData | null>(null);
  const [aiWorkspaceLoading, setAiWorkspaceLoading] = useState(currentView === 'ai');
  const [mailboxData, setMailboxData] = useState<MailboxData | null>(null);
  const [mailboxLoading, setMailboxLoading] = useState(currentView === 'mail' && !mailboxThreadId);
  const [mailboxThreadData, setMailboxThreadData] = useState<MailboxThreadData | null>(null);
  const [mailboxThreadLoading, setMailboxThreadLoading] = useState(Boolean(mailboxThreadId));
  const [mailboxBox, setMailboxBox] = useState<MailboxType>(initialMailboxBox);
  const [mailboxQuery, setMailboxQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [mailboxPage, setMailboxPage] = useState(() => Number(new URLSearchParams(window.location.search).get('page') || '1') || 1);
  const [mailComposeOpen, setMailComposeOpen] = useState(
    currentView === 'mail' && !mailboxThreadId && new URLSearchParams(window.location.search).get('compose') === '1',
  );
  const [mailComposeForm, setMailComposeForm] = useState<MailComposeFormState>(() => makeEmptyMailComposeForm());
  const [mailComposing, setMailComposing] = useState(false);
  const [mailComposeError, setMailComposeError] = useState('');
  const [mailComposeMessage, setMailComposeMessage] = useState('');
  const [mailSyncing, setMailSyncing] = useState(false);
  const [mailActioningId, setMailActioningId] = useState<number | null>(null);
  const [mailReplyOpen, setMailReplyOpen] = useState(false);
  const [mailReplyForm, setMailReplyForm] = useState<MailComposeFormState>(() => makeEmptyMailComposeForm());
  const [mailReplySaving, setMailReplySaving] = useState(false);
  const [mailReplyError, setMailReplyError] = useState('');
  const [mailReplyMessage, setMailReplyMessage] = useState('');
  const [selectedDealId, setSelectedDealId] = useState<number | null>(mockPipelineData.deals[0]?.id ?? null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<SavedView>('priority');
  const [movingDealId, setMovingDealId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState('');
  const [moveMessage, setMoveMessage] = useState('');

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
    if (currentView !== 'customers' || customerDetailId) {
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
  }, [currentView, customerDetailId, customerOwner, customerPriority, customerQuery, customerStage]);

  useEffect(() => {
    if (currentView !== 'customers' || !customerDetailId) {
      setCustomerDetailData(null);
      setCustomerDetailLoading(false);
      return;
    }
    let alive = true;
    setCustomerDetailLoading(true);
    loadCustomerDetailData(customerDetailId).then((data) => {
      if (!alive) {
        return;
      }
      setCustomerDetailData(data);
      setCustomerDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, customerDetailId]);

  useEffect(() => {
    if (currentView !== 'customers' || customerDetailId || !customersData?.create.canCreate) {
      return;
    }
    const firstCompanyId = customersData.create.companies[0]?.id;
    const firstPriority = customersData.create.priorities[0]?.value || 'scheduled';
    setCustomerCreateForm((previous) => {
      const companyId = previous.companyId || (firstCompanyId ? String(firstCompanyId) : '');
      const companyDepartments = customersData.create.departments.filter(
        (department) => !companyId || String(department.companyId) === companyId,
      );
      const previousDepartmentValid = companyDepartments.some((department) => String(department.id) === previous.departmentId);
      return {
        ...previous,
        companyId,
        departmentId: previousDepartmentValid ? previous.departmentId : (companyDepartments[0]?.id ? String(companyDepartments[0].id) : ''),
        priority: previous.priority || firstPriority,
      };
    });
  }, [currentView, customerDetailId, customersData]);

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
  }, [currentView, noteActionType, noteDetailId, noteNextAction, noteOwner, noteQuery, noteReview]);

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
    const requestedCustomer = notesData.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const fallbackCustomerId = notesData.create.customers[0]?.id;
    const firstActionType = notesData.create.actionTypes[0]?.value || 'customer_meeting';
    setNoteCreateForm((previous) => ({
      ...previous,
      actionType: previous.actionType || firstActionType,
      followupId: requestedCustomer
        ? String(requestedCustomer.id)
        : previous.followupId || (fallbackCustomerId ? String(fallbackCustomerId) : ''),
    }));
  }, [currentView, noteDetailId, notesData]);

  useEffect(() => {
    if (currentView !== 'schedules' || scheduleDetailId) {
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
  }, [currentView, scheduleActivityType, scheduleDetailId, scheduleOwner, scheduleQuery, scheduleRange, scheduleStatus]);

  useEffect(() => {
    if (currentView !== 'schedules' || scheduleDetailId || !schedulesData?.create.canCreate) {
      return;
    }
    const requestedCustomerId = getCreateCustomerParam();
    const requestedCustomer = schedulesData.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const firstCustomerId = requestedCustomer?.id ?? schedulesData.create.customers[0]?.id;
    const firstActivityType = schedulesData.create.activityTypes[0]?.value || 'customer_meeting';
    setScheduleCreateForm((previous) => ({
      ...previous,
      activityType: previous.activityType || firstActivityType,
      followupId: previous.followupId || (firstCustomerId ? String(firstCustomerId) : ''),
    }));
  }, [currentView, scheduleDetailId, schedulesData]);

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
    if (currentView !== 'prepayments' || prepaymentCustomerId || prepaymentDetailId || prepaymentCreateRoute) {
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
  }, [currentView, prepaymentCreateRoute, prepaymentCustomerId, prepaymentDataFilter, prepaymentDetailId, prepaymentFilterUser, prepaymentQuery, prepaymentStatus]);

  useEffect(() => {
    if (currentView !== 'prepayments' || !prepaymentCustomerId) {
      setPrepaymentCustomerData(null);
      setPrepaymentCustomerLoading(false);
      return;
    }
    let alive = true;
    setPrepaymentCustomerLoading(true);
    loadPrepaymentCustomerData(prepaymentCustomerId, prepaymentCustomerUser).then((data) => {
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
  }, [currentView, prepaymentCustomerId, prepaymentCustomerUser]);

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
    if (currentView !== 'weeklyReports' || weeklyReportDetailId || weeklyReportCreateRoute) {
      setWeeklyReportsLoading(false);
      return;
    }
    let alive = true;
    setWeeklyReportsLoading(true);
    loadWeeklyReportsData({
      year: weeklyReportYear,
      month: weeklyReportMonth,
      userId: weeklyReportUser,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setWeeklyReportsData(data);
      setWeeklyReportsLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, weeklyReportCreateRoute, weeklyReportDetailId, weeklyReportMonth, weeklyReportUser, weeklyReportYear]);

  useEffect(() => {
    if (currentView !== 'weeklyReports' || !weeklyReportCreateRoute) {
      setWeeklyReportCreateData(null);
      setWeeklyReportCreateLoading(false);
      return;
    }
    let alive = true;
    setWeeklyReportCreateLoading(true);
    loadWeeklyReportCreateData().then((data) => {
      if (!alive) {
        return;
      }
      setWeeklyReportCreateData(data);
      setWeeklyReportCreateLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, weeklyReportCreateRoute]);

  useEffect(() => {
    if (currentView !== 'weeklyReports' || !weeklyReportDetailId) {
      setWeeklyReportDetailData(null);
      setWeeklyReportDetailLoading(false);
      return;
    }
    let alive = true;
    setWeeklyReportDetailLoading(true);
    loadWeeklyReportDetailData(weeklyReportDetailId).then((data) => {
      if (!alive) {
        return;
      }
      setWeeklyReportDetailData(data);
      setWeeklyReportDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, weeklyReportDetailId]);

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

  useEffect(() => {
    if (currentView !== 'mail' || mailboxThreadId) {
      setMailboxData(null);
      setMailboxLoading(false);
      return;
    }
    let alive = true;
    setMailboxLoading(true);
    loadMailboxData({
      box: mailboxBox,
      q: mailboxQuery,
      page: mailboxPage,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setMailboxData(data);
      setMailboxLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, mailboxBox, mailboxPage, mailboxQuery, mailboxThreadId]);

  useEffect(() => {
    if (currentView !== 'mail' || !mailboxThreadId) {
      setMailboxThreadData(null);
      setMailboxThreadLoading(false);
      return;
    }
    let alive = true;
    setMailboxThreadLoading(true);
    loadMailboxThreadData(mailboxThreadId).then((data) => {
      if (!alive) {
        return;
      }
      setMailboxThreadData(data);
      setMailboxThreadLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, mailboxThreadId]);

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
  const refreshCustomersData = async () => {
    const data = await loadCustomersData({
      q: customerQuery,
      owner: customerOwner,
      priority: customerPriority,
      stage: customerStage,
    });
    setCustomersData(data);
    return data;
  };
  const refreshCustomerDetailData = async () => {
    if (!customerDetailId) {
      return null;
    }
    const data = await loadCustomerDetailData(customerDetailId);
    setCustomerDetailData(data);
    return data;
  };
  const handleCustomerCreateOpenChange = (open: boolean) => {
    setCustomerCreateOpen(open);
    setCustomerCreateError('');
    if (open) {
      setCustomerCreateMessage('');
      setCustomerCreatedDetailHref('');
    }
  };
  const handleCustomerCreateFormChange = (field: keyof CustomerCreateFormState, value: string) => {
    setCustomerCreateForm((previous) => ({
      ...previous,
      [field]: value,
      ...(field === 'companyId' ? { departmentId: '' } : {}),
    }));
    setCustomerCreateError('');
  };
  const handleCustomerCompanyCreateNameChange = (value: string) => {
    setCustomerCompanyCreateName(value);
    setCustomerCreateError('');
  };
  const handleCustomerDepartmentCreateNameChange = (value: string) => {
    setCustomerDepartmentCreateName(value);
    setCustomerCreateError('');
  };
  const handleCreateCustomerCompany = async () => {
    const name = customerCompanyCreateName.trim();
    if (!customersData || customerCompanyCreating || !name) {
      return;
    }
    if (!customersData.create.canCreate) {
      setCustomerCreateError(customersData.create.message || '업체 등록 권한이 없습니다.');
      return;
    }
    setCustomerCompanyCreating(true);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const createdCompany = await createCompanyRecord(name, customersData.create.companySubmitUrl);
      await refreshCustomersData();
      if (createdCompany.company) {
        setCustomerCreateForm((previous) => ({
          ...previous,
          companyId: String(createdCompany.company!.id),
          departmentId: '',
        }));
      }
      setCustomerCompanyCreateName('');
      setCustomerDepartmentCreateName('');
      setCustomerCreateMessage(createdCompany.message || '업체/학교를 추가했습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '업체/학교 추가에 실패했습니다.');
    } finally {
      setCustomerCompanyCreating(false);
    }
  };
  const handleCreateCustomerDepartment = async () => {
    const name = customerDepartmentCreateName.trim();
    const companyId = Number(customerCreateForm.companyId);
    if (!customersData || customerDepartmentCreating || !name) {
      return;
    }
    if (!customersData.create.canCreate) {
      setCustomerCreateError(customersData.create.message || '부서 등록 권한이 없습니다.');
      return;
    }
    if (!companyId) {
      setCustomerCreateError('업체/학교를 먼저 선택하세요.');
      return;
    }
    setCustomerDepartmentCreating(true);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const createdDepartment = await createDepartmentRecord(companyId, name, customersData.create.departmentSubmitUrl);
      await refreshCustomersData();
      if (createdDepartment.department) {
        setCustomerCreateForm((previous) => ({
          ...previous,
          companyId: String(createdDepartment.department!.company_id),
          departmentId: String(createdDepartment.department!.id),
        }));
      }
      setCustomerDepartmentCreateName('');
      setCustomerCreateMessage(createdDepartment.message || '부서/연구실을 추가했습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '부서/연구실 추가에 실패했습니다.');
    } finally {
      setCustomerDepartmentCreating(false);
    }
  };
  const resetCustomerCreateForm = (data: CustomersData | null) => {
    const nextForm = makeEmptyCustomerCreateForm();
    nextForm.priority = data?.create.priorities[0]?.value || nextForm.priority;
    nextForm.companyId = data?.create.companies[0]?.id ? String(data.create.companies[0].id) : '';
    const firstDepartment = data?.create.departments.find((department) => String(department.companyId) === nextForm.companyId);
    nextForm.departmentId = firstDepartment?.id ? String(firstDepartment.id) : '';
    setCustomerCreateForm(nextForm);
  };
  const handleCreateCustomerSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!customersData || customerCreating) {
      return;
    }
    if (!customersData.create.canCreate) {
      setCustomerCreateError(customersData.create.message || '고객 등록 권한이 없습니다.');
      return;
    }
    const companyId = Number(customerCreateForm.companyId);
    const departmentId = Number(customerCreateForm.departmentId);
    if (!companyId) {
      setCustomerCreateError('업체/학교를 선택하세요.');
      return;
    }
    if (!departmentId) {
      setCustomerCreateError('부서/연구실을 선택하세요.');
      return;
    }
    if (!customerCreateForm.customerName.trim()) {
      setCustomerCreateError('고객명을 입력하세요.');
      return;
    }
    if (!customerCreateForm.priority) {
      setCustomerCreateError('우선순위를 선택하세요.');
      return;
    }

    const payload: CustomerCreatePayload = {
      address: customerCreateForm.address.trim() || undefined,
      companyId,
      customerName: customerCreateForm.customerName.trim(),
      departmentId,
      email: customerCreateForm.email.trim() || undefined,
      manager: customerCreateForm.manager.trim() || undefined,
      notes: customerCreateForm.notes.trim() || undefined,
      phoneNumber: customerCreateForm.phoneNumber.trim() || undefined,
      priority: customerCreateForm.priority,
    };

    setCustomerCreating(true);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const createdCustomer = await createCustomerRecord(payload, customersData.create.submitUrl);
      const refreshedData = await refreshCustomersData();
      resetCustomerCreateForm(refreshedData);
      setCustomerCreateMessage(createdCustomer.message || '고객을 등록했습니다.');
      setCustomerCreatedDetailHref(createdCustomer.href || '');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '고객 등록에 실패했습니다.');
    } finally {
      setCustomerCreating(false);
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
    const requestedCustomer = data?.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    nextForm.followupId = requestedCustomer?.id
      ? String(requestedCustomer.id)
      : data?.create.customers[0]?.id
        ? String(data.create.customers[0].id)
        : '';
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
    const nextForm = makeEmptyScheduleCreateForm();
    nextForm.activityType = data?.create.activityTypes[0]?.value || nextForm.activityType;
    nextForm.followupId = data?.create.customers[0]?.id ? String(data.create.customers[0].id) : '';
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
    if (!followupId) {
      setScheduleCreateError('고객을 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.activityType) {
      setScheduleCreateError('활동 유형을 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.visitDate) {
      setScheduleCreateError('방문 날짜를 선택하세요.');
      return;
    }
    if (!scheduleCreateForm.visitTime) {
      setScheduleCreateError('방문 시간을 선택하세요.');
      return;
    }

    const payload: ScheduleCreatePayload = {
      activityType: scheduleCreateForm.activityType,
      expectedRevenue: scheduleCreateForm.expectedRevenue.trim() || undefined,
      followupId,
      location: scheduleCreateForm.location.trim() || undefined,
      notes: scheduleCreateForm.notes.trim() || undefined,
      probability: scheduleCreateForm.probability.trim() || undefined,
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
  const refreshWeeklyReportDetailData = async () => {
    if (!weeklyReportDetailId) {
      return null;
    }
    const data = await loadWeeklyReportDetailData(weeklyReportDetailId);
    setWeeklyReportDetailData(data);
    return data;
  };
  const refreshPrepaymentDetailData = async () => {
    if (!prepaymentDetailId) {
      return null;
    }
    const data = await loadPrepaymentDetailData(prepaymentDetailId);
    setPrepaymentDetailData(data);
    return data;
  };
  const refreshMailboxData = async () => {
    const data = await loadMailboxData({
      box: mailboxBox,
      q: mailboxQuery,
      page: mailboxPage,
    });
    setMailboxData(data);
    return data;
  };
  const refreshMailboxThreadData = async () => {
    if (!mailboxThreadId) {
      return null;
    }
    const data = await loadMailboxThreadData(mailboxThreadId);
    setMailboxThreadData(data);
    return data;
  };
  const handleMailboxBoxChange = (box: MailboxType) => {
    setMailboxBox(box);
    setMailboxPage(1);
    window.history.replaceState(null, '', `/mailbox/?box=${box}`);
  };
  const handleMailComposeOpenChange = (open: boolean) => {
    setMailComposeOpen(open);
    setMailComposeError('');
    if (open) {
      setMailComposeMessage('');
    }
  };
  const handleMailComposeFormChange = (field: keyof MailComposeFormState, value: string) => {
    setMailComposeForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setMailComposeError('');
  };
  const handleMailComposeCustomerChange = (customerId: string) => {
    const customer = mailboxData?.create.customers.find((item) => String(item.id) === customerId);
    setMailComposeForm((previous) => ({
      ...previous,
      followupId: customerId,
      toEmail: customer?.email || previous.toEmail,
    }));
    setMailComposeError('');
  };
  const makeMailboxPayload = (form: MailComposeFormState): MailboxSendPayload => ({
    toEmail: form.toEmail.trim(),
    ccEmails: form.ccEmails.trim() || undefined,
    bccEmails: form.bccEmails.trim() || undefined,
    subject: form.subject.trim(),
    bodyText: form.bodyText.trim(),
    followupId: form.followupId ? Number(form.followupId) : undefined,
    businessCardId: form.businessCardId ? Number(form.businessCardId) : undefined,
  });
  const handleMailComposeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!mailboxData || mailComposing) {
      return;
    }
    const payload = makeMailboxPayload(mailComposeForm);
    if (!payload.toEmail || !payload.subject || !payload.bodyText) {
      setMailComposeError('받는 사람, 제목, 본문을 입력하세요.');
      return;
    }
    setMailComposing(true);
    setMailComposeError('');
    setMailComposeMessage('');
    try {
      await sendMailboxEmail(payload, mailboxData.create.submitUrl);
      setMailComposeMessage('메일을 발송했습니다.');
      setMailComposeForm(makeEmptyMailComposeForm());
      await refreshMailboxData();
    } catch (error) {
      setMailComposeError(error instanceof Error ? error.message : '메일 발송에 실패했습니다.');
    } finally {
      setMailComposing(false);
    }
  };
  const handleMailboxSync = async () => {
    if (!mailboxData || mailSyncing) {
      return;
    }
    setMailSyncing(true);
    setMailComposeError('');
    setMailComposeMessage('');
    try {
      const result = await runMailboxSync(mailboxData.links.sync);
      setMailComposeMessage(result.message || '메일 동기화를 완료했습니다.');
      await refreshMailboxData();
    } catch (error) {
      setMailComposeError(error instanceof Error ? error.message : '메일 동기화에 실패했습니다.');
    } finally {
      setMailSyncing(false);
    }
  };
  const handleMailboxAction = async (
    email: MailboxEmailItem,
    action: 'star' | 'archive' | 'trash' | 'restore' | 'delete',
  ) => {
    if (mailActioningId !== null) {
      return;
    }
    const url = {
      star: email.toggleStarHref,
      archive: email.archiveHref,
      trash: email.trashHref,
      restore: email.restoreHref,
      delete: email.deleteHref,
    }[action];
    if (!url) {
      return;
    }
    if (action === 'delete' && !window.confirm('메일을 영구 삭제하시겠습니까?')) {
      return;
    }
    setMailActioningId(email.id);
    try {
      await runMailboxAction(url);
      if (mailboxThreadId) {
        await refreshMailboxThreadData();
      } else {
        await refreshMailboxData();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '메일 작업에 실패했습니다.';
      if (mailboxThreadId) {
        setMailReplyError(message);
      } else {
        setMailComposeError(message);
      }
    } finally {
      setMailActioningId(null);
    }
  };
  const handleMailReplyOpenChange = (open: boolean) => {
    setMailReplyOpen(open);
    setMailReplyError('');
    if (!open) {
      return;
    }
    setMailReplyMessage('');
    const received = [...(mailboxThreadData?.emails ?? [])].reverse().find((email) => email.type === 'received');
    const target = received ?? mailboxThreadData?.emails[mailboxThreadData.emails.length - 1];
    setMailReplyForm((previous) => ({
      ...previous,
      toEmail: target?.senderEmail || previous.toEmail,
      subject: mailboxThreadData?.thread.subject
        ? mailboxThreadData.thread.subject.startsWith('Re:')
          ? mailboxThreadData.thread.subject
          : `Re: ${mailboxThreadData.thread.subject}`
        : previous.subject,
      followupId: target?.followup.id ? String(target.followup.id) : previous.followupId,
    }));
  };
  const handleMailReplyFormChange = (field: keyof MailComposeFormState, value: string) => {
    setMailReplyForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setMailReplyError('');
  };
  const handleMailReplySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!mailboxThreadData || mailReplySaving) {
      return;
    }
    const payload = makeMailboxPayload(mailReplyForm);
    if (!payload.toEmail || !payload.subject || !payload.bodyText) {
      setMailReplyError('받는 사람, 제목, 본문을 입력하세요.');
      return;
    }
    const received = [...mailboxThreadData.emails].reverse().find((email) => email.type === 'received');
    const target = received ?? mailboxThreadData.emails[mailboxThreadData.emails.length - 1];
    const submitUrl = mailboxThreadData.links.reply || target?.replyHref;
    if (!submitUrl) {
      setMailReplyError('답장 대상 메일을 찾을 수 없습니다.');
      return;
    }
    setMailReplySaving(true);
    setMailReplyError('');
    setMailReplyMessage('');
    try {
      await replyMailboxEmail(submitUrl, payload);
      setMailReplyMessage('답장을 발송했습니다.');
      setMailReplyForm(makeEmptyMailComposeForm());
      await refreshMailboxThreadData();
    } catch (error) {
      setMailReplyError(error instanceof Error ? error.message : '답장 발송에 실패했습니다.');
    } finally {
      setMailReplySaving(false);
    }
  };

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
          companyCreateName={customerCompanyCreateName}
          companyCreating={customerCompanyCreating}
          createDetailHref={customerCreatedDetailHref}
          createDepartmentName={customerDepartmentCreateName}
          createError={customerCreateError}
          createForm={customerCreateForm}
          createMessage={customerCreateMessage}
          createOpen={customerCreateOpen}
          creating={customerCreating}
          data={customersData}
          departmentCreating={customerDepartmentCreating}
          detailData={customerDetailData}
          detailLoading={customerDetailLoading}
          loading={customersLoading}
          owner={customerOwner}
          priority={customerPriority}
          query={customerQuery}
          selectedCustomerId={customerDetailId}
          stage={customerStage}
          onCompanyCreateNameChange={handleCustomerCompanyCreateNameChange}
          onCompanyCreateSubmit={handleCreateCustomerCompany}
          onCreateFormChange={handleCustomerCreateFormChange}
          onCreateOpenChange={handleCustomerCreateOpenChange}
          onCreateSubmit={handleCreateCustomerSubmit}
          onDepartmentCreateNameChange={handleCustomerDepartmentCreateNameChange}
          onDepartmentCreateSubmit={handleCreateCustomerDepartment}
          onDetailRefresh={refreshCustomerDetailData}
          onOwnerChange={setCustomerOwner}
          onPriorityChange={setCustomerPriority}
          onQueryChange={setCustomerQuery}
          onStageChange={setCustomerStage}
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

  if (currentView === 'mail') {
    if (mailboxThreadId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <MailboxThreadPage
            actioningId={mailActioningId}
            data={mailboxThreadData}
            loading={mailboxThreadLoading}
            replyError={mailReplyError}
            replyForm={mailReplyForm}
            replyMessage={mailReplyMessage}
            replyOpen={mailReplyOpen}
            replySaving={mailReplySaving}
            onAction={handleMailboxAction}
            onReplyFormChange={handleMailReplyFormChange}
            onReplyOpenChange={handleMailReplyOpenChange}
            onReplySubmit={handleMailReplySubmit}
          />
        </AppShell>
      );
    }

    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <MailboxPage
          actioningId={mailActioningId}
          composeError={mailComposeError}
          composeForm={mailComposeForm}
          composeMessage={mailComposeMessage}
          composeOpen={mailComposeOpen}
          composing={mailComposing}
          data={mailboxData}
          loading={mailboxLoading}
          query={mailboxQuery}
          selectedBox={mailboxBox}
          syncing={mailSyncing}
          onAction={handleMailboxAction}
          onBoxChange={handleMailboxBoxChange}
          onComposeCustomerChange={handleMailComposeCustomerChange}
          onComposeFormChange={handleMailComposeFormChange}
          onComposeOpenChange={handleMailComposeOpenChange}
          onComposeSubmit={handleMailComposeSubmit}
          onQueryChange={setMailboxQuery}
          onSync={handleMailboxSync}
        />
      </AppShell>
    );
  }

  if (currentView === 'weeklyReports') {
    if (weeklyReportCreateRoute) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <WeeklyReportEditorPage
            createData={weeklyReportCreateData}
            detailData={null}
            loading={weeklyReportCreateLoading}
            mode="create"
            routeData={pipelineData}
          />
        </AppShell>
      );
    }

    if (weeklyReportDetailId && weeklyReportEditRoute) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <WeeklyReportEditorPage
            createData={null}
            detailData={weeklyReportDetailData}
            loading={weeklyReportDetailLoading}
            mode="edit"
            routeData={pipelineData}
          />
        </AppShell>
      );
    }

    if (weeklyReportDetailId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <WeeklyReportDetailPage
            data={weeklyReportDetailData}
            loading={weeklyReportDetailLoading}
            onRefresh={refreshWeeklyReportDetailData}
            routeData={pipelineData}
          />
        </AppShell>
      );
    }

    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <WeeklyReportsPage
          data={weeklyReportsData}
          loading={weeklyReportsLoading}
          month={weeklyReportMonth}
          routeData={pipelineData}
          userId={weeklyReportUser}
          year={weeklyReportYear}
          onMonthChange={setWeeklyReportMonth}
          onUserChange={setWeeklyReportUser}
          onYearChange={setWeeklyReportYear}
        />
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

    if (prepaymentCustomerId) {
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
