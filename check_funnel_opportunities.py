#!/usr/bin/env python
"""
펀넬 영업기회 카운트 검증 스크립트

목적:
- OpportunityTracking과 실제 Schedule 개수 비교
- 견적 단계의 정확한 카운트 확인
- hana008 등 특정 고객의 견적 개수 확인
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, Schedule, FollowUp, FunnelStage
from django.db.models import Count, Q

def print_separator(title=""):
    """구분선 출력"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'='*80}\n")

def check_quote_stage_counts():
    """견적 단계의 OpportunityTracking vs Schedule 개수 비교"""
    print_separator("1. 견적 단계 카운트 비교")
    
    # 견적 단계의 OpportunityTracking
    quote_opps = OpportunityTracking.objects.filter(current_stage='quote')
    opp_count = quote_opps.count()
    
    print(f"📊 OpportunityTracking 개수 (quote 단계): {opp_count}개")
    
    # 실제 예정된 견적 Schedule 개수
    followup_ids = quote_opps.values_list('followup_id', flat=True)
    scheduled_quotes = Schedule.objects.filter(
        followup_id__in=followup_ids,
        activity_type='quote',
        status='scheduled'
    )
    schedule_count = scheduled_quotes.count()
    
    print(f"📅 Schedule 개수 (예정된 견적): {schedule_count}개")
    print(f"📈 차이: {schedule_count - opp_count}개")
    
    if schedule_count != opp_count:
        print(f"\n⚠️  OpportunityTracking과 Schedule 개수가 다릅니다!")
        print(f"   → 이는 정상입니다. 한 고객에 여러 견적이 있을 수 있습니다.")
    
    return quote_opps, scheduled_quotes

def check_customer_details(quote_opps, scheduled_quotes):
    """고객별 상세 견적 개수 확인"""
    print_separator("2. 고객별 견적 개수 상세")
    
    # FollowUp별 견적 개수 집계
    customer_quote_counts = {}
    
    for opp in quote_opps:
        followup = opp.followup
        customer_key = (
            followup.customer_name,
            followup.company.name if followup.company else '업체명 없음'
        )
        
        # 해당 FollowUp의 예정된 견적 개수
        quote_count = Schedule.objects.filter(
            followup=followup,
            activity_type='quote',
            status='scheduled'
        ).count()
        
        customer_quote_counts[customer_key] = {
            'followup_id': followup.id,
            'quote_count': quote_count,
            'user': followup.user.username,
            'opp_id': opp.id
        }
    
    # 견적이 2개 이상인 고객 출력
    print("🔍 견적이 여러 개인 고객:")
    multi_quote_customers = [(k, v) for k, v in customer_quote_counts.items() if v['quote_count'] > 1]
    
    if multi_quote_customers:
        for (customer_name, company_name), info in sorted(multi_quote_customers, key=lambda x: x[1]['quote_count'], reverse=True):
            print(f"\n  • {customer_name} ({company_name})")
            print(f"    - FollowUp ID: {info['followup_id']}")
            print(f"    - OpportunityTracking ID: {info['opp_id']}")
            print(f"    - 담당자: {info['user']}")
            print(f"    - 예정 견적 개수: {info['quote_count']}개")
            
            # 해당 고객의 견적 스케줄 상세
            quotes = Schedule.objects.filter(
                followup_id=info['followup_id'],
                activity_type='quote',
                status='scheduled'
            ).order_by('visit_date')
            
            for idx, quote in enumerate(quotes, 1):
                print(f"      {idx}. {quote.visit_date} {quote.visit_time.strftime('%H:%M')} - {quote.notes or '메모 없음'}")
    else:
        print("  ✅ 모든 고객이 견적 1개씩 가지고 있습니다.")
    
    # 전체 통계
    total_customers = len(customer_quote_counts)
    total_quotes = sum(v['quote_count'] for v in customer_quote_counts.values())
    
    print(f"\n📊 전체 통계:")
    print(f"  - 견적 단계 고객 수: {total_customers}명")
    print(f"  - 총 예정 견적 수: {total_quotes}개")
    print(f"  - 고객당 평균 견적: {total_quotes / total_customers:.1f}개" if total_customers > 0 else "  - 고객당 평균 견적: 0개")

def check_specific_customer(customer_name_part="hana"):
    """특정 고객 검색 및 상세 정보"""
    print_separator(f"3. 특정 담당자/고객 검색 ('{customer_name_part}' 포함)")
    
    followups = FollowUp.objects.filter(
        Q(customer_name__icontains=customer_name_part) |
        Q(company__name__icontains=customer_name_part) |
        Q(user__username__icontains=customer_name_part)
    ).select_related('company', 'user')
    
    if not followups.exists():
        print(f"⚠️  '{customer_name_part}'을(를) 포함하는 담당자/고객을 찾을 수 없습니다.")
        return
    
    print(f"🔍 검색 결과: {followups.count()}명\n")
    
    for followup in followups:
        print(f"  📇 {followup.customer_name} ({followup.company.name if followup.company else '업체명 없음'})")
        print(f"     - FollowUp ID: {followup.id}")
        print(f"     - 담당자: {followup.user.username}")
        
        # OpportunityTracking 확인
        try:
            opp = OpportunityTracking.objects.get(followup=followup)
            print(f"     - OpportunityTracking: {opp.current_stage} 단계 (ID: {opp.id})")
        except OpportunityTracking.DoesNotExist:
            print(f"     - OpportunityTracking: 없음")
        
        # Schedule 확인
        all_schedules = Schedule.objects.filter(followup=followup).order_by('visit_date')
        quotes = all_schedules.filter(activity_type='quote')
        scheduled_quotes = quotes.filter(status='scheduled')
        
        print(f"     - 전체 일정: {all_schedules.count()}개")
        print(f"     - 견적 일정: {quotes.count()}개")
        print(f"     - 예정 견적: {scheduled_quotes.count()}개")
        
        if scheduled_quotes.exists():
            print(f"     - 예정 견적 상세:")
            for idx, quote in enumerate(scheduled_quotes, 1):
                print(f"       {idx}. [{quote.status}] {quote.visit_date} {quote.visit_time.strftime('%H:%M')} - {quote.notes or '메모 없음'}")
        
        print()

def check_all_stage_counts():
    """모든 펀넬 단계별 개수 확인"""
    print_separator("4. 모든 펀넬 단계별 개수")
    
    stages = FunnelStage.objects.all().order_by('stage_order')
    
    for stage in stages:
        opps = OpportunityTracking.objects.filter(current_stage=stage.name)
        opp_count = opps.count()
        
        print(f"\n🎯 {stage.display_name} ({stage.name})")
        print(f"   OpportunityTracking: {opp_count}개")
        
        # 견적 단계만 Schedule로 카운트
        if stage.name == 'quote':
            followup_ids = opps.values_list('followup_id', flat=True)
            schedule_count = Schedule.objects.filter(
                followup_id__in=followup_ids,
                activity_type='quote',
                status='scheduled'
            ).count()
            print(f"   예정 견적 Schedule: {schedule_count}개")
            if schedule_count != opp_count:
                print(f"   ⚠️  차이: {schedule_count - opp_count}개")

def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print("  펀넬 영업기회 카운트 검증 스크립트")
    print("="*80)
    
    try:
        # 1. 견적 단계 카운트 비교
        quote_opps, scheduled_quotes = check_quote_stage_counts()
        
        # 2. 고객별 상세
        check_customer_details(quote_opps, scheduled_quotes)
        
        # 3. 특정 고객 검색 (hana로 시작하는 고객)
        check_specific_customer("hana")
        
        # 4. 모든 단계 확인
        check_all_stage_counts()
        
        print_separator("검증 완료")
        print("✅ 스크립트 실행 완료\n")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
