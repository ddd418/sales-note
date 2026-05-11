import { emptyPipelineData, PipelineData, PipelineStage } from './mockData';

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

export type MailboxType = 'inbox' | 'sent' | 'starred' | 'archived' | 'trash';

export type MailboxEmailItem = {
  id: number;
  type: 'sent' | 'received';
  typeLabel: string;
  subject: string;
  contact: string;
  senderEmail: string;
  recipientEmail: string;
  ccEmails: string;
  preview: string;
  bodyText: string;
  sentAt: string | null;
  receivedAt: string | null;
  happenedAt: string | null;
  isRead: boolean;
  isStarred: boolean;
  isArchived: boolean;
  isTrashed: boolean;
  threadId: string;
  threadHref: string;
  djangoThreadHref: string;
  replyHref: string;
  toggleStarHref: string;
  archiveHref: string;
  trashHref: string;
  restoreHref: string;
  deleteHref: string;
  followup: {
    id: number | null;
    customer: string;
    company: string;
    department: string;
    href: string;
    djangoHref: string;
  };
  schedule: {
    id: number | null;
    href: string;
    djangoHref: string;
  };
  attachments: Array<{
    filename?: string;
    size?: number;
    mimetype?: string;
  }>;
};

export type MailboxCreateOptions = {
  canSend: boolean;
  message: string;
  submitUrl: string;
  djangoUrl: string;
  customers: Array<{
    id: number;
    customer: string;
    company: string;
    department: string;
    email: string;
  }>;
  businessCards: Array<{
    id: number;
    name: string;
    fullName: string;
    email: string;
    isDefault: boolean;
  }>;
};

export type MailboxData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  mailboxType: MailboxType;
  filters: {
    q: string;
    page: number;
  };
  connection: {
    connected: boolean;
    provider: string;
    address: string;
    gmailConnected: boolean;
    imapConnected: boolean;
    lastSyncAt: string | null;
    connectHref: string;
    imapConnectHref: string;
    profileHref: string;
  };
  counts: Record<MailboxType | 'unread', number>;
  pagination: {
    page: number;
    totalPages: number;
    totalCount: number;
    hasNext: boolean;
    hasPrevious: boolean;
    nextPage: number | null;
    previousPage: number | null;
  };
  links: {
    inbox: string;
    sent: string;
    starred: string;
    archived: string;
    trash: string;
    sync: string;
    djangoInbox: string;
    djangoSent: string;
  };
  create: MailboxCreateOptions;
  emails: MailboxEmailItem[];
};

export type MailboxThreadData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  thread: {
    id: string;
    subject: string;
    followup: MailboxEmailItem['followup'] | null;
    messageCount: number;
    lastReceivedEmailId: number | null;
  };
  connection: MailboxData['connection'];
  links: {
    mailbox: string;
    djangoThread: string;
    reply: string;
  };
  create: MailboxCreateOptions;
  emails: MailboxEmailItem[];
};

export type MailboxSendPayload = {
  toEmail: string;
  ccEmails?: string;
  bccEmails?: string;
  subject: string;
  bodyText: string;
  followupId?: number;
  businessCardId?: number;
  attachments?: File[];
};

export type MailboxActionResponse = {
  success?: boolean;
  error?: string;
  message?: string;
  href?: string;
  djangoHref?: string;
  is_starred?: boolean;
  is_archived?: boolean;
  synced?: number;
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
    departments: Array<{ id: number; name: string; companyId: number; companyName: string; searchText?: string }>;
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

export type CustomerPrepaymentSummary = {
  metrics: {
    totalAmount: number;
    totalBalance: number;
    totalUsed: number;
    totalCount: number;
    activeCount: number;
    depletedCount: number;
    cancelledCount: number;
  };
  links: {
    prepayments: string;
    createPrepayment: string;
    customerPrepayments: string;
    djangoCustomerPrepayments: string;
  };
  recentPrepayments: PrepaymentListItem[];
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
  prepaymentSummary: CustomerPrepaymentSummary;
  aiDepartment: CustomerAiDepartment;
  edit: {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
    priorities: Array<{ value: string; label: string }>;
    statuses: Array<{ value: string; label: string }>;
    stages: Array<{ value: string; label: string }>;
    companies: Array<{ id: number; name: string }>;
    departments: Array<{ id: number; name: string; companyId: number; companyName: string; searchText?: string }>;
  };
  recentNotes: NoteItem[];
  overdueActions: NoteItem[];
  upcomingActions: NoteItem[];
  upcomingSchedules: ScheduleItem[];
  recentSchedules: ScheduleItem[];
};

export type CustomerAiDepartment = {
  departmentId: number | null;
  departmentName: string;
  companyName: string;
  canUseAi: boolean;
  canAnalyze: boolean;
  hasAnalysis: boolean;
  message: string;
  summary: string;
  updatedAt: string | null;
  meetingCount: number;
  quoteCount: number;
  deliveryCount: number;
  painpointCount: number;
  unverifiedPainpointCount: number;
  href: string;
  hubHref: string;
  runHref: string;
  periodStart: string | null;
  periodEnd: string | null;
  tokenUsage: number;
  meetingInsights: CustomerAiMeetingInsight[];
  quoteDelivery: CustomerAiQuoteDelivery;
  quoteInsights: CustomerAiQuoteInsights;
  nextActions: CustomerAiNextAction[];
  verificationInsights: CustomerAiVerificationInsight[];
  missingInfo: CustomerAiMissingInfo;
  painpoints: CustomerAiPainpoint[];
};

export type CustomerAiMeetingInsight = {
  theme: string;
  details: string;
  frequency: string;
};

export type CustomerAiQuoteDelivery = {
  totalQuotes: number;
  convertedQuotes: number;
  conversionRate: number;
  totalDeliveries: number;
  avgDeliveryIntervalDays: number;
  productStats: CustomerAiProductStat[];
  recentDeliveries: CustomerAiRecentDelivery[];
};

export type CustomerAiProductStat = {
  name: string;
  quoted: number;
  quoteAmount: number;
  delivered: number;
  deliveryAmount: number;
};

export type CustomerAiDeliveryItem = {
  product: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
};

export type CustomerAiRecentDelivery = {
  date: string;
  customer: string;
  amount: number;
  items: CustomerAiDeliveryItem[];
  source: string;
  scheduleId: number | null;
  notes: string;
};

export type CustomerAiQuoteInsights = {
  conversionAnalysis: string;
  deliveryCycle: string;
  productTrends: string;
  stalledQuotes: Array<{
    quoteInfo: string;
    possibleReason: string;
    suggestion: string;
  }>;
};

export type CustomerAiNextAction = {
  action: string;
  priority: string;
  reason: string;
};

export type CustomerAiVerificationInsight = {
  status: string;
  statusLabel: string;
  hypothesis: string;
  insight: string;
  impact: string;
  previousQuestion: string;
  nextVerification: string;
  verifiedAt: string | null;
};

export type CustomerAiMissingInfo = {
  items: string[];
  questions: string[];
};

export type CustomerAiPainpointEvidence = {
  type: string;
  typeLabel: string;
  text: string;
  sourceSection: string;
};

export type CustomerAiPainpoint = {
  id: number;
  category: string;
  categoryLabel: string;
  hypothesis: string;
  confidence: string;
  confidenceLabel: string;
  confidenceScore: number;
  evidence: CustomerAiPainpointEvidence[];
  attribution: string;
  attributionLabel: string;
  verificationQuestion: string;
  actionIfYes: string;
  actionIfNo: string;
  caution: string;
  verificationStatus: string;
  verificationStatusLabel: string;
  verificationNote: string;
  verifiedAt: string | null;
  canVerify: boolean;
  verifyHref: string;
};

export type AiDepartmentRunResponse = {
  success: boolean;
  error?: string;
  message?: string;
  redirect_url?: string;
  redirectUrl?: string;
  cards_created?: number;
  cardsCreated?: number;
};

export type AiPainpointVerifyResponse = {
  success: boolean;
  error?: string;
  message?: string;
  card_id?: number;
  status?: string;
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

export type ScheduleReportItem = {
  id: number;
  actionType: string;
  actionLabel: string;
  summary: string;
  content: string;
  meetingSituation: string;
  meetingResearcherQuote: string;
  meetingConfirmedFacts: string;
  meetingObstacles: string;
  meetingNextAction: string;
  deliveryItems: string;
  deliveryAmount: number;
  nextAction: string;
  nextActionDate: string | null;
  activityDate: string | null;
  createdAt: string | null;
  overdue: boolean;
  href: string;
  djangoHref: string;
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
  reports?: ScheduleReportItem[];
  href: string;
  djangoHref?: string;
  djangoEditHref?: string;
  statusUpdateHref?: string;
  canEdit?: boolean;
  statusOptions?: Array<{ value: string; label: string }>;
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
  productId?: number | null;
  productCode?: string;
  productDescription?: string;
  itemName: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  totalPrice: number;
  taxInvoiceIssued: boolean;
  notes: string;
};

export type ScheduleDeliveryItemPayload = {
  id?: number;
  productId?: number | null;
  itemName: string;
  quantity: string | number;
  unit: string;
  unitPrice?: string | number | null;
  taxInvoiceIssued: boolean;
  notes?: string;
};

export type ProductOption = {
  id: number;
  productCode: string;
  name: string;
  description: string;
  unit: string;
  specification: string;
  standardPrice: number;
  currentPrice: number;
  isPromo: boolean;
};

type ProductApiItem = {
  id: number;
  product_code?: string;
  productCode?: string;
  name?: string;
  description?: string | null;
  unit?: string | null;
  specification?: string | null;
  standard_price?: number | string;
  standardPrice?: number | string;
  current_price?: number | string;
  currentPrice?: number | string;
  is_promo?: boolean;
  isPromo?: boolean;
};

type ProductsApiResponse = {
  products?: ProductApiItem[];
  success?: boolean;
  error?: string;
  message?: string;
};

export type SchedulePrepaymentUsage = {
  id: number;
  prepaymentId: number;
  paymentDate: string | null;
  payerName: string;
  customerName: string;
  productName: string;
  quantity: number;
  amount: number;
  remainingBalance: number;
  usedAt: string | null;
  memo: string;
};

export type PrepaymentOption = {
  id: number;
  paymentDate: string | null;
  payerName: string;
  customerName: string;
  amount: number;
  balance: number;
  availableBalance: number;
  selectedAmount: number;
  status: string;
  statusLabel: string;
};

type PrepaymentApiItem = {
  id: number;
  payment_date?: string | null;
  paymentDate?: string | null;
  payer_name?: string;
  payerName?: string;
  customer_name?: string;
  customerName?: string;
  amount?: number | string;
  balance?: number | string;
  available_balance?: number | string;
  availableBalance?: number | string;
  selected_amount?: number | string;
  selectedAmount?: number | string;
  status?: string;
  status_label?: string;
  statusLabel?: string;
};

type PrepaymentsApiResponse = {
  prepayments?: PrepaymentApiItem[];
  success?: boolean;
  error?: string;
  message?: string;
};

export type PrepaymentListItem = {
  id: number;
  customerId: number | null;
  customerName: string;
  companyId: number | null;
  companyName: string;
  departmentId: number | null;
  departmentName: string;
  payerName: string;
  paymentDate: string | null;
  paymentMethod: string;
  paymentMethodLabel: string;
  amount: number;
  balance: number;
  usedAmount: number;
  usageCount: number;
  status: string;
  statusLabel: string;
  ownerId: number;
  ownerName: string;
  memo: string;
  createdAt: string | null;
  cancelledAt: string | null;
  cancelReason: string;
  canManage: boolean;
  href: string;
  editHref: string;
  deleteHref: string;
  transferHref: string;
  customerHref: string;
  djangoCustomerHref: string;
  customerPrepaymentHref: string;
  djangoCustomerPrepaymentHref: string;
};

export type PrepaymentUsageItem = {
  id: number;
  usedAt: string | null;
  productName: string;
  quantity: number;
  amount: number;
  remainingBalance: number;
  memo: string;
  scheduleId: number | null;
  scheduleDate: string | null;
  scheduleHref: string;
  djangoScheduleHref: string;
  deliveryItems: Array<{
    id: number;
    itemName: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    totalPrice: number;
  }>;
};

export type PrepaymentCustomerOption = {
  id: number;
  customerName: string;
  companyName: string;
  departmentName: string;
  ownerName: string;
  label: string;
};

export type PrepaymentFormOptions = {
  customers: PrepaymentCustomerOption[];
  paymentMethods: Array<{ value: string; label: string }>;
  statuses: Array<{ value: string; label: string }>;
};

export type PrepaymentsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    dataFilter: string;
    filterUserId: number | null;
    isViewingOthers: boolean;
    canViewTeam: boolean;
  };
  filters: {
    search: string;
    status: string;
    dataFilter: string;
    filterUser: string;
    limit: number;
  };
  options: {
    statuses: Array<{ value: string; label: string }>;
    owners: Array<{ id: number; name: string }>;
    dataFilters: Array<{ value: string; label: string }>;
  };
  metrics: {
    totalAmount: number;
    totalBalance: number;
    totalUsed: number;
    totalCount: number;
    filteredPrepayments: number;
    activeCount: number;
    depletedCount: number;
    cancelledCount: number;
    returnedCount: number;
    truncated: boolean;
  };
  links: {
    djangoList: string;
    create: string;
    excel: string;
    customers: string;
  };
  prepayments: PrepaymentListItem[];
};

export type PrepaymentDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    canManage: boolean;
    isOwner: boolean;
  };
  prepayment: (PrepaymentListItem & {
    usagePercent: number;
    balancePercent: number;
  }) | null;
  metrics: {
    amount: number;
    balance: number;
    usedAmount: number;
    usageCount: number;
    usagePercent: number;
    balancePercent: number;
  };
  links: {
    prepayments: string;
    reactDetail: string;
    reactEdit: string;
    djangoList: string;
    djangoDetail: string;
    djangoEdit: string;
    djangoDelete: string;
    djangoTransfer: string;
  };
  actions: {
    canCancel: boolean;
    cancelUrl: string;
    canDelete: boolean;
    deleteUrl: string;
    deleteMessage: string;
    canTransfer: boolean;
    transferUrl: string;
    transferUsers: Array<{ id: number; name: string }>;
  };
  edit: PrepaymentFormOptions & {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
  };
  usages: PrepaymentUsageItem[];
};

export type PrepaymentCreateData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  create: PrepaymentFormOptions & {
    canCreate: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
  };
  links: {
    prepayments: string;
    djangoList: string;
  };
};

export type PrepaymentCustomerData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    mode: string;
    name: string;
    label: string;
    targetUserId: number | null;
    targetUserName: string;
    canSelectUser: boolean;
  };
  customer: {
    id: number | null;
    customerName: string;
    companyId: number | null;
    companyName: string;
    departmentId: number | null;
    departmentName: string;
    ownerName: string;
    href: string;
    djangoHref: string;
  };
  departmentCustomers: Array<{
    id: number;
    customerName: string;
    ownerName: string;
    href: string;
    djangoHref: string;
  }>;
  metrics: {
    totalAmount: number;
    totalBalance: number;
    totalUsed: number;
    totalCount: number;
    activeCount: number;
    depletedCount: number;
    cancelledCount: number;
  };
  options: {
    owners: Array<{ id: number; name: string }>;
  };
  links: {
    prepayments: string;
    reactCustomer: string;
    djangoList: string;
    djangoCustomer: string;
    djangoExcel: string;
    customerDetail: string;
    djangoCustomerDetail: string;
  };
  prepayments: PrepaymentListItem[];
};

export type PrepaymentFormPayload = {
  amount: string;
  balance?: string;
  customerId: number;
  memo?: string;
  payerName?: string;
  paymentDate: string;
  paymentMethod: string;
  status?: string;
};

export type PrepaymentMutationResponse = {
  success: boolean;
  error?: string;
  message?: string;
  prepaymentId?: number;
  href?: string;
  djangoHref?: string;
  prepayment?: PrepaymentListItem;
};

export type SchedulePrepaymentSelectionPayload = {
  id: number;
  amount: string | number;
};

export type ScheduleDetailItem = ScheduleItem & {
  canEdit: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  vatMode: string;
  usePrepayment: boolean;
  prepaymentId: number | null;
  prepaymentAmount: number;
  prepaymentUsages: SchedulePrepaymentUsage[];
  fileCount: number;
  emailThreadCount: number;
  files: ScheduleFileItem[];
};

export type ScheduleDocumentFormatAction = {
  format: 'pdf' | 'xlsx';
  label: string;
  href: string;
};

export type ScheduleDocumentAction = {
  type: string;
  label: string;
  description: string;
  templateCount: number;
  previewHref: string;
  formats: ScheduleDocumentFormatAction[];
};

export type ScheduleDocumentsData = {
  canGenerate: boolean;
  templateManagerHref: string;
  djangoTemplateManagerHref?: string;
  items: ScheduleDocumentAction[];
};

export type ScheduleDocumentPreviewData = {
  success?: boolean;
  error?: string;
  templateUrl?: string;
  templateFilename?: string;
  variables: Record<string, string | number | null | undefined>;
  fileInfo: {
    companyName?: string;
    customerCompany?: string;
    docName?: string;
    todayStr?: string;
    baseDate?: string;
    transactionNumber?: string;
  };
  items: Array<{
    index: number;
    name: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    subtotal: number;
  }>;
  itemCount: number;
};

export type ScheduleDocumentDownloadResult = {
  blob: Blob;
  filename: string;
};

export type DocumentTemplateTypeOption = {
  value: string;
  label: string;
};

export type DocumentTemplateCompanyOption = {
  id: number;
  name: string;
};

export type DocumentTemplateItem = {
  id: number;
  documentType: string;
  documentTypeLabel: string;
  name: string;
  description: string;
  fileType: string;
  fileName: string;
  isDefault: boolean;
  isActive: boolean;
  company: DocumentTemplateCompanyOption;
  createdBy: string;
  createdAt: string | null;
  updatedAt: string | null;
  downloadHref: string;
  toggleDefaultUrl: string;
  updateUrl: string;
  deleteUrl: string;
  djangoEditHref: string;
  canManage: boolean;
  canToggleDefault: boolean;
};

export type DocumentGenerationItem = {
  id: number;
  documentType: string;
  documentTypeLabel: string;
  transactionNumber: string;
  outputFormat: 'pdf' | 'xlsx' | string;
  outputFormatLabel: string;
  createdAt: string | null;
  createdBy: string;
  company: DocumentTemplateCompanyOption;
  schedule: {
    id: number | null;
    visitDate: string | null;
    activityType: string;
    activityTypeLabel: string;
    status: string;
    statusLabel: string;
    href: string;
    djangoHref: string;
  };
  customerName: string;
  customerCompany: string;
  departmentName: string;
};

export type DocumentTemplatesData = {
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
    isSuperuser: boolean;
  };
  filters: {
    type: string;
  };
  documentTypes: DocumentTemplateTypeOption[];
  summary: {
    totalTemplates: number;
    defaultTemplates: number;
    generatedToday: number;
    recentGenerationCount: number;
    byType: Array<{
      type: string;
      label: string;
      count: number;
      defaultCount: number;
    }>;
  };
  create: {
    canCreate: boolean;
    message: string;
    submitUrl: string;
    djangoCreateHref: string;
    companies: DocumentTemplateCompanyOption[];
  };
  links: {
    self: string;
    djangoList: string;
    scheduleList: string;
    scheduleCalendar: string;
  };
  templates: DocumentTemplateItem[];
  recentGenerations: DocumentGenerationItem[];
};

export type DocumentTemplateMutationPayload = {
  documentType: string;
  name: string;
  description?: string;
  isDefault: boolean;
  companyId?: string;
  file?: File | null;
};

export type DocumentTemplateMutationResponse = {
  success: boolean;
  source?: 'django';
  error?: string;
  message?: string;
  isDefault?: boolean;
  template?: DocumentTemplateItem;
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

export type ScheduleStatusUpdateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  new_status?: string;
  newStatus?: string;
  status_display?: string;
  statusDisplay?: string;
};

export type ScheduleEditPayload = {
  activityType: string;
  expectedCloseDate?: string;
  expectedRevenue?: string;
  followupId: number;
  location?: string;
  notes?: string;
  probability?: string;
  prepayments?: SchedulePrepaymentSelectionPayload[];
  purchaseConfirmed?: boolean;
  status: string;
  usePrepayment?: boolean;
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
    djangoSchedules?: string;
    calendar: string;
    djangoCalendar?: string;
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

export type ScheduleCalendarData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    dataFilter: string;
    filterUserId: number | null;
    canViewCompany: boolean;
    userCount: number;
  };
  filters: {
    start: string;
    end: string;
    dataFilter: string;
    filterUser: string;
  };
  options: {
    dataFilters: Array<{ value: string; label: string }>;
    users: Array<{
      id: number;
      name: string;
      username: string;
      role: string;
      isCurrent: boolean;
    }>;
  };
  metrics: {
    totalSchedules: number;
    customerSchedules: number;
    personalSchedules: number;
    scheduledSchedules: number;
    completedSchedules: number;
    cancelledSchedules: number;
    overdueSchedules: number;
  };
  links: {
    schedules: string;
    djangoSchedules: string;
    calendar: string;
    djangoCalendar: string;
    createSchedule: string;
    createPersonalSchedule: string;
    weeklyReports: string;
  };
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
    updateDeliveryItems: string;
    prepayments: string;
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
  documents: ScheduleDocumentsData;
};

export type ScheduleEditResponse = ScheduleDetailData & {
  success: boolean;
  error?: string;
  message?: string;
};

export type ScheduleDeliveryItemsUpdateResponse = ScheduleDetailData & {
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

export type AIWorkspaceFeaturedDepartment = CustomerAiDepartment & {
  customerCount: number;
  customerPreview: string[];
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
  featuredDepartment: AIWorkspaceFeaturedDepartment | null;
  selectedDepartmentId: number | null;
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

export type AIWorkspaceLoadParams = {
  departmentId?: number | null;
};

export type WeeklyReportUser = {
  id: number;
  name: string;
  username: string;
  role: string;
  roleLabel: string;
  company: string;
};

export type WeeklyReportItem = {
  id: number;
  title: string;
  weekStart: string;
  weekEnd: string;
  user: WeeklyReportUser;
  activityNotesHtml: string;
  quoteDeliveryNotesHtml: string;
  otherNotesHtml: string;
  activityNotes?: string;
  quoteDeliveryNotes?: string;
  otherNotes?: string;
  managerComment: string;
  reviewed: boolean;
  reviewedBy: string;
  reviewedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  canEdit: boolean;
  canDelete: boolean;
  canComment: boolean;
  href: string;
  editHref: string;
  deleteHref: string;
  updateHref: string;
  managerCommentHref: string;
  djangoHref: string;
  djangoEditHref: string;
};

export type WeeklyReportFormPayload = {
  weekStart: string;
  weekEnd: string;
  title: string;
  activityNotes: string;
  quoteDeliveryNotes: string;
  otherNotes: string;
};

export type WeeklyReportsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    canViewAll: boolean;
    userCount: number;
  };
  filters: {
    year: string;
    month: string;
    userId: string;
  };
  options: {
    years: number[];
    months: number[];
    users: WeeklyReportUser[];
  };
  metrics: {
    filteredReports: number;
    reviewedReports: number;
    pendingReports: number;
    thisMonthReports: number;
  };
  links: {
    list: string;
    create: string;
    createApi: string;
    schedulesApi: string;
    aiDraftApi: string;
    djangoList: string;
    djangoCreate: string;
  };
  reports: WeeklyReportItem[];
};

export type WeeklyReportCreateData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  canUseAi: boolean;
  form: WeeklyReportFormPayload;
  existingReport: WeeklyReportItem | null;
  links: WeeklyReportsData['links'];
};

export type WeeklyReportDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  canUseAi: boolean;
  report: WeeklyReportItem;
  form: WeeklyReportFormPayload | null;
  links: WeeklyReportsData['links'];
};

export type WeeklyReportScheduleItem = {
  id: number;
  date: string;
  weekday?: string;
  customer: string;
  company: string;
  department: string;
  manager?: string;
  activity_type?: string;
  activity_type_display?: string;
  activityType?: string;
  notes: string;
  status?: string;
  amount?: string;
  amount_label?: string;
  histories?: Array<{
    id: number;
    type: string;
    snippet: string;
    next_action: string;
    next_action_date: string;
    amount?: string;
  }>;
  quotes?: Array<{
    number: string;
    stage: string;
    amount: string;
    probability: number;
  }>;
};

export type WeeklyReportSchedulesData = {
  schedules: WeeklyReportScheduleItem[];
  categorized: {
    activity: WeeklyReportScheduleItem[];
    quote_delivery: WeeklyReportScheduleItem[];
  };
  error?: string;
};

export type WeeklyReportAiDraft = {
  title?: string;
  activityNotes?: string;
  quoteDeliveryNotes?: string;
  otherNotes?: string;
  activity_notes?: string;
  quote_delivery_notes?: string;
  other_notes?: string;
  activity?: string;
  quoteDelivery?: string;
  other?: string;
  summary?: string;
};

export type WeeklyReportSaveResponse = {
  success?: boolean;
  source?: 'django';
  message?: string;
  error?: string;
  redirect?: string;
  report?: WeeklyReportItem;
  existingHref?: string;
};

export type WeeklyReportManagerCommentResponse = {
  ok?: boolean;
  success?: boolean;
  error?: string;
  reviewer?: string;
  reviewed_at?: string;
  comment?: string;
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
    calendar: '/schedules/calendar/',
    pipeline: '/reporting/funnel/pipeline/',
    weeklyReports: '/weekly-reports/',
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

const emptyMailboxCreateOptions: MailboxCreateOptions = {
  canSend: false,
  message: '',
  submitUrl: '/reporting/api/mailbox/send/',
  djangoUrl: '/reporting/gmail/send/mailbox/',
  customers: [],
  businessCards: [],
};

const emptyMailboxData: MailboxData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  mailboxType: 'inbox',
  filters: {
    q: '',
    page: 1,
  },
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
  counts: {
    inbox: 0,
    sent: 0,
    starred: 0,
    archived: 0,
    trash: 0,
    unread: 0,
  },
  pagination: {
    page: 1,
    totalPages: 1,
    totalCount: 0,
    hasNext: false,
    hasPrevious: false,
    nextPage: null,
    previousPage: null,
  },
  links: {
    inbox: '/mailbox/?box=inbox',
    sent: '/mailbox/?box=sent',
    starred: '/mailbox/?box=starred',
    archived: '/mailbox/?box=archived',
    trash: '/mailbox/?box=trash',
    sync: '/reporting/api/mailbox/sync/',
    djangoInbox: '/reporting/mailbox/inbox/',
    djangoSent: '/reporting/mailbox/sent/',
  },
  create: emptyMailboxCreateOptions,
  emails: [],
};

const emptyMailboxThreadData: MailboxThreadData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  thread: {
    id: '',
    subject: '',
    followup: null,
    messageCount: 0,
    lastReceivedEmailId: null,
  },
  connection: emptyMailboxData.connection,
  links: {
    mailbox: '/mailbox/',
    djangoThread: '',
    reply: '',
  },
  create: emptyMailboxCreateOptions,
  emails: [],
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
  prepaymentSummary: {
    metrics: {
      totalAmount: 0,
      totalBalance: 0,
      totalUsed: 0,
      totalCount: 0,
      activeCount: 0,
      depletedCount: 0,
      cancelledCount: 0,
    },
    links: {
      prepayments: '/prepayments/',
      createPrepayment: '/prepayments/new/',
      customerPrepayments: '',
      djangoCustomerPrepayments: '',
    },
    recentPrepayments: [],
  },
  aiDepartment: {
    departmentId: null,
    departmentName: '',
    companyName: '',
    canUseAi: false,
    canAnalyze: false,
    hasAnalysis: false,
    message: '',
    summary: '',
    updatedAt: null,
    meetingCount: 0,
    quoteCount: 0,
    deliveryCount: 0,
    painpointCount: 0,
    unverifiedPainpointCount: 0,
    href: '',
    hubHref: '',
    runHref: '',
    periodStart: null,
    periodEnd: null,
    tokenUsage: 0,
    meetingInsights: [],
    quoteDelivery: {
      totalQuotes: 0,
      convertedQuotes: 0,
      conversionRate: 0,
      totalDeliveries: 0,
      avgDeliveryIntervalDays: 0,
      productStats: [],
      recentDeliveries: [],
    },
    quoteInsights: {
      conversionAnalysis: '',
      deliveryCycle: '',
      productTrends: '',
      stalledQuotes: [],
    },
    nextActions: [],
    verificationInsights: [],
    missingInfo: {
      items: [],
      questions: [],
    },
    painpoints: [],
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
    weeklyReports: '/weekly-reports/',
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
    schedules: '/schedules/',
    djangoSchedules: '/reporting/schedules/',
    calendar: '/schedules/calendar/',
    djangoCalendar: '/reporting/schedules/calendar/',
    weeklyReports: '/weekly-reports/',
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

const emptyScheduleCalendarData: ScheduleCalendarData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    dataFilter: 'me',
    filterUserId: null,
    canViewCompany: false,
    userCount: 0,
  },
  filters: {
    start: '',
    end: '',
    dataFilter: 'me',
    filterUser: '',
  },
  options: {
    dataFilters: [
      { value: 'me', label: '내 일정' },
      { value: 'all', label: '회사 전체' },
      { value: 'user', label: '직원 선택' },
    ],
    users: [],
  },
  metrics: {
    totalSchedules: 0,
    customerSchedules: 0,
    personalSchedules: 0,
    scheduledSchedules: 0,
    completedSchedules: 0,
    cancelledSchedules: 0,
    overdueSchedules: 0,
  },
  links: {
    schedules: '/schedules/',
    djangoSchedules: '/reporting/schedules/',
    calendar: '/schedules/calendar/',
    djangoCalendar: '/reporting/schedules/calendar/',
    createSchedule: '/reporting/schedules/create/',
    createPersonalSchedule: '/reporting/personal-schedules/create/',
    weeklyReports: '/weekly-reports/',
  },
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
    calendar: '/schedules/calendar/',
    djangoDetail: '',
    djangoEdit: '',
    customer: '',
    djangoCustomer: '',
    createNote: '',
    uploadFiles: '',
    updateDeliveryItems: '',
    prepayments: '',
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
  documents: {
    canGenerate: false,
    templateManagerHref: '/documents/',
    djangoTemplateManagerHref: '/reporting/documents/',
    items: [],
  },
};

const emptyDocumentTemplatesData: DocumentTemplatesData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  currentUser: {
    id: null,
    name: '',
    role: '',
    roleLabel: '',
    company: '',
    isSuperuser: false,
  },
  filters: {
    type: '',
  },
  documentTypes: [
    { value: 'quotation', label: '견적서' },
    { value: 'transaction_statement', label: '거래명세서' },
    { value: 'delivery_note', label: '납품서' },
  ],
  summary: {
    totalTemplates: 0,
    defaultTemplates: 0,
    generatedToday: 0,
    recentGenerationCount: 0,
    byType: [],
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/documents/create/',
    djangoCreateHref: '/reporting/documents/create/',
    companies: [],
  },
  links: {
    self: '/documents/',
    djangoList: '/reporting/documents/',
    scheduleList: '/schedules/',
    scheduleCalendar: '/schedules/calendar/',
  },
  templates: [],
  recentGenerations: [],
};

const emptyPrepaymentsData: PrepaymentsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    dataFilter: 'me',
    filterUserId: null,
    isViewingOthers: false,
    canViewTeam: false,
  },
  filters: {
    search: '',
    status: '',
    dataFilter: 'me',
    filterUser: '',
    limit: 80,
  },
  options: {
    statuses: [],
    owners: [],
    dataFilters: [
      { value: 'me', label: '나' },
      { value: 'all', label: '전체' },
      { value: 'user', label: '직원 선택' },
    ],
  },
  metrics: {
    totalAmount: 0,
    totalBalance: 0,
    totalUsed: 0,
    totalCount: 0,
    filteredPrepayments: 0,
    activeCount: 0,
    depletedCount: 0,
    cancelledCount: 0,
    returnedCount: 0,
    truncated: false,
  },
  links: {
    djangoList: '/reporting/prepayment/',
    create: '/reporting/prepayment/create/',
    excel: '/reporting/prepayment/excel/',
    customers: '/customers/',
  },
  prepayments: [],
};

const emptyPrepaymentFormOptions: PrepaymentFormOptions = {
  customers: [],
  paymentMethods: [
    { value: 'transfer', label: '계좌이체' },
    { value: 'card', label: '카드' },
    { value: 'cash', label: '현금' },
  ],
  statuses: [
    { value: 'active', label: '활성' },
    { value: 'depleted', label: '소진' },
    { value: 'cancelled', label: '취소' },
  ],
};

const emptyPrepaymentDetailData: PrepaymentDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    canManage: false,
    isOwner: false,
  },
  prepayment: null,
  metrics: {
    amount: 0,
    balance: 0,
    usedAmount: 0,
    usageCount: 0,
    usagePercent: 0,
    balancePercent: 0,
  },
  links: {
    prepayments: '/prepayments/',
    reactDetail: '',
    reactEdit: '',
    djangoList: '/reporting/prepayment/',
    djangoDetail: '',
    djangoEdit: '',
    djangoDelete: '',
    djangoTransfer: '',
  },
  actions: {
    canCancel: false,
    cancelUrl: '',
    canDelete: false,
    deleteUrl: '',
    deleteMessage: '',
    canTransfer: false,
    transferUrl: '',
    transferUsers: [],
  },
  edit: {
    canEdit: false,
    message: '',
    submitUrl: '',
    djangoUrl: '',
    ...emptyPrepaymentFormOptions,
  },
  usages: [],
};

const emptyPrepaymentCreateData: PrepaymentCreateData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/prepayments/create/',
    djangoUrl: '/reporting/prepayment/create/',
    ...emptyPrepaymentFormOptions,
  },
  links: {
    prepayments: '/prepayments/',
    djangoList: '/reporting/prepayment/',
  },
};

const emptyPrepaymentCustomerData: PrepaymentCustomerData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    mode: '',
    name: '',
    label: '',
    targetUserId: null,
    targetUserName: '',
    canSelectUser: false,
  },
  customer: {
    id: null,
    customerName: '',
    companyId: null,
    companyName: '',
    departmentId: null,
    departmentName: '',
    ownerName: '',
    href: '',
    djangoHref: '',
  },
  departmentCustomers: [],
  metrics: {
    totalAmount: 0,
    totalBalance: 0,
    totalUsed: 0,
    totalCount: 0,
    activeCount: 0,
    depletedCount: 0,
    cancelledCount: 0,
  },
  options: {
    owners: [],
  },
  links: {
    prepayments: '/prepayments/',
    reactCustomer: '',
    djangoList: '/reporting/prepayment/',
    djangoCustomer: '',
    djangoExcel: '',
    customerDetail: '',
    djangoCustomerDetail: '',
  },
  prepayments: [],
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
    weeklyReports: '/weekly-reports/',
    weeklyReportCreate: '/weekly-reports/new/',
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
  featuredDepartment: null,
  selectedDepartmentId: null,
  recentDepartmentAnalyses: [],
  painpoints: [],
  followupTargets: [],
  recentFollowupAnalyses: [],
  promptTargets: [],
  recommendedGoals: [],
};

const emptyWeeklyReportLinks: WeeklyReportsData['links'] = {
  list: '/weekly-reports/',
  create: '/weekly-reports/new/',
  createApi: '/reporting/api/weekly-reports/create/',
  schedulesApi: '/reporting/api/weekly-reports/schedules/',
  aiDraftApi: '/reporting/api/weekly-reports/ai-draft/',
  djangoList: '/reporting/weekly-reports/',
  djangoCreate: '/reporting/weekly-reports/create/',
};

const emptyWeeklyReportForm: WeeklyReportFormPayload = {
  weekStart: '',
  weekEnd: '',
  title: '',
  activityNotes: '',
  quoteDeliveryNotes: '',
  otherNotes: '',
};

const emptyWeeklyReportItem: WeeklyReportItem = {
  id: 0,
  title: '',
  weekStart: '',
  weekEnd: '',
  user: {
    id: 0,
    name: '',
    username: '',
    role: '',
    roleLabel: '',
    company: '',
  },
  activityNotesHtml: '',
  quoteDeliveryNotesHtml: '',
  otherNotesHtml: '',
  managerComment: '',
  reviewed: false,
  reviewedBy: '',
  reviewedAt: null,
  createdAt: null,
  updatedAt: null,
  canEdit: false,
  canDelete: false,
  canComment: false,
  href: '',
  editHref: '',
  deleteHref: '',
  updateHref: '',
  managerCommentHref: '',
  djangoHref: '',
  djangoEditHref: '',
};

const emptyWeeklyReportsData: WeeklyReportsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    canViewAll: false,
    userCount: 0,
  },
  filters: {
    year: '',
    month: '',
    userId: '',
  },
  options: {
    years: [],
    months: [],
    users: [],
  },
  metrics: {
    filteredReports: 0,
    reviewedReports: 0,
    pendingReports: 0,
    thisMonthReports: 0,
  },
  links: emptyWeeklyReportLinks,
  reports: [],
};

const emptyWeeklyReportCreateData: WeeklyReportCreateData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  canUseAi: false,
  form: emptyWeeklyReportForm,
  existingReport: null,
  links: emptyWeeklyReportLinks,
};

const emptyWeeklyReportDetailData: WeeklyReportDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  canUseAi: false,
  report: emptyWeeklyReportItem,
  form: null,
  links: emptyWeeklyReportLinks,
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

export async function loadMailboxData(params: {
  box?: MailboxType;
  q?: string;
  page?: number;
} = {}): Promise<MailboxData> {
  const query = new URLSearchParams();
  if (params.box) query.set('box', params.box);
  if (params.q) query.set('q', params.q);
  if (params.page && params.page > 1) query.set('page', String(params.page));

  try {
    const response = await fetch(`/reporting/api/mailbox/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Mailbox API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<MailboxData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Mailbox API unavailable: ${response.status}`);
    }
    return {
      ...emptyMailboxData,
      ...payload,
      mailboxType: payload.mailboxType ?? params.box ?? emptyMailboxData.mailboxType,
      filters: {
        ...emptyMailboxData.filters,
        ...(payload.filters ?? {}),
      },
      connection: {
        ...emptyMailboxData.connection,
        ...(payload.connection ?? {}),
      },
      counts: {
        ...emptyMailboxData.counts,
        ...(payload.counts ?? {}),
      },
      pagination: {
        ...emptyMailboxData.pagination,
        ...(payload.pagination ?? {}),
      },
      links: {
        ...emptyMailboxData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptyMailboxCreateOptions,
        ...(payload.create ?? {}),
        customers: payload.create?.customers ?? emptyMailboxCreateOptions.customers,
        businessCards: payload.create?.businessCards ?? emptyMailboxCreateOptions.businessCards,
      },
      emails: payload.emails ?? emptyMailboxData.emails,
    };
  } catch (error) {
    return {
      ...emptyMailboxData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Mailbox API unavailable',
      mailboxType: params.box ?? emptyMailboxData.mailboxType,
      filters: {
        ...emptyMailboxData.filters,
        q: params.q ?? '',
        page: params.page ?? 1,
      },
    };
  }
}

export async function loadMailboxThreadData(threadId: string): Promise<MailboxThreadData> {
  try {
    const response = await fetch(`/reporting/api/mailbox/thread/${encodeURIComponent(threadId)}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Mailbox thread API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<MailboxThreadData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Mailbox thread API unavailable: ${response.status}`);
    }
    return {
      ...emptyMailboxThreadData,
      ...payload,
      thread: {
        ...emptyMailboxThreadData.thread,
        ...(payload.thread ?? {}),
      },
      connection: {
        ...emptyMailboxData.connection,
        ...(payload.connection ?? {}),
      },
      links: {
        ...emptyMailboxThreadData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptyMailboxCreateOptions,
        ...(payload.create ?? {}),
        customers: payload.create?.customers ?? emptyMailboxCreateOptions.customers,
        businessCards: payload.create?.businessCards ?? emptyMailboxCreateOptions.businessCards,
      },
      emails: payload.emails ?? emptyMailboxThreadData.emails,
    };
  } catch (error) {
    return {
      ...emptyMailboxThreadData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Mailbox thread API unavailable',
      thread: {
        ...emptyMailboxThreadData.thread,
        id: threadId,
      },
    };
  }
}

function mailboxPayloadToBody(payload: MailboxSendPayload): FormData {
  const body = new FormData();
  body.set('to_email', payload.toEmail);
  body.set('subject', payload.subject);
  body.set('body_text', payload.bodyText);
  if (payload.ccEmails) body.set('cc_emails', payload.ccEmails);
  if (payload.bccEmails) body.set('bcc_emails', payload.bccEmails);
  if (payload.followupId) body.set('selected_followup_id', String(payload.followupId));
  if (payload.businessCardId) body.set('business_card_id', String(payload.businessCardId));
  payload.attachments?.forEach((file) => body.append('attachments', file));
  return body;
}

async function postMailboxForm(url: string, payload?: MailboxSendPayload): Promise<MailboxActionResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: payload ? mailboxPayloadToBody(payload) : undefined,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Mailbox request failed: ${response.status}`);
  }
  const data = (await response.json()) as MailboxActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Mailbox request failed: ${response.status}`);
  }
  return data;
}

export async function sendMailboxEmail(
  payload: MailboxSendPayload,
  submitUrl = '/reporting/api/mailbox/send/',
): Promise<MailboxActionResponse> {
  return postMailboxForm(submitUrl, payload);
}

export async function replyMailboxEmail(
  submitUrl: string,
  payload: MailboxSendPayload,
): Promise<MailboxActionResponse> {
  return postMailboxForm(submitUrl, payload);
}

export async function runMailboxSync(syncUrl = '/reporting/api/mailbox/sync/'): Promise<MailboxActionResponse> {
  return postMailboxForm(syncUrl);
}

export async function runMailboxAction(actionUrl: string): Promise<MailboxActionResponse> {
  return postMailboxForm(actionUrl);
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
      prepaymentSummary: {
        ...emptyCustomerDetailData.prepaymentSummary,
        ...(payload.prepaymentSummary ?? {}),
        metrics: {
          ...emptyCustomerDetailData.prepaymentSummary.metrics,
          ...(payload.prepaymentSummary?.metrics ?? {}),
        },
        links: {
          ...emptyCustomerDetailData.prepaymentSummary.links,
          ...(payload.prepaymentSummary?.links ?? {}),
        },
        recentPrepayments: payload.prepaymentSummary?.recentPrepayments ?? emptyCustomerDetailData.prepaymentSummary.recentPrepayments,
      },
      aiDepartment: {
        ...emptyCustomerDetailData.aiDepartment,
        ...(payload.aiDepartment ?? {}),
        quoteDelivery: {
          ...emptyCustomerDetailData.aiDepartment.quoteDelivery,
          ...(payload.aiDepartment?.quoteDelivery ?? {}),
          productStats: payload.aiDepartment?.quoteDelivery?.productStats ?? emptyCustomerDetailData.aiDepartment.quoteDelivery.productStats,
          recentDeliveries: payload.aiDepartment?.quoteDelivery?.recentDeliveries ?? emptyCustomerDetailData.aiDepartment.quoteDelivery.recentDeliveries,
        },
        quoteInsights: {
          ...emptyCustomerDetailData.aiDepartment.quoteInsights,
          ...(payload.aiDepartment?.quoteInsights ?? {}),
          stalledQuotes: payload.aiDepartment?.quoteInsights?.stalledQuotes ?? emptyCustomerDetailData.aiDepartment.quoteInsights.stalledQuotes,
        },
        missingInfo: {
          ...emptyCustomerDetailData.aiDepartment.missingInfo,
          ...(payload.aiDepartment?.missingInfo ?? {}),
        },
        meetingInsights: payload.aiDepartment?.meetingInsights ?? emptyCustomerDetailData.aiDepartment.meetingInsights,
        nextActions: payload.aiDepartment?.nextActions ?? emptyCustomerDetailData.aiDepartment.nextActions,
        verificationInsights: payload.aiDepartment?.verificationInsights ?? emptyCustomerDetailData.aiDepartment.verificationInsights,
        painpoints: payload.aiDepartment?.painpoints ?? emptyCustomerDetailData.aiDepartment.painpoints,
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

export async function runAiDepartmentAnalysis(runHref: string): Promise<AiDepartmentRunResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(runHref, {
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
    throw new Error(`AI department analysis API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AiDepartmentRunResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI department analysis failed: ${response.status}`);
  }
  return data;
}

export async function verifyAiPainpoint(
  verifyHref: string,
  note = '',
): Promise<AiPainpointVerifyResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  if (note.trim()) {
    body.set('note', note.trim());
  }

  const response = await fetch(verifyHref, {
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
    throw new Error(`AI PainPoint verification API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AiPainpointVerifyResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI PainPoint verification failed: ${response.status}`);
  }
  return data;
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

export async function loadScheduleCalendarData(params: {
  start?: string;
  end?: string;
  dataFilter?: string;
  filterUser?: string;
} = {}): Promise<ScheduleCalendarData> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  try {
    const response = await fetch(`/reporting/api/schedules/calendar/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Schedule calendar API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<ScheduleCalendarData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Schedule calendar API unavailable: ${response.status}`);
    }
    return {
      ...emptyScheduleCalendarData,
      ...payload,
      scope: {
        ...emptyScheduleCalendarData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyScheduleCalendarData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyScheduleCalendarData.options,
        ...(payload.options ?? {}),
      },
      metrics: {
        ...emptyScheduleCalendarData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyScheduleCalendarData.links,
        ...(payload.links ?? {}),
      },
      schedules: payload.schedules ?? emptyScheduleCalendarData.schedules,
    };
  } catch (error) {
    return {
      ...emptyScheduleCalendarData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Schedule calendar API unavailable',
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

export async function updateScheduleStatus(submitUrl: string, status: string): Promise<ScheduleStatusUpdateResponse> {
  const csrfToken = getCookie('csrftoken');
  const formData = new FormData();
  formData.set('status', status);
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: formData,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule status API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleStatusUpdateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule status update failed: ${response.status}`);
  }
  return data;
}

export async function loadProducts(search = ''): Promise<ProductOption[]> {
  const params = new URLSearchParams();
  const query = search.trim();
  if (query) {
    params.set('search', query);
  }

  const queryString = params.toString();
  const response = await fetch(`/reporting/api/products/${queryString ? `?${queryString}` : ''}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Products API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ProductsApiResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Products API unavailable: ${response.status}`);
  }

  return (data.products ?? []).map((product) => {
    const productCode = product.product_code ?? product.productCode ?? product.name ?? '';
    const standardPrice = Number(product.standard_price ?? product.standardPrice ?? 0);
    const currentPrice = Number(product.current_price ?? product.currentPrice ?? standardPrice);

    return {
      id: product.id,
      productCode,
      name: product.name ?? productCode,
      description: product.description ?? '',
      unit: product.unit || 'EA',
      specification: product.specification ?? '',
      standardPrice: Number.isFinite(standardPrice) ? standardPrice : 0,
      currentPrice: Number.isFinite(currentPrice) ? currentPrice : 0,
      isPromo: Boolean(product.is_promo ?? product.isPromo),
    };
  });
}

export async function loadPrepayments(customerId: number, scheduleId?: number): Promise<PrepaymentOption[]> {
  const params = new URLSearchParams();
  params.set('customer_id', String(customerId));
  if (scheduleId) {
    params.set('schedule_id', String(scheduleId));
  }

  const response = await fetch(`/reporting/api/prepayments/?${params.toString()}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Prepayments API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentsApiResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayments API unavailable: ${response.status}`);
  }

  return (data.prepayments ?? []).map((prepayment) => {
    const amount = Number(prepayment.amount ?? 0);
    const balance = Number(prepayment.balance ?? 0);
    const selectedAmount = Number(prepayment.selected_amount ?? prepayment.selectedAmount ?? 0);
    const availableBalance = Number(prepayment.available_balance ?? prepayment.availableBalance ?? balance + selectedAmount);
    return {
      id: prepayment.id,
      paymentDate: prepayment.payment_date ?? prepayment.paymentDate ?? null,
      payerName: prepayment.payer_name ?? prepayment.payerName ?? '미지정',
      customerName: prepayment.customer_name ?? prepayment.customerName ?? '',
      amount: Number.isFinite(amount) ? amount : 0,
      balance: Number.isFinite(balance) ? balance : 0,
      availableBalance: Number.isFinite(availableBalance) ? availableBalance : 0,
      selectedAmount: Number.isFinite(selectedAmount) ? selectedAmount : 0,
      status: prepayment.status ?? '',
      statusLabel: prepayment.status_label ?? prepayment.statusLabel ?? '',
    };
  });
}

export async function loadPrepaymentsData(params: {
  search?: string;
  status?: string;
  dataFilter?: string;
  filterUser?: string;
} = {}): Promise<PrepaymentsData> {
  const query = new URLSearchParams();
  if (params.search) {
    query.set('search', params.search);
  }
  if (params.status) {
    query.set('status', params.status);
  }
  if (params.dataFilter) {
    query.set('data_filter', params.dataFilter);
  }
  if (params.filterUser) {
    query.set('filter_user', params.filterUser);
  }

  try {
    const response = await fetch(`/reporting/api/prepayments/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Prepayments API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PrepaymentsData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Prepayments API unavailable: ${response.status}`);
    }
    return {
      ...emptyPrepaymentsData,
      ...payload,
      scope: {
        ...emptyPrepaymentsData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyPrepaymentsData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyPrepaymentsData.options,
        ...(payload.options ?? {}),
        statuses: payload.options?.statuses ?? emptyPrepaymentsData.options.statuses,
        owners: payload.options?.owners ?? emptyPrepaymentsData.options.owners,
        dataFilters: payload.options?.dataFilters ?? emptyPrepaymentsData.options.dataFilters,
      },
      metrics: {
        ...emptyPrepaymentsData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyPrepaymentsData.links,
        ...(payload.links ?? {}),
      },
      prepayments: payload.prepayments ?? emptyPrepaymentsData.prepayments,
    };
  } catch (error) {
    return {
      ...emptyPrepaymentsData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Prepayments API unavailable',
    };
  }
}

export async function loadPrepaymentCreateData(): Promise<PrepaymentCreateData> {
  try {
    const response = await fetch('/reporting/api/prepayments/create/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Prepayment create API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PrepaymentCreateData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Prepayment create API unavailable: ${response.status}`);
    }
    return {
      ...emptyPrepaymentCreateData,
      ...payload,
      create: {
        ...emptyPrepaymentCreateData.create,
        ...(payload.create ?? {}),
        customers: payload.create?.customers ?? emptyPrepaymentCreateData.create.customers,
        paymentMethods: payload.create?.paymentMethods ?? emptyPrepaymentCreateData.create.paymentMethods,
        statuses: payload.create?.statuses ?? emptyPrepaymentCreateData.create.statuses,
      },
      links: {
        ...emptyPrepaymentCreateData.links,
        ...(payload.links ?? {}),
      },
    };
  } catch (error) {
    return {
      ...emptyPrepaymentCreateData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Prepayment create API unavailable',
    };
  }
}

export async function loadPrepaymentCustomerData(
  customerId: number,
  targetUserId?: string,
): Promise<PrepaymentCustomerData> {
  const query = new URLSearchParams();
  if (targetUserId) {
    query.set('user', targetUserId);
  }

  try {
    const response = await fetch(`/reporting/api/prepayments/customer/${customerId}/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Prepayment customer API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PrepaymentCustomerData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Prepayment customer API unavailable: ${response.status}`);
    }
    return {
      ...emptyPrepaymentCustomerData,
      ...payload,
      scope: {
        ...emptyPrepaymentCustomerData.scope,
        ...(payload.scope ?? {}),
      },
      customer: {
        ...emptyPrepaymentCustomerData.customer,
        ...(payload.customer ?? {}),
      },
      metrics: {
        ...emptyPrepaymentCustomerData.metrics,
        ...(payload.metrics ?? {}),
      },
      options: {
        ...emptyPrepaymentCustomerData.options,
        ...(payload.options ?? {}),
        owners: payload.options?.owners ?? emptyPrepaymentCustomerData.options.owners,
      },
      links: {
        ...emptyPrepaymentCustomerData.links,
        ...(payload.links ?? {}),
      },
      departmentCustomers: payload.departmentCustomers ?? emptyPrepaymentCustomerData.departmentCustomers,
      prepayments: payload.prepayments ?? emptyPrepaymentCustomerData.prepayments,
    };
  } catch (error) {
    return {
      ...emptyPrepaymentCustomerData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Prepayment customer API unavailable',
    };
  }
}

export async function loadPrepaymentDetailData(prepaymentId: number): Promise<PrepaymentDetailData> {
  try {
    const response = await fetch(`/reporting/api/prepayments/${prepaymentId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Prepayment detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PrepaymentDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Prepayment detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyPrepaymentDetailData,
      ...payload,
      scope: {
        ...emptyPrepaymentDetailData.scope,
        ...(payload.scope ?? {}),
      },
      metrics: {
        ...emptyPrepaymentDetailData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyPrepaymentDetailData.links,
        ...(payload.links ?? {}),
      },
      actions: {
        ...emptyPrepaymentDetailData.actions,
        ...(payload.actions ?? {}),
        transferUsers: payload.actions?.transferUsers ?? emptyPrepaymentDetailData.actions.transferUsers,
      },
      edit: {
        ...emptyPrepaymentDetailData.edit,
        ...(payload.edit ?? {}),
        customers: payload.edit?.customers ?? emptyPrepaymentDetailData.edit.customers,
        paymentMethods: payload.edit?.paymentMethods ?? emptyPrepaymentDetailData.edit.paymentMethods,
        statuses: payload.edit?.statuses ?? emptyPrepaymentDetailData.edit.statuses,
      },
      prepayment: payload.prepayment ?? emptyPrepaymentDetailData.prepayment,
      usages: payload.usages ?? emptyPrepaymentDetailData.usages,
    };
  } catch (error) {
    return {
      ...emptyPrepaymentDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Prepayment detail API unavailable',
    };
  }
}

function prepaymentPayloadBody(payload: PrepaymentFormPayload): URLSearchParams {
  const body = new URLSearchParams();
  body.set('customer', String(payload.customerId));
  body.set('amount', payload.amount);
  body.set('payment_date', payload.paymentDate);
  body.set('payment_method', payload.paymentMethod);
  if (payload.balance !== undefined) body.set('balance', payload.balance);
  if (payload.status) body.set('status', payload.status);
  if (payload.payerName) body.set('payer_name', payload.payerName);
  if (payload.memo) body.set('memo', payload.memo);
  return body;
}

export async function createPrepayment(
  payload: PrepaymentFormPayload,
  submitUrl = '/reporting/api/prepayments/create/',
): Promise<PrepaymentMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: prepaymentPayloadBody(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Prepayment create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayment create failed: ${response.status}`);
  }
  return data;
}

export async function updatePrepayment(
  payload: PrepaymentFormPayload,
  submitUrl: string,
): Promise<PrepaymentMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: prepaymentPayloadBody(payload),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Prepayment update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayment update failed: ${response.status}`);
  }
  return data;
}

export async function cancelPrepayment(
  cancelUrl: string,
  reason: string,
): Promise<PrepaymentMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  if (reason.trim()) {
    body.set('cancel_reason', reason.trim());
  }

  const response = await fetch(cancelUrl, {
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
    throw new Error(`Prepayment cancel API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayment cancel failed: ${response.status}`);
  }
  return data;
}

export async function deletePrepayment(
  deleteUrl: string,
): Promise<PrepaymentMutationResponse> {
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
    throw new Error(`Prepayment delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayment delete failed: ${response.status}`);
  }
  return data;
}

export async function transferPrepayment(
  transferUrl: string,
  targetUserId: number,
  reason: string,
): Promise<PrepaymentMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('target_user', String(targetUserId));
  if (reason.trim()) {
    body.set('reason', reason.trim());
  }

  const response = await fetch(transferUrl, {
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
    throw new Error(`Prepayment transfer API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PrepaymentMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Prepayment transfer failed: ${response.status}`);
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
      documents: {
        ...emptyScheduleDetailData.documents,
        ...(payload.documents ?? {}),
        items: payload.documents?.items ?? emptyScheduleDetailData.documents.items,
      },
    };
  } catch (error) {
    return {
      ...emptyScheduleDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Schedule detail API unavailable',
    };
  }
}

export async function loadScheduleDocumentPreview(previewUrl: string): Promise<ScheduleDocumentPreviewData> {
  type RawScheduleDocumentPreviewData = {
    success?: boolean;
    error?: string;
    templateUrl?: string;
    template_url?: string;
    templateFilename?: string;
    template_filename?: string;
    variables?: ScheduleDocumentPreviewData['variables'];
    fileInfo?: ScheduleDocumentPreviewData['fileInfo'];
    file_info?: {
      company_name?: string;
      customer_company?: string;
      doc_name?: string;
      today_str?: string;
      base_date?: string;
      transaction_number?: string;
    };
    items?: Array<{
      index?: number;
      name?: string;
      quantity?: number;
      unit?: string;
      unit_price?: number;
      unitPrice?: number;
      subtotal?: number;
    }>;
    itemCount?: number;
    item_count?: number;
  };

  const response = await fetch(previewUrl, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Document preview API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as RawScheduleDocumentPreviewData;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || `Document preview failed: ${response.status}`);
  }
  const rawFileInfo = data.fileInfo ?? {};
  const snakeFileInfo = data.file_info ?? {};
  return {
    success: true,
    variables: data.variables ?? {},
    fileInfo: {
      companyName: rawFileInfo.companyName ?? snakeFileInfo.company_name,
      customerCompany: rawFileInfo.customerCompany ?? snakeFileInfo.customer_company,
      docName: rawFileInfo.docName ?? snakeFileInfo.doc_name,
      todayStr: rawFileInfo.todayStr ?? snakeFileInfo.today_str,
      baseDate: rawFileInfo.baseDate ?? snakeFileInfo.base_date,
      transactionNumber: rawFileInfo.transactionNumber ?? snakeFileInfo.transaction_number,
    },
    items: (data.items ?? []).map((item, index) => ({
      index: item.index ?? index + 1,
      name: item.name ?? '',
      quantity: item.quantity ?? 0,
      unit: item.unit ?? '',
      unitPrice: item.unitPrice ?? item.unit_price ?? 0,
      subtotal: item.subtotal ?? 0,
    })),
    itemCount: data.itemCount ?? data.item_count ?? 0,
    templateUrl: data.templateUrl ?? data.template_url,
    templateFilename: data.templateFilename ?? data.template_filename,
  };
}

function filenameFromContentDisposition(value: string): string {
  const encodedMatch = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (encodedMatch?.[1]) {
    try {
      return decodeURIComponent(encodedMatch[1].trim());
    } catch {
      return encodedMatch[1].trim();
    }
  }
  const quotedMatch = value.match(/filename="?([^";]+)"?/i);
  return quotedMatch?.[1]?.trim() || '';
}

export async function downloadScheduleDocument(downloadUrl: string): Promise<ScheduleDocumentDownloadResult> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(downloadUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/octet-stream, application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const data = (await response.json()) as { success?: boolean; error?: string; message?: string };
    redirectIfLoginRequired(response, data);
    throw new Error(data.error || data.message || `Document download failed: ${response.status}`);
  }
  if (!response.ok) {
    throw new Error(`Document download failed: ${response.status}`);
  }
  const xFilename = response.headers.get('X-Filename') || '';
  let filename = '';
  if (xFilename) {
    try {
      filename = decodeURIComponent(xFilename);
    } catch {
      filename = xFilename;
    }
  }
  if (!filename) {
    filename = filenameFromContentDisposition(response.headers.get('content-disposition') || '');
  }
  return {
    blob: await response.blob(),
    filename: filename || 'document.xlsx',
  };
}

export async function loadDocumentTemplatesData(type = ''): Promise<DocumentTemplatesData> {
  try {
    const params = new URLSearchParams();
    if (type) params.set('type', type);
    const response = await fetch(`/reporting/api/documents/${params.toString() ? `?${params.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Document templates API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<DocumentTemplatesData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Document templates API unavailable: ${response.status}`);
    }
    return {
      ...emptyDocumentTemplatesData,
      ...payload,
      currentUser: {
        ...emptyDocumentTemplatesData.currentUser,
        ...(payload.currentUser ?? {}),
      },
      filters: {
        ...emptyDocumentTemplatesData.filters,
        ...(payload.filters ?? {}),
      },
      documentTypes: payload.documentTypes ?? emptyDocumentTemplatesData.documentTypes,
      summary: {
        ...emptyDocumentTemplatesData.summary,
        ...(payload.summary ?? {}),
        byType: payload.summary?.byType ?? emptyDocumentTemplatesData.summary.byType,
      },
      create: {
        ...emptyDocumentTemplatesData.create,
        ...(payload.create ?? {}),
        companies: payload.create?.companies ?? emptyDocumentTemplatesData.create.companies,
      },
      links: {
        ...emptyDocumentTemplatesData.links,
        ...(payload.links ?? {}),
      },
      templates: payload.templates ?? emptyDocumentTemplatesData.templates,
      recentGenerations: payload.recentGenerations ?? emptyDocumentTemplatesData.recentGenerations,
    };
  } catch (error) {
    return {
      ...emptyDocumentTemplatesData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Document templates API unavailable',
      filters: {
        type,
      },
    };
  }
}

function documentTemplatePayloadToFormData(payload: DocumentTemplateMutationPayload): FormData {
  const formData = new FormData();
  formData.set('documentType', payload.documentType);
  formData.set('name', payload.name);
  formData.set('description', payload.description ?? '');
  formData.set('isDefault', payload.isDefault ? 'true' : 'false');
  if (payload.companyId) formData.set('companyId', payload.companyId);
  if (payload.file) formData.set('file', payload.file);
  return formData;
}

async function postDocumentTemplateForm(
  submitUrl: string,
  payload?: DocumentTemplateMutationPayload,
): Promise<DocumentTemplateMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: payload ? documentTemplatePayloadToFormData(payload) : undefined,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Document template request failed: ${response.status}`);
  }
  const data = (await response.json()) as DocumentTemplateMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Document template request failed: ${response.status}`);
  }
  return data;
}

export async function createDocumentTemplate(
  submitUrl: string,
  payload: DocumentTemplateMutationPayload,
): Promise<DocumentTemplateMutationResponse> {
  return postDocumentTemplateForm(submitUrl, payload);
}

export async function updateDocumentTemplate(
  submitUrl: string,
  payload: DocumentTemplateMutationPayload,
): Promise<DocumentTemplateMutationResponse> {
  return postDocumentTemplateForm(submitUrl, payload);
}

export async function deleteDocumentTemplate(deleteUrl: string): Promise<DocumentTemplateMutationResponse> {
  return postDocumentTemplateForm(deleteUrl);
}

export async function toggleDocumentTemplateDefault(toggleUrl: string): Promise<DocumentTemplateMutationResponse> {
  return postDocumentTemplateForm(toggleUrl);
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

export async function updateScheduleDeliveryItems(
  submitUrl: string,
  items: ScheduleDeliveryItemPayload[],
): Promise<ScheduleDeliveryItemsUpdateResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ items }),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule delivery items API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleDeliveryItemsUpdateResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule delivery items update failed: ${response.status}`);
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

export async function loadAIWorkspaceData(params: AIWorkspaceLoadParams = {}): Promise<AIWorkspaceData> {
  const query = new URLSearchParams();
  if (params.departmentId) {
    query.set('department_id', String(params.departmentId));
  }
  const queryString = query.toString();
  try {
    const response = await fetch(`/reporting/api/ai-workspace/${queryString ? `?${queryString}` : ''}`, {
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
    const featuredDepartment = payload.featuredDepartment
      ? {
          ...payload.featuredDepartment,
          quoteDelivery: {
            ...emptyCustomerDetailData.aiDepartment.quoteDelivery,
            ...(payload.featuredDepartment.quoteDelivery ?? {}),
            productStats: payload.featuredDepartment.quoteDelivery?.productStats ?? emptyCustomerDetailData.aiDepartment.quoteDelivery.productStats,
            recentDeliveries: payload.featuredDepartment.quoteDelivery?.recentDeliveries ?? emptyCustomerDetailData.aiDepartment.quoteDelivery.recentDeliveries,
          },
        }
      : null;
    return {
      ...payload,
      featuredDepartment,
      selectedDepartmentId: payload.selectedDepartmentId ?? featuredDepartment?.departmentId ?? null,
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

export async function loadWeeklyReportsData(params: {
  year?: string;
  month?: string;
  userId?: string;
} = {}): Promise<WeeklyReportsData> {
  const query = new URLSearchParams();
  if (params.year) query.set('year', params.year);
  if (params.month) query.set('month', params.month);
  if (params.userId) query.set('user_id', params.userId);

  try {
    const response = await fetch(`/reporting/api/weekly-reports/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Weekly reports API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<WeeklyReportsData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Weekly reports API unavailable: ${response.status}`);
    }
    return {
      ...emptyWeeklyReportsData,
      ...payload,
      scope: {
        ...emptyWeeklyReportsData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyWeeklyReportsData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyWeeklyReportsData.options,
        ...(payload.options ?? {}),
        years: payload.options?.years ?? emptyWeeklyReportsData.options.years,
        months: payload.options?.months ?? emptyWeeklyReportsData.options.months,
        users: payload.options?.users ?? emptyWeeklyReportsData.options.users,
      },
      metrics: {
        ...emptyWeeklyReportsData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyWeeklyReportLinks,
        ...(payload.links ?? {}),
      },
      reports: payload.reports ?? [],
    };
  } catch (error) {
    return {
      ...emptyWeeklyReportsData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Weekly reports API unavailable',
    };
  }
}

export async function loadWeeklyReportCreateData(): Promise<WeeklyReportCreateData> {
  try {
    const response = await fetch('/reporting/api/weekly-reports/create/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Weekly report create API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<WeeklyReportCreateData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Weekly report create API unavailable: ${response.status}`);
    }
    return {
      ...emptyWeeklyReportCreateData,
      ...payload,
      form: {
        ...emptyWeeklyReportForm,
        ...(payload.form ?? {}),
      },
      links: {
        ...emptyWeeklyReportLinks,
        ...(payload.links ?? {}),
      },
      existingReport: payload.existingReport ?? null,
    };
  } catch (error) {
    return {
      ...emptyWeeklyReportCreateData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Weekly report create API unavailable',
    };
  }
}

export async function loadWeeklyReportDetailData(reportId: number): Promise<WeeklyReportDetailData> {
  try {
    const response = await fetch(`/reporting/api/weekly-reports/${reportId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Weekly report detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<WeeklyReportDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Weekly report detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyWeeklyReportDetailData,
      ...payload,
      report: {
        ...emptyWeeklyReportItem,
        ...(payload.report ?? {}),
      },
      form: payload.form
        ? {
            ...emptyWeeklyReportForm,
            ...payload.form,
          }
        : null,
      links: {
        ...emptyWeeklyReportLinks,
        ...(payload.links ?? {}),
      },
    };
  } catch (error) {
    return {
      ...emptyWeeklyReportDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Weekly report detail API unavailable',
    };
  }
}

export async function saveWeeklyReport(
  submitUrl: string,
  payload: WeeklyReportFormPayload,
): Promise<WeeklyReportSaveResponse> {
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
    throw new Error(`Weekly report save API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as WeeklyReportSaveResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Weekly report save failed: ${response.status}`);
  }
  return data;
}

export async function deleteWeeklyReport(deleteUrl: string): Promise<WeeklyReportSaveResponse> {
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
    throw new Error(`Weekly report delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as WeeklyReportSaveResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Weekly report delete failed: ${response.status}`);
  }
  return data;
}

export async function loadWeeklyReportSchedules(weekStart: string, weekEnd: string): Promise<WeeklyReportSchedulesData> {
  const query = new URLSearchParams();
  query.set('week_start', weekStart);
  query.set('week_end', weekEnd);
  const response = await fetch(`/reporting/api/weekly-reports/schedules/?${query.toString()}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Weekly report schedules API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as WeeklyReportSchedulesData;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.error) {
    throw new Error(data.error || `Weekly report schedules failed: ${response.status}`);
  }
  return {
    schedules: data.schedules ?? [],
    categorized: {
      activity: data.categorized?.activity ?? [],
      quote_delivery: data.categorized?.quote_delivery ?? [],
    },
  };
}

export async function generateWeeklyReportAiDraft(weekStart: string, weekEnd: string): Promise<WeeklyReportAiDraft> {
  const query = new URLSearchParams();
  query.set('week_start', weekStart);
  query.set('week_end', weekEnd);
  const response = await fetch(`/reporting/api/weekly-reports/ai-draft/?${query.toString()}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Weekly report AI draft API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as { draft?: WeeklyReportAiDraft; error?: string };
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.error) {
    throw new Error(data.error || `Weekly report AI draft failed: ${response.status}`);
  }
  return data.draft ?? {};
}

export async function saveWeeklyReportManagerComment(
  submitUrl: string,
  comment: string,
): Promise<WeeklyReportManagerCommentResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = new URLSearchParams();
  body.set('manager_comment', comment);
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
    throw new Error(`Weekly report manager comment API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as WeeklyReportManagerCommentResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.error) {
    throw new Error(data.error || `Weekly report manager comment failed: ${response.status}`);
  }
  return data;
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
    return {
      ...emptyPipelineData,
      generatedAt: new Date().toISOString(),
    };
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
