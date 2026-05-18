from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Process due scheduled emails."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help='Maximum number of scheduled emails to process.')

    def handle(self, *args, **options):
        from reporting.gmail_views import process_due_scheduled_emails

        result = process_due_scheduled_emails(limit=options['limit'])
        self.stdout.write(
            self.style.SUCCESS(
                f"processed={result['processed']} sent={result['sent']} failed={result['failed']}"
            )
        )
