"""
파일 정리 명령어
- 영구 보관: 서류 템플릿, 회사 로고, 5MB 이하 파일
- 100일 후 삭제: 5MB 초과 임시 파일

사용법:
    python manage.py cleanup_old_files          # 실제 삭제
    python manage.py cleanup_old_files --dry-run  # 미리보기 (삭제 안함)
"""
import os
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '100일이 지난 5MB 초과 임시 파일을 삭제합니다. 서류 템플릿, 회사 로고, 5MB 이하 파일은 영구 보관됩니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 삭제 없이 삭제 대상 파일만 출력합니다.',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=100,
            help='보관 기간 (일). 기본값: 100일',
        )
        parser.add_argument(
            '--max-size',
            type=float,
            default=5.0,
            help='영구 보관 최대 파일 크기 (MB). 기본값: 5MB',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        retention_days = options['days']
        max_size_mb = options['max_size']
        max_size_bytes = max_size_mb * 1024 * 1024  # MB to bytes

        # 설정에서 가져오거나 기본값 사용
        cleanup_settings = getattr(settings, 'FILE_CLEANUP_SETTINGS', {})
        permanent_paths = cleanup_settings.get('PERMANENT_PATHS', [
            'document_templates/',
            'business_card_logos/',
        ])

        # MEDIA_ROOT 확인
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            self.stderr.write(self.style.ERROR('MEDIA_ROOT가 설정되지 않았습니다.'))
            return

        if not os.path.exists(media_root):
            self.stderr.write(self.style.ERROR(f'MEDIA_ROOT 경로가 존재하지 않습니다: {media_root}'))
            return

        self.stdout.write(self.style.NOTICE(f'=== 파일 정리 시작 ==='))
        self.stdout.write(f'MEDIA_ROOT: {media_root}')
        self.stdout.write(f'보관 기간: {retention_days}일')
        self.stdout.write(f'영구 보관 최대 크기: {max_size_mb}MB')
        self.stdout.write(f'영구 보관 경로: {permanent_paths}')
        if dry_run:
            self.stdout.write(self.style.WARNING('*** DRY-RUN 모드: 실제 삭제 없음 ***'))
        self.stdout.write('')

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        total_files = 0
        deleted_files = 0
        deleted_size = 0
        skipped_permanent_path = 0
        skipped_small_file = 0
        skipped_recent = 0

        for root, dirs, files in os.walk(media_root):
            for filename in files:
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, media_root)
                total_files += 1

                try:
                    file_stat = os.stat(filepath)
                    file_size = file_stat.st_size
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

                    # 1. 영구 보관 경로 체크
                    is_permanent_path = any(
                        relative_path.startswith(path) for path in permanent_paths
                    )
                    if is_permanent_path:
                        skipped_permanent_path += 1
                        continue

                    # 2. 5MB 이하 파일은 영구 보관
                    if file_size <= max_size_bytes:
                        skipped_small_file += 1
                        continue

                    # 3. 최근 파일 (100일 이내)
                    if file_mtime > cutoff_date:
                        skipped_recent += 1
                        continue

                    # 삭제 대상
                    file_size_mb = file_size / (1024 * 1024)
                    age_days = (datetime.now() - file_mtime).days

                    if dry_run:
                        self.stdout.write(
                            f'[삭제 대상] {relative_path} '
                            f'({file_size_mb:.2f}MB, {age_days}일 전)'
                        )
                    else:
                        os.remove(filepath)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'[삭제됨] {relative_path} '
                                f'({file_size_mb:.2f}MB, {age_days}일 전)'
                            )
                        )

                    deleted_files += 1
                    deleted_size += file_size

                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f'[오류] {filepath}: {str(e)}')
                    )

        # 빈 디렉토리 정리 (dry-run이 아닐 때만)
        empty_dirs_removed = 0
        if not dry_run:
            for root, dirs, files in os.walk(media_root, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            empty_dirs_removed += 1
                    except Exception:
                        pass

        # 결과 출력
        deleted_size_mb = deleted_size / (1024 * 1024)
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=== 정리 결과 ==='))
        self.stdout.write(f'총 파일 수: {total_files}')
        self.stdout.write(f'영구 보관 (경로): {skipped_permanent_path}')
        self.stdout.write(f'영구 보관 (5MB 이하): {skipped_small_file}')
        self.stdout.write(f'보관 중 (100일 이내): {skipped_recent}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'삭제 예정: {deleted_files}개 ({deleted_size_mb:.2f}MB)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'삭제 완료: {deleted_files}개 ({deleted_size_mb:.2f}MB)'
            ))
            if empty_dirs_removed > 0:
                self.stdout.write(f'빈 디렉토리 정리: {empty_dirs_removed}개')
