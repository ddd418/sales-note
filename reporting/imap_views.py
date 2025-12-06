"""
IMAP/SMTP 이메일 연동 뷰
커스텀 도메인 이메일 연동 지원
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import UserProfile, EmailLog, FollowUp, Schedule
from .imap_utils import (
    IMAPEmailService, SMTPEmailService, EmailEncryption,
    test_imap_connection, test_smtp_connection, EMAIL_PRESETS
)
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def imap_connect(request):
    """IMAP/SMTP 연결 설정 페이지"""
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        # 이메일 제공업체 선택
        provider = request.POST.get('provider', 'imap')
        
        # 프리셋 적용
        preset = EMAIL_PRESETS.get(provider, {})
        
        # 폼 데이터 수집
        imap_email = request.POST.get('imap_email', '').strip()
        imap_host = request.POST.get('imap_host', preset.get('imap_host', '')).strip()
        imap_port = int(request.POST.get('imap_port', preset.get('imap_port', 993)))
        imap_username = request.POST.get('imap_username', imap_email).strip()
        imap_password = request.POST.get('imap_password', '').strip()
        imap_use_ssl = request.POST.get('imap_use_ssl', 'on') == 'on'
        
        smtp_host = request.POST.get('smtp_host', preset.get('smtp_host', '')).strip()
        smtp_port = int(request.POST.get('smtp_port', preset.get('smtp_port', 587)))
        smtp_username = request.POST.get('smtp_username', imap_username).strip()
        smtp_password = request.POST.get('smtp_password', imap_password).strip()
        smtp_use_tls = request.POST.get('smtp_use_tls', 'on') == 'on'
        
        # 연결 테스트
        test_type = request.POST.get('test_connection')
        
        if test_type == 'imap':
            # IMAP 테스트
            success, message = test_imap_connection(
                imap_host, imap_port, imap_username, imap_password, imap_use_ssl
            )
            if success:
                messages.success(request, f"✓ IMAP 연결 성공: {message}")
            else:
                messages.error(request, f"✗ IMAP 연결 실패: {message}")
            
            # 테스트만 하고 저장하지 않음
            context = {
                'user_profile': user_profile,
                'form_data': request.POST,
                'presets': EMAIL_PRESETS,
            }
            return render(request, 'reporting/imap_connect.html', context)
        
        elif test_type == 'smtp':
            # SMTP 테스트
            success, message = test_smtp_connection(
                smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_tls
            )
            if success:
                messages.success(request, f"✓ SMTP 연결 성공: {message}")
            else:
                messages.error(request, f"✗ SMTP 연결 실패: {message}")
            
            # 테스트만 하고 저장하지 않음
            context = {
                'user_profile': user_profile,
                'form_data': request.POST,
                'presets': EMAIL_PRESETS,
            }
            return render(request, 'reporting/imap_connect.html', context)
        
        else:
            # 저장
            # 먼저 연결 테스트
            imap_ok, imap_msg = test_imap_connection(
                imap_host, imap_port, imap_username, imap_password, imap_use_ssl
            )
            smtp_ok, smtp_msg = test_smtp_connection(
                smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_tls
            )
            
            if not (imap_ok and smtp_ok):
                if not imap_ok:
                    messages.error(request, f"IMAP 연결 실패: {imap_msg}")
                if not smtp_ok:
                    messages.error(request, f"SMTP 연결 실패: {smtp_msg}")
                
                context = {
                    'user_profile': user_profile,
                    'form_data': request.POST,
                    'presets': EMAIL_PRESETS,
                }
                return render(request, 'reporting/imap_connect.html', context)
            
            # 비밀번호 암호화
            encrypted_imap_password = EmailEncryption.encrypt_password(imap_password)
            encrypted_smtp_password = EmailEncryption.encrypt_password(smtp_password)
            
            # UserProfile 업데이트
            user_profile.email_provider = provider
            user_profile.imap_email = imap_email
            user_profile.imap_host = imap_host
            user_profile.imap_port = imap_port
            user_profile.imap_username = imap_username
            user_profile.imap_password = encrypted_imap_password
            user_profile.imap_use_ssl = imap_use_ssl
            
            user_profile.smtp_host = smtp_host
            user_profile.smtp_port = smtp_port
            user_profile.smtp_username = smtp_username
            user_profile.smtp_password = encrypted_smtp_password
            user_profile.smtp_use_tls = smtp_use_tls
            
            user_profile.imap_connected_at = timezone.now()
            user_profile.save()
            
            messages.success(request, f"✓ 이메일 연동 완료: {imap_email}")
            return redirect('profile')
    
    # GET 요청
    context = {
        'user_profile': user_profile,
        'presets': EMAIL_PRESETS,
    }
    return render(request, 'reporting/imap_connect.html', context)


@login_required
def imap_disconnect(request):
    """IMAP/SMTP 연결 해제"""
    user_profile = request.user.userprofile
    
    # 연동 정보 삭제
    user_profile.email_provider = 'gmail'
    user_profile.imap_email = ''
    user_profile.imap_host = ''
    user_profile.imap_port = 993
    user_profile.imap_username = ''
    user_profile.imap_password = ''
    user_profile.smtp_host = ''
    user_profile.smtp_port = 587
    user_profile.smtp_username = ''
    user_profile.smtp_password = ''
    user_profile.imap_connected_at = None
    user_profile.save()
    
    messages.success(request, "이메일 연동이 해제되었습니다.")
    return redirect('profile')


@login_required
def sync_imap_emails(request):
    """IMAP 이메일 동기화"""
    user_profile = request.user.userprofile
    
    if not user_profile.imap_email:
        messages.error(request, "먼저 이메일을 연동해주세요.")
        return redirect('profile')
    
    try:
        # 대상 이메일 목록 가져오기
        target_emails = set()
        
        # FollowUp의 고객 이메일
        followups = FollowUp.objects.filter(user=request.user, status='active')
        for followup in followups:
            if followup.customer and followup.customer.email:
                target_emails.add(followup.customer.email.lower())
        
        # Schedule의 담당자 이메일
        schedules = Schedule.objects.filter(user=request.user)
        for schedule in schedules:
            if schedule.contact_person_email:
                target_emails.add(schedule.contact_person_email.lower())
        
        # IMAP 서비스 초기화
        imap_service = IMAPEmailService(user_profile)
        
        if not imap_service.connect():
            messages.error(request, "이메일 서버 연결에 실패했습니다.")
            return redirect('mailbox')
        
        try:
            # 이메일 가져오기 (최근 7일)
            days = int(request.GET.get('days', 7))
            emails = imap_service.fetch_emails(
                folder='INBOX',
                days=days,
                target_emails=list(target_emails)
            )
            
            # EmailLog에 저장
            saved_count = 0
            for email_data in emails:
                # 중복 확인 (message_id 기준)
                if EmailLog.objects.filter(
                    user=request.user,
                    message_id=email_data['message_id']
                ).exists():
                    continue
                
                # FollowUp 연결
                followup = None
                from_email = email_data['from_email'].lower()
                to_email = email_data['to_email'].lower()
                
                # 발신자나 수신자가 followup 고객과 매칭되는지 확인
                for fu in followups:
                    if fu.customer and fu.customer.email:
                        customer_email = fu.customer.email.lower()
                        if customer_email in [from_email, to_email]:
                            followup = fu
                            break
                
                # EmailLog 생성
                EmailLog.objects.create(
                    user=request.user,
                    followup=followup,
                    message_id=email_data['message_id'],
                    thread_id=email_data['thread_id'],
                    from_email=email_data['from_email'],
                    from_name=email_data['from_name'],
                    to_email=email_data['to_email'],
                    cc_emails=','.join(email_data['cc_emails']) if email_data['cc_emails'] else '',
                    subject=email_data['subject'],
                    body=email_data['body'],
                    sent_at=email_data['date'],
                    is_sent=False,
                    provider='imap',
                )
                saved_count += 1
            
            # 동기화 시간 업데이트
            user_profile.imap_last_sync_at = timezone.now()
            user_profile.save()
            
            messages.success(request, f"✓ 이메일 동기화 완료: {saved_count}개의 새 메일")
            
        finally:
            imap_service.disconnect()
        
    except Exception as e:
        logger.error(f"IMAP 동기화 실패: {e}")
        messages.error(request, f"이메일 동기화 중 오류가 발생했습니다: {str(e)}")
    
    return redirect('mailbox')


@login_required
@require_http_methods(["POST"])
def send_email_imap(request):
    """IMAP/SMTP를 통한 이메일 발송"""
    user_profile = request.user.userprofile
    
    if not user_profile.imap_email:
        return JsonResponse({
            'success': False,
            'message': '먼저 이메일을 연동해주세요.'
        }, status=400)
    
    try:
        # 폼 데이터
        to_email = request.POST.get('to_email', '').strip()
        cc_emails_str = request.POST.get('cc_emails', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        html_body = request.POST.get('html_body', '').strip()
        
        # 답장 정보
        in_reply_to = request.POST.get('in_reply_to', '').strip()
        references = request.POST.get('references', '').strip()
        
        # FollowUp ID
        followup_id = request.POST.get('followup_id')
        schedule_id = request.POST.get('schedule_id')
        
        # CC 이메일 파싱
        cc_emails = [email.strip() for email in cc_emails_str.split(',') if email.strip()] if cc_emails_str else []
        
        # SMTP 서비스
        smtp_service = SMTPEmailService(user_profile)
        
        # 이메일 발송
        success = smtp_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails,
            html_body=html_body or None,
            in_reply_to=in_reply_to or None,
            references=references or None,
        )
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': '이메일 발송에 실패했습니다.'
            }, status=500)
        
        # EmailLog 저장
        followup = None
        if followup_id:
            try:
                followup = FollowUp.objects.get(id=followup_id, user=request.user)
            except FollowUp.DoesNotExist:
                pass
        
        schedule = None
        if schedule_id:
            try:
                schedule = Schedule.objects.get(id=schedule_id, user=request.user)
            except Schedule.DoesNotExist:
                pass
        
        # Message-ID 생성 (간단한 형식)
        import uuid
        message_id = f"<{uuid.uuid4()}@{user_profile.smtp_host}>"
        
        EmailLog.objects.create(
            user=request.user,
            followup=followup,
            schedule=schedule,
            message_id=message_id,
            thread_id=in_reply_to or message_id,
            from_email=user_profile.imap_email,
            from_name=request.user.get_full_name() or request.user.username,
            to_email=to_email,
            cc_emails=','.join(cc_emails) if cc_emails else '',
            subject=subject,
            body=body,
            sent_at=timezone.now(),
            is_sent=True,
            provider='smtp',
        )
        
        return JsonResponse({
            'success': True,
            'message': '이메일이 발송되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"IMAP 이메일 발송 실패: {e}")
        return JsonResponse({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }, status=500)
