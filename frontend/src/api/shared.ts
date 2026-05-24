// Shared browser API helpers used by the CRM API modules.

export function getCookie(name: string): string {
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

export function redirectIfLoginRequired(response: Response, payload?: unknown): void {
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

export function normalizeCoreCrmHref(href?: string | null): string {
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
  match = pathname.match(/^\/reporting\/schedules\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactHref(`/schedules/${match[1]}/`, params, { extra: { delete: '1' } });
  }
  match = pathname.match(/^\/reporting\/schedules\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactHref(`/schedules/${match[1]}/`, params);
  }
  if (pathname === '/reporting/personal-schedules/create/' || pathname === '/reporting/personal-schedules/create') {
    return buildReactHref('/schedules/calendar/', params, { extra: { create: 'personal' } });
  }
  match = pathname.match(/^\/reporting\/personal-schedules\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactHref('/schedules/calendar/', params, { extra: { personal: match[1], edit: '1' } });
  }
  match = pathname.match(/^\/reporting\/personal-schedules\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactHref('/schedules/calendar/', params, { extra: { personal: match[1], delete: '1' } });
  }
  match = pathname.match(/^\/reporting\/personal-schedules\/(\d+)\/?$/);
  if (match) {
    return buildReactHref('/schedules/calendar/', params, { extra: { personal: match[1] } });
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

export function normalizeHrefFields<T extends object>(item: T, fields: string[]): T {
  const normalized: Record<string, unknown> = { ...(item as Record<string, unknown>) };
  fields.forEach((field) => {
    if (typeof normalized[field] === 'string') {
      normalized[field] = normalizeCoreCrmHref(normalized[field] as string);
    }
  });
  return normalized as T;
}
