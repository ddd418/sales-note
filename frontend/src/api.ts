import { mockPipelineData, PipelineData, PipelineStage } from './mockData';

type PipelineApiResponse = PipelineData & {
  success?: boolean;
};

type PipelineMoveResponse = {
  success?: boolean;
  error?: string;
};

function getCookie(name: string): string {
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));
  return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : '';
}

export async function loadPipelineData(): Promise<PipelineData> {
  try {
    const response = await fetch('/reporting/api/pipeline/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    const contentType = response.headers.get('content-type') || '';
    if (!response.ok || !contentType.includes('application/json')) {
      throw new Error(`Pipeline API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as PipelineApiResponse;
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
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(`Pipeline move API unavailable: ${response.status}`);
  }
  const payload = (await response.json()) as PipelineMoveResponse;
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || `Pipeline move failed: ${response.status}`);
  }
}
