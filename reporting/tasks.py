"""
Celery 비동기 작업
- 주기적 Gmail 동기화 (10분마다)
"""
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


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
