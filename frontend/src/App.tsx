import {
  Activity,
  AlertTriangle,
  Archive,
  Bell,
  Bold,
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
  LogOut,
  Loader2,
  Inbox,
  ImagePlus,
  Italic,
  Link2,
  Mail,
  MessageSquareText,
  MoveUpRight,
  ArrowRightLeft,
  PanelRight,
  Pencil,
  Plus,
  RefreshCw,
  Reply,
  Search,
  Send,
  Sparkles,
  Star,
  Target,
  Trash2,
  Type,
  Underline,
  Upload,
  Users,
  Wrench,
  X,
} from 'lucide-react';
import { type ChangeEvent, type ClipboardEvent, type DragEvent, type FormEvent, type KeyboardEvent, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  DashboardData,
  DashboardHistoryItem,
  DashboardScheduleItem,
  CustomerAssetDirectoryData,
  CustomerAssetDirectoryItem,
  CustomerAssetSummary,
  CustomerAssetItem,
  CustomerAssetPayload,
  CustomerCalibrationRecord,
  CustomerCalibrationPayload,
  CustomerDetailData,
  CustomerAiDepartment,
  CustomerAiPainpoint,
  CustomerEditPayload,
  CustomerCreatePayload,
  CustomerServiceCase,
  CustomerServiceCasePayload,
  CustomersData,
  CustomerItem,
  DocumentTemplateItem,
  DocumentTemplateMutationPayload,
  DocumentTemplatesData,
  FollowupQuoteItem,
  FollowupQuoteItemsData,
  FollowupQuoteOption,
  MailAutoAttachment,
  MailInternalCcContact,
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
  ScheduleGeneratedDocument,
  ScheduleDocumentPreviewData,
  ScheduleFileItem,
  ScheduleEditPayload,
  ScheduleItem,
  SchedulePrepaymentSelectionPayload,
  AIWorkspaceAction,
  AIWorkspaceData,
  AIWorkspaceDepartment,
  AIWorkspaceDepartmentQuestionResponse,
  AIWorkspaceDraftType,
  AIWorkspaceActionDraftResponse,
  AIWorkspaceQuestionModel,
  AIWorkspaceQuestionScope,
  AIWorkspaceQuestionLog,
  AIWorkspaceQuestionLogDetailData,
  AIWorkspaceFollowupTarget,
  AIWorkspacePainpoint,
  AIWorkspacePromptTarget,
  NavigationData,
  NavigationItem,
  TaskFormPayload,
  TaskItem,
  TaskManagerAssignPayload,
  TaskManagerData,
  TaskRequestPayload,
  TasksData,
  WeeklyReportCreateData,
  WeeklyReportDetailData,
  WeeklyReportFormPayload,
  WeeklyReportsData,
  WeeklyReportSchedulesData,
  NoteCreatePayload,
  PersonalScheduleDetailData,
  PersonalSchedulePayload,
  addNoteReply,
  assignManagerTask,
  askAIWorkspaceDepartmentQuestion,
  bulkDeleteProducts,
  bulkUpsertProducts,
  cancelPrepayment as cancelCustomerPrepayment,
  createCompany as createCompanyRecord,
  createDepartment as createDepartmentRecord,
  createNote as createSalesNote,
  createPrepayment as createCustomerPrepayment,
  createTask,
  ScheduleCreatePayload,
  createCustomer as createCustomerRecord,
  createDocumentTemplate,
  generateAIWorkspaceActionDraft,
  createPersonalSchedule,
  changeManagerTaskStatus,
  changeTaskStatus,
  deletePrepayment as deleteCustomerPrepayment,
  createSchedule as createCustomerSchedule,
  deleteNoteFile,
  deleteNoteReply,
  deleteAIWorkspaceQuestionLog,
  deleteSchedule,
  deleteScheduleFile,
  deleteGeneratedDocument,
  deleteDocumentTemplate,
  deleteWeeklyReport,
  downloadScheduleDocument,
  generateWeeklyReportAiDraft,
  loadDashboardData,
  loadDocumentTemplatesData,
  loadCustomerAssetDirectoryData,
  loadCustomerDetailData,
  loadCustomersData,
  loadMailboxData,
  loadMailboxThreadData,
  loadNoteDetailData,
  loadNavigationData,
  loadNotesData,
  loadPrepaymentCreateData,
  loadPrepaymentCustomerData,
  loadPrepaymentDetailData,
  loadPrepayments,
  loadPrepaymentsData,
  loadProductManagementData,
  loadProducts,
  loadPersonalScheduleDetailData,
  loadScheduleCalendarData,
  loadScheduleDocumentPreview,
  loadScheduleDetailData,
  loadFollowupQuoteItems,
  loadSchedulesData,
  loadTaskManagerData,
  loadTasksData,
  loadAIWorkspaceData,
  loadAIWorkspaceQuestionLogDetailData,
  loadWeeklyReportCreateData,
  loadWeeklyReportDetailData,
  loadWeeklyReportsData,
  loadWeeklyReportSchedules,
  loadPipelineData,
  moveDealStage,
  normalizeCustomerAiDepartment,
  runAiDepartmentAnalysis,
  runMailboxAction,
  runMailboxSync,
  saveCustomerAsset,
  saveCustomerCalibration,
  saveCustomerServiceCase,
  sendMailboxEmail,
  submitAIWorkspaceActionFeedback,
  toggleNoteReviewed,
  transferPrepayment as transferCustomerPrepayment,
  updateCustomer as updateCustomerRecord,
  updateNote as updateSalesNote,
  updatePrepayment as updateCustomerPrepayment,
  updatePersonalSchedule,
  updateSchedule as updateCustomerSchedule,
  updateScheduleDeliveryItems,
  updateScheduleStatus,
  uploadMailboxEditorImage,
  uploadNoteFiles,
  uploadScheduleFiles,
  verifyAiPainpoint,
  replyMailboxEmail,
  replaceProductReference,
  requestTask,
  saveProduct,
  saveWeeklyReport,
  saveWeeklyReportManagerComment,
  toggleDocumentTemplateDefault,
  updateDocumentTemplate,
} from './api';
import { Deal, emptyPipelineData, PipelineData, PipelineStage, PriorityTask, StageSummary } from './mockData';

const navItems = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'assets', label: '장비', icon: Wrench, href: '/assets/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/pipeline/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/calendar/' },
  { id: 'tasks', label: '업무', icon: CheckCircle2, href: '/tasks/' },
  { id: 'mail', label: '메일', icon: Mail, href: '/mailbox/' },
  { id: 'weeklyReports', label: '주간보고', icon: ListChecks, href: '/weekly-reports/' },
  { id: 'documents', label: '서류', icon: FileSpreadsheet, href: '/documents/' },
  { id: 'products', label: '제품', icon: Archive, href: '/products/' },
  { id: 'prepayments', label: '선결제', icon: CircleDollarSign, href: '/prepayments/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

const navIconMap: Record<string, typeof LayoutDashboard> = {
  dashboard: LayoutDashboard,
  customers: Users,
  assets: Wrench,
  pipeline: Columns3,
  notes: FileText,
  schedules: CalendarDays,
  tasks: CheckCircle2,
  tasksManager: Users,
  mail: Mail,
  weeklyReports: ListChecks,
  documents: FileSpreadsheet,
  products: Archive,
  prepayments: CircleDollarSign,
  ai: Sparkles,
};

const scheduleCalendarUrl = '/schedules/calendar/';

type SavedView = 'priority' | 'thisWeek' | 'quoteDelay' | 'managerReview';
type MainView = 'dashboard' | 'customers' | 'assets' | 'pipeline' | 'notes' | 'schedules' | 'tasks' | 'mail' | 'weeklyReports' | 'documents' | 'products' | 'prepayments' | 'ai';

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
  scheduleId: string;
};

type NoteEditFormState = NoteCreateFormState & {
  deliveryAmount: string;
  deliveryItems: string;
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

type PersonalScheduleFormState = {
  title: string;
  content: string;
  scheduleDate: string;
  scheduleTime: string;
};

type TaskFormState = {
  title: string;
  description: string;
  dueDate: string;
  expectedDuration: string;
  assignedToId: string;
};

type TaskTab = 'my' | 'received' | 'requested';

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
  discountRate: string;
  discountUnitPrice: string;
  taxInvoiceIssued: boolean;
  quoteGroup: string;
  notes: string;
  sourceQuoteScheduleId: string;
  sourceQuoteItemId: string;
};

type ScheduleDeliveryEditField = 'productId' | 'productQuery' | 'itemName' | 'quantity' | 'unit' | 'unitPrice' | 'discountRate' | 'discountUnitPrice' | 'taxInvoiceIssued' | 'quoteGroup' | 'notes';

type ScheduleQuoteGroupNoteState = Record<string, string>;

type MailComposeFormState = {
  attachments: File[];
  autoAttachments: MailAutoAttachment[];
  autoAttachmentSeed: string;
  bodyHtml: string;
  bodyText: string;
  businessCardId: string;
  ccEmails: string;
  bccEmails: string;
  excludedAutoAttachmentKeys: string[];
  followupId: string;
  includeInternalCc: boolean;
  internalCcEmails: string[];
  scheduleId: string;
  subject: string;
  toEmail: string;
};

type MailComposeTextField = Exclude<keyof MailComposeFormState, 'attachments' | 'autoAttachments' | 'autoAttachmentSeed' | 'excludedAutoAttachmentKeys' | 'includeInternalCc' | 'internalCcEmails'>;

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

type CustomerAssetEditorMode = '' | 'asset' | 'service' | 'calibration';

type CustomerAssetFormState = {
  assetName: string;
  installLocation: string;
  modelName: string;
  notes: string;
  purchaseDate: string;
  serialNumber: string;
  status: string;
  warrantyUntil: string;
};

type CustomerServiceCaseFormState = {
  assetId: string;
  caseType: string;
  completedDate: string;
  dueDate: string;
  priority: string;
  receivedDate: string;
  resolution: string;
  serviceReport: File | null;
  status: string;
  symptom: string;
};

type CustomerCalibrationFormState = {
  assetId: string;
  calibrationDate: string;
  certificateFile: File | null;
  nextDueDate: string;
  notes: string;
  result: string;
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

const parseLocalDate = (value: string) => {
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) {
    return new Date();
  }
  return new Date(year, month - 1, day);
};

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

const shouldOpenCreatePanel = () => new URLSearchParams(window.location.search).get('create') === '1';

const makeEmptyWeeklyReportForm = (): WeeklyReportFormPayload => ({
  weekStart: '',
  weekEnd: '',
  title: '',
  activityNotes: '',
  quoteDeliveryNotes: '',
  otherNotes: '',
});

const makeEmptyTaskForm = (): TaskFormState => ({
  title: '',
  description: '',
  dueDate: '',
  expectedDuration: '',
  assignedToId: '',
});

const makeEmptyNoteCreateForm = (): NoteCreateFormState => ({
  actionType: 'customer_meeting',
  activityDate: localDateInputValue(),
  content: '',
  followupId: '',
  nextAction: '',
  nextActionDate: '',
  scheduleId: '',
});

const makeNoteEditForm = (note: NoteDetailItem | null): NoteEditFormState => ({
  actionType: note?.actionType || 'customer_meeting',
  activityDate: note?.meetingDate || note?.deliveryDate || note?.activityDate || '',
  content: note?.content || '',
  deliveryAmount: note?.deliveryAmount ? String(note.deliveryAmount) : '',
  deliveryItems: note?.deliveryItems || '',
  followupId: note?.followupId ? String(note.followupId) : '',
  nextAction: note?.nextAction || '',
  nextActionDate: note?.nextActionDate || '',
  scheduleId: note?.scheduleId ? String(note.scheduleId) : '',
  serviceStatus: note?.serviceStatus || 'received',
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

const scheduleNoteActionTypeOptions = [
  { value: 'customer_meeting', label: '고객 미팅' },
  { value: 'quote', label: '견적' },
  { value: 'delivery_schedule', label: '납품 일정' },
  { value: 'service', label: '서비스' },
];

const makeScheduleNoteCreateForm = (schedule: ScheduleDetailItem | null): NoteCreateFormState => ({
  actionType: scheduleActivityToNoteActionType(schedule?.activityType || ''),
  activityDate: schedule?.date || localDateInputValue(),
  content: '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  nextAction: '',
  nextActionDate: '',
  scheduleId: schedule?.id ? String(schedule.id) : '',
});

const makeEmptyScheduleCreateForm = (visitDate = localDateInputValue()): ScheduleCreateFormState => ({
  activityType: 'customer_meeting',
  expectedRevenue: '',
  followupId: '',
  location: '',
  notes: '',
  probability: '',
  visitDate,
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
  form.followupId = data?.create.customers[0]?.id ? String(data.create.customers[0].id) : '';
  return form;
};

const scheduleCreateFormToPayload = (form: ScheduleCreateFormState): { payload?: ScheduleCreatePayload; error?: string } => {
  const followupId = Number(form.followupId);
  if (!followupId) {
    return { error: '고객을 선택하세요.' };
  }
  if (!form.activityType) {
    return { error: '활동 유형을 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '방문 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '방문 시간을 선택하세요.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      followupId,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: form.probability.trim() || undefined,
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
    return { error: '활동 유형을 선택하세요.' };
  }
  if (!form.status) {
    return { error: '일정 상태를 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '방문 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '방문 시간을 선택하세요.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      expectedCloseDate: form.expectedCloseDate || undefined,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      followupId,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: form.probability.trim() || undefined,
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
  discountRate: item?.discountRate ? String(item.discountRate) : '',
  discountUnitPrice: item?.discountUnitPrice !== undefined && item.discountUnitPrice !== null ? String(item.discountUnitPrice) : '',
  taxInvoiceIssued: Boolean(item?.taxInvoiceIssued),
  quoteGroup: item?.quoteGroup || '',
  notes: item?.notes || '',
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
      row.notes.trim(),
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
    taxInvoiceIssued: Boolean(item.taxInvoiceIssued),
    quoteGroup: item.quoteGroup || '',
    notes: item.notes || '',
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
  row.notes.trim()
));

const makeEmptyMailComposeForm = (): MailComposeFormState => ({
  attachments: [],
  autoAttachments: [],
  autoAttachmentSeed: '',
  bodyHtml: '',
  bodyText: '',
  businessCardId: '',
  ccEmails: '',
  bccEmails: '',
  excludedAutoAttachmentKeys: [],
  followupId: '',
  includeInternalCc: false,
  internalCcEmails: [],
  scheduleId: '',
  subject: '',
  toEmail: '',
});

const makeInitialMailComposeForm = (): MailComposeFormState => {
  const form = makeEmptyMailComposeForm();
  const params = new URLSearchParams(window.location.search);
  form.followupId = params.get('followup_id') || params.get('followupId') || '';
  form.scheduleId = params.get('schedule_id') || params.get('scheduleId') || '';
  form.toEmail = params.get('to') || params.get('to_email') || '';
  form.subject = params.get('subject') || '';
  return form;
};

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

const getOptionValue = (options: Array<{ value: string }>, fallback: string) => options[0]?.value || fallback;

const getDefaultCustomerAssetId = (summary?: CustomerAssetSummary | null) => (
  summary?.assets[0]?.id ? String(summary.assets[0].id) : ''
);

const makeCustomerAssetForm = (
  asset?: CustomerAssetItem | null,
  status = 'active',
): CustomerAssetFormState => ({
  assetName: asset?.assetName || '',
  installLocation: asset?.installLocation || '',
  modelName: asset?.modelName || '',
  notes: asset?.notes || '',
  purchaseDate: asset?.purchaseDate || '',
  serialNumber: asset?.serialNumber || '',
  status: asset?.status || status,
  warrantyUntil: asset?.warrantyUntil || '',
});

const makeCustomerServiceCaseForm = (
  summary?: CustomerAssetSummary | null,
  assetId = getDefaultCustomerAssetId(summary),
  serviceCase?: CustomerServiceCase | null,
): CustomerServiceCaseFormState => ({
  assetId: serviceCase?.assetId ? String(serviceCase.assetId) : assetId,
  caseType: serviceCase?.caseType || getOptionValue(summary?.options.serviceCaseTypes ?? [], 'repair'),
  completedDate: serviceCase?.completedDate || '',
  dueDate: serviceCase?.dueDate || '',
  priority: serviceCase?.priority || getOptionValue(summary?.options.servicePriorities ?? [], 'normal'),
  receivedDate: serviceCase?.receivedDate || localDateInputValue(),
  resolution: serviceCase?.resolution || '',
  serviceReport: null,
  status: serviceCase?.status || getOptionValue(summary?.options.serviceStatuses ?? [], 'received'),
  symptom: serviceCase?.symptom || '',
});

const makeCustomerCalibrationForm = (
  summary?: CustomerAssetSummary | null,
  assetId = getDefaultCustomerAssetId(summary),
  calibration?: CustomerCalibrationRecord | null,
): CustomerCalibrationFormState => ({
  assetId: calibration?.assetId ? String(calibration.assetId) : assetId,
  calibrationDate: calibration?.calibrationDate || localDateInputValue(),
  certificateFile: null,
  nextDueDate: calibration?.nextDueDate || '',
  notes: calibration?.notes || '',
  result: calibration?.result || getOptionValue(summary?.options.calibrationResults ?? [], 'pass'),
});

const customerAssetFormToPayload = (form: CustomerAssetFormState): { payload?: CustomerAssetPayload; error?: string } => {
  if (!form.assetName.trim()) {
    return { error: '장비/자산명을 입력하세요.' };
  }
  if (!form.status) {
    return { error: '장비 상태를 선택하세요.' };
  }
  return {
    payload: {
      assetName: form.assetName.trim(),
      installLocation: form.installLocation.trim() || undefined,
      modelName: form.modelName.trim() || undefined,
      notes: form.notes.trim() || undefined,
      purchaseDate: form.purchaseDate || undefined,
      serialNumber: form.serialNumber.trim() || undefined,
      status: form.status,
      warrantyUntil: form.warrantyUntil || undefined,
    },
  };
};

const customerServiceCaseFormToPayload = (form: CustomerServiceCaseFormState): { payload?: CustomerServiceCasePayload; error?: string } => {
  const assetId = Number(form.assetId);
  if (!assetId) {
    return { error: '서비스 대상 장비를 선택하세요.' };
  }
  if (!form.caseType) {
    return { error: '서비스 유형을 선택하세요.' };
  }
  if (!form.status) {
    return { error: '서비스 상태를 선택하세요.' };
  }
  if (!form.priority) {
    return { error: '서비스 우선순위를 선택하세요.' };
  }
  if (!form.receivedDate) {
    return { error: '접수일을 입력하세요.' };
  }
  return {
    payload: {
      assetId,
      caseType: form.caseType,
      completedDate: form.completedDate || undefined,
      dueDate: form.dueDate || undefined,
      priority: form.priority,
      receivedDate: form.receivedDate,
      resolution: form.resolution.trim() || undefined,
      serviceReport: form.serviceReport,
      status: form.status,
      symptom: form.symptom.trim() || undefined,
    },
  };
};

const customerCalibrationFormToPayload = (form: CustomerCalibrationFormState): { payload?: CustomerCalibrationPayload; error?: string } => {
  const assetId = Number(form.assetId);
  if (!assetId) {
    return { error: '교정 대상 장비를 선택하세요.' };
  }
  if (!form.calibrationDate) {
    return { error: '교정일을 입력하세요.' };
  }
  if (!form.result) {
    return { error: '교정 결과를 선택하세요.' };
  }
  return {
    payload: {
      assetId,
      calibrationDate: form.calibrationDate,
      certificateFile: form.certificateFile,
      nextDueDate: form.nextDueDate || undefined,
      notes: form.notes.trim() || undefined,
      result: form.result,
    },
  };
};

const findCustomerServiceCase = (summary: CustomerAssetSummary | undefined, serviceCaseId: number | null) => {
  if (!summary || !serviceCaseId) {
    return null;
  }
  return summary.assets.flatMap((asset) => asset.serviceCases).find((serviceCase) => serviceCase.id === serviceCaseId) || null;
};

const findCustomerCalibration = (summary: CustomerAssetSummary | undefined, calibrationId: number | null) => {
  if (!summary || !calibrationId) {
    return null;
  }
  return summary.assets.flatMap((asset) => asset.calibrations).find((calibration) => calibration.id === calibrationId) || null;
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
  assets: {
    eyebrow: 'Sales CRM / Assets',
    title: '장비',
    summary: '고객 보유 장비, A/S 진행, 교정 예정 상태를 전체 범위에서 검색합니다.',
    primaryHref: '/assets/',
    primaryLabel: '장비 디렉터리 열기',
    actions: [
      { label: '고객 목록', href: '/customers/', primary: true },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
      { label: '영업노트', href: '/notes/' },
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
  tasks: {
    eyebrow: 'Sales CRM / Tasks',
    title: '업무',
    summary: '내 할 일, 받은 업무, 맡긴 업무와 매니저 하달 업무를 React CRM에서 처리합니다.',
    primaryHref: '/tasks/',
    primaryLabel: '업무 보기',
    actions: [
      { label: '업무 보기', href: '/tasks/', primary: true },
      { label: '업무하달', href: '/tasks/manager/' },
      { label: 'Django TODOLIST', href: '/todos/' },
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
  documents: {
    eyebrow: 'Sales CRM / Documents',
    title: '서류',
    summary: '견적서, 거래명세서, 납품서 템플릿을 관리하고 일정 서류 생성 흐름과 연결합니다.',
    primaryHref: '/documents/',
    primaryLabel: '서류 템플릿 관리',
    actions: [
      { label: '서류 등록', href: '/documents/?create=1', primary: true },
      { label: 'Django 서류 관리', href: '/reporting/documents/' },
      { label: '일정', href: '/schedules/' },
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
      { label: 'Django 제품관리', href: '/reporting/products/' },
      { label: '엑셀 다운로드', href: '/reporting/api/products/export.xlsx' },
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
  if (pathname.startsWith('/assets/')) return 'assets';
  if (pathname.startsWith('/notes/')) return 'notes';
  if (pathname.startsWith('/schedules/')) return 'schedules';
  if (pathname.startsWith('/tasks/')) return 'tasks';
  if (pathname.startsWith('/mailbox/')) return 'mail';
  if (pathname.startsWith('/weekly-reports/')) return 'weeklyReports';
  if (pathname.startsWith('/documents/')) return 'documents';
  if (pathname.startsWith('/products/')) return 'products';
  if (pathname.startsWith('/prepayments/')) return 'prepayments';
  if (pathname.startsWith('/ai-workspace/')) return 'ai';
  if (pathname.startsWith('/pipeline/')) return 'pipeline';
  return 'pipeline';
}

function isTaskManagerRoute(): boolean {
  return /^\/tasks\/manager\/?$/.test(window.location.pathname);
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

function isScheduleCalendarRoute(): boolean {
  return /^\/schedules\/calendar\/?$/.test(window.location.pathname);
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

function getAIWorkspaceDepartmentIdParam(): number | null {
  const params = new URLSearchParams(window.location.search);
  const rawValue = params.get('department_id') || params.get('department');
  const id = Number(rawValue);
  return Number.isFinite(id) && id > 0 ? id : null;
}

function getAIWorkspaceQuestionScopeParam(): AIWorkspaceQuestionScope {
  const value = new URLSearchParams(window.location.search).get('question_scope')
    || new URLSearchParams(window.location.search).get('questionScope');
  return value === 'all' ? 'all' : 'department';
}

function getAIWorkspaceQuestionLogId(): number | null {
  const match = window.location.pathname.match(/^\/ai-workspace\/questions\/(\d+)\/?$/);
  if (!match) {
    return null;
  }
  const id = Number(match[1]);
  return Number.isFinite(id) && id > 0 ? id : null;
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
  const items: Array<NavigationItem & { icon?: typeof LayoutDashboard }> = dynamicItems
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
  onVerify: (card: CustomerAiPainpoint) => void;
}) {
  const quoteDelivery = aiDepartment.quoteDelivery;
  const quoteInsights = aiDepartment.quoteInsights;
  const missingInfo = aiDepartment.missingInfo;
  const recommendedQuestions = aiDepartment.recommendedQuestions ?? [];
  const [copiedQuestionKey, setCopiedQuestionKey] = useState('');
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
  const hasQuoteSection = hasQuoteMetrics
    || quoteInsightItems.length > 0
    || quoteDelivery.productStats.length > 0
    || quoteDelivery.recentDeliveries.length > 0
    || quoteInsights.stalledQuotes.length > 0;

  const handleQuestionCopy = async (question: string, key: string) => {
    try {
      await navigator.clipboard.writeText(question);
      setCopiedQuestionKey(key);
      window.setTimeout(() => setCopiedQuestionKey(''), 1400);
    } catch {
      setCopiedQuestionKey('');
    }
  };

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

      {hasQuoteSection ? (
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
          {quoteDelivery.recentDeliveries.length > 0 ? (
            <div className="customer-ai-delivery-list">
              <strong className="customer-ai-list-label">최근 납품 품목</strong>
              {quoteDelivery.recentDeliveries.slice(0, 5).map((delivery) => (
                <div className="customer-ai-delivery-item" key={`${delivery.date}-${delivery.customer}-${delivery.source}`}>
                  <div className="customer-ai-delivery-head">
                    <strong>{[delivery.date ? formatDateLabel(delivery.date) : '', delivery.customer].filter(Boolean).join(' · ') || '최근 납품'}</strong>
                    <span>{[delivery.source, delivery.amount ? formatWon(delivery.amount) : ''].filter(Boolean).join(' · ')}</span>
                  </div>
                  {delivery.items.length > 0 ? (
                    <div className="customer-ai-delivery-products">
                      {delivery.items.map((item) => (
                        <small key={`${delivery.date}-${delivery.customer}-${item.product}`}>
                          {item.product} · {formatNumber(item.quantity)}개{item.totalPrice ? ` · ${formatWon(item.totalPrice)}` : ''}
                        </small>
                      ))}
                    </div>
                  ) : (
                    <small>품목 정보 없음</small>
                  )}
                  {delivery.notes ? <small>{delivery.notes}</small> : null}
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

      {recommendedQuestions.length > 0 ? (
        <section className="customer-ai-section">
          <h4>추천 질문</h4>
          <div className="customer-ai-question-list">
            {recommendedQuestions.map((item, index) => {
              const key = `${item.source}-${item.question}-${index}`;
              return (
                <article className="customer-ai-question-item" key={key}>
                  <div>
                    <span className={`customer-ai-priority ${item.priority || 'medium'}`}>{item.sourceLabel || '질문'}</span>
                    <strong>{item.question}</strong>
                    {item.context ? <small>{item.context}</small> : null}
                  </div>
                  <button onClick={() => handleQuestionCopy(item.question, key)} type="button">
                    {copiedQuestionKey === key ? <Check size={14} /> : <Copy size={14} />}
                    {copiedQuestionKey === key ? '복사됨' : '복사'}
                  </button>
                </article>
              );
            })}
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
                        onClick={() => onVerify(card)}
                        type="button"
                      >
                        {verifyingId === card.id ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
                        확인
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
  const [assetEditor, setAssetEditor] = useState<CustomerAssetEditorMode>('');
  const [assetForm, setAssetForm] = useState<CustomerAssetFormState>(() => makeCustomerAssetForm());
  const [serviceCaseForm, setServiceCaseForm] = useState<CustomerServiceCaseFormState>(() => makeCustomerServiceCaseForm());
  const [calibrationForm, setCalibrationForm] = useState<CustomerCalibrationFormState>(() => makeCustomerCalibrationForm());
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null);
  const [editingServiceCaseId, setEditingServiceCaseId] = useState<number | null>(null);
  const [editingCalibrationId, setEditingCalibrationId] = useState<number | null>(null);
  const [assetSaving, setAssetSaving] = useState(false);
  const [assetError, setAssetError] = useState('');
  const [assetMessage, setAssetMessage] = useState('');

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
    setAssetEditor('');
    setAssetForm(makeCustomerAssetForm(null, getOptionValue(data?.assetSummary.options.assetStatuses ?? [], 'active')));
    setServiceCaseForm(makeCustomerServiceCaseForm(data?.assetSummary));
    setCalibrationForm(makeCustomerCalibrationForm(data?.assetSummary));
    setEditingAssetId(null);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(null);
    setAssetSaving(false);
    setAssetError('');
    setAssetMessage('');
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

  const handleAiPainpointVerify = async (card: CustomerAiPainpoint) => {
    if (!card.canVerify || !card.verifyHref || aiVerifyingId) {
      return;
    }

    setAiVerifyingId(card.id);
    setAiError('');
    setAiMessage('');
    try {
      await verifyAiPainpoint(card.verifyHref, aiVerificationNotes[card.id] || '');
      await onRefresh();
      setAiMessage('PainPoint 검증 메모를 저장했습니다.');
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

  const resetAssetFeedback = () => {
    setAssetError('');
    setAssetMessage('');
  };

  const openAssetEditor = (mode: CustomerAssetEditorMode) => {
    setAssetEditor(mode);
    resetAssetFeedback();
  };

  const handleAssetCreateOpen = () => {
    const summary = data?.assetSummary;
    setEditingAssetId(null);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(null);
    setAssetForm(makeCustomerAssetForm(null, getOptionValue(summary?.options.assetStatuses ?? [], 'active')));
    openAssetEditor('asset');
  };

  const handleAssetEditOpen = (asset: CustomerAssetItem) => {
    const summary = data?.assetSummary;
    setEditingAssetId(asset.id);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(null);
    setAssetForm(makeCustomerAssetForm(asset, getOptionValue(summary?.options.assetStatuses ?? [], 'active')));
    openAssetEditor('asset');
  };

  const handleServiceCaseCreateOpen = (asset?: CustomerAssetItem) => {
    const summary = data?.assetSummary;
    if (!summary?.assets.length) {
      setAssetError('서비스를 등록하려면 먼저 장비를 등록하세요.');
      setAssetMessage('');
      return;
    }
    setEditingAssetId(null);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(null);
    setServiceCaseForm(makeCustomerServiceCaseForm(summary, asset?.id ? String(asset.id) : getDefaultCustomerAssetId(summary)));
    openAssetEditor('service');
  };

  const handleServiceCaseEditOpen = (serviceCase: CustomerServiceCase) => {
    const summary = data?.assetSummary;
    setEditingAssetId(null);
    setEditingServiceCaseId(serviceCase.id);
    setEditingCalibrationId(null);
    setServiceCaseForm(makeCustomerServiceCaseForm(summary, String(serviceCase.assetId), serviceCase));
    openAssetEditor('service');
  };

  const handleCalibrationCreateOpen = (asset?: CustomerAssetItem) => {
    const summary = data?.assetSummary;
    if (!summary?.assets.length) {
      setAssetError('교정 기록을 등록하려면 먼저 장비를 등록하세요.');
      setAssetMessage('');
      return;
    }
    setEditingAssetId(null);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(null);
    setCalibrationForm(makeCustomerCalibrationForm(summary, asset?.id ? String(asset.id) : getDefaultCustomerAssetId(summary)));
    openAssetEditor('calibration');
  };

  const handleCalibrationEditOpen = (calibration: CustomerCalibrationRecord) => {
    const summary = data?.assetSummary;
    setEditingAssetId(null);
    setEditingServiceCaseId(null);
    setEditingCalibrationId(calibration.id);
    setCalibrationForm(makeCustomerCalibrationForm(summary, String(calibration.assetId), calibration));
    openAssetEditor('calibration');
  };

  const handleAssetFieldChange = (field: keyof CustomerAssetFormState, value: string) => {
    setAssetForm((previous) => ({ ...previous, [field]: value }));
    resetAssetFeedback();
  };

  const handleServiceCaseFieldChange = (
    field: Exclude<keyof CustomerServiceCaseFormState, 'serviceReport'>,
    value: string,
  ) => {
    setServiceCaseForm((previous) => ({ ...previous, [field]: value }));
    resetAssetFeedback();
  };

  const handleCalibrationFieldChange = (
    field: Exclude<keyof CustomerCalibrationFormState, 'certificateFile'>,
    value: string,
  ) => {
    setCalibrationForm((previous) => ({ ...previous, [field]: value }));
    resetAssetFeedback();
  };

  const handleAssetSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const summary = data?.assetSummary;
    if (!summary?.canManage || assetSaving) {
      setAssetError(summary?.message || '장비 정보를 저장할 권한이 없습니다.');
      setAssetMessage('');
      return;
    }
    const { payload, error } = customerAssetFormToPayload(assetForm);
    if (!payload || error) {
      setAssetError(error || '장비 정보를 확인하세요.');
      setAssetMessage('');
      return;
    }
    const submitUrl = editingAssetId
      ? summary.assets.find((asset) => asset.id === editingAssetId)?.updateUrl
      : summary.links.createAsset;
    if (!submitUrl) {
      setAssetError('장비 저장 API가 준비되지 않았습니다.');
      setAssetMessage('');
      return;
    }

    setAssetSaving(true);
    resetAssetFeedback();
    try {
      const result = await saveCustomerAsset(payload, submitUrl);
      await onRefresh();
      setAssetMessage(result.message || '장비 정보를 저장했습니다.');
      setAssetEditor('');
      setEditingAssetId(null);
    } catch (error) {
      setAssetError(error instanceof Error ? error.message : '장비 정보 저장에 실패했습니다.');
    } finally {
      setAssetSaving(false);
    }
  };

  const handleServiceCaseSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const summary = data?.assetSummary;
    if (!summary?.canManage || assetSaving) {
      setAssetError(summary?.message || '서비스 케이스를 저장할 권한이 없습니다.');
      setAssetMessage('');
      return;
    }
    const { payload, error } = customerServiceCaseFormToPayload(serviceCaseForm);
    if (!payload || error) {
      setAssetError(error || '서비스 케이스 정보를 확인하세요.');
      setAssetMessage('');
      return;
    }
    const submitUrl = editingServiceCaseId
      ? findCustomerServiceCase(summary, editingServiceCaseId)?.updateUrl
      : summary.links.createServiceCase;
    if (!submitUrl) {
      setAssetError('서비스 저장 API가 준비되지 않았습니다.');
      setAssetMessage('');
      return;
    }

    setAssetSaving(true);
    resetAssetFeedback();
    try {
      const result = await saveCustomerServiceCase(payload, submitUrl);
      await onRefresh();
      setAssetMessage(result.message || '서비스 케이스를 저장했습니다.');
      setAssetEditor('');
      setEditingServiceCaseId(null);
    } catch (error) {
      setAssetError(error instanceof Error ? error.message : '서비스 케이스 저장에 실패했습니다.');
    } finally {
      setAssetSaving(false);
    }
  };

  const handleCalibrationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const summary = data?.assetSummary;
    if (!summary?.canManage || assetSaving) {
      setAssetError(summary?.message || '교정 기록을 저장할 권한이 없습니다.');
      setAssetMessage('');
      return;
    }
    const { payload, error } = customerCalibrationFormToPayload(calibrationForm);
    if (!payload || error) {
      setAssetError(error || '교정 기록 정보를 확인하세요.');
      setAssetMessage('');
      return;
    }
    const submitUrl = editingCalibrationId
      ? findCustomerCalibration(summary, editingCalibrationId)?.updateUrl
      : summary.links.createCalibration;
    if (!submitUrl) {
      setAssetError('교정 저장 API가 준비되지 않았습니다.');
      setAssetMessage('');
      return;
    }

    setAssetSaving(true);
    resetAssetFeedback();
    try {
      const result = await saveCustomerCalibration(payload, submitUrl);
      await onRefresh();
      setAssetMessage(result.message || '교정 기록을 저장했습니다.');
      setAssetEditor('');
      setEditingCalibrationId(null);
    } catch (error) {
      setAssetError(error instanceof Error ? error.message : '교정 기록 저장에 실패했습니다.');
    } finally {
      setAssetSaving(false);
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
  const assetSummary = data.assetSummary;
  const metrics = [
    { label: '최근 노트', value: `${formatNumber(data.metrics.recentNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '예정 일정', value: `${formatNumber(data.metrics.upcomingSchedules)}건`, detail: '진행 예정', icon: CalendarDays, tone: 'green' as const },
    { label: '지연 후속', value: `${formatNumber(data.metrics.overdueActions)}건`, detail: '확인 필요', icon: AlertTriangle, tone: 'red' as const },
    { label: '14일 내 후속', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '예정 액션', icon: Clock, tone: 'teal' as const },
  ];
  const assetMetrics = [
    { label: '등록 장비', value: `${formatNumber(assetSummary.metrics.assetCount)}건` },
    { label: '운영 장비', value: `${formatNumber(assetSummary.metrics.activeAssetCount)}건` },
    { label: '진행 서비스', value: `${formatNumber(assetSummary.metrics.openServiceCaseCount)}건` },
    { label: '교정 예정', value: `${formatNumber(assetSummary.metrics.dueCalibrationCount)}건` },
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

      <section className="dashboard-panel customer-assets-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Assets & service</span>
            <h2>장비/교정/서비스</h2>
          </div>
          <Archive size={18} />
        </div>
        <div className="customer-assets-metrics">
          {assetMetrics.map((metric) => (
            <span key={metric.label}>
              {metric.label}
              <strong>{metric.value}</strong>
            </span>
          ))}
        </div>
        {!assetSummary.canManage && assetSummary.message ? (
          <div className="dashboard-api-alert compact">
            <AlertTriangle size={16} />
            <span>{assetSummary.message}</span>
          </div>
        ) : null}
        {assetError ? (
          <div className="dashboard-api-alert compact">
            <AlertTriangle size={16} />
            <span>{assetError}</span>
          </div>
        ) : null}
        {assetMessage ? (
          <div className="dashboard-api-alert compact success">
            <CheckCircle2 size={16} />
            <span>{assetMessage}</span>
          </div>
        ) : null}
        <div className="customer-assets-actions">
          {assetSummary.canManage ? (
            <>
              <button className="route-secondary-action" onClick={handleAssetCreateOpen} type="button">
                <Plus size={15} />
                장비 등록
              </button>
              <button
                className="route-secondary-action"
                disabled={assetSummary.assets.length === 0}
                onClick={() => handleServiceCaseCreateOpen()}
                type="button"
              >
                <ListChecks size={15} />
                서비스 접수
              </button>
              <button
                className="route-secondary-action"
                disabled={assetSummary.assets.length === 0}
                onClick={() => handleCalibrationCreateOpen()}
                type="button"
              >
                <CheckCircle2 size={15} />
                교정 기록
              </button>
            </>
          ) : null}
        </div>

        {assetEditor === 'asset' ? (
          <form className="notes-create-form customer-asset-form" onSubmit={handleAssetSubmit}>
            <div className="dashboard-panel-heading customer-asset-editor-heading">
              <div>
                <span className="eyebrow">{editingAssetId ? 'Edit asset' : 'New asset'}</span>
                <h3>{editingAssetId ? '장비 정보 수정' : '장비 등록'}</h3>
              </div>
            </div>
            <div className="notes-create-grid">
              <label>
                <span>장비/자산명</span>
                <input
                  onChange={(event) => handleAssetFieldChange('assetName', event.target.value)}
                  required
                  value={assetForm.assetName}
                />
              </label>
              <label>
                <span>상태</span>
                <select
                  onChange={(event) => handleAssetFieldChange('status', event.target.value)}
                  required
                  value={assetForm.status}
                >
                  {assetSummary.options.assetStatuses.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>모델명</span>
                <input
                  onChange={(event) => handleAssetFieldChange('modelName', event.target.value)}
                  value={assetForm.modelName}
                />
              </label>
              <label>
                <span>시리얼번호</span>
                <input
                  onChange={(event) => handleAssetFieldChange('serialNumber', event.target.value)}
                  value={assetForm.serialNumber}
                />
              </label>
              <label>
                <span>구매일</span>
                <input
                  onChange={(event) => handleAssetFieldChange('purchaseDate', event.target.value)}
                  type="date"
                  value={assetForm.purchaseDate}
                />
              </label>
              <label>
                <span>보증 만료일</span>
                <input
                  onChange={(event) => handleAssetFieldChange('warrantyUntil', event.target.value)}
                  type="date"
                  value={assetForm.warrantyUntil}
                />
              </label>
              <label>
                <span>설치 위치</span>
                <input
                  onChange={(event) => handleAssetFieldChange('installLocation', event.target.value)}
                  value={assetForm.installLocation}
                />
              </label>
            </div>
            <label>
              <span>메모</span>
              <textarea
                onChange={(event) => handleAssetFieldChange('notes', event.target.value)}
                rows={3}
                value={assetForm.notes}
              />
            </label>
            <div className="notes-create-actions">
              <button className="route-secondary-action" onClick={() => setAssetEditor('')} type="button">
                취소
              </button>
              <button className="route-primary-action" disabled={assetSaving} type="submit">
                {assetSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                저장
              </button>
            </div>
          </form>
        ) : null}

        {assetEditor === 'service' ? (
          <form className="notes-create-form customer-asset-form" onSubmit={handleServiceCaseSubmit}>
            <div className="dashboard-panel-heading customer-asset-editor-heading">
              <div>
                <span className="eyebrow">{editingServiceCaseId ? 'Edit service' : 'New service'}</span>
                <h3>{editingServiceCaseId ? '서비스 케이스 수정' : '서비스 접수'}</h3>
              </div>
            </div>
            <div className="notes-create-grid">
              <label>
                <span>대상 장비</span>
                <select
                  onChange={(event) => handleServiceCaseFieldChange('assetId', event.target.value)}
                  required
                  value={serviceCaseForm.assetId}
                >
                  {assetSummary.assets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {[asset.assetName, asset.modelName, asset.serialNumber ? `SN ${asset.serialNumber}` : ''].filter(Boolean).join(' · ')}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>유형</span>
                <select
                  onChange={(event) => handleServiceCaseFieldChange('caseType', event.target.value)}
                  required
                  value={serviceCaseForm.caseType}
                >
                  {assetSummary.options.serviceCaseTypes.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>상태</span>
                <select
                  onChange={(event) => handleServiceCaseFieldChange('status', event.target.value)}
                  required
                  value={serviceCaseForm.status}
                >
                  {assetSummary.options.serviceStatuses.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>우선순위</span>
                <select
                  onChange={(event) => handleServiceCaseFieldChange('priority', event.target.value)}
                  required
                  value={serviceCaseForm.priority}
                >
                  {assetSummary.options.servicePriorities.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>접수일</span>
                <input
                  onChange={(event) => handleServiceCaseFieldChange('receivedDate', event.target.value)}
                  required
                  type="date"
                  value={serviceCaseForm.receivedDate}
                />
              </label>
              <label>
                <span>처리 기한</span>
                <input
                  onChange={(event) => handleServiceCaseFieldChange('dueDate', event.target.value)}
                  type="date"
                  value={serviceCaseForm.dueDate}
                />
              </label>
              <label>
                <span>완료일</span>
                <input
                  onChange={(event) => handleServiceCaseFieldChange('completedDate', event.target.value)}
                  type="date"
                  value={serviceCaseForm.completedDate}
                />
              </label>
              <label>
                <span>서비스 리포트</span>
                <input
                  onChange={(event) => {
                    setServiceCaseForm((previous) => ({
                      ...previous,
                      serviceReport: event.target.files?.[0] ?? null,
                    }));
                    resetAssetFeedback();
                  }}
                  type="file"
                />
              </label>
            </div>
            <label>
              <span>증상/요청</span>
              <textarea
                onChange={(event) => handleServiceCaseFieldChange('symptom', event.target.value)}
                rows={3}
                value={serviceCaseForm.symptom}
              />
            </label>
            <label>
              <span>처리 내용</span>
              <textarea
                onChange={(event) => handleServiceCaseFieldChange('resolution', event.target.value)}
                rows={3}
                value={serviceCaseForm.resolution}
              />
            </label>
            <div className="notes-create-actions">
              <button className="route-secondary-action" onClick={() => setAssetEditor('')} type="button">
                취소
              </button>
              <button className="route-primary-action" disabled={assetSaving} type="submit">
                {assetSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                저장
              </button>
            </div>
          </form>
        ) : null}

        {assetEditor === 'calibration' ? (
          <form className="notes-create-form customer-asset-form" onSubmit={handleCalibrationSubmit}>
            <div className="dashboard-panel-heading customer-asset-editor-heading">
              <div>
                <span className="eyebrow">{editingCalibrationId ? 'Edit calibration' : 'New calibration'}</span>
                <h3>{editingCalibrationId ? '교정 기록 수정' : '교정 기록'}</h3>
              </div>
            </div>
            <div className="notes-create-grid">
              <label>
                <span>대상 장비</span>
                <select
                  onChange={(event) => handleCalibrationFieldChange('assetId', event.target.value)}
                  required
                  value={calibrationForm.assetId}
                >
                  {assetSummary.assets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {[asset.assetName, asset.modelName, asset.serialNumber ? `SN ${asset.serialNumber}` : ''].filter(Boolean).join(' · ')}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>교정일</span>
                <input
                  onChange={(event) => handleCalibrationFieldChange('calibrationDate', event.target.value)}
                  required
                  type="date"
                  value={calibrationForm.calibrationDate}
                />
              </label>
              <label>
                <span>다음 교정일</span>
                <input
                  onChange={(event) => handleCalibrationFieldChange('nextDueDate', event.target.value)}
                  type="date"
                  value={calibrationForm.nextDueDate}
                />
              </label>
              <label>
                <span>결과</span>
                <select
                  onChange={(event) => handleCalibrationFieldChange('result', event.target.value)}
                  required
                  value={calibrationForm.result}
                >
                  {assetSummary.options.calibrationResults.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>성적서</span>
                <input
                  onChange={(event) => {
                    setCalibrationForm((previous) => ({
                      ...previous,
                      certificateFile: event.target.files?.[0] ?? null,
                    }));
                    resetAssetFeedback();
                  }}
                  type="file"
                />
              </label>
            </div>
            <label>
              <span>메모</span>
              <textarea
                onChange={(event) => handleCalibrationFieldChange('notes', event.target.value)}
                rows={3}
                value={calibrationForm.notes}
              />
            </label>
            <div className="notes-create-actions">
              <button className="route-secondary-action" onClick={() => setAssetEditor('')} type="button">
                취소
              </button>
              <button className="route-primary-action" disabled={assetSaving} type="submit">
                {assetSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                저장
              </button>
            </div>
          </form>
        ) : null}

        {assetSummary.assets.length > 0 ? (
          <div className="customer-asset-list">
            {assetSummary.assets.map((asset) => (
              <article className="customer-asset-card" key={asset.id}>
                <div className="customer-asset-card-heading">
                  <div>
                    <strong>{asset.assetName}</strong>
                    <span>
                      {[asset.modelName, asset.serialNumber ? `SN ${asset.serialNumber}` : '', asset.installLocation].filter(Boolean).join(' · ') || '상세 정보 없음'}
                    </span>
                  </div>
                  <span className={`customer-asset-status ${asset.status}`}>{asset.statusLabel}</span>
                </div>
                <div className="customer-asset-card-meta">
                  <span>구매 <strong>{formatDateLabel(asset.purchaseDate) || '-'}</strong></span>
                  <span>보증 <strong>{formatDateLabel(asset.warrantyUntil) || '-'}</strong></span>
                  <span>소유 <strong>{asset.primaryFollowupName || asset.createdBy || '-'}</strong></span>
                  <span>수정 <strong>{formatDateTimeLabel(asset.updatedAt) || '-'}</strong></span>
                </div>
                <div className="customer-asset-latest-grid">
                  <div>
                    <span>최근 서비스</span>
                    {asset.latestServiceCase ? (
                      <strong>
                        {asset.latestServiceCase.statusLabel}
                        {asset.latestServiceCase.receivedDate ? ` · ${formatDateLabel(asset.latestServiceCase.receivedDate)}` : ''}
                      </strong>
                    ) : (
                      <strong>기록 없음</strong>
                    )}
                  </div>
                  <div>
                    <span>최근 교정</span>
                    {asset.latestCalibration ? (
                      <strong>
                        {asset.latestCalibration.resultLabel}
                        {asset.latestCalibration.nextDueDate ? ` · 다음 ${formatDateLabel(asset.latestCalibration.nextDueDate)}` : ''}
                      </strong>
                    ) : (
                      <strong>기록 없음</strong>
                    )}
                  </div>
                </div>
                {asset.notes ? <p>{asset.notes}</p> : null}
                {assetSummary.canManage ? (
                  <div className="customer-asset-card-actions">
                    <button className="customer-row-action" onClick={() => handleAssetEditOpen(asset)} type="button">
                      장비 수정
                    </button>
                    <button className="customer-row-action" onClick={() => handleServiceCaseCreateOpen(asset)} type="button">
                      서비스
                    </button>
                    <button className="customer-row-action" onClick={() => handleCalibrationCreateOpen(asset)} type="button">
                      교정
                    </button>
                  </div>
                ) : null}
                {asset.serviceCases.length > 0 || asset.calibrations.length > 0 ? (
                  <div className="customer-asset-history-grid">
                    <div>
                      <h4>서비스 이력</h4>
                      {asset.serviceCases.slice(0, 3).map((serviceCase) => (
                        <button
                          className="customer-asset-history-row"
                          disabled={!assetSummary.canManage}
                          key={serviceCase.id}
                          onClick={() => handleServiceCaseEditOpen(serviceCase)}
                          type="button"
                        >
                          <span>{serviceCase.caseTypeLabel} · {serviceCase.statusLabel}</span>
                          <small>{serviceCase.receivedDate ? formatDateLabel(serviceCase.receivedDate) : '접수일 없음'}</small>
                        </button>
                      ))}
                    </div>
                    <div>
                      <h4>교정 이력</h4>
                      {asset.calibrations.slice(0, 3).map((calibration) => (
                        <button
                          className="customer-asset-history-row"
                          disabled={!assetSummary.canManage}
                          key={calibration.id}
                          onClick={() => handleCalibrationEditOpen(calibration)}
                          type="button"
                        >
                          <span>{calibration.resultLabel}</span>
                          <small>
                            {calibration.calibrationDate ? formatDateLabel(calibration.calibrationDate) : '교정일 없음'}
                            {calibration.nextDueDate ? ` · 다음 ${formatDateLabel(calibration.nextDueDate)}` : ''}
                          </small>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label="등록된 장비/교정/서비스 이력이 없습니다" />
        )}
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

function CustomerAssetDirectoryTable({ assets }: { assets: CustomerAssetDirectoryItem[] }) {
  if (assets.length === 0) {
    return <DashboardEmpty label="조건에 맞는 장비가 없습니다" />;
  }

  return (
    <div className="customers-table-wrap assets-table-wrap">
      <table className="customers-table assets-table">
        <thead>
          <tr>
            <th>장비</th>
            <th>고객/위치</th>
            <th>A/S</th>
            <th>교정</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id}>
              <td>
                <div className="asset-directory-info">
                  <strong>{asset.assetName}</strong>
                  <span>{[asset.modelName, asset.serialNumber ? `SN ${asset.serialNumber}` : '', asset.productCode].filter(Boolean).join(' · ') || '모델/시리얼 없음'}</span>
                  <span className={`customer-asset-status ${asset.status}`}>{asset.statusLabel}</span>
                </div>
              </td>
              <td>
                <div className="asset-directory-info">
                  <strong>{asset.companyName || '업체 없음'}</strong>
                  <span>{[asset.departmentName, asset.customerName || asset.primaryFollowupName, asset.installLocation].filter(Boolean).join(' · ') || '고객/위치 없음'}</span>
                  <small>{asset.ownerName || asset.createdBy || '등록자 없음'}</small>
                </div>
              </td>
              <td>
                <div className="asset-directory-info">
                  {asset.latestServiceCase ? (
                    <>
                      <strong>{asset.latestServiceCase.statusLabel}</strong>
                      <span>{[asset.latestServiceCase.caseTypeLabel, asset.latestServiceCase.priorityLabel].filter(Boolean).join(' · ')}</span>
                      <small>{asset.latestServiceCase.receivedDate ? formatDateLabel(asset.latestServiceCase.receivedDate) : '접수일 없음'}</small>
                    </>
                  ) : (
                    <span>서비스 이력 없음</span>
                  )}
                </div>
              </td>
              <td>
                <div className="asset-directory-info">
                  {asset.latestCalibration ? (
                    <>
                      <strong>{asset.latestCalibration.resultLabel}</strong>
                      <span>{asset.latestCalibration.nextDueDate ? `다음 ${formatDateLabel(asset.latestCalibration.nextDueDate)}` : '다음 예정일 없음'}</span>
                      <small>{asset.latestCalibration.calibrationDate ? formatDateLabel(asset.latestCalibration.calibrationDate) : '교정일 없음'}</small>
                    </>
                  ) : (
                    <span>교정 이력 없음</span>
                  )}
                </div>
              </td>
              <td>
                <div className="customer-row-actions">
                  {asset.customerHref ? <a className="customer-row-action" href={asset.customerHref}>고객 상세</a> : null}
                  {asset.djangoCustomerHref ? <a className="customer-row-action" href={asset.djangoCustomerHref}>Django</a> : null}
                </div>
                <small className="asset-directory-updated">{asset.updatedAt ? formatDateTimeLabel(asset.updatedAt) : '-'}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CustomerAssetsPage({
  calibration,
  data,
  loading,
  owner,
  query,
  service,
  status,
  onCalibrationChange,
  onOwnerChange,
  onQueryChange,
  onServiceChange,
  onStatusChange,
}: {
  calibration: string;
  data: CustomerAssetDirectoryData | null;
  loading: boolean;
  owner: string;
  query: string;
  service: string;
  status: string;
  onCalibrationChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onServiceChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>장비 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 장비', value: `${formatNumber(data.metrics.totalAssets)}건`, detail: data.scope.label, icon: Wrench, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(data.metrics.filteredAssets)}건`, detail: '현재 필터', icon: Search, tone: 'teal' as const },
    { label: '진행 서비스', value: `${formatNumber(data.metrics.openServiceAssets)}건`, detail: '접수/진행/대기', icon: Activity, tone: 'amber' as const },
    {
      label: '교정 예정',
      value: `${formatNumber(data.metrics.dueCalibrationAssets)}건`,
      detail: `지연 ${formatNumber(data.metrics.overdueCalibrationAssets)}건`,
      icon: CalendarDays,
      tone: data.metrics.overdueCalibrationAssets > 0 ? 'red' as const : 'green' as const,
    },
  ];

  return (
    <section className="customers-page assets-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>장비 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Customer assets</span>
          <h2>{data.scope.label || '장비 디렉터리'}</h2>
          <p>고객별 장비, 최근 A/S 상태, 다음 교정 예정일을 한 화면에서 검색합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.customers || '/customers/'}>고객 목록</a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="장비 핵심 지표">
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

      <div className="customers-filter-bar assets-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="장비명, 모델, 시리얼, 업체, 연구실 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="">상태 전체</option>
          {data.options.assetStatuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onServiceChange(event.target.value)} value={service}>
          <option value="">서비스 전체</option>
          {data.options.serviceFilters.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onCalibrationChange(event.target.value)} value={calibration}>
          <option value="">교정 전체</option>
          {data.options.calibrationFilters.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      {data.metrics.truncated ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>결과가 많아 최근 {formatNumber(data.metrics.returnedAssets)}건만 표시합니다. 검색어나 필터를 좁혀 확인하세요.</span>
        </div>
      ) : null}

      <section className="dashboard-panel assets-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Asset list</span>
            <h2>장비 목록</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <Wrench size={18} />}
        </div>
        <CustomerAssetDirectoryTable assets={data.assets} />
      </section>
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
    if (!editForm.content.trim()) {
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
              {item.djangoHref ? <a href={item.djangoHref}>Django 상세</a> : null}
              {item.djangoEditHref ? <a href={item.djangoEditHref}>Django 수정</a> : null}
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
  const [selectedDate, setSelectedDate] = useState(() => {
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
  const schedules = data?.schedules ?? [];
  const days = useMemo(() => buildScheduleCalendarDays(month, schedules), [month, schedules]);
  const selectedDayItems = useMemo(
    () => schedules.filter((schedule) => schedule.date === selectedDate).sort((a, b) => `${a.time} ${a.type}`.localeCompare(`${b.time} ${b.type}`)),
    [schedules, selectedDate],
  );
  const monthLabel = new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long' }).format(parseLocalDate(`${month}-01`));
  const todayMonth = localDateInputValue().slice(0, 7);
  const showUserFilter = dataFilter === 'user';

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
  const djangoScheduleCreateHref = appendDateQuery(data.links.createSchedule, selectedDate);
  const personalScheduleCreateConfig = data.create.personalSchedule;
  const personalScheduleCreateBaseHref = personalScheduleCreateConfig?.djangoUrl || data.links.createPersonalSchedule;

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
          <a className="route-secondary-action" href={data.links.djangoCalendar}>
            Django 캘린더
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
            <button
              disabled={!personalScheduleCreateConfig?.canCreate}
              onClick={openPersonalCreatePanel}
              type="button"
            >
              {personalScheduleCreateConfig?.canCreate ? '개인 일정 등록' : '개인 일정 권한 없음'}
            </button>
            <a href={djangoScheduleCreateHref}>Django 상세 등록</a>
            <a href={data.links.weeklyReports}>주간보고</a>
            <a href={data.links.djangoSchedules}>Django 일정 목록</a>
          </div>

          {calendarCreateOpen || calendarCreateError || calendarCreateMessage ? (
            <div className="schedule-calendar-inline-editor">
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
              ) : data.create.customers.length === 0 ? (
                <DashboardEmpty label="등록 가능한 담당 고객이 없습니다" />
              ) : data.create.activityTypes.length === 0 ? (
                <DashboardEmpty label="등록 가능한 활동 유형이 없습니다" />
              ) : calendarCreateOpen ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handleCalendarCreateSubmit}>
                  <div className="notes-create-grid schedules-create-grid">
                    <div className="form-field">
                      <span>고객</span>
                      <SearchableSelect
                        ariaLabel="고객 선택"
                        onChange={(nextValue) => handleCalendarCreateFieldChange('followupId', nextValue)}
                        options={data.create.customers.map(makeCustomerSelectOption)}
                        placeholder="고객, 회사, 부서 검색"
                        value={calendarCreateForm.followupId}
                      />
                    </div>
                    <label>
                      <span>활동 유형</span>
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
                      <span>방문 날짜</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarCreateForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>방문 시간</span>
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
                        onChange={(event) => handleCalendarCreateFieldChange('probability', event.target.value)}
                        placeholder="0-100"
                        type="number"
                        value={calendarCreateForm.probability}
                      />
                    </label>
                  </div>
                  <label>
                    <span>메모</span>
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
            <div className="schedule-calendar-inline-editor">
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
                    <a className="route-secondary-action" href={appendDateQuery(personalScheduleCreateBaseHref, personalCreateForm.scheduleDate || selectedDate)}>
                      Django 등록
                      <MoveUpRight size={15} />
                    </a>
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
            <div className="schedule-calendar-inline-editor">
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
                      <span>활동 유형</span>
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
                      <span>방문 날짜</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarEditForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>방문 시간</span>
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
                    <span>메모</span>
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
                    {calendarEditData.edit.djangoUrl ? (
                      <a className="route-secondary-action" href={calendarEditData.edit.djangoUrl}>
                        Django 수정
                        <MoveUpRight size={15} />
                      </a>
                    ) : null}
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
            <div className="schedule-calendar-inline-editor">
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
                    {personalEditData.edit.djangoUrl ? (
                      <a className="route-secondary-action" href={personalEditData.edit.djangoUrl}>
                        Django 수정
                        <MoveUpRight size={15} />
                      </a>
                    ) : null}
                    <button className="route-primary-action" disabled={personalEditSaving} type="submit">
                      {personalEditSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
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
  onDownload: (action: ScheduleDocumentAction, formatAction: ScheduleDocumentFormatAction) => void;
  onPreview: (action: ScheduleDocumentAction) => void;
}) {
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
              <div className="schedule-document-actions">
                <button
                  className="customer-row-action schedule-document-action-button"
                  disabled={!hasTemplate || previewLoading}
                  onClick={() => onPreview(action)}
                  type="button"
                >
                  {previewLoading && previewAction?.previewHref === action.previewHref ? <Loader2 className="spin-icon" size={14} /> : <Eye size={14} />}
                  <span>미리보기</span>
                </button>
                {action.formats.map((formatAction) => {
                  const actionKey = `${action.type}-${formatAction.format}-${formatAction.href}`;
                  const downloading = downloadingKey === actionKey;
                  return (
                    <button
                      className="customer-row-action schedule-document-action-button"
                      disabled={!hasTemplate || Boolean(downloadingKey)}
                      key={formatAction.format}
                      onClick={() => onDownload(action, formatAction)}
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
                        item.discountUnitPrice !== null ? `기준 ${formatWon(item.baseUnitPrice)}` : '',
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
    const scheduleId = Number(scheduleNoteForm.scheduleId);
    if (!followupId || !scheduleId) {
      setScheduleNoteError('연결할 고객과 일정 정보가 없습니다.');
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
      followupId,
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
        taxInvoiceIssued: row.taxInvoiceIssued,
        quoteGroup: row.quoteGroup.trim(),
        notes: row.notes.trim(),
        sourceQuoteScheduleId: row.sourceQuoteScheduleId ? Number(row.sourceQuoteScheduleId) : null,
        sourceQuoteItemId: row.sourceQuoteItemId ? Number(row.sourceQuoteItemId) : null,
      });
    }
    const sourceQuoteScheduleIds = Array.from(new Set(
      rowsWithInput
        .map((row) => Number(row.sourceQuoteScheduleId))
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
      }
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

  const handleDocumentPreview = async (action: ScheduleDocumentAction) => {
    if (documentPreviewLoading) {
      return;
    }
    setDocumentPreviewAction(action);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(true);
    setDocumentPreviewError('');
    try {
      const preview = await loadScheduleDocumentPreview(action.previewHref);
      setDocumentPreviewData(preview);
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : '서류 변수 미리보기에 실패했습니다.');
    } finally {
      setDocumentPreviewLoading(false);
    }
  };

  const handleDocumentDownload = async (action: ScheduleDocumentAction, formatAction: ScheduleDocumentFormatAction) => {
    if (documentDownloadingKey) {
      return;
    }
    const actionKey = `${action.type}-${formatAction.format}-${formatAction.href}`;
    setDocumentDownloadingKey(actionKey);
    setDocumentPreviewError('');
    try {
      const result = await downloadScheduleDocument(formatAction.href);
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
  const editableQuoteGroups = scheduleQuoteGroupsFromRows(deliveryRows);
  const savedQuoteGroupNotes = schedule.quoteGroupNotes?.filter((item) => item.notes.trim()) ?? [];
  const scheduleMailSubject = isQuoteSchedule
    ? `${schedule.customer || '고객'} 견적서 전달드립니다`
    : `${schedule.customer || '고객'} 거래명세서 전달드립니다`;
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
  const metrics = [
    { label: '일정 상태', value: schedule.statusLabel, detail: schedule.activityLabel, icon: CalendarDays, tone: schedule.overdue ? 'red' as const : 'blue' as const },
    { label: '방문 일시', value: schedule.date ? formatDateLabel(schedule.date) : '날짜 없음', detail: schedule.time || '시간 없음', icon: Clock, tone: 'green' as const },
    { label: '예상 매출', value: schedule.expectedRevenue > 0 ? formatWon(schedule.expectedRevenue) : '없음', detail: schedule.probability ? `${schedule.probability}%` : '확률 미입력', icon: CircleDollarSign, tone: 'amber' as const },
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
          <a className="route-secondary-action" href={data.links.djangoDetail}>Django 상세</a>
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

      {scheduleNoteOpen || scheduleNoteMessage || scheduleNoteError ? (
        <section className="dashboard-panel notes-create-panel schedule-note-create-panel">
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
                    Django 작성
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
            {data.links.sendMail ? (
              <a href={`${data.links.sendMail}${schedule.customerEmail ? `&to=${encodeURIComponent(schedule.customerEmail)}` : ''}&subject=${encodeURIComponent(scheduleMailSubject)}`}>
                메일 발송
              </a>
            ) : data.links.djangoSendMail ? <a href={data.links.djangoSendMail}>메일 발송</a> : null}
            {data.links.createNote ? <a href={data.links.createNote}>보고 작성</a> : null}
            <a href={data.links.calendar}>일정 캘린더</a>
          </div>
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
          {!isQuoteSchedule && quoteImportOpen ? (
            <div className="schedule-quote-import-panel">
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
                      <label className="schedule-edit-inline-check schedule-delivery-tax-check">
                        <input
                          checked={row.taxInvoiceIssued}
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'taxInvoiceIssued', event.target.checked)}
                          type="checkbox"
                        />
                        <span>세금계산서</span>
                      </label>
                      <label className="schedule-delivery-notes-field">
                        <span>적요</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'notes', event.target.value)}
                          value={row.notes}
                        />
                      </label>
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
                    item.taxInvoiceIssued ? '세금계산서 발행' : '미발행',
                  ].filter(Boolean).join(' · ')}</span>
                  {item.notes ? <p>{item.notes}</p> : null}
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
            <a href={data.links.djangoSchedules || data.links.schedules}>Django 일정 목록</a>
            {data.links.djangoCalendar ? <a href={data.links.djangoCalendar}>Django 캘린더</a> : null}
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

function AIWorkspaceDepartmentList({
  departments,
  selectedDepartmentId,
  onSelect,
}: {
  departments: AIWorkspaceDepartment[];
  selectedDepartmentId: number | null;
  onSelect: (department: AIWorkspaceDepartment) => void;
}) {
  const [query, setQuery] = useState('');
  const normalizedQuery = query.trim().toLowerCase();
  const hasSearchQuery = normalizedQuery.length > 0;
  const filteredDepartments = useMemo(() => {
    if (!normalizedQuery) {
      return [];
    }
    return departments.filter((department) => {
      const searchableText = [
        department.company,
        department.name,
        department.summary,
        department.searchText || '',
        ...department.customerPreview,
      ].join(' ').toLowerCase();
      return searchableText.includes(normalizedQuery);
    });
  }, [departments, normalizedQuery]);
  const visibleDepartments = filteredDepartments.slice(0, 5);

  if (departments.length === 0) {
    return <DashboardEmpty label="AI 분석 대상 부서가 없습니다" />;
  }

  return (
    <div className="ai-department-block">
      <label className="ai-department-search">
        <Search size={16} />
        <input
          onChange={(event) => setQuery(event.target.value)}
          placeholder="회사, 부서, 고객, PI/담당자 검색"
          value={query}
        />
      </label>
      <div className="ai-department-list-meta">
        <span>
          전체 {formatNumber(departments.length)}개
          {hasSearchQuery ? ` · 검색 ${formatNumber(filteredDepartments.length)}개` : ''}
        </span>
        <strong>{hasSearchQuery ? '최대 5개 표시' : '검색 후 표시'}</strong>
      </div>
      {!hasSearchQuery ? (
        <p className="ai-department-list-hint">
          회사, 부서, 고객명, PI/담당자 이름, 분석 요약을 검색하면 결과가 표시됩니다.
        </p>
      ) : visibleDepartments.length === 0 ? (
        <DashboardEmpty label="검색 결과가 없습니다" />
      ) : (
        <div className="ai-department-list">
          {visibleDepartments.map((department) => {
            const selected = department.id === selectedDepartmentId;
            return (
              <button
                className={`ai-department-row ${department.hasAnalysis ? 'ready' : ''} ${selected ? 'selected' : ''}`}
                key={department.id}
                onClick={() => onSelect(department)}
                type="button"
              >
                <div>
                  <strong>{department.company || department.name}</strong>
                  <span>{[department.name, `${formatNumber(department.customerCount)}명`].filter(Boolean).join(' · ')}</span>
                  {department.summary ? <small>{department.summary}</small> : null}
                  {!department.summary && department.customerPreview.length > 0 ? (
                    <small>{department.customerPreview.join(', ')}</small>
                  ) : null}
                </div>
                <div className="ai-row-meta">
                  <span>{selected ? '선택됨' : department.hasAnalysis ? '분석 완료' : '분석 필요'}</span>
                  <strong>{formatNumber(department.unverifiedPainpointCount)}</strong>
                </div>
              </button>
            );
          })}
        </div>
      )}
      {hasSearchQuery && filteredDepartments.length > visibleDepartments.length ? (
        <p className="ai-department-list-hint">
          {formatNumber(filteredDepartments.length - visibleDepartments.length)}개가 더 있습니다. 검색어를 더 구체적으로 입력하세요.
        </p>
      ) : null}
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

function MailAttachmentLinks({ attachments }: { attachments: MailboxEmailItem['attachments'] }) {
  const visibleAttachments = (attachments ?? []).filter((attachment) => attachment.filename);
  if (visibleAttachments.length === 0) {
    return null;
  }

  return (
    <div className="mail-message-attachments">
      {visibleAttachments.map((attachment, index) => {
        const content = (
          <>
            <Download size={14} />
            <span>{attachment.filename}</span>
            {attachment.size ? <small>{formatFileSize(attachment.size)}</small> : null}
          </>
        );
        return attachment.downloadHref ? (
          <a href={attachment.downloadHref} key={`${attachment.filename}-${index}`}>
            {content}
          </a>
        ) : (
          <span key={`${attachment.filename}-${index}`}>
            {content}
          </span>
        );
      })}
    </div>
  );
}

const mailEditorFonts = [
  { label: '기본', value: 'Arial, sans-serif' },
  { label: '맑은 고딕', value: '"Malgun Gothic", "Apple SD Gothic Neo", sans-serif' },
  { label: '나눔고딕', value: '"Nanum Gothic", sans-serif' },
  { label: '명조', value: 'Georgia, "Times New Roman", serif' },
  { label: '고정폭', value: '"Courier New", monospace' },
];

const escapeHtml = (value: string) => (
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
);

const normalizeMailEditorUrl = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }
  if (/^(https?:|mailto:)/i.test(trimmed)) {
    return trimmed;
  }
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return `mailto:${trimmed}`;
  }
  return `https://${trimmed}`;
};

const sanitizeMailEditorHtml = (html: string) => {
  if (typeof document === 'undefined') {
    return html;
  }
  const container = document.createElement('div');
  container.innerHTML = html || '';
  container.querySelectorAll('script, style, iframe, object, embed, form, input, button, textarea, select, meta, link').forEach((node) => node.remove());
  container.querySelectorAll<HTMLElement>('*').forEach((node) => {
    Array.from(node.attributes).forEach((attribute) => {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim();
      if (name.startsWith('on')) {
        node.removeAttribute(attribute.name);
      }
      if ((name === 'href' || name === 'src') && /^javascript:/i.test(value)) {
        node.removeAttribute(attribute.name);
      }
    });
    if (node.tagName.toLowerCase() === 'a') {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener noreferrer');
    }
    if (node.tagName.toLowerCase() === 'img') {
      node.setAttribute('style', `${node.getAttribute('style') || ''};max-width:100%;height:auto;`.replace(/^;/, ''));
    }
  });
  return container.innerHTML;
};

const mailHtmlHasMeaningfulContent = (html: string) => {
  if (typeof document === 'undefined') {
    return /<(img|a|strong|b|em|i|u|p|div|span|li|table)\b/i.test(html || '');
  }
  const container = document.createElement('div');
  container.innerHTML = sanitizeMailEditorHtml(html || '');
  return Boolean(container.textContent?.trim() || container.querySelector('img'));
};

function MailRichTextEditor({
  disabled,
  valueHtml,
  onChange,
}: {
  disabled?: boolean;
  valueHtml: string;
  onChange: (bodyText: string, bodyHtml: string) => void;
}) {
  const editorRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [empty, setEmpty] = useState(true);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const emitChange = () => {
    const editor = editorRef.current;
    if (!editor) {
      return;
    }
    const bodyText = (editor.innerText || '').replace(/\u00a0/g, ' ').replace(/\n{4,}/g, '\n\n\n');
    const bodyHtml = sanitizeMailEditorHtml(editor.innerHTML || '');
    setEmpty(!bodyText.trim() && !/<img\b/i.test(bodyHtml));
    onChange(bodyText, bodyHtml);
  };

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) {
      return;
    }
    const nextHtml = valueHtml || '';
    if (editor.innerHTML !== nextHtml && (!nextHtml || document.activeElement !== editor)) {
      editor.innerHTML = nextHtml;
    }
    const bodyText = (editor.innerText || '').replace(/\u00a0/g, ' ');
    setEmpty(!bodyText.trim() && !/<img\b/i.test(nextHtml));
  }, [valueHtml]);

  const focusEditor = () => {
    editorRef.current?.focus();
  };

  const applyCommand = (command: string, value?: string) => {
    if (disabled) {
      return;
    }
    focusEditor();
    document.execCommand(command, false, value);
    emitChange();
  };

  const getEditorSelectionRange = () => {
    const editor = editorRef.current;
    const selection = window.getSelection();
    if (!editor || !selection || selection.rangeCount === 0) {
      return null;
    }
    const range = selection.getRangeAt(0);
    if (!editor.contains(range.startContainer) || !editor.contains(range.endContainer)) {
      return null;
    }
    return range.cloneRange();
  };

  const restoreEditorSelection = (range: Range | null) => {
    if (!range) {
      focusEditor();
      return;
    }
    const selection = window.getSelection();
    focusEditor();
    if (!selection) {
      return;
    }
    selection.removeAllRanges();
    selection.addRange(range);
  };

  const insertHtml = (html: string, range?: Range | null) => {
    if (disabled) {
      return;
    }
    if (range !== undefined) {
      restoreEditorSelection(range);
    } else {
      focusEditor();
    }
    document.execCommand('insertHTML', false, sanitizeMailEditorHtml(html));
    emitChange();
  };

  const handleLinkInsert = () => {
    const range = getEditorSelectionRange();
    const selectedText = range?.toString().trim() || '';
    const rawLabel = window.prompt('링크로 표시할 텍스트를 입력하세요.', selectedText);
    if (rawLabel === null) {
      return;
    }
    const label = rawLabel.trim();
    if (!label) {
      return;
    }
    const rawUrl = window.prompt('링크 URL을 입력하세요.');
    if (rawUrl === null) {
      return;
    }
    const url = normalizeMailEditorUrl(rawUrl);
    if (!url) {
      return;
    }
    insertHtml(`<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`, range);
  };

  const handleImageFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      setUploadError('이미지 파일만 넣을 수 있습니다.');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setUploadError('이미지는 2MB 이하만 넣을 수 있습니다.');
      return;
    }
    setUploadingImage(true);
    setUploadError('');
    try {
      const result = await uploadMailboxEditorImage(file);
      if (!result.url) {
        throw new Error('이미지 URL을 받지 못했습니다.');
      }
      insertHtml(`<img src="${escapeHtml(result.url)}" alt="${escapeHtml(file.name)}" style="max-width:100%;height:auto;">`);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : '이미지 업로드에 실패했습니다.');
    } finally {
      setUploadingImage(false);
    }
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    const imageFile = Array.from(event.clipboardData.files).find((file) => file.type.startsWith('image/'));
    if (imageFile) {
      event.preventDefault();
      void handleImageFile(imageFile);
      return;
    }
    const html = event.clipboardData.getData('text/html');
    if (html) {
      event.preventDefault();
      insertHtml(html);
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    const imageFile = Array.from(event.dataTransfer.files).find((file) => file.type.startsWith('image/'));
    if (!imageFile) {
      return;
    }
    event.preventDefault();
    void handleImageFile(imageFile);
  };

  return (
    <div className="mail-rich-editor">
      <div className="mail-rich-toolbar" aria-label="메일 본문 서식 도구">
        <button aria-label="굵게" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('bold')} title="굵게" type="button">
          <Bold size={15} />
        </button>
        <button aria-label="기울임" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('italic')} title="기울임" type="button">
          <Italic size={15} />
        </button>
        <button aria-label="밑줄" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('underline')} title="밑줄" type="button">
          <Underline size={15} />
        </button>
        <select aria-label="글씨체" disabled={disabled} onChange={(event) => applyCommand('fontName', event.target.value)} defaultValue={mailEditorFonts[0].value} title="글씨체">
          {mailEditorFonts.map((font) => (
            <option key={font.value} value={font.value}>{font.label}</option>
          ))}
        </select>
        <select aria-label="글씨 크기" disabled={disabled} onChange={(event) => applyCommand('fontSize', event.target.value)} defaultValue="3" title="글씨 크기">
          <option value="2">작게</option>
          <option value="3">보통</option>
          <option value="4">크게</option>
          <option value="5">아주 크게</option>
        </select>
        <label className="mail-rich-color" title="글자색">
          <Type size={14} />
          <input aria-label="글자색" disabled={disabled} onChange={(event) => applyCommand('foreColor', event.target.value)} type="color" />
        </label>
        <label className="mail-rich-color" title="배경색">
          <span>A</span>
          <input aria-label="배경색" disabled={disabled} onChange={(event) => applyCommand('hiliteColor', event.target.value)} type="color" />
        </label>
        <button aria-label="번호 목록" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('insertOrderedList')} title="번호 목록" type="button">
          1.
        </button>
        <button aria-label="글머리 목록" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('insertUnorderedList')} title="글머리 목록" type="button">
          •
        </button>
        <button aria-label="링크" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={handleLinkInsert} title="링크" type="button">
          <Link2 size={15} />
        </button>
        <button aria-label="사진" disabled={disabled || uploadingImage} onMouseDown={(event) => event.preventDefault()} onClick={() => fileInputRef.current?.click()} title="사진" type="button">
          {uploadingImage ? <Loader2 className="spin-icon" size={15} /> : <ImagePlus size={15} />}
        </button>
        <button aria-label="서식 지우기" disabled={disabled} onMouseDown={(event) => event.preventDefault()} onClick={() => applyCommand('removeFormat')} title="서식 지우기" type="button">
          <X size={15} />
        </button>
        <input
          accept="image/*"
          className="visually-hidden"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (file) {
              void handleImageFile(file);
            }
            event.currentTarget.value = '';
          }}
          ref={fileInputRef}
          type="file"
        />
      </div>
      <div
        aria-label="메일 본문"
        className={`mail-rich-editor-surface${empty ? ' empty' : ''}`}
        contentEditable={!disabled}
        data-placeholder="메일 본문을 작성하세요"
        onBlur={emitChange}
        onDrop={handleDrop}
        onInput={emitChange}
        onKeyUp={emitChange}
        onPaste={handlePaste}
        ref={editorRef}
        role="textbox"
        suppressContentEditableWarning
      />
      {uploadError ? <div className="mail-rich-error">{uploadError}</div> : null}
    </div>
  );
}

function MailInternalCcPicker({
  contacts,
  disabled,
  includeAll,
  selectedEmails,
  onIncludeAllChange,
  onSelectedEmailsChange,
}: {
  contacts: MailInternalCcContact[];
  disabled?: boolean;
  includeAll: boolean;
  selectedEmails: string[];
  onIncludeAllChange: (checked: boolean) => void;
  onSelectedEmailsChange: (emails: string[]) => void;
}) {
  const [query, setQuery] = useState('');
  const normalizedSelected = useMemo(
    () => new Set(selectedEmails.map((email) => email.trim().toLowerCase()).filter(Boolean)),
    [selectedEmails],
  );
  const uniqueContacts = useMemo(() => {
    const seen = new Set<string>();
    return contacts.filter((contact) => {
      const key = contact.email.trim().toLowerCase();
      if (!key || seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }, [contacts]);
  const selectedContacts = uniqueContacts.filter((contact) => normalizedSelected.has(contact.email.trim().toLowerCase()));
  const normalizedQuery = query.trim().toLowerCase();
  const filteredContacts = uniqueContacts.filter((contact) => {
    if (!normalizedQuery) {
      return true;
    }
    return [contact.name, contact.email, contact.label ?? ''].join(' ').toLowerCase().includes(normalizedQuery);
  });
  const visibleContacts = filteredContacts.slice(0, 8);
  const selectedCount = includeAll ? uniqueContacts.length : selectedContacts.length;

  const toggleContact = (email: string) => {
    if (disabled || includeAll) {
      return;
    }
    const key = email.trim().toLowerCase();
    const next = normalizedSelected.has(key)
      ? selectedEmails.filter((item) => item.trim().toLowerCase() !== key)
      : [...selectedEmails, email];
    onSelectedEmailsChange(next);
  };

  return (
    <div className="mail-internal-cc-picker">
      <div className="mail-internal-cc-head">
        <div>
          <span>내부 직원 참조</span>
          <small>{includeAll ? `전체 ${formatNumber(uniqueContacts.length)}명` : `선택 ${formatNumber(selectedCount)}명 / 전체 ${formatNumber(uniqueContacts.length)}명`}</small>
        </div>
        <div className="mail-internal-cc-actions">
          <button
            className={includeAll ? 'active' : ''}
            disabled={disabled || uniqueContacts.length === 0}
            onClick={() => onIncludeAllChange(!includeAll)}
            type="button"
          >
            <Users size={13} />
            {includeAll ? '전체 해제' : '전체 참조'}
          </button>
          <button
            disabled={disabled || includeAll || selectedEmails.length === 0}
            onClick={() => onSelectedEmailsChange([])}
            type="button"
          >
            <X size={13} />
            선택 해제
          </button>
        </div>
      </div>

      {includeAll ? (
        <div className="mail-internal-cc-all">
          <CheckCircle2 size={15} />
          <span>발송 시 회사 내부 직원 전체가 참조에 포함됩니다.</span>
        </div>
      ) : (
        <>
          <label className="mail-internal-cc-search">
            <Search size={14} />
            <input
              disabled={disabled}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="이름 또는 이메일 검색"
              value={query}
            />
          </label>
          {selectedContacts.length > 0 ? (
            <div className="mail-internal-cc-selected" aria-label="선택된 내부 직원 참조">
              {selectedContacts.map((contact) => (
                <button key={contact.email} onClick={() => toggleContact(contact.email)} type="button">
                  <span>{contact.name}</span>
                  <small>{contact.email}</small>
                  <X size={12} />
                </button>
              ))}
            </div>
          ) : null}
          <div className="mail-internal-cc-results">
            {visibleContacts.length === 0 ? (
              <span className="mail-internal-cc-empty">검색 결과가 없습니다</span>
            ) : (
              visibleContacts.map((contact) => {
                const selected = normalizedSelected.has(contact.email.trim().toLowerCase());
                return (
                  <button
                    className={selected ? 'selected' : ''}
                    disabled={disabled}
                    key={contact.email}
                    onClick={() => toggleContact(contact.email)}
                    type="button"
                  >
                    <div>
                      <strong>{contact.name || contact.email}</strong>
                      <span>{contact.email}</span>
                    </div>
                    {selected ? <Check size={14} /> : null}
                  </button>
                );
              })
            )}
          </div>
          {filteredContacts.length > visibleContacts.length ? (
            <p className="mail-internal-cc-hint">
              {formatNumber(filteredContacts.length - visibleContacts.length)}명이 더 있습니다. 검색어를 더 구체적으로 입력하세요.
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}

function MailComposePanel({
  create,
  form,
  open,
  saving,
  error,
  message,
  submitLabel,
  onAutoAttachmentRemove,
  onAttachmentRemove,
  onAttachmentsChange,
  onBodyChange,
  onChange,
  onCustomerChange,
  onInternalCcChange,
  onInternalCcEmailsChange,
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
  onAutoAttachmentRemove: (key: string) => void;
  onAttachmentRemove: (index: number) => void;
  onAttachmentsChange: (files: File[]) => void;
  onBodyChange: (bodyText: string, bodyHtml: string) => void;
  onChange: (field: MailComposeTextField, value: string) => void;
  onCustomerChange: (customerId: string) => void;
  onInternalCcChange: (checked: boolean) => void;
  onInternalCcEmailsChange: (emails: string[]) => void;
  onOpenChange: (open: boolean) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (!open) {
    return null;
  }
  const visibleAutoAttachments = form.autoAttachments.filter((attachment) => !form.excludedAutoAttachmentKeys.includes(attachment.key));

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
        {create.internalCcContacts.length > 0 ? (
          <MailInternalCcPicker
            contacts={create.internalCcContacts}
            disabled={saving}
            includeAll={form.includeInternalCc}
            onIncludeAllChange={onInternalCcChange}
            onSelectedEmailsChange={onInternalCcEmailsChange}
            selectedEmails={form.internalCcEmails}
          />
        ) : null}
        <label>
          <span>제목</span>
          <input value={form.subject} onChange={(event) => onChange('subject', event.target.value)} placeholder="메일 제목" />
        </label>
        <label>
          <span>본문</span>
          <MailRichTextEditor
            disabled={saving}
            onChange={onBodyChange}
            valueHtml={form.bodyHtml}
          />
        </label>
        <label className="mail-attachment-field">
          <span>첨부파일</span>
          <input
            multiple
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              onAttachmentsChange(Array.from(event.target.files ?? []));
              event.currentTarget.value = '';
            }}
            type="file"
          />
        </label>
        {form.attachments.length > 0 ? (
          <div className="mail-attachment-list" aria-label="선택된 첨부파일">
            {form.attachments.map((file, index) => (
              <div className="mail-attachment-item" key={`${file.name}-${file.size}-${index}`}>
                <Upload size={14} />
                <span>{file.name}</span>
                <small>{formatFileSize(file.size)}</small>
                <button aria-label={`${file.name} 첨부 제거`} onClick={() => onAttachmentRemove(index)} type="button">
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
        ) : null}
        {form.autoAttachments.length > 0 ? (
          <div className="mail-auto-attachments" aria-label="자동 첨부 예정 문서">
            <div className="dashboard-api-alert compact success">
              <FileText size={16} />
              <span>
                {visibleAutoAttachments.length > 0
                  ? `자동 첨부 ${visibleAutoAttachments.length}개가 발송에 포함됩니다.`
                  : '자동 첨부를 모두 제외했습니다.'}
              </span>
            </div>
            {visibleAutoAttachments.length > 0 ? (
              <div className="mail-attachment-list">
                {visibleAutoAttachments.map((attachment) => (
                  <div className="mail-attachment-item auto" key={attachment.key}>
                    <FileText size={14} />
                    <span>{attachment.filename}</span>
                    <small>{attachment.willGenerate ? '발송 시 생성' : attachment.size ? formatFileSize(attachment.size) : attachment.documentTypeLabel}</small>
                    <button aria-label={`${attachment.filename} 자동 첨부 제외`} onClick={() => onAutoAttachmentRemove(attachment.key)} type="button">
                      <X size={13} />
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
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
  onComposeAutoAttachmentRemove,
  onComposeAttachmentRemove,
  onComposeAttachmentsChange,
  onComposeBodyChange,
  onBoxChange,
  onComposeCustomerChange,
  onComposeFormChange,
  onComposeInternalCcChange,
  onComposeInternalCcEmailsChange,
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
  onComposeAutoAttachmentRemove: (key: string) => void;
  onComposeAttachmentRemove: (index: number) => void;
  onComposeAttachmentsChange: (files: File[]) => void;
  onComposeBodyChange: (bodyText: string, bodyHtml: string) => void;
  onBoxChange: (box: MailboxType) => void;
  onComposeCustomerChange: (customerId: string) => void;
  onComposeFormChange: (field: MailComposeTextField, value: string) => void;
  onComposeInternalCcChange: (checked: boolean) => void;
  onComposeInternalCcEmailsChange: (emails: string[]) => void;
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
          autoAttachments: [],
          autoAttachLabel: '',
          schedule: null,
          internalCcEmails: [],
          internalCcContacts: [],
          customers: [],
          businessCards: [],
        }}
        error={composeError}
        form={composeForm}
        message={composeMessage}
        open={composeOpen}
        saving={composing}
        submitLabel="메일 발송"
        onAutoAttachmentRemove={onComposeAutoAttachmentRemove}
        onAttachmentRemove={onComposeAttachmentRemove}
        onAttachmentsChange={onComposeAttachmentsChange}
        onBodyChange={onComposeBodyChange}
        onChange={onComposeFormChange}
        onCustomerChange={onComposeCustomerChange}
        onInternalCcChange={onComposeInternalCcChange}
        onInternalCcEmailsChange={onComposeInternalCcEmailsChange}
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
                    {(email.attachments ?? []).length > 0 ? (
                      <small className="mail-row-attachment-count">첨부 {formatNumber(email.attachments.length)}개</small>
                    ) : null}
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
  onReplyAttachmentRemove,
  onReplyAttachmentsChange,
  onReplyBodyChange,
  onReplyFormChange,
  onReplyInternalCcChange,
  onReplyInternalCcEmailsChange,
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
  onReplyAttachmentRemove: (index: number) => void;
  onReplyAttachmentsChange: (files: File[]) => void;
  onReplyBodyChange: (bodyText: string, bodyHtml: string) => void;
  onReplyFormChange: (field: MailComposeTextField, value: string) => void;
  onReplyInternalCcChange: (checked: boolean) => void;
  onReplyInternalCcEmailsChange: (emails: string[]) => void;
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
    create: {
      canSend: false,
      message: '',
      submitUrl: '',
      djangoUrl: '',
      autoAttachments: [],
      autoAttachLabel: '',
      schedule: null,
      internalCcEmails: [],
      internalCcContacts: [],
      customers: [],
      businessCards: [],
    },
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
            onAutoAttachmentRemove={() => {}}
            onAttachmentRemove={onReplyAttachmentRemove}
            onAttachmentsChange={onReplyAttachmentsChange}
            onBodyChange={onReplyBodyChange}
            onChange={onReplyFormChange}
            onCustomerChange={(customerId) => onReplyFormChange('followupId', customerId)}
            onInternalCcChange={onReplyInternalCcChange}
            onInternalCcEmailsChange={onReplyInternalCcEmailsChange}
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
                <MailAttachmentLinks attachments={email.attachments} />
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

function taskFormPayload(form: TaskFormState): TaskFormPayload {
  return {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    dueDate: form.dueDate || undefined,
    expectedDuration: form.expectedDuration || undefined,
  };
}

function taskStatusClass(status: string) {
  if (status === 'done') return 'done';
  if (status === 'pending') return 'pending';
  if (status === 'rejected') return 'danger';
  if (status === 'on_hold') return 'hold';
  return 'active';
}

function tasksUserLabel(user: TaskItem['createdBy']) {
  return user?.name || user?.username || '';
}

function TaskCard({
  actioningId,
  onStatus,
  task,
}: {
  actioningId: number | null;
  onStatus: (task: TaskItem, payload: { action?: string; status?: string; reason?: string }) => void;
  task: TaskItem;
}) {
  const busy = actioningId === task.id;
  return (
    <article className={`task-card ${task.isOverdue ? 'overdue' : ''}`}>
      <div className="task-card-main">
        <div className="task-card-heading">
          <span className={`task-status ${taskStatusClass(task.status)}`}>{task.statusLabel}</span>
          <span className="task-source">{task.sourceLabel}</span>
          {task.isOverdue ? <span className="task-overdue">지연</span> : null}
        </div>
        <h3>{task.title}</h3>
        {task.description ? <p>{task.description}</p> : null}
        <div className="task-meta-row">
          {task.dueDate ? <span>마감 {formatDateLabel(task.dueDate)}</span> : <span>마감 없음</span>}
          {task.expectedDurationLabel ? <span>{task.expectedDurationLabel}</span> : null}
          {task.relatedClient ? <a href={task.relatedClient.href}>{[task.relatedClient.company, task.relatedClient.department, task.relatedClient.customer].filter(Boolean).join(' · ')}</a> : null}
        </div>
        <div className="task-people-row">
          {task.createdBy ? <span>생성 {tasksUserLabel(task.createdBy)}</span> : null}
          {task.assignedTo ? <span>담당 {tasksUserLabel(task.assignedTo)}</span> : null}
          {task.requestedBy ? <span>요청 {tasksUserLabel(task.requestedBy)}</span> : null}
        </div>
      </div>
      <div className="task-actions">
        {task.canApprove ? <button type="button" disabled={busy} onClick={() => onStatus(task, { action: 'approve' })}>승인</button> : null}
        {task.canReject ? <button type="button" disabled={busy} onClick={() => {
          const reason = window.prompt('반려 사유를 입력하세요.', '');
          if (reason !== null) onStatus(task, { action: 'reject', reason });
        }}>반려</button> : null}
        {task.canSetOngoing ? <button type="button" disabled={busy} onClick={() => onStatus(task, { status: 'ongoing' })}>진행</button> : null}
        {task.canSetOnHold ? <button type="button" disabled={busy} onClick={() => onStatus(task, { status: 'on_hold' })}>보류</button> : null}
        {task.canComplete ? <button type="button" disabled={busy} onClick={() => onStatus(task, { status: 'done' })}>완료</button> : null}
        <a href={task.djangoHref}>Django</a>
      </div>
    </article>
  );
}

function TaskComposer({
  assignees,
  durations,
  form,
  mode,
  saving,
  onFormChange,
  onModeChange,
  onSubmit,
}: {
  assignees: TasksData['options']['assignees'];
  durations: TasksData['options']['durations'];
  form: TaskFormState;
  mode: 'self' | 'request';
  saving: boolean;
  onFormChange: (field: keyof TaskFormState, value: string) => void;
  onModeChange: (mode: 'self' | 'request') => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="task-composer" onSubmit={onSubmit}>
      <div className="task-composer-mode">
        <button className={mode === 'self' ? 'active' : ''} type="button" onClick={() => onModeChange('self')}>내 업무</button>
        <button className={mode === 'request' ? 'active' : ''} type="button" onClick={() => onModeChange('request')}>동료 요청</button>
      </div>
      <label>
        <span>제목</span>
        <input value={form.title} onChange={(event) => onFormChange('title', event.target.value)} placeholder="처리할 업무" />
      </label>
      <label>
        <span>상세</span>
        <textarea value={form.description} onChange={(event) => onFormChange('description', event.target.value)} rows={4} />
      </label>
      <div className="form-grid two-columns">
        <label>
          <span>마감일</span>
          <input type="date" value={form.dueDate} onChange={(event) => onFormChange('dueDate', event.target.value)} />
        </label>
        <label>
          <span>예상 소요</span>
          <select value={form.expectedDuration} onChange={(event) => onFormChange('expectedDuration', event.target.value)}>
            <option value="">선택 안 함</option>
            {durations.map((duration) => (
              <option key={duration.value} value={duration.value}>{duration.label}</option>
            ))}
          </select>
        </label>
      </div>
      {mode === 'request' ? (
        <label>
          <span>담당자</span>
          <select value={form.assignedToId} onChange={(event) => onFormChange('assignedToId', event.target.value)}>
            <option value="">선택</option>
            {assignees.map((assignee) => (
              <option key={assignee.id} value={assignee.id}>{assignee.name}</option>
            ))}
          </select>
        </label>
      ) : null}
      <button className="primary-button" type="submit" disabled={saving}>
        {saving ? '저장 중' : mode === 'self' ? '업무 생성' : '업무 요청'}
      </button>
    </form>
  );
}

function TasksPage({ managerRoute, routeData }: { managerRoute: boolean; routeData: PipelineData }) {
  return managerRoute ? <TaskManagerPage routeData={routeData} /> : <PersonalTasksPage routeData={routeData} />;
}

function PersonalTasksPage({ routeData }: { routeData: PipelineData }) {
  const [data, setData] = useState<TasksData | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('active');
  const [tab, setTab] = useState<TaskTab>('my');
  const [mode, setMode] = useState<'self' | 'request'>('self');
  const [form, setForm] = useState<TaskFormState>(() => makeEmptyTaskForm());
  const [saving, setSaving] = useState(false);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    const result = await loadTasksData({ status });
    setData(result);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
  }, [status]);

  const handleFormChange = (field: keyof TaskFormState, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    setError('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) return;
    if (!form.title.trim()) {
      setError('제목을 입력하세요.');
      return;
    }
    if (mode === 'request' && !form.assignedToId) {
      setError('담당자를 선택하세요.');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      if (mode === 'request') {
        await requestTask(data.links.requestApi, { ...taskFormPayload(form), assignedToId: form.assignedToId });
      } else {
        await createTask(data.links.createApi, taskFormPayload(form));
      }
      setForm(makeEmptyTaskForm());
      setMessage(mode === 'request' ? '업무를 요청했습니다.' : '업무를 생성했습니다.');
      await refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '업무 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleStatus = async (task: TaskItem, payload: { action?: string; status?: string; reason?: string }) => {
    setActioningId(task.id);
    setError('');
    setMessage('');
    try {
      await changeTaskStatus(task.statusHref, payload);
      setMessage('업무 상태를 변경했습니다.');
      await refresh();
    } catch (statusError) {
      setError(statusError instanceof Error ? statusError.message : '상태 변경에 실패했습니다.');
    } finally {
      setActioningId(null);
    }
  };

  const source = data ?? undefined;
  const tasks = source?.tasks[tab] ?? [];
  const routeActions = source?.scope.canManage
    ? routeMeta.tasks.actions
    : routeMeta.tasks.actions.filter((action) => action.href !== '/tasks/manager/');
  return (
    <div className="tasks-page">
      <WorkspaceRoutePage actions={routeActions} data={routeData} view="tasks" />
      <section className="dashboard-metric-grid task-metrics">
        <DashboardMetricCard label="내 업무" value={`${formatNumber(source?.metrics.myActive ?? 0)}건`} detail="진행/대기" icon={CheckCircle2} tone="blue" />
        <DashboardMetricCard label="받은 업무" value={`${formatNumber(source?.metrics.receivedActive ?? 0)}건`} detail="승인/처리 필요" icon={Inbox} tone="amber" />
        <DashboardMetricCard label="맡긴 업무" value={`${formatNumber(source?.metrics.requestedActive ?? 0)}건`} detail="동료 요청" icon={Send} tone="teal" />
        <DashboardMetricCard label="지연" value={`${formatNumber(source?.metrics.overdue ?? 0)}건`} detail="마감일 초과" icon={AlertTriangle} tone="red" />
      </section>
      <section className="tasks-layout">
        <div className="table-card task-list-panel">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Tasks</p>
              <h2>업무 목록</h2>
            </div>
            <div className="route-actions">
              {source?.scope.canManage ? <a className="route-secondary-action" href="/tasks/manager/">업무하달</a> : null}
              <a className="route-secondary-action" href={source?.links.djangoList || '/todos/'}>Django</a>
            </div>
          </div>
          <div className="task-toolbar">
            <div className="segmented-control" role="tablist">
              <button className={tab === 'my' ? 'active' : ''} type="button" onClick={() => setTab('my')}>내 할 일</button>
              <button className={tab === 'received' ? 'active' : ''} type="button" onClick={() => setTab('received')}>받은 일</button>
              <button className={tab === 'requested' ? 'active' : ''} type="button" onClick={() => setTab('requested')}>맡긴 일</button>
            </div>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {(source?.options.statusFilters ?? []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          {loading ? (
            <div className="empty-state">업무를 불러오는 중입니다.</div>
          ) : source?.error ? (
            <div className="empty-state error">{source.error}</div>
          ) : tasks.length ? (
            <div className="task-card-list">
              {tasks.map((task) => (
                <TaskCard actioningId={actioningId} key={task.id} task={task} onStatus={handleStatus} />
              ))}
            </div>
          ) : (
            <div className="empty-state">조건에 맞는 업무가 없습니다.</div>
          )}
        </div>
        <aside className="task-side-panel">
          <div className="side-card">
            <h3>업무 등록</h3>
            <TaskComposer
              assignees={source?.options.assignees ?? []}
              durations={source?.options.durations ?? []}
              form={form}
              mode={mode}
              saving={saving}
              onFormChange={handleFormChange}
              onModeChange={setMode}
              onSubmit={handleSubmit}
            />
            {error ? <p className="form-error">{error}</p> : null}
            {message ? <p className="form-success">{message}</p> : null}
          </div>
        </aside>
      </section>
    </div>
  );
}

function TaskManagerPage({ routeData }: { routeData: PipelineData }) {
  const [data, setData] = useState<TaskManagerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('active');
  const [assignee, setAssignee] = useState('');
  const [form, setForm] = useState<TaskFormState>(() => makeEmptyTaskForm());
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const refresh = async () => {
    setLoading(true);
    const result = await loadTaskManagerData({ status, assignee });
    setData(result);
    setLoading(false);
  };

  useEffect(() => {
    refresh();
  }, [status, assignee]);

  const handleAssign = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) return;
    if (!form.title.trim()) {
      setError('업무 제목을 입력하세요.');
      return;
    }
    if (!selectedIds.length) {
      setError('담당자를 선택하세요.');
      return;
    }
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await assignManagerTask(data.links.assignApi, { ...taskFormPayload(form), assignedToIds: selectedIds });
      setForm(makeEmptyTaskForm());
      setSelectedIds([]);
      setMessage('업무를 하달했습니다.');
      await refresh();
    } catch (assignError) {
      setError(assignError instanceof Error ? assignError.message : '업무 하달에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleManagerStatus = async (task: TaskItem, payload: { action?: string; status?: string }) => {
    if (!payload.status) return;
    setActioningId(task.id);
    setError('');
    setMessage('');
    try {
      await changeManagerTaskStatus(`/reporting/api/tasks/manager/${task.id}/status/`, { status: payload.status });
      setMessage('업무 상태를 변경했습니다.');
      await refresh();
    } catch (statusError) {
      setError(statusError instanceof Error ? statusError.message : '상태 변경에 실패했습니다.');
    } finally {
      setActioningId(null);
    }
  };

  const source = data ?? undefined;
  return (
    <div className="tasks-page">
      <WorkspaceRoutePage actions={routeMeta.tasks.actions} data={routeData} view="tasks" />
      <section className="dashboard-metric-grid task-metrics">
        <DashboardMetricCard label="하달 업무" value={`${formatNumber(source?.metrics.total ?? 0)}건`} detail={source?.scope.label || '팀'} icon={Users} tone="blue" />
        <DashboardMetricCard label="진행/대기" value={`${formatNumber(source?.metrics.active ?? 0)}건`} detail="처리 중" icon={Clock} tone="amber" />
        <DashboardMetricCard label="완료" value={`${formatNumber(source?.metrics.done ?? 0)}건`} detail="완료 처리" icon={CheckCircle2} tone="green" />
        <DashboardMetricCard label="지연" value={`${formatNumber(source?.metrics.overdue ?? 0)}건`} detail="마감일 초과" icon={AlertTriangle} tone="red" />
      </section>
      <section className="tasks-layout">
        <div className="table-card task-list-panel">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Manager Tasks</p>
              <h2>업무 하달 현황</h2>
            </div>
            <div className="route-actions">
              <a className="route-secondary-action" href="/tasks/">개인 업무</a>
              <a className="route-secondary-action" href={source?.links.djangoManager || '/todos/manager/'}>Django</a>
            </div>
          </div>
          <div className="task-toolbar">
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {(source?.options.statusFilters ?? []).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            <select value={assignee} onChange={(event) => setAssignee(event.target.value)}>
              <option value="">담당자 전체</option>
              {(source?.options.teamMembers ?? []).map((member) => (
                <option key={member.id} value={member.id}>{member.name}</option>
              ))}
            </select>
          </div>
          <div className="task-team-summary">
            {(source?.teamSummary ?? []).map((summary) => (
              <div key={summary.user.id}>
                <strong>{summary.user.name}</strong>
                <span>진행 {summary.active} · 완료 {summary.done} · 지연 {summary.overdue}</span>
              </div>
            ))}
          </div>
          {loading ? (
            <div className="empty-state">업무 하달 현황을 불러오는 중입니다.</div>
          ) : source?.error ? (
            <div className="empty-state error">{source.error}</div>
          ) : source?.tasks.length ? (
            <div className="task-card-list">
              {source.tasks.map((task) => (
                <TaskCard actioningId={actioningId} key={task.id} task={task} onStatus={handleManagerStatus} />
              ))}
            </div>
          ) : (
            <div className="empty-state">조건에 맞는 하달 업무가 없습니다.</div>
          )}
        </div>
        <aside className="task-side-panel">
          <form className="side-card task-composer" onSubmit={handleAssign}>
            <h3>업무 하달</h3>
            <label>
              <span>제목</span>
              <input value={form.title} onChange={(event) => setForm((previous) => ({ ...previous, title: event.target.value }))} />
            </label>
            <label>
              <span>상세</span>
              <textarea rows={4} value={form.description} onChange={(event) => setForm((previous) => ({ ...previous, description: event.target.value }))} />
            </label>
            <div className="form-grid two-columns">
              <label>
                <span>마감일</span>
                <input type="date" value={form.dueDate} onChange={(event) => setForm((previous) => ({ ...previous, dueDate: event.target.value }))} />
              </label>
              <label>
                <span>예상 소요</span>
                <select value={form.expectedDuration} onChange={(event) => setForm((previous) => ({ ...previous, expectedDuration: event.target.value }))}>
                  <option value="">선택 안 함</option>
                  {(source?.options.durations ?? []).map((duration) => (
                    <option key={duration.value} value={duration.value}>{duration.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="task-assignee-list">
              {(source?.options.teamMembers ?? []).map((member) => (
                <label key={member.id}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(String(member.id))}
                    onChange={(event) => setSelectedIds((previous) => (
                      event.target.checked
                        ? [...previous, String(member.id)]
                        : previous.filter((id) => id !== String(member.id))
                    ))}
                  />
                  <span>{member.name}</span>
                </label>
              ))}
            </div>
            {error ? <p className="form-error">{error}</p> : null}
            {message ? <p className="form-success">{message}</p> : null}
            <button className="primary-button" type="submit" disabled={saving}>{saving ? '하달 중' : '업무 하달'}</button>
          </form>
        </aside>
      </section>
    </div>
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
          <div className="weekly-schedule-load">
            <button type="button" className="secondary-button" onClick={handleLoadSchedules} disabled={loadingSchedules || !form.weekStart || !form.weekEnd}>
              {loadingSchedules ? '불러오는 중' : '일정 불러오기'}
            </button>
            <small>{form.weekStart && form.weekEnd ? `${formatDateLabel(form.weekStart)} - ${formatDateLabel(form.weekEnd)}` : '보고 기간을 먼저 선택하세요.'}</small>
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
              <a className="route-secondary-action" href={data?.links.djangoList || '/reporting/documents/'}>Django 관리</a>
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
            <form className="document-template-form" onSubmit={handleSubmit}>
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
                <a className="route-secondary-action" href={data?.links.djangoList || '/reporting/documents/'}>Django 서류 관리</a>
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

  const products = data?.products ?? [];
  const pagination = data?.pagination;
  const canManage = Boolean(data?.scope.canManage);
  const pastedProducts = useMemo(() => parseProductPasteRows(bulkText), [bulkText]);
  const deleteCodes = useMemo(() => parseProductDeleteCodes(deleteText), [deleteText]);
  const replaceableDeleteRows = useMemo(() => (
    (deleteResult?.results ?? []).filter((row) => row.status === 'blocked' && row.canReplace)
  ), [deleteResult]);

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
      <WorkspaceRoutePage data={routeData} view="products" />
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
        <form className="dashboard-panel notes-create-form product-editor-panel" onSubmit={handleSubmit}>
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

      <div className="products-layout">
        <section className="dashboard-panel products-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <h2>제품 목록</h2>
              <span>{loading ? '불러오는 중' : `현재 ${formatNumber(products.length)}건 표시`}</span>
            </div>
            <a className="route-secondary-action" href={data?.links.djangoList || '/reporting/products/'}>Django 제품관리</a>
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
                            <button className="route-secondary-action" onClick={() => openEdit(product)} type="button">수정</button>
                            {product.djangoEditHref ? <a className="icon-button" aria-label="Django 수정" href={product.djangoEditHref}><MoveUpRight size={16} /></a> : null}
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

        <aside className="products-side">
          <section className="dashboard-panel product-bulk-panel">
            <div className="dashboard-panel-heading">
              <div>
                <p className="eyebrow">Ecount / Excel</p>
                <h2>붙여넣기 반영</h2>
              </div>
              <Upload size={18} />
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
      </div>
    </section>
  );
}

const aiDraftTypeLabels: Record<AIWorkspaceDraftType, string> = {
  email: '메일',
  note: '노트',
  questions: '질문',
  weekly_report: '보고',
};

const aiDraftButtonLabels: Record<AIWorkspaceDraftType, string> = {
  email: '메일 초안',
  note: '노트 초안',
  questions: '질문 초안',
  weekly_report: '보고 초안',
};

function formatAIActionDate(value: string | null) {
  if (!value) {
    return '';
  }
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' });
}

function AIWorkspaceDailyBriefPanel({ data }: { data: AIWorkspaceData }) {
  const brief = data.dailyBrief;
  const counts = brief.counts;
  const briefCards = [
    { label: '추천 액션', value: `${formatNumber(counts.totalActions)}건`, icon: Sparkles },
    { label: '긴급', value: `${formatNumber(counts.urgentActions)}건`, icon: AlertTriangle },
    { label: '견적 후속', value: `${formatNumber(counts.quoteFollowups)}건`, icon: CircleDollarSign },
    { label: '고객 후속', value: `${formatNumber(counts.customerFollowups)}건`, icon: Clock },
  ];

  return (
    <section className="dashboard-panel ai-brief-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Daily sales brief</span>
          <h2>오늘의 AI 영업 지휘석</h2>
        </div>
        <Sparkles size={18} />
      </div>
      <p className="ai-brief-summary">{brief.summary || 'AI 추천 액션을 계산하는 중입니다.'}</p>
      <div className="ai-brief-grid">
        {briefCards.map((card) => {
          const Icon = card.icon;
          return (
            <div className="ai-brief-card" key={card.label}>
              <Icon size={17} />
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </div>
          );
        })}
      </div>
      <div className="ai-brief-columns">
        <div>
          <strong>리스크</strong>
          {brief.risks.length > 0 ? (
            brief.risks.map((risk) => (
              <span key={`${risk.kindLabel}-${risk.title}`}>{risk.priorityLabel} · {risk.title}</span>
            ))
          ) : (
            <span>즉시 확인할 리스크가 없습니다</span>
          )}
        </div>
        <div>
          <strong>기회</strong>
          {brief.opportunities.length > 0 ? (
            brief.opportunities.map((opportunity) => (
              <span key={`${opportunity.kindLabel}-${opportunity.title}`}>
                {opportunity.kindLabel} · {opportunity.title}
                {opportunity.moneyImpact ? ` · ${formatWon(opportunity.moneyImpact)}` : ''}
              </span>
            ))
          ) : (
            <span>견적/PainPoint 기회가 없습니다</span>
          )}
        </div>
      </div>
    </section>
  );
}

function AIWorkspaceDepartmentActionSummary({ data }: { data: AIWorkspaceData }) {
  const scope = data.feedbackHistory.scope;
  if (!scope.departmentId) {
    return null;
  }

  const actions = data.actionQueue || [];
  const kindCounts = actions.reduce<Array<{ kind: string; label: string; count: number }>>((items, action) => {
    const existing = items.find((item) => item.kind === action.kind);
    if (existing) {
      existing.count += 1;
    } else {
      items.push({ kind: action.kind, label: action.kindLabel, count: 1 });
    }
    return items;
  }, []).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
  const maxKindCount = Math.max(1, ...kindCounts.map((item) => item.count));
  const topActions = [...actions].sort((a, b) => {
    if (b.priorityScore !== a.priorityScore) {
      return b.priorityScore - a.priorityScore;
    }
    return (a.dueDate || '9999-12-31').localeCompare(b.dueDate || '9999-12-31');
  }).slice(0, 3);
  const weekEnd = data.week.end || '';
  const dueThisWeek = actions.filter((action) => action.dueDate && (!weekEnd || action.dueDate <= weekEnd)).length;
  const totalMoneyImpact = actions.reduce((sum, action) => sum + (action.moneyImpact || 0), 0);
  const departmentLabel = [
    data.featuredDepartment?.companyName,
    scope.departmentName || data.featuredDepartment?.departmentName,
  ].filter(Boolean).join(' · ') || scope.label || '선택 부서';
  const summaryStats = [
    { label: '전체 액션', value: `${formatNumber(actions.length)}건`, icon: ListChecks },
    { label: '긴급', value: `${formatNumber(data.dailyBrief.counts.urgentActions)}건`, icon: AlertTriangle },
    { label: '이번 주 기한', value: `${formatNumber(dueThisWeek)}건`, icon: CalendarDays },
    { label: '금액 영향', value: totalMoneyImpact ? formatWon(totalMoneyImpact) : '0원', icon: CircleDollarSign },
  ];

  return (
    <section className="dashboard-panel ai-department-action-summary">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Department action summary</span>
          <h2>부서 실행 요약</h2>
        </div>
        <ListChecks size={18} />
      </div>
      <div className="ai-department-summary-scope">
        <span>{departmentLabel}</span>
        <small>{formatDateLabel(data.week.start)} - {formatDateLabel(data.week.end)}</small>
      </div>
      <div className="ai-department-summary-stats">
        {summaryStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div className="ai-department-summary-stat" key={stat.label}>
              <Icon size={16} />
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          );
        })}
      </div>
      {actions.length > 0 ? (
        <div className="ai-department-summary-body">
          <div className="ai-department-kind-summary">
            {kindCounts.map((kind) => (
              <div className="ai-department-kind-row" key={kind.kind}>
                <span>{kind.label}</span>
                <strong>{formatNumber(kind.count)}건</strong>
                <i style={{ width: `${Math.max(12, Math.round((kind.count / maxKindCount) * 100))}%` }} />
              </div>
            ))}
          </div>
          <div className="ai-department-focus-list">
            {topActions.map((action) => (
              <article key={action.id}>
                <div>
                  <span>{action.kindLabel}</span>
                  <strong>{action.title}</strong>
                </div>
                <small>
                  {action.priorityLabel}
                  {action.dueDate ? ` · ${formatDateLabel(action.dueDate)}` : ''}
                  {action.moneyImpact ? ` · ${formatWon(action.moneyImpact)}` : ''}
                </small>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <DashboardEmpty label={`${scope.departmentName || '선택 부서'}에서 오늘 바로 처리할 추천 액션이 없습니다`} />
      )}
    </section>
  );
}

function AIWorkspaceDepartmentQuestionPanel({
  data,
  departmentId,
  deletingHistoryId,
  deleteHistoryError,
  deleteHistoryMessage,
  error,
  loading,
  model,
  onDeleteHistory,
  onHistoryPageChange,
  onModelChange,
  onQuestionChange,
  onQuestionScopeChange,
  onSubmit,
  question,
  questionScope,
  result,
}: {
  data: AIWorkspaceData;
  departmentId: number | null;
  deletingHistoryId: number | null;
  deleteHistoryError: string;
  deleteHistoryMessage: string;
  error: string;
  loading: boolean;
  model: AIWorkspaceQuestionModel | string;
  onDeleteHistory: (item: AIWorkspaceQuestionLog) => void;
  onHistoryPageChange: (page: number) => void;
  onModelChange: (value: AIWorkspaceQuestionModel | string) => void;
  onQuestionChange: (value: string) => void;
  onQuestionScopeChange: (value: AIWorkspaceQuestionScope) => void;
  onSubmit: () => void;
  question: string;
  questionScope: AIWorkspaceQuestionScope;
  result: AIWorkspaceDepartmentQuestionResponse | null;
}) {
  const scope = data.feedbackHistory.scope;

  const selectedDepartmentLabel = [
    data.featuredDepartment?.companyName,
    scope.departmentName || data.featuredDepartment?.departmentName,
  ].filter(Boolean).join(' · ') || '선택 부서';
  const allScopeSelected = questionScope === 'all';
  const canUseQuestionScope = allScopeSelected || Boolean(departmentId);
  const trimmedQuestion = question.trim();
  const canSubmit = canUseQuestionScope && trimmedQuestion.length >= 2 && !loading;
  const answer = result?.answer;
  const actionItems = answer?.actionItems ?? [];
  const decision = answer?.decision;
  const decisionDetailRows = decision ? [
    { label: '버릴 선택', value: decision.rejectedChoice },
    { label: '판단 이유', value: decision.reason },
    { label: '예외 조건', value: decision.exception },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value)) : [];
  const perspectiveRows = answer?.perspective ? [
    { label: '고객 입장 추정', value: answer.perspective.customerPerspective },
    { label: '영업 판단', value: answer.perspective.salesJudgment },
    { label: '추천 접근', value: answer.perspective.recommendedApproach },
    { label: '말문 예시', value: answer.perspective.talkTrack },
    { label: '주의점', value: answer.perspective.caution },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value)) : [];
  const lastDelivery = result?.context?.lastDelivery;
  const customerCount = result?.context?.customerCount ?? data.featuredDepartment?.customerCount ?? 0;
  const departmentCount = result?.context?.departmentCount ?? data.metrics.departmentsWithCustomers ?? 0;
  const visibleScopeLabel = result?.scope?.label || (allScopeSelected ? '전체 부서' : selectedDepartmentLabel);
  const scopeMetaLabel = allScopeSelected
    ? `부서 ${formatNumber(departmentCount)}개`
    : `고객 ${formatNumber(customerCount)}명`;
  const history = data.questionHistory;
  const modelChoices = data.questionModelChoices.length > 0
    ? data.questionModelChoices
    : [
      { id: 'gpt-5.5', label: 'GPT-5.5' },
      { id: 'gpt-5.4-mini', label: 'GPT-5.4 mini' },
    ];

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (canSubmit) {
      onSubmit();
    }
  };

  return (
    <section className="dashboard-panel ai-department-question-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Department Q&A</span>
          <h2>부서 상황 질문</h2>
        </div>
        <MessageSquareText size={18} />
      </div>
      <div className="ai-department-question-scope">
        <span>{visibleScopeLabel}</span>
        <small>{scopeMetaLabel}</small>
        {result?.webSearchUsed ? <small>웹 검색 사용</small> : null}
      </div>
      <div className="segmented-control ai-question-scope-toggle" aria-label="AI 질문 범위">
        <button
          className={questionScope === 'department' ? 'active' : ''}
          disabled={!departmentId}
          onClick={() => onQuestionScopeChange('department')}
          type="button"
        >
          선택 부서
        </button>
        <button
          className={questionScope === 'all' ? 'active' : ''}
          onClick={() => onQuestionScopeChange('all')}
          type="button"
        >
          전체 부서
        </button>
      </div>
      <div className="segmented-control ai-question-model-toggle" aria-label="AI 질문 모델">
        {modelChoices.map((choice) => (
          <button
            className={model === choice.id ? 'active' : ''}
            key={choice.id}
            onClick={() => onModelChange(choice.id)}
            type="button"
          >
            {choice.label}
          </button>
        ))}
      </div>
      <form className="ai-department-question-form" onSubmit={handleSubmit}>
        <textarea
          maxLength={600}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder={allScopeSelected ? '예: 전체 부서에서 이번 주 먼저 챙길 고객은?' : '예: 재견적 줄 때 샘플 피드백을 다시 물어볼까?'}
          rows={3}
          value={question}
        />
        <div>
          <span>{formatNumber(trimmedQuestion.length)} / 600</span>
          <button disabled={!canSubmit} type="submit">
            {loading ? <Loader2 className="spin-icon" size={14} /> : <Send size={14} />}
            {loading ? '분석 중' : 'AI에게 질문'}
          </button>
        </div>
      </form>
      {error ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{error}</span></div> : null}
      {answer ? (
        <article className="ai-department-question-answer">
          <div className="ai-department-question-answer-head">
            <p>{answer.summary}</p>
            <span>{result.source === 'openai' ? `${result.modelLabel || 'AI'} 답변${result.webSearchUsed ? ' · 웹 검색' : ''}` : 'CRM 기반 답변'}</span>
          </div>
          {decision?.recommendedChoice ? (
            <section className="ai-department-question-decision">
              <span>추천 판단</span>
              <strong>{decision.recommendedChoice}</strong>
              {decisionDetailRows.length > 0 ? (
                <dl>
                  {decisionDetailRows.map((item) => (
                    <div key={item.label}>
                      <dt>{item.label}</dt>
                      <dd>{item.value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
            </section>
          ) : null}
          {perspectiveRows.length > 0 ? (
            <dl className="ai-department-question-perspective">
              {perspectiveRows.map((item) => (
                <div key={item.label}>
                  <dt>{item.label}</dt>
                  <dd>{item.value}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          {actionItems.length > 0 ? (
            <div className="ai-department-question-actions">
              {actionItems.map((item, index) => {
                const meta = [item.customer, item.department, item.company].filter(Boolean).join(' · ');
                const evidence = item.crmEvidence ?? [];
                return (
                  <section className="ai-department-question-action-item" key={`${item.rank || index}-${item.title}-${item.customer}`}>
                    <div className="ai-department-question-action-head">
                      <div>
                        <span>{item.priority || '추천 작업'}</span>
                        <strong>{item.title || `추천 작업 ${index + 1}`}</strong>
                      </div>
                      <small>{formatNumber(item.rank || index + 1)}</small>
                    </div>
                    {meta ? <p className="ai-department-question-action-meta">{meta}</p> : null}
                    <dl className="ai-department-question-action-detail">
                      {item.reason ? (
                        <div>
                          <dt>판단 이유</dt>
                          <dd>{item.reason}</dd>
                        </div>
                      ) : null}
                      {item.nextAction ? (
                        <div>
                          <dt>다음 액션</dt>
                          <dd>{item.nextAction}</dd>
                        </div>
                      ) : null}
                      {item.timing ? (
                        <div>
                          <dt>확인 시점</dt>
                          <dd>{item.timing}</dd>
                        </div>
                      ) : null}
                    </dl>
                    {evidence.length > 0 ? (
                      <div className="ai-department-question-action-evidence">
                        {evidence.slice(0, 4).map((evidenceItem) => (
                          <span key={`${item.rank}-${evidenceItem.label}-${evidenceItem.value}`}>
                            <b>{evidenceItem.label}</b>
                            {evidenceItem.value}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </section>
                );
              })}
            </div>
          ) : null}
          {answer.bullets.length > 0 ? (
            <ul>
              {answer.bullets.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          {lastDelivery ? (
            <div className="ai-department-question-last-order">
              <span>마지막 주문/납품</span>
              <strong>{formatDateLabel(lastDelivery.date) || lastDelivery.date}</strong>
              <small>
                {[lastDelivery.customer, lastDelivery.amountLabel, lastDelivery.items].filter(Boolean).join(' · ')}
              </small>
            </div>
          ) : null}
          {answer.evidence.length > 0 ? (
            <div className="ai-evidence-list">
              {answer.evidence.slice(0, 6).map((item) => (
                <span key={`${item.label}-${item.value}`}>
                  <b>{item.label}</b>
                  {item.value}
                </span>
              ))}
            </div>
          ) : null}
        </article>
      ) : null}
      <section className="ai-question-history">
        <div className="ai-question-history-head">
          <strong>질문/답변 기록</strong>
          <span>{formatNumber(history.total)}건</span>
        </div>
        {deleteHistoryMessage ? <div className="ai-question-history-message success">{deleteHistoryMessage}</div> : null}
        {deleteHistoryError ? <div className="ai-question-history-message error">{deleteHistoryError}</div> : null}
        {history.items.length > 0 ? (
          <div className="ai-question-history-list">
            {history.items.map((item) => (
              <article className="ai-question-history-card" key={item.id}>
                <a className="ai-question-history-main" href={`/ai-workspace/questions/${item.id}/`}>
                  <div className="ai-question-history-meta">
                    <span>{formatDateLabel(item.createdAt || '')}</span>
                    {item.modelLabel ? <small>{item.modelLabel}</small> : null}
                    <MoveUpRight size={13} />
                  </div>
                  <strong>{item.question}</strong>
                  <p>{item.answerSummary}</p>
                  {item.decision?.recommendedChoice ? (
                    <em>{item.decision.recommendedChoice}</em>
                  ) : null}
                </a>
                <button
                  aria-label="질문/답변 기록 삭제"
                  className="ai-question-history-delete"
                  disabled={deletingHistoryId === item.id}
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    onDeleteHistory(item);
                  }}
                  title="삭제"
                  type="button"
                >
                  {deletingHistoryId === item.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                </button>
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label={history.scopeType === 'all' ? '전체 부서 질문 기록이 없습니다' : '선택 부서의 질문 기록이 없습니다'} />
        )}
        {history.totalPages > 1 ? (
          <div className="ai-question-history-pagination">
            <button disabled={!history.hasPrevious} onClick={() => onHistoryPageChange(history.page - 1)} type="button">
              <ChevronLeft size={14} />
              이전
            </button>
            <span>{formatNumber(history.page)} / {formatNumber(history.totalPages)}</span>
            <button disabled={!history.hasNext} onClick={() => onHistoryPageChange(history.page + 1)} type="button">
              다음
              <ChevronRight size={14} />
            </button>
          </div>
        ) : null}
      </section>
    </section>
  );
}

type AIQuestionDetailBlock = {
  title: string;
  lines: string[];
};

function aiQuestionRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function aiQuestionText(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value).trim();
}

function aiQuestionTextList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map(aiQuestionText).filter(Boolean);
}

function aiQuestionRecordList(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map(aiQuestionRecord).filter((item) => Object.keys(item).length > 0);
}

function aiQuestionEvidenceLine(value: unknown): string {
  return aiQuestionRecordList(value).map((item) => {
    const label = aiQuestionText(item.label) || '근거';
    const detail = aiQuestionText(item.value);
    return detail ? `${label}: ${detail}` : '';
  }).filter(Boolean).join(' / ');
}

function makeAIQuestionDetailAnswer(log: AIWorkspaceQuestionLog): { lead: string; blocks: AIQuestionDetailBlock[] } {
  const answer = aiQuestionRecord(log.answer);
  const lead = aiQuestionText(answer.summary) || log.answerSummary || '';
  const blocks: AIQuestionDetailBlock[] = [];
  const bullets = aiQuestionTextList(answer.bullets);
  if (bullets.length > 0) {
    blocks.push({ title: '핵심 포인트', lines: bullets });
  }

  const decision = aiQuestionRecord(answer.decision);
  const decisionLines = [
    ['추천 판단', decision.recommendedChoice],
    ['버릴 선택', decision.rejectedChoice],
    ['판단 이유', decision.reason],
    ['예외 조건', decision.exception],
  ].map(([label, value]) => {
    const text = aiQuestionText(value);
    return text ? `${label}: ${text}` : '';
  }).filter(Boolean);
  if (decisionLines.length > 0) {
    blocks.push({ title: '추천 판단', lines: decisionLines });
  }

  const perspective = aiQuestionRecord(answer.perspective);
  const perspectiveLines = [
    ['고객 입장 추정', perspective.customerPerspective],
    ['영업 판단', perspective.salesJudgment],
    ['추천 접근', perspective.recommendedApproach],
    ['말문 예시', perspective.talkTrack],
    ['주의점', perspective.caution],
  ].map(([label, value]) => {
    const text = aiQuestionText(value);
    return text ? `${label}: ${text}` : '';
  }).filter(Boolean);
  if (perspectiveLines.length > 0) {
    blocks.push({ title: '고객/영업 관점', lines: perspectiveLines });
  }

  const actionLines = aiQuestionRecordList(answer.actionItems).map((item, index) => {
    const rank = aiQuestionText(item.rank) || String(index + 1);
    const title = aiQuestionText(item.title) || `추천 액션 ${rank}`;
    const ownerContext = [item.company, item.department, item.customer].map(aiQuestionText).filter(Boolean).join(' · ');
    const detailParts = [
      ownerContext,
      aiQuestionText(item.priority) ? `우선순위: ${aiQuestionText(item.priority)}` : '',
      aiQuestionText(item.reason) ? `이유: ${aiQuestionText(item.reason)}` : '',
      aiQuestionText(item.nextAction) ? `다음 액션: ${aiQuestionText(item.nextAction)}` : '',
      aiQuestionText(item.timing) ? `시점: ${aiQuestionText(item.timing)}` : '',
      aiQuestionEvidenceLine(item.crmEvidence),
    ].filter(Boolean);
    return `${rank}. ${title}${detailParts.length > 0 ? `\n${detailParts.join('\n')}` : ''}`;
  });
  if (actionLines.length > 0) {
    blocks.push({ title: '추천 액션', lines: actionLines });
  }

  const evidenceLines = aiQuestionRecordList(answer.evidence).map((item) => {
    const label = aiQuestionText(item.label) || '근거';
    const value = aiQuestionText(item.value);
    return value ? `${label}: ${value}` : '';
  }).filter(Boolean);
  if (evidenceLines.length > 0) {
    blocks.push({ title: '근거', lines: evidenceLines });
  }

  const confidence = aiQuestionText(answer.confidence);
  if (confidence) {
    blocks.push({ title: '신뢰도', lines: [confidence] });
  }

  return { lead, blocks };
}

function AIWorkspaceQuestionDetailPage({
  data,
  loading,
}: {
  data: AIWorkspaceQuestionLogDetailData | null;
  loading: boolean;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>질문/답변 기록을 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || data.source !== 'django' || !data.questionLog) {
    return (
      <section className="ai-question-detail-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>질문/답변 기록을 불러오지 못했습니다</strong>
            <span>{data?.error || data?.message || '기록이 없거나 접근 권한이 없습니다.'}</span>
          </div>
          <a href="/ai-workspace/">AI Workspace</a>
        </div>
      </section>
    );
  }

  const log = data.questionLog;
  const answer = makeAIQuestionDetailAnswer(log);
  const departmentLabel = [
    log.department?.company,
    log.department?.name,
  ].filter(Boolean).join(' · ') || (log.scopeType === 'all' ? '전체 부서' : 'AI Workspace');
  const meta = [
    log.createdAt ? formatDateTimeLabel(log.createdAt) : '',
    log.modelLabel,
    log.webSearchUsed ? '웹 검색 사용' : '',
  ].filter(Boolean).join(' · ');

  return (
    <section className="ai-question-detail-page">
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Question detail</span>
          <h2>질문/답변 기록</h2>
          <p>{departmentLabel}{meta ? ` · ${meta}` : ''}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.aiWorkspace}>
            <ChevronLeft size={16} />
            목록으로
          </a>
        </div>
      </div>

      <div className="ai-question-detail-chat">
        <article className="ai-question-detail-block">
          <span className="eyebrow">Question</span>
          <h3>질문</h3>
          <p>{log.question}</p>
        </article>

        <article className="ai-question-detail-block">
          <span className="eyebrow">Answer</span>
          <h3>답변</h3>
          {answer.lead ? <p className="ai-question-detail-answer-lead">{answer.lead}</p> : <DashboardEmpty label="저장된 답변 내용이 없습니다" />}
          {answer.blocks.map((block) => (
            <section className="ai-question-detail-answer-section" key={block.title}>
              <strong>{block.title}</strong>
              <ul>
                {block.lines.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </section>
          ))}
        </article>
      </div>
    </section>
  );
}

function AIWorkspaceActionQueue({
  actions,
  draftLoadingKey,
  feedbackDrafts,
  feedbackSavingId,
  onFeedbackChange,
  onSubmitFeedback,
  onGenerateDraft,
}: {
  actions: AIWorkspaceAction[];
  draftLoadingKey: string;
  feedbackDrafts: Record<string, string>;
  feedbackSavingId: string;
  onFeedbackChange: (actionId: string, value: string) => void;
  onSubmitFeedback: (action: AIWorkspaceAction) => void;
  onGenerateDraft: (action: AIWorkspaceAction, draftType: AIWorkspaceDraftType) => void;
}) {
  if (actions.length === 0) {
    return <DashboardEmpty label="오늘 바로 실행할 AI 추천 액션이 없습니다" />;
  }

  return (
    <div className="ai-action-list">
      {actions.slice(0, 8).map((action) => {
        const feedbackText = feedbackDrafts[action.id] ?? '';
        const feedbackInputId = `ai-feedback-${action.id.replace(/[^a-zA-Z0-9_-]/g, '-')}`;
        const isSavingFeedback = feedbackSavingId === action.id;
        return (
          <article className={`ai-action-card ${action.kind}`} key={action.id}>
            <div className="ai-action-card-head">
              <div>
                <span>{action.kindLabel}</span>
                <strong>{action.title}</strong>
                <small>{[action.company, action.department, action.customer].filter(Boolean).join(' · ')}</small>
              </div>
              <div className="ai-action-score">
                <span>{action.priorityLabel}</span>
                <strong>{formatNumber(action.priorityScore)}</strong>
              </div>
            </div>
            <p>{action.recommendedAction}</p>
            <div className="ai-action-meta">
              {action.moneyImpact ? <span>{formatWon(action.moneyImpact)}</span> : null}
              {action.dueDate ? <span>기한 {formatAIActionDate(action.dueDate)}</span> : null}
            </div>
            {action.evidence.length > 0 ? (
              <div className="ai-evidence-list">
                {action.evidence.slice(0, 4).map((item) => (
                  <span key={`${action.id}-${item.label}-${item.value}`}>
                    <b>{item.label}</b>
                    {item.value}
                  </span>
                ))}
              </div>
            ) : null}
            {action.feedback ? (
              <div className="ai-action-feedback-status">
                <CheckCircle2 size={16} />
                <div>
                  <strong>{action.feedback.statusLabel}</strong>
                  <span>{action.feedback.feedback}</span>
                  {action.feedback.intentLabel ? <small>{action.feedback.intentLabel}</small> : null}
                  {action.feedback.nextAction ? <small>{action.feedback.nextAction}</small> : null}
                  {action.feedback.crmSync?.message ? <small>{action.feedback.crmSync.message}</small> : null}
                  {action.feedback.crmSync?.changes?.length ? (
                    <small>
                      {action.feedback.crmSync.changes.slice(0, 2).map((change) => change.label).join(' · ')}
                    </small>
                  ) : null}
                </div>
              </div>
            ) : null}
            <div className="ai-action-feedback-form">
              <label htmlFor={feedbackInputId}>현장 답변 기록</label>
              <textarea
                id={feedbackInputId}
                maxLength={1200}
                onChange={(event) => onFeedbackChange(action.id, event.target.value)}
                placeholder="예: 고객이 아직 안산대요 / 다음달 예산 확정 후 다시 연락 / 추가 자료를 메일로 요청"
                rows={3}
                value={feedbackText}
              />
              <div className="ai-action-feedback-footer">
                <button
                  className="ai-action-feedback-submit"
                  disabled={isSavingFeedback || !feedbackText.trim()}
                  onClick={() => onSubmitFeedback(action)}
                  type="button"
                >
                  {isSavingFeedback ? <Loader2 className="spin-icon" size={14} /> : <Send size={14} />}
                  {isSavingFeedback ? '기록 중' : '기록하고 AI 판단'}
                </button>
              </div>
            </div>
            <div className="ai-action-buttons">
              {action.draftTypes.map((draftType) => {
                const loadingKey = `${action.id}:${draftType}`;
                return (
                  <button
                    disabled={draftLoadingKey === loadingKey}
                    key={draftType}
                    onClick={() => onGenerateDraft(action, draftType)}
                    type="button"
                  >
                    {draftLoadingKey === loadingKey ? <Loader2 className="spin-icon" size={14} /> : <Sparkles size={14} />}
                    {aiDraftButtonLabels[draftType]}
                  </button>
                );
              })}
              {action.hrefs.customer ? <a href={action.hrefs.customer}>고객 보기</a> : null}
              {action.hrefs.schedule ? <a href={action.hrefs.schedule}>일정 보기</a> : null}
              {action.hrefs.note ? <a href={action.hrefs.note}>노트 보기</a> : null}
              {action.hrefs.mailboxThread ? <a href={action.hrefs.mailboxThread}>메일 보기</a> : null}
              {action.hrefs.report ? <a href={action.hrefs.report}>보고 작성</a> : null}
              {action.hrefs.ai ? <a href={action.hrefs.ai}>AI 분석</a> : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function AIWorkspaceDraftPreview({
  copied,
  result,
  onCopy,
}: {
  copied: boolean;
  result: AIWorkspaceActionDraftResponse;
  onCopy: () => void;
}) {
  const draft = result.draft;
  return (
    <section className="dashboard-panel ai-draft-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Draft copilot</span>
          <h2>{aiDraftTypeLabels[result.draftType]} 초안</h2>
        </div>
        <MessageSquareText size={18} />
      </div>
      <div className="ai-draft-meta">
        <span>{result.action.title}</span>
        <span>{result.source === 'openai' ? 'AI 생성' : '기본 초안'}</span>
        <span>승인 전 저장 안 됨</span>
      </div>
      {draft.subject ? <strong className="ai-draft-subject">{draft.subject}</strong> : null}
      {draft.body ? <pre>{draft.body}</pre> : null}
      {draft.bullets.length > 0 ? (
        <ul>
          {draft.bullets.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      <div className="ai-prompt-actions">
        <button onClick={onCopy} type="button">
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? '복사됨' : '초안 복사'}
        </button>
      </div>
    </section>
  );
}

function AIWorkspaceFeedbackPerformance({ data }: { data: AIWorkspaceData }) {
  const feedbackHistory = data.feedbackHistory;
  const stats = feedbackHistory.stats;
  const statCards = [
    { label: '누적 답변', value: `${formatNumber(stats.total)}건`, detail: feedbackHistory.scope.label || data.currentUser.name || '현재 범위', tone: 'blue' },
    { label: '최근 30일', value: `${formatNumber(stats.recent30Days)}건`, detail: `영업노트 연결 ${formatNumber(stats.linkedNotes)}건`, tone: 'green' },
    { label: '종료/제외', value: `${formatNumber(stats.resolved + stats.dismissed)}건`, detail: `${formatNumber(stats.hideRate)}% 정리`, tone: 'red' },
    { label: '다음 액션', value: `${formatNumber(stats.nextActions)}건`, detail: `${formatNumber(stats.nextActionRate)}% 전환`, tone: 'amber' },
  ];

  return (
    <section className="dashboard-panel ai-feedback-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Feedback loop</span>
          <h2>AI 실행 피드백</h2>
        </div>
        <ListChecks size={18} />
      </div>
      <div className="ai-feedback-scope">
        <span>{feedbackHistory.scope.label || '현재 사용자'}</span>
        {feedbackHistory.scope.canViewAll ? <small>{formatNumber(feedbackHistory.scope.userCount)}명 범위</small> : null}
      </div>
      <div className="ai-feedback-metrics">
        {statCards.map((card) => (
          <div className={`ai-feedback-stat ${card.tone}`} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.detail}</small>
          </div>
        ))}
      </div>
      {feedbackHistory.byKind.length > 0 ? (
        <div className="ai-feedback-kind-strip">
          {feedbackHistory.byKind.map((kind) => (
            <span key={`${kind.kind || 'unknown'}-${kind.count}`}>
              {kind.kindLabel} {formatNumber(kind.count)}
            </span>
          ))}
        </div>
      ) : null}
      {feedbackHistory.recent.length > 0 ? (
        <div className="ai-feedback-list">
          {feedbackHistory.recent.map((item) => (
            <article className={`ai-feedback-row ${item.status}`} key={item.id}>
              <div className="ai-feedback-row-head">
                <div>
                  <span>{item.kindLabel} · {item.statusLabel}</span>
                  <strong>{item.title}</strong>
                  <small>{[item.company, item.department, item.customer].filter(Boolean).join(' · ') || '고객 정보 없음'}</small>
                </div>
                <div className="ai-feedback-owner">
                  <span>{item.owner}</span>
                  <small>{formatDateTimeLabel(item.updatedAt)}</small>
                </div>
              </div>
              <div className="ai-feedback-row-body">
                {item.feedback ? (
                  <p>
                    <b>답변</b>
                    {item.feedback}
                  </p>
                ) : null}
                {item.summary ? (
                  <p>
                    <b>판단</b>
                    {item.summary}
                  </p>
                ) : null}
                {item.nextAction ? (
                  <p>
                    <b>다음 액션</b>
                    {item.nextAction}
                    {item.nextActionDate ? ` · ${formatDateLabel(item.nextActionDate)}` : ''}
                  </p>
                ) : null}
              </div>
              <div className="ai-feedback-links">
                {item.historyHref ? <a href={item.historyHref}>기록 보기</a> : null}
                {item.customerHref ? <a href={item.customerHref}>고객 보기</a> : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <DashboardEmpty label="아직 기록된 AI 실행 피드백이 없습니다" />
      )}
    </section>
  );
}

function AIWorkspacePage({
  data,
  loading,
  onRefresh,
  questionScope,
  onQuestionScopeChange,
  selectedDepartmentId,
  onDepartmentSelect,
}: {
  data: AIWorkspaceData | null;
  loading: boolean;
  onRefresh: (params?: { departmentId?: number | null; questionPage?: number; questionScope?: AIWorkspaceQuestionScope }) => Promise<AIWorkspaceData>;
  questionScope: AIWorkspaceQuestionScope;
  onQuestionScopeChange: (scope: AIWorkspaceQuestionScope) => void;
  selectedDepartmentId: number | null;
  onDepartmentSelect: (department: AIWorkspaceDepartment) => void;
}) {
  const [copiedPromptId, setCopiedPromptId] = useState('');
  const [draftLoadingKey, setDraftLoadingKey] = useState('');
  const [draftResult, setDraftResult] = useState<AIWorkspaceActionDraftResponse | null>(null);
  const [draftError, setDraftError] = useState('');
  const [copiedDraft, setCopiedDraft] = useState(false);
  const [actionFeedbackDrafts, setActionFeedbackDrafts] = useState<Record<string, string>>({});
  const [actionFeedbackSavingId, setActionFeedbackSavingId] = useState('');
  const [actionFeedbackMessage, setActionFeedbackMessage] = useState('');
  const [actionFeedbackError, setActionFeedbackError] = useState('');
  const [departmentQuestion, setDepartmentQuestion] = useState('');
  const [departmentQuestionModel, setDepartmentQuestionModel] = useState<AIWorkspaceQuestionModel | string>('gpt-5.5');
  const [departmentQuestionResult, setDepartmentQuestionResult] = useState<AIWorkspaceDepartmentQuestionResponse | null>(null);
  const [departmentQuestionLoading, setDepartmentQuestionLoading] = useState(false);
  const [departmentQuestionError, setDepartmentQuestionError] = useState('');
  const [questionHistoryPage, setQuestionHistoryPage] = useState(1);
  const [deletingQuestionLogId, setDeletingQuestionLogId] = useState<number | null>(null);
  const [deleteQuestionLogMessage, setDeleteQuestionLogMessage] = useState('');
  const [deleteQuestionLogError, setDeleteQuestionLogError] = useState('');
  const activeDepartmentId = data?.featuredDepartment?.departmentId ?? selectedDepartmentId ?? data?.selectedDepartmentId ?? null;

  useEffect(() => {
    setDepartmentQuestionResult(null);
    setDepartmentQuestionError('');
    setQuestionHistoryPage(1);
    setDeleteQuestionLogMessage('');
    setDeleteQuestionLogError('');
  }, [activeDepartmentId, questionScope]);

  useEffect(() => {
    const choices = data?.questionModelChoices ?? [];
    if (choices.length === 0) {
      return;
    }
    if (!choices.some((choice) => choice.id === departmentQuestionModel)) {
      setDepartmentQuestionModel(data?.defaultQuestionModel || choices[0].id);
    }
  }, [data?.defaultQuestionModel, data?.questionModelChoices, departmentQuestionModel]);

  const handleCopyPrompt = async (target: AIWorkspacePromptTarget) => {
    try {
      await navigator.clipboard.writeText(target.prompt);
      setCopiedPromptId(target.id);
      window.setTimeout(() => setCopiedPromptId(''), 1600);
    } catch {
      setCopiedPromptId('');
    }
  };

  const handleGenerateActionDraft = async (action: AIWorkspaceAction, draftType: AIWorkspaceDraftType) => {
    const loadingKey = `${action.id}:${draftType}`;
    setDraftLoadingKey(loadingKey);
    setDraftError('');
    setCopiedDraft(false);
    try {
      const result = await generateAIWorkspaceActionDraft(action.id, draftType);
      setDraftResult(result);
    } catch (error) {
      setDraftError(error instanceof Error ? error.message : 'AI 초안 생성에 실패했습니다.');
    } finally {
      setDraftLoadingKey('');
    }
  };

  const handleActionFeedbackChange = (actionId: string, value: string) => {
    setActionFeedbackDrafts((previous) => ({
      ...previous,
      [actionId]: value,
    }));
  };

  const handleSubmitActionFeedback = async (action: AIWorkspaceAction) => {
    const feedback = (actionFeedbackDrafts[action.id] || '').trim();
    if (!feedback || actionFeedbackSavingId) {
      return;
    }

    setActionFeedbackSavingId(action.id);
    setActionFeedbackError('');
    setActionFeedbackMessage('');
    try {
      const result = await submitAIWorkspaceActionFeedback(action.id, feedback);
      setActionFeedbackDrafts((previous) => {
        const next = { ...previous };
        delete next[action.id];
        return next;
      });
      await onRefresh({ departmentId: data?.featuredDepartment?.departmentId ?? selectedDepartmentId });
      if (result.crmSync?.message) {
        setActionFeedbackMessage(result.crmSync.message);
      } else if (result.hidden) {
        setActionFeedbackMessage('답변을 기록했고 추천 실행 목록에서 정리했습니다.');
      } else if (result.feedback.nextAction) {
        setActionFeedbackMessage(`답변을 기록했습니다. 다음 액션: ${result.feedback.nextAction}`);
      } else {
        setActionFeedbackMessage(result.message || '답변을 기록했습니다.');
      }
    } catch (error) {
      setActionFeedbackError(error instanceof Error ? error.message : '답변 기록에 실패했습니다.');
    } finally {
      setActionFeedbackSavingId('');
    }
  };

  const handleCopyDraft = async () => {
    if (!draftResult) {
      return;
    }
    const draft = draftResult.draft;
    const text = [
      draft.subject,
      draft.body,
      ...(draft.bullets || []).map((item) => `- ${item}`),
    ].filter(Boolean).join('\n\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopiedDraft(true);
      window.setTimeout(() => setCopiedDraft(false), 1600);
    } catch {
      setCopiedDraft(false);
    }
  };

  const handleAskDepartmentQuestion = async () => {
    const question = departmentQuestion.trim();
    if (!question || departmentQuestionLoading) {
      return;
    }
    if (questionScope === 'department' && !activeDepartmentId) {
      setDepartmentQuestionError('질문할 부서를 먼저 선택하세요.');
      return;
    }

    setDepartmentQuestionLoading(true);
    setDepartmentQuestionError('');
    try {
      const questionDepartmentId = questionScope === 'department' ? activeDepartmentId : null;
      const result = await askAIWorkspaceDepartmentQuestion(
        questionDepartmentId,
        question,
        departmentQuestionModel,
        questionScope,
      );
      setDepartmentQuestionResult(result);
      setQuestionHistoryPage(1);
      await onRefresh({ departmentId: activeDepartmentId, questionPage: 1, questionScope });
    } catch (error) {
      setDepartmentQuestionError(error instanceof Error ? error.message : '부서 질문 답변에 실패했습니다.');
    } finally {
      setDepartmentQuestionLoading(false);
    }
  };

  const handleQuestionHistoryPageChange = async (page: number) => {
    if (page < 1 || (questionScope === 'department' && !activeDepartmentId)) {
      return;
    }
    setQuestionHistoryPage(page);
    await onRefresh({ departmentId: activeDepartmentId, questionPage: page, questionScope });
  };

  const handleDeleteQuestionHistory = async (item: AIWorkspaceQuestionLog) => {
    if (deletingQuestionLogId) {
      return;
    }
    const confirmed = window.confirm('이 질문/답변 기록을 삭제할까요? 삭제 후에는 복구할 수 없습니다.');
    if (!confirmed) {
      return;
    }
    setDeletingQuestionLogId(item.id);
    setDeleteQuestionLogMessage('');
    setDeleteQuestionLogError('');
    try {
      const result = await deleteAIWorkspaceQuestionLog(item.id);
      const currentHistory = data?.questionHistory;
      const currentPage = currentHistory?.page ?? questionHistoryPage;
      const nextPage = currentHistory && currentHistory.items.length <= 1 && currentPage > 1
        ? currentPage - 1
        : currentPage;
      setQuestionHistoryPage(nextPage);
      await onRefresh({ departmentId: activeDepartmentId, questionPage: nextPage, questionScope });
      setDeleteQuestionLogMessage(result.message || '질문/답변 기록을 삭제했습니다.');
    } catch (error) {
      setDeleteQuestionLogError(error instanceof Error ? error.message : '질문/답변 기록 삭제에 실패했습니다.');
    } finally {
      setDeletingQuestionLogId(null);
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
          <p>부서를 선택하고 현재 상황을 질문합니다. 질문 기록은 선택 부서 기준으로 관리됩니다.</p>
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

      {data.permission.canUseAi ? (
        <>
        <div className="ai-workspace-layout">
          <div className="ai-workspace-main">
            <section className="dashboard-panel ai-main-panel">
              <div className="dashboard-panel-heading">
                <div>
                  <span className="eyebrow">Department analysis</span>
                  <h2>부서 분석 대상</h2>
                </div>
                <Sparkles size={18} />
              </div>
              <AIWorkspaceDepartmentList
                departments={data.departments}
                selectedDepartmentId={activeDepartmentId}
                onSelect={onDepartmentSelect}
              />
            </section>

            <AIWorkspaceDepartmentQuestionPanel
              data={data}
              departmentId={activeDepartmentId}
              deletingHistoryId={deletingQuestionLogId}
              deleteHistoryError={deleteQuestionLogError}
              deleteHistoryMessage={deleteQuestionLogMessage}
              error={departmentQuestionError}
              loading={departmentQuestionLoading}
              model={departmentQuestionModel}
              onDeleteHistory={handleDeleteQuestionHistory}
              onHistoryPageChange={handleQuestionHistoryPageChange}
              onModelChange={setDepartmentQuestionModel}
              onQuestionChange={setDepartmentQuestion}
              onQuestionScopeChange={onQuestionScopeChange}
              onSubmit={handleAskDepartmentQuestion}
              question={departmentQuestion}
              questionScope={questionScope}
              result={departmentQuestionResult}
            />
          </div>

        </div>
        </>
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
      href: data.links.operationalDashboard,
    },
    {
      label: '현재 분기 매출',
      value: formatWon(data.metrics.quarterRevenue),
      detail: `${revenueYear}년 ${revenueQuarter}분기`,
      icon: Target,
      tone: 'green' as const,
      href: data.links.operationalDashboard,
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
  onRefresh,
  onMoveStage,
}: {
  deal?: Deal;
  stages: StageSummary[];
  canMove: boolean;
  moving: boolean;
  moveError: string;
  moveMessage: string;
  onRefresh: (preferredDealId?: number | null) => Promise<PipelineData>;
  onMoveStage: (deal: Deal, stage: PipelineStage) => void;
}) {
  const [aiResultOpen, setAiResultOpen] = useState(false);
  const [aiRunning, setAiRunning] = useState(false);
  const [aiError, setAiError] = useState('');
  const [aiMessage, setAiMessage] = useState('');
  const [aiVerificationNotes, setAiVerificationNotes] = useState<Record<number, string>>({});
  const [aiVerifyingId, setAiVerifyingId] = useState<number | null>(null);

  useEffect(() => {
    setAiResultOpen(Boolean(deal?.aiDepartment?.hasAnalysis));
    setAiRunning(false);
    setAiError('');
    setAiMessage('');
    setAiVerificationNotes({});
    setAiVerifyingId(null);
  }, [deal?.id, deal?.aiDepartment?.hasAnalysis]);

  const aiDepartment = deal?.aiDepartment
    ? normalizeCustomerAiDepartment(deal.aiDepartment as Partial<CustomerAiDepartment>)
    : null;

  const handleAiDepartmentRun = async () => {
    if (!deal || !aiDepartment?.canAnalyze || !aiDepartment.runHref || aiRunning) {
      setAiError(aiDepartment?.message || 'AI 분석을 실행할 수 없습니다.');
      setAiMessage('');
      return;
    }

    setAiRunning(true);
    setAiError('');
    setAiMessage('');
    try {
      const result = await runAiDepartmentAnalysis(aiDepartment.runHref);
      await onRefresh(deal.id);
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

  const handleAiPainpointVerify = async (card: CustomerAiPainpoint) => {
    if (!deal || !card.canVerify || !card.verifyHref || aiVerifyingId) {
      return;
    }

    setAiVerifyingId(card.id);
    setAiError('');
    setAiMessage('');
    try {
      await verifyAiPainpoint(card.verifyHref, aiVerificationNotes[card.id] || '');
      await onRefresh(deal.id);
      setAiMessage('PainPoint 검증 메모를 저장했습니다.');
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
          {deal.latestQuote.basisDate ? <small>기준일 {formatDateLabel(deal.latestQuote.basisDate)}</small> : null}
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
  const scheduleCalendarRoute = currentView === 'schedules' && isScheduleCalendarRoute();
  const mailboxThreadId = currentView === 'mail' ? getMailboxThreadId() : '';
  const initialMailboxBox = currentView === 'mail' ? getMailboxTypeParam() : 'inbox';
  const prepaymentCustomerId = currentView === 'prepayments' ? getPrepaymentCustomerId() : null;
  const prepaymentDetailId = currentView === 'prepayments' ? getPrepaymentDetailId() : null;
  const prepaymentCreateRoute = currentView === 'prepayments' && isPrepaymentCreateRoute();
  const prepaymentEditRoute = currentView === 'prepayments' && isPrepaymentEditRoute();
  const weeklyReportDetailId = currentView === 'weeklyReports' ? getWeeklyReportDetailId() : null;
  const weeklyReportCreateRoute = currentView === 'weeklyReports' && isWeeklyReportCreateRoute();
  const weeklyReportEditRoute = currentView === 'weeklyReports' && isWeeklyReportEditRoute();
  const aiWorkspaceQuestionLogId = currentView === 'ai' ? getAIWorkspaceQuestionLogId() : null;
  const initialAIWorkspaceDepartmentId = currentView === 'ai' ? getAIWorkspaceDepartmentIdParam() : null;
  const initialAIWorkspaceQuestionScope = currentView === 'ai' ? getAIWorkspaceQuestionScopeParam() : 'department';
  const [mode, setMode] = useState<'board' | 'list'>('board');
  const [pipelineData, setPipelineData] = useState(emptyPipelineData);
  const [pipelineLoading, setPipelineLoading] = useState(currentView === 'pipeline');
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
  const [assetsData, setAssetsData] = useState<CustomerAssetDirectoryData | null>(null);
  const [assetsLoading, setAssetsLoading] = useState(currentView === 'assets');
  const [assetDirectoryQuery, setAssetDirectoryQuery] = useState(() => new URLSearchParams(window.location.search).get('q') || '');
  const [assetDirectoryStatus, setAssetDirectoryStatus] = useState(() => new URLSearchParams(window.location.search).get('status') || '');
  const [assetDirectoryOwner, setAssetDirectoryOwner] = useState(() => new URLSearchParams(window.location.search).get('owner') || '');
  const [assetDirectoryService, setAssetDirectoryService] = useState(() => new URLSearchParams(window.location.search).get('service') || '');
  const [assetDirectoryCalibration, setAssetDirectoryCalibration] = useState(() => new URLSearchParams(window.location.search).get('calibration') || '');
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
  const [aiWorkspaceData, setAiWorkspaceData] = useState<AIWorkspaceData | null>(null);
  const [aiWorkspaceLoading, setAiWorkspaceLoading] = useState(currentView === 'ai' && !aiWorkspaceQuestionLogId);
  const [aiWorkspaceDepartmentId, setAiWorkspaceDepartmentId] = useState<number | null>(() => initialAIWorkspaceDepartmentId);
  const [aiWorkspaceQuestionScope, setAiWorkspaceQuestionScope] = useState<AIWorkspaceQuestionScope>(() => initialAIWorkspaceQuestionScope);
  const [aiWorkspaceQuestionDetailData, setAiWorkspaceQuestionDetailData] = useState<AIWorkspaceQuestionLogDetailData | null>(null);
  const [aiWorkspaceQuestionDetailLoading, setAiWorkspaceQuestionDetailLoading] = useState(Boolean(aiWorkspaceQuestionLogId));
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
  const [mailComposeForm, setMailComposeForm] = useState<MailComposeFormState>(() => makeInitialMailComposeForm());
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
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedView, setSelectedView] = useState<SavedView>('priority');
  const [movingDealId, setMovingDealId] = useState<number | null>(null);
  const [moveError, setMoveError] = useState('');
  const [moveMessage, setMoveMessage] = useState('');
  const scheduleCalendarRange = useMemo(() => getScheduleCalendarRange(scheduleCalendarMonth), [scheduleCalendarMonth]);

  useEffect(() => {
    if (currentView === 'dashboard') {
      return;
    }
    let alive = true;
    setPipelineLoading(true);
    loadPipelineData().then((data) => {
      if (!alive) {
        return;
      }
      setPipelineData(data);
      setSelectedDealId(data.deals[0]?.id ?? null);
      setPipelineLoading(false);
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
    if (currentView !== 'assets') {
      return;
    }
    let alive = true;
    setAssetsLoading(true);
    loadCustomerAssetDirectoryData({
      q: assetDirectoryQuery,
      status: assetDirectoryStatus,
      owner: assetDirectoryOwner,
      service: assetDirectoryService,
      calibration: assetDirectoryCalibration,
    }).then((data) => {
      if (!alive) {
        return;
      }
      setAssetsData(data);
      setAssetsLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [assetDirectoryCalibration, assetDirectoryOwner, assetDirectoryQuery, assetDirectoryService, assetDirectoryStatus, currentView]);

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
    const requestedScheduleId = getCreateScheduleParam();
    setNoteCreateForm((previous) => ({
      ...previous,
      actionType: previous.actionType || firstActionType,
      followupId: requestedCustomer
        ? String(requestedCustomer.id)
        : previous.followupId || (fallbackCustomerId ? String(fallbackCustomerId) : ''),
      scheduleId: requestedScheduleId || previous.scheduleId,
    }));
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
    const requestedCustomer = schedulesData.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    const firstCustomerId = requestedCustomer?.id ?? schedulesData.create.customers[0]?.id;
    const firstActivityType = schedulesData.create.activityTypes[0]?.value || 'customer_meeting';
    setScheduleCreateForm((previous) => ({
      ...previous,
      activityType: previous.activityType || firstActivityType,
      followupId: previous.followupId || (firstCustomerId ? String(firstCustomerId) : ''),
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
    setProductsLoading(true);
    loadProductManagementData({
      order: productOrder,
      page: productPage,
      pageSize: 50,
      q: productQuery,
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
    const queryString = params.toString();
    window.history.replaceState(null, '', `/products/${queryString ? `?${queryString}` : ''}`);

    return () => {
      alive = false;
    };
  }, [currentView, productOrder, productPage, productQuery, productSort, productStatus]);

  useEffect(() => {
    if (currentView !== 'ai' || aiWorkspaceQuestionLogId) {
      setAiWorkspaceLoading(false);
      return;
    }
    let alive = true;
    setAiWorkspaceLoading(true);
    loadAIWorkspaceData({ departmentId: aiWorkspaceDepartmentId, questionScope: aiWorkspaceQuestionScope }).then((data) => {
      if (!alive) {
        return;
      }
      setAiWorkspaceData(data);
      setAiWorkspaceDepartmentId(data.selectedDepartmentId ?? data.featuredDepartment?.departmentId ?? null);
      setAiWorkspaceLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, aiWorkspaceQuestionLogId]);

  useEffect(() => {
    if (currentView !== 'ai' || !aiWorkspaceQuestionLogId) {
      setAiWorkspaceQuestionDetailData(null);
      setAiWorkspaceQuestionDetailLoading(false);
      return;
    }
    let alive = true;
    setAiWorkspaceQuestionDetailLoading(true);
    loadAIWorkspaceQuestionLogDetailData(aiWorkspaceQuestionLogId).then((data) => {
      if (!alive) {
        return;
      }
      setAiWorkspaceQuestionDetailData(data);
      setAiWorkspaceQuestionDetailLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [currentView, aiWorkspaceQuestionLogId]);

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
      scheduleId: mailComposeForm.scheduleId ? Number(mailComposeForm.scheduleId) : undefined,
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
  }, [currentView, mailboxBox, mailboxPage, mailboxQuery, mailboxThreadId, mailComposeForm.scheduleId]);

  useEffect(() => {
    if (currentView !== 'mail' || mailboxThreadId || !mailboxData || !mailComposeForm.scheduleId) {
      return;
    }
    const autoAttachments = mailboxData.create.autoAttachments ?? [];
    const seed = [
      mailComposeForm.scheduleId,
      ...autoAttachments.map((attachment) => attachment.key),
    ].join('|');
    setMailComposeForm((previous) => {
      if (!previous.scheduleId || previous.autoAttachmentSeed === seed) {
        return previous;
      }
      return {
        ...previous,
        autoAttachments,
        autoAttachmentSeed: seed,
        excludedAutoAttachmentKeys: [],
      };
    });
  }, [currentView, mailboxData, mailboxThreadId, mailComposeForm.scheduleId]);

  useEffect(() => {
    if (currentView !== 'mail' || !mailboxData || !mailComposeForm.followupId || mailComposeForm.toEmail) {
      return;
    }
    const customer = mailboxData.create.customers.find((item) => String(item.id) === mailComposeForm.followupId);
    if (!customer?.email) {
      return;
    }
    setMailComposeForm((previous) => (
      previous.toEmail
        ? previous
        : {
          ...previous,
          toEmail: customer.email,
        }
    ));
  }, [currentView, mailboxData, mailComposeForm.followupId, mailComposeForm.toEmail]);

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
    const requestedScheduleId = getCreateScheduleParam();
    const requestedCustomer = data?.create.customers.find((customer) => String(customer.id) === requestedCustomerId);
    nextForm.followupId = requestedCustomer?.id
      ? String(requestedCustomer.id)
      : data?.create.customers[0]?.id
        ? String(data.create.customers[0].id)
        : '';
    nextForm.scheduleId = requestedScheduleId;
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
      scheduleId: noteCreateForm.scheduleId ? Number(noteCreateForm.scheduleId) : undefined,
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
  const refreshAIWorkspaceData = async (
    params: { departmentId?: number | null; questionPage?: number; questionScope?: AIWorkspaceQuestionScope } = {},
  ) => {
    const departmentId = params.departmentId !== undefined ? params.departmentId : aiWorkspaceDepartmentId;
    const questionScope = params.questionScope ?? aiWorkspaceQuestionScope;
    const data = await loadAIWorkspaceData({ departmentId, questionPage: params.questionPage, questionScope });
    setAiWorkspaceData(data);
    setAiWorkspaceDepartmentId(data.selectedDepartmentId ?? data.featuredDepartment?.departmentId ?? null);
    return data;
  };
  const handleAIWorkspaceDepartmentSelect = async (department: AIWorkspaceDepartment) => {
    setAiWorkspaceDepartmentId(department.id);
    setAiWorkspaceQuestionScope('department');
    const params = new URLSearchParams(window.location.search);
    params.set('department_id', String(department.id));
    params.delete('department');
    params.delete('question_page');
    params.delete('question_scope');
    const query = params.toString();
    window.history.replaceState(null, '', `/ai-workspace/${query ? `?${query}` : ''}`);
    setAiWorkspaceLoading(true);
    await refreshAIWorkspaceData({ departmentId: department.id, questionScope: 'department', questionPage: 1 });
    setAiWorkspaceLoading(false);
  };
  const handleAIWorkspaceQuestionScopeChange = async (scope: AIWorkspaceQuestionScope) => {
    setAiWorkspaceQuestionScope(scope);
    const params = new URLSearchParams(window.location.search);
    if (aiWorkspaceDepartmentId) {
      params.set('department_id', String(aiWorkspaceDepartmentId));
    } else {
      params.delete('department_id');
    }
    params.delete('department');
    params.delete('question_page');
    if (scope === 'all') {
      params.set('question_scope', 'all');
    } else {
      params.delete('question_scope');
    }
    const query = params.toString();
    window.history.replaceState(null, '', `/ai-workspace/${query ? `?${query}` : ''}`);
    setAiWorkspaceLoading(true);
    await refreshAIWorkspaceData({ departmentId: aiWorkspaceDepartmentId, questionScope: scope, questionPage: 1 });
    setAiWorkspaceLoading(false);
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
  const refreshMailboxData = async () => {
    const data = await loadMailboxData({
      box: mailboxBox,
      q: mailboxQuery,
      page: mailboxPage,
      scheduleId: mailComposeForm.scheduleId ? Number(mailComposeForm.scheduleId) : undefined,
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
  const handleMailComposeFormChange = (field: MailComposeTextField, value: string) => {
    setMailComposeForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setMailComposeError('');
  };
  const handleMailComposeBodyChange = (bodyText: string, bodyHtml: string) => {
    setMailComposeForm((previous) => ({
      ...previous,
      bodyHtml,
      bodyText,
    }));
    setMailComposeError('');
  };
  const handleMailComposeInternalCcChange = (checked: boolean) => {
    setMailComposeForm((previous) => ({
      ...previous,
      includeInternalCc: checked,
      internalCcEmails: checked ? [] : previous.internalCcEmails,
    }));
    setMailComposeError('');
  };
  const handleMailComposeInternalCcEmailsChange = (emails: string[]) => {
    setMailComposeForm((previous) => ({
      ...previous,
      includeInternalCc: false,
      internalCcEmails: emails,
    }));
    setMailComposeError('');
  };
  const handleMailComposeAttachmentsChange = (files: File[]) => {
    if (files.length === 0) {
      return;
    }
    setMailComposeForm((previous) => ({
      ...previous,
      attachments: [...previous.attachments, ...files],
    }));
    setMailComposeError('');
  };
  const handleMailComposeAttachmentRemove = (index: number) => {
    setMailComposeForm((previous) => ({
      ...previous,
      attachments: previous.attachments.filter((_, fileIndex) => fileIndex !== index),
    }));
    setMailComposeError('');
  };
  const handleMailComposeAutoAttachmentRemove = (key: string) => {
    setMailComposeForm((previous) => ({
      ...previous,
      excludedAutoAttachmentKeys: previous.excludedAutoAttachmentKeys.includes(key)
        ? previous.excludedAutoAttachmentKeys
        : [...previous.excludedAutoAttachmentKeys, key],
    }));
    setMailComposeError('');
  };
  const handleMailComposeCustomerChange = (customerId: string) => {
    const customer = mailboxData?.create.customers.find((item) => String(item.id) === customerId);
    setMailComposeForm((previous) => ({
      ...previous,
      autoAttachments: previous.followupId === customerId ? previous.autoAttachments : [],
      autoAttachmentSeed: previous.followupId === customerId ? previous.autoAttachmentSeed : '',
      excludedAutoAttachmentKeys: previous.followupId === customerId ? previous.excludedAutoAttachmentKeys : [],
      followupId: customerId,
      scheduleId: previous.followupId === customerId ? previous.scheduleId : '',
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
    bodyHtml: form.bodyHtml.trim() || undefined,
    followupId: form.followupId ? Number(form.followupId) : undefined,
    scheduleId: form.scheduleId ? Number(form.scheduleId) : undefined,
    businessCardId: form.businessCardId ? Number(form.businessCardId) : undefined,
    includeInternalCc: form.includeInternalCc,
    internalCcEmails: form.includeInternalCc ? [] : form.internalCcEmails,
    attachments: form.attachments,
    excludedAutoAttachmentKeys: form.excludedAutoAttachmentKeys,
  });
  const handleMailComposeSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!mailboxData || mailComposing) {
      return;
    }
    const payload = makeMailboxPayload(mailComposeForm);
    if (!payload.toEmail || !payload.subject || (!payload.bodyText && !mailHtmlHasMeaningfulContent(payload.bodyHtml || ''))) {
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
  const handleMailReplyFormChange = (field: MailComposeTextField, value: string) => {
    setMailReplyForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setMailReplyError('');
  };
  const handleMailReplyBodyChange = (bodyText: string, bodyHtml: string) => {
    setMailReplyForm((previous) => ({
      ...previous,
      bodyHtml,
      bodyText,
    }));
    setMailReplyError('');
  };
  const handleMailReplyInternalCcChange = (checked: boolean) => {
    setMailReplyForm((previous) => ({
      ...previous,
      includeInternalCc: checked,
      internalCcEmails: checked ? [] : previous.internalCcEmails,
    }));
    setMailReplyError('');
  };
  const handleMailReplyInternalCcEmailsChange = (emails: string[]) => {
    setMailReplyForm((previous) => ({
      ...previous,
      includeInternalCc: false,
      internalCcEmails: emails,
    }));
    setMailReplyError('');
  };
  const handleMailReplyAttachmentsChange = (files: File[]) => {
    if (files.length === 0) {
      return;
    }
    setMailReplyForm((previous) => ({
      ...previous,
      attachments: [...previous.attachments, ...files],
    }));
    setMailReplyError('');
  };
  const handleMailReplyAttachmentRemove = (index: number) => {
    setMailReplyForm((previous) => ({
      ...previous,
      attachments: previous.attachments.filter((_, fileIndex) => fileIndex !== index),
    }));
    setMailReplyError('');
  };
  const handleMailReplySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!mailboxThreadData || mailReplySaving) {
      return;
    }
    const payload = makeMailboxPayload(mailReplyForm);
    if (!payload.toEmail || !payload.subject || (!payload.bodyText && !mailHtmlHasMeaningfulContent(payload.bodyHtml || ''))) {
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

  if (currentView === 'assets') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <CustomerAssetsPage
          calibration={assetDirectoryCalibration}
          data={assetsData}
          loading={assetsLoading}
          owner={assetDirectoryOwner}
          query={assetDirectoryQuery}
          service={assetDirectoryService}
          status={assetDirectoryStatus}
          onCalibrationChange={setAssetDirectoryCalibration}
          onOwnerChange={setAssetDirectoryOwner}
          onQueryChange={setAssetDirectoryQuery}
          onServiceChange={setAssetDirectoryService}
          onStatusChange={setAssetDirectoryStatus}
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

  if (currentView === 'tasks') {
    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <TasksPage managerRoute={isTaskManagerRoute()} routeData={pipelineData} />
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
            onReplyAttachmentRemove={handleMailReplyAttachmentRemove}
            onReplyAttachmentsChange={handleMailReplyAttachmentsChange}
            onReplyBodyChange={handleMailReplyBodyChange}
            onReplyFormChange={handleMailReplyFormChange}
            onReplyInternalCcChange={handleMailReplyInternalCcChange}
            onReplyInternalCcEmailsChange={handleMailReplyInternalCcEmailsChange}
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
          onComposeAutoAttachmentRemove={handleMailComposeAutoAttachmentRemove}
          onComposeAttachmentRemove={handleMailComposeAttachmentRemove}
          onComposeAttachmentsChange={handleMailComposeAttachmentsChange}
          onComposeBodyChange={handleMailComposeBodyChange}
          onComposeCustomerChange={handleMailComposeCustomerChange}
          onComposeFormChange={handleMailComposeFormChange}
          onComposeInternalCcChange={handleMailComposeInternalCcChange}
          onComposeInternalCcEmailsChange={handleMailComposeInternalCcEmailsChange}
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
    if (aiWorkspaceQuestionLogId) {
      return (
        <AppShell activeView={currentView}>
          <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
          <AIWorkspaceQuestionDetailPage
            data={aiWorkspaceQuestionDetailData}
            loading={aiWorkspaceQuestionDetailLoading}
          />
        </AppShell>
      );
    }

    return (
      <AppShell activeView={currentView}>
        <TopBar activeView={currentView} searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <AIWorkspacePage
          data={aiWorkspaceData}
          loading={aiWorkspaceLoading}
          questionScope={aiWorkspaceQuestionScope}
          selectedDepartmentId={aiWorkspaceDepartmentId}
          onDepartmentSelect={handleAIWorkspaceDepartmentSelect}
          onQuestionScopeChange={handleAIWorkspaceQuestionScopeChange}
          onRefresh={refreshAIWorkspaceData}
        />
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
          onRefresh={refreshPipelineData}
          onMoveStage={handleMoveStage}
        />
      </div>
    </AppShell>
  );
}
