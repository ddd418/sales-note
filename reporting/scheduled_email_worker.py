import logging
import os
import sys
import threading
import time

from django.db import close_old_connections, connection

logger = logging.getLogger(__name__)

_worker_lock = threading.Lock()
_worker_started = False
_SCHEDULED_EMAIL_LOCK_ID = 831_202_605


def _truthy(value):
    return str(value or '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _int_env(name, default, minimum):
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(value, minimum)


def _is_server_process():
    argv = ' '.join(sys.argv).lower()
    if 'gunicorn' in argv or 'uwsgi' in argv or 'daphne' in argv:
        return True
    if 'runserver' in argv:
        return os.environ.get('RUN_MAIN') == 'true'
    return False


def _try_acquire_dispatch_lock():
    if connection.vendor != 'postgresql':
        return True
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_try_advisory_lock(%s)', [_SCHEDULED_EMAIL_LOCK_ID])
        return bool(cursor.fetchone()[0])


def _release_dispatch_lock():
    if connection.vendor != 'postgresql':
        return
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_unlock(%s)', [_SCHEDULED_EMAIL_LOCK_ID])


def _scheduled_email_loop(interval_seconds, batch_limit, initial_delay_seconds):
    if initial_delay_seconds:
        time.sleep(initial_delay_seconds)

    while True:
        try:
            close_old_connections()
            if not _try_acquire_dispatch_lock():
                logger.debug('예약 메일 자동 처리 루프 건너뜀: 다른 프로세스가 lock 보유 중')
                continue
            from reporting.gmail_views import process_due_scheduled_emails

            try:
                result = process_due_scheduled_emails(limit=batch_limit)
                if result.get('processed') or result.get('failed'):
                    logger.info(
                        '예약 메일 자동 처리: processed=%s sent=%s failed=%s',
                        result.get('processed'),
                        result.get('sent'),
                        result.get('failed'),
                    )
            finally:
                _release_dispatch_lock()
        except Exception:
            logger.exception('예약 메일 자동 처리 루프 오류')
        finally:
            close_old_connections()
            time.sleep(interval_seconds)


def start_scheduled_email_inline_worker():
    """Start a small dispatcher loop inside a server process when explicitly enabled."""
    global _worker_started

    enabled_value = os.environ.get('SCHEDULED_EMAIL_INLINE_WORKER')
    if enabled_value is None and (os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL')):
        enabled_value = '1'
    if not _truthy(enabled_value):
        return
    if not _is_server_process():
        return

    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True

        interval_seconds = _int_env('SCHEDULED_EMAIL_INLINE_INTERVAL_SECONDS', 60, 15)
        batch_limit = _int_env('SCHEDULED_EMAIL_INLINE_BATCH_LIMIT', 50, 1)
        initial_delay_seconds = _int_env('SCHEDULED_EMAIL_INLINE_INITIAL_DELAY_SECONDS', 10, 0)

        thread = threading.Thread(
            target=_scheduled_email_loop,
            args=(interval_seconds, batch_limit, initial_delay_seconds),
            daemon=True,
            name='scheduled-email-dispatcher',
        )
        thread.start()
        logger.info(
            '예약 메일 자동 처리 루프 시작: interval=%ss limit=%s initial_delay=%ss',
            interval_seconds,
            batch_limit,
            initial_delay_seconds,
        )
