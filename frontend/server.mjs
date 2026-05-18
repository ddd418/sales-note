import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distDir = join(__dirname, 'dist');
const port = Number(process.env.PORT || 4173);
const djangoBaseUrl = new URL(process.env.DJANGO_BASE_URL || 'https://web-production-2cc17.up.railway.app');

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
  const headers = Object.fromEntries(
    Object.entries(clientRequest.headers).filter(([key]) => !hopByHopHeaders.has(key.toLowerCase())),
  );
  headers.host = djangoBaseUrl.host;
  headers['x-forwarded-host'] = clientRequest.headers.host || '';
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

function shouldRedirectToDjangoPage(clientRequest) {
  const method = (clientRequest.method || 'GET').toUpperCase();
  const pathname = getPathname(clientRequest.url || '/');
  return (
    (method === 'GET' || method === 'HEAD') &&
    isDjangoLegacyNamespace(pathname) &&
    !isDjangoApiRequest(pathname) &&
    !isDjangoAssetRequest(pathname) &&
    !isFrontendSessionRequest(pathname)
  );
}

function redirectToDjango(clientRequest, clientResponse) {
  const target = new URL(clientRequest.url || '/', djangoBaseUrl);
  clientResponse.writeHead(302, {
    'Cache-Control': 'no-cache',
    Location: target.toString(),
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
  if (shouldRedirectToDjangoPage(request)) {
    redirectToDjango(request, response);
    return;
  }
  if (shouldProxy(requestUrl)) {
    proxyToDjango(request, response);
    return;
  }
  sendStatic(response, resolveStaticPath(requestUrl));
}).listen(port, '0.0.0.0', () => {
  console.log(`Frontend server listening on ${port}`);
  console.log(`Redirecting legacy Django pages to ${djangoBaseUrl.origin}`);
  console.log(
    `Proxying /reporting/api/*, session routes, /static/*, /media/* and non-GET legacy actions to ${djangoBaseUrl.origin}`,
  );
});
