"""
Schedule 데이터 확인 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking

# 예상 매출이 입력된 Schedule 확인
schedules_with_revenue = Schedule.objects.filter(expected_revenue__isnull=False)
total_schedules = Schedule.objects.count()

print("=" * 60)
print("Schedule 데이터 현황")
print("=" * 60)
print(f"\n전체 Schedule: {total_schedules}개")
print(f"예상 매출이 입력된 Schedule: {schedules_with_revenue.count()}개")
print(f"OpportunityTracking: {OpportunityTracking.objects.count()}개")

if schedules_with_revenue.exists():
    print("\n[예상 매출이 입력된 Schedule 목록 (최대 10개)]")
    for idx, schedule in enumerate(schedules_with_revenue[:10], 1):
        print(f"{idx}. {schedule.customer_name} ({schedule.company_name})")
        print(f"   예상 매출: {schedule.expected_revenue:,}원")
        print(f"   확률: {schedule.probability}%")
        if schedule.expected_close_date:
            print(f"   예상 계약일: {schedule.expected_close_date}")
        print()
else:
    print("\n⚠️  예상 매출이 입력된 Schedule이 없습니다.")
    print("Schedule 생성 시 '영업 기회 정보'를 입력하면 자동으로 OpportunityTracking이 생성됩니다.")

print("=" * 60)
