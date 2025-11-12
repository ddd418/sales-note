"""
History에 저장된 납품 금액을 OpportunityTracking에 반영
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking, History
from decimal import Decimal

# History에 납품 금액이 있는 Schedule ID들
schedule_history_mapping = {
    155: 558415,   # 이다민
    32: 60060,     # 박진희
    242: 58520,    # 이수진
    287: 1331352,  # 오세영
}

print("=" * 80)
print("History 납품 금액을 OpportunityTracking에 업데이트")
print("=" * 80)
print()

updated_count = 0

for schedule_id, delivery_amount in schedule_history_mapping.items():
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        if not schedule.opportunity:
            print(f"⚠️  Schedule {schedule_id}: Opportunity 없음, 건너뜀")
            continue
        
        opportunity = schedule.opportunity
        old_revenue = opportunity.actual_revenue or 0
        old_expected = opportunity.expected_revenue or 0
        
        # actual_revenue와 expected_revenue 업데이트
        opportunity.actual_revenue = Decimal(str(delivery_amount))
        
        # expected_revenue가 없거나 actual_revenue보다 작으면 업데이트
        if not opportunity.expected_revenue or opportunity.expected_revenue < Decimal(str(delivery_amount)):
            opportunity.expected_revenue = Decimal(str(delivery_amount))
        
        opportunity.save()
        opportunity.update_revenue_amounts()  # weighted_revenue 재계산
        
        print(f"✅ Schedule {schedule_id} ({schedule.followup.customer_name})")
        print(f"   Opportunity ID: {opportunity.id}")
        print(f"   실제 수주액: {old_revenue:,}원 → {delivery_amount:,}원")
        print(f"   예상 수주액: {old_expected:,}원 → {opportunity.expected_revenue:,}원")
        
        updated_count += 1
        
    except Schedule.DoesNotExist:
        print(f"❌ Schedule {schedule_id}: 존재하지 않음")
    except Exception as e:
        print(f"❌ Schedule {schedule_id}: 오류 - {e}")

print(f"\n{'='*80}")
print(f"✅ 업데이트 완료: {updated_count}건")
print(f"{'='*80}")

# 총 수주 금액 확인
total_won_revenue = OpportunityTracking.objects.filter(
    current_stage='won'
).aggregate(
    total=django.db.models.Sum('actual_revenue')
)['total'] or 0

print(f"\n💰 현재 총 수주 금액: {total_won_revenue:,}원")
