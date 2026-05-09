import { mockPipelineData, PipelineData, PipelineStage } from './mockData';

type PipelineApiResponse = PipelineData & {
  success?: boolean;
};

type PipelineMoveResponse = {
  success?: boolean;
  error?: string;
};

type NoteReviewToggleResponse = {
  success?: boolean;
  error?: string;
  is_reviewed?: boolean;
  reviewed_at?: string | null;
  reviewer?: string | null;
};

export type DashboardScheduleItem = {
  id: number;
  type: 'schedule' | 'personal';
  customer: string;
  company: string;
  department: string;
  owner: string;
  date: string;
  time: string;
  activityType: string;
  activityLabel: string;
  status: string;
  statusLabel: string;
  notes: string;
  href: string;
  djangoHref?: string;
  customerHref: string;
  djangoCustomerHref?: string;
};

export type DashboardHistoryItem = {
  id: number;
  customer: string;
  company: string;
  department: string;
  owner: string;
  actionType: string;
  actionLabel: string;
  summary: string;
  nextAction: string;
  nextActionDate: string | null;
  createdAt: string | null;
  reviewed: boolean;
  href: string;
  customerHref: string;
};

export type DashboardCustomerItem = {
  id: number;
  customer: string;
  company: string;
  department: string;
  owner: string;
  priority: string;
  priorityLabel: string;
  status: string;
  statusLabel: string;
  pipelineStage: string;
  pipelineLabel: string;
  grade: string;
  score: number;
  overdue: boolean;
  lastActivity: string | null;
  nextAction: string;
  nextActionDate: string | null;
  href: string;
};

export type DashboardData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
  };
  currentUser: {
    id: number | null;
    name: string;
    role: string;
    roleLabel: string;
    company: string;
  };
  metrics: {
    totalCustomers: number;
    activeCustomers: number;
    todaySchedules: number;
    weeklySchedules: number;
    overdueActions: number;
    dueTodayActions: number;
    recentNotes: number;
    pendingReviews: number;
    monthlyActivity: number;
    monthlyRevenue: number;
  };
  links: {
    operationalDashboard: string;
    createNote: string;
    customers: string;
    customerReport: string;
    notes: string;
    schedules: string;
    calendar: string;
    pipeline: string;
    weeklyReports: string;
    pendingReviews: string;
  };
  today: {
    date: string;
    items: DashboardScheduleItem[];
  };
  upcomingSchedules: DashboardScheduleItem[];
  overdueActions: DashboardHistoryItem[];
  dueTodayActions: DashboardHistoryItem[];
  recentActivities: DashboardHistoryItem[];
  priorityCustomers: DashboardCustomerItem[];
  pipelineSummary: Array<{
    stage: string;
    label: string;
    count: number;
  }>;
  teamActivity: Array<{
    userId: number;
    name: string;
    recentCount: number;
    overdueCount: number;
  }>;
};

export type CustomerItem = {
  id: number;
  customer: string;
  company: string;
  companyId: number | null;
  department: string;
  departmentId: number | null;
  manager: string;
  owner: string;
  ownerId: number;
  priority: string;
  priorityLabel: string;
  status: string;
  statusLabel: string;
  pipelineStage: string;
  pipelineLabel: string;
  grade: string;
  score: number;
  phone: string;
  email: string;
  address: string;
  contactSummary: string;
  notes: string;
  notesFull: string;
  lastActivityAt: string | null;
  lastActivityLabel: string;
  lastActivitySummary: string;
  nextAction: string;
  nextActionDate: string | null;
  overdue: boolean;
  activityCount: number;
  scheduleCount: number;
  upcomingScheduleCount: number;
  overdueActionCount: number;
  upcomingSchedule: {
    id: number;
    date: string | null;
    time: string;
    activityType: string;
    activityLabel: string;
    status: string;
    statusLabel: string;
    location: string;
    notes: string;
    href: string;
    createHistoryHref: string;
  } | null;
  href: string;
  companyHref: string;
  createScheduleHref: string;
};

export type CustomersData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
  };
  filters: {
    q: string;
    owner: string;
    priority: string;
    stage: string;
  };
  options: {
    owners: Array<{ id: number; name: string }>;
    priorities: Array<{ value: string; label: string }>;
    stages: Array<{ value: string; label: string }>;
  };
  metrics: {
    totalCustomers: number;
    filteredCustomers: number;
    activeCustomers: number;
    urgentCustomers: number;
    followupCustomers: number;
    scheduledCustomers: number;
    priorityCustomers: number;
    overdueCustomers: number;
    vipCustomers: number;
  };
  links: {
    createCustomer: string;
    customers: string;
    companies: string;
    customerReport: string;
    createNote: string;
  };
  create: {
    canCreate: boolean;
    message: string;
    submitUrl: string;
    companySubmitUrl: string;
    departmentSubmitUrl: string;
    advancedUrl: string;
    priorities: Array<{ value: string; label: string }>;
    companies: Array<{ id: number; name: string }>;
    departments: Array<{ id: number; name: string; companyId: number; companyName: string }>;
  };
  customers: CustomerItem[];
  priorityCustomers: CustomerItem[];
};

export type CustomerCreatePayload = {
  address?: string;
  companyId: number;
  customerName: string;
  departmentId: number;
  email?: string;
  manager?: string;
  notes?: string;
  phoneNumber?: string;
  priority: string;
};

export type CustomerCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  followup_id?: number;
  followup_text?: string;
  href?: string;
};

export type CustomerEditPayload = {
  address?: string;
  companyId: number;
  customerName: string;
  departmentId: number;
  email?: string;
  manager?: string;
  notes?: string;
  phoneNumber?: string;
  pipelineStage: string;
  priority: string;
  status: string;
};

export type CustomerEditResponse = {
  success: boolean;
  error?: string;
  message?: string;
  followup_id?: number;
  href?: string;
};

export type CompanyCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  company?: {
    id: number;
    name: string;
  };
};

export type DepartmentCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  department?: {
    id: number;
    name: string;
    company_id: number;
    company_name: string;
  };
};

export type CustomerDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
  };
  customer: CustomerItem | null;
  metrics: {
    recentNotes: number;
    upcomingSchedules: number;
    overdueActions: number;
    upcomingActions: number;
  };
  links: {
    customers: string;
    djangoDetail: string;
    djangoEdit: string;
    createSchedule: string;
    createNote: string;
  };
  edit: {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
    priorities: Array<{ value: string; label: string }>;
    statuses: Array<{ value: string; label: string }>;
    stages: Array<{ value: string; label: string }>;
    companies: Array<{ id: number; name: string }>;
    departments: Array<{ id: number; name: string; companyId: number; companyName: string }>;
  };
  recentNotes: NoteItem[];
  overdueActions: NoteItem[];
  upcomingActions: NoteItem[];
  upcomingSchedules: ScheduleItem[];
  recentSchedules: ScheduleItem[];
};

export type NoteItem = {
  id: number;
  customer: string;
  company: string;
  department: string;
  owner: string;
  ownerId: number;
  actionType: string;
  actionLabel: string;
  serviceStatus: string;
  serviceStatusLabel: string;
  summary: string;
  nextAction: string;
  nextActionDate: string | null;
  overdue: boolean;
  activityDate: string | null;
  createdAt: string | null;
  reviewed: boolean;
  reviewedAt: string | null;
  reviewer: string;
  reviewRequired: boolean;
  canReview: boolean;
  reviewToggleHref: string;
  replyCount: number;
  fileCount: number;
  href: string;
  djangoHref: string;
  customerHref: string;
  djangoCustomerHref: string;
  scheduleHref: string;
};

export type NoteFileItem = {
  id: number;
  filename: string;
  size: string;
  downloadHref: string;
  deleteHref?: string;
  canDelete?: boolean;
  uploadedAt: string | null;
  uploadedBy?: string;
};

export type NoteReplyItem = {
  id: number;
  content: string;
  author: string;
  authorRole?: string;
  createdAt: string | null;
  djangoHref: string;
  deleteHref?: string;
  canDelete?: boolean;
};

export type NoteDetailItem = NoteItem & {
  content: string;
  createdBy: string;
  followupId: number | null;
  scheduleId: number | null;
  personalScheduleId: number | null;
  meetingDate: string | null;
  meetingSituation: string;
  meetingResearcherQuote: string;
  meetingConfirmedFacts: string;
  meetingObstacles: string;
  meetingNextAction: string;
  deliveryDate: string | null;
  deliveryAmount: number;
  deliveryItems: string;
  taxInvoiceIssued: boolean;
  files: NoteFileItem[];
  replies: NoteReplyItem[];
  canEdit: boolean;
};

export type NoteDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    canReview: boolean;
    selectedUserId: number | null;
  };
  note: NoteDetailItem | null;
  links: {
    notes: string;
    djangoDetail: string;
    djangoEdit: string;
    customer: string;
    djangoCustomer: string;
    schedule: string;
    createNote: string;
    uploadFiles: string;
  };
  edit: {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
    actionTypes: Array<{ value: string; label: string }>;
    serviceStatuses: Array<{ value: string; label: string }>;
    customers: Array<{
      id: number;
      label: string;
      customer: string;
      company: string;
      department: string;
      priorityLabel: string;
      href: string;
      djangoHref?: string;
    }>;
  };
  comments: {
    canCreate: boolean;
    message: string;
    submitUrl: string;
  };
  relatedNotes: NoteItem[];
};

export type NotesData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    canReview: boolean;
    selectedUserId: number | null;
  };
  filters: {
    q: string;
    owner: string;
    actionType: string;
    review: string;
    nextAction: string;
  };
  options: {
    owners: Array<{ id: number; name: string }>;
    actionTypes: Array<{ value: string; label: string }>;
    reviewStates: Array<{ value: string; label: string }>;
    nextActionStates: Array<{ value: string; label: string }>;
  };
  metrics: {
    totalNotes: number;
    activityNotes: number;
    filteredNotes: number;
    unreviewedNotes: number;
    overdueActions: number;
    upcomingActions: number;
  };
  actionCounts: Array<{
    value: string;
    label: string;
    count: number;
  }>;
  links: {
    createNote: string;
    notes: string;
    unreviewed: string;
    weeklyReports: string;
  };
  create: {
    canCreate: boolean;
    message: string;
    submitUrl: string;
    actionTypes: Array<{ value: string; label: string }>;
    customers: Array<{
      id: number;
      label: string;
      customer: string;
      company: string;
      department: string;
      priorityLabel: string;
      href: string;
    }>;
  };
  notes: NoteItem[];
};

export type NoteCreatePayload = {
  actionType: string;
  activityDate?: string;
  content: string;
  followupId: number;
  nextAction?: string;
  nextActionDate?: string;
};

export type NoteCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  historyId?: number;
  href?: string;
  note?: NoteItem;
};

export type NoteEditPayload = {
  actionType: string;
  activityDate?: string;
  content: string;
  deliveryAmount?: string;
  deliveryItems?: string;
  followupId: number;
  meetingConfirmedFacts?: string;
  meetingNextAction?: string;
  meetingObstacles?: string;
  meetingResearcherQuote?: string;
  meetingSituation?: string;
  nextAction?: string;
  nextActionDate?: string;
  serviceStatus?: string;
};

export type NoteEditResponse = NoteDetailData & {
  success: boolean;
  error?: string;
  message?: string;
};

export type NoteFileActionResponse = {
  success: boolean;
  error?: string;
  message?: string;
  files?: NoteFileItem[];
};

export type NoteReplyActionResponse = {
  success: boolean;
  error?: string;
  message?: string;
  memo?: NoteReplyItem;
};

export type ScheduleItem = {
  id: number;
  type: 'customer' | 'personal';
  followupId: number | null;
  customer: string;
  title: string;
  company: string;
  department: string;
  owner: string;
  ownerId: number;
  date: string | null;
  time: string;
  activityType: string;
  activityLabel: string;
  status: string;
  statusLabel: string;
  location: string;
  notes: string;
  notesFull?: string;
  priority: string;
  priorityLabel: string;
  expectedRevenue: number;
  probability: number;
  expectedCloseDate: string | null;
  purchaseConfirmed?: boolean;
  overdue: boolean;
  historyCount: number;
  href: string;
  djangoHref?: string;
  customerHref: string;
  djangoCustomerHref?: string;
  createHistoryHref: string;
};

export type ScheduleFileItem = {
  id: number;
  filename: string;
  size: string;
  downloadHref: string;
  deleteHref?: string;
  canDelete?: boolean;
  uploadedAt: string | null;
  uploadedBy?: string;
};

export type ScheduleDeliveryItem = {
  id: number;
  itemName: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  totalPrice: number;
  taxInvoiceIssued: boolean;
  notes: string;
};

export type ScheduleDetailItem = ScheduleItem & {
  canEdit: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  vatMode: string;
  usePrepayment: boolean;
  prepaymentAmount: number;
  fileCount: number;
  emailThreadCount: number;
  files: ScheduleFileItem[];
};

export type ScheduleCreatePayload = {
  activityType: string;
  expectedRevenue?: string;
  followupId: number;
  location?: string;
  notes?: string;
  probability?: string;
  visitDate: string;
  visitTime: string;
};

export type ScheduleCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  scheduleId?: number;
  href?: string;
  schedule?: ScheduleItem;
};

export type ScheduleEditPayload = {
  activityType: string;
  expectedCloseDate?: string;
  expectedRevenue?: string;
  followupId: number;
  location?: string;
  notes?: string;
  probability?: string;
  purchaseConfirmed?: boolean;
  status: string;
  visitDate: string;
  visitTime: string;
};

export type SchedulesData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
  };
  filters: {
    q: string;
    owner: string;
    status: string;
    activityType: string;
    range: string;
  };
  options: {
    owners: Array<{ id: number; name: string }>;
    statuses: Array<{ value: string; label: string }>;
    activityTypes: Array<{ value: string; label: string }>;
    ranges: Array<{ value: string; label: string }>;
  };
  metrics: {
    totalSchedules: number;
    customerSchedules: number;
    personalSchedules: number;
    filteredSchedules: number;
    todaySchedules: number;
    weekSchedules: number;
    overdueSchedules: number;
    scheduledSchedules: number;
    completedSchedules: number;
    cancelledSchedules: number;
  };
  statusCounts: Array<{
    value: string;
    label: string;
    count: number;
  }>;
  activityCounts: Array<{
    value: string;
    label: string;
    count: number;
  }>;
  links: {
    createSchedule: string;
    createPersonalSchedule: string;
    schedules: string;
    calendar: string;
    weeklyReports: string;
  };
  create: {
    canCreate: boolean;
    message: string;
    submitUrl: string;
    activityTypes: Array<{ value: string; label: string }>;
    customers: Array<{
      id: number;
      label: string;
      customer: string;
      company: string;
      department: string;
      priorityLabel: string;
      href: string;
      djangoHref?: string;
    }>;
  };
  today: ScheduleItem[];
  upcoming: ScheduleItem[];
  overdue: ScheduleItem[];
  schedules: ScheduleItem[];
};

export type ScheduleDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    canReview: boolean;
    selectedUserId: number | null;
  };
  schedule: ScheduleDetailItem | null;
  links: {
    schedules: string;
    djangoSchedules: string;
    calendar: string;
    djangoDetail: string;
    djangoEdit: string;
    customer: string;
    djangoCustomer: string;
    createNote: string;
    uploadFiles: string;
  };
  edit: {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
    activityTypes: Array<{ value: string; label: string }>;
    statuses: Array<{ value: string; label: string }>;
    customers: Array<{
      id: number;
      label: string;
      customer: string;
      company: string;
      department: string;
      priorityLabel: string;
      href: string;
      djangoHref?: string;
    }>;
  };
  relatedNotes: NoteItem[];
  deliveryItems: ScheduleDeliveryItem[];
};

export type ScheduleEditResponse = ScheduleDetailData & {
  success: boolean;
  error?: string;
  message?: string;
};

export type ScheduleFileActionResponse = {
  success: boolean;
  error?: string;
  message?: string;
  files?: ScheduleFileItem[];
};

export type AIWorkspaceDepartment = {
  id: number;
  name: string;
  company: string;
  customerCount: number;
  customerPreview: string[];
  hasAnalysis: boolean;
  meetingCount: number;
  quoteCount: number;
  deliveryCount: number;
  painpointCount: number;
  unverifiedPainpointCount: number;
  summary: string;
  updatedAt: string | null;
  href: string;
  hubHref: string;
  runHref: string;
};

export type AIWorkspacePainpoint = {
  id: number;
  category: string;
  categoryLabel: string;
  hypothesis: string;
  confidence: string;
  confidenceLabel: string;
  confidenceScore: number;
  department: string;
  company: string;
  question: string;
  href: string;
};

export type AIWorkspaceFollowupTarget = {
  id: number;
  customer: string;
  company: string;
  department: string;
  grade: string;
  score: number;
  priority: string;
  priorityLabel: string;
  hasAnalysis: boolean;
  analysisUpdatedAt: string | null;
  analysisSummary: string;
  href: string;
  customerHref: string;
};

export type AIWorkspaceAnalysis = {
  id: number;
  departmentId?: number;
  followupId?: number;
  department?: string;
  customer?: string;
  company: string;
  summary: string;
  meetingCount: number;
  quoteCount?: number;
  deliveryCount?: number;
  updatedAt: string | null;
  href: string;
};

export type AIWorkspacePromptTarget = {
  id: string;
  type: 'department' | 'followup' | 'painpoint';
  typeLabel: string;
  title: string;
  subtitle: string;
  priority: string;
  context: string[];
  prompt: string;
  href: string;
};

export type AIWorkspaceData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  currentUser: {
    id: number | null;
    name: string;
    role: string;
    roleLabel: string;
    company: string;
    canUseAi: boolean;
  };
  permission: {
    canUseAi: boolean;
    message: string;
  };
  metrics: {
    departmentsWithCustomers: number;
    analyzedDepartments: number;
    painpointCards: number;
    unverifiedPainpoints: number;
    followupAnalyses: number;
    weeklyReportsThisMonth: number;
  };
  links: {
    aiHub: string;
    weeklyReports: string;
    weeklyReportCreate: string;
    weeklyAiDraft: string;
    customers: string;
    notes: string;
    dashboard: string;
  };
  week: {
    start: string;
    end: string;
  };
  departments: AIWorkspaceDepartment[];
  recentDepartmentAnalyses: AIWorkspaceAnalysis[];
  painpoints: AIWorkspacePainpoint[];
  followupTargets: AIWorkspaceFollowupTarget[];
  recentFollowupAnalyses: AIWorkspaceAnalysis[];
  promptTargets: AIWorkspacePromptTarget[];
  recommendedGoals: Array<{
    title: string;
    description: string;
    reason: string;
  }>;
};

const emptyDashboardData: DashboardData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  currentUser: {
    id: null,
    name: '',
    role: '',
    roleLabel: '',
    company: '',
  },
  metrics: {
    totalCustomers: 0,
    activeCustomers: 0,
    todaySchedules: 0,
    weeklySchedules: 0,
    overdueActions: 0,
    dueTodayActions: 0,
    recentNotes: 0,
    pendingReviews: 0,
    monthlyActivity: 0,
    monthlyRevenue: 0,
  },
  links: {
    operationalDashboard: '/reporting/dashboard/',
    createNote: '/notes/?create=1',
    customers: '/reporting/followups/',
    customerReport: '/reporting/customer-report/',
    notes: '/reporting/histories/',
    schedules: '/reporting/schedules/',
    calendar: '/reporting/schedules/calendar/',
    pipeline: '/reporting/funnel/pipeline/',
    weeklyReports: '/reporting/weekly-reports/',
    pendingReviews: '/reporting/histories/?review_filter=unreviewed',
  },
  today: {
    date: '',
    items: [],
  },
  upcomingSchedules: [],
  overdueActions: [],
  dueTodayActions: [],
  recentActivities: [],
  priorityCustomers: [],
  pipelineSummary: [],
  teamActivity: [],
};

const emptyCustomersData: CustomersData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  filters: {
    q: '',
    owner: '',
    priority: '',
    stage: '',
  },
  options: {
    owners: [],
    priorities: [],
    stages: [],
  },
  metrics: {
    totalCustomers: 0,
    filteredCustomers: 0,
    activeCustomers: 0,
    urgentCustomers: 0,
    followupCustomers: 0,
    scheduledCustomers: 0,
    priorityCustomers: 0,
    overdueCustomers: 0,
    vipCustomers: 0,
  },
  links: {
    createCustomer: '/customers/?create=1',
    customers: '/reporting/followups/',
    companies: '/reporting/companies/',
    customerReport: '/reporting/customer-report/',
    createNote: '/notes/?create=1',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/followups/create/',
    companySubmitUrl: '/reporting/api/companies/create/',
    departmentSubmitUrl: '/reporting/api/departments/create/',
    advancedUrl: '/reporting/followups/create/',
    priorities: [],
    companies: [],
    departments: [],
  },
  customers: [],
  priorityCustomers: [],
};

const emptyCustomerDetailData: CustomerDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  customer: null,
  metrics: {
    recentNotes: 0,
    upcomingSchedules: 0,
    overdueActions: 0,
    upcomingActions: 0,
  },
  links: {
    customers: '/customers/',
    djangoDetail: '',
    djangoEdit: '',
    createSchedule: '/schedules/?create=1',
    createNote: '/notes/?create=1',
  },
  edit: {
    canEdit: false,
    message: '',
    submitUrl: '',
    djangoUrl: '',
    priorities: [],
    statuses: [],
    stages: [],
    companies: [],
    departments: [],
  },
  recentNotes: [],
  overdueActions: [],
  upcomingActions: [],
  upcomingSchedules: [],
  recentSchedules: [],
};

const emptyNotesData: NotesData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    canReview: false,
    selectedUserId: null,
  },
  filters: {
    q: '',
    owner: '',
    actionType: '',
    review: '',
    nextAction: '',
  },
  options: {
    owners: [],
    actionTypes: [],
    reviewStates: [],
    nextActionStates: [],
  },
  metrics: {
    totalNotes: 0,
    activityNotes: 0,
    filteredNotes: 0,
    unreviewedNotes: 0,
    overdueActions: 0,
    upcomingActions: 0,
  },
  actionCounts: [],
  links: {
    createNote: '/notes/?create=1',
    notes: '/reporting/histories/',
    unreviewed: '/reporting/histories/?review_filter=unreviewed',
    weeklyReports: '/reporting/weekly-reports/',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/notes/create/',
    actionTypes: [],
    customers: [],
  },
  notes: [],
};

const emptyNoteDetailData: NoteDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    canReview: false,
    selectedUserId: null,
  },
  note: null,
  links: {
    notes: '/notes/',
    djangoDetail: '',
    djangoEdit: '',
    customer: '',
    djangoCustomer: '',
    schedule: '',
    createNote: '/notes/?create=1',
    uploadFiles: '',
  },
  edit: {
    canEdit: false,
    message: '',
    submitUrl: '',
    djangoUrl: '',
    actionTypes: [],
    serviceStatuses: [],
    customers: [],
  },
  comments: {
    canCreate: false,
    message: '',
    submitUrl: '',
  },
  relatedNotes: [],
};

const emptySchedulesData: SchedulesData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  filters: {
    q: '',
    owner: '',
    status: '',
    activityType: '',
    range: '',
  },
  options: {
    owners: [],
    statuses: [],
    activityTypes: [],
    ranges: [],
  },
  metrics: {
    totalSchedules: 0,
    customerSchedules: 0,
    personalSchedules: 0,
    filteredSchedules: 0,
    todaySchedules: 0,
    weekSchedules: 0,
    overdueSchedules: 0,
    scheduledSchedules: 0,
    completedSchedules: 0,
    cancelledSchedules: 0,
  },
  statusCounts: [],
  activityCounts: [],
  links: {
    createSchedule: '/reporting/schedules/create/',
    createPersonalSchedule: '/reporting/personal-schedules/create/',
    schedules: '/reporting/schedules/',
    calendar: '/reporting/schedules/calendar/',
    weeklyReports: '/reporting/weekly-reports/',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/schedules/create/',
    activityTypes: [],
    customers: [],
  },
  today: [],
  upcoming: [],
  overdue: [],
  schedules: [],
};

const emptyScheduleDetailData: ScheduleDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    canReview: false,
    selectedUserId: null,
  },
  schedule: null,
  links: {
    schedules: '/schedules/',
    djangoSchedules: '/reporting/schedules/',
    calendar: '/reporting/schedules/calendar/',
    djangoDetail: '',
    djangoEdit: '',
    customer: '',
    djangoCustomer: '',
    createNote: '',
    uploadFiles: '',
  },
  edit: {
    canEdit: false,
    message: '',
    submitUrl: '',
    djangoUrl: '',
    activityTypes: [],
    statuses: [],
    customers: [],
  },
  relatedNotes: [],
  deliveryItems: [],
};

const emptyAIWorkspaceData: AIWorkspaceData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  currentUser: {
    id: null,
    name: '',
    role: '',
    roleLabel: '',
    company: '',
    canUseAi: false,
  },
  permission: {
    canUseAi: false,
    message: '',
  },
  metrics: {
    departmentsWithCustomers: 0,
    analyzedDepartments: 0,
    painpointCards: 0,
    unverifiedPainpoints: 0,
    followupAnalyses: 0,
    weeklyReportsThisMonth: 0,
  },
  links: {
    aiHub: '/ai/',
    weeklyReports: '/reporting/weekly-reports/',
    weeklyReportCreate: '/reporting/weekly-reports/create/',
    weeklyAiDraft: '/reporting/api/weekly-reports/ai-draft/',
    customers: '/reporting/followups/',
    notes: '/reporting/histories/',
    dashboard: '/reporting/dashboard/',
  },
  week: {
    start: '',
    end: '',
  },
  departments: [],
  recentDepartmentAnalyses: [],
  painpoints: [],
  followupTargets: [],
  recentFollowupAnalyses: [],
  promptTargets: [],
  recommendedGoals: [],
};

function getCookie(name: string): string {
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));
  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : '';
}

class LoginRequiredRedirectError extends Error {
  constructor() {
    super('login_required');
    this.name = 'LoginRequiredRedirectError';
  }
}

function getFrontendNextPath(): string {
  const path = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  return path || '/';
}

function responseUrlPathname(response: Response): string {
  try {
    return new URL(response.url).pathname;
  } catch {
    return '';
  }
}

function redirectToLogin(): never {
  const currentPath = window.location.pathname;
  if (!currentPath.startsWith('/reporting/login')) {
    window.location.replace(`/reporting/login/?next=${encodeURIComponent(getFrontendNextPath())}`);
  }
  throw new LoginRequiredRedirectError();
}

function getPayloadError(payload: unknown): string {
  if (!payload || typeof payload !== 'object') {
    return '';
  }
  const error = 'error' in payload ? payload.error : '';
  return typeof error === 'string' ? error : '';
}

function redirectIfLoginRequired(response: Response, payload?: unknown): void {
  const finalPath = responseUrlPathname(response);
  const redirectedToLogin = response.redirected && finalPath.startsWith('/reporting/login');
  const jsonLoginRequired = response.status === 401 && getPayloadError(payload) === 'login_required';

  if (redirectedToLogin || jsonLoginRequired) {
    redirectToLogin();
  }
}

export async function loadDashboardData(): Promise<DashboardData> {
  try {
    const response = await fetch('/reporting/api/dashboard/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Dashboard API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as DashboardData;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Dashboard API unavailable: ${response.status}`);
    }
    return payload;
  } catch (error) {
    return {
      ...emptyDashboardData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Dashboard API unavailable',
    };
  }
}

export async function loadCustomersData(params: {
  q?: string;
  owner?: string;
  priority?: string;
  stage?: string;
} = {}): Promise<CustomersData> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  try {
    const response = await fetch(`/reporting/api/customers/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Customers API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as CustomersData;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Customers API unavailable: ${response.status}`);
    }
    return {
      ...emptyCustomersData,
      ...payload,
      scope: {
        ...emptyCustomersData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyCustomersData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyCustomersData.options,
        ...(payload.options ?? {}),
      },
      metrics: {
        ...emptyCustomersData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyCustomersData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptyCustomersData.create,
        ...(payload.create ?? {}),
      },
      customers: payload.customers ?? emptyCustomersData.customers,
      priorityCustomers: payload.priorityCustomers ?? emptyCustomersData.priorityCustomers,
    };
  } catch (error) {
    return {
      ...emptyCustomersData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Customers API unavailable',
    };
  }
}

export async function createCustomer(
  payload: CustomerCreatePayload,
  submitUrl = '/reporting/api/followups/create/',
): Promise<CustomerCreateResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('customer_name', payload.customerName);
  body.set('company', String(payload.companyId));
  body.set('department', String(payload.departmentId));
  body.set('priority', payload.priority);
  if (payload.manager) body.set('manager', payload.manager);
  if (payload.phoneNumber) body.set('phone_number', payload.phoneNumber);
  if (payload.email) body.set('email', payload.email);
  if (payload.address) body.set('address', payload.address);
  if (payload.notes) body.set('notes', payload.notes);

  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Customer create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as CustomerCreateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Customer create failed: ${response.status}`);
  }
  return {
    ...data,
    href: data.href || (data.followup_id ? `/customers/${data.followup_id}/` : ''),
  };
}

export async function updateCustomer(
  payload: CustomerEditPayload,
  submitUrl: string,
): Promise<CustomerEditResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('customer_name', payload.customerName);
  body.set('company', String(payload.companyId));
  body.set('department', String(payload.departmentId));
  body.set('priority', payload.priority);
  body.set('status', payload.status);
  body.set('pipeline_stage', payload.pipelineStage);
  if (payload.manager) body.set('manager', payload.manager);
  if (payload.phoneNumber) body.set('phone_number', payload.phoneNumber);
  if (payload.email) body.set('email', payload.email);
  if (payload.address) body.set('address', payload.address);
  if (payload.notes) body.set('notes', payload.notes);

  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Customer update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as CustomerEditResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Customer update failed: ${response.status}`);
  }
  return data;
}

export async function createCompany(name: string, submitUrl = '/reporting/api/companies/create/'): Promise<CompanyCreateResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('name', name);

  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Company create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as CompanyCreateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false || !data.company) {
    throw new Error(data.error || data.message || `Company create failed: ${response.status}`);
  }
  return data;
}

export async function createDepartment(
  companyId: number,
  name: string,
  submitUrl = '/reporting/api/departments/create/',
): Promise<DepartmentCreateResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('company_id', String(companyId));
  body.set('name', name);

  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Department create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as DepartmentCreateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false || !data.department) {
    throw new Error(data.error || data.message || `Department create failed: ${response.status}`);
  }
  return data;
}

export async function loadCustomerDetailData(customerId: number): Promise<CustomerDetailData> {
  try {
    const response = await fetch(`/reporting/api/customers/${customerId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Customer detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<CustomerDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Customer detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyCustomerDetailData,
      ...payload,
      scope: {
        ...emptyCustomerDetailData.scope,
        ...(payload.scope ?? {}),
      },
      metrics: {
        ...emptyCustomerDetailData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyCustomerDetailData.links,
        ...(payload.links ?? {}),
      },
      edit: {
        ...emptyCustomerDetailData.edit,
        ...(payload.edit ?? {}),
      },
      recentNotes: payload.recentNotes ?? emptyCustomerDetailData.recentNotes,
      overdueActions: payload.overdueActions ?? emptyCustomerDetailData.overdueActions,
      upcomingActions: payload.upcomingActions ?? emptyCustomerDetailData.upcomingActions,
      upcomingSchedules: payload.upcomingSchedules ?? emptyCustomerDetailData.upcomingSchedules,
      recentSchedules: payload.recentSchedules ?? emptyCustomerDetailData.recentSchedules,
      customer: payload.customer ?? emptyCustomerDetailData.customer,
    };
  } catch (error) {
    return {
      ...emptyCustomerDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Customer detail API unavailable',
    };
  }
}

export async function loadNotesData(params: {
  q?: string;
  owner?: string;
  actionType?: string;
  review?: string;
  nextAction?: string;
} = {}): Promise<NotesData> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  try {
    const response = await fetch(`/reporting/api/notes/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Notes API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<NotesData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Notes API unavailable: ${response.status}`);
    }
    return {
      ...emptyNotesData,
      ...payload,
      scope: {
        ...emptyNotesData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyNotesData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyNotesData.options,
        ...(payload.options ?? {}),
      },
      metrics: {
        ...emptyNotesData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyNotesData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptyNotesData.create,
        ...(payload.create ?? {}),
      },
      actionCounts: payload.actionCounts ?? emptyNotesData.actionCounts,
      notes: payload.notes ?? emptyNotesData.notes,
    };
  } catch (error) {
    return {
      ...emptyNotesData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Notes API unavailable',
    };
  }
}

export async function loadNoteDetailData(noteId: number): Promise<NoteDetailData> {
  try {
    const response = await fetch(`/reporting/api/notes/${noteId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Note detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<NoteDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Note detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyNoteDetailData,
      ...payload,
      scope: {
        ...emptyNoteDetailData.scope,
        ...(payload.scope ?? {}),
      },
      links: {
        ...emptyNoteDetailData.links,
        ...(payload.links ?? {}),
      },
      edit: {
        ...emptyNoteDetailData.edit,
        ...(payload.edit ?? {}),
      },
      comments: {
        ...emptyNoteDetailData.comments,
        ...(payload.comments ?? {}),
      },
      note: payload.note ?? emptyNoteDetailData.note,
      relatedNotes: payload.relatedNotes ?? emptyNoteDetailData.relatedNotes,
    };
  } catch (error) {
    return {
      ...emptyNoteDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Note detail API unavailable',
    };
  }
}

export async function createNote(payload: NoteCreatePayload, submitUrl = '/reporting/api/notes/create/'): Promise<NoteCreateResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteCreateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note create failed: ${response.status}`);
  }
  return data;
}

export async function updateNote(payload: NoteEditPayload, submitUrl: string): Promise<NoteEditResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteEditResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note update failed: ${response.status}`);
  }
  return data;
}

export async function uploadNoteFiles(uploadUrl: string, files: File[]): Promise<NoteFileActionResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const csrfToken = getCookie('csrftoken');
  const response = await fetch(uploadUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: formData,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note file upload API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteFileActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note file upload failed: ${response.status}`);
  }
  return data;
}

export async function deleteNoteFile(deleteUrl: string): Promise<NoteFileActionResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(deleteUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note file delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteFileActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note file delete failed: ${response.status}`);
  }
  return data;
}

export async function addNoteReply(submitUrl: string, memo: string): Promise<NoteReplyActionResponse> {
  const formData = new FormData();
  formData.append('memo', memo);

  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: formData,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note reply API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteReplyActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note reply failed: ${response.status}`);
  }
  return data;
}

export async function deleteNoteReply(deleteUrl: string): Promise<NoteReplyActionResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(deleteUrl, {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note reply delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as NoteReplyActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Note reply delete failed: ${response.status}`);
  }
  return data;
}

export async function toggleNoteReviewed(reviewToggleHref: string): Promise<void> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(reviewToggleHref, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Note review API unavailable: ${response.status}`);
  }
  const payload = (await response.json()) as NoteReviewToggleResponse;
  redirectIfLoginRequired(response, payload);
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || `Note review failed: ${response.status}`);
  }
}

export async function loadSchedulesData(params: {
  q?: string;
  owner?: string;
  status?: string;
  activityType?: string;
  range?: string;
} = {}): Promise<SchedulesData> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  try {
    const response = await fetch(`/reporting/api/schedules/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Schedules API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<SchedulesData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Schedules API unavailable: ${response.status}`);
    }
    return {
      ...emptySchedulesData,
      ...payload,
      scope: {
        ...emptySchedulesData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptySchedulesData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptySchedulesData.options,
        ...(payload.options ?? {}),
      },
      metrics: {
        ...emptySchedulesData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptySchedulesData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptySchedulesData.create,
        ...(payload.create ?? {}),
      },
      statusCounts: payload.statusCounts ?? emptySchedulesData.statusCounts,
      activityCounts: payload.activityCounts ?? emptySchedulesData.activityCounts,
      today: payload.today ?? emptySchedulesData.today,
      upcoming: payload.upcoming ?? emptySchedulesData.upcoming,
      overdue: payload.overdue ?? emptySchedulesData.overdue,
      schedules: payload.schedules ?? emptySchedulesData.schedules,
    };
  } catch (error) {
    return {
      ...emptySchedulesData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Schedules API unavailable',
    };
  }
}

export async function createSchedule(payload: ScheduleCreatePayload, submitUrl = '/reporting/api/schedules/create/'): Promise<ScheduleCreateResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleCreateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule create failed: ${response.status}`);
  }
  return data;
}

export async function loadScheduleDetailData(scheduleId: number): Promise<ScheduleDetailData> {
  try {
    const response = await fetch(`/reporting/api/schedules/${scheduleId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Schedule detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<ScheduleDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Schedule detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyScheduleDetailData,
      ...payload,
      scope: {
        ...emptyScheduleDetailData.scope,
        ...(payload.scope ?? {}),
      },
      links: {
        ...emptyScheduleDetailData.links,
        ...(payload.links ?? {}),
      },
      edit: {
        ...emptyScheduleDetailData.edit,
        ...(payload.edit ?? {}),
      },
      schedule: payload.schedule ?? emptyScheduleDetailData.schedule,
      relatedNotes: payload.relatedNotes ?? emptyScheduleDetailData.relatedNotes,
      deliveryItems: payload.deliveryItems ?? emptyScheduleDetailData.deliveryItems,
    };
  } catch (error) {
    return {
      ...emptyScheduleDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Schedule detail API unavailable',
    };
  }
}

export async function updateSchedule(payload: ScheduleEditPayload, submitUrl: string): Promise<ScheduleEditResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleEditResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule update failed: ${response.status}`);
  }
  return data;
}

export async function uploadScheduleFiles(uploadUrl: string, files: File[]): Promise<ScheduleFileActionResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const csrfToken = getCookie('csrftoken');
  const response = await fetch(uploadUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: formData,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule file upload API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleFileActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule file upload failed: ${response.status}`);
  }
  return data;
}

export async function deleteScheduleFile(deleteUrl: string): Promise<ScheduleFileActionResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(deleteUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule file delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleFileActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule file delete failed: ${response.status}`);
  }
  return data;
}

export async function loadAIWorkspaceData(): Promise<AIWorkspaceData> {
  try {
    const response = await fetch('/reporting/api/ai-workspace/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`AI workspace API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as AIWorkspaceData;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `AI workspace API unavailable: ${response.status}`);
    }
    return {
      ...payload,
      promptTargets: payload.promptTargets ?? [],
    };
  } catch (error) {
    return {
      ...emptyAIWorkspaceData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'AI workspace API unavailable',
    };
  }
}

export async function loadPipelineData(): Promise<PipelineData> {
  try {
    const response = await fetch('/reporting/api/pipeline/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!response.ok || !contentType.includes('application/json')) {
      throw new Error(`Pipeline API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as PipelineApiResponse;
    redirectIfLoginRequired(response, payload);
    if (payload.success === false || !Array.isArray(payload.deals)) {
      throw new Error('Pipeline API returned invalid payload');
    }
    return {
      ...payload,
      source: 'django',
    };
  } catch {
    return mockPipelineData;
  }
}

export async function moveDealStage(dealId: number, stage: PipelineStage): Promise<void> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/reporting/funnel/api/pipeline-move/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ followup_id: dealId, stage }),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Pipeline move API unavailable: ${response.status}`);
  }
  const payload = (await response.json()) as PipelineMoveResponse;
  redirectIfLoginRequired(response, payload);
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || `Pipeline move failed: ${response.status}`);
  }
}
