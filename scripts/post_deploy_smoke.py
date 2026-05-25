#!/usr/bin/env python
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from urllib.parse import urljoin

import requests


DEFAULT_BACKEND_URL = 'https://web-production-8a820.up.railway.app'
DEFAULT_FRONTEND_URL = 'https://sales-note-frontend-production.up.railway.app'
FRONTEND_REACT_ROUTES = (
    '/dashboard/',
    '/customers/',
    '/reports/',
    '/prepayments/',
    '/assets/',
    '/ai-workspace/',
)
REMOVED_FRONTEND_ROUTES = (
    '/data-cleanup/',
    '/downloads/',
)
PROTECTED_DOMAIN_APIS = (
    '/reporting/api/customers/',
    '/reporting/api/reports/',
    '/reporting/api/prepayments/',
    '/reporting/api/customer-assets/',
    '/reporting/api/ai-workspace/',
)


@dataclass
class SmokeResult:
    name: str
    ok: bool
    detail: str


def build_url(base_url, path):
    return urljoin(f'{base_url.rstrip("/")}/', path.lstrip('/'))


def record(results, name, ok, detail):
    results.append(SmokeResult(name=name, ok=ok, detail=detail))


def expect_json_status(session, results, name, base_url, path, expected_status, expected_payload_status=None, timeout=10):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout)
        payload = response.json()
        ok = response.status_code == expected_status
        if expected_payload_status is not None:
            ok = ok and payload.get('status') == expected_payload_status
        detail = f'{response.status_code} {payload.get("status", "")}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def expect_status(session, results, name, base_url, path, expected_statuses, timeout=10, contains=''):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout, allow_redirects=False)
        ok = response.status_code in expected_statuses
        if contains:
            ok = ok and contains in response.text
        detail = f'{response.status_code} {response.headers.get("content-type", "")}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def expect_html_route(session, results, name, base_url, path, timeout=10):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout, allow_redirects=False)
        content_type = response.headers.get('content-type', '')
        ok = response.status_code == 200 and 'text/html' in content_type
        detail = f'{response.status_code} {content_type}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def expect_removed_route(session, results, name, base_url, path, timeout=10):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout, allow_redirects=False)
        ok = response.status_code == 404
        detail = f'{response.status_code} {response.headers.get("content-type", "")}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def expect_frontend_static_cache(session, results, base_url, timeout=10):
    route_url = build_url(base_url, '/dashboard/')
    try:
        response = session.get(route_url, timeout=timeout, allow_redirects=False)
        html_cache = response.headers.get('cache-control', '')
        asset_match = re.search(r'(?:src|href)="([^"]*/assets/[^"]+\.(?:js|css))"', response.text)
        if response.status_code != 200 or not asset_match:
            record(
                results,
                'frontend static cache headers',
                False,
                f'html {response.status_code} asset_missing',
            )
            return

        asset_url = build_url(base_url, asset_match.group(1))
        asset_response = session.get(
            asset_url,
            timeout=timeout,
            allow_redirects=False,
            headers={'Accept-Encoding': 'br, gzip'},
        )
        asset_cache = asset_response.headers.get('cache-control', '')
        asset_encoding = asset_response.headers.get('content-encoding', '').lower()
        ok = (
            'no-cache' in html_cache.lower()
            and asset_response.status_code == 200
            and 'max-age=31536000' in asset_cache.lower()
            and 'immutable' in asset_cache.lower()
            and asset_encoding in {'br', 'gzip'}
        )
        detail = (
            f'html={html_cache or "-"} '
            f'asset={asset_response.status_code} {asset_cache or "-"} '
            f'encoding={asset_encoding or "identity"}'
        )
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, 'frontend static cache headers', ok, detail)


def expect_login_required_api(session, results, name, base_url, path, timeout=10):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout, allow_redirects=False)
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error = payload.get('error', '')
        ok = response.status_code == 401 and error == 'login_required'
        detail = f'{response.status_code} {error or response.headers.get("content-type", "")}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def expect_protected(session, results, name, base_url, path, timeout=10):
    url = build_url(base_url, path)
    try:
        response = session.get(url, timeout=timeout, allow_redirects=False)
        ok = response.status_code in (302, 401, 403)
        detail = f'{response.status_code} {response.headers.get("location", "")}'.strip()
    except Exception as exc:
        ok = False
        detail = exc.__class__.__name__
    record(results, name, ok, detail)


def authenticated_profile_check(results, backend_url, username, password, timeout=10):
    session = requests.Session()
    login_url = build_url(backend_url, '/reporting/login/')
    profile_url = build_url(backend_url, '/reporting/api/profile/')

    try:
        login_page = session.get(login_url, timeout=timeout)
        csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', login_page.text)
        csrf_token = csrf_match.group(1) if csrf_match else session.cookies.get('csrftoken', '')
        response = session.post(
            login_url,
            data={
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token,
            },
            headers={'Referer': login_url},
            timeout=timeout,
            allow_redirects=True,
        )
        if response.status_code >= 400:
            record(results, 'authenticated login', False, f'login {response.status_code}')
            return

        profile = session.get(profile_url, timeout=timeout)
        record(results, 'authenticated profile API', profile.status_code == 200, f'{profile.status_code}')
    except Exception as exc:
        record(results, 'authenticated login/profile', False, exc.__class__.__name__)


def main():
    parser = argparse.ArgumentParser(description='Run post-deploy smoke checks for Sales Note.')
    parser.add_argument('--backend-url', default=os.environ.get('BACKEND_URL', DEFAULT_BACKEND_URL))
    parser.add_argument('--frontend-url', default=os.environ.get('FRONTEND_URL', DEFAULT_FRONTEND_URL))
    parser.add_argument('--username', default=os.environ.get('SMOKE_USERNAME', ''))
    parser.add_argument('--password', default=os.environ.get('SMOKE_PASSWORD', ''))
    parser.add_argument('--timeout', type=int, default=int(os.environ.get('SMOKE_TIMEOUT', '10')))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    results = []
    session = requests.Session()

    expect_json_status(session, results, 'backend healthz', args.backend_url, '/healthz/', 200, 'ok', args.timeout)
    expect_json_status(session, results, 'backend readyz', args.backend_url, '/readyz/', 200, 'ok', args.timeout)
    expect_status(session, results, 'backend login page', args.backend_url, '/reporting/login/', (200,), args.timeout, contains='영업')
    expect_protected(session, results, 'backend reports API protected', args.backend_url, '/reporting/api/reports/', args.timeout)

    expect_json_status(session, results, 'frontend healthz', args.frontend_url, '/healthz/', 200, 'ok', args.timeout)
    expect_status(session, results, 'frontend dashboard shell', args.frontend_url, '/dashboard/', (200,), args.timeout)
    expect_frontend_static_cache(session, results, args.frontend_url, args.timeout)
    expect_protected(session, results, 'frontend reports API protected', args.frontend_url, '/reporting/api/reports/', args.timeout)

    for route in FRONTEND_REACT_ROUTES:
        expect_html_route(session, results, f'frontend React route {route}', args.frontend_url, route, args.timeout)

    for route in REMOVED_FRONTEND_ROUTES:
        expect_removed_route(session, results, f'frontend removed route {route}', args.frontend_url, route, args.timeout)

    for api_path in PROTECTED_DOMAIN_APIS:
        expect_login_required_api(session, results, f'frontend protected API {api_path}', args.frontend_url, api_path, args.timeout)
        expect_login_required_api(session, results, f'backend protected API {api_path}', args.backend_url, api_path, args.timeout)

    if args.username and args.password:
        authenticated_profile_check(results, args.backend_url, args.username, args.password, args.timeout)

    payload = {
        'status': 'ok' if all(result.ok for result in results) else 'failed',
        'backendUrl': args.backend_url,
        'frontendUrl': args.frontend_url,
        'results': [result.__dict__ for result in results],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for result in results:
            marker = 'PASS' if result.ok else 'FAIL'
            print(f'{marker} {result.name}: {result.detail}')
        print(f"Smoke status: {payload['status']}")

    return 0 if payload['status'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
