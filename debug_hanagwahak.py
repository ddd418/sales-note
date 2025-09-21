#!/usr/bin/env python
"""
하나과학 회사 인식 문제 디버깅 스크립트

서버에서 다음과 같이 실행:
python manage.py shell < debug_hanagwahak.py

또는:
python debug_hanagwahak.py
"""

import os
import sys
import django

# Django 설정
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings_production')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from reporting.models import UserCompany, UserProfile
import unicodedata

def debug_hanagwahak():
    print("=== 하나과학 회사 인식 디버깅 ===")
    print()
    
    # 모든 회사 목록 조회
    companies = UserCompany.objects.all()
    print(f"총 {companies.count()}개의 회사가 등록되어 있습니다:")
    print()
    
    for company in companies:
        print(f"회사 ID: {company.id}")
        print(f"회사명: '{company.name}'")
        print(f"회사명 repr: {repr(company.name)}")
        print(f"회사명 길이: {len(company.name)}")
        print(f"회사명 UTF-8 바이트: {company.name.encode('utf-8').hex()}")
        
        # 기본 정리
        company_name_clean = company.name.strip().replace(' ', '').lower()
        print(f"정리된 회사명: '{company_name_clean}'")
        
        # 유니코드 정규화
        normalized_name = unicodedata.normalize('NFKC', company_name_clean)
        print(f"정규화된 회사명: '{normalized_name}'")
        
        # 하나과학 패턴 매칭 테스트
        hanagwahak_variations = [
            '하나과학', 'hanagwahak', 'hana', '하나',
            'hanagwahac', 'hana gwahak', '하나 과학',
            'hanascience', 'hana science'
        ]
        
        print("패턴 매칭 결과:")
        matches = []
        for variation in hanagwahak_variations:
            is_match = variation.lower() in company_name_clean
            is_match_normalized = variation.lower() in normalized_name
            print(f"  '{variation}' in clean: {is_match}, in normalized: {is_match_normalized}")
            if is_match or is_match_normalized:
                matches.append(variation)
        
        # 부분 매칭
        has_hana = any(hana in company_name_clean for hana in ['하나', 'hana'])
        has_science = any(science in company_name_clean for science in ['과학', 'gwahak', 'science'])
        partial_match = has_hana and has_science
        
        print(f"부분 매칭 - 하나: {has_hana}, 과학: {has_science}, 결과: {partial_match}")
        
        # 최종 결과
        final_result = bool(matches) or partial_match
        print(f"최종 하나과학 인식 결과: {final_result}")
        
        # 이 회사에 속한 사용자들
        users = UserProfile.objects.filter(company=company)
        print(f"이 회사의 사용자 수: {users.count()}")
        if users.count() > 0:
            for user in users:
                print(f"  - {user.user.username} ({user.role})")
        
        print("-" * 50)
        print()
    
    # 하나과학으로 인식되는 회사가 있는지 확인
    print("=== 하나과학으로 인식되는 회사 목록 ===")
    hanagwahak_companies = []
    
    for company in companies:
        company_name_clean = company.name.strip().replace(' ', '').lower()
        normalized_name = unicodedata.normalize('NFKC', company_name_clean)
        
        hanagwahak_variations = [
            '하나과학', 'hanagwahak', 'hana', '하나',
            'hanagwahac', 'hana gwahak', '하나 과학',
            'hanascience', 'hana science'
        ]
        
        is_match = any(variation.lower() in company_name_clean for variation in hanagwahak_variations)
        is_match_normalized = any(variation.lower() in normalized_name for variation in hanagwahak_variations)
        
        has_hana = any(hana in company_name_clean for hana in ['하나', 'hana'])
        has_science = any(science in company_name_clean for science in ['과학', 'gwahak', 'science'])
        partial_match = has_hana and has_science
        
        if is_match or is_match_normalized or partial_match:
            hanagwahak_companies.append(company)
            print(f"✓ {company.name} (ID: {company.id})")
    
    if not hanagwahak_companies:
        print("❌ 하나과학으로 인식되는 회사가 없습니다!")
    else:
        print(f"✅ {len(hanagwahak_companies)}개의 회사가 하나과학으로 인식됩니다.")
    
    print("\n=== 환경 정보 ===")
    print(f"Python 버전: {sys.version}")
    print(f"Python 인코딩: {sys.stdout.encoding}")
    print(f"파일시스템 인코딩: {sys.getfilesystemencoding()}")
    print(f"Django 설정: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")
    
    # DB 연결 정보
    from django.db import connection
    print(f"데이터베이스 엔진: {connection.settings_dict['ENGINE']}")

if __name__ == "__main__":
    debug_hanagwahak()