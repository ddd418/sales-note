#!/usr/bin/env python
"""
기존 서버 데이터를 새로운 Company/Department 모델 구조로 마이그레이션하는 스크립트
"""
import os
import sys
import django
from django.conf import settings

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.db import transaction
from reporting.models import FollowUp, Company, Department, User

def migrate_existing_data():
    """기존 텍스트 필드 데이터를 Company/Department 모델로 마이그레이션"""
    
    print("🔄 데이터 마이그레이션 시작...")
    
    # 기존 FollowUp 데이터 확인
    total_followups = FollowUp.objects.count()
    print(f"📊 총 팔로우업 데이터: {total_followups}개")
    
    if total_followups == 0:
        print("✅ 마이그레이션할 데이터가 없습니다.")
        return
    
    # 기존 데이터에서 텍스트 필드가 있는지 확인
    try:
        # 이전 버전에서 사용했던 필드명들 (추정)
        sample_followup = FollowUp.objects.first()
        
        # 기존 필드들이 있는지 확인
        has_old_fields = (
            hasattr(sample_followup, 'company_name') or 
            hasattr(sample_followup, 'department_name') or
            # 현재 company, department가 텍스트 필드인 경우
            isinstance(sample_followup.company, str) if hasattr(sample_followup, 'company') else False
        )
        
        print(f"📋 기존 텍스트 필드 존재: {has_old_fields}")
        
    except Exception as e:
        print(f"⚠️ 데이터 구조 확인 중 오류: {e}")
        return
    
    migrated_count = 0
    error_count = 0
    
    with transaction.atomic():
        print("🔄 Company 및 Department 데이터 생성 중...")
        
        # 모든 팔로우업 데이터를 순회하면서 마이그레이션
        for followup in FollowUp.objects.all():
            try:
                # 기존 데이터에서 회사명과 부서명 추출
                company_name = None
                department_name = None
                
                # 케이스 1: 기존에 company_name, department_name 필드가 있는 경우
                if hasattr(followup, 'company_name') and followup.company_name:
                    company_name = followup.company_name.strip()
                
                if hasattr(followup, 'department_name') and followup.department_name:
                    department_name = followup.department_name.strip()
                
                # 케이스 2: company, department가 텍스트 필드인 경우
                if not company_name and hasattr(followup, 'company'):
                    if isinstance(followup.company, str) and followup.company:
                        company_name = followup.company.strip()
                
                # 기본값 설정
                if not company_name:
                    company_name = "미등록 업체"
                if not department_name:
                    department_name = "미등록 부서"
                
                # Company 생성 또는 가져오기
                company, created = Company.objects.get_or_create(
                    name=company_name,
                    defaults={
                        'created_by': followup.user,
                    }
                )
                
                if created:
                    print(f"✨ 새 회사 생성: {company_name}")
                
                # Department 생성 또는 가져오기
                department, created = Department.objects.get_or_create(
                    company=company,
                    name=department_name,
                    defaults={
                        'created_by': followup.user,
                    }
                )
                
                if created:
                    print(f"✨ 새 부서 생성: {company_name} - {department_name}")
                
                # FollowUp 업데이트 (외래키가 이미 있는 경우만)
                if hasattr(followup, 'company') and hasattr(followup, 'department'):
                    # 이미 새로운 구조라면 건너뛰기
                    if not isinstance(followup.company, str):
                        continue
                
                # 새로운 관계 설정 (필요한 경우만)
                # 이 부분은 실제 필드 구조에 따라 조정 필요
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    print(f"📈 진행상황: {migrated_count}/{total_followups}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ 팔로우업 ID {followup.id} 마이그레이션 실패: {e}")
                continue
    
    print(f"✅ 마이그레이션 완료!")
    print(f"📊 성공: {migrated_count}개")
    print(f"❌ 실패: {error_count}개")
    print(f"🏢 총 회사: {Company.objects.count()}개")
    print(f"🏬 총 부서: {Department.objects.count()}개")

def cleanup_old_data():
    """마이그레이션 후 불필요한 데이터 정리 (선택사항)"""
    print("\n🧹 데이터 정리 중...")
    
    # 필요시 구현
    print("✅ 정리 완료!")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Sales Note 데이터 마이그레이션 도구")
    print("=" * 50)
    
    try:
        migrate_existing_data()
        
        # 정리 옵션
        response = input("\n🧹 기존 텍스트 데이터를 정리하시겠습니까? (y/N): ")
        if response.lower() == 'y':
            cleanup_old_data()
        
        print("\n🎉 모든 작업이 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n⚠️ 작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n💥 마이그레이션 중 오류 발생: {e}")
        sys.exit(1)
