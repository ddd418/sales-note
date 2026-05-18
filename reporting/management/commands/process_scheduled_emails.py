from django.core.management.base import BaseCommand
from django.db import close_old_connections
import time


class Command(BaseCommand):
    help = "Process due scheduled emails."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help='Maximum number of scheduled emails to process.')
        parser.add_argument('--loop', action='store_true', help='Keep processing due scheduled emails on an interval.')
        parser.add_argument('--interval', type=int, default=60, help='Loop interval in seconds when --loop is used.')

    def handle(self, *args, **options):
        from reporting.gmail_views import process_due_scheduled_emails

        limit = max(int(options['limit']), 1)
        interval = max(int(options['interval']), 15)

        while True:
            close_old_connections()
            result = process_due_scheduled_emails(limit=limit)
            close_old_connections()
            self.stdout.write(
                self.style.SUCCESS(
                    f"processed={result['processed']} sent={result['sent']} failed={result['failed']}"
                )
            )
            if not options['loop']:
                break
            time.sleep(interval)
