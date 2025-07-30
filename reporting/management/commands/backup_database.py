from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import json
import psycopg2
from psycopg2 import sql


class Command(BaseCommand):
    help = 'Railway PostgreSQL 자동 백업 및 이메일 알림'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='이메일 알림을 보내지 않습니다',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('Railway PostgreSQL 백업 시작')
        self.stdout.write(f'시작 시간: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 50)

        try:
            # 백업 실행
            backup_result = self.perform_backup()
            
            # 이메일 알림 (옵션으로 비활성화 가능)
            if not options['no_email']:
                self.send_email_notification(
                    subject="✅ Railway DB 백업 성공",
                    body=backup_result,
                    is_success=True
                )
            
            self.stdout.write(
                self.style.SUCCESS('백업이 성공적으로 완료되었습니다!')
            )
            
        except Exception as e:
            error_msg = f"백업 실패: {str(e)}"
            self.stdout.write(
                self.style.ERROR(error_msg)
            )
            
            # 실패 시에도 이메일 알림
            if not options['no_email']:
                self.send_email_notification(
                    subject="❌ Railway DB 백업 실패",
                    body=error_msg,
                    is_success=False
                )
            
            sys.exit(1)

    def perform_backup(self):
        """실제 백업 수행"""
        try:
            # Railway PostgreSQL 연결 정보 가져오기
            database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
            if not database_url:
                raise Exception("DATABASE_PUBLIC_URL 또는 DATABASE_URL 환경변수가 설정되지 않았습니다.")

            # 백업 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'railway_pg_backup_{timestamp}.sql'
            
            self.stdout.write(f'백업 파일명: {backup_filename}')
            
            # pg_dump 명령어 실행
            backup_command = [
                'pg_dump',
                database_url,
                '--no-owner',
                '--no-privileges',
                '--verbose',
                '--file', backup_filename
            ]
            
            self.stdout.write(f'백업 명령어 실행 중...')
            
            # subprocess로 pg_dump 실행
            result = subprocess.run(
                backup_command,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode == 0:
                # 백업 파일 크기 확인
                if os.path.exists(backup_filename):
                    file_size = os.path.getsize(backup_filename)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    backup_result = f"""
백업 성공 ✅

📋 백업 정보:
• 백업 파일: {backup_filename}
• 파일 크기: {file_size_mb:.2f} MB
• 백업 시간: {datetime.datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
• 서버: Railway PostgreSQL

📊 백업 상세:
{result.stderr if result.stderr else '백업이 정상적으로 완료되었습니다.'}
                    """
                    
                    self.stdout.write(f'백업 완료 - 파일 크기: {file_size_mb:.2f} MB')
                    return backup_result.strip()
                else:
                    raise Exception("백업 파일이 생성되지 않았습니다.")
            else:
                raise Exception(f"pg_dump 실행 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("백업 작업이 시간 초과되었습니다 (5분)")
        except Exception as e:
            raise Exception(f"백업 중 오류 발생: {str(e)}")

    def send_email_notification(self, subject, body, is_success=True):
        """이메일 알림 전송"""
        try:
            # SMTP 설정
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            recipient_email = 'jhahn.hana@gmail.com'
            
            if not all([smtp_username, smtp_password]):
                self.stdout.write(
                    self.style.WARNING('SMTP 설정이 없어 이메일을 보낼 수 없습니다.')
                )
                return
            
            # 이메일 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"[Sales System] {subject}"
            
            # 이메일 본문
            email_body = f"""
안녕하세요!

Railway 영업 시스템 데이터베이스 백업 결과를 알려드립니다.

{body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 이 메시지는 자동으로 발송되었습니다.
📧 문의사항이 있으시면 시스템 관리자에게 연락해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
Sales System Auto Backup
            """
            
            msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
            
            # SMTP 서버 연결 및 이메일 발송
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                text = msg.as_string()
                server.sendmail(smtp_username, recipient_email, text)
            
            self.stdout.write(f'이메일 알림이 {recipient_email}로 전송되었습니다.')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'이메일 전송 실패: {str(e)}')
            )

    def get_database_stats(self):
        """데이터베이스 통계 정보 조회"""
        try:
            database_url = os.environ.get('DATABASE_PUBLIC_URL') or os.environ.get('DATABASE_URL')
            if not database_url:
                return "데이터베이스 연결 정보가 없습니다."
            
            # 간단한 통계 조회
            import psycopg2
            from urllib.parse import urlparse
            
            # DATABASE_URL 파싱
            url = urlparse(database_url)
            
            conn = psycopg2.connect(
                host=url.hostname,
                database=url.path[1:],  # 첫 번째 '/' 제거
                user=url.username,
                password=url.password,
                port=url.port
            )
            
            with conn.cursor() as cursor:
                # 테이블별 레코드 수 조회
                tables_info = []
                
                # 주요 테이블들의 레코드 수 조회
                main_tables = [
                    'reporting_followup',
                    'reporting_schedule', 
                    'reporting_history',
                    'auth_user'
                ]
                
                for table in main_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        tables_info.append(f"• {table}: {count:,}개")
                    except:
                        tables_info.append(f"• {table}: 조회 실패")
                
                return "\n".join(tables_info)
                
        except Exception as e:
            return f"통계 조회 실패: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()
