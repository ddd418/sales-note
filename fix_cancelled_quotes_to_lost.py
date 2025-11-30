"""
취소된 견적의 영업기회를 실주(lost)로 변경하는 스크립트

견적(quote) 일정이 취소(cancelled)되었으면 해당 영업기회는 실주(lost)로 처리되어야 함
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking
from django.db.models import Q


def fix_cancelled_quotes():
    """취소된 견적의 영업기회를 실주로 변경"""
    
    # 취소된 견적 일정 조회
    cancelled_quotes = Schedule.objects.filter(
        activity_type='quote',
        status='cancelled',
        followup__isnull=False
    ).select_related('followup', 'user')
    
    print(f"=== 취소된 견적 일정: {cancelled_quotes.count()}건 ===\n")
    
    fixed_count = 0
    already_lost_count = 0
    no_opportunity_count = 0
    
    for schedule in cancelled_quotes:
        followup = schedule.followup
        user = schedule.user
        
        # 해당 FollowUp의 영업기회 조회
        opportunities = followup.opportunities.all()
        
        if not opportunities.exists():
            print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 영업기회 없음")
            no_opportunity_count += 1
            continue
        
        for opp in opportunities:
            if opp.current_stage == 'lost':
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 이미 실주")
                already_lost_count += 1
            elif opp.current_stage != 'won':  # 수주 완료된 건은 제외
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - {opp.current_stage} → lost 변경")
                opp.update_stage('lost')
                fixed_count += 1
            else:
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 수주 완료(변경 안함)")
    
    print(f"\n=== 결과 ===")
    print(f"실주로 변경: {fixed_count}건")
    print(f"이미 실주: {already_lost_count}건")
    print(f"영업기회 없음: {no_opportunity_count}건")
    
    return fixed_count


def check_user_opportunities(username):
    """특정 사용자의 영업기회 현황 확인"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"사용자 '{username}' 없음")
        return
    
    print(f"\n=== {username} 영업기회 현황 ===\n")
    
    opps = OpportunityTracking.objects.filter(
        followup__user=user
    ).select_related('followup', 'followup__company')
    
    stage_counts = {}
    for opp in opps:
        stage = opp.current_stage
        if stage not in stage_counts:
            stage_counts[stage] = []
        stage_counts[stage].append(opp)
    
    for stage, opp_list in sorted(stage_counts.items()):
        print(f"\n[{stage}] {len(opp_list)}건:")
        for opp in opp_list:
            company = opp.followup.company.name if opp.followup.company else '업체명 없음'
            customer = opp.followup.customer_name or '고객명 없음'
            print(f"  - ID {opp.id}: {company} / {customer} (예상매출: {opp.expected_revenue:,}원)")
    
    # 취소된 견적 확인
    print(f"\n=== {username} 취소된 견적 일정 ===")
    cancelled = Schedule.objects.filter(
        user=user,
        activity_type='quote',
        status='cancelled'
    ).select_related('followup')
    
    for s in cancelled:
        customer = s.followup.customer_name if s.followup else '없음'
        print(f"  - 일정 #{s.id}: {customer} (날짜: {s.visit_date})")


if __name__ == '__main__':
    # 특정 사용자 확인
    check_user_opportunities('dkswogus95')
    
    print("\n" + "="*50)
    print("취소된 견적을 실주로 변경하시겠습니까?")
    print("실행: fix_cancelled_quotes()")
