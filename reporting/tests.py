import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.utils import timezone
from reporting.models import (
    Company,
    Department,
    DocumentGenerationLog,
    DocumentTemplate,
    EmailLog,
    FollowUp,
    Schedule,
    UserProfile,
    UserCompany,
)


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼: 역할이 있는 사용자 생성
# ─────────────────────────────────────────────────────────────────────────────

def make_user(username, password='TestPass123!', role='salesman',
              can_use_ai=False, can_download_excel=False, company=None):
    """테스트용 사용자 생성 헬퍼"""
    user = User.objects.create_user(username=username, password=password)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.can_use_ai = can_use_ai
    profile.can_download_excel = can_download_excel
    if company:
        profile.company = company
    profile.save()
    return user


class AuthenticationSmoke(TestCase):
    """인증 기본 smoke 테스트"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass123!',
        )

    def test_login_page_returns_200(self):
        """로그인 페이지 접근 가능"""
        response = self.client.get(reverse('reporting:login'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_followup_list_redirects(self):
        """미인증 상태에서 거래처 목록 접근 시 로그인으로 리다이렉트"""
        response = self.client.get(reverse('reporting:followup_list'))
        self.assertIn(response.status_code, [302, 301])
        self.assertIn('/login', response.get('Location', ''))

    def test_login_success(self):
        """올바른 자격 증명으로 로그인하면 프론트 CRM 대시보드로 이동"""
        response = self.client.post(
            reverse('reporting:login'),
            {'username': 'testuser', 'password': 'TestPass123!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            'https://sales-note-frontend-production.up.railway.app/dashboard/',
        )
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(self.user.id))

    def test_login_fail_wrong_password(self):
        """잘못된 비밀번호로 로그인 실패"""
        response = self.client.post(
            reverse('reporting:login'),
            {'username': 'testuser', 'password': 'wrongpassword'},
        )
        self.assertEqual(response.status_code, 200)  # 로그인 페이지 재표시

    def test_followup_list_authenticated(self):
        """인증 후 거래처 목록 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:followup_list'))
        self.assertEqual(response.status_code, 200)

    def test_opportunity_list_url_removed(self):
        """별도 영업기회 목록 URL은 제거되어야 함"""
        self.client.force_login(self.user)
        response = self.client.get('/reporting/opportunities/')
        self.assertEqual(response.status_code, 404)

    def test_schedule_list_authenticated(self):
        """인증 후 일정 목록 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:schedule_list'))
        self.assertEqual(response.status_code, 200)

    def test_schedule_calendar_authenticated(self):
        """인증 후 일정 캘린더 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:schedule_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '일정 캘린더')

    def test_history_list_authenticated(self):
        """인증 후 영업 활동 목록 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:history_list'))
        self.assertEqual(response.status_code, 200)


class GmailMailboxThreadRegressionTests(TestCase):
    """Gmail 스레드 상세 Railway 500 회귀 테스트"""

    def test_thread_detail_template_compiles(self):
        template = get_template('reporting/gmail/thread_detail.html')
        self.assertIsNotNone(template)

    def test_save_email_to_db_accepts_gmail_thread_message(self):
        from reporting.imap_utils import save_email_to_db

        user = User.objects.create_user(
            username='mailbox-user',
            password='TestPass123!',
            email='sales@example.com',
        )

        email_log = save_email_to_db(
            user=user,
            message_id='gmail-msg-1',
            thread_id='gmail-thread-1',
            sender_email='Customer Name <customer@example.com>',
            recipient_email='Sales User <sales@example.com>',
            cc_emails='Manager <manager@example.com>',
            subject='Railway thread regression',
            body='고객 문의 내용입니다.',
            body_html='<p>고객 문의 내용입니다.</p>',
            sent_at='Wed, 08 May 2024 12:30:00 +0900',
            email_type='received',
            labels=['INBOX', 'UNREAD'],
        )

        self.assertEqual(EmailLog.objects.count(), 1)
        self.assertEqual(email_log.gmail_message_id, 'gmail-msg-1')
        self.assertEqual(email_log.gmail_thread_id, 'gmail-thread-1')
        self.assertEqual(email_log.sender_email, 'customer@example.com')
        self.assertEqual(email_log.recipient_email, 'sales@example.com')
        self.assertEqual(email_log.cc_emails, 'manager@example.com')
        self.assertEqual(email_log.email_type, 'received')
        self.assertEqual(email_log.status, 'received')
        self.assertFalse(email_log.is_read)
        self.assertIsNotNone(email_log.sent_at)
        self.assertIsNotNone(email_log.received_at)


class ReactMailboxApiTests(TestCase):
    """React 메일함 API 회귀 테스트"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='Hana CRM')
        self.user = make_user('mail-api-user', company=self.company)
        self.other_user = make_user('mail-api-other', company=self.company)
        self.customer_company = Company.objects.create(name='고객사 A', created_by=self.user)
        self.department = Department.objects.create(
            company=self.customer_company,
            name='연구실 A',
            created_by=self.user,
        )
        self.followup = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='김고객',
            email='customer@example.com',
        )
        self.other_followup = FollowUp.objects.create(
            user=self.other_user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='다른고객',
            email='other@example.com',
        )
        self.email = EmailLog.objects.create(
            email_type='received',
            sender_email='customer@example.com',
            recipient_email='sales@example.com',
            subject='React mailbox inbound',
            body='고객이 보낸 중요한 요청입니다.\n\n첫 번째 확인 사항입니다.\n두 번째 확인 사항입니다.',
            gmail_message_id='gmail-msg-react-1',
            gmail_thread_id='gmail-thread-react-1',
            followup=self.followup,
            status='received',
            received_at=timezone.now(),
            is_read=False,
        )
        EmailLog.objects.create(
            email_type='received',
            sender_email='other@example.com',
            recipient_email='sales@example.com',
            subject='Hidden mailbox inbound',
            body='다른 담당자 메일입니다.',
            gmail_message_id='gmail-msg-hidden-1',
            gmail_thread_id='gmail-thread-hidden-1',
            followup=self.other_followup,
            status='received',
            received_at=timezone.now(),
        )

    def test_mailbox_api_lists_only_current_users_customer_mail(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:mailbox_api_list'), {'box': 'inbox'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['source'], 'django')
        self.assertEqual(payload['counts']['inbox'], 1)
        self.assertEqual(len(payload['emails']), 1)
        self.assertEqual(payload['emails'][0]['subject'], 'React mailbox inbound')
        self.assertEqual(payload['emails'][0]['threadHref'], '/mailbox/thread/gmail-thread-react-1/')
        self.assertEqual(payload['create']['customers'][0]['email'], 'customer@example.com')

    def test_mailbox_thread_api_marks_received_mail_read(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['thread']['messageCount'], 1)
        self.assertIn('중요한 요청', payload['emails'][0]['bodyText'])
        self.assertIn('\n\n첫 번째 확인 사항입니다.\n두 번째 확인 사항입니다.', payload['emails'][0]['bodyText'])
        self.email.refresh_from_db()
        self.assertTrue(self.email.is_read)

    def test_mailbox_thread_api_hides_quoted_reply_chain_from_display_body(self):
        self.email.body = (
            '이번 답장에 새로 작성한 내용입니다.\n\n'
            '검토 부탁드립니다.\n\n'
            '2026년 5월 10일 (일) 오후 3:00, 영업팀 <sales@example.com>님이 작성:\n'
            '> 이전 메일 내용입니다.\n'
            '> 더 오래된 답장입니다.'
        )
        self.email.save(update_fields=['body'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        body_text = response.json()['emails'][0]['bodyText']
        self.assertIn('이번 답장에 새로 작성한 내용입니다.', body_text)
        self.assertIn('검토 부탁드립니다.', body_text)
        self.assertNotIn('이전 메일 내용입니다.', body_text)
        self.assertNotIn('더 오래된 답장입니다.', body_text)

    def test_mailbox_thread_api_hides_gmail_html_quote_from_display_body(self):
        self.email.body = ''
        self.email.body_html = (
            '<div>새 답장 본문입니다.</div>'
            '<div>두 번째 줄입니다.</div>'
            '<div class="gmail_quote">'
            '<div>2026년 5월 10일 영업팀 &lt;sales@example.com&gt;님이 작성:</div>'
            '<blockquote>이전 메일 HTML 본문입니다.</blockquote>'
            '</div>'
        )
        self.email.save(update_fields=['body', 'body_html'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        body_text = response.json()['emails'][0]['bodyText']
        self.assertIn('새 답장 본문입니다.', body_text)
        self.assertIn('두 번째 줄입니다.', body_text)
        self.assertNotIn('이전 메일 HTML 본문입니다.', body_text)

    def test_mailbox_action_api_toggles_star(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:mailbox_api_toggle_star', args=[self.email.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.email.refresh_from_db()
        self.assertTrue(self.email.is_starred)

    def test_mailbox_send_api_accepts_attachments(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)

        uploaded_file = SimpleUploadedFile(
            'quote.txt',
            b'quote attachment body',
            content_type='text/plain',
        )

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-react-attachment',
                'thread_id': 'gmail-thread-react-attachment',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '첨부 테스트',
                    'body_text': '첨부파일 확인 부탁드립니다.',
                    'selected_followup_id': str(self.followup.id),
                    'attachments': uploaded_file,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        gmail_service.send_email.assert_called_once()
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual(sent_attachments[0]['filename'], 'quote.txt')
        self.assertEqual(sent_attachments[0]['content'], b'quote attachment body')
        self.assertEqual(sent_attachments[0]['mimetype'], 'text/plain')

        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-react-attachment')
        self.assertEqual(email_log.attachments_info[0]['filename'], 'quote.txt')
        self.assertEqual(email_log.attachments_info[0]['size'], len(b'quote attachment body'))
        self.assertEqual(email_log.attachments_info[0]['mimetype'], 'text/plain')

    def test_mailbox_send_api_auto_attaches_registered_quote_pdfs_for_schedule(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='quote',
        )
        first_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=schedule,
            user=self.user,
            transaction_number='QUOTE-PDF-001',
            output_format='pdf',
            file=SimpleUploadedFile('quote-one.pdf', b'%PDF quote one', content_type='application/pdf'),
            filename='quote-one.pdf',
            file_size=len(b'%PDF quote one'),
        )
        second_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=schedule,
            user=self.user,
            transaction_number='QUOTE-PDF-002',
            output_format='pdf',
            file=SimpleUploadedFile('quote-two.pdf', b'%PDF quote two', content_type='application/pdf'),
            filename='quote-two.pdf',
            file_size=len(b'%PDF quote two'),
        )
        delivery_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='delivery_note',
            schedule=schedule,
            user=self.user,
            transaction_number='DELIVERY-PDF-001',
            output_format='pdf',
            file=SimpleUploadedFile('delivery.pdf', b'%PDF delivery', content_type='application/pdf'),
            filename='delivery.pdf',
            file_size=len(b'%PDF delivery'),
        )
        self.addCleanup(first_log.file.delete, False)
        self.addCleanup(second_log.file.delete, False)
        self.addCleanup(delivery_log.file.delete, False)
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-auto-quote-docs',
                'thread_id': 'gmail-thread-auto-quote-docs',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '견적서 전달',
                    'body_text': '견적서 확인 부탁드립니다.',
                    'schedule_id': str(schedule.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual([item['filename'] for item in sent_attachments], ['quote-one.pdf', 'quote-two.pdf'])
        self.assertEqual(sent_attachments[0]['content'], b'%PDF quote one')
        self.assertEqual(sent_attachments[1]['mimetype'], 'application/pdf')

        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-auto-quote-docs')
        self.assertEqual(email_log.schedule, schedule)
        self.assertEqual(email_log.followup, self.followup)
        self.assertEqual([item['filename'] for item in email_log.attachments_info], ['quote-one.pdf', 'quote-two.pdf'])
        self.assertEqual(email_log.attachments_info[0]['source'], 'quote_document')
        self.assertEqual(email_log.attachments_info[0]['documentLogId'], first_log.id)

    def test_mailbox_send_api_generates_quote_pdf_when_schedule_has_no_registered_pdf(self):
        from django.http import HttpResponse

        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='quote',
        )
        self.client.force_login(self.user)
        document_response = HttpResponse(b'%PDF generated quote', content_type='application/pdf')
        document_response['X-Filename'] = 'generated-quote.pdf'

        with patch('reporting.views.generate_document_pdf', return_value=document_response) as generate_pdf:
            with patch('reporting.gmail_views.GmailService') as gmail_service_class:
                gmail_service = gmail_service_class.return_value
                gmail_service.send_email.return_value = {
                    'message_id': 'gmail-sent-generated-quote',
                    'thread_id': 'gmail-thread-generated-quote',
                }

                response = self.client.post(
                    reverse('reporting:mailbox_api_send'),
                    {
                        'to_email': 'customer@example.com',
                        'subject': '견적서 자동 생성',
                        'body_text': '견적서 확인 부탁드립니다.',
                        'schedule_id': str(schedule.id),
                    },
                )

        self.assertEqual(response.status_code, 200)
        generate_pdf.assert_called_once()
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual(sent_attachments[0]['filename'], 'generated-quote.pdf')
        self.assertEqual(sent_attachments[0]['content'], b'%PDF generated quote')
        self.assertEqual(sent_attachments[0]['mimetype'], 'application/pdf')

    def test_mailbox_send_api_generates_quote_pdf_per_quote_group_when_no_registered_pdf(self):
        from django.http import HttpResponse
        from reporting.models import DeliveryItem

        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='quote',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Trade In Kit',
            quantity=1,
            unit='EA',
            unit_price=100000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Repair Service',
            quantity=1,
            unit='EA',
            unit_price=50000,
            quote_group='수리',
        )
        first_response = HttpResponse(b'%PDF trade in quote', content_type='application/pdf')
        first_response['X-Filename'] = 'trade-in-quote.pdf'
        second_response = HttpResponse(b'%PDF repair quote', content_type='application/pdf')
        second_response['X-Filename'] = 'repair-quote.pdf'
        self.client.force_login(self.user)

        with patch('reporting.views.generate_document_pdf', side_effect=[first_response, second_response]) as generate_pdf:
            with patch('reporting.gmail_views.GmailService') as gmail_service_class:
                gmail_service = gmail_service_class.return_value
                gmail_service.send_email.return_value = {
                    'message_id': 'gmail-sent-generated-grouped-quote',
                    'thread_id': 'gmail-thread-generated-grouped-quote',
                }

                response = self.client.post(
                    reverse('reporting:mailbox_api_send'),
                    {
                        'to_email': 'customer@example.com',
                        'subject': '견적서 자동 생성',
                        'body_text': '견적서 확인 부탁드립니다.',
                        'schedule_id': str(schedule.id),
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(generate_pdf.call_count, 2)
        self.assertEqual([call.kwargs['quote_group'] for call in generate_pdf.call_args_list], ['보상판매', '수리'])
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual([item['filename'] for item in sent_attachments], ['trade-in-quote.pdf', 'repair-quote.pdf'])
        self.assertEqual(sent_attachments[0]['content'], b'%PDF trade in quote')
        self.assertEqual(sent_attachments[1]['content'], b'%PDF repair quote')

    def test_mailbox_send_api_does_not_auto_attach_for_delivery_schedule(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='delivery',
        )
        log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=schedule,
            user=self.user,
            transaction_number='QUOTE-IGNORED-001',
            output_format='pdf',
            file=SimpleUploadedFile('ignored-quote.pdf', b'%PDF ignored', content_type='application/pdf'),
            filename='ignored-quote.pdf',
            file_size=len(b'%PDF ignored'),
        )
        self.addCleanup(log.file.delete, False)
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-delivery-no-auto',
                'thread_id': 'gmail-thread-delivery-no-auto',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '납품 일정 메일',
                    'body_text': '일정 확인 부탁드립니다.',
                    'schedule_id': str(schedule.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual(sent_attachments, [])

    def test_mailbox_send_api_normalizes_plain_text_line_breaks_for_html(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)

        body_text = (
            '안녕하세요 이다민 연구원님.\r\n'
            '하나과학 안재현 대리입니다.\r\n'
            '\r\n'
            '5 < 10 & 확인 부탁드립니다.'
        )

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-linebreak-normalized',
                'thread_id': 'gmail-thread-linebreak-normalized',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '줄바꿈 테스트',
                    'body_text': body_text,
                    'selected_followup_id': str(self.followup.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_kwargs = gmail_service.send_email.call_args.kwargs
        self.assertEqual(
            sent_kwargs['body_text'],
            '안녕하세요 이다민 연구원님.\n'
            '하나과학 안재현 대리입니다.\n'
            '\n'
            '5 < 10 & 확인 부탁드립니다.',
        )
        body_html = sent_kwargs['body_html']
        self.assertIn('안녕하세요 이다민 연구원님.<br>\n하나과학 안재현 대리입니다.', body_html)
        self.assertIn('하나과학 안재현 대리입니다.<br>\n<br>\n5 &lt; 10 &amp; 확인 부탁드립니다.', body_html)
        self.assertEqual(body_html.count('<br>'), 3)
        self.assertNotIn('\r', body_html)
        self.assertNotIn('white-space: pre-wrap', body_html)

        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-linebreak-normalized')
        self.assertEqual(email_log.body, sent_kwargs['body_text'])
        self.assertEqual(email_log.body_html.count('<br>'), 3)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: 익명 사용자 URL 차단 테스트
# ─────────────────────────────────────────────────────────────────────────────

class AnonymousAccessTests(TestCase):
    """익명 사용자가 모든 내부 CRM 페이지에 접근할 수 없음을 검증"""

    def setUp(self):
        self.client = Client()

    def _assert_redirects_to_login(self, url):
        response = self.client.get(url)
        self.assertIn(
            response.status_code, [301, 302],
            msg=f"Expected redirect for anonymous access to {url}, got {response.status_code}"
        )
        location = response.get('Location', '')
        self.assertIn('login', location, msg=f"Redirect target should be login for {url}, got {location}")

    def test_dashboard_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:dashboard'))

    def test_followup_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:followup_list'))

    def test_history_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:history_list'))

    def test_schedule_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:schedule_list'))

    def test_schedule_calendar_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:schedule_calendar'))

    def test_funnel_pipeline_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:funnel_pipeline'))

    def test_weekly_report_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:weekly_report_list'))

    def test_document_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:document_template_list'))

    def test_analytics_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:analytics_dashboard'))

    def test_analytics_activity_csv_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:analytics_activity_csv'))

    def test_analytics_pipeline_csv_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:analytics_pipeline_csv'))

    def test_analytics_activity_xlsx_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:analytics_activity_xlsx'))

    def test_analytics_pipeline_xlsx_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:analytics_pipeline_xlsx'))

    def test_followup_excel_download_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:followup_excel_download'))

    def test_followup_basic_excel_download_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:followup_basic_excel_download'))

    def test_prepayment_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:prepayment_list'))

    def test_user_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:user_list'))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: export 권한 테스트 (salesman=403, manager=200, admin=200)
# ─────────────────────────────────────────────────────────────────────────────

class ExportPermissionTests(TestCase):
    """CSV/XLSX export 뷰의 역할별 권한 차단 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='테스트회사')
        self.salesman = make_user('salesman1', role='salesman', company=self.company)
        self.manager = make_user('manager1', role='manager', company=self.company)
        self.admin = make_user('admin1', role='admin', company=self.company)

    def _check_export(self, url_name, salesman_status, manager_status, admin_status):
        url = reverse(f'reporting:{url_name}')

        self.client.force_login(self.salesman)
        r = self.client.get(url)
        self.assertEqual(r.status_code, salesman_status,
                         msg=f"Salesman @ {url_name}: expected {salesman_status}, got {r.status_code}")

        self.client.force_login(self.manager)
        r = self.client.get(url)
        self.assertEqual(r.status_code, manager_status,
                         msg=f"Manager @ {url_name}: expected {manager_status}, got {r.status_code}")

        self.client.force_login(self.admin)
        r = self.client.get(url)
        self.assertEqual(r.status_code, admin_status,
                         msg=f"Admin @ {url_name}: expected {admin_status}, got {r.status_code}")

    def test_activity_csv_export_permission(self):
        """활동 CSV export: salesman=403, manager=200, admin=200"""
        self._check_export('analytics_activity_csv', 403, 200, 200)

    def test_pipeline_csv_export_permission(self):
        """파이프라인 CSV export: salesman=403, manager=200, admin=200"""
        self._check_export('analytics_pipeline_csv', 403, 200, 200)

    def test_activity_xlsx_export_permission(self):
        """활동 XLSX export: salesman=403, manager=200, admin=200"""
        self._check_export('analytics_activity_xlsx', 403, 200, 200)

    def test_pipeline_xlsx_export_permission(self):
        """파이프라인 XLSX export: salesman=403, manager=200, admin=200"""
        self._check_export('analytics_pipeline_xlsx', 403, 200, 200)

    def test_followup_excel_salesman_blocked(self):
        """followup excel download: can_download_excel=False salesman 차단"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:followup_excel_download'))
        # 권한 없으면 리다이렉트
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Salesman without excel perm should be blocked, got {r.status_code}")

    def test_followup_basic_excel_salesman_blocked(self):
        """followup basic excel download: can_download_excel=False salesman 차단"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:followup_basic_excel_download'))
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Salesman without excel perm should be blocked, got {r.status_code}")

    def test_followup_excel_admin_allowed(self):
        """followup excel download: admin 허용"""
        self.client.force_login(self.admin)
        r = self.client.get(reverse('reporting:followup_excel_download'))
        self.assertEqual(r.status_code, 200)

    def test_followup_basic_excel_admin_allowed(self):
        """followup basic excel download: admin 허용"""
        self.client.force_login(self.admin)
        r = self.client.get(reverse('reporting:followup_basic_excel_download'))
        self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: AI 권한 테스트
# ─────────────────────────────────────────────────────────────────────────────

class AIPermissionTests(TestCase):
    """AI 기능 접근 권한 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='테스트AI회사')
        self.user_no_ai = make_user('no_ai_user', role='salesman',
                                    can_use_ai=False, company=self.company)
        self.user_with_ai = make_user('ai_user', role='salesman',
                                      can_use_ai=True, company=self.company)

    def test_ai_departments_blocked_without_permission(self):
        """can_use_ai=False 사용자는 AI 분석 페이지에서 리다이렉트"""
        self.client.force_login(self.user_no_ai)
        r = self.client.get('/ai/')
        # ai_permission_required 데코레이터가 대시보드로 리다이렉트
        self.assertIn(r.status_code, [302, 403],
                      msg=f"User without AI perm should be blocked, got {r.status_code}")

    def test_ai_departments_accessible_with_permission(self):
        """can_use_ai=True 사용자는 AI 분석 페이지 접근 가능"""
        self.client.force_login(self.user_with_ai)
        r = self.client.get('/ai/')
        self.assertEqual(r.status_code, 200,
                         msg=f"User with AI perm should access, got {r.status_code}")

    def test_weekly_report_ai_draft_blocked_without_permission(self):
        """can_use_ai=False 사용자는 AI 주간보고 초안 생성 API에서 403"""
        self.client.force_login(self.user_no_ai)
        r = self.client.get(
            reverse('reporting:weekly_report_ai_draft'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'}
        )
        self.assertEqual(r.status_code, 403)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: 대시보드 smoke 테스트
# ─────────────────────────────────────────────────────────────────────────────

class DashboardSmokeTests(TestCase):
    """대시보드 기본 동작 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='대시보드테스트회사')
        self.user = make_user('dash_user', role='salesman', company=self.company)

    def test_dashboard_returns_200(self):
        """인증 후 대시보드 200 응답"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_has_frontend_pipeline_return_link(self):
        """백엔드 대시보드에서 React 파이프라인으로 돌아갈 수 있어야 함"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertContains(r, '프론트 CRM')
        self.assertContains(r, '파이프라인')
        self.assertContains(r, 'https://sales-note-frontend-production.up.railway.app/')

    def test_django_sidebar_schedule_points_to_calendar(self):
        """전환 기간 Django 사이드바 일정 메뉴는 캘린더를 우선 열어야 함"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertContains(r, 'href="/reporting/schedules/calendar/"')
        self.assertContains(r, '일정 캘린더')

    def test_dashboard_unauthenticated_redirects(self):
        """미인증 대시보드 접근 → 로그인 리다이렉트"""
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertIn(r.status_code, [301, 302])
        self.assertIn('login', r.get('Location', ''))

    def test_dashboard_contains_key_elements(self):
        """대시보드에 핵심 요소 포함 여부"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8', errors='replace')
        # 대시보드에 기본 섹션 존재 여부 (HTML content 체크)
        self.assertIn('dashboard', content.lower())

    def test_dashboard_note_quick_action_handles_same_page_hash(self):
        """상단 영업노트 링크는 같은 대시보드 페이지에서도 모달을 열 수 있어야 함"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8', errors='replace')
        self.assertIn('href="/reporting/dashboard/#dashboardNoteModal"', content)
        self.assertIn('window.addEventListener(\'hashchange\', openDashboardNoteModalFromHash)', content)
        self.assertIn('event.target.closest(\'a[href$="#dashboardNoteModal"]\')', content)

    def test_topbar_pipeline_link_replaces_quote_opportunity_link(self):
        """상단 견적 버튼은 프론트 파이프라인 링크로 대체되어야 함"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 200)
        content = r.content.decode('utf-8', errors='replace')
        self.assertIn('href="https://sales-note-frontend-production.up.railway.app/"', content)
        self.assertIn('파이프라인', content)
        self.assertNotIn('href="/reporting/opportunities/"', content)


class DashboardSummaryApiTests(TestCase):
    """React 대시보드 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='대시보드API회사')
        self.other_company = UserCompany.objects.create(name='대시보드API타사회사')
        self.user = make_user('dash_api_me', role='salesman', company=self.company)
        self.coworker = make_user('dash_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('dash_api_manager', role='manager', company=self.company)
        self.other_user = make_user('dash_api_other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:dashboard_summary_api')

    def _create_customer(self, owner, name, overdue=True, today_schedule=True):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Company, Department, FollowUp, History, Schedule

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            company=customer_company,
            department=department,
            priority='urgent',
            pipeline_stage='quote',
            customer_grade='A',
            ai_score=82,
        )
        if today_schedule:
            Schedule.objects.create(
                user=owner,
                company=owner.userprofile.company,
                followup=followup,
                visit_date=timezone.localdate(),
                visit_time=time(10, 0),
                status='scheduled',
                activity_type='customer_meeting',
                notes='오늘 미팅',
            )
        History.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            action_type='customer_meeting',
            content=f'{name} 미팅 기록',
            next_action='후속 전화',
            next_action_date=timezone.localdate() - timedelta(days=1) if overdue else timezone.localdate(),
        )
        return followup

    def test_dashboard_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_dashboard_summary_api_uses_salesman_own_scope(self):
        own = self._create_customer(self.user, '내고객')
        coworker = self._create_customer(self.coworker, '동료고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['source'], 'django')
        self.assertEqual(payload['metrics']['totalCustomers'], 1)
        priority_ids = {item['id'] for item in payload['priorityCustomers']}
        self.assertIn(own.id, priority_ids)
        self.assertNotIn(coworker.id, priority_ids)

    def test_dashboard_summary_api_includes_dashboard_sections(self):
        followup = self._create_customer(self.user, '요약고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['metrics']['todaySchedules'], 1)
        self.assertEqual(payload['metrics']['overdueActions'], 1)
        self.assertEqual(payload['today']['items'][0]['customer'], '요약고객 담당자')
        self.assertEqual(payload['overdueActions'][0]['nextAction'], '후속 전화')
        self.assertEqual(payload['recentActivities'][0]['customer'], '요약고객 담당자')
        self.assertTrue(any(item['stage'] == followup.pipeline_stage for item in payload['pipelineSummary']))
        self.assertEqual(payload['links']['createNote'], '/notes/?create=1')

    def test_dashboard_summary_api_manager_sees_same_company_only(self):
        own = self._create_customer(self.user, '회사내고객')
        coworker = self._create_customer(self.coworker, '회사내동료')
        other = self._create_customer(self.other_user, '타사고객')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['metrics']['totalCustomers'], 2)
        priority_ids = {item['id'] for item in payload['priorityCustomers']}
        self.assertIn(own.id, priority_ids)
        self.assertIn(coworker.id, priority_ids)
        self.assertNotIn(other.id, priority_ids)
        self.assertTrue(payload['scope']['canViewAll'])


class CustomersSummaryApiTests(TestCase):
    """React 고객 화면 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='고객API회사')
        self.other_company = UserCompany.objects.create(name='고객API타사회사')
        self.user = make_user('customers_api_me', role='salesman', company=self.company)
        self.coworker = make_user('customers_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('customers_api_manager', role='manager', company=self.company)
        self.other_user = make_user('customers_api_other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:customers_summary_api')

    def _create_customer(self, owner, name, priority='urgent', stage='quote'):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import Company, Department, FollowUp, History

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} 책임',
            company=customer_company,
            department=department,
            priority=priority,
            pipeline_stage=stage,
            customer_grade='A',
            ai_score=80,
        )
        History.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            action_type='customer_meeting',
            content=f'{name} 고객 상담',
            next_action='다음 연락',
            next_action_date=timezone.localdate() - timedelta(days=1),
        )
        return followup

    def test_customers_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_customers_summary_api_uses_salesman_own_scope(self):
        own = self._create_customer(self.user, '내고객')
        coworker = self._create_customer(self.coworker, '동료고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['customers']}
        self.assertIn(own.id, ids)
        self.assertNotIn(coworker.id, ids)
        self.assertEqual(payload['metrics']['totalCustomers'], 1)
        self.assertTrue(payload['create']['canCreate'])
        self.assertEqual(payload['links']['createCustomer'], '/customers/?create=1')
        self.assertEqual(payload['create']['submitUrl'], reverse('reporting:followup_create_ajax'))
        self.assertEqual(payload['create']['companySubmitUrl'], reverse('reporting:company_create_api'))
        self.assertEqual(payload['create']['departmentSubmitUrl'], reverse('reporting:department_create_api'))
        self.assertTrue(any(option['id'] == own.company_id for option in payload['create']['companies']))
        department_option = next(option for option in payload['create']['departments'] if option['id'] == own.department_id)
        self.assertIn('내고객 책임', department_option['searchText'])

    def test_department_autocomplete_finds_department_by_pi_manager_name(self):
        target = self._create_customer(self.user, 'PI검색고객')
        target.manager = '김PI교수'
        target.save(update_fields=['manager'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:department_autocomplete'), {
            'q': '김PI',
            'company': target.company_id,
        })

        self.assertEqual(response.status_code, 200)
        department_ids = {item['id'] for item in response.json()['results']}
        self.assertIn(target.department_id, department_ids)

    def test_customers_summary_api_defaults_to_latest_updated_first(self):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import FollowUp

        older = self._create_customer(self.user, '오래된고객')
        newer = self._create_customer(self.user, '최근고객')
        FollowUp.objects.filter(pk=older.pk).update(
            updated_at=timezone.now() - timedelta(days=5),
            created_at=timezone.now() - timedelta(days=5),
        )
        FollowUp.objects.filter(pk=newer.pk).update(
            updated_at=timezone.now(),
            created_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['customers'][0]['id'], newer.id)

    def test_customers_summary_api_filters_search_owner_and_priority(self):
        target = self._create_customer(self.user, 'PCR핵심', priority='urgent')
        self._create_customer(self.user, '일반', priority='scheduled')
        self._create_customer(self.coworker, '동료PCR', priority='urgent')
        self.client.force_login(self.manager)

        response = self.client.get(self.url, {
            'q': 'PCR',
            'owner': str(self.user.id),
            'priority': 'urgent',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = [item['id'] for item in payload['customers']]
        self.assertEqual(ids, [target.id])
        self.assertEqual(payload['filters']['q'], 'PCR')
        self.assertTrue(any(option['id'] == self.user.id for option in payload['options']['owners']))

    def test_customers_summary_api_manager_sees_same_company_only(self):
        own = self._create_customer(self.user, '회사내고객')
        coworker = self._create_customer(self.coworker, '회사내동료')
        other = self._create_customer(self.other_user, '타사고객')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['customers']}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        priority_ids = {item['id'] for item in payload['priorityCustomers']}
        self.assertIn(own.id, priority_ids)
        self.assertTrue(payload['scope']['canViewAll'])
        self.assertFalse(payload['create']['canCreate'])

    def test_customers_summary_api_includes_activity_and_schedule_snapshot(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import History, Schedule

        target = self._create_customer(self.user, '일정있는고객', priority='urgent')
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            action_type='quote',
            content='견적 재확인',
            next_action='견적 후속',
            next_action_date=timezone.localdate() + timedelta(days=2),
        )
        upcoming = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 30),
            activity_type='quote',
            status='scheduled',
            location='고객 연구실',
        )
        Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() - timedelta(days=3),
            visit_time=time(9, 0),
            activity_type='customer_meeting',
            status='completed',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        customer = next(item for item in payload['customers'] if item['id'] == target.id)
        self.assertEqual(customer['activityCount'], 2)
        self.assertEqual(customer['scheduleCount'], 2)
        self.assertEqual(customer['upcomingScheduleCount'], 1)
        self.assertEqual(customer['overdueActionCount'], 1)
        self.assertEqual(customer['upcomingSchedule']['id'], upcoming.id)
        self.assertEqual(customer['upcomingSchedule']['activityLabel'], '견적 제출')
        self.assertEqual(customer['upcomingSchedule']['time'], '10:30')
        self.assertEqual(payload['metrics']['scheduledCustomers'], 1)

    def test_followup_create_ajax_creates_customer_for_salesman(self):
        from reporting.models import Company, Department, FollowUp

        customer_company = Company.objects.create(name='빠른등록 회사', created_by=self.user)
        department = Department.objects.create(
            company=customer_company,
            name='빠른등록 연구실',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:followup_create_ajax'), {
            'customer_name': '빠른등록 담당자',
            'company': str(customer_company.id),
            'department': str(department.id),
            'priority': 'urgent',
            'manager': '빠른 책임',
            'phone_number': '010-0000-0000',
            'email': 'quick@example.com',
            'notes': 'React 빠른 등록',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['href'], f"/customers/{payload['followup_id']}/")
        followup = FollowUp.objects.get(id=payload['followup_id'])
        self.assertEqual(followup.customer_name, '빠른등록 담당자')
        self.assertEqual(followup.user, self.user)
        self.assertEqual(followup.user_company, self.company)
        self.assertEqual(followup.priority, 'urgent')

    def test_followup_create_ajax_blocks_manager(self):
        from reporting.models import Company, Department

        customer_company = Company.objects.create(name='매니저차단 회사', created_by=self.user)
        department = Department.objects.create(
            company=customer_company,
            name='매니저차단 연구실',
            created_by=self.user,
        )
        self.client.force_login(self.manager)

        response = self.client.post(reverse('reporting:followup_create_ajax'), {
            'customer_name': '매니저 생성 시도',
            'company': str(customer_company.id),
            'department': str(department.id),
            'priority': 'urgent',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

    def test_company_and_department_create_apis_create_records_for_salesman(self):
        from reporting.models import Company, Department

        self.client.force_login(self.user)

        company_response = self.client.post(reverse('reporting:company_create_api'), {
            'name': 'React인라인 회사',
        })

        self.assertEqual(company_response.status_code, 200)
        company_payload = company_response.json()
        self.assertTrue(company_payload['success'])
        company = Company.objects.get(id=company_payload['company']['id'])
        self.assertEqual(company.name, 'React인라인 회사')
        self.assertEqual(company.created_by, self.user)

        department_response = self.client.post(reverse('reporting:department_create_api'), {
            'company_id': str(company.id),
            'name': 'React인라인 연구실',
        })

        self.assertEqual(department_response.status_code, 200)
        department_payload = department_response.json()
        self.assertTrue(department_payload['success'])
        department = Department.objects.get(id=department_payload['department']['id'])
        self.assertEqual(department.company, company)
        self.assertEqual(department.name, 'React인라인 연구실')
        self.assertEqual(department.created_by, self.user)

    def test_company_and_department_create_apis_block_manager(self):
        from reporting.models import Company

        customer_company = Company.objects.create(name='매니저업체차단 회사', created_by=self.user)
        self.client.force_login(self.manager)

        company_response = self.client.post(reverse('reporting:company_create_api'), {
            'name': '매니저 신규 업체',
        })
        department_response = self.client.post(reverse('reporting:department_create_api'), {
            'company_id': str(customer_company.id),
            'name': '매니저 신규 부서',
        })

        self.assertEqual(company_response.status_code, 403)
        self.assertFalse(company_response.json()['success'])
        self.assertEqual(department_response.status_code, 403)
        self.assertFalse(department_response.json()['success'])

    def test_department_create_api_blocks_other_company(self):
        from reporting.models import Company

        other_company = Company.objects.create(name='타사부서차단 회사', created_by=self.other_user)
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:department_create_api'), {
            'company_id': str(other_company.id),
            'name': '타사 신규 부서',
        })

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], '접근 권한이 없는 업체입니다.')

    def test_customer_detail_summary_api_requires_login_json(self):
        target = self._create_customer(self.user, '상세로그인')
        url = reverse('reporting:customer_detail_summary_api', args=[target.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_customer_detail_summary_api_returns_notes_and_schedules(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import History, Schedule

        target = self._create_customer(self.user, '상세고객', priority='urgent')
        upcoming = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(11, 0),
            activity_type='quote',
            status='scheduled',
            location='상세 회의실',
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            action_type='quote',
            content='상세 견적 메모',
            next_action='상세 후속',
            next_action_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['customer']['id'], target.id)
        self.assertGreaterEqual(payload['metrics']['recentNotes'], 2)
        self.assertEqual(payload['upcomingSchedules'][0]['id'], upcoming.id)
        self.assertTrue(payload['links']['djangoDetail'].endswith(f'/followups/{target.id}/'))
        self.assertTrue(payload['links']['djangoEdit'].endswith(f'/followups/{target.id}/edit/'))
        self.assertEqual(payload['links']['createNote'], f'/notes/?create=1&customer={target.id}')
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(payload['edit']['submitUrl'], reverse('reporting:customer_update_api', args=[target.id]))
        self.assertTrue(any(option['id'] == target.company_id for option in payload['edit']['companies']))
        self.assertTrue(any(option['id'] == target.department_id for option in payload['edit']['departments']))

    def test_customer_detail_summary_api_includes_scoped_prepayment_summary(self):
        from django.utils import timezone
        from reporting.models import Prepayment

        target = self._create_customer(self.user, '상세선결제', priority='urgent')
        first = Prepayment.objects.create(
            customer=target,
            company=target.company,
            amount=100000,
            balance=80000,
            payment_date=timezone.localdate(),
            payer_name='상세입금자',
            status='active',
            created_by=self.user,
        )
        second = Prepayment.objects.create(
            customer=target,
            company=target.company,
            amount=50000,
            balance=0,
            payment_date=timezone.localdate(),
            payer_name='상세소진',
            status='depleted',
            created_by=self.user,
        )
        coworker_prepayment = Prepayment.objects.create(
            customer=target,
            company=target.company,
            amount=999000,
            balance=999000,
            payment_date=timezone.localdate(),
            payer_name='동료입금자',
            status='active',
            created_by=self.coworker,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        summary = response.json()['prepaymentSummary']
        self.assertEqual(summary['metrics']['totalAmount'], 150000)
        self.assertEqual(summary['metrics']['totalBalance'], 80000)
        self.assertEqual(summary['metrics']['totalUsed'], 70000)
        self.assertEqual(summary['metrics']['totalCount'], 2)
        self.assertEqual(summary['metrics']['activeCount'], 1)
        self.assertEqual(summary['metrics']['depletedCount'], 1)
        self.assertEqual(summary['links']['prepayments'], '/prepayments/')
        self.assertEqual(summary['links']['customerPrepayments'], f'/prepayments/customer/{target.id}/')
        self.assertTrue(summary['links']['djangoCustomerPrepayments'].endswith(f'/prepayment/customer/{target.id}/'))
        prepayment_ids = {item['id'] for item in summary['recentPrepayments']}
        self.assertIn(first.id, prepayment_ids)
        self.assertIn(second.id, prepayment_ids)
        self.assertNotIn(coworker_prepayment.id, prepayment_ids)

    def test_customer_detail_summary_api_includes_department_ai_action(self):
        from datetime import date
        from ai_chat.models import AIDepartmentAnalysis, PainPointCard

        target = self._create_customer(self.user, 'AI고객', priority='urgent')
        profile = self.user.userprofile
        profile.can_use_ai = True
        profile.save(update_fields=['can_use_ai'])
        long_summary = (
            'PCR 부서는 구매 프로세스 확인이 필요합니다. '
            '결재권자 확인, 예산 집행일, 필요 서류를 한 번에 정리해야 합니다. '
            '반복되는 견적 후속 지연을 줄이려면 다음 연락에서 승인자와 일정 기준을 명확히 확인해야 합니다.'
        )
        analysis = AIDepartmentAnalysis.objects.create(
            user=self.user,
            department=target.department,
            analysis_data={
                'department_summary': long_summary,
                'meeting_insights': [{
                    'theme': '구매 승인 지연',
                    'details': '견적 이후 결재권자 확인이 반복적으로 늦어집니다.',
                    'frequency': '최근 2회',
                }],
                'quote_delivery_insights': {
                    'conversion_analysis': '견적 대비 납품 전환율이 낮습니다.',
                    'delivery_cycle': '정기 납품 주기는 아직 확인이 필요합니다.',
                    'product_trends': 'PCR 소모품 문의가 반복됩니다.',
                    'stalled_quotes': [{
                        'quote_info': 'Q-001',
                        'possible_reason': '결재 승인자 미확인',
                        'suggestion': '승인자를 직접 확인합니다.',
                    }],
                },
                'next_actions': [{
                    'action': '결재 승인자 확인',
                    'priority': 'high',
                    'reason': '견적 후속 지연 해소',
                }],
                'verification_insights': [{
                    'status': 'checked',
                    'status_label': '검증 메모',
                    'hypothesis': '구매 결재 단계가 길어 견적 후속이 지연됩니다.',
                    'insight': '김박사가 최종 승인자로 확인되어 승인자 기준 후속이 필요합니다.',
                    'impact': '6월 예산 소진 뒤 구매 가능하다는 검증 메모를 다음 액션에 반영해야 합니다.',
                    'previous_question': '결재 승인자가 누구인지 확인했나요?',
                    'next_verification': '6월 예산 집행일과 필요 서류를 확인합니다.',
                    'verified_at': '2026-05-10T09:00:00+09:00',
                }],
                'missing_info': {
                    'items': ['구매 승인자'],
                    'questions': ['결재 최종 승인자는 누구인가요?'],
                },
            },
            quote_delivery_data={
                'summary': {
                    'total_quotes': 2,
                    'converted_quotes': 1,
                    'conversion_rate': 50,
                    'total_deliveries': 1,
                    'avg_delivery_interval_days': 21,
                    'product_stats': {
                        'PCR Mix': {
                            'quoted': 2,
                            'quote_amount': 300000,
                            'delivered': 1,
                            'delivery_amount': 150000,
                        },
                    },
                },
                'deliveries': [{
                    'date': '2026-04-29',
                    'customer': 'AI고객 담당자',
                    'amount': 150000,
                    'items': [{
                        'product': 'PCR Mix',
                        'quantity': 3,
                        'unit_price': 50000,
                        'total_price': 150000,
                    }],
                    'source': '납품 일정',
                    'schedule_id': 101,
                    'notes': '최근 납품 메모',
                }],
            },
            meeting_count=3,
            quote_count=2,
            delivery_count=1,
            analysis_period_start=date(2026, 4, 1),
            analysis_period_end=date(2026, 5, 1),
        )
        card = PainPointCard.objects.create(
            analysis=analysis,
            category='purchase_process',
            hypothesis='구매 결재 단계가 길어 견적 후속이 지연됩니다.',
            confidence='high',
            confidence_score=90,
            evidence=[{'type': 'verification', 'text': '김박사 승인자 확인', 'source_section': '검증 메모'}],
            attribution='lab',
            verification_question='결재 승인자가 누구인지 확인했나요?',
            action_if_yes='승인자에게 직접 후속합니다.',
            action_if_no='담당 연구원에게 결재 라인을 확인합니다.',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        ai_department = response.json()['aiDepartment']
        self.assertEqual(ai_department['departmentId'], target.department_id)
        self.assertTrue(ai_department['canUseAi'])
        self.assertTrue(ai_department['canAnalyze'])
        self.assertTrue(ai_department['hasAnalysis'])
        self.assertEqual(ai_department['summary'], long_summary)
        self.assertEqual(ai_department['meetingCount'], 3)
        self.assertEqual(ai_department['painpointCount'], 1)
        self.assertEqual(ai_department['unverifiedPainpointCount'], 1)
        self.assertEqual(ai_department['href'], reverse('ai_chat:department_analysis', args=[target.department_id]))
        self.assertEqual(ai_department['runHref'], reverse('ai_chat:run_analysis', args=[target.department_id]))
        self.assertEqual(ai_department['periodStart'], '2026-04-01')
        self.assertEqual(ai_department['periodEnd'], '2026-05-01')
        self.assertEqual(ai_department['meetingInsights'][0]['theme'], '구매 승인 지연')
        self.assertEqual(ai_department['quoteDelivery']['totalQuotes'], 2)
        self.assertEqual(ai_department['quoteDelivery']['convertedQuotes'], 1)
        self.assertEqual(ai_department['quoteDelivery']['conversionRate'], 50)
        self.assertEqual(ai_department['quoteDelivery']['productStats'][0]['name'], 'PCR Mix')
        self.assertEqual(ai_department['quoteDelivery']['recentDeliveries'][0]['items'][0]['product'], 'PCR Mix')
        self.assertEqual(ai_department['quoteDelivery']['recentDeliveries'][0]['items'][0]['quantity'], 3)
        self.assertIn('납품 전환율', ai_department['quoteInsights']['conversionAnalysis'])
        self.assertEqual(ai_department['quoteInsights']['stalledQuotes'][0]['quoteInfo'], 'Q-001')
        self.assertEqual(ai_department['nextActions'][0]['action'], '결재 승인자 확인')
        self.assertEqual(ai_department['verificationInsights'][0]['status'], 'checked')
        self.assertEqual(ai_department['verificationInsights'][0]['statusLabel'], '검증 메모')
        self.assertIn('김박사', ai_department['verificationInsights'][0]['insight'])
        self.assertEqual(ai_department['verificationInsights'][0]['nextVerification'], '6월 예산 집행일과 필요 서류를 확인합니다.')
        self.assertEqual(ai_department['missingInfo']['questions'][0], '결재 최종 승인자는 누구인가요?')
        recommended_questions = [item['question'] for item in ai_department['recommendedQuestions']]
        self.assertIn('결재 최종 승인자는 누구인가요?', recommended_questions)
        self.assertIn('6월 예산 집행일과 필요 서류를 확인합니다.', recommended_questions)
        self.assertIn('결재 승인자가 누구인지 확인했나요?', recommended_questions)
        self.assertEqual(ai_department['painpoints'][0]['id'], card.id)
        self.assertEqual(ai_department['painpoints'][0]['categoryLabel'], '결재/구매 프로세스')
        self.assertEqual(ai_department['painpoints'][0]['evidence'][0]['typeLabel'], '검증')
        self.assertEqual(ai_department['painpoints'][0]['verifyHref'], reverse('ai_chat:verify_card', args=[card.id]))
        self.assertTrue(ai_department['painpoints'][0]['canVerify'])

    def test_customer_detail_summary_api_hides_ai_run_without_permission(self):
        target = self._create_customer(self.user, 'AI권한없음', priority='urgent')
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        ai_department = response.json()['aiDepartment']
        self.assertFalse(ai_department['canUseAi'])
        self.assertFalse(ai_department['canAnalyze'])
        self.assertFalse(ai_department['hasAnalysis'])
        self.assertEqual(ai_department['runHref'], '')
        self.assertEqual(ai_department['href'], '')
        self.assertIn('AI 기능 사용 권한', ai_department['message'])

    def test_customer_update_api_updates_customer_for_owner(self):
        from reporting.models import Company, Department, FollowUp

        target = self._create_customer(self.user, '수정대상', priority='scheduled', stage='potential')
        next_company = Company.objects.create(name='수정가능 회사', created_by=self.user)
        next_department = Department.objects.create(
            company=next_company,
            name='수정가능 연구실',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:customer_update_api', args=[target.id]), {
            'customer_name': '수정완료 담당자',
            'company': str(next_company.id),
            'department': str(next_department.id),
            'priority': 'urgent',
            'status': 'paused',
            'pipeline_stage': 'quote',
            'manager': '수정 책임',
            'phone_number': '010-1111-2222',
            'email': 'edited@example.com',
            'address': '수정 주소',
            'notes': 'React 상세 수정',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['href'], f'/customers/{target.id}/')
        updated = FollowUp.objects.get(id=target.id)
        self.assertEqual(updated.customer_name, '수정완료 담당자')
        self.assertEqual(updated.company, next_company)
        self.assertEqual(updated.department, next_department)
        self.assertEqual(updated.priority, 'urgent')
        self.assertEqual(updated.status, 'paused')
        self.assertEqual(updated.pipeline_stage, 'quote')
        self.assertTrue(updated.pipeline_manually_set)
        self.assertEqual(updated.email, 'edited@example.com')

    def test_customer_update_api_blocks_manager_and_coworker(self):
        target = self._create_customer(self.user, '수정권한차단')
        payload = {
            'customer_name': '권한없는수정',
            'company': str(target.company_id),
            'department': str(target.department_id),
            'priority': target.priority,
            'status': target.status,
            'pipeline_stage': target.pipeline_stage,
        }

        self.client.force_login(self.manager)
        manager_response = self.client.post(reverse('reporting:customer_update_api', args=[target.id]), payload)
        self.assertEqual(manager_response.status_code, 403)
        self.assertFalse(manager_response.json()['success'])

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(reverse('reporting:customer_update_api', args=[target.id]), payload)
        self.assertEqual(coworker_response.status_code, 403)
        self.assertFalse(coworker_response.json()['success'])

    def test_customer_update_api_blocks_other_company_selection(self):
        from reporting.models import Company, Department

        target = self._create_customer(self.user, '타사업체수정차단')
        other_company = Company.objects.create(name='타사업체수정 회사', created_by=self.other_user)
        other_department = Department.objects.create(
            company=other_company,
            name='타사업체수정 연구실',
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:customer_update_api', args=[target.id]), {
            'customer_name': '타사변경시도',
            'company': str(other_company.id),
            'department': str(other_department.id),
            'priority': target.priority,
            'status': target.status,
            'pipeline_stage': target.pipeline_stage,
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

    def test_customer_detail_summary_api_blocks_other_company_customer(self):
        target = self._create_customer(self.other_user, '타사상세')
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 403)


class QuoteItemsApiTests(TestCase):
    """부서 기준 견적 품목 불러오기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='견적품목API회사')
        self.user = make_user('quote_items_me', role='salesman', company=self.company)
        self.coworker = make_user('quote_items_coworker', role='salesman', company=self.company)

        from reporting.models import Company, Department

        self.customer_company = Company.objects.create(name='견적품목 고객사', created_by=self.user)
        self.department = Department.objects.create(
            company=self.customer_company,
            name='공동 연구실',
            created_by=self.user,
        )
        self.other_department = Department.objects.create(
            company=self.customer_company,
            name='다른 연구실',
            created_by=self.user,
        )

    def _create_followup(self, owner, name, department=None):
        from reporting.models import FollowUp

        return FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=name,
            company=self.customer_company,
            department=department or self.department,
            priority='urgent',
            pipeline_stage='quote',
        )

    def _create_quote_schedule(self, followup, owner, item_name, unit_price):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name=item_name,
            quantity=1,
            unit_price=unit_price,
        )
        return schedule

    def test_quote_items_api_returns_all_own_quotes_in_same_department(self):
        target = self._create_followup(self.user, '대표 고객')
        same_department = self._create_followup(self.user, '같은 부서 고객')
        other_department = self._create_followup(self.user, '다른 부서 고객', self.other_department)
        coworker_customer = self._create_followup(self.coworker, '동료 고객')
        first = self._create_quote_schedule(target, self.user, 'PCR 장비', 1000000)
        second = self._create_quote_schedule(same_department, self.user, '원심분리기', 2000000)
        self._create_quote_schedule(other_department, self.user, '다른 부서 품목', 3000000)
        self._create_quote_schedule(coworker_customer, self.coworker, '동료 품목', 4000000)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['count'], 2)
        schedule_ids = {item['schedule_id'] for item in payload['quotes']}
        self.assertEqual(schedule_ids, {first.id, second.id})
        customer_names = {item['customer_name'] for item in payload['quotes']}
        self.assertEqual(customer_names, {'대표 고객', '같은 부서 고객'})

    def test_customer_records_api_includes_quote_schedules_without_quote_model(self):
        target = self._create_followup(self.user, '기록 대표')
        same_department = self._create_followup(self.user, '기록 같은 부서')
        first = self._create_quote_schedule(target, self.user, '견적A', 1000000)
        second = self._create_quote_schedule(same_department, self.user, '견적B', 2000000)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_records_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['quote_count'], 2)
        quote_ids = {item['id'] for item in payload['quotes']}
        self.assertEqual(quote_ids, {first.id, second.id})
        self.assertEqual(payload['total_quote_amount'], 3300000.0)


class NotesSummaryApiTests(TestCase):
    """React 영업노트 화면 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='노트API회사')
        self.other_company = UserCompany.objects.create(name='노트API타사회사')
        self.user = make_user('notes_api_me', role='salesman', company=self.company)
        self.coworker = make_user('notes_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('notes_api_manager', role='manager', company=self.company)
        self.admin = make_user('notes_api_admin', role='admin', company=self.company)
        self.other_user = make_user('notes_api_other', role='salesman', company=self.other_company)
        self.other_manager = make_user('notes_api_other_manager', role='manager', company=self.other_company)
        self.url = reverse('reporting:notes_summary_api')
        self.create_url = reverse('reporting:notes_create_api')

    def _create_note(
        self,
        owner,
        name,
        action_type='customer_meeting',
        content='고객 상담 기록',
        next_action='후속 연락',
        next_action_date=None,
        reviewed=False,
    ):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import Company, Department, FollowUp, History

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} 책임',
            company=customer_company,
            department=department,
            priority='urgent',
            pipeline_stage='quote',
        )
        history = History.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            action_type=action_type,
            content=content,
            next_action=next_action,
            next_action_date=next_action_date or timezone.localdate() - timedelta(days=1),
            reviewed_at=timezone.now() if reviewed else None,
            reviewer=self.manager if reviewed else None,
        )
        return history

    def test_notes_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_notes_summary_api_uses_salesman_own_scope(self):
        own = self._create_note(self.user, '내노트')
        coworker = self._create_note(self.coworker, '동료노트')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['notes']}
        self.assertIn(own.id, ids)
        self.assertNotIn(coworker.id, ids)
        self.assertEqual(payload['metrics']['totalNotes'], 1)
        note = payload['notes'][0]
        self.assertFalse(payload['scope']['canReview'])
        self.assertFalse(note['canReview'])
        self.assertEqual(note['reviewToggleHref'], '')
        self.assertEqual(note['href'], f'/notes/{own.id}/')
        self.assertIn(f'/reporting/histories/{own.id}/', note['djangoHref'])

    def test_notes_summary_api_filters_search_owner_action_review_and_next_action(self):
        target = self._create_note(
            self.user,
            'PCR핵심',
            action_type='quote',
            content='PCR 견적 후속 필요',
            reviewed=False,
        )
        self._create_note(self.user, 'PCR완료', action_type='quote', content='PCR 견적 완료', reviewed=True)
        self._create_note(self.user, '서비스', action_type='service', content='PCR 서비스', reviewed=False)
        self._create_note(self.coworker, 'PCR동료', action_type='quote', content='PCR 동료 건', reviewed=False)
        self.client.force_login(self.manager)

        response = self.client.get(self.url, {
            'q': 'PCR',
            'owner': str(self.user.id),
            'actionType': 'quote',
            'review': 'unreviewed',
            'nextAction': 'overdue',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = [item['id'] for item in payload['notes']]
        self.assertEqual(ids, [target.id])
        self.assertEqual(payload['filters']['q'], 'PCR')
        self.assertTrue(any(option['value'] == 'quote' for option in payload['options']['actionTypes']))
        self.assertEqual(payload['metrics']['filteredNotes'], 1)

    def test_notes_summary_api_manager_sees_same_company_only(self):
        own = self._create_note(self.user, '회사내노트')
        coworker = self._create_note(self.coworker, '회사내동료노트')
        other = self._create_note(self.other_user, '타사노트')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['notes']}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(payload['metrics']['totalNotes'], 2)
        self.assertTrue(payload['scope']['canViewAll'])

    def test_notes_summary_api_exposes_review_metadata_for_manager(self):
        from reporting.models import History

        target = self._create_note(
            self.user,
            '검토대상',
            action_type='customer_meeting',
            content='검토가 필요한 고객 미팅',
            reviewed=False,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            parent_history=target,
            action_type='memo',
            content='관리자 확인 메모',
            created_by=self.manager,
        )
        self.client.force_login(self.manager)

        response = self.client.get(self.url, {'owner': str(self.user.id)})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        note = next(item for item in payload['notes'] if item['id'] == target.id)
        self.assertTrue(payload['scope']['canReview'])
        self.assertTrue(note['canReview'])
        self.assertIn(f'/reporting/histories/{target.id}/toggle-reviewed/', note['reviewToggleHref'])
        self.assertIsNone(note['reviewedAt'])
        self.assertEqual(note['reviewer'], '')
        self.assertEqual(note['replyCount'], 1)
        self.assertEqual(note['fileCount'], 0)

    def test_notes_summary_api_does_not_expose_review_action_for_admin(self):
        target = self._create_note(
            self.user,
            '어드민검토제외',
            action_type='customer_meeting',
            content='회사 매니저만 검토 처리 가능',
            reviewed=False,
        )
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        note = next(item for item in payload['notes'] if item['id'] == target.id)
        self.assertFalse(payload['scope']['canReview'])
        self.assertFalse(note['canReview'])
        self.assertEqual(note['reviewToggleHref'], '')

    def test_notes_summary_api_includes_react_create_options_for_salesman(self):
        target = self._create_note(self.user, '작성대상')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['links']['createNote'], '/notes/?create=1')
        self.assertTrue(payload['create']['canCreate'])
        self.assertEqual(payload['create']['submitUrl'], self.create_url)
        customer_ids = {item['id'] for item in payload['create']['customers']}
        self.assertIn(target.followup_id, customer_ids)
        self.assertTrue(any(item['value'] == 'customer_meeting' for item in payload['create']['actionTypes']))
        self.assertFalse(any(item['value'] == 'memo' for item in payload['create']['actionTypes']))

    def test_notes_create_api_requires_login_json(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps({}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_notes_create_api_creates_own_customer_note(self):
        from django.utils import timezone
        from reporting.models import History

        target = self._create_note(self.user, '빠른작성기준')
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': target.followup_id,
                'actionType': 'customer_meeting',
                'content': 'React에서 바로 작성한 영업노트',
                'nextAction': '다음 주 견적 확인',
                'nextActionDate': timezone.localdate().isoformat(),
                'activityDate': timezone.localdate().isoformat(),
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload['success'])
        created = History.objects.get(pk=payload['historyId'])
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.followup_id, target.followup_id)
        self.assertEqual(created.content, 'React에서 바로 작성한 영업노트')
        self.assertEqual(created.next_action, '다음 주 견적 확인')
        self.assertEqual(created.meeting_date, timezone.localdate())

    def test_notes_create_api_blocks_manager_and_other_owner_customer(self):
        target = self._create_note(self.coworker, '동료작성차단')

        self.client.force_login(self.manager)
        manager_response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': target.followup_id,
                'actionType': 'customer_meeting',
                'content': '매니저 작성 시도',
            }),
            content_type='application/json',
        )
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.user)
        other_owner_response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': target.followup_id,
                'actionType': 'customer_meeting',
                'content': '동료 고객 작성 시도',
            }),
            content_type='application/json',
        )
        self.assertEqual(other_owner_response.status_code, 403)

    def test_notes_detail_api_returns_detail_and_edit_config(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils import timezone
        from reporting.models import History, HistoryFile

        target = self._create_note(
            self.user,
            '상세대상',
            action_type='customer_meeting',
            content='초기 상담',
        )
        target.meeting_date = timezone.localdate()
        target.meeting_situation = '예산 검토 중'
        target.meeting_next_action = '견적서 발송'
        target.save()
        history_file = HistoryFile.objects.create(
            history=target,
            file=SimpleUploadedFile('note-detail.txt', b'note detail memo', content_type='text/plain'),
            original_filename='note-detail.txt',
            file_size=16,
            uploaded_by=self.user,
        )
        self.addCleanup(history_file.file.delete, False)
        owner_reply = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            parent_history=target,
            action_type='memo',
            content='실무자 댓글',
        )
        manager_reply = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            parent_history=target,
            action_type='memo',
            content='관리자 확인 메모',
            created_by=self.manager,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:notes_detail_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['note']['id'], target.id)
        self.assertEqual(payload['note']['href'], f'/notes/{target.id}/')
        self.assertEqual(payload['note']['content'], '초기 상담')
        self.assertEqual(payload['note']['meetingSituation'], '예산 검토 중')
        self.assertEqual(payload['links']['notes'], '/notes/')
        self.assertIn(f'/reporting/histories/{target.id}/', payload['links']['djangoDetail'])
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(payload['edit']['submitUrl'], reverse('reporting:notes_update_api', args=[target.id]))
        self.assertEqual(payload['links']['uploadFiles'], reverse('reporting:note_file_upload', args=[target.id]))
        self.assertEqual(payload['note']['files'][0]['id'], history_file.id)
        self.assertEqual(payload['note']['files'][0]['deleteHref'], reverse('reporting:file_delete', args=[history_file.id]))
        self.assertTrue(payload['comments']['canCreate'])
        self.assertEqual(payload['comments']['submitUrl'], reverse('reporting:add_manager_memo_to_history_api', args=[target.id]))
        owner_reply_payload = next(reply for reply in payload['note']['replies'] if reply['id'] == owner_reply.id)
        manager_reply_payload = next(reply for reply in payload['note']['replies'] if reply['id'] == manager_reply.id)
        self.assertEqual(owner_reply_payload['authorRole'], '댓글')
        self.assertTrue(owner_reply_payload['canDelete'])
        self.assertEqual(owner_reply_payload['deleteHref'], reverse('reporting:delete_manager_memo_api', args=[owner_reply.id]))
        self.assertEqual(manager_reply_payload['authorRole'], '매니저 메모')
        self.assertFalse(manager_reply_payload['canDelete'])
        customer_ids = {item['id'] for item in payload['edit']['customers']}
        self.assertIn(target.followup_id, customer_ids)

    def test_notes_detail_api_manager_read_only_and_other_company_blocked(self):
        target = self._create_note(self.user, '매니저상세', action_type='quote', content='견적 확인')

        self.client.force_login(self.manager)
        manager_response = self.client.get(reverse('reporting:notes_detail_api', args=[target.id]))
        self.assertEqual(manager_response.status_code, 200)
        manager_payload = manager_response.json()
        self.assertFalse(manager_payload['edit']['canEdit'])
        self.assertTrue(manager_payload['scope']['canReview'])

        self.client.force_login(self.other_manager)
        other_response = self.client.get(reverse('reporting:notes_detail_api', args=[target.id]))
        self.assertEqual(other_response.status_code, 403)

    def test_notes_update_api_updates_owned_note(self):
        from django.utils import timezone

        target = self._create_note(self.user, '수정대상', action_type='customer_meeting', content='수정 전')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:notes_update_api', args=[target.id]),
            data=json.dumps({
                'followupId': target.followup_id,
                'actionType': 'customer_meeting',
                'activityDate': timezone.localdate().isoformat(),
                'content': 'React 상세에서 수정',
                'meetingSituation': '도입 검토',
                'meetingResearcherQuote': '다음 주에 다시 확인하겠습니다',
                'meetingConfirmedFacts': '예산은 6월 배정',
                'meetingObstacles': '내부 승인 필요',
                'meetingNextAction': '승인자 연락',
                'nextAction': '견적서 재발송',
                'nextActionDate': timezone.localdate().isoformat(),
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['message'], '영업노트를 수정했습니다.')
        target.refresh_from_db()
        self.assertEqual(target.content, 'React 상세에서 수정')
        self.assertEqual(target.meeting_situation, '도입 검토')
        self.assertEqual(target.meeting_next_action, '승인자 연락')
        self.assertEqual(target.next_action, '견적서 재발송')
        self.assertEqual(target.meeting_date, timezone.localdate())

    def test_notes_update_api_blocks_manager_and_other_company_customer(self):
        target = self._create_note(self.user, '수정차단', action_type='quote', content='견적 전')
        other_target = self._create_note(self.other_user, '타사고객', action_type='quote', content='타사')

        self.client.force_login(self.manager)
        manager_response = self.client.post(
            reverse('reporting:notes_update_api', args=[target.id]),
            data=json.dumps({
                'followupId': target.followup_id,
                'actionType': 'quote',
                'content': '매니저 수정 시도',
            }),
            content_type='application/json',
        )
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.user)
        other_company_response = self.client.post(
            reverse('reporting:notes_update_api', args=[target.id]),
            data=json.dumps({
                'followupId': other_target.followup_id,
                'actionType': 'quote',
                'content': '타사 고객으로 변경 시도',
            }),
            content_type='application/json',
        )
        self.assertEqual(other_company_response.status_code, 403)

    def test_note_file_upload_api_allows_owner_only(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from reporting.models import HistoryFile

        target = self._create_note(self.user, '파일업로드', action_type='quote', content='견적 파일')
        upload_url = reverse('reporting:note_file_upload', args=[target.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('manager.txt', b'manager memo', content_type='text/plain'),
        })
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('coworker.txt', b'coworker memo', content_type='text/plain'),
        })
        self.assertEqual(coworker_response.status_code, 403)

        self.client.force_login(self.user)
        response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('owner.txt', b'owner memo', content_type='text/plain'),
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        history_file = HistoryFile.objects.get(history=target)
        self.addCleanup(history_file.file.delete, False)
        self.assertEqual(history_file.original_filename, 'owner.txt')
        self.assertEqual(payload['files'][0]['id'], history_file.id)
        self.assertEqual(payload['files'][0]['downloadHref'], reverse('reporting:file_download', args=[history_file.id]))
        self.assertEqual(payload['files'][0]['deleteHref'], reverse('reporting:file_delete', args=[history_file.id]))

    def test_note_file_delete_api_allows_owner_only(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from reporting.models import HistoryFile

        target = self._create_note(self.user, '파일삭제', action_type='quote', content='삭제 파일')
        history_file = HistoryFile.objects.create(
            history=target,
            file=SimpleUploadedFile('delete-me.txt', b'delete memo', content_type='text/plain'),
            original_filename='delete-me.txt',
            file_size=11,
            uploaded_by=self.user,
        )
        delete_url = reverse('reporting:file_delete', args=[history_file.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(delete_url)
        self.assertEqual(manager_response.status_code, 403)
        self.assertTrue(HistoryFile.objects.filter(pk=history_file.id).exists())

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(delete_url)
        self.assertEqual(coworker_response.status_code, 403)
        self.assertTrue(HistoryFile.objects.filter(pk=history_file.id).exists())

        self.client.force_login(self.user)
        response = self.client.post(delete_url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertFalse(HistoryFile.objects.filter(pk=history_file.id).exists())

    def test_note_reply_create_api_allows_owner_and_same_company_manager(self):
        from reporting.models import History

        target = self._create_note(self.user, '댓글작성', action_type='quote', content='견적 댓글')
        reply_url = reverse('reporting:add_manager_memo_to_history_api', args=[target.id])

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(reply_url, {'memo': '동료 댓글 시도'})
        self.assertEqual(coworker_response.status_code, 403)

        self.client.force_login(self.other_manager)
        other_manager_response = self.client.post(reply_url, {'memo': '타사 매니저 댓글 시도'})
        self.assertEqual(other_manager_response.status_code, 403)

        self.client.force_login(self.user)
        owner_response = self.client.post(reply_url, {'memo': '실무자 댓글'})
        self.assertEqual(owner_response.status_code, 200)
        owner_reply = History.objects.get(parent_history=target, content='실무자 댓글')
        self.assertEqual(owner_reply.user, self.user)
        self.assertIsNone(owner_reply.created_by)

        self.client.force_login(self.manager)
        manager_response = self.client.post(reply_url, {'memo': '관리자 메모'})
        self.assertEqual(manager_response.status_code, 200)
        manager_reply = History.objects.get(parent_history=target, content='관리자 메모')
        self.assertEqual(manager_reply.user, self.user)
        self.assertEqual(manager_reply.created_by, self.manager)

    def test_note_reply_delete_api_allows_author_only(self):
        from reporting.models import History

        target = self._create_note(self.user, '댓글삭제', action_type='quote', content='삭제 댓글')
        owner_reply = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            parent_history=target,
            action_type='memo',
            content='실무자 삭제 댓글',
        )
        manager_reply = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            parent_history=target,
            action_type='memo',
            content='매니저 삭제 메모',
            created_by=self.manager,
        )

        owner_delete_url = reverse('reporting:delete_manager_memo_api', args=[owner_reply.id])
        manager_delete_url = reverse('reporting:delete_manager_memo_api', args=[manager_reply.id])

        self.client.force_login(self.manager)
        manager_denied = self.client.delete(owner_delete_url)
        self.assertEqual(manager_denied.status_code, 403)
        self.assertTrue(History.objects.filter(pk=owner_reply.id).exists())

        self.client.force_login(self.user)
        owner_denied = self.client.delete(manager_delete_url)
        self.assertEqual(owner_denied.status_code, 403)
        self.assertTrue(History.objects.filter(pk=manager_reply.id).exists())

        owner_response = self.client.delete(owner_delete_url)
        self.assertEqual(owner_response.status_code, 200)
        self.assertFalse(History.objects.filter(pk=owner_reply.id).exists())

        self.client.force_login(self.manager)
        manager_response = self.client.delete(manager_delete_url)
        self.assertEqual(manager_response.status_code, 200)
        self.assertFalse(History.objects.filter(pk=manager_reply.id).exists())

    def test_history_toggle_reviewed_allows_manager_only(self):
        target = self._create_note(
            self.user,
            '토글대상',
            action_type='quote',
            content='견적 보고 검토',
            reviewed=False,
        )
        toggle_url = reverse('reporting:history_toggle_reviewed', args=[target.id])

        self.client.force_login(self.user)
        denied = self.client.post(toggle_url)
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.admin)
        admin_denied = self.client.post(toggle_url)
        self.assertEqual(admin_denied.status_code, 403)

        self.client.force_login(self.other_manager)
        other_manager_denied = self.client.post(toggle_url)
        self.assertEqual(other_manager_denied.status_code, 403)

        self.client.force_login(self.manager)
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['is_reviewed'])
        target.refresh_from_db()
        self.assertIsNotNone(target.reviewed_at)
        self.assertEqual(target.reviewer, self.manager)


class PrepaymentsSummaryApiTests(TestCase):
    """React 선결제 현황 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='선결제API회사')
        self.other_company = UserCompany.objects.create(name='선결제API타사회사')
        self.user = make_user('prepayment_api_me', role='salesman', company=self.company)
        self.coworker = make_user('prepayment_api_coworker', role='salesman', company=self.company)
        self.other_user = make_user('prepayment_api_other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:prepayment_api_list')

    def _create_customer(self, owner, name):
        from reporting.models import Company, Department, FollowUp

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        return FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} 책임자',
            company=customer_company,
            department=department,
        )

    def _create_prepayment(self, owner, name, amount=100000, balance=70000, status='active', payer='입금자'):
        from django.utils import timezone
        from reporting.models import Prepayment

        customer = self._create_customer(owner, name)
        return Prepayment.objects.create(
            customer=customer,
            company=customer.company,
            amount=amount,
            balance=balance,
            payment_date=timezone.localdate(),
            payer_name=payer,
            status=status,
            created_by=owner,
        )

    def test_prepayment_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_prepayment_summary_api_defaults_to_current_user(self):
        own = self._create_prepayment(self.user, '내선결제', amount=100000, balance=70000, payer='내입금자')
        coworker = self._create_prepayment(self.coworker, '동료선결제', amount=200000, balance=200000, payer='동료입금자')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['scope']['dataFilter'], 'me')
        self.assertFalse(payload['scope']['isViewingOthers'])
        ids = {item['id'] for item in payload['prepayments']}
        self.assertIn(own.id, ids)
        self.assertNotIn(coworker.id, ids)
        self.assertEqual(payload['metrics']['totalAmount'], 100000)
        self.assertEqual(payload['metrics']['totalBalance'], 70000)
        self.assertEqual(payload['metrics']['totalUsed'], 30000)
        self.assertEqual(payload['links']['create'], reverse('reporting:prepayment_create'))
        own_payload = payload['prepayments'][0]
        self.assertEqual(own_payload['payerName'], '내입금자')
        self.assertEqual(own_payload['customerHref'], f'/customers/{own.customer_id}/')
        self.assertTrue(own_payload['canManage'])

    def test_prepayment_summary_api_filters_team_scope_search_and_status(self):
        own = self._create_prepayment(self.user, '내활성', amount=100000, balance=90000, status='active', payer='내입금')
        coworker = self._create_prepayment(
            self.coworker,
            '동료소진',
            amount=150000,
            balance=0,
            status='depleted',
            payer='동료입금자',
        )
        other = self._create_prepayment(
            self.other_user,
            '타사소진',
            amount=999000,
            balance=0,
            status='depleted',
            payer='동료입금자',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {
            'data_filter': 'all',
            'status': 'depleted',
            'search': '동료입금자',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['prepayments']}
        self.assertNotIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertTrue(payload['scope']['isViewingOthers'])
        self.assertEqual(payload['filters']['status'], 'depleted')
        self.assertEqual(payload['metrics']['depletedCount'], 1)
        self.assertEqual(payload['metrics']['totalAmount'], 150000)
        self.assertEqual(payload['links']['create'], '')


class PrepaymentDetailApiTests(TestCase):
    """React 선결제 상세/등록/수정 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='선결제상세API회사')
        self.other_company = UserCompany.objects.create(name='선결제상세API타사회사')
        self.user = make_user('prepayment_detail_me', role='salesman', company=self.company)
        self.coworker = make_user('prepayment_detail_coworker', role='salesman', company=self.company)
        self.other_user = make_user('prepayment_detail_other', role='salesman', company=self.other_company)

    def _create_customer(self, owner, name):
        from reporting.models import Company, Department, FollowUp

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        return FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            company=customer_company,
            department=department,
        )

    def _create_prepayment(self, owner, name='선결제', amount=100000, balance=70000):
        from django.utils import timezone
        from reporting.models import Prepayment

        customer = self._create_customer(owner, name)
        return Prepayment.objects.create(
            customer=customer,
            company=customer.company,
            amount=amount,
            balance=balance,
            payment_date=timezone.localdate(),
            payment_method='transfer',
            payer_name=f'{name} 입금자',
            memo='초기 메모',
            created_by=owner,
        )

    def test_prepayment_detail_api_returns_usage_and_edit_config(self):
        from datetime import time
        from django.utils import timezone
        from reporting.models import DeliveryItem, PrepaymentUsage, Schedule

        prepayment = self._create_prepayment(self.user, amount=120000, balance=90000)
        schedule = Schedule.objects.create(
            user=self.user,
            followup=prepayment.customer,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='테스트 품목',
            quantity=2,
            unit='EA',
            unit_price=15000,
            total_price=30000,
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=schedule,
            product_name='테스트 품목',
            quantity=2,
            amount=30000,
            remaining_balance=90000,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:prepayment_detail_api', args=[prepayment.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['prepayment']['id'], prepayment.id)
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(payload['metrics']['usedAmount'], 30000)
        self.assertEqual(payload['usages'][0]['amount'], 30000)
        self.assertEqual(payload['usages'][0]['deliveryItems'][0]['itemName'], '테스트 품목')
        self.assertEqual(payload['links']['reactEdit'], f'/prepayments/{prepayment.id}/edit/')
        self.assertTrue(payload['actions']['canCancel'])
        self.assertFalse(payload['actions']['canDelete'])
        self.assertIn('1개의 사용 내역', payload['actions']['deleteMessage'])
        self.assertTrue(payload['actions']['canTransfer'])
        self.assertEqual(payload['actions']['cancelUrl'], reverse('reporting:prepayment_cancel_api', args=[prepayment.id]))
        self.assertEqual(payload['actions']['deleteUrl'], reverse('reporting:prepayment_delete_api', args=[prepayment.id]))
        self.assertEqual(payload['actions']['transferUrl'], reverse('reporting:prepayment_transfer_api', args=[prepayment.id]))
        self.assertIn(self.coworker.id, [user['id'] for user in payload['actions']['transferUsers']])

    def test_prepayment_detail_api_blocks_other_company(self):
        prepayment = self._create_prepayment(self.other_user)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:prepayment_detail_api', args=[prepayment.id]))

        self.assertEqual(response.status_code, 403)

    def test_prepayment_create_api_creates_with_initial_balance(self):
        from reporting.models import Prepayment

        customer = self._create_customer(self.user, '등록고객')
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:prepayment_create_api'), {
            'customer': str(customer.id),
            'amount': '250000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'payer_name': '등록 입금자',
            'memo': 'React 등록',
        })

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        created = Prepayment.objects.get(id=payload['prepaymentId'])
        self.assertEqual(created.created_by, self.user)
        self.assertEqual(int(created.amount), 250000)
        self.assertEqual(int(created.balance), 250000)
        self.assertEqual(created.company, customer.company)
        self.assertEqual(payload['href'], f'/prepayments/{created.id}/')

    def test_prepayment_update_api_only_owner_and_validates_balance(self):
        prepayment = self._create_prepayment(self.user, amount=100000, balance=80000)

        self.client.force_login(self.coworker)
        denied = self.client.post(reverse('reporting:prepayment_update_api', args=[prepayment.id]), {
            'customer': str(prepayment.customer_id),
            'amount': '100000',
            'balance': '70000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'status': 'active',
        })
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.user)
        invalid = self.client.post(reverse('reporting:prepayment_update_api', args=[prepayment.id]), {
            'customer': str(prepayment.customer_id),
            'amount': '100000',
            'balance': '120000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'status': 'active',
        })
        self.assertEqual(invalid.status_code, 400)

        response = self.client.post(reverse('reporting:prepayment_update_api', args=[prepayment.id]), {
            'customer': str(prepayment.customer_id),
            'amount': '110000',
            'balance': '70000',
            'payment_date': '2026-05-10',
            'payment_method': 'card',
            'payer_name': '수정 입금자',
            'status': 'active',
            'memo': 'React 수정',
        })
        self.assertEqual(response.status_code, 200)
        prepayment.refresh_from_db()
        self.assertEqual(int(prepayment.amount), 110000)
        self.assertEqual(int(prepayment.balance), 70000)
        self.assertEqual(prepayment.payment_method, 'card')
        self.assertEqual(prepayment.memo, 'React 수정')

    def test_prepayment_cancel_api_only_owner_and_records_reason(self):
        prepayment = self._create_prepayment(self.user)

        self.client.force_login(self.coworker)
        denied = self.client.post(reverse('reporting:prepayment_cancel_api', args=[prepayment.id]), {
            'cancel_reason': '동료 취소 시도',
        })
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.user)
        response = self.client.post(reverse('reporting:prepayment_cancel_api', args=[prepayment.id]), {
            'cancel_reason': 'React 취소',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        prepayment.refresh_from_db()
        self.assertEqual(prepayment.status, 'cancelled')
        self.assertEqual(prepayment.cancel_reason, 'React 취소')
        self.assertIsNotNone(prepayment.cancelled_at)
        self.assertEqual(payload['prepayment']['status'], 'cancelled')

    def test_prepayment_delete_api_blocks_used_records_and_deletes_unused(self):
        from reporting.models import Prepayment, PrepaymentUsage

        used_prepayment = self._create_prepayment(self.user)
        PrepaymentUsage.objects.create(
            prepayment=used_prepayment,
            product_name='삭제 차단 품목',
            quantity=1,
            amount=10000,
            remaining_balance=60000,
        )
        self.client.force_login(self.user)

        blocked = self.client.post(reverse('reporting:prepayment_delete_api', args=[used_prepayment.id]))
        self.assertEqual(blocked.status_code, 400)
        self.assertTrue(Prepayment.objects.filter(id=used_prepayment.id).exists())

        unused_prepayment = self._create_prepayment(self.user, name='삭제가능')
        deleted = self.client.post(reverse('reporting:prepayment_delete_api', args=[unused_prepayment.id]))

        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(deleted.json()['success'])
        self.assertEqual(deleted.json()['href'], '/prepayments/')
        self.assertFalse(Prepayment.objects.filter(id=unused_prepayment.id).exists())

    def test_prepayment_transfer_api_moves_owner_and_appends_memo(self):
        prepayment = self._create_prepayment(self.user)
        self.client.force_login(self.user)

        other_company_response = self.client.post(reverse('reporting:prepayment_transfer_api', args=[prepayment.id]), {
            'target_user': str(self.other_user.id),
            'reason': '타사 이관 시도',
        })
        self.assertEqual(other_company_response.status_code, 400)

        response = self.client.post(reverse('reporting:prepayment_transfer_api', args=[prepayment.id]), {
            'target_user': str(self.coworker.id),
            'reason': '담당자 변경',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['prepayment']['ownerId'], self.coworker.id)
        self.assertFalse(payload['prepayment']['canManage'])

        prepayment.refresh_from_db()
        self.assertEqual(prepayment.created_by, self.coworker)
        self.assertIn('[이관]', prepayment.memo)
        self.assertIn('담당자 변경', prepayment.memo)

        detail = self.client.get(reverse('reporting:prepayment_detail_api', args=[prepayment.id]))
        self.assertEqual(detail.status_code, 200)
        detail_payload = detail.json()
        self.assertFalse(detail_payload['edit']['canEdit'])
        self.assertFalse(detail_payload['actions']['canTransfer'])


class PrepaymentCustomerApiTests(TestCase):
    """React 고객별/부서별 선결제 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='고객별선결제API회사')
        self.other_company = UserCompany.objects.create(name='고객별선결제API타사회사')
        self.user = make_user('prepayment_customer_me', role='salesman', company=self.company)
        self.coworker = make_user('prepayment_customer_coworker', role='salesman', company=self.company)
        self.manager = make_user('prepayment_customer_manager', role='manager', company=self.company)
        self.other_user = make_user('prepayment_customer_other', role='salesman', company=self.other_company)

    def _create_department_customers(self, owner=None):
        from reporting.models import Company, Department, FollowUp

        owner = owner or self.user
        customer_company = Company.objects.create(name=f'고객별선결제 고객사 {owner.username}', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name='공동 연구실',
            created_by=owner,
        )
        first = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name='1번 담당자',
            company=customer_company,
            department=department,
        )
        second = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name='2번 담당자',
            company=customer_company,
            department=department,
        )
        return customer_company, department, first, second

    def _create_prepayment(self, owner, customer, amount=100000, balance=70000, status='active', payer='입금자'):
        from django.utils import timezone
        from reporting.models import Prepayment

        return Prepayment.objects.create(
            customer=customer,
            company=customer.company,
            amount=amount,
            balance=balance,
            payment_date=timezone.localdate(),
            payment_method='transfer',
            payer_name=payer,
            memo='고객별 메모',
            status=status,
            created_by=owner,
        )

    def test_customer_prepayment_api_returns_department_scope_and_metrics(self):
        _company, department, first, second = self._create_department_customers()
        self._create_prepayment(self.user, first, amount=100000, balance=70000, status='active', payer='첫 입금')
        self._create_prepayment(self.user, second, amount=200000, balance=0, status='depleted', payer='둘째 입금')
        self._create_prepayment(self.coworker, first, amount=500000, balance=500000, payer='동료 입금')
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['scope']['mode'], 'department')
        self.assertEqual(payload['customer']['departmentId'], department.id)
        self.assertEqual(payload['scope']['targetUserId'], self.user.id)
        self.assertEqual(len(payload['departmentCustomers']), 2)
        self.assertEqual(payload['metrics']['totalAmount'], 300000)
        self.assertEqual(payload['metrics']['totalBalance'], 70000)
        self.assertEqual(payload['metrics']['totalUsed'], 230000)
        self.assertEqual(payload['metrics']['totalCount'], 2)
        self.assertEqual(payload['metrics']['activeCount'], 1)
        self.assertEqual(payload['metrics']['depletedCount'], 1)
        self.assertEqual([item['customerId'] for item in payload['prepayments']], [first.id, second.id])
        self.assertEqual(payload['links']['reactCustomer'], f'/prepayments/customer/{first.id}/')
        self.assertEqual(payload['links']['djangoExcel'], reverse('reporting:prepayment_customer_excel', args=[first.id]))
        self.assertEqual(payload['prepayments'][0]['customerPrepaymentHref'], f'/prepayments/customer/{first.id}/')

    def test_customer_prepayment_api_uses_selected_accessible_user_for_manager(self):
        _company, _department, first, _second = self._create_department_customers()
        self._create_prepayment(self.user, first, amount=100000, balance=100000, payer='내 입금')
        self._create_prepayment(self.coworker, first, amount=250000, balance=150000, payer='동료 입금')
        session = self.client.session
        session['selected_user_id'] = str(self.coworker.id)
        session.save()
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['scope']['canSelectUser'])
        self.assertEqual(payload['scope']['targetUserId'], self.coworker.id)
        self.assertEqual(payload['metrics']['totalAmount'], 250000)
        self.assertEqual(len(payload['prepayments']), 1)
        self.assertEqual(payload['prepayments'][0]['ownerId'], self.coworker.id)

    def test_customer_prepayment_api_allows_salesman_with_own_prepayment_and_blocks_unrelated(self):
        _company, _department, first, _second = self._create_department_customers(owner=self.coworker)
        self._create_prepayment(self.user, first, amount=90000, balance=50000, payer='접근 허용 입금')

        self.client.force_login(self.user)
        allowed = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()['metrics']['totalAmount'], 90000)

        self.client.force_login(self.other_user)
        blocked = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))
        self.assertEqual(blocked.status_code, 403)

    def test_customer_prepayment_api_requires_login(self):
        _company, _department, first, _second = self._create_department_customers()

        response = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')


class SchedulesSummaryApiTests(TestCase):
    """React 일정 화면 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='일정API회사')
        self.other_company = UserCompany.objects.create(name='일정API타사회사')
        self.user = make_user('schedules_api_me', role='salesman', company=self.company)
        self.coworker = make_user('schedules_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('schedules_api_manager', role='manager', company=self.company)
        self.other_user = make_user('schedules_api_other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:schedules_summary_api')
        self.create_url = reverse('reporting:schedules_create_api')
        self.calendar_url = reverse('reporting:schedules_calendar_api')

    def _create_customer(self, owner, name):
        from reporting.models import Company, Department, FollowUp

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        return FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} 책임',
            company=customer_company,
            department=department,
            priority='urgent',
            pipeline_stage='quote',
        )

    def _create_schedule(
        self,
        owner,
        name,
        activity_type='customer_meeting',
        status='scheduled',
        visit_date=None,
    ):
        import datetime
        from django.utils import timezone
        from reporting.models import Schedule

        followup = self._create_customer(owner, name)
        return Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=visit_date or timezone.localdate(),
            visit_time=datetime.time(9, 0),
            activity_type=activity_type,
            status=status,
            location=f'{name} 회의실',
            notes=f'{name} 일정 메모',
        )

    def _create_personal_schedule(self, owner, title, schedule_date=None):
        import datetime
        from django.utils import timezone
        from reporting.models import PersonalSchedule

        return PersonalSchedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            title=title,
            content=f'{title} 내용',
            schedule_date=schedule_date or timezone.localdate(),
            schedule_time=datetime.time(14, 0),
        )

    def test_schedules_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_schedules_summary_api_uses_salesman_own_scope(self):
        own = self._create_schedule(self.user, '내일정')
        personal = self._create_personal_schedule(self.user, '내 개인 일정')
        coworker = self._create_schedule(self.coworker, '동료일정')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {(item['type'], item['id']) for item in payload['schedules']}
        self.assertIn(('customer', own.id), ids)
        self.assertIn(('personal', personal.id), ids)
        self.assertNotIn(('customer', coworker.id), ids)
        self.assertEqual(payload['metrics']['totalSchedules'], 2)
        self.assertTrue(payload['create']['canCreate'])
        self.assertEqual(payload['create']['submitUrl'], self.create_url)
        self.assertTrue(any(customer['id'] == own.followup_id for customer in payload['create']['customers']))
        own_item = next(item for item in payload['schedules'] if item['type'] == 'customer' and item['id'] == own.id)
        self.assertEqual(own_item['href'], f'/schedules/{own.id}/')
        self.assertEqual(own_item['djangoHref'], reverse('reporting:schedule_detail', args=[own.id]))

    def test_schedules_summary_api_defaults_to_latest_schedule_first(self):
        from datetime import timedelta
        from django.utils import timezone

        older = self._create_schedule(
            self.user,
            '오래된일정',
            visit_date=timezone.localdate() - timedelta(days=4),
        )
        newer = self._create_schedule(
            self.user,
            '최근일정',
            visit_date=timezone.localdate() + timedelta(days=2),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['schedules'][0]['type'], 'customer')
        self.assertEqual(payload['schedules'][0]['id'], newer.id)
        self.assertNotEqual(payload['schedules'][0]['id'], older.id)

    def test_schedules_summary_api_filters_search_owner_status_activity_and_range(self):
        from datetime import timedelta
        from django.utils import timezone

        target = self._create_schedule(
            self.user,
            'PCR핵심',
            activity_type='quote',
            status='scheduled',
            visit_date=timezone.localdate() + timedelta(days=1),
        )
        self._create_schedule(
            self.user,
            'PCR완료',
            activity_type='quote',
            status='completed',
            visit_date=timezone.localdate() + timedelta(days=1),
        )
        self._create_schedule(
            self.user,
            'PCR서비스',
            activity_type='service',
            status='scheduled',
            visit_date=timezone.localdate() + timedelta(days=1),
        )
        self._create_schedule(
            self.coworker,
            'PCR동료',
            activity_type='quote',
            status='scheduled',
            visit_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(self.manager)

        response = self.client.get(self.url, {
            'q': 'PCR',
            'owner': str(self.user.id),
            'status': 'scheduled',
            'activityType': 'quote',
            'range': 'week',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = [(item['type'], item['id']) for item in payload['schedules']]
        self.assertEqual(ids, [('customer', target.id)])
        self.assertEqual(payload['filters']['q'], 'PCR')
        self.assertTrue(any(option['value'] == 'quote' for option in payload['options']['activityTypes']))
        self.assertEqual(payload['metrics']['filteredSchedules'], 1)

    def test_schedules_summary_api_manager_sees_same_company_only(self):
        own = self._create_schedule(self.user, '회사내일정')
        coworker = self._create_schedule(self.coworker, '회사내동료일정')
        other = self._create_schedule(self.other_user, '타사일정')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['schedules'] if item['type'] == 'customer'}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(payload['metrics']['totalSchedules'], 2)
        self.assertTrue(payload['scope']['canViewAll'])
        self.assertFalse(payload['create']['canCreate'])

    def test_schedules_calendar_api_requires_login_json(self):
        response = self.client.get(self.calendar_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_schedules_calendar_api_returns_month_range_items(self):
        import datetime
        from reporting.models import History

        target_date = datetime.date(2026, 5, 10)
        outside_date = datetime.date(2026, 6, 1)
        own = self._create_schedule(self.user, '월간일정', visit_date=target_date)
        personal = self._create_personal_schedule(self.user, '월간 개인 일정', schedule_date=target_date)
        outside = self._create_schedule(self.user, '범위밖일정', visit_date=outside_date)
        report = History.objects.create(
            user=self.user,
            company=self.company,
            followup=own.followup,
            schedule=own,
            action_type='customer_meeting',
            content='캘린더에서 보여줄 미팅 보고 본문',
            meeting_situation='PCR 장비 도입 검토 중',
            meeting_confirmed_facts='예산 담당자 확인',
            meeting_next_action='견적서 송부',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.calendar_url, {
            'start': '2026-05-01',
            'end': '2026-05-31',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {(item['type'], item['id']) for item in payload['schedules']}
        self.assertIn(('customer', own.id), ids)
        self.assertIn(('personal', personal.id), ids)
        self.assertNotIn(('customer', outside.id), ids)
        own_item = next(item for item in payload['schedules'] if item['type'] == 'customer' and item['id'] == own.id)
        personal_item = next(item for item in payload['schedules'] if item['type'] == 'personal' and item['id'] == personal.id)
        self.assertTrue(own_item['canEdit'])
        self.assertEqual(own_item['statusUpdateHref'], reverse('reporting:schedule_status_update', args=[own.id]))
        self.assertEqual(own_item['djangoEditHref'], reverse('reporting:schedule_edit', args=[own.id]))
        self.assertEqual(
            {option['value'] for option in own_item['statusOptions']},
            {'scheduled', 'completed', 'cancelled'},
        )
        self.assertEqual(own_item['reports'][0]['id'], report.id)
        self.assertEqual(own_item['reports'][0]['content'], '캘린더에서 보여줄 미팅 보고 본문')
        self.assertEqual(own_item['reports'][0]['meetingSituation'], 'PCR 장비 도입 검토 중')
        self.assertEqual(own_item['reports'][0]['meetingConfirmedFacts'], '예산 담당자 확인')
        self.assertEqual(own_item['reports'][0]['nextAction'], '견적서 송부')
        self.assertFalse(personal_item['canEdit'])
        self.assertEqual(personal_item['statusOptions'], [])
        self.assertEqual(personal_item['reports'], [])
        self.assertEqual(payload['filters']['start'], '2026-05-01')
        self.assertEqual(payload['filters']['end'], '2026-05-31')
        self.assertEqual(payload['metrics']['totalSchedules'], 2)
        self.assertEqual(payload['links']['calendar'], '/schedules/calendar/')
        self.assertEqual(payload['links']['djangoCalendar'], reverse('reporting:schedule_calendar'))

    def test_schedules_calendar_api_all_filter_uses_same_company_only(self):
        import datetime

        target_date = datetime.date(2026, 5, 10)
        own = self._create_schedule(self.user, '회사내월간일정', visit_date=target_date)
        coworker = self._create_schedule(self.coworker, '동료월간일정', visit_date=target_date)
        other = self._create_schedule(self.other_user, '타사회사월간일정', visit_date=target_date)
        self.client.force_login(self.user)

        response = self.client.get(self.calendar_url, {
            'start': '2026-05-01',
            'end': '2026-05-31',
            'data_filter': 'all',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['schedules'] if item['type'] == 'customer'}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        own_item = next(item for item in payload['schedules'] if item['type'] == 'customer' and item['id'] == own.id)
        coworker_item = next(item for item in payload['schedules'] if item['type'] == 'customer' and item['id'] == coworker.id)
        self.assertTrue(own_item['canEdit'])
        self.assertFalse(coworker_item['canEdit'])
        self.assertEqual(coworker_item['statusUpdateHref'], '')
        self.assertEqual(payload['scope']['dataFilter'], 'all')
        self.assertTrue(any(option['id'] == self.coworker.id for option in payload['options']['users']))

    def test_schedules_calendar_api_user_filter_limits_to_selected_company_user(self):
        import datetime

        target_date = datetime.date(2026, 5, 10)
        self._create_schedule(self.user, '내월간일정', visit_date=target_date)
        coworker = self._create_schedule(self.coworker, '선택직원월간일정', visit_date=target_date)
        self.client.force_login(self.manager)

        response = self.client.get(self.calendar_url, {
            'start': '2026-05-01',
            'end': '2026-05-31',
            'data_filter': 'user',
            'filter_user': str(self.coworker.id),
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = [(item['type'], item['id']) for item in payload['schedules']]
        self.assertEqual(ids, [('customer', coworker.id)])
        self.assertEqual(payload['scope']['dataFilter'], 'user')
        self.assertEqual(payload['scope']['filterUserId'], self.coworker.id)

    def test_schedules_create_api_requires_login_json(self):
        import json

        response = self.client.post(
            self.create_url,
            data=json.dumps({}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_schedules_create_api_blocks_manager(self):
        import json

        followup = self._create_customer(self.user, '매니저차단')
        self.client.force_login(self.manager)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': followup.id,
                'activityType': 'customer_meeting',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_schedules_create_api_salesman_creates_own_schedule(self):
        import json
        from reporting.models import Schedule

        followup = self._create_customer(self.user, '빠른등록')
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': followup.id,
                'activityType': 'quote',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
                'location': '고객 회의실',
                'notes': '견적 일정 등록',
                'expectedRevenue': '1200000',
                'probability': '60',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload['success'])
        schedule = Schedule.objects.get(pk=payload['scheduleId'])
        self.assertEqual(schedule.user, self.user)
        self.assertEqual(schedule.followup, followup)
        self.assertEqual(schedule.activity_type, 'quote')
        self.assertEqual(schedule.location, '고객 회의실')
        self.assertEqual(int(schedule.expected_revenue), 1200000)
        self.assertEqual(schedule.probability, 60)
        self.assertEqual(payload['schedule']['id'], schedule.id)
        self.assertEqual(payload['href'], f'/schedules/{schedule.id}/')

    def test_schedules_create_api_blocks_other_salesman_customer(self):
        import json
        from reporting.models import Schedule

        followup = self._create_customer(self.coworker, '동료고객')
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': followup.id,
                'activityType': 'customer_meeting',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Schedule.objects.filter(followup=followup, user=self.user).exists())

    def test_schedules_detail_api_returns_detail_and_edit_config(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from reporting.models import DeliveryItem, History, ScheduleFile

        schedule = self._create_schedule(self.user, '상세일정', activity_type='delivery')
        schedule.quote_extra_notes = '전체 견적 기타사항'
        schedule.save(update_fields=['quote_extra_notes'])
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            schedule=schedule,
            action_type='delivery_schedule',
            content='납품 보고',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='PCR Kit',
            quantity=2,
            unit='EA',
            unit_price=100000,
            discount_rate=10,
            notes='PCR 적요',
        )
        schedule_file = ScheduleFile.objects.create(
            schedule=schedule,
            file=SimpleUploadedFile('schedule-note.txt', b'schedule file note', content_type='text/plain'),
            original_filename='schedule-note.txt',
            file_size=18,
            uploaded_by=self.user,
        )
        self.addCleanup(schedule_file.file.delete, False)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['schedule']['id'], schedule.id)
        self.assertEqual(payload['schedule']['href'], f'/schedules/{schedule.id}/')
        self.assertEqual(payload['schedule']['customerHref'], f'/customers/{schedule.followup_id}/')
        self.assertEqual(payload['schedule']['quoteExtraNotes'], '전체 견적 기타사항')
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(payload['edit']['submitUrl'], reverse('reporting:schedules_update_api', args=[schedule.id]))
        self.assertEqual(payload['relatedNotes'][0]['id'], schedule.histories.first().id)
        self.assertEqual(payload['deliveryItems'][0]['itemName'], 'PCR Kit')
        self.assertEqual(payload['deliveryItems'][0]['discountRate'], 10.0)
        self.assertEqual(payload['deliveryItems'][0]['discountUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['effectiveUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['totalPrice'], 198000)
        self.assertEqual(payload['deliveryItems'][0]['notes'], 'PCR 적요')
        self.assertEqual(payload['links']['uploadFiles'], reverse('reporting:schedule_file_upload', args=[schedule.id]))
        self.assertEqual(payload['links']['updateDeliveryItems'], reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]))
        self.assertEqual(payload['links']['prepayments'], reverse('reporting:prepayment_api_list'))
        self.assertEqual(payload['schedule']['files'][0]['id'], schedule_file.id)
        self.assertEqual(payload['schedule']['files'][0]['deleteHref'], reverse('reporting:schedule_file_delete', args=[schedule_file.id]))
        document_types = [item['type'] for item in payload['documents']['items']]
        self.assertEqual(document_types, ['transaction_statement', 'delivery_note'])
        first_document = payload['documents']['items'][0]
        self.assertEqual(first_document['previewHref'], reverse('reporting:get_document_template_data', args=['transaction_statement', schedule.id]))
        self.assertEqual(
            first_document['formats'][0]['href'],
            reverse('reporting:generate_document_pdf_format', args=['transaction_statement', schedule.id, 'pdf']),
        )
        self.assertEqual(
            first_document['formats'][1]['href'],
            reverse('reporting:generate_document_pdf_format', args=['transaction_statement', schedule.id, 'xlsx']),
        )
        self.assertEqual(payload['documents']['templateManagerHref'], '/documents/')
        self.assertEqual(payload['documents']['djangoTemplateManagerHref'], reverse('reporting:document_template_list'))

    def test_schedules_detail_api_document_actions_match_activity_type(self):
        quote_schedule = self._create_schedule(self.user, '견적서류', activity_type='quote')
        meeting_schedule = self._create_schedule(self.user, '미팅서류없음', activity_type='customer_meeting')
        self.client.force_login(self.user)

        quote_response = self.client.get(reverse('reporting:schedules_detail_api', args=[quote_schedule.id]))
        meeting_response = self.client.get(reverse('reporting:schedules_detail_api', args=[meeting_schedule.id]))

        self.assertEqual(quote_response.status_code, 200)
        self.assertEqual(meeting_response.status_code, 200)
        quote_payload = quote_response.json()
        meeting_payload = meeting_response.json()
        self.assertTrue(quote_payload['documents']['canGenerate'])
        self.assertEqual([item['type'] for item in quote_payload['documents']['items']], ['quotation'])
        self.assertEqual(
            quote_payload['documents']['items'][0]['formats'][1]['href'],
            reverse('reporting:generate_document_pdf_format', args=['quotation', quote_schedule.id, 'xlsx']),
        )
        self.assertFalse(meeting_payload['documents']['canGenerate'])
        self.assertEqual(meeting_payload['documents']['items'], [])

    def test_schedules_detail_api_splits_quotation_documents_by_quote_group(self):
        from reporting.models import DeliveryItem

        quote_schedule = self._create_schedule(self.user, '복수견적서류', activity_type='quote')
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Trade In Kit',
            quantity=1,
            unit='EA',
            unit_price=100000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Repair Service',
            quantity=1,
            unit='EA',
            unit_price=50000,
            quote_group='수리',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[quote_schedule.id]))

        self.assertEqual(response.status_code, 200)
        actions = response.json()['documents']['items']
        self.assertEqual([action['quoteGroup'] for action in actions], ['보상판매', '수리'])
        self.assertEqual([action['label'] for action in actions], ['보상판매 견적서', '수리 견적서'])
        self.assertIn('quote_group=', actions[0]['previewHref'])
        self.assertIn('quote_group=', actions[1]['formats'][0]['href'])
        self.assertEqual(actions[0]['itemCount'], 1)

    def test_schedules_detail_api_includes_registered_generated_documents(self):
        schedule = self._create_schedule(self.user, '등록서류목록', activity_type='delivery')
        log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='transaction_statement',
            schedule=schedule,
            user=self.user,
            transaction_number='TS-20260512-001',
            output_format='pdf',
            file=SimpleUploadedFile('statement.pdf', b'%PDF statement', content_type='application/pdf'),
            filename='statement.pdf',
            file_size=14,
        )
        self.addCleanup(log.file.delete, False)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 200)
        documents = response.json()['documents']
        self.assertEqual(documents['registeredDocumentCount'], 1)
        self.assertEqual(documents['registeredQuotationCount'], 0)
        registered = documents['registeredDocuments'][0]
        self.assertEqual(registered['id'], log.id)
        self.assertEqual(registered['documentType'], 'transaction_statement')
        self.assertEqual(registered['documentTypeLabel'], '거래명세서')
        self.assertEqual(registered['downloadHref'], reverse('reporting:generated_document_download', args=[log.id]))
        self.assertEqual(registered['deleteHref'], reverse('reporting:generated_document_delete', args=[log.id]))
        self.assertTrue(registered['canDelete'])

    def test_generated_document_delete_api_allows_owner_only(self):
        schedule = self._create_schedule(self.user, '등록서류삭제', activity_type='quote')
        log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=schedule,
            user=self.user,
            transaction_number='Q-20260512-001',
            output_format='pdf',
            file=SimpleUploadedFile('quote.pdf', b'%PDF quote', content_type='application/pdf'),
            filename='quote.pdf',
            file_size=10,
            quote_group='수리',
        )
        self.addCleanup(log.file.delete, False)
        delete_url = reverse('reporting:generated_document_delete', args=[log.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(delete_url)
        self.assertEqual(manager_response.status_code, 403)
        self.assertTrue(DocumentGenerationLog.objects.filter(pk=log.id).exists())

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(delete_url)
        self.assertEqual(coworker_response.status_code, 403)
        self.assertTrue(DocumentGenerationLog.objects.filter(pk=log.id).exists())

        self.client.force_login(self.user)
        response = self.client.post(delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(DocumentGenerationLog.objects.filter(pk=log.id).exists())

    def test_schedules_detail_api_manager_read_only_and_other_company_blocked(self):
        schedule = self._create_schedule(self.user, '읽기전용')
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['edit']['canEdit'])
        self.assertEqual(response.json()['links']['updateDeliveryItems'], '')

        self.client.force_login(self.other_user)
        denied = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))
        self.assertEqual(denied.status_code, 403)

    def test_product_api_list_returns_accessible_product_master_data(self):
        from reporting.models import Product

        global_product = Product.objects.create(
            product_code='MASTER-GLOBAL-PCR',
            unit='BOX',
            specification='96 reactions',
            standard_price=1000,
            created_by=None,
        )
        own_product = Product.objects.create(
            product_code='MASTER-OWN-PCR',
            unit='EA',
            standard_price=2000,
            created_by=self.user,
        )
        coworker_product = Product.objects.create(
            product_code='MASTER-COWORKER-PCR',
            unit='SET',
            standard_price=3000,
            created_by=self.coworker,
        )
        other_product = Product.objects.create(
            product_code='MASTER-OTHER-PCR',
            unit='EA',
            standard_price=4000,
            created_by=self.other_user,
        )
        inactive_product = Product.objects.create(
            product_code='MASTER-INACTIVE-PCR',
            unit='EA',
            standard_price=5000,
            is_active=False,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:product_api_list'), {'search': 'MASTER-'})

        self.assertEqual(response.status_code, 200)
        products = response.json()['products']
        product_codes = {product['product_code'] for product in products}
        self.assertIn(global_product.product_code, product_codes)
        self.assertIn(own_product.product_code, product_codes)
        self.assertIn(coworker_product.product_code, product_codes)
        self.assertNotIn(other_product.product_code, product_codes)
        self.assertNotIn(inactive_product.product_code, product_codes)
        global_payload = next(product for product in products if product['product_code'] == global_product.product_code)
        self.assertEqual(global_payload['unit'], 'BOX')
        self.assertEqual(global_payload['specification'], '96 reactions')
        self.assertEqual(global_payload['current_price'], 1000.0)

    def test_schedules_update_api_updates_owned_schedule(self):
        import json

        schedule = self._create_schedule(self.user, '수정전')
        target_followup = self._create_customer(self.coworker, '수정후')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_update_api', args=[schedule.id]),
            data=json.dumps({
                'followupId': target_followup.id,
                'activityType': 'delivery',
                'status': 'completed',
                'visitDate': '2026-05-11',
                'visitTime': '15:45',
                'location': '수정 회의실',
                'notes': '일정 수정 메모',
                'expectedRevenue': '2500000',
                'probability': '80',
                'expectedCloseDate': '2026-06-01',
                'purchaseConfirmed': True,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        schedule.refresh_from_db()
        self.assertEqual(schedule.followup, target_followup)
        self.assertEqual(schedule.activity_type, 'delivery')
        self.assertEqual(schedule.status, 'completed')
        self.assertEqual(schedule.visit_date.isoformat(), '2026-05-11')
        self.assertEqual(schedule.visit_time.strftime('%H:%M'), '15:45')
        self.assertEqual(schedule.location, '수정 회의실')
        self.assertEqual(schedule.notes, '일정 수정 메모')
        self.assertEqual(int(schedule.expected_revenue), 2500000)
        self.assertEqual(schedule.probability, 80)
        self.assertEqual(schedule.expected_close_date.isoformat(), '2026-06-01')
        self.assertTrue(schedule.purchase_confirmed)
        self.assertEqual(payload['schedule']['id'], schedule.id)
        self.assertEqual(payload['message'], '일정을 수정했습니다.')

    def test_prepayment_api_list_includes_same_department_and_existing_usage(self):
        from django.utils import timezone
        from reporting.models import FollowUp, Prepayment, PrepaymentUsage

        schedule = self._create_schedule(self.user, '선결제조회', activity_type='delivery')
        same_department_customer = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            customer_name='같은부서 고객',
            manager='같은부서 담당',
            company=schedule.followup.company,
            department=schedule.followup.department,
        )
        other_department_customer = self._create_customer(self.user, '다른부서')
        active_prepayment = Prepayment.objects.create(
            customer=same_department_customer,
            company=same_department_customer.company,
            amount=100000,
            balance=80000,
            payment_date=timezone.localdate(),
            payer_name='같은부서입금',
            created_by=self.user,
        )
        selected_depleted_prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=40000,
            balance=0,
            payment_date=timezone.localdate(),
            payer_name='기존차감',
            status='depleted',
            created_by=self.user,
        )
        PrepaymentUsage.objects.create(
            prepayment=selected_depleted_prepayment,
            schedule=schedule,
            product_name='기존 납품',
            quantity=1,
            amount=40000,
            remaining_balance=0,
        )
        Prepayment.objects.create(
            customer=other_department_customer,
            company=other_department_customer.company,
            amount=50000,
            balance=50000,
            payment_date=timezone.localdate(),
            payer_name='다른부서입금',
            created_by=self.user,
        )
        schedule.use_prepayment = True
        schedule.prepayment = selected_depleted_prepayment
        schedule.prepayment_amount = 40000
        schedule.save(update_fields=['use_prepayment', 'prepayment', 'prepayment_amount'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:prepayment_api_list'), {
            'customer_id': schedule.followup_id,
            'schedule_id': schedule.id,
        })

        self.assertEqual(response.status_code, 200)
        prepayments = response.json()['prepayments']
        ids = {item['id'] for item in prepayments}
        self.assertIn(active_prepayment.id, ids)
        self.assertIn(selected_depleted_prepayment.id, ids)
        selected_payload = next(item for item in prepayments if item['id'] == selected_depleted_prepayment.id)
        self.assertEqual(selected_payload['balance'], 0)
        self.assertEqual(selected_payload['selectedAmount'], 40000)
        self.assertEqual(selected_payload['availableBalance'], 40000)

    def test_schedules_update_api_applies_and_restores_prepayments(self):
        import json
        from django.utils import timezone
        from reporting.models import Prepayment, PrepaymentUsage

        schedule = self._create_schedule(self.user, '선결제수정', activity_type='delivery')
        prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=100000,
            balance=100000,
            payment_date=timezone.localdate(),
            payer_name='선결제고객',
            created_by=self.user,
        )
        update_url = reverse('reporting:schedules_update_api', args=[schedule.id])
        self.client.force_login(self.user)

        apply_response = self.client.post(
            update_url,
            data=json.dumps({
                'followupId': schedule.followup_id,
                'activityType': 'delivery',
                'status': 'scheduled',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
                'usePrepayment': True,
                'prepayments': [
                    {'id': prepayment.id, 'amount': '60000'},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(apply_response.status_code, 200)
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 40000)
        self.assertTrue(schedule.use_prepayment)
        self.assertEqual(schedule.prepayment, prepayment)
        self.assertEqual(int(schedule.prepayment_amount), 60000)
        usage = PrepaymentUsage.objects.get(schedule=schedule)
        self.assertEqual(int(usage.amount), 60000)
        self.assertEqual(apply_response.json()['schedule']['prepaymentUsages'][0]['amount'], 60000)

        restore_response = self.client.post(
            update_url,
            data=json.dumps({
                'followupId': schedule.followup_id,
                'activityType': 'delivery',
                'status': 'scheduled',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
                'usePrepayment': False,
                'prepayments': [],
            }),
            content_type='application/json',
        )

        self.assertEqual(restore_response.status_code, 200)
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 100000)
        self.assertFalse(schedule.use_prepayment)
        self.assertIsNone(schedule.prepayment)
        self.assertEqual(int(schedule.prepayment_amount), 0)
        self.assertFalse(PrepaymentUsage.objects.filter(schedule=schedule).exists())

    def test_schedules_update_api_blocks_over_balance_prepayment(self):
        import json
        from django.utils import timezone
        from reporting.models import Prepayment, PrepaymentUsage

        schedule = self._create_schedule(self.user, '선결제잔액차단', activity_type='delivery')
        prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=1000,
            balance=1000,
            payment_date=timezone.localdate(),
            payer_name='잔액부족',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_update_api', args=[schedule.id]),
            data=json.dumps({
                'followupId': schedule.followup_id,
                'activityType': 'delivery',
                'status': 'scheduled',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
                'usePrepayment': True,
                'prepayments': [
                    {'id': prepayment.id, 'amount': '2000'},
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('잔액이 부족', response.json()['error'])
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 1000)
        self.assertFalse(schedule.use_prepayment)
        self.assertFalse(PrepaymentUsage.objects.filter(schedule=schedule).exists())

    def test_schedules_update_api_blocks_manager_and_other_company_customer(self):
        import json

        schedule = self._create_schedule(self.user, '수정차단')
        other_followup = self._create_customer(self.other_user, '타사고객')
        update_url = reverse('reporting:schedules_update_api', args=[schedule.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(
            update_url,
            data=json.dumps({
                'followupId': schedule.followup_id,
                'activityType': 'customer_meeting',
                'status': 'scheduled',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
            }),
            content_type='application/json',
        )
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.user)
        other_company_response = self.client.post(
            update_url,
            data=json.dumps({
                'followupId': other_followup.id,
                'activityType': 'customer_meeting',
                'status': 'scheduled',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
            }),
            content_type='application/json',
        )
        self.assertEqual(other_company_response.status_code, 403)
        schedule.refresh_from_db()
        self.assertNotEqual(schedule.followup, other_followup)

    def test_schedule_delivery_items_update_api_updates_owned_items_and_history(self):
        import json
        from reporting.models import DeliveryItem, History

        schedule = self._create_schedule(self.user, '납품품목', activity_type='delivery')
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Old Kit',
            quantity=1,
            unit='EA',
            unit_price=1000,
        )
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            schedule=schedule,
            action_type='delivery_schedule',
            delivery_items='old',
            delivery_amount=1000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'quoteExtraNotes': '견적 전체 기타사항',
                'items': [
                    {
                        'itemName': 'PCR Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '100000',
                        'discountRate': '10',
                        'taxInvoiceIssued': True,
                        'notes': 'PCR 적요',
                    },
                    {
                        'itemName': 'Buffer',
                        'quantity': 3,
                        'unit': 'BOX',
                        'unitPrice': '',
                        'taxInvoiceIssued': False,
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['message'], '납품 품목을 저장했습니다.')
        items = list(DeliveryItem.objects.filter(schedule=schedule).order_by('id'))
        self.assertEqual([item.item_name for item in items], ['PCR Kit', 'Buffer'])
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].unit, 'EA')
        self.assertEqual(int(items[0].unit_price), 100000)
        self.assertEqual(float(items[0].discount_rate), 10.0)
        self.assertEqual(int(items[0].discount_unit_price), 90000)
        self.assertEqual(int(items[0].get_effective_unit_price()), 90000)
        self.assertEqual(int(items[0].total_price), 198000)
        self.assertTrue(items[0].tax_invoice_issued)
        self.assertEqual(items[0].notes, 'PCR 적요')
        self.assertIsNone(items[1].unit_price)
        schedule.refresh_from_db()
        self.assertEqual(schedule.quote_extra_notes, '견적 전체 기타사항')
        history.refresh_from_db()
        self.assertIn('PCR Kit', history.delivery_items)
        self.assertIn('Buffer', history.delivery_items)
        self.assertEqual(int(history.delivery_amount), 198000)
        self.assertEqual(payload['deliveryItems'][0]['itemName'], 'PCR Kit')
        self.assertEqual(payload['deliveryItems'][0]['discountRate'], 10.0)
        self.assertEqual(payload['deliveryItems'][0]['discountUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['effectiveUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['totalPrice'], 198000)
        self.assertEqual(payload['deliveryItems'][0]['notes'], 'PCR 적요')

    def test_schedule_delivery_items_update_api_accepts_product_master_selection(self):
        import json
        from reporting.models import DeliveryItem, Product

        schedule = self._create_schedule(self.user, '제품선택납품', activity_type='delivery')
        product = Product.objects.create(
            product_code='MASTER-DELIVERY-PCR',
            unit='BOX',
            specification='100 tests',
            standard_price=12345,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'productId': product.id,
                        'itemName': '',
                        'quantity': 2,
                        'unit': '',
                        'unitPrice': '',
                        'taxInvoiceIssued': True,
                        'notes': '제품 마스터 선택',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        item = DeliveryItem.objects.get(schedule=schedule)
        self.assertEqual(item.product, product)
        self.assertEqual(item.item_name, product.product_code)
        self.assertEqual(item.unit, 'BOX')
        self.assertEqual(int(item.unit_price), 12345)
        self.assertEqual(int(item.total_price), 27159)
        payload_item = response.json()['deliveryItems'][0]
        self.assertEqual(payload_item['productId'], product.id)
        self.assertEqual(payload_item['productCode'], product.product_code)
        self.assertEqual(payload_item['productDescription'], '')
        self.assertEqual(payload_item['unit'], 'BOX')
        self.assertEqual(payload_item['unitPrice'], 12345)
        self.assertEqual(payload_item['totalPrice'], 27159)

    def test_schedule_delivery_items_update_api_saves_quote_groups(self):
        import json
        from reporting.models import DeliveryItem

        schedule = self._create_schedule(self.user, '견적구분저장', activity_type='quote')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'itemName': 'Trade In Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '100000',
                        'quoteGroup': '보상판매',
                        'taxInvoiceIssued': False,
                    },
                    {
                        'itemName': 'Repair Service',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                        'quoteGroup': '수리',
                        'taxInvoiceIssued': False,
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        items = list(DeliveryItem.objects.filter(schedule=schedule).order_by('id'))
        self.assertEqual([item.quote_group for item in items], ['보상판매', '수리'])
        payload_items = response.json()['deliveryItems']
        self.assertEqual([item['quoteGroup'] for item in payload_items], ['보상판매', '수리'])
        self.assertEqual([item['quoteGroupLabel'] for item in payload_items], ['보상판매', '수리'])

    def test_schedule_delivery_items_update_api_blocks_inaccessible_product(self):
        import json
        from reporting.models import DeliveryItem, Product

        schedule = self._create_schedule(self.user, '타사제품차단', activity_type='delivery')
        other_product = Product.objects.create(
            product_code='MASTER-OTHER-PRIVATE',
            unit='EA',
            standard_price=5000,
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'productId': other_product.id,
                        'itemName': '허용되지 않은 제품',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '5000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('선택한 제품을 찾을 수 없습니다', response.json()['error'])
        self.assertFalse(DeliveryItem.objects.filter(schedule=schedule).exists())

    def test_schedule_delivery_items_update_api_blocks_manager_and_coworker(self):
        import json
        from reporting.models import DeliveryItem

        schedule = self._create_schedule(self.user, '납품차단', activity_type='delivery')
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Protected Kit',
            quantity=1,
            unit='EA',
            unit_price=5000,
        )
        update_url = reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id])
        payload = {
            'items': [
                {
                    'itemName': 'Changed Kit',
                    'quantity': 2,
                    'unit': 'EA',
                    'unitPrice': '10000',
                },
            ],
        }

        self.client.force_login(self.manager)
        manager_response = self.client.post(update_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(update_url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(coworker_response.status_code, 403)

        self.assertEqual(DeliveryItem.objects.get(schedule=schedule).item_name, 'Protected Kit')

    def test_schedule_file_upload_api_allows_owner_only(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from reporting.models import ScheduleFile

        schedule = self._create_schedule(self.user, '파일업로드')
        upload_url = reverse('reporting:schedule_file_upload', args=[schedule.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('manager.txt', b'manager memo', content_type='text/plain'),
        })
        self.assertEqual(manager_response.status_code, 403)

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('coworker.txt', b'coworker memo', content_type='text/plain'),
        })
        self.assertEqual(coworker_response.status_code, 403)

        self.client.force_login(self.user)
        response = self.client.post(upload_url, {
            'files': SimpleUploadedFile('owner.txt', b'owner memo', content_type='text/plain'),
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        schedule_file = ScheduleFile.objects.get(schedule=schedule)
        self.addCleanup(schedule_file.file.delete, False)
        self.assertEqual(schedule_file.original_filename, 'owner.txt')
        self.assertEqual(payload['files'][0]['id'], schedule_file.id)
        self.assertEqual(payload['files'][0]['downloadHref'], reverse('reporting:schedule_file_download', args=[schedule_file.id]))
        self.assertEqual(payload['files'][0]['deleteHref'], reverse('reporting:schedule_file_delete', args=[schedule_file.id]))

    def test_schedule_file_delete_api_allows_owner_only(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from reporting.models import ScheduleFile

        schedule = self._create_schedule(self.user, '파일삭제')
        schedule_file = ScheduleFile.objects.create(
            schedule=schedule,
            file=SimpleUploadedFile('delete-me.txt', b'delete memo', content_type='text/plain'),
            original_filename='delete-me.txt',
            file_size=11,
            uploaded_by=self.user,
        )
        delete_url = reverse('reporting:schedule_file_delete', args=[schedule_file.id])

        self.client.force_login(self.manager)
        manager_response = self.client.post(delete_url)
        self.assertEqual(manager_response.status_code, 403)
        self.assertTrue(ScheduleFile.objects.filter(pk=schedule_file.id).exists())

        self.client.force_login(self.coworker)
        coworker_response = self.client.post(delete_url)
        self.assertEqual(coworker_response.status_code, 403)
        self.assertTrue(ScheduleFile.objects.filter(pk=schedule_file.id).exists())

        self.client.force_login(self.user)
        response = self.client.post(delete_url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertFalse(ScheduleFile.objects.filter(pk=schedule_file.id).exists())


class DocumentTemplatesReactApiTests(TestCase):
    """React 서류 템플릿 관리 API 회귀 테스트"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='서류API회사')
        self.other_company = UserCompany.objects.create(name='서류API타사회사')
        self.admin = make_user('doc-admin', role='admin', company=self.company)
        self.manager = make_user('doc-manager', role='manager', company=self.company)
        self.salesman = make_user('doc-sales', role='salesman', company=self.company)
        self.other_manager = make_user('doc-other-manager', role='manager', company=self.other_company)
        self.list_url = reverse('reporting:document_templates_api')
        self.create_url = reverse('reporting:document_template_api_create')

    def _uploaded_xlsx(self, name='template.xlsx'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(
            name,
            b'fake xlsx content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def _create_template(self, company, name, document_type='quotation', is_default=False, created_by=None):
        template = DocumentTemplate.objects.create(
            company=company,
            document_type=document_type,
            name=name,
            description=f'{name} 설명',
            file=self._uploaded_xlsx(f'{name}.xlsx'),
            file_type='xlsx',
            is_default=is_default,
            created_by=created_by or self.manager,
        )
        self.addCleanup(template.file.delete, False)
        return template

    def _create_schedule(self, owner, name='서류고객', activity_type='quote'):
        from reporting.models import Schedule

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            company=customer_company,
            department=department,
            manager=f'{name} 책임',
        )
        return Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type=activity_type,
        )

    def test_document_templates_api_requires_login(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_document_templates_api_lists_same_company_and_summary(self):
        default_template = self._create_template(self.company, '기본견적서', is_default=True)
        delivery_template = self._create_template(self.company, '납품서', document_type='delivery_note')
        self._create_template(self.other_company, '타사견적서', created_by=self.other_manager)
        self.client.force_login(self.salesman)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['source'], 'django')
        self.assertFalse(payload['create']['canCreate'])
        self.assertEqual({item['id'] for item in payload['templates']}, {default_template.id, delivery_template.id})
        self.assertNotIn('타사견적서', [item['name'] for item in payload['templates']])
        quotation_summary = next(item for item in payload['summary']['byType'] if item['type'] == 'quotation')
        self.assertEqual(quotation_summary['count'], 1)
        self.assertEqual(quotation_summary['defaultCount'], 1)
        variable_tokens = {
            variable['token']
            for group in payload['templateVariableGroups']
            for variable in group['variables']
        }
        self.assertIn('{{견적기타사항}}', variable_tokens)
        self.assertIn('{{견적구분}}', variable_tokens)
        self.assertIn('{{견적명}}', variable_tokens)
        self.assertIn('{{견적제목}}', variable_tokens)
        self.assertIn('{{품목1_적요}}', variable_tokens)
        self.assertIn('{{품목1_기준단가}}', variable_tokens)
        self.assertIn('{{품목1_할인율}}', variable_tokens)
        self.assertIn('{{품목1_할인단가}}', variable_tokens)
        self.assertEqual(payload['links']['djangoList'], reverse('reporting:document_template_list'))

    def test_document_templates_api_includes_recent_generation_logs_scoped_by_company(self):
        quote_schedule = self._create_schedule(self.manager, name='견적이력', activity_type='quote')
        delivery_schedule = self._create_schedule(self.manager, name='납품이력', activity_type='delivery')
        other_schedule = self._create_schedule(self.other_manager, name='타사이력', activity_type='quote')
        quote_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=quote_schedule,
            user=self.manager,
            transaction_number='Q-20260511-001',
            output_format='xlsx',
        )
        DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='delivery_note',
            schedule=delivery_schedule,
            user=self.manager,
            transaction_number='D-20260511-001',
            output_format='pdf',
        )
        DocumentGenerationLog.objects.create(
            company=self.other_company,
            document_type='quotation',
            schedule=other_schedule,
            user=self.other_manager,
            transaction_number='OTHER-001',
            output_format='xlsx',
        )
        self.client.force_login(self.salesman)

        response = self.client.get(self.list_url, {'type': 'quotation'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['summary']['generatedToday'], 1)
        self.assertEqual(payload['summary']['recentGenerationCount'], 1)
        self.assertEqual([item['id'] for item in payload['recentGenerations']], [quote_log.id])
        generation = payload['recentGenerations'][0]
        self.assertEqual(generation['transactionNumber'], 'Q-20260511-001')
        self.assertEqual(generation['documentTypeLabel'], '견적서')
        self.assertEqual(generation['outputFormatLabel'], 'Excel')
        self.assertEqual(generation['createdBy'], self.manager.get_full_name() or self.manager.username)
        self.assertEqual(generation['customerName'], '견적이력 담당자')
        self.assertEqual(generation['customerCompany'], '견적이력 회사')
        self.assertEqual(generation['departmentName'], '견적이력 연구실')
        self.assertEqual(generation['schedule']['href'], f'/schedules/{quote_schedule.id}/')
        self.assertEqual(generation['schedule']['djangoHref'], reverse('reporting:schedule_detail', args=[quote_schedule.id]))
        self.assertNotIn('OTHER-001', [item['transactionNumber'] for item in payload['recentGenerations']])

    def test_document_templates_api_filters_by_document_type(self):
        quotation = self._create_template(self.company, '견적서')
        self._create_template(self.company, '거래명세서', document_type='transaction_statement')
        self.client.force_login(self.manager)

        response = self.client.get(self.list_url, {'type': 'quotation'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item['id'] for item in payload['templates']], [quotation.id])
        self.assertTrue(payload['create']['canCreate'])

    def test_document_template_create_update_delete_api(self):
        old_default = self._create_template(self.company, '기존기본', is_default=True)
        self.client.force_login(self.manager)

        create_response = self.client.post(self.create_url, {
            'documentType': 'quotation',
            'name': '신규견적서',
            'description': 'React 업로드',
            'isDefault': 'true',
            'file': self._uploaded_xlsx('new-template.xlsx'),
        })

        self.assertEqual(create_response.status_code, 200)
        created_payload = create_response.json()
        self.assertTrue(created_payload['success'])
        created = DocumentTemplate.objects.get(pk=created_payload['template']['id'])
        self.addCleanup(created.file.delete, False)
        self.assertEqual(created.company, self.company)
        self.assertEqual(created.created_by, self.manager)
        self.assertTrue(created.is_default)
        old_default.refresh_from_db()
        self.assertFalse(old_default.is_default)

        update_response = self.client.post(
            reverse('reporting:document_template_api_update', args=[created.id]),
            {
                'documentType': 'transaction_statement',
                'name': '수정거래명세서',
                'description': '수정 설명',
                'isDefault': 'false',
            },
        )

        self.assertEqual(update_response.status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.document_type, 'transaction_statement')
        self.assertEqual(created.name, '수정거래명세서')
        self.assertFalse(created.is_default)

        delete_response = self.client.post(reverse('reporting:document_template_api_delete', args=[created.id]))

        self.assertEqual(delete_response.status_code, 200)
        created.refresh_from_db()
        self.assertFalse(created.is_active)

    def test_document_template_api_blocks_salesman_mutations(self):
        template = self._create_template(self.company, '수정불가')
        self.client.force_login(self.salesman)

        create_response = self.client.post(self.create_url, {
            'documentType': 'quotation',
            'name': '권한없음',
            'file': self._uploaded_xlsx('blocked.xlsx'),
        })
        update_response = self.client.post(
            reverse('reporting:document_template_api_update', args=[template.id]),
            {'documentType': 'quotation', 'name': '수정시도'},
        )
        delete_response = self.client.post(reverse('reporting:document_template_api_delete', args=[template.id]))

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

    def test_document_template_api_blocks_other_company(self):
        other_template = self._create_template(self.other_company, '타사서류', created_by=self.other_manager)
        self.client.force_login(self.manager)

        update_response = self.client.post(
            reverse('reporting:document_template_api_update', args=[other_template.id]),
            {'documentType': 'quotation', 'name': '타사수정'},
        )
        toggle_response = self.client.post(reverse('reporting:document_template_api_toggle_default', args=[other_template.id]))

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(toggle_response.status_code, 403)

    def test_document_template_toggle_default_api_uses_existing_single_default_rule(self):
        old_default = self._create_template(self.company, '기존기본', is_default=True)
        new_template = self._create_template(self.company, '새기본')
        self.client.force_login(self.salesman)

        response = self.client.post(reverse('reporting:document_template_api_toggle_default', args=[new_template.id]))

        self.assertEqual(response.status_code, 200)
        new_template.refresh_from_db()
        old_default.refresh_from_db()
        self.assertTrue(new_template.is_default)
        self.assertFalse(old_default.is_default)

    def test_document_template_data_includes_quote_discount_and_note_variables(self):
        from reporting.models import DeliveryItem

        self.manager.first_name = '재현'
        self.manager.last_name = '안'
        self.manager.save(update_fields=['first_name', 'last_name'])
        self._create_template(self.company, '견적기본', is_default=True)
        schedule = self._create_schedule(self.manager, name='견적변수', activity_type='quote')
        schedule.notes = '견적 메모'
        schedule.quote_extra_notes = '전체 견적 기타사항'
        schedule.save(update_fields=['notes', 'quote_extra_notes'])
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='PCR Kit',
            quantity=2,
            unit='EA',
            unit_price=100000,
            discount_rate=10,
            notes='품목 적요',
        )
        self.client.force_login(self.salesman)

        response = self.client.get(reverse('reporting:get_document_template_data', args=['quotation', schedule.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        variables = payload['variables']
        self.assertEqual(variables['실무자'], '안재현')
        self.assertEqual(variables['영업담당자'], '안재현')
        self.assertEqual(variables['담당영업'], '안재현')
        self.assertEqual(variables['메모'], '견적 메모')
        self.assertEqual(variables['기타사항'], '전체 견적 기타사항')
        self.assertEqual(variables['견적기타사항'], '전체 견적 기타사항')
        self.assertEqual(variables['품목1_적요'], '품목 적요')
        self.assertEqual(variables['품목1_비고'], '품목 적요')
        self.assertEqual(variables['품목1_기준단가'], '100,000')
        self.assertEqual(variables['품목1_할인율'], '10%')
        self.assertEqual(variables['품목1_할인단가'], '90,000')
        self.assertEqual(variables['품목1_단가'], '90,000')
        self.assertEqual(variables['공급가액'], '180,000')
        self.assertEqual(variables['부가세액'], '18,000')
        self.assertEqual(variables['총액'], '198,000')
        self.assertEqual(payload['items'][0]['unitPrice'], 90000)
        self.assertEqual(payload['items'][0]['baseUnitPrice'], 100000)
        self.assertEqual(payload['items'][0]['discountUnitPrice'], 90000)
        self.assertEqual(payload['items'][0]['discountRate'], 10.0)
        self.assertEqual(payload['items'][0]['notes'], '품목 적요')

    def test_document_template_data_normalizes_legacy_reversed_korean_salesperson_name(self):
        self.manager.first_name = '안'
        self.manager.last_name = '재현'
        self.manager.save(update_fields=['first_name', 'last_name'])
        self._create_template(self.company, '견적담당자', is_default=True)
        schedule = self._create_schedule(self.manager, name='담당자변수', activity_type='quote')
        self.client.force_login(self.salesman)

        response = self.client.get(reverse('reporting:get_document_template_data', args=['quotation', schedule.id]))

        self.assertEqual(response.status_code, 200)
        variables = response.json()['variables']
        self.assertEqual(variables['실무자'], '안재현')
        self.assertEqual(variables['영업담당자'], '안재현')
        self.assertEqual(variables['담당영업'], '안재현')

    def test_document_template_data_filters_quotation_items_by_quote_group(self):
        from reporting.models import DeliveryItem

        self._create_template(self.company, '견적구분기본', is_default=True)
        schedule = self._create_schedule(self.manager, name='견적구분변수', activity_type='quote')
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Trade In Kit',
            quantity=1,
            unit='EA',
            unit_price=100000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Repair Service',
            quantity=1,
            unit='EA',
            unit_price=50000,
            quote_group='수리',
        )
        self.client.force_login(self.salesman)

        response = self.client.get(
            reverse('reporting:get_document_template_data', args=['quotation', schedule.id]),
            {'quote_group': '수리'},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['quote_group'], '수리')
        self.assertEqual(payload['quote_group_label'], '수리')
        self.assertEqual(payload['variables']['견적구분'], '수리')
        self.assertEqual(payload['variables']['견적제목'], '수리 견적서')
        self.assertEqual(payload['item_count'], 1)
        self.assertEqual(payload['items'][0]['name'], 'Repair Service')
        self.assertEqual(payload['items'][0]['quoteGroup'], '수리')
        self.assertEqual(payload['variables']['품목1_이름'], 'Repair Service')
        self.assertNotIn('품목2_이름', payload['variables'])

    def test_document_pdf_layout_helper_sets_a4_fit_to_page(self):
        import os
        import tempfile
        import zipfile
        from openpyxl import Workbook
        from reporting.views import _ensure_xlsx_a4_print_layout

        workbook = Workbook()
        sheet = workbook.active
        sheet['A1'] = '견적서'
        sheet['J40'] = 'A4 자동 맞춤 테스트'
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name
        self.addCleanup(lambda: os.path.exists(temp_path) and os.unlink(temp_path))
        workbook.save(temp_path)

        changed = _ensure_xlsx_a4_print_layout(temp_path)

        self.assertTrue(changed)
        with zipfile.ZipFile(temp_path, 'r') as archive:
            sheet_xml = archive.read('xl/worksheets/sheet1.xml').decode('utf-8')
        self.assertIn('fitToPage="1"', sheet_xml)
        self.assertIn('paperSize="9"', sheet_xml)
        self.assertIn('fitToWidth="1"', sheet_xml)
        self.assertIn('fitToHeight="0"', sheet_xml)
        self.assertIn('left="0.25"', sheet_xml)


class AIWorkspaceSummaryApiTests(TestCase):
    """React AI workspace 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='AI워크스페이스회사')
        self.other_company = UserCompany.objects.create(name='AI워크스페이스타사회사')
        self.user = make_user('ai_workspace_me', role='salesman', can_use_ai=True, company=self.company)
        self.no_ai_user = make_user('ai_workspace_no_permission', role='salesman', can_use_ai=False, company=self.company)
        self.coworker = make_user('ai_workspace_coworker', role='salesman', can_use_ai=True, company=self.company)
        self.url = reverse('reporting:ai_workspace_summary_api')

    def _create_customer(self, owner, name):
        from reporting.models import Company, Department, FollowUp

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} 책임',
            company=customer_company,
            department=department,
            priority='urgent',
            customer_grade='A',
            ai_score=88,
        )
        return followup, department

    def _create_department_analysis(self, owner, department):
        from datetime import date
        from ai_chat.models import AIDepartmentAnalysis, PainPointCard

        summary = (
            '후속 연락이 지연되고 있어 견적 대응이 필요합니다. '
            '고객 답장, 견적 기록, 최근 미팅 내용을 함께 확인해야 하며 '
            '다음 연락에서는 구매 일정과 필요 서류를 구체적으로 물어봐야 합니다.'
        )
        analysis = AIDepartmentAnalysis.objects.create(
            user=owner,
            department=department,
            analysis_data={
                'department_summary': summary,
                'meeting_insights': [
                    {
                        'theme': '후속 견적',
                        'details': '견적 제출 이후 고객 확인이 늦어지고 있습니다.',
                        'frequency': '최근 3회',
                    },
                ],
                'next_actions': [{'action': '견적 후속 연락', 'priority': 'high'}],
            },
            quote_delivery_data={
                'summary': {'total_quotes': 2, 'total_deliveries': 1},
                'deliveries': [{
                    'date': '2026-04-30',
                    'customer': f'{department.name} 담당자',
                    'amount': 220000,
                    'items': [{
                        'product': 'qPCR Reagent',
                        'quantity': 4,
                        'unit_price': 55000,
                        'total_price': 220000,
                    }],
                    'source': '납품 일정',
                    'schedule_id': 202,
                    'notes': 'AI 워크스페이스 최근 납품',
                }],
            },
            meeting_count=3,
            quote_count=2,
            delivery_count=1,
            analysis_period_start=date(2026, 4, 1),
            analysis_period_end=date(2026, 5, 1),
        )
        PainPointCard.objects.create(
            analysis=analysis,
            category='delivery',
            hypothesis='납기 확인이 늦어지고 있습니다.',
            confidence='high',
            confidence_score=84,
            evidence=[],
            attribution='lab',
            verification_question='납기 기준일을 다시 확인할까요?',
            action_if_yes='납기 가능 일정을 제시합니다.',
            action_if_no='대체 제품을 제안합니다.',
        )
        return analysis

    def test_ai_workspace_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_ai_workspace_summary_api_returns_permission_state_without_ai_access(self):
        self.client.force_login(self.no_ai_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['permission']['canUseAi'])
        self.assertEqual(payload['departments'], [])
        self.assertEqual(payload['promptTargets'], [])
        self.assertIsNone(payload['featuredDepartment'])
        self.assertEqual(payload['metrics']['departmentsWithCustomers'], 0)

    def test_ai_workspace_summary_api_lists_own_ai_operational_data(self):
        followup, department = self._create_customer(self.user, 'PCR핵심')
        self._create_department_analysis(self.user, department)

        from ai_chat.models import AIFollowUpAnalysis
        AIFollowUpAnalysis.objects.create(
            followup=followup,
            user=self.user,
            analysis_data={'customer_summary': 'PCR 고객은 후속 견적 대응이 필요합니다.'},
            meeting_count=2,
        )
        self._create_customer(self.coworker, '동료고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['permission']['canUseAi'])
        self.assertEqual(payload['metrics']['departmentsWithCustomers'], 1)
        self.assertEqual(payload['metrics']['analyzedDepartments'], 1)
        self.assertEqual(payload['metrics']['unverifiedPainpoints'], 1)
        self.assertEqual(payload['departments'][0]['id'], department.id)
        self.assertEqual(payload['followupTargets'][0]['id'], followup.id)
        self.assertTrue(payload['promptTargets'])
        prompt_text = '\n'.join(item['prompt'] for item in payload['promptTargets'])
        self.assertIn('PCR핵심', prompt_text)
        self.assertIn('후속', prompt_text)
        self.assertIn('/ai/department/', payload['departments'][0]['href'])
        self.assertIn('week_start=', payload['links']['weeklyAiDraft'])
        self.assertEqual(payload['featuredDepartment']['departmentId'], department.id)
        self.assertTrue(payload['featuredDepartment']['hasAnalysis'])
        self.assertEqual(payload['featuredDepartment']['meetingCount'], 3)
        self.assertEqual(payload['featuredDepartment']['customerCount'], 1)
        self.assertIn('필요 서류를 구체적으로 물어봐야 합니다', payload['featuredDepartment']['summary'])
        self.assertEqual(payload['featuredDepartment']['meetingInsights'][0]['theme'], '후속 견적')
        self.assertEqual(payload['featuredDepartment']['quoteDelivery']['recentDeliveries'][0]['items'][0]['product'], 'qPCR Reagent')
        self.assertEqual(payload['featuredDepartment']['quoteDelivery']['recentDeliveries'][0]['items'][0]['quantity'], 4)
        self.assertEqual(payload['featuredDepartment']['painpoints'][0]['verificationStatusLabel'], '미검증')
        self.assertIn('/ai/card/', payload['featuredDepartment']['painpoints'][0]['verifyHref'])
        self.assertTrue(payload['recommendedGoals'])
        self.assertEqual(payload['recommendedGoals'][0]['customer'], 'PCR핵심 담당자')
        self.assertIn('PCR핵심 담당자', payload['recommendedGoals'][0]['title'])
        recommended_questions = [item['question'] for item in payload['featuredDepartment']['recommendedQuestions']]
        self.assertIn('납기 기준일을 다시 확인할까요?', recommended_questions)

    def test_ai_workspace_summary_api_uses_requested_department_for_featured_panel(self):
        _first_followup, first_department = self._create_customer(self.user, '선택부서')
        _second_followup, second_department = self._create_customer(self.user, '최신부서')
        self._create_department_analysis(self.user, first_department)
        self._create_department_analysis(self.user, second_department)
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': first_department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['featuredDepartment']['departmentId'], first_department.id)
        self.assertEqual(payload['featuredDepartment']['departmentName'], first_department.name)
        self.assertEqual(payload['selectedDepartmentId'], first_department.id)

    def test_ai_workspace_summary_api_ignores_inaccessible_requested_department(self):
        _own_followup, own_department = self._create_customer(self.user, '내부서')
        _coworker_followup, coworker_department = self._create_customer(self.coworker, '동료부서')
        self._create_department_analysis(self.user, own_department)
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': coworker_department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['featuredDepartment']['departmentId'], own_department.id)
        self.assertEqual(payload['selectedDepartmentId'], own_department.id)
        department_ids = {department['id'] for department in payload['departments']}
        self.assertNotIn(coworker_department.id, department_ids)

    def test_ai_workspace_prompts_include_recent_notes_and_sales_amounts(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from django.utils import timezone
        from reporting.models import History, OpportunityTracking, Quote, Schedule

        followup, _department = self._create_customer(self.user, '문맥고객')
        now = timezone.now()

        recent_1 = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='최근 상담 1: 의사결정 일정 확인',
        )
        recent_2 = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='quote',
            content='최근 상담 2: 추가 견적 요청',
        )
        recent_3 = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='최근 상담 3: 예산 범위 확인',
        )
        old_note = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='오래된 상담: 프롬프트 제외 대상',
        )
        History.objects.filter(pk=recent_1.pk).update(created_at=now)
        History.objects.filter(pk=recent_2.pk).update(created_at=now - timedelta(days=1))
        History.objects.filter(pk=recent_3.pk).update(created_at=now - timedelta(days=2))
        History.objects.filter(pk=old_note.pk).update(created_at=now - timedelta(days=10))

        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1000000'),
        )
        Quote.objects.create(
            quote_number='AI-Q-001',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=timezone.localdate() + timedelta(days=14),
            stage='sent',
            subtotal=Decimal('1000000'),
            probability=70,
        )
        OpportunityTracking.objects.create(
            followup=followup,
            title='문맥 수주',
            current_stage='won',
            expected_revenue=Decimal('2500000'),
            actual_revenue=Decimal('2300000'),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        prompt_text = '\n'.join(item['prompt'] for item in payload['promptTargets'])
        self.assertIn('최근 영업노트 1', prompt_text)
        self.assertIn('최근 상담 1', prompt_text)
        self.assertIn('최근 상담 2', prompt_text)
        self.assertIn('최근 상담 3', prompt_text)
        self.assertNotIn('오래된 상담', prompt_text)
        self.assertIn('열린 견적 1건 / 1,100,000원', prompt_text)
        self.assertIn('수주 금액 1건 / 2,300,000원', prompt_text)


class PipelineApiTests(TestCase):
    """React 파일럿용 파이프라인 읽기 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='파이프라인API회사')
        self.user = make_user('pipeline_api_me', role='salesman', company=self.company)
        self.coworker = make_user('pipeline_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('pipeline_api_manager', role='manager', company=self.company)
        self.url = reverse('reporting:pipeline_command_center_api')
        self.move_url = reverse('reporting:funnel_pipeline_move')

    def _create_pipeline_customer(self, owner, name, stage='quote'):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Company, Department, FollowUp, History, Quote, Schedule

        customer_company = Company.objects.create(name=f'{name} 회사', created_by=owner)
        department = Department.objects.create(
            company=customer_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            company=customer_company,
            department=department,
            pipeline_stage=stage,
            customer_grade='A',
        )
        schedule = Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
        )
        Quote.objects.create(
            quote_number=f'Q-{name}',
            schedule=schedule,
            followup=followup,
            user=owner,
            valid_until=timezone.localdate() + timedelta(days=30),
            subtotal=1000000,
            probability=65,
            stage='sent',
        )
        History.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            action_type='quote',
            content='견적 후속 필요',
            next_action='견적서 확인 전화',
            next_action_date=timezone.localdate() - timedelta(days=1),
        )
        return followup

    def _create_quote_for_followup(self, followup, owner, suffix, stage, subtotal, converted=False):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import Quote

        schedule = followup.schedules.first()
        return Quote.objects.create(
            quote_number=f'Q-{suffix}',
            schedule=schedule,
            followup=followup,
            user=owner,
            valid_until=timezone.localdate() + timedelta(days=30),
            subtotal=subtotal,
            probability=100 if stage in ('approved', 'converted') else 65,
            stage=stage,
            converted_to_delivery=converted,
        )

    def _create_delivery_item(self, schedule, item_name, unit_price, quantity=1):
        from reporting.models import DeliveryItem

        return DeliveryItem.objects.create(
            schedule=schedule,
            item_name=item_name,
            quantity=quantity,
            unit_price=unit_price,
        )

    def _create_history_item(self, history, item_name, unit_price, quantity=1):
        from reporting.models import DeliveryItem

        return DeliveryItem.objects.create(
            history=history,
            item_name=item_name,
            quantity=quantity,
            unit_price=unit_price,
        )

    def _create_delivery_schedule(self, followup, owner, name, unit_price, quantity=1):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Schedule

        schedule = Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() - timedelta(days=1),
            visit_time=time(11, 0),
            status='completed',
            activity_type='delivery',
        )
        self._create_delivery_item(schedule, name, unit_price, quantity)
        return schedule

    def test_pipeline_api_requires_login(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('login', response.get('Location', ''))

    def test_pipeline_api_returns_current_user_scope(self):
        own = self._create_pipeline_customer(self.user, '내고객')
        coworker = self._create_pipeline_customer(self.coworker, '동료고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['source'], 'django')
        deal_ids = {deal['id'] for deal in payload['deals']}
        self.assertIn(own.id, deal_ids)
        self.assertNotIn(coworker.id, deal_ids)

    def test_pipeline_api_includes_metrics_stages_and_tasks(self):
        own = self._create_pipeline_customer(self.user, '지표고객')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload['metrics']['totalPipelineValue'], 1000000)
        self.assertEqual(payload['metrics']['activeCount'], 1)
        self.assertEqual(payload['metrics']['overdueCount'], 1)
        self.assertTrue(any(stage['id'] == own.pipeline_stage for stage in payload['stages']))
        self.assertTrue(any(task['title'] == '견적 후속 지연 고객' for task in payload['priorityTasks']))
        deal = payload['deals'][0]
        self.assertEqual(deal['stageLabel'], '견적 제출')
        self.assertIn('recentActivities', deal)
        self.assertEqual(deal['latestQuote']['amount'], 1100000)
        self.assertEqual(deal['nextSchedule']['type'], '견적 제출')
        self.assertIn('csrftoken', response.cookies)

    def test_pipeline_api_includes_department_ai_summary(self):
        from datetime import date
        from ai_chat.models import AIDepartmentAnalysis, PainPointCard

        profile = self.user.userprofile
        profile.can_use_ai = True
        profile.save(update_fields=['can_use_ai'])
        followup = self._create_pipeline_customer(self.user, 'AI고객')
        long_summary = (
            '검수 메모를 반영해야 하는 부서입니다. '
            '예산 승인 지연 가능성과 납기 조건을 함께 확인해야 하며 '
            '다음 파이프라인 후속에서는 승인자, 필요 서류, 납품 가능일을 한 번에 정리해야 합니다.'
        )
        analysis = AIDepartmentAnalysis.objects.create(
            user=self.user,
            department=followup.department,
            analysis_data={
                'department_summary': long_summary,
                'missing_info': {
                    'questions': ['승인자와 필요 서류를 확인했나요?'],
                },
            },
            meeting_count=3,
            quote_count=2,
            delivery_count=1,
            analysis_period_start=date(2026, 4, 1),
            analysis_period_end=date(2026, 5, 1),
        )
        PainPointCard.objects.create(
            analysis=analysis,
            category='budget',
            hypothesis='예산 승인 지연 가능성',
            confidence='high',
            confidence_score=82,
            evidence=[],
            attribution='lab',
            verification_question='예산 승인자가 누구인가요?',
            action_if_yes='승인자에게 필요 서류를 보냅니다.',
            action_if_no='대체 지연 원인을 확인합니다.',
        )
        PainPointCard.objects.create(
            analysis=analysis,
            category='delivery',
            hypothesis='납기 리스크는 낮음',
            confidence='med',
            confidence_score=65,
            evidence=[],
            attribution='lab',
            verification_question='납기 조건이 확정됐나요?',
            action_if_yes='납품 일정을 잡습니다.',
            action_if_no='납기 조건을 재확인합니다.',
            verification_status='confirmed',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        deal = next(deal for deal in response.json()['deals'] if deal['id'] == followup.id)
        ai_department = deal['aiDepartment']
        self.assertEqual(ai_department['departmentId'], followup.department_id)
        self.assertEqual(ai_department['departmentName'], followup.department.name)
        self.assertTrue(ai_department['canUseAi'])
        self.assertTrue(ai_department['canAnalyze'])
        self.assertTrue(ai_department['hasAnalysis'])
        self.assertEqual(ai_department['summary'], long_summary)
        self.assertEqual(ai_department['meetingCount'], 3)
        self.assertEqual(ai_department['quoteCount'], 2)
        self.assertEqual(ai_department['deliveryCount'], 1)
        self.assertEqual(ai_department['painpointCount'], 2)
        self.assertEqual(ai_department['unverifiedPainpointCount'], 1)
        self.assertEqual(ai_department['href'], reverse('ai_chat:department_analysis', args=[followup.department_id]))
        self.assertEqual(ai_department['runHref'], reverse('ai_chat:run_analysis', args=[followup.department_id]))
        self.assertEqual(ai_department['periodStart'], '2026-04-01')
        self.assertEqual(ai_department['periodEnd'], '2026-05-01')
        self.assertEqual(ai_department['painpoints'][0]['hypothesis'], '예산 승인 지연 가능성')
        recommended_questions = [item['question'] for item in ai_department['recommendedQuestions']]
        self.assertIn('승인자와 필요 서류를 확인했나요?', recommended_questions)
        self.assertIn('예산 승인자가 누구인가요?', recommended_questions)

    def test_pipeline_api_uses_stage_relevant_quote_amount(self):
        quote_followup = self._create_pipeline_customer(self.user, '견적가격', stage='quote')
        self._create_delivery_item(quote_followup.schedules.first(), '견적품목', 2000000)
        self._create_quote_for_followup(
            quote_followup, self.user, 'quote-latest-rejected', 'rejected', 3000000
        )
        negotiation_followup = self._create_pipeline_customer(self.user, '협상가격', stage='negotiation')
        self._create_delivery_item(negotiation_followup.schedules.first(), '협상품목', 2000000)
        self._create_quote_for_followup(
            negotiation_followup, self.user, 'negotiation-active', 'negotiation', 2000000
        )
        self._create_quote_for_followup(
            negotiation_followup, self.user, 'negotiation-latest-expired', 'expired', 5000000
        )
        won_followup = self._create_pipeline_customer(self.user, '수주가격', stage='won')
        self._create_delivery_schedule(won_followup, self.user, '납품품목', 4000000)
        self._create_quote_for_followup(
            won_followup, self.user, 'won-approved', 'approved', 4000000
        )
        self._create_quote_for_followup(
            won_followup, self.user, 'won-latest-draft', 'draft', 9000000
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        deals = {deal['id']: deal for deal in payload['deals']}
        self.assertEqual(deals[quote_followup.id]['value'], 2200000)
        self.assertEqual(deals[quote_followup.id]['latestQuote']['source'], '견적 일정')
        self.assertEqual(deals[quote_followup.id]['latestQuote']['basisType'], 'schedule')
        self.assertEqual(deals[negotiation_followup.id]['value'], 2200000)
        self.assertEqual(deals[negotiation_followup.id]['latestQuote']['source'], '견적 일정')
        self.assertEqual(deals[won_followup.id]['value'], 4400000)
        self.assertEqual(deals[won_followup.id]['latestQuote']['source'], '실제 납품 매출')
        self.assertEqual(deals[won_followup.id]['latestQuote']['basisType'], 'delivery')
        self.assertEqual(deals[won_followup.id]['quoteComparison']['quotedAmount'], 4400000)
        self.assertEqual(deals[won_followup.id]['quoteComparison']['actualAmount'], 4400000)
        self.assertEqual(deals[won_followup.id]['quoteComparison']['deltaAmount'], 0)
        self.assertEqual(deals[won_followup.id]['quoteComparison']['status'], 'match')
        stages = {stage['id']: stage for stage in payload['stages']}
        self.assertEqual(stages['won']['totalValue'], 4400000)

    def test_pipeline_api_sums_multiple_quote_schedules(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Schedule

        followup = self._create_pipeline_customer(self.user, '복수견적', stage='quote')
        self._create_delivery_item(followup.schedules.first(), '첫 견적품목', 1000000)
        second_schedule = Schedule.objects.create(
            user=self.user,
            company=self.user.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=2),
            visit_time=time(14, 0),
            status='scheduled',
            activity_type='quote',
        )
        self._create_delivery_item(second_schedule, '두번째 견적품목', 2000000)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        deal = next(deal for deal in response.json()['deals'] if deal['id'] == followup.id)
        self.assertEqual(deal['value'], 3300000)
        self.assertEqual(deal['latestQuote']['source'], '견적 일정 2건')
        self.assertIn('외 1건', deal['latestQuote']['number'])

    def test_pipeline_api_uses_quote_history_items_before_quote_model_fallback(self):
        followup = self._create_pipeline_customer(self.user, '견적히스토리', stage='quote')
        quote_history = followup.histories.filter(action_type='quote').first()
        self._create_history_item(quote_history, '히스토리견적품목', 3000000)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        deal = next(deal for deal in response.json()['deals'] if deal['id'] == followup.id)
        self.assertEqual(deal['value'], 3300000)
        self.assertEqual(deal['latestQuote']['source'], '견적 활동')
        self.assertEqual(deal['latestQuote']['basisType'], 'history')

    def test_pipeline_api_uses_delivery_history_items_for_won_revenue(self):
        from django.utils import timezone
        from reporting.models import History

        followup = self._create_pipeline_customer(self.user, '수주히스토리', stage='won')
        delivery_history = History.objects.create(
            user=self.user,
            company=self.user.userprofile.company,
            followup=followup,
            action_type='delivery_schedule',
            content='실제 납품 완료',
            delivery_date=timezone.localdate(),
        )
        self._create_history_item(delivery_history, '히스토리납품품목', 5000000)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        deal = next(deal for deal in response.json()['deals'] if deal['id'] == followup.id)
        self.assertEqual(deal['value'], 5500000)
        self.assertEqual(deal['latestQuote']['source'], '실제 납품 매출')
        self.assertEqual(deal['latestQuote']['basisType'], 'delivery')
        self.assertEqual(deal['quoteComparison']['quotedAmount'], 1100000)
        self.assertEqual(deal['quoteComparison']['actualAmount'], 5500000)
        self.assertEqual(deal['quoteComparison']['deltaAmount'], 4400000)
        self.assertEqual(deal['quoteComparison']['deltaRate'], 400.0)
        self.assertEqual(deal['quoteComparison']['status'], 'over')

    def test_pipeline_api_marks_potential_overflow_after_top_ten(self):
        for index in range(12):
            self._create_pipeline_customer(self.user, f'잠재{index}', stage='potential')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        potential_deals = [deal for deal in response.json()['deals'] if deal['stage'] == 'potential']
        self.assertEqual(len(potential_deals), 12)
        self.assertEqual(sum(1 for deal in potential_deals if deal['isPotentialOverflow']), 2)
        self.assertTrue(all('attentionScore' in deal for deal in potential_deals))
        self.assertTrue(all('attentionReason' in deal for deal in potential_deals))

    def test_pipeline_move_updates_accessible_followup_stage(self):
        followup = self._create_pipeline_customer(self.user, '이동고객', stage='potential')
        self.client.force_login(self.user)

        response = self.client.post(
            self.move_url,
            data=json.dumps({'followup_id': followup.id, 'stage': 'quote'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        followup.refresh_from_db()
        self.assertEqual(followup.pipeline_stage, 'quote')
        self.assertTrue(followup.pipeline_manually_set)

    def test_pipeline_move_rejects_invalid_stage(self):
        followup = self._create_pipeline_customer(self.user, '잘못된단계', stage='potential')
        self.client.force_login(self.user)

        response = self.client.post(
            self.move_url,
            data=json.dumps({'followup_id': followup.id, 'stage': 'invalid'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        followup.refresh_from_db()
        self.assertEqual(followup.pipeline_stage, 'potential')

    def test_pipeline_move_rejects_manager(self):
        followup = self._create_pipeline_customer(self.user, '매니저차단', stage='potential')
        self.client.force_login(self.manager)

        response = self.client.post(
            self.move_url,
            data=json.dumps({'followup_id': followup.id, 'stage': 'quote'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])
        followup.refresh_from_db()
        self.assertEqual(followup.pipeline_stage, 'potential')


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: 권한 격리 테스트 (can_access_user_data)
# ─────────────────────────────────────────────────────────────────────────────

class PermissionIsolationTests(TestCase):
    """역할 기반 데이터 격리 검증"""

    def test_can_access_user_data_same_company(self):
        """같은 회사 사용자끼리 접근 가능"""
        from reporting.views import can_access_user_data
        company = UserCompany.objects.create(name='같은회사')
        u1 = make_user('user_a', company=company)
        u2 = make_user('user_b', company=company)
        self.assertTrue(can_access_user_data(u1, u2))

    def test_can_access_user_data_different_company(self):
        """다른 회사 사용자 접근 차단"""
        from reporting.views import can_access_user_data
        c1 = UserCompany.objects.create(name='회사A')
        c2 = UserCompany.objects.create(name='회사B')
        u1 = make_user('user_c', company=c1)
        u2 = make_user('user_d', company=c2)
        self.assertFalse(can_access_user_data(u1, u2))

    def test_can_access_user_data_no_company(self):
        """company=None 사용자 간 상호 접근 차단 (None == None 버그 없음)"""
        from reporting.views import can_access_user_data
        u1 = make_user('user_e')  # company=None
        u2 = make_user('user_f')  # company=None
        # 서로 다른 사용자이고 company가 None → 접근 불가
        self.assertFalse(can_access_user_data(u1, u2))

    def test_can_access_user_data_self(self):
        """자기 자신의 데이터 항상 접근 가능"""
        from reporting.views import can_access_user_data
        u = make_user('user_g')
        self.assertTrue(can_access_user_data(u, u))

    def test_admin_can_access_all(self):
        """admin은 모든 회사 사용자 데이터 접근 가능"""
        from reporting.views import can_access_user_data
        c1 = UserCompany.objects.create(name='회사C')
        c2 = UserCompany.objects.create(name='회사D')
        admin_user = make_user('admin_x', role='admin', company=c1)
        other_user = make_user('other_x', role='salesman', company=c2)
        self.assertTrue(can_access_user_data(admin_user, other_user))

    def test_can_modify_user_data_manager_blocked(self):
        """manager는 타인 데이터 수정 불가"""
        from reporting.views import can_modify_user_data
        company = UserCompany.objects.create(name='수정테스트회사')
        mgr = make_user('mgr_x', role='manager', company=company)
        sales = make_user('sales_x', role='salesman', company=company)
        self.assertFalse(can_modify_user_data(mgr, sales))

    def test_can_modify_user_data_salesman_own(self):
        """salesman은 자기 자신 데이터 수정 가능"""
        from reporting.views import can_modify_user_data
        u = make_user('sales_own')
        self.assertTrue(can_modify_user_data(u, u))

    def test_can_modify_user_data_salesman_other_blocked(self):
        """salesman은 타인 데이터 수정 불가"""
        from reporting.views import can_modify_user_data
        company = UserCompany.objects.create(name='수정테스트회사2')
        u1 = make_user('sales_p', role='salesman', company=company)
        u2 = make_user('sales_q', role='salesman', company=company)
        self.assertFalse(can_modify_user_data(u1, u2))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: 주간보고 API 테스트
# ─────────────────────────────────────────────────────────────────────────────

class WeeklyReportTests(TestCase):
    """주간보고 API 기본 동작 및 권한 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='주간보고회사')
        self.salesman = make_user('wr_salesman', role='salesman', company=self.company)
        self.manager = make_user('wr_manager', role='manager', company=self.company)

    def test_load_schedules_authenticated(self):
        """주간보고 일정 로드 API: 인증 후 200"""
        self.client.force_login(self.salesman)
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'}
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('schedules', data)

    def test_load_schedules_unauthenticated(self):
        """주간보고 일정 로드 API: 미인증 → 리다이렉트"""
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'}
        )
        self.assertIn(r.status_code, [301, 302])

    def test_load_schedules_bad_dates(self):
        """주간보고 일정 로드 API: 잘못된 날짜 → 400"""
        self.client.force_login(self.salesman)
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': 'invalid', 'week_end': 'invalid'}
        )
        self.assertEqual(r.status_code, 400)

    def test_weekly_report_list_accessible(self):
        """주간보고 목록: 인증 후 200"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:weekly_report_list'))
        self.assertEqual(r.status_code, 200)

    def test_weekly_report_create_page_renders_schedule_loader(self):
        """주간보고 작성 화면은 일정 자동 로드 스크립트를 렌더링"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:weekly_report_create'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'loadSchedules();')
        self.assertContains(r, 'normalizeEditorHtmlInput')

    def test_weekly_report_create_normalizes_double_escaped_html(self):
        """Quill HTML이 이중 escape되어 들어와도 정상 HTML로 저장/렌더링"""
        import datetime
        from reporting.models import WeeklyReport

        self.client.force_login(self.salesman)
        activity = (
            '<p>&lt;p&gt;04/28(화): 홍철화 (연세대학교 의과대학 · 김민환 교수님 연구실)&lt;/p&gt;'
            '&lt;p&gt;&amp;gt; 수리 피펫 가져다드리고 데모피펫 회수&lt;/p&gt;</p>'
        )
        quote_delivery = (
            '<p>&lt;p&gt;- 04/28(화): 홍철화 - 피펫 견적 제출&lt;/p&gt;'
            '&lt;p&gt;- 04/29(수): 이진영 - 피펫에이드 보상판매&lt;/p&gt;</p>'
        )
        other = '<p>&lt;p&gt;국민대학교 방문&lt;/p&gt;</p>'

        r = self.client.post(reverse('reporting:weekly_report_create'), {
            'week_start': '2026-04-20',
            'week_end': '2026-04-24',
            'title': 'HTML 정규화 테스트',
            'activity_notes': activity,
            'quote_delivery_notes': quote_delivery,
            'other_notes': other,
        })
        self.assertEqual(r.status_code, 302)

        report = WeeklyReport.objects.get(
            user=self.salesman,
            week_start=datetime.date(2026, 4, 20),
        )
        self.assertIn('<p>04/28(화): 홍철화', report.activity_notes)
        self.assertNotIn('&lt;p&gt;', report.activity_notes)
        self.assertNotIn('&amp;lt;p&amp;gt;', report.activity_notes)
        self.assertIn('<p>국민대학교 방문</p>', report.other_notes)

        detail = self.client.get(reverse('reporting:weekly_report_detail', args=[report.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, '수리 피펫 가져다드리고 데모피펫 회수')
        self.assertContains(detail, '국민대학교 방문')
        self.assertNotContains(detail, '&lt;p&gt;04/28')


class WeeklyReportReactApiTests(TestCase):
    """React 주간보고 API 권한/저장 동작 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='React주간보고회사')
        self.other_company = UserCompany.objects.create(name='다른주간보고회사')
        self.salesman = make_user('react_wr_salesman', role='salesman', company=self.company, can_use_ai=True)
        self.colleague = make_user('react_wr_colleague', role='salesman', company=self.company)
        self.manager = make_user('react_wr_manager', role='manager', company=self.company)
        self.other_salesman = make_user('react_wr_other', role='salesman', company=self.other_company)

    def test_weekly_reports_api_requires_login(self):
        r = self.client.get(reverse('reporting:weekly_reports_api'))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['error'], 'login_required')

    def test_salesman_list_api_returns_own_reports_only(self):
        import datetime
        from reporting.models import WeeklyReport

        own = WeeklyReport.objects.create(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='내 주간보고',
        )
        WeeklyReport.objects.create(
            user=self.colleague,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='동료 주간보고',
        )

        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:weekly_reports_api'), {'year': '2026', 'month': '5'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['source'], 'django')
        self.assertEqual([item['id'] for item in data['reports']], [own.id])
        self.assertEqual(data['links']['create'], '/weekly-reports/new/')

    def test_manager_list_api_is_limited_to_same_company(self):
        import datetime
        from reporting.models import WeeklyReport

        same_company = WeeklyReport.objects.create(
            user=self.colleague,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='같은 회사 보고',
        )
        WeeklyReport.objects.create(
            user=self.other_salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='다른 회사 보고',
        )

        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:weekly_reports_api'), {'year': '2026', 'month': '5'})
        self.assertEqual(r.status_code, 200)
        report_ids = [item['id'] for item in r.json()['reports']]
        self.assertIn(same_company.id, report_ids)
        self.assertEqual(len(report_ids), 1)

    def test_create_api_saves_plain_text_as_readable_html(self):
        import datetime
        from reporting.models import WeeklyReport

        self.client.force_login(self.salesman)
        r = self.client.post(
            reverse('reporting:weekly_report_create_api'),
            data=json.dumps({
                'weekStart': '2026-05-04',
                'weekEnd': '2026-05-08',
                'title': 'React 저장 테스트',
                'activityNotes': '첫 줄\n둘째 줄\n\n다음 문단',
                'quoteDeliveryNotes': '- 견적 A\n- 납품 B',
                'otherNotes': '기타 메모',
            }),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        report = WeeklyReport.objects.get(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
        )
        self.assertIn('<p>첫 줄<br>둘째 줄</p>', report.activity_notes)
        self.assertIn('<p>다음 문단</p>', report.activity_notes)
        response_report = r.json()['report']
        self.assertIn('첫 줄', response_report['activityNotesHtml'])
        self.assertIn('둘째 줄', response_report['activityNotesHtml'])
        self.assertIn('다음 문단', response_report['activityNotesHtml'])
        self.assertIn('<br>', response_report['activityNotesHtml'])
        self.assertEqual(response_report['href'], f'/weekly-reports/{report.id}/')

    def test_detail_api_returns_html_and_editor_text(self):
        import datetime
        from reporting.models import WeeklyReport

        report = WeeklyReport.objects.create(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='상세 테스트',
            activity_notes='<p>첫 줄<br>둘째 줄</p>',
        )

        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:weekly_report_detail_api', args=[report.id]))
        self.assertEqual(r.status_code, 200)
        data = r.json()['report']
        self.assertIn('첫 줄', data['activityNotesHtml'])
        self.assertIn('<br>', data['activityNotesHtml'])
        self.assertEqual(data['activityNotes'], '첫 줄\n둘째 줄')
        self.assertTrue(data['canComment'])
        self.assertFalse(data['canEdit'])

    def test_detail_api_preserves_paragraph_breaks_for_edit_text(self):
        import datetime
        from reporting.models import WeeklyReport

        report = WeeklyReport.objects.create(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='문단 줄바꿈 테스트',
            activity_notes='<p>첫 문단<br>둘째 줄</p><p>다음 문단</p>',
            quote_delivery_notes='<p>제품 A 납품</p><p>제품 B 납품</p>',
        )

        self.client.force_login(self.salesman)
        response = self.client.get(reverse('reporting:weekly_report_detail_api', args=[report.id]))

        self.assertEqual(response.status_code, 200)
        data = response.json()['report']
        self.assertEqual(data['activityNotes'], '첫 문단\n둘째 줄\n\n다음 문단')
        self.assertEqual(data['quoteDeliveryNotes'], '제품 A 납품\n\n제품 B 납품')

    def test_update_and_delete_api_owner_only(self):
        import datetime
        from reporting.models import WeeklyReport

        report = WeeklyReport.objects.create(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='삭제 테스트',
        )

        self.client.force_login(self.manager)
        forbidden_update = self.client.post(
            reverse('reporting:weekly_report_update_api', args=[report.id]),
            data=json.dumps({'title': '권한 없음'}),
            content_type='application/json',
        )
        self.assertEqual(forbidden_update.status_code, 403)

        self.client.force_login(self.salesman)
        update = self.client.post(
            reverse('reporting:weekly_report_update_api', args=[report.id]),
            data=json.dumps({
                'weekStart': '2026-05-04',
                'weekEnd': '2026-05-08',
                'title': '수정 완료',
                'activityNotes': '수정된 내용',
            }),
            content_type='application/json',
        )
        self.assertEqual(update.status_code, 200)
        report.refresh_from_db()
        self.assertEqual(report.title, '수정 완료')

        delete = self.client.post(reverse('reporting:weekly_report_delete_api', args=[report.id]))
        self.assertEqual(delete.status_code, 200)
        self.assertFalse(WeeklyReport.objects.filter(pk=report.id).exists())


# ─────────────────────────────────────────────────────────────────────────────
# Manager 역할 권한 검증 테스트
# ─────────────────────────────────────────────────────────────────────────────

class ManagerRolePermissionTests(TestCase):
    """Manager(뷰어)는 영업노트/일정/고객 데이터를 생성·수정할 수 없음을 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='테스트회사')
        self.manager = make_user('mgr_test', role='manager', company=self.company)
        self.salesman = make_user('slm_test', role='salesman', company=self.company)

    # ── 히스토리 생성 차단 (일정 기반) ────────────────────────────────────

    def test_manager_cannot_access_history_create_from_schedule(self):
        """Manager: 일정 기반 히스토리 생성 → 리다이렉트/403 차단"""
        from reporting.models import Company, Department, FollowUp, Schedule
        import datetime
        # 최소 필요 객체 생성
        company = Company.objects.create(name='테스트업체', created_by=self.salesman)
        dept = Department.objects.create(name='테스트부서', company=company, created_by=self.salesman)
        followup = FollowUp.objects.create(
            user=self.salesman, customer_name='테스트고객',
            company=company, department=dept
        )
        schedule = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=datetime.date.today(),
            visit_time=datetime.time(9, 0),
            activity_type='customer_meeting'
        )
        self.client.force_login(self.manager)
        url = reverse('reporting:history_create_from_schedule', args=[schedule.pk])
        r = self.client.get(url)
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager GET history_create_from_schedule: expected redirect/403, got {r.status_code}")

    def test_manager_cannot_post_history_create_from_schedule(self):
        """Manager: 일정 기반 히스토리 생성 POST → 리다이렉트/403 차단"""
        from reporting.models import Company, Department, FollowUp, Schedule
        import datetime
        company = Company.objects.create(name='테스트업체2', created_by=self.salesman)
        dept = Department.objects.create(name='테스트부서2', company=company, created_by=self.salesman)
        followup = FollowUp.objects.create(
            user=self.salesman, customer_name='테스트고객2',
            company=company, department=dept
        )
        schedule = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=datetime.date.today(),
            visit_time=datetime.time(9, 0),
            activity_type='customer_meeting'
        )
        self.client.force_login(self.manager)
        url = reverse('reporting:history_create_from_schedule', args=[schedule.pk])
        r = self.client.post(url, {'action_type': 'customer_meeting'})
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager POST history_create_from_schedule: expected redirect/403, got {r.status_code}")

    # ── 일정 생성 차단 ──────────────────────────────────────────────────────

    def test_manager_cannot_get_schedule_create(self):
        """Manager: 일정 생성 폼 GET → 리다이렉트(차단)"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:schedule_create'))
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager GET schedule_create: expected redirect/403, got {r.status_code}")

    def test_manager_cannot_post_schedule_create(self):
        """Manager: 일정 생성 POST → 리다이렉트(차단)"""
        self.client.force_login(self.manager)
        r = self.client.post(reverse('reporting:schedule_create'), {
            'visit_date': '2026-05-01',
            'activity_type': 'customer_meeting',
        })
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager POST schedule_create: expected redirect/403, got {r.status_code}")

    # ── 고객(팔로우업) 생성 차단 ────────────────────────────────────────────

    def test_manager_cannot_get_followup_create(self):
        """Manager: 고객 생성 폼 GET → 리다이렉트(차단)"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:followup_create'))
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager GET followup_create: expected redirect/403, got {r.status_code}")

    def test_manager_cannot_post_followup_create(self):
        """Manager: 고객 생성 POST → 리다이렉트(차단)"""
        self.client.force_login(self.manager)
        r = self.client.post(reverse('reporting:followup_create'), {
            'customer_name': '홍길동',
        })
        self.assertIn(r.status_code, [302, 403],
                      msg=f"Manager POST followup_create: expected redirect/403, got {r.status_code}")

    # ── Salesman은 정상 접근 가능 (form 렌더링) ─────────────────────────────

    def test_salesman_can_get_schedule_create(self):
        """Salesman: 일정 생성 폼 GET → 200"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:schedule_create'))
        self.assertEqual(r.status_code, 200,
                         msg=f"Salesman GET schedule_create: expected 200, got {r.status_code}")

    def test_salesman_can_get_followup_create(self):
        """Salesman: 고객 생성 폼 GET → 200"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:followup_create'))
        self.assertEqual(r.status_code, 200,
                         msg=f"Salesman GET followup_create: expected 200, got {r.status_code}")

    # ── 조회는 허용 ─────────────────────────────────────────────────────────

    def test_manager_can_view_history_list(self):
        """Manager: 히스토리 목록 조회 → 200"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:history_list'))
        self.assertEqual(r.status_code, 200,
                         msg=f"Manager GET history_list: expected 200, got {r.status_code}")

    def test_manager_can_view_schedule_list(self):
        """Manager: 일정 목록 조회 → 200"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:schedule_list'))
        self.assertEqual(r.status_code, 200,
                         msg=f"Manager GET schedule_list: expected 200, got {r.status_code}")

    def test_manager_can_view_followup_list(self):
        """Manager: 고객 목록 조회 → 200"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:followup_list'))
        self.assertEqual(r.status_code, 200,
                         msg=f"Manager GET followup_list: expected 200, got {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: 디버그 엔드포인트 제거 확인 테스트
# ─────────────────────────────────────────────────────────────────────────────

class DebugEndpointTests(TestCase):
    """Phase 8: debug/user-company/ 엔드포인트가 제거되었는지 확인"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='디버그테스트회사')
        self.superuser = User.objects.create_superuser(
            username='superuser_debug', password='TestPass123!'
        )
        self.regular_user = make_user('regular_debug', role='salesman', company=self.company)

    def test_debug_endpoint_does_not_exist(self):
        """debug/user-company/ URL이 URL 설정에 존재하지 않음"""
        from django.urls import NoReverseMatch
        with self.assertRaises(NoReverseMatch):
            reverse('reporting:debug_user_company_info')

    def test_debug_url_returns_404(self):
        """debug/user-company/ 직접 접근 시 404 반환"""
        self.client.force_login(self.superuser)
        r = self.client.get('/reporting/debug/user-company/')
        self.assertEqual(r.status_code, 404,
                         msg=f"debug URL should be 404, got {r.status_code}")

    def test_debug_url_anonymous_returns_404(self):
        """미인증 사용자 debug URL 접근 시 404 반환"""
        r = self.client.get('/reporting/debug/user-company/')
        self.assertEqual(r.status_code, 404,
                         msg=f"anonymous debug URL should be 404, got {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: 파일 업로드 MIME 검증 테스트
# ─────────────────────────────────────────────────────────────────────────────

class FileUploadValidationTests(TestCase):
    """Phase 8: 파일 업로드 MIME 검증 및 확장자 화이트리스트 테스트"""

    def _make_file(self, name, content):
        """테스트용 가짜 InMemoryUploadedFile 생성"""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(name, content)

    def test_valid_pdf_accepted(self):
        """올바른 PDF 파일 (매직 바이트 + 확장자 일치) 허용"""
        from reporting.views import validate_file_upload
        f = self._make_file('test.pdf', b'%PDF-1.4 valid pdf content')
        ok, msg = validate_file_upload(f)
        self.assertTrue(ok, msg=f"Valid PDF should be accepted: {msg}")

    def test_valid_jpeg_accepted(self):
        """올바른 JPEG 파일 허용"""
        from reporting.views import validate_file_upload
        f = self._make_file('photo.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertTrue(ok, msg=f"Valid JPEG should be accepted: {msg}")

    def test_valid_png_accepted(self):
        """올바른 PNG 파일 허용"""
        from reporting.views import validate_file_upload
        f = self._make_file('image.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertTrue(ok, msg=f"Valid PNG should be accepted: {msg}")

    def test_invalid_extension_rejected(self):
        """허용되지 않은 확장자 차단"""
        from reporting.views import validate_file_upload
        f = self._make_file('malware.exe', b'MZ\x90\x00' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertFalse(ok, msg="EXE file should be rejected")

    def test_disguised_exe_as_pdf_rejected(self):
        """EXE 파일을 PDF로 위장한 경우 차단 (MIME 스푸핑 방지)"""
        from reporting.views import validate_file_upload
        # .pdf 확장자지만 실제로는 EXE 매직 바이트 MZ
        f = self._make_file('fake.pdf', b'MZ\x90\x00' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertFalse(ok, msg=f"EXE disguised as PDF should be rejected: {msg}")

    def test_disguised_exe_as_jpg_rejected(self):
        """EXE 파일을 JPG로 위장한 경우 차단"""
        from reporting.views import validate_file_upload
        f = self._make_file('photo.jpg', b'MZ\x90\x00' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertFalse(ok, msg=f"EXE disguised as JPG should be rejected: {msg}")

    def test_oversized_file_rejected(self):
        """10MB 초과 파일 차단"""
        from reporting.views import validate_file_upload
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile
        content = b'%PDF' + b'\x00' * (10 * 1024 * 1024 + 1)
        buf = io.BytesIO(content)
        f = InMemoryUploadedFile(buf, 'file', 'big.pdf', 'application/pdf', len(content), None)
        ok, msg = validate_file_upload(f)
        self.assertFalse(ok, msg="Oversized file should be rejected")

    def test_valid_docx_accepted(self):
        """올바른 DOCX 파일 (ZIP 기반) 허용"""
        from reporting.views import validate_file_upload
        # DOCX는 ZIP 포맷 (PK\x03\x04 시그니처)
        f = self._make_file('report.docx', b'PK\x03\x04' + b'\x00' * 100)
        ok, msg = validate_file_upload(f)
        self.assertTrue(ok, msg=f"Valid DOCX should be accepted: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9: 프로덕션 설정 보안 검증 테스트
# ─────────────────────────────────────────────────────────────────────────────

class ProductionSettingsTests(TestCase):
    """Phase 9: settings_production.py 보안 설정 유효성 검증"""

    def test_allowed_hosts_no_invalid_wildcards(self):
        """ALLOWED_HOSTS에 Django 미지원 와일드카드(*.xxx)가 없음을 확인"""
        from django.conf import settings as django_settings
        for host in django_settings.ALLOWED_HOSTS:
            self.assertFalse(
                host.startswith('*.'),
                f"ALLOWED_HOSTS에 미지원 와일드카드 발견: {host}"
            )

    def test_email_encryption_key_is_bytes_or_none(self):
        """EMAIL_ENCRYPTION_KEY가 bytes 또는 None인지 확인 (문자열 금지)"""
        from django.conf import settings as django_settings
        key = getattr(django_settings, 'EMAIL_ENCRYPTION_KEY', 'NOT_SET')
        if key != 'NOT_SET' and key is not None:
            self.assertIsInstance(
                key, bytes,
                f"EMAIL_ENCRYPTION_KEY는 bytes여야 합니다. 현재 타입: {type(key)}"
            )

    def test_email_encryption_key_not_hardcoded_default(self):
        """EMAIL_ENCRYPTION_KEY가 알려진 하드코딩 기본값이 아님을 확인"""
        from django.conf import settings as django_settings
        key = getattr(django_settings, 'EMAIL_ENCRYPTION_KEY', None)
        # 이전에 사용된 안전하지 않은 공개 기본값
        UNSAFE_FALLBACK = b'YXNkZmFzZGZhc2RmYXNkZmFzZGZhc2RmYXNkZmFzZGY='
        if key is not None:
            self.assertNotEqual(
                key, UNSAFE_FALLBACK,
                "EMAIL_ENCRYPTION_KEY가 알려진 안전하지 않은 기본값으로 설정되어 있습니다."
            )

    def test_hsts_seconds_env_non_negative(self):
        """HSTS_SECONDS 환경변수가 있으면 0 이상인지 확인"""
        import os
        val_str = os.environ.get('HSTS_SECONDS', '0')
        val = int(val_str)
        self.assertGreaterEqual(val, 0, "HSTS_SECONDS는 0 이상이어야 합니다")

    def test_secure_content_type_nosniff(self):
        """프로덕션 환경(not DEBUG)에서 MIME 스니핑 방지 헤더가 활성화됨"""
        from django.conf import settings as django_settings
        if not django_settings.DEBUG:
            self.assertTrue(
                getattr(django_settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
                "프로덕션에서 SECURE_CONTENT_TYPE_NOSNIFF가 활성화되어야 합니다"
            )

    def test_secret_key_not_insecure_prefix_in_production(self):
        """RAILWAY_ENVIRONMENT가 설정된 실제 프로덕션에서 django-insecure- 접두어 금지"""
        import os
        from django.conf import settings as django_settings
        # RAILWAY_ENVIRONMENT가 실제로 설정된 경우에만 검증 (로컬 개발 환경 제외)
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            self.assertFalse(
                django_settings.SECRET_KEY.startswith('django-insecure-'),
                "Railway 프로덕션에서 insecure SECRET_KEY(django-insecure- 접두어)를 사용하면 안 됩니다."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9: EmailEncryption 안전성 테스트
# ─────────────────────────────────────────────────────────────────────────────

class EmailEncryptionSafetyTests(TestCase):
    """Phase 9: EmailEncryption 클래스의 안전한 키 처리 검증"""

    def test_get_cipher_without_key_raises_value_error(self):
        """EMAIL_ENCRYPTION_KEY=None일 때 get_cipher()가 ValueError 발생"""
        from unittest.mock import patch
        from reporting.imap_utils import EmailEncryption

        with patch.object(
            __import__('django.conf', fromlist=['settings']).settings,
            'EMAIL_ENCRYPTION_KEY',
            None
        ):
            with self.assertRaises(ValueError):
                EmailEncryption.get_cipher()

    def test_encrypt_password_without_key_returns_empty(self):
        """EMAIL_ENCRYPTION_KEY=None일 때 encrypt_password()가 빈 문자열 반환 (예외 미전파)"""
        from unittest.mock import patch
        from reporting.imap_utils import EmailEncryption

        with patch.object(
            __import__('django.conf', fromlist=['settings']).settings,
            'EMAIL_ENCRYPTION_KEY',
            None
        ):
            result = EmailEncryption.encrypt_password('my_password')
            self.assertEqual(result, '', "키 없이 암호화 시 빈 문자열을 반환해야 합니다")

    def test_decrypt_password_without_key_returns_empty(self):
        """EMAIL_ENCRYPTION_KEY=None일 때 decrypt_password()가 빈 문자열 반환 (예외 미전파)"""
        from unittest.mock import patch
        from reporting.imap_utils import EmailEncryption

        with patch.object(
            __import__('django.conf', fromlist=['settings']).settings,
            'EMAIL_ENCRYPTION_KEY',
            None
        ):
            result = EmailEncryption.decrypt_password('some_encrypted_data')
            self.assertEqual(result, '', "키 없이 복호화 시 빈 문자열을 반환해야 합니다")

    def test_encrypt_decrypt_roundtrip_with_valid_key(self):
        """유효한 Fernet 키로 암호화 후 복호화하면 원본과 동일"""
        from unittest.mock import patch
        from cryptography.fernet import Fernet
        from reporting.imap_utils import EmailEncryption

        test_key = Fernet.generate_key()
        with patch.object(
            __import__('django.conf', fromlist=['settings']).settings,
            'EMAIL_ENCRYPTION_KEY',
            test_key
        ):
            original = 'my_secure_password_123!'
            encrypted = EmailEncryption.encrypt_password(original)
            self.assertNotEqual(encrypted, original, "암호화된 값은 원본과 달라야 합니다")
            self.assertNotEqual(encrypted, '', "유효한 키로 암호화 시 빈 문자열이 아니어야 합니다")

            decrypted = EmailEncryption.decrypt_password(encrypted)
            self.assertEqual(decrypted, original, "복호화된 값이 원본과 일치해야 합니다")

    def test_encrypt_empty_password_returns_empty(self):
        """빈 비밀번호 입력 시 빈 문자열 반환"""
        from reporting.imap_utils import EmailEncryption
        result = EmailEncryption.encrypt_password('')
        self.assertEqual(result, '')

    def test_decrypt_empty_password_returns_empty(self):
        """빈 암호화 비밀번호 입력 시 빈 문자열 반환"""
        from reporting.imap_utils import EmailEncryption
        result = EmailEncryption.decrypt_password('')
        self.assertEqual(result, '')


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.5: 제품 규격/단위 저장 테스트 (Bug 1)
# ─────────────────────────────────────────────────────────────────────────────

class ProductSpecificationSaveTests(TestCase):
    """제품 생성/수정 시 specification 및 unit 필드가 올바르게 저장되는지 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='제품테스트회사')
        self.salesman = make_user('prod_salesman', role='salesman', company=self.company)
        self.client.force_login(self.salesman)

    def test_product_create_saves_specification(self):
        """일반 폼 제출로 제품 생성 시 specification 저장"""
        from reporting.models import Product
        response = self.client.post(
            reverse('reporting:product_create'),
            {
                'product_code': 'TEST-SPEC-001',
                'standard_price': '10000',
                'specification': '100x200mm',
                'unit': 'EA',
                'is_active': 'on',
            },
        )
        # 성공 시 목록으로 리다이렉트
        self.assertIn(response.status_code, [200, 302])
        product = Product.objects.filter(product_code='TEST-SPEC-001').first()
        self.assertIsNotNone(product, '제품이 생성되어야 합니다')
        self.assertEqual(product.specification, '100x200mm',
                         '규격(specification)이 저장되어야 합니다')

    def test_product_create_saves_unit(self):
        """일반 폼 제출로 제품 생성 시 unit 저장"""
        from reporting.models import Product
        self.client.post(
            reverse('reporting:product_create'),
            {
                'product_code': 'TEST-UNIT-001',
                'standard_price': '5000',
                'specification': '',
                'unit': 'SET',
                'is_active': 'on',
            },
        )
        product = Product.objects.filter(product_code='TEST-UNIT-001').first()
        self.assertIsNotNone(product, '제품이 생성되어야 합니다')
        self.assertEqual(product.unit, 'SET', '단위(unit)가 저장되어야 합니다')

    def test_product_edit_saves_specification(self):
        """제품 수정 시 specification 저장"""
        from reporting.models import Product
        product = Product.objects.create(
            product_code='EDIT-SPEC-001',
            standard_price=1000,
            specification='',
            unit='EA',
            created_by=self.salesman,
        )
        self.client.post(
            reverse('reporting:product_edit', args=[product.pk]),
            {
                'product_code': 'EDIT-SPEC-001',
                'standard_price': '1000',
                'specification': '200x300mm',
                'unit': 'EA',
                'is_active': 'on',
            },
        )
        product.refresh_from_db()
        self.assertEqual(product.specification, '200x300mm',
                         '수정된 규격(specification)이 저장되어야 합니다')

    def test_product_edit_saves_unit(self):
        """제품 수정 시 unit 저장"""
        from reporting.models import Product
        product = Product.objects.create(
            product_code='EDIT-UNIT-001',
            standard_price=1000,
            specification='',
            unit='EA',
            created_by=self.salesman,
        )
        self.client.post(
            reverse('reporting:product_edit', args=[product.pk]),
            {
                'product_code': 'EDIT-UNIT-001',
                'standard_price': '1000',
                'specification': '',
                'unit': 'BOX',
                'is_active': 'on',
            },
        )
        product.refresh_from_db()
        self.assertEqual(product.unit, 'BOX',
                         '수정된 단위(unit)가 저장되어야 합니다')

    def test_product_edit_existing_data_preserved(self):
        """제품 수정 시 기존 데이터(가격 등)가 보존됨"""
        from reporting.models import Product
        from decimal import Decimal
        product = Product.objects.create(
            product_code='PRES-001',
            standard_price=Decimal('9999'),
            specification='기존규격',
            unit='EA',
            created_by=self.salesman,
        )
        self.client.post(
            reverse('reporting:product_edit', args=[product.pk]),
            {
                'product_code': 'PRES-001',
                'standard_price': '9999',
                'specification': '새규격',
                'unit': 'EA',
                'is_active': 'on',
            },
        )
        product.refresh_from_db()
        self.assertEqual(product.standard_price, Decimal('9999'),
                         '수정 후 기존 가격이 보존되어야 합니다')
        self.assertEqual(product.specification, '새규격')


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.5: 대시보드 일정 표시 테스트 (Bug 2 & 3)
# ─────────────────────────────────────────────────────────────────────────────

class DashboardScheduleDisplayTests(TestCase):
    """대시보드 today_schedules / upcoming_schedules_dash / schedule_count 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='대시보드일정테스트회사')
        self.salesman = make_user('dash_sched_user', role='salesman', company=self.company)
        self.client.force_login(self.salesman)

        from reporting.models import Company, Department, FollowUp, Schedule
        from django.utils import timezone
        from datetime import timedelta
        import datetime

        company = Company.objects.create(name='테스트고객사', created_by=self.salesman)
        dept = Department.objects.create(name='테스트부서', company=company, created_by=self.salesman)
        followup = FollowUp.objects.create(
            user=self.salesman, customer_name='테스트담당자',
            company=company, department=dept,
        )
        today = timezone.localdate()

        # 오늘 예정 일정
        self.today_scheduled = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today, visit_time=datetime.time(9, 0),
            activity_type='customer_meeting', status='scheduled',
        )
        # 오늘 완료된 일정
        self.today_completed = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today, visit_time=datetime.time(14, 0),
            activity_type='customer_meeting', status='completed',
        )
        # 내일 예정 일정
        self.tomorrow_scheduled = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today + timedelta(days=1), visit_time=datetime.time(10, 0),
            activity_type='customer_meeting', status='scheduled',
        )
        # 3일 후 완료 일정
        self.upcoming_completed = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today + timedelta(days=3), visit_time=datetime.time(11, 0),
            activity_type='customer_meeting', status='completed',
        )
        # 8일 후 (범위 밖) 일정
        self.out_of_range = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today + timedelta(days=8), visit_time=datetime.time(9, 0),
            activity_type='customer_meeting', status='scheduled',
        )
        # 어제 일정 (과거 - upcoming에 포함 안 됨)
        self.yesterday = Schedule.objects.create(
            user=self.salesman, followup=followup,
            visit_date=today - timedelta(days=1), visit_time=datetime.time(9, 0),
            activity_type='customer_meeting', status='scheduled',
        )

    def test_dashboard_returns_200(self):
        """대시보드 200 응답"""
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_today_schedules_includes_scheduled(self):
        """today_schedules에 오늘 예정 일정 포함"""
        r = self.client.get(reverse('reporting:dashboard'))
        today_scheds = list(r.context.get('today_schedules', []))
        ids = [s.pk for s in today_scheds]
        self.assertIn(self.today_scheduled.pk, ids,
                      '오늘 예정 일정이 today_schedules에 포함되어야 합니다')

    def test_today_schedules_includes_completed(self):
        """today_schedules에 오늘 완료된 일정도 포함"""
        r = self.client.get(reverse('reporting:dashboard'))
        today_scheds = list(r.context.get('today_schedules', []))
        ids = [s.pk for s in today_scheds]
        self.assertIn(self.today_completed.pk, ids,
                      '오늘 완료된 일정도 today_schedules에 포함되어야 합니다')

    def test_upcoming_includes_tomorrow_scheduled(self):
        """upcoming_schedules_dash에 내일 예정 일정 포함"""
        r = self.client.get(reverse('reporting:dashboard'))
        upcoming = list(r.context.get('upcoming_schedules_dash', []))
        ids = [s.pk for s in upcoming]
        self.assertIn(self.tomorrow_scheduled.pk, ids,
                      '내일 예정 일정이 upcoming_schedules_dash에 포함되어야 합니다')

    def test_upcoming_includes_completed_within_range(self):
        """upcoming_schedules_dash에 이번 주 완료된 일정도 포함 (Bug 2 핵심)"""
        r = self.client.get(reverse('reporting:dashboard'))
        upcoming = list(r.context.get('upcoming_schedules_dash', []))
        ids = [s.pk for s in upcoming]
        self.assertIn(self.upcoming_completed.pk, ids,
                      '이번 주 완료된 일정도 upcoming_schedules_dash에 포함되어야 합니다 (Bug 2 수정)')

    def test_upcoming_excludes_out_of_range(self):
        """upcoming_schedules_dash에 6일 초과 일정은 미포함"""
        r = self.client.get(reverse('reporting:dashboard'))
        upcoming = list(r.context.get('upcoming_schedules_dash', []))
        ids = [s.pk for s in upcoming]
        self.assertNotIn(self.out_of_range.pk, ids,
                         '6일 초과 일정은 upcoming_schedules_dash에 포함되지 않아야 합니다')

    def test_upcoming_excludes_past_schedules(self):
        """upcoming_schedules_dash에 과거 일정 미포함"""
        r = self.client.get(reverse('reporting:dashboard'))
        upcoming = list(r.context.get('upcoming_schedules_dash', []))
        ids = [s.pk for s in upcoming]
        self.assertNotIn(self.yesterday.pk, ids,
                         '어제 일정은 upcoming_schedules_dash에 포함되지 않아야 합니다')

    def test_schedule_count_nonzero_when_schedules_exist(self):
        """일정이 있을 때 schedule_count가 0이 아님 (Bug 3 핵심)"""
        r = self.client.get(reverse('reporting:dashboard'))
        count = r.context.get('schedule_count', 0)
        self.assertGreater(int(count), 0,
                           'today/upcoming 일정이 있을 때 schedule_count > 0이어야 합니다 (Bug 3 수정)')


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.5: 주간보고 일정 로드 API 심화 테스트 (Bug 4)
# ─────────────────────────────────────────────────────────────────────────────

class WeeklyReportLoadSchedulesExtendedTests(TestCase):
    """주간보고 일정 로드 API: 일정 데이터가 올바르게 반환되는지 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='주간보고심화테스트회사')
        self.salesman = make_user('wr_ext_salesman', role='salesman', company=self.company)
        self.client.force_login(self.salesman)

        from reporting.models import Company, Department, FollowUp, Schedule
        import datetime

        company = Company.objects.create(name='주간보고고객사', created_by=self.salesman)
        dept = Department.objects.create(name='주간보고부서', company=company, created_by=self.salesman)
        self.followup = FollowUp.objects.create(
            user=self.salesman, customer_name='주간보고담당자',
            company=company, department=dept,
        )
        self.schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 21),
            visit_time=datetime.time(9, 0),
            activity_type='customer_meeting', status='completed',
        )

    def test_load_schedules_returns_schedules_key(self):
        """schedules 키가 응답에 포함됨"""
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('schedules', data)

    def test_load_schedules_contains_created_schedule(self):
        """해당 주에 생성된 일정이 결과에 포함됨"""
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        schedules = data.get('schedules', [])
        self.assertGreater(len(schedules), 0,
                           '해당 주에 일정이 있으면 schedules 목록이 비어있지 않아야 합니다')

    def test_load_schedules_out_of_range_excluded(self):
        """범위 밖 주에는 해당 일정이 포함되지 않음"""
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-05-04', 'week_end': '2026-05-10'},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        schedules = data.get('schedules', [])
        schedule_ids = [s.get('id') for s in schedules]
        self.assertNotIn(self.schedule.pk, schedule_ids,
                         '범위 밖 일정은 반환되지 않아야 합니다')

    def test_load_schedules_unauthorized_data_excluded(self):
        """다른 사용자의 일정은 반환되지 않음"""
        from reporting.models import Schedule
        import datetime
        other_user = make_user('wr_other_user', role='salesman', company=self.company)
        Schedule.objects.create(
            user=other_user, followup=self.followup,
            visit_date=datetime.date(2026, 4, 22),
            visit_time=datetime.time(9, 0),
            activity_type='customer_meeting', status='completed',
        )
        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        schedules_data = data.get('schedules', [])
        for s in schedules_data:
            self.assertNotEqual(
                s.get('user_id'), other_user.pk,
                '다른 사용자의 일정이 포함되면 안 됩니다',
            )

    def test_quote_schedule_returns_quote_total_amount(self):
        """견적 제출 일정은 연결된 Quote 총액을 함께 반환"""
        from decimal import Decimal
        from reporting.models import Quote, Schedule
        import datetime

        quote_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 22),
            visit_time=datetime.time(10, 0),
            activity_type='quote', status='completed',
            vat_mode='none',
        )
        Quote.objects.create(
            quote_number='WR-QUOTE-001',
            schedule=quote_schedule,
            followup=self.followup,
            user=self.salesman,
            valid_until=datetime.date(2026, 5, 22),
            subtotal=Decimal('250000'),
        )

        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        quote_items = r.json().get('categorized', {}).get('quote_delivery', [])
        payload = next(item for item in quote_items if item['id'] == quote_schedule.pk)
        self.assertEqual(payload['quotes'][0]['amount'], '250,000원')

    def test_quote_schedule_without_quote_uses_expected_revenue_amount(self):
        """Quote 객체가 없는 견적 일정도 예상 매출액을 금액으로 반환"""
        from decimal import Decimal
        from reporting.models import Schedule
        import datetime

        quote_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 23),
            visit_time=datetime.time(11, 0),
            activity_type='quote', status='scheduled',
            expected_revenue=Decimal('320000'),
        )

        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        quote_items = r.json().get('categorized', {}).get('quote_delivery', [])
        payload = next(item for item in quote_items if item['id'] == quote_schedule.pk)
        self.assertEqual(payload['amount'], '320,000원')
        self.assertEqual(payload['amount_label'], '견적 금액')

    def test_delivery_schedule_returns_delivery_item_amount(self):
        """납품 일정은 DeliveryItem 합계 금액을 함께 반환"""
        from decimal import Decimal
        from reporting.models import DeliveryItem, Schedule
        import datetime

        delivery_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 24),
            visit_time=datetime.time(14, 0),
            activity_type='delivery', status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='WR 납품 품목',
            quantity=2,
            unit_price=Decimal('50000'),
        )

        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        delivery_items = r.json().get('categorized', {}).get('quote_delivery', [])
        payload = next(item for item in delivery_items if item['id'] == delivery_schedule.pk)
        self.assertEqual(payload['amount'], '110,000원')
        self.assertEqual(payload['amount_label'], '납품 금액')

    def test_delivery_schedule_falls_back_to_history_amount(self):
        """DeliveryItem이 없으면 연결된 History 납품 금액을 반환"""
        from decimal import Decimal
        from reporting.models import History, Schedule
        import datetime

        delivery_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 25),
            visit_time=datetime.time(15, 0),
            activity_type='delivery', status='completed',
        )
        History.objects.create(
            user=self.salesman,
            followup=self.followup,
            schedule=delivery_schedule,
            action_type='delivery_schedule',
            content='납품 완료',
            delivery_amount=Decimal('88000'),
        )

        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        delivery_items = r.json().get('categorized', {}).get('quote_delivery', [])
        payload = next(item for item in delivery_items if item['id'] == delivery_schedule.pk)
        self.assertEqual(payload['amount'], '88,000원')
        self.assertEqual(payload['amount_label'], '납품 금액')

    def test_delivery_schedule_preserves_explicit_zero_history_amount(self):
        """명시적으로 저장된 0원 납품 금액도 응답에 포함"""
        from decimal import Decimal
        from reporting.models import History, Schedule
        import datetime

        delivery_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 4, 26),
            visit_time=datetime.time(16, 0),
            activity_type='delivery', status='completed',
        )
        History.objects.create(
            user=self.salesman,
            followup=self.followup,
            schedule=delivery_schedule,
            action_type='delivery_schedule',
            content='무상 납품',
            delivery_amount=Decimal('0'),
        )

        r = self.client.get(
            reverse('reporting:weekly_report_load_schedules'),
            {'week_start': '2026-04-21', 'week_end': '2026-04-27'},
        )
        self.assertEqual(r.status_code, 200)
        delivery_items = r.json().get('categorized', {}).get('quote_delivery', [])
        payload = next(item for item in delivery_items if item['id'] == delivery_schedule.pk)
        self.assertEqual(payload['amount'], '0원')
        self.assertEqual(payload['amount_label'], '납품 금액')


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.6-1: 세금계산서 요청 API 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TaxInvoiceRequestAPITests(TestCase):
    """세금계산서 요청 API (followup_tax_invoices_api / tax_invoice_update_status_api) 테스트"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='세금계산서테스트회사')
        self.salesman = make_user('taxinv_salesman', role='salesman', company=self.company)
        self.manager = make_user('taxinv_manager', role='manager', company=self.company)
        self.other_salesman = make_user('taxinv_other', role='salesman', company=self.company)
        self.client.force_login(self.salesman)

        from reporting.models import Company, Department, FollowUp, Schedule
        import datetime

        cust_company = Company.objects.create(name='세금계산서고객사', created_by=self.salesman)
        dept = Department.objects.create(name='세금계산서부서', company=cust_company, created_by=self.salesman)
        self.followup = FollowUp.objects.create(
            user=self.salesman, customer_name='테스트담당자',
            company=cust_company, department=dept,
        )
        self.delivery_schedule = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 6, 1),
            visit_time=datetime.time(10, 0),
            activity_type='delivery', status='completed',
        )

    def _url_list(self):
        return reverse('reporting:followup_tax_invoices_api',
                       kwargs={'followup_id': self.followup.pk})

    def _url_status(self, req_id):
        return reverse('reporting:tax_invoice_update_status_api',
                       kwargs={'request_id': req_id})

    # ── GET: 목록 조회 ─────────────────────────────────────────────────────

    def test_get_list_success(self):
        """로그인한 영업사원이 GET 요청 시 200 + success=True 반환"""
        r = self.client.get(self._url_list())
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('success'), 'success 필드가 True여야 합니다')
        self.assertIn('tax_invoices', data)
        self.assertIn('delivery_schedules', data)

    def test_get_list_requires_login(self):
        """비로그인 상태에서 GET 요청 시 리다이렉트 또는 403"""
        self.client.logout()
        r = self.client.get(self._url_list())
        self.assertIn(r.status_code, [302, 403],
                      '비로그인 요청은 302 또는 403이어야 합니다')

    def test_get_list_other_company_blocked(self):
        """다른 회사 사용자는 403 반환"""
        other_company = UserCompany.objects.create(name='다른회사')
        outsider = make_user('taxinv_outsider', role='salesman', company=other_company)
        self.client.force_login(outsider)
        r = self.client.get(self._url_list())
        self.assertEqual(r.status_code, 403)

    # ── POST: 요청 생성 ────────────────────────────────────────────────────

    def test_post_create_request_success(self):
        """영업사원이 납품 일정에 세금계산서 발행 요청 생성 성공"""
        r = self.client.post(self._url_list(), {
            'schedule_id': self.delivery_schedule.pk,
            'memo': '발행 부탁드립니다',
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('success'), f'success가 True여야 합니다: {data}')
        self.assertEqual(data.get('status'), 'requested')

    def test_post_create_duplicate_blocked(self):
        """이미 요청 중인 일정에 중복 요청 시 400 반환"""
        from reporting.models import TaxInvoiceRequest
        TaxInvoiceRequest.objects.create(
            followup=self.followup,
            schedule=self.delivery_schedule,
            status='requested',
            requested_by=self.salesman,
        )
        r = self.client.post(self._url_list(), {
            'schedule_id': self.delivery_schedule.pk,
        })
        self.assertEqual(r.status_code, 400)

    def test_post_without_schedule_succeeds(self):
        """일정 없이 followup만으로도 요청 생성 가능"""
        r = self.client.post(self._url_list(), {'memo': '일정 없는 요청'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('success'))

    # ── 상태 변경: 발행완료 ────────────────────────────────────────────────

    def test_salesman_cannot_issue(self):
        """영업사원은 발행완료 처리 불가 → 403"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        r = self.client.post(self._url_status(req.pk), {'status': 'issued'})
        self.assertEqual(r.status_code, 403)

    def test_manager_can_issue(self):
        """매니저는 발행완료 처리 가능"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        self.client.force_login(self.manager)
        r = self.client.post(self._url_status(req.pk), {
            'status': 'issued', 'memo': '발행 처리함'
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('status'), 'issued')

    # ── 상태 변경: 취소 ───────────────────────────────────────────────────

    def test_requester_can_cancel_own_request(self):
        """요청자 본인은 자신의 요청 취소 가능"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        r = self.client.post(self._url_status(req.pk), {
            'status': 'cancelled', 'memo': '취소 사유'
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('status'), 'cancelled')

    def test_other_salesman_cannot_cancel_others_request(self):
        """다른 영업사원은 타인의 요청을 취소 불가 → 403"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        self.client.force_login(self.other_salesman)
        r = self.client.post(self._url_status(req.pk), {
            'status': 'cancelled', 'memo': '취소'
        })
        self.assertEqual(r.status_code, 403)

    # ── 보류 처리 ─────────────────────────────────────────────────────────

    def test_manager_can_set_on_hold(self):
        """매니저는 보류 처리 가능"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        self.client.force_login(self.manager)
        r = self.client.post(self._url_status(req.pk), {
            'status': 'on_hold', 'memo': '검토 중'
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get('status'), 'on_hold')

    # ── 잘못된 상태값 ─────────────────────────────────────────────────────

    def test_invalid_status_value_returns_400(self):
        """올바르지 않은 status 값은 400 반환"""
        from reporting.models import TaxInvoiceRequest
        req = TaxInvoiceRequest.objects.create(
            followup=self.followup, status='requested',
            requested_by=self.salesman,
        )
        self.client.force_login(self.manager)
        r = self.client.post(self._url_status(req.pk), {'status': 'INVALID'})
        self.assertEqual(r.status_code, 400)

    # ── 404 처리 ─────────────────────────────────────────────────────────

    def test_nonexistent_followup_returns_404(self):
        """존재하지 않는 followup_id는 404 반환"""
        r = self.client.get(
            reverse('reporting:followup_tax_invoices_api',
                    kwargs={'followup_id': 99999})
        )
        self.assertEqual(r.status_code, 404)

    def test_nonexistent_request_id_returns_404(self):
        """존재하지 않는 request_id는 404 반환"""
        self.client.force_login(self.manager)
        r = self.client.post(
            reverse('reporting:tax_invoice_update_status_api',
                    kwargs={'request_id': 99999}),
            {'status': 'issued'},
        )
        self.assertEqual(r.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# [재현] 대시보드 통합 검색 API 테스트
# ─────────────────────────────────────────────────────────────────────────────

class DashboardSearchAPITests(TestCase):
    """dashboard_search_api 통합 검색 API 테스트"""

    def setUp(self):
        import datetime
        self.client = Client()
        # 자사 (검색 허용 범위)
        self.company_uc = UserCompany.objects.create(name='검색테스트회사')
        self.salesman = make_user('ds_salesman', role='salesman', company=self.company_uc)
        self.client.force_login(self.salesman)

        # 타사 (검색 제외 범위)
        self.other_uc = UserCompany.objects.create(name='타사회사')
        self.other_user = make_user('ds_other', role='salesman', company=self.other_uc)

        from reporting.models import Company, Department, FollowUp, Schedule, History, DeliveryItem

        # ── 자사 거래처/연구실/담당자 ──────────────────────────────────────
        cust = Company.objects.create(name='검색한국대학교', created_by=self.salesman)
        self.dept = Department.objects.create(name='PCR연구실', company=cust, created_by=self.salesman)
        self.followup = FollowUp.objects.create(
            user=self.salesman,
            customer_name='김연구원',
            company=cust,
            department=self.dept,
            user_company=self.company_uc,
        )

        # 납품 품목 (DeliveryItem)
        sched = Schedule.objects.create(
            user=self.salesman, followup=self.followup,
            visit_date=datetime.date(2026, 5, 1),
            visit_time=datetime.time(10, 0),
            activity_type='delivery', status='completed',
            notes='PCR 실험 관련 방문',
        )
        DeliveryItem.objects.create(
            schedule=sched,
            item_name='PCR 시약 키트',
            quantity=10, unit_price=5000, total_price=50000,
        )
        # 활동 내역
        History.objects.create(
            user=self.salesman, followup=self.followup,
            action_type='customer_meeting',
            content='PCR 장비 데모 진행',
        )

        # ── 타사 거래처/연구실 (검색 제외 확인용) ──────────────────────────
        other_cust = Company.objects.create(name='타사학교', created_by=self.other_user)
        other_dept = Department.objects.create(name='PCR타부서', company=other_cust, created_by=self.other_user)
        other_fu = FollowUp.objects.create(
            user=self.other_user,
            customer_name='박타사',
            company=other_cust,
            department=other_dept,
            user_company=self.other_uc,
        )

    def _url(self):
        return reverse('reporting:dashboard_search_api')

    def test_requires_login(self):
        """비로그인 시 로그인 페이지로 리다이렉트."""
        self.client.logout()
        r = self.client.get(self._url(), {'q': 'PCR'})
        self.assertIn(r.status_code, [302, 403])

    def test_short_query_returns_400(self):
        """1자 검색어는 400 에러를 반환."""
        r = self.client.get(self._url(), {'q': 'P'})
        self.assertEqual(r.status_code, 400)
        data = r.json()
        self.assertIn('error', data)

    def test_empty_query_returns_400(self):
        """빈 검색어는 400 에러를 반환."""
        r = self.client.get(self._url(), {'q': ''})
        self.assertEqual(r.status_code, 400)

    def test_keyword_finds_delivery_item(self):
        """납품 품목명 키워드로 연구실을 찾는다."""
        r = self.client.get(self._url(), {'q': 'PCR 시약'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        dept_names = [d['department_name'] for d in data['departments']]
        self.assertIn('PCR연구실', dept_names)

    def test_keyword_finds_history_content(self):
        """활동 내용 키워드로 연구실을 찾는다."""
        r = self.client.get(self._url(), {'q': 'PCR 장비'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        dept_names = [d['department_name'] for d in data['departments']]
        self.assertIn('PCR연구실', dept_names)

    def test_other_company_excluded(self):
        """타사 연구실은 검색 결과에 포함되지 않는다."""
        r = self.client.get(self._url(), {'q': 'PCR타부서'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        dept_names = [d['department_name'] for d in data['departments']]
        self.assertNotIn('PCR타부서', dept_names)

    def test_no_match_returns_empty_list(self):
        """매칭 없으면 빈 리스트 반환."""
        r = self.client.get(self._url(), {'q': '없는키워드XYZ9999'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['result_count'], 0)
        self.assertEqual(data['departments'], [])


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.6-2: 부가세 모드 (VAT Mode) 테스트
# ─────────────────────────────────────────────────────────────────────────────

class ScheduleVatModeTests(TestCase):
    """Schedule.vat_mode 필드 및 Quote.save() 부가세 계산 테스트"""

    def setUp(self):
        import datetime
        from decimal import Decimal
        from reporting.models import UserCompany, Company, Department, FollowUp, Schedule, Quote

        self.company_uc = UserCompany.objects.create(name='VAT테스트회사')
        self.salesman = make_user('vat_salesman', role='salesman', company=self.company_uc)
        cust = Company.objects.create(name='VAT테스트거래처', created_by=self.salesman)
        dept = Department.objects.create(name='VAT테스트연구실', company=cust, created_by=self.salesman)
        self.followup = FollowUp.objects.create(
            user=self.salesman,
            customer_name='VAT담당자',
            company=cust,
            department=dept,
            user_company=self.company_uc,
        )
        self.base_schedule_date = datetime.date(2026, 6, 1)
        self.base_schedule_time = datetime.time(10, 0)

    def _make_schedule(self, vat_mode='excluded'):
        from reporting.models import Schedule
        import datetime
        return Schedule.objects.create(
            user=self.salesman,
            followup=self.followup,
            visit_date=self.base_schedule_date,
            visit_time=self.base_schedule_time,
            activity_type='quote',
            status='scheduled',
            vat_mode=vat_mode,
        )

    def _make_quote(self, schedule, subtotal_val, probability=50):
        import datetime
        from decimal import Decimal
        from reporting.models import Quote
        return Quote.objects.create(
            quote_number=f'Q-TEST-{schedule.pk}-{subtotal_val}',
            schedule=schedule,
            followup=self.followup,
            user=self.salesman,
            valid_until=self.base_schedule_date,
            subtotal=subtotal_val,
            probability=probability,
        )

    def test_default_vat_mode_is_excluded(self):
        """vat_mode 기본값은 'excluded'이어야 한다."""
        schedule = self._make_schedule()
        self.assertEqual(schedule.vat_mode, 'excluded')

    def test_vat_excluded_calculation(self):
        """부가세 별도: tax = subtotal * 10%, total = subtotal + tax."""
        from decimal import Decimal
        schedule = self._make_schedule(vat_mode='excluded')
        quote = self._make_quote(schedule, subtotal_val=100000)
        self.assertEqual(quote.tax_amount, Decimal('10000'))
        self.assertEqual(quote.total_amount, Decimal('110000'))

    def test_vat_included_calculation(self):
        """부가세 포함: total = subtotal(입력값), tax = total - total/1.1."""
        from decimal import Decimal, ROUND_HALF_UP
        schedule = self._make_schedule(vat_mode='included')
        quote = self._make_quote(schedule, subtotal_val=110000)
        supply = (Decimal('110000') / Decimal('1.1')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        expected_tax = Decimal('110000') - supply
        self.assertEqual(quote.total_amount, Decimal('110000'))
        self.assertEqual(quote.tax_amount, expected_tax)

    def test_vat_none_calculation(self):
        """부가세 없음: tax = 0, total = subtotal."""
        from decimal import Decimal
        schedule = self._make_schedule(vat_mode='none')
        quote = self._make_quote(schedule, subtotal_val=100000)
        self.assertEqual(quote.tax_amount, Decimal('0'))
        self.assertEqual(quote.total_amount, Decimal('100000'))

    def test_vat_excluded_weighted_revenue(self):
        """부가세 별도: 가중매출 = total * probability / 100."""
        from decimal import Decimal
        schedule = self._make_schedule(vat_mode='excluded')
        quote = self._make_quote(schedule, subtotal_val=100000, probability=50)
        self.assertEqual(quote.weighted_revenue, Decimal('55000'))  # 110000 * 0.5

    def test_vat_none_weighted_revenue(self):
        """부가세 없음: 가중매출 = total * probability / 100."""
        from decimal import Decimal
        schedule = self._make_schedule(vat_mode='none')
        quote = self._make_quote(schedule, subtotal_val=100000, probability=50)
        self.assertEqual(quote.weighted_revenue, Decimal('50000'))  # 100000 * 0.5

    def test_schedule_form_includes_vat_mode(self):
        """스케줄 생성 시 vat_mode가 POST 데이터로 저장된다."""
        import datetime
        from reporting.models import Schedule
        self.client = Client()
        self.client.force_login(self.salesman)

        post_data = {
            'followup': self.followup.pk,
            'visit_date': '2026-06-10',
            'visit_time': '10:00',
            'activity_type': 'quote',
            'location': '',
            'status': 'scheduled',
            'notes': 'VAT 모드 테스트',
            'vat_mode': 'none',
        }
        r = self.client.post(reverse('reporting:schedule_create'), post_data, follow=False)
        # 성공 시 리다이렉트
        self.assertIn(r.status_code, [200, 302])
        created = Schedule.objects.filter(
            followup=self.followup, vat_mode='none'
        ).first()
        self.assertIsNotNone(created, 'vat_mode=none인 스케줄이 생성되어야 합니다.')

