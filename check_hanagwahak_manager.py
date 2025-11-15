import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.contrib.auth.models import User
from reporting.models import UserProfile, UserCompany

# 하나과학 매니저 찾기
print("=== 하나과학 관련 사용자 확인 ===\n")

# 모든 매니저 확인
managers = UserProfile.objects.filter(role='manager')
print(f"전체 매니저 수: {managers.count()}")
for manager in managers:
    print(f"\n매니저: {manager.user.username}")
    print(f"  - 이름: {manager.user.get_full_name()}")
    print(f"  - 회사: {manager.company}")
    print(f"  - 회사 ID: {manager.company.id if manager.company else 'None'}")

# UserCompany 목록 확인
print("\n=== UserCompany 목록 ===\n")
user_companies = UserCompany.objects.all()
for company in user_companies:
    print(f"UserCompany: {company.name} (ID: {company.id})")
    
    # 해당 회사의 사용자들
    users = UserProfile.objects.filter(company=company)
    print(f"  소속 사용자 수: {users.count()}")
    for user_profile in users:
        print(f"    - {user_profile.user.username} ({user_profile.role})")

# 하나과학 실무자 확인
print("\n=== 실무자(Salesman) 목록 ===\n")
salesmen = UserProfile.objects.filter(role='salesman')
for salesman in salesmen:
    print(f"실무자: {salesman.user.username}")
    print(f"  - 회사: {salesman.company}")
