import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, Company, Quote, OpportunityTracking

# 수정된 로직 확인
print("=" * 80)
print("수정된 영업기회 전환 현황 (completed 일정 필수)")
print("=" * 80)

# 종료된 영업기회 중 완료된 일정이 있는 것만
all_opportunities = OpportunityTracking.objects.filter(
    current_stage__in=['won', 'lost'],
    schedules__status='completed'  # 완료된 일정이 있는 영업기회만
).distinct()

print(f"\n종료된 영업기회 (completed 일정 필수): {all_opportunities.count()}개")

for opp in all_opportunities:
    print(f"\n  ID: {opp.id}")
    print(f"  current_stage: {opp.current_stage}")
    schedules = opp.schedules.all()
    if schedules:
        for s in schedules:
            print(f"    -> 일정 ID: {s.id}, 상태: {s.status}")
    print("-" * 40)

won_count = all_opportunities.filter(current_stage='won').count()
print(f"\n수주(won): {won_count}개")
print(f"전체: {all_opportunities.count()}개")
print(f"승률: {round(won_count / all_opportunities.count() * 100, 1) if all_opportunities.count() > 0 else 0}%")
