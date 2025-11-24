"""
수주 완료된 일정이 있는데 펀넬이 수주 상태가 아닌 영업기회를 자동으로 동기화하는 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import OpportunityTracking, Schedule
from django.utils import timezone

def sync_won_opportunities():
    """수주 완료된 일정이 있는 영업기회를 수주 상태로 변경"""
    
    # 수주 상태가 아닌 영업기회 중에서 수주 완료된 일정이 있는 것들 찾기
    opportunities = OpportunityTracking.objects.exclude(current_stage='won')
    
    total = opportunities.count()
    print(f"총 {total}개의 영업기회를 확인합니다...\n")
    
    updated_count = 0
    skipped_count = 0
    
    for opp in opportunities:
        # 해당 팔로우업의 수주 완료된 일정 찾기
        won_schedules = Schedule.objects.filter(
            followup=opp.followup,
            activity_type='won',  # 수주 일정
            status='completed'  # 완료된 상태
        ).order_by('visit_date')
        
        if won_schedules.exists():
            # 수주 완료된 일정이 있으면 영업기회를 수주 상태로 변경
            latest_won = won_schedules.last()
            
            # 실제 매출액 계산 (수주 일정의 금액 또는 예상 매출액)
            if latest_won.amount and latest_won.amount > 0:
                actual_revenue = latest_won.amount
            else:
                actual_revenue = opp.expected_revenue
            
            # 백로그 금액 (실제 매출액과 동일하게 설정)
            backlog_amount = actual_revenue
            
            # 상태 업데이트
            old_stage = opp.current_stage
            opp.current_stage = 'won'
            opp.probability = 100
            opp.actual_revenue = actual_revenue
            opp.backlog_amount = backlog_amount
            opp.won_date = latest_won.visit_date
            opp.save()
            
            updated_count += 1
            print(f"[{updated_count}] ✓ {opp.followup.customer_name or '고객명 미정'}")
            print(f"   - 단계: {old_stage} → won")
            print(f"   - 수주일: {latest_won.visit_date}")
            print(f"   - 매출액: {actual_revenue:,}원")
            print()
        else:
            skipped_count += 1
    
    print(f"\n{'='*50}")
    print(f"완료: {updated_count}건 수주로 변경, {skipped_count}건 변경 없음")
    print(f"{'='*50}\n")
    
    if updated_count > 0:
        print("✓ 수주 완료된 일정과 펀넬 상태가 동기화되었습니다.")
    else:
        print("✓ 동기화가 필요한 영업기회가 없습니다.")

if __name__ == '__main__':
    sync_won_opportunities()
