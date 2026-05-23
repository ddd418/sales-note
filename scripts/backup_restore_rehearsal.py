#!/usr/bin/env python
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def redact_url(database_url):
    if not database_url:
        return ''
    parsed = urlparse(database_url)
    hostname = parsed.hostname or ''
    port = f':{parsed.port}' if parsed.port else ''
    netloc = f'***@{hostname}{port}' if parsed.username or parsed.password else f'{hostname}{port}'
    return urlunparse((parsed.scheme, netloc, parsed.path, '', '', ''))


def require_binary(name):
    if not shutil.which(name):
        raise RuntimeError(f'{name} is not available on PATH.')


def run_command(command, env=None):
    printable = ' '.join(command)
    print(f'RUN {printable}')
    subprocess.run(command, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description='Practice backup and restore into an isolated target database.')
    parser.add_argument('--source-url', default=os.environ.get('DATABASE_URL', ''))
    parser.add_argument('--target-url', default=os.environ.get('RESTORE_REHEARSAL_DATABASE_URL', ''))
    parser.add_argument('--output-dir', default='output/backup-rehearsals')
    parser.add_argument('--dry-run', action='store_true', help='Print planned commands without running them.')
    parser.add_argument('--allow-target-reset', action='store_true', help='Allow pg_restore --clean against the target DB.')
    parser.add_argument('--skip-checks', action='store_true', help='Skip manage.py check and runtime audit on restored target.')
    args = parser.parse_args()

    if args.dry_run and not args.source_url:
        args.source_url = 'postgresql://source-user:source-pass@source-host/source-db'
    if args.dry_run and not args.target_url:
        args.target_url = 'postgresql://target-user:target-pass@target-host/restore-rehearsal-db'

    if not args.source_url:
        raise SystemExit('Missing --source-url or DATABASE_URL.')
    if not args.target_url:
        raise SystemExit('Missing --target-url or RESTORE_REHEARSAL_DATABASE_URL.')
    if args.source_url == args.target_url:
        raise SystemExit('Source and target database URLs must be different.')
    if not args.dry_run and not args.allow_target_reset:
        raise SystemExit('Refusing to reset target DB without --allow-target-reset.')

    output_dir = Path(args.output_dir)
    backup_path = output_dir / 'restore_rehearsal.dump'
    commands = [
        [
            'pg_dump',
            '--format=custom',
            '--no-owner',
            '--no-acl',
            '--file',
            str(backup_path),
            redact_url(args.source_url),
        ],
        [
            'pg_restore',
            '--clean',
            '--if-exists',
            '--no-owner',
            '--no-acl',
            '--dbname',
            redact_url(args.target_url),
            str(backup_path),
        ],
    ]

    if args.dry_run:
        print('Backup/restore rehearsal dry-run')
        print(f'Source: {redact_url(args.source_url)}')
        print(f'Target: {redact_url(args.target_url)}')
        for command in commands:
            print('PLAN ' + ' '.join(command))
        if not args.skip_checks:
            print('PLAN python manage.py check')
            print('PLAN python manage.py audit_runtime_config --json')
        return 0

    require_binary('pg_dump')
    require_binary('pg_restore')
    output_dir.mkdir(parents=True, exist_ok=True)

    run_command([
        'pg_dump',
        '--format=custom',
        '--no-owner',
        '--no-acl',
        '--file',
        str(backup_path),
        args.source_url,
    ])
    run_command([
        'pg_restore',
        '--clean',
        '--if-exists',
        '--no-owner',
        '--no-acl',
        '--dbname',
        args.target_url,
        str(backup_path),
    ])

    if not args.skip_checks:
        env = os.environ.copy()
        env['DATABASE_URL'] = args.target_url
        run_command([sys.executable, 'manage.py', 'check'], env=env)
        run_command([sys.executable, 'manage.py', 'audit_runtime_config', '--json'], env=env)

    print('Backup/restore rehearsal completed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
