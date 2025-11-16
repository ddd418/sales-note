#!/usr/bin/env python
"""
FollowUp 169 (심윤지)가 펀넬에 표시되지 않는 원인 분석 스크립트
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, FollowUp, Schedule, FunnelStage
from reporting.funnel_analytics import FunnelAnalytics

def analyze_followup_169():
    """FollowUp 169의 펀넬 표시 여부 분석"""
    
    print("="*80)
    print("  FollowUp 169 (심윤지) 펀넬 표시 원인 분석")
    print("="*80)
    
    try:
        # 1. FollowUp 조회
        followup = FollowUp.objects.get(id=169)
        print(f"\n[1] FollowUp 정보")
        print(f"  - ID: {followup.id}")
        print(f"  - 고객명: {followup.customer_name}")
        print(f"  - 업체: {followup.company.name if followup.company else '없음'}")
        print(f"  - 담당자: {followup.user.username}")
        
        # 2. OpportunityTracking 조회
        opps = OpportunityTracking.objects.filter(followup=followup)
        print(f"\n[2] OpportunityTracking 조회")
        print(f"  - 개수: {opps.count()}개")
        
        if opps.exists():
            for opp in opps:
                print(f"\n  OpportunityTracking ID: {opp.id}")
                print(f"  - current_stage: '{opp.current_stage}'")
                print(f"  - 단계 표시명: {opp.get_current_stage_display()}")
                print(f"  - 확률: {opp.probability}%")
                print(f"  - 예상 매출: {opp.expected_revenue:,}원")
                print(f"  - 생성일: {opp.created_at}")
        else:
            print("  ⚠️ OpportunityTracking이 없습니다!")
        
        # 3. Schedule 조회
        print(f"\n[3] Schedule 조회")
        all_schedules = Schedule.objects.filter(followup=followup).order_by('visit_date')
        print(f"  - 전체 일정: {all_schedules.count()}개")
        
        quote_schedules = all_schedules.filter(activity_type='quote')
        print(f"  - 견적 일정: {quote_schedules.count()}개")
        
        scheduled_quotes = quote_schedules.filter(status='scheduled')
        print(f"  - 예정된 견적: {scheduled_quotes.count()}개")
        
        if scheduled_quotes.exists():
            print(f"\n  📅 예정된 견적 상세:")
            for quote in scheduled_quotes:
                print(f"    - ID: {quote.id}")
                print(f"      날짜: {quote.visit_date} {quote.visit_time}")
                print(f"      activity_type: '{quote.activity_type}'")
                print(f"      status: '{quote.status}'")
                print(f"      user: {quote.user.username}")
                print(f"      메모: {quote.notes or '없음'}")
        
        # 4. 펀넬 견적 단계 분석
        print(f"\n[4] 펀넬 견적 단계 분석")
        print(f"\n  4-1. quote 단계 OpportunityTracking 조회:")
        quote_opps = OpportunityTracking.objects.filter(current_stage='quote')
        print(f"    - 전체: {quote_opps.count()}개")
        
        # FollowUp 169가 포함되는지 확인
        followup_169_in_quote = quote_opps.filter(followup_id=169).exists()
        print(f"    - FollowUp 169 포함 여부: {followup_169_in_quote}")
        
        print(f"\n  4-2. funnel_analytics.py의 get_stage_breakdown 로직 시뮬레이션:")
        
        # quote 단계 가져오기
        try:
            quote_stage = FunnelStage.objects.get(name='quote')
            print(f"    - FunnelStage 'quote' 찾음: {quote_stage.display_name}")
        except FunnelStage.DoesNotExist:
            print(f"    ❌ FunnelStage 'quote'를 찾을 수 없습니다!")
            return
        
        # 현재 코드 로직 재현
        opps_in_quote_stage = OpportunityTracking.objects.filter(current_stage='quote')
        print(f"    - OpportunityTracking (quote 단계): {opps_in_quote_stage.count()}개")
        
        followup_ids = opps_in_quote_stage.values_list('followup_id', flat=True)
        print(f"    - FollowUp IDs: {list(followup_ids)}")
        print(f"    - FollowUp 169 포함?: {169 in followup_ids}")
        
        schedule_count = Schedule.objects.filter(
            followup_id__in=followup_ids,
            activity_type='quote',
            status='scheduled'
        ).count()
        print(f"    - 예정된 견적 Schedule (해당 FollowUp들): {schedule_count}개")
        
        actual_count = schedule_count if schedule_count > 0 else opps_in_quote_stage.count()
        print(f"    - 최종 카운트 (actual_count): {actual_count}개")
        
        # 5. 문제 진단
        print(f"\n[5] 문제 진단")
        
        if not opps.exists():
            print(f"  ❌ 문제: OpportunityTracking이 존재하지 않습니다!")
            print(f"     → 해결: OpportunityTracking을 생성해야 합니다.")
        elif opps.exists() and not opps.filter(current_stage='quote').exists():
            current_stage = opps.first().current_stage
            print(f"  ❌ 문제: OpportunityTracking의 current_stage가 '{current_stage}'입니다!")
            print(f"     → get_stage_breakdown은 current_stage='quote'인 것만 찾습니다.")
            print(f"     → 예정된 견적이 있지만 OpportunityTracking 단계가 달라서 제외됩니다.")
            print(f"\n  💡 해결 방법:")
            print(f"     1. OpportunityTracking의 current_stage를 'quote'로 변경")
            print(f"     2. 또는 funnel_analytics.py 로직을 수정하여")
            print(f"        OpportunityTracking 단계와 무관하게 예정된 견적 Schedule 모두 포함")
        else:
            print(f"  ✅ OpportunityTracking이 quote 단계에 있습니다.")
            print(f"     → 펀넬에 정상적으로 표시되어야 합니다.")
        
        # 6. 실제 펀넬 API 호출 결과
        print(f"\n[6] 실제 FunnelAnalytics.get_stage_breakdown() 호출")
        breakdown = FunnelAnalytics.get_stage_breakdown(user=followup.user)
        
        quote_stage_data = None
        for stage_data in breakdown:
            if stage_data['stage_code'] == 'quote':
                quote_stage_data = stage_data
                break
        
        if quote_stage_data:
            print(f"  견적 단계 데이터:")
            print(f"    - count: {quote_stage_data['count']}")
            print(f"    - total_value: {quote_stage_data['total_value']:,}원")
        else:
            print(f"  ❌ 견적 단계 데이터를 찾을 수 없습니다!")
        
        print(f"\n{'='*80}")
        print("  분석 완료")
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
    analyze_followup_169()
