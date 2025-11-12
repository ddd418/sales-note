"""
기존 견적/납품 일정을 펀넬(OpportunityTracking)에 연결하는 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking, FollowUp
from decimal import Decimal
from datetime import date

def migrate_schedules_to_funnel():
    """기존 견적/납품 일정을 펀넬에 연결"""
    
    # 견적 또는 납품 일정 중 opportunity가 없는 것들
    schedules_without_opportunity = Schedule.objects.filter(
        activity_type__in=['quote', 'delivery'],
        opportunity__isnull=True
    ).select_related('followup').order_by('followup', 'visit_date')
    
    print(f"📦 총 {schedules_without_opportunity.count()}개의 견적/납품 일정 발견 (펀넬 미연결)")
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    # FollowUp별로 그룹화하여 처리
    processed_followups = set()
    
    for schedule in schedules_without_opportunity:
        followup = schedule.followup
        
        # 이미 처리한 FollowUp은 건너뛰기
        if followup.id in processed_followups:
            # 같은 FollowUp의 기존 Opportunity에 연결
            existing_opportunity = OpportunityTracking.objects.filter(
                followup=followup
            ).order_by('-created_at').first()
            
            if existing_opportunity:
                schedule.opportunity = existing_opportunity
                schedule.save(update_fields=['opportunity'])
                print(f"  ↳ Schedule ID {schedule.id} → 기존 Opportunity ID {existing_opportunity.id}에 연결")
                updated_count += 1
            continue
        
        processed_followups.add(followup.id)
        
        # 해당 FollowUp의 기존 Opportunity 찾기
        existing_opportunity = OpportunityTracking.objects.filter(
            followup=followup
        ).order_by('-created_at').first()
        
        if existing_opportunity:
            print(f"\n✅ FollowUp ID {followup.id} ({followup.customer_name}) - 기존 Opportunity 사용")
            print(f"   Opportunity ID: {existing_opportunity.id}")
            
            # 같은 FollowUp의 모든 견적/납품 일정을 이 Opportunity에 연결
            related_schedules = Schedule.objects.filter(
                followup=followup,
                activity_type__in=['quote', 'delivery'],
                opportunity__isnull=True
            )
            
            for sch in related_schedules:
                sch.opportunity = existing_opportunity
                sch.save(update_fields=['opportunity'])
                print(f"  ↳ Schedule ID {sch.id} ({sch.get_activity_type_display()}, {sch.visit_date}) 연결")
                updated_count += 1
            
            # Opportunity 정보 업데이트
            update_opportunity_from_schedules(existing_opportunity, followup)
            
        else:
            # 새로운 Opportunity 생성
            print(f"\n🆕 FollowUp ID {followup.id} ({followup.customer_name}) - 새 Opportunity 생성")
            
            # 해당 FollowUp의 첫 견적/납품 일정 찾기
            first_schedule = Schedule.objects.filter(
                followup=followup,
                activity_type__in=['quote', 'delivery']
            ).order_by('visit_date').first()
            
            if not first_schedule:
                print(f"  ⚠️ 견적/납품 일정 없음, 건너뜀")
                skipped_count += 1
                continue
            
            # OpportunityTracking 생성
            opportunity = OpportunityTracking.objects.create(
                followup=followup,
                title=f"{followup.customer_name} - {first_schedule.get_activity_type_display()}",
                source='existing_migration',  # 마이그레이션으로 생성됨을 표시
                current_stage='quote' if first_schedule.activity_type == 'quote' else 'won',
                stage_entry_date=first_schedule.visit_date or date.today(),
                created_at=first_schedule.visit_date or date.today(),
            )
            
            print(f"   생성된 Opportunity ID: {opportunity.id}")
            print(f"   초기 단계: {opportunity.current_stage}")
            
            # 같은 FollowUp의 모든 견적/납품 일정을 이 Opportunity에 연결
            related_schedules = Schedule.objects.filter(
                followup=followup,
                activity_type__in=['quote', 'delivery']
            )
            
            for sch in related_schedules:
                sch.opportunity = opportunity
                sch.save(update_fields=['opportunity'])
                print(f"  ↳ Schedule ID {sch.id} ({sch.get_activity_type_display()}, {sch.visit_date}) 연결")
            
            # Opportunity 정보 업데이트
            update_opportunity_from_schedules(opportunity, followup)
            
            created_count += 1
    
    print(f"\n{'='*60}")
    print(f"🆕 새 Opportunity 생성: {created_count}건")
    print(f"✅ 기존 Opportunity에 연결: {updated_count}건")
    print(f"⚠️  건너뜀: {skipped_count}건")
    print(f"{'='*60}")


def update_opportunity_from_schedules(opportunity, followup):
    """Schedule 데이터를 기반으로 Opportunity 정보 업데이트"""
    
    # 해당 Opportunity에 연결된 모든 일정
    schedules = Schedule.objects.filter(
        followup=followup,
        opportunity=opportunity
    ).order_by('visit_date')
    
    # 견적 일정들
    quote_schedules = schedules.filter(activity_type='quote')
    # 납품 일정들
    delivery_schedules = schedules.filter(activity_type='delivery')
    
    # 예상 수주액 계산 (견적 또는 납품 일정의 예상 매출액)
    if not opportunity.expected_revenue:
        for schedule in schedules:
            if schedule.expected_revenue and schedule.expected_revenue > 0:
                opportunity.expected_revenue = schedule.expected_revenue
                break
        
        # 예상 매출액이 없으면 납품 품목에서 계산
        if not opportunity.expected_revenue:
            for delivery in delivery_schedules:
                items = delivery.delivery_items_set.all()
                if items.exists():
                    total = Decimal('0')
                    for item in items:
                        if item.total_price:
                            total += item.total_price
                        elif item.unit_price and item.quantity:
                            total += item.unit_price * item.quantity * Decimal('1.1')
                    
                    if total > 0:
                        opportunity.expected_revenue = total
                        break
    
    # 실제 수주액 계산 (완료된 납품 일정의 품목 총액)
    completed_deliveries = delivery_schedules.filter(status='completed')
    if completed_deliveries.exists():
        total_actual_revenue = Decimal('0')
        
        for delivery in completed_deliveries:
            items = delivery.delivery_items_set.all()
            for item in items:
                if item.total_price:
                    total_actual_revenue += item.total_price
                elif item.unit_price and item.quantity:
                    total_actual_revenue += item.unit_price * item.quantity * Decimal('1.1')
        
        if total_actual_revenue > 0:
            opportunity.actual_revenue = total_actual_revenue
            
            # 완료된 납품이 있으면 won 단계로
            if opportunity.current_stage != 'won':
                opportunity.current_stage = 'won'
                opportunity.stage_entry_date = completed_deliveries.first().visit_date or date.today()
    
    # 예상 클로징 날짜 (가장 최근 일정의 날짜)
    if not opportunity.expected_close_date and schedules.exists():
        latest_schedule = schedules.last()
        if latest_schedule.visit_date:
            opportunity.expected_close_date = latest_schedule.visit_date
    
    # 확률 (견적이 있으면 기본 50%, 납품 완료면 100%)
    if not opportunity.probability:
        if completed_deliveries.exists():
            opportunity.probability = 100
        elif quote_schedules.exists():
            opportunity.probability = 50
        else:
            opportunity.probability = 30
    
    opportunity.save()
    
    print(f"   📊 Opportunity 업데이트:")
    print(f"      예상 수주액: {opportunity.expected_revenue or 0:,}원")
    print(f"      실제 수주액: {opportunity.actual_revenue or 0:,}원")
    print(f"      확률: {opportunity.probability}%")
    print(f"      현재 단계: {opportunity.current_stage}")


if __name__ == '__main__':
    print("=" * 60)
    print("기존 견적/납품 일정을 펀넬에 연결")
    print("=" * 60)
    print()
    
    response = input("⚠️  이 작업은 기존 데이터를 수정합니다. 계속하시겠습니까? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_schedules_to_funnel()
    else:
        print("취소되었습니다.")
