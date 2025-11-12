#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실무자 대시보드 차트에 History DeliveryItem 포함 수정 스크립트
"""

def fix_salesman_customer_distribution():
    """실무자 대시보드 3️⃣ 고객사별 매출 비중 수정"""
    with open('reporting/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Line 1225부터 시작하는 3️⃣ 섹션 찾기
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if '# 3️⃣ 고객사별 매출 비중 (Top 5 + 기타) - Schedule 기준' in line and i < 2000:
            start_idx = i
        if start_idx is not None and '# 4️⃣' in line:
            end_idx = i
            break
    
    if start_idx is None:
        print("❌ 실무자 대시보드 3️⃣ 섹션을 찾을 수 없습니다.")
        return False
    
    print(f"✅ 실무자 대시보드 3️⃣ 섹션 찾음: lines {start_idx+1} ~ {end_idx}")
    
    # 새로운 코드로 교체
    new_code = '''    # 3️⃣ 고객사별 매출 비중 (Top 5 + 기타) - Schedule + History 기준
    # Schedule 기반 매출
    schedule_top_customers = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # History 기반 매출
    histories_current_year_with_company = histories_current_year.filter(
        followup__isnull=False,
        followup__company__isnull=False
    )
    
    history_top_customers = DeliveryItem.objects.filter(
        history__in=histories_current_year_with_company
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price')
    )
    
    # 고객사별 매출 합산
    from collections import defaultdict
    company_revenue = defaultdict(float)
    
    for item in schedule_top_customers:
        company_name = item['schedule__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    for item in history_top_customers:
        company_name = item['history__followup__company__name'] or '미정'
        company_revenue[company_name] += float(item['total_revenue'])
    
    # 상위 5개 추출
    sorted_companies = sorted(company_revenue.items(), key=lambda x: x[1], reverse=True)[:5]
    
    customer_distribution = {
        'labels': [],
        'data': []
    }
    
    total_top5_revenue = 0
    for company_name, revenue in sorted_companies:
        customer_distribution['labels'].append(company_name)
        customer_distribution['data'].append(revenue)
        total_top5_revenue += revenue
    
    # 기타 금액 계산 - Schedule + History 합산
    schedule_total = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    history_total = DeliveryItem.objects.filter(
        history__in=histories_current_year
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    total_all_revenue = float(schedule_total) + float(history_total)
    other_revenue = total_all_revenue - total_top5_revenue
    if other_revenue > 0:
        customer_distribution['labels'].append('기타')
        customer_distribution['data'].append(other_revenue)

'''
    
    # 교체
    new_lines = lines[:start_idx] + [new_code] + lines[end_idx:]
    
    with open('reporting/views.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ 실무자 대시보드 3️⃣ 섹션 수정 완료")
    return True


def fix_salesman_customer_type_stats():
    """실무자 대시보드 6️⃣ 고객 유형별 통계 수정"""
    with open('reporting/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Line 1330 근처에서 6️⃣ 섹션 찾기
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if '# 6️⃣ 고객 유형별 통계 (대학/기업/관공서) - Schedule 기준' in line and i < 2000:
            start_idx = i
        if start_idx is not None and '# 7️⃣' in line:
            end_idx = i
            break
    
    if start_idx is None:
        print("❌ 실무자 대시보드 6️⃣ 섹션을 찾을 수 없습니다.")
        return False
    
    print(f"✅ 실무자 대시보드 6️⃣ 섹션 찾음: lines {start_idx+1} ~ {end_idx}")
    
    # 새로운 코드로 교체
    new_code = '''    # 6️⃣ 고객 유형별 통계 (대학/기업/관공서) - Schedule + History 기준
    customer_type_stats = {
        'labels': ['대학', '기업', '관공서'],
        'revenue': [0, 0, 0],
        'count': [0, 0, 0]
    }
    
    # Schedule 기반 통계
    schedule_company_stats = DeliveryItem.objects.filter(
        schedule__in=schedules_current_year,
        schedule__status__in=['scheduled', 'completed'],  # 취소된 일정 제외
        schedule__followup__isnull=False,
        schedule__followup__company__isnull=False
    ).values('schedule__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    for item in schedule_company_stats:
        company_name = item['schedule__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt
    
    # History 기반 통계
    history_company_stats = DeliveryItem.objects.filter(
        history__in=histories_current_year,
        history__followup__isnull=False,
        history__followup__company__isnull=False
    ).values('history__followup__company__name').annotate(
        total_revenue=Sum('total_price'),
        count=Count('id')
    )
    
    for item in history_company_stats:
        company_name = item['history__followup__company__name'] or ''
        revenue = float(item['total_revenue']) / 1000000  # 백만원 단위
        cnt = item['count']
        
        if '대학' in company_name or '대학교' in company_name:
            customer_type_stats['revenue'][0] += revenue
            customer_type_stats['count'][0] += cnt
        elif '청' in company_name or '부' in company_name or '시' in company_name or '구' in company_name:
            customer_type_stats['revenue'][2] += revenue
            customer_type_stats['count'][2] += cnt
        else:
            customer_type_stats['revenue'][1] += revenue
            customer_type_stats['count'][1] += cnt

'''
    
    # 교체
    new_lines = lines[:start_idx] + [new_code] + lines[end_idx:]
    
    with open('reporting/views.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ 실무자 대시보드 6️⃣ 섹션 수정 완료")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("실무자 대시보드 차트 수정 시작")
    print("=" * 60)
    
    if fix_salesman_customer_distribution():
        print("\n3️⃣ 고객사별 매출 비중: Schedule + History 포함 ✅")
    
    if fix_salesman_customer_type_stats():
        print("\n6️⃣ 고객 유형별 통계: Schedule + History 포함 ✅")
    
    print("\n" + "=" * 60)
    print("✅ 실무자 대시보드 차트 수정 완료!")
    print("=" * 60)
