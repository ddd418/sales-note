import os
import json
import shutil
import zipfile
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from reporting.models import UserProfile, FollowUp, Schedule, History


class Command(BaseCommand):
    help = '백업된 데이터베이스를 복원합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_path',
            type=str,
            help='복원할 백업 디렉토리 또는 ZIP 파일 경로'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='기존 데이터를 모두 삭제하고 복원 (주의: 모든 데이터가 삭제됩니다!)'
        )
        parser.add_argument(
            '--restore-media',
            action='store_true',
            help='미디어 파일도 함께 복원'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='확인 없이 강제 실행'
        )

    def handle(self, *args, **options):
        backup_path = options['backup_path']
        clear_existing = options['clear_existing']
        restore_media = options['restore_media']
        force = options['force']
        
        # 백업 파일/디렉토리 존재 확인
        if not os.path.exists(backup_path):
            raise CommandError(f'백업 파일이 존재하지 않습니다: {backup_path}')
        
        # ZIP 파일인 경우 압축 해제
        extracted_path = None
        if backup_path.endswith('.zip'):
            extracted_path = self._extract_backup(backup_path)
            working_path = extracted_path
        else:
            working_path = backup_path
        
        # 백업 정보 확인
        info_file = os.path.join(working_path, 'backup_info.json')
        if os.path.exists(info_file):
            self._show_backup_info(info_file)
        
        # 안전 확인
        if not force and clear_existing:
            confirm = input('\n⚠️  기존 데이터를 모두 삭제하고 복원하시겠습니까? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write('복원이 취소되었습니다.')
                if extracted_path:
                    shutil.rmtree(extracted_path)
                return
        
        try:
            self.stdout.write('데이터베이스 복원을 시작합니다...')
            
            # 1. 기존 데이터 삭제 (옵션)
            if clear_existing:
                self._clear_existing_data()
            
            # 2. 데이터베이스 복원
            self._restore_database(working_path)
            
            # 3. SQLite 파일 복원 (옵션)
            self._restore_sqlite_file(working_path)
            
            # 4. 미디어 파일 복원 (옵션)
            if restore_media:
                self._restore_media_files(working_path)
            
            self.stdout.write(
                self.style.SUCCESS('데이터베이스 복원이 완료되었습니다!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'복원 중 오류가 발생했습니다: {str(e)}')
            )
            raise
        
        finally:
            # 임시 압축 해제 디렉토리 정리
            if extracted_path:
                shutil.rmtree(extracted_path)

    def _extract_backup(self, zip_path):
        """ZIP 백업 파일 압축 해제"""
        self.stdout.write('백업 파일 압축 해제 중...')
        
        extract_path = f'{zip_path}_extracted'
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_path)
        
        self.stdout.write('  ✓ 압축 해제 완료')
        return extract_path

    def _show_backup_info(self, info_file):
        """백업 정보 표시"""
        with open(info_file, 'r', encoding='utf-8') as f:
            backup_info = json.load(f)
        
        self.stdout.write('\n=== 백업 정보 ===')
        self.stdout.write(f"백업 시간: {backup_info.get('timestamp', 'Unknown')}")
        self.stdout.write(f"Django 버전: {backup_info.get('django_version', 'Unknown')}")
        self.stdout.write(f"데이터베이스: {backup_info.get('database_engine', 'Unknown')}")
        self.stdout.write(f"미디어 포함: {backup_info.get('include_media', False)}")
        
        if 'models' in backup_info:
            self.stdout.write('\n모델별 데이터 수:')
            for model, count in backup_info['models'].items():
                self.stdout.write(f"  - {model}: {count}개")
        
        self.stdout.write('=' * 20)

    def _clear_existing_data(self):
        """기존 데이터 삭제"""
        self.stdout.write('기존 데이터 삭제 중...')
        
        # 외래키 관계를 고려하여 역순으로 삭제
        models_to_clear = [History, Schedule, FollowUp, UserProfile]
        
        with transaction.atomic():
            for model in models_to_clear:
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    self.stdout.write(f'  - {model.__name__}: {count}개 삭제')

    def _restore_database(self, backup_path):
        """JSON 백업에서 데이터베이스 복원"""
        self.stdout.write('데이터베이스 모델 복원 중...')
        
        # 복원할 파일들과 순서 (외래키 관계 고려)
        files_to_restore = [
            ('users.json', User),
            ('userprofiles.json', UserProfile),
            ('followups.json', FollowUp),
            ('schedules.json', Schedule),
            ('histories.json', History),
        ]
        
        with transaction.atomic():
            for filename, model in files_to_restore:
                file_path = os.path.join(backup_path, filename)
                
                if os.path.exists(file_path):
                    self.stdout.write(f'  - {model.__name__} 복원 중...')
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    
                    # JSON 데이터를 객체로 역직렬화
                    objects = serializers.deserialize('json', data)
                    restored_count = 0
                    
                    for obj in objects:
                        try:
                            obj.save()
                            restored_count += 1
                        except Exception as e:
                            self.stdout.write(f'    ⚠️  객체 복원 실패: {str(e)}')
                    
                    self.stdout.write(f'    ✓ {restored_count}개 항목 복원 완료')
                else:
                    self.stdout.write(f'    ⚠️  {filename} 파일을 찾을 수 없습니다.')

    def _restore_sqlite_file(self, backup_path):
        """SQLite 데이터베이스 파일 복원"""
        db_config = settings.DATABASES['default']
        
        if db_config['ENGINE'] == 'django.db.backends.sqlite3':
            backup_db_file = os.path.join(backup_path, 'db.sqlite3')
            
            if os.path.exists(backup_db_file):
                current_db_file = db_config['NAME']
                
                # 현재 DB 파일 백업
                if os.path.exists(current_db_file):
                    backup_current = f'{current_db_file}.backup'
                    shutil.copy2(current_db_file, backup_current)
                    self.stdout.write(f'현재 DB 파일을 {backup_current}로 백업했습니다.')
                
                # 백업 DB 파일로 교체
                shutil.copy2(backup_db_file, current_db_file)
                self.stdout.write('SQLite 데이터베이스 파일 복원 완료')

    def _restore_media_files(self, backup_path):
        """미디어 파일 복원"""
        media_backup_path = os.path.join(backup_path, 'media')
        
        if os.path.exists(media_backup_path):
            self.stdout.write('미디어 파일 복원 중...')
            
            media_root = settings.MEDIA_ROOT
            
            # 기존 미디어 디렉토리 백업
            if os.path.exists(media_root):
                media_backup = f'{media_root}_backup'
                if os.path.exists(media_backup):
                    shutil.rmtree(media_backup)
                shutil.move(media_root, media_backup)
                self.stdout.write(f'기존 미디어 파일을 {media_backup}로 백업했습니다.')
            
            # 백업된 미디어 파일 복원
            shutil.copytree(media_backup_path, media_root)
            self.stdout.write('  ✓ 미디어 파일 복원 완료')
