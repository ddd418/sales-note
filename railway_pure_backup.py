#!/usr/bin/env python
"""
Railway PostgreSQL 순수 백업 스크립트 (Django 의존성 없음)
psycopg2를 직접 사용하여 데이터를 백업합니다.
"""
import os
import sys
import datetime
import smtplib
import gzip
import json
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import pytz

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_korea_time():
    """한국 시간을 반환"""
    return datetime.datetime.now(KST)

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

def get_database_connection():
    """데이터베이스 연결 생성"""
    try:
        # DATABASE_PUBLIC_URL에서 연결 정보 파싱
        database_url = os.environ.get('DATABASE_PUBLIC_URL')
        if not database_url:
            raise Exception("DATABASE_PUBLIC_URL 환경변수를 찾을 수 없습니다.")
        
        # psycopg2로 직접 연결
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        raise Exception(f"데이터베이스 연결 실패: {e}")

def backup_table_data(conn, table_name):
    """특정 테이블의 데이터를 백업"""
    try:
        cursor = conn.cursor()
        
        # 테이블의 모든 데이터 조회
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # 컬럼 정보 가져오기
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # 데이터를 딕셔너리 형태로 변환
        table_data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                # 날짜/시간 객체를 문자열로 변환
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row_dict[columns[i]] = value
            table_data.append(row_dict)
        
        cursor.close()
        return table_data
        
    except Exception as e:
        print(f"⚠️ 테이블 {table_name} 백업 실패: {e}")
        return []

def create_database_backup():
    """데이터베이스 백업 생성"""
    try:
        # 한국 시간으로 파일명 생성
        korea_now = get_korea_time()
        timestamp = format_korea_datetime(korea_now)
        
        # 백업 파일명
        backup_filename = f"railway_pure_backup_{timestamp}.json"
        compressed_filename = f"{backup_filename}.gz"
        backup_path = f"/tmp/{backup_filename}"
        compressed_path = f"/tmp/{compressed_filename}"
        
        print(f"🔄 데이터베이스 백업 생성 시작: {backup_filename}")
        print(f"🕐 한국 시간: {format_korea_time(korea_now)}")
        
        # 데이터베이스 연결
        conn = get_database_connection()
        
        # 백업할 테이블들 (reporting 앱 관련)
        tables_to_backup = [
            'reporting_company',
            'reporting_department', 
            'reporting_followup',
            'reporting_history',
            'reporting_userprofile',
            'auth_user',
            'auth_group',
            'auth_permission'
        ]
        
        backup_data = {
            'timestamp': timestamp,
            'korea_time': korea_now.isoformat(),
            'backup_type': 'pure_postgresql',
            'tables': {}
        }
        
        total_records = 0
        
        # 각 테이블 백업
        for table_name in tables_to_backup:
            print(f"📝 백업 중: {table_name}")
            table_data = backup_table_data(conn, table_name)
            backup_data['tables'][table_name] = table_data
            total_records += len(table_data)
            print(f"   ✅ {len(table_data)}개 레코드 백업 완료")
        
        conn.close()
        
        # JSON 파일로 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
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
        
        print(f"✅ 데이터베이스 백업 완료!")
        print(f"📊 총 레코드 수: {total_records}")
        print(f"📁 원본 크기: {original_size / 1024 / 1024:.2f} MB")
        print(f"📁 압축 크기: {compressed_size / 1024 / 1024:.2f} MB")
        print(f"🗜️ 압축률: {((original_size - compressed_size) / original_size * 100):.1f}%")
        
        return True, compressed_filename, compressed_size, total_records
        
    except Exception as e:
        error_msg = f"데이터베이스 백업 중 오류: {e}"
        print(f"❌ {error_msg}")
        return False, error_msg

def cleanup_old_backups():
    """7일 이상 된 백업 파일 삭제"""
    try:
        backup_dir = Path("/tmp")
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=7)
        
        deleted_count = 0
        patterns = ["railway_*_backup_*.json*", "railway_*_backup_*.sql*"]
        
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
    korea_start_time = get_korea_time()
    
    print("=" * 60)
    print(f"🚀 Sales Note 순수 PostgreSQL 백업 시스템")
    print(f"🕐 한국 시간: {format_korea_time(korea_start_time)}")
    print(f"⏰ 서버 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 1. 데이터베이스 백업 생성
        result = create_database_backup()
        
        if isinstance(result, tuple) and len(result) >= 4:
            # 성공한 경우
            success, backup_filename, file_size, total_records = result[:4]
            duration = (get_korea_time() - korea_start_time).total_seconds()
            
            # 이메일 알림 전송
            subject = f"[자동] Sales Note DB 백업 완료 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
안녕하세요,

Sales Note 데이터베이스 자동 백업이 성공적으로 완료되었습니다.

📋 백업 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 백업 방식: 순수 PostgreSQL 데이터 백업
• 완료 시간: {format_korea_time(get_korea_time())}
• 백업 파일: {backup_filename}
• 파일 크기: {file_size / (1024*1024):.2f} MB
• 총 레코드 수: {total_records:,}개
• 소요 시간: {duration:.1f}초

💾 백업 상태: ✅ 성공

이 백업은 7일간 보관된 후 자동으로 삭제됩니다.

---
Sales Note 자동 백업 시스템 (한국시간 기준)
"""
            send_email_notification(subject, body, is_success=True)
            
        elif isinstance(result, tuple) and len(result) == 2:
            # 실패한 경우
            success, error_msg = result
            
            subject = f"🚨 [자동] Sales Note DB 백업 실패 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
            body = f"""
⚠️ 주의: Sales Note 데이터베이스 자동 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {format_korea_time(get_korea_time())}
• 오류 메시지: {error_msg}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_PUBLIC_URL 환경변수 확인
3. 필요시 수동 백업 실행

---
Sales Note 자동 백업 시스템 (한국시간 기준)
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
        subject = f"🚨 [자동] Sales Note DB 백업 실패 - {get_korea_time().strftime('%Y-%m-%d %H:%M')}"
        body = f"""
⚠️ 주의: Sales Note 데이터베이스 자동 백업이 실패했습니다.

📋 오류 정보:
• 실행 유형: 자동 백업 (매일 오전 8시)
• 실패 시간: {format_korea_time(get_korea_time())}
• 오류 메시지: {error_message}

🔧 조치사항:
1. Railway 대시보드에서 로그 확인
2. DATABASE_PUBLIC_URL 환경변수 확인
3. 필요시 수동 백업 실행

---
Sales Note 자동 백업 시스템 (한국시간 기준)
"""
        send_email_notification(subject, body, is_success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
