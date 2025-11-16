#!/usr/bin/env python
"""
FollowUp 169 (심윤지)의 won 단계 OpportunityTracking 삭제 스크립트

문제: 사용자가 일정을 완료 처리하면서 자동으로 won 단계로 이동됨
해결: won 단계 OpportunityTracking을 삭제하여 다시 quote 단계로 되돌림
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, FollowUp, Schedule

def delete_won_opportunity_169():
    """FollowUp 169의 won 단계 OpportunityTracking 삭제"""
    
    print("="*80)
    print("  FollowUp 169 (심윤지) won 단계 OpportunityTracking 삭제")
    print("="*80)
    
    try:
        # FollowUp 169 조회
        followup = FollowUp.objects.get(id=169)
        print(f"\n✓ FollowUp 찾음: {followup.customer_name} ({followup.company.name if followup.company else '업체명 없음'})")
        print(f"  담당자: {followup.user.username}")
        
        # OpportunityTracking 조회
        opps = OpportunityTracking.objects.filter(followup=followup)
        print(f"\n📊 OpportunityTracking 개수: {opps.count()}개")
        
        if not opps.exists():
            print("⚠️  OpportunityTracking이 없습니다.")
            return
        
        # 현재 OpportunityTracking 정보 출력
        won_opps = []
        for opp in opps:
            print(f"\n  OpportunityTracking ID: {opp.id}")
            print(f"  - 단계: {opp.current_stage} ({opp.get_current_stage_display()})")
            print(f"  - 확률: {opp.probability}%")
            print(f"  - 예상 매출: {opp.expected_revenue:,}원")
            print(f"  - 가중 매출: {opp.weighted_revenue:,}원")
            print(f"  - 생성일: {opp.created_at}")
            
            if opp.current_stage == 'won':
                won_opps.append(opp)
        
        if not won_opps:
            print("\n⚠️  won 단계 OpportunityTracking이 없습니다.")
            return
        
        # 예정된 견적 확인
        scheduled_quotes = Schedule.objects.filter(
            followup=followup,
            activity_type='quote',
            status='scheduled'
        )
        
        print(f"\n📅 예정된 견적 일정: {scheduled_quotes.count()}개")
        for quote in scheduled_quotes:
            print(f"  - {quote.visit_date} {quote.visit_time} - {quote.notes or '메모 없음'}")
        
        # 사용자 확인
        print(f"\n⚠️  won 단계 OpportunityTracking {len(won_opps)}개를 삭제하시겠습니까?")
        print(f"삭제 후에는 예정된 견적에 따라 자동으로 OpportunityTracking이 재생성됩니다.")
        confirm = input("계속하려면 'yes' 입력: ")
        
        if confirm.lower() != 'yes':
            print("\n❌ 취소되었습니다.")
            return
        
        # won 단계 OpportunityTracking 삭제
        deleted_count = 0
        for opp in won_opps:
            opp_id = opp.id
            opp.delete()
            deleted_count += 1
            print(f"🗑️  OpportunityTracking ID {opp_id} 삭제 완료")
        
        print(f"\n✅ won 단계 OpportunityTracking {deleted_count}개 삭제 완료!")
        
        # 남은 OpportunityTracking 확인
        remaining_opps = OpportunityTracking.objects.filter(followup=followup)
        if remaining_opps.exists():
            print(f"\n📊 남은 OpportunityTracking:")
            for opp in remaining_opps:
                print(f"  - ID {opp.id}: {opp.current_stage} 단계")
        else:
            print(f"\n📊 남은 OpportunityTracking: 없음")
            print(f"  → 예정된 견적이 있으므로 시스템이 자동으로 quote 단계 OpportunityTracking을 생성할 수 있습니다.")
        
        print(f"\n{'='*80}")
        print("  완료!")
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
    delete_won_opportunity_169()
