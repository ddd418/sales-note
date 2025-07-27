#!/usr/bin/env python
"""
PostgreSQL 수동 백업 스크립트
Railway에서 언제든지 수동으로 백업을 실행할 수 있습니다.
"""
import os
import sys
import subprocess
import datetime
import gzip
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def send_backup_notification(backup_file, file_size, duration, is_manual=True):
    """백업 완료 알림 이메일 전송"""
    try:
        # SMTP 설정 (Gmail 기준)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            print("⚠️ SMTP 설정이 없어 이메일 알림을 건너뜁니다.")
            return
        
        # 이메일 내용 구성
        subject = f"{'[수동]' if is_manual else '[자동]'} Sales Note DB 백업 완료 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
안녕하세요,

Sales Note 데이터베이스 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: {'수동 백업' if is_manual else '자동 백업'}
• 완료 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
• 백업 파일: {backup_file}
• 파일 크기: {file_size / (1024*1024):.2f} MB
• 소요 시간: {duration:.1f}초

💾 백업 상태: ✅ 성공

이 백업은 7일간 보관된 후 자동으로 삭제됩니다.

---
Sales Note 자동 백업 시스템
"""
        
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
        
        print(f"📧 백업 완료 알림을 jhahn.hana@gmail.com으로 전송했습니다.")
        
    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")

def send_backup_failure_notification(error_message, is_manual=True):
    """백업 실패 알림 이메일 전송"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_username, smtp_password]):
            print("⚠️ SMTP 설정이 없어 이메일 알림을 건너뜁니다.")
            return
        
        subject = f"🚨 {'[수동]' if is_manual else '[자동]'} Sales Note DB 백업 실패 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
⚠️ 주의: Sales Note 데이터베이스 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: {'수동 백업' if is_manual else '자동 백업'}
• 실패 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
• 오류 메시지: {error_message}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_URL 환경변수 확인
3. 필요시 수동 백업 재시도

---
Sales Note 자동 백업 시스템
"""
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = 'jhahn.hana@gmail.com'
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, 'jhahn.hana@gmail.com', text)
        server.quit()
        
        print(f"📧 백업 실패 알림을 jhahn.hana@gmail.com으로 전송했습니다.")
        
    except Exception as e:
        print(f"❌ 실패 알림 이메일 전송 실패: {e}")

def create_backup():
    """PostgreSQL 데이터베이스 백업 생성"""
    print("🔄 수동 백업을 시작합니다...")
    start_time = datetime.datetime.now()
    
    # 환경변수에서 데이터베이스 URL 가져오기
    database_url = os.environ.get('DATABASE_PUBLIC_URL')
    if not database_url:
        error_msg = "DATABASE_PUBLIC_URL 환경변수가 설정되지 않았습니다."
        print(f"❌ {error_msg}")
        send_backup_failure_notification(error_msg, is_manual=True)
        return False
    
    # 백업 파일명 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"railway_manual_backup_{timestamp}.sql"
    compressed_filename = f"{backup_filename}.gz"
    
    # 임시 디렉토리에 백업 생성
    backup_dir = "/tmp"
    backup_path = os.path.join(backup_dir, backup_filename)
    compressed_path = os.path.join(backup_dir, compressed_filename)
    
    try:
        # pg_dump 실행
        print("📥 PostgreSQL 덤프를 생성하는 중...")
        dump_command = [
            "pg_dump",
            database_url,
            "--verbose",
            "--no-password",
            "--format=plain",
            "--file", backup_path
        ]
        
        result = subprocess.run(
            dump_command,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode != 0:
            error_msg = f"pg_dump 실행 실패: {result.stderr}"
            print(f"❌ {error_msg}")
            send_backup_failure_notification(error_msg, is_manual=True)
            return False
        
        # 파일 존재 확인
        if not os.path.exists(backup_path):
            error_msg = "백업 파일이 생성되지 않았습니다."
            print(f"❌ {error_msg}")
            send_backup_failure_notification(error_msg, is_manual=True)
            return False
        
        # 파일 압축
        print("🗜️ 백업 파일을 압축하는 중...")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # 원본 파일 삭제
        os.remove(backup_path)
        
        # 백업 완료 정보
        file_size = os.path.getsize(compressed_path)
        duration = (datetime.datetime.now() - start_time).total_seconds()
        
        print(f"✅ 수동 백업 완료!")
        print(f"📁 파일: {compressed_filename}")
        print(f"📏 크기: {file_size / (1024*1024):.2f} MB")
        print(f"⏱️ 소요시간: {duration:.1f}초")
        
        # 성공 알림 전송
        send_backup_notification(compressed_filename, file_size, duration, is_manual=True)
        
        return True
        
    except subprocess.TimeoutExpired:
        error_msg = "백업 작업 타임아웃 (5분 초과)"
        print(f"❌ {error_msg}")
        send_backup_failure_notification(error_msg, is_manual=True)
        return False
    except Exception as e:
        error_msg = f"백업 중 예상치 못한 오류: {str(e)}"
        print(f"❌ {error_msg}")
        send_backup_failure_notification(error_msg, is_manual=True)
        return False

def show_manual_backup_guide():
    """Railway 웹 대시보드를 통한 수동 백업 가이드"""
    print("=" * 60)
    print("🚂 Railway 수동 백업 가이드")
    print("=" * 60)
    
    print("\n📋 1. Railway 대시보드에서 수동 실행:")
    print("   ➤ https://railway.app/dashboard 접속")
    print("   ➤ sales-note 프로젝트 선택")
    print("   ➤ Settings > Cron Jobs 탭")
    print("   ➤ 백업 작업 찾아서 'Run Now' 클릭")
    
    print("\n📋 2. Railway Shell에서 직접 실행:")
    print("   ➤ Railway CLI 설치: npm install -g @railway/cli")
    print("   ➤ 로그인: railway login")
    print("   ➤ 프로젝트 연결: railway link")
    print("   ➤ Shell 접속: railway shell")
    print("   ➤ 수동 백업 실행: python railway_manual_backup.py")
    
    print("\n📋 3. 로컬에서 Railway DB 백업:")
    print("   ➤ Railway 환경변수 복사")
    print("   ➤ 로컬 환경변수 설정:")
    print("     set DATABASE_URL=<Railway의 DATABASE_URL>")
    print("     set SMTP_USERNAME=<Gmail 주소>")
    print("     set SMTP_PASSWORD=<Gmail 앱 비밀번호>")
    print("   ➤ 백업 실행: python railway_manual_backup.py")

def main():
    """메인 실행 함수"""
    print("🚀 Sales Note 수동 백업 시스템")
    print("=" * 50)
    print(f"📅 실행 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")
    print()
    
    # 인자가 있으면 가이드만 표시
    if len(sys.argv) > 1 and sys.argv[1] == 'guide':
        show_manual_backup_guide()
        return
    
    # 백업 실행
    success = create_backup()
    
    if success:
        print("\n🎉 수동 백업이 성공적으로 완료되었습니다!")
        print("📧 완료 알림 이메일이 jhahn.hana@gmail.com으로 전송되었습니다.")
    else:
        print("\n❌ 수동 백업이 실패했습니다.")
        print("📧 실패 알림 이메일이 jhahn.hana@gmail.com으로 전송되었습니다.")
        print("\n💡 수동 백업 가이드를 보려면: python railway_manual_backup.py guide")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    print("\n📋 단계별 백업 방법:")
    
    print("\n1️⃣ Railway 웹 대시보드 접속")
    print("   ➤ https://railway.app/dashboard 방문")
    print("   ➤ 로그인 후 sales-note 프로젝트 선택")
    
    print("\n2️⃣ 데이터베이스 정보 확인")
    print("   ➤ PostgreSQL 서비스 클릭")
    print("   ➤ 'Connect' 탭 선택")
    print("   ➤ 'Database URL' 복사 (postgres://로 시작하는 URL)")
    
    print("\n3️⃣ 로컬에서 백업 실행")
    print("   다음 중 하나의 방법 선택:")
    print("   ")
    print("   📦 방법 A: Django dumpdata (권장)")
    print("   ➤ Railway 환경변수 설정 후:")
    print("     set DATABASE_URL=복사한_URL")
    print("     python manage.py dumpdata reporting --indent=2 > railway_backup.json")
    print("   ")
    print("   🗄️ 방법 B: PostgreSQL 직접 백업")
    print("   ➤ PostgreSQL 설치 후:")
    print("     pg_dump \"복사한_DATABASE_URL\" > railway_backup.sql")
    
    print("\n4️⃣ 백업 검증")
    print("   ➤ 생성된 파일 크기 확인")
    print("   ➤ JSON/SQL 파일 문법 검증")
    
    print("\n💡 추가 팁:")
    print("   • 백업 전 서비스 일시 중단 권장")
    print("   • 여러 형태로 백업 (JSON + SQL)")
    print("   • 안전한 위치에 백업 파일 저장")

def create_env_backup_script():
    """환경변수 기반 백업 스크립트"""
    print("\n" + "=" * 40)
    print("🔧 환경변수 백업 스크립트 생성")
    print("=" * 40)
    
    script_content = '''@echo off
REM Railway 데이터베이스 백업 배치 스크립트
REM 사용법: railway_backup.bat [DATABASE_URL]

set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if "%1"=="" (
    echo 사용법: railway_backup.bat "DATABASE_URL"
    echo 예시: railway_backup.bat "postgres://user:pass@host:port/db"
    pause
    exit /b 1
)

set DATABASE_URL=%1

echo ========================
echo Railway 데이터베이스 백업
echo ========================
echo 시간: %TIMESTAMP%
echo URL: %DATABASE_URL%
echo ========================

REM Django 백업
echo.
echo [1/3] Django 데이터 백업 중...
python manage.py dumpdata reporting --indent=2 > railway_django_backup_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✅ Django 백업 완료: railway_django_backup_%TIMESTAMP%.json
) else (
    echo ❌ Django 백업 실패
)

REM PostgreSQL 백업 (pg_dump 설치된 경우)
echo.
echo [2/3] PostgreSQL 백업 시도 중...
pg_dump "%DATABASE_URL%" > railway_pg_backup_%TIMESTAMP%.sql 2>nul
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL 백업 완료: railway_pg_backup_%TIMESTAMP%.sql
) else (
    echo ⚠️ PostgreSQL 백업 실패 (pg_dump 없음 또는 연결 오류)
)

REM 백업 검증
echo.
echo [3/3] 백업 파일 검증 중...
for %%f in (railway_*_backup_%TIMESTAMP%.*) do (
    echo   📁 %%f - 크기: %%~zf bytes
)

echo.
echo 🎉 백업 작업 완료!
echo 💾 생성된 파일들을 안전한 위치에 보관하세요.
pause
'''
    
    with open("railway_backup.bat", "w", encoding="cp949") as f:
        f.write(script_content)
    
    print("✅ 배치 스크립트 생성: railway_backup.bat")
    print("📋 사용법:")
    print('   railway_backup.bat "복사한_DATABASE_URL"')

if __name__ == "__main__":
    main()
