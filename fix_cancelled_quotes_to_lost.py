"""
취소된 견적의 영업기회를 실주(lost)로 변경하는 스크립트

견적(quote) 일정이 취소(cancelled)되었으면 해당 영업기회는 실주(lost)로 처리되어야 함

사용법:
railway shell -s sales-note
/opt/venv/bin/python manage.py shell -c "from fix_cancelled_quotes_to_lost import fix_cancelled_quotes; fix_cancelled_quotes()"
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import Schedule, OpportunityTracking


def fix_cancelled_quotes():
    """취소된 견적의 영업기회를 실주로 변경"""
    
    # 취소된 견적 일정 조회
    cancelled_quotes = Schedule.objects.filter(
        activity_type='quote',
        status='cancelled',
        followup__isnull=False
    ).select_related('followup', 'user', 'opportunity')
    
    print(f"=== 취소된 견적 일정: {cancelled_quotes.count()}건 ===\n")
    
    fixed_count = 0
    already_lost_count = 0
    no_opportunity_count = 0
    won_skip_count = 0
    
    for schedule in cancelled_quotes:
        followup = schedule.followup
        user = schedule.user
        
        # 1. 일정에 직접 연결된 영업기회 확인
        if schedule.opportunity:
            opp = schedule.opportunity
            if opp.current_stage == 'lost':
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 이미 실주")
                already_lost_count += 1
            elif opp.current_stage == 'won':
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 수주 완료(변경 안함)")
                won_skip_count += 1
            else:
                print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - {opp.current_stage} → lost 변경")
                opp.update_stage('lost')
                fixed_count += 1
            continue
        
        # 2. FollowUp에 연결된 영업기회 중 quote 단계 찾기
        quote_opps = followup.opportunities.filter(current_stage='quote').order_by('-created_at')
        if quote_opps.exists():
            opp = quote_opps.first()
            print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - quote → lost 변경")
            opp.update_stage('lost')
            fixed_count += 1
            continue
        
        # 3. FollowUp에 연결된 영업기회 중 이미 lost인 것 확인
        lost_opps = followup.opportunities.filter(current_stage='lost')
        if lost_opps.exists():
            print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 이미 실주")
            already_lost_count += 1
            continue
        
        # 4. won 제외한 다른 단계 영업기회 찾기
        other_opps = followup.opportunities.exclude(current_stage__in=['won', 'lost']).order_by('-created_at')
        if other_opps.exists():
            opp = other_opps.first()
            print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - {opp.current_stage} → lost 변경")
            opp.update_stage('lost')
            fixed_count += 1
            continue
        
        # 5. 영업기회 없음
        print(f"[{user.username}] 일정 #{schedule.id} '{followup.customer_name}' - 영업기회 없음")
        no_opportunity_count += 1
    
    print(f"\n{'='*50}")
    print(f"=== 결과 ===")
    print(f"실주로 변경: {fixed_count}건")
    print(f"이미 실주: {already_lost_count}건")
    print(f"수주 완료(변경 안함): {won_skip_count}건")
    print(f"영업기회 없음: {no_opportunity_count}건")
    
    return fixed_count


def check_user_lost(username):
    """특정 사용자의 실주 현황 확인"""
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"사용자 '{username}' 없음")
        return
    
    print(f"\n=== {username} 실주(lost) 현황 ===\n")
    
    lost_opps = OpportunityTracking.objects.filter(
        followup__user=user,
        current_stage='lost'
    ).select_related('followup', 'followup__company')
    
    print(f"실주 건수: {lost_opps.count()}건\n")
    
    for opp in lost_opps:
        company = opp.followup.company.name if opp.followup.company else '업체명 없음'
        customer = opp.followup.customer_name or '고객명 없음'
        print(f"  - ID {opp.id}: {company} / {customer} (예상매출: {opp.expected_revenue:,}원)")


if __name__ == '__main__':
    print("사용법:")
    print("1. 취소된 견적을 실주로 변경: fix_cancelled_quotes()")
    print("2. 특정 사용자 실주 확인: check_user_lost('username')")
    print("")
    print("예시:")
    print("  from fix_cancelled_quotes_to_lost import fix_cancelled_quotes, check_user_lost")
    print("  fix_cancelled_quotes()")
    print("  check_user_lost('dkswogus95')")
