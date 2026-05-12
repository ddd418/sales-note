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

from .models import UserProfile, EmailLog, BusinessCard, Schedule, FollowUp, DocumentGenerationLog
from .gmail_utils import GmailService, get_authorization_url, exchange_code_for_token


# ============================================
# 헬퍼 함수
# ============================================

def _normalize_email_body_text(value):
    """Normalize textarea line endings before MIME and HTML conversion."""
    return (value or '').replace('\r\n', '\n').replace('\r', '\n')


def _plain_email_body_to_html(value):
    from html import escape

    normalized = _normalize_email_body_text(value)
    escaped = escape(normalized, quote=False)
    html_body = escaped.replace('\n', '<br>\n')
    return f'<div style="font-family: Arial, sans-serif; line-height: 1.45; margin: 0;">{html_body}</div>'


def _uploaded_email_attachments(request):
    attachments = []
    for uploaded_file in request.FILES.getlist('attachments'):
        attachments.append({
            'filename': uploaded_file.name,
            'content': uploaded_file.read(),
            'mimetype': uploaded_file.content_type or 'application/octet-stream',
            'size': uploaded_file.size,
            'source': 'uploaded',
        })
    return attachments


def _quote_document_logs_for_schedule(schedule):
    return DocumentGenerationLog.objects.filter(
        schedule=schedule,
        document_type='quotation',
        output_format='pdf',
        file__isnull=False,
    ).exclude(file='').select_related('user').order_by('created_at', 'id')


def _quote_group_keys_for_schedule(schedule):
    groups = []
    seen = set()
    for item in schedule.delivery_items_set.all().order_by('id'):
        group = (getattr(item, 'quote_group', '') or '').strip()[:100]
        if group in seen:
            continue
        seen.add(group)
        groups.append(group)
    return groups or ['']


def _decode_response_filename(response, fallback='quotation.pdf'):
    from urllib.parse import unquote
    import re

    encoded = response.get('X-Filename', '') if hasattr(response, 'get') else ''
    if encoded:
        try:
            return unquote(encoded)
        except Exception:
            return encoded

    disposition = response.get('Content-Disposition', '') if hasattr(response, 'get') else ''
    encoded_match = re.search(r"filename\*=UTF-8''([^;]+)", disposition, flags=re.I)
    if encoded_match:
        try:
            return unquote(encoded_match.group(1).strip())
        except Exception:
            return encoded_match.group(1).strip()
    quoted_match = re.search(r'filename="?([^";]+)"?', disposition, flags=re.I)
    return quoted_match.group(1).strip() if quoted_match else fallback


def _json_error_from_document_response(response):
    try:
        payload = json.loads(response.content.decode('utf-8') or '{}')
    except Exception:
        payload = {}
    return payload.get('error') or payload.get('message') or '견적서 PDF 생성에 실패했습니다.'


def _attachment_from_document_log(log):
    filename = log.filename or (log.file.name.rsplit('/', 1)[-1] if log.file else 'quotation.pdf')
    with log.file.open('rb') as file_handle:
        content = file_handle.read()
    return {
        'filename': filename,
        'content': content,
        'mimetype': 'application/pdf',
        'size': log.file_size or len(content),
        'source': 'quote_document',
        'documentLogId': log.id,
    }


def _auto_quote_pdf_attachments(request, schedule):
    if not schedule or schedule.activity_type != 'quote':
        return []

    logs = list(_quote_document_logs_for_schedule(schedule))
    if not logs:
        from .views import generate_document_pdf

        generated_fallbacks = []
        for quote_group in _quote_group_keys_for_schedule(schedule):
            response = generate_document_pdf(request, 'quotation', schedule.id, 'pdf', quote_group=quote_group)
            content_type = (response.get('Content-Type', '') if hasattr(response, 'get') else '').split(';')[0].strip()
            if content_type == 'application/json':
                raise Exception(_json_error_from_document_response(response))
            if getattr(response, 'status_code', 500) >= 400:
                raise Exception(_json_error_from_document_response(response))
            if content_type != 'application/pdf':
                raise Exception('견적서 PDF를 생성하지 못했습니다. PDF 변환 설정을 확인해주세요.')
            generated_fallbacks.append({
                'filename': _decode_response_filename(response),
                'content': bytes(response.content),
                'mimetype': 'application/pdf',
                'size': len(response.content),
                'source': 'quote_document',
                'documentLogId': None,
            })

        logs = list(_quote_document_logs_for_schedule(schedule))
        if not logs:
            return generated_fallbacks

    return [_attachment_from_document_log(log) for log in logs]


def _attachment_info(attachment):
    info = {
        'filename': attachment['filename'],
        'size': attachment['size'],
        'mimetype': attachment['mimetype'],
    }
    if attachment.get('source') == 'quote_document':
        info['source'] = 'quote_document'
        info['label'] = '자동 첨부 견적서'
        if attachment.get('documentLogId'):
            info['documentLogId'] = attachment['documentLogId']
    return info


def _email_address_list(value):
    from email.utils import getaddresses

    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = [str(item or '') for item in value]
    else:
        raw_values = [str(value or '')]

    addresses = []
    seen = set()
    for _name, address in getaddresses(raw_values):
        normalized = (address or '').strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        addresses.append(normalized)
    return addresses


def _email_address_text(addresses):
    cleaned = []
    seen = set()
    for address in addresses or []:
        normalized = str(address or '').strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)
    return ', '.join(cleaned)


def _internal_cc_requested(request):
    value = request.POST.get('include_internal_cc') or request.POST.get('includeInternalCc') or ''
    return str(value).lower() in {'1', 'true', 'yes', 'y', 'on'}


def _internal_cc_emails_for_user(user, exclude_emails=None):
    from django.contrib.auth import get_user_model

    try:
        company_id = user.userprofile.company_id
    except UserProfile.DoesNotExist:
        company_id = None
    if not company_id:
        return []

    excluded = {email.lower() for email in _email_address_list(exclude_emails or [])}
    excluded.update(_email_address_list([user.email]))
    excluded = {email.lower() for email in excluded if email}

    User = get_user_model()
    emails = []
    seen = set()
    users = User.objects.filter(
        is_active=True,
        userprofile__company_id=company_id,
    ).exclude(id=user.id).select_related('userprofile').order_by('username')
    for teammate in users:
        profile = getattr(teammate, 'userprofile', None)
        candidates = [
            teammate.email,
            getattr(profile, 'gmail_email', ''),
            getattr(profile, 'imap_email', ''),
        ]
        added_for_user = False
        for candidate in candidates:
            for address in _email_address_list(candidate):
                key = address.lower()
                if key in excluded or key in seen:
                    continue
                seen.add(key)
                emails.append(address)
                added_for_user = True
                break
            if added_for_user:
                break
    return emails


def _strip_html_style_blocks(value):
    import re

    text = str(value or '')
    text = re.sub(r'(?is)<\s*style\b[^>]*>.*?<\s*/\s*style\s*>', ' ', text)
    text = re.sub(r'(?is)<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', ' ', text)
    return text


def _strip_css_text_artifacts(value):
    import re

    text = str(value or '')
    selector_pattern = r'(?:p|div|span|body|td|table|tr|a|li|ul|ol)'
    css_prop_pattern = r'(?:margin|padding|font|color|line-height|mso-|text-|background|border|white-space)'
    text = re.sub(
        rf'(?im)^\s*{selector_pattern}\s*\{{[^{{}}\n]*{css_prop_pattern}[^{{}}\n]*\}}\s*$',
        '',
        text,
    )
    text = re.sub(
        rf'(?i)\b{selector_pattern}\s*\{{[^{{}}]*(?:margin|padding|font|mso-)[^{{}}]*\}}\s*',
        '',
        text,
    )
    return text


def _sanitize_received_attachments(attachments, message_id=''):
    rows = []
    for attachment in attachments or []:
        if not isinstance(attachment, dict):
            continue
        filename = str(attachment.get('filename') or '').strip()
        if not filename:
            continue
        try:
            size = int(attachment.get('size') or 0)
        except (TypeError, ValueError):
            size = 0
        row = {
            'filename': filename,
            'size': size,
            'mimetype': attachment.get('mimetype') or attachment.get('mimeType') or 'application/octet-stream',
            'source': attachment.get('source') or ('gmail' if attachment.get('gmailAttachmentId') else ''),
        }
        if attachment.get('gmailAttachmentId'):
            row['gmailAttachmentId'] = attachment['gmailAttachmentId']
            row['gmailMessageId'] = attachment.get('gmailMessageId') or message_id
        if attachment.get('contentBase64'):
            row['contentBase64'] = attachment['contentBase64']
        if attachment.get('documentLogId'):
            row['documentLogId'] = attachment['documentLogId']
        rows.append(row)
    return rows


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
            existing_email = EmailLog.objects.filter(gmail_message_id=msg['id']).first()
            if existing_email:
                if not existing_email.attachments_info:
                    msg_detail = gmail_service.get_message_detail(msg['id'])
                    attachments_info = _sanitize_received_attachments(
                        (msg_detail or {}).get('attachments') or [],
                        (msg_detail or {}).get('id') or msg['id'],
                    )
                    if attachments_info:
                        existing_email.attachments_info = attachments_info
                        existing_email.save(update_fields=['attachments_info', 'updated_at'])
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
                attachments_info=_sanitize_received_attachments(
                    msg_detail.get('attachments') or [],
                    msg_detail.get('id') or msg['id'],
                ),
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
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return redirect('reporting:profile')
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'schedule': schedule,
        'followup': schedule.followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
        'quote_document_count': _quote_document_logs_for_schedule(schedule).count() if schedule.activity_type == 'quote' else 0,
    }
    
    if request.method == 'POST':
        result = _handle_email_send(request, schedule=schedule, auto_attach_quote_documents=True)
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
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return redirect('reporting:profile')
    
    # 컨텍스트 준비 (GET과 POST 모두 사용)
    context = {
        'followup': followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    
    if request.method == 'POST':
        logger.info(f"POST request received, calling _handle_email_send")
        
        # 팔로우업 검색으로 선택한 경우 처리
        if not followup:
            selected_followup_id = request.POST.get('selected_followup_id')
            if selected_followup_id:
                try:
                    # 같은 회사 내 팔로우업이면 허용
                    followup = FollowUp.objects.get(
                        id=selected_followup_id,
                        user__userprofile__company=request.user.userprofile.company
                    )
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
    
    # Gmail 또는 IMAP 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.error(request, '이메일 계정을 먼저 연결해주세요.')
        return redirect('reporting:profile')
    
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


def _handle_email_send(request, schedule=None, followup=None, reply_to=None, auto_attach_quote_documents=False):
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
        body_text = _normalize_email_body_text(request.POST.get('body_text', ''))
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
                full_body_html = _plain_email_body_to_html(body_text) + separator + signature_html
            else:
                full_body_html = signature_html
        
        if reply_to:
            if not followup:
                followup = reply_to.followup
            if not schedule:
                schedule = reply_to.schedule

        cc_list = _email_address_list(cc_emails)
        bcc_list = _email_address_list(bcc_emails)
        if _internal_cc_requested(request):
            exclude_emails = [to_email, *cc_list, *bcc_list]
            cc_list = [*cc_list, *_internal_cc_emails_for_user(request.user, exclude_emails=exclude_emails)]
        cc_emails = _email_address_text(cc_list)
        bcc_emails = _email_address_text(bcc_list)

        attachment_entries = _uploaded_email_attachments(request)
        if auto_attach_quote_documents and schedule and schedule.activity_type == 'quote':
            attachment_entries.extend(_auto_quote_pdf_attachments(request, schedule))
        attachments_info = [_attachment_info(attachment) for attachment in attachment_entries]

        # Gmail 또는 IMAP/SMTP로 이메일 발송
        profile = request.user.userprofile
        
        if profile.gmail_token:
            # Gmail OAuth 사용
            gmail_service = GmailService(profile)
            
            # 첨부파일 처리
            attachments = [
                {
                    'filename': attachment['filename'],
                    'content': attachment['content'],
                    'mimetype': attachment['mimetype'],
                }
                for attachment in attachment_entries
            ]
            
            # 답장 정보
            in_reply_to = None
            thread_id = None
            if reply_to:
                in_reply_to = reply_to.gmail_message_id
                thread_id = reply_to.gmail_thread_id
            
            # 이메일 발송
            message_info = gmail_service.send_email(
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                body_html=full_body_html,
                cc=cc_list,
                bcc=bcc_list,
                attachments=attachments,
                in_reply_to=in_reply_to,
                thread_id=thread_id
            )
            
            if not message_info:
                raise Exception("이메일 발송에 실패했습니다.")
            
            message_id = message_info['message_id']
            thread_id_result = message_info['thread_id']
            
        elif profile.imap_connected_at:
            # IMAP/SMTP 사용
            from .imap_utils import SMTPEmailService
            import uuid
            
            smtp_service = SMTPEmailService(profile)
            
            # 첨부파일 처리 (SMTP는 다른 형식)
            attachments = [
                {
                    'filename': attachment['filename'],
                    'content': attachment['content'],
                    'content_type': attachment['mimetype'],
                }
                for attachment in attachment_entries
            ]
            
            # SMTP로 이메일 발송
            success = smtp_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body_text,
                html_body=full_body_html,
                cc_emails=cc_list,
                bcc_emails=bcc_list,
                attachments=attachments
            )
            
            if not success:
                raise Exception("이메일 발송에 실패했습니다.")
            
            # IMAP의 경우 message_id와 thread_id를 생성
            message_id = f"<{uuid.uuid4()}@{profile.imap_email.split('@')[1]}>"
            thread_id_result = message_id  # IMAP는 thread 개념이 없으므로 message_id 사용
            
        else:
            raise Exception("이메일 계정이 연결되지 않았습니다.")
        
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
                sender_email=profile.gmail_email or profile.imap_email,
                recipient_email=to_email,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body=body_html if body_html else body_text,
                body_html=full_body_html,
                gmail_message_id=message_id,
                gmail_thread_id=thread_id_result,
                followup=followup,
                schedule=schedule,
                business_card=business_card,
                in_reply_to=reply_to,
                status='sent',
                sent_at=timezone.now(),
                attachments_info=attachments_info,  # 첨부파일 정보 저장
                user=request.user,  # IMAP용
                provider=profile.email_provider or 'gmail'  # IMAP용
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
        
        # 토큰 만료 에러 체크
        error_message = str(e)
        if 'invalid_grant' in error_message or 'Token has been expired or revoked' in error_message:
            messages.error(request, '⚠️ Gmail 인증이 만료되었습니다. 우측 상단 "Gmail 연동" 버튼을 눌러 재인증해주세요.')
        elif 'SMTP' in error_message and ('Authentication' in error_message or '535' in error_message):
            messages.error(request, '⚠️ IMAP/SMTP 인증 실패. 앱 비밀번호를 확인하거나 "IMAP 연결" 버튼으로 재설정해주세요.')
        else:
            messages.error(request, f'이메일 발송 실패: {error_message}')
        
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

def _mailbox_email_q(user):
    from django.db.models import Q

    return Q(sender=user) | Q(user=user) | Q(followup__user=user) | Q(schedule__user=user)


def _email_thread_identifier(email):
    return email.gmail_thread_id or email.thread_id or email.gmail_message_id or email.message_id or str(email.id)


def _email_contact_for_box(email, mailbox_type):
    if mailbox_type == 'sent':
        return email.recipient_name or email.to_name or email.recipient_email or email.to_email
    return email.from_name or email.sender_email or email.from_email or email.sender_email


def _email_datetime(email):
    return email.received_at or email.sent_at or email.created_at


def _email_text_preview(email, limit=160):
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = _strip_html_style_blocks(email.body_html or email.body or '')
    text = strip_tags(raw).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = ' '.join(text.split())
    return Truncator(text).chars(limit)


def _email_body_text(email, limit=12000):
    import html
    import re
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = email.body_html or email.body or ''
    if email.body_html:
        raw = _strip_html_style_blocks(raw)
        raw = _strip_quoted_html_for_display(raw)
        text = re.sub(r'(?i)<\s*br\s*/?\s*>', '\n', raw)
        text = re.sub(r'(?i)<\s*/\s*(p|div|li|tr|h[1-6]|blockquote|section|article|table)\s*>', '\n', text)
        text = re.sub(r'(?i)<\s*li(?:\s[^>]*)?>', '- ', text)
        text = strip_tags(text)
    else:
        text = raw

    text = html.unescape(text).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [' '.join(line.split()) for line in text.split('\n')]
    normalized = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append('')
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False

    return Truncator(_strip_quoted_text_for_display('\n'.join(normalized).strip())).chars(limit)


def _strip_quoted_html_for_display(raw_html):
    """React 메일 상세 표시에서는 Gmail/Outlook 인용 체인을 숨긴다."""
    import re

    quote_patterns = [
        r'(?is)<div[^>]+class=["\'][^"\']*gmail_quote[^"\']*["\'][^>]*>.*$',
        r'(?is)<div[^>]+id=["\']mail-editor-reference-message-container["\'][^>]*>.*$',
        r'(?is)<div[^>]+class=["\'][^"\']*ms-outlook-mobile-reference-message[^"\']*["\'][^>]*>.*$',
        r'(?is)<blockquote\b[^>]*>.*$',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, raw_html)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return raw_html
    return raw_html[:min(cut_positions)]


def _strip_quoted_text_for_display(text):
    import re

    quote_patterns = [
        r'\n\s*\d{4}년\s+\d{1,2}월\s+\d{1,2}일.{0,500}?(님이 작성:|wrote:)',
        r'\n\s*On .{1,500}? wrote:',
        r'\n\s*-{2,}\s*Original Message\s*-{2,}',
        r'\n\s*-----Original Message-----',
        r'\n\s*보낸 사람\s*:',
        r'\n\s*From\s*:',
        r'\n\s*Sent\s*:',
        r'\n\s*받는 사람\s*:',
        r'\n\s*To\s*:',
        r'\n\s*Get Outlook for',
        r'\n\s*받기 Mac용 Outlook',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return text
    return text[:min(cut_positions)].rstrip()


def _ensure_gmail_attachment_metadata(email, user):
    if email.attachments_info:
        return
    if not email.gmail_message_id:
        return
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return
    if not profile.gmail_token:
        return

    try:
        msg_detail = GmailService(profile).get_message_detail(email.gmail_message_id)
    except Exception:
        return
    attachments_info = _sanitize_received_attachments(
        (msg_detail or {}).get('attachments') or [],
        (msg_detail or {}).get('id') or email.gmail_message_id,
    )
    if attachments_info:
        email.attachments_info = attachments_info
        email.save(update_fields=['attachments_info', 'updated_at'])


def _email_attachment_payloads(email):
    rows = []
    for index, attachment in enumerate(email.attachments_info or []):
        if not isinstance(attachment, dict):
            continue
        filename = str(attachment.get('filename') or '').strip()
        if not filename:
            continue
        try:
            size = int(attachment.get('size') or 0)
        except (TypeError, ValueError):
            size = 0
        can_download = any([
            attachment.get('gmailAttachmentId'),
            attachment.get('contentBase64'),
            attachment.get('documentLogId'),
        ])
        rows.append({
            'filename': filename,
            'size': size,
            'mimetype': attachment.get('mimetype') or 'application/octet-stream',
            'source': attachment.get('source') or '',
            'downloadHref': reverse('reporting:mailbox_api_attachment_download', args=[email.id, index]) if can_download else '',
        })
    return rows


def _serialize_email_item(email, mailbox_type='inbox'):
    thread_id = _email_thread_identifier(email)
    followup = email.followup
    schedule = email.schedule
    happened_at = _email_datetime(email)
    return {
        'id': email.id,
        'type': email.email_type,
        'typeLabel': '보낸 메일' if email.email_type == 'sent' else '받은 메일',
        'subject': email.subject,
        'contact': _email_contact_for_box(email, mailbox_type),
        'senderEmail': email.sender_email or email.from_email,
        'recipientEmail': email.recipient_email or email.to_email,
        'ccEmails': email.cc_emails,
        'preview': _email_text_preview(email),
        'bodyText': _email_body_text(email),
        'sentAt': email.sent_at.isoformat() if email.sent_at else None,
        'receivedAt': email.received_at.isoformat() if email.received_at else None,
        'happenedAt': happened_at.isoformat() if happened_at else None,
        'isRead': email.is_read,
        'isStarred': email.is_starred,
        'isArchived': email.is_archived,
        'isTrashed': email.is_trashed,
        'threadId': thread_id,
        'threadHref': f'/mailbox/thread/{thread_id}/',
        'djangoThreadHref': reverse('reporting:mailbox_thread', args=[thread_id]),
        'replyHref': reverse('reporting:mailbox_api_reply', args=[email.id]),
        'toggleStarHref': reverse('reporting:mailbox_api_toggle_star', args=[email.id]),
        'archiveHref': reverse('reporting:mailbox_api_archive', args=[email.id]),
        'trashHref': reverse('reporting:mailbox_api_move_to_trash', args=[email.id]),
        'restoreHref': reverse('reporting:mailbox_api_restore', args=[email.id]),
        'deleteHref': reverse('reporting:mailbox_api_delete', args=[email.id]),
        'followup': {
            'id': followup.id if followup else None,
            'customer': followup.customer_name if followup else '',
            'company': followup.company.name if followup and followup.company else '',
            'department': followup.department.name if followup and followup.department else '',
            'href': f'/customers/{followup.id}/' if followup else '',
            'djangoHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
        },
        'schedule': {
            'id': schedule.id if schedule else None,
            'href': f'/schedules/{schedule.id}/' if schedule else '',
            'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        },
        'attachments': _email_attachment_payloads(email),
    }


def _mailbox_connection_payload(profile):
    provider = profile.email_provider or ('gmail' if profile.gmail_token else 'imap')
    address = profile.gmail_email or profile.imap_email or ''
    connected = bool(profile.gmail_token or profile.imap_connected_at)
    return {
        'connected': connected,
        'provider': provider,
        'address': address,
        'gmailConnected': bool(profile.gmail_token),
        'imapConnected': bool(profile.imap_connected_at),
        'lastSyncAt': (
            profile.gmail_last_sync_at.isoformat() if profile.gmail_last_sync_at
            else profile.imap_last_sync_at.isoformat() if profile.imap_last_sync_at
            else None
        ),
        'connectHref': reverse('reporting:gmail_connect'),
        'imapConnectHref': reverse('reporting:imap_connect'),
        'profileHref': reverse('reporting:profile'),
    }


def _mailbox_counts(user):
    base = EmailLog.objects.filter(_mailbox_email_q(user))
    return {
        'inbox': base.filter(email_type='received', is_trashed=False, is_archived=False).count(),
        'sent': base.filter(email_type='sent', is_trashed=False).count(),
        'starred': base.filter(is_starred=True, is_trashed=False).count(),
        'archived': base.filter(is_archived=True, is_trashed=False).count(),
        'trash': base.filter(is_trashed=True).count(),
        'unread': base.filter(email_type='received', is_read=False, is_trashed=False).count(),
    }


def _mailbox_queryset(user, mailbox_type):
    from django.db.models.functions import Coalesce

    base = EmailLog.objects.filter(_mailbox_email_q(user)).select_related(
        'sender', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card'
    )
    if mailbox_type == 'sent':
        return base.filter(email_type='sent', is_trashed=False).order_by('-sent_at', '-created_at')
    if mailbox_type == 'starred':
        return base.filter(is_starred=True, is_trashed=False).order_by(Coalesce('received_at', 'sent_at', 'created_at').desc())
    if mailbox_type == 'archived':
        return base.filter(is_archived=True, is_trashed=False).order_by(Coalesce('received_at', 'sent_at', 'created_at').desc())
    if mailbox_type == 'trash':
        return base.filter(is_trashed=True).order_by('-trashed_at', '-created_at')
    return base.filter(email_type='received', is_trashed=False, is_archived=False).order_by(
        Coalesce('received_at', 'created_at').desc()
    )


def _mailbox_create_payload(user):
    followups = FollowUp.objects.filter(user=user).select_related('company', 'department').order_by('company__name', 'customer_name')
    business_cards = BusinessCard.objects.filter(user=user, is_active=True).order_by('-is_default', '-created_at')
    return {
        'canSend': True,
        'message': '',
        'submitUrl': reverse('reporting:mailbox_api_send'),
        'djangoUrl': reverse('reporting:send_email_from_mailbox'),
        'internalCcEmails': _internal_cc_emails_for_user(user),
        'customers': [
            {
                'id': followup.id,
                'customer': followup.customer_name or '',
                'company': followup.company.name if followup.company else '',
                'department': followup.department.name if followup.department else '',
                'email': followup.email or '',
            }
            for followup in followups
        ],
        'businessCards': [
            {
                'id': card.id,
                'name': card.name,
                'fullName': card.full_name,
                'email': card.email,
                'isDefault': card.is_default,
            }
            for card in business_cards
        ],
    }


def _followup_allowed_for_mail(user, followup):
    profile = user.userprofile
    if profile.is_admin():
        return True
    if followup.user_id == user.id:
        return True
    if profile.company and followup.user_id:
        try:
            return followup.user.userprofile.company_id == profile.company_id
        except UserProfile.DoesNotExist:
            return False
    return False


def _json_method_error():
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'}, status=405)


@login_required
def mailbox_api_list(request):
    """React 메일함 목록 API"""
    from django.db.models import Q

    mailbox_type = request.GET.get('box') or 'inbox'
    if mailbox_type not in {'inbox', 'sent', 'starred', 'archived', 'trash'}:
        mailbox_type = 'inbox'

    query = (request.GET.get('q') or '').strip()
    emails = _mailbox_queryset(request.user, mailbox_type)
    if query:
        emails = emails.filter(
            Q(subject__icontains=query) |
            Q(body__icontains=query) |
            Q(body_html__icontains=query) |
            Q(sender_email__icontains=query) |
            Q(recipient_email__icontains=query) |
            Q(followup__customer_name__icontains=query) |
            Q(followup__company__name__icontains=query) |
            Q(followup__department__name__icontains=query)
        )

    paginator = Paginator(emails, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    profile = request.user.userprofile

    return JsonResponse({
        'success': True,
        'source': 'django',
        'mailboxType': mailbox_type,
        'filters': {
            'q': query,
            'page': page_obj.number,
        },
        'connection': _mailbox_connection_payload(profile),
        'counts': _mailbox_counts(request.user),
        'pagination': {
            'page': page_obj.number,
            'totalPages': paginator.num_pages,
            'totalCount': paginator.count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
            'nextPage': page_obj.next_page_number() if page_obj.has_next() else None,
            'previousPage': page_obj.previous_page_number() if page_obj.has_previous() else None,
        },
        'links': {
            'inbox': '/mailbox/?box=inbox',
            'sent': '/mailbox/?box=sent',
            'starred': '/mailbox/?box=starred',
            'archived': '/mailbox/?box=archived',
            'trash': '/mailbox/?box=trash',
            'sync': reverse('reporting:mailbox_api_sync'),
            'djangoInbox': reverse('reporting:mailbox_inbox'),
            'djangoSent': reverse('reporting:mailbox_sent'),
        },
        'create': _mailbox_create_payload(request.user),
        'emails': [_serialize_email_item(email, mailbox_type) for email in page_obj],
    })


@login_required
def mailbox_api_thread(request, thread_id):
    """React 메일 스레드 상세 API"""
    from django.db.models import Q

    emails = EmailLog.objects.filter(
        _mailbox_email_q(request.user),
        Q(gmail_thread_id=thread_id) | Q(thread_id=thread_id) | Q(message_id=thread_id) | Q(gmail_message_id=thread_id)
    ).select_related('sender', 'followup', 'followup__company', 'followup__department', 'schedule', 'business_card').order_by(
        'sent_at', 'received_at', 'created_at'
    )

    if not emails.exists():
        return JsonResponse({'success': False, 'error': '메일 스레드를 찾을 수 없습니다.'}, status=404)

    unread = emails.filter(email_type='received', is_read=False)
    if unread.exists():
        unread.update(is_read=True)

    first_email = emails.first()
    last_received_email = emails.filter(email_type='received').order_by('-sent_at', '-received_at', '-created_at').first()
    profile = request.user.userprofile
    email_rows = list(emails)
    for email in email_rows:
        _ensure_gmail_attachment_metadata(email, request.user)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'thread': {
            'id': thread_id,
            'subject': first_email.subject if first_email else '',
            'followup': _serialize_email_item(first_email)['followup'] if first_email else None,
            'messageCount': emails.count(),
            'lastReceivedEmailId': last_received_email.id if last_received_email else None,
        },
        'connection': _mailbox_connection_payload(profile),
        'links': {
            'mailbox': '/mailbox/',
            'djangoThread': reverse('reporting:mailbox_thread', args=[thread_id]),
            'reply': reverse('reporting:mailbox_api_reply', args=[last_received_email.id]) if last_received_email else '',
        },
        'create': _mailbox_create_payload(request.user),
        'emails': [_serialize_email_item(email) for email in email_rows],
    })


@login_required
def mailbox_api_send(request):
    """React 메일 작성 API"""
    if request.method != 'POST':
        return _json_method_error()

    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 먼저 연결해주세요.'}, status=400)

    followup = None
    schedule = None
    schedule_id = request.POST.get('schedule_id') or request.POST.get('scheduleId')
    if schedule_id:
        try:
            schedule = Schedule.objects.select_related('user', 'followup', 'followup__user').get(id=schedule_id)
        except (Schedule.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': '선택한 일정을 찾을 수 없습니다.'}, status=404)

        from .views import can_access_user_data
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'success': False, 'error': '일정 메일 발송 권한이 없습니다.'}, status=403)
        followup = schedule.followup

    selected_followup_id = request.POST.get('selected_followup_id') or request.POST.get('followup_id')
    if selected_followup_id and not followup:
        try:
            followup = FollowUp.objects.select_related('user', 'user__userprofile').get(id=selected_followup_id)
        except (FollowUp.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'error': '선택한 고객을 찾을 수 없습니다.'}, status=404)
        if not _followup_allowed_for_mail(request.user, followup):
            return JsonResponse({'success': False, 'error': '고객 메일 발송 권한이 없습니다.'}, status=403)
    elif selected_followup_id and followup and str(followup.id) != str(selected_followup_id):
        return JsonResponse({'success': False, 'error': '일정과 고객 정보가 일치하지 않습니다.'}, status=400)

    result = _handle_email_send(
        request,
        schedule=schedule,
        followup=followup,
        auto_attach_quote_documents=bool(schedule),
    )
    if isinstance(result, dict):
        return JsonResponse({
            'success': False,
            'error': result.get('exception') or '메일 발송 입력값을 확인해주세요.',
            'form': result.get('form_data', {}),
        }, status=400)

    location = result.get('Location', '/mailbox/?box=sent') if hasattr(result, 'get') else '/mailbox/?box=sent'
    return JsonResponse({
        'success': True,
        'message': '이메일이 발송되었습니다.',
        'href': location.replace('/reporting/mailbox/thread/', '/mailbox/thread/') if location else '/mailbox/?box=sent',
        'djangoHref': location,
    })


@login_required
def mailbox_api_reply(request, email_id):
    """React 메일 답장 API"""
    if request.method != 'POST':
        return _json_method_error()

    email = EmailLog.objects.filter(_mailbox_email_q(request.user), id=email_id).select_related('followup', 'schedule').first()
    if not email:
        return JsonResponse({'success': False, 'error': '답장할 메일을 찾을 수 없습니다.'}, status=404)

    profile = request.user.userprofile
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 먼저 연결해주세요.'}, status=400)

    result = _handle_email_send(request, reply_to=email)
    if isinstance(result, dict):
        return JsonResponse({
            'success': False,
            'error': result.get('exception') or '메일 답장 입력값을 확인해주세요.',
            'form': result.get('form_data', {}),
        }, status=400)

    thread_id = _email_thread_identifier(email)
    return JsonResponse({
        'success': True,
        'message': '답장을 발송했습니다.',
        'href': f'/mailbox/thread/{thread_id}/',
        'djangoHref': reverse('reporting:mailbox_thread', args=[thread_id]),
    })


@login_required
def mailbox_api_sync(request):
    """React 메일 동기화 API"""
    if request.method != 'POST':
        return _json_method_error()
    return sync_received_emails(request)


@login_required
def mailbox_api_toggle_star(request, email_id):
    return toggle_star_email(request, email_id)


@login_required
def mailbox_api_archive(request, email_id):
    return archive_email(request, email_id)


@login_required
def mailbox_api_move_to_trash(request, email_id):
    return move_to_trash_email(request, email_id)


@login_required
def mailbox_api_restore(request, email_id):
    return restore_email(request, email_id)


@login_required
def mailbox_api_delete(request, email_id):
    return delete_email(request, email_id)


@login_required
def mailbox_api_attachment_download(request, email_id, attachment_index):
    import base64
    from urllib.parse import quote

    email = EmailLog.objects.filter(
        _mailbox_email_q(request.user),
        id=email_id,
    ).select_related('user').first()
    if not email:
        return JsonResponse({'success': False, 'error': '메일을 찾을 수 없습니다.'}, status=404)

    attachments = email.attachments_info or []
    try:
        attachment = attachments[int(attachment_index)]
    except (IndexError, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': '첨부파일을 찾을 수 없습니다.'}, status=404)
    if not isinstance(attachment, dict):
        return JsonResponse({'success': False, 'error': '첨부파일 정보를 읽을 수 없습니다.'}, status=404)

    filename = str(attachment.get('filename') or 'attachment').strip() or 'attachment'
    mimetype = attachment.get('mimetype') or 'application/octet-stream'
    content = None

    if attachment.get('contentBase64'):
        try:
            content = base64.b64decode(attachment['contentBase64'])
        except Exception:
            content = None

    if content is None and attachment.get('documentLogId'):
        log = DocumentGenerationLog.objects.filter(id=attachment.get('documentLogId')).first()
        if log and log.file:
            with log.file.open('rb') as file_handle:
                content = file_handle.read()
            filename = log.filename or filename

    if content is None and attachment.get('gmailAttachmentId'):
        profile = request.user.userprofile
        if not profile.gmail_token:
            return JsonResponse({'success': False, 'error': 'Gmail 연결이 필요합니다.'}, status=400)
        message_id = attachment.get('gmailMessageId') or email.gmail_message_id
        content = GmailService(profile).get_attachment(message_id, attachment.get('gmailAttachmentId'))

    if content is None:
        return JsonResponse({'success': False, 'error': '첨부파일을 다운로드할 수 없습니다.'}, status=404)

    response = HttpResponse(content, content_type=mimetype)
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return response


@login_required
def mailbox_inbox(request):
    """받은편지함 (본인 담당 팔로우업 연결 메일만)"""
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return redirect('reporting:profile')
    
    # DB에서 수신 메일 조회 (본인 담당 팔로우업만, 휴지통 제외)
    # 최신순 정렬: received_at이 null이면 created_at 사용
    from django.db.models.functions import Coalesce
    emails = EmailLog.objects.filter(
        email_type='received',
        followup__isnull=False,  # 팔로우업 연결된 메일만
        followup__user=request.user,  # 본인 담당 팔로우업만
        is_trashed=False,  # 휴지통 제외
        is_archived=False  # 보관함 제외
    ).select_related('followup', 'sender', 'business_card').order_by(
        Coalesce('received_at', 'created_at').desc()
    )
    
    # 페이지네이션 (20개씩)
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 중요편지 개수
    starred_count = EmailLog.objects.filter(
        followup__user=request.user,
        is_starred=True,
        is_trashed=False
    ).count()
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'inbox',
        'total_count': paginator.count,
        'starred_count': starred_count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_sent(request):
    """보낸편지함"""
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return redirect('reporting:profile')
    
    emails = EmailLog.objects.filter(
        email_type='sent',
        sender=request.user,
        is_trashed=False
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
def mailbox_starred(request):
    """중요편지함"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return redirect('reporting:profile')
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_starred=True,
        is_trashed=False
    ).select_related('followup', 'schedule', 'business_card').order_by(
        Coalesce('received_at', 'sent_at').desc()
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'starred',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_archived(request):
    """보관함"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_archived=True,
        is_trashed=False
    ).select_related('followup', 'schedule', 'business_card').order_by(
        Coalesce('received_at', 'sent_at').desc()
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'archived',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_trash(request):
    """휴지통"""
    from django.db.models import Q
    from django.db.models.functions import Coalesce
    
    emails = EmailLog.objects.filter(
        Q(sender=request.user) | Q(followup__user=request.user),
        is_trashed=True
    ).select_related('followup', 'schedule', 'business_card').order_by(
        '-trashed_at'
    )
    
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'trash',
        'total_count': paginator.count
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def toggle_star_email(request, email_id):
    """이메일 중요 표시 토글"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_starred = not email.is_starred
        email.save(update_fields=['is_starred'])
        
        return JsonResponse({
            'success': True,
            'is_starred': email.is_starred,
            'message': '중요 표시됨' if email.is_starred else '중요 표시 해제됨'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def archive_email(request, email_id):
    """이메일 보관"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_archived = not email.is_archived
        email.save(update_fields=['is_archived'])
        
        return JsonResponse({
            'success': True,
            'is_archived': email.is_archived,
            'message': '보관함으로 이동됨' if email.is_archived else '보관 해제됨'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def move_to_trash_email(request, email_id):
    """이메일 휴지통으로 이동"""
    from django.db.models import Q
    from django.utils import timezone
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_trashed = True
        email.trashed_at = timezone.now()
        email.save(update_fields=['is_trashed', 'trashed_at'])
        
        return JsonResponse({
            'success': True,
            'message': '휴지통으로 이동되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def restore_email(request, email_id):
    """이메일 복원 (휴지통에서)"""
    from django.db.models import Q
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        email = EmailLog.objects.filter(
            Q(sender=request.user) | Q(followup__user=request.user),
            id=email_id,
            is_trashed=True
        ).first()
        
        if not email:
            return JsonResponse({'success': False, 'error': '이메일을 찾을 수 없습니다.'})
        
        email.is_trashed = False
        email.trashed_at = None
        email.save(update_fields=['is_trashed', 'trashed_at'])
        
        return JsonResponse({
            'success': True,
            'message': '이메일이 복원되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mailbox_thread(request, thread_id):
    """이메일 스레드 상세 (대화 전체)"""
    import logging
    logger = logging.getLogger(__name__)
    
    profile = request.user.userprofile
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        messages.warning(request, '이메일 계정을 연결해주세요.')
        return redirect('reporting:profile')
    
    # Gmail에서 최신 스레드 데이터 가져와서 DB 동기화
    if profile.gmail_token:
        try:
            gmail_service = GmailService(profile)
            thread_data = gmail_service.get_thread(thread_id)
            
            if thread_data and thread_data.get('messages'):
                logger.info(f"스레드 {thread_id}: Gmail에서 {len(thread_data['messages'])}개 메시지 조회")
                
                # DB에 저장된 메시지 ID 목록
                existing_message_ids = set(
                    EmailLog.objects.filter(gmail_thread_id=thread_id)
                    .values_list('gmail_message_id', flat=True)
                )
                
                # 새로운 메시지만 DB에 저장
                new_count = 0
                for msg_detail in thread_data['messages']:
                    msg_id = msg_detail['id']
                    
                    if msg_id not in existing_message_ids:
                        # 새 메시지 저장
                        try:
                            from .imap_utils import save_email_to_db
                            
                            # 이메일 타입 결정 (From 주소로 판단)
                            from_email = msg_detail.get('from', '').lower()
                            user_email = request.user.email.lower() if request.user.email else ''
                            email_type = 'sent' if user_email in from_email else 'received'
                            
                            save_email_to_db(
                                user=request.user,
                                message_id=msg_id,
                                thread_id=thread_id,
                                sender_email=msg_detail.get('from', ''),
                                recipient_email=msg_detail.get('to', ''),
                                cc_emails=msg_detail.get('cc', ''),
                                bcc_emails=msg_detail.get('bcc', ''),
                                subject=msg_detail.get('subject', ''),
                                body=msg_detail.get('body_text') or msg_detail.get('body') or msg_detail.get('snippet', ''),
                                body_html=msg_detail.get('body_html', ''),
                                sent_at=msg_detail.get('date'),
                                email_type=email_type,
                                labels=msg_detail.get('labels', []),
                                attachments_info=_sanitize_received_attachments(
                                    msg_detail.get('attachments') or [],
                                    msg_id,
                                ),
                            )
                            new_count += 1
                            logger.info(f"새 메시지 저장: {msg_id}")
                        except Exception as e:
                            logger.error(f"메시지 저장 실패 ({msg_id}): {e}")
                            continue
                    else:
                        existing_email = EmailLog.objects.filter(gmail_message_id=msg_id).first()
                        if existing_email and not existing_email.attachments_info:
                            attachments_info = _sanitize_received_attachments(
                                msg_detail.get('attachments') or [],
                                msg_id,
                            )
                            if attachments_info:
                                existing_email.attachments_info = attachments_info
                                existing_email.save(update_fields=['attachments_info', 'updated_at'])
                
                if new_count > 0:
                    logger.info(f"스레드 {thread_id}: {new_count}개 새 메시지 동기화 완료")
        except Exception as e:
            logger.error(f"스레드 동기화 오류: {e}")
            # 동기화 실패해도 계속 진행
    
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
    
    # Gmail 또는 IMAP 연결 확인
    if not profile.gmail_token and not profile.imap_connected_at:
        return JsonResponse({'success': False, 'error': '이메일 계정을 연결해주세요.'})
    
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
