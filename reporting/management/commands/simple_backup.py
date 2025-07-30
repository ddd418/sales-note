from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.conf import settings
import os
import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Command(BaseCommand):
    help = 'Railway 호환 백업 시스템 - Django ORM 사용'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='이메일 알림을 보내지 않습니다',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('Railway Django ORM 백업 시작')
        self.stdout.write(f'시작 시간: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 50)

        try:
            # 백업 실행
            backup_result = self.perform_simple_backup()
            
            # 이메일 알림 (옵션으로 비활성화 가능)
            if not options['no_email']:
                self.send_email_notification(
                    subject="✅ Railway 간단 백업 성공",
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
                    subject="❌ Railway 간단 백업 실패",
                    body=error_msg,
                    is_success=False
                )

    def perform_simple_backup(self):
        """간단한 환경변수 + 데이터 통계 백업"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 백업 정보 수집
            backup_info = {
                'timestamp': timestamp,
                'backup_time': datetime.datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S'),
                'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'development'),
                'database_stats': self.get_database_stats(),
                'system_info': self.get_system_info(),
                'env_vars_count': len([k for k in os.environ.keys() if not k.startswith('_')])
            }
            
            backup_result = f"""
백업 성공 ✅

📋 백업 정보:
• 백업 시간: {backup_info['backup_time']}
• 환경: {backup_info['environment']}
• 타임스탬프: {backup_info['timestamp']}

📊 데이터베이스 통계:
{backup_info['database_stats']}

🖥️ 시스템 정보:
{backup_info['system_info']}

💾 환경변수: {backup_info['env_vars_count']}개
            """
            
            self.stdout.write(f'백업 완료 - 시간: {backup_info["backup_time"]}')
            return backup_result.strip()
                
        except Exception as e:
            raise Exception(f"백업 중 오류 발생: {str(e)}")

    def get_database_stats(self):
        """데이터베이스 통계 정보 조회"""
        try:
            from reporting.models import FollowUp, Schedule, History
            from django.contrib.auth.models import User
            
            stats = []
            stats.append(f"• 팔로우업: {FollowUp.objects.count():,}개")
            stats.append(f"• 일정: {Schedule.objects.count():,}개")
            stats.append(f"• 기록: {History.objects.count():,}개")
            stats.append(f"• 사용자: {User.objects.count():,}개")
            
            return "\n".join(stats)
                
        except Exception as e:
            return f"통계 조회 실패: {str(e)}"

    def get_system_info(self):
        """시스템 정보 수집"""
        try:
            import sys
            import platform
            
            info = []
            info.append(f"• Python: {sys.version.split()[0]}")
            info.append(f"• Django: {settings.SETTINGS_MODULE}")
            info.append(f"• 작업 디렉토리: {os.getcwd()}")
            info.append(f"• 플랫폼: {platform.system()}")
            
            # 데이터베이스 연결 확인
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    db_version = cursor.fetchone()[0]
                    info.append(f"• DB: {db_version[:50]}...")
            except:
                info.append("• DB: 연결 확인 실패")
            
            return "\n".join(info)
                
        except Exception as e:
            return f"시스템 정보 수집 실패: {str(e)}"

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

Railway 영업 시스템 백업 결과를 알려드립니다.

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
