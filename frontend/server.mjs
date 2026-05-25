import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distDir = join(__dirname, 'dist');
const port = Number(process.env.PORT || 4173);
const djangoBaseUrl = new URL(process.env.DJANGO_BASE_URL || 'http://127.0.0.1:8000');

const mimeTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};

const hopByHopHeaders = new Set([
  'connection',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
]);

function sendStatic(response, filePath) {
  const extension = extname(filePath);
  response.writeHead(200, {
    'Cache-Control': extension === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable',
    'Content-Type': mimeTypes[extension] || 'application/octet-stream',
  });
  createReadStream(filePath).pipe(response);
}

function sendJson(response, statusCode, body) {
  response.writeHead(statusCode, {
    'Cache-Control': 'no-store',
    'Content-Type': 'application/json; charset=utf-8',
  });
  response.end(JSON.stringify(body));
}

function resolveStaticPath(urlPath) {
  const decodedPath = decodeURIComponent(urlPath.split('?')[0]);
  const safePath = normalize(decodedPath).replace(/^(\.\.[/\\])+/, '');
  const candidate = join(distDir, safePath === '/' ? 'index.html' : safePath);
  if (candidate.startsWith(distDir) && existsSync(candidate) && statSync(candidate).isFile()) {
    return candidate;
  }
  return join(distDir, 'index.html');
}

function proxyToDjango(clientRequest, clientResponse) {
  const target = new URL(clientRequest.url || '/', djangoBaseUrl);
  if (target.protocol !== 'http:' && target.protocol !== 'https:') {
    clientResponse.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
    clientResponse.end('Django upstream URL must use http or https.');
    return;
  }

  const headers = Object.fromEntries(
    Object.entries(clientRequest.headers).filter(([key]) => !hopByHopHeaders.has(key.toLowerCase())),
  );
  headers.host = clientRequest.headers.host || djangoBaseUrl.host;
  headers['x-forwarded-host'] = clientRequest.headers.host || djangoBaseUrl.host;
  headers['x-forwarded-proto'] = 'https';

  const proxyRequest = (target.protocol === 'https:' ? httpsRequest : httpRequest)(
    {
      protocol: target.protocol,
      hostname: target.hostname,
      port: target.port,
      path: `${target.pathname}${target.search}`,
      method: clientRequest.method,
      headers,
    },
    (proxyResponse) => {
      const responseHeaders = Object.fromEntries(
        Object.entries(proxyResponse.headers).filter(([key]) => !hopByHopHeaders.has(key.toLowerCase())),
      );
      clientResponse.writeHead(proxyResponse.statusCode || 502, responseHeaders);
      proxyResponse.pipe(clientResponse);
    },
  );

  proxyRequest.on('error', () => {
    if (clientResponse.destroyed) {
      return;
    }
    if (clientResponse.headersSent) {
      clientResponse.destroy();
      return;
    }
    clientResponse.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
    clientResponse.end('Django upstream is unavailable.');
  });

  clientRequest.pipe(proxyRequest);
}

function getPathname(requestUrl) {
  try {
    return new URL(requestUrl, 'http://frontend.local').pathname;
  } catch {
    return requestUrl.split('?')[0];
  }
}

function buildReactLocation(pathname, sourceParams, options = {}) {
  const rename = options.rename || {};
  const drop = new Set(options.drop || []);
  const params = new URLSearchParams();

  for (const [key, value] of sourceParams.entries()) {
    const targetKey = rename[key] || key;
    if (drop.has(key) || drop.has(targetKey)) {
      continue;
    }
    params.append(targetKey, value);
  }

  for (const [key, value] of Object.entries(options.extra || {})) {
    params.set(key, String(value));
  }

  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function getCoreCrmReactLocation(requestUrl) {
  let parsed;
  try {
    parsed = new URL(requestUrl || '/', 'http://frontend.local');
  } catch {
    return '';
  }

  const pathname = parsed.pathname;
  const params = parsed.searchParams;
  let match;

  if (pathname === '/reporting/dashboard/' || pathname === '/reporting/dashboard') {
    return buildReactLocation('/dashboard/', params);
  }
  if (pathname === '/reporting/followups/' || pathname === '/reporting/followups') {
    return buildReactLocation('/customers/', params, { rename: { pipeline_stage: 'stage' } });
  }
  if (pathname === '/reporting/followups/create/' || pathname === '/reporting/followups/create') {
    return buildReactLocation('/customers/', params, { extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/followups\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactLocation(`/customers/${match[1]}/`, params);
  }
  if (pathname === '/reporting/customer-report/' || pathname === '/reporting/customer-report') {
    return buildReactLocation('/customers/', params);
  }
  match = pathname.match(/^\/reporting\/customer-report\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/customers/${match[1]}/`, params);
  }

  if (pathname === '/reporting/histories/' || pathname === '/reporting/histories') {
    return buildReactLocation('/notes/', params);
  }
  match = pathname.match(/^\/reporting\/histories\/create-from-schedule\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation('/notes/', params, { extra: { create: '1', schedule: match[1] } });
  }
  match = pathname.match(/^\/reporting\/histories\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactLocation(`/notes/${match[1]}/`, params);
  }

  if (pathname === '/reporting/schedules/' || pathname === '/reporting/schedules') {
    return buildReactLocation('/schedules/', params);
  }
  if (pathname === '/reporting/schedules/calendar/' || pathname === '/reporting/schedules/calendar') {
    return buildReactLocation('/schedules/calendar/', params);
  }
  if (pathname === '/reporting/schedules/create/' || pathname === '/reporting/schedules/create') {
    return buildReactLocation('/schedules/', params, { rename: { followup: 'customer' }, extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/schedules\/(\d+)\/(?:edit\/?)?$/);
  if (match) {
    return buildReactLocation(`/schedules/${match[1]}/`, params);
  }

  if (
    pathname === '/reporting/funnel/' ||
    pathname === '/reporting/funnel' ||
    pathname === '/reporting/funnel/pipeline/' ||
    pathname === '/reporting/funnel/pipeline'
  ) {
    return buildReactLocation('/pipeline/', params);
  }
  if (/^\/reporting\/funnel\/\d+\/?$/.test(pathname)) {
    return buildReactLocation('/pipeline/', params);
  }
  if (pathname === '/reporting/analytics/' || pathname === '/reporting/analytics') {
    return buildReactLocation('/reports/', params);
  }
  if (
    pathname === '/reporting/users/' ||
    pathname === '/reporting/users' ||
    pathname === '/reporting/manager/users/' ||
    pathname === '/reporting/manager/users'
  ) {
    return buildReactLocation('/employees/', params, { rename: { search: 'q' } });
  }
  if (
    pathname === '/reporting/users/create/' ||
    pathname === '/reporting/users/create' ||
    pathname === '/reporting/manager/users/create/' ||
    pathname === '/reporting/manager/users/create'
  ) {
    return buildReactLocation('/employees/', params, { extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/(?:manager\/)?users\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation('/employees/', params, { extra: { employee: match[1], edit: '1' } });
  }
  match = pathname.match(/^\/reporting\/users\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactLocation('/employees/', params, { extra: { employee: match[1] } });
  }
  if (pathname === '/reporting/prepayment/' || pathname === '/reporting/prepayment') {
    return buildReactLocation('/prepayments/', params, { rename: { search: 'q' } });
  }
  if (pathname === '/reporting/prepayment/create/' || pathname === '/reporting/prepayment/create') {
    return buildReactLocation('/prepayments/new/', params);
  }
  match = pathname.match(/^\/reporting\/prepayment\/customer\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/prepayments/customer/${match[1]}/`, params);
  }
  match = pathname.match(/^\/reporting\/prepayment\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation(`/prepayments/${match[1]}/edit/`, params);
  }
  match = pathname.match(/^\/reporting\/prepayment\/(\d+)\/(?:delete|transfer)\/?$/);
  if (match) {
    return buildReactLocation(`/prepayments/${match[1]}/`, params);
  }
  match = pathname.match(/^\/reporting\/prepayment\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/prepayments/${match[1]}/`, params);
  }

  if (pathname === '/todos/' || pathname === '/todos') {
    return buildReactLocation('/tasks/', params);
  }
  if (pathname === '/todos/create/' || pathname === '/todos/create') {
    return buildReactLocation('/tasks/', params, { extra: { create: '1' } });
  }
  if (pathname === '/todos/request/' || pathname === '/todos/request') {
    return buildReactLocation('/tasks/', params, { extra: { mode: 'request' } });
  }
  if (pathname === '/todos/my/' || pathname === '/todos/my') {
    return buildReactLocation('/tasks/', params, { extra: { tab: 'my' } });
  }
  if (pathname === '/todos/received/' || pathname === '/todos/received') {
    return buildReactLocation('/tasks/', params, { extra: { tab: 'received' } });
  }
  if (pathname === '/todos/requested/' || pathname === '/todos/requested') {
    return buildReactLocation('/tasks/', params, { extra: { tab: 'requested' } });
  }
  if (
    pathname === '/todos/manager/' ||
    pathname === '/todos/manager' ||
    pathname === '/todos/manager/workload/' ||
    pathname === '/todos/manager/workload'
  ) {
    return buildReactLocation('/tasks/manager/', params);
  }
  if (pathname === '/todos/manager/assign/' || pathname === '/todos/manager/assign') {
    return buildReactLocation('/tasks/manager/', params, { extra: { assign: '1' } });
  }
  match = pathname.match(/^\/todos\/manager\/task\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/tasks/${match[1]}/`, params);
  }
  match = pathname.match(/^\/todos\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation(`/tasks/${match[1]}/`, params, { extra: { edit: '1' } });
  }
  match = pathname.match(/^\/todos\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactLocation(`/tasks/${match[1]}/`, params, { extra: { delete: '1' } });
  }
  match = pathname.match(/^\/todos\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/tasks/${match[1]}/`, params);
  }

  return '';
}

function isDjangoApiRequest(pathname) {
  return pathname === '/reporting/api' || pathname.startsWith('/reporting/api/');
}

function isDjangoAssetRequest(pathname) {
  return (
    pathname.startsWith('/static/') ||
    pathname === '/static' ||
    pathname.startsWith('/media/') ||
    pathname === '/media'
  );
}

function isFrontendSessionRequest(pathname) {
  return (
    pathname === '/reporting/login' ||
    pathname === '/reporting/login/' ||
    pathname === '/reporting/logout' ||
    pathname === '/reporting/logout/' ||
    pathname.startsWith('/reporting/gmail/') ||
    pathname.startsWith('/reporting/imap/')
  );
}

function isDjangoLegacyNamespace(pathname) {
  return (
    pathname.startsWith('/reporting/') ||
    pathname === '/reporting' ||
    pathname.startsWith('/todos/') ||
    pathname === '/todos' ||
    pathname.startsWith('/ai/') ||
    pathname === '/ai'
  );
}

function shouldRedirectToReactPage(clientRequest) {
  const method = (clientRequest.method || 'GET').toUpperCase();
  return (method === 'GET' || method === 'HEAD') && Boolean(getCoreCrmReactLocation(clientRequest.url || '/'));
}

function redirectToReact(clientRequest, clientResponse) {
  clientResponse.writeHead(302, {
    'Cache-Control': 'no-cache',
    Location: getCoreCrmReactLocation(clientRequest.url || '/') || '/',
  });
  clientResponse.end();
}

function shouldProxy(requestUrl) {
  const pathname = getPathname(requestUrl);
  return (
    isDjangoApiRequest(pathname) ||
    isDjangoAssetRequest(pathname) ||
    isDjangoLegacyNamespace(pathname)
  );
}

createServer((request, response) => {
  const requestUrl = request.url || '/';
  const pathname = getPathname(requestUrl);
  if (pathname === '/healthz' || pathname === '/healthz/') {
    sendJson(response, 200, {
      status: 'ok',
      service: 'sales-note-frontend',
      generatedAt: new Date().toISOString(),
      upstream: djangoBaseUrl.origin,
    });
    return;
  }
  if (shouldRedirectToReactPage(request)) {
    redirectToReact(request, response);
    return;
  }
  if (shouldProxy(requestUrl)) {
    proxyToDjango(request, response);
    return;
  }
  sendStatic(response, resolveStaticPath(requestUrl));
}).listen(port, '0.0.0.0', () => {
  console.log(`Frontend server listening on ${port}`);
  console.log('Redirecting migrated core CRM legacy pages to React routes');
  console.log(`Proxying remaining legacy Django pages and API requests to ${djangoBaseUrl.origin}`);
});
