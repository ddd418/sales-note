#!/usr/bin/env python
"""
고객명 중복 확인 스크립트
- 같은 회사 내에서 중복되는 고객명 출력
- 전체 시스템에서 동일한 고객명 확인
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.db.models import Count
from reporting.models import FollowUp


def check_duplicate_customers():
    print("=" * 60)
    print("고객명 중복 확인 스크립트")
    print("=" * 60)
    
    # 1. 전체 시스템에서 동일한 고객명 찾기
    print("\n[1] 전체 시스템에서 중복되는 고객명")
    print("-" * 60)
    
    duplicates = (
        FollowUp.objects
        .values('customer_name')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    
    if duplicates:
        for dup in duplicates:
            print(f"\n고객명: '{dup['customer_name']}' ({dup['count']}명)")
            
            # 해당 고객명의 상세 정보 출력
            customers = FollowUp.objects.filter(customer_name=dup['customer_name']).select_related('company', 'department', 'user')
            for c in customers:
                company = c.company.name if c.company else '미지정'
                dept = c.department.name if c.department else '미지정'
                user = c.user.username if c.user else '미지정'
                print(f"  - ID:{c.id} | 업체:{company} | 부서:{dept} | 담당자:{user}")
    else:
        print("중복되는 고객명이 없습니다.")
    
    # 2. 같은 업체 내에서 중복되는 고객명 찾기
    print("\n\n[2] 같은 업체 내에서 중복되는 고객명")
    print("-" * 60)
    
    company_duplicates = (
        FollowUp.objects
        .values('company__name', 'customer_name')
        .annotate(count=Count('id'))
        .filter(count__gt=1, company__isnull=False)
        .order_by('company__name', '-count')
    )
    
    if company_duplicates:
        current_company = None
        for dup in company_duplicates:
            if current_company != dup['company__name']:
                current_company = dup['company__name']
                print(f"\n[업체: {current_company}]")
            
            print(f"  고객명: '{dup['customer_name']}' ({dup['count']}명)")
            
            # 상세 정보
            customers = FollowUp.objects.filter(
                company__name=dup['company__name'],
                customer_name=dup['customer_name']
            ).select_related('department', 'user')
            for c in customers:
                dept = c.department.name if c.department else '미지정'
                user = c.user.username if c.user else '미지정'
                print(f"    - ID:{c.id} | 부서:{dept} | 담당자:{user}")
    else:
        print("같은 업체 내에서 중복되는 고객명이 없습니다.")
    
    # 3. 같은 담당자가 추가한 중복 고객명
    print("\n\n[3] 같은 담당자가 추가한 중복 고객명")
    print("-" * 60)
    
    user_duplicates = (
        FollowUp.objects
        .values('user__username', 'customer_name')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('user__username', '-count')
    )
    
    if user_duplicates:
        current_user = None
        for dup in user_duplicates:
            if current_user != dup['user__username']:
                current_user = dup['user__username']
                print(f"\n[담당자: {current_user}]")
            
            print(f"  고객명: '{dup['customer_name']}' ({dup['count']}명)")
            
            # 상세 정보
            customers = FollowUp.objects.filter(
                user__username=dup['user__username'],
                customer_name=dup['customer_name']
            ).select_related('company', 'department')
            for c in customers:
                company = c.company.name if c.company else '미지정'
                dept = c.department.name if c.department else '미지정'
                print(f"    - ID:{c.id} | 업체:{company} | 부서:{dept}")
    else:
        print("같은 담당자가 추가한 중복 고객명이 없습니다.")
    
    # 통계
    print("\n\n[통계]")
    print("-" * 60)
    total_customers = FollowUp.objects.count()
    unique_names = FollowUp.objects.values('customer_name').distinct().count()
    print(f"총 고객 수: {total_customers}명")
    print(f"고유 고객명 수: {unique_names}개")
    print(f"중복 가능성: {total_customers - unique_names}건")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    check_duplicate_customers()
