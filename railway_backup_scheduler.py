#!/usr/bin/env python
"""
Railway PostgreSQL 자동 백업 스케줄러
매일 아침 8시에 실행되는 백업 스크립트
jhahn.hana@gmail.com으로 결과 알림을 전송합니다.
"""
import os
import sys
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')

import django
django.setup()

from django.conf import settings

def send_email_notification(subject, body, is_success=True):
    """이메일 알림 전송"""
    try:
        # SMTP 설정
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            print("⚠️ SMTP 설정이 없어 이메일 알림을 건너뜁니다.")
            return
        
        # 이메일 구성
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = 'jhahn.hana@gmail.com'
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP 서버 연결 및 전송
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, 'jhahn.hana@gmail.com', text)
        server.quit()
        
        status = "✅ 성공" if is_success else "❌ 실패"
        print(f"📧 {status} 알림을 jhahn.hana@gmail.com으로 전송했습니다.")
        
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")

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
            
            return True, backup_filename, file_size
        else:
            error_msg = f"덤프 생성 실패:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            print(f"❌ 덤프 생성 실패:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "덤프 생성 타임아웃 (5분 초과)"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"덤프 생성 중 오류: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg

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
    
    start_time = datetime.datetime.now()
    
    try:
        # 1. PostgreSQL 덤프 생성
        result = create_postgres_dump()
        
        if isinstance(result, tuple) and len(result) >= 3:
            # 성공한 경우
            success, backup_filename, file_size = result[:3]
            duration = (datetime.datetime.now() - start_time).total_seconds()
            
            # 이메일 알림 전송
            subject = f"[자동] Sales Note DB 백업 완료 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
안녕하세요,

Sales Note 데이터베이스 자동 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 완료 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
• 백업 파일: {backup_filename}
• 파일 크기: {file_size / (1024*1024):.2f} MB
• 소요 시간: {duration:.1f}초

💾 백업 상태: ✅ 성공

이 백업은 7일간 보관된 후 자동으로 삭제됩니다.

---
Sales Note 자동 백업 시스템
"""
            send_email_notification(subject, body, is_success=True)
            
        elif isinstance(result, tuple) and len(result) == 2:
            # 실패한 경우
            success, error_msg = result
            
            subject = f"🚨 [자동] Sales Note DB 백업 실패 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
⚠️ 주의: Sales Note 데이터베이스 자동 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
• 오류 메시지: {error_msg}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_URL 환경변수 확인
3. 필요시 수동 백업 실행

---
Sales Note 자동 백업 시스템
"""
            send_email_notification(subject, body, is_success=False)
            
        else:
            # 예상치 못한 반환값
            success = False
            error_msg = "알 수 없는 백업 오류"
            
        # 2. 오래된 백업 파일 정리
        cleanup_old_backups()
        
        # 3. Slack 알림 (기존 기능 유지)
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
