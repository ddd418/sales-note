"""Compatibility redirects for Django template pages that moved to React."""

from functools import wraps
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


DEFAULT_FRONTEND_URL = "https://sales-note-frontend-production.up.railway.app/"
READ_PAGE_METHODS = {"GET", "HEAD"}


def frontend_url(path, query=None):
    base_url = getattr(settings, "FRONTEND_PIPELINE_URL", DEFAULT_FRONTEND_URL)
    normalized = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
    params = query or {}
    encoded = urlencode(
        [(key, value) for key, value in params.items() if value not in (None, "")],
        doseq=True,
    )
    return f"{normalized}?{encoded}" if encoded else normalized


def query_with(request, *, rename=None, extra=None, drop=None):
    rename = rename or {}
    extra = extra or {}
    drop = set(drop or [])
    result = {}
    for key, values in request.GET.lists():
        target_key = rename.get(key, key)
        if key in drop or target_key in drop:
            continue
        result[target_key] = values if len(values) > 1 else values[0]
    result.update(extra)
    return result


def react_page_redirect(legacy_view, target):
    """Redirect authenticated GET/HEAD template requests to React.

    Other methods continue to the original Django view so transition-period
    form posts and legacy actions are not removed by the redirect layer.
    """
    @login_required
    @wraps(legacy_view)
    def _wrapped(request, *args, **kwargs):
        if request.method.upper() in READ_PAGE_METHODS:
            target_url = target(request, *args, **kwargs) if callable(target) else target
            return redirect(target_url)
        return legacy_view(request, *args, **kwargs)

    return _wrapped


def static_react_page(path, *, rename=None, extra=None, drop=None):
    return lambda request, *args, **kwargs: frontend_url(
        path,
        query_with(request, rename=rename, extra=extra, drop=drop),
    )


def id_react_page(path_template):
    return lambda request, pk=None, **kwargs: frontend_url(
        path_template.format(pk=pk, **kwargs),
        query_with(request),
    )
