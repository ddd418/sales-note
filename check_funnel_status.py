import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, Schedule

print("현재 OpportunityTracking 상태:\n")

for opp in OpportunityTracking.objects.all():
    print(f"OpportunityTracking #{opp.id}")
    print(f"  고객: {opp.followup.customer_name}")
    print(f"  현재 단계: {opp.get_current_stage_display()}")
    print(f"  수주 금액: {opp.backlog_amount:,}원")
    
    # 관련 일정 확인
    schedules = opp.schedules.all()
    print(f"  관련 일정 수: {schedules.count()}개")
    
    for schedule in schedules:
        print(f"    - ID: {schedule.id}, 상태: {schedule.get_status_display()}, 유형: {schedule.get_activity_type_display()}, 예상매출: {schedule.expected_revenue or 0:,}원")
    
    # 예정 상태의 일정만 확인
    scheduled = opp.schedules.filter(status='scheduled', expected_revenue__isnull=False)
    total = sum(s.expected_revenue for s in scheduled) if scheduled.exists() else 0
    print(f"  예정 일정 매출 합계: {total:,}원")
    print(f"  ⚠️ 불일치 여부: {'예' if total != opp.backlog_amount else '아니오'}")
    print()
