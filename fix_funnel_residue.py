#!/usr/bin/env python
"""
펀넬 잔상 데이터 정리 스크립트

납품 일정이 모두 삭제되었는데도 OpportunityTracking에 금액이 남아있는 경우를 정리합니다.
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, Schedule
from decimal import Decimal

def fix_funnel_residue():
    """모든 OpportunityTracking의 수주/실주 금액을 재계산하고 불필요한 것은 삭제"""
    
    print("=" * 60)
    print("펀넬 잔상 데이터 정리 시작")
    print("=" * 60)
    
    # 모든 OpportunityTracking 조회
    opportunities = OpportunityTracking.objects.all()
    total_count = opportunities.count()
    fixed_count = 0
    deleted_count = 0
    
    print(f"\n총 {total_count}개의 OpportunityTracking 발견")
    print("\n처리 중...\n")
    
    for idx, opportunity in enumerate(opportunities, 1):
        # 현재 상태 저장
        old_backlog = opportunity.backlog_amount
        old_revenue = opportunity.actual_revenue
        
        # 연결된 일정 확인
        schedules = opportunity.schedules.all()
        schedule_count = schedules.count()
        
        print(f"[{idx}/{total_count}] OpportunityTracking #{opportunity.id}")
        print(f"  - 고객: {opportunity.followup.customer_name}")
        print(f"  - 현재 단계: {opportunity.get_current_stage_display()}")
        print(f"  - 연결된 일정: {schedule_count}개")
        
        # 연결된 일정 상세 정보
        has_delivery = False
        has_quote = False
        
        for sch in schedules:
            print(f"    * Schedule #{sch.id}: {sch.get_activity_type_display()} - {sch.get_status_display()} ({sch.visit_date})")
            
            if sch.activity_type == 'delivery':
                has_delivery = True
                # 납품 일정이면 품목 확인
                from reporting.models import DeliveryItem
                items = DeliveryItem.objects.filter(schedule=sch)
                item_count = items.count()
                total_price = sum(item.total_price or 0 for item in items)
                print(f"      - 납품 품목: {item_count}개, 총액: {total_price:,}원")
            elif sch.activity_type == 'quote':
                has_quote = True
        
        print(f"  - 기존 수주 금액: {old_backlog:,}원")
        print(f"  - 기존 실주 금액: {old_revenue:,}원" if old_revenue else "  - 기존 실주 금액: 없음")
        
        # 납품이나 견적이 없고 미팅만 있는 경우 삭제 (잘못 생성된 펀넬)
        if not has_delivery and not has_quote and opportunity.current_stage in ['won', 'closing']:
            print(f"  ⚠️  납품/견적 없이 {opportunity.get_current_stage_display()} 단계인 잘못된 펀넬 발견")
            print(f"  ✓ OpportunityTracking #{opportunity.id} 삭제")
            opportunity.delete()
            deleted_count += 1
            print()
            continue
        
        # 견적만 있는데 수주(won) 단계인 경우 삭제 (잘못된 펀넬)
        if has_quote and not has_delivery and opportunity.current_stage == 'won':
            print(f"  ⚠️  견적만 있는데 수주 단계인 잘못된 펀넬 발견")
            print(f"  ✓ OpportunityTracking #{opportunity.id} 삭제")
            opportunity.delete()
            deleted_count += 1
            print()
            continue
        
        # 금액 재계산
        opportunity.update_revenue_amounts()
        opportunity.refresh_from_db()
        
        # 변경 사항 확인
        new_backlog = opportunity.backlog_amount
        new_revenue = opportunity.actual_revenue
        
        changed = False
        if old_backlog != new_backlog:
            print(f"  ✓ 수주 금액 수정: {old_backlog:,}원 → {new_backlog:,}원")
            changed = True
        
        if old_revenue != new_revenue:
            old_str = f"{old_revenue:,}원" if old_revenue else "없음"
            new_str = f"{new_revenue:,}원" if new_revenue else "없음"
            print(f"  ✓ 실주 금액 수정: {old_str} → {new_str}")
            changed = True
        
        if changed:
            fixed_count += 1
            print(f"  → 수정 완료")
        else:
            print(f"  → 변경 없음")
        
        print()
    
    print("=" * 60)
    print(f"정리 완료: {total_count}개 중 {fixed_count}개 수정, {deleted_count}개 삭제됨")
    print("=" * 60)

if __name__ == '__main__':
    try:
        fix_funnel_residue()
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
