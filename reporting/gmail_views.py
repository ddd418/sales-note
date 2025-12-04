"""
Gmail 연동 관련 뷰
- OAuth2 인증 (연결, 콜백, 연결 해제)
- 메일 발송 (일정/메일함에서)
- 메일함 조회 (받은편지함, 보낸편지함, 스레드 상세)
- 수신 메일 동기화
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.core.paginator import Paginator
import json

from .models import UserProfile, EmailLog, BusinessCard, Schedule, FollowUp, History
from .gmail_utils import GmailService, get_authorization_url, exchange_code_for_token


# ============================================
# 헬퍼 함수
# ============================================

def _sync_emails_by_days(user, days=1):
    """
    지정한 일수만큼 메일 동기화
    
    Args:
        user: User 객체
        days: 동기화할 일수 (기본 1일)
    
    Returns:
        동기화된 메일 개수
    """
    from django.utils import timezone
    from datetime import timedelta
    
    profile = user.userprofile
    
    if not profile.gmail_token:
        return 0
    
    gmail_service = GmailService(profile)
    
    # 팔로우업 및 일정 관련 이메일 주소 목록
    target_emails = set()
    followups = FollowUp.objects.filter(user=user)
    for followup in followups:
        if followup.email:
            target_emails.add(followup.email.lower())
    
    # 일정 관련 이메일도 추가
    schedules = Schedule.objects.filter(user=user).select_related('followup')
    for schedule in schedules:
        if schedule.followup and schedule.followup.email:
            target_emails.add(schedule.followup.email.lower())
    
    if not target_emails:
        return 0
    
    # 마지막 동기화 시점 이후의 메일만 가져오기
    if profile.gmail_last_sync_at:
        # 마지막 동기화 이후 메일만
        query = f'after:{int(profile.gmail_last_sync_at.timestamp())}'
        max_results = 100
    else:
        # 첫 동기화 또는 지정된 일수
        query = f'newer_than:{days}d'
        max_results = 200 if days > 7 else 100
    
    result = gmail_service.get_messages(query=query, max_results=max_results)
    messages_list = result.get('messages', [])
    
    synced_count = 0
    with transaction.atomic():
        for msg in messages_list:
            # 이미 DB에 있는지 확인 (중복 방지)
            if EmailLog.objects.filter(gmail_message_id=msg['id']).exists():
                continue
            
            msg_detail = gmail_service.get_message_detail(msg['id'])
            if not msg_detail:
                continue
            
            # From/To 주소 추출
            from_header = msg_detail.get('from', '')
            to_header = msg_detail.get('to', '')
            
            # From 이메일 추출
            from_email = ''
            if from_header:
                if '<' in from_header:
                    try:
                        from_email = from_header.split('<')[1].split('>')[0].lower()
                    except:
                        from_email = from_header.lower()
                else:
                    from_email = from_header.lower()
            
            # To 이메일 추출 (첫 번째 수신자만)
            to_email = ''
            if to_header:
                # 여러 수신자가 있을 수 있으므로 쉼표로 분리
                first_to = to_header.split(',')[0].strip()
                if '<' in first_to:
                    try:
                        to_email = first_to.split('<')[1].split('>')[0].lower()
                    except:
                        to_email = first_to.lower()
                else:
                    to_email = first_to.lower()
            
            if not from_email or not to_email:
                continue
            
            # 수신 메일인지 발신 메일인지 확인
            is_sent = from_email == profile.gmail_email.lower()
            
            # 팔로우업 또는 일정 이메일과 매칭
            matched_followup = None
            matched_schedule = None
            target_email = to_email if is_sent else from_email
            
            # 먼저 일정 확인 (스레드 ID로 매칭)
            if msg_detail.get('thread_id'):
                existing_email = EmailLog.objects.filter(
                    gmail_thread_id=msg_detail['thread_id']
                ).select_related('schedule', 'followup').first()
                
                if existing_email:
                    matched_schedule = existing_email.schedule
                    matched_followup = existing_email.followup or matched_followup
            
            # 일정이 없으면 팔로우업으로 매칭
            if not matched_followup:
                for followup in followups:
                    if followup.email and followup.email.lower() == target_email:
                        matched_followup = followup
                        break
            
            if not matched_followup and not matched_schedule:
                continue
            
            # 본문 내용 처리 (HTML 우선, 없으면 텍스트)
            body_html = msg_detail.get('body_html', '')
            body_text = msg_detail.get('body_text', '')
            
            # body 필드는 HTML이 있으면 HTML, 없으면 텍스트 사용
            body_content = body_html if body_html else body_text
            
            # 둘 다 없으면 snippet 사용
            if not body_content:
                body_content = msg_detail.get('snippet', '')
            
            # 날짜 파싱
            from email.utils import parsedate_to_datetime
            email_date = None
            if msg_detail.get('date'):
                try:
                    email_date = parsedate_to_datetime(msg_detail['date'])
                except:
                    pass
            
            EmailLog.objects.create(
                email_type='sent' if is_sent else 'received',
                sender=user if is_sent else None,
                sender_email=from_email,
                recipient_email=to_email,
                subject=msg_detail['subject'],
                body=body_content,
                body_html=body_html,
                gmail_message_id=msg_detail['id'],
                gmail_thread_id=msg_detail['thread_id'],
                followup=matched_followup,
                schedule=matched_schedule,
                is_read=True if is_sent else False,
                status='sent' if is_sent else 'received',
                sent_at=email_date if is_sent else None,
                received_at=email_date if not is_sent else None
            )
            synced_count += 1
    
    # 동기화 시점 업데이트
    if synced_count > 0 or profile.gmail_last_sync_at:
        profile.gmail_last_sync_at = timezone.now()
        profile.save(update_fields=['gmail_last_sync_at'])
    
    return synced_count


# ============================================
# Gmail OAuth2 인증
# ============================================

@login_required
def gmail_connect(request):
    """Gmail 계정 연결 시작"""
    # 환경 변수 체크
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET or not settings.GMAIL_REDIRECT_URI:
        messages.error(request, 'Gmail API 설정이 올바르지 않습니다. 관리자에게 문의하세요.')
        return redirect('reporting:profile')
    
    try:
        redirect_uri = settings.GMAIL_REDIRECT_URI
        auth_url, state = get_authorization_url(redirect_uri)
        # state를 세션에 저장 (보안을 위해)
        request.session['gmail_oauth_state'] = state
        return redirect(auth_url)
    except Exception as e:
        messages.error(request, f'Gmail 연결 시작 중 오류: {str(e)}')
        return redirect('reporting:profile')


@login_required
def gmail_callback(request):
    """Gmail OAuth2 콜백"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f'Gmail 연결 실패: {error}')
        return redirect('reporting:profile')  # 프로필 페이지로 리다이렉트
    
    if not code:
        messages.error(request, 'Gmail 인증 코드가 없습니다.')
        return redirect('reporting:profile')
    
    try:
        # 인증 코드를 토큰으로 교환
        redirect_uri = settings.GMAIL_REDIRECT_URI
        creds, gmail_email = exchange_code_for_token(code, redirect_uri)
        
        # UserProfile에 토큰 저장
        profile = request.user.userprofile
        profile.gmail_token = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        profile.gmail_email = gmail_email
        profile.save()
        
        # 첫 연동 시 메시지만 표시 (동기화는 사용자가 수동으로 또는 나중에)
        messages.success(request, f'Gmail 계정({gmail_email})이 연결되었습니다. 메일함에서 "메일 동기화" 버튼을 눌러 이메일을 가져올 수 있습니다.')
        
        return redirect('reporting:profile')
        
    except Exception as e:
        messages.error(request, f'Gmail 연결 중 오류 발생: {str(e)}')
        return redirect('reporting:profile')


@login_required
def gmail_disconnect(request):
    """Gmail 계정 연결 해제"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            profile.gmail_token = None
            profile.gmail_email = ''
            profile.gmail_connected_at = None
            profile.gmail_last_sync_at = None
            profile.save()
            
            messages.success(request, 'Gmail 계정 연결이 해제되었습니다.')
        except Exception as e:
            messages.error(request, f'연결 해제 중 오류 발생: {str(e)}')
    
    return redirect('reporting:profile')


# ============================================
# 이메일 발송
# ============================================

@login_required
def send_email_from_schedule(request, schedule_id):
    """일정에서 이메일 발송"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # 권한 확인: 자신의 일정 또는 매니저
    if schedule.user != request.user and request.user.userprofile.role != 'manager':
        messages.error(request, '권한이 없습니다.')
        return redirect('reporting:schedule_detail', pk=schedule_id)
    
    # Gmail 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token:
        messages.error(request, 'Gmail 계정을 먼저 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'schedule': schedule,
        'followup': schedule.followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    
    if request.method == 'POST':
        result = _handle_email_send(request, schedule=schedule)
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            # 디버그: 오류 정보 로깅
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Email send validation failed: {result}")
            context.update(result)
            return render(request, 'reporting/gmail/compose_from_schedule.html', context)
        # 성공 시 (리다이렉트 반환)
        return result
    
    # GET: 이메일 작성 폼
    return render(request, 'reporting/gmail/compose_from_schedule.html', context)


@login_required
def send_email_from_mailbox(request, followup_id=None):
    """메일함에서 이메일 발송 (팔로우업 연결)"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"send_email_from_mailbox called: method={request.method}, user={request.user}, followup_id={followup_id}")
    
    followup = None
    if followup_id:
        followup = get_object_or_404(FollowUp, id=followup_id)
        
        # 권한 확인: 자신의 팔로우업 또는 매니저
        if followup.user != request.user and request.user.userprofile.role != 'manager':
            messages.error(request, '권한이 없습니다.')
            return redirect('reporting:mailbox_inbox')
    
    # Gmail 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token:
        messages.error(request, 'Gmail 계정을 먼저 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'followup': followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
        'all_followups': FollowUp.objects.filter(user=request.user).order_by('-created_at')[:100],
    }
    
    if request.method == 'POST':
        logger.info(f"POST request received, calling _handle_email_send")
        
        # 팔로우업 검색으로 선택한 경우 처리
        if not followup:
            selected_followup_id = request.POST.get('selected_followup_id')
            if selected_followup_id:
                try:
                    followup = FollowUp.objects.get(id=selected_followup_id, user=request.user)
                    logger.info(f"Followup selected from search: {followup.id}")
                except FollowUp.DoesNotExist:
                    pass
        
        result = _handle_email_send(request, followup=followup)
        logger.info(f"_handle_email_send result type: {type(result)}, is_dict: {isinstance(result, dict)}")
        
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            logger.warning(f"Email validation failed, re-rendering template with errors: {result}")
            context.update(result)
            return render(request, 'reporting/gmail/compose_from_mailbox.html', context)
        # 성공 시 (리다이렉트 반환)
        logger.info(f"Email sent successfully, redirecting")
        return result
    
    # GET: 이메일 작성 폼
    return render(request, 'reporting/gmail/compose_from_mailbox.html', context)


@login_required
def reply_email(request, email_log_id):
    """이메일 답장"""
    email_log = get_object_or_404(EmailLog, id=email_log_id)
    
    # 권한 확인: 발신 메일은 발신자만, 수신 메일은 누구나 답장 가능
    if email_log.email_type == 'sent':
        # 발신 메일: 본인이 보낸 메일만 답장 가능
        if email_log.sender != request.user and request.user.userprofile.role != 'manager':
            messages.error(request, '권한이 없습니다.')
            return redirect('reporting:mailbox_inbox')
    # 수신 메일은 권한 체크 없이 누구나 답장 가능
    
    # Gmail 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token:
        messages.error(request, 'Gmail 계정을 먼저 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'original_email': email_log,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    
    if request.method == 'POST':
        result = _handle_email_send(request, reply_to=email_log)
        # 검증 실패 시 (템플릿 반환)
        if isinstance(result, dict):
            context.update(result)
            return render(request, 'reporting/gmail/reply_email.html', context)
        # 성공 시 (리다이렉트 반환)
        return result
    
    # GET: 답장 폼
    return render(request, 'reporting/gmail/reply_email.html', context)


def _handle_email_send(request, schedule=None, followup=None, reply_to=None):
    """이메일 발송 공통 처리"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"_handle_email_send called: user={request.user}, schedule={schedule}, followup={followup}")
        
        # POST 데이터 추출
        to_email = request.POST.get('to_email', '')
        cc_emails = request.POST.get('cc_emails', '')
        bcc_emails = request.POST.get('bcc_emails', '')
        subject = request.POST.get('subject', '')
        body_text = request.POST.get('body_text', '')
        body_html = request.POST.get('body_html', '')
        business_card_id = request.POST.get('business_card_id', '')
        
        logger.info(f"Form data: to_email={to_email}, subject={subject}, body_text_len={len(body_text)}, body_html_len={len(body_html)}")
        
        # 유효성 검사 - 검증 실패 시 딕셔너리 반환 (템플릿 재렌더링용)
        if not to_email or not subject:
            logger.warning(f"Validation failed: missing to_email or subject")
            messages.error(request, '받는 사람과 제목은 필수입니다.')
            return {
                'error': True,
                'form_data': {
                    'to_email': to_email,
                    'cc_emails': cc_emails,
                    'bcc_emails': bcc_emails,
                    'subject': subject,
                    'body_text': body_text,
                    'body_html': body_html,
                    'business_card_id': business_card_id,
                }
            }
        
        if not body_text and not body_html:
            logger.warning(f"Validation failed: missing body")
            messages.error(request, '본문을 입력해주세요.')
            return {
                'error': True,
                'form_data': {
                    'to_email': to_email,
                    'cc_emails': cc_emails,
                    'bcc_emails': bcc_emails,
                    'subject': subject,
                    'body_text': body_text,
                    'body_html': body_html,
                    'business_card_id': business_card_id,
                }
            }
        
        # 명함 서명 추가
        signature_html = ''
        business_card = None
        if business_card_id:
            business_card = BusinessCard.objects.get(id=business_card_id, user=request.user)
            signature_html = business_card.generate_signature(request=request)
        
        # 본문과 서명 사이 구분선
        separator = '<div style="margin: 20px 0; padding-top: 20px; border-top: 1px solid #ddd;"></div>' if signature_html else ''
        
        # HTML 본문에 서명 추가
        if body_html and body_html.strip():
            full_body_html = body_html + separator + signature_html
        else:
            # HTML이 비어있으면 body_text를 사용
            if body_text and body_text.strip():
                # 텍스트를 HTML로 변환 (줄바꿈 보존)
                text_as_html = body_text.replace('\n', '<br>')
                full_body_html = f'<div style="font-family: Arial, sans-serif; white-space: pre-wrap;">{text_as_html}</div>' + separator + signature_html
            else:
                full_body_html = signature_html
        
        # Gmail 서비스 생성
        gmail_service = GmailService(request.user.userprofile)
        
        # 첨부파일 처리
        attachments = []
        attachments_info = []  # 첨부파일 정보 저장용
        files = request.FILES.getlist('attachments')
        for uploaded_file in files:
            attachments.append({
                'filename': uploaded_file.name,
                'content': uploaded_file.read(),
                'mimetype': uploaded_file.content_type
            })
            # 첨부파일 정보 저장
            attachments_info.append({
                'filename': uploaded_file.name,
                'size': uploaded_file.size,
                'mimetype': uploaded_file.content_type
            })
        
        # 답장 정보
        in_reply_to = None
        thread_id = None
        if reply_to:
            in_reply_to = reply_to.gmail_message_id
            thread_id = reply_to.gmail_thread_id
            if not followup:
                followup = reply_to.followup
            if not schedule:
                schedule = reply_to.schedule
        
        # 이메일 발송
        message_info = gmail_service.send_email(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            body_html=full_body_html,
            cc=[email.strip() for email in cc_emails.split(',') if email.strip()],
            bcc=[email.strip() for email in bcc_emails.split(',') if email.strip()],
            attachments=attachments,
            in_reply_to=in_reply_to,
            thread_id=thread_id
        )
        
        if not message_info:
            raise Exception("이메일 발송에 실패했습니다.")
        
        # EmailLog 생성
        from django.utils import timezone
        
        # 일정 자동 생성 옵션 확인
        create_schedule_option = request.POST.get('create_schedule') == '1'
        created_schedule = None
        
        with transaction.atomic():
            # 일정 자동 생성 (팔로우업이 있고, 기존 일정이 없고, 옵션이 선택된 경우)
            if followup and not schedule and create_schedule_option:
                from datetime import datetime, time
                today = timezone.now().date()
                current_time = timezone.now().time()
                
                # 새 일정 생성
                created_schedule = Schedule.objects.create(
                    user=request.user,
                    company=request.user.userprofile.company,
                    followup=followup,
                    visit_date=today,
                    visit_time=current_time.replace(second=0, microsecond=0),
                    location='이메일',
                    status='completed',  # 이메일 발송은 완료 상태로
                    activity_type='customer_meeting',
                    notes=f'이메일 발송: {subject}'
                )
                schedule = created_schedule
                logger.info(f"Schedule auto-created: id={created_schedule.id} for followup={followup.id}")
            
            email_log = EmailLog.objects.create(
                email_type='sent',
                sender=request.user,
                sender_email=request.user.userprofile.gmail_email,
                recipient_email=to_email,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body=body_html if body_html else body_text,
                body_html=full_body_html,
                gmail_message_id=message_info['message_id'],
                gmail_thread_id=message_info['thread_id'],
                followup=followup,
                schedule=schedule,
                business_card=business_card,
                in_reply_to=reply_to,
                status='sent',
                sent_at=timezone.now(),
                attachments_info=attachments_info  # 첨부파일 정보 저장
            )
            
            # 자동 생성된 일정에 히스토리 추가
            if created_schedule:
                History.objects.create(
                    user=request.user,
                    company=request.user.userprofile.company,
                    followup=followup,
                    schedule=created_schedule,
                    action_type='customer_meeting',
                    content=f'📧 이메일 발송\n\n받는 사람: {to_email}\n제목: {subject}',
                    meeting_date=today
                )
        
        if created_schedule:
            messages.success(request, f'이메일이 발송되었고, 일정이 자동 생성되었습니다.')
        else:
            messages.success(request, '이메일이 발송되었습니다.')
        
        # 리다이렉트 경로 결정
        if schedule:
            return redirect('reporting:schedule_detail', pk=schedule.id)
        elif followup:
            return redirect('reporting:mailbox_thread', thread_id=email_log.gmail_thread_id)
        else:
            return redirect('reporting:mailbox_sent')
        
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Exception in _handle_email_send: {str(e)}")
        logger.error(traceback.format_exc())
        
        messages.error(request, f'이메일 발송 실패: {str(e)}')
        # POST 데이터 다시 가져오기
        return {
            'error': True,
            'exception': str(e),
            'form_data': {
                'to_email': request.POST.get('to_email', ''),
                'cc_emails': request.POST.get('cc_emails', ''),
                'bcc_emails': request.POST.get('bcc_emails', ''),
                'subject': request.POST.get('subject', ''),
                'body_text': request.POST.get('body_text', ''),
                'body_html': request.POST.get('body_html', ''),
                'business_card_id': request.POST.get('business_card_id', ''),
            }
        }


# ============================================
# 메일함 조회
# ============================================

@login_required
def mailbox_inbox(request):
    """받은편지함 (본인 담당 팔로우업 연결 메일만)"""
    profile = request.user.userprofile
    
    # Gmail 연결 확인
    if not profile.gmail_token:
        messages.warning(request, 'Gmail 계정을 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # DB에서 수신 메일 조회 (본인 담당 팔로우업만)
    emails = EmailLog.objects.filter(
        email_type='received',
        followup__isnull=False,  # 팔로우업 연결된 메일만
        followup__user=request.user  # 본인 담당 팔로우업만
    ).select_related('followup', 'sender', 'business_card').order_by('-sent_at')
    
    # 페이지네이션 (20개씩)
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'inbox',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_sent(request):
    """보낸편지함"""
    emails = EmailLog.objects.filter(
        email_type='sent',
        sender=request.user
    ).select_related('followup', 'schedule', 'business_card').order_by('-sent_at')
    
    # 페이지네이션 (20개씩)
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'sent',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_thread(request, thread_id):
    """이메일 스레드 상세 (대화 전체)"""
    profile = request.user.userprofile
    
    # Gmail 연결 확인
    if not profile.gmail_token:
        messages.warning(request, 'Gmail 계정을 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # DB에서 스레드의 모든 메일 조회
    emails = EmailLog.objects.filter(
        gmail_thread_id=thread_id
    ).select_related('sender', 'followup', 'schedule', 'business_card').order_by('sent_at')
    
    if not emails.exists():
        messages.error(request, '해당 스레드를 찾을 수 없습니다.')
        return redirect('reporting:mailbox_inbox')
    
    # 읽음 표시 (수신 메일만)
    unread_emails = emails.filter(email_type='received', is_read=False)
    if unread_emails.exists():
        unread_emails.update(is_read=True)
        
        # Gmail에도 읽음 표시
        gmail_service = GmailService(profile)
        for email in unread_emails:
            try:
                gmail_service.mark_as_read(email.gmail_message_id)
            except:
                pass  # 실패해도 계속 진행
    
    # 답장 대상: 가장 최근 수신 메일
    last_received_email = emails.filter(email_type='received').order_by('-sent_at', '-received_at').first()
    
    context = {
        'thread_id': thread_id,
        'emails': emails,
        'followup': emails.first().followup,
        'last_received_email': last_received_email,
    }
    return render(request, 'reporting/gmail/thread_detail.html', context)


@login_required
@login_required
@login_required
def sync_received_emails(request):
    """
    수동 메일 동기화
    - 마지막 동기화 시점 이후의 메일만 가져옴
    - 첫 동기화인 경우 최근 1일치
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    profile = request.user.userprofile
    
    # Gmail 연결 확인
    if not profile.gmail_token:
        return JsonResponse({'success': False, 'error': 'Gmail 계정이 연결되지 않았습니다.'})
    
    try:
        # 마지막 동기화 시점 이후의 메일만 동기화
        synced_count = _sync_emails_by_days(request.user, days=1)
        
        if synced_count > 0:
            message = f'{synced_count}개의 새 메일을 동기화했습니다.'
        else:
            message = '새로운 메일이 없습니다.'
        
        return JsonResponse({
            'success': True,
            'synced': synced_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_email(request, email_id):
    """이메일 삭제"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"delete_email called: email_id={email_id}, user={request.user.username}, method={request.method}")
    
    if request.method == 'POST':
        try:
            email = get_object_or_404(EmailLog, id=email_id)
            logger.info(f"Email found: id={email.id}, type={email.email_type}, sender={email.sender}, sender_email={email.sender_email}")
            
            # 권한 확인: 관리자, 본인이 보낸 메일, 또는 본인 팔로우업 관련 메일만 삭제 가능
            can_delete = False
            
            # 관리자는 모든 메일 삭제 가능
            if request.user.is_staff or request.user.is_superuser:
                can_delete = True
                logger.info("Delete allowed: user is staff/superuser")
            # 보낸 메일: sender가 본인이거나 sender_email이 본인 이메일
            elif email.email_type == 'sent':
                if email.sender == request.user:
                    can_delete = True
                    logger.info("Delete allowed: sender matches user")
                elif email.sender_email and request.user.email and email.sender_email == request.user.email:
                    can_delete = True
                    logger.info("Delete allowed: sender_email matches user email")
                else:
                    logger.info(f"Delete denied: sent mail - sender={email.sender}, user={request.user}, sender_email={email.sender_email}, user_email={request.user.email}")
            # 받은 메일: followup 담당자가 본인
            elif email.email_type == 'received':
                if email.followup and email.followup.user == request.user:
                    can_delete = True
                    logger.info("Delete allowed: followup user matches")
                elif not email.followup:
                    # followup이 없는 받은 메일은 삭제 가능
                    can_delete = True
                    logger.info("Delete allowed: no followup")
                else:
                    logger.info(f"Delete denied: received mail - followup.user={email.followup.user if email.followup else None}, user={request.user}")
            
            if not can_delete:
                logger.warning(f"Delete permission denied for email {email_id}")
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다.'})
            
            email.delete()
            logger.info(f"Email {email_id} deleted successfully")
            return JsonResponse({'success': True, 'message': '메일이 삭제되었습니다.'})
            
        except Exception as e:
            logger.exception(f"Error deleting email {email_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})


# ============================================
# 명함 관리
# ============================================

@login_required
def business_card_list(request):
    """명함 목록"""
    cards = BusinessCard.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    # 각 카드의 서명을 미리 생성 (절대 URL 포함)
    for card in cards:
        card.signature_preview = card.generate_signature(request=request)
    
    context = {
        'cards': cards
    }
    return render(request, 'reporting/gmail/business_card_list.html', context)


@login_required
def business_card_create(request):
    """명함 생성"""
    if request.method == 'POST':
        try:
            card = BusinessCard.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                full_name=request.POST.get('full_name'),
                title=request.POST.get('title'),
                company_name=request.POST.get('company_name'),
                phone=request.POST.get('phone', ''),
                mobile=request.POST.get('mobile', ''),
                email=request.POST.get('email'),
                address=request.POST.get('address', ''),
                website=request.POST.get('website', ''),
                logo_url=request.POST.get('logo_url', ''),
                logo_link_url=request.POST.get('logo_link_url', ''),
                is_default=request.POST.get('is_default') == 'on'
            )
            
            # 로고 이미지 파일 업로드
            if 'logo' in request.FILES:
                card.logo = request.FILES['logo']
                card.save()
            
            messages.success(request, '명함이 생성되었습니다.')
            return redirect('reporting:business_card_list')
        except Exception as e:
            messages.error(request, f'명함 생성 실패: {str(e)}')
    
    return render(request, 'reporting/gmail/business_card_form.html', {'card': None})


@login_required
def business_card_edit(request, card_id):
    """명함 수정"""
    card = get_object_or_404(BusinessCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        try:
            card.name = request.POST.get('name')
            card.full_name = request.POST.get('full_name')
            card.title = request.POST.get('title')
            card.company_name = request.POST.get('company_name')
            card.phone = request.POST.get('phone', '')
            card.mobile = request.POST.get('mobile', '')
            card.email = request.POST.get('email')
            card.address = request.POST.get('address', '')
            card.website = request.POST.get('website', '')
            card.logo_url = request.POST.get('logo_url', '')
            card.logo_link_url = request.POST.get('logo_link_url', '')
            card.is_default = request.POST.get('is_default') == 'on'
            
            # 로고 이미지 파일 업로드
            if 'logo' in request.FILES:
                card.logo = request.FILES['logo']
            
            card.save()
            
            messages.success(request, '명함이 수정되었습니다.')
            return redirect('reporting:business_card_list')
        except Exception as e:
            messages.error(request, f'명함 수정 실패: {str(e)}')
    
    return render(request, 'reporting/gmail/business_card_form.html', {'card': card})


@login_required
def business_card_delete(request, card_id):
    """명함 삭제 (비활성화)"""
    if request.method == 'POST':
        card = get_object_or_404(BusinessCard, id=card_id, user=request.user)
        card.is_active = False
        card.save()
        
        messages.success(request, '명함이 삭제되었습니다.')
    
    return redirect('reporting:business_card_list')


@login_required
def business_card_set_default(request, card_id):
    """기본 명함 설정"""
    if request.method == 'POST':
        card = get_object_or_404(BusinessCard, id=card_id, user=request.user, is_active=True)
        
        # 기존 기본 명함 해제
        BusinessCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # 새 기본 명함 설정
        card.is_default = True
        card.save()
        
        messages.success(request, f'{card.name} 명함이 기본 명함으로 설정되었습니다.')
    
    return redirect('reporting:business_card_list')


# ============================================
# 이미지 업로드 (Quill 에디터용)
# ============================================

@login_required
def upload_editor_image(request):
    """Quill 에디터에서 이미지 업로드"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            import os
            from django.core.files.storage import default_storage
            from django.conf import settings
            
            uploaded_file = request.FILES['image']
            
            # 파일 크기 제한 (2MB)
            max_size = 2 * 1024 * 1024  # 2MB
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'success': False,
                    'error': '이미지 크기는 2MB 이하여야 합니다.'
                }, status=400)
            
            # 이미지 파일 타입 검증
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if uploaded_file.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'error': '지원하지 않는 이미지 형식입니다. (JPG, PNG, GIF, WebP만 가능)'
                }, status=400)
            
            # 파일명 생성 (중복 방지)
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = os.path.splitext(uploaded_file.name)[1]
            filename = f'email_images/{timestamp}_{uuid.uuid4().hex[:8]}{ext}'
            
            # 파일 저장
            file_path = default_storage.save(filename, uploaded_file)
            
            # 절대 URL 생성
            file_url = default_storage.url(file_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            return JsonResponse({
                'success': True,
                'url': absolute_url
            })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Image upload failed: {str(e)}")
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    }, status=400)
