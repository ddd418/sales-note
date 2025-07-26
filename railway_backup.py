#!/usr/bin/env python
"""
Railway PostgreSQL 데이터베이스 백업 스크립트
"""
import os
import subprocess
import sys
from datetime import datetime
import json

def get_railway_db_url():
    """Railway 데이터베이스 URL 가져오기"""
    try:
        # Railway CLI로 환경 변수 가져오기
        result = subprocess.run(['railway', 'variables'], 
                              capture_output=True, text=True, check=True)
        
        lines = result.stdout.split('\n')
        for line in lines:
            if 'DATABASE_URL' in line:
                # DATABASE_URL=postgresql://... 형태에서 URL 추출
                return line.split('=', 1)[1].strip()
        
        print("❌ DATABASE_URL을 찾을 수 없습니다.")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Railway CLI 오류: {e}")
        return None

def backup_database_pg_dump(db_url):
    """pg_dump를 사용한 데이터베이스 백업"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"railway_backup_{timestamp}.sql"
    
    print(f"💾 pg_dump를 사용하여 백업 중... ({backup_filename})")
    
    try:
        # pg_dump 명령 실행
        cmd = ['pg_dump', db_url, '--no-password', '--verbose']
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, 
                                  text=True, check=True)
        
        print(f"✅ pg_dump 백업 완료: {backup_filename}")
        return backup_filename
        
    except subprocess.CalledProcessError as e:
        print(f"❌ pg_dump 백업 실패: {e}")
        print(f"오류 메시지: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ pg_dump가 설치되지 않았습니다.")
        print("PostgreSQL을 설치하거나 다른 방법을 사용해주세요.")
        return None

def backup_database_django():
    """Django dumpdata를 사용한 백업"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"railway_django_backup_{timestamp}.json"
    
    print(f"💾 Django dumpdata를 사용하여 백업 중... ({backup_filename})")
    
    try:
        # Railway에서 Django 명령 실행
        cmd = ['railway', 'run', 'python', 'manage.py', 'dumpdata', 
               '--indent=2', '--output', backup_filename]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"✅ Django 백업 완료: {backup_filename}")
        return backup_filename
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Django 백업 실패: {e}")
        print(f"오류 메시지: {e.stderr}")
        return None

def create_backup_info(backup_files):
    """백업 정보 파일 생성"""
    backup_info = {
        "timestamp": datetime.now().isoformat(),
        "backup_files": backup_files,
        "railway_project": get_railway_project_info(),
        "backup_methods": {
            "pg_dump": "PostgreSQL 전체 구조와 데이터",
            "django_dumpdata": "Django 모델 데이터만"
        },
        "restore_instructions": {
            "pg_dump": "psql [database_url] < backup_file.sql",
            "django_dumpdata": "python manage.py loaddata backup_file.json"
        }
    }
    
    info_filename = f"backup_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(info_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, indent=2, ensure_ascii=False)
    
    print(f"📋 백업 정보 저장: {info_filename}")
    return info_filename

def get_railway_project_info():
    """Railway 프로젝트 정보 가져오기"""
    try:
        result = subprocess.run(['railway', 'status'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "프로젝트 정보를 가져올 수 없습니다."

def main():
    print("=" * 60)
    print("🚂 Railway 데이터베이스 백업 도구")
    print("=" * 60)
    
    backup_files = []
    
    # 1. Railway CLI 연결 확인
    try:
        result = subprocess.run(['railway', 'status'], 
                              capture_output=True, text=True, check=True)
        print("✅ Railway CLI 연결됨")
        print(f"프로젝트 상태: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Railway CLI에 연결할 수 없습니다.")
        print("'railway login' 명령으로 먼저 로그인해주세요.")
        return False
    except FileNotFoundError:
        print("❌ Railway CLI가 설치되지 않았습니다.")
        print("'npm install -g @railway/cli' 명령으로 설치해주세요.")
        return False
    
    # 2. Django dumpdata 백업 (권장)
    print("\n📦 Django 데이터 백업 시도...")
    django_backup = backup_database_django()
    if django_backup:
        backup_files.append(django_backup)
    
    # 3. PostgreSQL 백업 (옵션)
    print("\n🗄️ PostgreSQL 백업 시도...")
    db_url = get_railway_db_url()
    if db_url:
        pg_backup = backup_database_pg_dump(db_url)
        if pg_backup:
            backup_files.append(pg_backup)
    
    # 4. 백업 정보 생성
    if backup_files:
        create_backup_info(backup_files)
        
        print("\n🎉 백업 완료!")
        print("📁 생성된 파일:")
        for file in backup_files:
            print(f"  - {file}")
        
        print("\n💡 복원 방법:")
        print("Django 백업 복원: railway run python manage.py loaddata [backup_file.json]")
        print("PostgreSQL 백업 복원: psql [DATABASE_URL] < [backup_file.sql]")
        
        return True
    else:
        print("\n❌ 백업 파일을 생성할 수 없었습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
