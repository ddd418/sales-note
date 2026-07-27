"""
Celery 비동기 작업
- 오래된 파일 정리 (매일 새벽 3시)
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def cleanup_old_files_task(self):
    """
    오래된 파일 자동 정리 (매일 새벽 3시)
    
    영구 보관:
    - document_templates/ (서류 템플릿)
    - business_card_logos/ (서명 관리 회사 로고)
    - 5MB 이하 파일
    
    100일 후 삭제:
    - 위 조건에 해당하지 않는 5MB 초과 파일
    """
    import os
    from datetime import datetime, timedelta
    from django.conf import settings
    
    # 설정 가져오기
    cleanup_settings = getattr(settings, 'FILE_CLEANUP_SETTINGS', {})
    permanent_paths = cleanup_settings.get('PERMANENT_PATHS', [
        'document_templates/',
        'business_card_logos/',
    ])
    max_size_mb = cleanup_settings.get('PERMANENT_MAX_SIZE_MB', 5)
    retention_days = cleanup_settings.get('TEMP_FILE_RETENTION_DAYS', 100)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    
    if not media_root or not os.path.exists(media_root):
        logger.warning(f'MEDIA_ROOT가 없거나 존재하지 않음: {media_root}')
        return {'deleted': 0, 'error': 'MEDIA_ROOT not found'}
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    deleted_files = 0
    deleted_size = 0
    errors = []
    
    for root, dirs, files in os.walk(media_root):
        for filename in files:
            filepath = os.path.join(root, filename)
            relative_path = os.path.relpath(filepath, media_root)
            
            try:
                file_stat = os.stat(filepath)
                file_size = file_stat.st_size
                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                
                # 영구 보관 경로 체크
                is_permanent = any(
                    relative_path.startswith(path) for path in permanent_paths
                )
                if is_permanent:
                    continue
                
                # 5MB 이하는 영구 보관
                if file_size <= max_size_bytes:
                    continue
                
                # 100일 이내는 보관
                if file_mtime > cutoff_date:
                    continue
                
                # 삭제
                os.remove(filepath)
                deleted_files += 1
                deleted_size += file_size
                
                file_size_mb = file_size / (1024 * 1024)
                age_days = (datetime.now() - file_mtime).days
                logger.info(f'파일 삭제: {relative_path} ({file_size_mb:.2f}MB, {age_days}일 전)')
                
            except Exception as e:
                errors.append(f'{filepath}: {str(e)}')
                logger.error(f'파일 삭제 실패: {filepath} - {str(e)}')
    
    # 빈 디렉토리 정리
    for root, dirs, files in os.walk(media_root, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except Exception:
                pass
    
    deleted_size_mb = deleted_size / (1024 * 1024)
    logger.info(f'파일 정리 완료: {deleted_files}개 삭제 ({deleted_size_mb:.2f}MB)')
    
    return {
        'deleted_files': deleted_files,
        'deleted_size_mb': round(deleted_size_mb, 2),
        'errors': len(errors)
    }
