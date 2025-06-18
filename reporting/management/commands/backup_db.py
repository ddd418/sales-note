import os
import json
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
from reporting.models import UserProfile, FollowUp, Schedule, History


class Command(BaseCommand):
    help = '데이터베이스를 JSON 형태로 백업합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='백업 파일을 저장할 디렉토리 (기본값: backups)'
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='미디어 파일도 함께 백업'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='백업 파일을 압축'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        include_media = options['include_media']
        compress = options['compress']
        
        # 백업 디렉토리 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'sales_db_backup_{timestamp}'
        backup_path = os.path.join(output_dir, backup_name)
        
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        
        self.stdout.write(f'백업을 시작합니다: {backup_path}')
        
        try:
            # 1. 데이터베이스 백업
            self._backup_database(backup_path)
            
            # 2. SQLite 파일 백업 (SQLite 사용 시)
            self._backup_sqlite_file(backup_path)
            
            # 3. 미디어 파일 백업 (옵션)
            if include_media:
                self._backup_media_files(backup_path)
            
            # 4. 백업 정보 파일 생성
            self._create_backup_info(backup_path, include_media)
            
            # 5. 압축 (옵션)
            if compress:
                backup_path = self._compress_backup(backup_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'백업이 완료되었습니다: {backup_path}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'백업 중 오류가 발생했습니다: {str(e)}')
            )
            # 실패 시 백업 디렉토리 정리
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)

    def _backup_database(self, backup_path):
        """데이터베이스 모델들을 JSON으로 백업"""
        self.stdout.write('데이터베이스 모델 백업 중...')
        
        # 백업할 모델들과 순서 (외래키 관계 고려)
        models_to_backup = [
            (User, 'users.json'),
            (UserProfile, 'userprofiles.json'),
            (FollowUp, 'followups.json'),
            (Schedule, 'schedules.json'),
            (History, 'histories.json'),
        ]
        
        for model, filename in models_to_backup:
            self.stdout.write(f'  - {model.__name__} 백업 중...')
            
            # 모든 객체를 JSON으로 직렬화
            data = serializers.serialize('json', model.objects.all())
            
            # 파일에 저장
            file_path = os.path.join(backup_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
            
            count = model.objects.count()
            self.stdout.write(f'    ✓ {count}개 항목 백업 완료')

    def _backup_sqlite_file(self, backup_path):
        """SQLite 데이터베이스 파일 직접 복사"""
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            db_file = db_config['NAME']
            if os.path.exists(db_file):
                self.stdout.write('SQLite 데이터베이스 파일 백업 중...')
                dest_file = os.path.join(backup_path, 'db.sqlite3')
                shutil.copy2(db_file, dest_file)
                self.stdout.write('  ✓ SQLite 파일 백업 완료')

    def _backup_media_files(self, backup_path):
        """미디어 파일들 백업"""
        media_root = settings.MEDIA_ROOT
        
        if os.path.exists(media_root):
            self.stdout.write('미디어 파일 백업 중...')
            media_backup_path = os.path.join(backup_path, 'media')
            shutil.copytree(media_root, media_backup_path)
            self.stdout.write('  ✓ 미디어 파일 백업 완료')

    def _create_backup_info(self, backup_path, include_media):
        """백업 정보 파일 생성"""
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'include_media': include_media,
            'models': {
                'User': User.objects.count(),
                'UserProfile': UserProfile.objects.count(),
                'FollowUp': FollowUp.objects.count(),
                'Schedule': Schedule.objects.count(),
                'History': History.objects.count(),
            }
        }
        
        info_file = os.path.join(backup_path, 'backup_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        self.stdout.write('백업 정보 파일 생성 완료')

    def _compress_backup(self, backup_path):
        """백업 디렉토리를 ZIP으로 압축"""
        self.stdout.write('백업 파일 압축 중...')
        
        import zipfile
        zip_path = f'{backup_path}.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        # 원본 디렉토리 삭제
        shutil.rmtree(backup_path)
        
        self.stdout.write(f'  ✓ 압축 완료: {zip_path}')
        return zip_path
