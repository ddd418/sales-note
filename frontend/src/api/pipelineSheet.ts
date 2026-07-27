import { assertSuccessfulJsonPayload, fetchJson } from './shared';

export type PipelineSheetOption = {
  value: string;
  label: string;
};

export type PipelineSheetScope = {
  label: string;
  canSelectUser: boolean;
  selectedUserId: number | null;
  users: { id: number; name: string }[];
};

export type PipelineSheetStage = {
  id: string;
  label: string;
  color: string;
};

export type PipelineSheetActivity = {
  kind: 'history' | 'schedule';
  id: number;
  date: string;
  weekday: string;
  type: string;
  body: string;
  obstacle: string;
  nextAction: string;
  nextActionDate: string | null;
  amount: number;
  href: string;
};

export type PipelineSheetWeeklyRow = {
  accountKey: string;
  accountId: number | null;
  accountType: string;
  company: string;
  department: string;
  contact: string;
  owner: string;
  ownerId: number | null;
  stage: string;
  stageLabel: string;
  amount: number;
  probability: number | null;
  weightedAmount: number;
  href: string;
  activities: PipelineSheetActivity[];
  activityCount: number;
  weekAmount: number;
  nextAction: string;
  nextActionDate: string | null;
  hasObstacle: boolean;
};

export type PipelineSheetUntouchedAccount = {
  accountKey: string;
  company: string;
  department: string;
  stage: string;
  stageLabel: string;
  amount: number;
  href: string;
};

export type PipelineSheetWeeklyData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  week: {
    start: string;
    end: string;
    label: string;
    isCurrent: boolean;
  };
  weekOptions: { value: string; label: string; weekStart: string; weekEnd: string }[];
  scope: PipelineSheetScope;
  stages: PipelineSheetStage[];
  stageTotals: Record<string, { count: number; amount: number }>;
  rows: PipelineSheetWeeklyRow[];
  untouchedAccounts: PipelineSheetUntouchedAccount[];
  metrics: {
    activeAccounts: number;
    totalActivities: number;
    untouchedCount: number;
    untouchedAmount: number;
  };
};

export type PipelineSheetQuote = {
  id: number | null;
  recordType: string;
  number: string;
  date: string | null;
  amount: number;
  status: string;
  statusLabel: string;
  converted: boolean;
  ageDays: number | null;
  source: string;
  href: string;
};

export type PipelineSheetQuoteRow = {
  accountKey: string;
  accountId: number | null;
  accountType: string;
  company: string;
  department: string;
  contact: string;
  owner: string;
  ownerId: number | null;
  stage: string;
  stageLabel: string;
  amount: number;
  probability: number | null;
  weightedAmount: number;
  href: string;
  quoteCount: number;
  quoteAmount: number;
  convertedCount: number;
  convertedAmount: number;
  conversionRate: number;
  conversionAmountRate: number;
  pendingCount: number;
  pendingAmount: number;
  deadCount: number;
  latestQuoteDate: string | null;
  latestQuoteAgeDays: number | null;
  quotes: PipelineSheetQuote[];
};

export type PipelineSheetQuotesData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  scope: PipelineSheetScope;
  filters: {
    filter: string;
    query: string;
    sort: string;
  };
  sortOptions: PipelineSheetOption[];
  rows: PipelineSheetQuoteRow[];
  metrics: {
    accounts: number;
    quoteCount: number;
    quoteAmount: number;
    convertedCount: number;
    convertedAmount: number;
    conversionRate: number;
    conversionAmountRate: number;
  };
};

const emptyScope: PipelineSheetScope = {
  label: '',
  canSelectUser: false,
  selectedUserId: null,
  users: [],
};

export type PipelineSheetWeeklyParams = {
  week?: string;
  user?: number | null;
};

export type PipelineSheetQuotesParams = {
  filter?: string;
  query?: string;
  sort?: string;
  user?: number | null;
};

function weeklyQuery(params: PipelineSheetWeeklyParams): URLSearchParams {
  const query = new URLSearchParams();
  if (params.week) query.set('week', params.week);
  if (params.user) query.set('user', String(params.user));
  return query;
}

function quotesQuery(params: PipelineSheetQuotesParams): URLSearchParams {
  const query = new URLSearchParams();
  if (params.filter && params.filter !== 'all') query.set('filter', params.filter);
  if (params.query?.trim()) query.set('q', params.query.trim());
  if (params.sort) query.set('sort', params.sort);
  if (params.user) query.set('user', String(params.user));
  return query;
}

export async function loadPipelineSheetWeekly(
  params: PipelineSheetWeeklyParams = {},
): Promise<PipelineSheetWeeklyData> {
  const query = weeklyQuery(params);
  const href = `/reporting/api/pipeline-sheet/weekly/${query.toString() ? `?${query.toString()}` : ''}`;
  const { response, payload } = await fetchJson<PipelineSheetWeeklyData>(
    href,
    {},
    'Pipeline sheet API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'Pipeline sheet API unavailable', {
    requireDjangoSource: true,
  });
  return {
    ...payload,
    scope: { ...emptyScope, ...(payload.scope ?? {}) },
    stages: payload.stages ?? [],
    stageTotals: payload.stageTotals ?? {},
    rows: payload.rows ?? [],
    untouchedAccounts: payload.untouchedAccounts ?? [],
    weekOptions: payload.weekOptions ?? [],
  };
}

export async function loadPipelineSheetQuotes(
  params: PipelineSheetQuotesParams = {},
): Promise<PipelineSheetQuotesData> {
  const query = quotesQuery(params);
  const href = `/reporting/api/pipeline-sheet/quotes/${query.toString() ? `?${query.toString()}` : ''}`;
  const { response, payload } = await fetchJson<PipelineSheetQuotesData>(
    href,
    {},
    'Pipeline sheet API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'Pipeline sheet API unavailable', {
    requireDjangoSource: true,
  });
  return {
    ...payload,
    scope: { ...emptyScope, ...(payload.scope ?? {}) },
    sortOptions: payload.sortOptions ?? [],
    rows: payload.rows ?? [],
  };
}

/** 화면과 같은 파라미터로 워크북을 내려받는다(주간 활동 + 미접촉 + 견적 전환). */
export function pipelineSheetExportHref(
  weekly: PipelineSheetWeeklyParams,
  quotes: PipelineSheetQuotesParams,
): string {
  const query = weeklyQuery(weekly);
  quotesQuery(quotes).forEach((value, key) => {
    if (!query.has(key)) {
      query.set(key, value);
    }
  });
  return `/reporting/api/pipeline-sheet/export/${query.toString() ? `?${query.toString()}` : ''}`;
}
