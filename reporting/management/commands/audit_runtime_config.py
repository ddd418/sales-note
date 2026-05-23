import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Audit runtime environment, session, backup, and security settings without printing secrets.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Print JSON output.')
        parser.add_argument('--fail-on-warning', action='store_true', help='Return non-zero when warnings exist.')

    def handle(self, *args, **options):
        payload = self._build_payload()
        status = payload['status']

        if options['json']:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            self.stdout.write(f"Runtime config audit: {status}")
            for item in payload['errors']:
                self.stdout.write(self.style.ERROR(f"ERROR {item['code']}: {item['message']}"))
            for item in payload['warnings']:
                self.stdout.write(self.style.WARNING(f"WARNING {item['code']}: {item['message']}"))
            for item in payload['checks']:
                self.stdout.write(self.style.SUCCESS(f"OK {item['code']}: {item['message']}"))

        if payload['errors']:
            raise CommandError('Runtime config audit failed.')
        if options['fail_on_warning'] and payload['warnings']:
            raise CommandError('Runtime config audit has warnings.')

    def _build_payload(self):
        production_like = self._is_production_like()
        errors = []
        warnings = []
        checks = []

        secret_key = getattr(settings, 'SECRET_KEY', '')
        if production_like and not secret_key:
            errors.append(self._item('SECRET_KEY_MISSING', 'SECRET_KEY must be configured in production-like environments.'))
        elif production_like and secret_key.startswith('django-insecure-'):
            errors.append(self._item('SECRET_KEY_INSECURE', 'SECRET_KEY must not use the django-insecure- prefix in production.'))
        else:
            checks.append(self._item('SECRET_KEY_PRESENT', 'SECRET_KEY is configured or local DEBUG mode is active.'))

        if os.environ.get('RAILWAY_ENVIRONMENT') and getattr(settings, 'DEBUG', False):
            errors.append(self._item('DEBUG_ON_RAILWAY', 'DEBUG must be false on Railway.'))
        else:
            checks.append(self._item('DEBUG_MODE', 'DEBUG setting is compatible with the detected environment.'))

        if os.environ.get('RAILWAY_ENVIRONMENT') and not os.environ.get('DATABASE_URL'):
            errors.append(self._item('DATABASE_URL_MISSING', 'DATABASE_URL must be configured on Railway.'))
        else:
            checks.append(self._item('DATABASE_CONFIGURED', 'Database configuration is present.'))

        if production_like and not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            errors.append(self._item('SESSION_COOKIE_SECURE_OFF', 'SESSION_COOKIE_SECURE must be enabled in production.'))
        else:
            checks.append(self._item('SESSION_COOKIE_SECURE', 'Session secure-cookie setting is acceptable.'))

        if production_like and not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            errors.append(self._item('CSRF_COOKIE_SECURE_OFF', 'CSRF_COOKIE_SECURE must be enabled in production.'))
        else:
            checks.append(self._item('CSRF_COOKIE_SECURE', 'CSRF secure-cookie setting is acceptable.'))

        if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
            errors.append(self._item('SESSION_COOKIE_HTTPONLY_OFF', 'SESSION_COOKIE_HTTPONLY must stay enabled.'))
        else:
            checks.append(self._item('SESSION_COOKIE_HTTPONLY', 'Session HttpOnly cookie setting is enabled.'))

        if getattr(settings, 'SESSION_COOKIE_SAMESITE', '') not in ('Lax', 'Strict', 'None'):
            errors.append(self._item('SESSION_COOKIE_SAMESITE_INVALID', 'SESSION_COOKIE_SAMESITE must be Lax, Strict, or None.'))
        else:
            checks.append(self._item('SESSION_COOKIE_SAMESITE', 'Session SameSite value is recognized.'))

        if production_like and not getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            errors.append(self._item('NOSNIFF_OFF', 'SECURE_CONTENT_TYPE_NOSNIFF must be enabled in production.'))
        else:
            checks.append(self._item('NOSNIFF', 'Content-type nosniff setting is acceptable.'))

        if production_like and int(getattr(settings, 'SECURE_HSTS_SECONDS', 0) or 0) <= 0:
            warnings.append(self._item('HSTS_DISABLED', 'HSTS is disabled. Enable after confirming all production traffic is HTTPS.'))

        optional_env = (
            ('EMAIL_ENCRYPTION_KEY', 'IMAP/SMTP password encryption is disabled without EMAIL_ENCRYPTION_KEY.'),
            ('BACKUP_API_TOKEN', 'Scheduled backup API is disabled without BACKUP_API_TOKEN.'),
            ('ERROR_ALERT_WEBHOOK_URL', 'Error webhook alerts are disabled without ERROR_ALERT_WEBHOOK_URL.'),
            ('FRONTEND_PIPELINE_URL', 'Root redirects use the default frontend URL without FRONTEND_PIPELINE_URL.'),
            ('SALES_NOTE_READONLY_TOKEN', 'Read-only integration access is disabled without SALES_NOTE_READONLY_TOKEN.'),
        )
        for env_name, message in optional_env:
            if not os.environ.get(env_name):
                warnings.append(self._item(f'{env_name}_MISSING', message))
            else:
                checks.append(self._item(f'{env_name}_PRESENT', f'{env_name} is configured.'))

        status = 'error' if errors else 'warning' if warnings else 'ok'
        return {
            'status': status,
            'environment': os.environ.get('RAILWAY_ENVIRONMENT') or 'local',
            'debug': bool(getattr(settings, 'DEBUG', False)),
            'productionLike': production_like,
            'errors': errors,
            'warnings': warnings,
            'checks': checks,
        }

    def _is_production_like(self):
        return bool(
            os.environ.get('RAILWAY_ENVIRONMENT')
            or os.environ.get('DATABASE_URL')
            or not getattr(settings, 'DEBUG', False)
        )

    def _item(self, code, message):
        return {'code': code, 'message': message}
