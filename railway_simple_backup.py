#!/usr/bin/env python
"""
Railway 초간단 백업 스크립트
환경변수만 사용하여 최대한 안정적으로 백업합니다.
"""
import os
import sys
import datetime
import smtplib
import gzip
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_korea_time():
    """한국 시간을 반환 (UTC+9 시간대)"""
    utc_now = datetime.datetime.utcnow()
    korea_offset = datetime.timedelta(hours=9)
    return utc_now + korea_offset

def format_korea_time(dt=None):
    """한국 시간을 문자열로 포맷팅"""
    if dt is None:
        dt = get_korea_time()
    return dt.strftime('%Y년 %m월 %d일 %H시 %M분')

def format_korea_datetime(dt=None):
    """한국 시간을 파일명 형식으로 포맷팅"""
    if dt is None:
        dt = get_korea_time()
    return dt.strftime('%Y%m%d_%H%M%S')

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

def create_environment_backup():
    """환경변수 정보만 백업"""
    try:
        # 한국 시간으로 파일명 생성
        korea_now = get_korea_time()
        timestamp = format_korea_datetime(korea_now)
        
        # 백업 파일명
        backup_filename = f"railway_env_backup_{timestamp}.txt"
        compressed_filename = f"{backup_filename}.gz"
        backup_path = f"/tmp/{backup_filename}"
        compressed_path = f"/tmp/{compressed_filename}"
        
        print(f"🔄 환경변수 백업 생성 시작: {backup_filename}")
        print(f"🕐 한국 시간: {format_korea_time(korea_now)}")
        
        # 백업 정보 수집
        backup_content = [
            f"Sales Note 환경변수 백업",
            f"생성 시간: {format_korea_time(korea_now)}",
            f"서버 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"타임스탬프: {timestamp}",
            "",
            "=== 환경변수 정보 ===",
        ]
        
        # 중요한 환경변수들 확인
        important_vars = [
            'DATABASE_URL',
            'DATABASE_PUBLIC_URL',
            'SMTP_SERVER',
            'SMTP_PORT', 
            'SMTP_USERNAME',
            'DJANGO_SETTINGS_MODULE',
            'PORT',
            'PYTHONPATH'
        ]
        
        for var in important_vars:
            value = os.environ.get(var, 'NOT_SET')
            if 'password' in var.lower() or 'secret' in var.lower():
                value = "***HIDDEN***" if value != 'NOT_SET' else 'NOT_SET'
            backup_content.append(f"{var}: {value}")
        
        backup_content.extend([
            "",
            "=== 시스템 정보 ===",
            f"Python 버전: {sys.version}",
            f"작업 디렉토리: {os.getcwd()}",
            f"사용자: {os.environ.get('USER', 'unknown')}",
            f"호스트명: {os.environ.get('HOSTNAME', 'unknown')}",
            "",
            "=== 파일 시스템 ===",
        ])
        
        # /app 디렉토리 확인
        try:
            if os.path.exists('/app'):
                app_files = os.listdir('/app')[:20]  # 상위 20개만
                backup_content.append(f"/app 디렉토리 파일들: {', '.join(app_files)}")
            else:
                backup_content.append("/app 디렉토리가 존재하지 않습니다.")
        except Exception as e:
            backup_content.append(f"/app 디렉토리 확인 실패: {e}")
        
        # manage.py 확인
        try:
            if os.path.exists('/app/manage.py'):
                backup_content.append("✅ Django manage.py 발견")
            else:
                backup_content.append("❌ Django manage.py 없음")
        except Exception as e:
            backup_content.append(f"manage.py 확인 실패: {e}")
        
        backup_content.extend([
            "",
            "=== 백업 완료 ===",
            f"총 라인 수: {len(backup_content)}"
        ])
        
        # 파일에 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(backup_content))
        
        # 파일 크기 확인
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
        
        print(f"✅ 환경변수 백업 완료!")
        print(f"📁 원본 크기: {original_size / 1024:.2f} KB")
        print(f"📁 압축 크기: {compressed_size / 1024:.2f} KB")
        print(f"📊 총 정보 라인: {len(backup_content)}")
        
        return True, compressed_filename, compressed_size, len(backup_content)
        
    except Exception as e:
        error_msg = f"환경변수 백업 중 오류: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg

def main():
    """메인 백업 프로세스"""
    korea_start_time = get_korea_time()
    
    print("=" * 60)
    print(f"🚀 Sales Note 초간단 백업 시스템")
    print(f"🕐 한국 시간: {format_korea_time(korea_start_time)}")
    print(f"⏰ 서버 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 작업 디렉토리: {os.getcwd()}")
    print("=" * 60)
    
    try:
        # 환경변수 백업 생성
        result = create_environment_backup()
        
        if isinstance(result, tuple) and len(result) >= 4:
            # 성공한 경우
            success, backup_filename, file_size, total_lines = result[:4]
            duration = (get_korea_time() - korea_start_time).total_seconds()
            
            # 이메일 알림 전송
            subject = f"[자동] Sales Note 시스템 백업 완료 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
안녕하세요,

Sales Note 시스템 정보 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 백업 방식: 환경변수 및 시스템 정보
• 완료 시간: {format_korea_time(get_korea_time())}
• 백업 파일: {backup_filename}
• 파일 크기: {file_size / 1024:.2f} KB
• 총 정보 라인: {total_lines}개
• 소요 시간: {duration:.1f}초

💾 백업 상태: ✅ 성공

이 백업으로 Railway 환경 설정을 확인할 수 있습니다.

---
Sales Note 자동 백업 시스템 (한국시간 기준)
"""
            send_email_notification(subject, body, is_success=True)
            
        elif isinstance(result, tuple) and len(result) == 2:
            # 실패한 경우
            success, error_msg = result
            
            subject = f"🚨 [자동] Sales Note 시스템 백업 실패 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
⚠️ 주의: Sales Note 시스템 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {format_korea_time(get_korea_time())}
• 오류 메시지: {error_msg}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. 시스템 상태 확인

---
Sales Note 자동 백업 시스템 (한국시간 기준)
"""
            send_email_notification(subject, body, is_success=False)
            
        else:
            # 예상치 못한 반환값
            success = False
            error_msg = "알 수 없는 백업 오류"
            
        # 결과 출력
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
        subject = f"🚨 [자동] Sales Note 시스템 백업 실패 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
        body = f"""
⚠️ 주의: Sales Note 시스템 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {format_korea_time(get_korea_time())}
• 오류 메시지: {error_message}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. 시스템 상태 확인

---
Sales Note 자동 백업 시스템 (한국시간 기준)
"""
        send_email_notification(subject, body, is_success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
