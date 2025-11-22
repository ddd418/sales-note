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

from .models import UserProfile, EmailLog, BusinessCard, Schedule, FollowUp
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
    
    # 팔로우업 이메일 주소 목록
    followup_emails = set()
    followups = FollowUp.objects.filter(user=user)
    for followup in followups:
        if followup.email:
            followup_emails.add(followup.email.lower())
    
    if not followup_emails:
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
            
            # 팔로우업 이메일과 매칭
            matched_followup = None
            target_email = to_email if is_sent else from_email
            
            for followup in followups:
                if followup.email and followup.email.lower() == target_email:
                    matched_followup = followup
                    break
            
            if not matched_followup:
                continue
            
            # 본문 내용 처리 (HTML 우선, 없으면 텍스트)
            body_html = msg_detail.get('body_html', '')
            body_text = msg_detail.get('body_text', '')
            
            # body 필드는 HTML이 있으면 HTML, 없으면 텍스트 사용
            body_content = body_html if body_html else body_text
            
            # 둘 다 없으면 snippet 사용
            if not body_content:
                body_content = msg_detail.get('snippet', '')
            
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
                is_read=True if is_sent else False,
                status='sent' if is_sent else 'received'
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
    redirect_uri = request.build_absolute_uri(reverse('reporting:gmail_callback'))
    auth_url, state = get_authorization_url(redirect_uri)
    # state를 세션에 저장 (보안을 위해)
    request.session['gmail_oauth_state'] = state
    return redirect(auth_url)


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
        redirect_uri = request.build_absolute_uri(reverse('reporting:gmail_callback'))
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
        
        # 첫 연동 시 자동으로 30일치 메일 동기화
        try:
            synced = _sync_emails_by_days(request.user, days=30)
            messages.success(request, f'Gmail 계정({gmail_email})이 연결되었습니다. 최근 30일치 메일 {synced}개를 동기화했습니다.')
        except Exception as sync_error:
            messages.success(request, f'Gmail 계정({gmail_email})이 연결되었습니다.')
            messages.warning(request, f'메일 동기화 중 오류: {str(sync_error)}')
        
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
            profile.gmail_email = None
            profile.gmail_connected_at = None
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
        return redirect('reporting:schedule_detail', schedule_id=schedule_id)
    
    # Gmail 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token:
        messages.error(request, 'Gmail 계정을 먼저 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    if request.method == 'POST':
        return _handle_email_send(request, schedule=schedule)
    
    # GET: 이메일 작성 폼
    context = {
        'schedule': schedule,
        'followup': schedule.followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    return render(request, 'reporting/gmail/compose_from_schedule.html', context)


@login_required
def send_email_from_mailbox(request, followup_id=None):
    """메일함에서 이메일 발송 (팔로우업 연결)"""
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
    
    if request.method == 'POST':
        return _handle_email_send(request, followup=followup)
    
    # GET: 이메일 작성 폼
    context = {
        'followup': followup,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
        'all_followups': FollowUp.objects.filter(user=request.user).order_by('-created_at')[:100],
    }
    return render(request, 'reporting/gmail/compose_from_mailbox.html', context)


@login_required
def reply_email(request, email_log_id):
    """이메일 답장"""
    email_log = get_object_or_404(EmailLog, id=email_log_id)
    
    # 권한 확인
    if email_log.sender != request.user and request.user.userprofile.role != 'manager':
        messages.error(request, '권한이 없습니다.')
        return redirect('reporting:mailbox_inbox')
    
    # Gmail 연결 확인
    profile = request.user.userprofile
    if not profile.gmail_token:
        messages.error(request, 'Gmail 계정을 먼저 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    if request.method == 'POST':
        return _handle_email_send(request, reply_to=email_log)
    
    # GET: 답장 폼
    context = {
        'original_email': email_log,
        'business_cards': BusinessCard.objects.filter(user=request.user, is_active=True),
        'default_card': BusinessCard.objects.filter(user=request.user, is_default=True, is_active=True).first(),
    }
    return render(request, 'reporting/gmail/reply_email.html', context)


def _handle_email_send(request, schedule=None, followup=None, reply_to=None):
    """이메일 발송 공통 처리"""
    try:
        # POST 데이터 추출
        to_email = request.POST.get('to_email')
        cc_emails = request.POST.get('cc_emails', '')
        bcc_emails = request.POST.get('bcc_emails', '')
        subject = request.POST.get('subject')
        body_text = request.POST.get('body_text', '')
        body_html = request.POST.get('body_html', '')
        business_card_id = request.POST.get('business_card_id')
        
        # 유효성 검사
        if not to_email or not subject:
            messages.error(request, '받는 사람과 제목은 필수입니다.')
            return redirect(request.path)
        
        # 명함 서명 추가
        signature_html = ''
        business_card = None
        if business_card_id:
            business_card = BusinessCard.objects.get(id=business_card_id, user=request.user)
            signature_html = business_card.generate_signature()
        
        # HTML 본문에 서명 추가
        if body_html:
            full_body_html = body_html + signature_html
        else:
            # 텍스트만 있는 경우 HTML로 변환 후 서명 추가
            full_body_html = f'<pre>{body_text}</pre>' + signature_html
        
        # Gmail 서비스 생성
        gmail_service = GmailService(request.user.userprofile)
        
        # 첨부파일 처리
        attachments = []
        files = request.FILES.getlist('attachments')
        for uploaded_file in files:
            attachments.append({
                'filename': uploaded_file.name,
                'content': uploaded_file.read(),
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
            cc_emails=[email.strip() for email in cc_emails.split(',') if email.strip()],
            bcc_emails=[email.strip() for email in bcc_emails.split(',') if email.strip()],
            attachments=attachments,
            in_reply_to=in_reply_to,
            thread_id=thread_id
        )
        
        # EmailLog 생성
        with transaction.atomic():
            email_log = EmailLog.objects.create(
                email_type='sent',
                sender=request.user,
                sender_email=request.user.userprofile.gmail_email,
                recipient_email=to_email,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                subject=subject,
                body_text=body_text,
                body_html=full_body_html,
                gmail_message_id=message_info['id'],
                gmail_thread_id=message_info['threadId'],
                followup=followup,
                schedule=schedule,
                business_card=business_card,
                in_reply_to=reply_to,
                status='sent'
            )
        
        messages.success(request, '이메일이 발송되었습니다.')
        
        # 리다이렉트 경로 결정
        if schedule:
            return redirect('reporting:schedule_detail', schedule_id=schedule.id)
        elif followup:
            return redirect('reporting:mailbox_thread', thread_id=email_log.gmail_thread_id)
        else:
            return redirect('reporting:mailbox_sent')
        
    except Exception as e:
        messages.error(request, f'이메일 발송 실패: {str(e)}')
        return redirect(request.path)


# ============================================
# 메일함 조회
# ============================================

@login_required
def mailbox_inbox(request):
    """받은편지함 (팔로우업 연결 메일만)"""
    profile = request.user.userprofile
    
    # Gmail 연결 확인
    if not profile.gmail_token:
        messages.warning(request, 'Gmail 계정을 연결해주세요.')
        return redirect('reporting:gmail_connect')
    
    # DB에서 수신 메일 조회
    emails = EmailLog.objects.filter(
        email_type='received',
        followup__isnull=False  # 팔로우업 연결된 메일만
    ).select_related('followup', 'sender', 'business_card').order_by('-sent_at')
    
    # 페이지네이션
    paginator = Paginator(emails, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'inbox'
    }
    return render(request, 'reporting/gmail/mailbox.html', context)


@login_required
def mailbox_sent(request):
    """보낸편지함"""
    emails = EmailLog.objects.filter(
        email_type='sent',
        sender=request.user
    ).select_related('followup', 'schedule', 'business_card').order_by('-sent_at')
    
    # 페이지네이션
    paginator = Paginator(emails, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'emails': page_obj,
        'mailbox_type': 'sent'
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
    
    context = {
        'thread_id': thread_id,
        'emails': emails,
        'followup': emails.first().followup,
    }
    return render(request, 'reporting/gmail/thread_detail.html', context)


@login_required
@login_required
def sync_received_emails(request):
    """
    수동 메일 동기화
    - 마지막 동기화 시점 이후의 메일만 가져옴
    - 첫 동기화인 경우 최근 1일치
    """
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
    if request.method == 'POST':
        try:
            email = get_object_or_404(EmailLog, id=email_id)
            
            # 권한 확인: 받은 메일(팔로우업 관련) 또는 본인이 보낸 메일만 삭제 가능
            if email.email_type == 'sent' and email.sender != request.user:
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다.'})
            
            if email.email_type == 'received' and email.followup and email.followup.user != request.user:
                return JsonResponse({'success': False, 'error': '삭제 권한이 없습니다.'})
            
            email.delete()
            return JsonResponse({'success': True, 'message': '메일이 삭제되었습니다.'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})


# ============================================
# 명함 관리
# ============================================

@login_required
def business_card_list(request):
    """명함 목록"""
    cards = BusinessCard.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
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
                is_default=request.POST.get('is_default') == 'on'
            )
            
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
            card.is_default = request.POST.get('is_default') == 'on'
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
