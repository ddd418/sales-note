import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking
from django.db.models import Count
from django.contrib.auth.models import User

# 전체 영업기회 (필터 없음)
total = OpportunityTracking.objects.count()
won = OpportunityTracking.objects.filter(current_stage='won').count()
win_rate = round(won / total * 100, 1) if total > 0 else 0

print("=" * 50)
print("영업기회 전환 현황 (전체)")
print("=" * 50)
print(f"전체 영업기회: {total}건")
print(f"수주(won): {won}건")
print(f"승률: {win_rate}%")
print()

# 사용자별 영업기회
print("=" * 50)
print("사용자별 영업기회")
print("=" * 50)
for user in User.objects.all():
    user_total = OpportunityTracking.objects.filter(followup__user=user).count()
    user_won = OpportunityTracking.objects.filter(followup__user=user, current_stage='won').count()
    user_rate = round(user_won / user_total * 100, 1) if user_total > 0 else 0
    if user_total > 0:
        print(f"{user.username}: 전체 {user_total}건, 수주 {user_won}건, 승률 {user_rate}%")

print()
print("단계별 분포:")
print("-" * 30)

stages = OpportunityTracking.objects.values('current_stage').annotate(cnt=Count('id')).order_by('-cnt')
for s in stages:
    print(f"  {s['current_stage']}: {s['cnt']}건")
