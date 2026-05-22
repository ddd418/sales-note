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
  canManage: boolean;
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
    yearRevenue: number;
    quarterRevenue: number;
    monthlyRevenue: number;
  };
  revenuePeriod: {
    year: number;
    quarter: number;
    yearStart: string;
    yearEnd: string;
    quarterStart: string;
    quarterEnd: string;
    monthStart: string;
    monthEnd: string;
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

export type ReportsCustomerRecentDelivery = {
  date: string | null;
  label: string;
  amount: number;
  paymentSource: 'normal' | 'prepayment' | string;
  paymentSourceLabel: string;
};

export type ReportsCustomerOperationRow = {
  id: number;
  accountId?: number | null;
  representativeCustomerId?: number;
  customer: string;
  company: string;
  department: string;
  manager: string;
  contactCount?: number;
  contactPreview?: string[];
  owner: string;
  status: string;
  statusLabel: string;
  priority: string;
  priorityLabel: string;
  pipelineStage: string;
  pipelineStageLabel: string;
  deliveryCount: number;
  deliveryAmount: number;
  normalDeliveryCount: number;
  normalDeliveryAmount: number;
  prepaymentDeliveryCount: number;
  prepaymentDeliveryAmount: number;
  prepaymentUsedAmount: number;
  lastDeliveryDate: string | null;
  quoteCount: number;
  quoteAmount: number;
  lastQuoteDate: string | null;
  serviceCount: number;
  openServiceCount: number;
  lastServiceDate: string | null;
  prepaymentCount: number;
  prepaymentAmount: number;
  prepaymentBalance: number;
  prepaymentUsedTotal: number;
  lastPrepaymentDate: string | null;
  lastActivityDate: string | null;
  recentDeliveryItems: ReportsCustomerRecentDelivery[];
  href: string;
  customerHref?: string;
  djangoHref: string;
};

export type ReportsCustomerOperations = {
  metrics: {
    totalCustomers: number;
    customersWithDeliveries: number;
    deliveryCount: number;
    deliveryAmount: number;
    normalDeliveryCount: number;
    normalDeliveryAmount: number;
    prepaymentDeliveryCount: number;
    prepaymentDeliveryAmount: number;
    prepaymentUsedAmount: number;
    quoteCount: number;
    quoteAmount: number;
    serviceCount: number;
    openServiceCount: number;
    prepaymentCount: number;
    prepaymentAmount: number;
    prepaymentBalance: number;
    prepaymentUsedTotal: number;
  };
  rows: ReportsCustomerOperationRow[];
};

export type ReportsDataQualityContact = {
  id: number;
  name: string;
  manager: string;
  email: string;
  phone: string;
  companyName: string;
  departmentName: string;
  departmentId: number | null;
  ownerName: string;
  scheduleCount: number;
  historyCount: number;
  quoteCount: number;
  prepaymentCount: number;
  recordCount: number;
  recordSummary: string;
  href: string;
  accountHref: string;
};

export type ReportsDataQualityDepartment = {
  id: number;
  name: string;
  companyName: string;
  accountHref: string;
  contactCount: number;
  recordCount: number;
  scheduleCount: number;
  historyCount: number;
  quoteCount: number;
  prepaymentCount: number;
  contacts: ReportsDataQualityContact[];
};

export type ReportsDuplicateAccountGroup = {
  companyName: string;
  normalizedDepartmentName: string;
  departmentNames: string[];
  departmentIds: number[];
  contactCount: number;
  recordCount: number;
  riskLevel: string;
  riskLabel: string;
  suggestedAction: string;
  departments: ReportsDataQualityDepartment[];
  contacts: ReportsDataQualityContact[];
};

export type ReportsDuplicateContactGroup = {
  companyName: string;
  departmentName: string;
  identity: string;
  contactCount: number;
  recordCount: number;
  contactIds: number[];
  riskLevel: string;
  riskLabel: string;
  suggestedAction: string;
  contacts: ReportsDataQualityContact[];
};

export type ReportsDataQuality = {
  metrics: {
    duplicateAccountGroups: number;
    duplicateContactGroups: number;
    contactsWithoutDepartment: number;
    contactsWithoutCompany: number;
    cleanupCandidateCount: number;
  };
  normalizationRule: string;
  duplicateAccounts: ReportsDuplicateAccountGroup[];
  duplicateContacts: ReportsDuplicateContactGroup[];
  contactsWithoutDepartment: ReportsDataQualityContact[];
  contactsWithoutCompany: ReportsDataQualityContact[];
};

export type AccountCleanupAffectedRecord = {
  key: string;
  label: string;
  count: number;
  amount: number;
  detail: string;
};

export type AccountCleanupPreviewAccount = {
  id: number | null;
  name: string;
  companyId: number | null;
  companyName: string;
  href: string;
  djangoHref: string;
  metrics: {
    contactCount: number;
    recordCount: number;
    scheduleCount: number;
    deliveryCount: number;
    quoteCount: number;
    quoteAmount: number;
    historyCount: number;
    prepaymentCount: number;
    prepaymentAmount: number;
    prepaymentBalance: number;
    prepaymentUsageCount: number;
    prepaymentUsedAmount: number;
    assetCount: number;
    serviceCaseCount: number;
    calibrationCount: number;
  };
  affectedRecords: AccountCleanupAffectedRecord[];
  contacts: ReportsDataQualityContact[];
};

export type AccountCleanupPreviewData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  mode: 'source' | 'compare' | string;
  sourceAccount: AccountCleanupPreviewAccount;
  targetAccount: AccountCleanupPreviewAccount | null;
  combined: {
    metrics: AccountCleanupPreviewAccount['metrics'];
    description: string;
  };
  warnings: string[];
  links: {
    sourceAccount: string;
    reports: string;
  };
};

export type AccountCleanupSearchResult = {
  id: number;
  label: string;
  companyName: string;
  departmentName: string;
  contactPreview: string[];
  piPreview: string[];
  emailPreview: string[];
  meta: string;
  searchText: string;
  href: string;
  previewHref: string;
};

export type ReportsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  filters: {
    dateFrom: string;
    dateTo: string;
    selectedUserId: number | null;
  };
  scope: {
    canFilterUsers: boolean;
    canExport: boolean;
    label: string;
    salespeople: Array<{ id: number; name: string; username: string }>;
  };
  metrics: {
    totalHistories: number;
    completedFollowups: number;
    overdueFollowups: number;
    upcomingFollowups: number;
    activePipeline: number;
    totalAssets: number;
    activeAssets: number;
    openServiceAssets: number;
    overdueServiceAssets: number;
    dueCalibrationAssets: number;
    overdueCalibrationAssets: number;
  };
  activityReport: Array<{
    user: { id: number; name: string; username: string };
    historyCount: number;
    followupCount: number;
    overdueCount: number;
    lastActivityAt: string | null;
  }>;
  customerReport: Array<{
    id: number;
    customer: string;
    company: string;
    department: string;
    owner: string;
    pipelineStage: string;
    pipelineStageLabel: string;
    lastActivityAt: string | null;
    nextActionDate: string | null;
    href: string;
    djangoHref: string;
  }>;
  customerOperations: ReportsCustomerOperations;
  dataQuality: ReportsDataQuality;
  pipelineSummary: Array<{ stage: string; label: string; count: number }>;
  links: {
    activityCsv: string;
    pipelineCsv: string;
    activityXlsx: string;
    pipelineXlsx: string;
    customerOperationsXlsx: string;
    assets: string;
    legacy: string;
  };
};

export type ProfileData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  user: {
    id: number | null;
    username: string;
    firstName: string;
    lastName: string;
    fullName: string;
    email: string;
    dateJoined: string | null;
    lastLogin: string | null;
  };
  profile: {
    role: string;
    roleLabel: string;
    company: string;
    canUseAi: boolean;
    canDownloadExcel: boolean;
  };
  emailConnection: {
    enabled: boolean;
    connected: boolean;
    provider: string;
    providerLabel: string;
    address: string;
    connectedAt: string | null;
    lastSyncAt: string | null;
    gmailConnected: boolean;
    imapConnected: boolean;
    links: {
      mailbox: string;
      businessCards: string;
      gmailConnect: string;
      imapConnect: string;
      imapSync: string;
      disconnect: string;
    };
  };
  links: {
    update: string;
    password: string;
    legacy: string;
    legacyEdit: string;
    dashboard: string;
  };
};

export type ProfileUpdatePayload = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
};

export type ProfilePasswordPayload = {
  oldPassword: string;
  newPassword1: string;
  newPassword2: string;
};

export type BusinessCardItem = {
  id: number;
  name: string;
  fullName: string;
  title: string;
  companyName: string;
  department: string;
  phone: string;
  mobile: string;
  email: string;
  address: string;
  website: string;
  fax: string;
  logoUrl: string;
  logoFileUrl: string;
  logoLinkUrl: string;
  signatureHtml: string;
  signaturePreviewHtml: string;
  isDefault: boolean;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  links: {
    update: string;
    delete: string;
    setDefault: string;
    legacyEdit: string;
  };
};

export type BusinessCardsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  error?: string;
  message?: string;
  cards: BusinessCardItem[];
  links: {
    create: string;
    legacy: string;
    mailbox: string;
    profile: string;
  };
};

export type BusinessCardPayload = {
  name: string;
  fullName: string;
  title: string;
  companyName: string;
  department: string;
  phone: string;
  mobile: string;
  email: string;
  address: string;
  website: string;
  fax: string;
  logoUrl: string;
  logoLinkUrl: string;
  signatureHtml: string;
  isDefault: boolean;
  logo?: File | null;
};

export type MailboxType = 'inbox' | 'sent' | 'scheduled' | 'starred' | 'archived' | 'trash';

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
  status?: string;
  statusLabel?: string;
  scheduledAt?: string | null;
  isScheduled?: boolean;
  threadId: string;
  threadHref: string;
  djangoThreadHref: string;
  replyHref: string;
  toggleStarHref: string;
  archiveHref: string;
  trashHref: string;
  restoreHref: string;
  deleteHref: string;
  cancelHref?: string;
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
    source?: string;
    downloadHref?: string;
  }>;
};

export type MailAutoAttachment = {
  key: string;
  filename: string;
  size?: number;
  documentLogId?: number | null;
  documentType: string;
  documentTypeLabel: string;
  quoteGroup?: string;
  quoteGroupLabel?: string;
  willGenerate?: boolean;
  description?: string;
};

export type MailInternalCcContact = {
  id: number;
  name: string;
  email: string;
  label?: string;
};

export type MailboxCreateOptions = {
  canSend: boolean;
  message: string;
  submitUrl: string;
  djangoUrl: string;
  autoAttachments: MailAutoAttachment[];
  autoAttachLabel: string;
  schedule: {
    id: number;
    activityType: string;
  } | null;
  internalCcEmails: string[];
  internalCcContacts: MailInternalCcContact[];
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
  scheduled: string;
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
    isScheduled?: boolean;
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
  includeInternalCc?: boolean;
  internalCcEmails?: string[];
  subject: string;
  bodyText: string;
  bodyHtml?: string;
  scheduledAt?: string;
  followupId?: number;
  scheduleId?: number;
  businessCardId?: number;
  attachments?: File[];
  excludedAutoAttachmentKeys?: string[];
};

export type MailboxActionResponse = {
  success?: boolean;
  error?: string;
  message?: string;
  href?: string;
  djangoHref?: string;
  scheduled?: boolean;
  is_starred?: boolean;
  is_archived?: boolean;
  synced?: number;
};

export type CustomerItem = {
  id: number;
  accountId?: number | null;
  accountType?: 'department' | 'followup' | string;
  representativeCustomerId?: number;
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
  contactCount?: number;
  contactPreview?: string[];
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
  accountHref?: string;
  customerHref?: string;
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
    totalAccounts: number;
    filteredAccounts: number;
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
  accounts: CustomerItem[];
  priorityCustomers: CustomerItem[];
  priorityAccounts: CustomerItem[];
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
    accountPrepayments: string;
    customerPrepayments: string;
    djangoCustomerPrepayments: string;
  };
  recentPrepayments: PrepaymentListItem[];
};

export type CustomerServiceCase = {
  id: number;
  assetId: number;
  followupId: number | null;
  caseType: string;
  caseTypeLabel: string;
  status: string;
  statusLabel: string;
  priority: string;
  priorityLabel: string;
  receivedDate: string | null;
  dueDate: string | null;
  completedDate: string | null;
  symptom: string;
  resolution: string;
  assignedTo: string;
  hasReport: boolean;
  reportUrl: string;
  updateUrl: string;
  updatedAt: string | null;
};

export type CustomerCalibrationRecord = {
  id: number;
  assetId: number;
  followupId: number | null;
  calibrationDate: string | null;
  nextDueDate: string | null;
  result: string;
  resultLabel: string;
  notes: string;
  performedBy: string;
  hasCertificate: boolean;
  certificateUrl: string;
  updateUrl: string;
  updatedAt: string | null;
};

export type CustomerAssetItem = {
  id: number;
  companyId: number;
  departmentId: number;
  primaryFollowupId: number | null;
  primaryFollowupName: string;
  productId: number | null;
  productCode: string;
  assetName: string;
  modelName: string;
  serialNumber: string;
  purchaseDate: string | null;
  installLocation: string;
  warrantyUntil: string | null;
  status: string;
  statusLabel: string;
  notes: string;
  createdBy: string;
  updatedAt: string | null;
  updateUrl: string;
  serviceCaseCreateUrl: string;
  calibrationCreateUrl: string;
  latestServiceCase: CustomerServiceCase | null;
  latestCalibration: CustomerCalibrationRecord | null;
  serviceCases: CustomerServiceCase[];
  calibrations: CustomerCalibrationRecord[];
};

export type CustomerAssetSummary = {
  canManage: boolean;
  message: string;
  metrics: {
    assetCount: number;
    activeAssetCount: number;
    openServiceCaseCount: number;
    dueCalibrationCount: number;
  };
  links: {
    createAsset: string;
    createServiceCase: string;
    createCalibration: string;
  };
  options: {
    assetStatuses: Array<{ value: string; label: string }>;
    serviceCaseTypes: Array<{ value: string; label: string }>;
    serviceStatuses: Array<{ value: string; label: string }>;
    servicePriorities: Array<{ value: string; label: string }>;
    calibrationResults: Array<{ value: string; label: string }>;
  };
  assets: CustomerAssetItem[];
};

export type CustomerAssetDirectoryItem = CustomerAssetItem & {
  companyName: string;
  departmentName: string;
  customerName: string;
  ownerName: string;
  customerHref: string;
  djangoCustomerHref: string;
  assetDirectoryHref: string;
};

export type CustomerAssetWorkQueueItem = {
  id: string;
  kind: string;
  kindLabel: string;
  assetId: number;
  assetName: string;
  customerName: string;
  companyName: string;
  departmentName: string;
  ownerName: string;
  dueDate: string | null;
  statusLabel: string;
  priorityLabel: string;
  href: string;
  customerHref: string;
};

export type CustomerAssetCreateCustomerOption = {
  id: number;
  customerName: string;
  companyName: string;
  departmentName: string;
  manager: string;
  email: string;
  ownerName: string;
  priorityLabel: string;
  href: string;
  assetCreateUrl: string;
};

export type CustomerAssetDirectoryData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  canManage: boolean;
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
    status: string;
    owner: string;
    service: string;
    calibration: string;
  };
  options: {
    owners: Array<{ id: number; name: string }>;
    assetStatuses: Array<{ value: string; label: string }>;
    serviceCaseTypes: Array<{ value: string; label: string }>;
    serviceStatuses: Array<{ value: string; label: string }>;
    servicePriorities: Array<{ value: string; label: string }>;
    calibrationResults: Array<{ value: string; label: string }>;
    serviceFilters: Array<{ value: string; label: string }>;
    calibrationFilters: Array<{ value: string; label: string }>;
  };
  metrics: {
    totalAssets: number;
    filteredAssets: number;
    activeAssets: number;
    openServiceAssets: number;
    dueCalibrationAssets: number;
    overdueCalibrationAssets: number;
    noCalibrationAssets: number;
    returnedAssets: number;
    truncated: boolean;
  };
  links: {
    assets: string;
    customers: string;
  };
  create: {
    canCreate: boolean;
    message: string;
    customers: CustomerAssetCreateCustomerOption[];
  };
  workQueue: CustomerAssetWorkQueueItem[];
  assets: CustomerAssetDirectoryItem[];
};

export type CustomerAssetPayload = {
  assetName: string;
  modelName?: string;
  serialNumber?: string;
  purchaseDate?: string;
  installLocation?: string;
  warrantyUntil?: string;
  status: string;
  notes?: string;
};

export type CustomerServiceCasePayload = {
  assetId: number;
  caseType: string;
  status: string;
  priority: string;
  receivedDate: string;
  dueDate?: string;
  completedDate?: string;
  symptom?: string;
  resolution?: string;
  serviceReport?: File | null;
};

export type CustomerCalibrationPayload = {
  assetId: number;
  calibrationDate: string;
  nextDueDate?: string;
  result: string;
  notes?: string;
  certificateFile?: File | null;
};

export type CustomerAssetMutationResponse = {
  success: boolean;
  error?: string;
  message?: string;
  asset?: CustomerAssetItem;
  serviceCase?: CustomerServiceCase;
  calibration?: CustomerCalibrationRecord;
};

export type CustomerOperationalMetrics = {
  serviceRecords: number;
  quoteRecords: number;
  deliveryRecords: number;
  prepaymentDeliveryRecords: number;
  normalDeliveryRecords: number;
  prepaymentRecords: number;
  deliveryAmount: number;
  prepaymentDeliveryAmount: number;
  normalDeliveryAmount: number;
  prepaymentUsedAmount: number;
};

export type CustomerDeliveryRecord = {
  id: number;
  recordType: string;
  date: string | null;
  time?: string | null;
  customerName: string;
  companyName: string;
  departmentName: string;
  ownerName: string;
  status: string;
  statusLabel: string;
  activityLabel: string;
  items: ScheduleDeliveryItem[];
  itemCount: number;
  totalAmount: number;
  notes: string;
  href: string;
  djangoHref: string;
  paymentSource: 'prepayment' | 'normal' | string;
  paymentSourceLabel: string;
  paymentType: 'prepayment_deduction' | 'normal' | string;
  paymentTypeLabel: string;
  prepaymentId: number | null;
  prepaymentAmount: number;
  prepaymentUsages: SchedulePrepaymentUsage[];
  paymentEvidence: string;
};

export type CustomerQuoteRecord = {
  id: number;
  recordType: string;
  scheduleId: number | null;
  quoteNumber: string;
  date: string | null;
  validUntil: string | null;
  customerName: string;
  companyName: string;
  departmentName: string;
  ownerName: string;
  status: string;
  statusLabel: string;
  items: ScheduleDeliveryItem[];
  itemCount: number;
  totalAmount: number;
  notes: string;
  href: string;
  djangoHref: string;
};

export type CustomerServiceRecord = {
  id: number;
  recordType: string;
  date: string | null;
  dueDate: string | null;
  completedDate: string | null;
  customerName: string;
  assetName: string;
  assetModelName: string;
  ownerName: string;
  assignedTo: string;
  status: string;
  statusLabel: string;
  priority: string;
  priorityLabel: string;
  caseType: string;
  caseTypeLabel: string;
  summary: string;
  detail: string;
  href: string;
  djangoHref: string;
  scheduleHref?: string;
};

export type CustomerOperationalRecords = {
  metrics: CustomerOperationalMetrics;
  serviceRecords: CustomerServiceRecord[];
  quoteRecords: CustomerQuoteRecord[];
  deliveryRecords: CustomerDeliveryRecord[];
  prepaymentRecords: PrepaymentListItem[];
};

export type CustomerAccountContact = {
  id: number;
  name: string;
  manager: string;
  email: string;
  phone: string;
  contactSummary: string;
  ownerName: string;
  ownerId: number;
  status: string;
  statusLabel: string;
  priority: string;
  priorityLabel: string;
  pipelineStage: string;
  pipelineLabel: string;
  address: string;
  notes: string;
  href: string;
  djangoHref: string;
};

export type CustomerAccountSummary = {
  id: number | null;
  type: 'department' | 'followup' | string;
  name: string;
  companyId: number | null;
  companyName: string;
  departmentId: number | null;
  departmentName: string;
  representativeCustomerId: number | null;
  representativeName: string;
  contactCount: number;
  ledgerScopeLabel: string;
  ledgerScopeDescription: string;
  contacts: CustomerAccountContact[];
  href: string;
  djangoRepresentativeHref: string;
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
  account: CustomerAccountSummary;
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
    deliveryRecordsXlsx: string;
    accountDetail: string;
    accountDeliveryRecordsXlsx: string;
  };
  prepaymentSummary: CustomerPrepaymentSummary;
  operationalRecords: CustomerOperationalRecords;
  assetSummary: CustomerAssetSummary;
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
  recommendedQuestions: CustomerAiRecommendedQuestion[];
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

export type CustomerAiRecommendedQuestion = {
  question: string;
  source: string;
  sourceLabel: string;
  context: string;
  priority: string;
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
  priority_updates?: number;
  priorityUpdates?: number;
  priority_recommendations?: number;
  priorityRecommendations?: number;
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
    personalSchedule?: {
      canCreate: boolean;
      message: string;
      submitUrl: string;
      djangoUrl: string;
    };
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
  scheduleId?: number;
};

export type NoteCreateResponse = {
  success: boolean;
  error?: string;
  message?: string;
  historyId?: number;
  href?: string;
  reactHref?: string;
  note?: NoteItem;
};

export type NoteEditPayload = {
  actionType: string;
  activityDate?: string;
  content: string;
  deliveryAmount?: string;
  deliveryItems?: string;
  followupId: number;
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
  customerEmail?: string;
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
  deleteHref?: string;
  canEdit?: boolean;
  statusOptions?: Array<{ value: string; label: string }>;
  customerHref: string;
  djangoCustomerHref?: string;
  createHistoryHref: string;
  djangoCreateHistoryHref?: string;
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
  unitPrice: number | null;
  discountRate: number;
  discountUnitPrice: number | null;
  effectiveUnitPrice: number | null;
  totalPrice: number;
  taxInvoiceIssued: boolean;
  quoteGroup: string;
  quoteGroupLabel: string;
  notes: string;
  sourceQuoteScheduleId?: number | null;
  sourceQuoteItemId?: number | null;
};

export type ScheduleDeliveryItemPayload = {
  id?: number;
  productId?: number | null;
  itemName: string;
  quantity: string | number;
  unit: string;
  unitPrice?: string | number | null;
  discountRate?: string | number | null;
  discountUnitPrice?: string | number | null;
  taxInvoiceIssued: boolean;
  quoteGroup?: string;
  notes?: string;
  sourceQuoteScheduleId?: number | null;
  sourceQuoteItemId?: number | null;
};

export type ScheduleDeliveryItemsUpdateOptions = {
  usePrepayment?: boolean;
  prepayments?: SchedulePrepaymentSelectionPayload[];
};

export type FollowupQuoteItem = {
  id: number | null;
  productId?: number | null;
  productCode?: string;
  productDescription?: string;
  sourceQuoteScheduleId?: number | null;
  sourceQuoteItemId?: number | null;
  itemName: string;
  originalQuantity: number;
  deliveredQuantity: number;
  remainingQuantity: number;
  quantity: number;
  unit: string;
  unitPrice: number;
  discountRate: number;
  discountUnitPrice: number | null;
  effectiveUnitPrice: number;
  totalPrice: number;
  remainingAmount: number;
  quotedAmount: number;
  deliveredAmount: number;
  taxInvoiceIssued: boolean;
  quoteGroup: string;
  quoteGroupLabel: string;
  notes: string;
};

export type FollowupQuoteOption = {
  id: number;
  optionId: string;
  scheduleId: number;
  quoteGroup: string;
  quoteGroupLabel: string;
  quoteDate: string;
  expectedRevenue: number;
  quotedAmount: number;
  deliveredAmount: number;
  remainingAmount: number;
  deliveryStatus: string;
  deliveryStatusLabel: string;
  hasPartialDelivery: boolean;
  customerName: string;
  companyName: string;
  departmentName: string;
  href: string;
  djangoHref: string;
  items: FollowupQuoteItem[];
};

export type FollowupQuoteItemsData = {
  success?: boolean;
  error?: string;
  quotes: FollowupQuoteOption[];
  count: number;
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
  is_active?: boolean;
  isActive?: boolean;
  is_promo?: boolean;
  isPromo?: boolean;
  quoteCount?: number;
  deliveryCount?: number;
  createdBy?: string;
  createdAt?: string | null;
  updatedAt?: string | null;
  djangoEditHref?: string;
};

type ProductsApiResponse = {
  products?: ProductApiItem[];
  count?: number;
  totalCount?: number;
  hasMore?: boolean;
  success?: boolean;
  error?: string;
  message?: string;
};

export type ProductManagementItem = ProductOption & {
  product_code: string;
  standard_price: number;
  current_price: number;
  is_active: boolean;
  isActive: boolean;
  is_promo: boolean;
  isPromo: boolean;
  quoteCount: number;
  deliveryCount: number;
  createdBy: string;
  createdAt: string | null;
  updatedAt: string | null;
  djangoEditHref: string;
};

export type ProductManagementData = {
  success: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    canManage: boolean;
    label: string;
  };
  metrics: {
    totalProducts: number;
    activeProducts: number;
    inactiveProducts: number;
    filteredProducts: number;
  };
  products: ProductManagementItem[];
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalCount: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  links: {
    djangoList: string;
    excelDownload: string;
    bulkUpsert: string;
    bulkDelete: string;
    save: string;
  };
};

export type ProductMutationPayload = {
  productCode: string;
  description: string;
  specification: string;
  unit: string;
  standardPrice: number | string;
  isActive: boolean;
};

export type ProductSaveResult = {
  success: boolean;
  created: boolean;
  updated: boolean;
  changedFields: string[];
  product: ProductManagementItem;
  message: string;
};

export type ProductDeleteReference = {
  referenceType: 'deliveryItem' | 'quoteItem' | string;
  referenceId: number;
  itemName: string;
  quantity: number;
  unit: string;
  unitPrice: number;
  quoteGroup?: string;
  quoteGroupLabel?: string;
  scheduleId?: number | null;
  historyId?: number | null;
  scheduleType?: string;
  scheduleTypeLabel?: string;
  scheduleDate?: string;
  quoteId?: number | null;
  quoteNumber?: string;
  customerName?: string;
  companyName?: string;
  departmentName?: string;
};

export type ProductBulkResultRow = {
  row?: number;
  productCode: string;
  status: 'created' | 'updated' | 'unchanged' | 'deleted' | 'blocked' | 'missing' | 'error';
  changedFields?: string[];
  canReplace?: boolean;
  deliveryItemCount?: number;
  quoteItemCount?: number;
  referenceCount?: number;
  references?: ProductDeleteReference[];
  hasMoreReferences?: boolean;
  replacementProductId?: number;
  replacementProductCode?: string;
  replacedCount?: number;
  message?: string;
  error?: string;
};

export type ProductReplaceReferenceResult = {
  success: boolean;
  productCode: string;
  deletedOriginal: boolean;
  replacementProductId: number;
  replacementProductCode: string;
  replacedReference?: ProductDeleteReference;
  result: ProductBulkResultRow;
  message: string;
  error?: string;
};

export type ProductBulkUpsertResult = {
  success: boolean;
  createdCount: number;
  updatedCount: number;
  unchangedCount: number;
  errorCount: number;
  results: ProductBulkResultRow[];
  message: string;
  error?: string;
};

export type ProductBulkDeleteResult = {
  success: boolean;
  deletedCount: number;
  blockedCount: number;
  missingCount: number;
  replacedCount?: number;
  results: ProductBulkResultRow[];
  message: string;
  error?: string;
};

const emptyProductManagementData: ProductManagementData = {
  success: false,
  source: 'unavailable',
  scope: {
    canManage: false,
    label: '',
  },
  metrics: {
    totalProducts: 0,
    activeProducts: 0,
    inactiveProducts: 0,
    filteredProducts: 0,
  },
  products: [],
  pagination: {
    page: 1,
    pageSize: 50,
    totalPages: 1,
    totalCount: 0,
    hasNext: false,
    hasPrevious: false,
  },
  links: {
    djangoList: '/reporting/products/',
    excelDownload: '/reporting/api/products/export.xlsx',
    bulkUpsert: '/reporting/api/products/bulk-upsert/',
    bulkDelete: '/reporting/api/products/bulk-delete/',
    save: '/reporting/api/products/save/',
  },
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
    reactAccount: string;
    reactCustomer: string;
    djangoList: string;
    djangoCustomer: string;
    djangoExcel: string;
    accountDetail: string;
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
  quoteExtraNotes: string;
  quoteGroupNotes: Array<{
    quoteGroup: string;
    quoteGroupLabel: string;
    notes: string;
  }>;
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
  quoteGroup?: string;
  quoteGroupLabel?: string;
  itemCount?: number;
  totalAmount?: number;
  formats: ScheduleDocumentFormatAction[];
};

export type ScheduleGeneratedDocument = {
  id: number;
  filename: string;
  size: string;
  fileSize: number;
  transactionNumber: string;
  documentType: string;
  documentTypeLabel: string;
  outputFormat: string;
  outputFormatLabel: string;
  quoteGroup: string;
  quoteGroupLabel: string;
  createdAt: string | null;
  createdBy: string;
  downloadHref: string;
  deleteHref?: string;
  canDelete?: boolean;
};

export type ScheduleDocumentsData = {
  canGenerate: boolean;
  templateManagerHref: string;
  djangoTemplateManagerHref?: string;
  registeredDocuments: ScheduleGeneratedDocument[];
  registeredDocumentCount: number;
  registeredQuotations: ScheduleGeneratedDocument[];
  registeredQuotationCount: number;
  autoAttachLabel: string;
  items: ScheduleDocumentAction[];
};

export type ScheduleCommercialWarning = {
  code: string;
  severity: 'info' | 'warning' | 'error' | string;
  message: string;
  context?: Record<string, string | number | boolean | null | undefined>;
};

export type ScheduleCommercialQuoteGroup = {
  quoteGroup: string;
  quoteGroupLabel: string;
  itemCount: number;
  quoteAmount: number;
  deliveredAmount: number;
  remainingAmount: number;
  registeredQuotationCount: number;
  templateCount: number;
  autoAttachStatus: string;
  autoAttachLabel: string;
  fulfillmentStatus: string;
  fulfillmentLabel: string;
  status: string;
  statusLabel: string;
  warnings: ScheduleCommercialWarning[];
};

export type ScheduleCommercialSourceQuote = {
  sourceQuoteScheduleId: number;
  quoteGroup: string;
  quoteGroupLabel: string;
  itemCount: number;
  amount: number;
};

export type ScheduleCommercialHistoryMismatch = {
  historyId: number;
  noteAmount: number;
  itemAmount: number;
  createdAt: string | null;
};

export type ScheduleCommercialChecks = {
  applies: boolean;
  kind: string;
  status: string;
  statusLabel: string;
  summary: {
    quoteGroupCount: number;
    quoteItemCount: number;
    quoteAmount: number;
    deliveredAmount: number;
    remainingAmount: number;
    deliveryItemCount: number;
    deliveryAmount: number;
    registeredDocumentCount: number;
    registeredQuotationCount: number;
    autoAttachReady: boolean;
    emailThreadCount: number;
    warningCount: number;
  };
  quoteGroups: ScheduleCommercialQuoteGroup[];
  delivery: {
    itemCount: number;
    totalAmount: number;
    sourceQuoteCount: number;
    sourceQuoteItemCount: number;
    historyAmountMismatches: ScheduleCommercialHistoryMismatch[];
    sourceQuotes: ScheduleCommercialSourceQuote[];
    registeredStatementCount?: number;
    templateCount?: number;
    autoAttachStatus?: string;
    autoAttachLabel?: string;
  };
  documents: {
    registeredDocumentCount: number;
    registeredQuotationCount: number;
    autoAttachLabel: string;
  };
  warnings: ScheduleCommercialWarning[];
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
    quoteGroup?: string;
    quoteGroupLabel?: string;
  };
  items: Array<{
    index: number;
    name: string;
    quantity: number;
    unit: string;
    unitPrice: number;
    baseUnitPrice: number;
    discountRate: number;
    discountUnitPrice: number | null;
    quoteGroup?: string;
    quoteGroupLabel?: string;
    notes: string;
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

export type DocumentTemplateVariableItem = {
  key: string;
  token: string;
  display: string;
};

export type DocumentTemplateVariableGroup = {
  label: string;
  variables: DocumentTemplateVariableItem[];
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
  quoteGroup?: string;
  quoteGroupLabel?: string;
  filename?: string;
  fileSize?: number;
  downloadHref?: string;
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
  templateVariableGroups: DocumentTemplateVariableGroup[];
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

export type PersonalSchedulePayload = {
  title: string;
  content?: string;
  scheduleDate: string;
  scheduleTime: string;
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
    personalSchedule?: {
      canCreate: boolean;
      message: string;
      submitUrl: string;
      djangoUrl: string;
    };
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
    personalSchedule?: {
      canCreate: boolean;
      message: string;
      submitUrl: string;
      djangoUrl: string;
    };
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
    djangoCreateNote?: string;
    deleteSchedule: string;
    uploadFiles: string;
    updateDeliveryItems: string;
    prepayments: string;
    sendMail: string;
    djangoSendMail: string;
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
  ai: {
    canUseAi: boolean;
    message: string;
  };
  relatedNotes: NoteItem[];
  deliveryItems: ScheduleDeliveryItem[];
  documents: ScheduleDocumentsData;
  commercialChecks?: ScheduleCommercialChecks;
};

export type ScheduleEditResponse = ScheduleDetailData & {
  success: boolean;
  error?: string;
  message?: string;
};

export type ScheduleDeliveryItemsUpdateResponse = ScheduleDetailData & {
  success: boolean;
  error?: string;
  completedQuoteScheduleIds?: number[];
  message?: string;
};

export type ScheduleFileActionResponse = {
  success: boolean;
  error?: string;
  message?: string;
  files?: ScheduleFileItem[];
};

export type ScheduleDeleteResponse = {
  success: boolean;
  error?: string;
  message?: string;
};

export type PersonalScheduleDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  schedule: ScheduleItem | null;
  links: {
    calendar: string;
    djangoCalendar: string;
    djangoDetail: string;
    djangoEdit: string;
    deleteSchedule: string;
  };
  edit: {
    canEdit: boolean;
    message: string;
    submitUrl: string;
    djangoUrl: string;
  };
};

export type PersonalScheduleMutationResponse = PersonalScheduleDetailData & {
  success: boolean;
  scheduleId?: number;
  href?: string;
};

export type AIWorkspaceDepartment = {
  id: number;
  name: string;
  company: string;
  customerCount: number;
  customerPreview: string[];
  searchText?: string;
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

export type AIWorkspaceDraftType = 'email' | 'note' | 'questions' | 'weekly_report';

export type AIWorkspaceActionKind =
  | 'quote_followup'
  | 'delivery_risk'
  | 'service_case'
  | 'calibration_due'
  | 'email_waiting'
  | 'painpoint_validation'
  | 'customer_followup'
  | 'weekly_report'
  | 'data_quality';

export type AIWorkspaceActionEvidence = {
  label: string;
  value: string;
  href?: string;
};

export type AIWorkspaceActionFeedback = {
  status: 'answered' | 'next_action' | 'resolved' | 'dismissed';
  statusLabel: string;
  intent:
    | 'resolved_no_purchase'
    | 'follow_up_needed'
    | 'positive_buying_signal'
    | 'email_waiting'
    | 'needs_human_review'
    | string;
  intentLabel: string;
  feedback: string;
  summary: string;
  nextAction: string;
  nextActionDate: string | null;
  reason: string;
  decision: string;
  source: 'openai' | 'fallback' | '';
  issueFollowups: Array<{
    key: string;
    kind: string;
    issue: string;
    priority: string;
    isPrimary?: boolean;
    nextAction: string;
    nextActionDate: string | null;
  }>;
  crmSync: {
    intent: string;
    intentLabel: string;
    applied: boolean;
    message: string;
    changes: Array<{
      label: string;
      objectType: string;
      objectId: number | string | null;
      href: string;
      detail: string;
    }>;
    taskHistoryId: number | null;
    taskHistoryHref: string;
    issueTaskHistories: Array<{
      key: string;
      kind: string;
      issue: string;
      priority: string;
      historyId: number;
      historyHref: string;
      nextAction: string;
      nextActionDate: string | null;
    }>;
  };
  updatedAt: string | null;
  historyId: number | null;
  historyHref: string;
};

export type AIWorkspaceAction = {
  id: string;
  kind: AIWorkspaceActionKind;
  kindLabel: string;
  priorityScore: number;
  priorityLabel: string;
  title: string;
  followupId: number | null;
  customer: string;
  company: string;
  department: string;
  moneyImpact: number | null;
  dueDate: string | null;
  evidence: AIWorkspaceActionEvidence[];
  recommendedAction: string;
  draftTypes: AIWorkspaceDraftType[];
  feedback: AIWorkspaceActionFeedback | null;
  hrefs: {
    customer?: string;
    schedule?: string;
    note?: string;
    report?: string;
    assets?: string;
    ai?: string;
    aiHub?: string;
    mailboxThread?: string;
    weeklyAiDraft?: string;
    djangoCustomer?: string;
    djangoSchedule?: string;
    djangoNote?: string;
    djangoMailboxThread?: string;
  };
};

export type AIWorkspaceDailyBrief = {
  summary: string;
  focusDate: string;
  weekStart: string;
  weekEnd: string;
  counts: {
    totalActions: number;
    urgentActions: number;
    quoteFollowups: number;
    deliveryRisks: number;
    serviceCases: number;
    calibrationDue: number;
    emailWaiting: number;
    painpointValidations: number;
    customerFollowups: number;
    weeklyReports: number;
  };
  risks: Array<{
    title: string;
    kindLabel: string;
    priorityLabel: string;
  }>;
  opportunities: Array<{
    title: string;
    kindLabel: string;
    moneyImpact: number | null;
  }>;
  suggestedFocus: string[];
};

export type AIWorkspaceActionDraftResponse = {
  success?: boolean;
  source: 'openai' | 'fallback';
  generatedAt: string;
  action: AIWorkspaceAction;
  draftType: AIWorkspaceDraftType;
  draft: {
    subject: string;
    body: string;
    bullets: string[];
  };
  evidence: AIWorkspaceActionEvidence[];
  requiresHumanApproval: boolean;
  error?: string;
  message?: string;
};

export type AIWorkspaceActionFeedbackResponse = {
  success?: boolean;
  source: 'openai' | 'fallback';
  generatedAt: string;
  actionId: string;
  action: AIWorkspaceAction;
  feedback: AIWorkspaceActionFeedback;
  history: {
    id: number | null;
    href: string;
  };
  crmSync: AIWorkspaceActionFeedback['crmSync'];
  hidden: boolean;
  error?: string;
  message?: string;
};

export type AIWorkspaceQuestionModel = 'gpt-5.4-mini';

export type AIWorkspaceQuestionScope = 'department' | 'all';

export type AIWorkspaceQuestionModelChoice = {
  id: AIWorkspaceQuestionModel | string;
  label: string;
};

export type AIWorkspaceQuestionAnswer = {
  summary: string;
  bullets: string[];
  decision?: {
    recommendedChoice?: string;
    rejectedChoice?: string;
    reason?: string;
    exception?: string;
  };
  perspective?: {
    customerPerspective?: string;
    salesJudgment?: string;
    recommendedApproach?: string;
    talkTrack?: string;
    caution?: string;
  };
  evidence: AIWorkspaceActionEvidence[];
  actionItems?: {
    rank: number;
    title: string;
    customer: string;
    company: string;
    department: string;
    priority: string;
    reason: string;
    nextAction: string;
    timing: string;
    crmEvidence: AIWorkspaceActionEvidence[];
  }[];
  confidence: 'high' | 'medium' | 'low' | string;
};

export type AIWorkspaceQuestionLog = {
  id: number;
  scopeType: 'all' | 'department' | string;
  question: string;
  answerSummary: string;
  answer?: AIWorkspaceQuestionAnswer | Record<string, unknown>;
  decision?: AIWorkspaceQuestionAnswer['decision'] | null;
  perspective?: AIWorkspaceQuestionAnswer['perspective'] | null;
  source: string;
  model: string;
  modelLabel: string;
  webSearchUsed: boolean;
  department: {
    id: number;
    name: string;
    company: string;
  } | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type AIWorkspaceQuestionHistory = {
  scopeType: AIWorkspaceQuestionScope | string;
  departmentId: number | null;
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  items: AIWorkspaceQuestionLog[];
};

export type AIWorkspaceDepartmentQuestionResponse = {
  success?: boolean;
  source: 'openai' | 'fallback';
  model?: string;
  modelLabel?: string;
  webSearchUsed?: boolean;
  generatedAt: string;
  scope?: {
    type?: string;
    label?: string;
    departmentId?: number | null;
  };
  department: {
    id: number;
    name: string;
    company: string;
  } | null;
  question: string;
  answer: AIWorkspaceQuestionAnswer;
  questionLog?: AIWorkspaceQuestionLog;
  context: {
    customerCount: number;
    departmentCount?: number;
    summary: Record<string, number | string | null>;
    lastDelivery: {
      date: string;
      customer: string;
      amount: number;
      amountLabel: string;
      items: string;
      source: string;
      scheduleId: number | null;
      notes: string;
    } | null;
    recommendedActionCount?: number;
    recentFeedbackCount?: number;
    questionFeedbackCount?: number;
    verifiedMemoryCount?: number;
    recentQuestionLogCount?: number;
  };
  requiresHumanReview: boolean;
  error?: string;
  message?: string;
};

export type ScheduleAICoach = {
  summary: string;
  priority: 'high' | 'medium' | 'low' | string;
  talkTrack: string[];
  checklist: string[];
  risks: Array<{
    level: 'high' | 'medium' | 'low' | string;
    label: string;
    value: string;
  }>;
  recommendedNextAction: string;
  afterMeetingNoteDraft: {
    actionType: string;
    content: string;
    nextAction: string;
  };
  mailDraft: {
    subject: string;
    body: string;
  };
  evidence: AIWorkspaceActionEvidence[];
  confidence: 'high' | 'medium' | 'low' | string;
};

export type ScheduleAICoachResponse = {
  success?: boolean;
  source: 'openai' | 'fallback';
  model?: string;
  modelLabel?: string;
  generatedAt: string;
  scope?: {
    type?: string;
    label?: string;
    scheduleId?: number;
    followupId?: number | null;
    departmentId?: number | null;
  };
  coach: ScheduleAICoach;
  context: {
    scheduleId: number;
    followupId: number | null;
    departmentId: number | null;
    recentNoteCount: number;
    recentEmailCount: number;
    deliveryItemCount: number;
    stored: boolean;
  };
  requiresHumanReview: boolean;
  error?: string;
  message?: string;
};

export type AIWorkspaceQuestionFeedbackRating = 'helpful' | 'needs_style' | 'incorrect';

export type AIWorkspaceQuestionFeedbackPayload = {
  departmentId?: number | null;
  scopeType?: 'all' | 'department';
  question: string;
  answer: AIWorkspaceQuestionAnswer;
  source?: AIWorkspaceDepartmentQuestionResponse['source'];
  rating: AIWorkspaceQuestionFeedbackRating;
  comment?: string;
};

export type AIWorkspaceQuestionFeedbackResponse = {
  success?: boolean;
  generatedAt: string;
  feedback: {
    id: number;
    scopeType: 'all' | 'department' | string;
    rating: AIWorkspaceQuestionFeedbackRating | string;
    ratingLabel: string;
    comment: string;
    question: string;
    answerSummary: string;
    source: string;
    department: {
      id: number;
      name: string;
      company: string;
    } | null;
    createdAt: string | null;
    updatedAt: string | null;
  };
  error?: string;
  message?: string;
};

export type AIWorkspaceMemoryType = 'fact' | 'correction' | 'preference';

export type AIWorkspaceMemoryPayload = {
  departmentId?: number | null;
  scopeType?: 'all' | 'department';
  questionLogId?: number | null;
  feedbackId?: number | null;
  memoryType: AIWorkspaceMemoryType;
  title?: string;
  content: string;
};

export type AIWorkspaceMemoryItem = {
  id: number;
  scopeType: 'all' | 'department' | string;
  memoryType: AIWorkspaceMemoryType | string;
  memoryTypeLabel: string;
  title: string;
  content: string;
  isActive: boolean;
  department: {
    id: number;
    name: string;
    company: string;
  } | null;
  sourceQuestionLogId: number | null;
  sourceQuestion: string;
  createdAt: string | null;
  updatedAt: string | null;
};

export type AIWorkspaceMemoryResponse = {
  success?: boolean;
  generatedAt: string;
  source?: 'django';
  memory: AIWorkspaceMemoryItem;
  error?: string;
  message?: string;
};

export type AIWorkspaceMemoryFilters = {
  status?: 'active' | 'inactive' | 'all';
  scope?: 'any' | 'department' | 'all';
  memoryType?: '' | AIWorkspaceMemoryType;
  departmentId?: number | null;
  q?: string;
  page?: number;
};

export type AIWorkspaceMemoriesData = {
  success?: boolean;
  source: 'django';
  generatedAt: string;
  filters: {
    status: 'active' | 'inactive' | 'all';
    scope: 'any' | 'department' | 'all';
    memoryType: '' | AIWorkspaceMemoryType | string;
    departmentId: number | null;
    q: string;
    page: number;
  };
  counts: {
    total: number;
    active: number;
    inactive: number;
    department: number;
    all: number;
    filtered: number;
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  memories: AIWorkspaceMemoryItem[];
  error?: string;
  message?: string;
};

export type AIWorkspaceFeedbackKindSummary = {
  kind: AIWorkspaceActionKind | string;
  kindLabel: string;
  count: number;
};

export type AIWorkspaceFeedbackHistoryItem = {
  id: number;
  actionId: string;
  kind: AIWorkspaceActionKind | string;
  kindLabel: string;
  status: 'answered' | 'next_action' | 'resolved' | 'dismissed';
  statusLabel: string;
  title: string;
  owner: string;
  ownerId: number | null;
  customer: string;
  company: string;
  department: string;
  customerHref: string;
  djangoCustomerHref: string;
  feedback: string;
  summary: string;
  nextAction: string;
  nextActionDate: string | null;
  reason: string;
  issueFollowups: AIWorkspaceActionFeedback['issueFollowups'];
  source: 'openai' | 'fallback' | '';
  historyId: number | null;
  historyHref: string;
  updatedAt: string | null;
  createdAt: string | null;
};

export type AIWorkspaceFeedbackHistory = {
  scope: {
    label: string;
    userCount: number;
    canViewAll: boolean;
    selectedUserId: number | null;
    departmentId?: number | null;
    departmentName?: string;
  };
  stats: {
    total: number;
    recent30Days: number;
    answered: number;
    nextActions: number;
    resolved: number;
    dismissed: number;
    linkedNotes: number;
    hideRate: number;
    nextActionRate: number;
  };
  byKind: AIWorkspaceFeedbackKindSummary[];
  recent: AIWorkspaceFeedbackHistoryItem[];
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
  dailyBrief: AIWorkspaceDailyBrief;
  actionQueue: AIWorkspaceAction[];
  feedbackHistory: AIWorkspaceFeedbackHistory;
  departments: AIWorkspaceDepartment[];
  featuredDepartment: AIWorkspaceFeaturedDepartment | null;
  selectedDepartmentId: number | null;
  questionHistory: AIWorkspaceQuestionHistory;
  questionModelChoices: AIWorkspaceQuestionModelChoice[];
  defaultQuestionModel: AIWorkspaceQuestionModel | string;
  recentDepartmentAnalyses: AIWorkspaceAnalysis[];
  painpoints: AIWorkspacePainpoint[];
  followupTargets: AIWorkspaceFollowupTarget[];
  recentFollowupAnalyses: AIWorkspaceAnalysis[];
  promptTargets: AIWorkspacePromptTarget[];
  recommendedGoals: Array<{
    title: string;
    description: string;
    reason: string;
    customer?: string;
    priority?: string;
    priorityLabel?: string;
    source?: string;
    sourceLabel?: string;
    updatedAt?: string | null;
  }>;
};

export type AIWorkspaceLoadParams = {
  departmentId?: number | null;
  questionPage?: number;
  questionScope?: AIWorkspaceQuestionScope;
};

export type AIWorkspaceQuestionLogDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt: string;
  questionLog: AIWorkspaceQuestionLog | null;
  links: {
    aiWorkspace: string;
  };
  error?: string;
  message?: string;
};

export type AIWorkspaceQuestionLogDeleteResponse = {
  success?: boolean;
  source: 'django';
  deletedId: number;
  message?: string;
  links?: {
    aiWorkspace?: string;
  };
  error?: string;
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

export type NavigationItem = {
  id: string;
  label: string;
  href: string;
};

export type NavigationData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  currentUser: {
    id: number | null;
    name: string;
    username: string;
    role: string;
    roleLabel: string;
    company: string;
    canUseAi: boolean;
  };
  capabilities: {
    canManageTasks: boolean;
    canUseAi: boolean;
    canUseMailbox: boolean;
    canViewAllUsers: boolean;
  };
  items: NavigationItem[];
};

export type TaskUser = {
  id: number;
  name: string;
  username: string;
  role: string;
  roleLabel: string;
  company: string;
};

export type TaskCustomer = {
  id: number;
  customer: string;
  company: string;
  department: string;
  owner: string;
  href: string;
  djangoHref: string;
};

export type TaskItem = {
  id: number;
  title: string;
  description: string;
  status: string;
  statusLabel: string;
  sourceType: string;
  sourceLabel: string;
  dueDate: string | null;
  completedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  isOverdue: boolean;
  expectedDuration: number | null;
  expectedDurationLabel: string;
  category: {
    id: number | null;
    name: string;
    color: string;
  } | null;
  createdBy: TaskUser | null;
  assignedTo: TaskUser | null;
  requestedBy: TaskUser | null;
  relatedClient: TaskCustomer | null;
  canApprove: boolean;
  canReject: boolean;
  canChangeStatus: boolean;
  canComplete: boolean;
  canSetOngoing: boolean;
  canSetOnHold: boolean;
  canUpdate?: boolean;
  canDelete?: boolean;
  canUploadAttachment?: boolean;
  attachmentCount?: number;
  logCount?: number;
  detailHref?: string;
  statusHref: string;
  updateHref?: string;
  deleteHref?: string;
  uploadHref?: string;
  djangoHref: string;
};

export type TaskAttachment = {
  id: number;
  filename: string;
  fileSize: number;
  uploadedAt: string | null;
  uploadedBy: TaskUser | null;
  downloadHref: string;
};

export type TaskLog = {
  id: number;
  actionType: string;
  actionLabel: string;
  actor: TaskUser | null;
  message: string;
  prevStatus: string;
  newStatus: string;
  createdAt: string | null;
};

export type TaskFormPayload = {
  title: string;
  description?: string;
  dueDate?: string;
  expectedDuration?: string;
  relatedClientId?: string;
};

export type TaskRequestPayload = TaskFormPayload & {
  assignedToId: string;
};

export type TaskManagerAssignPayload = TaskFormPayload & {
  assignedToIds: string[];
};

export type TasksData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  currentUser: TaskUser | null;
  scope: {
    label: string;
    canManage: boolean;
  };
  filters: {
    status: string;
  };
  metrics: {
    myActive: number;
    receivedActive: number;
    requestedActive: number;
    overdue: number;
    done: number;
  };
  options: {
    statuses: Array<{ value: string; label: string }>;
    statusFilters: Array<{ value: string; label: string }>;
    durations: Array<{ value: number; label: string }>;
    assignees: TaskUser[];
  };
  links: {
    createApi: string;
    requestApi: string;
    assigneesApi: string;
    customersApi: string;
    managerApi: string;
    djangoList: string;
    djangoCreate: string;
  };
  tasks: {
    my: TaskItem[];
    received: TaskItem[];
    requested: TaskItem[];
  };
};

export type TaskManagerData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  scope: {
    label: string;
    canManage: boolean;
  };
  filters: {
    status: string;
    assignee: string;
  };
  metrics: {
    total: number;
    active: number;
    done: number;
    overdue: number;
  };
  options: TasksData['options'] & {
    teamMembers: TaskUser[];
  };
  links: {
    assignApi: string;
    customersApi: string;
    djangoManager: string;
  };
  teamSummary: Array<{
    user: TaskUser;
    total: number;
    active: number;
    done: number;
    overdue: number;
  }>;
  tasks: TaskItem[];
};

export type TaskMutationResponse = {
  success?: boolean;
  source?: 'django';
  message?: string;
  error?: string;
  href?: string;
  task?: TaskItem;
  tasks?: TaskItem[];
};

export type TaskDetailData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  task: TaskItem | null;
  attachments: TaskAttachment[];
  logs: TaskLog[];
  options: TasksData['options'];
  links: {
    list: string;
    manager: string;
    djangoDetail: string;
  };
};

const emptyDashboardData: DashboardData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  canManage: false,
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
    yearRevenue: 0,
    quarterRevenue: 0,
    monthlyRevenue: 0,
  },
  revenuePeriod: {
    year: new Date().getFullYear(),
    quarter: Math.floor(new Date().getMonth() / 3) + 1,
    yearStart: '',
    yearEnd: '',
    quarterStart: '',
    quarterEnd: '',
    monthStart: '',
    monthEnd: '',
  },
  links: {
    operationalDashboard: '/dashboard/',
    createNote: '/notes/?create=1',
    customers: '/customers/',
    customerReport: '/customers/',
    notes: '/notes/',
    schedules: '/schedules/',
    calendar: '/schedules/calendar/',
    pipeline: '/pipeline/',
    weeklyReports: '/weekly-reports/',
    pendingReviews: '/notes/?review=unreviewed',
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

const emptyAccountCleanupPreviewAccount: AccountCleanupPreviewAccount = {
  id: null,
  name: '',
  companyId: null,
  companyName: '',
  href: '',
  djangoHref: '',
  metrics: {
    contactCount: 0,
    recordCount: 0,
    scheduleCount: 0,
    deliveryCount: 0,
    quoteCount: 0,
    quoteAmount: 0,
    historyCount: 0,
    prepaymentCount: 0,
    prepaymentAmount: 0,
    prepaymentBalance: 0,
    prepaymentUsageCount: 0,
    prepaymentUsedAmount: 0,
    assetCount: 0,
    serviceCaseCount: 0,
    calibrationCount: 0,
  },
  affectedRecords: [],
  contacts: [],
};

const emptyAccountCleanupPreviewData: AccountCleanupPreviewData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  mode: 'source',
  sourceAccount: emptyAccountCleanupPreviewAccount,
  targetAccount: null,
  combined: {
    metrics: emptyAccountCleanupPreviewAccount.metrics,
    description: '',
  },
  warnings: [],
  links: {
    sourceAccount: '',
    reports: '/reports/',
  },
};

const emptyAccountCleanupSearchResult = {
  results: [] as AccountCleanupSearchResult[],
};

const emptyReportsData: ReportsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  filters: {
    dateFrom: '',
    dateTo: '',
    selectedUserId: null,
  },
  scope: {
    canFilterUsers: false,
    canExport: false,
    label: '',
    salespeople: [],
  },
  metrics: {
    totalHistories: 0,
    completedFollowups: 0,
    overdueFollowups: 0,
    upcomingFollowups: 0,
    activePipeline: 0,
    totalAssets: 0,
    activeAssets: 0,
    openServiceAssets: 0,
    overdueServiceAssets: 0,
    dueCalibrationAssets: 0,
    overdueCalibrationAssets: 0,
  },
  activityReport: [],
  customerReport: [],
  customerOperations: {
    metrics: {
      totalCustomers: 0,
      customersWithDeliveries: 0,
      deliveryCount: 0,
      deliveryAmount: 0,
      normalDeliveryCount: 0,
      normalDeliveryAmount: 0,
      prepaymentDeliveryCount: 0,
      prepaymentDeliveryAmount: 0,
      prepaymentUsedAmount: 0,
      quoteCount: 0,
      quoteAmount: 0,
      serviceCount: 0,
      openServiceCount: 0,
      prepaymentCount: 0,
      prepaymentAmount: 0,
      prepaymentBalance: 0,
      prepaymentUsedTotal: 0,
    },
    rows: [],
  },
  dataQuality: {
    metrics: {
      duplicateAccountGroups: 0,
      duplicateContactGroups: 0,
      contactsWithoutDepartment: 0,
      contactsWithoutCompany: 0,
      cleanupCandidateCount: 0,
    },
    normalizationRule: '',
    duplicateAccounts: [],
    duplicateContacts: [],
    contactsWithoutDepartment: [],
    contactsWithoutCompany: [],
  },
  pipelineSummary: [],
  links: {
    activityCsv: '/reporting/analytics/export/activity.csv',
    pipelineCsv: '/reporting/analytics/export/pipeline.csv',
    activityXlsx: '/reporting/analytics/export/activity.xlsx',
    pipelineXlsx: '/reporting/analytics/export/pipeline.xlsx',
    customerOperationsXlsx: '/reporting/api/reports/customer-operations.xlsx',
    assets: '/assets/',
    legacy: '/reporting/analytics/',
  },
};

const emptyProfileData: ProfileData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  user: {
    id: null,
    username: '',
    firstName: '',
    lastName: '',
    fullName: '',
    email: '',
    dateJoined: null,
    lastLogin: null,
  },
  profile: {
    role: '',
    roleLabel: '',
    company: '',
    canUseAi: false,
    canDownloadExcel: false,
  },
  emailConnection: {
    enabled: false,
    connected: false,
    provider: '',
    providerLabel: '',
    address: '',
    connectedAt: null,
    lastSyncAt: null,
    gmailConnected: false,
    imapConnected: false,
    links: {
      mailbox: '/mailbox/',
      businessCards: '/mailbox/business-cards/',
      gmailConnect: '/reporting/gmail/connect/',
      imapConnect: '/reporting/imap/connect/',
      imapSync: '/reporting/imap/sync/',
      disconnect: '/reporting/api/profile/email/disconnect/',
    },
  },
  links: {
    update: '/reporting/api/profile/update/',
    password: '/reporting/api/profile/password/',
    legacy: '/reporting/profile/',
    legacyEdit: '/reporting/profile/edit/',
    dashboard: '/dashboard/',
  },
};

const emptyBusinessCardsData: BusinessCardsData = {
  success: false,
  source: 'unavailable',
  cards: [],
  links: {
    create: '/reporting/api/business-cards/create/',
    legacy: '/reporting/business-cards/',
    mailbox: '/mailbox/',
    profile: '/profile/',
  },
};

const emptyMailboxCreateOptions: MailboxCreateOptions = {
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
    scheduled: 0,
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
    scheduled: '/mailbox/?box=scheduled',
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
    totalAccounts: 0,
    filteredAccounts: 0,
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
    customers: '/customers/',
    companies: '/reporting/companies/',
    customerReport: '/customers/',
    createNote: '/notes/?create=1',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/followups/create/',
    companySubmitUrl: '/reporting/api/companies/create/',
    departmentSubmitUrl: '/reporting/api/departments/create/',
    advancedUrl: '/customers/?create=1',
    priorities: [],
    companies: [],
    departments: [],
  },
  customers: [],
  accounts: [],
  priorityCustomers: [],
  priorityAccounts: [],
};

const emptyCustomerAiDepartment: CustomerAiDepartment = {
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
  recommendedQuestions: [],
  painpoints: [],
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
  account: {
    id: null,
    type: '',
    name: '',
    companyId: null,
    companyName: '',
    departmentId: null,
    departmentName: '',
    representativeCustomerId: null,
    representativeName: '',
    contactCount: 0,
    ledgerScopeLabel: '',
    ledgerScopeDescription: '',
    contacts: [],
    href: '',
    djangoRepresentativeHref: '',
  },
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
    deliveryRecordsXlsx: '',
    accountDetail: '',
    accountDeliveryRecordsXlsx: '',
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
      accountPrepayments: '',
      customerPrepayments: '',
      djangoCustomerPrepayments: '',
    },
    recentPrepayments: [],
  },
  operationalRecords: {
    metrics: {
      serviceRecords: 0,
      quoteRecords: 0,
      deliveryRecords: 0,
      prepaymentDeliveryRecords: 0,
      normalDeliveryRecords: 0,
      prepaymentRecords: 0,
      deliveryAmount: 0,
      prepaymentDeliveryAmount: 0,
      normalDeliveryAmount: 0,
      prepaymentUsedAmount: 0,
    },
    serviceRecords: [],
    quoteRecords: [],
    deliveryRecords: [],
    prepaymentRecords: [],
  },
  assetSummary: {
    canManage: false,
    message: '',
    metrics: {
      assetCount: 0,
      activeAssetCount: 0,
      openServiceCaseCount: 0,
      dueCalibrationCount: 0,
    },
    links: {
      createAsset: '',
      createServiceCase: '',
      createCalibration: '',
    },
    options: {
      assetStatuses: [],
      serviceCaseTypes: [],
      serviceStatuses: [],
      servicePriorities: [],
      calibrationResults: [],
    },
    assets: [],
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

const emptyCustomerAssetDirectoryData: CustomerAssetDirectoryData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  canManage: false,
  scope: {
    label: '',
    userCount: 0,
    canViewAll: false,
    selectedUserId: null,
  },
  filters: {
    q: '',
    status: '',
    owner: '',
    service: '',
    calibration: '',
  },
  options: {
    owners: [],
    assetStatuses: [],
    serviceCaseTypes: [],
    serviceStatuses: [],
    servicePriorities: [],
    calibrationResults: [],
    serviceFilters: [
      { value: 'open', label: '진행 서비스' },
      { value: 'overdue', label: '처리 지연' },
      { value: 'none', label: '서비스 이력 없음' },
    ],
    calibrationFilters: [
      { value: 'due30', label: '30일 내 교정' },
      { value: 'overdue', label: '교정 지연' },
      { value: 'none', label: '교정 이력 없음' },
    ],
  },
  metrics: {
    totalAssets: 0,
    filteredAssets: 0,
    activeAssets: 0,
    openServiceAssets: 0,
    dueCalibrationAssets: 0,
    overdueCalibrationAssets: 0,
    noCalibrationAssets: 0,
    returnedAssets: 0,
    truncated: false,
  },
  links: {
    assets: '/assets/',
    customers: '/customers/',
  },
  create: {
    canCreate: false,
    message: '',
    customers: [],
  },
  workQueue: [],
  assets: [],
};

export function normalizeCustomerAiDepartment(payload?: Partial<CustomerAiDepartment> | null): CustomerAiDepartment {
  return {
    ...emptyCustomerAiDepartment,
    ...(payload ?? {}),
    quoteDelivery: {
      ...emptyCustomerAiDepartment.quoteDelivery,
      ...(payload?.quoteDelivery ?? {}),
      productStats: payload?.quoteDelivery?.productStats ?? emptyCustomerAiDepartment.quoteDelivery.productStats,
      recentDeliveries: payload?.quoteDelivery?.recentDeliveries ?? emptyCustomerAiDepartment.quoteDelivery.recentDeliveries,
    },
    quoteInsights: {
      ...emptyCustomerAiDepartment.quoteInsights,
      ...(payload?.quoteInsights ?? {}),
      stalledQuotes: payload?.quoteInsights?.stalledQuotes ?? emptyCustomerAiDepartment.quoteInsights.stalledQuotes,
    },
    missingInfo: {
      ...emptyCustomerAiDepartment.missingInfo,
      ...(payload?.missingInfo ?? {}),
      items: payload?.missingInfo?.items ?? emptyCustomerAiDepartment.missingInfo.items,
      questions: payload?.missingInfo?.questions ?? emptyCustomerAiDepartment.missingInfo.questions,
    },
    meetingInsights: payload?.meetingInsights ?? emptyCustomerAiDepartment.meetingInsights,
    nextActions: payload?.nextActions ?? emptyCustomerAiDepartment.nextActions,
    verificationInsights: payload?.verificationInsights ?? emptyCustomerAiDepartment.verificationInsights,
    recommendedQuestions: payload?.recommendedQuestions ?? emptyCustomerAiDepartment.recommendedQuestions,
    painpoints: payload?.painpoints ?? emptyCustomerAiDepartment.painpoints,
  };
}

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
    notes: '/notes/',
    unreviewed: '/notes/?review=unreviewed',
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
    createSchedule: '/schedules/?create=1',
    createPersonalSchedule: '/reporting/personal-schedules/create/',
    schedules: '/schedules/',
    djangoSchedules: '/schedules/',
    calendar: '/schedules/calendar/',
    djangoCalendar: '/schedules/calendar/',
    weeklyReports: '/weekly-reports/',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/schedules/create/',
    activityTypes: [],
    customers: [],
    personalSchedule: {
      canCreate: false,
      message: '',
      submitUrl: '/reporting/api/personal-schedules/create/',
      djangoUrl: '/reporting/personal-schedules/create/',
    },
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
    djangoSchedules: '/schedules/',
    calendar: '/schedules/calendar/',
    djangoCalendar: '/schedules/calendar/',
    createSchedule: '/schedules/?create=1',
    createPersonalSchedule: '/reporting/personal-schedules/create/',
    weeklyReports: '/weekly-reports/',
  },
  create: {
    canCreate: false,
    message: '',
    submitUrl: '/reporting/api/schedules/create/',
    activityTypes: [],
    customers: [],
    personalSchedule: {
      canCreate: false,
      message: '',
      submitUrl: '/reporting/api/personal-schedules/create/',
      djangoUrl: '/reporting/personal-schedules/create/',
    },
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
    djangoSchedules: '/schedules/',
    calendar: '/schedules/calendar/',
    djangoDetail: '',
    djangoEdit: '',
    customer: '',
    djangoCustomer: '',
    createNote: '',
    djangoCreateNote: '',
    deleteSchedule: '',
    uploadFiles: '',
    updateDeliveryItems: '',
    prepayments: '',
    sendMail: '',
    djangoSendMail: '',
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
  ai: {
    canUseAi: false,
    message: '',
  },
  relatedNotes: [],
  deliveryItems: [],
  documents: {
    canGenerate: false,
    templateManagerHref: '/documents/',
    djangoTemplateManagerHref: '/reporting/documents/',
    registeredDocuments: [],
    registeredDocumentCount: 0,
    registeredQuotations: [],
    registeredQuotationCount: 0,
    autoAttachLabel: '',
    items: [],
  },
  commercialChecks: {
    applies: false,
    kind: '',
    status: 'info',
    statusLabel: '정보',
    summary: {
      quoteGroupCount: 0,
      quoteItemCount: 0,
      quoteAmount: 0,
      deliveredAmount: 0,
      remainingAmount: 0,
      deliveryItemCount: 0,
      deliveryAmount: 0,
      registeredDocumentCount: 0,
      registeredQuotationCount: 0,
      autoAttachReady: false,
      emailThreadCount: 0,
      warningCount: 0,
    },
    quoteGroups: [],
    delivery: {
      itemCount: 0,
      totalAmount: 0,
      sourceQuoteCount: 0,
      sourceQuoteItemCount: 0,
      historyAmountMismatches: [],
      sourceQuotes: [],
    },
    documents: {
      registeredDocumentCount: 0,
      registeredQuotationCount: 0,
      autoAttachLabel: '',
    },
    warnings: [],
  },
};

const emptyPersonalScheduleDetailData: PersonalScheduleDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  schedule: null,
  links: {
    calendar: '/schedules/calendar/',
    djangoCalendar: '/schedules/calendar/',
    djangoDetail: '',
    djangoEdit: '',
    deleteSchedule: '',
  },
  edit: {
    canEdit: false,
    message: '',
    submitUrl: '',
    djangoUrl: '',
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
  templateVariableGroups: [],
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
    reactAccount: '',
    reactCustomer: '',
    djangoList: '/reporting/prepayment/',
    djangoCustomer: '',
    djangoExcel: '',
    accountDetail: '',
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
    aiHub: '/ai-workspace/',
    weeklyReports: '/weekly-reports/',
    weeklyReportCreate: '/weekly-reports/new/',
    weeklyAiDraft: '/reporting/api/weekly-reports/ai-draft/',
    customers: '/customers/',
    notes: '/notes/',
    dashboard: '/dashboard/',
  },
  week: {
    start: '',
    end: '',
  },
  dailyBrief: {
    summary: '',
    focusDate: '',
    weekStart: '',
    weekEnd: '',
    counts: {
      totalActions: 0,
      urgentActions: 0,
      quoteFollowups: 0,
      deliveryRisks: 0,
      serviceCases: 0,
      calibrationDue: 0,
      emailWaiting: 0,
      painpointValidations: 0,
      customerFollowups: 0,
      weeklyReports: 0,
    },
    risks: [],
    opportunities: [],
    suggestedFocus: [],
  },
  actionQueue: [],
  feedbackHistory: {
    scope: {
      label: '',
      userCount: 0,
      canViewAll: false,
      selectedUserId: null,
    },
    stats: {
      total: 0,
      recent30Days: 0,
      answered: 0,
      nextActions: 0,
      resolved: 0,
      dismissed: 0,
      linkedNotes: 0,
      hideRate: 0,
      nextActionRate: 0,
    },
    byKind: [],
    recent: [],
  },
  departments: [],
  featuredDepartment: null,
  selectedDepartmentId: null,
  questionHistory: {
    scopeType: 'department',
    departmentId: null,
    page: 1,
    pageSize: 5,
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrevious: false,
    items: [],
  },
  questionModelChoices: [
    { id: 'gpt-5.4-mini', label: 'GPT-5.4 mini' },
  ],
  defaultQuestionModel: 'gpt-5.4-mini',
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

const emptyTaskUser: TaskUser = {
  id: 0,
  name: '',
  username: '',
  role: '',
  roleLabel: '',
  company: '',
};

const emptyNavigationData: NavigationData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  currentUser: {
    id: null,
    name: '',
    username: '',
    role: '',
    roleLabel: '',
    company: '',
    canUseAi: false,
  },
  capabilities: {
    canManageTasks: false,
    canUseAi: false,
    canUseMailbox: true,
    canViewAllUsers: false,
  },
  items: [],
};

const emptyTasksLinks: TasksData['links'] = {
  createApi: '/reporting/api/tasks/create/',
  requestApi: '/reporting/api/tasks/request/',
  assigneesApi: '/reporting/api/tasks/assignees/',
  customersApi: '/reporting/api/tasks/customers/',
  managerApi: '/reporting/api/tasks/manager/',
  djangoList: '/todos/',
  djangoCreate: '/todos/create/',
};

const emptyTaskOptions: TasksData['options'] = {
  statuses: [],
  statusFilters: [
    { value: 'active', label: '진행/대기' },
    { value: 'overdue', label: '지연' },
    { value: 'pending', label: '승인 대기' },
    { value: 'ongoing', label: '진행중' },
    { value: 'on_hold', label: '보류' },
    { value: 'done', label: '완료' },
    { value: 'rejected', label: '반려' },
    { value: 'all', label: '전체' },
  ],
  durations: [],
  assignees: [],
};

const emptyTasksData: TasksData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  currentUser: null,
  scope: {
    label: '',
    canManage: false,
  },
  filters: {
    status: 'active',
  },
  metrics: {
    myActive: 0,
    receivedActive: 0,
    requestedActive: 0,
    overdue: 0,
    done: 0,
  },
  options: emptyTaskOptions,
  links: emptyTasksLinks,
  tasks: {
    my: [],
    received: [],
    requested: [],
  },
};

const emptyTaskManagerData: TaskManagerData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  scope: {
    label: '',
    canManage: false,
  },
  filters: {
    status: 'active',
    assignee: '',
  },
  metrics: {
    total: 0,
    active: 0,
    done: 0,
    overdue: 0,
  },
  options: {
    ...emptyTaskOptions,
    teamMembers: [],
  },
  links: {
    assignApi: '/reporting/api/tasks/manager/assign/',
    customersApi: '/reporting/api/tasks/customers/',
    djangoManager: '/todos/manager/',
  },
  teamSummary: [],
  tasks: [],
};

const emptyTaskDetailData: TaskDetailData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  task: null,
  attachments: [],
  logs: [],
  options: emptyTaskOptions,
  links: {
    list: '/tasks/',
    manager: '/tasks/manager/',
    djangoDetail: '/todos/',
  },
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

function buildReactHref(pathname: string, sourceParams: URLSearchParams, options: {
  rename?: Record<string, string>;
  extra?: Record<string, string | number>;
  drop?: string[];
} = {}): string {
  const params = new URLSearchParams();
  const drop = new Set(options.drop ?? []);
  sourceParams.forEach((value, key) => {
    const targetKey = options.rename?.[key] ?? key;
    if (!drop.has(key) && !drop.has(targetKey)) {
      params.append(targetKey, value);
    }
  });
  Object.entries(options.extra ?? {}).forEach(([key, value]) => {
    params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function normalizeCoreCrmHref(href?: string | null): string {
  if (!href) {
    return '';
  }
  let parsed: URL;
  try {
    parsed = new URL(href, window.location.origin);
  } catch {
    return href;
  }

  const pathname = parsed.pathname;
  const params = parsed.searchParams;
  const hash = parsed.hash;
  let match: RegExpMatchArray | null;

  if ((pathname === '/reporting/dashboard/' || pathname === '/reporting/dashboard') && hash === '#dashboardNoteModal') {
    return '/notes/?create=1';
  }
  if (pathname === '/reporting/dashboard/' || pathname === '/reporting/dashboard') {
    return buildReactHref('/dashboard/', params);
  }
  if (pathname === '/reporting/followups/' || pathname === '/reporting/followups') {
    return buildReactHref('/customers/', params, { rename: { pipeline_stage: 'stage' } });
  }
  if (pathname === '/reporting/followups/create/' || pathname === '/reporting/followups/create') {
    return buildReactHref('/customers/', params, { extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/followups\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactHref(`/customers/${match[1]}/`, params);
  }
  if (pathname === '/reporting/customer-report/' || pathname === '/reporting/customer-report') {
    return buildReactHref('/customers/', params);
  }
  match = pathname.match(/^\/reporting\/customer-report\/(\d+)\/?$/);
  if (match) {
    return buildReactHref(`/customers/${match[1]}/`, params);
  }
  if (pathname === '/reporting/histories/' || pathname === '/reporting/histories') {
    return buildReactHref('/notes/', params);
  }
  match = pathname.match(/^\/reporting\/histories\/create-from-schedule\/(\d+)\/?$/);
  if (match) {
    return buildReactHref('/notes/', params, { extra: { create: '1', schedule: match[1] } });
  }
  match = pathname.match(/^\/reporting\/histories\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactHref(`/notes/${match[1]}/`, params);
  }
  if (pathname === '/reporting/schedules/' || pathname === '/reporting/schedules') {
    return buildReactHref('/schedules/', params);
  }
  if (pathname === '/reporting/schedules/calendar/' || pathname === '/reporting/schedules/calendar') {
    return buildReactHref('/schedules/calendar/', params);
  }
  if (pathname === '/reporting/schedules/create/' || pathname === '/reporting/schedules/create') {
    return buildReactHref('/schedules/', params, { rename: { followup: 'customer' }, extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/schedules\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactHref(`/schedules/${match[1]}/`, params);
  }
  if (
    pathname === '/reporting/funnel/' ||
    pathname === '/reporting/funnel' ||
    pathname === '/reporting/funnel/pipeline/' ||
    pathname === '/reporting/funnel/pipeline' ||
    /^\/reporting\/funnel\/\d+\/?$/.test(pathname)
  ) {
    return buildReactHref('/pipeline/', params);
  }
  return href;
}

function normalizeHrefFields<T extends object>(item: T, fields: string[]): T {
  const normalized: Record<string, unknown> = { ...(item as Record<string, unknown>) };
  fields.forEach((field) => {
    if (typeof normalized[field] === 'string') {
      normalized[field] = normalizeCoreCrmHref(normalized[field] as string);
    }
  });
  return normalized as T;
}

function normalizeScheduleLinks<T extends ScheduleItem | DashboardScheduleItem>(item: T): T {
  const normalized = normalizeHrefFields(item, [
    'href',
    'djangoHref',
    'customerHref',
    'djangoCustomerHref',
    'createHistoryHref',
    'djangoCreateHistoryHref',
    'djangoEditHref',
  ]) as T & { reports?: ScheduleReportItem[] };
  if (Array.isArray(normalized.reports)) {
    normalized.reports = normalized.reports.map((report) => normalizeHrefFields(report, ['href', 'djangoHref']));
  }
  return normalized as T;
}

function normalizeNoteLinks<T extends NoteItem>(item: T): T {
  return normalizeHrefFields(item, [
    'href',
    'djangoHref',
    'customerHref',
    'djangoCustomerHref',
    'scheduleHref',
  ]);
}

function normalizeCustomerLinks<T extends CustomerItem | DashboardCustomerItem>(item: T): T {
  const normalized = normalizeHrefFields(item, ['href', 'accountHref', 'customerHref', 'companyHref', 'createScheduleHref']) as T & {
    upcomingSchedule?: CustomerItem['upcomingSchedule'];
  };
  if (normalized.upcomingSchedule) {
    normalized.upcomingSchedule = normalizeHrefFields(normalized.upcomingSchedule, ['href', 'createHistoryHref']);
  }
  return normalized as T;
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
    return {
      ...emptyDashboardData,
      ...payload,
      scope: {
        ...emptyDashboardData.scope,
        ...(payload.scope ?? {}),
      },
      currentUser: {
        ...emptyDashboardData.currentUser,
        ...(payload.currentUser ?? {}),
      },
      metrics: {
        ...emptyDashboardData.metrics,
        ...(payload.metrics ?? {}),
      },
      revenuePeriod: {
        ...emptyDashboardData.revenuePeriod,
        ...(payload.revenuePeriod ?? {}),
      },
      today: {
        ...emptyDashboardData.today,
        ...(payload.today ?? {}),
        items: (payload.today?.items ?? emptyDashboardData.today.items).map(normalizeScheduleLinks),
      },
      links: normalizeHrefFields({
        ...emptyDashboardData.links,
        ...(payload.links ?? {}),
      }, [
        'operationalDashboard',
        'createNote',
        'customers',
        'customerReport',
        'notes',
        'schedules',
        'calendar',
        'pipeline',
        'weeklyReports',
        'pendingReviews',
      ]),
      upcomingSchedules: (payload.upcomingSchedules ?? emptyDashboardData.upcomingSchedules).map(normalizeScheduleLinks),
      overdueActions: (payload.overdueActions ?? emptyDashboardData.overdueActions).map((item) => (
        normalizeHrefFields(item, ['href', 'customerHref'])
      )),
      dueTodayActions: (payload.dueTodayActions ?? emptyDashboardData.dueTodayActions).map((item) => (
        normalizeHrefFields(item, ['href', 'customerHref'])
      )),
      recentActivities: (payload.recentActivities ?? emptyDashboardData.recentActivities).map((item) => (
        normalizeHrefFields(item, ['href', 'customerHref'])
      )),
      priorityCustomers: (payload.priorityCustomers ?? emptyDashboardData.priorityCustomers).map(normalizeCustomerLinks),
      pipelineSummary: payload.pipelineSummary ?? emptyDashboardData.pipelineSummary,
      teamActivity: payload.teamActivity ?? emptyDashboardData.teamActivity,
    };
  } catch (error) {
    return {
      ...emptyDashboardData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Dashboard API unavailable',
    };
  }
}

export async function loadReportsData(params: {
  dateFrom?: string;
  dateTo?: string;
  userId?: string;
} = {}): Promise<ReportsData> {
  const query = new URLSearchParams();
  if (params.dateFrom) query.set('date_from', params.dateFrom);
  if (params.dateTo) query.set('date_to', params.dateTo);
  if (params.userId) query.set('user_id', params.userId);

  try {
    const response = await fetch(`/reporting/api/reports/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Reports API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<ReportsData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Reports API unavailable: ${response.status}`);
    }
    return {
      ...emptyReportsData,
      ...payload,
      filters: {
        ...emptyReportsData.filters,
        ...(payload.filters ?? {}),
      },
      scope: {
        ...emptyReportsData.scope,
        ...(payload.scope ?? {}),
        salespeople: payload.scope?.salespeople ?? emptyReportsData.scope.salespeople,
      },
      metrics: {
        ...emptyReportsData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyReportsData.links,
        ...(payload.links ?? {}),
      },
      activityReport: payload.activityReport ?? emptyReportsData.activityReport,
      customerReport: (payload.customerReport ?? emptyReportsData.customerReport).map((customer) => (
        normalizeHrefFields(customer, ['href', 'djangoHref'])
      )),
      customerOperations: {
        ...emptyReportsData.customerOperations,
        ...(payload.customerOperations ?? {}),
        metrics: {
          ...emptyReportsData.customerOperations.metrics,
          ...(payload.customerOperations?.metrics ?? {}),
        },
        rows: (payload.customerOperations?.rows ?? emptyReportsData.customerOperations.rows).map((customer) => (
          normalizeHrefFields(customer, ['href', 'djangoHref'])
        )),
      },
      dataQuality: {
        ...emptyReportsData.dataQuality,
        ...(payload.dataQuality ?? {}),
        metrics: {
          ...emptyReportsData.dataQuality.metrics,
          ...(payload.dataQuality?.metrics ?? {}),
        },
        duplicateAccounts: (payload.dataQuality?.duplicateAccounts ?? emptyReportsData.dataQuality.duplicateAccounts).map((group) => ({
          ...group,
          departments: (group.departments ?? []).map((department) => ({
            ...department,
            accountHref: normalizeCoreCrmHref(department.accountHref),
            contacts: (department.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
          })),
          contacts: (group.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
        })),
        duplicateContacts: (payload.dataQuality?.duplicateContacts ?? emptyReportsData.dataQuality.duplicateContacts).map((group) => ({
          ...group,
          contacts: (group.contacts ?? []).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
        })),
        contactsWithoutDepartment: (
          payload.dataQuality?.contactsWithoutDepartment ?? emptyReportsData.dataQuality.contactsWithoutDepartment
        ).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
        contactsWithoutCompany: (
          payload.dataQuality?.contactsWithoutCompany ?? emptyReportsData.dataQuality.contactsWithoutCompany
        ).map((contact) => normalizeHrefFields(contact, ['href', 'accountHref'])),
      },
      pipelineSummary: payload.pipelineSummary ?? emptyReportsData.pipelineSummary,
    };
  } catch (error) {
    return {
      ...emptyReportsData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Reports API unavailable',
    };
  }
}

function normalizeAccountCleanupPreviewAccount(
  account?: Partial<AccountCleanupPreviewAccount> | null,
): AccountCleanupPreviewAccount | null {
  if (!account) {
    return null;
  }
  return {
    ...emptyAccountCleanupPreviewAccount,
    ...account,
    href: normalizeCoreCrmHref(account.href ?? emptyAccountCleanupPreviewAccount.href),
    djangoHref: normalizeCoreCrmHref(account.djangoHref ?? emptyAccountCleanupPreviewAccount.djangoHref),
    metrics: {
      ...emptyAccountCleanupPreviewAccount.metrics,
      ...(account.metrics ?? {}),
    },
    affectedRecords: account.affectedRecords ?? emptyAccountCleanupPreviewAccount.affectedRecords,
    contacts: (account.contacts ?? emptyAccountCleanupPreviewAccount.contacts).map((contact) => (
      normalizeHrefFields(contact, ['href', 'accountHref'])
    )),
  };
}

export async function loadAccountCleanupPreviewData(
  departmentId: number,
  targetDepartmentId?: string,
): Promise<AccountCleanupPreviewData> {
  const query = new URLSearchParams();
  if (targetDepartmentId) {
    query.set('target', targetDepartmentId);
  }

  try {
    const response = await fetch(`/reporting/api/accounts/${departmentId}/cleanup-preview/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Account cleanup preview API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<AccountCleanupPreviewData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Account cleanup preview API unavailable: ${response.status}`);
    }
    const sourceAccount = normalizeAccountCleanupPreviewAccount(payload.sourceAccount) ?? emptyAccountCleanupPreviewAccount;
    const targetAccount = normalizeAccountCleanupPreviewAccount(payload.targetAccount);
    return {
      ...emptyAccountCleanupPreviewData,
      ...payload,
      sourceAccount,
      targetAccount,
      combined: {
        ...emptyAccountCleanupPreviewData.combined,
        ...(payload.combined ?? {}),
        metrics: {
          ...emptyAccountCleanupPreviewData.combined.metrics,
          ...(payload.combined?.metrics ?? {}),
        },
      },
      warnings: payload.warnings ?? emptyAccountCleanupPreviewData.warnings,
      links: {
        ...emptyAccountCleanupPreviewData.links,
        ...(payload.links ?? {}),
        sourceAccount: normalizeCoreCrmHref(payload.links?.sourceAccount ?? sourceAccount.href),
        reports: normalizeCoreCrmHref(payload.links?.reports ?? emptyAccountCleanupPreviewData.links.reports),
      },
    };
  } catch (error) {
    return {
      ...emptyAccountCleanupPreviewData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Account cleanup preview API unavailable',
    };
  }
}

export async function searchAccountCleanupTargets(
  query: string,
  sourceDepartmentId?: number | null,
): Promise<AccountCleanupSearchResult[]> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('q', query.trim());
  }
  if (sourceDepartmentId) {
    params.set('source', String(sourceDepartmentId));
  }

  try {
    const response = await fetch(`/reporting/api/accounts/search/${params.toString() ? `?${params.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Account search API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as {
      success?: boolean;
      source?: string;
      error?: string;
      message?: string;
      results?: AccountCleanupSearchResult[];
    };
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Account search API unavailable: ${response.status}`);
    }
    return (payload.results ?? emptyAccountCleanupSearchResult.results).map((result) => ({
      ...result,
      href: normalizeCoreCrmHref(result.href),
      previewHref: normalizeCoreCrmHref(result.previewHref),
      contactPreview: result.contactPreview ?? [],
      piPreview: result.piPreview ?? [],
      emailPreview: result.emailPreview ?? [],
      meta: result.meta ?? '',
      searchText: result.searchText ?? '',
    }));
  } catch {
    return emptyAccountCleanupSearchResult.results;
  }
}

export async function loadProfileData(): Promise<ProfileData> {
  try {
    const response = await fetch('/reporting/api/profile/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Profile API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<ProfileData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Profile API unavailable: ${response.status}`);
    }
    return {
      ...emptyProfileData,
      ...payload,
      user: {
        ...emptyProfileData.user,
        ...(payload.user ?? {}),
      },
      profile: {
        ...emptyProfileData.profile,
        ...(payload.profile ?? {}),
      },
      emailConnection: {
        ...emptyProfileData.emailConnection,
        ...(payload.emailConnection ?? {}),
        links: {
          ...emptyProfileData.emailConnection.links,
          ...(payload.emailConnection?.links ?? {}),
        },
      },
      links: {
        ...emptyProfileData.links,
        ...(payload.links ?? {}),
      },
    };
  } catch (error) {
    return {
      ...emptyProfileData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Profile API unavailable',
    };
  }
}

async function postProfileJson<T>(url: string, payload?: unknown): Promise<T> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(payload ?? {}),
  });
  redirectIfLoginRequired(response);
  const data = (await response.json()) as T & { success?: boolean; error?: string; message?: string };
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Profile request failed: ${response.status}`);
  }
  return data;
}

export async function updateProfile(payload: ProfileUpdatePayload, submitUrl = '/reporting/api/profile/update/'): Promise<ProfileData> {
  const data = await postProfileJson<Partial<ProfileData>>(submitUrl, payload);
  return {
    ...emptyProfileData,
    ...data,
    user: {
      ...emptyProfileData.user,
      ...(data.user ?? {}),
    },
    profile: {
      ...emptyProfileData.profile,
      ...(data.profile ?? {}),
    },
    emailConnection: {
      ...emptyProfileData.emailConnection,
      ...(data.emailConnection ?? {}),
      links: {
        ...emptyProfileData.emailConnection.links,
        ...(data.emailConnection?.links ?? {}),
      },
    },
    links: {
      ...emptyProfileData.links,
      ...(data.links ?? {}),
    },
  };
}

export async function changeProfilePassword(payload: ProfilePasswordPayload, submitUrl = '/reporting/api/profile/password/') {
  return postProfileJson<{ success?: boolean; message?: string }>(submitUrl, payload);
}

export async function disconnectProfileEmail(submitUrl = '/reporting/api/profile/email/disconnect/'): Promise<ProfileData> {
  const data = await postProfileJson<Partial<ProfileData>>(submitUrl);
  return {
    ...emptyProfileData,
    ...data,
    user: {
      ...emptyProfileData.user,
      ...(data.user ?? {}),
    },
    profile: {
      ...emptyProfileData.profile,
      ...(data.profile ?? {}),
    },
    emailConnection: {
      ...emptyProfileData.emailConnection,
      ...(data.emailConnection ?? {}),
      links: {
        ...emptyProfileData.emailConnection.links,
        ...(data.emailConnection?.links ?? {}),
      },
    },
    links: {
      ...emptyProfileData.links,
      ...(data.links ?? {}),
    },
  };
}

export async function loadBusinessCardsData(): Promise<BusinessCardsData> {
  try {
    const response = await fetch('/reporting/api/business-cards/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Business cards API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<BusinessCardsData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Business cards API unavailable: ${response.status}`);
    }
    return {
      ...emptyBusinessCardsData,
      ...payload,
      cards: payload.cards ?? emptyBusinessCardsData.cards,
      links: {
        ...emptyBusinessCardsData.links,
        ...(payload.links ?? {}),
      },
    };
  } catch (error) {
    return {
      ...emptyBusinessCardsData,
      error: error instanceof Error ? error.message : 'Business cards API unavailable',
    };
  }
}

function businessCardPayloadToFormData(payload: BusinessCardPayload): FormData {
  const body = new FormData();
  body.set('name', payload.name);
  body.set('fullName', payload.fullName);
  body.set('title', payload.title);
  body.set('companyName', payload.companyName);
  body.set('department', payload.department);
  body.set('phone', payload.phone);
  body.set('mobile', payload.mobile);
  body.set('email', payload.email);
  body.set('address', payload.address);
  body.set('website', payload.website);
  body.set('fax', payload.fax);
  body.set('logoUrl', payload.logoUrl);
  body.set('logoLinkUrl', payload.logoLinkUrl);
  body.set('signatureHtml', payload.signatureHtml);
  if (payload.isDefault) body.set('isDefault', '1');
  if (payload.logo) body.set('logo', payload.logo);
  return body;
}

async function postBusinessCardForm(url: string, payload?: BusinessCardPayload): Promise<BusinessCardsData> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: payload ? businessCardPayloadToFormData(payload) : undefined,
  });
  redirectIfLoginRequired(response);
  const data = (await response.json()) as Partial<BusinessCardsData>;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Business card request failed: ${response.status}`);
  }
  return {
    ...emptyBusinessCardsData,
    ...data,
    cards: data.cards ?? emptyBusinessCardsData.cards,
    links: {
      ...emptyBusinessCardsData.links,
      ...(data.links ?? {}),
    },
  };
}

export async function saveBusinessCard(payload: BusinessCardPayload, submitUrl: string): Promise<BusinessCardsData> {
  return postBusinessCardForm(submitUrl, payload);
}

export async function deleteBusinessCard(submitUrl: string): Promise<BusinessCardsData> {
  return postBusinessCardForm(submitUrl);
}

export async function setDefaultBusinessCard(submitUrl: string): Promise<BusinessCardsData> {
  return postBusinessCardForm(submitUrl);
}

export async function loadMailboxData(params: {
  box?: MailboxType;
  q?: string;
  page?: number;
  scheduleId?: number;
} = {}): Promise<MailboxData> {
  const query = new URLSearchParams();
  if (params.box) query.set('box', params.box);
  if (params.q) query.set('q', params.q);
  if (params.page && params.page > 1) query.set('page', String(params.page));
  if (params.scheduleId) query.set('schedule_id', String(params.scheduleId));

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
        autoAttachments: payload.create?.autoAttachments ?? emptyMailboxCreateOptions.autoAttachments,
        autoAttachLabel: payload.create?.autoAttachLabel ?? emptyMailboxCreateOptions.autoAttachLabel,
        schedule: payload.create?.schedule ?? emptyMailboxCreateOptions.schedule,
        internalCcEmails: payload.create?.internalCcEmails ?? emptyMailboxCreateOptions.internalCcEmails,
        internalCcContacts: payload.create?.internalCcContacts ?? emptyMailboxCreateOptions.internalCcContacts,
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
        autoAttachments: payload.create?.autoAttachments ?? emptyMailboxCreateOptions.autoAttachments,
        autoAttachLabel: payload.create?.autoAttachLabel ?? emptyMailboxCreateOptions.autoAttachLabel,
        schedule: payload.create?.schedule ?? emptyMailboxCreateOptions.schedule,
        internalCcEmails: payload.create?.internalCcEmails ?? emptyMailboxCreateOptions.internalCcEmails,
        internalCcContacts: payload.create?.internalCcContacts ?? emptyMailboxCreateOptions.internalCcContacts,
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

export async function loadMailboxScheduledEmailData(scheduledEmailId: number): Promise<MailboxThreadData> {
  try {
    const response = await fetch(`/reporting/api/mailbox/scheduled/${scheduledEmailId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Scheduled email API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<MailboxThreadData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Scheduled email API unavailable: ${response.status}`);
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
        autoAttachments: payload.create?.autoAttachments ?? emptyMailboxCreateOptions.autoAttachments,
        autoAttachLabel: payload.create?.autoAttachLabel ?? emptyMailboxCreateOptions.autoAttachLabel,
        schedule: payload.create?.schedule ?? emptyMailboxCreateOptions.schedule,
        internalCcEmails: payload.create?.internalCcEmails ?? emptyMailboxCreateOptions.internalCcEmails,
        internalCcContacts: payload.create?.internalCcContacts ?? emptyMailboxCreateOptions.internalCcContacts,
        customers: payload.create?.customers ?? emptyMailboxCreateOptions.customers,
        businessCards: payload.create?.businessCards ?? emptyMailboxCreateOptions.businessCards,
      },
      emails: payload.emails ?? emptyMailboxThreadData.emails,
    };
  } catch (error) {
    return {
      ...emptyMailboxThreadData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Scheduled email API unavailable',
      thread: {
        ...emptyMailboxThreadData.thread,
        id: `scheduled-${scheduledEmailId}`,
      },
    };
  }
}

function mailboxPayloadToBody(payload: MailboxSendPayload): FormData {
  const body = new FormData();
  body.set('to_email', payload.toEmail);
  body.set('subject', payload.subject);
  body.set('body_text', payload.bodyText);
  if (payload.bodyHtml) body.set('body_html', payload.bodyHtml);
  if (payload.scheduledAt) body.set('scheduled_at', payload.scheduledAt);
  if (payload.ccEmails) body.set('cc_emails', payload.ccEmails);
  if (payload.bccEmails) body.set('bcc_emails', payload.bccEmails);
  if (payload.includeInternalCc) body.set('include_internal_cc', '1');
  if (payload.internalCcEmails?.length) body.set('internal_cc_emails', JSON.stringify(payload.internalCcEmails));
  if (payload.followupId) body.set('selected_followup_id', String(payload.followupId));
  if (payload.scheduleId) body.set('schedule_id', String(payload.scheduleId));
  if (payload.businessCardId) body.set('business_card_id', String(payload.businessCardId));
  if (payload.excludedAutoAttachmentKeys?.length) {
    body.set('excluded_auto_attachment_keys', JSON.stringify(payload.excludedAutoAttachmentKeys));
  }
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

export async function uploadMailboxEditorImage(file: File): Promise<{ success?: boolean; url?: string; error?: string }> {
  const csrfToken = getCookie('csrftoken');
  const body = new FormData();
  body.set('image', file);
  const response = await fetch('/reporting/upload-image/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body,
  });
  redirectIfLoginRequired(response);
  const data = await response.json() as { success?: boolean; url?: string; error?: string };
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false || !data.url) {
    throw new Error(data.error || `Image upload failed: ${response.status}`);
  }
  return data;
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
      create: {
        ...emptyCustomersData.create,
        ...(payload.create ?? {}),
        advancedUrl: normalizeCoreCrmHref(payload.create?.advancedUrl ?? emptyCustomersData.create.advancedUrl),
      },
      links: normalizeHrefFields({
        ...emptyCustomersData.links,
        ...(payload.links ?? {}),
      }, ['createCustomer', 'customers', 'customerReport', 'createNote']),
      customers: (payload.customers ?? emptyCustomersData.customers).map(normalizeCustomerLinks),
      accounts: (payload.accounts ?? emptyCustomersData.accounts).map(normalizeCustomerLinks),
      priorityCustomers: (payload.priorityCustomers ?? emptyCustomersData.priorityCustomers).map(normalizeCustomerLinks),
      priorityAccounts: (payload.priorityAccounts ?? emptyCustomersData.priorityAccounts).map(normalizeCustomerLinks),
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

async function submitCustomerAssetForm(form: FormData, submitUrl: string): Promise<CustomerAssetMutationResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(submitUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: form,
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Customer asset API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as CustomerAssetMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Customer asset mutation failed: ${response.status}`);
  }
  return data;
}

export async function saveCustomerAsset(
  payload: CustomerAssetPayload,
  submitUrl: string,
): Promise<CustomerAssetMutationResponse> {
  const form = new FormData();
  form.set('asset_name', payload.assetName);
  form.set('status', payload.status);
  if (payload.modelName) form.set('model_name', payload.modelName);
  if (payload.serialNumber) form.set('serial_number', payload.serialNumber);
  if (payload.purchaseDate) form.set('purchase_date', payload.purchaseDate);
  if (payload.installLocation) form.set('install_location', payload.installLocation);
  if (payload.warrantyUntil) form.set('warranty_until', payload.warrantyUntil);
  if (payload.notes) form.set('notes', payload.notes);
  return submitCustomerAssetForm(form, submitUrl);
}

export async function saveCustomerServiceCase(
  payload: CustomerServiceCasePayload,
  submitUrl: string,
): Promise<CustomerAssetMutationResponse> {
  const form = new FormData();
  form.set('asset_id', String(payload.assetId));
  form.set('case_type', payload.caseType);
  form.set('status', payload.status);
  form.set('priority', payload.priority);
  form.set('received_date', payload.receivedDate);
  if (payload.dueDate) form.set('due_date', payload.dueDate);
  if (payload.completedDate) form.set('completed_date', payload.completedDate);
  if (payload.symptom) form.set('symptom', payload.symptom);
  if (payload.resolution) form.set('resolution', payload.resolution);
  if (payload.serviceReport) form.set('service_report', payload.serviceReport);
  return submitCustomerAssetForm(form, submitUrl);
}

export async function saveCustomerCalibration(
  payload: CustomerCalibrationPayload,
  submitUrl: string,
): Promise<CustomerAssetMutationResponse> {
  const form = new FormData();
  form.set('asset_id', String(payload.assetId));
  form.set('calibration_date', payload.calibrationDate);
  form.set('result', payload.result);
  if (payload.nextDueDate) form.set('next_due_date', payload.nextDueDate);
  if (payload.notes) form.set('notes', payload.notes);
  if (payload.certificateFile) form.set('certificate_file', payload.certificateFile);
  return submitCustomerAssetForm(form, submitUrl);
}

export async function loadCustomerAssetDirectoryData(params: {
  q?: string;
  status?: string;
  owner?: string;
  service?: string;
  calibration?: string;
} = {}): Promise<CustomerAssetDirectoryData> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });

  try {
    const response = await fetch(`/reporting/api/customer-assets/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Customer assets API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<CustomerAssetDirectoryData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Customer assets API unavailable: ${response.status}`);
    }
    return {
      ...emptyCustomerAssetDirectoryData,
      ...payload,
      scope: {
        ...emptyCustomerAssetDirectoryData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyCustomerAssetDirectoryData.filters,
        ...(payload.filters ?? {}),
      },
      options: {
        ...emptyCustomerAssetDirectoryData.options,
        ...(payload.options ?? {}),
        owners: payload.options?.owners ?? emptyCustomerAssetDirectoryData.options.owners,
        assetStatuses: payload.options?.assetStatuses ?? emptyCustomerAssetDirectoryData.options.assetStatuses,
        serviceCaseTypes: payload.options?.serviceCaseTypes ?? emptyCustomerAssetDirectoryData.options.serviceCaseTypes,
        serviceStatuses: payload.options?.serviceStatuses ?? emptyCustomerAssetDirectoryData.options.serviceStatuses,
        servicePriorities: payload.options?.servicePriorities ?? emptyCustomerAssetDirectoryData.options.servicePriorities,
        calibrationResults: payload.options?.calibrationResults ?? emptyCustomerAssetDirectoryData.options.calibrationResults,
        serviceFilters: payload.options?.serviceFilters ?? emptyCustomerAssetDirectoryData.options.serviceFilters,
        calibrationFilters: payload.options?.calibrationFilters ?? emptyCustomerAssetDirectoryData.options.calibrationFilters,
      },
      metrics: {
        ...emptyCustomerAssetDirectoryData.metrics,
        ...(payload.metrics ?? {}),
      },
      links: {
        ...emptyCustomerAssetDirectoryData.links,
        ...(payload.links ?? {}),
      },
      create: {
        ...emptyCustomerAssetDirectoryData.create,
        ...(payload.create ?? {}),
        customers: (payload.create?.customers ?? emptyCustomerAssetDirectoryData.create.customers).map((customer) => (
          normalizeHrefFields(customer, ['href', 'assetCreateUrl'])
        )),
      },
      workQueue: (payload.workQueue ?? emptyCustomerAssetDirectoryData.workQueue).map((item) => (
        normalizeHrefFields(item, ['href', 'customerHref'])
      )),
      assets: (payload.assets ?? emptyCustomerAssetDirectoryData.assets).map((asset) => (
        normalizeHrefFields(asset, ['customerHref', 'djangoCustomerHref', 'assetDirectoryHref'])
      )),
    };
  } catch (error) {
    return {
      ...emptyCustomerAssetDirectoryData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Customer assets API unavailable',
    };
  }
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

async function loadCustomerDetailFromUrl(apiUrl: string, errorPrefix: string): Promise<CustomerDetailData> {
  try {
    const response = await fetch(apiUrl, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`${errorPrefix} API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<CustomerDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `${errorPrefix} API unavailable: ${response.status}`);
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
      account: {
        ...emptyCustomerDetailData.account,
        ...(payload.account ?? {}),
        href: normalizeCoreCrmHref(payload.account?.href ?? emptyCustomerDetailData.account.href),
        djangoRepresentativeHref: normalizeCoreCrmHref(
          payload.account?.djangoRepresentativeHref ?? emptyCustomerDetailData.account.djangoRepresentativeHref,
        ),
        contacts: (payload.account?.contacts ?? emptyCustomerDetailData.account.contacts).map((contact) => ({
          ...contact,
          href: normalizeCoreCrmHref(contact.href),
          djangoHref: normalizeCoreCrmHref(contact.djangoHref),
        })),
      },
      links: normalizeHrefFields({
        ...emptyCustomerDetailData.links,
        ...(payload.links ?? {}),
      }, ['customers', 'djangoDetail', 'djangoEdit', 'createSchedule', 'createNote', 'deliveryRecordsXlsx', 'accountDetail', 'accountDeliveryRecordsXlsx']),
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
      operationalRecords: {
        ...emptyCustomerDetailData.operationalRecords,
        ...(payload.operationalRecords ?? {}),
        metrics: {
          ...emptyCustomerDetailData.operationalRecords.metrics,
          ...(payload.operationalRecords?.metrics ?? {}),
        },
        serviceRecords: payload.operationalRecords?.serviceRecords ?? emptyCustomerDetailData.operationalRecords.serviceRecords,
        quoteRecords: payload.operationalRecords?.quoteRecords ?? emptyCustomerDetailData.operationalRecords.quoteRecords,
        deliveryRecords: payload.operationalRecords?.deliveryRecords ?? emptyCustomerDetailData.operationalRecords.deliveryRecords,
        prepaymentRecords: payload.operationalRecords?.prepaymentRecords ?? emptyCustomerDetailData.operationalRecords.prepaymentRecords,
      },
      assetSummary: {
        ...emptyCustomerDetailData.assetSummary,
        ...(payload.assetSummary ?? {}),
        metrics: {
          ...emptyCustomerDetailData.assetSummary.metrics,
          ...(payload.assetSummary?.metrics ?? {}),
        },
        links: {
          ...emptyCustomerDetailData.assetSummary.links,
          ...(payload.assetSummary?.links ?? {}),
        },
        options: {
          ...emptyCustomerDetailData.assetSummary.options,
          ...(payload.assetSummary?.options ?? {}),
        },
        assets: payload.assetSummary?.assets ?? emptyCustomerDetailData.assetSummary.assets,
      },
      edit: {
        ...emptyCustomerDetailData.edit,
        ...(payload.edit ?? {}),
        djangoUrl: normalizeCoreCrmHref(payload.edit?.djangoUrl ?? emptyCustomerDetailData.edit.djangoUrl),
      },
      recentNotes: (payload.recentNotes ?? emptyCustomerDetailData.recentNotes).map(normalizeNoteLinks),
      overdueActions: (payload.overdueActions ?? emptyCustomerDetailData.overdueActions).map(normalizeNoteLinks),
      upcomingActions: (payload.upcomingActions ?? emptyCustomerDetailData.upcomingActions).map(normalizeNoteLinks),
      upcomingSchedules: (payload.upcomingSchedules ?? emptyCustomerDetailData.upcomingSchedules).map(normalizeScheduleLinks),
      recentSchedules: (payload.recentSchedules ?? emptyCustomerDetailData.recentSchedules).map(normalizeScheduleLinks),
      customer: payload.customer ? normalizeCustomerLinks(payload.customer) : emptyCustomerDetailData.customer,
    };
  } catch (error) {
    return {
      ...emptyCustomerDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : `${errorPrefix} API unavailable`,
    };
  }
}

export async function loadCustomerDetailData(customerId: number): Promise<CustomerDetailData> {
  return loadCustomerDetailFromUrl(`/reporting/api/customers/${customerId}/`, 'Customer detail');
}

export async function loadAccountDetailData(departmentId: number): Promise<CustomerDetailData> {
  return loadCustomerDetailFromUrl(`/reporting/api/accounts/${departmentId}/`, 'Account detail');
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
      links: normalizeHrefFields({
        ...emptyNotesData.links,
        ...(payload.links ?? {}),
      }, ['createNote', 'notes', 'unreviewed', 'weeklyReports']),
      create: {
        ...emptyNotesData.create,
        ...(payload.create ?? {}),
        customers: payload.create?.customers?.map((customer) => (
          normalizeHrefFields(customer, ['href'])
        )) ?? emptyNotesData.create.customers,
      },
      actionCounts: payload.actionCounts ?? emptyNotesData.actionCounts,
      notes: (payload.notes ?? emptyNotesData.notes).map(normalizeNoteLinks),
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
      links: normalizeHrefFields({
        ...emptyNoteDetailData.links,
        ...(payload.links ?? {}),
      }, ['notes', 'djangoDetail', 'djangoEdit', 'customer', 'djangoCustomer', 'schedule', 'createNote']),
      edit: {
        ...emptyNoteDetailData.edit,
        ...(payload.edit ?? {}),
        djangoUrl: normalizeCoreCrmHref(payload.edit?.djangoUrl ?? emptyNoteDetailData.edit.djangoUrl),
        customers: payload.edit?.customers?.map((customer) => (
          normalizeHrefFields(customer, ['href', 'djangoHref'])
        )) ?? emptyNoteDetailData.edit.customers,
      },
      comments: {
        ...emptyNoteDetailData.comments,
        ...(payload.comments ?? {}),
      },
      note: payload.note ? normalizeNoteLinks(payload.note) : emptyNoteDetailData.note,
      relatedNotes: (payload.relatedNotes ?? emptyNoteDetailData.relatedNotes).map(normalizeNoteLinks),
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
      links: normalizeHrefFields({
        ...emptySchedulesData.links,
        ...(payload.links ?? {}),
      }, ['createSchedule', 'schedules', 'djangoSchedules', 'calendar', 'djangoCalendar', 'weeklyReports']),
      create: {
        ...emptySchedulesData.create,
        ...(payload.create ?? {}),
        customers: payload.create?.customers?.map((customer) => (
          normalizeHrefFields(customer, ['href', 'djangoHref'])
        )) ?? emptySchedulesData.create.customers,
        personalSchedule: {
          canCreate: payload.create?.personalSchedule?.canCreate ?? emptySchedulesData.create.personalSchedule?.canCreate ?? false,
          message: payload.create?.personalSchedule?.message ?? emptySchedulesData.create.personalSchedule?.message ?? '',
          submitUrl: payload.create?.personalSchedule?.submitUrl ?? emptySchedulesData.create.personalSchedule?.submitUrl ?? '/reporting/api/personal-schedules/create/',
          djangoUrl: payload.create?.personalSchedule?.djangoUrl ?? emptySchedulesData.create.personalSchedule?.djangoUrl ?? '/reporting/personal-schedules/create/',
        },
      },
      statusCounts: payload.statusCounts ?? emptySchedulesData.statusCounts,
      activityCounts: payload.activityCounts ?? emptySchedulesData.activityCounts,
      today: (payload.today ?? emptySchedulesData.today).map(normalizeScheduleLinks),
      upcoming: (payload.upcoming ?? emptySchedulesData.upcoming).map(normalizeScheduleLinks),
      overdue: (payload.overdue ?? emptySchedulesData.overdue).map(normalizeScheduleLinks),
      schedules: (payload.schedules ?? emptySchedulesData.schedules).map(normalizeScheduleLinks),
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
      links: normalizeHrefFields({
        ...emptyScheduleCalendarData.links,
        ...(payload.links ?? {}),
      }, ['schedules', 'djangoSchedules', 'calendar', 'djangoCalendar', 'createSchedule', 'weeklyReports']),
      create: {
        ...emptyScheduleCalendarData.create,
        ...(payload.create ?? {}),
        customers: payload.create?.customers?.map((customer) => (
          normalizeHrefFields(customer, ['href', 'djangoHref'])
        )) ?? emptyScheduleCalendarData.create.customers,
        personalSchedule: {
          canCreate: payload.create?.personalSchedule?.canCreate ?? emptyScheduleCalendarData.create.personalSchedule?.canCreate ?? false,
          message: payload.create?.personalSchedule?.message ?? emptyScheduleCalendarData.create.personalSchedule?.message ?? '',
          submitUrl: payload.create?.personalSchedule?.submitUrl ?? emptyScheduleCalendarData.create.personalSchedule?.submitUrl ?? '/reporting/api/personal-schedules/create/',
          djangoUrl: payload.create?.personalSchedule?.djangoUrl ?? emptyScheduleCalendarData.create.personalSchedule?.djangoUrl ?? '/reporting/personal-schedules/create/',
        },
      },
      schedules: (payload.schedules ?? emptyScheduleCalendarData.schedules).map(normalizeScheduleLinks),
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

export async function createPersonalSchedule(
  payload: PersonalSchedulePayload,
  submitUrl = '/reporting/api/personal-schedules/create/',
): Promise<PersonalScheduleMutationResponse> {
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
    throw new Error(`Personal schedule create API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PersonalScheduleMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Personal schedule create failed: ${response.status}`);
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

function normalizeProductManagementItem(product: ProductApiItem): ProductManagementItem {
  const productCode = product.product_code ?? product.productCode ?? product.name ?? '';
  const standardPrice = Number(product.standard_price ?? product.standardPrice ?? 0);
  const normalizedStandardPrice = Number.isFinite(standardPrice) ? standardPrice : 0;
  const currentPrice = Number(product.current_price ?? product.currentPrice ?? normalizedStandardPrice);
  const normalizedCurrentPrice = Number.isFinite(currentPrice) ? currentPrice : normalizedStandardPrice;
  const isActive = Boolean(product.is_active ?? product.isActive ?? true);

  return {
    id: product.id,
    productCode,
    product_code: productCode,
    name: product.name ?? productCode,
    description: product.description ?? '',
    unit: product.unit || 'EA',
    specification: product.specification ?? '',
    standardPrice: normalizedStandardPrice,
    standard_price: normalizedStandardPrice,
    currentPrice: normalizedCurrentPrice,
    current_price: normalizedCurrentPrice,
    isActive,
    is_active: isActive,
    isPromo: Boolean(product.is_promo ?? product.isPromo),
    is_promo: Boolean(product.is_promo ?? product.isPromo),
    quoteCount: Number(product.quoteCount ?? 0),
    deliveryCount: Number(product.deliveryCount ?? 0),
    createdBy: product.createdBy ?? '',
    createdAt: product.createdAt ?? null,
    updatedAt: product.updatedAt ?? null,
    djangoEditHref: product.djangoEditHref ?? '',
  };
}

export async function loadProductManagementData(params: {
  q?: string;
  status?: string;
  sort?: string;
  order?: string;
  page?: number;
  pageSize?: number;
} = {}): Promise<ProductManagementData> {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.status) query.set('status', params.status);
  if (params.sort) query.set('sort', params.sort);
  if (params.order) query.set('order', params.order);
  if (params.page) query.set('page', String(params.page));
  if (params.pageSize) query.set('page_size', String(params.pageSize));

  try {
    const response = await fetch(`/reporting/api/products/manage/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Product management API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<ProductManagementData> & ProductsApiResponse;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Product management API unavailable: ${response.status}`);
    }

    return {
      ...emptyProductManagementData,
      ...payload,
      source: 'django',
      scope: {
        ...emptyProductManagementData.scope,
        ...(payload.scope ?? {}),
      },
      metrics: {
        ...emptyProductManagementData.metrics,
        ...(payload.metrics ?? {}),
      },
      pagination: {
        ...emptyProductManagementData.pagination,
        ...(payload.pagination ?? {}),
      },
      links: {
        ...emptyProductManagementData.links,
        ...(payload.links ?? {}),
      },
      products: (payload.products ?? []).map((product) => normalizeProductManagementItem(product)),
    };
  } catch (error) {
    return {
      ...emptyProductManagementData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Product management API unavailable',
    };
  }
}

async function postProductJson<T>(url: string, body: unknown): Promise<T> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(body),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Product API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as T & { success?: boolean; error?: string; message?: string };
  redirectIfLoginRequired(response, data);
  if (!response.ok) {
    throw new Error(data.error || data.message || `Product API failed: ${response.status}`);
  }
  return data;
}

export async function saveProduct(
  payload: ProductMutationPayload,
  productId?: number | null,
): Promise<ProductSaveResult> {
  const url = productId ? `/reporting/api/products/${productId}/save/` : '/reporting/api/products/save/';
  const data = await postProductJson<ProductSaveResult>(url, payload);
  if (data.success === false) {
    throw new Error(data.message || '제품 저장에 실패했습니다.');
  }
  return {
    ...data,
    product: normalizeProductManagementItem(data.product),
  };
}

export async function bulkUpsertProducts(products: ProductMutationPayload[]): Promise<ProductBulkUpsertResult> {
  const data = await postProductJson<ProductBulkUpsertResult>('/reporting/api/products/bulk-upsert/', { products });
  if (!data.results) {
    data.results = [];
  }
  return data;
}

export async function bulkDeleteProducts(
  productCodes: string[],
): Promise<ProductBulkDeleteResult> {
  const data = await postProductJson<ProductBulkDeleteResult>('/reporting/api/products/bulk-delete/', { productCodes });
  if (data.success === false) {
    throw new Error(data.error || data.message || '제품 삭제에 실패했습니다.');
  }
  if (!data.results) {
    data.results = [];
  }
  return data;
}

export async function replaceProductReference(payload: {
  productCode: string;
  referenceType: string;
  referenceId: number;
  replacementProductId: number;
}): Promise<ProductReplaceReferenceResult> {
  const data = await postProductJson<ProductReplaceReferenceResult>('/reporting/api/products/replace-reference/', payload);
  if (data.success === false) {
    throw new Error(data.error || data.message || '품목 대체에 실패했습니다.');
  }
  return data;
}

export async function loadProducts(
  search = '',
  options: { limit?: number; signal?: AbortSignal } = {},
): Promise<ProductOption[]> {
  const params = new URLSearchParams();
  const query = search.trim();
  if (query) {
    params.set('search', query);
  }
  if (options.limit && options.limit > 0) {
    params.set('limit', String(options.limit));
  }

  const queryString = params.toString();
  const response = await fetch(`/reporting/api/products/${queryString ? `?${queryString}` : ''}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
    signal: options.signal,
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

async function loadPrepaymentCustomerContext(
  apiPath: string,
  unavailableLabel: string,
  targetUserId?: string,
): Promise<PrepaymentCustomerData> {
  const query = new URLSearchParams();
  if (targetUserId) {
    query.set('user', targetUserId);
  }

  try {
    const response = await fetch(`${apiPath}${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`${unavailableLabel}: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PrepaymentCustomerData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `${unavailableLabel}: ${response.status}`);
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
      error: error instanceof Error ? error.message : unavailableLabel,
    };
  }
}

export async function loadPrepaymentCustomerData(
  customerId: number,
  targetUserId?: string,
): Promise<PrepaymentCustomerData> {
  return loadPrepaymentCustomerContext(
    `/reporting/api/prepayments/customer/${customerId}/`,
    'Prepayment customer API unavailable',
    targetUserId,
  );
}

export async function loadPrepaymentAccountData(
  departmentId: number,
  targetUserId?: string,
): Promise<PrepaymentCustomerData> {
  return loadPrepaymentCustomerContext(
    `/reporting/api/prepayments/account/${departmentId}/`,
    'Prepayment account API unavailable',
    targetUserId,
  );
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
      links: normalizeHrefFields({
        ...emptyScheduleDetailData.links,
        ...(payload.links ?? {}),
      }, [
        'schedules',
        'djangoSchedules',
        'calendar',
        'djangoDetail',
        'djangoEdit',
        'customer',
        'djangoCustomer',
        'createNote',
        'djangoCreateNote',
      ]),
      edit: {
        ...emptyScheduleDetailData.edit,
        ...(payload.edit ?? {}),
        djangoUrl: normalizeCoreCrmHref(payload.edit?.djangoUrl ?? emptyScheduleDetailData.edit.djangoUrl),
        customers: payload.edit?.customers?.map((customer) => (
          normalizeHrefFields(customer, ['href', 'djangoHref'])
        )) ?? emptyScheduleDetailData.edit.customers,
      },
      ai: {
        ...emptyScheduleDetailData.ai,
        ...(payload.ai ?? {}),
      },
      schedule: payload.schedule ? normalizeScheduleLinks(payload.schedule) : emptyScheduleDetailData.schedule,
      relatedNotes: (payload.relatedNotes ?? emptyScheduleDetailData.relatedNotes).map(normalizeNoteLinks),
      deliveryItems: payload.deliveryItems ?? emptyScheduleDetailData.deliveryItems,
      documents: {
        ...emptyScheduleDetailData.documents,
        ...(payload.documents ?? {}),
        items: payload.documents?.items ?? emptyScheduleDetailData.documents.items,
        registeredDocuments: payload.documents?.registeredDocuments ?? emptyScheduleDetailData.documents.registeredDocuments,
        registeredDocumentCount: payload.documents?.registeredDocumentCount ?? emptyScheduleDetailData.documents.registeredDocumentCount,
        registeredQuotations: payload.documents?.registeredQuotations ?? emptyScheduleDetailData.documents.registeredQuotations,
        registeredQuotationCount: payload.documents?.registeredQuotationCount ?? emptyScheduleDetailData.documents.registeredQuotationCount,
        autoAttachLabel: payload.documents?.autoAttachLabel ?? emptyScheduleDetailData.documents.autoAttachLabel,
      },
      commercialChecks: payload.commercialChecks ?? emptyScheduleDetailData.commercialChecks,
    };
  } catch (error) {
    return {
      ...emptyScheduleDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Schedule detail API unavailable',
    };
  }
}

export async function loadPersonalScheduleDetailData(scheduleId: number): Promise<PersonalScheduleDetailData> {
  try {
    const response = await fetch(`/reporting/api/personal-schedules/${scheduleId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Personal schedule detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<PersonalScheduleDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Personal schedule detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyPersonalScheduleDetailData,
      ...payload,
      links: normalizeHrefFields({
        ...emptyPersonalScheduleDetailData.links,
        ...(payload.links ?? {}),
      }, ['calendar', 'djangoCalendar', 'djangoDetail', 'djangoEdit']),
      edit: {
        ...emptyPersonalScheduleDetailData.edit,
        ...(payload.edit ?? {}),
        djangoUrl: normalizeCoreCrmHref(payload.edit?.djangoUrl ?? emptyPersonalScheduleDetailData.edit.djangoUrl),
      },
      schedule: payload.schedule ? normalizeScheduleLinks(payload.schedule) : emptyPersonalScheduleDetailData.schedule,
    };
  } catch (error) {
    return {
      ...emptyPersonalScheduleDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Personal schedule detail API unavailable',
    };
  }
}

const rawRecord = (value: unknown): Record<string, unknown> => (
  value && typeof value === 'object' ? value as Record<string, unknown> : {}
);

const rawValue = (record: Record<string, unknown>, camelKey: string, snakeKey?: string): unknown => (
  record[camelKey] ?? (snakeKey ? record[snakeKey] : undefined)
);

const rawString = (value: unknown): string => (
  value === undefined || value === null ? '' : String(value)
);

const rawNumber = (value: unknown, fallback = 0): number => {
  const parsed = Number(value ?? fallback);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const rawNullableNumber = (value: unknown): number | null => {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const rawBoolean = (value: unknown): boolean => (
  value === true || value === 1 || value === '1' || value === 'true' || value === 'True' || value === 'Y' || value === 'yes'
);

const normalizeFollowupQuoteItem = (value: unknown): FollowupQuoteItem => {
  const item = rawRecord(value);
  const unitPrice = rawNumber(rawValue(item, 'unitPrice', 'unit_price'));
  const quoteGroup = rawString(rawValue(item, 'quoteGroup', 'quote_group')).trim();
  const productId = rawNullableNumber(rawValue(item, 'productId', 'product_id'));
  const remainingQuantity = Math.max(1, rawNumber(rawValue(item, 'remainingQuantity', 'remaining_quantity') ?? item.quantity, 1));
  const originalQuantity = Math.max(remainingQuantity, rawNumber(rawValue(item, 'originalQuantity', 'original_quantity'), remainingQuantity));
  const deliveredQuantity = Math.max(0, rawNumber(rawValue(item, 'deliveredQuantity', 'delivered_quantity')));
  const totalPrice = rawNumber(rawValue(item, 'totalPrice', 'total_price'));
  const discountRate = rawNumber(rawValue(item, 'discountRate', 'discount_rate'));
  const rawDiscountUnitPrice = rawNullableNumber(rawValue(item, 'discountUnitPrice', 'discount_unit_price'));
  const discountUnitPrice = rawDiscountUnitPrice !== null && !(rawDiscountUnitPrice <= 0 && discountRate <= 0 && unitPrice > 0)
    ? rawDiscountUnitPrice
    : null;
  const rawEffectiveUnitPrice = rawNullableNumber(rawValue(item, 'effectiveUnitPrice', 'effective_unit_price'));
  const effectiveUnitPrice = rawEffectiveUnitPrice !== null && !(rawEffectiveUnitPrice <= 0 && discountUnitPrice === null && unitPrice > 0)
    ? rawEffectiveUnitPrice
    : unitPrice;
  return {
    id: rawNullableNumber(item.id),
    productId,
    productCode: rawString(rawValue(item, 'productCode', 'product_code')),
    productDescription: rawString(rawValue(item, 'productDescription', 'product_description')),
    sourceQuoteScheduleId: rawNullableNumber(rawValue(item, 'sourceQuoteScheduleId', 'source_quote_schedule_id')),
    sourceQuoteItemId: rawNullableNumber(rawValue(item, 'sourceQuoteItemId', 'source_quote_item_id')) ?? rawNullableNumber(item.id),
    itemName: rawString(rawValue(item, 'itemName', 'item_name')),
    originalQuantity,
    deliveredQuantity,
    remainingQuantity,
    quantity: remainingQuantity,
    unit: rawString(item.unit) || 'EA',
    unitPrice,
    discountRate,
    discountUnitPrice,
    effectiveUnitPrice,
    totalPrice,
    remainingAmount: rawNumber(rawValue(item, 'remainingAmount', 'remaining_amount'), totalPrice),
    quotedAmount: rawNumber(rawValue(item, 'quotedAmount', 'quoted_amount'), totalPrice),
    deliveredAmount: rawNumber(rawValue(item, 'deliveredAmount', 'delivered_amount')),
    taxInvoiceIssued: rawBoolean(rawValue(item, 'taxInvoiceIssued', 'tax_invoice_issued')),
    quoteGroup,
    quoteGroupLabel: rawString(rawValue(item, 'quoteGroupLabel', 'quote_group_label')) || quoteGroup || '기본 견적서',
    notes: rawString(item.notes),
  };
};

const normalizeFollowupQuoteOption = (value: unknown): FollowupQuoteOption => {
  const quote = rawRecord(value);
  const scheduleId = rawNumber(rawValue(quote, 'scheduleId', 'schedule_id') ?? quote.id);
  const quoteGroup = rawString(rawValue(quote, 'quoteGroup', 'quote_group')).trim();
  const quoteGroupLabel = rawString(rawValue(quote, 'quoteGroupLabel', 'quote_group_label')) || quoteGroup || '기본 견적서';
  const rawItems = quote.items;
  const remainingAmount = rawNumber(rawValue(quote, 'remainingAmount', 'remaining_amount') ?? rawValue(quote, 'expectedRevenue', 'expected_revenue'));
  const deliveredAmount = rawNumber(rawValue(quote, 'deliveredAmount', 'delivered_amount'));
  const quotedAmount = rawNumber(rawValue(quote, 'quotedAmount', 'quoted_amount'), remainingAmount + deliveredAmount);
  return {
    id: rawNumber(quote.id, scheduleId),
    optionId: rawString(rawValue(quote, 'optionId', 'option_id')) || `${scheduleId}:${quoteGroup || 'default'}`,
    scheduleId,
    quoteGroup,
    quoteGroupLabel,
    quoteDate: rawString(rawValue(quote, 'quoteDate', 'quote_date')),
    expectedRevenue: rawNumber(rawValue(quote, 'expectedRevenue', 'expected_revenue')),
    quotedAmount,
    deliveredAmount,
    remainingAmount,
    deliveryStatus: rawString(rawValue(quote, 'deliveryStatus', 'delivery_status')) || (deliveredAmount > 0 ? 'partial' : 'pending'),
    deliveryStatusLabel: rawString(rawValue(quote, 'deliveryStatusLabel', 'delivery_status_label')) || (deliveredAmount > 0 ? '부분 납품 잔여' : '미납 견적'),
    hasPartialDelivery: rawBoolean(rawValue(quote, 'hasPartialDelivery', 'has_partial_delivery')) || (deliveredAmount > 0 && remainingAmount > 0),
    customerName: rawString(rawValue(quote, 'customerName', 'customer_name')),
    companyName: rawString(rawValue(quote, 'companyName', 'company_name')),
    departmentName: rawString(rawValue(quote, 'departmentName', 'department_name')),
    href: rawString(quote.href) || (scheduleId ? `/schedules/${scheduleId}/` : ''),
    djangoHref: rawString(quote.djangoHref),
    items: Array.isArray(rawItems) ? rawItems.map(normalizeFollowupQuoteItem) : [],
  };
};

export async function loadFollowupQuoteItems(followupId: number): Promise<FollowupQuoteItemsData> {
  const response = await fetch(`/reporting/api/followups/${followupId}/quote-items/`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Quote items API unavailable: ${response.status}`);
  }
  const payload = rawRecord(await response.json());
  redirectIfLoginRequired(response, payload);
  if (!response.ok || payload.error) {
    throw new Error(rawString(payload.error) || `Quote items API unavailable: ${response.status}`);
  }
  const rawQuotes = payload.quotes;
  const quotes = Array.isArray(rawQuotes) ? rawQuotes.map(normalizeFollowupQuoteOption) : [];
  return {
    success: payload.success === undefined ? true : rawBoolean(payload.success),
    error: rawString(payload.error),
    quotes,
    count: rawNumber(payload.count, quotes.length),
  };
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
      quote_group?: string;
      quote_group_label?: string;
    };
    items?: Array<{
      index?: number;
      name?: string;
      quantity?: number;
      unit?: string;
      unit_price?: number;
      unitPrice?: number;
      base_unit_price?: number;
      baseUnitPrice?: number;
      discount_rate?: number;
      discountRate?: number;
      discount_unit_price?: number | null;
      discountUnitPrice?: number | null;
      quote_group?: string;
      quoteGroup?: string;
      quote_group_label?: string;
      quoteGroupLabel?: string;
      notes?: string;
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
      quoteGroup: rawFileInfo.quoteGroup ?? snakeFileInfo.quote_group,
      quoteGroupLabel: rawFileInfo.quoteGroupLabel ?? snakeFileInfo.quote_group_label,
    },
    items: (data.items ?? []).map((item, index) => ({
      index: item.index ?? index + 1,
      name: item.name ?? '',
      quantity: item.quantity ?? 0,
      unit: item.unit ?? '',
      unitPrice: item.unitPrice ?? item.unit_price ?? 0,
      baseUnitPrice: item.baseUnitPrice ?? item.base_unit_price ?? item.unitPrice ?? item.unit_price ?? 0,
      discountRate: item.discountRate ?? item.discount_rate ?? 0,
      discountUnitPrice: item.discountUnitPrice ?? item.discount_unit_price ?? null,
      quoteGroup: item.quoteGroup ?? item.quote_group ?? '',
      quoteGroupLabel: item.quoteGroupLabel ?? item.quote_group_label ?? '',
      notes: item.notes ?? '',
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

export async function deleteGeneratedDocument(deleteUrl: string): Promise<ScheduleFileActionResponse> {
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
    throw new Error(`Generated document delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleFileActionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Generated document delete failed: ${response.status}`);
  }
  return data;
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
      templateVariableGroups: payload.templateVariableGroups ?? emptyDocumentTemplatesData.templateVariableGroups,
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

export async function updatePersonalSchedule(
  payload: PersonalSchedulePayload,
  submitUrl: string,
): Promise<PersonalScheduleMutationResponse> {
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
    throw new Error(`Personal schedule update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as PersonalScheduleMutationResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Personal schedule update failed: ${response.status}`);
  }
  return data;
}

export async function updateScheduleDeliveryItems(
  submitUrl: string,
  items: ScheduleDeliveryItemPayload[],
  quoteGroupNotes?: Record<string, string>,
  sourceQuoteScheduleIds?: number[],
  options?: ScheduleDeliveryItemsUpdateOptions,
): Promise<ScheduleDeliveryItemsUpdateResponse> {
  const csrfToken = getCookie('csrftoken');
  const payload: {
    items: ScheduleDeliveryItemPayload[];
    quoteGroupNotes: Record<string, string>;
    sourceQuoteScheduleIds?: number[];
    usePrepayment?: boolean;
    prepayments?: SchedulePrepaymentSelectionPayload[];
  } = {
    items,
    quoteGroupNotes: quoteGroupNotes ?? {},
  };
  if (sourceQuoteScheduleIds?.length) {
    payload.sourceQuoteScheduleIds = sourceQuoteScheduleIds;
  }
  if (options) {
    payload.usePrepayment = Boolean(options.usePrepayment);
    payload.prepayments = options.usePrepayment ? options.prepayments ?? [] : [];
  }
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

export async function deleteSchedule(deleteUrl: string): Promise<ScheduleDeleteResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(deleteUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule delete API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleDeleteResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule delete failed: ${response.status}`);
  }
  return data;
}

export async function loadAIWorkspaceData(params: AIWorkspaceLoadParams = {}): Promise<AIWorkspaceData> {
  const query = new URLSearchParams();
  if (params.departmentId) {
    query.set('department_id', String(params.departmentId));
  }
  if (params.questionPage && params.questionPage > 1) {
    query.set('question_page', String(params.questionPage));
  }
  if (params.questionScope === 'all') {
    query.set('question_scope', 'all');
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
          ...normalizeCustomerAiDepartment(payload.featuredDepartment),
          customerCount: payload.featuredDepartment.customerCount ?? 0,
          customerPreview: payload.featuredDepartment.customerPreview ?? [],
        }
      : null;
    return {
      ...payload,
      featuredDepartment,
      selectedDepartmentId: payload.selectedDepartmentId ?? featuredDepartment?.departmentId ?? null,
      promptTargets: payload.promptTargets ?? [],
      actionQueue: payload.actionQueue ?? [],
      feedbackHistory: payload.feedbackHistory ?? emptyAIWorkspaceData.feedbackHistory,
      questionHistory: payload.questionHistory ?? emptyAIWorkspaceData.questionHistory,
      questionModelChoices: payload.questionModelChoices ?? emptyAIWorkspaceData.questionModelChoices,
      defaultQuestionModel: payload.defaultQuestionModel ?? emptyAIWorkspaceData.defaultQuestionModel,
    };
  } catch (error) {
    return {
      ...emptyAIWorkspaceData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'AI workspace API unavailable',
    };
  }
}

export async function loadAIWorkspaceQuestionLogDetailData(questionLogId: number): Promise<AIWorkspaceQuestionLogDetailData> {
  try {
    const response = await fetch(`/reporting/api/ai-workspace/questions/${questionLogId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`AI question detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as AIWorkspaceQuestionLogDetailData;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `AI question detail unavailable: ${response.status}`);
    }
    return {
      ...payload,
      links: {
        aiWorkspace: payload.links?.aiWorkspace || '/ai-workspace/',
      },
      questionLog: payload.questionLog ?? null,
    };
  } catch (error) {
    return {
      success: false,
      source: 'unavailable',
      generatedAt: new Date().toISOString(),
      questionLog: null,
      links: {
        aiWorkspace: '/ai-workspace/',
      },
      error: error instanceof Error ? error.message : 'AI question detail unavailable',
    };
  }
}

export async function deleteAIWorkspaceQuestionLog(questionLogId: number): Promise<AIWorkspaceQuestionLogDeleteResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(`/reporting/api/ai-workspace/questions/${questionLogId}/delete/`, {
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
    throw new Error(`AI question history delete API unavailable: ${response.status}`);
  }
  const payload = (await response.json()) as AIWorkspaceQuestionLogDeleteResponse;
  redirectIfLoginRequired(response, payload);
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || payload.message || `AI question history delete failed: ${response.status}`);
  }
  return payload;
}

export async function generateAIWorkspaceActionDraft(
  actionId: string,
  draftType: AIWorkspaceDraftType,
): Promise<AIWorkspaceActionDraftResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/reporting/api/ai-workspace/actions/draft/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ actionId, draftType }),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`AI action draft API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceActionDraftResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI action draft failed: ${response.status}`);
  }
  return data;
}

export async function submitAIWorkspaceActionFeedback(
  actionId: string,
  feedback: string,
): Promise<AIWorkspaceActionFeedbackResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/reporting/api/ai-workspace/actions/feedback/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ actionId, feedback }),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`AI action feedback API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceActionFeedbackResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI action feedback failed: ${response.status}`);
  }
  return data;
}

export async function askAIWorkspaceDepartmentQuestion(
  departmentId: number | null,
  question: string,
  model: AIWorkspaceQuestionModel | string,
  scopeType: AIWorkspaceQuestionScope = departmentId ? 'department' : 'all',
): Promise<AIWorkspaceDepartmentQuestionResponse> {
  const csrfToken = getCookie('csrftoken');
  const body = scopeType === 'all'
    ? { scopeType: 'all', question, model }
    : { scopeType: 'department', departmentId, question, model };
  const response = await fetch('/reporting/api/ai-workspace/question/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify(body),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`AI department question API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceDepartmentQuestionResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI department question failed: ${response.status}`);
  }
  return data;
}

export async function generateScheduleAICoach(scheduleId: number): Promise<ScheduleAICoachResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(`/reporting/api/schedules/${scheduleId}/ai-coach/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({}),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Schedule AI coach API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as ScheduleAICoachResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Schedule AI coach failed: ${response.status}`);
  }
  return data;
}

export async function submitAIWorkspaceQuestionFeedback(
  payload: AIWorkspaceQuestionFeedbackPayload,
): Promise<AIWorkspaceQuestionFeedbackResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/reporting/api/ai-workspace/question/feedback/', {
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
    throw new Error(`AI question feedback API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceQuestionFeedbackResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI question feedback failed: ${response.status}`);
  }
  return data;
}

export async function saveAIWorkspaceMemory(payload: AIWorkspaceMemoryPayload): Promise<AIWorkspaceMemoryResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch('/reporting/api/ai-workspace/memories/create/', {
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
    throw new Error(`AI memory API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceMemoryResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI memory save failed: ${response.status}`);
  }
  return data;
}

export async function loadAIWorkspaceMemories(params: AIWorkspaceMemoryFilters = {}): Promise<AIWorkspaceMemoriesData> {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'active') {
    query.set('status', params.status);
  }
  if (params.scope && params.scope !== 'any') {
    query.set('scope', params.scope);
  }
  if (params.memoryType) {
    query.set('memory_type', params.memoryType);
  }
  if (params.departmentId) {
    query.set('department_id', String(params.departmentId));
  }
  if (params.q?.trim()) {
    query.set('q', params.q.trim());
  }
  if (params.page && params.page > 1) {
    query.set('page', String(params.page));
  }
  const queryString = query.toString();
  const response = await fetch(`/reporting/api/ai-workspace/memories/${queryString ? `?${queryString}` : ''}`, {
    credentials: 'include',
    headers: {
      Accept: 'application/json',
    },
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`AI memories API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceMemoriesData;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI memories load failed: ${response.status}`);
  }
  return data;
}

export async function updateAIWorkspaceMemory(memoryId: number, payload: Partial<AIWorkspaceMemoryPayload>): Promise<AIWorkspaceMemoryResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(`/reporting/api/ai-workspace/memories/${memoryId}/update/`, {
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
    throw new Error(`AI memory update API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceMemoryResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI memory update failed: ${response.status}`);
  }
  return data;
}

export async function toggleAIWorkspaceMemory(memoryId: number, isActive: boolean): Promise<AIWorkspaceMemoryResponse> {
  const csrfToken = getCookie('csrftoken');
  const response = await fetch(`/reporting/api/ai-workspace/memories/${memoryId}/toggle-active/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ isActive }),
  });
  redirectIfLoginRequired(response);
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`AI memory toggle API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as AIWorkspaceMemoryResponse;
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `AI memory toggle failed: ${response.status}`);
  }
  return data;
}

export async function loadNavigationData(): Promise<NavigationData> {
  try {
    const response = await fetch('/reporting/api/navigation/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Navigation API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<NavigationData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || `Navigation API unavailable: ${response.status}`);
    }
    return {
      ...emptyNavigationData,
      ...payload,
      currentUser: {
        ...emptyNavigationData.currentUser,
        ...(payload.currentUser ?? {}),
      },
      capabilities: {
        ...emptyNavigationData.capabilities,
        ...(payload.capabilities ?? {}),
      },
      items: payload.items ?? [],
    };
  } catch (error) {
    return {
      ...emptyNavigationData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Navigation API unavailable',
    };
  }
}

export async function loadTasksData(params: { status?: string } = {}): Promise<TasksData> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  try {
    const response = await fetch(`/reporting/api/tasks/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Tasks API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<TasksData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Tasks API unavailable: ${response.status}`);
    }
    return {
      ...emptyTasksData,
      ...payload,
      currentUser: payload.currentUser ?? null,
      scope: {
        ...emptyTasksData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyTasksData.filters,
        ...(payload.filters ?? {}),
      },
      metrics: {
        ...emptyTasksData.metrics,
        ...(payload.metrics ?? {}),
      },
      options: {
        ...emptyTaskOptions,
        ...(payload.options ?? {}),
        statuses: payload.options?.statuses ?? [],
        statusFilters: payload.options?.statusFilters ?? emptyTaskOptions.statusFilters,
        durations: payload.options?.durations ?? [],
        assignees: payload.options?.assignees ?? [],
      },
      links: {
        ...emptyTasksLinks,
        ...(payload.links ?? {}),
      },
      tasks: {
        my: payload.tasks?.my ?? [],
        received: payload.tasks?.received ?? [],
        requested: payload.tasks?.requested ?? [],
      },
    };
  } catch (error) {
    return {
      ...emptyTasksData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Tasks API unavailable',
    };
  }
}

export async function loadTaskDetailData(taskId: number): Promise<TaskDetailData> {
  try {
    const response = await fetch(`/reporting/api/tasks/${taskId}/`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Task detail API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<TaskDetailData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Task detail API unavailable: ${response.status}`);
    }
    return {
      ...emptyTaskDetailData,
      ...payload,
      task: payload.task ?? null,
      attachments: payload.attachments ?? [],
      logs: payload.logs ?? [],
      options: {
        ...emptyTaskOptions,
        ...(payload.options ?? {}),
        statuses: payload.options?.statuses ?? [],
        statusFilters: payload.options?.statusFilters ?? emptyTaskOptions.statusFilters,
        durations: payload.options?.durations ?? [],
        assignees: payload.options?.assignees ?? [],
      },
      links: {
        ...emptyTaskDetailData.links,
        ...(payload.links ?? {}),
      },
    };
  } catch (error) {
    return {
      ...emptyTaskDetailData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Task detail API unavailable',
    };
  }
}

export async function loadTaskManagerData(params: { status?: string; assignee?: string } = {}): Promise<TaskManagerData> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.assignee) query.set('assignee', params.assignee);
  try {
    const response = await fetch(`/reporting/api/tasks/manager/${query.toString() ? `?${query.toString()}` : ''}`, {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Task manager API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<TaskManagerData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Task manager API unavailable: ${response.status}`);
    }
    return {
      ...emptyTaskManagerData,
      ...payload,
      scope: {
        ...emptyTaskManagerData.scope,
        ...(payload.scope ?? {}),
      },
      filters: {
        ...emptyTaskManagerData.filters,
        ...(payload.filters ?? {}),
      },
      metrics: {
        ...emptyTaskManagerData.metrics,
        ...(payload.metrics ?? {}),
      },
      options: {
        ...emptyTaskManagerData.options,
        ...(payload.options ?? {}),
        statusFilters: payload.options?.statusFilters ?? emptyTaskOptions.statusFilters,
        teamMembers: payload.options?.teamMembers ?? [],
      },
      links: {
        ...emptyTaskManagerData.links,
        ...(payload.links ?? {}),
      },
      teamSummary: payload.teamSummary ?? [],
      tasks: payload.tasks ?? [],
    };
  } catch (error) {
    return {
      ...emptyTaskManagerData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Task manager API unavailable',
    };
  }
}

async function postTaskJson<TPayload, TResponse = TaskMutationResponse>(submitUrl: string, payload: TPayload): Promise<TResponse> {
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
    throw new Error(`Task mutation API unavailable: ${response.status}`);
  }
  const data = (await response.json()) as TResponse & { success?: boolean; error?: string; message?: string };
  redirectIfLoginRequired(response, data);
  if (!response.ok || data.success === false) {
    throw new Error(data.error || data.message || `Task mutation failed: ${response.status}`);
  }
  return data;
}

export const createTask = (submitUrl: string, payload: TaskFormPayload) =>
  postTaskJson<TaskFormPayload>(submitUrl, payload);

export const requestTask = (submitUrl: string, payload: TaskRequestPayload) =>
  postTaskJson<TaskRequestPayload>(submitUrl, payload);

export const changeTaskStatus = (submitUrl: string, payload: { action?: string; status?: string; reason?: string }) =>
  postTaskJson<{ action?: string; status?: string; reason?: string }>(submitUrl, payload);

export const updateTask = (submitUrl: string, payload: TaskFormPayload) =>
  postTaskJson<TaskFormPayload, TaskDetailData>(submitUrl, payload);

export const deleteTask = (submitUrl: string) =>
  postTaskJson<Record<string, never>, TaskMutationResponse>(submitUrl, {});

export async function uploadTaskAttachments(submitUrl: string, files: File[]): Promise<TaskDetailData> {
  const csrfToken = getCookie('csrftoken');
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
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
    throw new Error(`Task attachment API unavailable: ${response.status}`);
  }
  const payload = (await response.json()) as Partial<TaskDetailData>;
  redirectIfLoginRequired(response, payload);
  if (!response.ok || payload.success === false || payload.source !== 'django') {
    throw new Error(payload.error || payload.message || `Task attachment upload failed: ${response.status}`);
  }
  return {
    ...emptyTaskDetailData,
    ...payload,
    task: payload.task ?? null,
    attachments: payload.attachments ?? [],
    logs: payload.logs ?? [],
    options: {
      ...emptyTaskOptions,
      ...(payload.options ?? {}),
      statuses: payload.options?.statuses ?? [],
      statusFilters: payload.options?.statusFilters ?? emptyTaskOptions.statusFilters,
      durations: payload.options?.durations ?? [],
      assignees: payload.options?.assignees ?? [],
    },
    links: {
      ...emptyTaskDetailData.links,
      ...(payload.links ?? {}),
    },
  };
}

export const assignManagerTask = (submitUrl: string, payload: TaskManagerAssignPayload) =>
  postTaskJson<TaskManagerAssignPayload>(submitUrl, payload);

export const changeManagerTaskStatus = (submitUrl: string, payload: { status: string }) =>
  postTaskJson<{ status: string }>(submitUrl, payload);

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
    const deals = payload.deals.map((deal) => ({
      ...deal,
      detailUrl: normalizeCoreCrmHref(deal.detailUrl),
      aiDepartment: deal.aiDepartment
        ? normalizeCustomerAiDepartment(deal.aiDepartment as Partial<CustomerAiDepartment>)
        : deal.aiDepartment,
    }));
    return {
      ...payload,
      deals,
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
