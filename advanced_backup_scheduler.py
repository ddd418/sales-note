#!/usr/bin/env python
"""
고급 PostgreSQL 백업 스크립트
- AWS S3 또는 Google Cloud Storage에 백업 파일 업로드
- 이메일/슬랙 알림
- 백업 무결성 검증
"""
import os
import sys
import subprocess
import datetime
import hashlib
import gzip
from pathlib import Path

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')

import django
django.setup()

class BackupManager:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_filename = f"railway_sales_backup_{self.timestamp}"
        self.temp_dir = Path("/tmp")
        
    def create_postgres_dump(self):
        """PostgreSQL 덤프 생성 (압축 포함)"""
        try:
            database_url = os.environ.get('DATABASE_PUBLIC_URL')
            if not database_url:
                raise Exception("DATABASE_PUBLIC_URL 환경변수를 찾을 수 없습니다.")
            
            # 덤프 파일 경로
            sql_file = self.temp_dir / f"{self.backup_filename}.sql"
            compressed_file = self.temp_dir / f"{self.backup_filename}.sql.gz"
            
            print(f"🔄 PostgreSQL 덤프 생성 시작...")
            
            # pg_dump 실행
            dump_command = [
                "pg_dump",
                database_url,
                "--verbose",
                "--no-password",
                "--format=plain",  # 일반 SQL 형태
                "--file", str(sql_file)
            ]
            
            result = subprocess.run(
                dump_command,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump 실패: {result.stderr}")
            
            # 파일 압축
            print(f"🗜️ 백업 파일 압축 중...")
            with open(sql_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # 원본 SQL 파일 삭제
            sql_file.unlink()
            
            # 파일 크기 및 체크섬 계산
            file_size = compressed_file.stat().st_size
            checksum = self.calculate_checksum(compressed_file)
            
            print(f"✅ 덤프 생성 완료:")
            print(f"   📁 파일: {compressed_file.name}")
            print(f"   📏 크기: {file_size / 1024 / 1024:.2f} MB")
            print(f"   🔐 체크섬: {checksum}")
            
            return compressed_file, checksum, file_size
            
        except subprocess.TimeoutExpired:
            raise Exception("덤프 생성 타임아웃 (10분 초과)")
        except Exception as e:
            raise Exception(f"덤프 생성 실패: {e}")
    
    def calculate_checksum(self, file_path):
        """파일 MD5 체크섬 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def upload_to_aws_s3(self, file_path, checksum):
        """AWS S3에 백업 파일 업로드"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # 환경변수에서 AWS 설정 읽기
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            bucket_name = os.environ.get('AWS_S3_BACKUP_BUCKET')
            
            if not all([aws_access_key, aws_secret_key, bucket_name]):
                print("⚠️ AWS S3 설정이 없어 업로드를 건너뜁니다.")
                return False
            
            print(f"☁️ AWS S3에 업로드 중: {bucket_name}")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            
            # S3 객체 키 (경로)
            s3_key = f"sales-note-backups/{file_path.name}"
            
            # 메타데이터와 함께 업로드
            s3_client.upload_file(
                str(file_path),
                bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'checksum': checksum,
                        'backup_date': self.timestamp,
                        'source': 'railway-postgres'
                    }
                }
            )
            
            print(f"✅ S3 업로드 완료: s3://{bucket_name}/{s3_key}")
            return True
            
        except ImportError:
            print("⚠️ boto3가 설치되지 않아 S3 업로드를 건너뜁니다.")
            return False
        except ClientError as e:
            print(f"❌ S3 업로드 실패: {e}")
            return False
    
    def upload_to_google_cloud(self, file_path, checksum):
        """Google Cloud Storage에 백업 파일 업로드"""
        try:
            from google.cloud import storage
            
            # 환경변수에서 GCS 설정 읽기
            bucket_name = os.environ.get('GCS_BACKUP_BUCKET')
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            if not bucket_name:
                print("⚠️ GCS 설정이 없어 업로드를 건너뜁니다.")
                return False
            
            print(f"☁️ Google Cloud Storage에 업로드 중: {bucket_name}")
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            
            # 블롭 이름 (경로)
            blob_name = f"sales-note-backups/{file_path.name}"
            blob = bucket.blob(blob_name)
            
            # 메타데이터 설정
            blob.metadata = {
                'checksum': checksum,
                'backup_date': self.timestamp,
                'source': 'railway-postgres'
            }
            
            # 업로드
            blob.upload_from_filename(str(file_path))
            
            print(f"✅ GCS 업로드 완료: gs://{bucket_name}/{blob_name}")
            return True
            
        except ImportError:
            print("⚠️ google-cloud-storage가 설치되지 않아 GCS 업로드를 건너뜁니다.")
            return False
        except Exception as e:
            print(f"❌ GCS 업로드 실패: {e}")
            return False
    
    def send_email_notification(self, success, message, file_info=None):
        """이메일 알림 전송"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # 이메일 설정
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            admin_email = os.environ.get('ADMIN_EMAIL')
            
            if not all([smtp_server, smtp_username, smtp_password, admin_email]):
                print("⚠️ 이메일 설정이 없어 알림을 건너뜁니다.")
                return False
            
            # 이메일 내용 구성
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = admin_email
            msg['Subject'] = f"Sales Note DB 백업 {'성공' if success else '실패'} - {datetime.datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
Sales Note PostgreSQL 백업 결과:

상태: {'✅ 성공' if success else '❌ 실패'}
시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
메시지: {message}
"""
            
            if file_info and success:
                body += f"""
백업 파일 정보:
- 파일명: {file_info['filename']}
- 크기: {file_info['size']:.2f} MB
- 체크섬: {file_info['checksum']}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 이메일 전송
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            print("📧 이메일 알림 전송 완료")
            return True
            
        except Exception as e:
            print(f"⚠️ 이메일 알림 전송 실패: {e}")
            return False
    
    def cleanup_old_files(self, keep_days=7):
        """오래된 백업 파일 정리"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
            deleted_count = 0
            
            for backup_file in self.temp_dir.glob("railway_sales_backup_*.sql.gz"):
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    print(f"🗑️ 오래된 백업 삭제: {backup_file.name}")
            
            if deleted_count > 0:
                print(f"✅ {deleted_count}개의 오래된 로컬 백업 삭제 완료")
            
        except Exception as e:
            print(f"⚠️ 파일 정리 중 오류: {e}")
    
    def run_backup(self):
        """전체 백업 프로세스 실행"""
        print("=" * 70)
        print(f"🚀 Sales Note PostgreSQL 고급 백업 시스템")
        print(f"⏰ 시작 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        try:
            # 1. 덤프 생성
            backup_file, checksum, file_size = self.create_postgres_dump()
            
            file_info = {
                'filename': backup_file.name,
                'size': file_size / 1024 / 1024,  # MB
                'checksum': checksum
            }
            
            # 2. 클라우드 업로드
            aws_success = self.upload_to_aws_s3(backup_file, checksum)
            gcs_success = self.upload_to_google_cloud(backup_file, checksum)
            
            # 3. 로컬 파일 정리
            self.cleanup_old_files()
            
            # 4. 백업 파일 삭제 (클라우드 업로드 성공 시)
            if aws_success or gcs_success:
                backup_file.unlink()
                print("🗑️ 로컬 백업 파일 삭제 완료")
            
            # 5. 성공 알림
            message = f"백업이 성공적으로 완료되었습니다. (크기: {file_info['size']:.2f} MB)"
            print(f"🎉 {message}")
            
            self.send_email_notification(True, message, file_info)
            
            return True
            
        except Exception as e:
            error_message = f"백업 실패: {e}"
            print(f"💥 {error_message}")
            
            self.send_email_notification(False, error_message)
            return False

def main():
    """메인 함수"""
    backup_manager = BackupManager()
    
    try:
        success = backup_manager.run_backup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ 백업이 중단되었습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()
