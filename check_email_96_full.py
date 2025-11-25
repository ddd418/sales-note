import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import EmailLog

email = EmailLog.objects.get(id=96)

print("=== EmailLog ID 96 상세 정보 ===")
print(f"email_type: {email.email_type}")
print(f"sender_email: {email.sender_email}")
print(f"recipient_email: {email.recipient_email}")
print(f"recipient_name: {email.recipient_name}")
print(f"subject: {email.subject}")
print(f"\nschedule: {email.schedule}")
if email.schedule:
    print(f"  - followup: {email.schedule.followup}")
    if email.schedule.followup:
        print(f"  - customer_name: {email.schedule.followup.customer_name}")
        print(f"  - company: {email.schedule.followup.company}")
        print(f"  - manager: {email.schedule.followup.manager}")
        print(f"  - email: {email.schedule.followup.email}")
    
print(f"\nfollowup: {email.followup}")
if email.followup:
    print(f"  - customer_name: {email.followup.customer_name}")
    print(f"  - company: {email.followup.company}")
    print(f"  - manager: {email.followup.manager}")

# 원본 메일 발신자 정보 추출
if email.email_type == 'received':
    print("\n=== 답장 시 사용할 고객 정보 ===")
    print(f"고객 이메일: {email.sender_email}")
    
    # 우선순위: schedule.followup > followup
    customer_name = ""
    company_name = ""
    
    if email.schedule and email.schedule.followup:
        customer_name = email.schedule.followup.customer_name or ""
        company_name = email.schedule.followup.company.name if email.schedule.followup.company else ""
    elif email.followup:
        customer_name = email.followup.customer_name or ""
        company_name = email.followup.company.name if email.followup.company else ""
    
    print(f"추출된 고객명: {customer_name}")
    print(f"추출된 회사명: {company_name}")
    
    if not customer_name:
        # 이메일에서 이름 추출 시도
        if '<' in email.sender_email and '>' in email.sender_email:
            # "홍길동 <hong@example.com>" 형식
            name_part = email.sender_email.split('<')[0].strip()
            print(f"이메일에서 추출된 이름: {name_part}")
        else:
            # 이메일 주소만 있는 경우
            print(f"이메일 계정명 사용: {email.sender_email.split('@')[0]}")
