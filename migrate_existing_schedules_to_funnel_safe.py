"""
기존 견적/납품 일정을 펀넬(OpportunityTracking)에 연결하는 스크립트 (DRY RUN 모드 포함)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking, FollowUp
from decimal import Decimal
from datetime import date

def migrate_schedules_to_funnel(dry_run=True):
    """기존 견적/납품 일정을 펀넬에 연결"""
    
    if dry_run:
        print("🔍 DRY RUN 모드: 실제로 데이터를 변경하지 않고 미리보기만 합니다.")
        print()
    
    # 견적 또는 납품 일정 중 opportunity가 없는 것들
    schedules_without_opportunity = Schedule.objects.filter(
        activity_type__in=['quote', 'delivery'],
        opportunity__isnull=True
    ).select_related('followup').order_by('followup', 'visit_date')
    
    print(f"📦 총 {schedules_without_opportunity.count()}개의 견적/납품 일정 발견 (펀넬 미연결)")
    
    if schedules_without_opportunity.count() == 0:
        print("✅ 모든 견적/납품 일정이 이미 펀넬에 연결되어 있습니다.")
        return
    
    print()
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    # FollowUp별로 그룹화하여 미리보기
    followup_groups = {}
    for schedule in schedules_without_opportunity:
        if schedule.followup.id not in followup_groups:
            followup_groups[schedule.followup.id] = {
                'followup': schedule.followup,
                'schedules': []
            }
        followup_groups[schedule.followup.id]['schedules'].append(schedule)
    
    print(f"📋 영향받을 고객(FollowUp): {len(followup_groups)}명\n")
    
    # FollowUp별로 처리
    for followup_id, group_data in followup_groups.items():
        followup = group_data['followup']
        schedules = group_data['schedules']
        
        # 해당 FollowUp의 기존 Opportunity 찾기
        existing_opportunity = OpportunityTracking.objects.filter(
            followup=followup
        ).order_by('-created_at').first()
        
        if existing_opportunity:
            print(f"✅ {followup.customer_name} (FollowUp ID: {followup.id})")
            print(f"   → 기존 Opportunity ID {existing_opportunity.id}에 연결")
            print(f"   영향받을 일정: {len(schedules)}개")
            for sch in schedules:
                print(f"      - Schedule ID {sch.id}: {sch.get_activity_type_display()} ({sch.visit_date})")
            
            if not dry_run:
                # 실제 연결
                for sch in schedules:
                    sch.opportunity = existing_opportunity
                    sch.save(update_fields=['opportunity'])
                
                # Opportunity 정보 업데이트
                update_opportunity_from_schedules(existing_opportunity, followup, dry_run=False)
            
            updated_count += len(schedules)
            
        else:
            print(f"🆕 {followup.customer_name} (FollowUp ID: {followup.id})")
            print(f"   → 새 Opportunity 생성 필요")
            print(f"   연결될 일정: {len(schedules)}개")
            for sch in schedules:
                print(f"      - Schedule ID {sch.id}: {sch.get_activity_type_display()} ({sch.visit_date})")
            
            if not dry_run:
                # 첫 일정 기준으로 Opportunity 생성
                first_schedule = schedules[0]
                
                opportunity = OpportunityTracking.objects.create(
                    followup=followup,
                    title=f"{followup.customer_name} - {first_schedule.get_activity_type_display()}",
                    source='existing_migration',
                    current_stage='quote' if first_schedule.activity_type == 'quote' else 'won',
                    stage_entry_date=first_schedule.visit_date or date.today(),
                    created_at=first_schedule.visit_date or date.today(),
                )
                
                print(f"   ✅ 생성된 Opportunity ID: {opportunity.id}")
                
                # 모든 일정 연결
                for sch in schedules:
                    sch.opportunity = opportunity
                    sch.save(update_fields=['opportunity'])
                
                # Opportunity 정보 업데이트
                update_opportunity_from_schedules(opportunity, followup, dry_run=False)
            
            created_count += 1
        
        print()
    
    print(f"{'='*60}")
    if dry_run:
        print("🔍 DRY RUN 결과 (실제로 변경되지 않음):")
    else:
        print("✅ 마이그레이션 완료:")
    print(f"   🆕 새 Opportunity 생성 예정/완료: {created_count}건")
    print(f"   ✅ 기존 Opportunity에 연결 예정/완료: {updated_count}개 일정")
    print(f"   ⚠️  건너뜀: {skipped_count}건")
    print(f"{'='*60}")


def update_opportunity_from_schedules(opportunity, followup, dry_run=True):
    """Schedule 데이터를 기반으로 Opportunity 정보 업데이트"""
    
    if dry_run:
        return
    
    # 해당 Opportunity에 연결된 모든 일정
    schedules = Schedule.objects.filter(
        followup=followup,
        opportunity=opportunity
    ).order_by('visit_date')
    
    # 견적 일정들
    quote_schedules = schedules.filter(activity_type='quote')
    # 납품 일정들
    delivery_schedules = schedules.filter(activity_type='delivery')
    
    # 예상 수주액 계산
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
    
    # 실제 수주액 계산
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
    
    # 예상 클로징 날짜
    if not opportunity.expected_close_date and schedules.exists():
        latest_schedule = schedules.last()
        if latest_schedule.visit_date:
            opportunity.expected_close_date = latest_schedule.visit_date
    
    # 확률
    if not opportunity.probability:
        if completed_deliveries.exists():
            opportunity.probability = 100
        elif quote_schedules.exists():
            opportunity.probability = 50
        else:
            opportunity.probability = 30
    
    opportunity.save()
    
    print(f"      📊 예상 수주액: {opportunity.expected_revenue or 0:,}원")
    print(f"      📊 실제 수주액: {opportunity.actual_revenue or 0:,}원")
    print(f"      📊 확률: {opportunity.probability}%")
    print(f"      📊 현재 단계: {opportunity.current_stage}")


if __name__ == '__main__':
    print("=" * 60)
    print("기존 견적/납품 일정을 펀넬에 연결")
    print("=" * 60)
    print()
    
    print("1️⃣  DRY RUN (미리보기만)")
    print("2️⃣  실제 실행 (데이터 변경)")
    print()
    
    choice = input("선택하세요 (1/2): ").strip()
    
    if choice == '1':
        migrate_schedules_to_funnel(dry_run=True)
    elif choice == '2':
        print()
        confirm = input("⚠️  정말로 실행하시겠습니까? 'YES' 입력: ").strip()
        if confirm == 'YES':
            print()
            migrate_schedules_to_funnel(dry_run=False)
        else:
            print("취소되었습니다.")
    else:
        print("잘못된 선택입니다.")
