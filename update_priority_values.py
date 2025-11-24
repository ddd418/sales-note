"""
기존 우선순위 값을 새로운 값으로 변환하는 스크립트
한달 -> 긴급 (urgent)
세달 -> 팔로업 (followup)  
장기 -> 예정 (scheduled)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import FollowUp

def update_priority_values():
    """기존 우선순위 값을 새 값으로 변환"""
    
    # 변환 매핑
    mapping = {
        'one_month': 'urgent',      # 한달 -> 긴급
        'three_months': 'followup',  # 세달 -> 팔로업
        'long_term': 'scheduled',    # 장기 -> 예정
    }
    
    total_updated = 0
    
    for old_value, new_value in mapping.items():
        count = FollowUp.objects.filter(priority=old_value).update(priority=new_value)
        if count > 0:
            print(f"'{old_value}' -> '{new_value}': {count}건 업데이트")
            total_updated += count
    
    print(f"\n총 {total_updated}건의 우선순위가 업데이트되었습니다.")
    
    # 업데이트 후 통계
    from django.db.models import Count
    priority_stats = FollowUp.objects.values('priority').annotate(count=Count('id')).order_by('-count')
    
    print("\n=== 우선순위별 통계 ===")
    priority_display = {
        'urgent': '긴급',
        'followup': '팔로업',
        'scheduled': '예정'
    }
    for stat in priority_stats:
        display_name = priority_display.get(stat['priority'], stat['priority'])
        print(f"{display_name}: {stat['count']}건")

if __name__ == '__main__':
    update_priority_values()
