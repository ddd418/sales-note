"""
IMAP/SMTP 이메일 통합 유틸리티
커스텀 도메인 이메일(@inside.com 등) 연동 지원
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email import encoders
from email.header import decode_header
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailEncryption:
    """이메일 비밀번호 암호화/복호화"""
    
    @staticmethod
    def get_cipher():
        """암호화 키 가져오기 (settings에서)"""
        key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', Fernet.generate_key())
        return Fernet(key)
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """비밀번호 암호화"""
        if not password:
            return ""
        cipher = EmailEncryption.get_cipher()
        return cipher.encrypt(password.encode()).decode()
    
    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """비밀번호 복호화"""
        if not encrypted_password:
            return ""
        try:
            cipher = EmailEncryption.get_cipher()
            return cipher.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"비밀번호 복호화 실패: {e}")
            return ""


class IMAPEmailService:
    """IMAP을 통한 이메일 수신 서비스"""
    
    def __init__(self, user_profile):
        self.user_profile = user_profile
        self.imap = None
    
    def connect(self) -> bool:
        """IMAP 서버에 연결"""
        try:
            host = self.user_profile.imap_host
            port = self.user_profile.imap_port
            username = self.user_profile.imap_username
            password = EmailEncryption.decrypt_password(self.user_profile.imap_password)
            
            if not all([host, username, password]):
                logger.error("IMAP 연결 정보가 불완전합니다.")
                return False
            
            # SSL 연결
            if self.user_profile.imap_use_ssl:
                self.imap = imaplib.IMAP4_SSL(host, port)
            else:
                self.imap = imaplib.IMAP4(host, port)
            
            # 로그인
            self.imap.login(username, password)
            logger.info(f"IMAP 연결 성공: {username}@{host}")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP 인증 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"IMAP 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """IMAP 연결 종료"""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
    
    def get_folders(self) -> List[str]:
        """사용 가능한 메일함 목록 조회"""
        try:
            status, folders = self.imap.list()
            if status != 'OK':
                return []
            
            folder_list = []
            for folder in folders:
                # 폴더명 디코딩
                folder_str = folder.decode() if isinstance(folder, bytes) else folder
                # 폴더명 추출 (마지막 부분)
                parts = folder_str.split('"')
                if len(parts) >= 3:
                    folder_list.append(parts[-2])
            
            return folder_list
        except Exception as e:
            logger.error(f"메일함 목록 조회 실패: {e}")
            return []
    
    def fetch_emails(self, folder: str = 'INBOX', days: int = 7, target_emails: List[str] = None) -> List[Dict]:
        """이메일 가져오기
        
        Args:
            folder: 메일함 이름 (기본: INBOX)
            days: 조회 기간 (일)
            target_emails: 필터링할 이메일 주소 목록
        
        Returns:
            이메일 정보 딕셔너리 리스트
        """
        try:
            # 메일함 선택
            status, messages = self.imap.select(folder, readonly=True)
            if status != 'OK':
                logger.error(f"메일함 선택 실패: {folder}")
                return []
            
            # 날짜 필터 생성
            since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            
            # 이메일 검색
            search_criteria = f'(SINCE {since_date})'
            status, message_ids = self.imap.search(None, search_criteria)
            
            if status != 'OK':
                logger.error("이메일 검색 실패")
                return []
            
            email_list = []
            message_id_list = message_ids[0].split()
            
            # 최신 메일부터 처리 (역순)
            for msg_id in reversed(message_id_list[-100:]):  # 최대 100개
                try:
                    email_data = self._fetch_email_by_id(msg_id, target_emails)
                    if email_data:
                        email_list.append(email_data)
                except Exception as e:
                    logger.error(f"이메일 처리 실패 (ID: {msg_id}): {e}")
                    continue
            
            return email_list
            
        except Exception as e:
            logger.error(f"이메일 가져오기 실패: {e}")
            return []
    
    def _fetch_email_by_id(self, msg_id: bytes, target_emails: List[str] = None) -> Optional[Dict]:
        """개별 이메일 가져오기"""
        try:
            status, msg_data = self.imap.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return None
            
            # 이메일 파싱
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # 발신자
            from_header = email_message.get('From', '')
            from_email = self._extract_email_address(from_header)
            from_name = self._decode_header(from_header)
            
            # 수신자
            to_header = email_message.get('To', '')
            to_email = self._extract_email_address(to_header)
            
            # 참조
            cc_header = email_message.get('Cc', '')
            cc_emails = self._extract_email_addresses(cc_header) if cc_header else []
            
            # 필터링 (target_emails가 있는 경우)
            if target_emails:
                all_recipients = [to_email] + cc_emails
                if not any(email in target_emails for email in [from_email] + all_recipients):
                    return None
            
            # 제목
            subject = self._decode_header(email_message.get('Subject', ''))
            
            # 날짜
            date_str = email_message.get('Date', '')
            date = self._parse_email_date(date_str)
            
            # 본문
            body = self._get_email_body(email_message)
            
            # Message-ID
            message_id = email_message.get('Message-ID', '')
            in_reply_to = email_message.get('In-Reply-To', '')
            
            return {
                'message_id': message_id,
                'thread_id': in_reply_to or message_id,  # 스레드 ID (답장이면 원본 ID)
                'from_email': from_email,
                'from_name': from_name,
                'to_email': to_email,
                'cc_emails': cc_emails,
                'subject': subject,
                'body': body,
                'date': date,
                'is_sent': False,  # 수신 메일
            }
            
        except Exception as e:
            logger.error(f"이메일 파싱 실패: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """이메일 헤더 디코딩"""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
    
    def _extract_email_address(self, header: str) -> str:
        """헤더에서 이메일 주소만 추출"""
        if not header:
            return ""
        
        # <email@example.com> 형식에서 추출
        if '<' in header and '>' in header:
            start = header.index('<') + 1
            end = header.index('>')
            return header[start:end].strip()
        
        # 공백으로 분리된 경우
        parts = header.split()
        for part in parts:
            if '@' in part:
                return part.strip('<>').strip()
        
        return header.strip()
    
    def _extract_email_addresses(self, header: str) -> List[str]:
        """헤더에서 여러 이메일 주소 추출"""
        if not header:
            return []
        
        addresses = []
        for part in header.split(','):
            email_addr = self._extract_email_address(part.strip())
            if email_addr:
                addresses.append(email_addr)
        
        return addresses
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """이메일 날짜 파싱"""
        if not date_str:
            return timezone.now()
        
        try:
            # email.utils.parsedate_to_datetime 사용
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.error(f"날짜 파싱 실패: {date_str}, {e}")
            return timezone.now()
    
    def _get_email_body(self, email_message) -> str:
        """이메일 본문 추출"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # 첨부파일 건너뛰기
                if 'attachment' in content_disposition:
                    continue
                
                # 텍스트 본문
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break  # 첫 번째 텍스트 본문만 사용
                    except Exception as e:
                        logger.error(f"본문 디코딩 실패: {e}")
                        continue
                
                # HTML 본문 (텍스트가 없는 경우)
                elif content_type == 'text/html' and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                    except Exception as e:
                        logger.error(f"HTML 본문 디코딩 실패: {e}")
                        continue
        else:
            # 단일 파트 메시지
            try:
                payload = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except Exception as e:
                logger.error(f"본문 디코딩 실패: {e}")
                body = str(email_message.get_payload())
        
        return body


class SMTPEmailService:
    """SMTP를 통한 이메일 발송 서비스"""
    
    def __init__(self, user_profile):
        self.user_profile = user_profile
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   cc_emails: List[str] = None, bcc_emails: List[str] = None,
                   html_body: str = None, attachments: List[dict] = None,
                   in_reply_to: str = None, references: str = None) -> bool:
        """이메일 발송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            body: 본문 (텍스트)
            cc_emails: 참조 이메일 리스트
            bcc_emails: 숨은 참조 이메일 리스트
            html_body: HTML 본문
            attachments: 첨부파일 리스트 [{'filename': str, 'content': bytes, 'content_type': str}]
            in_reply_to: 답장 대상 Message-ID
            references: 참조 Message-ID들
        
        Returns:
            발송 성공 여부
        """
        try:
            # SMTP 설정
            host = self.user_profile.smtp_host
            port = self.user_profile.smtp_port
            username = self.user_profile.smtp_username
            password = EmailEncryption.decrypt_password(self.user_profile.smtp_password)
            from_email = self.user_profile.imap_email or username
            
            if not all([host, username, password]):
                logger.error("SMTP 설정 정보가 불완전합니다.")
                return False
            
            # 메시지 생성 (첨부파일이 있으면 multipart/mixed 사용)
            if attachments:
                msg = MIMEMultipart('mixed')
                # 본문 파트 생성
                if html_body:
                    msg_alternative = MIMEMultipart('alternative')
                    msg_alternative.attach(MIMEText(body, 'plain', 'utf-8'))
                    msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))
                    msg.attach(msg_alternative)
                else:
                    msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 첨부파일 추가
                for attachment in attachments:
                    filename = attachment.get('filename', 'attachment')
                    content = attachment.get('content', b'')
                    content_type = attachment.get('content_type', 'application/octet-stream')
                    
                    # MIME 타입 파싱
                    maintype, subtype = content_type.split('/', 1) if '/' in content_type else ('application', 'octet-stream')
                    
                    if maintype == 'text':
                        part = MIMEText(content.decode('utf-8'), _subtype=subtype)
                    elif maintype == 'image':
                        part = MIMEImage(content, _subtype=subtype)
                    elif maintype == 'audio':
                        part = MIMEAudio(content, _subtype=subtype)
                    else:
                        part = MIMEBase(maintype, subtype)
                        part.set_payload(content)
                        encoders.encode_base64(part)
                    
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
            elif html_body:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            else:
                msg = MIMEText(body, 'plain', 'utf-8')
            
            # 헤더 설정
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            if bcc_emails:
                msg['Bcc'] = ', '.join(bcc_emails)
            
            # 스레드 헤더 (답장인 경우)
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
            if references:
                msg['References'] = references
            
            # SMTP 연결 및 발송
            if self.user_profile.smtp_use_tls:
                smtp = smtplib.SMTP(host, port)
                smtp.starttls()
            else:
                smtp = smtplib.SMTP_SSL(host, port)
            
            smtp.login(username, password)
            
            # 수신자 목록 (To, Cc, Bcc 모두 포함)
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)
            
            smtp.sendmail(from_email, recipients, msg.as_string())
            smtp.quit()
            
            logger.info(f"이메일 발송 성공: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 인증 실패: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False


def test_imap_connection(host: str, port: int, username: str, password: str, use_ssl: bool = True) -> Tuple[bool, str]:
    """IMAP 연결 테스트
    
    Returns:
        (성공 여부, 메시지)
    """
    try:
        if use_ssl:
            imap = imaplib.IMAP4_SSL(host, port, timeout=10)
        else:
            imap = imaplib.IMAP4(host, port, timeout=10)
        
        imap.login(username, password)
        imap.logout()
        
        return True, "연결 성공"
    except imaplib.IMAP4.error as e:
        return False, f"인증 실패: {str(e)}"
    except Exception as e:
        return False, f"연결 실패: {str(e)}"


def test_smtp_connection(host: str, port: int, username: str, password: str, use_tls: bool = True) -> Tuple[bool, str]:
    """SMTP 연결 테스트
    
    Returns:
        (성공 여부, 메시지)
    """
    try:
        if use_tls:
            smtp = smtplib.SMTP(host, port, timeout=10)
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(host, port, timeout=10)
        
        smtp.login(username, password)
        smtp.quit()
        
        return True, "연결 성공"
    except smtplib.SMTPAuthenticationError as e:
        return False, f"인증 실패: {str(e)}"
    except smtplib.SMTPException as e:
        return False, f"SMTP 오류: {str(e)}"
    except Exception as e:
        return False, f"연결 실패: {str(e)}"


# 기본 IMAP/SMTP 설정 프리셋
EMAIL_PRESETS = {
    'gmail': {
        'imap_host': 'imap.gmail.com',
        'imap_port': 993,
        'imap_use_ssl': True,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_use_tls': True,
    },
    'outlook': {
        'imap_host': 'outlook.office365.com',
        'imap_port': 993,
        'imap_use_ssl': True,
        'smtp_host': 'smtp.office365.com',
        'smtp_port': 587,
        'smtp_use_tls': True,
    },
    'naver': {
        'imap_host': 'imap.naver.com',
        'imap_port': 993,
        'imap_use_ssl': True,
        'smtp_host': 'smtp.naver.com',
        'smtp_port': 587,
        'smtp_use_tls': True,
    },
}
