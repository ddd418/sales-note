import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


BACKUP_PREFIX = 'sales_note_backup_'


class Command(BaseCommand):
    help = 'Create a CRM database backup artifact with local retention.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='', help='Directory for backup artifacts.')
        parser.add_argument(
            '--format',
            choices=('auto', 'json', 'pgdump'),
            default='auto',
            help='Backup format. auto uses pg_dump when DATABASE_URL and pg_dump are available.',
        )
        parser.add_argument('--keep', type=int, default=7, help='Number of recent backup files to keep.')
        parser.add_argument(
            '--database-url',
            default='',
            help='Database URL for pg_dump. Defaults to DATABASE_URL when present.',
        )

    def handle(self, *args, **options):
        output_dir = self._resolve_output_dir(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        database_url = options['database_url'] or os.environ.get('DATABASE_URL', '')
        backup_format = self._resolve_format(options['format'], database_url)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        if backup_format == 'pgdump':
            backup_path = output_dir / f'{BACKUP_PREFIX}{timestamp}.dump'
            self._run_pg_dump(database_url, backup_path)
        else:
            backup_path = output_dir / f'{BACKUP_PREFIX}{timestamp}.json'
            self._run_dumpdata(backup_path)

        self._apply_retention(output_dir, options['keep'])
        size_bytes = backup_path.stat().st_size if backup_path.exists() else 0
        self.stdout.write(
            self.style.SUCCESS(
                f'Backup written: {backup_path} ({backup_format}, {size_bytes} bytes)'
            )
        )

    def _resolve_output_dir(self, value):
        if value:
            return Path(value)
        if os.environ.get('BACKUP_DIR'):
            return Path(os.environ['BACKUP_DIR'])
        media_root = getattr(settings, 'MEDIA_ROOT', '')
        if media_root:
            return Path(media_root) / 'backups'
        return Path('output/backups')

    def _resolve_format(self, requested_format, database_url):
        if requested_format != 'auto':
            return requested_format
        if database_url and shutil.which('pg_dump'):
            return 'pgdump'
        return 'json'

    def _run_pg_dump(self, database_url, backup_path):
        if not database_url:
            raise CommandError('DATABASE_URL or --database-url is required for pgdump backups.')
        if not shutil.which('pg_dump'):
            raise CommandError('pg_dump is not available on PATH.')

        subprocess.run(
            [
                'pg_dump',
                '--format=custom',
                '--no-owner',
                '--no-acl',
                '--file',
                str(backup_path),
                database_url,
            ],
            check=True,
        )

    def _run_dumpdata(self, backup_path):
        with backup_path.open('w', encoding='utf-8') as handle:
            call_command(
                'dumpdata',
                '--natural-foreign',
                '--natural-primary',
                '--indent',
                '2',
                '--exclude',
                'contenttypes',
                '--exclude',
                'auth.permission',
                stdout=handle,
            )

    def _apply_retention(self, output_dir, keep):
        if keep <= 0:
            return
        backups = sorted(
            [path for path in output_dir.glob(f'{BACKUP_PREFIX}*') if path.is_file()],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for old_backup in backups[keep:]:
            old_backup.unlink()
