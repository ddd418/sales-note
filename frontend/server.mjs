import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distDir = join(__dirname, 'dist');
const port = Number(process.env.PORT || 4173);
const djangoBaseUrl = new URL(process.env.DJANGO_BASE_URL || 'https://web-production-5096.up.railway.app');

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

function redirect(response, location) {
  response.writeHead(302, {
    'Cache-Control': 'no-cache',
    Location: location,
  });
  response.end();
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

function shouldProxy(requestUrl) {
  return (
    requestUrl.startsWith('/reporting/') ||
    requestUrl === '/reporting' ||
    requestUrl.startsWith('/ai/') ||
    requestUrl === '/ai' ||
    requestUrl.startsWith('/static/') ||
    requestUrl === '/static' ||
    requestUrl.startsWith('/media/') ||
    requestUrl === '/media'
  );
}

function scheduleCalendarRedirect(requestUrl) {
  const target = new URL(requestUrl, 'http://sales-note.local');
  if (target.pathname === '/schedules' || target.pathname === '/schedules/') {
    return `/reporting/schedules/calendar/${target.search}`;
  }
  return '';
}

createServer((request, response) => {
  const requestUrl = request.url || '/';
  const calendarLocation = scheduleCalendarRedirect(requestUrl);
  if (calendarLocation) {
    redirect(response, calendarLocation);
    return;
  }
  if (shouldProxy(requestUrl)) {
    proxyToDjango(request, response);
    return;
  }
  sendStatic(response, resolveStaticPath(requestUrl));
}).listen(port, '0.0.0.0', () => {
  console.log(`Frontend server listening on ${port}`);
  console.log(`Proxying /reporting/*, /ai/*, /static/* and /media/* to ${djangoBaseUrl.origin}`);
});
