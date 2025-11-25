#!/usr/bin/env python
"""EmailLog ID 95번 확인 스크립트"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import EmailLog

try:
    email = EmailLog.objects.get(id=95)
    
    print("="*80)
    print(f"  EmailLog ID: {email.id}")
    print("="*80)
    print(f"이메일 타입: {email.email_type} ({email.get_email_type_display()})")
    print(f"상태: {email.status} ({email.get_status_display()})")
    print(f"\n발신자 (sender): {email.sender}")
    print(f"발신자 이메일 (sender_email): {email.sender_email}")
    print(f"\n수신자 이메일 (recipient_email): {email.recipient_email}")
    print(f"수신자명 (recipient_name): {email.recipient_name}")
    print(f"\n제목: {email.subject}")
    print(f"Gmail 메시지 ID: {email.gmail_message_id}")
    print(f"Gmail 스레드 ID: {email.gmail_thread_id}")
    print(f"\n발송일시: {email.sent_at}")
    print(f"수신일시: {email.received_at}")
    
    print("\n" + "="*80)
    print("진단:")
    print("="*80)
    
    if email.email_type == 'received':
        print(f"✓ 수신 메일입니다.")
        print(f"  답장 받는 사람: {email.sender_email} (발신자에게 답장)")
        if email.sender_email == 'jhahn.hana@gmail.com':
            print(f"  ❌ 오류: sender_email이 본인 이메일입니다!")
            print(f"     실제 발신자: dkswogus95@gmail.com 이어야 함")
    else:
        print(f"✓ 발신 메일입니다.")
        print(f"  답장 받는 사람: {email.recipient_email} (수신자에게 답장)")
        
except EmailLog.DoesNotExist:
    print(f"❌ EmailLog ID 95를 찾을 수 없습니다.")
