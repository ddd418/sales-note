import json
import logging
import os
import urllib.error
import urllib.request


class WebhookErrorHandler(logging.Handler):
    """Send compact error notifications without request headers, cookies, or data."""

    def __init__(self, webhook_url, service_name='sales-note-backend', timeout=3):
        super().__init__()
        self.webhook_url = webhook_url
        self.service_name = service_name
        self.timeout = timeout

    def emit(self, record):
        if not self.webhook_url:
            return

        try:
            payload = {
                'service': self.service_name,
                'environment': os.environ.get('RAILWAY_ENVIRONMENT') or 'local',
                'commit': os.environ.get('RAILWAY_GIT_COMMIT_SHA') or '',
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'pathname': record.pathname,
                'lineno': record.lineno,
            }

            request = getattr(record, 'request', None)
            if request is not None:
                payload['request'] = {
                    'method': getattr(request, 'method', ''),
                    'path': getattr(request, 'path', ''),
                    'userAuthenticated': bool(getattr(getattr(request, 'user', None), 'is_authenticated', False)),
                }

            status_code = getattr(record, 'status_code', None)
            if status_code is not None:
                payload['statusCode'] = status_code

            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=body,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=self.timeout):
                pass
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            self.handleError(record)
