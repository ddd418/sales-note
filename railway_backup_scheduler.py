#!/usr/bin/env python
"""
Railway PostgreSQL 자동 백업 스케줄러
매일 아침 8시에 실행되는 백업 스크립트
"""
import os
import sys
import subprocess
import datetime
from pathlib import Path

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')

import django
django.setup()

from django.conf import settings

def create_postgres_dump():
    """PostgreSQL 덤프 생성"""
    try:
        # 현재 시간으로 파일명 생성
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Railway에서 환경변수로 제공되는 DATABASE_URL 사용
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL 환경변수를 찾을 수 없습니다.")
            return False
        
        # 백업 파일명
        backup_filename = f"railway_backup_{timestamp}.sql"
        backup_path = f"/tmp/{backup_filename}"
        
        print(f"🔄 PostgreSQL 덤프 생성 시작: {backup_filename}")
        
        # pg_dump 명령어 실행
        dump_command = [
            "pg_dump",
            database_url,
            "--verbose",
            "--no-password",
            "--format=custom",  # 압축된 형태로 저장
            "--file", backup_path
        ]
        
        # 덤프 실행
        result = subprocess.run(
            dump_command,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode == 0:
            print(f"✅ 덤프 생성 완료: {backup_path}")
            
            # 파일 크기 확인
            file_size = os.path.getsize(backup_path)
            print(f"📁 파일 크기: {file_size / 1024 / 1024:.2f} MB")
            
            # 선택사항: 외부 저장소에 업로드 (예: AWS S3, Google Cloud Storage)
            # upload_to_cloud_storage(backup_path, backup_filename)
            
            return True
        else:
            print(f"❌ 덤프 생성 실패:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 덤프 생성 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"❌ 덤프 생성 중 오류: {e}")
        return False

def cleanup_old_backups():
    """7일 이상 된 백업 파일 삭제"""
    try:
        backup_dir = Path("/tmp")
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=7)
        
        deleted_count = 0
        for backup_file in backup_dir.glob("railway_backup_*.sql"):
            # 파일 생성 시간 확인
            file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_time < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
                print(f"🗑️ 오래된 백업 파일 삭제: {backup_file.name}")
        
        if deleted_count > 0:
            print(f"✅ {deleted_count}개의 오래된 백업 파일 삭제 완료")
        else:
            print("📝 삭제할 오래된 백업 파일 없음")
            
    except Exception as e:
        print(f"⚠️ 백업 파일 정리 중 오류: {e}")

def send_notification(success, message):
    """백업 결과 알림 (선택사항)"""
    try:
        # 이메일 또는 슬랙 알림 구현 가능
        # 예: 관리자에게 백업 성공/실패 알림
        
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            import requests
            
            status_emoji = "✅" if success else "❌"
            payload = {
                "text": f"{status_emoji} Sales Note DB 백업 {message}",
                "username": "DB Backup Bot"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("📢 슬랙 알림 전송 완료")
            else:
                print(f"⚠️ 슬랙 알림 전송 실패: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ 알림 전송 중 오류: {e}")

def main():
    """메인 백업 프로세스"""
    print("=" * 60)
    print(f"🚀 Sales Note PostgreSQL 자동 백업")
    print(f"⏰ 실행 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. PostgreSQL 덤프 생성
        success = create_postgres_dump()
        
        # 2. 오래된 백업 파일 정리
        cleanup_old_backups()
        
        # 3. 결과 알림
        if success:
            message = "성공적으로 완료되었습니다."
            print(f"🎉 {message}")
            send_notification(True, message)
        else:
            message = "실패했습니다."
            print(f"💥 {message}")
            send_notification(False, message)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 백업이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        error_message = f"백업 중 예상치 못한 오류 발생: {e}"
        print(f"💥 {error_message}")
        send_notification(False, error_message)
        sys.exit(1)

if __name__ == "__main__":
    main()
