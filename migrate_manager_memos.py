#!/usr/bin/env python
"""
기존 매니저 메모를 새로운 parent_history 구조로 마이그레이션하는 스크립트

사용법:
python migrate_manager_memos.py

작업 내용:
1. [매니저 메모 - username] 형태의 메모를 찾아서
2. 같은 스케줄/팔로우업과 연관된 다른 히스토리를 부모로 연결
3. content에서 [매니저 메모 - username] 부분 제거
"""

import os
import sys
import django
import re
from django.db import transaction

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import History

def migrate_manager_memos():
    """매니저 메모 마이그레이션 실행"""
    
    print("=== 기존 매니저 메모 마이그레이션 시작 ===")
    
    # 1. [매니저 메모 - username] 형태의 메모 찾기
    manager_memo_pattern = r'^\[매니저 메모 - [^\]]+\]\s*'
    
    manager_memos = History.objects.filter(
        action_type='memo',
        content__icontains='[매니저 메모 -',
        parent_history__isnull=True  # 아직 마이그레이션 안 된 것만
    )
    
    total_memos = manager_memos.count()
    print(f"마이그레이션할 매니저 메모: {total_memos}개")
    
    if total_memos == 0:
        print("마이그레이션할 매니저 메모가 없습니다.")
        return
    
    migrated_count = 0
    failed_count = 0
    
    with transaction.atomic():
        for memo in manager_memos:
            try:
                # 부모 히스토리 찾기 로직
                parent_history = find_parent_history(memo)
                
                if parent_history:
                    # parent_history 설정
                    memo.parent_history = parent_history
                    
                    # content에서 [매니저 메모 - username] 부분 제거
                    cleaned_content = re.sub(manager_memo_pattern, '', memo.content).strip()
                    memo.content = cleaned_content
                    
                    memo.save()
                    
                    print(f"✓ 매니저 메모 ID {memo.id} -> 부모 히스토리 ID {parent_history.id}")
                    migrated_count += 1
                else:
                    print(f"✗ 매니저 메모 ID {memo.id}: 적절한 부모 히스토리를 찾을 수 없음")
                    failed_count += 1
                    
            except Exception as e:
                print(f"✗ 매니저 메모 ID {memo.id} 마이그레이션 실패: {e}")
                failed_count += 1
    
    print(f"\n=== 마이그레이션 완료 ===")
    print(f"성공: {migrated_count}개")
    print(f"실패: {failed_count}개")
    print(f"전체: {total_memos}개")

def find_parent_history(memo):
    """매니저 메모에 대한 적절한 부모 히스토리 찾기"""
    
    # 1. 같은 스케줄에 연결된 다른 히스토리 찾기
    if memo.schedule:
        parent_candidates = History.objects.filter(
            schedule=memo.schedule,
            parent_history__isnull=True,  # 부모 히스토리가 아닌 것
            action_type__in=['customer_meeting', 'delivery_schedule', 'service']  # 실제 활동
        ).exclude(id=memo.id).order_by('-created_at')
        
        if parent_candidates.exists():
            return parent_candidates.first()
    
    # 2. 같은 팔로우업의 최근 히스토리 찾기
    if memo.followup:
        parent_candidates = History.objects.filter(
            followup=memo.followup,
            user=memo.user,  # 같은 실무자
            parent_history__isnull=True,
            action_type__in=['customer_meeting', 'delivery_schedule', 'service']
        ).exclude(id=memo.id).order_by('-created_at')
        
        if parent_candidates.exists():
            return parent_candidates.first()
    
    # 3. 같은 사용자의 최근 히스토리 찾기 (시간 기준)
    parent_candidates = History.objects.filter(
        user=memo.user,
        parent_history__isnull=True,
        action_type__in=['customer_meeting', 'delivery_schedule', 'service'],
        created_at__lt=memo.created_at  # 메모보다 이전에 생성된 것
    ).exclude(id=memo.id).order_by('-created_at')
    
    if parent_candidates.exists():
        return parent_candidates.first()
    
    return None

def test_migration():
    """마이그레이션 테스트 (실제 변경 없이 시뮬레이션)"""
    
    print("=== 매니저 메모 마이그레이션 테스트 ===")
    
    manager_memo_pattern = r'^\[매니저 메모 - [^\]]+\]\s*'
    
    manager_memos = History.objects.filter(
        action_type='memo',
        content__icontains='[매니저 메모 -',
        parent_history__isnull=True
    )
    
    total_memos = manager_memos.count()
    print(f"테스트할 매니저 메모: {total_memos}개")
    
    can_migrate = 0
    cannot_migrate = 0
    
    for memo in manager_memos:
        parent_history = find_parent_history(memo)
        
        if parent_history:
            cleaned_content = re.sub(manager_memo_pattern, '', memo.content).strip()
            print(f"✓ 매니저 메모 ID {memo.id} -> 부모 히스토리 ID {parent_history.id}")
            print(f"  원본 내용: {memo.content[:50]}...")
            print(f"  정리된 내용: {cleaned_content[:50]}...")
            can_migrate += 1
        else:
            print(f"✗ 매니저 메모 ID {memo.id}: 적절한 부모 히스토리를 찾을 수 없음")
            cannot_migrate += 1
    
    print(f"\n테스트 결과:")
    print(f"마이그레이션 가능: {can_migrate}개")
    print(f"마이그레이션 불가능: {cannot_migrate}개")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_migration()
    else:
        confirm = input("매니저 메모 마이그레이션을 실행하시겠습니까? (y/N): ")
        if confirm.lower() == 'y':
            migrate_manager_memos()
        else:
            print("마이그레이션이 취소되었습니다.")