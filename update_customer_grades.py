"""
기존 고객들의 AI 등급을 일괄 계산하는 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import FollowUp

def update_all_customer_grades():
    """모든 고객의 등급을 재계산"""
    followups = FollowUp.objects.all()
    total = followups.count()
    
    print(f"총 {total}개 고객의 등급을 계산합니다...")
    
    success_count = 0
    error_count = 0
    
    for i, followup in enumerate(followups, 1):
        try:
            result = followup.calculate_customer_grade()
            success_count += 1
            print(f"[{i}/{total}] {followup.customer_name or '고객명 미정'} - 등급: {result['grade']}, 점수: {result['score']}")
        except Exception as e:
            error_count += 1
            print(f"[{i}/{total}] 오류: {followup.customer_name or '고객명 미정'} - {e}")
    
    print(f"\n완료: 성공 {success_count}건, 실패 {error_count}건")
    
    # 등급별 통계
    from django.db.models import Count
    grade_stats = FollowUp.objects.values('customer_grade').annotate(count=Count('id')).order_by('-count')
    
    print("\n=== 등급별 통계 ===")
    for stat in grade_stats:
        print(f"{stat['customer_grade']}: {stat['count']}명")

if __name__ == '__main__':
    update_all_customer_grades()
