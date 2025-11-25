#!/usr/bin/env python
"""스레드 19ab7e8cf353ed34의 모든 이메일 확인"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import EmailLog

thread_id = '19ab7e8cf353ed34'

emails = EmailLog.objects.filter(gmail_thread_id=thread_id).order_by('created_at')

print("="*80)
print(f"  Gmail 스레드 ID: {thread_id}")
print(f"  총 {emails.count()}개의 이메일")
print("="*80)

for email in emails:
    print(f"\n{'='*80}")
    print(f"EmailLog ID: {email.id}")
    print(f"타입: {email.email_type} ({email.get_email_type_display()})")
    print(f"발신자 이메일: {email.sender_email}")
    print(f"수신자 이메일: {email.recipient_email}")
    print(f"제목: {email.subject}")
    print(f"생성일시: {email.created_at}")
    print(f"발송/수신일시: {email.sent_at or email.received_at}")
    
    if email.email_type == 'received':
        print(f"\n>>> 이 메일에 답장하려면:")
        print(f"    받는 사람: {email.sender_email}")
        print(f"    URL: /reporting/gmail/reply/{email.id}/")

print("\n" + "="*80)
