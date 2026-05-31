import gzip
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_safe


COMPRESSIBLE_EXTENSIONS = {'.css', '.html', '.js', '.json', '.map', '.svg', '.txt'}


def _frontend_dist_dir():
    configured = getattr(settings, 'FRONTEND_DIST_DIR', None)
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR) / 'frontend' / 'dist'


def _safe_frontend_file(*parts):
    dist_dir = _frontend_dist_dir().resolve()
    candidate = dist_dir.joinpath(*parts).resolve()
    if not candidate.is_file() or dist_dir not in candidate.parents:
        raise Http404('Frontend file not found')
    return candidate


def _content_type(path):
    guessed, _ = mimetypes.guess_type(str(path))
    if path.suffix == '.js':
        return 'text/javascript; charset=utf-8'
    if path.suffix == '.css':
        return 'text/css; charset=utf-8'
    return guessed or 'application/octet-stream'


def _accepts_gzip(request):
    encodings = request.headers.get('Accept-Encoding', '').lower()
    return 'gzip' in {part.strip().split(';', 1)[0] for part in encodings.split(',')}


@require_safe
def react_index(request, path=''):
    index_path = _safe_frontend_file('index.html')
    response = FileResponse(index_path.open('rb'), content_type='text/html; charset=utf-8')
    response['Cache-Control'] = 'no-cache'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_safe
def react_asset(request, path):
    safe_parts = [part for part in Path(path).parts if part not in ('', '.', '..')]
    asset_path = _safe_frontend_file('assets', *safe_parts)
    content_type = _content_type(asset_path)
    headers = {
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Content-Type': content_type,
        'Vary': 'Accept-Encoding',
        'X-Content-Type-Options': 'nosniff',
    }
    if asset_path.suffix.lower() in COMPRESSIBLE_EXTENSIONS and _accepts_gzip(request):
        content = gzip.compress(asset_path.read_bytes(), compresslevel=6)
        response = HttpResponse(content, headers=headers)
        response['Content-Encoding'] = 'gzip'
        return response
    return FileResponse(asset_path.open('rb'), headers=headers)


@require_safe
def removed_react_route(request, path=''):
    return HttpResponse('Not found', status=404, content_type='text/plain; charset=utf-8')
