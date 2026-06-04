import { assertSuccessfulJsonPayload, csrfHeaders, fetchJson } from './shared';

export type AIWorkspaceQuestionScope = 'department' | 'all';
export type AIWorkspaceQuestionModel = 'gpt-5.4-nano';
export type AIWorkspaceQuestionFeedbackRating = 'helpful' | 'needs_style' | 'incorrect';
export type AIWorkspaceMemoryType = 'fact' | 'correction' | 'preference';

export type AIWorkspaceActionEvidence = {
  label: string;
  value: string;
  href?: string;
  linkLabel?: string;
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

export type AIWorkspaceFeaturedDepartment = {
  departmentId: number;
  departmentName: string;
  companyName: string;
  customerCount: number;
  customerPreview: string[];
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
};

export type AIWorkspaceQuestionModelChoice = {
  id: AIWorkspaceQuestionModel | string;
  label: string;
};

export type AIWorkspaceQuestionAnswer = {
  summary: string;
  bullets: string[];
  evidence: AIWorkspaceActionEvidence[];
  confidence: 'high' | 'medium' | 'low' | string;
};

export type AIWorkspaceQuestionLog = {
  id: number;
  scopeType: AIWorkspaceQuestionScope | string;
  question: string;
  answerSummary?: string;
  answer?: Partial<AIWorkspaceQuestionAnswer> | Record<string, unknown>;
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
  byKind: Array<{
    kind: string;
    kindLabel: string;
    count: number;
  }>;
  recent: Array<Record<string, unknown>>;
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
    customers: string;
    notes: string;
    dashboard: string;
  };
  week: {
    start: string;
    end: string;
  };
  dailyBrief: AIWorkspaceDailyBrief;
  actionQueue: Array<Record<string, unknown>>;
  feedbackHistory: AIWorkspaceFeedbackHistory;
  departments: AIWorkspaceDepartment[];
  featuredDepartment: AIWorkspaceFeaturedDepartment | null;
  selectedDepartmentId: number | null;
  questionHistory: AIWorkspaceQuestionHistory;
  questionModelChoices: AIWorkspaceQuestionModelChoice[];
  defaultQuestionModel: AIWorkspaceQuestionModel | string;
  recommendedGoals: Array<{
    title: string;
    description: string;
    reason: string;
    customer?: string;
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

export type AIWorkspaceDepartmentQuestionResponse = {
  success?: boolean;
  source: 'openai' | 'fallback' | 'ledger';
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
  };
  requiresHumanReview: boolean;
  error?: string;
  message?: string;
};

export type AIWorkspaceQuestionFeedbackPayload = {
  departmentId?: number | null;
  scopeType?: AIWorkspaceQuestionScope;
  question: string;
  answer: AIWorkspaceQuestionAnswer;
  source?: AIWorkspaceDepartmentQuestionResponse['source'];
  rating: AIWorkspaceQuestionFeedbackRating;
  comment?: string;
};

export type AIWorkspaceQuestionFeedbackResponse = {
  success?: boolean;
  generatedAt: string;
  error?: string;
  message?: string;
};

export type AIWorkspaceMemoryPayload = {
  departmentId?: number | null;
  scopeType?: AIWorkspaceQuestionScope;
  questionLogId?: number | null;
  feedbackId?: number | null;
  memoryType: AIWorkspaceMemoryType;
  title?: string;
  content: string;
};

export type AIWorkspaceMemoryItem = {
  id: number;
  scopeType: AIWorkspaceQuestionScope | string;
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
  generatedAt: string;
  links?: {
    aiWorkspace?: string;
  };
  error?: string;
  message?: string;
};

function queryString(params: AIWorkspaceLoadParams): string {
  const query = new URLSearchParams();
  if (params.departmentId) query.set('department_id', String(params.departmentId));
  if (params.questionPage && params.questionPage > 1) query.set('question_page', String(params.questionPage));
  if (params.questionScope === 'all') query.set('question_scope', 'all');
  return query.toString();
}

export async function loadAIWorkspaceData(params: AIWorkspaceLoadParams = {}): Promise<AIWorkspaceData> {
  const query = queryString(params);
  const { response, payload } = await fetchJson<AIWorkspaceData>(
    `/reporting/api/ai-workspace/${query ? `?${query}` : ''}`,
    {},
    'AI workspace API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI workspace API unavailable', { requireDjangoSource: true });
  return {
    ...payload,
    departments: payload.departments ?? [],
    actionQueue: payload.actionQueue ?? [],
    questionModelChoices: payload.questionModelChoices ?? [],
    selectedDepartmentId: payload.selectedDepartmentId ?? payload.featuredDepartment?.departmentId ?? null,
  };
}

export async function loadAIWorkspaceQuestionLogDetailData(questionLogId: number): Promise<AIWorkspaceQuestionLogDetailData> {
  const { response, payload } = await fetchJson<AIWorkspaceQuestionLogDetailData>(
    `/reporting/api/ai-workspace/questions/${questionLogId}/`,
    {},
    'AI question detail API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI question detail unavailable', { requireDjangoSource: true });
  return {
    ...payload,
    links: {
      aiWorkspace: payload.links?.aiWorkspace || '/ai-workspace/',
    },
    questionLog: payload.questionLog ?? null,
  };
}

export async function askAIWorkspaceDepartmentQuestion(
  departmentId: number | null,
  question: string,
  model: AIWorkspaceQuestionModel | string,
  scopeType: AIWorkspaceQuestionScope = departmentId ? 'department' : 'all',
): Promise<AIWorkspaceDepartmentQuestionResponse> {
  const body = scopeType === 'all'
    ? { scopeType: 'all', question, model }
    : { scopeType: 'department', departmentId, question, model };
  const { response, payload } = await fetchJson<AIWorkspaceDepartmentQuestionResponse>(
    '/reporting/api/ai-workspace/question/',
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    },
    'AI department question API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI department question failed');
  return payload;
}

export async function submitAIWorkspaceQuestionFeedback(
  payload: AIWorkspaceQuestionFeedbackPayload,
): Promise<AIWorkspaceQuestionFeedbackResponse> {
  const { response, payload: result } = await fetchJson<AIWorkspaceQuestionFeedbackResponse>(
    '/reporting/api/ai-workspace/question/feedback/',
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    },
    'AI question feedback API unavailable',
  );
  assertSuccessfulJsonPayload(response, result, 'AI question feedback failed');
  return result;
}

export async function saveAIWorkspaceMemory(payload: AIWorkspaceMemoryPayload): Promise<AIWorkspaceMemoryResponse> {
  const { response, payload: result } = await fetchJson<AIWorkspaceMemoryResponse>(
    '/reporting/api/ai-workspace/memories/create/',
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    },
    'AI memory API unavailable',
  );
  assertSuccessfulJsonPayload(response, result, 'AI memory save failed');
  return result;
}

export async function loadAIWorkspaceMemories(params: AIWorkspaceMemoryFilters = {}): Promise<AIWorkspaceMemoriesData> {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'active') query.set('status', params.status);
  if (params.scope && params.scope !== 'any') query.set('scope', params.scope);
  if (params.memoryType) query.set('memory_type', params.memoryType);
  if (params.departmentId) query.set('department_id', String(params.departmentId));
  if (params.q?.trim()) query.set('q', params.q.trim());
  if (params.page && params.page > 1) query.set('page', String(params.page));
  const queryValue = query.toString();
  const { response, payload } = await fetchJson<AIWorkspaceMemoriesData>(
    `/reporting/api/ai-workspace/memories/${queryValue ? `?${queryValue}` : ''}`,
    {},
    'AI memories API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI memories load failed', { requireDjangoSource: true });
  return payload;
}

export async function updateAIWorkspaceMemory(
  memoryId: number,
  payload: Partial<AIWorkspaceMemoryPayload>,
): Promise<AIWorkspaceMemoryResponse> {
  const { response, payload: result } = await fetchJson<AIWorkspaceMemoryResponse>(
    `/reporting/api/ai-workspace/memories/${memoryId}/update/`,
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    },
    'AI memory update API unavailable',
  );
  assertSuccessfulJsonPayload(response, result, 'AI memory update failed');
  return result;
}

export async function toggleAIWorkspaceMemory(memoryId: number, isActive: boolean): Promise<AIWorkspaceMemoryResponse> {
  const { response, payload } = await fetchJson<AIWorkspaceMemoryResponse>(
    `/reporting/api/ai-workspace/memories/${memoryId}/toggle-active/`,
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ isActive }),
    },
    'AI memory toggle API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI memory toggle failed');
  return payload;
}

export async function deleteAIWorkspaceQuestionLog(questionLogId: number): Promise<AIWorkspaceQuestionLogDeleteResponse> {
  const { response, payload } = await fetchJson<AIWorkspaceQuestionLogDeleteResponse>(
    `/reporting/api/ai-workspace/questions/${questionLogId}/delete/`,
    {
      method: 'POST',
      headers: csrfHeaders(),
    },
    'AI question history delete API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'AI question history delete failed');
  return payload;
}
