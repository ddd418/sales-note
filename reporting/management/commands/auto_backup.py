import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = '자동 백업을 실행하고 오래된 백업 파일을 정리합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='백업 디렉토리 (기본값: backups)'
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='보관할 백업 파일 일수 (기본값: 30일)'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='백업 파일 압축'
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='미디어 파일 포함'
        )

    def handle(self, *args, **options):
        backup_dir = options['backup_dir']
        keep_days = options['keep_days']
        compress = options['compress']
        include_media = options['include_media']
        
        self.stdout.write('자동 백업을 시작합니다...')
        
        try:
            # 1. 새 백업 생성
            self._create_backup(backup_dir, compress, include_media)
            
            # 2. 오래된 백업 파일 정리
            self._cleanup_old_backups(backup_dir, keep_days)
            
            # 3. 백업 상태 보고
            self._report_backup_status(backup_dir)
            
            self.stdout.write(
                self.style.SUCCESS('자동 백업이 성공적으로 완료되었습니다!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'자동 백업 중 오류가 발생했습니다: {str(e)}')
            )
            raise

    def _create_backup(self, backup_dir, compress, include_media):
        """새 백업 생성"""
        self.stdout.write('새 백업을 생성합니다...')
        
        # backup_db 명령어 호출
        cmd_options = {
            'output_dir': backup_dir,
            'compress': compress,
            'include_media': include_media,
        }
        
        call_command('backup_db', **cmd_options)

    def _cleanup_old_backups(self, backup_dir, keep_days):
        """오래된 백업 파일 정리"""
        if not os.path.exists(backup_dir):
            return
        
        self.stdout.write(f'{keep_days}일 이전의 백업 파일을 정리합니다...')
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            
            # 백업 파일/디렉토리인지 확인 (이름 패턴으로)
            if not item.startswith('sales_db_backup_'):
                continue
            
            # 파일/디렉토리 수정 시간 확인
            item_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            
            if item_mtime < cutoff_date:
                try:
                    if os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    
                    self.stdout.write(f'  - 삭제됨: {item}')
                    deleted_count += 1
                    
                except Exception as e:
                    self.stdout.write(f'  ⚠️  삭제 실패: {item} ({str(e)})')
        
        if deleted_count > 0:
            self.stdout.write(f'  ✓ {deleted_count}개의 오래된 백업 파일을 삭제했습니다.')
        else:
            self.stdout.write('  - 삭제할 오래된 백업 파일이 없습니다.')

    def _report_backup_status(self, backup_dir):
        """백업 상태 보고"""
        if not os.path.exists(backup_dir):
            self.stdout.write('백업 디렉토리가 존재하지 않습니다.')
            return
        
        backups = []
        total_size = 0
        
        for item in os.listdir(backup_dir):
            if item.startswith('sales_db_backup_'):
                item_path = os.path.join(backup_dir, item)
                item_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                
                if os.path.isdir(item_path):
                    # 디렉토리 크기 계산
                    size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(item_path)
                        for filename in filenames
                    )
                else:
                    # 파일 크기
                    size = os.path.getsize(item_path)
                
                backups.append({
                    'name': item,
                    'date': item_mtime,
                    'size': size
                })
                total_size += size
        
        # 날짜순 정렬 (최신순)
        backups.sort(key=lambda x: x['date'], reverse=True)
        
        self.stdout.write('\n=== 백업 상태 보고 ===')
        self.stdout.write(f'총 백업 개수: {len(backups)}개')
        self.stdout.write(f'총 사용 용량: {self._format_size(total_size)}')
        
        if backups:
            self.stdout.write('\n최근 백업 파일들:')
            for i, backup in enumerate(backups[:5]):  # 최근 5개만 표시
                self.stdout.write(
                    f'  {i+1}. {backup["name"]} '
                    f'({backup["date"].strftime("%Y-%m-%d %H:%M:%S")}, '
                    f'{self._format_size(backup["size"])})'
                )
        
        self.stdout.write('=' * 25)

    def _format_size(self, size_bytes):
        """바이트 크기를 읽기 쉬운 형태로 변환"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
