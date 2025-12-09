"""
Gmail API 연동 유틸리티
- OAuth2 인증
- 이메일 발송
- 이메일 수신 조회
"""

import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header, make_header, decode_header
from email import policy
from email import utils as email_utils
from email.generator import Generator
from io import BytesIO, StringIO
from datetime import datetime, timedelta
import json

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailService:
    """Gmail API 서비스 클래스"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, user_profile):
        """
        Args:
            user_profile: UserProfile 인스턴스
        """
        self.user_profile = user_profile
        self.service = None
    
    def _get_sender_display_name(self):
        """발신자 표시명 생성: 회사명_성명"""
        try:
            user = self.user_profile.user
            company_name = self.user_profile.company.name if self.user_profile.company else ''
            
            # 성명 추출 (first_name + last_name)
            full_name = ''
            if user.first_name and user.last_name:
                full_name = f"{user.first_name}{user.last_name}"
            elif user.first_name:
                full_name = user.first_name
            elif user.last_name:
                full_name = user.last_name
            else:
                full_name = user.username
            
            # 회사명_성명 형식
            if company_name:
                return f"{company_name}_{full_name}"
            else:
                return full_name
        except:
            return None
        
    def get_credentials(self):
        """저장된 토큰으로 Credentials 객체 생성 (자동 갱신 포함)"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.user_profile.gmail_token:
            logger.warning(f'Gmail 토큰 없음 ({self.user_profile.user.username})')
            return None
            
        token_data = self.user_profile.gmail_token
        
        # refresh_token이 없으면 재인증 필요
        if not token_data.get('refresh_token'):
            logger.warning(f'Refresh token 없음 ({self.user_profile.user.username}) - 재인증 필요')
            return None
        
        creds = Credentials(
            token=token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=self.SCOPES
        )
        
        # 토큰 만료 여부 확인 및 자동 갱신
        try:
            if creds.expired and creds.refresh_token:
                logger.info(f'Gmail 토큰 만료됨, 자동 갱신 시도 ({self.user_profile.user.username})')
                creds.refresh(Request())
                self.save_credentials(creds)
                logger.info(f'Gmail 토큰 자동 갱신 성공 ({self.user_profile.user.username})')
        except RefreshError as e:
            # Refresh token도 만료된 경우 - 재인증 필요
            logger.error(f'Gmail 토큰 갱신 실패 - Refresh token 만료 ({self.user_profile.user.username}): {e}')
            # 토큰 정보 삭제 (재인증 유도)
            self.user_profile.gmail_token = None
            self.user_profile.save(update_fields=['gmail_token'])
            return None
        except Exception as e:
            # 기타 오류 - 한 번 더 재시도
            logger.warning(f'Gmail 토큰 갱신 중 오류, 재시도 ({self.user_profile.user.username}): {e}')
            try:
                creds.refresh(Request())
                self.save_credentials(creds)
                logger.info(f'Gmail 토큰 재시도 갱신 성공 ({self.user_profile.user.username})')
            except Exception as retry_error:
                logger.error(f'Gmail 토큰 갱신 재시도 실패 ({self.user_profile.user.username}): {retry_error}')
                # 토큰 정보 삭제 (재인증 유도)
                self.user_profile.gmail_token = None
                self.user_profile.save(update_fields=['gmail_token'])
                return None
            
        return creds
    
    def save_credentials(self, creds):
        """Credentials를 UserProfile에 저장"""
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        self.user_profile.gmail_token = token_data
        self.user_profile.gmail_connected_at = datetime.now()
        self.user_profile.save(update_fields=['gmail_token', 'gmail_connected_at'])
    
    def get_service(self):
        """Gmail API 서비스 객체 반환"""
        if self.service:
            return self.service
            
        creds = self.get_credentials()
        if not creds:
            return None
            
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def send_email(self, to_email, subject, body_text, body_html=None, 
                   cc=None, bcc=None, attachments=None, in_reply_to=None,
                   thread_id=None):
        """
        이메일 발송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            body_text: 텍스트 본문
            body_html: HTML 본문 (선택)
            cc: 참조 이메일 리스트
            bcc: 숨은 참조 이메일 리스트
            attachments: 첨부파일 리스트 [(filename, filepath), ...]
            in_reply_to: 답장할 메시지 ID
            thread_id: 스레드 ID (답장 시)
            
        Returns:
            dict: {'message_id': str, 'thread_id': str} or None
        """
        service = self.get_service()
        if not service:
            return None
        
        try:
            # MIME 메시지 생성
            if body_html or attachments:
                # HTML 본문이 있거나 첨부파일이 있으면 multipart 사용
                message = MIMEMultipart('mixed')
                
                if body_html:
                    # HTML과 텍스트 둘 다 있으면 alternative로 묶음
                    msg_alternative = MIMEMultipart('alternative')
                    part1 = MIMEText(body_text, 'plain', 'utf-8')
                    part2 = MIMEText(body_html, 'html', 'utf-8')
                    msg_alternative.attach(part1)
                    msg_alternative.attach(part2)
                    message.attach(msg_alternative)
                else:
                    # 텍스트만 있으면 그냥 추가
                    part1 = MIMEText(body_text, 'plain', 'utf-8')
                    message.attach(part1)
            else:
                message = MIMEText(body_text, 'plain', 'utf-8')
            
            # 헤더 설정
            message['To'] = to_email
            
            # 발신자 표시명: "회사명_성명" <이메일>
            from_name = self._get_sender_display_name()
            if from_name:
                message['From'] = f"{from_name} <{self.user_profile.gmail_email}>"
            else:
                message['From'] = self.user_profile.gmail_email
            
            # 한글 제목 - RFC2047 방식으로 인코딩 (Gmail 호환성)
            message['Subject'] = str(Header(subject, 'utf-8'))
            
            if cc:
                message['Cc'] = ', '.join(cc) if isinstance(cc, list) else cc
            if bcc:
                message['Bcc'] = ', '.join(bcc) if isinstance(bcc, list) else bcc
                
            # 답장 헤더
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to
            
            # 첨부파일 처리
            if attachments:
                for attachment in attachments:
                    # 딕셔너리 형태: {'filename': str, 'content': bytes, 'mimetype': str}
                    if isinstance(attachment, dict):
                        filename = attachment['filename']
                        content = attachment['content']
                        mimetype = attachment.get('mimetype', 'application/octet-stream')
                        
                        if '/' in mimetype:
                            maintype, subtype = mimetype.split('/', 1)
                        else:
                            maintype, subtype = 'application', 'octet-stream'
                        
                        part = MIMEBase(maintype, subtype)
                        part.set_payload(content)
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 
                                      'attachment', filename=filename)
                        message.attach(part)
                    # 튜플 형태: (filename, filepath)
                    else:
                        filename, filepath = attachment
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', 
                                          'attachment', filename=filename)
                            message.attach(part)
            
            # Base64 인코딩 - SMTP 정책 사용 (ASCII 헤더, Gmail 호환성)
            from email import policy
            msg_bytes = message.as_bytes(policy=policy.SMTP)
            raw_message = base64.urlsafe_b64encode(msg_bytes).decode('ascii')
            
            # 발송
            send_params = {'raw': raw_message}
            if thread_id:
                send_params['threadId'] = thread_id
                
            result = service.users().messages().send(
                userId='me',
                body=send_params
            ).execute()
            
            return {
                'message_id': result['id'],
                'thread_id': result['threadId']
            }
            
        except HttpError as error:
            print(f'Gmail API 오류: {error}')
            return None
    
    def get_messages(self, query='', max_results=50, page_token=None):
        """
        메시지 목록 조회
        
        Args:
            query: Gmail 검색 쿼리 (예: 'from:example@gmail.com')
            max_results: 최대 결과 수
            page_token: 페이지네이션 토큰
            
        Returns:
            dict: {'messages': [...], 'next_page_token': str}
        """
        service = self.get_service()
        if not service:
            return {'messages': [], 'next_page_token': None}
        
        try:
            params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            if query:
                params['q'] = query
            if page_token:
                params['pageToken'] = page_token
                
            results = service.users().messages().list(**params).execute()
            
            messages = results.get('messages', [])
            next_page_token = results.get('nextPageToken')
            
            return {
                'messages': messages,
                'next_page_token': next_page_token
            }
            
        except HttpError as error:
            print(f'Gmail API 오류: {error}')
            return {'messages': [], 'next_page_token': None}
    
    def get_message_detail(self, message_id):
        """
        메시지 상세 정보 조회
        
        Args:
            message_id: Gmail 메시지 ID
            
        Returns:
            dict: 메시지 상세 정보
        """
        service = self.get_service()
        if not service:
            return None
        
        try:
            from email.header import decode_header, make_header
            
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # 헤더 파싱
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # 본문 추출 - 재귀적으로 모든 parts 처리
            def extract_body_parts(parts):
                """재귀적으로 모든 본문 파트 추출"""
                text_parts = []
                html_parts = []
                
                for part in parts:
                    mime_type = part.get('mimeType', '')
                    
                    # multipart인 경우 재귀 처리
                    if mime_type.startswith('multipart/') and 'parts' in part:
                        sub_text, sub_html = extract_body_parts(part['parts'])
                        text_parts.extend(sub_text)
                        html_parts.extend(sub_html)
                    # text/plain
                    elif mime_type == 'text/plain' and 'data' in part.get('body', {}):
                        try:
                            decoded = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            text_parts.append(decoded)
                        except Exception as e:
                            print(f'텍스트 디코딩 실패: {e}')
                    # text/html
                    elif mime_type == 'text/html' and 'data' in part.get('body', {}):
                        try:
                            decoded = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            html_parts.append(decoded)
                        except Exception as e:
                            print(f'HTML 디코딩 실패: {e}')
                
                return text_parts, html_parts
            
            body_text = ''
            body_html = ''
            
            if 'parts' in message['payload']:
                text_parts, html_parts = extract_body_parts(message['payload']['parts'])
                body_text = '\n'.join(text_parts)
                body_html = ''.join(html_parts)
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                try:
                    body_text = base64.urlsafe_b64decode(
                        message['payload']['body']['data']
                    ).decode('utf-8')
                except Exception as e:
                    print(f'본문 디코딩 실패: {e}')
            
            # Subject RFC2047 디코딩
            raw_subject = headers.get('subject', '(제목 없음)')
            try:
                decoded_subject = str(make_header(decode_header(raw_subject)))
            except Exception as e:
                decoded_subject = raw_subject
            
            return {
                'id': message['id'],
                'thread_id': message['threadId'],
                'subject': decoded_subject,
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'cc': headers.get('cc', ''),
                'date': headers.get('date', ''),
                'body_text': body_text,
                'body_html': body_html,
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'in_reply_to': headers.get('in-reply-to', ''),
                'references': headers.get('references', ''),
            }
            
        except HttpError as error:
            print(f'Gmail API 오류: {error}')
            return None
    
    def mark_as_read(self, message_id):
        """메시지를 읽음으로 표시"""
        service = self.get_service()
        if not service:
            return False
        
        try:
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f'Gmail API 오류: {error}')
            return False
    
    def get_thread(self, thread_id):
        """스레드 전체 메시지 조회"""
        service = self.get_service()
        if not service:
            return None
        
        try:
            thread = service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            messages = []
            for msg in thread.get('messages', []):
                detail = self.get_message_detail(msg['id'])
                if detail:
                    messages.append(detail)
            
            return {
                'id': thread['id'],
                'messages': messages
            }
            
        except HttpError as error:
            print(f'Gmail API 오류: {error}')
            return None


def get_authorization_url(redirect_uri):
    """OAuth2 인증 URL 생성"""
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise ValueError('Gmail API 설정(GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET)이 설정되지 않았습니다.')
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=GmailService.SCOPES,
        redirect_uri=redirect_uri
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return authorization_url, state


def exchange_code_for_token(code, redirect_uri):
    """인증 코드를 토큰으로 교환"""
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise ValueError('Gmail API 설정(GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET)이 설정되지 않았습니다.')
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=GmailService.SCOPES,
        redirect_uri=redirect_uri
    )
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # 사용자 이메일 조회
    service = build('gmail', 'v1', credentials=credentials)
    profile = service.users().getProfile(userId='me').execute()
    
    return credentials, profile.get('emailAddress')
