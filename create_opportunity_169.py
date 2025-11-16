#!/usr/bin/env python
"""
FollowUp 169 (심윤지)의 OpportunityTracking 생성 스크립트

문제: OpportunityTracking이 없어서 펀넬에 표시되지 않음
해결: 예정된 견적에 맞춰 quote 단계 OpportunityTracking 생성
"""

import os
import sys
import django
from datetime import date

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, FollowUp, Schedule, FunnelStage
from decimal import Decimal

def create_opportunity_tracking_169():
    """FollowUp 169의 OpportunityTracking 생성"""
    
    print("="*80)
    print("  FollowUp 169 (심윤지) OpportunityTracking 생성")
    print("="*80)
    
    try:
        # FollowUp 169 조회
        followup = FollowUp.objects.get(id=169)
        print(f"\n✓ FollowUp 찾음: {followup.customer_name} ({followup.company.name if followup.company else '업체명 없음'})")
        print(f"  담당자: {followup.user.username}")
        
        # 기존 OpportunityTracking 확인
        existing_opps = OpportunityTracking.objects.filter(followup=followup)
        if existing_opps.exists():
            print(f"\n⚠️ 이미 OpportunityTracking이 {existing_opps.count()}개 존재합니다:")
            for opp in existing_opps:
                print(f"  - ID {opp.id}: {opp.current_stage} 단계")
            
            confirm = input("\n계속하시겠습니까? (yes/no): ")
            if confirm.lower() != 'yes':
                print("\n❌ 취소되었습니다.")
                return
        
        # 예정된 견적 확인
        scheduled_quote = Schedule.objects.filter(
            followup=followup,
            activity_type='quote',
            status='scheduled'
        ).first()
        
        if not scheduled_quote:
            print(f"\n⚠️ 예정된 견적이 없습니다. OpportunityTracking을 생성할 수 없습니다.")
            return
        
        print(f"\n📅 예정된 견적:")
        print(f"  - 날짜: {scheduled_quote.visit_date} {scheduled_quote.visit_time}")
        print(f"  - 메모: {scheduled_quote.notes or '없음'}")
        
        # 견적 품목에서 예상 매출 계산
        from reporting.models import DeliveryItem
        delivery_items = DeliveryItem.objects.filter(schedule=scheduled_quote)
        expected_revenue = Decimal('0')
        
        if delivery_items.exists():
            print(f"\n📦 견적 품목 {delivery_items.count()}개:")
            for item in delivery_items:
                print(f"  - {item.item_name}: {item.quantity}개 x {item.unit_price:,}원 = {item.total_price:,}원")
                if item.total_price:
                    expected_revenue += item.total_price
            print(f"\n  💰 총 예상 매출: {expected_revenue:,}원")
        else:
            print(f"\n⚠️ 견적 품목이 없습니다. 기본값 0원으로 설정합니다.")
        
        # quote 단계 확인
        try:
            quote_stage = FunnelStage.objects.get(name='quote')
            print(f"\n✓ FunnelStage 찾음: {quote_stage.display_name}")
            print(f"  - 확률: {quote_stage.default_probability}%")
        except FunnelStage.DoesNotExist:
            print(f"\n❌ 'quote' FunnelStage를 찾을 수 없습니다!")
            return
        
        # 사용자 확인
        print(f"\n새로운 OpportunityTracking을 생성하시겠습니까?")
        print(f"  - 단계: quote (견적)")
        print(f"  - 확률: {quote_stage.default_probability}%")
        print(f"  - 예상 매출: {expected_revenue:,}원")
        print(f"  - 예상 마감일: {scheduled_quote.visit_date}")
        
        confirm = input("\n계속하려면 'yes' 입력: ")
        if confirm.lower() != 'yes':
            print("\n❌ 취소되었습니다.")
            return
        
        # OpportunityTracking 생성
        new_opp = OpportunityTracking.objects.create(
            followup=followup,
            current_stage='quote',
            probability=quote_stage.default_probability,
            expected_revenue=expected_revenue,
            weighted_revenue=expected_revenue * Decimal(quote_stage.default_probability) / Decimal('100'),
            expected_close_date=scheduled_quote.visit_date,
            stage_history=[{
                'stage': 'quote',
                'entered': date.today().isoformat(),
                'probability': quote_stage.default_probability,
            }]
        )
        
        print(f"\n✅ OpportunityTracking 생성 완료!")
        print(f"\n생성된 OpportunityTracking:")
        print(f"  - ID: {new_opp.id}")
        print(f"  - 단계: {new_opp.current_stage} ({new_opp.get_current_stage_display()})")
        print(f"  - 확률: {new_opp.probability}%")
        print(f"  - 예상 매출: {new_opp.expected_revenue:,}원")
        print(f"  - 가중 매출: {new_opp.weighted_revenue:,}원")
        print(f"  - 예상 마감일: {new_opp.expected_close_date}")
        
        print(f"\n{'='*80}")
        print("  완료! 이제 펀넬 견적 단계에 표시됩니다.")
        print("="*80)
        
    except FollowUp.DoesNotExist:
        print(f"\n❌ FollowUp ID 169를 찾을 수 없습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    create_opportunity_tracking_169()
