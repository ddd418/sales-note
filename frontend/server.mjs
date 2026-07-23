import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { basename, extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { constants as zlibConstants, createBrotliCompress, createGzip } from 'node:zlib';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distDir = join(__dirname, 'dist');
const port = Number(process.env.PORT || 4173);
const djangoBaseUrl = new URL(process.env.DJANGO_BASE_URL || 'http://127.0.0.1:8000');
const errorAlertWebhookUrl = process.env.FRONTEND_ERROR_ALERT_WEBHOOK_URL || process.env.ERROR_ALERT_WEBHOOK_URL || '';
const serviceName = process.env.RAILWAY_SERVICE_NAME || 'sales-note-frontend';

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
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.webp': 'image/webp',
};

// 서비스워커/매니페스트는 브라우저가 즉시 최신 버전을 다시 받아가야 한다.
// 여기에 immutable 장기 캐시를 걸면 배포 후에도 사용자가 옛 앱 셸에 갇힌다.
const noCacheFileNames = new Set(['sw.js', 'registerSW.js', 'manifest.webmanifest']);

const compressibleStaticExtensions = new Set(['.css', '.html', '.js', '.json', '.map', '.svg', '.txt', '.webmanifest']);

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

function compactError(error) {
  if (!error || typeof error !== 'object') {
    return { name: 'Error', message: String(error || '').slice(0, 240), code: '' };
  }
  return {
    name: error.name || 'Error',
    message: String(error.message || '').slice(0, 240),
    code: String(error.code || ''),
  };
}

function sendWebhookAlert(payload) {
  if (!errorAlertWebhookUrl) {
    return;
  }
  let webhookUrl;
  try {
    webhookUrl = new URL(errorAlertWebhookUrl);
  } catch {
    return;
  }
  if (webhookUrl.protocol !== 'http:' && webhookUrl.protocol !== 'https:') {
    return;
  }
  const body = JSON.stringify(payload);
  const alertRequest = (webhookUrl.protocol === 'https:' ? httpsRequest : httpRequest)(
    {
      protocol: webhookUrl.protocol,
      hostname: webhookUrl.hostname,
      port: webhookUrl.port,
      path: `${webhookUrl.pathname}${webhookUrl.search}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    },
    (alertResponse) => {
      alertResponse.resume();
    },
  );
  alertRequest.setTimeout(2500, () => alertRequest.destroy());
  alertRequest.on('error', () => {});
  alertRequest.write(body);
  alertRequest.end();
}

function recordOperationalError(event, details = {}) {
  const payload = {
    service: serviceName,
    event,
    level: 'error',
    generatedAt: new Date().toISOString(),
    ...details,
  };
  console.error(JSON.stringify(payload));
  sendWebhookAlert(payload);
}

function selectStaticEncoding(request, extension) {
  if (!compressibleStaticExtensions.has(extension)) {
    return '';
  }
  const acceptedEncodings = String(request.headers['accept-encoding'] || '')
    .toLowerCase()
    .split(',')
    .map((value) => value.trim().split(';')[0])
    .filter(Boolean);
  if (acceptedEncodings.includes('br')) {
    return 'br';
  }
  if (acceptedEncodings.includes('gzip')) {
    return 'gzip';
  }
  return '';
}

function sendStatic(request, response, filePath) {
  const extension = extname(filePath);
  const fileStat = statSync(filePath);
  const contentEncoding = selectStaticEncoding(request, extension);
  const noCache = extension === '.html' || noCacheFileNames.has(basename(filePath));
  const headers = {
    'Cache-Control': noCache ? 'no-cache' : 'public, max-age=31536000, immutable',
    'Content-Length': fileStat.size,
    'Content-Type': mimeTypes[extension] || 'application/octet-stream',
    'X-Content-Type-Options': 'nosniff',
  };
  if (compressibleStaticExtensions.has(extension)) {
    headers.Vary = 'Accept-Encoding';
  }
  if (contentEncoding) {
    headers['Content-Encoding'] = contentEncoding;
    delete headers['Content-Length'];
  }
  response.writeHead(200, {
    ...headers,
  });
  if ((request.method || 'GET').toUpperCase() === 'HEAD') {
    response.end();
    return;
  }
  const readStream = createReadStream(filePath);
  readStream.on('error', () => {
    if (!response.destroyed) {
      response.destroy();
    }
  });
  if (contentEncoding === 'br') {
    readStream.pipe(createBrotliCompress({
      params: {
        [zlibConstants.BROTLI_PARAM_QUALITY]: 5,
      },
    })).pipe(response);
    return;
  }
  if (contentEncoding === 'gzip') {
    readStream.pipe(createGzip({ level: 6 })).pipe(response);
    return;
  }
  readStream.pipe(response);
}

function sendJson(response, statusCode, body) {
  response.writeHead(statusCode, {
    'Cache-Control': 'no-store',
    'Content-Type': 'application/json; charset=utf-8',
    'X-Content-Type-Options': 'nosniff',
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

  proxyRequest.on('error', (error) => {
    recordOperationalError('frontend_proxy_error', {
      method: clientRequest.method || 'GET',
      path: getPathname(clientRequest.url || '/'),
      upstreamHost: djangoBaseUrl.host,
      error: compactError(error),
    });
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
  if (pathname === '/reporting/receivables/' || pathname === '/reporting/receivables') {
    return buildReactLocation('/receivables/', params);
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
  if (pathname === '/reporting/weekly-reports/' || pathname === '/reporting/weekly-reports') {
    return buildReactLocation('/weekly-reports/', params);
  }
  if (pathname === '/reporting/weekly-reports/create/' || pathname === '/reporting/weekly-reports/create') {
    return buildReactLocation('/weekly-reports/new/', params);
  }
  match = pathname.match(/^\/reporting\/weekly-reports\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation(`/weekly-reports/${match[1]}/edit/`, params);
  }
  match = pathname.match(/^\/reporting\/weekly-reports\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactLocation(`/weekly-reports/${match[1]}/`, params);
  }
  match = pathname.match(/^\/reporting\/weekly-reports\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation(`/weekly-reports/${match[1]}/`, params);
  }
  if (pathname === '/reporting/profile/' || pathname === '/reporting/profile') {
    return buildReactLocation('/profile/', params);
  }
  if (pathname === '/reporting/profile/edit/' || pathname === '/reporting/profile/edit') {
    return buildReactLocation('/profile/', params, { extra: { edit: '1' } });
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

  if (pathname === '/reporting/gmail/send/mailbox/' || pathname === '/reporting/gmail/send/mailbox') {
    return buildReactLocation('/mailbox/', params, { extra: { compose: '1' } });
  }
  match = pathname.match(/^\/reporting\/gmail\/send\/mailbox\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/', params, { extra: { compose: '1', followup_id: match[1] } });
  }
  const mailboxBoxRoutes = {
    '/reporting/mailbox/inbox/': 'inbox',
    '/reporting/mailbox/inbox': 'inbox',
    '/reporting/mailbox/sent/': 'sent',
    '/reporting/mailbox/sent': 'sent',
    '/reporting/mailbox/starred/': 'starred',
    '/reporting/mailbox/starred': 'starred',
    '/reporting/mailbox/trash/': 'trash',
    '/reporting/mailbox/trash': 'trash',
    '/reporting/mailbox/sync/': 'inbox',
    '/reporting/mailbox/sync': 'inbox',
  };
  if (mailboxBoxRoutes[pathname]) {
    return buildReactLocation('/mailbox/', params, { extra: { box: mailboxBoxRoutes[pathname] } });
  }
  match = pathname.match(/^\/reporting\/mailbox\/thread\/([^/]+)\/?$/);
  if (match) {
    return buildReactLocation(`/mailbox/thread/${match[1]}/`, params);
  }
  match = pathname.match(/^\/reporting\/mailbox\/(?:delete|move-to-trash|restore)\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/', params, { extra: { box: 'trash' } });
  }
  match = pathname.match(/^\/reporting\/mailbox\/toggle-star\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/', params, { extra: { box: 'inbox' } });
  }
  match = pathname.match(/^\/reporting\/mailbox\/archive\/(\d+)\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/', params, { extra: { box: 'archived' } });
  }

  if (pathname === '/reporting/business-cards/' || pathname === '/reporting/business-cards') {
    return buildReactLocation('/mailbox/business-cards/', params);
  }
  if (pathname === '/reporting/business-cards/create/' || pathname === '/reporting/business-cards/create') {
    return buildReactLocation('/mailbox/business-cards/', params, { extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/business-cards\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/business-cards/', params, { extra: { card: match[1], edit: '1' } });
  }
  match = pathname.match(/^\/reporting\/business-cards\/(\d+)\/(?:delete|set-default)\/?$/);
  if (match) {
    return buildReactLocation('/mailbox/business-cards/', params, { extra: { card: match[1] } });
  }

  if (pathname === '/reporting/gmail/disconnect/' || pathname === '/reporting/gmail/disconnect') {
    return buildReactLocation('/profile/', params);
  }
  if (pathname === '/reporting/imap/connect/' || pathname === '/reporting/imap/connect') {
    return buildReactLocation('/profile/', params, { extra: { imap: '1' } });
  }
  if (pathname === '/reporting/imap/disconnect/' || pathname === '/reporting/imap/disconnect') {
    return buildReactLocation('/profile/', params);
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

  if (pathname === '/reporting/products/' || pathname === '/reporting/products') {
    const status = params.get('is_active');
    if (status === 'true') params.set('status', 'active');
    if (status === 'false') params.set('status', 'inactive');
    params.delete('is_active');
    const sort = params.get('sort');
    if (sort === 'quote_count') params.set('sort', 'quoteCount');
    if (sort === 'delivery_count') params.set('sort', 'deliveryCount');
    return buildReactLocation('/products/', params, { rename: { search: 'q' } });
  }
  if (pathname === '/reporting/products/create/' || pathname === '/reporting/products/create') {
    return buildReactLocation('/products/', params, { extra: { create: '1' }, rename: { search: 'q' } });
  }
  if (pathname === '/reporting/products/bulk-create/' || pathname === '/reporting/products/bulk-create') {
    return buildReactLocation('/products/', params, { extra: { import: '1' }, rename: { search: 'q' } });
  }
  match = pathname.match(/^\/reporting\/products\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation('/products/', params, { extra: { product: match[1], edit: '1' }, rename: { search: 'q' } });
  }
  match = pathname.match(/^\/reporting\/products\/(\d+)\/delete\/?$/);
  if (match) {
    return buildReactLocation('/products/', params, { extra: { product: match[1], delete: '1' }, rename: { search: 'q' } });
  }

  if (pathname === '/reporting/documents/' || pathname === '/reporting/documents') {
    return buildReactLocation('/documents/', params);
  }
  if (pathname === '/reporting/documents/create/' || pathname === '/reporting/documents/create') {
    return buildReactLocation('/documents/', params, { extra: { create: '1' } });
  }
  match = pathname.match(/^\/reporting\/documents\/(\d+)\/edit\/?$/);
  if (match) {
    return buildReactLocation('/documents/', params, { extra: { template_id: match[1], edit: '1' } });
  }
  match = pathname.match(/^\/reporting\/documents\/(\d+)\/(?:delete|toggle-default)\/?$/);
  if (match) {
    return buildReactLocation('/documents/', params, { extra: { template_id: match[1] } });
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

function isRemovedFrontendRoute(pathname) {
  return (
    pathname === '/data-cleanup' ||
    pathname === '/data-cleanup/' ||
    pathname.startsWith('/data-cleanup/') ||
    pathname === '/downloads' ||
    pathname === '/downloads/' ||
    pathname.startsWith('/downloads/')
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
  if (isRemovedFrontendRoute(pathname)) {
    response.writeHead(404, {
      'Cache-Control': 'no-cache',
      'Content-Type': 'text/plain; charset=utf-8',
    });
    response.end('Not found');
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
  sendStatic(request, response, resolveStaticPath(requestUrl));
}).listen(port, '0.0.0.0', () => {
  console.log(`Frontend server listening on ${port}`);
  console.log('Redirecting migrated core CRM legacy pages to React routes');
  console.log(`Proxying remaining legacy Django pages and API requests to ${djangoBaseUrl.origin}`);
});

process.on('unhandledRejection', (reason) => {
  recordOperationalError('frontend_unhandled_rejection', {
    error: compactError(reason),
  });
});

process.on('uncaughtException', (error) => {
  recordOperationalError('frontend_uncaught_exception', {
    error: compactError(error),
  });
  setImmediate(() => process.exit(1));
});
