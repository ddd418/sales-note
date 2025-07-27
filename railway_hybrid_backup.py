#!/usr/bin/env python
"""
Django 기반 PostgreSQL 백업 스크립트 (Railway 최적화)
pg_dump 대신 Django의 dumpdata를 사용합니다.
"""
import os
import sys
import subprocess
import datetime
import smtplib
import gzip
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')

import django
django.setup()

from django.core.management import call_command

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

def create_django_backup():
    """Django dumpdata를 사용한 백업 생성"""
    try:
        # 현재 시간으로 파일명 생성
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # 백업 파일명
        backup_filename = f"railway_django_backup_{timestamp}.json"
        compressed_filename = f"{backup_filename}.gz"
        backup_path = f"/tmp/{backup_filename}"
        compressed_path = f"/tmp/{compressed_filename}"
        
        print(f"🔄 Django 데이터 덤프 생성 시작: {backup_filename}")
        
        # Django dumpdata 실행
        with open(backup_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        'reporting',  # reporting 앱만 백업
                        format='json',
                        indent=2,
                        stdout=f)
        
        # 파일 존재 및 크기 확인
        if not os.path.exists(backup_path):
            error_msg = "백업 파일이 생성되지 않았습니다."
            print(f"❌ {error_msg}")
            return False, error_msg
        
        original_size = os.path.getsize(backup_path)
        
        # 파일 압축
        print(f"🗜️ 백업 파일 압축 중...")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # 원본 파일 삭제
        os.remove(backup_path)
        
        # 압축 파일 크기 확인
        compressed_size = os.path.getsize(compressed_path)
        
        print(f"✅ Django 백업 완료!")
        print(f"📁 원본 크기: {original_size / 1024 / 1024:.2f} MB")
        print(f"📁 압축 크기: {compressed_size / 1024 / 1024:.2f} MB")
        print(f"🗜️ 압축률: {((original_size - compressed_size) / original_size * 100):.1f}%")
        
        return True, compressed_filename, compressed_size
        
    except Exception as e:
        error_msg = f"Django 백업 중 오류: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg

def create_pg_backup_fallback():
    """pg_dump 사용한 백업 (pg_dump가 있는 경우)"""
    try:
        # pg_dump 사용 가능 확인
        result = subprocess.run(['which', 'pg_dump'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ pg_dump를 찾을 수 없어 Django 백업을 사용합니다.")
            return create_django_backup()
        
        # 현재 시간으로 파일명 생성
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # Railway에서 환경변수로 제공되는 DATABASE_PUBLIC_URL 사용
        database_url = os.environ.get('DATABASE_PUBLIC_URL')
        if not database_url:
            error_msg = "DATABASE_PUBLIC_URL 환경변수를 찾을 수 없습니다."
            print(f"❌ {error_msg}")
            return False, error_msg
        
        # 백업 파일명
        backup_filename = f"railway_pg_backup_{timestamp}.sql"
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
            print(f"✅ PostgreSQL 덤프 생성 완료: {backup_path}")
            
            # 파일 크기 확인
            file_size = os.path.getsize(backup_path)
            print(f"📁 파일 크기: {file_size / 1024 / 1024:.2f} MB")
            
            return True, backup_filename, file_size
        else:
            error_msg = f"pg_dump 실패: {result.stderr}"
            print(f"❌ {error_msg}")
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "pg_dump 타임아웃 (5분 초과)"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"pg_dump 오류: {e}"
        print(f"❌ {error_msg}")
        # pg_dump 실패 시 Django 백업으로 폴백
        print("🔄 Django 백업으로 전환합니다...")
        return create_django_backup()

def cleanup_old_backups():
    """7일 이상 된 백업 파일 삭제"""
    try:
        backup_dir = Path("/tmp")
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=7)
        
        deleted_count = 0
        patterns = ["railway_backup_*.sql", "railway_django_backup_*.json*", "railway_pg_backup_*.sql"]
        
        for pattern in patterns:
            for backup_file in backup_dir.glob(pattern):
                # 파일 생성 시간 확인
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"🗑️ 오래된 백업 삭제: {backup_file.name}")
        
        if deleted_count > 0:
            print(f"✅ {deleted_count}개의 오래된 백업 파일 삭제 완료")
        else:
            print("📂 삭제할 오래된 백업 파일이 없습니다.")
            
    except Exception as e:
        print(f"⚠️ 파일 정리 중 오류: {e}")

def main():
    """메인 백업 프로세스"""
    print("=" * 60)
    print(f"🚀 Sales Note 하이브리드 백업 시스템")
    print(f"⏰ 실행 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    start_time = datetime.datetime.now()
    
    try:
        # 1. 백업 생성 (pg_dump 우선, 실패 시 Django dumpdata)
        result = create_pg_backup_fallback()
        
        if isinstance(result, tuple) and len(result) >= 3:
            # 성공한 경우
            success, backup_filename, file_size = result[:3]
            duration = (datetime.datetime.now() - start_time).total_seconds()
            
            # 백업 타입 결정
            backup_type = "PostgreSQL 덤프" if "pg_backup" in backup_filename else "Django 데이터 덤프"
            
            # 이메일 알림 전송
            subject = f"[자동] Sales Note DB 백업 완료 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
안녕하세요,

Sales Note 데이터베이스 자동 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 백업 방식: {backup_type}
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
2. DATABASE_PUBLIC_URL 환경변수 확인
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
        
        # 3. 결과 출력
        if success:
            message = "성공적으로 완료되었습니다."
            print(f"🎉 {message}")
        else:
            message = "실패했습니다."
            print(f"💥 {message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 백업이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        error_message = f"백업 중 예상치 못한 오류 발생: {e}"
        print(f"💥 {error_message}")
        
        # 실패 알림 전송
        subject = f"🚨 [자동] Sales Note DB 백업 실패 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body = f"""
⚠️ 주의: Sales Note 데이터베이스 자동 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
• 오류 메시지: {error_message}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_PUBLIC_URL 환경변수 확인
3. 필요시 수동 백업 실행

---
Sales Note 자동 백업 시스템
"""
        send_email_notification(subject, body, is_success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
