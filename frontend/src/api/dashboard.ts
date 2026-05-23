import { normalizeHrefFields, redirectIfLoginRequired } from './shared';

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

function normalizeScheduleLinks(item: DashboardScheduleItem): DashboardScheduleItem {
  return normalizeHrefFields(item, [
    'href',
    'djangoHref',
    'customerHref',
    'djangoCustomerHref',
    'createHistoryHref',
    'djangoCreateHistoryHref',
    'djangoEditHref',
  ]);
}

function normalizeCustomerLinks(item: DashboardCustomerItem): DashboardCustomerItem {
  return normalizeHrefFields(item, ['href', 'accountHref', 'customerHref', 'companyHref', 'createScheduleHref']);
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
