"""
Celery 비동기 작업
- 주기적 Gmail 동기화 (10분마다)
- 오래된 파일 정리 (매일 새벽 3시)
"""
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def refresh_gmail_tokens(self):
    """
    Gmail 연결된 사용자들의 토큰 자동 갱신 (매일 1회)
    - 만료된 토큰 자동 갱신
    - refresh_token이 있는 경우에만 갱신 시도
    - 사용자가 다시 인증할 필요 없이 자동으로 토큰 유지
    """
    from .models import UserProfile
    from .gmail_utils import GmailService
    
    refreshed_count = 0
    failed_count = 0
    
    # Gmail 연결된 모든 사용자 조회
    profiles = UserProfile.objects.filter(
        gmail_token__isnull=False
    ).select_related('user')
    
    for profile in profiles:
        try:
            # refresh_token 존재 확인
            token_data = profile.gmail_token
            if not token_data or not token_data.get('refresh_token'):
                logger.warning(f'Gmail refresh_token 없음: {profile.user.username}')
                continue
            
            # GmailService를 통해 토큰 갱신 시도
            gmail_service = GmailService(profile)
            creds = gmail_service.get_credentials()
            
            if creds:
                # 갱신 성공 - 저장은 get_credentials에서 자동으로 됨
                refreshed_count += 1
                logger.info(f'Gmail 토큰 갱신 성공: {profile.user.username}')
            else:
                failed_count += 1
                logger.warning(f'Gmail 토큰 갱신 실패 (재인증 필요): {profile.user.username}')
                
        except Exception as e:
            failed_count += 1
            logger.error(f'Gmail 토큰 갱신 오류 ({profile.user.username}): {str(e)}')
            continue
    
    logger.info(f'Gmail 토큰 갱신 완료: 성공 {refreshed_count}명, 실패 {failed_count}명')
    
    return {'refreshed': refreshed_count, 'failed': failed_count}


@shared_task(bind=True, ignore_result=True)
def auto_sync_gmail(self):
    """
    모든 Gmail 연결된 사용자의 메일 자동 동기화 (10분마다)
    - 최근 1일치 메일만 가져옴
    - 이미 동기화된 메일은 스킵
    """
    from .models import UserProfile, EmailLog, FollowUp
    from .gmail_utils import GmailService
    from django.db import transaction
    
    synced_users = 0
    total_synced = 0
    
    # Gmail 연결된 모든 사용자 조회
    profiles = UserProfile.objects.filter(
        gmail_token__isnull=False
    ).select_related('user')
    
    for profile in profiles:
        try:
            gmail_service = GmailService(profile)
            
            # 팔로우업 이메일 주소 목록
            followup_emails = set()
            followups = FollowUp.objects.filter(user=profile.user)
            for followup in followups:
                if followup.email:
                    followup_emails.add(followup.email.lower())
            
            if not followup_emails:
                continue
            
            # 최근 1일치 메일만 가져오기
            query = 'newer_than:1d'
            result = gmail_service.get_messages(query=query, max_results=50)
            messages = result.get('messages', [])
            
            user_synced = 0
            with transaction.atomic():
                for msg in messages:
                    # 이미 DB에 있는지 확인 (중복 방지)
                    if EmailLog.objects.filter(gmail_message_id=msg['id']).exists():
                        continue
                    
                    msg_detail = gmail_service.get_message_detail(msg['id'])
                    if not msg_detail:
                        continue
                    
                    # From 주소 추출
                    from_header = msg_detail.get('from', '')
                    from_email = ''
                    if '<' in from_header:
                        from_email = from_header.split('<')[1].split('>')[0].lower()
                    else:
                        from_email = from_header.lower()
                    
                    # 팔로우업 이메일과 매칭
                    matched_followup = None
                    for followup in followups:
                        if followup.email and followup.email.lower() == from_email:
                            matched_followup = followup
                            break
                    
                    if not matched_followup:
                        continue
                    
                    # EmailLog 생성
                    body_content = msg_detail['body_text'] or msg_detail.get('snippet', '')
                    
                    EmailLog.objects.create(
                        email_type='received',
                        sender_email=from_email,
                        recipient_email=profile.gmail_email,
                        subject=msg_detail['subject'],
                        body=body_content,
                        body_html=msg_detail['body_html'],
                        gmail_message_id=msg_detail['id'],
                        gmail_thread_id=msg_detail['thread_id'],
                        followup=matched_followup,
                        is_read=False,
                        status='received'
                    )
                    user_synced += 1
            
            if user_synced > 0:
                synced_users += 1
                total_synced += user_synced
                logger.info(f'Gmail 자동 동기화: {profile.user.username} - {user_synced}개 메일')
                
        except Exception as e:
            logger.error(f'Gmail 자동 동기화 실패 ({profile.user.username}): {str(e)}')
            continue
    
    if total_synced > 0:
        logger.info(f'Gmail 자동 동기화 완료: {synced_users}명 사용자, 총 {total_synced}개 메일')
    
    return {'synced_users': synced_users, 'total_synced': total_synced}


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
