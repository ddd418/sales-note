"""
기존 납품 완료 일정의 actual_revenue 업데이트 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking, DeliveryItem
from decimal import Decimal

def update_actual_revenue():
    """납품 완료 일정의 actual_revenue 업데이트"""
    
    # 납품 완료 일정 중 OpportunityTracking이 연결된 것들
    completed_deliveries = Schedule.objects.filter(
        activity_type='delivery',
        status='completed',
        opportunity__isnull=False
    ).select_related('opportunity')
    
    print(f"📦 총 {completed_deliveries.count()}개의 완료된 납품 일정 발견")
    
    updated_count = 0
    skipped_count = 0
    
    for schedule in completed_deliveries:
        opportunity = schedule.opportunity
        
        # 납품 품목 총액 계산
        total_delivery_amount = Decimal('0')
        delivery_items = schedule.delivery_items_set.all()
        
        for item in delivery_items:
            if item.total_price:
                total_delivery_amount += item.total_price
            elif item.unit_price and item.quantity:
                total_delivery_amount += item.unit_price * item.quantity * Decimal('1.1')
        
        # actual_revenue 업데이트
        if total_delivery_amount > 0:
            old_revenue = opportunity.actual_revenue or 0
            opportunity.actual_revenue = total_delivery_amount
            opportunity.save(update_fields=['actual_revenue'])
            
            print(f"✅ Schedule ID {schedule.id} ({schedule.followup.customer_name})")
            print(f"   이전: {old_revenue:,}원 → 현재: {total_delivery_amount:,}원")
            print(f"   납품 품목: {delivery_items.count()}개")
            updated_count += 1
        else:
            print(f"⚠️  Schedule ID {schedule.id} ({schedule.followup.customer_name}) - 납품 품목 없음, 건너뜀")
            skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ 업데이트 완료: {updated_count}건")
    print(f"⚠️  건너뜀: {skipped_count}건")
    print(f"{'='*60}")
    
    # 총 수주 금액 확인
    total_won_revenue = OpportunityTracking.objects.filter(
        current_stage='won'
    ).aggregate(
        total=django.db.models.Sum('actual_revenue')
    )['total'] or 0
    
    print(f"\n💰 현재 총 수주 금액: {total_won_revenue:,}원")

if __name__ == '__main__':
    print("=" * 60)
    print("납품 완료 일정의 actual_revenue 업데이트 시작")
    print("=" * 60)
    update_actual_revenue()
