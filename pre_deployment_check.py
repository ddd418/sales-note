#!/usr/bin/env python
"""
서버 배포 전 데이터베이스 상태 체크 및 백업 스크립트
"""
import os
import sys
import django
from datetime import datetime
import json

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from reporting.models import FollowUp, Company, Department

def check_database_structure():
    """현재 데이터베이스 구조 확인"""
    print("🔍 데이터베이스 구조 분석 중...")
    
    with connection.cursor() as cursor:
        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(reporting_followup)")
        columns = cursor.fetchall()
        
        print("\n📋 FollowUp 테이블 컬럼:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # 기존 데이터 샘플 확인
        cursor.execute("SELECT COUNT(*) FROM reporting_followup")
        total_count = cursor.fetchone()[0]
        
        print(f"\n📊 총 FollowUp 레코드: {total_count}개")
        
        if total_count > 0:
            # 샘플 데이터 확인
            cursor.execute("SELECT * FROM reporting_followup LIMIT 5")
            samples = cursor.fetchall()
            
            print("\n📝 샘플 데이터:")
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. ID: {sample[0]}")
                # 실제 컬럼 구조에 맞게 조정 필요
        
        return total_count

def backup_database():
    """데이터베이스 백업"""
    print("\n💾 데이터베이스 백업 중...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"sales_db_backup_before_migration_{timestamp}.json"
    
    try:
        # Django dumpdata 명령 사용
        with open(backup_filename, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'reporting', stdout=f, indent=2)
        
        print(f"✅ 백업 완료: {backup_filename}")
        return backup_filename
        
    except Exception as e:
        print(f"❌ 백업 실패: {e}")
        return None

def analyze_migration_needs():
    """마이그레이션 필요성 분석"""
    print("\n🔬 마이그레이션 요구사항 분석...")
    
    try:
        # Company, Department 테이블 존재 확인
        company_count = Company.objects.count()
        department_count = Department.objects.count()
        followup_count = FollowUp.objects.count()
        
        print(f"📊 현재 상태:")
        print(f"  - 회사: {company_count}개")
        print(f"  - 부서: {department_count}개") 
        print(f"  - 팔로우업: {followup_count}개")
        
        # 마이그레이션 필요성 판단
        needs_migration = False
        
        if followup_count > 0 and (company_count == 0 or department_count == 0):
            needs_migration = True
            print("\n⚠️ 마이그레이션이 필요합니다!")
            print("  - 팔로우업 데이터는 있지만 Company/Department 데이터가 없습니다.")
        
        elif followup_count > 0:
            # 첫 번째 팔로우업 데이터 확인
            sample = FollowUp.objects.first()
            if not sample.company or not sample.department:
                needs_migration = True
                print("\n⚠️ 마이그레이션이 필요합니다!")
                print("  - 팔로우업에 연결된 Company/Department가 없습니다.")
        
        if not needs_migration:
            print("\n✅ 마이그레이션이 필요하지 않습니다.")
        
        return needs_migration
        
    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")
        return True  # 안전을 위해 마이그레이션 필요로 간주

def create_migration_plan():
    """마이그레이션 계획 생성"""
    print("\n📋 마이그레이션 계획 생성...")
    
    plan = {
        "timestamp": datetime.now().isoformat(),
        "steps": [
            "1. 데이터베이스 백업",
            "2. 새로운 마이그레이션 파일 적용",
            "3. Company/Department 데이터 생성",
            "4. FollowUp 관계 업데이트",
            "5. 데이터 무결성 검증"
        ],
        "rollback_plan": [
            "1. 서비스 중단",
            "2. 백업 파일로 복원",
            "3. 이전 코드로 롤백",
            "4. 서비스 재시작"
        ]
    }
    
    with open("migration_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print("✅ 마이그레이션 계획 저장: migration_plan.json")

def main():
    print("=" * 60)
    print("🚀 Sales Note 서버 배포 전 검사 도구")
    print("=" * 60)
    
    try:
        # 1. 데이터베이스 구조 확인
        record_count = check_database_structure()
        
        # 2. 마이그레이션 필요성 분석
        needs_migration = analyze_migration_needs()
        
        if needs_migration:
            print("\n" + "=" * 40)
            print("⚠️ 마이그레이션 필요!")
            print("=" * 40)
            
            # 3. 백업 생성
            backup_file = backup_database()
            
            if backup_file:
                # 4. 마이그레이션 계획 생성
                create_migration_plan()
                
                print("\n🎯 다음 단계:")
                print("1. 백업 파일 확인 및 안전한 위치에 저장")
                print("2. 서버에서 다음 명령 실행:")
                print("   python manage.py makemigrations")
                print("   python manage.py migrate")
                print("   python migrate_existing_data.py")
                print("3. 데이터 무결성 검증")
                print("4. 서비스 테스트")
                
            else:
                print("❌ 백업 실패로 인해 마이그레이션을 중단합니다.")
                return False
        else:
            print("\n✅ 마이그레이션이 필요하지 않습니다.")
            print("🚀 바로 배포 가능합니다!")
        
        return True
        
    except Exception as e:
        print(f"\n💥 검사 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
