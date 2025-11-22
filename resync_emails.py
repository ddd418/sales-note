"""
기존 메일 삭제 후 재동기화 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import EmailLog, UserProfile
from django.contrib.auth.models import User

def resync_all_emails():
    """모든 메일 삭제 후 재동기화"""
    print("=== 메일 재동기화 시작 ===\n")
    
    # 기존 메일 삭제
    deleted_count = EmailLog.objects.all().count()
    EmailLog.objects.all().delete()
    print(f"✓ 기존 메일 {deleted_count}개 삭제 완료\n")
    
    # 모든 사용자의 마지막 동기화 시점 초기화
    UserProfile.objects.all().update(gmail_last_sync_at=None)
    print("✓ 동기화 시점 초기화 완료\n")
    
    # Gmail 연결된 사용자들 재동기화
    from reporting.gmail_views import _sync_emails_by_days
    
    users_with_gmail = User.objects.filter(userprofile__gmail_token__isnull=False)
    
    for user in users_with_gmail:
        print(f"사용자: {user.username}")
        synced = _sync_emails_by_days(user, days=30)
        print(f"  → {synced}개 메일 동기화 완료\n")
    
    print("=== 재동기화 완료 ===")
    print(f"총 {EmailLog.objects.count()}개 메일 동기화됨")

if __name__ == '__main__':
    resync_all_emails()
