import { assertSuccessfulJsonPayload, csrfHeaders, fetchJson } from './shared';

export type MeetingMovementItem = {
  followupId: number;
  customer: string;
  company: string;
  owner: string;
  ownerId: number;
  fromStage: string;
  fromLabel: string;
  toStage: string;
  toLabel: string;
  amount: number;
  href: string;
};

export type MeetingMovementGroup = { count: number; amount: number; items: MeetingMovementItem[] };

export type MeetingActionItem = {
  id: number;
  kind: 'promise' | 'report';
  dueReached: boolean;
  title: string;
  ownerId: number;
  owner: string;
  dueDate: string | null;
  overdue: boolean;
  status: 'open' | 'done';
  customer: string;
  company: string;
  followupId: number | null;
  href: string;
  carriedWeeks: number;
  canEdit: boolean;
};

export type MeetingNextAction = {
  id: number;
  customer: string;
  company: string;
  owner: string;
  ownerId: number;
  text: string;
  dueDate: string;
  followedUp: boolean;
  href: string;
};

export type MeetingServiceRecord = {
  id: number;
  institution: string;
  content: string;
  createdAt: string;
  canEdit: boolean;
};

export type MeetingPlanItem = {
  id: number;
  date: string;
  weekday: string;
  time: string;
  type: string;
  typeLabel: string;
  customer: string;
  company: string;
  amount: number;
  href: string;
};

export type PipelineMeetingData = {
  success?: boolean;
  source: 'django';
  week: { start: string; end: string; isCurrent: boolean };
  weekOptions: { value: string; label: string; weekStart: string; weekEnd: string }[];
  scope: {
    label: string;
    canSelectUser: boolean;
    selectedUserId: number | null;
    users: { id: number; name: string }[];
  };
  summary: {
    yearRevenue: number;
    lastYearRevenue: number;
    weekRevenue: number;
    previousWeekRevenue: number;
    weekDelta: number;
    deliveryCount: number;
    quoteAmount: number;
    activeAccounts: number;
    /** 기록이 없는 주는 null */
    lostAmount: number | null;
  };
  movement: {
    won: MeetingMovementGroup;
    advanced: MeetingMovementGroup;
    regressed: MeetingMovementGroup;
    lost: MeetingMovementGroup;
    created: MeetingMovementGroup;
    tracked: boolean;
    restored: boolean;
    trackingSince: string | null;
  };
  promises: { actionItems: MeetingActionItem[]; nextActions: MeetingNextAction[] };
  services: MeetingServiceRecord[];
  plan: {
    start: string;
    end: string;
    total: number;
    byOwner: { ownerId: number; owner: string; items: MeetingPlanItem[] }[];
  };
  form: {
    institutions: string[];
    owners: { id: number; name: string }[];
    customers: { id: number; label: string }[];
  };
};

export type MeetingActionPayload = {
  title: string;
  kind?: 'promise' | 'report';
  ownerId?: number;
  dueDate?: string;
  followupId?: number;
};

const API = '/reporting/api/pipeline-meeting/';

export async function loadPipelineMeeting(params: { week?: string; user?: number | null }): Promise<PipelineMeetingData> {
  const query = new URLSearchParams();
  if (params.week) query.set('week', params.week);
  if (params.user) query.set('user', String(params.user));
  const { response, payload } = await fetchJson<PipelineMeetingData>(
    `${API}${query.toString() ? `?${query.toString()}` : ''}`,
    {},
    'Pipeline meeting API unavailable',
  );
  assertSuccessfulJsonPayload(response, payload, 'Pipeline meeting API unavailable', { requireDjangoSource: true });
  return payload;
}

async function postJson<T>(href: string, body: unknown, label: string): Promise<T> {
  const { response, payload } = await fetchJson<T & { success?: boolean }>(
    href,
    {
      method: 'POST',
      headers: csrfHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body ?? {}),
    },
    label,
  );
  assertSuccessfulJsonPayload(response, payload, label);
  return payload;
}

export async function createMeetingAction(body: MeetingActionPayload): Promise<MeetingActionItem> {
  const result = await postJson<{ item: MeetingActionItem }>(`${API}actions/create/`, body, '약속을 저장하지 못했습니다.');
  return result.item;
}

export async function toggleMeetingAction(id: number): Promise<MeetingActionItem> {
  const result = await postJson<{ item: MeetingActionItem }>(`${API}actions/${id}/toggle/`, {}, '약속을 변경하지 못했습니다.');
  return result.item;
}

export async function deleteMeetingAction(id: number): Promise<void> {
  await postJson(`${API}actions/${id}/delete/`, {}, '약속을 삭제하지 못했습니다.');
}

export async function dismissMeetingNextAction(noteId: number): Promise<void> {
  await postJson(`${API}next-actions/${noteId}/dismiss/`, {}, '목록에서 숨기지 못했습니다.');
}

export async function restoreMeetingNextAction(noteId: number): Promise<void> {
  await postJson(`${API}next-actions/${noteId}/restore/`, {}, '되돌리지 못했습니다.');
}

export async function createMeetingService(body: {
  institution: string;
  content: string;
  week: string;
}): Promise<MeetingServiceRecord> {
  const result = await postJson<{ record: MeetingServiceRecord }>(`${API}services/create/`, body, '서비스 기록을 저장하지 못했습니다.');
  return result.record;
}

export async function updateMeetingService(id: number, body: { institution: string; content: string }): Promise<MeetingServiceRecord> {
  const result = await postJson<{ record: MeetingServiceRecord }>(`${API}services/${id}/update/`, body, '서비스 기록을 수정하지 못했습니다.');
  return result.record;
}

export async function reorderMeetingServices(week: string, ids: number[]): Promise<void> {
  await postJson(`${API}services/reorder/`, { week, ids }, '순서를 저장하지 못했습니다.');
}

export async function updateMeetingAction(id: number, title: string): Promise<MeetingActionItem> {
  const result = await postJson<{ item: MeetingActionItem }>(`${API}actions/${id}/update/`, { title }, '내용을 수정하지 못했습니다.');
  return result.item;
}

export async function deleteMeetingService(id: number): Promise<void> {
  await postJson(`${API}services/${id}/delete/`, {}, '서비스 기록을 삭제하지 못했습니다.');
}
