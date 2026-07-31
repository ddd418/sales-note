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
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Clock,
  Columns3,
  Copy,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Filter,
  LayoutDashboard,
  ListChecks,
  Loader2,
  Link2,
  MessageSquareText,
  MoveUpRight,
  ArrowRightLeft,
  PanelRight,
  PanelRightClose,
  PanelRightOpen,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  Trash2,
  Upload,
  Users,
  X,
} from 'lucide-react';
import { Fragment, Suspense, type ChangeEvent, type ClipboardEvent, type DragEvent, type FormEvent, type KeyboardEvent, type ReactNode, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  DashboardData,
  DashboardHistoryItem,
  DashboardScheduleItem,
  DemoAccountOption,
  DemoRecordItem,
  DemoRecordPayload,
  DemoRecordsData,
  DocumentTemplateItem,
  DocumentTemplateMutationPayload,
  DocumentTemplatesData,
  EmployeeManagementItem,
  EmployeeMutationPayload,
  EmployeesData,
  FollowupQuoteItem,
  FollowupQuoteItemsData,
  FollowupQuoteOption,
  NotesData,
  NoteDetailData,
  NoteDetailItem,
  NoteEditPayload,
  NoteFileItem,
  NoteItem,
  NoteReplyItem,
  ProductBulkDeleteResult,
  ProductBulkUpsertResult,
  ProductDeleteReference,
  ProductManagementData,
  ProductManagementItem,
  ProductMutationPayload,
  ProductOption,
  ScheduleCalendarData,
  SchedulesData,
  ScheduleDetailData,
  ScheduleDetailItem,
  ScheduleDeliveryItem,
  ScheduleDeliveryItemPayload,
  ScheduleDocumentAction,
  ScheduleDocumentFormatAction,
  ScheduleDocumentRequestOptions,
  ScheduleGeneratedDocument,
  ScheduleDocumentPreviewData,
  ScheduleFileItem,
  ScheduleEditPayload,
  ScheduleItem,
  ProfileData,
  ProfilePasswordPayload,
  ProfileUpdatePayload,
  NoteCreatePayload,
  PersonalScheduleDetailData,
  PersonalSchedulePayload,
  addNoteReply,
  bulkDeleteProducts,
  bulkUpsertProducts,
  changeProfilePassword,
  createDemoRecord,
  createEmployee,
  createNote as createSalesNote,
  ScheduleCreatePayload,
  createDocumentTemplate,
  deleteNote as deleteSalesNote,
  createPersonalSchedule,
  importProductsExcel,
  createSchedule as createCustomerSchedule,
  deleteNoteFile,
  deleteNoteReply,
  deleteSchedule,
  deleteScheduleFile,
  deleteGeneratedDocument,
  deleteDocumentTemplate,
  deleteDemoRecord,
  downloadScheduleDocument,
  loadDashboardData,
  loadDemoRecordsData,
  loadDocumentTemplatesData,
  loadEmployeesData,
  loadNoteDetailData,
  loadNotesData,
  loadProductManagementData,
  loadProducts,
  loadPersonalScheduleDetailData,
  loadProfileData,
  loadScheduleCalendarData,
  loadScheduleDocumentPreview,
  loadScheduleDetailData,
  loadFollowupQuoteItems,
  loadSchedulesData,
  loadPipelineData,
  moveDealStage,
  hideDealCard,
  unhideDealCard,
  toggleEmployeeActive,
  toggleNoteReviewed,
  updateEmployee,
  updateNote as updateSalesNote,
  updatePersonalSchedule,
  updateSchedule as updateCustomerSchedule,
  updateScheduleDeliveryItems,
  updateScheduleStatus,
  uploadNoteFiles,
  uploadScheduleFiles,
  replaceProductReference,
  saveProduct,
  toggleDocumentTemplateDefault,
  updateDocumentTemplate,
  updateDemoRecord,
  updateProfile,
} from './api';
import type {
  AccountContactPayload,
  AccountInfoUpdatePayload,
  CustomerAccountContact,
  CustomerAttachmentItem,
  CustomerCreatePayload,
  CustomerDeliveryRecord,
  CustomerDetailData,
  CustomerEditPayload,
  CustomerItem,
  CustomerQuoteRecord,
  CustomerRowMode,
  CustomerServiceRecord,
  CustomersData,
} from './api/accounts';
import {
  createCompany as createCompanyRecord,
  createCustomer as createCustomerRecord,
  createDepartment as createDepartmentRecord,
  deleteCompanyRecord,
  deleteCustomer as deleteCustomerRecord,
  deleteDepartmentRecord,
  loadAccountDetailData,
  loadCustomerDetailData,
  loadCustomersData,
  saveAccountContact,
  updateAccountInfo,
  updateCompany as updateCompanyRecord,
  updateCustomer as updateCustomerRecord,
  updateDepartment as updateDepartmentRecord,
} from './api/accounts';
import type {
  PrepaymentCreateData,
  PrepaymentCustomerData,
  PrepaymentDetailData,
  PrepaymentFormPayload,
  PrepaymentListItem,
  PrepaymentOption,
  PrepaymentsData,
  SchedulePrepaymentSelectionPayload,
} from './api/prepayments';
import {
  cancelPrepayment as cancelCustomerPrepayment,
  createPrepayment as createCustomerPrepayment,
  deletePrepayment as deleteCustomerPrepayment,
  loadPrepaymentAccountData,
  loadPrepaymentCreateData,
  loadPrepaymentCustomerData,
  loadPrepaymentDetailData,
  loadPrepayments,
  loadPrepaymentsData,
  transferPrepayment as transferCustomerPrepayment,
  updatePrepayment as updateCustomerPrepayment,
} from './api/prepayments';
import type {
  AIWorkspaceActionEvidence,
  ScheduleAICoachResponse,
} from './api/ai';
import {
  generateScheduleAICoach,
} from './api/ai';
import { emptyPipelineData, type Deal, type HiddenDeal, type PipelineData, type PipelineStage, type PriorityTask, type StageSummary } from './mockData';
import {
  CompanyManagementPage,
  PipelineSheetPage,
  ReceivablesPage,
} from './pages/lazyPages';
import { AppShell, TopBar, type MainView } from './components/shared/CrmShell';
import { AttachmentManager, type AttachmentManagerFile } from './components/shared/AttachmentManager';
import { DashboardApiAlert, DashboardEmpty, DashboardLoading } from './components/shared/FeedbackStates';
import { CRM_CLIENT_NAVIGATION_EVENT } from './navigationEvents';

const scheduleCalendarUrl = '/schedules/calendar/';

type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';

type RouteAction = {
  label: string;
  href: string;
  primary?: boolean;
};

type CustomerDetailMode = 'customer' | 'account';

type NoteCreateFormState = {
  actionType: string;
  activityDate: string;
  content: string;
  departmentId: string;
  followupId: string;
  nextAction: string;
  nextActionDate: string;
  scheduleId: string;
};

type NoteEditFormState = NoteCreateFormState & {
  deliveryAmount: string;
  deliveryItems: string;
};

type ScheduleCreateFormState = {
  activityType: string;
  departmentId: string;
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

type PersonalScheduleFormState = {
  title: string;
  content: string;
  scheduleDate: string;
  scheduleTime: string;
};

type EmployeeFormState = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  companyId: string;
  companyName: string;
  password: string;
  passwordConfirm: string;
  canDownloadExcel: boolean;
  canUseAi: boolean;
  isActive: boolean;
};

type SchedulePrepaymentEditRow = PrepaymentOption & {
  selected: boolean;
  amountInput: string;
};

type PrepaymentFormState = {
  amount: string;
  balance: string;
  customerId: string;
  departmentId: string;
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
  discountRate: string;
  discountUnitPrice: string;
  quoteGroup: string;
  notes: string;
  optionDescription: string;
  sourceQuoteScheduleId: string;
  sourceQuoteItemId: string;
};

type ScheduleDeliveryEditField = 'productId' | 'productQuery' | 'itemName' | 'quantity' | 'unit' | 'unitPrice' | 'discountRate' | 'discountUnitPrice' | 'quoteGroup' | 'notes' | 'optionDescription';

type ScheduleQuoteGroupNoteState = Record<string, string>;

type ProfileFormState = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
};

type ProfilePasswordFormState = {
  oldPassword: string;
  newPassword1: string;
  newPassword2: string;
};

type DocumentTemplateFormState = {
  companyId: string;
  description: string;
  documentType: string;
  isDefault: boolean;
  name: string;
};

type ProductFormState = {
  description: string;
  isActive: boolean;
  productCode: string;
  specification: string;
  standardPrice: string;
  unit: string;
};

type ProductSortField = 'code' | 'description' | 'specification' | 'unit' | 'price' | 'status' | 'quoteCount' | 'deliveryCount' | 'updatedAt';
type ProductSortOrder = 'asc' | 'desc';

type CustomerCreateFormState = {
  address: string;
  companyId: string;
  customerName: string;
  departmentId: string;
  email: string;
  manager: string;
  notes: string;
  phoneNumber: string;
};

type CustomerCompanyManageOption = CustomersData['create']['companies'][number];
type CustomerDepartmentManageOption = CustomersData['create']['departments'][number];

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
  status: string;
};

type AccountInfoFormState = {
  address: string;
  companyId: string;
  departmentName: string;
  notes: string;
};

type AccountContactFormState = {
  address: string;
  contactRole: string;
  customerName: string;
  departmentId: string;
  email: string;
  isActive: boolean;
  manager: string;
  notes: string;
  phoneNumber: string;
  pipelineStage: string;
  status: string;
};

type AccountContactEditorMode = '' | 'create' | 'edit';

type DemoRecordFormState = {
  departmentId: string;
  customerId: string;
  productId: string;
  productName: string;
  serialNumber: string;
  quantity: string;
  status: string;
  startDate: string;
  expectedReturnDate: string;
  returnedDate: string;
  ownerId: string;
  notes: string;
};

type SearchableSelectOption = {
  value: string;
  label: string;
  meta?: string;
  searchText?: string;
};

type CustomerSelectSource = {
  id: number;
  departmentId?: number | null;
  companyId?: number | null;
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

const parseLocalDate = (value: string) => {
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) {
    return new Date();
  }
  return new Date(year, month - 1, day);
};

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

const getScheduleCalendarRange = (monthValue: string) => {
  const [year, month] = monthValue.split('-').map(Number);
  const start = new Date(year, month - 1, 1);
  const end = new Date(year, month, 0);
  return {
    start: localDateInputValue(start),
    end: localDateInputValue(end),
  };
};

const shiftScheduleCalendarMonth = (monthValue: string, offset: number) => {
  const [year, month] = monthValue.split('-').map(Number);
  const shifted = new Date(year, month - 1 + offset, 1);
  return localDateInputValue(shifted).slice(0, 7);
};

const getScheduleCalendarDataFilterParam = () => {
  const value = new URLSearchParams(window.location.search).get('data_filter') || '';
  return value === 'all' || value === 'user' ? value : 'me';
};

const getScheduleCalendarCreateParam = () => (
  new URLSearchParams(window.location.search).get('create') || ''
);

const getScheduleCalendarPersonalIdParam = () => {
  const value = new URLSearchParams(window.location.search).get('personal') || '';
  const id = Number(value);
  return Number.isFinite(id) && id > 0 ? id : 0;
};

const shouldOpenCreatePanel = () => new URLSearchParams(window.location.search).get('create') === '1';

const guidedPanelFocusableSelector = [
  'input:not([type="hidden"]):not(:disabled):not([readonly])',
  'select:not(:disabled)',
  'textarea:not(:disabled):not([readonly])',
  'button:not(:disabled)',
  'a[href]',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

type GuidedPanelFocusRef = {
  current: HTMLElement | null;
};

type GuidedPanelFocusKey = string | number | boolean | null | undefined;

const requestGuidedPanelFocus = (
  targetRef: GuidedPanelFocusRef,
  options: { focusFirst?: boolean } = {},
) => {
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      const section = targetRef.current;
      if (!section) {
        return;
      }
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      section.classList.remove('guided-panel-focus');
      void section.offsetWidth;
      section.classList.add('guided-panel-focus');
      window.setTimeout(() => section.classList.remove('guided-panel-focus'), 1800);
      if (options.focusFirst === false) {
        return;
      }
      window.setTimeout(() => {
        const focusTarget = section.querySelector<HTMLElement>(guidedPanelFocusableSelector);
        focusTarget?.focus({ preventScroll: true });
      }, 280);
    });
  });
};

function useGuidedPanelFocus(
  isOpen: boolean,
  targetRef: GuidedPanelFocusRef,
  focusKey: GuidedPanelFocusKey = 'open',
  options: { focusFirst?: boolean } = {},
) {
  const lastFocusKeyRef = useRef('');

  useEffect(() => {
    const normalizedKey = isOpen ? String(focusKey ?? 'open') : '';
    if (isOpen && normalizedKey && lastFocusKeyRef.current !== normalizedKey) {
      requestGuidedPanelFocus(targetRef, options);
    }
    lastFocusKeyRef.current = normalizedKey;
  }, [focusKey, isOpen, targetRef, options.focusFirst]);
}

const getNoteReviewParam = () => {
  const value = new URLSearchParams(window.location.search).get('review') ||
    new URLSearchParams(window.location.search).get('review_filter') ||
    '';
  return value === 'unreviewed' || value === 'reviewed' ? value : '';
};

const makeEmptyEmployeeForm = (data?: EmployeesData | null): EmployeeFormState => ({
  username: '',
  firstName: '',
  lastName: '',
  email: '',
  role: data?.scope.mode === 'admin' ? 'salesman' : 'salesman',
  companyId: data?.scope.mode === 'manager' && data.scope.companyId ? String(data.scope.companyId) : '',
  companyName: data?.scope.mode === 'manager' ? data.scope.companyName : '',
  password: '',
  passwordConfirm: '',
  canDownloadExcel: false,
  canUseAi: false,
  isActive: true,
});

const makeEmployeeEditForm = (employee: EmployeeManagementItem, data?: EmployeesData | null): EmployeeFormState => ({
  username: employee.username || '',
  firstName: employee.firstName || '',
  lastName: employee.lastName || '',
  email: employee.email || '',
  role: employee.role || 'salesman',
  companyId: employee.companyId ? String(employee.companyId) : '',
  companyName: employee.company || data?.scope.companyName || '',
  password: '',
  passwordConfirm: '',
  canDownloadExcel: Boolean(employee.canDownloadExcel),
  canUseAi: Boolean(employee.canUseAi),
  isActive: Boolean(employee.isActive),
});

const employeePayloadFromForm = (form: EmployeeFormState): EmployeeMutationPayload => ({
  username: form.username.trim(),
  firstName: form.firstName.trim(),
  lastName: form.lastName.trim(),
  email: form.email.trim(),
  role: form.role,
  companyId: form.companyId || undefined,
  companyName: form.companyName.trim() || undefined,
  password: form.password || undefined,
  passwordConfirm: form.passwordConfirm || undefined,
  canDownloadExcel: form.canDownloadExcel,
  canUseAi: form.canUseAi,
  isActive: form.isActive,
});

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

const makeNoteEditForm = (note: NoteDetailItem | null): NoteEditFormState => ({
  actionType: note?.actionType || 'customer_meeting',
  activityDate: note?.meetingDate || note?.deliveryDate || note?.activityDate || '',
  content: note?.content || '',
  departmentId: note?.departmentId ? String(note.departmentId) : '',
  deliveryAmount: note?.deliveryAmount ? String(note.deliveryAmount) : '',
  deliveryItems: note?.deliveryItems || '',
  followupId: note?.followupId ? String(note.followupId) : '',
  nextAction: note?.nextAction || '',
  nextActionDate: note?.nextActionDate || '',
  scheduleId: note?.scheduleId ? String(note.scheduleId) : '',
});

const scheduleActivityToNoteActionType = (activityType: string) => {
  if (activityType === 'delivery') {
    return 'delivery_schedule';
  }
  if (activityType === 'quote') {
    return 'quote';
  }
  if (activityType === 'service') {
    return 'service';
  }
  return 'customer_meeting';
};

const isNoteActionAllowed = (actionTypes: Array<{ value: string }>, actionType: string) => (
  Boolean(actionType && actionTypes.some((option) => option.value === actionType))
);

const scheduleNoteActionTypeOptions = [
  { value: 'customer_meeting', label: '고객 미팅' },
  { value: 'quote', label: '견적' },
  { value: 'delivery_schedule', label: '납품 일정' },
  { value: 'service', label: '메모' },
];

const makeScheduleNoteCreateForm = (schedule: ScheduleDetailItem | null): NoteCreateFormState => ({
  actionType: scheduleActivityToNoteActionType(schedule?.activityType || ''),
  activityDate: schedule?.date || localDateInputValue(),
  content: '',
  departmentId: schedule?.departmentId ? String(schedule.departmentId) : '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  nextAction: '',
  nextActionDate: '',
  scheduleId: schedule?.id ? String(schedule.id) : '',
});

const makeEmptyScheduleCreateForm = (visitDate = localDateInputValue()): ScheduleCreateFormState => ({
  activityType: 'customer_meeting',
  departmentId: '',
  expectedRevenue: '',
  followupId: '',
  location: '',
  notes: '',
  probability: '',
  visitDate,
  visitTime: '09:00',
});

const probabilityInputValueFromSchedule = (probability: number | null | undefined) => (
  probability === null || probability === undefined ? '' : String(probability)
);

const makeScheduleEditForm = (schedule: ScheduleDetailItem | null): ScheduleEditFormState => ({
  activityType: schedule?.activityType || 'customer_meeting',
  departmentId: schedule?.departmentId ? String(schedule.departmentId) : '',
  expectedCloseDate: schedule?.expectedCloseDate || '',
  expectedRevenue: schedule?.expectedRevenue ? String(schedule.expectedRevenue) : '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  location: schedule?.location || '',
  notes: schedule?.notesFull || schedule?.notes || '',
  probability: probabilityInputValueFromSchedule(schedule?.probability),
  purchaseConfirmed: Boolean(schedule?.purchaseConfirmed),
  status: schedule?.status || 'scheduled',
  usePrepayment: Boolean(schedule?.usePrepayment),
  visitDate: schedule?.date || '',
  visitTime: schedule?.time || '09:00',
});

const makeEmptyPersonalScheduleForm = (scheduleDate = localDateInputValue()): PersonalScheduleFormState => ({
  title: '',
  content: '',
  scheduleDate,
  scheduleTime: '09:00',
});

const makePersonalScheduleEditForm = (schedule: ScheduleItem | null): PersonalScheduleFormState => ({
  title: schedule?.title || '',
  content: schedule?.notesFull || schedule?.notes || '',
  scheduleDate: schedule?.date || localDateInputValue(),
  scheduleTime: schedule?.time || '09:00',
});

const makeScheduleCalendarCreateForm = (data: ScheduleCalendarData | null, visitDate: string): ScheduleCreateFormState => {
  const form = makeEmptyScheduleCreateForm(visitDate);
  form.activityType = data?.create.activityTypes[0]?.value || form.activityType;
  const firstCustomer = data?.create.customers[0];
  const firstDepartmentId = firstCustomer?.departmentId ?? data?.create.departments[0]?.id;
  form.departmentId = firstDepartmentId ? String(firstDepartmentId) : '';
  form.followupId = firstCustomer?.id ? String(firstCustomer.id) : '';
  return form;
};

const normalizeProbabilityInputValue = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return trimmed;
  }
  const normalized = Math.min(100, Math.max(0, Math.round(parsed / 5) * 5));
  return String(normalized);
};

const isQuoteProbabilityRequired = (activityType: string) => activityType === 'quote';

const scheduleCreateFormToPayload = (form: ScheduleCreateFormState): { payload?: ScheduleCreatePayload; error?: string } => {
  const followupId = Number(form.followupId);
  const departmentId = Number(form.departmentId);
  if (!followupId && !departmentId) {
    return { error: '고객 또는 부서/연구실을 선택하세요.' };
  }
  if (!form.activityType) {
    return { error: '일정 유형을 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '일정 시간을 선택하세요.' };
  }
  const probability = normalizeProbabilityInputValue(form.probability);
  if (isQuoteProbabilityRequired(form.activityType) && !probability) {
    return { error: '견적 성공 확률은 필수입니다.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      departmentId: departmentId || undefined,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      followupId: followupId || undefined,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: probability || undefined,
      visitDate: form.visitDate,
      visitTime: form.visitTime,
    },
  };
};

const personalScheduleFormToPayload = (form: PersonalScheduleFormState): { payload?: PersonalSchedulePayload; error?: string } => {
  if (!form.title.trim()) {
    return { error: '일정 제목을 입력하세요.' };
  }
  if (!form.scheduleDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.scheduleTime) {
    return { error: '일정 시간을 선택하세요.' };
  }

  return {
    payload: {
      title: form.title.trim(),
      content: form.content.trim() || undefined,
      scheduleDate: form.scheduleDate,
      scheduleTime: form.scheduleTime,
    },
  };
};

const scheduleEditFormToPayload = (form: ScheduleEditFormState): { payload?: ScheduleEditPayload; error?: string } => {
  const followupId = Number(form.followupId);
  if (!followupId) {
    return { error: '고객을 선택하세요.' };
  }
  if (!form.activityType) {
    return { error: '일정 유형을 선택하세요.' };
  }
  if (!form.status) {
    return { error: '일정 상태를 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '일정 시간을 선택하세요.' };
  }
  const probability = normalizeProbabilityInputValue(form.probability);
  if (isQuoteProbabilityRequired(form.activityType) && !probability) {
    return { error: '견적 성공 확률은 필수입니다.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      expectedCloseDate: form.expectedCloseDate || undefined,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      followupId,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: probability || undefined,
      purchaseConfirmed: form.purchaseConfirmed,
      status: form.status,
      visitDate: form.visitDate,
      visitTime: form.visitTime,
    },
  };
};

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
  departmentId: '',
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
  departmentId: prepayment?.departmentId ? String(prepayment.departmentId) : '',
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
  discountRate: item?.discountRate ? String(item.discountRate) : '',
  discountUnitPrice: item?.discountUnitPrice !== undefined && item.discountUnitPrice !== null ? String(item.discountUnitPrice) : '',
  quoteGroup: item?.quoteGroup || '',
  notes: item?.notes || '',
  optionDescription: item?.optionDescription || '',
  sourceQuoteScheduleId: item?.sourceQuoteScheduleId ? String(item.sourceQuoteScheduleId) : '',
  sourceQuoteItemId: item?.sourceQuoteItemId ? String(item.sourceQuoteItemId) : '',
});

const makeScheduleDeliveryEditRows = (items: ScheduleDeliveryItem[] = []): ScheduleDeliveryEditRow[] => (
  items.length > 0
    ? items.map((item, index) => makeScheduleDeliveryEditRow(item, index))
    : [makeScheduleDeliveryEditRow(undefined, 0)]
);

const normalizeQuoteGroupKey = (value: string) => value.trim().slice(0, 100);

const quoteGroupLabel = (value: string) => normalizeQuoteGroupKey(value) || '기본 견적서';

const quoteImportOptionTitle = (quote: FollowupQuoteOption) => {
  const label = quote.quoteGroupLabel || quoteGroupLabel(quote.quoteGroup);
  return label.includes('견적') ? label : `${label} 견적`;
};

const quoteImportItemSummary = (item: FollowupQuoteItem) => {
  const remaining = item.remainingQuantity || item.quantity || 0;
  const original = item.originalQuantity || remaining;
  const unit = item.unit || '';
  const numberLabel = (value: number) => new Intl.NumberFormat('ko-KR').format(value);
  const quantityLabel = original > remaining
    ? `${numberLabel(remaining)}/${numberLabel(original)}${unit}`
    : `${numberLabel(remaining)}${unit}`;
  return `${item.itemName || item.productCode || '품목'} ${quantityLabel}`;
};

const makeScheduleQuoteGroupNotes = (schedule: ScheduleDetailItem | null): ScheduleQuoteGroupNoteState => {
  const notes: ScheduleQuoteGroupNoteState = {};
  schedule?.quoteGroupNotes?.forEach((item) => {
    notes[normalizeQuoteGroupKey(item.quoteGroup)] = item.notes || '';
  });
  if (!notes[''] && schedule?.quoteExtraNotes) {
    notes[''] = schedule.quoteExtraNotes;
  }
  return notes;
};

const scheduleQuoteGroupsFromRows = (rows: ScheduleDeliveryEditRow[]): string[] => {
  const seen = new Set<string>();
  const groups: string[] = [];
  rows.forEach((row) => {
    const hasItemInput = Boolean(
      row.productId ||
      row.itemName.trim() ||
      row.quantity.trim() ||
      row.unitPrice.trim() ||
      row.discountRate.trim() ||
      row.discountUnitPrice.trim() ||
      row.notes.trim() ||
      row.optionDescription.trim(),
    );
    if (!hasItemInput && !row.quoteGroup.trim()) {
      return;
    }
    const group = normalizeQuoteGroupKey(row.quoteGroup);
    if (seen.has(group)) {
      return;
    }
    seen.add(group);
    groups.push(group);
  });
  return groups.length > 0 ? groups : [''];
};

const parsePositiveFormNumber = (value: string) => {
  const normalized = String(value ?? '').replace(/,/g, '').trim();
  if (!normalized) {
    return null;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
};

const moneyInputValue = (value: number) => String(Math.round(value));

const rateInputValue = (value: number) => {
  if (!Number.isFinite(value)) return '';
  return String(Math.round(value * 100) / 100);
};

const discountUnitFromRate = (base: number, rate: number) => (
  Math.max(Math.round(base * (100 - rate) / 100), 0)
);

const discountRateFromUnit = (base: number, discountUnit: number) => (
  base > 0 ? Math.max(Math.min((1 - discountUnit / base) * 100, 100), 0) : 0
);

const scheduleDeliveryEditRowsTotal = (rows: ScheduleDeliveryEditRow[]) => (
  rows.reduce((total, row) => {
    const quantity = Number(row.quantity);
    const unitPrice = parsePositiveFormNumber(row.unitPrice);
    const discountUnitPrice = parsePositiveFormNumber(row.discountUnitPrice);
    const discountRate = parsePositiveFormNumber(row.discountRate);
    if (!Number.isFinite(quantity) || quantity <= 0 || unitPrice === null || unitPrice < 0) {
      return total;
    }
    let effectiveUnitPrice = unitPrice;
    if (discountUnitPrice !== null) {
      effectiveUnitPrice = Math.max(discountUnitPrice, 0);
    } else if (discountRate !== null) {
      effectiveUnitPrice = discountUnitFromRate(unitPrice, Math.min(Math.max(discountRate, 0), 100));
    }
    return total + Math.round(quantity * effectiveUnitPrice * 1.1);
  }, 0)
);

const makeScheduleDeliveryEditRowFromQuoteItem = (
  item: FollowupQuoteItem,
  quote: FollowupQuoteOption,
  index: number,
): ScheduleDeliveryEditRow => {
  const quantity = item.quantity || 1;
  const itemTotal = item.totalPrice || item.remainingAmount || 0;
  const quoteSingleItemFallback = quote.items.length === 1 ? quote.remainingAmount || quote.expectedRevenue || 0 : 0;
  const totalFallback = itemTotal || quoteSingleItemFallback;
  const fallbackUnitPrice = totalFallback > 0 && quantity > 0
    ? Math.round(totalFallback / quantity / 1.1)
    : 0;
  const unitPrice = item.unitPrice > 0
    ? item.unitPrice
    : item.effectiveUnitPrice > 0
      ? item.effectiveUnitPrice
      : fallbackUnitPrice;
  const usesOriginalUnitPrice = item.unitPrice > 0;
  const hasExplicitDiscount = usesOriginalUnitPrice
    && item.discountUnitPrice !== undefined
    && item.discountUnitPrice !== null
    && (item.discountRate > 0 || item.discountUnitPrice < unitPrice);
  return {
    rowId: `quote-${quote.optionId}-${item.id ?? index}-${Date.now()}-${index}`,
    productId: item.productId ? String(item.productId) : '',
    productQuery: item.productCode || '',
    itemName: item.itemName || item.productCode || '',
    quantity: String(quantity),
    unit: item.unit || 'EA',
    unitPrice: unitPrice > 0 ? moneyInputValue(unitPrice) : '',
    discountRate: usesOriginalUnitPrice && item.discountRate ? rateInputValue(item.discountRate) : '',
    discountUnitPrice: hasExplicitDiscount ? moneyInputValue(item.discountUnitPrice ?? 0) : '',
    quoteGroup: item.quoteGroup || '',
    notes: item.notes || '',
    optionDescription: item.optionDescription || '',
    sourceQuoteScheduleId: item.sourceQuoteScheduleId ? String(item.sourceQuoteScheduleId) : String(quote.scheduleId || ''),
    sourceQuoteItemId: item.sourceQuoteItemId ? String(item.sourceQuoteItemId) : String(item.id || ''),
  };
};

const scheduleDeliveryRowsHaveUserInput = (rows: ScheduleDeliveryEditRow[]) => rows.some((row) => Boolean(
  row.id ||
  row.productId ||
  row.itemName.trim() ||
  row.unitPrice.trim() ||
  row.discountRate.trim() ||
  row.discountUnitPrice.trim() ||
  row.quoteGroup.trim() ||
  row.notes.trim() ||
  row.optionDescription.trim()
));

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

const makeEmptyDocumentTemplateForm = (): DocumentTemplateFormState => ({
  companyId: '',
  description: '',
  documentType: 'quotation',
  isDefault: false,
  name: '',
});

const makeDocumentTemplateForm = (template: DocumentTemplateItem | null): DocumentTemplateFormState => ({
  companyId: template?.company?.id ? String(template.company.id) : '',
  description: template?.description || '',
  documentType: template?.documentType || 'quotation',
  isDefault: Boolean(template?.isDefault),
  name: template?.name || '',
});

const makeEmptyProductForm = (): ProductFormState => ({
  description: '',
  isActive: true,
  productCode: '',
  specification: '',
  standardPrice: '',
  unit: 'EA',
});

const makeProductForm = (product: ProductManagementItem | null): ProductFormState => ({
  description: product?.description || '',
  isActive: product ? product.isActive : true,
  productCode: product?.productCode || '',
  specification: product?.specification || '',
  standardPrice: product ? String(product.standardPrice) : '',
  unit: product?.unit || 'EA',
});

const normalizeProductPriceInput = (value: string) => value.replace(/[,\s원]/g, '').trim();

const productFormToPayload = (form: ProductFormState): ProductMutationPayload => ({
  description: form.description.trim(),
  isActive: form.isActive,
  productCode: form.productCode.trim(),
  specification: form.specification.trim(),
  standardPrice: normalizeProductPriceInput(form.standardPrice) || '0',
  unit: form.unit.trim() || 'EA',
});

const splitProductPasteLine = (line: string) => {
  const trimmed = line.trim();
  if (!trimmed) return [];
  if (trimmed.includes('\t')) {
    return trimmed.split('\t').map((cell) => cell.trim());
  }
  return trimmed.split(/\s{2,}/).map((cell) => cell.trim());
};

const isProductPasteHeader = (cells: string[]) => {
  const normalizedCells = cells.map((cell) => cell.trim().toLowerCase());
  const headerText = normalizedCells.join(' ');
  return (
    normalizedCells.some((cell) => ['품번', '품목코드', '제품코드', '코드', 'code'].includes(cell)) ||
    headerText.includes('product code') ||
    headerText.includes('기준단가') ||
    headerText.includes('출고단가')
  );
};

const parseProductPasteRows = (text: string): ProductMutationPayload[] => {
  const rows: ProductMutationPayload[] = [];
  const seenCodes = new Set<string>();
  text.split(/\r?\n/).forEach((line) => {
    const cells = splitProductPasteLine(line);
    if (cells.length < 2 || isProductPasteHeader(cells)) {
      return;
    }

    const productCode = cells[0] || '';
    let description = '';
    let specification = '';
    let unit = 'EA';
    let price = '';

    if (cells.length >= 5) {
      description = cells[1] || '';
      specification = cells[2] || '';
      unit = cells[3] || 'EA';
      price = cells.slice(4).join('');
    } else if (cells.length >= 4) {
      specification = cells[1] || '';
      unit = cells[2] || 'EA';
      price = cells.slice(3).join('');
    } else {
      specification = cells[1] || '';
      price = cells[2] || '';
    }

    const normalizedCode = productCode.trim();
    if (!normalizedCode || seenCodes.has(normalizedCode)) {
      return;
    }
    seenCodes.add(normalizedCode);
    rows.push({
      description: description.trim(),
      isActive: true,
      productCode: normalizedCode,
      specification: specification.trim(),
      standardPrice: normalizeProductPriceInput(price) || '0',
      unit: unit.trim() || 'EA',
    });
  });
  return rows;
};

const parseProductDeleteCodes = (text: string): string[] => {
  const codes: string[] = [];
  text.split(/\r?\n/).forEach((line) => {
    const [firstCell] = line.split(/\t|,|\s{2,}/).map((cell) => cell.trim());
    if (!firstCell || isProductPasteHeader([firstCell]) || codes.includes(firstCell)) {
      return;
    }
    codes.push(firstCell);
  });
  return codes;
};

const mergeProductOptions = (current: ProductOption[], incoming: ProductOption[]) => {
  const optionsById = new Map<number, ProductOption>();
  current.forEach((option) => optionsById.set(option.id, option));
  incoming.forEach((option) => optionsById.set(option.id, option));
  return Array.from(optionsById.values()).sort((a, b) => a.productCode.localeCompare(b.productCode));
};

const makeEmptyCustomerCreateForm = (): CustomerCreateFormState => ({
  address: '',
  companyId: '',
  customerName: '',
  departmentId: '',
  email: '',
  manager: '',
  notes: '',
  phoneNumber: '',
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
  status: customer?.status || 'active',
});

const makeAccountInfoForm = (data?: CustomerDetailData | null): AccountInfoFormState => ({
  address: data?.account.address || '',
  companyId: data?.account.companyId ? String(data.account.companyId) : '',
  departmentName: data?.account.departmentName || data?.account.name || '',
  notes: data?.account.notes || '',
});

const makeAccountContactForm = (
  data?: CustomerDetailData | null,
  contact?: CustomerAccountContact | null,
): AccountContactFormState => {
  const management = data?.account.management;
  return {
    address: contact?.address || '',
    contactRole: contact?.contactRole || management?.contactRoles[0]?.value || 'practitioner',
    customerName: contact?.name || '',
    departmentId: String(data?.account.departmentId || ''),
    email: contact?.email || '',
    isActive: contact?.isActive ?? true,
    manager: contact?.manager || '',
    notes: contact?.notesFull || contact?.notes || '',
    phoneNumber: contact?.phone || '',
    pipelineStage: contact?.pipelineStage || management?.stages[0]?.value || 'potential',
    status: contact?.status || management?.statuses[0]?.value || 'active',
  };
};

const accountInfoFormToPayload = (form: AccountInfoFormState): { payload: AccountInfoUpdatePayload | null; error: string } => {
  const companyId = Number(form.companyId);
  if (!companyId) {
    return { payload: null, error: '업체/학교를 선택하세요.' };
  }
  if (!form.departmentName.trim()) {
    return { payload: null, error: '부서/연구실명을 입력하세요.' };
  }
  return {
    payload: {
      address: form.address.trim() || undefined,
      companyId,
      departmentName: form.departmentName.trim(),
      notes: form.notes.trim() || undefined,
    },
    error: '',
  };
};

const accountContactFormToPayload = (form: AccountContactFormState): { payload: AccountContactPayload | null; error: string } => {
  const departmentId = Number(form.departmentId);
  if (!departmentId) {
    return { payload: null, error: '부서/연구실을 선택하세요.' };
  }
  if (!form.customerName.trim()) {
    return { payload: null, error: '담당자명을 입력하세요.' };
  }
  return {
    payload: {
      address: form.address.trim() || undefined,
      contactRole: form.contactRole || 'practitioner',
      customerName: form.customerName.trim(),
      departmentId,
      email: form.email.trim() || undefined,
      isActive: form.isActive,
      manager: form.manager.trim() || undefined,
      notes: form.notes.trim() || undefined,
      phoneNumber: form.phoneNumber.trim() || undefined,
      pipelineStage: form.pipelineStage || 'potential',
      status: form.status || 'active',
    },
    error: '',
  };
};

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
    summary: '영업 현황과 이번 주 접촉을 한 화면에서 확인합니다.',
    primaryHref: '/dashboard/',
    primaryLabel: '프론트 대시보드 보기',
    actions: [
      { label: '영업노트 작성', href: '/notes/?create=1', primary: true },
      { label: '미검토 노트', href: '/notes/?review=unreviewed' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  customers: {
    eyebrow: 'Sales CRM / Customers',
    title: '고객',
    summary: '고객, 업체, 부서, 팔로우업을 하나의 고객 업무 흐름으로 묶습니다.',
    primaryHref: '/customers/',
    primaryLabel: '프론트 고객 보기',
    actions: [
      { label: '파이프라인', href: '/pipeline/', primary: true },
    ],
  },
  companies: {
    eyebrow: 'Sales CRM / Companies',
    title: '업체/부서',
    summary: '업체와 부서/연구실 계정을 React에서 검색, 생성, 수정, 삭제 검토합니다.',
    primaryHref: '/companies/',
    primaryLabel: '업체/부서 관리 열기',
    actions: [
      { label: '업체/부서 관리', href: '/companies/', primary: true },
      { label: '고객 목록', href: '/customers/' },
    ],
  },
  demos: {
    eyebrow: 'Sales CRM / Demos',
    title: '데모관리',
    summary: '고객/계정별 데모 제품, 상태, 반납 예정일을 한 화면에서 관리합니다.',
    primaryHref: '/demos/?create=1',
    primaryLabel: '데모 등록',
    actions: [
      { label: '데모 등록', href: '/demos/?create=1', primary: true },
      { label: '고객 목록', href: '/customers/' },
      { label: '제품관리', href: '/products/' },
    ],
  },
  pipeline: {
    eyebrow: 'Sales CRM / Pipeline',
    title: '파이프라인 관리',
    summary: '견적, 협상, 수주 가능성을 중심으로 이번 주 우선 영업 건을 관리합니다.',
    primaryHref: '/pipeline/',
    primaryLabel: '파이프라인 보기',
    actions: [
      { label: '고객 목록', href: '/customers/' },
      { label: '영업노트', href: '/notes/' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  pipelineSheet: {
    eyebrow: 'Sales CRM / Pipeline Sheet',
    title: '파이프라인 시트',
    summary: '계정별 주간 활동과 누적 견적 전환을 한 장에서 보고, 다음 주 계획을 세웁니다.',
    primaryHref: '/pipeline-sheet/',
    primaryLabel: '시트 보기',
    actions: [
      { label: '견적 전환', href: '/pipeline-sheet/?tab=quotes' },
      { label: '파이프라인', href: '/pipeline/' },
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
    ],
  },
  schedules: {
    eyebrow: 'Sales CRM / Schedule',
    title: '일정',
    summary: '미팅, 견적, 납품 일정을 캘린더 중심으로 관리합니다.',
    primaryHref: scheduleCalendarUrl,
    primaryLabel: '일정 캘린더 열기',
    actions: [
      { label: '일정 캘린더', href: scheduleCalendarUrl, primary: true },
      { label: '새 일정 등록', href: '/schedules/?create=1' },
    ],
  },
  employees: {
    eyebrow: 'Sales CRM / Employees',
    title: '사용자/직원관리',
    summary: 'Admin은 전체 사용자, Manager는 같은 회사 직원을 React CRM에서 관리합니다.',
    primaryHref: '/employees/',
    primaryLabel: '사용자/직원관리 열기',
    actions: [
      { label: '사용자/직원관리', href: '/employees/', primary: true },
    ],
  },
  documents: {
    eyebrow: 'Sales CRM / Documents',
    title: '서류',
    summary: '견적서, 거래명세서, 납품서 템플릿을 관리하고 일정 서류 생성 흐름과 연결합니다.',
    primaryHref: '/documents/',
    primaryLabel: '서류 템플릿 관리',
    actions: [
      { label: '서류 등록', href: '/documents/?create=1', primary: true },
      { label: '일정', href: '/schedules/' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  products: {
    eyebrow: 'Sales CRM / Products',
    title: '제품',
    summary: '제품 기준단가, 규격, 단위, Ecount 반영 데이터를 React CRM에서 관리합니다.',
    primaryHref: '/products/',
    primaryLabel: '제품관리 열기',
    actions: [
      { label: '제품 등록', href: '/products/?create=1', primary: true },
      { label: '엑셀 다운로드', href: '/reporting/api/products/export.xlsx' },
      { label: '일정', href: '/schedules/' },
    ],
  },
  receivables: {
    eyebrow: 'Sales CRM / Receivables',
    title: '외상고객',
    summary: '납품 품목별 외상, 카드결제, 수금완료 상태를 한 곳에서 처리합니다.',
    primaryHref: '/receivables/',
    primaryLabel: '외상고객 열기',
    actions: [
      { label: '외상고객', href: '/receivables/', primary: true },
      { label: '납품 일정', href: '/schedules/' },
      { label: '고객 목록', href: '/customers/' },
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
      { label: '고객 목록', href: '/customers/' },
      { label: '일정', href: '/schedules/' },
    ],
  },
  profile: {
    eyebrow: 'Sales CRM / Profile',
    title: '프로필',
    summary: '내 계정과 권한을 확인합니다.',
    primaryHref: '/profile/',
    primaryLabel: '프로필 열기',
    actions: [
      { label: '프로필 보기', href: '/profile/', primary: true },
    ],
  },
  notFound: {
    eyebrow: 'Sales CRM',
    title: '페이지를 찾을 수 없습니다',
    summary: '요청한 화면은 현재 CRM 메뉴에서 제공하지 않습니다.',
    primaryHref: '/dashboard/',
    primaryLabel: '대시보드로 이동',
    actions: [
      { label: '대시보드', href: '/dashboard/', primary: true },
      { label: '고객', href: '/customers/' },
    ],
  },
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

function getCreateDateParam(): string {
  const value = new URLSearchParams(window.location.search).get('date') || '';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return '';
  }
  return localDateInputValue(parseLocalDate(value)) === value ? value : '';
}

function getCreateTimeParam(): string {
  const value = new URLSearchParams(window.location.search).get('time') || '';
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value) ? value : '';
}

function appendDateQuery(href: string, dateValue: string): string {
  if (!dateValue) {
    return href;
  }
  const separator = href.includes('?') ? '&' : '?';
  return `${href}${separator}date=${encodeURIComponent(dateValue)}`;
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

const formatSignedNumber = (value: number) => `${value > 0 ? '+' : ''}${formatNumber(value)}`;

const formatFileSize = (size: number) => {
  if (size >= 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (size >= 1024) {
    return `${Math.round(size / 1024)} KB`;
  }
  return `${size} B`;
};

const formatDateLabel = (value?: string | null) => {
  if (!value) return '';
  const datePart = /^\d{4}-\d{2}-\d{2}/.test(value) ? value.slice(0, 10) : value;
  const [year, month, day] = datePart.split('-');
  if (!year || !month || !day) return value;
  return `${Number(month)}월 ${Number(day)}일`;
};

const noteNextActionLabel = (note: Pick<NoteItem, 'nextAction' | 'nextActionDate'> & { nextActionDisplay?: string }) => (
  note.nextActionDisplay || note.nextAction || (note.nextActionDate ? '후속 예정' : '')
);

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

const formatDateTimeLocalInputValue = (date: Date) => {
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const sortScheduleItems = (items: DashboardScheduleItem[]) =>
  [...items].sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

const riskLabel: Record<Deal['risk'], string> = {
  low: '정상',
  medium: '확인',
  high: '지연',
};

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

const searchableOptionLimit = 80;

const joinOptionParts = (parts: Array<string | undefined>) => parts.filter(Boolean).join(' · ');

const koreanAdministrativeAliasPairs: Array<[string, string]> = [
  ['서울특별시', '서울시'],
  ['부산광역시', '부산시'],
  ['대구광역시', '대구시'],
  ['인천광역시', '인천시'],
  ['광주광역시', '광주시'],
  ['대전광역시', '대전시'],
  ['울산광역시', '울산시'],
  ['세종특별자치시', '세종시'],
  ['제주특별자치도', '제주도'],
];

function normalizeOptionText(value: string): string {
  return value.trim().toLocaleLowerCase('ko-KR').replace(/\s+/g, '');
}

function searchableTextVariants(value: string): string[] {
  const normalized = normalizeOptionText(value);
  const variants = new Set([normalized]);
  koreanAdministrativeAliasPairs.forEach(([formal, short]) => {
    const formalText = normalizeOptionText(formal);
    const shortText = normalizeOptionText(short);
    if (normalized.includes(formalText)) {
      variants.add(normalized.split(formalText).join(shortText));
    }
    if (normalized.includes(shortText)) {
      variants.add(normalized.split(shortText).join(formalText));
    }
  });
  return Array.from(variants).filter(Boolean);
}

function makeCompanySelectOption(company: { id: number; name: string }): SearchableSelectOption {
  return {
    value: String(company.id),
    label: company.name,
    searchText: company.name,
  };
}

function makeDepartmentSelectOption(department: { id: number; name: string; companyName?: string; searchText?: string }): SearchableSelectOption {
  const label = joinOptionParts([department.companyName, department.name]) || department.name;
  return {
    value: String(department.id),
    label,
    searchText: [label, department.searchText || ''].filter(Boolean).join(' '),
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

function customerDepartmentValue(customer: CustomerSelectSource): string {
  return customer.departmentId ? String(customer.departmentId) : '';
}

function customersForDepartment<T extends CustomerSelectSource>(customers: T[], departmentId: string): T[] {
  if (!departmentId) {
    return customers;
  }
  return customers.filter((customer) => customerDepartmentValue(customer) === departmentId);
}

function makeDemoAccountSelectOption(account: DemoAccountOption): SearchableSelectOption {
  const contactNames = account.contacts.map((contact) => contact.name).filter(Boolean).slice(0, 4).join(', ');
  return {
    value: String(account.departmentId),
    label: account.label || joinOptionParts([account.companyName, account.departmentName]),
    meta: joinOptionParts([`${account.contactCount}명`, contactNames]),
    searchText: [account.searchText, account.companyName, account.departmentName, contactNames].filter(Boolean).join(' '),
  };
}

function makeProductSelectOption(product: ProductOption): SearchableSelectOption {
  const meta = joinOptionParts([product.specification, product.unit, product.description]);
  return {
    value: String(product.id),
    label: product.productCode || product.name || `제품 #${product.id}`,
    meta,
    searchText: [product.productCode, product.name, product.specification, product.description].filter(Boolean).join(' '),
  };
}

function SearchableSelect({
  allowEmpty = false,
  ariaLabel,
  className = '',
  disabled = false,
  emptyLabel = '선택 없음',
  onChange,
  onSearchChange,
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
  onSearchChange?: (query: string) => void;
  options: SearchableSelectOption[];
  placeholder?: string;
  value: string;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const selectedOption = options.find((option) => option.value === value);
  useEffect(() => {
    onSearchChange?.(query);
  }, [onSearchChange, query]);
  const allOptions = useMemo(
    () => (allowEmpty ? [{ value: '', label: emptyLabel, searchText: emptyLabel }, ...options] : options),
    [allowEmpty, emptyLabel, options],
  );
  const filteredOptions = useMemo(() => {
    const normalizedQuery = normalizeOptionText(query);
    const queryVariants = searchableTextVariants(query);
    const matches = normalizedQuery
      ? allOptions.filter((option) => {
        const optionVariants = searchableTextVariants(`${option.label} ${option.meta || ''} ${option.searchText || ''}`);
        return queryVariants.some((queryVariant) => (
          optionVariants.some((optionVariant) => optionVariant.includes(queryVariant))
        ));
      })
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

function WorkspaceRoutePage({
  actions,
  data,
  view,
}: {
  actions?: typeof routeMeta[MainView]['actions'];
  data: PipelineData;
  view: MainView;
}) {
  const meta = routeMeta[view];
  const routeActions = actions ?? meta.actions;
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
            {routeActions.map((action) => (
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
              <a href={deal.detailUrl || `/customers/${deal.id}/`} key={deal.id}>
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

function LazyPageBoundary({ children }: { children: ReactNode }) {
  return (
    <Suspense
      fallback={(
        <section className="dashboard-loading">
          <Loader2 className="spin-icon" size={24} />
          <span>화면 모듈을 불러오는 중입니다</span>
        </section>
      )}
    >
      {children}
    </Suspense>
  );
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
          </article>
        ))}
      </div>
    </section>
  );
}

function CustomerStatusBadge({ customer }: { customer: CustomerItem }) {
  return (
    <div className="customer-badge-row">
      <span>{customer.pipelineLabel}</span>
      {customer.grade ? <span>{customer.grade}</span> : null}
    </div>
  );
}

function CustomersTable({ customers, emptyLabel = '조건에 맞는 계정이 없습니다' }: { customers: CustomerItem[]; emptyLabel?: string }) {
  if (customers.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="customers-table-wrap">
      <table className="customers-table">
        <thead>
          <tr>
            <th>계정</th>
            <th>상태</th>
            <th>후속</th>
            <th>예정 일정</th>
            <th>활동</th>
            <th>영업/담당자</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={`${customer.accountType || 'customer'}-${customer.id}`}>
              <td>
                <a className="customer-name-link" href={customer.href}>
                  <strong>{customer.company || customer.customer}</strong>
                  <span>{[
                    customer.department || customer.customer,
                    customer.contactCount ? `담당자 ${formatNumber(customer.contactCount)}명` : '',
                  ].filter(Boolean).join(' · ')}</span>
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
            <small>{noteNextActionLabel(note) || note.summary || '내용 없음'}</small>
            {note.fileCount || note.replyCount ? (
              <small className="customer-note-submeta">
                {[note.fileCount ? `첨부 ${formatNumber(note.fileCount)}` : '', note.replyCount ? `댓글 ${formatNumber(note.replyCount)}` : ''].filter(Boolean).join(' · ')}
              </small>
            ) : null}
          </div>
          <time>{note.nextActionDate ? formatDateLabel(note.nextActionDate) : formatDateTimeLabel(note.createdAt)}</time>
        </a>
      ))}
    </div>
  );
}

function CustomerAttachmentList({ files }: { files: CustomerAttachmentItem[] }) {
  return (
    <AttachmentManager
      className="customer-attachment-manager"
      emptyLabel="첨부된 파일이 없습니다"
      files={files}
      title="첨부파일"
    />
  );
}

function CustomerRecordItems({ items }: { items: ScheduleDeliveryItem[] }) {
  if (!items.length) {
    return <span className="customer-record-empty-line">품목 정보 없음</span>;
  }

  const visibleItems = items.slice(0, 3);
  const hiddenCount = Math.max(items.length - visibleItems.length, 0);

  return (
    <div className="customer-record-item-list">
      {visibleItems.map((item) => (
        <span key={`${item.id}-${item.itemName}`}>
          <strong>{item.itemName}</strong>
          <small>
            {formatNumber(item.quantity)}{item.unit || 'EA'}
            {item.totalPrice ? ` · ${formatWon(item.totalPrice)}` : ''}
          </small>
        </span>
      ))}
      {hiddenCount > 0 ? <span className="customer-record-more">외 {formatNumber(hiddenCount)}개</span> : null}
    </div>
  );
}

function CustomerDeliveryRecords({ records }: { records: CustomerDeliveryRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="납품 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list delivery-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row" key={record.id}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <span className={`customer-delivery-source ${record.paymentSource}`}>
                {record.paymentTypeLabel || record.paymentSourceLabel || '일반 납품'}
              </span>
              {record.paymentStatusLabel && record.paymentStatusLabel !== (record.paymentTypeLabel || record.paymentSourceLabel) ? (
                <span className={`customer-delivery-status ${record.paymentStatus}`}>
                  {record.paymentStatusLabel}
                </span>
              ) : null}
              <strong>{record.date ? formatDateLabel(record.date) : '납품일 없음'}</strong>
              <span>{record.statusLabel}</span>
            </div>
            <CustomerRecordItems items={record.items ?? []} />
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `영업 ${record.ownerName}` : ''].filter(Boolean).join(' · ')}
            </small>
            {record.notes ? <p>{record.notes}</p> : null}
            <small>{record.paymentEvidence}</small>
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.totalAmount || 0)}</strong>
            {record.paymentSource === 'prepayment' ? (
              <span>차감 {formatWon(record.prepaymentAmount || 0)}</span>
            ) : (
              <span>선결제 차감 없음</span>
            )}
            {record.href ? <a href={record.href}>일정</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerQuoteRecords({ records }: { records: CustomerQuoteRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="견적 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row" key={`${record.recordType}-${record.id}`}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.quoteNumber || '견적 일정'}</strong>
              <span>{record.date ? formatDateLabel(record.date) : '견적일 없음'}</span>
              <span>{record.statusLabel}</span>
            </div>
            <CustomerRecordItems items={record.items ?? []} />
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `영업 ${record.ownerName}` : ''].filter(Boolean).join(' · ')}
            </small>
            {record.notes ? <p>{record.notes}</p> : null}
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.totalAmount || 0)}</strong>
            {record.validUntil ? <span>유효 {formatDateLabel(record.validUntil)}</span> : null}
            {record.href ? <a href={record.href}>일정</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerServiceRecords({ records }: { records: CustomerServiceRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="서비스 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row compact" key={`${record.recordType}-${record.id}`}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.assetName || record.caseTypeLabel || '서비스 기록'}</strong>
              <span>{record.date ? formatDateLabel(record.date) : '일자 없음'}</span>
              <span>{record.statusLabel}</span>
            </div>
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `접수 ${record.ownerName}` : '', record.assignedTo ? `배정 ${record.assignedTo}` : ''].filter(Boolean).join(' · ')}
            </small>
            <p>{record.summary || record.detail || '상세 내용 없음'}</p>
            <small>{[record.caseTypeLabel, record.priorityLabel, record.assignedTo || record.ownerName].filter(Boolean).join(' · ')}</small>
          </div>
          <div className="customer-record-side">
            {record.dueDate ? <span>처리기한 {formatDateLabel(record.dueDate)}</span> : null}
            {record.completedDate ? <span>완료 {formatDateLabel(record.completedDate)}</span> : null}
            {record.href ? <a href={record.href}>열기</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerPrepaymentRecords({ records }: { records: PrepaymentListItem[] }) {
  if (!records.length) {
    return <DashboardEmpty label="선결제 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list prepayment-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row compact" key={record.id}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.paymentDate ? formatDateLabel(record.paymentDate) : '입금일 없음'}</strong>
              <span>{record.payerName || '입금자 미지정'}</span>
              <PrepaymentStatusBadge label={record.statusLabel} status={record.status} />
            </div>
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `등록 ${record.ownerName}` : '', record.departmentName].filter(Boolean).join(' · ')}
            </small>
            {record.memo ? <p>{record.memo}</p> : null}
            <small>사용 {formatWon(record.usedAmount || 0)} · 사용내역 {formatNumber(record.usageCount || 0)}건</small>
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.amount || 0)}</strong>
            <span>잔액 {formatWon(record.balance || 0)}</span>
            <a href={`/prepayments/${record.id}/`}>상세</a>
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerDetailPage({
  data,
  detailMode = 'customer',
  loading,
  onRefresh,
}: {
  data: CustomerDetailData | null;
  detailMode?: CustomerDetailMode;
  loading: boolean;
  onRefresh: () => Promise<CustomerDetailData | null>;
}) {
  const customer = data?.customer ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<CustomerEditFormState>(() => makeCustomerEditForm(customer));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [deleteSaving, setDeleteSaving] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [deleteMessage, setDeleteMessage] = useState('');
  const [accountInfoOpen, setAccountInfoOpen] = useState(false);
  const [accountInfoForm, setAccountInfoForm] = useState<AccountInfoFormState>(() => makeAccountInfoForm(data));
  const [accountInfoSaving, setAccountInfoSaving] = useState(false);
  const [accountInfoError, setAccountInfoError] = useState('');
  const [accountInfoMessage, setAccountInfoMessage] = useState('');
  const [accountContactEditor, setAccountContactEditor] = useState<AccountContactEditorMode>('');
  const [accountContactForm, setAccountContactForm] = useState<AccountContactFormState>(() => makeAccountContactForm(data));
  const [editingAccountContactId, setEditingAccountContactId] = useState<number | null>(null);
  const [accountContactSaving, setAccountContactSaving] = useState(false);
  const [accountContactError, setAccountContactError] = useState('');
  const [accountContactMessage, setAccountContactMessage] = useState('');
  const accountInfoPanelRef = useRef<HTMLFormElement | null>(null);
  const accountContactPanelRef = useRef<HTMLFormElement | null>(null);
  const customerEditPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(accountInfoOpen, accountInfoPanelRef, `account-info-${data?.account.id || customer?.id || 'new'}`);
  useGuidedPanelFocus(
    Boolean(accountContactEditor),
    accountContactPanelRef,
    `${accountContactEditor || 'closed'}-${editingAccountContactId || 'new'}`,
  );
  useGuidedPanelFocus(editOpen, customerEditPanelRef, `customer-edit-${customer?.id || 'new'}`);

  useEffect(() => {
    setEditForm(makeCustomerEditForm(customer));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setDeleteSaving(false);
    setDeleteError('');
    setDeleteMessage('');
    setAccountInfoOpen(false);
    setAccountInfoForm(makeAccountInfoForm(data));
    setAccountInfoSaving(false);
    setAccountInfoError('');
    setAccountInfoMessage('');
    setAccountContactEditor('');
    setAccountContactForm(makeAccountContactForm(data));
    setEditingAccountContactId(null);
    setAccountContactSaving(false);
    setAccountContactError('');
    setAccountContactMessage('');
  }, [customer?.id, data?.account.id]);

  const editConfig = data?.edit;
  const editCompanies = editConfig?.companies ?? [];
  const editDepartments = editForm.companyId
    ? (editConfig?.departments ?? []).filter((department) => String(department.companyId) === editForm.companyId)
    : editConfig?.departments ?? [];
  const accountManagement = data?.account.management;
  const accountInfoCompanies = accountManagement?.companies ?? [];
  const accountInfoDepartments = accountInfoForm.companyId
    ? (accountManagement?.departments ?? []).filter((department) => String(department.companyId) === accountInfoForm.companyId)
    : accountManagement?.departments ?? [];
  const contactTargetDepartments = accountManagement?.departments ?? [];

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

  const handleCustomerDelete = async () => {
    if (!customer || !editConfig || deleteSaving) {
      return;
    }
    if (!editConfig.canDelete || !editConfig.deleteUrl) {
      setDeleteError(editConfig.message || '삭제 권한이 없습니다.');
      setDeleteMessage('');
      return;
    }
    const label = customer.customer || '고객';
    if (!window.confirm(`"${label}" 고객 정보를 삭제할까요?\n연결된 일정, 영업노트, 파일 기록도 함께 삭제될 수 있습니다.`)) {
      return;
    }

    setDeleteSaving(true);
    setDeleteError('');
    setDeleteMessage('');
    try {
      const result = await deleteCustomerRecord(editConfig.deleteUrl);
      setDeleteMessage(result.message || '고객 정보를 삭제했습니다.');
      window.location.href = result.href || data?.links.customers || '/customers/';
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '고객 삭제에 실패했습니다.');
    } finally {
      setDeleteSaving(false);
    }
  };

  const handleAccountInfoFieldChange = (field: keyof AccountInfoFormState, value: string) => {
    setAccountInfoForm((previous) => {
      return {
        ...previous,
        [field]: value,
      };
    });
    setAccountInfoError('');
    setAccountInfoMessage('');
  };

  const handleAccountInfoSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accountManagement?.canManage || accountInfoSaving) {
      setAccountInfoError(accountManagement?.message || '계정 관리 권한이 없습니다.');
      return;
    }
    if (!accountManagement.accountSubmitUrl) {
      setAccountInfoError('계정 저장 API가 준비되지 않았습니다.');
      return;
    }
    const { payload, error } = accountInfoFormToPayload(accountInfoForm);
    if (!payload || error) {
      setAccountInfoError(error || '계정 정보를 확인하세요.');
      return;
    }

    setAccountInfoSaving(true);
    setAccountInfoError('');
    setAccountInfoMessage('');
    try {
      const result = await updateAccountInfo(payload, accountManagement.accountSubmitUrl);
      await onRefresh();
      setAccountInfoMessage(result.message || '계정 정보를 저장했습니다.');
      setAccountInfoOpen(false);
    } catch (error) {
      setAccountInfoError(error instanceof Error ? error.message : '계정 정보 저장에 실패했습니다.');
    } finally {
      setAccountInfoSaving(false);
    }
  };

  const resetAccountContactFeedback = () => {
    setAccountContactError('');
    setAccountContactMessage('');
  };

  const handleAccountContactFieldChange = (field: keyof AccountContactFormState, value: string | boolean) => {
    setAccountContactForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    resetAccountContactFeedback();
  };

  const openAccountContactCreate = () => {
    setEditingAccountContactId(null);
    setAccountContactForm(makeAccountContactForm(data));
    setAccountContactEditor('create');
    resetAccountContactFeedback();
  };

  const openAccountContactEdit = (contact: CustomerAccountContact) => {
    if (!contact.canManage) {
      setAccountContactError(contact.manageMessage || '이 담당자 수정 권한이 없습니다.');
      setAccountContactMessage('');
      return;
    }
    setEditingAccountContactId(contact.id);
    setAccountContactForm(makeAccountContactForm(data, contact));
    setAccountContactEditor('edit');
    resetAccountContactFeedback();
  };

  const handleAccountContactSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accountManagement?.canManage || accountContactSaving) {
      setAccountContactError(accountManagement?.message || '담당자 관리 권한이 없습니다.');
      return;
    }
    const editingContact = data?.account.contacts.find((contact) => contact.id === editingAccountContactId) ?? null;
    const submitUrl = editingContact ? editingContact.updateUrl : accountManagement.contactCreateUrl;
    if (!submitUrl) {
      setAccountContactError('담당자 저장 API가 준비되지 않았습니다.');
      return;
    }
    const { payload, error } = accountContactFormToPayload(accountContactForm);
    if (!payload || error) {
      setAccountContactError(error || '담당자 정보를 확인하세요.');
      return;
    }

    setAccountContactSaving(true);
    resetAccountContactFeedback();
    try {
      const result = await saveAccountContact(payload, submitUrl);
      await onRefresh();
      setAccountContactMessage(result.message || '담당자 정보를 저장했습니다.');
      setAccountContactEditor('');
      setEditingAccountContactId(null);
    } catch (error) {
      setAccountContactError(error instanceof Error ? error.message : '담당자 저장에 실패했습니다.');
    } finally {
      setAccountContactSaving(false);
    }
  };

  const toggleAccountContactActive = async (contact: CustomerAccountContact, isActive: boolean) => {
    if (!contact.canManage || !contact.updateUrl || accountContactSaving) {
      setAccountContactError(contact.manageMessage || '이 담당자 수정 권한이 없습니다.');
      setAccountContactMessage('');
      return;
    }
    const payload = accountContactFormToPayload({
      ...makeAccountContactForm(data, contact),
      isActive,
    }).payload;
    if (!payload) {
      setAccountContactError('담당자 정보를 확인하세요.');
      setAccountContactMessage('');
      return;
    }
    setAccountContactSaving(true);
    resetAccountContactFeedback();
    try {
      const result = await saveAccountContact(payload, contact.updateUrl);
      await onRefresh();
      setAccountContactMessage(result.message || (isActive ? '담당자를 활성화했습니다.' : '담당자를 비활성화했습니다.'));
    } catch (error) {
      setAccountContactError(error instanceof Error ? error.message : '담당자 상태 변경에 실패했습니다.');
    } finally {
      setAccountContactSaving(false);
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
  const prepaymentSummary = data.prepaymentSummary;
  const operationalRecords = data.operationalRecords;
  const demoSummary = data.demoSummary;
  const attachments = data.attachments;
  const account = data.account;
  const isAccountDetail = detailMode === 'account';
  const canCreateNote = data.permissions.canCreateNote && Boolean(data.links.createNote);
  const canCreateSchedule = data.permissions.canCreateSchedule && Boolean(data.links.createSchedule);
  const canEditRepresentative = data.permissions.canEditRepresentative && data.edit.canEdit && !isAccountDetail;
  const canDeleteRepresentative = data.permissions.canDeleteRepresentative && data.edit.canDelete && !isAccountDetail;
  const accountContacts = account.contacts ?? [];
  const ledgerScopeLabel = account.ledgerScopeLabel || (
    account.type === 'department' ? '부서/연구실 계정 공유 원장' : '담당자 단일 원장'
  );
  const ledgerScopeDescription = account.ledgerScopeDescription || (
    account.type === 'department'
      ? '같은 업체/부서/연구실 담당자의 납품, 견적, 선결제, 서비스 기록을 함께 집계합니다.'
      : '부서/연구실 연결이 없어 이 담당자에게 연결된 기록만 집계합니다.'
  );
  const prepaymentScopeHref = prepaymentSummary.links.accountPrepayments
    || prepaymentSummary.links.customerPrepayments
    || prepaymentSummary.links.djangoCustomerPrepayments;
  const prepaymentScopeLabel = account.type === 'department' ? '계정 선결제' : '고객별 선결제';
  const accountContactPreview = accountContacts
    .map((contact) => contact.name)
    .filter(Boolean)
    .slice(0, 4)
    .join(', ');
  const accountAddress = account.address || customerDetail.address || '';
  const accountNotes = account.notes || customerDetail.notesFull || customerDetail.notes || '';
  const metrics = [
    { label: '최근 노트', value: `${formatNumber(data.metrics.recentNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '예정 일정', value: `${formatNumber(data.metrics.upcomingSchedules)}건`, detail: '진행 예정', icon: CalendarDays, tone: 'green' as const },
    { label: '14일 내 후속', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '예정 액션', icon: Clock, tone: 'teal' as const },
  ];
  const demoMetrics = [
    { label: '전체 데모', value: `${formatNumber(demoSummary.metrics.total)}건` },
    { label: '진행중', value: `${formatNumber(demoSummary.metrics.active)}건` },
    { label: '반납 지연', value: `${formatNumber(demoSummary.metrics.overdue)}건` },
    { label: '구매전환', value: `${formatNumber(demoSummary.metrics.converted)}건` },
  ];
  const operationalMetrics = [
    { label: '납품', value: `${formatNumber(operationalRecords.metrics.deliveryRecords)}건` },
    { label: '선결제 차감 납품', value: `${formatNumber(operationalRecords.metrics.prepaymentDeliveryRecords)}건` },
    { label: '일반 납품', value: `${formatNumber(operationalRecords.metrics.normalDeliveryRecords)}건` },
    { label: '견적', value: `${formatNumber(operationalRecords.metrics.quoteRecords)}건` },
    { label: '선결제 기록', value: `${formatNumber(operationalRecords.metrics.prepaymentRecords)}건` },
    { label: '서비스', value: `${formatNumber(operationalRecords.metrics.serviceRecords)}건` },
  ];
  const ledgerCards = [
    {
      label: '원장 범위',
      value: ledgerScopeLabel,
      detail: ledgerScopeDescription,
    },
    {
      label: '공유 담당자',
      value: `${formatNumber(account.contactCount || accountContacts.length)}명`,
      detail: accountContactPreview || '담당자 없음',
    },
    {
      label: '납품 구분',
      value: `선결제 ${formatNumber(operationalRecords.metrics.prepaymentDeliveryRecords)}건 / 일반 ${formatNumber(operationalRecords.metrics.normalDeliveryRecords)}건`,
      detail: '구조화 선결제 사용 기록 기준',
    },
  ];
  const customerProfileFields = [
    { label: '업체/학교', value: account.companyName || customerDetail.company },
    { label: '부서/연구실', value: account.departmentName || customerDetail.department },
    { label: 'PI', value: account.piContactName || '-' },
    { label: '대표 담당자', value: account.representativeName || customerDetail.customer },
    { label: '계정 담당자 수', value: account.contactCount ? `${formatNumber(account.contactCount)}명` : '' },
    { label: '활성/비활성', value: `${formatNumber(account.activeContactCount || account.contactCount)}명 / ${formatNumber(account.inactiveContactCount)}명` },
    { label: '영업 담당자', value: customerDetail.owner },
    { label: '책임자', value: customerDetail.manager },
    { label: '전화번호', value: customerDetail.phone },
    { label: '이메일', value: customerDetail.email },
    { label: '파이프라인', value: customerDetail.pipelineLabel },
  ];
  const customerDetailNotes = accountNotes;

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
          <span className="eyebrow">Department account</span>
          <h2>{[account.companyName || customerDetail.company, account.departmentName || customerDetail.department].filter(Boolean).join(' · ') || account.name || customerDetail.customer}</h2>
          <p>{[account.representativeName || customerDetail.customer, account.contactCount ? `담당자 ${formatNumber(account.contactCount)}명` : '', data.scope.label].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/customers/">{isAccountDetail ? '계정 목록' : '목록'}</a>
          {!isAccountDetail && data.links.accountDetail ? (
            <a className="route-secondary-action" href={data.links.accountDetail}>계정 링크</a>
          ) : null}
          {data.links.pipeline ? (
            <a className="route-secondary-action" href={data.links.pipeline}>
              <Target size={15} />
              파이프라인
            </a>
          ) : null}
          {accountManagement?.canManage ? (
            <>
              <button className="route-secondary-action" onClick={() => setAccountInfoOpen((open) => !open)} type="button">
                <Pencil size={15} />
                계정 관리
              </button>
              <button className="route-secondary-action" onClick={openAccountContactCreate} type="button">
                <Plus size={15} />
                담당자 추가
              </button>
            </>
          ) : null}
          {canEditRepresentative ? (
            <button className="route-secondary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              담당자 수정
            </button>
          ) : null}
          {canDeleteRepresentative && data.edit.deleteUrl ? (
            <button className="route-secondary-action danger" disabled={deleteSaving} onClick={handleCustomerDelete} type="button">
              {deleteSaving ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
              담당자 삭제
            </button>
          ) : null}
          {canCreateNote ? (
            <a className="route-secondary-action" href={data.links.createNote}>
              노트 작성
              <FileText size={16} />
            </a>
          ) : null}
          {canCreateSchedule ? (
            <a className="route-primary-action" href={data.links.createSchedule}>
              일정 등록
              <Plus size={16} />
            </a>
          ) : null}
        </div>
      </div>

      {isAccountDetail && data.permissions.readOnlyMessage && !accountManagement?.canManage ? (
        <div className="dashboard-api-alert compact">
          <ShieldCheck size={16} />
          <span>{data.permissions.readOnlyMessage}</span>
        </div>
      ) : null}

      {deleteError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{deleteError}</span>
        </div>
      ) : null}
      {deleteMessage ? (
        <div className="dashboard-api-alert compact success">
          <CheckCircle2 size={16} />
          <span>{deleteMessage}</span>
        </div>
      ) : null}

      <div className="customer-account-ledger-strip">
        {ledgerCards.map((item) => (
          <div key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <small>{item.detail}</small>
          </div>
        ))}
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

      <section className="dashboard-panel customer-profile-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Customer profile</span>
            <h2>부서/연구실 계정 정보</h2>
          </div>
          <Building2 size={18} />
        </div>
        <dl className="customer-profile-grid">
          {customerProfileFields.map((field) => (
            <div key={field.label}>
              <dt>{field.label}</dt>
              <dd>{field.value || '-'}</dd>
            </div>
          ))}
        </dl>
        <div className="customer-profile-text-grid">
          <article className={`customer-profile-text ${accountAddress ? '' : 'empty'}`}>
            <span>계정 주소</span>
            <p>{accountAddress || '등록된 주소 없음'}</p>
          </article>
          <article className={`customer-profile-text ${customerDetailNotes ? '' : 'empty'}`}>
            <span>계정 메모</span>
            <p>{customerDetailNotes || '등록된 상세 내용 없음'}</p>
          </article>
        </div>
        {accountManagement && !accountManagement.canManage && accountManagement.message ? (
          <div className="dashboard-api-alert compact">
            <AlertTriangle size={16} />
            <span>{accountManagement.message}</span>
          </div>
        ) : null}
        {accountInfoOpen || accountInfoError || accountInfoMessage ? (
          <form className="notes-create-form account-info-form" onSubmit={handleAccountInfoSubmit} ref={accountInfoPanelRef}>
            {accountInfoError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{accountInfoError}</span></div> : null}
            {accountInfoMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{accountInfoMessage}</span></div> : null}
            {accountInfoOpen ? (
              <>
                <div className="notes-create-grid">
                  <div className="form-field">
                    <span>업체/학교</span>
                    <SearchableSelect
                      ariaLabel="계정 업체/학교 선택"
                      onChange={(nextValue) => handleAccountInfoFieldChange('companyId', nextValue)}
                      options={accountInfoCompanies.map(makeCompanySelectOption)}
                      placeholder="업체/학교 검색"
                      value={accountInfoForm.companyId}
                    />
                  </div>
                  <label>
                    <span>부서/연구실명</span>
                    <input
                      onChange={(event) => handleAccountInfoFieldChange('departmentName', event.target.value)}
                      required
                      value={accountInfoForm.departmentName}
                    />
                  </label>
                  <div className="form-field account-info-reference">
                    <span>같은 업체 부서 참고</span>
                    <SearchableSelect
                      allowEmpty
                      ariaLabel="부서/연구실 참고 선택"
                      disabled={!accountInfoForm.companyId}
                      emptyLabel="직접 입력 유지"
                      onChange={(nextValue) => {
                        const selected = accountInfoDepartments.find((department) => String(department.id) === nextValue);
                        if (selected) {
                          handleAccountInfoFieldChange('departmentName', selected.name);
                        }
                      }}
                      options={accountInfoDepartments.map(makeDepartmentSelectOption)}
                      placeholder={accountInfoForm.companyId ? '기존 부서 검색' : '업체를 먼저 선택'}
                      value=""
                    />
                  </div>
                  <label>
                    <span>계정 주소</span>
                    <input
                      onChange={(event) => handleAccountInfoFieldChange('address', event.target.value)}
                      value={accountInfoForm.address}
                    />
                  </label>
                </div>
                <label>
                  <span>계정 메모</span>
                  <textarea
                    onChange={(event) => handleAccountInfoFieldChange('notes', event.target.value)}
                    rows={3}
                    value={accountInfoForm.notes}
                  />
                </label>
                <div className="notes-create-actions">
                  <button className="route-secondary-action" onClick={() => setAccountInfoOpen(false)} type="button">
                    취소
                  </button>
                  <button className="route-primary-action" disabled={accountInfoSaving} type="submit">
                    {accountInfoSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                    저장
                  </button>
                </div>
              </>
            ) : null}
          </form>
        ) : null}
      </section>

      <section className="dashboard-panel customer-account-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Account contacts</span>
            <h2>계정 담당자</h2>
          </div>
          <div className="customer-account-heading-actions">
            {accountManagement?.canManage ? (
              <button className="route-secondary-action" onClick={openAccountContactCreate} type="button">
                <Plus size={15} />
                담당자 추가
              </button>
            ) : null}
            <Users size={18} />
          </div>
        </div>
        {accountContactError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{accountContactError}</span></div> : null}
        {accountContactMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{accountContactMessage}</span></div> : null}
        {accountContacts.length > 0 ? (
          <div className="customer-account-contact-list">
            {accountContacts.map((contact) => (
              <article className={`customer-account-contact-card ${contact.isActive ? '' : 'inactive'}`} key={contact.id}>
                <div>
                  <div className="customer-account-contact-title">
                    <strong>{contact.name}</strong>
                    <span className="customer-contact-role-badge">{contact.contactRoleLabel || '실무자'}</span>
                    {!contact.isActive ? <span className="customer-contact-role-badge inactive">비활성</span> : null}
                  </div>
                  <span>{[contact.manager, contact.ownerName].filter(Boolean).join(' · ') || '담당자 정보 없음'}</span>
                </div>
                <dl>
                  <div>
                    <dt>연락처</dt>
                    <dd>{contact.contactSummary || '연락처 없음'}</dd>
                  </div>
                  <div>
                    <dt>주소</dt>
                    <dd>{contact.address || '주소 없음'}</dd>
                  </div>
                  <div>
                    <dt>상세</dt>
                    <dd>{contact.notes || '상세 내용 없음'}</dd>
                  </div>
                </dl>
                <div className="customer-account-contact-actions">
                  <a className="customer-row-action" href={contact.href}>
                    상세 <MoveUpRight size={13} />
                  </a>
                  {contact.canManage ? (
                    <>
                      <button className="customer-row-action" onClick={() => openAccountContactEdit(contact)} type="button">
                        수정/이동
                      </button>
                      <button
                        className="customer-row-action"
                        disabled={accountContactSaving}
                        onClick={() => toggleAccountContactActive(contact, !contact.isActive)}
                        type="button"
                      >
                        {contact.isActive ? '비활성화' : '활성화'}
                      </button>
                    </>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label="이 계정에 표시할 담당자가 없습니다" />
        )}
        {accountContactEditor ? (
          <form className="notes-create-form account-contact-form" onSubmit={handleAccountContactSubmit} ref={accountContactPanelRef}>
            <div className="dashboard-panel-heading customer-asset-editor-heading">
              <div>
                <span className="eyebrow">{accountContactEditor === 'create' ? 'New contact' : 'Edit contact'}</span>
                <h3>{accountContactEditor === 'create' ? '담당자 추가' : '담당자 수정/이동'}</h3>
              </div>
            </div>
            <div className="notes-create-grid">
              <label>
                <span>담당자명</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('customerName', event.target.value)}
                  required
                  value={accountContactForm.customerName}
                />
              </label>
              <label>
                <span>역할</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('contactRole', event.target.value)}
                  required
                  value={accountContactForm.contactRole}
                >
                  {(accountManagement?.contactRoles ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <div className="form-field">
                <span>소속 계정</span>
                <SearchableSelect
                  ariaLabel="담당자 이동 대상 부서/연구실"
                  onChange={(nextValue) => handleAccountContactFieldChange('departmentId', nextValue)}
                  options={contactTargetDepartments.map(makeDepartmentSelectOption)}
                  placeholder="부서/연구실 검색"
                  value={accountContactForm.departmentId}
                />
              </div>
              <label>
                <span>활성 여부</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('isActive', event.target.value === 'true')}
                  value={accountContactForm.isActive ? 'true' : 'false'}
                >
                  <option value="true">활성</option>
                  <option value="false">비활성</option>
                </select>
              </label>
              <label>
                <span>PI/책임자</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('manager', event.target.value)}
                  value={accountContactForm.manager}
                />
              </label>
              <label>
                <span>연락처</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('phoneNumber', event.target.value)}
                  value={accountContactForm.phoneNumber}
                />
              </label>
              <label>
                <span>이메일</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('email', event.target.value)}
                  type="email"
                  value={accountContactForm.email}
                />
              </label>
              <label>
                <span>주소</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('address', event.target.value)}
                  value={accountContactForm.address}
                />
              </label>
              <label>
                <span>파이프라인</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('pipelineStage', event.target.value)}
                  required
                  value={accountContactForm.pipelineStage}
                >
                  {(accountManagement?.stages ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              <span>담당자 메모</span>
              <textarea
                onChange={(event) => handleAccountContactFieldChange('notes', event.target.value)}
                rows={3}
                value={accountContactForm.notes}
              />
            </label>
            <div className="notes-create-actions">
              <button className="route-secondary-action" onClick={() => setAccountContactEditor('')} type="button">
                취소
              </button>
              <button className="route-primary-action" disabled={accountContactSaving} type="submit">
                {accountContactSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                저장
              </button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="dashboard-panel customer-records-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Operational records</span>
            <h2>고객 운영 기록</h2>
          </div>
          <ListChecks size={18} />
        </div>
        <div className="customer-record-metrics">
          {operationalMetrics.map((metric) => (
            <span key={metric.label}>
              {metric.label}
              <strong>{metric.value}</strong>
            </span>
          ))}
        </div>
        <div className="customer-record-ledger-note">
          <span>납품 합계 {formatWon(operationalRecords.metrics.deliveryAmount)}</span>
          <span>선결제 차감 납품 {formatWon(operationalRecords.metrics.prepaymentDeliveryAmount)}</span>
          <span>일반 납품 {formatWon(operationalRecords.metrics.normalDeliveryAmount)}</span>
          <span>선결제 차감액 {formatWon(operationalRecords.metrics.prepaymentUsedAmount)}</span>
        </div>
        <div className="customer-record-sections">
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <div>
                <h3>납품 기록</h3>
                <span>부서/연구실 계정 기준 · 명시 결제구분 표시</span>
              </div>
              {(data.links.accountDeliveryRecordsXlsx || data.links.deliveryRecordsXlsx) ? (
                <a className="route-secondary-action" href={data.links.accountDeliveryRecordsXlsx || data.links.deliveryRecordsXlsx}>
                  <Download size={15} />
                  납품 엑셀
                </a>
              ) : null}
            </div>
            <CustomerDeliveryRecords records={operationalRecords.deliveryRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>견적 기록</h3>
              <span>같은 부서 견적서/견적 일정 기준</span>
            </div>
            <CustomerQuoteRecords records={operationalRecords.quoteRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>서비스 기록</h3>
              <span>A/S, 수리, 서비스 일정</span>
            </div>
            <CustomerServiceRecords records={operationalRecords.serviceRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>선결제 기록</h3>
              <span>같은 부서 입금, 잔액, 사용내역</span>
            </div>
            <CustomerPrepaymentRecords records={operationalRecords.prepaymentRecords} />
          </section>
        </div>
      </section>

      <section className="dashboard-panel customer-demo-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Demos</span>
            <h2>데모 현황</h2>
          </div>
          <Archive size={18} />
        </div>
        <div className="customer-assets-metrics">
          {demoMetrics.map((metric) => (
            <span key={metric.label}>
              {metric.label}
              <strong>{metric.value}</strong>
            </span>
          ))}
        </div>
        {!demoSummary.canManage && demoSummary.message ? (
          <div className="dashboard-api-alert compact">
            <ShieldCheck size={16} />
            <span>{demoSummary.message}</span>
          </div>
        ) : null}
        <div className="customer-assets-actions">
          {demoSummary.canManage && demoSummary.links.createDemo ? (
            <a className="route-secondary-action" href={demoSummary.links.createDemo}>
              <Plus size={15} />
              데모 등록
            </a>
          ) : null}
          <a className="route-secondary-action" href={demoSummary.links.demos || '/demos/'}>
            데모관리
            <MoveUpRight size={15} />
          </a>
        </div>
        {demoSummary.demos.length > 0 ? (
          <div className="customer-asset-list demo-summary-list">
            {demoSummary.demos.map((record) => (
              <article className="customer-asset-card" key={record.id}>
                <div>
                  <strong>{record.productName}</strong>
                  <span>{[record.customerName || '부서 연결', record.serialNumber, `${formatNumber(record.quantity)}개`].filter(Boolean).join(' · ')}</span>
                </div>
                <DemoStatusBadge record={record} />
                <div className="customer-asset-meta">
                  {record.startDate ? <span>시작 {formatDateLabel(record.startDate)}</span> : null}
                  {record.expectedReturnDate ? <span>예정 {formatDateLabel(record.expectedReturnDate)}</span> : null}
                  {record.returnedDate ? <span>회수 {formatDateLabel(record.returnedDate)}</span> : null}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label="등록된 데모 기록이 없습니다" />
        )}
      </section>

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel customer-edit-panel" ref={customerEditPanelRef}>
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
        <div className="customer-detail-main-stack">
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

          <section className="dashboard-panel customer-detail-main">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Schedule history</span>
                <h2>최근 일정</h2>
              </div>
              <CalendarDays size={18} />
            </div>
            <SchedulesCompactList emptyLabel="최근 일정이 없습니다" items={data.recentSchedules} />
          </section>

          <section className="dashboard-panel customer-detail-main customer-attachments-panel">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Files</span>
                <h2>첨부 파일</h2>
              </div>
              <Upload size={18} />
            </div>
            <div className="customer-attachment-metrics">
              <span>전체 <strong>{formatNumber(attachments.metrics.totalFiles)}개</strong></span>
              <span>영업노트 <strong>{formatNumber(attachments.metrics.noteFiles)}개</strong></span>
              <span>일정 <strong>{formatNumber(attachments.metrics.scheduleFiles)}개</strong></span>
            </div>
            <div className="customer-attachment-links">
              <a className="route-secondary-action" href={attachments.links.notes}>
                노트 파일
                <MoveUpRight size={14} />
              </a>
              <a className="route-secondary-action" href={attachments.links.schedules}>
                일정 파일
                <MoveUpRight size={14} />
              </a>
            </div>
            <CustomerAttachmentList files={attachments.recentFiles} />
          </section>
        </div>

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
              <a className="route-secondary-action" href={prepaymentScopeHref}>
                {prepaymentScopeLabel}
                <MoveUpRight size={15} />
              </a>
              <a className="route-secondary-action" href={prepaymentSummary.links.prepayments}>
                선결제 목록
                <MoveUpRight size={15} />
              </a>
            </div>
          </div>

          <div className="dashboard-panel-heading customer-detail-section-heading">
            <div>
              <span className="eyebrow">Upcoming</span>
              <h2>예정 일정</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          <SchedulesCompactList emptyLabel="예정 일정이 없습니다" items={data.upcomingSchedules} />
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
  departmentEditId,
  departmentEditName,
  departmentCreating,
  detailData,
  detailLoading,
  companyEditId,
  companyEditName,
  loading,
  managementSavingKey,
  company,
  grade,
  level,
  owner,
  page,
  query,
  rowMode,
  selectedCustomerId,
  selectedDetailMode,
  stage,
  onCompanyCreateNameChange,
  onCompanyCreateSubmit,
  onCompanyDelete,
  onCompanyEditCancel,
  onCompanyEditNameChange,
  onCompanyEditStart,
  onCompanyEditSubmit,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onDepartmentDelete,
  onDepartmentCreateNameChange,
  onDepartmentCreateSubmit,
  onDepartmentEditCancel,
  onDepartmentEditNameChange,
  onDepartmentEditStart,
  onDepartmentEditSubmit,
  onDetailRefresh,
  onCompanyFilterChange,
  onGradeChange,
  onLevelChange,
  onOwnerChange,
  onPageChange,
  onQueryChange,
  onRowModeChange,
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
  departmentEditId: number | null;
  departmentEditName: string;
  departmentCreating: boolean;
  detailData: CustomerDetailData | null;
  detailLoading: boolean;
  companyEditId: number | null;
  companyEditName: string;
  loading: boolean;
  managementSavingKey: string;
  company: string;
  grade: string;
  level: string;
  owner: string;
  page: number;
  query: string;
  rowMode: CustomerRowMode;
  selectedCustomerId: number | null;
  selectedDetailMode: CustomerDetailMode;
  stage: string;
  onCompanyCreateNameChange: (value: string) => void;
  onCompanyCreateSubmit: () => void;
  onCompanyDelete: (company: CustomerCompanyManageOption) => void;
  onCompanyEditCancel: () => void;
  onCompanyEditNameChange: (value: string) => void;
  onCompanyEditStart: (company: CustomerCompanyManageOption) => void;
  onCompanyEditSubmit: (company: CustomerCompanyManageOption) => void;
  onCreateFormChange: (field: keyof CustomerCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDepartmentDelete: (department: CustomerDepartmentManageOption) => void;
  onDepartmentCreateNameChange: (value: string) => void;
  onDepartmentCreateSubmit: () => void;
  onDepartmentEditCancel: () => void;
  onDepartmentEditNameChange: (value: string) => void;
  onDepartmentEditStart: (department: CustomerDepartmentManageOption) => void;
  onDepartmentEditSubmit: (department: CustomerDepartmentManageOption) => void;
  onDetailRefresh: () => Promise<CustomerDetailData | null>;
  onCompanyFilterChange: (value: string) => void;
  onGradeChange: (value: string) => void;
  onLevelChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onPageChange: (value: number) => void;
  onQueryChange: (value: string) => void;
  onRowModeChange: (value: CustomerRowMode) => void;
  onStageChange: (value: string) => void;
}) {
  if (selectedCustomerId) {
    return (
      <CustomerDetailPage
        data={detailData}
        detailMode={selectedDetailMode}
        loading={detailLoading}
        onRefresh={onDetailRefresh}
      />
    );
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

  const listRows = rowMode === 'contact' ? data.customers : (data.accounts.length > 0 ? data.accounts : data.customers);
  const totalAccountCount = data.metrics.totalAccounts || data.metrics.totalCustomers;
  const filteredAccountCount = data.metrics.filteredAccounts || data.metrics.filteredCustomers;
  const rowModeLabel = rowMode === 'contact' ? '담당자 목록' : '계정 목록';
  const rowModeDetail = rowMode === 'contact'
    ? `${formatNumber(data.pagination.contactRows || data.metrics.filteredCustomers)}명`
    : `${formatNumber(data.pagination.accountRows || filteredAccountCount)}개 계정`;
  const pagination = data.pagination;
  const currentPage = pagination.page || page || 1;
  const metrics = [
    { label: '계정', value: `${formatNumber(totalAccountCount)}개`, detail: data.scope.label, icon: Users, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(filteredAccountCount)}개`, detail: '부서/연구실 계정', icon: Search, tone: 'teal' as const },
    { label: '담당자', value: `${formatNumber(data.metrics.totalCustomers)}명`, detail: rowModeDetail, icon: Building2, tone: 'amber' as const },
    { label: '예정 일정 고객', value: `${formatNumber(data.metrics.scheduledCustomers)}건`, detail: '미래 일정 보유', icon: CalendarDays, tone: 'green' as const },
  ];
  const createConfig = data.create;
  const canCreateCustomers = createConfig.canCreate;
  const createCompanies = createConfig.companies;
  const createDepartments = createForm.companyId
    ? createConfig.departments.filter((department) => String(department.companyId) === createForm.companyId)
    : createConfig.departments;
  const manageableCompanies = createCompanies.filter((company) => company.canManage);
  const manageableDepartments = createDepartments.filter((department) => department.canManage);
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
          <h2>{data.scope.label || '계정 관리'}</h2>
          <p>부서/연구실 계정 기준으로 담당자, 일정, 활동, 후속조치를 확인합니다.</p>
        </div>
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

      <div className="customers-filter-tools">
        <div className="customer-row-mode" role="tablist" aria-label="고객 목록 표시 기준">
          {(data.options.rowModes.length > 0 ? data.options.rowModes : [
            { value: 'account' as CustomerRowMode, label: '계정 기준' },
            { value: 'contact' as CustomerRowMode, label: '담당자 기준' },
          ]).map((option) => (
            <button
              aria-selected={rowMode === option.value}
              className={rowMode === option.value ? 'active' : ''}
              key={option.value}
              onClick={() => onRowModeChange(option.value)}
              role="tab"
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="customer-export-actions">
          {data.export.canDownload ? (
            <>
              <a className="route-secondary-action" href={data.export.basicUrl}>
                <Download size={15} />
                기본 엑셀
              </a>
              <a className="route-secondary-action" href={data.export.fullUrl}>
                <FileSpreadsheet size={15} />
                전체 엑셀
              </a>
            </>
          ) : (
            <span>{data.export.message || '엑셀 권한 없음'}</span>
          )}
        </div>
      </div>

      <div className="customers-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="계정, 담당자, 회사, 연구실, 연락처 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onCompanyFilterChange(event.target.value)} value={company}>
          <option value="">업체 전체</option>
          {data.options.companies.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} ({formatNumber(option.count)})
            </option>
          ))}
        </select>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onStageChange(event.target.value)} value={stage}>
          <option value="">파이프라인 전체</option>
          {data.options.stages.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onGradeChange(event.target.value)} value={grade}>
          <option value="">고객등급 전체</option>
          {data.options.grades.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onLevelChange(event.target.value)} value={level}>
          <option value="">종합점수 전체</option>
          {data.options.scoreLevels.map((option) => (
            <option key={option.value} value={option.value}>
              {option.description ? `${option.label} (${option.description})` : option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="customers-layout">
        <section className="dashboard-panel customers-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customer list</span>
              <h2>{rowModeLabel}</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
          </div>
          <CustomersTable customers={listRows} emptyLabel={rowMode === 'contact' ? '조건에 맞는 담당자가 없습니다' : '조건에 맞는 계정이 없습니다'} />
          <div className="customers-pagination">
            <button
              className="route-secondary-action"
              disabled={!pagination.hasPrevious || loading}
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              type="button"
            >
              <ChevronLeft size={15} />
              이전
            </button>
            <span>
              {formatNumber(currentPage)} / {formatNumber(pagination.totalPages || 1)}
              {' · '}
              {formatNumber(pagination.totalRows)}건
            </span>
            <button
              className="route-secondary-action"
              disabled={!pagination.hasNext || loading}
              onClick={() => onPageChange(currentPage + 1)}
              type="button"
            >
              다음
              <ChevronRight size={15} />
            </button>
          </div>
        </section>

      </div>
    </section>
  );
}

function DemoStatusBadge({ record }: { record: DemoRecordItem }) {
  const overdue = record.expectedReturnDate
    && ['scheduled', 'active'].includes(record.status)
    && record.expectedReturnDate < localDateInputValue();
  return (
    <div className="customer-badge-row service-badge-row">
      <span className={`service-case-status ${record.status}`}>{record.statusLabel}</span>
      {overdue ? <span className="schedule-overdue">반납 지연</span> : null}
    </div>
  );
}

function DemoRecordFormPanel({
  data,
  editingId,
  form,
  open,
  saving,
  onClose,
  onFormChange,
  onSubmit,
}: {
  data: DemoRecordsData;
  editingId: number | null;
  form: DemoRecordFormState;
  open: boolean;
  saving: boolean;
  onClose: () => void;
  onFormChange: (updater: (form: DemoRecordFormState) => DemoRecordFormState) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (!open) {
    return null;
  }

  const selectedAccount = data.options.accounts.find((account) => String(account.departmentId) === form.departmentId) || null;
  const contactOptions = selectedAccount?.contacts ?? [];

  return (
    <section className="dashboard-panel demo-form-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Demo form</span>
          <h2>{editingId ? '데모 기록 수정' : '데모 등록'}</h2>
        </div>
        <button className="route-secondary-action icon-only" onClick={onClose} type="button" aria-label="닫기">
          <X size={16} />
        </button>
      </div>
      <form className="notes-create-form demo-record-form" onSubmit={onSubmit}>
        <div className="notes-create-grid demo-form-grid">
          <div className="form-field demo-field-account">
            <span>부서/연구실</span>
            <SearchableSelect
              ariaLabel="데모 계정 선택"
              onChange={(value) => onFormChange((current) => ({
                ...current,
                departmentId: value,
                customerId: '',
              }))}
              options={data.options.accounts.map(makeDemoAccountSelectOption)}
              placeholder="업체, 부서, 연구원 이름으로 검색"
              value={form.departmentId}
            />
          </div>
          <label>
            <span>고객</span>
            <select
              disabled={!selectedAccount || contactOptions.length === 0}
              onChange={(event) => onFormChange((current) => ({ ...current, customerId: event.target.value }))}
              value={form.customerId}
            >
              <option value="">부서에만 연결</option>
              {contactOptions.map((contact) => (
                <option key={contact.id} value={contact.id}>{contact.name} · {contact.ownerName}</option>
              ))}
            </select>
          </label>
          <label>
            <span>제품</span>
            <SearchableSelect
              ariaLabel="데모 제품 선택"
              onChange={(value) => onFormChange((current) => ({ ...current, productId: value, productName: '' }))}
              options={data.options.products.map(makeProductSelectOption)}
              placeholder="제품 코드/규격 검색"
              value={form.productId}
            />
          </label>
          <label>
            <span>수량</span>
            <input
              min="1"
              onChange={(event) => onFormChange((current) => ({ ...current, quantity: event.target.value }))}
              type="number"
              value={form.quantity}
            />
          </label>
          <label>
            <span>상태</span>
            <select
              onChange={(event) => onFormChange((current) => ({ ...current, status: event.target.value }))}
              value={form.status}
            >
              {data.options.statuses.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>시작일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, startDate: event.target.value }))}
              type="date"
              value={form.startDate}
            />
          </label>
          <label>
            <span>반납 예정일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, expectedReturnDate: event.target.value }))}
              type="date"
              value={form.expectedReturnDate}
            />
          </label>
          <label>
            <span>회수일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, returnedDate: event.target.value }))}
              type="date"
              value={form.returnedDate}
            />
          </label>
          <label>
            <span>담당자</span>
            <select
              onChange={(event) => onFormChange((current) => ({ ...current, ownerId: event.target.value }))}
              value={form.ownerId}
            >
              <option value="">현재 사용자</option>
              {data.options.owners.map((owner) => (
                <option key={owner.id} value={owner.id}>{owner.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>시리얼/식별번호</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, serialNumber: event.target.value }))}
              placeholder="선택 입력"
              value={form.serialNumber}
            />
          </label>
          <label className="demo-field-wide">
            <span>메모</span>
            <textarea
              onChange={(event) => onFormChange((current) => ({ ...current, notes: event.target.value }))}
              placeholder="데모 조건, 설치 위치, 회수 메모"
              rows={3}
              value={form.notes}
            />
          </label>
        </div>
        <div className="notes-create-actions demo-form-actions">
          <button className="route-secondary-action" onClick={onClose} type="button">취소</button>
          <button className="route-primary-action" disabled={saving} type="submit">
            {saving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
            저장
          </button>
        </div>
      </form>
    </section>
  );
}

function DemoRecordsTable({
  demos,
  order,
  sort,
  saving,
  onDelete,
  onEdit,
  onSort,
}: {
  demos: DemoRecordItem[];
  order: string;
  sort: string;
  saving: boolean;
  onDelete: (record: DemoRecordItem) => void;
  onEdit: (record: DemoRecordItem) => void;
  onSort: (key: string) => void;
}) {
  if (demos.length === 0) {
    return <DashboardEmpty label="조건에 맞는 데모 기록이 없습니다" />;
  }

  const sortLabel = (key: string) => (sort === key ? (order === 'asc' ? '↑' : '↓') : '');
  return (
    <div className="customers-table-wrap service-cases-table-wrap">
      <table className="customers-table service-cases-table demos-table">
        <thead>
          <tr>
            <th><button className={`product-sort-button ${sort === 'account' ? 'active' : ''}`.trim()} onClick={() => onSort('account')} type="button">고객/계정 {sortLabel('account')}</button></th>
            <th><button className={`product-sort-button ${sort === 'product' ? 'active' : ''}`.trim()} onClick={() => onSort('product')} type="button">제품 {sortLabel('product')}</button></th>
            <th><button className={`product-sort-button ${sort === 'status' ? 'active' : ''}`.trim()} onClick={() => onSort('status')} type="button">상태 {sortLabel('status')}</button></th>
            <th><button className={`product-sort-button ${sort === 'expectedReturnDate' ? 'active' : ''}`.trim()} onClick={() => onSort('expectedReturnDate')} type="button">기간 {sortLabel('expectedReturnDate')}</button></th>
            <th>담당/메모</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          {demos.map((record) => (
            <tr key={record.id}>
              <td>
                <a className="customer-name-link" href={record.customerHref || record.accountHref || '/customers/'}>
                  <strong>{record.customerName || '담당자 없음'}</strong>
                  <span>{[record.companyName, record.departmentName].filter(Boolean).join(' · ')}</span>
                </a>
                <div className="notes-row-actions">
                  {record.accountHref ? <a className="customer-row-action" href={record.accountHref}>계정</a> : null}
                  {record.customerHref ? <a className="customer-row-action" href={record.customerHref}>고객</a> : null}
                </div>
              </td>
              <td>
                <strong>{record.productName}</strong>
                <small>{record.quantity ? `${formatNumber(record.quantity)}개` : ''}</small>
                {record.serialNumber ? <small>{record.serialNumber}</small> : null}
              </td>
              <td>
                <DemoStatusBadge record={record} />
              </td>
              <td>
                <span>{record.startDate ? `시작 ${formatDateLabel(record.startDate)}` : '시작일 없음'}</span>
                {record.expectedReturnDate ? <small>예정 {formatDateLabel(record.expectedReturnDate)}</small> : null}
                {record.returnedDate ? <small>회수 {formatDateLabel(record.returnedDate)}</small> : null}
              </td>
              <td>
                <span>{record.ownerName || record.createdByName || '담당자 없음'}</span>
                {record.notes ? <small>{record.notes}</small> : null}
              </td>
              <td>
                <div className="notes-row-actions">
                  <button className="customer-row-action" disabled={!record.canManage || saving} onClick={() => onEdit(record)} type="button">수정</button>
                  <button className="customer-row-action danger" disabled={!record.canManage || saving} onClick={() => onDelete(record)} type="button">삭제</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DemoManagementPage({
  data,
  error,
  form,
  loading,
  message,
  open,
  owner,
  product,
  query,
  saving,
  sort,
  order,
  status,
  editingId,
  onCloseForm,
  onDelete,
  onEdit,
  onFormChange,
  onOpenCreate,
  onOwnerChange,
  onProductChange,
  onQueryChange,
  onSort,
  onStatusChange,
  onSubmit,
}: {
  data: DemoRecordsData | null;
  error: string;
  form: DemoRecordFormState;
  loading: boolean;
  message: string;
  open: boolean;
  owner: string;
  product: string;
  query: string;
  saving: boolean;
  sort: string;
  order: string;
  status: string;
  editingId: number | null;
  onCloseForm: () => void;
  onDelete: (record: DemoRecordItem) => void;
  onEdit: (record: DemoRecordItem) => void;
  onFormChange: (updater: (form: DemoRecordFormState) => DemoRecordFormState) => void;
  onOpenCreate: () => void;
  onOwnerChange: (value: string) => void;
  onProductChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSort: (key: string) => void;
  onStatusChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>데모 기록을 불러오는 중입니다</span>
      </section>
    );
  }
  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 데모', value: `${formatNumber(data.summary.total)}건`, detail: data.scope.label, icon: Archive, tone: 'blue' as const },
    { label: '진행중', value: `${formatNumber(data.summary.active)}건`, detail: '현재 대여/설치', icon: Activity, tone: 'teal' as const },
    { label: '반납 지연', value: `${formatNumber(data.summary.overdue)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: data.summary.overdue > 0 ? 'red' as const : 'green' as const },
    { label: '구매전환', value: `${formatNumber(data.summary.converted)}건`, detail: '데모 후 구매', icon: CheckCircle2, tone: 'green' as const },
  ];

  return (
    <section className="customers-page demos-page">
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Demo management</span>
          <h2>{data.scope.label || '데모관리'}</h2>
          <p>고객/계정별 데모 제품과 반납 상태를 제품 원장과 연결해 확인합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          {data.permissions.canCreate ? (
            <button className="route-primary-action" onClick={onOpenCreate} type="button">
              <Plus size={15} />
              데모 등록
            </button>
          ) : null}
          <a className="route-secondary-action" href="/products/">제품관리</a>
        </div>
      </div>

      {error ? <div className="form-status error">{error}</div> : null}
      {message ? <div className="form-status success">{message}</div> : null}
      {!data.permissions.canCreate && data.permissions.readOnlyMessage ? (
        <div className="dashboard-api-alert compact">
          <ShieldCheck size={16} />
          <span>{data.permissions.readOnlyMessage}</span>
        </div>
      ) : null}

      <DemoRecordFormPanel
        data={data}
        editingId={editingId}
        form={form}
        open={open}
        saving={saving}
        onClose={onCloseForm}
        onFormChange={onFormChange}
        onSubmit={onSubmit}
      />

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="데모 핵심 지표">
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

      <div className="customers-filter-bar demos-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 부서, 제품, 시리얼 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="all">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onProductChange(event.target.value)} value={product}>
          <option value="">제품 전체</option>
          {data.options.products.map((item) => (
            <option key={item.id} value={item.id}>{item.productCode}</option>
          ))}
        </select>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((item) => (
            <option key={item.id} value={item.id}>{item.name}</option>
          ))}
        </select>
      </div>

      <section className="dashboard-panel services-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Demo list</span>
            <h2>데모 현황</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <Archive size={18} />}
        </div>
        <DemoRecordsTable
          demos={data.demos}
          order={order}
          saving={saving}
          sort={sort}
          onDelete={onDelete}
          onEdit={onEdit}
          onSort={onSort}
        />
      </section>
    </section>
  );
}

function ProfileSettingsPage({
  data,
  error,
  form,
  loading,
  message,
  passwordForm,
  passwordSaving,
  saving,
  onFormChange,
  onPasswordFormChange,
  onPasswordSubmit,
  onSubmit,
}: {
  data: ProfileData | null;
  error: string;
  form: ProfileFormState;
  loading: boolean;
  message: string;
  passwordForm: ProfilePasswordFormState;
  passwordSaving: boolean;
  saving: boolean;
  onFormChange: (field: keyof ProfileFormState, value: string) => void;
  onPasswordFormChange: (field: keyof ProfilePasswordFormState, value: string) => void;
  onPasswordSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>프로필 데이터를 불러오는 중입니다</span>
      </section>
    );
  }
  if (!data) return null;
  const permissionItems = [
    { label: 'AI 사용', enabled: data.profile.canUseAi },
    { label: '엑셀 다운로드', enabled: data.profile.canDownloadExcel },
  ];

  return (
    <section className="profile-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>프로필 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}
      {message ? <div className="form-success-message">{message}</div> : null}
      {error ? <div className="form-error-message">{error}</div> : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Profile</span>
          <h2>{data.user.fullName || data.user.username || '프로필'}</h2>
          <p>{[data.profile.roleLabel, data.profile.company].filter(Boolean).join(' · ') || '계정 정보'}</p>
        </div>
        <a className="route-secondary-action" href={data.links.dashboard}>대시보드</a>
      </div>

      <div className="profile-overview-strip">
        <div>
          <Users size={18} />
          <span>계정</span>
          <strong>{data.user.username || '-'}</strong>
        </div>
        <div>
          <Building2 size={18} />
          <span>소속</span>
          <strong>{data.profile.company || '-'}</strong>
        </div>
        <div>
          <ShieldCheck size={18} />
          <span>권한</span>
          <strong>{permissionItems.filter((item) => item.enabled).length} / {permissionItems.length}</strong>
        </div>
      </div>

      <div className="profile-layout">
        <section className="dashboard-panel profile-info-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Account</span>
              <h2>기본 정보</h2>
            </div>
            <Users size={18} />
          </div>
          <form className="profile-form" onSubmit={onSubmit}>
            <label className="profile-form-wide">사용자명<input value={form.username} onChange={(event) => onFormChange('username', event.target.value)} required /></label>
            <label>성<input value={form.firstName} onChange={(event) => onFormChange('firstName', event.target.value)} /></label>
            <label>이름<input value={form.lastName} onChange={(event) => onFormChange('lastName', event.target.value)} /></label>
            <label className="profile-form-wide">이메일<input type="email" value={form.email} onChange={(event) => onFormChange('email', event.target.value)} /></label>
            <div className="profile-readonly-grid">
              <div><span>권한</span><strong>{data.profile.roleLabel || '-'}</strong></div>
              <div><span>소속</span><strong>{data.profile.company || '-'}</strong></div>
              <div><span>가입일</span><strong>{data.user.dateJoined ? formatDateLabel(data.user.dateJoined) : '-'}</strong></div>
              <div><span>최종 로그인</span><strong>{data.user.lastLogin ? formatDateTimeLabel(data.user.lastLogin) : '-'}</strong></div>
            </div>
            <div className="profile-permission-row">
              {permissionItems.map((item) => (
                <span className={item.enabled ? 'status-pill done' : 'status-pill neutral'} key={item.label}>
                  {item.label}
                </span>
              ))}
            </div>
            <button className="primary-button" disabled={saving} type="submit">
              {saving ? <Loader2 className="spin-icon" size={16} /> : <Check size={16} />}
              기본 정보 저장
            </button>
          </form>
        </section>

        <section className="dashboard-panel profile-password-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Password</span>
              <h2>비밀번호 변경</h2>
            </div>
            <Target size={18} />
          </div>
          <form className="profile-form profile-password-form" onSubmit={onPasswordSubmit}>
            <label>현재 비밀번호<input type="password" value={passwordForm.oldPassword} onChange={(event) => onPasswordFormChange('oldPassword', event.target.value)} required /></label>
            <label>새 비밀번호<input type="password" value={passwordForm.newPassword1} onChange={(event) => onPasswordFormChange('newPassword1', event.target.value)} required /></label>
            <label>새 비밀번호 확인<input type="password" value={passwordForm.newPassword2} onChange={(event) => onPasswordFormChange('newPassword2', event.target.value)} required /></label>
            <button className="primary-button" disabled={passwordSaving} type="submit">
              {passwordSaving ? <Loader2 className="spin-icon" size={16} /> : <Check size={16} />}
              비밀번호 변경
            </button>
          </form>
        </section>
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
                  {noteNextActionLabel(note) || '다음 액션 없음'}
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
  const [noteDeleting, setNoteDeleting] = useState(false);
  const [noteDeleteError, setNoteDeleteError] = useState('');
  const [noteDeleteMessage, setNoteDeleteMessage] = useState('');
  const noteEditPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(editOpen, noteEditPanelRef, `note-edit-${currentNote?.id || 'new'}`);

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
    setNoteDeleting(false);
    setNoteDeleteError('');
    setNoteDeleteMessage('');
    if (noteFileInputRef.current) {
      noteFileInputRef.current.value = '';
    }
  }, [currentNote?.id]);

  const editConfig = data?.edit;
  const activityDateVisible = editForm.actionType === 'customer_meeting' || editForm.actionType === 'delivery_schedule';
  const editCustomers = editConfig?.customers ?? [];
  const editDepartments = editConfig?.departments ?? [];
  const filteredEditCustomers = customersForDepartment(editCustomers, editForm.departmentId);
  const selectedEditDepartmentHasCustomers = filteredEditCustomers.length > 0;
  const editCustomerCanBeEmpty = Boolean(editForm.departmentId) && (
    !selectedEditDepartmentHasCustomers || !currentNote?.followupId
  );

  const handleEditFieldChange = (field: keyof NoteEditFormState, value: string) => {
    setEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(editCustomers, nextValue);
    const currentCustomerStillAvailable = nextCustomers.some((customer) => String(customer.id) === editForm.followupId);
    setEditForm((previous) => ({
      ...previous,
      departmentId: nextValue,
      followupId: currentCustomerStillAvailable ? previous.followupId : '',
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditCustomerChange = (nextValue: string) => {
    const nextCustomer = editCustomers.find((customer) => String(customer.id) === nextValue);
    setEditForm((previous) => ({
      ...previous,
      departmentId: nextCustomer?.departmentId ? String(nextCustomer.departmentId) : previous.departmentId,
      followupId: nextValue,
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
    const departmentId = Number(editForm.departmentId);
    if (!followupId && !departmentId) {
      setEditError('고객 또는 부서/연구실을 선택하세요.');
      return;
    }
    if (!editForm.actionType) {
      setEditError('활동 유형을 선택하세요.');
      return;
    }
    if (!editForm.content.trim()) {
      setEditError('활동 내용을 입력하세요.');
      return;
    }
    const payload: NoteEditPayload = {
      actionType: editForm.actionType,
      activityDate: activityDateVisible ? editForm.activityDate || undefined : undefined,
      content: editForm.content.trim(),
      departmentId: departmentId || undefined,
      deliveryAmount: editForm.deliveryAmount.trim() || undefined,
      deliveryItems: editForm.deliveryItems.trim() || undefined,
      followupId: followupId || undefined,
      nextAction: editForm.nextAction.trim() || undefined,
      nextActionDate: editForm.nextActionDate || undefined,
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

  const handleDeleteNote = async () => {
    if (!currentNote?.canDelete || !currentNote.deleteHref || noteDeleting) {
      setNoteDeleteError('삭제 권한이 없습니다.');
      setNoteDeleteMessage('');
      return;
    }
    if (!window.confirm('이 영업노트를 삭제할까요? 첨부파일과 댓글도 함께 정리됩니다.')) {
      return;
    }

    setNoteDeleting(true);
    setNoteDeleteError('');
    setNoteDeleteMessage('');
    try {
      const result = await deleteSalesNote(currentNote.deleteHref);
      setNoteDeleteMessage(result.message || '영업노트를 삭제했습니다.');
      window.location.assign(result.redirect || '/notes/');
    } catch (error) {
      setNoteDeleteError(error instanceof Error ? error.message : '영업노트 삭제에 실패했습니다.');
    } finally {
      setNoteDeleting(false);
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

  const handleNoteFileDelete = async (file: NoteFileItem | AttachmentManagerFile) => {
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

    setNoteFileDeletingId(Number(file.id));
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
  const deleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
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
          {note.canDelete && note.deleteHref ? (
            <button className="route-secondary-action danger" disabled={noteDeleting} onClick={handleDeleteNote} type="button">
              {noteDeleting ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
              삭제
            </button>
          ) : null}
        </div>
      </div>

      {deleteRequested && note.canDelete ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>삭제 요청으로 들어왔습니다. 상단의 삭제 버튼으로 확정하세요.</span>
        </div>
      ) : null}
      {noteDeleteError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{noteDeleteError}</span></div> : null}
      {noteDeleteMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{noteDeleteMessage}</span></div> : null}

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
        <section className="dashboard-panel notes-create-panel note-edit-panel" ref={noteEditPanelRef}>
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
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    onChange={handleEditDepartmentChange}
                    options={editDepartments.map(makeDepartmentSelectOption)}
                    placeholder="회사, 부서/연구실, 담당자 검색"
                    value={editForm.departmentId}
                  />
                </div>
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    allowEmpty={editCustomerCanBeEmpty}
                    ariaLabel="고객 선택"
                    disabled={Boolean(editForm.departmentId) && !selectedEditDepartmentHasCustomers}
                    emptyLabel="부서에만 연결"
                    onChange={handleEditCustomerChange}
                    options={filteredEditCustomers.map(makeCustomerSelectOption)}
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
                  required
                  rows={4}
                  value={editForm.content}
                />
              </label>
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
          <div className="note-detail-next-action">
            <span>다음 액션</span>
            <p className={note.overdue ? 'customer-overdue-text' : ''}>{noteNextActionLabel(note) || '다음 액션 없음'}</p>
            {note.nextActionDate ? <small>{formatDateLabel(note.nextActionDate)}</small> : null}
          </div>
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
              <span className="eyebrow">Related</span>
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
                <dd className={note.overdue ? 'customer-overdue-text' : ''}>{noteNextActionLabel(note) || '다음 액션 없음'}</dd>
              </div>
            </dl>
          </div>
          <div className="customers-side-actions note-detail-actions">
            {data.links.customer ? <a href={data.links.customer}>고객 상세</a> : null}
            {data.links.schedule ? <a href={data.links.schedule}>연결 일정</a> : null}
            <a href={data.links.createNote}>새 노트 작성</a>
          </div>
          {noteFileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{noteFileError}</span></div> : null}
          {noteFileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{noteFileMessage}</span></div> : null}
          <AttachmentManager
            canUpload={note.canEdit && Boolean(data.links.uploadFiles)}
            deletingId={noteFileDeletingId}
            emptyLabel="첨부파일이 없습니다"
            files={note.files}
            inputRef={noteFileInputRef}
            title="첨부파일"
            uploadAriaLabel="영업노트 첨부파일 선택"
            uploading={noteFileUploading}
            onDelete={handleNoteFileDelete}
            onFilesSelected={handleNoteFilesSelected}
            onUploadClick={handleNoteFileUploadClick}
          />
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
                  <div className="note-reply-content">
                    <strong>{reply.author}</strong>
                    <span>{[reply.authorRole, reply.createdAt ? formatDateTimeLabel(reply.createdAt) : ''].filter(Boolean).join(' · ')}</span>
                    <p>{reply.content}</p>
                  </div>
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
  dateFrom,
  dateTo,
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
  onDateFromChange,
  onDateToChange,
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
  dateFrom: string;
  dateTo: string;
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
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onNextActionChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onReviewChange: (value: string) => void;
  onToggleReview: (note: NoteItem) => void;
}) {
  const createPanelRef = useRef<HTMLElement | null>(null);
  useGuidedPanelFocus(createOpen, createPanelRef, 'note-create');

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
    { label: '7일 이내', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '다가오는 액션', icon: Clock, tone: 'green' as const },
  ];
  const createConfig = data.create;
  const canCreateNotes = createConfig.canCreate;
  const createCustomers = createConfig.customers;
  const createDepartments = createConfig.departments ?? [];
  const createActionTypes = createConfig.actionTypes;
  const createSchedules = createConfig.schedules ?? [];
  const filteredCreateCustomers = customersForDepartment(createCustomers, createForm.departmentId);
  const availableCreateSchedules = createSchedules.filter((schedule) => (
    createForm.followupId
      ? String(schedule.followupId) === createForm.followupId
      : !createForm.departmentId || String(schedule.departmentId || '') === createForm.departmentId
  ));
  const selectedCreateSchedule = createSchedules.find((schedule) => String(schedule.id) === createForm.scheduleId) ?? null;
  const selectedDepartmentHasCustomers = filteredCreateCustomers.length > 0;
  const handleCreateDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(createCustomers, nextValue);
    const nextCustomerId = nextCustomers[0]?.id ? String(nextCustomers[0].id) : '';
    onCreateFormChange('departmentId', nextValue);
    onCreateFormChange('followupId', nextCustomerId);
    onCreateFormChange('scheduleId', '');
  };
  const handleCreateCustomerChange = (nextValue: string) => {
    const nextCustomer = createCustomers.find((customer) => String(customer.id) === nextValue);
    const selectedScheduleBelongsToCustomer = selectedCreateSchedule && String(selectedCreateSchedule.followupId) === nextValue;
    if (nextCustomer?.departmentId) {
      onCreateFormChange('departmentId', String(nextCustomer.departmentId));
    }
    onCreateFormChange('followupId', nextValue);
    if (!selectedScheduleBelongsToCustomer) {
      onCreateFormChange('scheduleId', '');
    }
  };
  const handleCreateScheduleChange = (nextValue: string) => {
    const nextSchedule = createSchedules.find((schedule) => String(schedule.id) === nextValue);
    onCreateFormChange('scheduleId', nextValue);
    if (!nextSchedule) {
      return;
    }
    if (String(nextSchedule.followupId) !== createForm.followupId) {
      onCreateFormChange('followupId', nextSchedule.followupId ? String(nextSchedule.followupId) : '');
    }
    if (nextSchedule.departmentId && String(nextSchedule.departmentId) !== createForm.departmentId) {
      onCreateFormChange('departmentId', String(nextSchedule.departmentId));
    }
    if (nextSchedule.date) {
      onCreateFormChange('activityDate', nextSchedule.date);
    }
    if (isNoteActionAllowed(createActionTypes, nextSchedule.suggestedActionType)) {
      onCreateFormChange('actionType', nextSchedule.suggestedActionType);
    }
  };

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
        <section className="dashboard-panel notes-create-panel" ref={createPanelRef}>
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
          ) : createDepartments.length === 0 && createCustomers.length === 0 ? (
            <DashboardEmpty label="작성 가능한 부서/연구실이 없습니다" />
          ) : createActionTypes.length === 0 ? (
            <DashboardEmpty label="작성 가능한 활동 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid">
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    onChange={handleCreateDepartmentChange}
                    options={createDepartments.map(makeDepartmentSelectOption)}
                    placeholder="회사, 부서/연구실, 담당자 검색"
                    value={createForm.departmentId}
                  />
                </div>
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    allowEmpty={!selectedDepartmentHasCustomers}
                    ariaLabel="고객 선택"
                    disabled={!selectedDepartmentHasCustomers}
                    emptyLabel="부서에만 연결"
                    onChange={handleCreateCustomerChange}
                    options={filteredCreateCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={createForm.followupId}
                  />
                </div>
                <label>
                  <span>연결 일정/납품</span>
                  <select
                    onChange={(event) => handleCreateScheduleChange(event.target.value)}
                    value={createForm.scheduleId}
                  >
                    <option value="">연결 없음</option>
                    {availableCreateSchedules.map((schedule) => (
                      <option key={schedule.id} value={schedule.id}>
                        {schedule.label}
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
              {selectedCreateSchedule ? (
                <div className="note-linked-schedule-card">
                  <div>
                    <strong>{selectedCreateSchedule.activityLabel}</strong>
                    <span>
                      {[
                        selectedCreateSchedule.date ? formatDateLabel(selectedCreateSchedule.date) : '',
                        selectedCreateSchedule.time,
                        selectedCreateSchedule.statusLabel,
                      ].filter(Boolean).join(' · ')}
                    </span>
                    {selectedCreateSchedule.deliveryItems ? <p>{selectedCreateSchedule.deliveryItems}</p> : null}
                  </div>
                  <div>
                    {selectedCreateSchedule.deliveryAmount > 0 ? <strong>{formatWon(selectedCreateSchedule.deliveryAmount)}</strong> : null}
                    <a className="customer-row-action" href={selectedCreateSchedule.href}>일정 상세</a>
                  </div>
                </div>
              ) : null}
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
                <a className="route-secondary-action" href="/notes/?create=1">
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
            placeholder="이름, 고객, 회사, 노트 내용, 다음 액션 검색"
            value={query}
          />
        </label>
        <label className="notes-date-filter">
          <span>시작</span>
          <input
            aria-label="영업노트 시작일"
            onChange={(event) => onDateFromChange(event.target.value)}
            type="date"
            value={dateFrom}
          />
        </label>
        <label className="notes-date-filter">
          <span>종료</span>
          <input
            aria-label="영업노트 종료일"
            onChange={(event) => onDateToChange(event.target.value)}
            type="date"
            value={dateTo}
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
            <a href={data.links.notes}>전체 노트</a>
            <a href={data.links.unreviewed}>미검토 노트</a>
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

function buildScheduleCalendarDays(monthValue: string, schedules: ScheduleItem[]) {
  const [year, month] = monthValue.split('-').map(Number);
  const firstDay = new Date(year, month - 1, 1);
  const gridStart = new Date(firstDay);
  gridStart.setDate(firstDay.getDate() - ((firstDay.getDay() + 6) % 7));
  const todayValue = localDateInputValue();
  const schedulesByDate = new Map<string, ScheduleItem[]>();

  schedules.forEach((schedule) => {
    if (!schedule.date) {
      return;
    }
    const items = schedulesByDate.get(schedule.date) ?? [];
    items.push(schedule);
    schedulesByDate.set(schedule.date, items);
  });
  schedulesByDate.forEach((items) => {
    items.sort((a, b) => `${a.time} ${a.type}`.localeCompare(`${b.time} ${b.type}`));
  });

  return Array.from({ length: 42 }, (_item, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    const dateValue = localDateInputValue(date);
    return {
      date: dateValue,
      dayNumber: date.getDate(),
      inMonth: date.getMonth() === month - 1,
      isToday: dateValue === todayValue,
      schedules: schedulesByDate.get(dateValue) ?? [],
    };
  });
}

function getScheduleReportPreviewLines(report: NonNullable<ScheduleItem['reports']>[number]) {
  const lines = [
    report.content,
    report.deliveryItems ? `납품 품목: ${report.deliveryItems}` : '',
    report.deliveryAmount > 0 ? `납품 금액: ${formatWon(report.deliveryAmount)}` : '',
    report.nextAction ? `다음 액션: ${report.nextAction}` : '',
  ].filter(Boolean);

  if (lines.length > 0) {
    return lines;
  }
  return report.summary ? [report.summary] : [];
}

function ScheduleCalendarSelectedList({
  deletingKey,
  items,
  statusUpdatingKey,
  onDelete,
  onEdit,
  onStatusChange,
}: {
  deletingKey: string;
  items: ScheduleItem[];
  statusUpdatingKey: string;
  onDelete: (schedule: ScheduleItem) => void;
  onEdit: (schedule: ScheduleItem) => void;
  onStatusChange: (schedule: ScheduleItem, status: string) => void;
}) {
  if (items.length === 0) {
    return <DashboardEmpty label="선택한 날짜의 일정이 없습니다" />;
  }

  return (
    <div className="schedule-calendar-selected-list">
      {items.map((item) => {
        const itemKey = `${item.type}-${item.id}`;
        const statusOptions = item.statusOptions ?? [];
        const reports = item.reports ?? [];
        const canChangeStatus = item.type === 'customer' && Boolean(item.canEdit && item.statusUpdateHref && statusOptions.length);
        const canManage = Boolean(item.canEdit);
        const isUpdating = statusUpdatingKey === itemKey;
        const isDeleting = deletingKey === itemKey;
        return (
          <article className={`schedule-calendar-selected-card ${item.overdue ? 'urgent' : ''}`} key={itemKey}>
            <div className="schedule-calendar-selected-main">
              <div>
                <strong>{item.company || item.title || item.customer}</strong>
                <span>{[item.customer, item.department, item.activityLabel, item.owner].filter(Boolean).join(' · ')}</span>
                {item.notes ? <small>{item.notes}</small> : null}
              </div>
              <time>
                {item.time || '시간 없음'}
              </time>
            </div>
            <ScheduleStatusBadge schedule={item} />
            {reports.length > 0 ? (
              <div className="schedule-calendar-report-list">
                <div className="schedule-calendar-report-heading">
                  <span>보고 내용</span>
                  <small>{reports.length}건</small>
                </div>
                {reports.map((report) => {
                  const previewLines = getScheduleReportPreviewLines(report);
                  return (
                    <div className="schedule-calendar-report-item" key={report.id}>
                      <div className="schedule-calendar-report-meta">
                        <strong>{report.actionLabel}</strong>
                        <span>{report.activityDate ? formatDateLabel(report.activityDate) : formatDateTimeLabel(report.createdAt)}</span>
                      </div>
                      {previewLines.length > 0 ? (
                        <div className="schedule-calendar-report-body">
                          {previewLines.map((line, index) => <p key={`${report.id}-${index}`}>{line}</p>)}
                        </div>
                      ) : (
                        <p className="schedule-calendar-report-empty">보고 내용이 비어 있습니다.</p>
                      )}
                      <a href={report.href}>보고 상세</a>
                    </div>
                  );
                })}
              </div>
            ) : null}
            <div className="schedule-calendar-selected-actions">
              {canManage ? (
                <button onClick={() => onEdit(item)} type="button">
                  <Pencil size={13} />
                  수정
                </button>
              ) : null}
              {canManage ? (
                <button className="danger" disabled={isDeleting} onClick={() => onDelete(item)} type="button">
                  {isDeleting ? <Loader2 className="spin-icon" size={13} /> : <Trash2 size={13} />}
                  삭제
                </button>
              ) : null}
              <a href={item.href}>상세</a>
              {item.customerHref ? <a href={item.customerHref}>고객</a> : null}
              {item.createHistoryHref ? <a href={item.createHistoryHref}>보고</a> : null}
            </div>
            {canChangeStatus ? (
              <div className="schedule-calendar-status-actions" aria-label={`${item.customer || item.title} 상태 변경`}>
                {statusOptions.map((option) => (
                  <button
                    className={option.value === item.status ? 'active' : ''}
                    disabled={isUpdating || option.value === item.status}
                    key={option.value}
                    onClick={() => onStatusChange(item, option.value)}
                    type="button"
                  >
                    {isUpdating && option.value !== item.status ? <Loader2 className="spin-icon" size={13} /> : null}
                    {option.label}
                  </button>
                ))}
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

function ScheduleCalendarPage({
  data,
  dataFilter,
  filterUser,
  loading,
  month,
  statusError,
  statusMessage,
  statusUpdatingKey,
  onDataFilterChange,
  onFilterUserChange,
  onMonthChange,
  onRefresh,
  onStatusChange,
}: {
  data: ScheduleCalendarData | null;
  dataFilter: string;
  filterUser: string;
  loading: boolean;
  month: string;
  statusError: string;
  statusMessage: string;
  statusUpdatingKey: string;
  onDataFilterChange: (value: string) => void;
  onFilterUserChange: (value: string) => void;
  onMonthChange: (value: string) => void;
  onRefresh: () => Promise<ScheduleCalendarData | null>;
  onStatusChange: (schedule: ScheduleItem, status: string) => void;
}) {
  const range = useMemo(() => getScheduleCalendarRange(month), [month]);
  const initialIntentRef = useRef({
    create: getScheduleCalendarCreateParam(),
    date: getCreateDateParam(),
    time: getCreateTimeParam(),
    personalId: getScheduleCalendarPersonalIdParam(),
    createHandled: false,
    personalHandled: false,
  });
  const [selectedDate, setSelectedDate] = useState(() => {
    const intentDate = initialIntentRef.current.date;
    if (intentDate) {
      return intentDate;
    }
    const today = localDateInputValue();
    return today >= range.start && today <= range.end ? today : range.start;
  });
  const [calendarCreateOpen, setCalendarCreateOpen] = useState(false);
  const [calendarCreateForm, setCalendarCreateForm] = useState<ScheduleCreateFormState>(() => makeEmptyScheduleCreateForm());
  const [calendarCreating, setCalendarCreating] = useState(false);
  const [calendarCreateError, setCalendarCreateError] = useState('');
  const [calendarCreateMessage, setCalendarCreateMessage] = useState('');
  const [calendarCreatedDetailHref, setCalendarCreatedDetailHref] = useState('');
  const [personalCreateOpen, setPersonalCreateOpen] = useState(false);
  const [personalCreateForm, setPersonalCreateForm] = useState<PersonalScheduleFormState>(() => makeEmptyPersonalScheduleForm());
  const [personalCreating, setPersonalCreating] = useState(false);
  const [personalCreateError, setPersonalCreateError] = useState('');
  const [personalCreateMessage, setPersonalCreateMessage] = useState('');
  const [personalCreatedDetailHref, setPersonalCreatedDetailHref] = useState('');
  const [calendarEditOpen, setCalendarEditOpen] = useState(false);
  const [calendarEditLoading, setCalendarEditLoading] = useState(false);
  const [calendarEditData, setCalendarEditData] = useState<ScheduleDetailData | null>(null);
  const [calendarEditForm, setCalendarEditForm] = useState<ScheduleEditFormState>(() => makeScheduleEditForm(null));
  const [calendarEditSaving, setCalendarEditSaving] = useState(false);
  const [calendarEditError, setCalendarEditError] = useState('');
  const [calendarEditMessage, setCalendarEditMessage] = useState('');
  const [personalEditOpen, setPersonalEditOpen] = useState(false);
  const [personalEditLoading, setPersonalEditLoading] = useState(false);
  const [personalEditData, setPersonalEditData] = useState<PersonalScheduleDetailData | null>(null);
  const [personalEditForm, setPersonalEditForm] = useState<PersonalScheduleFormState>(() => makeEmptyPersonalScheduleForm());
  const [personalEditSaving, setPersonalEditSaving] = useState(false);
  const [personalEditError, setPersonalEditError] = useState('');
  const [personalEditMessage, setPersonalEditMessage] = useState('');
  const [calendarDeletingKey, setCalendarDeletingKey] = useState('');
  const [calendarActionError, setCalendarActionError] = useState('');
  const [calendarActionMessage, setCalendarActionMessage] = useState('');
  const calendarCreatePanelRef = useRef<HTMLDivElement | null>(null);
  const personalCreatePanelRef = useRef<HTMLDivElement | null>(null);
  const calendarEditPanelRef = useRef<HTMLDivElement | null>(null);
  const personalEditPanelRef = useRef<HTMLDivElement | null>(null);
  const schedules = data?.schedules ?? [];
  const personalDeleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
  const days = useMemo(() => buildScheduleCalendarDays(month, schedules), [month, schedules]);
  const selectedDayItems = useMemo(
    () => schedules.filter((schedule) => schedule.date === selectedDate).sort((a, b) => `${a.time} ${a.type}`.localeCompare(`${b.time} ${b.type}`)),
    [schedules, selectedDate],
  );
  const monthLabel = new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long' }).format(parseLocalDate(`${month}-01`));
  const todayMonth = localDateInputValue().slice(0, 7);
  const showUserFilter = dataFilter === 'user';

  useGuidedPanelFocus(calendarCreateOpen, calendarCreatePanelRef, `calendar-create-${selectedDate}`);
  useGuidedPanelFocus(personalCreateOpen, personalCreatePanelRef, `personal-create-${selectedDate}`);
  useGuidedPanelFocus(calendarEditOpen, calendarEditPanelRef, `calendar-edit-${calendarEditData?.schedule?.id || 'loading'}`);
  useGuidedPanelFocus(personalEditOpen, personalEditPanelRef, `personal-edit-${personalEditData?.schedule?.id || 'loading'}`);

  useEffect(() => {
    setSelectedDate((previous) => {
      if (previous >= range.start && previous <= range.end) {
        return previous;
      }
      const firstScheduledDate = schedules.find((schedule) => schedule.date && schedule.date >= range.start && schedule.date <= range.end)?.date;
      const today = localDateInputValue();
      return firstScheduledDate || (today >= range.start && today <= range.end ? today : range.start);
    });
  }, [range.end, range.start, schedules]);

  useEffect(() => {
    setCalendarActionError('');
    setCalendarActionMessage('');
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarEditError('');
    setCalendarEditMessage('');
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalEditError('');
    setPersonalEditMessage('');
  }, [dataFilter, filterUser, month]);

  useEffect(() => {
    if (!data) {
      return;
    }
    const intent = initialIntentRef.current;
    if (intent.createHandled || (intent.create !== '1' && intent.create !== 'personal')) {
      return;
    }
    intent.createHandled = true;

    const intentDate = intent.date || selectedDate;
    if (intent.date && intent.date.slice(0, 7) !== month) {
      onMonthChange(intent.date.slice(0, 7));
    }
    setSelectedDate(intentDate);
    setCalendarActionError('');
    setCalendarActionMessage('');

    if (intent.create === 'personal') {
      setCalendarCreateOpen(false);
      setCalendarEditOpen(false);
      setPersonalEditOpen(false);
      setPersonalCreateOpen(true);
      setPersonalCreateError('');
      setPersonalCreateMessage('');
      setPersonalCreatedDetailHref('');
      setPersonalCreateForm({
        ...makeEmptyPersonalScheduleForm(intentDate),
        scheduleTime: intent.time || '09:00',
      });
      return;
    }

    setCalendarCreateOpen(true);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    setCalendarCreateForm(makeScheduleCalendarCreateForm(data, intentDate));
  }, [data, month, onMonthChange, selectedDate]);

  useEffect(() => {
    const intent = initialIntentRef.current;
    if (!intent.personalId || intent.personalHandled) {
      return;
    }
    intent.personalHandled = true;

    let alive = true;
    setCalendarCreateOpen(false);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(true);
    setPersonalEditLoading(true);
    setPersonalEditData(null);
    setPersonalEditError('');
    setPersonalEditMessage('');
    setCalendarActionError('');
    setCalendarActionMessage('');

    loadPersonalScheduleDetailData(intent.personalId).then((detail) => {
      if (!alive) {
        return;
      }
      if (detail.source !== 'django' || !detail.schedule) {
        throw new Error(detail.error || detail.message || '개인 일정 상세를 불러오지 못했습니다.');
      }
      const detailDate = detail.schedule.date || '';
      if (detailDate) {
        setSelectedDate(detailDate);
        if (detailDate.slice(0, 7) !== month) {
          onMonthChange(detailDate.slice(0, 7));
        }
      }
      setPersonalEditData(detail);
      setPersonalEditForm(makePersonalScheduleEditForm(detail.schedule));
      if (!detail.edit.canEdit) {
        setPersonalEditMessage('읽기 전용으로 개인 일정을 확인 중입니다.');
      } else if (personalDeleteRequested) {
        setPersonalEditMessage('삭제 요청으로 들어왔습니다. 아래 삭제 버튼으로 확정하세요.');
      }
    }).catch((error_) => {
      if (!alive) {
        return;
      }
      setPersonalEditData(null);
      setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 상세를 불러오지 못했습니다.');
    }).finally(() => {
      if (alive) {
        setPersonalEditLoading(false);
      }
    });

    return () => {
      alive = false;
    };
  }, [month, onMonthChange, personalDeleteRequested]);

  const openCalendarCreatePanel = () => {
    if (!data) {
      return;
    }
    setCalendarCreateForm(makeScheduleCalendarCreateForm(data, selectedDate));
    setCalendarCreateOpen(true);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    setCalendarActionError('');
    setCalendarActionMessage('');
  };

  const openPersonalCreatePanel = () => {
    if (!data) {
      return;
    }
    setPersonalCreateForm(makeEmptyPersonalScheduleForm(selectedDate));
    setPersonalCreateOpen(true);
    setCalendarCreateOpen(false);
    setCalendarEditOpen(false);
    setPersonalEditOpen(false);
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalCreatedDetailHref('');
    setCalendarActionError('');
    setCalendarActionMessage('');
  };

  const handleCalendarCreateFieldChange = (field: keyof ScheduleCreateFormState, value: string) => {
    setCalendarCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setCalendarCreateError('');
    setCalendarCreateMessage('');
  };

  const calendarCreateCustomers = data?.create.customers ?? [];
  const calendarCreateDepartments = data?.create.departments ?? [];
  const filteredCalendarCreateCustomers = customersForDepartment(calendarCreateCustomers, calendarCreateForm.departmentId);
  const calendarDepartmentHasCustomers = filteredCalendarCreateCustomers.length > 0;
  const handleCalendarDepartmentChange = (value: string) => {
    const nextCustomers = customersForDepartment(calendarCreateCustomers, value);
    handleCalendarCreateFieldChange('departmentId', value);
    handleCalendarCreateFieldChange('followupId', nextCustomers[0]?.id ? String(nextCustomers[0].id) : '');
  };
  const handleCalendarCustomerChange = (value: string) => {
    const nextCustomer = calendarCreateCustomers.find((customer) => String(customer.id) === value);
    if (nextCustomer?.departmentId) {
      handleCalendarCreateFieldChange('departmentId', String(nextCustomer.departmentId));
    }
    handleCalendarCreateFieldChange('followupId', value);
  };

  const handlePersonalCreateFieldChange = (field: keyof PersonalScheduleFormState, value: string) => {
    setPersonalCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setPersonalCreateError('');
    setPersonalCreateMessage('');
  };

  const handleCalendarCreateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || calendarCreating) {
      return;
    }
    if (!data.create.canCreate) {
      setCalendarCreateError(data.create.message || '일정 등록 권한이 없습니다.');
      return;
    }
    const { payload, error } = scheduleCreateFormToPayload(calendarCreateForm);
    if (!payload) {
      setCalendarCreateError(error || '일정 등록 정보를 확인하세요.');
      return;
    }

    setCalendarCreating(true);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    try {
      const created = await createCustomerSchedule(payload, data.create.submitUrl);
      await onRefresh();
      setCalendarCreateMessage(created.message || '일정을 등록했습니다.');
      setCalendarCreatedDetailHref(created.href || '');
      setCalendarCreateForm(makeScheduleCalendarCreateForm(data, calendarCreateForm.visitDate || selectedDate));
    } catch (error_) {
      setCalendarCreateError(error_ instanceof Error ? error_.message : '일정 등록에 실패했습니다.');
    } finally {
      setCalendarCreating(false);
    }
  };

  const handlePersonalCreateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || personalCreating) {
      return;
    }
    const createConfig = data.create.personalSchedule;
    if (!createConfig?.canCreate) {
      setPersonalCreateError(createConfig?.message || '개인 일정 등록 권한이 없습니다.');
      return;
    }
    const { payload, error } = personalScheduleFormToPayload(personalCreateForm);
    if (!payload) {
      setPersonalCreateError(error || '개인 일정 등록 정보를 확인하세요.');
      return;
    }

    setPersonalCreating(true);
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalCreatedDetailHref('');
    try {
      const created = await createPersonalSchedule(payload, createConfig.submitUrl);
      await onRefresh();
      setPersonalCreateMessage(created.message || '개인 일정을 등록했습니다.');
      setPersonalCreatedDetailHref(created.href || created.schedule?.href || '');
      setPersonalCreateForm(makeEmptyPersonalScheduleForm(personalCreateForm.scheduleDate || selectedDate));
    } catch (error_) {
      setPersonalCreateError(error_ instanceof Error ? error_.message : '개인 일정 등록에 실패했습니다.');
    } finally {
      setPersonalCreating(false);
    }
  };

  const handleCalendarEditFieldChange = (field: keyof ScheduleEditFormState, value: string | boolean) => {
    setCalendarEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setCalendarEditError('');
    setCalendarEditMessage('');
  };

  const handlePersonalEditFieldChange = (field: keyof PersonalScheduleFormState, value: string) => {
    setPersonalEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setPersonalEditError('');
    setPersonalEditMessage('');
  };

  const handleCalendarEditOpen = async (schedule: ScheduleItem) => {
    if (calendarEditLoading || calendarEditSaving || personalEditLoading || personalEditSaving) {
      return;
    }
    if (schedule.type === 'personal') {
      if (!schedule.canEdit) {
        setCalendarActionError('이 개인 일정의 수정 권한이 없습니다.');
        setCalendarActionMessage('');
        return;
      }

      setCalendarCreateOpen(false);
      setCalendarEditOpen(false);
      setPersonalCreateOpen(false);
      setPersonalEditOpen(true);
      setPersonalEditLoading(true);
      setPersonalEditData(null);
      setPersonalEditError('');
      setPersonalEditMessage('');
      setCalendarActionError('');
      setCalendarActionMessage('');
      try {
        const detail = await loadPersonalScheduleDetailData(schedule.id);
        if (detail.source !== 'django' || !detail.schedule) {
          throw new Error(detail.error || detail.message || '개인 일정 상세를 불러오지 못했습니다.');
        }
        if (!detail.edit.canEdit) {
          throw new Error(detail.edit.message || '수정 권한이 없습니다.');
        }
        setPersonalEditData(detail);
        setPersonalEditForm(makePersonalScheduleEditForm(detail.schedule));
      } catch (error_) {
        setPersonalEditData(null);
        setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 상세를 불러오지 못했습니다.');
      } finally {
        setPersonalEditLoading(false);
      }
      return;
    }
    if (schedule.type !== 'customer' || !schedule.canEdit) {
      setCalendarActionError('이 일정의 수정 권한이 없습니다.');
      setCalendarActionMessage('');
      return;
    }

    setCalendarCreateOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarEditOpen(true);
    setCalendarEditLoading(true);
    setCalendarEditData(null);
    setCalendarEditError('');
    setCalendarEditMessage('');
    setCalendarActionError('');
    setCalendarActionMessage('');
    try {
      const detail = await loadScheduleDetailData(schedule.id);
      if (detail.source !== 'django' || !detail.schedule) {
        throw new Error(detail.error || detail.message || '일정 상세를 불러오지 못했습니다.');
      }
      if (!detail.edit.canEdit) {
        throw new Error(detail.edit.message || '수정 권한이 없습니다.');
      }
      setCalendarEditData(detail);
      setCalendarEditForm(makeScheduleEditForm(detail.schedule));
    } catch (error_) {
      setCalendarEditData(null);
      setCalendarEditError(error_ instanceof Error ? error_.message : '일정 상세를 불러오지 못했습니다.');
    } finally {
      setCalendarEditLoading(false);
    }
  };

  const handleCalendarEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!calendarEditData?.edit || calendarEditSaving) {
      return;
    }
    if (!calendarEditData.edit.canEdit || !calendarEditData.edit.submitUrl) {
      setCalendarEditError(calendarEditData.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const { payload, error } = scheduleEditFormToPayload(calendarEditForm);
    if (!payload) {
      setCalendarEditError(error || '일정 수정 정보를 확인하세요.');
      return;
    }

    setCalendarEditSaving(true);
    setCalendarEditError('');
    setCalendarEditMessage('');
    try {
      const updated = await updateCustomerSchedule(payload, calendarEditData.edit.submitUrl);
      await onRefresh();
      setCalendarEditData(updated);
      setCalendarEditForm(makeScheduleEditForm(updated.schedule));
      setCalendarEditMessage(updated.message || '일정을 수정했습니다.');
      setCalendarEditOpen(false);
    } catch (error_) {
      setCalendarEditError(error_ instanceof Error ? error_.message : '일정 수정에 실패했습니다.');
    } finally {
      setCalendarEditSaving(false);
    }
  };

  const handlePersonalEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!personalEditData?.edit || personalEditSaving) {
      return;
    }
    if (!personalEditData.edit.canEdit || !personalEditData.edit.submitUrl) {
      setPersonalEditError(personalEditData.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const { payload, error } = personalScheduleFormToPayload(personalEditForm);
    if (!payload) {
      setPersonalEditError(error || '개인 일정 수정 정보를 확인하세요.');
      return;
    }

    setPersonalEditSaving(true);
    setPersonalEditError('');
    setPersonalEditMessage('');
    try {
      const updated = await updatePersonalSchedule(payload, personalEditData.edit.submitUrl);
      await onRefresh();
      setPersonalEditData(updated);
      setPersonalEditForm(makePersonalScheduleEditForm(updated.schedule));
      setPersonalEditMessage(updated.message || '개인 일정을 수정했습니다.');
      setPersonalEditOpen(false);
    } catch (error_) {
      setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 수정에 실패했습니다.');
    } finally {
      setPersonalEditSaving(false);
    }
  };

  const handleCalendarDelete = async (schedule: ScheduleItem) => {
    if (calendarDeletingKey) {
      return;
    }
    if (!schedule.canEdit || !schedule.deleteHref) {
      setCalendarActionError('이 일정의 삭제 권한이 없습니다.');
      setCalendarActionMessage('');
      return;
    }
    const confirmMessage = schedule.type === 'personal'
      ? [
        '이 개인 일정을 삭제할까요?',
        '',
        `제목: ${schedule.title || '제목 없음'}`,
        `날짜: ${schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}`,
        '',
        '관련 메모도 함께 삭제되며 복구할 수 없습니다.',
      ].join('\n')
      : [
        '이 일정을 삭제할까요?',
        '',
        `고객: ${schedule.customer || '고객명 미정'}`,
        `날짜: ${schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}`,
        '',
        '관련 활동 기록도 함께 삭제되며 복구할 수 없습니다.',
      ].join('\n');
    if (!window.confirm(confirmMessage)) {
      return;
    }

    const itemKey = `${schedule.type}-${schedule.id}`;
    setCalendarDeletingKey(itemKey);
    setCalendarActionError('');
    setCalendarActionMessage('');
    try {
      const result = await deleteSchedule(schedule.deleteHref);
      await onRefresh();
      if (schedule.type === 'customer' && calendarEditData?.schedule?.id === schedule.id) {
        setCalendarEditOpen(false);
        setCalendarEditData(null);
      }
      if (schedule.type === 'personal' && personalEditData?.schedule?.id === schedule.id) {
        setPersonalEditOpen(false);
        setPersonalEditData(null);
      }
      if (schedule.type === 'personal') {
        setPersonalCreateOpen(false);
        setPersonalCreateMessage('');
        setPersonalCreatedDetailHref('');
        setPersonalEditOpen(false);
        setPersonalEditData(null);
        setPersonalEditError('');
        setPersonalEditMessage('');
      }
      setCalendarActionMessage(result.message || '일정을 삭제했습니다.');
    } catch (error_) {
      setCalendarActionError(error_ instanceof Error ? error_.message : '일정 삭제에 실패했습니다.');
    } finally {
      setCalendarDeletingKey('');
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 캘린더를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '월간 일정', value: `${formatNumber(data.metrics.totalSchedules)}건`, detail: data.scope.label || '범위', icon: CalendarDays, tone: 'blue' as const },
    { label: '고객 일정', value: `${formatNumber(data.metrics.customerSchedules)}건`, detail: '방문/견적/납품', icon: Users, tone: 'green' as const },
    { label: '개인 일정', value: `${formatNumber(data.metrics.personalSchedules)}건`, detail: '일반 업무', icon: Clock, tone: 'teal' as const },
    { label: '완료', value: `${formatNumber(data.metrics.completedSchedules)}건`, detail: '고객 일정 기준', icon: CheckCircle2, tone: 'amber' as const },
    { label: '지연', value: `${formatNumber(data.metrics.overdueSchedules)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: 'red' as const },
  ];
  const personalScheduleCreateConfig = data.create.personalSchedule;

  return (
    <section className="schedules-page schedule-calendar-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>일정 캘린더 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band schedule-calendar-summary">
        <div>
          <span className="eyebrow">Schedule Calendar</span>
          <h2>{monthLabel}</h2>
          <p>{data.scope.label || '내 일정'} 기준으로 고객 일정과 개인 일정을 월간 캘린더에서 확인합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.schedules}>
            목록
          </a>
          <button
            className={data.create.canCreate ? 'route-primary-action' : 'route-secondary-action'}
            onClick={openCalendarCreatePanel}
            type="button"
          >
            {data.create.canCreate ? '일정 등록' : '등록 권한 없음'}
            <Plus size={16} />
          </button>
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="월간 일정 지표">
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

      <div className="schedule-calendar-toolbar">
        <div className="schedule-calendar-month-controls">
          <button aria-label="이전 달" onClick={() => onMonthChange(shiftScheduleCalendarMonth(month, -1))} type="button">
            <ChevronLeft size={17} />
          </button>
          <button onClick={() => onMonthChange(todayMonth)} type="button">오늘</button>
          <button aria-label="다음 달" onClick={() => onMonthChange(shiftScheduleCalendarMonth(month, 1))} type="button">
            <ChevronRight size={17} />
          </button>
          <strong>{monthLabel}</strong>
          {loading ? <Loader2 className="spin-icon" size={16} /> : null}
        </div>
        <div className="schedule-calendar-filters">
          <select onChange={(event) => onDataFilterChange(event.target.value)} value={dataFilter}>
            {data.options.dataFilters.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          {showUserFilter ? (
            <select onChange={(event) => onFilterUserChange(event.target.value)} value={filterUser}>
              <option value="">직원 선택</option>
              {data.options.users.map((user) => (
                <option key={user.id} value={user.id}>{user.name}{user.isCurrent ? ' (나)' : ''}</option>
              ))}
            </select>
          ) : null}
        </div>
      </div>

      <div className="schedule-calendar-layout">
        <section className="dashboard-panel schedule-calendar-grid-panel">
          <div className="schedule-calendar-weekdays" aria-hidden="true">
            {['월', '화', '수', '목', '금', '토', '일'].map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="schedule-calendar-grid" role="grid" aria-label={`${monthLabel} 일정 캘린더`}>
            {days.map((day) => (
              <button
                className={[
                  'schedule-calendar-day',
                  day.inMonth ? '' : 'muted',
                  day.isToday ? 'today' : '',
                  selectedDate === day.date ? 'selected' : '',
                ].filter(Boolean).join(' ')}
                key={day.date}
                onClick={() => setSelectedDate(day.date)}
                type="button"
              >
                <span className="schedule-calendar-date-number">{day.dayNumber}</span>
                <div className="schedule-calendar-events">
                  {day.schedules.slice(0, 4).map((schedule) => (
                    <span className={`schedule-calendar-event ${schedule.type} ${schedule.status}`} key={`${schedule.type}-${schedule.id}`}>
                      {schedule.time ? `${schedule.time} ` : ''}{schedule.company || schedule.title || schedule.customer}
                    </span>
                  ))}
                  {day.schedules.length > 4 ? <span className="schedule-calendar-more">+{day.schedules.length - 4}</span> : null}
                </div>
              </button>
            ))}
          </div>
        </section>

        <aside className="dashboard-panel schedule-calendar-day-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Selected day</span>
              <h2>{formatDateLabel(selectedDate)}</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          {statusError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{statusError}</span></div> : null}
          {statusMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{statusMessage}</span></div> : null}
          {calendarActionError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarActionError}</span></div> : null}
          {calendarActionMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{calendarActionMessage}</span></div> : null}
          <ScheduleCalendarSelectedList
            deletingKey={calendarDeletingKey}
            items={selectedDayItems}
            onDelete={handleCalendarDelete}
            onEdit={handleCalendarEditOpen}
            onStatusChange={onStatusChange}
            statusUpdatingKey={statusUpdatingKey}
          />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Actions</span>
              <h2>일정 작업</h2>
            </div>
            <Plus size={18} />
          </div>
          <div className="customers-side-actions">
            <button onClick={openCalendarCreatePanel} type="button">고객 일정 등록</button>
            {personalScheduleCreateConfig?.canCreate ? (
              <button onClick={openPersonalCreatePanel} type="button">
                개인 일정 등록
              </button>
            ) : null}
            <a href={data.links.schedules}>일정 목록</a>
          </div>

          {calendarCreateOpen || calendarCreateError || calendarCreateMessage ? (
            <div className="schedule-calendar-inline-editor" ref={calendarCreatePanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Quick schedule</span>
                  <h3>고객 일정 등록</h3>
                </div>
                <button aria-label="등록 패널 닫기" onClick={() => setCalendarCreateOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {calendarCreateError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarCreateError}</span></div> : null}
              {calendarCreateMessage ? (
                <div className="dashboard-api-alert compact success">
                  <CheckCircle2 size={16} />
                  <span>{calendarCreateMessage}</span>
                  {calendarCreatedDetailHref ? <a href={calendarCreatedDetailHref}>상세</a> : null}
                </div>
              ) : null}
              {!data.create.canCreate ? (
                <DashboardEmpty label={data.create.message || '일정 등록 권한이 없습니다'} />
              ) : (data.create.departments ?? []).length === 0 && data.create.customers.length === 0 ? (
                <DashboardEmpty label="등록 가능한 부서/연구실이 없습니다" />
              ) : data.create.activityTypes.length === 0 ? (
                <DashboardEmpty label="등록 가능한 일정 유형이 없습니다" />
              ) : calendarCreateOpen ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handleCalendarCreateSubmit}>
                  <div className="notes-create-grid schedules-create-grid">
                    <div className="form-field">
                      <span>부서/연구실</span>
                      <SearchableSelect
                        ariaLabel="부서/연구실 선택"
                        onChange={handleCalendarDepartmentChange}
                        options={calendarCreateDepartments.map(makeDepartmentSelectOption)}
                        placeholder="회사, 부서/연구실, 담당자 검색"
                        value={calendarCreateForm.departmentId}
                      />
                    </div>
                    <div className="form-field">
                      <span>고객</span>
                      <SearchableSelect
                        allowEmpty={!calendarDepartmentHasCustomers}
                        ariaLabel="고객 선택"
                        disabled={!calendarDepartmentHasCustomers}
                        emptyLabel="부서에만 연결"
                        onChange={handleCalendarCustomerChange}
                        options={filteredCalendarCreateCustomers.map(makeCustomerSelectOption)}
                        placeholder="고객, 회사, 부서 검색"
                        value={calendarCreateForm.followupId}
                      />
                    </div>
                    <label>
                      <span>일정 유형</span>
                      <select
                        onChange={(event) => handleCalendarCreateFieldChange('activityType', event.target.value)}
                        required
                        value={calendarCreateForm.activityType}
                      >
                        {data.create.activityTypes.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>일정 날짜</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarCreateForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>일정 시간</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('visitTime', event.target.value)}
                        required
                        type="time"
                        value={calendarCreateForm.visitTime}
                      />
                    </label>
                    <label>
                      <span>장소</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('location', event.target.value)}
                        placeholder="방문 장소"
                        value={calendarCreateForm.location}
                      />
                    </label>
                    <label>
                      <span>예상 매출</span>
                      <input
                        inputMode="numeric"
                        min="0"
                        onChange={(event) => handleCalendarCreateFieldChange('expectedRevenue', event.target.value)}
                        placeholder="원"
                        type="number"
                        value={calendarCreateForm.expectedRevenue}
                      />
                    </label>
                    <label>
                      <span>성공 확률</span>
                      <input
                        inputMode="numeric"
                        max="100"
                        min="0"
                        step="5"
                        required={isQuoteProbabilityRequired(calendarCreateForm.activityType)}
                        onBlur={(event) => handleCalendarCreateFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
                        onChange={(event) => handleCalendarCreateFieldChange('probability', event.target.value)}
                        placeholder="0-100, 5% 단위"
                        type="number"
                        value={calendarCreateForm.probability}
                      />
                    </label>
                  </div>
                  <label>
                    <span>일정 내용</span>
                    <textarea
                      onChange={(event) => handleCalendarCreateFieldChange('notes', event.target.value)}
                      rows={3}
                      value={calendarCreateForm.notes}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={appendDateQuery(data.links.createSchedule, calendarCreateForm.visitDate || selectedDate)}>
                      상세 등록
                      <MoveUpRight size={15} />
                    </a>
                    <button className="route-primary-action" disabled={calendarCreating} type="submit">
                      {calendarCreating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {personalCreateOpen || personalCreateError || personalCreateMessage ? (
            <div className="schedule-calendar-inline-editor" ref={personalCreatePanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Personal schedule</span>
                  <h3>개인 일정 등록</h3>
                </div>
                <button aria-label="개인 일정 등록 패널 닫기" onClick={() => setPersonalCreateOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {personalCreateError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{personalCreateError}</span></div> : null}
              {personalCreateMessage ? (
                <div className="dashboard-api-alert compact success">
                  <CheckCircle2 size={16} />
                  <span>{personalCreateMessage}</span>
                  {personalCreatedDetailHref ? <a href={personalCreatedDetailHref}>상세</a> : null}
                </div>
              ) : null}
              {!personalScheduleCreateConfig?.canCreate ? (
                <DashboardEmpty label={personalScheduleCreateConfig?.message || '개인 일정 등록 권한이 없습니다'} />
              ) : personalCreateOpen ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handlePersonalCreateSubmit}>
                  <label>
                    <span>일정 제목</span>
                    <input
                      onChange={(event) => handlePersonalCreateFieldChange('title', event.target.value)}
                      required
                      value={personalCreateForm.title}
                    />
                  </label>
                  <div className="notes-create-grid schedules-create-grid">
                    <label>
                      <span>날짜</span>
                      <input
                        onChange={(event) => handlePersonalCreateFieldChange('scheduleDate', event.target.value)}
                        required
                        type="date"
                        value={personalCreateForm.scheduleDate}
                      />
                    </label>
                    <label>
                      <span>시간</span>
                      <input
                        onChange={(event) => handlePersonalCreateFieldChange('scheduleTime', event.target.value)}
                        required
                        type="time"
                        value={personalCreateForm.scheduleTime}
                      />
                    </label>
                  </div>
                  <label>
                    <span>내용</span>
                    <textarea
                      onChange={(event) => handlePersonalCreateFieldChange('content', event.target.value)}
                      rows={3}
                      value={personalCreateForm.content}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <button className="route-primary-action" disabled={personalCreating} type="submit">
                      {personalCreating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {calendarEditOpen || calendarEditError || calendarEditMessage ? (
            <div className="schedule-calendar-inline-editor" ref={calendarEditPanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Edit schedule</span>
                  <h3>일정 수정</h3>
                </div>
                <button aria-label="수정 패널 닫기" onClick={() => setCalendarEditOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {calendarEditError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarEditError}</span></div> : null}
              {calendarEditMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{calendarEditMessage}</span></div> : null}
              {calendarEditLoading ? (
                <div className="schedule-calendar-editor-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>일정 상세를 불러오는 중입니다</span>
                </div>
              ) : calendarEditOpen && calendarEditData?.schedule && calendarEditData.edit.canEdit ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handleCalendarEditSubmit}>
                  <div className="notes-create-grid schedules-create-grid">
                    <div className="form-field">
                      <span>고객</span>
                      <SearchableSelect
                        ariaLabel="고객 선택"
                        onChange={(nextValue) => handleCalendarEditFieldChange('followupId', nextValue)}
                        options={calendarEditData.edit.customers.map(makeCustomerSelectOption)}
                        placeholder="고객, 회사, 부서 검색"
                        value={calendarEditForm.followupId}
                      />
                    </div>
                    <label>
                      <span>일정 유형</span>
                      <select
                        onChange={(event) => handleCalendarEditFieldChange('activityType', event.target.value)}
                        required
                        value={calendarEditForm.activityType}
                      >
                        {calendarEditData.edit.activityTypes.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>상태</span>
                      <select
                        onChange={(event) => handleCalendarEditFieldChange('status', event.target.value)}
                        required
                        value={calendarEditForm.status}
                      >
                        {calendarEditData.edit.statuses.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>일정 날짜</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarEditForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>일정 시간</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('visitTime', event.target.value)}
                        required
                        type="time"
                        value={calendarEditForm.visitTime}
                      />
                    </label>
                    <label>
                      <span>장소</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('location', event.target.value)}
                        value={calendarEditForm.location}
                      />
                    </label>
                    <label>
                      <span>예상 매출</span>
                      <input
                        inputMode="numeric"
                        min="0"
                        onChange={(event) => handleCalendarEditFieldChange('expectedRevenue', event.target.value)}
                        type="number"
                        value={calendarEditForm.expectedRevenue}
                      />
                    </label>
                    <label>
                      <span>성공 확률</span>
                      <input
                        inputMode="numeric"
                        max="100"
                        min="0"
                        step="5"
                        required={isQuoteProbabilityRequired(calendarEditForm.activityType)}
                        onBlur={(event) => handleCalendarEditFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
                        onChange={(event) => handleCalendarEditFieldChange('probability', event.target.value)}
                        type="number"
                        value={calendarEditForm.probability}
                      />
                    </label>
                    <label>
                      <span>예상 종료일</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('expectedCloseDate', event.target.value)}
                        type="date"
                        value={calendarEditForm.expectedCloseDate}
                      />
                    </label>
                  </div>
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={calendarEditForm.purchaseConfirmed}
                      onChange={(event) => handleCalendarEditFieldChange('purchaseConfirmed', event.target.checked)}
                      type="checkbox"
                    />
                    <span>구매 확정</span>
                  </label>
                  <label>
                    <span>일정 내용</span>
                    <textarea
                      onChange={(event) => handleCalendarEditFieldChange('notes', event.target.value)}
                      rows={3}
                      value={calendarEditForm.notes}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={calendarEditData.schedule.href}>
                      상세
                    </a>
                    <button className="route-primary-action" disabled={calendarEditSaving} type="submit">
                      {calendarEditSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {personalEditOpen || personalEditError || personalEditMessage ? (
            <div className="schedule-calendar-inline-editor" ref={personalEditPanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Edit personal</span>
                  <h3>개인 일정 수정</h3>
                </div>
                <button aria-label="개인 일정 수정 패널 닫기" onClick={() => setPersonalEditOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {personalEditError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{personalEditError}</span></div> : null}
              {personalEditMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{personalEditMessage}</span></div> : null}
              {personalEditLoading ? (
                <div className="schedule-calendar-editor-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>개인 일정 상세를 불러오는 중입니다</span>
                </div>
              ) : personalEditOpen && personalEditData?.schedule && personalEditData.edit.canEdit ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handlePersonalEditSubmit}>
                  <label>
                    <span>일정 제목</span>
                    <input
                      onChange={(event) => handlePersonalEditFieldChange('title', event.target.value)}
                      required
                      value={personalEditForm.title}
                    />
                  </label>
                  <div className="notes-create-grid schedules-create-grid">
                    <label>
                      <span>날짜</span>
                      <input
                        onChange={(event) => handlePersonalEditFieldChange('scheduleDate', event.target.value)}
                        required
                        type="date"
                        value={personalEditForm.scheduleDate}
                      />
                    </label>
                    <label>
                      <span>시간</span>
                      <input
                        onChange={(event) => handlePersonalEditFieldChange('scheduleTime', event.target.value)}
                        required
                        type="time"
                        value={personalEditForm.scheduleTime}
                      />
                    </label>
                  </div>
                  <label>
                    <span>내용</span>
                    <textarea
                      onChange={(event) => handlePersonalEditFieldChange('content', event.target.value)}
                      rows={3}
                      value={personalEditForm.content}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={personalEditData.schedule.href}>
                      상세
                    </a>
                    {personalEditData.links.deleteSchedule ? (
                      <button
                        className="route-secondary-action danger"
                        disabled={calendarDeletingKey === `personal-${personalEditData.schedule.id}`}
                        onClick={() => personalEditData.schedule && handleCalendarDelete(personalEditData.schedule)}
                        type="button"
                      >
                        {calendarDeletingKey === `personal-${personalEditData.schedule.id}` ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
                        삭제
                      </button>
                    ) : null}
                    <button className="route-primary-action" disabled={personalEditSaving} type="submit">
                      {personalEditSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : personalEditOpen && personalEditData?.schedule ? (
                <div className="schedule-calendar-readonly-detail">
                  <dl>
                    <div>
                      <dt>제목</dt>
                      <dd>{personalEditData.schedule.title || '제목 없음'}</dd>
                    </div>
                    <div>
                      <dt>담당자</dt>
                      <dd>{personalEditData.schedule.owner || '-'}</dd>
                    </div>
                    <div>
                      <dt>날짜</dt>
                      <dd>{personalEditData.schedule.date ? formatDateLabel(personalEditData.schedule.date) : '-'}</dd>
                    </div>
                    <div>
                      <dt>시간</dt>
                      <dd>{personalEditData.schedule.time || '-'}</dd>
                    </div>
                  </dl>
                  <p>{personalEditData.schedule.notesFull || personalEditData.schedule.notes || '내용이 없습니다.'}</p>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={personalEditData.links.calendar || '/schedules/calendar/'}>
                      캘린더
                    </a>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}

const scheduleDocumentVariableBuckets: Array<{ label: string; keys: string[] }> = [
  { label: '기본 정보', keys: ['년', '월', '일', '거래번호', '일정날짜', '날짜', '발행일'] },
  { label: '고객 정보', keys: ['고객명', '업체명', '학교명', '부서명', '연구실', '담당자', '이메일', '담당자이메일', '연락처', '전화번호'] },
  { label: '영업 담당', keys: ['실무자', '영업담당자', '담당영업', '영업담당자이메일'] },
  { label: '견적 정보', keys: ['견적번호', '메모', '기타사항', '견적기타사항'] },
  { label: '회사 정보', keys: ['회사명'] },
  { label: '금액', keys: ['공급가액', '소계', '부가세액', '부가세', '총액', '합계', '총액한글', '한글금액'] },
];

const isScheduleDocumentEmptyValue = (value: ScheduleDocumentPreviewData['variables'][string]) => (
  value === null || value === undefined || String(value).trim() === ''
);

const formatScheduleDocumentValue = (value: ScheduleDocumentPreviewData['variables'][string]) => {
  if (isScheduleDocumentEmptyValue(value)) {
    return '미입력';
  }
  return typeof value === 'number' ? formatNumber(value) : String(value);
};

function buildScheduleDocumentVariableGroups(variables: ScheduleDocumentPreviewData['variables']) {
  const usedKeys = new Set<string>();
  const groups = scheduleDocumentVariableBuckets.map((bucket) => {
    const entries = bucket.keys
      .filter((key) => Object.prototype.hasOwnProperty.call(variables, key))
      .map((key) => {
        usedKeys.add(key);
        return [key, variables[key]] as const;
      });
    return { label: bucket.label, entries };
  }).filter((group) => group.entries.length > 0);

  const itemEntries: Array<readonly [string, ScheduleDocumentPreviewData['variables'][string]]> = [];
  const otherEntries: Array<readonly [string, ScheduleDocumentPreviewData['variables'][string]]> = [];
  Object.entries(variables).forEach(([key, value]) => {
    if (usedKeys.has(key)) {
      return;
    }
    if (/^품목\d+_/.test(key)) {
      itemEntries.push([key, value]);
    } else {
      otherEntries.push([key, value]);
    }
  });

  if (itemEntries.length > 0) {
    groups.push({ label: '품목 변수', entries: itemEntries });
  }
  if (otherEntries.length > 0) {
    groups.push({ label: '기타 변수', entries: otherEntries });
  }
  return groups;
}

function saveDownloadedBlob(blob: Blob, filename: string) {
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}

function scheduleDocumentDownloadKey(
  action: ScheduleDocumentAction,
  formatAction: ScheduleDocumentFormatAction,
  options?: ScheduleDocumentRequestOptions,
) {
  return [
    action.type,
    formatAction.format,
    formatAction.href,
    options?.hideBaseUnitPrice ? 'hide-base-unit-price' : 'show-base-unit-price',
  ].join('-');
}

function commercialCheckStatusClass(status?: string) {
  if (status === 'warning' || status === 'error') return 'warning';
  if (status === 'ok') return 'ok';
  return 'info';
}

function ScheduleCommercialChecksPanel({ checks }: { checks?: ScheduleDetailData['commercialChecks'] }) {
  if (!checks?.applies) {
    return null;
  }

  const statusClass = commercialCheckStatusClass(checks.status);
  const isQuote = checks.kind === 'quote';
  const isDelivery = checks.kind === 'delivery';
  const autoAttachLabel = isDelivery
    ? checks.delivery.autoAttachLabel || checks.documents.autoAttachLabel
    : checks.summary.autoAttachReady
      ? checks.documents.autoAttachLabel
      : '메일 자동첨부 후보 없음';
  const metrics = isQuote
    ? [
      { label: '견적 품목', value: `${formatNumber(checks.summary.quoteItemCount)}개` },
      { label: '견적 금액', value: formatWon(checks.summary.quoteAmount) },
      { label: '납품 반영', value: formatWon(checks.summary.deliveredAmount) },
      { label: '미납 잔액', value: formatWon(checks.summary.remainingAmount) },
    ]
    : [
      { label: '납품 품목', value: `${formatNumber(checks.summary.deliveryItemCount)}개` },
      { label: '납품 금액', value: formatWon(checks.summary.deliveryAmount) },
      { label: '원본 견적', value: `${formatNumber(checks.delivery.sourceQuoteCount)}건` },
      { label: '등록 서류', value: `${formatNumber(checks.summary.registeredDocumentCount)}개` },
    ];

  return (
    <section className={`schedule-commercial-panel ${statusClass}`} aria-label="견적 납품 정합성">
      <div className="schedule-commercial-heading">
        <div>
          <span className="eyebrow">Commercial check</span>
          <h3 className="customer-detail-section-heading">견적/납품 정합성</h3>
        </div>
        <span className={`schedule-commercial-status ${statusClass}`}>
          {statusClass === 'warning' ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
          {checks.statusLabel}
        </span>
      </div>

      <div className="schedule-commercial-metrics">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      {autoAttachLabel ? (
        <div className={`schedule-commercial-auto ${checks.summary.autoAttachReady ? 'ok' : 'warning'}`}>
          <FileText size={15} />
          <span>{autoAttachLabel}</span>
        </div>
      ) : null}

      {isQuote && checks.quoteGroups.length > 0 ? (
        <div className="schedule-commercial-group-list">
          {checks.quoteGroups.map((group) => (
            <div className={`schedule-commercial-group ${commercialCheckStatusClass(group.status)}`} key={group.quoteGroup || 'default'}>
              <div>
                <strong>{group.quoteGroupLabel}</strong>
                <span>{[
                  `${formatNumber(group.itemCount)}개 품목`,
                  group.fulfillmentLabel,
                  group.autoAttachLabel,
                ].filter(Boolean).join(' · ')}</span>
              </div>
              <dl>
                <div>
                  <dt>견적</dt>
                  <dd>{formatWon(group.quoteAmount)}</dd>
                </div>
                <div>
                  <dt>납품</dt>
                  <dd>{formatWon(group.deliveredAmount)}</dd>
                </div>
                <div>
                  <dt>잔여</dt>
                  <dd>{formatWon(group.remainingAmount)}</dd>
                </div>
                <div>
                  <dt>등록</dt>
                  <dd>{formatNumber(group.registeredQuotationCount)}개</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      ) : null}

      {isDelivery && checks.delivery.sourceQuotes.length > 0 ? (
        <div className="schedule-commercial-source-list">
          <h4>연결된 원본 견적</h4>
          {checks.delivery.sourceQuotes.map((source) => (
            <div key={`${source.sourceQuoteScheduleId}-${source.quoteGroup}`}>
              <span>{[
                `일정 #${source.sourceQuoteScheduleId}`,
                source.quoteGroupLabel,
                `${formatNumber(source.itemCount)}개 품목`,
              ].filter(Boolean).join(' · ')}</span>
              <strong>{formatWon(source.amount)}</strong>
            </div>
          ))}
        </div>
      ) : null}

      {checks.delivery.historyAmountMismatches.length > 0 ? (
        <div className="schedule-commercial-source-list warning">
          <h4>납품 노트 금액</h4>
          {checks.delivery.historyAmountMismatches.slice(0, 3).map((mismatch) => (
            <div key={mismatch.historyId}>
              <span>{mismatch.createdAt ? formatDateTimeLabel(mismatch.createdAt) : `보고 #${mismatch.historyId}`}</span>
              <strong>{formatWon(mismatch.noteAmount)} / {formatWon(mismatch.itemAmount)}</strong>
            </div>
          ))}
        </div>
      ) : null}

      {checks.warnings.length > 0 ? (
        <div className="schedule-commercial-warning-list">
          {checks.warnings.map((warning, index) => (
            <div key={`${warning.code}-${index}`}>
              <AlertTriangle size={14} />
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="schedule-commercial-auto ok">
          <CheckCircle2 size={15} />
          <span>현재 확인된 정합성 경고가 없습니다.</span>
        </div>
      )}
    </section>
  );
}

function ScheduleDocumentsPanel({
  documents,
  deletingDocumentKey,
  downloadingKey,
  previewAction,
  previewData,
  previewError,
  previewLoading,
  onClosePreview,
  onDelete,
  onDownload,
  onPreview,
}: {
  documents: ScheduleDetailData['documents'];
  deletingDocumentKey: string;
  downloadingKey: string;
  previewAction: ScheduleDocumentAction | null;
  previewData: ScheduleDocumentPreviewData | null;
  previewError: string;
  previewLoading: boolean;
  onClosePreview: () => void;
  onDelete: (document: ScheduleGeneratedDocument) => void;
  onDownload: (action: ScheduleDocumentAction, formatAction: ScheduleDocumentFormatAction, options?: ScheduleDocumentRequestOptions) => void;
  onPreview: (action: ScheduleDocumentAction, options?: ScheduleDocumentRequestOptions) => void;
}) {
  const [hideBaseUnitPriceByAction, setHideBaseUnitPriceByAction] = useState<Record<string, boolean>>({});
  const registeredDocuments = documents.registeredDocuments.length > 0
    ? documents.registeredDocuments
    : documents.registeredQuotations;

  if (!documents.items.length && !registeredDocuments.length) {
    return null;
  }

  const variableGroups = previewData ? buildScheduleDocumentVariableGroups(previewData.variables) : [];

  return (
    <section className="schedule-documents-panel" aria-label="서류 다운로드">
      <div className="schedule-file-heading schedule-document-heading">
        <h3 className="customer-detail-section-heading">서류 다운로드</h3>
        <a className="customer-row-action schedule-document-template-link" href={documents.templateManagerHref}>
          <FileText size={14} />
          <span>템플릿</span>
        </a>
      </div>
      <div className="schedule-document-list">
        {documents.items.map((action) => {
          const hasTemplate = action.templateCount > 0;
          const actionListKey = `${action.type}-${action.quoteGroup ?? ''}-${action.previewHref}`;
          const supportsHideBaseUnitPrice = action.type === 'quotation';
          const hideBaseUnitPrice = supportsHideBaseUnitPrice && Boolean(hideBaseUnitPriceByAction[actionListKey]);
          const documentOptions = hideBaseUnitPrice ? { hideBaseUnitPrice: true } : undefined;
          return (
            <div className="schedule-document-card" key={actionListKey}>
              <div className="schedule-document-card-main">
                <div>
                  <strong>{action.label}</strong>
                  <span>{action.description}</span>
                </div>
                <span className={hasTemplate ? 'schedule-document-template-count' : 'schedule-document-template-count empty'}>
                  {hasTemplate ? `${formatNumber(action.templateCount)}개 템플릿` : '템플릿 없음'}
                </span>
              </div>
              {supportsHideBaseUnitPrice ? (
                <label className="schedule-document-option-check">
                  <input
                    checked={hideBaseUnitPrice}
                    onChange={(event) => setHideBaseUnitPriceByAction((previous) => ({
                      ...previous,
                      [actionListKey]: event.target.checked,
                    }))}
                    type="checkbox"
                  />
                  <span>기준단가 가리기</span>
                </label>
              ) : null}
              <div className="schedule-document-actions">
                <button
                  className="customer-row-action schedule-document-action-button"
                  disabled={!hasTemplate || previewLoading}
                  onClick={() => onPreview(action, documentOptions)}
                  type="button"
                >
                  {previewLoading && previewAction?.previewHref === action.previewHref ? <Loader2 className="spin-icon" size={14} /> : <Eye size={14} />}
                  <span>미리보기</span>
                </button>
                {action.formats.map((formatAction) => {
                  const actionKey = scheduleDocumentDownloadKey(action, formatAction, documentOptions);
                  const downloading = downloadingKey === actionKey;
                  return (
                    <button
                      className="customer-row-action schedule-document-action-button"
                      disabled={!hasTemplate || Boolean(downloadingKey)}
                      key={formatAction.format}
                      onClick={() => onDownload(action, formatAction, documentOptions)}
                      type="button"
                    >
                      {downloading ? (
                        <Loader2 className="spin-icon" size={14} />
                      ) : formatAction.format === 'xlsx' ? (
                        <FileSpreadsheet size={14} />
                      ) : (
                        <Download size={14} />
                      )}
                      <span>{formatAction.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {documents.autoAttachLabel ? (
        <div className="dashboard-api-alert compact success">
          <FileText size={16} />
          <span>{documents.autoAttachLabel}</span>
        </div>
      ) : null}

      {registeredDocuments.length > 0 ? (
        <div className="schedule-quote-document-list">
          <h4>등록된 서류</h4>
          {registeredDocuments.map((document) => (
            <div className="schedule-quote-document-row" key={document.id}>
              <a href={document.downloadHref}>
                <FileText size={14} />
                <span>
                  {[
                    document.documentTypeLabel,
                    document.quoteGroupLabel && document.documentType === 'quotation' ? document.quoteGroupLabel : '',
                    document.filename || document.transactionNumber,
                  ].filter(Boolean).join(' · ')}
                </span>
                <small>{[document.size, document.createdAt ? formatDateTimeLabel(document.createdAt) : ''].filter(Boolean).join(' · ')}</small>
              </a>
              {document.canDelete && document.deleteHref ? (
                <button
                  aria-label={`${document.filename || document.transactionNumber} 삭제`}
                  className="schedule-quote-document-delete"
                  disabled={Boolean(deletingDocumentKey)}
                  onClick={() => onDelete(document)}
                  type="button"
                >
                  {deletingDocumentKey === String(document.id) ? <Loader2 className="spin-icon" size={13} /> : <Trash2 size={13} />}
                </button>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {previewError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{previewError}</span>
        </div>
      ) : null}

      {previewAction ? (
        <div className="schedule-document-preview">
          <div className="schedule-document-preview-heading">
            <div>
              <span className="eyebrow">Preview</span>
              <h4>{previewAction.label} 변수</h4>
            </div>
            <button className="customer-row-action schedule-document-close-button" onClick={onClosePreview} type="button">
              <X size={13} />
              <span>닫기</span>
            </button>
          </div>
          {previewLoading ? (
            <div className="schedule-document-preview-loading">
              <Loader2 className="spin-icon" size={15} />
              <span>변수 데이터를 불러오는 중입니다</span>
            </div>
          ) : previewData ? (
            <>
              <div className="schedule-document-preview-meta">
                <span>{previewData.fileInfo.docName || previewAction.label}</span>
                <span>{previewData.templateFilename || '템플릿 파일명 없음'}</span>
                {previewData.fileInfo.quoteGroupLabel ? <span>{previewData.fileInfo.quoteGroupLabel}</span> : null}
                <span>품목 {formatNumber(previewData.itemCount)}개</span>
              </div>
              {variableGroups.length > 0 ? (
                <div className="schedule-document-variable-groups">
                  {variableGroups.map((group) => (
                    <div className="schedule-document-variable-group" key={group.label}>
                      <h5>{group.label}</h5>
                      <div className="schedule-document-variable-grid">
                        {group.entries.map(([key, value]) => (
                          <div className={isScheduleDocumentEmptyValue(value) ? 'schedule-document-variable-row empty' : 'schedule-document-variable-row'} key={key}>
                            <span>{key}</span>
                            <strong>{formatScheduleDocumentValue(value)}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DashboardEmpty label="표시할 서류 변수가 없습니다" />
              )}
              {previewData.items.length > 0 ? (
                <div className="schedule-document-item-list">
                  {previewData.items.map((item) => (
                    <div key={item.index}>
                      <strong>{item.quoteGroupLabel ? `[${item.quoteGroupLabel}] ${item.name || `품목 ${item.index}`}` : item.name || `품목 ${item.index}`}</strong>
                      <span>{[
                        `${formatNumber(item.quantity)}${item.unit || ''}`,
                        !item.baseUnitPriceHidden && item.discountUnitPrice !== null ? `기준 ${formatWon(item.baseUnitPrice)}` : '',
                        item.discountUnitPrice !== null ? `할인 ${formatWon(item.discountUnitPrice)}` : formatWon(item.unitPrice),
                        formatWon(item.subtotal),
                        item.notes,
                      ].filter(Boolean).join(' · ')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <DashboardEmpty label="서류에 들어갈 품목이 없습니다" />
              )}
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function AIEvidenceList({
  className = '',
  items,
  limit = 6,
}: {
  className?: string;
  items: AIWorkspaceActionEvidence[];
  limit?: number;
}) {
  const rows = items.slice(0, limit).filter((item) => item.label || item.value);
  if (!rows.length) {
    return null;
  }
  return (
    <div className={['ai-evidence-list', className].filter(Boolean).join(' ')}>
      {rows.map((item, index) => (
        <span className="ai-evidence-row" key={`${item.label}-${item.value}-${item.href || index}`}>
          <b>{item.label}</b>
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

function ScheduleAICoachPanel({
  canUseAi,
  error,
  loading,
  message,
  permissionMessage,
  onGenerate,
  result,
}: {
  canUseAi: boolean;
  error: string;
  loading: boolean;
  message: string;
  permissionMessage: string;
  onGenerate: () => void;
  result: ScheduleAICoachResponse | null;
}) {
  const coach = result?.coach ?? null;
  const risks = coach?.risks ?? [];
  const evidence = coach?.evidence ?? [];

  return (
    <section className="schedule-ai-coach-panel" aria-label="일정 AI 브리핑">
      <div className="schedule-ai-coach-heading">
        <div>
          <span className="eyebrow">Schedule brief</span>
          <h3>일정 브리핑</h3>
        </div>
        <button className="customer-row-action schedule-ai-coach-run" disabled={!canUseAi || loading} onClick={onGenerate} type="button">
          {loading ? <Loader2 className="spin-icon" size={14} /> : <Sparkles size={14} />}
          <span>{loading ? '분석 중' : coach ? '다시 보기' : '브리핑 보기'}</span>
        </button>
      </div>
      {!canUseAi ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{permissionMessage || 'AI 기능 사용 권한이 없습니다.'}</span></div> : null}
      {error ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{error}</span></div> : null}
      {message ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{message}</span></div> : null}
      {coach ? (
        <div className="schedule-ai-coach-body">
          <div className="schedule-ai-coach-summary">
            <p>{coach.summary}</p>
            <span>{result?.source === 'openai' ? `${result.modelLabel || 'AI'} 브리핑` : 'CRM 기반 브리핑'} · {coach.confidence}</span>
          </div>
          {coach.recommendedNextAction ? (
            <div className="schedule-ai-coach-next">
              <span>확인 필요</span>
              <strong>{coach.recommendedNextAction}</strong>
            </div>
          ) : null}
          {coach.talkTrack.length > 0 ? (
            <div className="schedule-ai-coach-list">
              <h4>브리핑 메모</h4>
              {coach.talkTrack.map((item) => <p key={item}>{item}</p>)}
            </div>
          ) : null}
          {coach.checklist.length > 0 ? (
            <div className="schedule-ai-coach-checklist">
              {coach.checklist.map((item) => (
                <span key={item}><CheckCircle2 size={13} />{item}</span>
              ))}
            </div>
          ) : null}
          {risks.length > 0 ? (
            <div className="schedule-ai-coach-risk-list">
              {risks.map((risk) => (
                <div className={risk.level || 'medium'} key={`${risk.label}-${risk.value}`}>
                  <AlertTriangle size={14} />
                  <span><strong>{risk.label}</strong>{risk.value}</span>
                </div>
              ))}
            </div>
          ) : null}
          {evidence.length > 0 ? (
            <AIEvidenceList className="schedule-ai-coach-evidence" items={evidence} limit={5} />
          ) : null}
        </div>
      ) : (
        <DashboardEmpty label="현재 일정 기준 브리핑을 확인하세요" />
      )}
    </section>
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
  const [quoteGroupNotes, setQuoteGroupNotes] = useState<ScheduleQuoteGroupNoteState>(() => makeScheduleQuoteGroupNotes(currentSchedule));
  const [deliverySaving, setDeliverySaving] = useState(false);
  const [deliveryError, setDeliveryError] = useState('');
  const [deliveryMessage, setDeliveryMessage] = useState('');
  const [deliveryUsePrepayment, setDeliveryUsePrepayment] = useState(Boolean(currentSchedule?.activityType === 'delivery' && currentSchedule.usePrepayment));
  const [deliveryPrepaymentRows, setDeliveryPrepaymentRows] = useState<SchedulePrepaymentEditRow[]>([]);
  const [deliveryPrepaymentsLoading, setDeliveryPrepaymentsLoading] = useState(false);
  const [deliveryPrepaymentsError, setDeliveryPrepaymentsError] = useState('');
  const [quoteImportData, setQuoteImportData] = useState<FollowupQuoteItemsData | null>(null);
  const [quoteImportOpen, setQuoteImportOpen] = useState(false);
  const [quoteImportLoading, setQuoteImportLoading] = useState(false);
  const [quoteImportError, setQuoteImportError] = useState('');
  const [selectedQuoteImportIds, setSelectedQuoteImportIds] = useState<string[]>([]);
  const [productOptions, setProductOptions] = useState<ProductOption[]>([]);
  const [productsLoaded, setProductsLoaded] = useState(false);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productError, setProductError] = useState('');
  const [scheduleDeleting, setScheduleDeleting] = useState(false);
  const [scheduleDeleteError, setScheduleDeleteError] = useState('');
  const [prepaymentRows, setPrepaymentRows] = useState<SchedulePrepaymentEditRow[]>([]);
  const [prepaymentsLoading, setPrepaymentsLoading] = useState(false);
  const [prepaymentsError, setPrepaymentsError] = useState('');
  const [documentDownloadingKey, setDocumentDownloadingKey] = useState('');
  const [documentDeletingKey, setDocumentDeletingKey] = useState('');
  const [documentPreviewAction, setDocumentPreviewAction] = useState<ScheduleDocumentAction | null>(null);
  const [documentPreviewData, setDocumentPreviewData] = useState<ScheduleDocumentPreviewData | null>(null);
  const [documentPreviewLoading, setDocumentPreviewLoading] = useState(false);
  const [documentPreviewError, setDocumentPreviewError] = useState('');
  const [scheduleNoteOpen, setScheduleNoteOpen] = useState(false);
  const [scheduleNoteForm, setScheduleNoteForm] = useState<NoteCreateFormState>(() => makeScheduleNoteCreateForm(currentSchedule));
  const [scheduleNoteSaving, setScheduleNoteSaving] = useState(false);
  const [scheduleNoteError, setScheduleNoteError] = useState('');
  const [scheduleNoteMessage, setScheduleNoteMessage] = useState('');
  const [scheduleNoteHref, setScheduleNoteHref] = useState('');
  const [scheduleCoachLoading, setScheduleCoachLoading] = useState(false);
  const [scheduleCoachError, setScheduleCoachError] = useState('');
  const [scheduleCoachMessage, setScheduleCoachMessage] = useState('');
  const [scheduleCoachResult, setScheduleCoachResult] = useState<ScheduleAICoachResponse | null>(null);
  const scheduleNotePanelRef = useRef<HTMLElement | null>(null);
  const scheduleEditPanelRef = useRef<HTMLElement | null>(null);
  const quoteImportPanelRef = useRef<HTMLDivElement | null>(null);
  const deliveryEditPanelRef = useRef<HTMLFormElement | null>(null);

  useGuidedPanelFocus(scheduleNoteOpen, scheduleNotePanelRef, `schedule-note-${currentSchedule?.id || 'new'}`);
  useGuidedPanelFocus(editOpen, scheduleEditPanelRef, `schedule-edit-${currentSchedule?.id || 'new'}`);
  useGuidedPanelFocus(quoteImportOpen, quoteImportPanelRef, `quote-import-${currentSchedule?.id || 'new'}`, { focusFirst: false });
  useGuidedPanelFocus(deliveryEditOpen, deliveryEditPanelRef, `delivery-edit-${currentSchedule?.id || 'new'}`);

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
    setQuoteGroupNotes(makeScheduleQuoteGroupNotes(data?.schedule ?? null));
    setDeliverySaving(false);
    setDeliveryError('');
    setDeliveryMessage('');
    setDeliveryUsePrepayment(Boolean(data?.schedule?.activityType === 'delivery' && data.schedule.usePrepayment));
    setDeliveryPrepaymentRows([]);
    setDeliveryPrepaymentsLoading(false);
    setDeliveryPrepaymentsError('');
    setQuoteImportData(null);
    setQuoteImportOpen(false);
    setQuoteImportLoading(false);
    setQuoteImportError('');
    setSelectedQuoteImportIds([]);
    setProductError('');
    setScheduleDeleting(false);
    setScheduleDeleteError('');
    setPrepaymentRows([]);
    setPrepaymentsLoading(false);
    setPrepaymentsError('');
    setDocumentDownloadingKey('');
    setDocumentDeletingKey('');
    setDocumentPreviewAction(null);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(false);
    setDocumentPreviewError('');
    setScheduleNoteOpen(false);
    setScheduleNoteForm(makeScheduleNoteCreateForm(data?.schedule ?? null));
    setScheduleNoteSaving(false);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
    setScheduleCoachLoading(false);
    setScheduleCoachError('');
    setScheduleCoachMessage('');
    setScheduleCoachResult(null);
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

  useEffect(() => {
    if (
      !deliveryEditOpen ||
      !currentSchedule?.canEdit ||
      currentSchedule.activityType !== 'delivery' ||
      !currentSchedule.followupId
    ) {
      setDeliveryPrepaymentRows([]);
      setDeliveryPrepaymentsLoading(false);
      setDeliveryPrepaymentsError('');
      return undefined;
    }

    let active = true;
    setDeliveryPrepaymentsLoading(true);
    setDeliveryPrepaymentsError('');
    loadPrepayments(currentSchedule.followupId, currentSchedule.id)
      .then((options) => {
        if (active) {
          setDeliveryPrepaymentRows(makeSchedulePrepaymentRows(options));
        }
      })
      .catch((error) => {
        if (active) {
          setDeliveryPrepaymentRows([]);
          setDeliveryPrepaymentsError(error instanceof Error ? error.message : '선결제 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        if (active) {
          setDeliveryPrepaymentsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [deliveryEditOpen, currentSchedule?.activityType, currentSchedule?.canEdit, currentSchedule?.followupId, currentSchedule?.id]);

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

  const handleScheduleNoteFieldChange = (field: keyof NoteCreateFormState, value: string) => {
    setScheduleNoteForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
  };

  const handleScheduleNoteToggle = () => {
    if (!currentSchedule?.canEdit) {
      setScheduleNoteError('영업노트 작성 권한이 없습니다.');
      return;
    }
    setScheduleNoteForm((previous) => ({
      ...makeScheduleNoteCreateForm(currentSchedule),
      content: previous.content,
      nextAction: previous.nextAction,
      nextActionDate: previous.nextActionDate,
    }));
    setScheduleNoteOpen((open) => !open);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
  };

  const handleScheduleNoteSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || scheduleNoteSaving) {
      return;
    }
    if (!currentSchedule.canEdit) {
      setScheduleNoteError('영업노트 작성 권한이 없습니다.');
      return;
    }
    const followupId = Number(scheduleNoteForm.followupId);
    const departmentId = Number(scheduleNoteForm.departmentId);
    const scheduleId = Number(scheduleNoteForm.scheduleId);
    if ((!followupId && !departmentId) || !scheduleId) {
      setScheduleNoteError('연결할 고객 또는 부서/연구실과 일정 정보가 없습니다.');
      return;
    }
    if (!scheduleNoteForm.actionType) {
      setScheduleNoteError('활동 유형을 선택하세요.');
      return;
    }
    if (!scheduleNoteForm.content.trim()) {
      setScheduleNoteError('활동 내용을 입력하세요.');
      return;
    }

    const payload: NoteCreatePayload = {
      actionType: scheduleNoteForm.actionType,
      activityDate: scheduleNoteForm.activityDate || undefined,
      content: scheduleNoteForm.content.trim(),
      departmentId: departmentId || undefined,
      followupId: followupId || undefined,
      nextAction: scheduleNoteForm.nextAction.trim() || undefined,
      nextActionDate: scheduleNoteForm.nextActionDate || undefined,
      scheduleId,
    };

    setScheduleNoteSaving(true);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
    try {
      const result = await createSalesNote(payload);
      await onRefresh();
      setScheduleNoteMessage(result.message || '일정에 영업노트를 연결했습니다.');
      setScheduleNoteHref(result.reactHref || (result.historyId ? `/notes/${result.historyId}/` : ''));
      setScheduleNoteForm(makeScheduleNoteCreateForm(currentSchedule));
      setScheduleNoteOpen(false);
    } catch (error) {
      setScheduleNoteError(error instanceof Error ? error.message : '영업노트 저장에 실패했습니다.');
    } finally {
      setScheduleNoteSaving(false);
    }
  };

  const handleScheduleCoachRun = async () => {
    if (!currentSchedule || scheduleCoachLoading) {
      return;
    }
    setScheduleCoachLoading(true);
    setScheduleCoachError('');
    setScheduleCoachMessage('');
    try {
      const result = await generateScheduleAICoach(currentSchedule.id);
      setScheduleCoachResult(result);
      setScheduleCoachMessage(result.context?.stored === false ? '브리핑은 저장되지 않았습니다.' : '');
    } catch (error) {
      setScheduleCoachResult(null);
      setScheduleCoachError(error instanceof Error ? error.message : '일정 AI 브리핑 생성에 실패했습니다.');
    } finally {
      setScheduleCoachLoading(false);
    }
  };

  const handleDeliveryPrepaymentToggle = (selected: boolean) => {
    if (selected && scheduleDeliveryEditRowsTotal(deliveryRows) <= 0) {
      setDeliveryUsePrepayment(true);
      setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
      setDeliveryMessage('');
      return;
    }
    setDeliveryUsePrepayment(selected);
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentRowToggle = (id: number, selected: boolean) => {
    if (selected && scheduleDeliveryEditRowsTotal(deliveryRows) <= 0) {
      setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
      setDeliveryMessage('');
      return;
    }
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id
        ? {
          ...row,
          selected,
          amountInput: selected && !row.amountInput && row.selectedAmount > 0 ? String(row.selectedAmount) : row.amountInput,
        }
        : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentAmountChange = (id: number, amountInput: string) => {
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentFillMax = (id: number, maxAmount: number) => {
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput: String(Math.max(Math.round(maxAmount), 0)) } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
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
      setEditError('일정 유형을 선택하세요.');
      return;
    }
    if (!editForm.status) {
      setEditError('일정 상태를 선택하세요.');
      return;
    }
    if (!editForm.visitDate) {
      setEditError('일정 날짜를 선택하세요.');
      return;
    }
    if (!editForm.visitTime) {
      setEditError('일정 시간을 선택하세요.');
      return;
    }
    const probability = normalizeProbabilityInputValue(editForm.probability);
    if (isQuoteProbabilityRequired(editForm.activityType) && !probability) {
      setEditError('견적 성공 확률은 필수입니다.');
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
      probability: probability || undefined,
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

  const handleScheduleFileDelete = async (file: ScheduleFileItem | AttachmentManagerFile) => {
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

    setFileDeletingId(Number(file.id));
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
    setDeliveryUsePrepayment(Boolean(willOpen && currentSchedule.activityType === 'delivery' && currentSchedule.usePrepayment));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
    setDeliveryEditOpen((open) => !open);
    if (willOpen) {
      void ensureProductsLoaded();
    }
  };

  const loadQuoteImports = async () => {
    if (!currentSchedule?.followupId) {
      setQuoteImportError('연결된 고객 정보가 없어 견적을 불러올 수 없습니다.');
      return;
    }
    if (quoteImportLoading) {
      return;
    }
    setQuoteImportLoading(true);
    setQuoteImportError('');
    try {
      const quotes = await loadFollowupQuoteItems(currentSchedule.followupId);
      setQuoteImportData(quotes);
      const availableQuoteIds = new Set(quotes.quotes.map((quote) => quote.optionId));
      setSelectedQuoteImportIds((previous) => previous.filter((optionId) => availableQuoteIds.has(optionId)));
      if (!quotes.quotes.length) {
        setQuoteImportError('불러올 수 있는 견적 품목이 없습니다.');
      }
    } catch (error) {
      setQuoteImportData(null);
      setQuoteImportError(error instanceof Error ? error.message : '견적 품목을 불러오지 못했습니다.');
    } finally {
      setQuoteImportLoading(false);
    }
  };

  const handleQuoteImportToggle = () => {
    if (!currentSchedule?.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }
    if (currentSchedule.activityType !== 'delivery') {
      setDeliveryError('견적 품목 불러오기는 납품 일정에서만 사용할 수 있습니다.');
      setDeliveryMessage('');
      return;
    }
    if (quoteImportOpen) {
      setQuoteImportOpen(false);
      setQuoteImportError('');
      setSelectedQuoteImportIds([]);
      return;
    }
    setDeliveryEditOpen(true);
    setDeliveryUsePrepayment((previous) => previous || Boolean(currentSchedule.usePrepayment));
    setDeliveryError('');
    setDeliveryMessage('');
    setQuoteImportOpen(true);
    setSelectedQuoteImportIds([]);
    void ensureProductsLoaded();
    void loadQuoteImports();
  };

  const handleQuoteImportOpenFromPrepayment = () => {
    if (quoteImportOpen) {
      void loadQuoteImports();
      return;
    }
    handleQuoteImportToggle();
  };

  const handleQuoteImportSelectionChange = (optionId: string, selected: boolean) => {
    setSelectedQuoteImportIds((previous) => {
      if (selected) {
        return previous.includes(optionId) ? previous : [...previous, optionId];
      }
      return previous.filter((id) => id !== optionId);
    });
    setQuoteImportError('');
  };

  const handleQuoteImportApply = (quotes: FollowupQuoteOption | FollowupQuoteOption[]) => {
    const quoteList = (Array.isArray(quotes) ? quotes : [quotes]).filter((quote) => quote.items.length > 0);
    if (!quoteList.length) {
      setQuoteImportError('선택한 견적에 품목이 없습니다.');
      return;
    }
    if (
      scheduleDeliveryRowsHaveUserInput(deliveryRows) &&
      !window.confirm('현재 입력된 납품 품목을 선택한 견적 품목으로 바꿀까요?')
    ) {
      return;
    }
    const importedRows = quoteList.flatMap((quote, quoteIndex) => (
      quote.items.map((item, itemIndex) => makeScheduleDeliveryEditRowFromQuoteItem(
        item,
        quote,
        quoteIndex * 1000 + itemIndex,
      ))
    ));
    setDeliveryRows(importedRows.length > 0 ? importedRows : [makeScheduleDeliveryEditRow(undefined, 0)]);
    setDeliveryEditOpen(true);
    setQuoteImportOpen(false);
    setSelectedQuoteImportIds([]);
    setQuoteImportError('');
    setDeliveryError('');
    const quoteLabel = quoteList.length === 1 ? quoteImportOptionTitle(quoteList[0]) : `${quoteList.length}개 견적`;
    setDeliveryMessage(`${quoteLabel} 품목 ${importedRows.length}개를 불러왔습니다. 저장을 눌러 납품 일정에 반영하세요.`);
  };

  const handleSelectedQuoteImportApply = () => {
    const selectedQuotes = quoteImportData?.quotes.filter((quote) => selectedQuoteImportIds.includes(quote.optionId)) ?? [];
    handleQuoteImportApply(selectedQuotes);
  };

  const handleDeliveryFieldChange = (rowId: string, field: ScheduleDeliveryEditField, value: string | boolean) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? (() => {
        const nextRow = { ...row, [field]: value } as ScheduleDeliveryEditRow;
        const basePrice = parsePositiveFormNumber(String(field === 'unitPrice' ? value : nextRow.unitPrice));
        if (field === 'discountRate') {
          const rate = parsePositiveFormNumber(String(value));
          nextRow.discountUnitPrice = basePrice !== null && rate !== null ? moneyInputValue(discountUnitFromRate(basePrice, rate)) : '';
        } else if (field === 'discountUnitPrice') {
          const discountUnit = parsePositiveFormNumber(String(value));
          nextRow.discountRate = basePrice !== null && discountUnit !== null ? rateInputValue(discountRateFromUnit(basePrice, discountUnit)) : '';
        } else if (field === 'unitPrice') {
          const rate = parsePositiveFormNumber(nextRow.discountRate);
          const discountUnit = parsePositiveFormNumber(nextRow.discountUnitPrice);
          if (basePrice !== null && rate !== null && nextRow.discountRate.trim()) {
            nextRow.discountUnitPrice = moneyInputValue(discountUnitFromRate(basePrice, rate));
          } else if (basePrice !== null && discountUnit !== null && nextRow.discountUnitPrice.trim()) {
            nextRow.discountRate = rateInputValue(discountRateFromUnit(basePrice, discountUnit));
          }
        }
        return nextRow;
      })() : row
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
        discountRate: '',
        discountUnitPrice: '',
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
      row.productId
      || row.itemName.trim()
      || row.quantity.trim()
      || row.unitPrice.trim()
      || row.discountRate.trim()
      || row.discountUnitPrice.trim()
      || row.quoteGroup.trim()
      || row.notes.trim()
      || row.optionDescription.trim()
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
      const discountRate = row.discountRate.trim();
      if (discountRate && Number.isNaN(Number(discountRate))) {
        setDeliveryError(`${index + 1}번째 할인율은 숫자로 입력하세요.`);
        return;
      }
      if (discountRate && (Number(discountRate) < 0 || Number(discountRate) > 100)) {
        setDeliveryError(`${index + 1}번째 할인율은 0부터 100 사이여야 합니다.`);
        return;
      }
      const discountUnitPrice = row.discountUnitPrice.trim();
      if (discountUnitPrice && Number.isNaN(Number(discountUnitPrice))) {
        setDeliveryError(`${index + 1}번째 할인단가는 숫자로 입력하세요.`);
        return;
      }
      if (discountUnitPrice && Number(discountUnitPrice) < 0) {
        setDeliveryError(`${index + 1}번째 할인단가는 0 이상이어야 합니다.`);
        return;
      }
      if (unitPrice && discountUnitPrice && Number(discountUnitPrice) > Number(unitPrice)) {
        setDeliveryError(`${index + 1}번째 할인단가는 기준단가보다 클 수 없습니다.`);
        return;
      }
      payloadItems.push({
        id: row.id,
        productId: row.productId ? Number(row.productId) : null,
        itemName,
        quantity,
        unit: row.unit.trim() || 'EA',
        unitPrice: unitPrice || null,
        discountRate: discountRate || null,
        discountUnitPrice: discountUnitPrice || null,
        quoteGroup: row.quoteGroup.trim(),
        notes: row.notes.trim(),
        optionDescription: row.optionDescription.trim(),
        sourceQuoteScheduleId: row.sourceQuoteScheduleId ? Number(row.sourceQuoteScheduleId) : null,
        sourceQuoteItemId: row.sourceQuoteItemId ? Number(row.sourceQuoteItemId) : null,
      });
    }
    const sourceQuoteScheduleIds = Array.from(new Set(
      rowsWithInput
        .map((row) => Number(row.sourceQuoteScheduleId))
        .filter((sourceId) => Number.isInteger(sourceId) && sourceId > 0),
    ));
    const checkedQuoteScheduleIds = Array.from(new Set(
      (quoteImportData?.quotes ?? [])
        .filter((quote) => selectedQuoteImportIds.includes(quote.optionId))
        .map((quote) => Number(quote.scheduleId))
        .filter((sourceId) => Number.isInteger(sourceId) && sourceId > 0),
    ));
    const quoteGroupNotesPayload = scheduleQuoteGroupsFromRows(rowsWithInput).reduce<ScheduleQuoteGroupNoteState>((acc, group) => {
      acc[group] = (quoteGroupNotes[group] || '').trim();
      return acc;
    }, {});
    const deliveryPrepaymentSelections = deliveryPrepaymentRows.filter((row) => row.selected);
    const useDeliveryPrepayment = currentSchedule.activityType === 'delivery' && deliveryUsePrepayment;
    if (useDeliveryPrepayment) {
      if (deliveryPrepaymentBaseAmount <= 0) {
        setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
        return;
      }
      if (deliveryPrepaymentsLoading) {
        setDeliveryError('선결제 목록을 불러오는 중입니다.');
        return;
      }
      if (deliveryPrepaymentsError) {
        setDeliveryError(deliveryPrepaymentsError);
        return;
      }
      if (!deliveryPrepaymentSelections.length) {
        setDeliveryError('차감할 선결제를 선택하세요.');
        return;
      }
      for (const [index, row] of deliveryPrepaymentSelections.entries()) {
        const amount = Number(row.amountInput);
        if (!Number.isFinite(amount) || amount <= 0) {
          setDeliveryError(`${index + 1}번째 선결제 차감 금액을 입력하세요.`);
          return;
        }
        if (amount > row.availableBalance) {
          setDeliveryError(`${row.payerName} 선결제 잔액이 부족합니다.`);
          return;
        }
        const otherSelectedAmount = deliveryPrepaymentSelections.reduce((total, otherRow) => {
          if (otherRow.id === row.id) {
            return total;
          }
          const otherAmount = Number(otherRow.amountInput);
          return Number.isFinite(otherAmount) && otherAmount > 0 ? total + otherAmount : total;
        }, 0);
        const rowMaxAmount = Math.min(
          row.availableBalance,
          Math.max(deliveryPrepaymentBaseAmount - otherSelectedAmount, 0),
        );
        if (amount > rowMaxAmount) {
          setDeliveryError(`${row.payerName} 차감 금액은 ${formatWon(rowMaxAmount)}까지 입력할 수 있습니다.`);
          return;
        }
      }
    }
    const prepaymentOptions = currentSchedule.activityType === 'delivery'
      ? {
        usePrepayment: useDeliveryPrepayment,
        prepayments: useDeliveryPrepayment
          ? deliveryPrepaymentSelections.map<SchedulePrepaymentSelectionPayload>((row) => ({ id: row.id, amount: row.amountInput.trim() }))
          : [],
        checkedQuoteScheduleIds,
      }
      : checkedQuoteScheduleIds.length
        ? { checkedQuoteScheduleIds }
        : undefined;

    setDeliverySaving(true);
    setDeliveryError('');
    setDeliveryMessage('');
    try {
      const updated = await updateScheduleDeliveryItems(
        data.links.updateDeliveryItems,
        payloadItems,
        quoteGroupNotesPayload,
        sourceQuoteScheduleIds,
        prepaymentOptions,
      );
      const refreshed = await onRefresh();
      setDeliveryRows(makeScheduleDeliveryEditRows(refreshed?.deliveryItems ?? updated.deliveryItems ?? []));
      setQuoteGroupNotes(makeScheduleQuoteGroupNotes(refreshed?.schedule ?? updated.schedule ?? null));
      setDeliveryMessage(updated.message || '납품 품목을 저장했습니다.');
      setDeliveryEditOpen(false);
    } catch (error) {
      setDeliveryError(error instanceof Error ? error.message : '납품 품목 저장에 실패했습니다.');
    } finally {
      setDeliverySaving(false);
    }
  };

  const handleDocumentPreview = async (action: ScheduleDocumentAction, options?: ScheduleDocumentRequestOptions) => {
    if (documentPreviewLoading) {
      return;
    }
    setDocumentPreviewAction(action);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(true);
    setDocumentPreviewError('');
    try {
      const preview = await loadScheduleDocumentPreview(action.previewHref, options);
      setDocumentPreviewData(preview);
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : '서류 변수 미리보기에 실패했습니다.');
    } finally {
      setDocumentPreviewLoading(false);
    }
  };

  const handleDocumentDownload = async (
    action: ScheduleDocumentAction,
    formatAction: ScheduleDocumentFormatAction,
    options?: ScheduleDocumentRequestOptions,
  ) => {
    if (documentDownloadingKey) {
      return;
    }
    const actionKey = scheduleDocumentDownloadKey(action, formatAction, options);
    setDocumentDownloadingKey(actionKey);
    setDocumentPreviewError('');
    try {
      const result = await downloadScheduleDocument(formatAction.href, options);
      saveDownloadedBlob(result.blob, result.filename);
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : `${action.label} 다운로드에 실패했습니다.`);
    } finally {
      setDocumentDownloadingKey('');
    }
  };

  const handleGeneratedDocumentDelete = async (document: ScheduleGeneratedDocument) => {
    if (documentDeletingKey) {
      return;
    }
    if (!currentSchedule?.canEdit || !document.canDelete || !document.deleteHref) {
      setDocumentPreviewError('등록 서류 삭제 권한이 없습니다.');
      return;
    }
    const filename = document.filename || document.transactionNumber || document.documentTypeLabel;
    if (!window.confirm(`"${filename}" 등록 서류를 삭제할까요?`)) {
      return;
    }

    setDocumentDeletingKey(String(document.id));
    setDocumentPreviewError('');
    try {
      await deleteGeneratedDocument(document.deleteHref);
      await onRefresh();
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : '등록 서류 삭제에 실패했습니다.');
    } finally {
      setDocumentDeletingKey('');
    }
  };

  const handleScheduleDelete = async () => {
    if (scheduleDeleting) {
      return;
    }
    if (!currentSchedule?.canEdit || !data?.links.deleteSchedule) {
      setScheduleDeleteError('일정 삭제 권한이 없습니다.');
      return;
    }
    const confirmMessage = [
      '이 일정을 삭제할까요?',
      '',
      `고객: ${currentSchedule.customer || '고객명 미정'}`,
      `날짜: ${currentSchedule.date ? formatDateLabel(currentSchedule.date) : '날짜 없음'}`,
      '',
      '관련 활동 기록도 함께 삭제되며 복구할 수 없습니다.',
    ].join('\n');
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setScheduleDeleting(true);
    setScheduleDeleteError('');
    try {
      await deleteSchedule(data.links.deleteSchedule);
      window.location.assign(data.links.schedules || '/schedules/');
    } catch (error) {
      setScheduleDeleteError(error instanceof Error ? error.message : '일정 삭제에 실패했습니다.');
    } finally {
      setScheduleDeleting(false);
    }
  };

  const handleDocumentPreviewClose = () => {
    setDocumentPreviewAction(null);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(false);
    setDocumentPreviewError('');
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
  const isQuoteSchedule = schedule.activityType === 'quote';
  const itemPanelLabel = isQuoteSchedule ? '견적 품목' : '납품 품목';
  const taxInvoice = data.taxInvoice;
  const editableQuoteGroups = scheduleQuoteGroupsFromRows(deliveryRows);
  const savedQuoteGroupNotes = schedule.quoteGroupNotes?.filter((item) => item.notes.trim()) ?? [];
  const prepaymentUsages = schedule.prepaymentUsages ?? [];
  const deliveryTotalAmount = deliveryItems.reduce((total, item) => total + (item.totalPrice || 0), 0);
  const prepaymentBaseAmount = deliveryTotalAmount > 0 ? deliveryTotalAmount : schedule.expectedRevenue;
  const selectedPrepaymentAmount = prepaymentRows.reduce((total, row) => {
    const amount = Number(row.amountInput);
    return row.selected && Number.isFinite(amount) && amount > 0 ? total + amount : total;
  }, 0);
  const payableAfterPrepayment = Math.max(prepaymentBaseAmount - selectedPrepaymentAmount, 0);
  const deliveryEditTotalAmount = scheduleDeliveryEditRowsTotal(deliveryRows);
  const deliveryPrepaymentBaseAmount = deliveryEditOpen
    ? deliveryEditTotalAmount
    : prepaymentBaseAmount;
  const deliveryPrepaymentNeedsItems = deliveryUsePrepayment && deliveryPrepaymentBaseAmount <= 0;
  const selectedDeliveryPrepaymentAmount = deliveryPrepaymentRows.reduce((total, row) => {
    const amount = Number(row.amountInput);
    return !deliveryPrepaymentNeedsItems && row.selected && Number.isFinite(amount) && amount > 0 ? total + amount : total;
  }, 0);
  const deliveryPayableAfterPrepayment = Math.max(deliveryPrepaymentBaseAmount - selectedDeliveryPrepaymentAmount, 0);
  const deleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
  const metrics = [
    { label: '일정 상태', value: schedule.statusLabel, detail: schedule.activityLabel, icon: CalendarDays, tone: schedule.overdue ? 'red' as const : 'blue' as const },
    { label: '방문 일시', value: schedule.date ? formatDateLabel(schedule.date) : '날짜 없음', detail: schedule.time || '시간 없음', icon: Clock, tone: 'green' as const },
    { label: '예상 매출', value: schedule.expectedRevenue > 0 ? formatWon(schedule.expectedRevenue) : '없음', detail: schedule.probability === null || schedule.probability === undefined ? '확률 미입력' : `${schedule.probability}%`, icon: CircleDollarSign, tone: 'amber' as const },
    { label: '보고/파일', value: `${formatNumber(schedule.historyCount)} / ${formatNumber(schedule.fileCount)}`, detail: '보고 / 첨부', icon: MessageSquareText, tone: 'teal' as const },
  ];
  const scheduleNoteActionOptions = schedule.activityType === 'service'
    ? scheduleNoteActionTypeOptions
    : scheduleNoteActionTypeOptions.filter((option) => option.value !== 'service');

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
          {schedule.canEdit ? (
            <button className="route-secondary-action" onClick={handleScheduleNoteToggle} type="button">
              {scheduleNoteOpen ? '작성 닫기' : '영업노트 작성'}
              <FileText size={16} />
            </button>
          ) : null}
          {data.edit.canEdit ? (
            <button className="route-primary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
              <Check size={16} />
            </button>
          ) : null}
          {schedule.canEdit && data.links.deleteSchedule ? (
            <button
              className="route-secondary-action danger schedule-delete-action"
              disabled={scheduleDeleting}
              onClick={handleScheduleDelete}
              type="button"
            >
              {scheduleDeleting ? <Loader2 className="spin-icon" size={16} /> : <Trash2 size={16} />}
              삭제
            </button>
          ) : null}
        </div>
      </div>

      {scheduleDeleteError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{scheduleDeleteError}</span>
        </div>
      ) : null}
      {deleteRequested && schedule.canEdit ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>삭제 요청으로 들어왔습니다. 상단의 삭제 버튼으로 확정하세요.</span>
        </div>
      ) : null}

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

      {data.relatedNotes.length > 0 ? (
        <section className="dashboard-panel note-related-panel schedule-linked-notes-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Linked notes</span>
              <h2>연결된 영업노트</h2>
            </div>
            <MessageSquareText size={18} />
          </div>
          <CustomerDetailNoteList emptyLabel="이 일정에 연결된 영업노트가 없습니다" notes={data.relatedNotes} />
        </section>
      ) : null}

      {scheduleNoteOpen || scheduleNoteMessage || scheduleNoteError ? (
        <section className="dashboard-panel notes-create-panel schedule-note-create-panel" ref={scheduleNotePanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Sales note</span>
              <h2>일정 영업노트 작성</h2>
            </div>
            {scheduleNoteSaving ? <Loader2 className="spin-icon" size={18} /> : <FileText size={18} />}
          </div>
          {scheduleNoteError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{scheduleNoteError}</span></div> : null}
          {scheduleNoteMessage ? (
            <div className="dashboard-api-alert compact success">
              <CheckCircle2 size={16} />
              <span>{scheduleNoteMessage}</span>
              {scheduleNoteHref ? <a href={scheduleNoteHref}>노트 보기</a> : null}
            </div>
          ) : null}
          {scheduleNoteOpen ? (
            <form className="notes-create-form schedule-note-create-form" onSubmit={handleScheduleNoteSubmit}>
              <div className="notes-create-grid">
                <label>
                  <span>고객</span>
                  <input
                    readOnly
                    value={[schedule.company, schedule.department, schedule.customer].filter(Boolean).join(' · ') || '고객 없음'}
                  />
                </label>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => handleScheduleNoteFieldChange('actionType', event.target.value)}
                    required
                    value={scheduleNoteForm.actionType}
                  >
                    {scheduleNoteActionOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동일</span>
                  <input
                    onChange={(event) => handleScheduleNoteFieldChange('activityDate', event.target.value)}
                    type="date"
                    value={scheduleNoteForm.activityDate}
                  />
                </label>
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => handleScheduleNoteFieldChange('nextActionDate', event.target.value)}
                    type="date"
                    value={scheduleNoteForm.nextActionDate}
                  />
                </label>
              </div>
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => handleScheduleNoteFieldChange('content', event.target.value)}
                  required
                  rows={4}
                  value={scheduleNoteForm.content}
                />
              </label>
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => handleScheduleNoteFieldChange('nextAction', event.target.value)}
                  rows={2}
                  value={scheduleNoteForm.nextAction}
                />
              </label>
              <div className="notes-create-actions">
                {data.links.djangoCreateNote ? (
                  <a className="route-secondary-action" href={data.links.djangoCreateNote}>
                    노트 페이지
                    <MoveUpRight size={15} />
                  </a>
                ) : null}
                <button className="route-primary-action" disabled={scheduleNoteSaving} type="submit">
                  {scheduleNoteSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel schedule-edit-panel" ref={scheduleEditPanelRef}>
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
                  <span>일정 유형</span>
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
                  <span>일정 날짜</span>
                  <input
                    onChange={(event) => handleEditFieldChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={editForm.visitDate}
                  />
                </label>
                <label>
                  <span>일정 시간</span>
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
                    step="5"
                    required={isQuoteProbabilityRequired(editForm.activityType)}
                    onBlur={(event) => handleEditFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
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
                <span>일정 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('notes', event.target.value)}
                  rows={4}
                  value={editForm.notes}
                />
              </label>
              <div className="notes-create-actions">
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
            {schedule.notesFull || schedule.notes ? <p>{schedule.notesFull || schedule.notes}</p> : <DashboardEmpty label="일정 내용이 없습니다" />}
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
              <span className="eyebrow">Related</span>
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
            {data.links.customer ? <a href={data.links.customer}>고객 상세</a> : null}
            {data.links.createNote ? <a href={data.links.createNote}>보고 작성</a> : null}
            <a href={data.links.calendar}>일정 캘린더</a>
          </div>
          <ScheduleAICoachPanel
            canUseAi={data.ai.canUseAi}
            error={scheduleCoachError}
            loading={scheduleCoachLoading}
            message={scheduleCoachMessage}
            permissionMessage={data.ai.message}
            onGenerate={handleScheduleCoachRun}
            result={scheduleCoachResult}
          />
          <ScheduleCommercialChecksPanel checks={data.commercialChecks} />
          <ScheduleDocumentsPanel
            documents={data.documents}
            deletingDocumentKey={documentDeletingKey}
            downloadingKey={documentDownloadingKey}
            onClosePreview={handleDocumentPreviewClose}
            onDelete={handleGeneratedDocumentDelete}
            onDownload={handleDocumentDownload}
            onPreview={handleDocumentPreview}
            previewAction={documentPreviewAction}
            previewData={documentPreviewData}
            previewError={documentPreviewError}
            previewLoading={documentPreviewLoading}
          />
          <div className="schedule-file-heading schedule-delivery-heading">
            <h3 className="customer-detail-section-heading">{itemPanelLabel}</h3>
            {schedule.canEdit && data.links.updateDeliveryItems ? (
              <div className="schedule-heading-actions">
                {!isQuoteSchedule ? (
                  <button
                    className="customer-row-action schedule-delivery-edit-toggle"
                    disabled={deliverySaving || quoteImportLoading}
                    onClick={handleQuoteImportToggle}
                    type="button"
                  >
                    {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <Copy size={14} />}
                    <span>{quoteImportOpen ? '불러오기 닫기' : '견적 불러오기'}</span>
                  </button>
                ) : null}
                <button
                  className="customer-row-action schedule-delivery-edit-toggle"
                  disabled={deliverySaving}
                  onClick={handleDeliveryEditToggle}
                  type="button"
                >
                  {deliveryEditOpen ? <ChevronDown size={14} /> : <ListChecks size={14} />}
                  <span>{deliveryEditOpen ? '닫기' : '편집'}</span>
                </button>
              </div>
            ) : null}
          </div>
          {deliveryError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{deliveryError}</span></div> : null}
          {deliveryMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{deliveryMessage}</span></div> : null}
          {!isQuoteSchedule && taxInvoice.applies ? (
            <div className={`schedule-tax-invoice-panel ${taxInvoice.status}`}>
              <div>
                <FileText size={15} />
                <span>
                  <strong>외상 {taxInvoice.statusLabel}</strong>
                  <small>{[
                    taxInvoice.message,
                    taxInvoice.totalCount ? `총 ${formatNumber(taxInvoice.totalCount)}개 품목` : '',
                  ].filter(Boolean).join(' · ')}</small>
                </span>
              </div>
              <a className="customer-row-action schedule-tax-invoice-toggle" href="/receivables/">
                <CircleDollarSign size={14} />
                <span>외상고객</span>
              </a>
            </div>
          ) : null}
          {!isQuoteSchedule && quoteImportOpen ? (
            <div className="schedule-quote-import-panel" ref={quoteImportPanelRef}>
              <div className="schedule-quote-import-heading">
                <div>
                  <strong>견적 품목 불러오기</strong>
                  <span>같은 부서의 본인 견적 일정에서 하나 이상 선택해 한 번에 가져옵니다.</span>
                </div>
                <div className="schedule-quote-import-actions">
                  <span>{selectedQuoteImportIds.length ? `${formatNumber(selectedQuoteImportIds.length)}개 선택` : '선택 대기'}</span>
                  <button
                    className="route-secondary-action"
                    disabled={deliverySaving || quoteImportLoading || selectedQuoteImportIds.length === 0}
                    onClick={handleSelectedQuoteImportApply}
                    type="button"
                  >
                    선택 적용
                  </button>
                  <button
                    className="customer-row-action schedule-delivery-edit-toggle"
                    disabled={quoteImportLoading}
                    onClick={() => void loadQuoteImports()}
                    type="button"
                  >
                    {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <RefreshCw size={14} />}
                    <span>새로고침</span>
                  </button>
                </div>
              </div>
              {quoteImportError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{quoteImportError}</span></div> : null}
              {quoteImportLoading ? (
                <div className="schedule-quote-import-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>견적을 불러오는 중입니다</span>
                </div>
              ) : quoteImportData?.quotes.length ? (
                <div className="schedule-quote-import-list">
                  {quoteImportData.quotes.map((quote) => {
                    const selected = selectedQuoteImportIds.includes(quote.optionId);
                    return (
                      <div className={selected ? 'schedule-quote-import-card selected' : 'schedule-quote-import-card'} key={quote.optionId}>
                        <label className="schedule-quote-import-select">
                          <input
                            checked={selected}
                            disabled={deliverySaving}
                            onChange={(event) => handleQuoteImportSelectionChange(quote.optionId, event.target.checked)}
                            type="checkbox"
                          />
                          <span className="schedule-quote-import-main">
                            <strong>{quoteImportOptionTitle(quote)}</strong>
                            <span>{[
                              quote.customerName || '고객명 미정',
                              quote.companyName,
                              quote.departmentName,
                              quote.quoteDate ? formatDateLabel(quote.quoteDate) : '',
                              `일정 #${quote.scheduleId}`,
                              `남은 품목 ${formatNumber(quote.items.length)}개`,
                              quote.remainingAmount ? `잔여 ${formatWon(quote.remainingAmount)}` : '',
                            ].filter(Boolean).join(' · ')}</span>
                            <span className="schedule-quote-import-badges">
                              <span className={quote.hasPartialDelivery ? 'partial' : 'pending'}>
                                {quote.deliveryStatusLabel}
                              </span>
                              {quote.deliveredAmount > 0 ? <span>납품 반영 {formatWon(quote.deliveredAmount)}</span> : null}
                              {quote.quotedAmount > 0 ? <span>원 견적 {formatWon(quote.quotedAmount)}</span> : null}
                            </span>
                            <p>{quote.items.map(quoteImportItemSummary).slice(0, 6).join(', ')}</p>
                          </span>
                        </label>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <DashboardEmpty label="불러올 수 있는 견적이 없습니다" />
              )}
            </div>
          ) : null}
          {deliveryEditOpen ? (
            <form className="schedule-delivery-edit-form" onSubmit={handleDeliverySubmit} ref={deliveryEditPanelRef}>
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
                              aria-label={`${index + 1}번째 ${itemPanelLabel} 제품 선택 해제`}
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
                      {isQuoteSchedule ? (
                        <label>
                          <span>견적서 구분</span>
                          <input
                            onChange={(event) => handleDeliveryFieldChange(row.rowId, 'quoteGroup', event.target.value)}
                            placeholder="예: 보상판매, 수리"
                            value={row.quoteGroup}
                          />
                        </label>
                      ) : null}
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
                        <span>기준단가</span>
                        <input
                          inputMode="numeric"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'unitPrice', event.target.value)}
                          type="number"
                          value={row.unitPrice}
                        />
                      </label>
                      <label>
                        <span>할인율(%)</span>
                        <input
                          inputMode="decimal"
                          max="100"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'discountRate', event.target.value)}
                          step="0.01"
                          type="number"
                          value={row.discountRate}
                        />
                      </label>
                      <label>
                        <span>할인단가</span>
                        <input
                          inputMode="numeric"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'discountUnitPrice', event.target.value)}
                          type="number"
                          value={row.discountUnitPrice}
                        />
                      </label>
                      <label className="schedule-delivery-notes-field">
                        <span>적요</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'notes', event.target.value)}
                          value={row.notes}
                        />
                      </label>
                      {isQuoteSchedule ? (
                        <label className="schedule-delivery-notes-field">
                          <span>옵션/설명</span>
                          <textarea
                            onChange={(event) => handleDeliveryFieldChange(row.rowId, 'optionDescription', event.target.value)}
                            placeholder="예: 구성 옵션, 설치 조건, 별도 안내 문구"
                            rows={2}
                            value={row.optionDescription}
                          />
                        </label>
                      ) : null}
                      <button
                        aria-label={`${index + 1}번째 ${itemPanelLabel} 삭제`}
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
              {isQuoteSchedule ? (
                <div className="schedule-quote-group-notes-grid">
                  {editableQuoteGroups.map((group) => (
                    <label className="schedule-quote-extra-notes-field" key={group || 'default'}>
                      <span>{quoteGroupLabel(group)} 기타사항</span>
                      <textarea
                        onChange={(event) => {
                          setQuoteGroupNotes((previous) => ({
                            ...previous,
                            [group]: event.target.value,
                          }));
                          setDeliveryError('');
                          setDeliveryMessage('');
                        }}
                        rows={3}
                        value={quoteGroupNotes[group] || ''}
                      />
                    </label>
                  ))}
                </div>
              ) : null}
              {!isQuoteSchedule ? (
                <div className="schedule-prepayment-editor schedule-delivery-prepayment-editor">
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={deliveryUsePrepayment}
                      onChange={(event) => handleDeliveryPrepaymentToggle(event.target.checked)}
                      type="checkbox"
                    />
                    <span>납품 저장 시 선결제 차감</span>
                  </label>
                  {deliveryUsePrepayment ? (
                    <div className="schedule-prepayment-body">
                      {deliveryPrepaymentsError ? (
                        <div className="dashboard-api-alert compact">
                          <AlertTriangle size={16} />
                          <span>{deliveryPrepaymentsError}</span>
                        </div>
                      ) : null}
                      {deliveryPrepaymentsLoading ? (
                        <div className="schedule-prepayment-loading">
                          <Loader2 className="spin-icon" size={15} />
                          <span>선결제 조회 중</span>
                        </div>
                      ) : deliveryPrepaymentRows.length > 0 ? (
                        <>
                          {deliveryPrepaymentNeedsItems ? (
                            <div className="dashboard-api-alert compact schedule-prepayment-item-required">
                              <AlertTriangle size={16} />
                              <span>차감할 납품 품목 합계가 없습니다. 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.</span>
                              {currentSchedule?.canEdit && data?.links.updateDeliveryItems ? (
                                <button
                                  className="customer-row-action"
                                  disabled={quoteImportLoading}
                                  onClick={handleQuoteImportOpenFromPrepayment}
                                  type="button"
                                >
                                  {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <FileText size={14} />}
                                  <span>견적 품목 불러오기</span>
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                          <div className="schedule-prepayment-list">
                            {deliveryPrepaymentRows.map((row) => {
                              const rowAmount = Number(row.amountInput);
                              const safeRowAmount = !deliveryPrepaymentNeedsItems && row.selected && Number.isFinite(rowAmount) && rowAmount > 0 ? rowAmount : 0;
                              const otherSelectedAmount = selectedDeliveryPrepaymentAmount - safeRowAmount;
                              const itemRemainingBeforeRow = Math.max(deliveryPrepaymentBaseAmount - otherSelectedAmount, 0);
                              const rowMaxAmount = deliveryPrepaymentNeedsItems ? 0 : Math.min(row.availableBalance, itemRemainingBeforeRow);
                              const itemRemainingAfterRow = Math.max(itemRemainingBeforeRow - safeRowAmount, 0);
                              const isOverRowMax = row.selected && safeRowAmount > rowMaxAmount;
                              return (
                                <div className={!deliveryPrepaymentNeedsItems && row.selected ? 'schedule-prepayment-row selected' : 'schedule-prepayment-row'} key={row.id}>
                                  <label className="schedule-prepayment-check">
                                    <input
                                      checked={!deliveryPrepaymentNeedsItems && row.selected}
                                      disabled={deliveryPrepaymentNeedsItems}
                                      onChange={(event) => handleDeliveryPrepaymentRowToggle(row.id, event.target.checked)}
                                      type="checkbox"
                                    />
                                    <span>
                                      <strong>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '입금일 없음', row.payerName].filter(Boolean).join(' · ')}</strong>
                                      <small>{[row.customerName, `잔액 ${formatWon(row.balance)}`, `사용 가능 ${formatWon(row.availableBalance)}`].filter(Boolean).join(' · ')}</small>
                                      {!deliveryPrepaymentNeedsItems && row.selected ? (
                                        <small className={isOverRowMax ? 'schedule-prepayment-limit over' : 'schedule-prepayment-limit'}>
                                          품목 상한 {formatWon(itemRemainingBeforeRow)} · 최대 차감 {formatWon(rowMaxAmount)} · 입력 후 남은 납품금액 {formatWon(itemRemainingAfterRow)}
                                        </small>
                                      ) : null}
                                    </span>
                                  </label>
                                  <div className="schedule-prepayment-amount">
                                    <label>
                                      <span>차감</span>
                                      <input
                                        disabled={deliveryPrepaymentNeedsItems || !row.selected}
                                        inputMode="numeric"
                                        max={row.selected ? rowMaxAmount : undefined}
                                        min="0"
                                        onChange={(event) => handleDeliveryPrepaymentAmountChange(row.id, event.target.value)}
                                        type="number"
                                        value={deliveryPrepaymentNeedsItems ? '' : row.amountInput}
                                      />
                                    </label>
                                    <button
                                      className="schedule-prepayment-fill-button"
                                      disabled={deliveryPrepaymentNeedsItems || !row.selected || rowMaxAmount <= 0}
                                      onClick={() => handleDeliveryPrepaymentFillMax(row.id, rowMaxAmount)}
                                      type="button"
                                    >
                                      전체 차감
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      ) : (
                        <DashboardEmpty label="사용 가능한 선결제가 없습니다" />
                      )}
                      <div className="schedule-prepayment-totals">
                        <span>납품 합계 <strong>{formatWon(deliveryPrepaymentBaseAmount)}</strong></span>
                        <span>차감 <strong>{formatWon(selectedDeliveryPrepaymentAmount)}</strong></span>
                        <span>실결제 <strong>{formatWon(deliveryPayableAfterPrepayment)}</strong></span>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <div className="notes-create-actions schedule-delivery-edit-actions">
                <button className="route-secondary-action" disabled={deliverySaving} onClick={handleDeliveryAddRow} type="button">
                  <Plus size={15} />
                  {itemPanelLabel} 추가
                </button>
                <button className="route-primary-action" disabled={deliverySaving} type="submit">
                  {deliverySaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : deliveryItems.length === 0 ? (
            <DashboardEmpty label={`등록된 ${itemPanelLabel}이 없습니다`} />
          ) : (
            <div className="schedule-delivery-list">
              {deliveryItems.map((item) => (
                <div key={item.id}>
                  <strong>{isQuoteSchedule && item.quoteGroupLabel ? `[${item.quoteGroupLabel}] ${item.itemName}` : item.itemName}</strong>
                  <span>{[
                    `${formatNumber(item.quantity)}${item.unit}`,
                    item.discountUnitPrice !== null ? `할인단가 ${formatWon(item.discountUnitPrice)}` : '',
                    item.totalPrice ? formatWon(item.totalPrice) : '',
                    item.cardPaymentReceived ? '카드결제' : item.receivableSettled ? '수금완료' : '외상 진행중',
                  ].filter(Boolean).join(' · ')}</span>
                  {item.notes ? <p>{isQuoteSchedule ? `적요: ${item.notes}` : item.notes}</p> : null}
                  {isQuoteSchedule && item.optionDescription ? <p>옵션/설명: {item.optionDescription}</p> : null}
                </div>
              ))}
              {isQuoteSchedule && savedQuoteGroupNotes.length > 0 ? (
                <div className="schedule-quote-group-notes-list">
                  {savedQuoteGroupNotes.map((note) => (
                    <div className="schedule-quote-extra-notes" key={note.quoteGroup || 'default'}>
                      <span>{note.quoteGroupLabel || quoteGroupLabel(note.quoteGroup)} 기타사항</span>
                      <p>{note.notes}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          )}
          {fileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{fileError}</span></div> : null}
          {fileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{fileMessage}</span></div> : null}
          <AttachmentManager
            canUpload={schedule.canEdit && Boolean(data.links.uploadFiles)}
            deletingId={fileDeletingId}
            emptyLabel="첨부파일이 없습니다"
            files={schedule.files}
            inputRef={fileInputRef}
            title="첨부파일"
            uploadAriaLabel="일정 첨부파일 선택"
            uploading={fileUploading}
            onDelete={handleScheduleFileDelete}
            onFilesSelected={handleScheduleFilesSelected}
            onUploadClick={handleScheduleFileUploadClick}
          />
        </aside>
      </div>

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
  const createPanelRef = useRef<HTMLElement | null>(null);
  useGuidedPanelFocus(createOpen, createPanelRef, 'schedule-create');

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
  const createDepartments = createConfig.departments ?? [];
  const createActivityTypes = createConfig.activityTypes;
  const filteredCreateCustomers = customersForDepartment(createCustomers, createForm.departmentId);
  const selectedDepartmentHasCustomers = filteredCreateCustomers.length > 0;
  const handleCreateDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(createCustomers, nextValue);
    onCreateFormChange('departmentId', nextValue);
    onCreateFormChange('followupId', nextCustomers[0]?.id ? String(nextCustomers[0].id) : '');
  };
  const handleCreateCustomerChange = (nextValue: string) => {
    const nextCustomer = createCustomers.find((customer) => String(customer.id) === nextValue);
    if (nextCustomer?.departmentId) {
      onCreateFormChange('departmentId', String(nextCustomer.departmentId));
    }
    onCreateFormChange('followupId', nextValue);
  };

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
        <section className="dashboard-panel notes-create-panel schedules-create-panel" ref={createPanelRef}>
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
          ) : createDepartments.length === 0 && createCustomers.length === 0 ? (
            <DashboardEmpty label="등록 가능한 부서/연구실이 없습니다" />
          ) : createActivityTypes.length === 0 ? (
            <DashboardEmpty label="등록 가능한 일정 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid schedules-create-grid">
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    onChange={handleCreateDepartmentChange}
                    options={createDepartments.map(makeDepartmentSelectOption)}
                    placeholder="회사, 부서/연구실, 담당자 검색"
                    value={createForm.departmentId}
                  />
                </div>
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    allowEmpty={!selectedDepartmentHasCustomers}
                    ariaLabel="고객 선택"
                    disabled={!selectedDepartmentHasCustomers}
                    emptyLabel="부서에만 연결"
                    onChange={handleCreateCustomerChange}
                    options={filteredCreateCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={createForm.followupId}
                  />
                </div>
                <label>
                  <span>일정 유형</span>
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
                  <span>일정 날짜</span>
                  <input
                    onChange={(event) => onCreateFormChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={createForm.visitDate}
                  />
                </label>
                <label>
                  <span>일정 시간</span>
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
                    step="5"
                    required={isQuoteProbabilityRequired(createForm.activityType)}
                    onBlur={(event) => onCreateFormChange('probability', normalizeProbabilityInputValue(event.target.value))}
                    onChange={(event) => onCreateFormChange('probability', event.target.value)}
                    placeholder="0-100, 5% 단위"
                    type="number"
                    value={createForm.probability}
                  />
                </label>
              </div>
              <label>
                <span>일정 내용</span>
                <textarea
                  onChange={(event) => onCreateFormChange('notes', event.target.value)}
                  placeholder="일정 내용, 준비사항, 후속 확인 사항"
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
            placeholder="고객, 회사, 장소, 일정 내용 검색"
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
          <option value="">일정 유형 전체</option>
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
            <a href={data.links.schedules}>일정 목록</a>
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
                <a className="customer-name-link" href={prepayment.customerHref || prepayment.customerPrepaymentHref || '/customers/'}>
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
                  {prepayment.customerPrepaymentHref ? (
                    <a className="customer-row-action" href={prepayment.customerPrepaymentHref}>계정별</a>
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
  const selectedDataFilter = dataFilter || data.filters.dataFilter || 'me';
  const selectedFilterUser = filterUser || data.filters.filterUser || '';
  const showOwnerSelect = selectedDataFilter === 'user';

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
          <p>입금액, 사용액, 잔액을 계정 단위로 확인하고 납품 일정 차감 흐름과 연결합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          {data.links.create ? (
            <a className="route-primary-action" href="/prepayments/new/">
              선결제 등록
              <Plus size={16} />
            </a>
          ) : null}
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
        <select onChange={(event) => onDataFilterChange(event.target.value)} value={selectedDataFilter}>
          {data.options.dataFilters.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select disabled={!showOwnerSelect} onChange={(event) => onFilterUserChange(event.target.value)} value={selectedFilterUser}>
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
        <span>계정 선결제 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const isAccountScope = data.scope.mode === 'department';
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
            <strong>계정 선결제 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">{isAccountScope ? 'Account prepayments' : 'Customer prepayments'}</span>
          <h2>{data.scope.name || data.customer.customerName || (isAccountScope ? '계정 선결제' : '고객별 선결제')}</h2>
          <p>
            {[
              isAccountScope ? '부서/연구실 계정 기준' : '고객 기준',
              data.scope.targetUserName ? `${data.scope.targetUserName} 등록분` : '',
            ].filter(Boolean).join(' · ')}
          </p>
        </div>
        <div className="schedules-summary-actions">
          {data.links.accountDetail ? <a className="route-secondary-action" href={data.links.accountDetail}>계정 상세</a> : null}
          <a className="route-secondary-action" href={data.links.prepayments}>선결제 목록</a>
          <a className="route-secondary-action" href={data.links.accountExcel || data.links.djangoExcel}>엑셀</a>
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
              <span className="eyebrow">{isAccountScope ? 'Account scope' : 'Customer scope'}</span>
              <h2>선결제 내역</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
          </div>
          {data.scope.canSelectUser ? (
            <div className="prepayment-customer-filter">
              <label>
                <span>조회 사용자</span>
                <select onChange={(event) => onSelectedUserChange(event.target.value)} value={selectedUser || (data.scope.targetUserId ? String(data.scope.targetUserId) : '')}>
                  <option value="">{data.scope.targetUserName || '회사 전체'}</option>
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
                        <a className="customer-name-link" href={prepayment.customerHref || '/customers/'}>
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
              <h2>{isAccountScope ? '계정 담당자' : '기준 고객'}</h2>
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
            <a href={data.links.accountDetail || data.links.customerDetail || '/prepayments/'}>{isAccountScope ? '계정 상세' : '고객 상세'}</a>
          </div>
        </aside>
      </div>

      <div className="prepayment-drilldown-grid">
        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Balance drilldown</span>
              <h2>계정 잔액</h2>
            </div>
            <CheckCircle2 size={18} />
          </div>
          {data.balanceRows.length === 0 ? (
            <DashboardEmpty label="표시할 잔액이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.balanceRows.map((row) => (
                <article className="prepayment-usage-row" key={row.id}>
                  <div>
                    <strong>{row.payerName || row.customerName || '입금자 미지정'}</strong>
                    <span>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '', row.customerName, row.statusLabel].filter(Boolean).join(' · ')}</span>
                    {row.memo ? <small>{row.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>{formatWon(row.balance)}</strong>
                    <span>원금 {formatWon(row.amount)} · 사용 {formatWon(row.usedAmount)}</span>
                    <a href={`/prepayments/${row.id}/`}>상세</a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Delivery deductions</span>
              <h2>납품 차감 내역</h2>
            </div>
            <ListChecks size={18} />
          </div>
          {data.deductionRows.length === 0 ? (
            <DashboardEmpty label="납품 차감 내역이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.deductionRows.map((usage) => (
                <article className="prepayment-usage-row" key={usage.id}>
                  <div>
                    <strong>{usage.productName || '납품 차감'}</strong>
                    <span>{[usage.usedAt ? formatDateTimeLabel(usage.usedAt) : '', usage.scheduleDate ? `납품 ${formatDateLabel(usage.scheduleDate)}` : '', usage.payerName].filter(Boolean).join(' · ')}</span>
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

        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Ledger</span>
              <h2>조정/이관/취소 기록</h2>
            </div>
            <Activity size={18} />
          </div>
          {data.ledgerEntries.length === 0 ? (
            <DashboardEmpty label="원장 기록이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.ledgerEntries.map((entry) => (
                <article className="prepayment-usage-row" key={entry.id}>
                  <div>
                    <strong>{entry.entryTypeLabel}</strong>
                    <span>{[entry.createdAt ? formatDateTimeLabel(entry.createdAt) : '', entry.actorName, entry.targetUserName ? `대상 ${entry.targetUserName}` : ''].filter(Boolean).join(' · ')}</span>
                    {entry.memo ? <small>{entry.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>{entry.amount < 0 ? '-' : ''}{formatWon(Math.abs(entry.amount))}</strong>
                    <span>잔액 {formatWon(entry.balanceAfter)}</span>
                    {entry.prepaymentHref ? <a href={entry.prepaymentHref}>선결제</a> : null}
                    {entry.scheduleHref ? <a href={entry.scheduleHref}>일정</a> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
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
    accounts: PrepaymentCreateData['create']['accounts'];
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
  const accountOptions = options.accounts.map((account) => ({
    value: String(account.id),
    label: account.label || joinOptionParts([account.companyName, account.departmentName || account.name]),
    meta: `${formatNumber(account.customerCount)}명`,
    searchText: [account.label, account.companyName, account.departmentName, account.name].filter(Boolean).join(' '),
  }));
  const filteredCustomers = form.departmentId
    ? options.customers.filter((customer) => String(customer.departmentId ?? '') === form.departmentId)
    : options.customers;
  return (
    <form className="notes-create-form prepayment-form" onSubmit={onSubmit}>
      <div className="notes-create-grid prepayment-form-grid">
        <div className="form-field">
          <span>계정</span>
          <SearchableSelect
            ariaLabel="계정 선택"
            onChange={(nextValue) => onChange('departmentId', nextValue)}
            options={accountOptions}
            placeholder="업체, 부서/연구실 검색"
            value={form.departmentId}
          />
        </div>
        <div className="form-field">
          <span>담당자 보조 정보</span>
          <SearchableSelect
            ariaLabel="담당자 선택"
            allowEmpty
            disabled={!form.departmentId}
            emptyLabel="담당자 미지정"
            onChange={(nextValue) => onChange('customerId', nextValue)}
            options={filteredCustomers.map(makeCustomerSelectOption)}
            placeholder={form.departmentId ? '담당자 검색' : '계정 선택 후 검색'}
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

  const handleChange = (field: keyof PrepaymentFormState, value: string) => {
    if (field === 'departmentId') {
      setForm((previous) => ({
        ...previous,
        departmentId: value,
        customerId: '',
      }));
      setError('');
      setMessage('');
      setCreatedHref('');
      return;
    }
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
    const departmentId = Number(form.departmentId);
    const customerId = Number(form.customerId);
    if (!departmentId) {
      setError('계정을 선택하세요.');
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
      departmentId,
      customerId: customerId || null,
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
        departmentId: previous.departmentId,
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
    accounts: data.create.accounts,
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
          <p>계정을 먼저 선택하고 담당자는 보조 정보로 연결해 납품 차감 잔액을 관리합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/prepayments/">목록</a>
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
    if (field === 'departmentId') {
      setForm((previous) => ({
        ...previous,
        departmentId: value,
        customerId: '',
      }));
      setError('');
      setMessage('');
      return;
    }
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
    const departmentId = Number(form.departmentId);
    const customerId = Number(form.customerId);
    const amount = Number(form.amount);
    const balance = Number(form.balance);
    if (!departmentId) {
      setError('계정을 선택하세요.');
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
      departmentId,
      customerId: customerId || null,
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
    accounts: data.edit.accounts,
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
            {prepayment.customerHref ? <a href={prepayment.customerHref}>고객 상세</a> : null}
            {prepayment.customerPrepaymentHref ? <a href={prepayment.customerPrepaymentHref}>계정별 선결제</a> : null}
          </div>
        </aside>
      </div>
    </section>
  );
}

function EmployeesPage({
  data,
  loading,
  company,
  status,
  query,
  role,
  onCompanyChange,
  onQueryChange,
  onRoleChange,
  onStatusChange,
  onRefresh,
}: {
  data: EmployeesData | null;
  loading: boolean;
  company: string;
  status: string;
  query: string;
  role: string;
  onCompanyChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRoleChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onRefresh: () => Promise<void>;
}) {
  const [formOpen, setFormOpen] = useState(() => new URLSearchParams(window.location.search).get('create') === '1');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EmployeeFormState>(() => makeEmptyEmployeeForm(data));
  const [saving, setSaving] = useState(false);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const employeeFormPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(formOpen, employeeFormPanelRef, `employee-${editingId || 'new'}`);

  useEffect(() => {
    if (!data) return;
    const params = new URLSearchParams(window.location.search);
    const requestedId = Number(params.get('employee') || 0);
    const shouldEdit = params.get('edit') === '1';
    if (requestedId && shouldEdit && editingId !== requestedId) {
      const employee = data.employees.find((item) => item.id === requestedId);
      if (employee?.canUpdate) {
        setEditingId(employee.id);
        setForm(makeEmployeeEditForm(employee, data));
        setFormOpen(true);
      }
    } else if (!editingId && !formOpen && data.scope.mode === 'manager') {
      setForm((previous) => ({
        ...previous,
        companyId: data.scope.companyId ? String(data.scope.companyId) : previous.companyId,
        companyName: data.scope.companyName || previous.companyName,
      }));
    }
  }, [data, editingId, formOpen]);

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>직원 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const isAdminMode = data.scope.mode === 'admin';
  const editingEmployee = editingId ? data.employees.find((employee) => employee.id === editingId) ?? null : null;
  const canSubmit = editingId ? Boolean(editingEmployee?.canUpdate) : data.scope.canCreate;
  const metrics = [
    { label: isAdminMode ? '전체 사용자' : '전체 직원', value: `${formatNumber(data.metrics.totalEmployees)}명`, detail: data.scope.companyName || '전체 회사', icon: Users, tone: 'blue' as const },
    { label: '활성 계정', value: `${formatNumber(data.metrics.activeEmployees)}명`, detail: `비활성 ${formatNumber(data.metrics.inactiveEmployees)}명`, icon: CheckCircle2, tone: 'green' as const },
    { label: 'Manager', value: `${formatNumber(data.metrics.managerCount)}명`, detail: '직원관리 가능', icon: ShieldCheck, tone: 'amber' as const },
    { label: 'SalesMan', value: `${formatNumber(data.metrics.salesmanCount)}명`, detail: '실무자 계정', icon: ListChecks, tone: 'teal' as const },
  ];

  const openCreateForm = () => {
    setEditingId(null);
    setForm(makeEmptyEmployeeForm(data));
    setFormOpen(true);
    setError('');
    setMessage('');
  };

  const openEditForm = (employee: EmployeeManagementItem) => {
    setEditingId(employee.id);
    setForm(makeEmployeeEditForm(employee, data));
    setFormOpen(true);
    setError('');
    setMessage('');
  };

  const handleFormChange = <K extends keyof EmployeeFormState>(field: K, value: EmployeeFormState[K]) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    setError('');
    setMessage('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit || saving) return;
    if (editingId && !editingEmployee) {
      setError('수정할 사용자 정보를 찾을 수 없습니다.');
      return;
    }
    if (!form.username.trim()) {
      setError('사용자 ID를 입력하세요.');
      return;
    }
    if (!editingEmployee && !form.password) {
      setError('새 사용자 비밀번호를 입력하세요.');
      return;
    }
    if (form.password || form.passwordConfirm) {
      if (form.password !== form.passwordConfirm) {
        setError('비밀번호가 일치하지 않습니다.');
        return;
      }
    }
    if (isAdminMode && form.role !== 'admin' && !form.companyName.trim()) {
      setError('소속 회사를 입력하세요.');
      return;
    }

    setSaving(true);
    setError('');
    setMessage('');
    try {
      const payload = employeePayloadFromForm(form);
      const result = editingEmployee
        ? await updateEmployee(editingEmployee.updateHref, payload)
        : await createEmployee(data.links.createApi, payload);
      setMessage(result.message || (editingEmployee ? '사용자 정보를 수정했습니다.' : '사용자를 생성했습니다.'));
      setFormOpen(false);
      setEditingId(null);
      setForm(makeEmptyEmployeeForm(data));
      await onRefresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '사용자 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (employee: EmployeeManagementItem) => {
    if (!employee.canToggleActive || !employee.toggleActiveHref || actioningId) return;
    const nextActive = !employee.isActive;
    const actionLabel = nextActive ? '활성화' : '비활성화';
    if (!window.confirm(`${employee.name || employee.username} 계정을 ${actionLabel}할까요?`)) {
      return;
    }
    setActioningId(employee.id);
    setError('');
    setMessage('');
    try {
      const result = await toggleEmployeeActive(employee.toggleActiveHref, nextActive);
      setMessage(result.message || `사용자를 ${actionLabel}했습니다.`);
      await onRefresh();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : '사용자 상태 변경에 실패했습니다.');
    } finally {
      setActioningId(null);
    }
  };

  return (
    <section className="employees-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>직원관리 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'management_required' ? 'Admin 또는 Manager 계정만 사용할 수 있습니다.' : data.message || data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Employee management</span>
          <h2>{data.scope.label || (isAdminMode ? '사용자관리' : '직원관리')}</h2>
          <p>{isAdminMode ? '전체 사용자 계정, 회사, 권한, 활성 상태를 React에서 관리합니다.' : '같은 회사 직원 계정, 권한, 활성 상태를 React에서 관리합니다.'}</p>
        </div>
        <div className="schedules-summary-actions">
          {data.scope.canCreate ? (
            <button className="route-primary-action" type="button" onClick={openCreateForm}>
              {isAdminMode ? '사용자 추가' : '직원 추가'}
              <Plus size={16} />
            </button>
          ) : null}
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="직원관리 지표">
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
            placeholder="이름, 사용자명, 이메일 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onRoleChange(event.target.value)} value={role}>
          {data.options.roles.map((option) => (
            <option key={option.value || 'all'} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          {(data.options.statuses ?? []).map((option) => (
            <option key={option.value || 'all'} value={option.value}>{option.label}</option>
          ))}
        </select>
        {isAdminMode ? (
          <select onChange={(event) => onCompanyChange(event.target.value)} value={company}>
            <option value="">회사 전체</option>
            {(data.options.companies ?? []).map((option) => (
              <option key={option.id} value={option.id}>{option.name}</option>
            ))}
          </select>
        ) : null}
      </div>

      {formOpen ? (
        <section className="dashboard-panel employee-form-panel" ref={employeeFormPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">{editingEmployee ? 'Edit account' : 'Create account'}</span>
              <h2>{editingEmployee ? `${editingEmployee.name || editingEmployee.username} 수정` : isAdminMode ? '사용자 추가' : '직원 추가'}</h2>
            </div>
            <button className="route-secondary-action" type="button" onClick={() => {
              setFormOpen(false);
              setEditingId(null);
              setForm(makeEmptyEmployeeForm(data));
              setError('');
              setMessage('');
            }}>닫기</button>
          </div>
          <form className="employee-form-grid" onSubmit={handleSubmit}>
            <label>
              <span>사용자 ID</span>
              <input value={form.username} onChange={(event) => handleFormChange('username', event.target.value)} />
            </label>
            <label>
              <span>성</span>
              <input value={form.lastName} onChange={(event) => handleFormChange('lastName', event.target.value)} />
            </label>
            <label>
              <span>이름</span>
              <input value={form.firstName} onChange={(event) => handleFormChange('firstName', event.target.value)} />
            </label>
            <label>
              <span>이메일</span>
              <input type="email" value={form.email} onChange={(event) => handleFormChange('email', event.target.value)} />
            </label>
            <label>
              <span>권한</span>
              <select
                disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeRole)}
                value={form.role}
                onChange={(event) => handleFormChange('role', event.target.value)}
              >
                {data.options.roles.filter((option) => option.value).map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>소속 회사</span>
              <input
                disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeCompany)}
                list="employee-company-options"
                value={form.companyName}
                onChange={(event) => {
                  handleFormChange('companyName', event.target.value);
                  handleFormChange('companyId', '');
                }}
              />
              <datalist id="employee-company-options">
                {(data.options.companies ?? []).map((option) => (
                  <option key={option.id} value={option.name} />
                ))}
              </datalist>
            </label>
            <label>
              <span>{editingEmployee ? '새 비밀번호' : '비밀번호'}</span>
              <input type="password" value={form.password} onChange={(event) => handleFormChange('password', event.target.value)} />
            </label>
            <label>
              <span>비밀번호 확인</span>
              <input type="password" value={form.passwordConfirm} onChange={(event) => handleFormChange('passwordConfirm', event.target.value)} />
            </label>
            <div className="employee-permission-row">
              <label>
                <input
                  checked={form.canDownloadExcel}
                  type="checkbox"
                  onChange={(event) => handleFormChange('canDownloadExcel', event.target.checked)}
                />
                <span>엑셀 다운로드</span>
              </label>
              <label>
                <input
                  checked={form.canUseAi}
                  disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeAi)}
                  type="checkbox"
                  onChange={(event) => handleFormChange('canUseAi', event.target.checked)}
                />
                <span>AI 사용</span>
              </label>
              {editingEmployee ? (
                <label>
                  <input
                    checked={form.isActive}
                    disabled={!editingEmployee.canToggleActive}
                    type="checkbox"
                    onChange={(event) => handleFormChange('isActive', event.target.checked)}
                  />
                  <span>활성 계정</span>
                </label>
              ) : null}
            </div>
            <div className="route-actions employee-form-actions">
              <button className="primary-button" type="submit" disabled={saving}>{saving ? '저장 중' : editingEmployee ? '수정 저장' : '계정 생성'}</button>
              <button className="route-secondary-action" type="button" onClick={() => {
                setFormOpen(false);
                setEditingId(null);
                setForm(makeEmptyEmployeeForm(data));
              }}>취소</button>
            </div>
          </form>
        </section>
      ) : null}

      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      <section className="dashboard-panel customers-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Employees</span>
            <h2>직원 목록</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
        </div>
        {data.employees.length ? (
          <div className="customers-table-wrap">
            <table className="customers-table">
              <thead>
                <tr>
                  <th>직원</th>
                  <th>권한</th>
                  <th>상태</th>
                  <th>권한 옵션</th>
                  {isAdminMode ? <th>회사</th> : null}
                  <th>최근 로그인</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {data.employees.map((employee) => (
                  <tr key={employee.id}>
                    <td>
                      <strong>{employee.name || employee.username}</strong>
                      <small className="customer-muted-cell">{[employee.username, employee.email].filter(Boolean).join(' · ') || '-'}</small>
                    </td>
                    <td>{employee.roleLabel || employee.role}</td>
                    <td>
                      <span className={`product-status ${employee.isActive ? 'active' : 'inactive'}`}>
                        {employee.isActive ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td>
                      {[
                        employee.canDownloadExcel ? '엑셀' : '',
                        employee.canUseAi ? 'AI' : '',
                      ].filter(Boolean).join(' · ') || '-'}
                    </td>
                    {isAdminMode ? <td>{employee.company || '-'}</td> : null}
                    <td>{employee.lastLogin ? formatDateTimeLabel(employee.lastLogin) : '-'}</td>
                    <td>
                      <div className="product-row-actions">
                        {employee.canUpdate ? (
                          <button className="route-secondary-action" type="button" onClick={() => openEditForm(employee)}>수정</button>
                        ) : (
                          <span className="customer-muted-cell">{employee.isCurrentUser ? '본인 계정' : '읽기 전용'}</span>
                        )}
                        {employee.canToggleActive ? (
                          <button
                            className={`route-secondary-action ${employee.isActive ? 'danger' : ''}`}
                            disabled={actioningId === employee.id}
                            type="button"
                            onClick={() => handleToggleActive(employee)}
                          >
                            {employee.isActive ? '비활성화' : '활성화'}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <DashboardEmpty label="조건에 맞는 직원이 없습니다" />
        )}
      </section>
    </section>
  );
}

function DocumentsPage({
  data,
  loading,
  onReload,
  onTypeChange,
  routeData,
  selectedType,
}: {
  data: DocumentTemplatesData | null;
  loading: boolean;
  onReload: () => Promise<DocumentTemplatesData>;
  onTypeChange: (value: string) => void;
  routeData: PipelineData;
  selectedType: string;
}) {
  const [formOpen, setFormOpen] = useState(() => shouldOpenCreatePanel());
  const [editingTemplate, setEditingTemplate] = useState<DocumentTemplateItem | null>(null);
  const [form, setForm] = useState<DocumentTemplateFormState>(() => makeEmptyDocumentTemplateForm());
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [formError, setFormError] = useState('');
  const [formMessage, setFormMessage] = useState('');
  const [copiedVariableToken, setCopiedVariableToken] = useState('');
  const documentFormPanelRef = useRef<HTMLFormElement | null>(null);

  useGuidedPanelFocus(formOpen, documentFormPanelRef, `document-${editingTemplate?.id || 'new'}`);

  const canCreate = Boolean(data?.create.canCreate);
  const documentTypes = data?.documentTypes ?? [];
  const recentGenerations = data?.recentGenerations ?? [];
  const templateVariableGroups = data?.templateVariableGroups ?? [];

  const openCreate = () => {
    setEditingTemplate(null);
    setForm(makeEmptyDocumentTemplateForm());
    setFile(null);
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const openEdit = (template: DocumentTemplateItem) => {
    setEditingTemplate(template);
    setForm(makeDocumentTemplateForm(template));
    setFile(null);
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingTemplate(null);
    setFile(null);
    setFormError('');
  };

  const handleFormChange = (field: keyof DocumentTemplateFormState, value: string | boolean) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setFormError('');
  };

  const handleVariableCopy = async (token: string) => {
    try {
      await navigator.clipboard.writeText(token);
      setCopiedVariableToken(token);
      window.setTimeout(() => setCopiedVariableToken(''), 1400);
    } catch {
      setCopiedVariableToken('');
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) return;
    if (!form.name.trim()) {
      setFormError('서류명을 입력하세요.');
      return;
    }
    if (!form.documentType) {
      setFormError('서류 종류를 선택하세요.');
      return;
    }
    if (!editingTemplate && !file) {
      setFormError('엑셀 템플릿 파일을 선택하세요.');
      return;
    }

    const payload: DocumentTemplateMutationPayload = {
      companyId: form.companyId,
      description: form.description,
      documentType: form.documentType,
      file,
      isDefault: form.isDefault,
      name: form.name.trim(),
    };

    setSaving(true);
    setFormError('');
    setFormMessage('');
    try {
      const result = editingTemplate
        ? await updateDocumentTemplate(editingTemplate.updateUrl, payload)
        : await createDocumentTemplate(data.create.submitUrl, payload);
      setFormMessage(result.message || '저장했습니다.');
      setFormOpen(false);
      setEditingTemplate(null);
      setFile(null);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '서류 템플릿 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleDefault = async (template: DocumentTemplateItem) => {
    if (actionId) return;
    setActionId(template.id);
    setFormError('');
    setFormMessage('');
    try {
      await toggleDocumentTemplateDefault(template.toggleDefaultUrl);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '기본 설정 변경에 실패했습니다.');
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (template: DocumentTemplateItem) => {
    if (actionId || !window.confirm(`"${template.name}" 서류 템플릿을 삭제할까요?`)) return;
    setActionId(template.id);
    setFormError('');
    setFormMessage('');
    try {
      const result = await deleteDocumentTemplate(template.deleteUrl);
      setFormMessage(result.message || '삭제했습니다.');
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '삭제에 실패했습니다.');
    } finally {
      setActionId(null);
    }
  };

  if (loading && !data) {
    return <div className="documents-page"><div className="empty-state">서류 템플릿을 불러오는 중입니다.</div></div>;
  }

  return (
    <section className="documents-page">
      <WorkspaceRoutePage data={routeData} view="documents" />
      {data?.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>서류 API에 연결되지 않았습니다</strong>
            <span>{data?.error === 'login_required' ? '로그인이 필요합니다.' : data?.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="documents-layout">
        <section className="documents-main">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Templates</p>
              <h2>서류 템플릿</h2>
            </div>
            <div className="schedules-summary-actions">
              {canCreate ? (
                <button type="button" className="route-secondary-action primary" onClick={openCreate}>
                  <Plus size={16} />
                  등록
                </button>
              ) : null}
            </div>
          </div>

          <div className="documents-filter-bar">
            <button className={!selectedType ? 'active' : ''} type="button" onClick={() => onTypeChange('')}>전체</button>
            {documentTypes.map((type) => (
              <button
                className={selectedType === type.value ? 'active' : ''}
                key={type.value}
                type="button"
                onClick={() => onTypeChange(type.value)}
              >
                {type.label}
              </button>
            ))}
          </div>

          {formError ? <p className="form-error">{formError}</p> : null}
          {formMessage ? <p className="form-success">{formMessage}</p> : null}

          {data?.templates.length ? (
            <div className="document-template-grid">
              {data.templates.map((template) => (
                <article className={`document-template-card ${template.isDefault ? 'default' : ''}`} key={template.id}>
                  <div className="document-template-card-head">
                    <div className="document-template-icon">
                      <FileSpreadsheet size={20} />
                    </div>
                    <div>
                      <h3>{template.name}</h3>
                      <span>{template.documentTypeLabel} · {template.company.name}</span>
                    </div>
                    {template.isDefault ? <strong className="status-pill done">기본</strong> : null}
                  </div>
                  {template.description ? <p>{template.description}</p> : <p className="muted-text">설명이 없습니다.</p>}
                  <dl className="document-template-meta">
                    <div>
                      <dt>파일</dt>
                      <dd>{template.fileName || template.fileType}</dd>
                    </div>
                    <div>
                      <dt>등록</dt>
                      <dd>{template.createdBy || '-'} · {formatDateTimeLabel(template.createdAt)}</dd>
                    </div>
                    <div>
                      <dt>수정</dt>
                      <dd>{formatDateTimeLabel(template.updatedAt) || '-'}</dd>
                    </div>
                  </dl>
                  <div className="document-template-actions">
                    <a className="icon-button" aria-label="다운로드" href={template.downloadHref}>
                      <Download size={17} />
                    </a>
                    {template.canToggleDefault ? (
                      <button
                        aria-label={template.isDefault ? '기본 해제' : '기본 설정'}
                        className="icon-button"
                        disabled={actionId === template.id}
                        onClick={() => handleToggleDefault(template)}
                        type="button"
                      >
                        <Star size={17} />
                      </button>
                    ) : null}
                    {template.canManage ? (
                      <>
                        <button className="route-secondary-action" onClick={() => openEdit(template)} type="button">수정</button>
                        <button
                          className="route-secondary-action danger"
                          disabled={actionId === template.id}
                          onClick={() => handleDelete(template)}
                          type="button"
                        >
                          삭제
                        </button>
                      </>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state compact">조건에 맞는 서류 템플릿이 없습니다.</div>
          )}
        </section>

        <aside className="documents-side">
          <div className="document-summary-panel">
            <h3>요약</h3>
            <div className="document-summary-metrics">
              <div>
                <span>전체</span>
                <strong>{formatNumber(data?.summary.totalTemplates ?? 0)}</strong>
              </div>
              <div>
                <span>기본</span>
                <strong>{formatNumber(data?.summary.defaultTemplates ?? 0)}</strong>
              </div>
              <div>
                <span>오늘 생성</span>
                <strong>{formatNumber(data?.summary.generatedToday ?? 0)}</strong>
              </div>
              <div>
                <span>최근 이력</span>
                <strong>{formatNumber(data?.summary.recentGenerationCount ?? 0)}</strong>
              </div>
            </div>
            <div className="document-type-summary">
              {(data?.summary.byType ?? []).map((item) => (
                <div key={item.type}>
                  <span>{item.label}</span>
                  <strong>{formatNumber(item.count)}</strong>
                  <small>기본 {formatNumber(item.defaultCount)}</small>
                </div>
              ))}
            </div>
          </div>

          {formOpen ? (
            <form className="document-template-form" onSubmit={handleSubmit} ref={documentFormPanelRef}>
              <div className="section-heading-row compact">
                <div>
                  <p className="eyebrow">{editingTemplate ? 'Edit' : 'Create'}</p>
                  <h3>{editingTemplate ? '서류 수정' : '서류 등록'}</h3>
                </div>
                <button className="icon-button" aria-label="닫기" onClick={closeForm} type="button">
                  <X size={17} />
                </button>
              </div>
              {data?.currentUser.isSuperuser && data.create.companies.length ? (
                <label>
                  <span>회사</span>
                  <select value={form.companyId} onChange={(event) => handleFormChange('companyId', event.target.value)} disabled={Boolean(editingTemplate)}>
                    <option value="">선택</option>
                    {data.create.companies.map((company) => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                </label>
              ) : null}
              <label>
                <span>서류 종류</span>
                <select value={form.documentType} onChange={(event) => handleFormChange('documentType', event.target.value)}>
                  {documentTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>서류명</span>
                <input value={form.name} onChange={(event) => handleFormChange('name', event.target.value)} />
              </label>
              <label>
                <span>설명</span>
                <textarea value={form.description} onChange={(event) => handleFormChange('description', event.target.value)} rows={4} />
              </label>
              <label>
                <span>{editingTemplate ? '파일 교체' : '파일'}</span>
                <input accept=".xlsx,.xls" onChange={(event) => setFile(event.target.files?.[0] ?? null)} type="file" />
              </label>
              {editingTemplate?.fileName ? <small>현재 파일: {editingTemplate.fileName}</small> : null}
              {templateVariableGroups.length > 0 ? (
                <div className="document-variable-panel">
                  <div className="section-heading-row compact">
                    <div>
                      <p className="eyebrow">Variables</p>
                      <h3>사용 가능한 템플릿 변수</h3>
                    </div>
                  </div>
                  <div className="document-variable-groups">
                    {templateVariableGroups.map((group) => (
                      <div className="document-variable-group" key={group.label}>
                        <h4>{group.label}</h4>
                        <div className="document-variable-chip-list">
                          {group.variables.map((variable) => (
                            <button
                              className={copiedVariableToken === variable.token ? 'copied' : ''}
                              key={variable.token}
                              onClick={() => handleVariableCopy(variable.token)}
                              type="button"
                            >
                              {copiedVariableToken === variable.token ? <Check size={13} /> : <Copy size={13} />}
                              <span>{variable.display || variable.token}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              <label className="checkbox-row">
                <input checked={form.isDefault} onChange={(event) => handleFormChange('isDefault', event.target.checked)} type="checkbox" />
                <span>기본 템플릿으로 설정</span>
              </label>
              <button className="primary-button" disabled={saving || !canCreate && !editingTemplate} type="submit">
                {saving ? '저장 중' : '저장'}
              </button>
              {!canCreate && !editingTemplate ? <p className="form-error">{data?.create.message}</p> : null}
            </form>
          ) : (
            <div className="document-summary-panel">
              <h3>연결 화면</h3>
              <div className="button-stack">
                <a className="route-secondary-action" href={data?.links.scheduleList || '/schedules/'}>일정 목록</a>
                <a className="route-secondary-action" href={data?.links.scheduleCalendar || '/schedules/calendar/'}>일정 캘린더</a>
              </div>
            </div>
          )}

          <div className="document-summary-panel document-generation-panel">
            <h3>최근 생성 이력</h3>
            {recentGenerations.length ? (
              <div className="document-generation-list">
                {recentGenerations.map((generation) => {
                  const customerLine = [
                    generation.customerCompany,
                    generation.departmentName,
                    generation.customerName,
                  ].filter(Boolean).join(' · ');
                  const cardBody = (
                    <>
                      <div className="document-generation-card-head">
                        <span>{generation.quoteGroupLabel ? `${generation.quoteGroupLabel} ${generation.documentTypeLabel}` : generation.documentTypeLabel}</span>
                        <strong>{generation.transactionNumber}</strong>
                      </div>
                      <div className="document-generation-card-meta">
                        <span>{generation.outputFormatLabel}</span>
                        <span>{formatDateTimeLabel(generation.createdAt)}</span>
                      </div>
                      <p>{customerLine || '연결된 고객 정보가 없습니다.'}</p>
                      <small>
                        {[generation.createdBy, generation.schedule.visitDate ? `일정 ${formatDateLabel(generation.schedule.visitDate)}` : ''].filter(Boolean).join(' · ')}
                      </small>
                    </>
                  );
                  return generation.schedule.href ? (
                    <a className="document-generation-card" href={generation.schedule.href} key={generation.id}>
                      {cardBody}
                    </a>
                  ) : (
                    <div className="document-generation-card" key={generation.id}>
                      {cardBody}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state compact">최근 생성된 서류가 없습니다.</div>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}

function ProductManagementPage({
  data,
  loading,
  onOrderChange,
  onPageChange,
  onQueryChange,
  onReload,
  onSortChange,
  onStatusChange,
  order,
  page,
  query,
  routeData,
  sort,
  status,
}: {
  data: ProductManagementData | null;
  loading: boolean;
  onOrderChange: (value: ProductSortOrder) => void;
  onPageChange: (value: number) => void;
  onQueryChange: (value: string) => void;
  onReload: () => Promise<ProductManagementData | null>;
  onSortChange: (value: ProductSortField) => void;
  onStatusChange: (value: string) => void;
  order: ProductSortOrder;
  page: number;
  query: string;
  routeData: PipelineData;
  sort: ProductSortField;
  status: string;
}) {
  const [formOpen, setFormOpen] = useState(() => shouldOpenCreatePanel());
  const [editingProduct, setEditingProduct] = useState<ProductManagementItem | null>(null);
  const [form, setForm] = useState<ProductFormState>(() => makeEmptyProductForm());
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [formMessage, setFormMessage] = useState('');
  const [bulkText, setBulkText] = useState('');
  const [bulkSaving, setBulkSaving] = useState(false);
  const [bulkResult, setBulkResult] = useState<ProductBulkUpsertResult | null>(null);
  const [bulkError, setBulkError] = useState('');
  const [importSaving, setImportSaving] = useState(false);
  const [importResult, setImportResult] = useState<ProductBulkUpsertResult | null>(null);
  const [importError, setImportError] = useState('');
  const [deleteText, setDeleteText] = useState('');
  const [deleteSaving, setDeleteSaving] = useState(false);
  const [deleteResult, setDeleteResult] = useState<ProductBulkDeleteResult | null>(null);
  const [deleteError, setDeleteError] = useState('');
  const [deleteReferenceReplacements, setDeleteReferenceReplacements] = useState<Record<string, string>>({});
  const [deleteReplacementOptions, setDeleteReplacementOptions] = useState<ProductOption[]>([]);
  const [deleteReplacementLoading, setDeleteReplacementLoading] = useState(false);
  const [deleteReplacementError, setDeleteReplacementError] = useState('');
  const [deleteReplacementSearch, setDeleteReplacementSearch] = useState('');
  const [deleteReplacementMessage, setDeleteReplacementMessage] = useState('');
  const [replacingReferenceKey, setReplacingReferenceKey] = useState('');
  const [handledProductAction, setHandledProductAction] = useState('');
  const productImportInputRef = useRef<HTMLInputElement | null>(null);
  const productFormPanelRef = useRef<HTMLFormElement | null>(null);

  const products = data?.products ?? [];
  const pagination = data?.pagination;
  const canManage = Boolean(data?.scope.canManage);
  const productRouteActions = data && !canManage
    ? routeMeta.products.actions.filter((action) => action.href !== '/products/?create=1')
    : routeMeta.products.actions;
  const pastedProducts = useMemo(() => parseProductPasteRows(bulkText), [bulkText]);
  const deleteCodes = useMemo(() => parseProductDeleteCodes(deleteText), [deleteText]);
  const replaceableDeleteRows = useMemo(() => (
    (deleteResult?.results ?? []).filter((row) => row.status === 'blocked' && row.canReplace)
  ), [deleteResult]);

  useGuidedPanelFocus(formOpen, productFormPanelRef, `product-${editingProduct?.id || 'new'}`);

  useEffect(() => {
    if (!data || canManage || !formOpen) {
      return;
    }
    setFormOpen(false);
    setEditingProduct(null);
    setFormError('');
    setFormMessage('');
  }, [canManage, data, formOpen]);

  useEffect(() => {
    if (!data || !canManage || !products.length) {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const productId = Number(params.get('product') || 0);
    const action = params.get('edit') === '1' ? 'edit' : params.get('delete') === '1' ? 'delete' : '';
    const signature = productId && action ? `${productId}:${action}` : '';
    if (!signature || handledProductAction === signature) {
      return;
    }
    const product = products.find((item) => item.id === productId);
    if (!product) {
      return;
    }
    setHandledProductAction(signature);
    if (action === 'edit') {
      openEdit(product);
    } else if (action === 'delete') {
      setDeleteText(product.productCode);
      setDeleteResult(null);
      setDeleteError('');
    }
    ['product', 'edit', 'delete'].forEach((key) => params.delete(key));
    const queryString = params.toString();
    window.history.replaceState(null, '', `/products/${queryString ? `?${queryString}` : ''}`);
  }, [canManage, data, handledProductAction, products]);

  useEffect(() => {
    if (!replaceableDeleteRows.length || deleteReplacementOptions.length) {
      return;
    }

    let active = true;
    setDeleteReplacementLoading(true);
    setDeleteReplacementError('');
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    loadProducts('', { limit: 80, signal: controller.signal })
      .then((options) => {
        if (active) {
          setDeleteReplacementOptions((previous) => mergeProductOptions(previous, options));
          if (!options.length) {
            setDeleteReplacementError('선택 가능한 활성 제품이 없습니다. 제품을 먼저 등록하거나 활성화하세요.');
          } else {
            setDeleteReplacementMessage(`최근 품번 기준 ${formatNumber(options.length)}건을 불러왔습니다. 필요한 제품이 없으면 검색하세요.`);
          }
        }
      })
      .catch((error) => {
        if (active) {
          setDeleteReplacementError(error instanceof Error && error.name === 'AbortError'
            ? '대체 제품 목록 조회가 지연되었습니다. 품번/제품명으로 검색하세요.'
            : error instanceof Error ? error.message : '대체 제품 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        window.clearTimeout(timeout);
        if (active) {
          setDeleteReplacementLoading(false);
        }
      });

    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [deleteReplacementOptions.length, replaceableDeleteRows.length]);

  const handleDeleteReplacementSearch = async () => {
    const search = deleteReplacementSearch.trim();
    if (deleteReplacementLoading) return;
    if (search.length < 2) {
      setDeleteReplacementError('품번, 제품설명, 규격 중 2글자 이상 입력하세요.');
      setDeleteReplacementMessage('');
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    setDeleteReplacementLoading(true);
    setDeleteReplacementError('');
    setDeleteReplacementMessage('');
    try {
      const options = await loadProducts(search, { limit: 80, signal: controller.signal });
      setDeleteReplacementOptions((previous) => mergeProductOptions(previous, options));
      setDeleteReplacementMessage(options.length
        ? `"${search}" 검색 결과 ${formatNumber(options.length)}건을 선택지에 추가했습니다.`
        : `"${search}" 검색 결과가 없습니다.`);
    } catch (error) {
      setDeleteReplacementError(error instanceof Error && error.name === 'AbortError'
        ? '제품 검색이 지연되었습니다. 더 구체적인 품번으로 다시 검색하세요.'
        : error instanceof Error ? error.message : '제품 검색에 실패했습니다.');
    } finally {
      window.clearTimeout(timeout);
      setDeleteReplacementLoading(false);
    }
  };

  const openCreate = () => {
    setEditingProduct(null);
    setForm(makeEmptyProductForm());
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const openEdit = (product: ProductManagementItem) => {
    setEditingProduct(product);
    setForm(makeProductForm(product));
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingProduct(null);
    setFormError('');
  };

  const handleFormChange = (field: keyof ProductFormState, value: string | boolean) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setFormError('');
  };

  const handleSort = (field: ProductSortField) => {
    if (sort === field) {
      onOrderChange(order === 'asc' ? 'desc' : 'asc');
    } else {
      onSortChange(field);
      onOrderChange(field === 'updatedAt' || field === 'price' ? 'desc' : 'asc');
    }
    onPageChange(1);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (saving) return;
    const payload = productFormToPayload(form);
    const price = Number(payload.standardPrice);
    if (!payload.productCode) {
      setFormError('품번을 입력하세요.');
      return;
    }
    if (!Number.isFinite(price) || price < 0) {
      setFormError('기준단가는 0 이상 숫자로 입력하세요.');
      return;
    }

    setSaving(true);
    setFormError('');
    setFormMessage('');
    try {
      const result = await saveProduct(payload, editingProduct?.id);
      setFormMessage(result.message || '제품을 저장했습니다.');
      setForm(makeEmptyProductForm());
      setEditingProduct(null);
      setFormOpen(false);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '제품 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkUpsert = async () => {
    if (bulkSaving) return;
    if (!pastedProducts.length) {
      setBulkError('붙여넣은 제품 데이터가 없습니다.');
      return;
    }
    setBulkSaving(true);
    setBulkError('');
    setBulkResult(null);
    try {
      const result = await bulkUpsertProducts(pastedProducts);
      setBulkResult(result);
      if (result.errorCount > 0) {
        setBulkError(result.message);
      }
      await onReload();
    } catch (error) {
      setBulkError(error instanceof Error ? error.message : '일괄 반영에 실패했습니다.');
    } finally {
      setBulkSaving(false);
    }
  };

  const handleProductExcelImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    event.target.value = '';
    if (!file || importSaving) return;
    setImportSaving(true);
    setImportError('');
    setImportResult(null);
    try {
      const result = await importProductsExcel(file, data?.links.excelImport || '/reporting/api/products/import.xlsx');
      setImportResult(result);
      if (result.errorCount > 0) {
        setImportError(result.message);
      }
      await onReload();
    } catch (error) {
      setImportError(error instanceof Error ? error.message : '엑셀 업로드에 실패했습니다.');
    } finally {
      setImportSaving(false);
    }
  };

  const handleBulkDelete = async () => {
    if (deleteSaving) return;
    if (!deleteCodes.length) {
      setDeleteError('삭제할 품번을 붙여넣으세요.');
      return;
    }
    if (!window.confirm(`${deleteCodes.length}개 품번을 삭제 처리할까요? 이미 사용된 제품은 삭제되지 않습니다.`)) {
      return;
    }
    setDeleteSaving(true);
    setDeleteError('');
    setDeleteReplacementError('');
    setDeleteReplacementMessage('');
    setDeleteReferenceReplacements({});
    setDeleteResult(null);
    try {
      const result = await bulkDeleteProducts(deleteCodes);
      setDeleteResult(result);
      await onReload();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '일괄 삭제에 실패했습니다.');
    } finally {
      setDeleteSaving(false);
    }
  };

  const productDeleteReferenceKey = (productCode: string, reference: ProductDeleteReference) => (
    `${productCode}:${reference.referenceType}:${reference.referenceId}`
  );

  const handleDeleteReferenceReplacementChange = (
    productCode: string,
    reference: ProductDeleteReference,
    replacementProductId: string,
  ) => {
    const referenceKey = productDeleteReferenceKey(productCode, reference);
    setDeleteReferenceReplacements((previous) => ({
      ...previous,
      [referenceKey]: replacementProductId,
    }));
    setDeleteError('');
    setDeleteReplacementError('');
  };

  const handleReplaceProductReference = async (productCode: string, reference: ProductDeleteReference) => {
    if (deleteSaving || replacingReferenceKey) return;
    const referenceKey = productDeleteReferenceKey(productCode, reference);
    const replacementId = Number(deleteReferenceReplacements[referenceKey] || 0);
    if (!replacementId) {
      setDeleteError(`${productCode}의 ${reference.itemName || '품목'} 대체 제품을 선택하세요.`);
      return;
    }
    const replacement = deleteReplacementOptions.find((option) => option.id === replacementId);
    if (!replacement) {
      setDeleteError('대체 제품을 찾을 수 없습니다.');
      return;
    }
    if (replacement.productCode === productCode) {
      setDeleteError(`${productCode} 자신은 대체 제품으로 사용할 수 없습니다.`);
      return;
    }

    setReplacingReferenceKey(referenceKey);
    setDeleteError('');
    try {
      const result = await replaceProductReference({
        productCode,
        referenceType: reference.referenceType,
        referenceId: reference.referenceId,
        replacementProductId: replacementId,
      });
      setDeleteResult((previous) => {
        const previousResults = previous?.results ?? [];
        const hasExistingRow = previousResults.some((row) => row.productCode === result.productCode);
        const nextResults = hasExistingRow
          ? previousResults.map((row) => (row.productCode === result.productCode ? result.result : row))
          : [result.result, ...previousResults];
        return {
          success: true,
          deletedCount: nextResults.filter((row) => row.status === 'deleted').length,
          blockedCount: nextResults.filter((row) => row.status === 'blocked').length,
          missingCount: nextResults.filter((row) => row.status === 'missing').length,
          replacedCount: (previous?.replacedCount ?? 0) + 1,
          results: nextResults,
          message: result.message,
        };
      });
      setDeleteReferenceReplacements((previous) => {
        const next = { ...previous };
        delete next[referenceKey];
        return next;
      });
      if (result.deletedOriginal) {
        await onReload();
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '품목 대체에 실패했습니다.');
    } finally {
      setReplacingReferenceKey('');
    }
  };

  const renderSortButton = (field: ProductSortField, label: string) => (
    <button
      className={`product-sort-button ${sort === field ? 'active' : ''}`.trim()}
      onClick={() => handleSort(field)}
      type="button"
    >
      {label}
      {sort === field ? <span>{order === 'asc' ? '↑' : '↓'}</span> : null}
    </button>
  );

  return (
    <section className="products-page">
      <WorkspaceRoutePage actions={productRouteActions} data={routeData} view="products" />
      {data?.source === 'unavailable' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>제품관리 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-metric-grid customers-metric-grid">
        <DashboardMetricCard label="전체 제품" value={`${formatNumber(data?.metrics.totalProducts ?? 0)}건`} detail={data?.scope.label || '제품 기준'} icon={Archive} tone="blue" />
        <DashboardMetricCard label="활성" value={`${formatNumber(data?.metrics.activeProducts ?? 0)}건`} detail="견적/납품 선택 가능" icon={CheckCircle2} tone="green" />
        <DashboardMetricCard label="비활성" value={`${formatNumber(data?.metrics.inactiveProducts ?? 0)}건`} detail="목록 보존" icon={AlertTriangle} tone="amber" />
        <DashboardMetricCard label="검색 결과" value={`${formatNumber(data?.metrics.filteredProducts ?? 0)}건`} detail="현재 필터" icon={Search} tone="teal" />
      </div>

      <div className="products-toolbar customers-filter-bar">
        <label className="customers-search">
          <Search size={16} />
          <input
            onChange={(event) => {
              onQueryChange(event.target.value);
              onPageChange(1);
            }}
            placeholder="품번, 제품설명, 규격 검색"
            value={query}
          />
        </label>
        <select
          value={status}
          onChange={(event) => {
            onStatusChange(event.target.value);
            onPageChange(1);
          }}
        >
          <option value="">전체 상태</option>
          <option value="active">활성</option>
          <option value="inactive">비활성</option>
        </select>
        <button className="route-secondary-action" onClick={() => void onReload()} type="button">
          <RefreshCw size={16} />
          새로고침
        </button>
        <a className="route-secondary-action" href={data?.links.excelDownload || '/reporting/api/products/export.xlsx'}>
          <Download size={16} />
          엑셀
        </a>
        {canManage ? (
          <button className="route-primary-action" onClick={openCreate} type="button">
            <Plus size={16} />
            제품 등록
          </button>
        ) : null}
      </div>

      {formOpen ? (
        <form className="dashboard-panel notes-create-form product-editor-panel" onSubmit={handleSubmit} ref={productFormPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <p className="eyebrow">{editingProduct ? 'Edit' : 'Create'}</p>
              <h2>{editingProduct ? '제품 수정' : '제품 등록'}</h2>
            </div>
            <button aria-label="닫기" className="icon-button" onClick={closeForm} type="button">
              <X size={17} />
            </button>
          </div>
          <div className="notes-create-grid product-form-grid">
            <label>
              <span>품번</span>
              <input value={form.productCode} onChange={(event) => handleFormChange('productCode', event.target.value)} />
            </label>
            <label>
              <span>제품설명</span>
              <input value={form.description} onChange={(event) => handleFormChange('description', event.target.value)} />
            </label>
            <label>
              <span>규격</span>
              <input value={form.specification} onChange={(event) => handleFormChange('specification', event.target.value)} />
            </label>
            <label>
              <span>단위</span>
              <input value={form.unit} onChange={(event) => handleFormChange('unit', event.target.value)} />
            </label>
            <label>
              <span>기준단가</span>
              <input inputMode="numeric" value={form.standardPrice} onChange={(event) => handleFormChange('standardPrice', event.target.value)} />
            </label>
            <label className="checkbox-row product-active-row">
              <input checked={form.isActive} onChange={(event) => handleFormChange('isActive', event.target.checked)} type="checkbox" />
              <span>활성 제품</span>
            </label>
          </div>
          {formError ? <p className="form-error">{formError}</p> : null}
          {formMessage ? <p className="form-success">{formMessage}</p> : null}
          <div className="notes-create-actions">
            <button className="route-secondary-action" onClick={closeForm} type="button">취소</button>
            <button className="route-primary-action" disabled={saving} type="submit">
              {saving ? '저장 중' : '저장'}
            </button>
          </div>
        </form>
      ) : null}

      <div className={`products-layout ${canManage ? '' : 'readonly'}`.trim()}>
        <section className="dashboard-panel products-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <h2>제품 목록</h2>
              <span>{loading ? '불러오는 중' : `현재 ${formatNumber(products.length)}건 표시`}</span>
            </div>
          </div>

          {loading && !data ? (
            <DashboardEmpty label="제품 데이터를 불러오는 중입니다" />
          ) : products.length ? (
            <>
              <div className="customers-table-wrap products-table-wrap">
                <table className="customers-table products-table">
                  <thead>
                    <tr>
                      <th>{renderSortButton('code', '품번')}</th>
                      <th>{renderSortButton('description', '제품설명')}</th>
                      <th>{renderSortButton('specification', '규격')}</th>
                      <th>{renderSortButton('unit', '단위')}</th>
                      <th>{renderSortButton('price', '기준단가')}</th>
                      <th>{renderSortButton('status', '상태')}</th>
                      <th>{renderSortButton('quoteCount', '견적')}</th>
                      <th>{renderSortButton('deliveryCount', '판매')}</th>
                      <th>{renderSortButton('updatedAt', '수정일')}</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td>
                          <strong>{product.productCode}</strong>
                          <small className="customer-muted-cell">{product.createdBy}</small>
                        </td>
                        <td>{product.description || '-'}</td>
                        <td>{product.specification || '-'}</td>
                        <td>{product.unit || 'EA'}</td>
                        <td>{formatWon(product.standardPrice)}</td>
                        <td>
                          <span className={`product-status ${product.isActive ? 'active' : 'inactive'}`}>{product.isActive ? '활성' : '비활성'}</span>
                        </td>
                        <td>{formatNumber(product.quoteCount)}</td>
                        <td>{formatNumber(product.deliveryCount)}</td>
                        <td>{product.updatedAt ? formatDateTimeLabel(product.updatedAt) : '-'}</td>
                        <td>
                          <div className="product-row-actions">
                            {canManage ? (
                              <>
                                <button className="route-secondary-action" onClick={() => openEdit(product)} type="button">수정</button>
                              </>
                            ) : (
                              <span className="customer-muted-cell">읽기 전용</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="products-pagination">
                <button className="route-secondary-action" disabled={!pagination?.hasPrevious} onClick={() => onPageChange(Math.max(page - 1, 1))} type="button">
                  <ChevronLeft size={16} />
                  이전
                </button>
                <span>{formatNumber(pagination?.page ?? page)} / {formatNumber(pagination?.totalPages ?? 1)} 페이지</span>
                <button className="route-secondary-action" disabled={!pagination?.hasNext} onClick={() => onPageChange(page + 1)} type="button">
                  다음
                  <ChevronRight size={16} />
                </button>
              </div>
            </>
          ) : (
            <DashboardEmpty label="조건에 맞는 제품이 없습니다" />
          )}
        </section>

        {canManage ? (
        <aside className="products-side">
          <section className="dashboard-panel product-bulk-panel">
            <div className="dashboard-panel-heading">
              <div>
                <p className="eyebrow">Ecount / Excel</p>
                <h2>붙여넣기 반영</h2>
              </div>
              <div className="product-import-actions">
                <input
                  accept=".xlsx"
                  hidden
                  onChange={handleProductExcelImport}
                  ref={productImportInputRef}
                  type="file"
                />
                <button
                  className="icon-button"
                  disabled={importSaving}
                  onClick={() => productImportInputRef.current?.click()}
                  title="엑셀 업로드"
                  type="button"
                >
                  {importSaving ? <Loader2 className="spin-icon" size={16} /> : <Upload size={16} />}
                </button>
              </div>
            </div>
            <textarea
              onChange={(event) => {
                setBulkText(event.target.value);
                setBulkError('');
              }}
              placeholder={'품번\t제품설명\t규격\t단위\t출고단가'}
              rows={8}
              value={bulkText}
            />
            <div className="product-bulk-summary">
              <span>인식 {formatNumber(pastedProducts.length)}건</span>
              {pastedProducts.slice(0, 3).map((item) => (
                <small key={item.productCode}>{item.productCode} · {item.unit} · {formatWon(Number(item.standardPrice) || 0)}</small>
              ))}
            </div>
            {importError ? <p className="form-error">{importError}</p> : null}
            {importResult && !importError ? <p className="form-success">{importResult.message}</p> : null}
            {bulkError ? <p className="form-error">{bulkError}</p> : null}
            {bulkResult && !bulkError ? <p className="form-success">{bulkResult.message}</p> : null}
            <button className="route-primary-action" disabled={bulkSaving || !pastedProducts.length} onClick={handleBulkUpsert} type="button">
              {bulkSaving ? '반영 중' : '등록/갱신'}
            </button>
          </section>

          <section className="dashboard-panel product-bulk-panel">
            <div className="dashboard-panel-heading">
              <div>
                <p className="eyebrow">Bulk Delete</p>
                <h2>품번 일괄 삭제</h2>
              </div>
              <Trash2 size={18} />
            </div>
            <textarea
              onChange={(event) => {
                setDeleteText(event.target.value);
                setDeleteError('');
              }}
              placeholder={'삭제할 품번을 한 줄에 하나씩 붙여넣기'}
              rows={7}
              value={deleteText}
            />
            <div className="product-bulk-summary">
              <span>삭제 대상 {formatNumber(deleteCodes.length)}건</span>
              {deleteCodes.slice(0, 4).map((code) => <small key={code}>{code}</small>)}
            </div>
            {deleteError ? <p className="form-error">{deleteError}</p> : null}
            {deleteResult ? <p className="form-success">{deleteResult.message}</p> : null}
            {replaceableDeleteRows.length > 0 ? (
              <div className="product-delete-replacement-panel">
                <div>
                  <strong>차단 품목 개별 대체</strong>
                  <span>견적/납품에 사용된 품목마다 대체 제품을 선택하고 한 건씩 이동합니다. 마지막 품목이 이동되면 원제품이 삭제됩니다.</span>
                </div>
                {deleteReplacementError ? <p className="form-error">{deleteReplacementError}</p> : null}
                {deleteReplacementMessage ? <p className="form-success">{deleteReplacementMessage}</p> : null}
                <div className="product-delete-replacement-search">
                  <input
                    onChange={(event) => {
                      setDeleteReplacementSearch(event.target.value);
                      setDeleteReplacementError('');
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault();
                        void handleDeleteReplacementSearch();
                      }
                    }}
                    placeholder="대체 제품 품번, 설명, 규격 검색"
                    value={deleteReplacementSearch}
                  />
                  <button
                    className="route-secondary-action"
                    disabled={deleteReplacementLoading}
                    onClick={() => void handleDeleteReplacementSearch()}
                    type="button"
                  >
                    검색
                  </button>
                </div>
                {deleteReplacementLoading ? (
                  <div className="product-delete-replacement-loading">
                    <Loader2 className="spin-icon" size={15} />
                    <span>대체 제품 목록을 불러오는 중입니다. 오래 걸리면 품번으로 검색하세요.</span>
                  </div>
                ) : (
                  <div className="product-delete-replacement-list">
                    {replaceableDeleteRows.map((row) => {
                      const replacementOptions = deleteReplacementOptions.filter((option) => (
                        option.productCode !== row.productCode &&
                        !deleteCodes.includes(option.productCode)
                      ));
                      return (
                        <div className="product-delete-reference-group" key={row.productCode}>
                          <div className="product-delete-reference-heading">
                            <strong>{row.productCode}</strong>
                            <span>납품/견적 품목 {formatNumber(row.deliveryItemCount ?? 0)}건 · 레거시 견적 {formatNumber(row.quoteItemCount ?? 0)}건</span>
                          </div>
                          {row.hasMoreReferences ? <small>표시된 품목 외 추가 참조가 있습니다. 표시된 항목부터 대체한 뒤 다시 확인하세요.</small> : null}
                          {(row.references ?? []).length ? (
                            (row.references ?? []).map((reference) => {
                              const referenceKey = productDeleteReferenceKey(row.productCode, reference);
                              const selectedReplacement = deleteReferenceReplacements[referenceKey] || '';
                              const isReplacing = replacingReferenceKey === referenceKey;
                              return (
                                <div className="product-delete-reference-row" key={referenceKey}>
                                  <div>
                                    <strong>{reference.itemName || row.productCode}</strong>
                                    <span>{[
                                      reference.scheduleTypeLabel || (reference.referenceType === 'quoteItem' ? '레거시 견적' : '품목'),
                                      reference.scheduleId ? `일정 #${reference.scheduleId}` : '',
                                      reference.historyId && !reference.scheduleId ? `영업노트 #${reference.historyId}` : '',
                                      reference.quoteNumber ? `견적 ${reference.quoteNumber}` : '',
                                      reference.customerName,
                                      reference.companyName,
                                      reference.departmentName,
                                      reference.scheduleDate ? formatDateLabel(reference.scheduleDate) : '',
                                      reference.quoteGroupLabel,
                                      `수량 ${formatNumber(reference.quantity)}${reference.unit ? reference.unit : ''}`,
                                    ].filter(Boolean).join(' · ')}</span>
                                  </div>
                                  <select
                                    disabled={Boolean(replacingReferenceKey)}
                                    onChange={(event) => handleDeleteReferenceReplacementChange(row.productCode, reference, event.target.value)}
                                    value={selectedReplacement}
                                  >
                                    <option value="">대체 제품 선택</option>
                                    {replacementOptions.map((option) => (
                                      <option key={option.id} value={option.id}>
                                        {option.productCode} · {option.description || option.specification || option.unit}
                                      </option>
                                    ))}
                                  </select>
                                  <button
                                    className="route-secondary-action"
                                    disabled={deleteSaving || Boolean(replacingReferenceKey) || !selectedReplacement}
                                    onClick={() => handleReplaceProductReference(row.productCode, reference)}
                                    type="button"
                                  >
                                    {isReplacing ? '처리 중' : '이 품목 대체'}
                                  </button>
                                </div>
                              );
                            })
                          ) : (
                            <small>표시할 품목 참조가 없습니다. 다시 삭제 실행으로 상태를 확인하세요.</small>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : null}
            <button className="route-secondary-action danger" disabled={deleteSaving || !deleteCodes.length} onClick={handleBulkDelete} type="button">
              {deleteSaving ? '삭제 중' : '삭제 실행'}
            </button>
          </section>
        </aside>
        ) : null}
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
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(currentView === 'dashboard');
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
  const [demoCustomer, setDemoCustomer] = useState(() => new URLSearchParams(window.location.search).get('customer') || '');
  const [demoDepartment, setDemoDepartment] = useState(() => new URLSearchParams(window.location.search).get('department') || '');
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
  const [customerCreateOpen, setCustomerCreateOpen] = useState(false);
  const [customerCreateForm, setCustomerCreateForm] = useState<CustomerCreateFormState>(() => makeEmptyCustomerCreateForm());
  const [customerCreating, setCustomerCreating] = useState(false);
  const [customerCreateError, setCustomerCreateError] = useState('');
  const [customerCreateMessage, setCustomerCreateMessage] = useState('');
  const [customerCreatedDetailHref, setCustomerCreatedDetailHref] = useState('');
  const [customerCompanyCreateName, setCustomerCompanyCreateName] = useState('');
  const [customerDepartmentCreateName, setCustomerDepartmentCreateName] = useState('');
  const [customerCompanyCreating, setCustomerCompanyCreating] = useState(false);
  const [customerDepartmentCreating, setCustomerDepartmentCreating] = useState(false);
  const [customerCompanyEditId, setCustomerCompanyEditId] = useState<number | null>(null);
  const [customerCompanyEditName, setCustomerCompanyEditName] = useState('');
  const [customerDepartmentEditId, setCustomerDepartmentEditId] = useState<number | null>(null);
  const [customerDepartmentEditName, setCustomerDepartmentEditName] = useState('');
  const [customerManagementSavingKey, setCustomerManagementSavingKey] = useState('');
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
    if (currentView !== 'customers' || customerDetailId || accountDetailId || !customersData?.create.canCreate) {
      return;
    }
    const firstCompanyId = customersData.create.companies[0]?.id;
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
      };
    });
  }, [accountDetailId, currentView, customerDetailId, customersData]);

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
  const refreshCustomersData = async () => {
    const data = await loadCustomersData({
      q: customerQuery,
      owner: customerOwner,
      stage: customerStage,
      company: customerCompany,
      grade: customerGrade,
      level: customerLevel,
      mode: customerRowMode,
      page: customerPage,
      pageSize: customerPageSize,
    });
    setCustomersData(data);
    return data;
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
  const handleCustomerCreateOpenChange = (open: boolean) => {
    setCustomerCreateOpen(open);
    setCustomerCreateError('');
    setCustomerCompanyEditId(null);
    setCustomerCompanyEditName('');
    setCustomerDepartmentEditId(null);
    setCustomerDepartmentEditName('');
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
  const handleCustomerCompanyEditStart = (company: CustomerCompanyManageOption) => {
    setCustomerCompanyEditId(company.id);
    setCustomerCompanyEditName(company.name);
    setCustomerDepartmentEditId(null);
    setCustomerDepartmentEditName('');
    setCustomerCreateError('');
    setCustomerCreateMessage('');
  };
  const handleCustomerCompanyEditCancel = () => {
    setCustomerCompanyEditId(null);
    setCustomerCompanyEditName('');
  };
  const handleUpdateCustomerCompany = async (company: CustomerCompanyManageOption) => {
    const name = customerCompanyEditName.trim();
    if (!customersData || customerManagementSavingKey || !company.canManage || !name) {
      return;
    }
    setCustomerManagementSavingKey(`company-${company.id}`);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const result = await updateCompanyRecord(company.id, name, company.updateUrl);
      await refreshCustomersData();
      setCustomerCompanyEditId(null);
      setCustomerCompanyEditName('');
      setCustomerCreateMessage(result.message || '업체/학교 정보가 수정되었습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '업체/학교 수정에 실패했습니다.');
    } finally {
      setCustomerManagementSavingKey('');
    }
  };
  const handleDeleteCustomerCompany = async (company: CustomerCompanyManageOption) => {
    if (!customersData || customerManagementSavingKey || !company.canManage) {
      return;
    }
    if (!company.canDelete) {
      setCustomerCreateError(company.deleteMessage || '연결 데이터가 있어 삭제할 수 없습니다.');
      return;
    }
    if (!window.confirm(`"${company.name}" 업체/학교를 삭제할까요?`)) {
      return;
    }
    setCustomerManagementSavingKey(`company-${company.id}`);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const result = await deleteCompanyRecord(company.id, company.deleteUrl);
      await refreshCustomersData();
      setCustomerCompanyEditId(null);
      setCustomerCompanyEditName('');
      setCustomerDepartmentEditId(null);
      setCustomerDepartmentEditName('');
      setCustomerCreateForm((previous) => (
        previous.companyId === String(company.id)
          ? { ...previous, companyId: '', departmentId: '' }
          : previous
      ));
      setCustomerCreateMessage(result.message || '업체/학교가 삭제되었습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '업체/학교 삭제에 실패했습니다.');
    } finally {
      setCustomerManagementSavingKey('');
    }
  };
  const handleCustomerDepartmentEditStart = (department: CustomerDepartmentManageOption) => {
    setCustomerDepartmentEditId(department.id);
    setCustomerDepartmentEditName(department.name);
    setCustomerCompanyEditId(null);
    setCustomerCompanyEditName('');
    setCustomerCreateError('');
    setCustomerCreateMessage('');
  };
  const handleCustomerDepartmentEditCancel = () => {
    setCustomerDepartmentEditId(null);
    setCustomerDepartmentEditName('');
  };
  const handleUpdateCustomerDepartment = async (department: CustomerDepartmentManageOption) => {
    const name = customerDepartmentEditName.trim();
    if (!customersData || customerManagementSavingKey || !department.canManage || !name) {
      return;
    }
    setCustomerManagementSavingKey(`department-${department.id}`);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const result = await updateDepartmentRecord(department.id, name, department.updateUrl);
      await refreshCustomersData();
      setCustomerDepartmentEditId(null);
      setCustomerDepartmentEditName('');
      setCustomerCreateMessage(result.message || '부서/연구실 정보가 수정되었습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '부서/연구실 수정에 실패했습니다.');
    } finally {
      setCustomerManagementSavingKey('');
    }
  };
  const handleDeleteCustomerDepartment = async (department: CustomerDepartmentManageOption) => {
    if (!customersData || customerManagementSavingKey || !department.canManage) {
      return;
    }
    if (!department.canDelete) {
      setCustomerCreateError(department.deleteMessage || '연결 데이터가 있어 삭제할 수 없습니다.');
      return;
    }
    if (!window.confirm(`"${department.companyName} - ${department.name}" 부서/연구실을 삭제할까요?`)) {
      return;
    }
    setCustomerManagementSavingKey(`department-${department.id}`);
    setCustomerCreateError('');
    setCustomerCreateMessage('');
    setCustomerCreatedDetailHref('');
    try {
      const result = await deleteDepartmentRecord(department.id, department.deleteUrl);
      await refreshCustomersData();
      setCustomerDepartmentEditId(null);
      setCustomerDepartmentEditName('');
      setCustomerCreateForm((previous) => (
        previous.departmentId === String(department.id)
          ? { ...previous, departmentId: '' }
          : previous
      ));
      setCustomerCreateMessage(result.message || '부서/연구실이 삭제되었습니다.');
    } catch (error) {
      setCustomerCreateError(error instanceof Error ? error.message : '부서/연구실 삭제에 실패했습니다.');
    } finally {
      setCustomerManagementSavingKey('');
    }
  };
  const resetCustomerCreateForm = (data: CustomersData | null) => {
    const nextForm = makeEmptyCustomerCreateForm();
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

    const payload: CustomerCreatePayload = {
      address: customerCreateForm.address.trim() || undefined,
      companyId,
      customerName: customerCreateForm.customerName.trim(),
      departmentId,
      email: customerCreateForm.email.trim() || undefined,
      manager: customerCreateForm.manager.trim() || undefined,
      notes: customerCreateForm.notes.trim() || undefined,
      phoneNumber: customerCreateForm.phoneNumber.trim() || undefined,
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
          departmentEditId={customerDepartmentEditId}
          departmentEditName={customerDepartmentEditName}
          departmentCreating={customerDepartmentCreating}
          detailData={customerDetailData}
          detailLoading={customerDetailLoading}
          companyEditId={customerCompanyEditId}
          companyEditName={customerCompanyEditName}
          company={customerCompany}
          grade={customerGrade}
          level={customerLevel}
          loading={customersLoading}
          managementSavingKey={customerManagementSavingKey}
          owner={customerOwner}
          page={customerPage}
          query={customerQuery}
          rowMode={customerRowMode}
          selectedCustomerId={customerDetailId || accountDetailId}
          selectedDetailMode={accountDetailId ? 'account' : 'customer'}
          stage={customerStage}
          onCompanyCreateNameChange={handleCustomerCompanyCreateNameChange}
          onCompanyCreateSubmit={handleCreateCustomerCompany}
          onCompanyDelete={handleDeleteCustomerCompany}
          onCompanyEditCancel={handleCustomerCompanyEditCancel}
          onCompanyEditNameChange={setCustomerCompanyEditName}
          onCompanyEditStart={handleCustomerCompanyEditStart}
          onCompanyEditSubmit={handleUpdateCustomerCompany}
          onCreateFormChange={handleCustomerCreateFormChange}
          onCreateOpenChange={handleCustomerCreateOpenChange}
          onCreateSubmit={handleCreateCustomerSubmit}
          onDepartmentDelete={handleDeleteCustomerDepartment}
          onDepartmentCreateNameChange={handleCustomerDepartmentCreateNameChange}
          onDepartmentCreateSubmit={handleCreateCustomerDepartment}
          onDepartmentEditCancel={handleCustomerDepartmentEditCancel}
          onDepartmentEditNameChange={setCustomerDepartmentEditName}
          onDepartmentEditStart={handleCustomerDepartmentEditStart}
          onDepartmentEditSubmit={handleUpdateCustomerDepartment}
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
          />
        )}
      </div>
    </AppShell>
  );
}
