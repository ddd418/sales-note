import { assertSuccessfulJsonPayload, csrfHeaders, fetchJson } from './shared';

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
  /** 본인 기록(또는 admin)일 때만 그리드에서 바로 수정할 수 있다. */
  editable: boolean;
};

export type PipelineSheetActivityPatch = {
  body?: string;
  obstacle?: string;
  nextAction?: string;
  nextActionDate?: string;
};

export async function updatePipelineSheetActivity(
  kind: 'history' | 'schedule',
  id: number,
  patch: PipelineSheetActivityPatch,
): Promise<PipelineSheetActivity> {
  const href = `/reporting/api/pipeline-sheet/activities/${kind}/${id}/update/`;
  const { response, payload } = await fetchJson<{ success?: boolean; activity: PipelineSheetActivity }>(
    href,
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(patch),
    },
    '활동을 저장하지 못했습니다.',
  );
  assertSuccessfulJsonPayload(response, payload, '활동을 저장하지 못했습니다.');
  return payload.activity;
}

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
  metrics: {
    activeAccounts: number;
    totalActivities: number;
    quoteAmount: number;
    deliveryAmount: number;
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

function weeklyQuery(params: PipelineSheetWeeklyParams): URLSearchParams {
  const query = new URLSearchParams();
  if (params.week) query.set('week', params.week);
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
    weekOptions: payload.weekOptions ?? [],
  };
}

/** 화면과 같은 파라미터로 워크북을 내려받는다(주간 활동). */
export function pipelineSheetExportHref(weekly: PipelineSheetWeeklyParams): string {
  const query = weeklyQuery(weekly);
  return `/reporting/api/pipeline-sheet/export/${query.toString() ? `?${query.toString()}` : ''}`;
}
