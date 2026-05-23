import os

from django.conf import settings
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


SERVICE_NAME = 'sales-note-backend'


def _health_response(payload, status=200):
    response = JsonResponse(payload, status=status)
    response['Cache-Control'] = 'no-store'
    return response


def _base_payload(status):
    return {
        'status': status,
        'service': SERVICE_NAME,
        'environment': os.environ.get('RAILWAY_ENVIRONMENT') or 'local',
        'generatedAt': timezone.now().isoformat(),
        'commit': os.environ.get('RAILWAY_GIT_COMMIT_SHA') or '',
    }


@never_cache
@require_safe
def healthz(request):
    """Public liveness check for Railway. Does not touch CRM data."""
    return _health_response(_base_payload('ok'))


def _database_ready():
    connection = connections['default']
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    return connection.vendor


def _pending_migration_count():
    connection = connections['default']
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return len(plan)


@never_cache
@require_safe
def readyz(request):
    """Public readiness check for deploy smoke tests. Returns only system status."""
    checks = {}
    ready = True

    try:
        checks['database'] = {'status': 'ok', 'vendor': _database_ready()}
    except Exception as exc:
        ready = False
        checks['database'] = {'status': 'error', 'error': exc.__class__.__name__}

    try:
        pending = _pending_migration_count()
        checks['migrations'] = {'status': 'ok' if pending == 0 else 'pending', 'pending': pending}
        if pending:
            ready = False
    except Exception as exc:
        ready = False
        checks['migrations'] = {'status': 'error', 'error': exc.__class__.__name__}

    payload = _base_payload('ok' if ready else 'degraded')
    payload['debug'] = bool(settings.DEBUG)
    payload['checks'] = checks
    return _health_response(payload, status=200 if ready else 503)
