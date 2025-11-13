#!/usr/bin/env python
"""
기존에 완료된 납품 일정 중 OpportunityTracking이 없는 것들을 자동으로 생성하는 스크립트
"""
import os
import django
from datetime import date
from decimal import Decimal

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking

def create_missing_opportunities():
    """모든 납품 일정마다 OpportunityTracking을 생성 (기존 것 삭제 후 재생성)"""
    
    # 모든 납품 일정 조회 (예정 + 완료)
    all_deliveries = Schedule.objects.filter(
        activity_type='delivery'
    ).exclude(status='cancelled').order_by('visit_date')
    
    completed_deliveries = all_deliveries.filter(status='completed')
    scheduled_deliveries = all_deliveries.filter(status='scheduled')
    
    print(f"[INFO] 납품 일정 총 {all_deliveries.count()}건 발견")
    print(f"  - 완료된 납품: {completed_deliveries.count()}건")
    print(f"  - 예정된 납품: {scheduled_deliveries.count()}건")
    
    # 기존 OpportunityTracking 삭제 전 백업 정보 출력
    existing_won_opps = OpportunityTracking.objects.filter(current_stage='won')
    existing_closing_opps = OpportunityTracking.objects.filter(current_stage='closing')
    print(f"[INFO] 기존 수주(won) 단계 OpportunityTracking {existing_won_opps.count()}건 발견")
    print(f"[INFO] 기존 클로징(closing) 단계 OpportunityTracking {existing_closing_opps.count()}건 발견")
    print(f"[WARNING] 기존 won/closing 단계 OpportunityTracking을 모두 삭제하고 납품마다 새로 생성합니다.")
    
    # 사용자 확인 (프로덕션에서는 주의!)
    confirmation = input("계속하시겠습니까? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("[CANCELLED] 작업이 취소되었습니다.")
        return
    
    # 기존 OpportunityTracking 삭제 (won + closing)
    deleted_won = existing_won_opps.count()
    deleted_closing = existing_closing_opps.count()
    existing_won_opps.delete()
    existing_closing_opps.delete()
    print(f"[DELETED] 기존 OpportunityTracking {deleted_won + deleted_closing}건 삭제 완료 (won: {deleted_won}, closing: {deleted_closing})")
    
    created_won_count = 0
    created_closing_count = 0
    
    for schedule in all_deliveries:
        # 납품 품목에서 총액 계산
        delivery_total = Decimal('0')
        delivery_items = schedule.delivery_items_set.all()
        if delivery_items.exists():
            delivery_total = sum(Decimal(str(item.total_price or 0)) for item in delivery_items)
        
        # 예상 수주액: DeliveryItem 총액 우선 (실제 납품 금액이 정확함)
        expected_revenue = delivery_total or schedule.expected_revenue or Decimal('0')
        
        # 납품 상태에 따라 단계 결정
        if schedule.status == 'completed':
            current_stage = 'won'  # 납품 완료 = 수주
            probability = 100
            stage_label = '수주'
        else:  # scheduled
            current_stage = 'closing'  # 납품 예정 = 클로징
            probability = 80
            stage_label = '클로징'
        
        # OpportunityTracking 생성
        activity_type_names = {
            'customer_meeting': '고객 미팅',
            'quote': '견적',
            'delivery': '납품',
            'service': '서비스'
        }
        opportunity_title = f"{activity_type_names.get(schedule.activity_type, '영업 기회')} - {schedule.visit_date.strftime('%m/%d')}"
        
        opportunity = OpportunityTracking.objects.create(
            followup=schedule.followup,
            title=opportunity_title,
            current_stage=current_stage,
            expected_revenue=expected_revenue,
            probability=probability,
            expected_close_date=schedule.visit_date,
            stage_history=[{
                'stage': current_stage,
                'entered': schedule.visit_date.isoformat(),
                'exited': None,
                'note': f'{schedule.get_status_display()} 납품 일정으로부터 자동 생성 (일정 ID: {schedule.id})'
            }]
        )
        
        # Schedule과 연결
        schedule.opportunity = opportunity
        schedule.save()
        
        # 수주/실주 금액 업데이트
        opportunity.update_revenue_amounts()
        
        company_name = schedule.followup.company.name if schedule.followup.company else "업체명 미정"
        print(f"[CREATE] 일정 ID {schedule.id} ({company_name}, {schedule.visit_date}, {schedule.get_status_display()}): {stage_label} 단계 OpportunityTracking 생성 (ID: {opportunity.id}, 금액: {expected_revenue:,}원)")
        
        if current_stage == 'won':
            created_won_count += 1
        else:
            created_closing_count += 1
    
    print(f"\n[SUMMARY]")
    print(f"- 전체 납품 일정: {all_deliveries.count()}건")
    print(f"- 삭제된 기존 OpportunityTracking: {deleted_won + deleted_closing}건 (won: {deleted_won}, closing: {deleted_closing})")
    print(f"- 새로 생성된 OpportunityTracking: {created_won_count + created_closing_count}건")
    print(f"  - 수주(won): {created_won_count}건 (완료된 납품)")
    print(f"  - 클로징(closing): {created_closing_count}건 (예정된 납품)")
    
    # 최종 확인
    total_won = OpportunityTracking.objects.filter(current_stage='won').count()
    total_closing = OpportunityTracking.objects.filter(current_stage='closing').count()
    print(f"\n[FINAL]")
    print(f"- 현재 수주(won) 단계 OpportunityTracking: {total_won}건")
    print(f"- 현재 클로징(closing) 단계 OpportunityTracking: {total_closing}건")

if __name__ == '__main__':
    create_missing_opportunities()
