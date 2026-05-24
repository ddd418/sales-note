import json
import os
from datetime import time, timedelta
from urllib.parse import urljoin
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.utils import timezone
from reporting.models import (
    AccountCleanupAuditLog,
    AccountCleanupDecision,
    Company,
    Department,
    DepartmentMemo,
    DocumentGenerationLog,
    DocumentTemplate,
    EmailLog,
    FollowUp,
    History,
    BusinessCard,
    CustomerAsset,
    ServiceCase,
    CalibrationRecord,
    DeliveryItem,
    Prepayment,
    PrepaymentLedgerEntry,
    PrepaymentUsage,
    Quote,
    Schedule,
    ScheduledEmail,
    ScheduledEmailAttachment,
    ScheduleQuoteGroupNote,
    UserProfile,
    UserCompany,
)
from reporting.test_fixtures import create_account_ledger_fixture


FRONTEND_BASE_URL = 'https://sales-note-frontend-production.up.railway.app/'


def frontend_url(path):
    return urljoin(FRONTEND_BASE_URL, path.lstrip('/'))


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

    def test_login_page_preserves_next_hidden_field(self):
        """React 직접 URL에서 온 next 값은 로그인 form POST까지 유지"""
        response = self.client.get(reverse('reporting:login'), {'next': '/customers/42/'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next"', html=False)
        self.assertContains(response, 'value="/customers/42/"', html=False)

    def test_login_success_redirects_to_next_react_path(self):
        """로그인 성공 후 상대 React next 경로로 복귀"""
        response = self.client.post(
            reverse('reporting:login'),
            {
                'username': 'testuser',
                'password': 'TestPass123!',
                'next': '/customers/42/',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/customers/42/')
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(self.user.id))

    @override_settings(FRONTEND_PIPELINE_URL=FRONTEND_BASE_URL)
    def test_login_success_allows_configured_frontend_absolute_next(self):
        """프론트 운영 도메인의 absolute next URL은 허용"""
        next_url = frontend_url('reports/?date_from=2026-05-01')

        response = self.client.post(
            reverse('reporting:login'),
            {
                'username': 'testuser',
                'password': 'TestPass123!',
                'next': next_url,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], next_url)

    def test_login_success_rejects_external_next(self):
        """외부 도메인 next는 Django safe redirect 검증으로 차단"""
        response = self.client.post(
            reverse('reporting:login'),
            {
                'username': 'testuser',
                'password': 'TestPass123!',
                'next': 'https://example.com/steal',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            'https://sales-note-frontend-production.up.railway.app/dashboard/',
        )

    def test_login_fail_wrong_password(self):
        """잘못된 비밀번호로 로그인 실패"""
        response = self.client.post(
            reverse('reporting:login'),
            {'username': 'testuser', 'password': 'wrongpassword'},
        )
        self.assertEqual(response.status_code, 200)  # 로그인 페이지 재표시

    def test_followup_list_authenticated(self):
        """인증 후 거래처 목록은 React 고객 화면으로 이동"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:followup_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], frontend_url('customers/'))

    def test_opportunity_list_url_removed(self):
        """별도 영업기회 목록 URL은 제거되어야 함"""
        self.client.force_login(self.user)
        response = self.client.get('/reporting/opportunities/')
        self.assertEqual(response.status_code, 404)

    def test_schedule_list_authenticated(self):
        """인증 후 일정 목록은 React 일정 화면으로 이동"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:schedule_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], frontend_url('schedules/'))

    def test_schedule_calendar_authenticated(self):
        """인증 후 일정 캘린더는 React 캘린더로 이동"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:schedule_calendar'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], frontend_url('schedules/calendar/'))

    def test_history_list_authenticated(self):
        """인증 후 영업 활동 목록은 React 영업노트 화면으로 이동"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:history_list'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], frontend_url('notes/'))


class CoreCrmLegacyRedirectTests(TestCase):
    """Core Django template pages should hand users to React during migration."""

    def setUp(self):
        self.client = Client()
        self.company_profile = UserCompany.objects.create(name='React전환회사')
        self.user = make_user('react_redirect_user', role='salesman', company=self.company_profile)
        self.company = Company.objects.create(name='React전환고객사', created_by=self.user)
        self.department = Department.objects.create(name='React전환부서', company=self.company, created_by=self.user)
        self.followup = FollowUp.objects.create(
            user=self.user,
            company=self.company,
            department=self.department,
            customer_name='React전환담당자',
        )
        self.schedule = Schedule.objects.create(
            user=self.user,
            company=self.company_profile,
            followup=self.followup,
            visit_date=timezone.localdate(),
            visit_time=time(9, 0),
            activity_type='customer_meeting',
        )
        self.history = History.objects.create(
            user=self.user,
            company=self.company_profile,
            followup=self.followup,
            action_type='customer_meeting',
            content='React 전환 테스트',
        )
        self.client.force_login(self.user)

    def assertReactRedirect(self, url, expected):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], frontend_url(expected))

    def test_core_list_page_redirects(self):
        self.assertReactRedirect(reverse('reporting:dashboard'), 'dashboard/')
        self.assertReactRedirect(reverse('reporting:followup_list'), 'customers/')
        self.assertReactRedirect(reverse('reporting:history_list'), 'notes/')
        self.assertReactRedirect(reverse('reporting:schedule_list'), 'schedules/')
        self.assertReactRedirect(reverse('reporting:schedule_calendar'), 'schedules/calendar/')
        self.assertReactRedirect(reverse('reporting:funnel_pipeline'), 'pipeline/')

    def test_core_detail_page_redirects(self):
        self.assertReactRedirect(reverse('reporting:followup_detail', args=[self.followup.id]), f'customers/{self.followup.id}/')
        self.assertReactRedirect(reverse('reporting:customer_detail_report', args=[self.followup.id]), f'customers/{self.followup.id}/')
        self.assertReactRedirect(reverse('reporting:history_detail', args=[self.history.id]), f'notes/{self.history.id}/')
        self.assertReactRedirect(reverse('reporting:schedule_detail', args=[self.schedule.id]), f'schedules/{self.schedule.id}/')

    def test_core_create_page_redirects_preserve_relevant_query(self):
        self.assertReactRedirect(reverse('reporting:followup_create'), 'customers/?create=1')
        self.assertReactRedirect(
            f"{reverse('reporting:schedule_create')}?followup={self.followup.id}&date=2026-05-20",
            f'schedules/?customer={self.followup.id}&date=2026-05-20&create=1',
        )
        self.assertReactRedirect(
            reverse('reporting:history_create_from_schedule', args=[self.schedule.id]),
            f'notes/?create=1&schedule={self.schedule.id}',
        )

    def test_core_filter_query_is_translated(self):
        self.assertReactRedirect(
            f"{reverse('reporting:followup_list')}?pipeline_stage=quote&q=Kim",
            'customers/?stage=quote&q=Kim',
        )

    def test_non_get_legacy_create_action_is_not_redirected_to_react(self):
        response = self.client.post(reverse('reporting:schedule_create'), {
            'followup': str(self.followup.id),
            'visit_date': '2026-05-20',
            'activity_type': 'customer_meeting',
        })
        self.assertNotEqual(response.get('Location', ''), frontend_url('schedules/?create=1'))


class ReactNavigationApiTests(TestCase):
    """React navigation API regression tests."""

    def setUp(self):
        self.client = Client()
        self.user = make_user('nav-user')

    def test_navigation_api_requires_login_json(self):
        response = self.client.get(reverse('reporting:navigation_api'))

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertEqual(payload['error'], 'login_required')

    def test_navigation_api_includes_legacy_fallback_react_menu_entries(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:navigation_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        items_by_id = {item['id']: item for item in payload['items']}
        self.assertEqual(items_by_id['analytics']['href'], '/reports/')
        self.assertEqual(items_by_id['analytics']['label'], '분석')
        self.assertEqual(items_by_id['businessCards']['href'], '/mailbox/business-cards/')
        self.assertEqual(items_by_id['businessCards']['label'], '명함')
        self.assertEqual(items_by_id['services']['href'], '/services/')
        self.assertEqual(items_by_id['services']['label'], '서비스')
        self.assertEqual(items_by_id['profile']['href'], '/profile/')
        self.assertEqual(items_by_id['profile']['label'], '프로필')
        self.assertNotIn('employees', items_by_id)
        self.assertNotIn('userAdmin', items_by_id)
        self.assertFalse(payload['capabilities']['canManageUsers'])

    def test_navigation_api_includes_employee_management_for_manager_only(self):
        company = UserCompany.objects.create(name='직원관리메뉴회사')
        manager = make_user('nav-manager', role='manager', company=company)
        admin = make_user('nav-admin', role='admin', company=company)

        self.client.force_login(manager)
        manager_response = self.client.get(reverse('reporting:navigation_api'))
        self.assertEqual(manager_response.status_code, 200)
        manager_items = {item['id']: item for item in manager_response.json()['items']}
        self.assertIn('employees', manager_items)
        self.assertEqual(manager_items['employees']['label'], '직원관리')
        self.assertEqual(manager_items['employees']['href'], '/employees/')
        self.assertTrue(manager_response.json()['capabilities']['canManageEmployees'])
        self.assertNotIn('userAdmin', manager_items)
        self.assertFalse(manager_response.json()['capabilities']['canManageUsers'])

        self.client.force_login(admin)
        admin_response = self.client.get(reverse('reporting:navigation_api'))
        admin_items = {item['id']: item for item in admin_response.json()['items']}
        self.assertNotIn('employees', admin_items)
        self.assertFalse(admin_response.json()['capabilities']['canManageEmployees'])
        self.assertIn('userAdmin', admin_items)
        self.assertEqual(admin_items['userAdmin']['label'], '사용자관리')
        self.assertEqual(admin_items['userAdmin']['href'], reverse('reporting:user_list'))
        self.assertTrue(admin_response.json()['capabilities']['canManageUsers'])

    def test_navigation_api_role_menu_differences(self):
        company = UserCompany.objects.create(name='권한별메뉴회사')
        salesman = make_user('nav-role-salesman', role='salesman', company=company)
        manager = make_user('nav-role-manager', role='manager', company=company)
        admin = make_user('nav-role-admin', role='admin', company=company)

        self.client.force_login(salesman)
        salesman_payload = self.client.get(reverse('reporting:navigation_api')).json()
        salesman_ids = {item['id'] for item in salesman_payload['items']}
        self.assertIn('tasks', salesman_ids)
        self.assertIn('mail', salesman_ids)
        self.assertNotIn('tasksManager', salesman_ids)
        self.assertNotIn('employees', salesman_ids)
        self.assertNotIn('userAdmin', salesman_ids)
        self.assertFalse(salesman_payload['capabilities']['canManageTasks'])
        self.assertFalse(salesman_payload['capabilities']['canManageUsers'])

        self.client.force_login(manager)
        manager_payload = self.client.get(reverse('reporting:navigation_api')).json()
        manager_ids = {item['id'] for item in manager_payload['items']}
        self.assertIn('tasks', manager_ids)
        self.assertIn('tasksManager', manager_ids)
        self.assertIn('employees', manager_ids)
        self.assertNotIn('mail', manager_ids)
        self.assertNotIn('userAdmin', manager_ids)
        self.assertTrue(manager_payload['capabilities']['canManageTasks'])
        self.assertTrue(manager_payload['capabilities']['canManageEmployees'])
        self.assertFalse(manager_payload['capabilities']['canUseMailbox'])

        self.client.force_login(admin)
        admin_payload = self.client.get(reverse('reporting:navigation_api')).json()
        admin_ids = {item['id'] for item in admin_payload['items']}
        self.assertIn('tasks', admin_ids)
        self.assertIn('mail', admin_ids)
        self.assertIn('userAdmin', admin_ids)
        self.assertNotIn('tasksManager', admin_ids)
        self.assertNotIn('employees', admin_ids)
        self.assertTrue(admin_payload['capabilities']['canManageUsers'])
        self.assertTrue(admin_payload['capabilities']['canUseMailbox'])


class EmployeeManagementApiTests(TestCase):
    """Manager-only employee management API tests."""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='직원관리API회사')
        self.other_company = UserCompany.objects.create(name='직원관리API타사회사')
        self.manager = make_user('employee-api-manager', role='manager', company=self.company)
        self.salesman = make_user('employee-api-sales', role='salesman', company=self.company)
        self.coworker = make_user('employee-api-coworker', role='salesman', company=self.company)
        self.other_user = make_user('employee-api-other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:employees_management_api')

    def test_employee_management_api_requires_manager(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.salesman)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'manager_required')

    def test_employee_management_api_lists_same_company_people(self):
        self.coworker.first_name = '길동'
        self.coworker.last_name = '홍'
        self.coworker.email = 'coworker@example.com'
        self.coworker.save(update_fields=['first_name', 'last_name', 'email'])
        profile = self.coworker.userprofile
        profile.can_download_excel = True
        profile.can_use_ai = True
        profile.created_by = self.manager
        profile.save(update_fields=['can_download_excel', 'can_use_ai', 'created_by'])
        self.salesman.is_active = False
        self.salesman.save(update_fields=['is_active'])
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['scope']['canManage'])
        self.assertEqual(payload['scope']['companyName'], self.company.name)
        ids = {item['id'] for item in payload['employees']}
        self.assertIn(self.manager.id, ids)
        self.assertIn(self.salesman.id, ids)
        self.assertIn(self.coworker.id, ids)
        self.assertNotIn(self.other_user.id, ids)
        self.assertEqual(payload['metrics']['totalEmployees'], 3)
        self.assertEqual(payload['metrics']['inactiveEmployees'], 1)
        coworker_payload = next(item for item in payload['employees'] if item['id'] == self.coworker.id)
        self.assertEqual(coworker_payload['name'], '길동 홍')
        self.assertTrue(coworker_payload['canDownloadExcel'])
        self.assertTrue(coworker_payload['canUseAi'])
        self.assertEqual(coworker_payload['createdByName'], self.manager.username)
        self.assertEqual(coworker_payload['editHref'], reverse('reporting:manager_user_edit', args=[self.coworker.id]))
        manager_payload = next(item for item in payload['employees'] if item['id'] == self.manager.id)
        self.assertEqual(manager_payload['editHref'], '')
        self.assertTrue(manager_payload['isCurrentUser'])

    def test_employee_management_api_filters_by_search_and_role(self):
        self.coworker.first_name = '필터'
        self.coworker.last_name = '대상'
        self.coworker.save(update_fields=['first_name', 'last_name'])
        self.client.force_login(self.manager)

        response = self.client.get(self.url, {'q': '필터', 'role': 'salesman'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['filters']['q'], '필터')
        self.assertEqual(payload['filters']['role'], 'salesman')
        self.assertEqual([item['id'] for item in payload['employees']], [self.coworker.id])


class SalesNoteReadonlyBearerApiTests(TestCase):
    """Readonly MCP bearer token access should cover safe GET API surfaces only."""

    token = 'readonly-test-token'

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='Readonly MCP 회사')
        self.readonly_user = make_user(
            'readonly-mcp-admin',
            role='admin',
            company=self.company,
            can_use_ai=True,
        )

    def _auth_headers(self):
        return {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    @patch.dict(os.environ, {
        'SALES_NOTE_READONLY_TOKEN': token,
        'SALES_NOTE_READONLY_USERNAME': 'readonly-mcp-admin',
    })
    def test_readonly_bearer_can_read_expanded_get_apis(self):
        endpoints = [
            reverse('reporting:navigation_api'),
            reverse('reporting:dashboard_summary_api'),
            reverse('reporting:customers_summary_api'),
            reverse('reporting:notes_summary_api'),
            reverse('reporting:schedules_summary_api'),
            reverse('reporting:customer_assets_summary_api'),
            reverse('reporting:service_cases_summary_api'),
            reverse('reporting:ai_workspace_summary_api'),
            reverse('reporting:prepayment_api_list'),
            reverse('reporting:product_api_list'),
            reverse('reporting:products_management_api'),
            reverse('reporting:document_templates_api'),
            reverse('reporting:weekly_reports_api'),
            reverse('reporting:tasks_api'),
            reverse('reporting:business_card_api_list'),
            reverse('reporting:mailbox_api_list'),
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, **self._auth_headers())
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertTrue(payload.get('success', True), payload)

    @patch.dict(os.environ, {
        'SALES_NOTE_READONLY_TOKEN': token,
        'SALES_NOTE_READONLY_USERNAME': 'readonly-mcp-admin',
    })
    def test_readonly_bearer_does_not_allow_writes(self):
        response = self.client.post(reverse('reporting:notes_create_api'), **self._auth_headers())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')


class ReactReportsProfileBusinessCardApiTests(TestCase):
    """Reports/profile/business card React API regression tests."""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='Hana CRM')
        self.user = make_user(
            'react-api-user',
            password='TestPass123!',
            company=self.company,
            can_download_excel=True,
        )
        self.manager = make_user('react-api-manager', role='manager', company=self.company)
        self.other = make_user('react-api-other', company=self.company)
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
            pipeline_stage='quote',
        )

    def test_reports_api_requires_login_json(self):
        response = self.client.get(reverse('reporting:reports_summary_api'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_business_card_api_requires_login_json(self):
        response = self.client.get(reverse('reporting:business_card_api_list'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_reports_api_returns_sales_and_global_reference_metrics(self):
        today = timezone.localdate()
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            action_type='customer_meeting',
            content='분석 대상 활동',
            next_action='후속 전화',
            next_action_date=today - timedelta(days=1),
        )
        asset = CustomerAsset.objects.create(
            company=self.customer_company,
            department=self.department,
            primary_followup=self.followup,
            asset_name='LC 장비',
            status='active',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=self.followup,
            case_type='service',
            status='received',
            priority='urgent',
            received_date=today,
            due_date=today - timedelta(days=1),
            created_by=self.user,
        )
        CalibrationRecord.objects.create(
            asset=asset,
            followup=self.followup,
            calibration_date=today,
            next_due_date=today + timedelta(days=10),
            result='pass',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:reports_summary_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['metrics']['totalHistories'], 1)
        self.assertEqual(payload['metrics']['overdueFollowups'], 1)
        self.assertEqual(payload['metrics']['activePipeline'], 1)
        self.assertEqual(payload['metrics']['totalAssets'], 1)
        self.assertEqual(payload['metrics']['openServiceAssets'], 1)
        self.assertEqual(payload['metrics']['overdueServiceAssets'], 1)
        self.assertEqual(payload['metrics']['dueCalibrationAssets'], 1)
        self.assertFalse(payload['scope']['canExport'])

    def test_reports_api_returns_customer_operations_with_structured_payment_split(self):
        today = timezone.localdate()
        normal_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=normal_schedule,
            item_name='일반 납품 품목',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1100,
        )
        prepayment = Prepayment.objects.create(
            customer=self.followup,
            company=self.customer_company,
            amount=5000,
            balance=3900,
            payment_date=today,
            created_by=self.user,
        )
        prepaid_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
            use_prepayment=True,
            prepayment=prepayment,
            prepayment_amount=1100,
        )
        prepaid_item = DeliveryItem.objects.create(
            schedule=prepaid_schedule,
            item_name='선결제 차감 품목',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1100,
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=prepaid_schedule,
            schedule_item=prepaid_item,
            product_name='선결제 차감 품목',
            quantity=1,
            amount=1100,
            remaining_balance=3900,
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(12, 0),
            activity_type='quote',
            status='completed',
        )
        Quote.objects.create(
            quote_number='Q-REPORT-001',
            schedule=quote_schedule,
            followup=self.followup,
            user=self.user,
            valid_until=today + timedelta(days=30),
            subtotal=2000,
            stage='sent',
        )
        asset = CustomerAsset.objects.create(
            company=self.customer_company,
            department=self.department,
            primary_followup=self.followup,
            asset_name='서비스 장비',
            status='active',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=self.followup,
            case_type='service',
            status='in_progress',
            received_date=today,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:reports_summary_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        operations = payload['customerOperations']
        row = next(item for item in operations['rows'] if item['id'] == self.followup.id)
        self.assertEqual(row['deliveryCount'], 2)
        self.assertEqual(row['normalDeliveryCount'], 1)
        self.assertEqual(row['prepaymentDeliveryCount'], 1)
        self.assertEqual(row['prepaymentUsedAmount'], 1100)
        self.assertEqual(row['quoteCount'], 1)
        self.assertEqual(row['serviceCount'], 1)
        self.assertEqual(row['openServiceCount'], 1)
        self.assertEqual(row['prepaymentCount'], 1)
        self.assertEqual(row['prepaymentBalance'], 3900)
        self.assertIn('prepayment', {item['paymentSource'] for item in row['recentDeliveryItems']})
        self.assertIn('normal', {item['paymentSource'] for item in row['recentDeliveryItems']})
        self.assertIn('선결제 차감 납품', {item['paymentStatusLabel'] for item in row['recentDeliveryItems']})
        self.assertIn('일반 납품', {item['paymentStatusLabel'] for item in row['recentDeliveryItems']})
        self.assertTrue(row['drilldown']['contacts'])
        self.assertTrue(row['drilldown']['deliveries'])
        self.assertTrue(row['drilldown']['quotes'])
        self.assertTrue(row['drilldown']['prepayments'])
        self.assertIn('links', row)
        self.assertEqual(row['links']['prepayments'], f'/prepayments/account/{self.department.id}/')
        self.assertEqual(operations['metrics']['prepaymentDeliveryCount'], 1)
        self.assertEqual(operations['metrics']['normalDeliveryCount'], 1)
        comparison = payload['comparison']['customerOperations']
        self.assertIn('deliveryCount', comparison['deltas'])
        self.assertIn('dateFrom', comparison)

    def test_common_account_ledger_feeds_reports_customer_detail_and_ai(self):
        from ai_chat.services import gather_prepayment_data, gather_quote_delivery_data
        from reporting.account_ledger import account_operational_ledger_for_followups

        today = timezone.localdate()
        create_account_ledger_fixture(
            self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            today=today,
            prefix='ledgercommon',
        )
        shared_followups = FollowUp.objects.filter(user=self.user, department=self.department)
        service_ledger = account_operational_ledger_for_followups(
            shared_followups,
            [self.user],
            actor=self.user,
            record_limit=None,
        )
        service_metrics = service_ledger['metrics']
        self.assertEqual(service_metrics['deliveryRecords'], 2)
        self.assertEqual(service_metrics['deliveryAmount'], 90000)
        self.assertEqual(service_metrics['prepaymentDeliveryRecords'], 1)
        self.assertEqual(service_metrics['prepaymentUsedAmount'], 60000)
        self.assertEqual(service_metrics['quoteRecords'], 1)
        self.assertEqual(service_metrics['quoteAmount'], 110000)
        self.assertEqual(service_metrics['prepaymentRecords'], 1)
        self.assertEqual(service_metrics['prepaymentBalance'], 40000)

        self.client.force_login(self.user)
        reports_response = self.client.get(reverse('reporting:reports_summary_api'), {
            'date_from': (today - timedelta(days=30)).isoformat(),
            'date_to': today.isoformat(),
        })
        self.assertEqual(reports_response.status_code, 200)
        reports_row = next(
            row for row in reports_response.json()['customerOperations']['rows']
            if row['id'] == self.department.id
        )
        self.assertEqual(reports_row['deliveryCount'], service_metrics['deliveryRecords'])
        self.assertEqual(reports_row['deliveryAmount'], service_metrics['deliveryAmount'])
        self.assertEqual(reports_row['prepaymentDeliveryCount'], service_metrics['prepaymentDeliveryRecords'])
        self.assertEqual(reports_row['prepaymentUsedAmount'], service_metrics['prepaymentUsedAmount'])
        self.assertEqual(reports_row['quoteCount'], service_metrics['quoteRecords'])
        self.assertEqual(reports_row['quoteAmount'], service_metrics['quoteAmount'])
        self.assertEqual(reports_row['prepaymentCount'], service_metrics['prepaymentRecords'])
        self.assertEqual(reports_row['prepaymentBalance'], service_metrics['prepaymentBalance'])

        account_response = self.client.get(reverse('reporting:account_detail_summary_api', args=[self.department.id]))
        self.assertEqual(account_response.status_code, 200)
        account_metrics = account_response.json()['operationalRecords']['metrics']
        self.assertEqual(account_metrics['deliveryRecords'], service_metrics['deliveryRecords'])
        self.assertEqual(account_metrics['quoteRecords'], service_metrics['quoteRecords'])
        self.assertEqual(account_metrics['prepaymentRecords'], service_metrics['prepaymentRecords'])
        self.assertEqual(account_metrics['prepaymentUsedAmount'], service_metrics['prepaymentUsedAmount'])

        ai_quote_delivery = gather_quote_delivery_data(self.department, self.user)
        self.assertEqual(ai_quote_delivery['summary']['total_deliveries'], service_metrics['deliveryRecords'])
        self.assertEqual(ai_quote_delivery['summary']['total_delivery_amount'], service_metrics['deliveryAmount'])
        self.assertEqual(ai_quote_delivery['summary']['total_quotes'], service_metrics['quoteRecords'])
        self.assertEqual(ai_quote_delivery['summary']['total_quote_amount'], service_metrics['quoteAmount'])
        self.assertIn('common_account_ledger', {row['ledgerSource'] for row in ai_quote_delivery['deliveries']})

        ai_prepayments = gather_prepayment_data(shared_followups)
        self.assertEqual(ai_prepayments['summary']['total_count'], service_metrics['prepaymentRecords'])
        self.assertEqual(ai_prepayments['summary']['total_remaining_balance'], service_metrics['prepaymentBalance'])

    def test_reports_api_groups_customer_operations_by_department_account(self):
        today = timezone.localdate()
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='이담당',
            pipeline_stage='contact',
        )
        first_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=first_schedule,
            item_name='첫 담당자 납품',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1000,
        )
        second_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=sibling,
            visit_date=today,
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=second_schedule,
            item_name='같은 부서 납품',
            quantity=1,
            unit='EA',
            unit_price=2000,
            total_price=2000,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:reports_summary_api'))

        self.assertEqual(response.status_code, 200)
        operations = response.json()['customerOperations']
        row = next(item for item in operations['rows'] if item['id'] == self.department.id)
        self.assertEqual(row['href'], f'/accounts/{self.department.id}/')
        self.assertEqual(row['customer'], '연구실 A')
        self.assertEqual(row['contactCount'], 2)
        self.assertIn('김고객', row['contactPreview'])
        self.assertIn('이담당', row['contactPreview'])
        self.assertEqual(row['deliveryCount'], 2)
        self.assertEqual(row['normalDeliveryCount'], 2)
        self.assertEqual(operations['metrics']['totalCustomers'], 1)

    def test_reports_api_returns_data_quality_cleanup_candidates(self):
        compact_department = Department.objects.create(
            company=self.customer_company,
            name='연구실A',
            created_by=self.user,
        )
        bracket_lab_department = Department.objects.create(
            company=self.customer_company,
            name='연구실 A (Lab)',
            created_by=self.user,
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=compact_department,
            customer_name='유사계정 담당자',
            email='similar@example.com',
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=bracket_lab_department,
            customer_name='괄호표기 담당자',
            email='bracket-lab@example.com',
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='중복담당자 1',
            email='dup@example.com',
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='중복담당자 2',
            email='dup@example.com',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:reports_summary_api'))

        self.assertEqual(response.status_code, 200)
        data_quality = response.json()['dataQuality']
        self.assertGreaterEqual(data_quality['metrics']['duplicateAccountGroups'], 1)
        self.assertGreaterEqual(data_quality['metrics']['duplicateContactGroups'], 1)
        account_text = json.dumps(data_quality['duplicateAccounts'], ensure_ascii=False)
        contact_text = json.dumps(data_quality['duplicateContacts'], ensure_ascii=False)
        self.assertIn('연구실 A', account_text)
        self.assertIn('연구실A', account_text)
        self.assertIn('연구실 A (Lab)', account_text)
        self.assertIn('dup@example.com', contact_text)
        duplicate_account = next(
            group for group in data_quality['duplicateAccounts']
            if (
                '연구실 A' in group['departmentNames']
                and '연구실A' in group['departmentNames']
                and '연구실 A (Lab)' in group['departmentNames']
            )
        )
        self.assertEqual(duplicate_account['riskLabel'], '검토 필요')
        self.assertIn('suggestedAction', duplicate_account)
        self.assertEqual(duplicate_account['reviewStatus'], 'new')
        self.assertIn('candidateKey', duplicate_account)
        self.assertEqual(duplicate_account['candidateType'], 'duplicate_account')
        self.assertGreaterEqual(duplicate_account['recordCount'], 0)
        self.assertTrue(duplicate_account['departments'])
        self.assertTrue(all('accountHref' in department for department in duplicate_account['departments']))
        sorted_department_ids = sorted(duplicate_account['departmentIds'])
        self.assertEqual(
            duplicate_account['cleanupPreviewHref'],
            f'/accounts/{sorted_department_ids[0]}/cleanup-preview/?target={sorted_department_ids[1]}',
        )
        for department in duplicate_account['departments']:
            target_id = next(
                department_id for department_id in sorted_department_ids
                if department_id != department['id']
            )
            self.assertEqual(
                department['cleanupPreviewHref'],
                f'/accounts/{department["id"]}/cleanup-preview/?target={target_id}',
            )
        self.assertTrue(all('contacts' in department for department in duplicate_account['departments']))
        duplicate_contact = next(
            group for group in data_quality['duplicateContacts']
            if group['identity'] == 'dup@example.com'
        )
        self.assertEqual(duplicate_contact['riskLabel'], '검토 필요')
        self.assertEqual(duplicate_contact['candidateType'], 'duplicate_contact')
        self.assertIn('candidateKey', duplicate_contact)
        self.assertIn('suggestedAction', duplicate_contact)
        self.assertGreaterEqual(duplicate_contact['recordCount'], 0)
        self.assertTrue(duplicate_contact['contactIds'])
        self.assertTrue(all('recordSummary' in contact for contact in duplicate_contact['contacts']))
        operations_row = next(
            item for item in response.json()['customerOperations']['rows']
            if item['id'] == self.department.id
        )
        self.assertGreaterEqual(operations_row['cleanupCandidateCount'], 1)
        self.assertIn('duplicate_account', operations_row['cleanupTypes'])
        self.assertTrue(operations_row['cleanupPreviewHref'])

    def test_account_cleanup_decision_api_holds_dismisses_and_restores_candidate(self):
        compact_department = Department.objects.create(
            company=self.customer_company,
            name='연구실A',
            created_by=self.user,
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=compact_department,
            customer_name='유사계정 담당자',
            email='decision-similar@example.com',
        )
        self.client.force_login(self.user)
        candidate = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']['duplicateAccounts'][0]

        hold_response = self.client.post(
            reverse('reporting:account_cleanup_decision_api'),
            data=json.dumps({
                'candidateType': candidate['candidateType'],
                'candidateKey': candidate['candidateKey'],
                'decision': 'hold',
                'label': '보류 테스트',
                'sourceDepartmentId': candidate['sourceDepartmentId'],
                'targetDepartmentId': candidate['targetDepartmentId'],
            }),
            content_type='application/json',
        )

        self.assertEqual(hold_response.status_code, 200)
        decision = AccountCleanupDecision.objects.get(candidate_key=candidate['candidateKey'])
        self.assertEqual(decision.decision, AccountCleanupDecision.DECISION_HOLD)
        held_quality = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']
        held_candidate = next(item for item in held_quality['duplicateAccounts'] if item['candidateKey'] == candidate['candidateKey'])
        self.assertEqual(held_candidate['reviewStatus'], 'hold')
        self.assertGreaterEqual(held_quality['metrics']['heldCandidateCount'], 1)
        self.assertTrue(any(item['kind'] == 'decision' for item in held_quality['history']))

        dismiss_response = self.client.post(
            reverse('reporting:account_cleanup_decision_api'),
            data=json.dumps({
                'candidateType': candidate['candidateType'],
                'candidateKey': candidate['candidateKey'],
                'decision': 'dismissed',
                'sourceDepartmentId': candidate['sourceDepartmentId'],
                'targetDepartmentId': candidate['targetDepartmentId'],
            }),
            content_type='application/json',
        )

        self.assertEqual(dismiss_response.status_code, 200)
        dismissed_quality = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']
        self.assertFalse(any(item['candidateKey'] == candidate['candidateKey'] for item in dismissed_quality['duplicateAccounts']))
        self.assertGreaterEqual(dismissed_quality['metrics']['dismissedCandidateCount'], 1)

        restore_response = self.client.post(
            reverse('reporting:account_cleanup_decision_api'),
            data=json.dumps({
                'candidateType': candidate['candidateType'],
                'candidateKey': candidate['candidateKey'],
                'decision': 'active',
            }),
            content_type='application/json',
        )

        self.assertEqual(restore_response.status_code, 200)
        self.assertFalse(AccountCleanupDecision.objects.filter(candidate_key=candidate['candidateKey']).exists())
        restored_quality = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']
        self.assertTrue(any(item['candidateKey'] == candidate['candidateKey'] for item in restored_quality['duplicateAccounts']))

    def test_data_quality_quick_assign_placeholder_contact_updates_account_and_audit_log(self):
        placeholder_company = Company.objects.create(name='업체 미지정', created_by=self.user)
        placeholder_department = Department.objects.create(
            company=placeholder_company,
            name='부서 미지정',
            created_by=self.user,
        )
        placeholder_contact = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=placeholder_company,
            department=placeholder_department,
            customer_name='미지정 담당자',
            email='unassigned@example.com',
        )
        self.client.force_login(self.user)

        quality = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']
        self.assertTrue(any(item['id'] == placeholder_contact.id for item in quality['contactsWithoutDepartment']))
        self.assertTrue(any(item['id'] == placeholder_contact.id for item in quality['contactsWithoutCompany']))

        assign_response = self.client.post(
            reverse('reporting:data_quality_contact_assign_account_api', args=[placeholder_contact.id]),
            data=json.dumps({'departmentId': self.department.id}),
            content_type='application/json',
        )

        self.assertEqual(assign_response.status_code, 200)
        placeholder_contact.refresh_from_db()
        self.assertEqual(placeholder_contact.company_id, self.customer_company.id)
        self.assertEqual(placeholder_contact.department_id, self.department.id)
        audit_log = AccountCleanupAuditLog.objects.get(action_type=AccountCleanupAuditLog.ACTION_CONTACT_ACCOUNT_ASSIGN)
        self.assertEqual(audit_log.target_department_id, self.department.id)
        self.assertEqual(audit_log.source_followup_id, placeholder_contact.id)
        refreshed_quality = self.client.get(reverse('reporting:reports_summary_api')).json()['dataQuality']
        self.assertFalse(any(item['id'] == placeholder_contact.id for item in refreshed_quality['contactsWithoutDepartment']))
        self.assertFalse(any(item['id'] == placeholder_contact.id for item in refreshed_quality['contactsWithoutCompany']))

    def test_reports_api_filters_account_rows_and_prepayment_balance(self):
        today = timezone.localdate()
        other_department = Department.objects.create(
            company=self.customer_company,
            name='잔액 연구실',
            created_by=self.user,
        )
        other_followup = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=other_department,
            customer_name='잔액담당',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='필터 납품',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1000,
        )
        previous_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today - timedelta(days=1),
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=previous_schedule,
            item_name='이전 납품',
            quantity=1,
            unit='EA',
            unit_price=500,
            total_price=500,
        )
        Prepayment.objects.create(
            department=other_department,
            customer=other_followup,
            company=self.customer_company,
            amount=7000,
            balance=7000,
            payment_date=today,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        with_delivery = self.client.get(reverse('reporting:reports_summary_api'), {
            'date_from': today.isoformat(),
            'date_to': today.isoformat(),
            'q': '연구실 A',
            'delivery_filter': 'with',
        })
        self.assertEqual(with_delivery.status_code, 200)
        payload = with_delivery.json()
        self.assertEqual(payload['filters']['query'], '연구실 A')
        self.assertEqual(payload['filters']['deliveryFilter'], 'with')
        self.assertEqual(payload['customerOperations']['metrics']['deliveryCount'], 1)
        self.assertEqual(payload['comparison']['customerOperations']['metrics']['deliveryCount'], 1)
        self.assertEqual(payload['comparison']['customerOperations']['deltas']['deliveryAmount'], 550)

        balance_without_delivery = self.client.get(reverse('reporting:reports_summary_api'), {
            'date_from': today.isoformat(),
            'date_to': today.isoformat(),
            'department_id': str(other_department.id),
            'delivery_filter': 'without',
            'prepayment_balance_filter': 'with',
        })
        self.assertEqual(balance_without_delivery.status_code, 200)
        rows = balance_without_delivery.json()['customerOperations']['rows']
        self.assertEqual([row['id'] for row in rows], [other_department.id])
        self.assertEqual(rows[0]['prepaymentBalance'], 7000)
        self.assertEqual(rows[0]['deliveryCount'], 0)

    def test_account_cleanup_preview_api_returns_source_and_target_impact(self):
        today = timezone.localdate()
        target_department = Department.objects.create(
            company=self.customer_company,
            name='연구실 A-2',
            created_by=self.user,
        )
        target_followup = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=target_department,
            customer_name='대상 담당자',
            email='target@example.com',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='영향 납품',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1000,
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(11, 0),
            activity_type='quote',
            status='completed',
        )
        Quote.objects.create(
            quote_number='CLEAN-PREVIEW-1',
            schedule=quote_schedule,
            followup=self.followup,
            user=self.user,
            valid_until=today + timedelta(days=30),
            subtotal=1000,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            action_type='customer_meeting',
            content='정리 영향 노트',
        )
        prepayment = Prepayment.objects.create(
            customer=self.followup,
            company=self.customer_company,
            amount=5000,
            balance=3000,
            payment_date=today,
            created_by=self.user,
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=delivery_schedule,
            product_name='차감 품목',
            quantity=1,
            amount=2000,
            remaining_balance=3000,
        )
        asset = CustomerAsset.objects.create(
            company=self.customer_company,
            department=self.department,
            primary_followup=self.followup,
            asset_name='영향 장비',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=self.followup,
            case_type='service',
            status='received',
            received_date=today,
            created_by=self.user,
        )
        CalibrationRecord.objects.create(
            asset=asset,
            followup=self.followup,
            calibration_date=today,
            next_due_date=today + timedelta(days=7),
            created_by=self.user,
        )
        Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target_followup,
            visit_date=today,
            visit_time=time(12, 0),
            activity_type='delivery',
            status='completed',
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:account_cleanup_preview_api', args=[self.department.id]),
            {'target': target_department.id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['mode'], 'compare')
        self.assertEqual(payload['sourceAccount']['id'], self.department.id)
        self.assertEqual(payload['targetAccount']['id'], target_department.id)
        self.assertEqual(payload['sourceAccount']['metrics']['contactCount'], 1)
        self.assertEqual(payload['sourceAccount']['metrics']['deliveryCount'], 1)
        self.assertEqual(payload['sourceAccount']['metrics']['quoteCount'], 1)
        self.assertEqual(payload['sourceAccount']['metrics']['prepaymentBalance'], 3000)
        self.assertEqual(payload['sourceAccount']['metrics']['prepaymentUsedAmount'], 2000)
        self.assertEqual(payload['sourceAccount']['metrics']['assetCount'], 1)
        self.assertEqual(payload['sourceAccount']['metrics']['serviceCaseCount'], 1)
        self.assertEqual(payload['sourceAccount']['metrics']['calibrationCount'], 1)
        self.assertEqual(payload['combined']['metrics']['contactCount'], 2)
        self.assertEqual(payload['combined']['metrics']['deliveryCount'], 2)
        self.assertFalse(payload['mergeReadiness']['canMerge'])
        self.assertEqual(payload['mergeReadiness']['status'], 'review')
        self.assertEqual(payload['mergeReadiness']['recommendedSurvivingAccount']['id'], target_department.id)
        self.assertIn(
            f'/reporting/api/accounts/{self.department.id}/cleanup-preview/?',
            payload['links']['previewExportJson'],
        )
        checklist = {item['key']: item for item in payload['mergeReadiness']['items']}
        self.assertEqual(checklist['same_company']['status'], 'pass')
        self.assertEqual(checklist['prepayment_balance']['status'], 'review')
        self.assertEqual(checklist['prepayment_balance']['amount'], 3000)
        self.assertEqual(checklist['prepayment_usage']['status'], 'review')
        self.assertEqual(checklist['prepayment_usage']['amount'], 2000)
        self.assertEqual(checklist['linked_records']['status'], 'review')
        self.assertEqual(checklist['export_ready']['status'], 'pass')
        self.assertEqual(checklist['audit_log_required']['status'], 'pass')
        self.assertIn('읽기 전용', ' '.join(payload['warnings']))

        export_response = self.client.get(
            reverse('reporting:account_cleanup_preview_api', args=[self.department.id]),
            {'target': target_department.id, 'export': '1'},
        )
        self.assertEqual(export_response.status_code, 200)
        self.assertIn('attachment;', export_response['Content-Disposition'])
        self.assertIn('account-cleanup-preview', export_response['Content-Disposition'])
        export_payload = json.loads(export_response.content.decode('utf-8'))
        self.assertEqual(export_payload['mergeReadiness']['status'], 'review')
        self.assertEqual(export_payload['targetAccount']['id'], target_department.id)

    def test_account_cleanup_preview_api_requires_login_and_blocks_inaccessible_target(self):
        other_department = Department.objects.create(
            company=self.customer_company,
            name='다른 담당 계정',
            created_by=self.other,
        )
        FollowUp.objects.create(
            user=self.other,
            user_company=self.company,
            company=self.customer_company,
            department=other_department,
            customer_name='다른 담당자',
        )

        unauthenticated = self.client.get(reverse('reporting:account_cleanup_preview_api', args=[self.department.id]))
        self.assertEqual(unauthenticated.status_code, 401)

        self.client.force_login(self.user)
        blocked = self.client.get(
            reverse('reporting:account_cleanup_preview_api', args=[self.department.id]),
            {'target': other_department.id},
        )
        self.assertEqual(blocked.status_code, 403)

    def test_account_cleanup_department_merge_api_dry_run_and_admin_execute(self):
        target_department = Department.objects.create(
            company=self.customer_company,
            name='연구실 A 통합',
            created_by=self.user,
        )
        FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=target_department,
            customer_name='대상 담당자',
        )
        asset = CustomerAsset.objects.create(
            company=self.customer_company,
            department=self.department,
            primary_followup=self.followup,
            asset_name='병합 장비',
            created_by=self.user,
        )
        memo = DepartmentMemo.objects.create(
            department=self.department,
            content='원본 부서 메모',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        url = reverse('reporting:account_cleanup_department_merge_api', args=[self.department.id])
        dry_run = self.client.post(
            url,
            data=json.dumps({'targetDepartmentId': target_department.id, 'mode': 'dry_run'}),
            content_type='application/json',
        )

        self.assertEqual(dry_run.status_code, 200)
        dry_payload = dry_run.json()
        self.assertTrue(dry_payload['dryRun'])
        self.assertFalse(dry_payload['executed'])
        transfers = {item['key']: item for item in dry_payload['plan']['transfers']}
        self.assertEqual(transfers['followups']['count'], 1)
        self.assertEqual(transfers['assets']['count'], 1)
        self.assertEqual(transfers['departmentMemos']['count'], 1)
        self.followup.refresh_from_db()
        asset.refresh_from_db()
        memo.refresh_from_db()
        self.assertEqual(self.followup.department_id, self.department.id)
        self.assertEqual(asset.department_id, self.department.id)
        self.assertEqual(memo.department_id, self.department.id)
        self.assertEqual(AccountCleanupAuditLog.objects.count(), 0)

        blocked = self.client.post(
            url,
            data=json.dumps({
                'targetDepartmentId': target_department.id,
                'mode': 'execute',
                'confirmationText': dry_payload['requiredConfirmationText'],
            }),
            content_type='application/json',
        )
        self.assertEqual(blocked.status_code, 403)

        admin_user = make_user('cleanup-admin', role='admin', company=self.company)
        self.client.force_login(admin_user)
        wrong_confirmation = self.client.post(
            url,
            data=json.dumps({
                'targetDepartmentId': target_department.id,
                'mode': 'execute',
                'confirmationText': 'WRONG',
            }),
            content_type='application/json',
        )
        self.assertEqual(wrong_confirmation.status_code, 400)
        self.assertEqual(
            wrong_confirmation.json()['requiredConfirmationText'],
            dry_payload['requiredConfirmationText'],
        )

        executed = self.client.post(
            url,
            data=json.dumps({
                'targetDepartmentId': target_department.id,
                'mode': 'execute',
                'confirmationText': dry_payload['requiredConfirmationText'],
            }),
            content_type='application/json',
        )

        self.assertEqual(executed.status_code, 200)
        executed_payload = executed.json()
        self.assertTrue(executed_payload['executed'])
        self.assertEqual(executed_payload['result']['followupsUpdated'], 1)
        self.assertEqual(executed_payload['result']['assetsUpdated'], 1)
        self.assertEqual(executed_payload['result']['departmentMemosMoved'], 1)
        self.followup.refresh_from_db()
        asset.refresh_from_db()
        memo.refresh_from_db()
        self.assertEqual(self.followup.department_id, target_department.id)
        self.assertEqual(asset.department_id, target_department.id)
        self.assertEqual(memo.department_id, target_department.id)
        self.assertTrue(DepartmentMemo.objects.filter(department=self.department, content__contains='정리 보존').exists())
        self.assertTrue(DepartmentMemo.objects.filter(department=target_department, content__contains='원본').exists())
        audit_log = AccountCleanupAuditLog.objects.get()
        self.assertEqual(audit_log.action_type, AccountCleanupAuditLog.ACTION_DEPARTMENT_MERGE)
        self.assertEqual(audit_log.mode, AccountCleanupAuditLog.MODE_EXECUTE)
        self.assertEqual(audit_log.result['status'], 'completed')

    def test_account_cleanup_contact_merge_api_dry_run_and_admin_execute(self):
        today = timezone.localdate()
        target_followup = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='통합 대상 담당자',
            email='target-contact@example.com',
        )
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        quote = Quote.objects.create(
            quote_number='CONTACT-MERGE-1',
            schedule=schedule,
            followup=self.followup,
            user=self.user,
            valid_until=today + timedelta(days=30),
            subtotal=1000,
        )
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            action_type='customer_meeting',
            content='담당자 병합 노트',
        )
        prepayment = Prepayment.objects.create(
            customer=self.followup,
            company=self.customer_company,
            amount=5000,
            balance=3000,
            payment_date=today,
            created_by=self.user,
        )
        asset = CustomerAsset.objects.create(
            company=self.customer_company,
            department=self.department,
            primary_followup=self.followup,
            asset_name='담당자 병합 장비',
            created_by=self.user,
        )
        service_case = ServiceCase.objects.create(
            asset=asset,
            followup=self.followup,
            case_type='service',
            status='received',
            received_date=today,
            created_by=self.user,
        )
        calibration = CalibrationRecord.objects.create(
            asset=asset,
            followup=self.followup,
            calibration_date=today,
            next_due_date=today + timedelta(days=7),
            created_by=self.user,
        )
        self.client.force_login(self.user)

        url = reverse('reporting:account_cleanup_contact_merge_api', args=[self.followup.id])
        dry_run = self.client.post(
            url,
            data=json.dumps({'targetFollowupId': target_followup.id, 'mode': 'dry_run'}),
            content_type='application/json',
        )

        self.assertEqual(dry_run.status_code, 200)
        dry_payload = dry_run.json()
        self.assertTrue(dry_payload['dryRun'])
        transfers = {item['key']: item for item in dry_payload['plan']['transfers']}
        self.assertEqual(transfers['histories']['count'], 1)
        self.assertEqual(transfers['schedules']['count'], 1)
        self.assertEqual(transfers['quotes']['count'], 1)
        self.assertEqual(transfers['prepayments']['count'], 1)
        self.assertEqual(transfers['serviceCases']['count'], 1)
        self.assertEqual(transfers['calibrations']['count'], 1)
        self.assertEqual(transfers['primaryAssets']['count'], 1)
        schedule.refresh_from_db()
        self.assertEqual(schedule.followup_id, self.followup.id)

        admin_user = make_user('cleanup-admin-contact', role='admin', company=self.company)
        self.client.force_login(admin_user)
        executed = self.client.post(
            url,
            data=json.dumps({
                'targetFollowupId': target_followup.id,
                'mode': 'execute',
                'confirmationText': dry_payload['requiredConfirmationText'],
            }),
            content_type='application/json',
        )

        self.assertEqual(executed.status_code, 200)
        executed_payload = executed.json()
        self.assertTrue(executed_payload['executed'])
        self.assertEqual(executed_payload['result']['historiesUpdated'], 1)
        self.assertEqual(executed_payload['result']['schedulesUpdated'], 1)
        self.assertEqual(executed_payload['result']['quotesUpdated'], 1)
        self.assertEqual(executed_payload['result']['prepaymentsUpdated'], 1)
        self.assertEqual(executed_payload['result']['serviceCasesUpdated'], 1)
        self.assertEqual(executed_payload['result']['calibrationsUpdated'], 1)
        self.assertEqual(executed_payload['result']['primaryAssetsUpdated'], 1)
        for obj in [schedule, quote, history, prepayment, asset, service_case, calibration]:
            obj.refresh_from_db()
        self.followup.refresh_from_db()
        self.assertEqual(schedule.followup_id, target_followup.id)
        self.assertEqual(quote.followup_id, target_followup.id)
        self.assertEqual(history.followup_id, target_followup.id)
        self.assertEqual(prepayment.customer_id, target_followup.id)
        self.assertEqual(asset.primary_followup_id, target_followup.id)
        self.assertEqual(service_case.followup_id, target_followup.id)
        self.assertEqual(calibration.followup_id, target_followup.id)
        self.assertEqual(self.followup.status, 'paused')
        self.assertIn('정리 보존', self.followup.notes)
        audit_log = AccountCleanupAuditLog.objects.get()
        self.assertEqual(audit_log.action_type, AccountCleanupAuditLog.ACTION_CONTACT_MERGE)
        self.assertEqual(audit_log.source_followup_id, self.followup.id)
        self.assertEqual(audit_log.target_followup_id, target_followup.id)

    def test_account_cleanup_account_search_api_finds_by_company_department_pi_contact_and_email(self):
        self.followup.manager = '김PI'
        self.followup.email = 'pi-search@example.com'
        self.followup.save(update_fields=['manager', 'email'])
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            company=self.customer_company,
            department=self.department,
            customer_name='검색 담당자',
            manager='공동PI',
        )
        other_department = Department.objects.create(
            company=self.customer_company,
            name='숨겨진 연구실',
            created_by=self.other,
        )
        FollowUp.objects.create(
            user=self.other,
            user_company=self.company,
            company=self.customer_company,
            department=other_department,
            customer_name='숨겨진 담당자',
            manager='김PI',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:account_cleanup_account_search_api'), {'q': '김PI'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        result_ids = {item['id'] for item in payload['results']}
        self.assertIn(self.department.id, result_ids)
        self.assertNotIn(other_department.id, result_ids)
        result = next(item for item in payload['results'] if item['id'] == self.department.id)
        self.assertEqual(result['label'], '고객사 A · 연구실 A')
        self.assertIn('김PI', result['piPreview'])
        self.assertIn('김고객', result['contactPreview'])
        self.assertIn('검색 담당자', result['contactPreview'])
        self.assertEqual(result['previewHref'], f'/accounts/{self.department.id}/cleanup-preview/')

        department_response = self.client.get(reverse('reporting:account_cleanup_account_search_api'), {'q': '연구실 A'})
        self.assertEqual(department_response.status_code, 200)
        self.assertIn(self.department.id, {item['id'] for item in department_response.json()['results']})

        email_response = self.client.get(reverse('reporting:account_cleanup_account_search_api'), {'q': 'pi-search@example.com'})
        self.assertEqual(email_response.status_code, 200)
        self.assertIn(self.department.id, {item['id'] for item in email_response.json()['results']})

        source_excluded = self.client.get(
            reverse('reporting:account_cleanup_account_search_api'),
            {'q': '김PI', 'source': self.department.id},
        )
        self.assertNotIn(self.department.id, {item['id'] for item in source_excluded.json()['results']})

        self.client.logout()
        unauthenticated = self.client.get(reverse('reporting:account_cleanup_account_search_api'), {'q': '김PI'})
        self.assertEqual(unauthenticated.status_code, 401)

    def test_reports_api_manager_can_filter_company_salesperson(self):
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            action_type='customer_meeting',
            content='담당자 활동',
        )
        History.objects.create(
            user=self.other,
            company=self.company,
            action_type='phone_call',
            content='다른 담당자 활동',
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:reports_summary_api'), {'user_id': self.user.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['metrics']['totalHistories'], 1)
        self.assertTrue(payload['scope']['canFilterUsers'])
        self.assertTrue(payload['scope']['canExport'])
        self.assertEqual(payload['filters']['selectedUserId'], self.user.id)
        self.assertIn('customer-operations.xlsx', payload['links']['customerOperationsXlsx'])
        self.assertIn(f'user_id={self.user.id}', payload['links']['customerOperationsXlsx'])

    def test_reports_customer_operations_xlsx_export_downloads_table(self):
        from io import BytesIO
        from openpyxl import load_workbook

        today = timezone.localdate()
        normal_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=normal_schedule,
            item_name='현황 일반 품목',
            quantity=1,
            unit='EA',
            unit_price=1000,
            total_price=1000,
        )
        prepayment = Prepayment.objects.create(
            customer=self.followup,
            company=self.customer_company,
            amount=5000,
            balance=2600,
            payment_date=today,
            created_by=self.user,
        )
        prepaid_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
            use_prepayment=True,
            prepayment=prepayment,
            prepayment_amount=2400,
        )
        prepaid_item = DeliveryItem.objects.create(
            schedule=prepaid_schedule,
            item_name='현황 선결제 품목',
            quantity=2,
            unit='EA',
            unit_price=1200,
            total_price=2400,
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=prepaid_schedule,
            schedule_item=prepaid_item,
            product_name='현황 선결제 품목',
            quantity=2,
            amount=2400,
            remaining_balance=2600,
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=self.followup,
            visit_date=today,
            visit_time=time(12, 0),
            activity_type='quote',
            status='completed',
        )
        Quote.objects.create(
            quote_number='Q-OPS-XLSX',
            schedule=quote_schedule,
            followup=self.followup,
            user=self.user,
            quote_date=today,
            valid_until=today + timedelta(days=30),
            subtotal=3000,
            stage='sent',
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:reports_customer_operations_xlsx'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        workbook = load_workbook(BytesIO(response.content), data_only=True)
        sheet = workbook['계정별 운영 현황']
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], '계정')
        row = next(item for item in rows[1:] if item[0] == '연구실 A')
        self.assertEqual(row[1], '고객사 A')
        self.assertEqual(row[3], 1)
        self.assertEqual(row[9], 2)
        self.assertEqual(row[10], 3740)
        self.assertEqual(row[11], 1)
        self.assertEqual(row[12], 2400)
        self.assertEqual(row[13], 1)
        self.assertEqual(row[14], 1100)
        self.assertEqual(row[15], 1)
        self.assertEqual(row[16], 3300)
        self.assertEqual(row[17], 1)
        self.assertEqual(row[18], 5000)
        self.assertEqual(row[19], 2600)
        self.assertEqual(row[28], 0)
        self.assertIn('현황 선결제 품목', row[30])
        self.assertIn('/accounts/', row[31])

    def test_reports_customer_operations_xlsx_export_blocks_salesman(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:reports_customer_operations_xlsx'))

        self.assertEqual(response.status_code, 403)

    def test_profile_api_update_and_password_change(self):
        self.client.force_login(self.user)

        update_response = self.client.post(
            reverse('reporting:profile_api_update'),
            data=json.dumps({
                'username': 'react-profile-user',
                'firstName': '길동',
                'lastName': '홍',
                'email': 'profile@example.com',
            }),
            content_type='application/json',
        )
        self.assertEqual(update_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'react-profile-user')
        self.assertEqual(self.user.email, 'profile@example.com')

        password_response = self.client.post(
            reverse('reporting:profile_api_password'),
            data=json.dumps({
                'oldPassword': 'TestPass123!',
                'newPassword1': 'NewPass12345!',
                'newPassword2': 'NewPass12345!',
            }),
            content_type='application/json',
        )
        self.assertEqual(password_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass12345!'))

    def test_business_card_api_owner_scope_default_and_soft_delete(self):
        other_card = BusinessCard.objects.create(
            user=self.other,
            name='동료 명함',
            full_name='동료',
            company_name='Hana',
            email='other@example.com',
        )
        self.client.force_login(self.user)

        create_response = self.client.post(reverse('reporting:business_card_api_create'), {
            'name': '회사 명함',
            'fullName': '홍길동',
            'companyName': 'Hana',
            'email': 'sales@example.com',
            'mobile': '010-0000-0000',
            'isDefault': '1',
        })
        self.assertEqual(create_response.status_code, 200)
        card = BusinessCard.objects.get(user=self.user)
        self.assertTrue(card.is_default)
        self.assertEqual(create_response.json()['cards'][0]['id'], card.id)

        forbidden_response = self.client.post(
            reverse('reporting:business_card_api_set_default', args=[other_card.id])
        )
        self.assertEqual(forbidden_response.status_code, 404)

        delete_response = self.client.post(reverse('reporting:business_card_api_delete', args=[card.id]))
        self.assertEqual(delete_response.status_code, 200)
        card.refresh_from_db()
        self.assertFalse(card.is_active)
        self.assertEqual(delete_response.json()['cards'], [])


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

    def test_mailbox_api_lists_scheduled_mail_without_connected_provider(self):
        from datetime import timedelta

        scheduled_email = ScheduledEmail.objects.create(
            user=self.user,
            provider='gmail',
            sender_email='sales@example.com',
            to_email='customer@example.com',
            subject='연결 없이 확인할 예약메일',
            body='예약메일은 연결 상태와 별개로 목록 확인이 필요합니다.',
            body_html='<div>예약메일은 연결 상태와 별개로 목록 확인이 필요합니다.</div>',
            followup=self.followup,
            scheduled_at=timezone.now() + timedelta(hours=1),
            status='pending',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:mailbox_api_list'), {'box': 'scheduled'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['connection']['connected'])
        self.assertEqual(payload['counts']['scheduled'], 1)
        self.assertEqual(payload['emails'][0]['subject'], '연결 없이 확인할 예약메일')
        self.assertTrue(payload['emails'][0]['isScheduled'])
        self.assertEqual(payload['emails'][0]['threadHref'], f'/mailbox/scheduled/{scheduled_email.id}/')

    def test_mailbox_api_returns_scheduled_email_detail(self):
        from datetime import timedelta

        scheduled_email = ScheduledEmail.objects.create(
            user=self.user,
            provider='gmail',
            sender_email='sales@example.com',
            to_email='customer@example.com',
            subject='예약메일 상세',
            body='예약메일 상세 본문입니다.',
            body_html='<div>예약메일 상세 본문입니다.</div>',
            followup=self.followup,
            scheduled_at=timezone.now() + timedelta(hours=1),
            status='pending',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:mailbox_api_scheduled_detail', args=[scheduled_email.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['thread']['id'], f'scheduled-{scheduled_email.id}')
        self.assertEqual(payload['thread']['subject'], '예약메일 상세')
        self.assertTrue(payload['thread']['isScheduled'])
        self.assertEqual(payload['links']['mailbox'], '/mailbox/?box=scheduled')
        self.assertEqual(payload['links']['reply'], '')
        self.assertEqual(payload['emails'][0]['bodyText'], '예약메일 상세 본문입니다.')
        self.assertEqual(payload['emails'][0]['cancelHref'], reverse('reporting:mailbox_api_cancel_scheduled', args=[scheduled_email.id]))

    def test_mailbox_api_list_returns_schedule_auto_attachments_for_compose(self):
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
            document_type='transaction_statement',
            schedule=schedule,
            user=self.user,
            transaction_number='TS-CREATE-001',
            output_format='pdf',
            file=SimpleUploadedFile('statement-create.pdf', b'%PDF statement', content_type='application/pdf'),
            filename='statement-create.pdf',
            file_size=len(b'%PDF statement'),
        )
        self.addCleanup(log.file.delete, False)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:mailbox_api_list'), {
            'box': 'inbox',
            'schedule_id': str(schedule.id),
        })

        self.assertEqual(response.status_code, 200)
        create_payload = response.json()['create']
        self.assertEqual(create_payload['schedule']['id'], schedule.id)
        self.assertIn('거래명세서', create_payload['autoAttachLabel'])
        self.assertEqual(create_payload['autoAttachments'][0]['key'], f'log:{log.id}')
        self.assertEqual(create_payload['autoAttachments'][0]['documentType'], 'transaction_statement')
        self.assertFalse(create_payload['autoAttachments'][0]['willGenerate'])

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

    def test_mailbox_thread_api_strips_css_artifacts_from_display_body(self):
        self.email.body = ''
        self.email.body_html = (
            '<style>p{margin-top:0px;margin-bottom:0px;}</style>'
            '<p>안녕하십니까.</p>'
            '<p>요청하신 사업자등록증 전달드립니다.</p>'
        )
        self.email.save(update_fields=['body', 'body_html'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        email_payload = response.json()['emails'][0]
        self.assertIn('안녕하십니까.', email_payload['bodyText'])
        self.assertIn('사업자등록증', email_payload['preview'])
        self.assertNotIn('p{margin-top', email_payload['bodyText'])
        self.assertNotIn('p{margin-top', email_payload['preview'])

    def test_mailbox_thread_api_converts_html_document_stored_in_plain_body(self):
        self.email.body_html = ''
        self.email.body = (
            '<html><head><style>p{margin-top:0px;font-size:13px;}</style></head>'
            '<body>'
            '<div style="color:#111;font-family:Apple SD Gothic Neo,Malgun Gothic;font-size:10pt;">'
            '<p>안녕하십니까.</p><p>요청하신 견적서 확인 부탁드립니다.</p>'
            '</div>'
            '</body></html>'
        )
        self.email.save(update_fields=['body', 'body_html'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        email_payload = response.json()['emails'][0]
        self.assertIn('안녕하십니까.', email_payload['bodyText'])
        self.assertIn('견적서 확인', email_payload['bodyText'])
        self.assertIn('견적서 확인', email_payload['preview'])
        self.assertNotIn('<html', email_payload['bodyText'])
        self.assertNotIn('font-family', email_payload['bodyText'])
        self.assertNotIn('margin-top', email_payload['preview'])

    def test_mailbox_thread_api_converts_escaped_html_document_stored_in_plain_body(self):
        self.email.body_html = ''
        self.email.body = (
            '&lt;html&gt;&lt;head&gt;&lt;style&gt;p{font-size:13px;}&lt;/style&gt;&lt;/head&gt;'
            '&lt;body&gt;&lt;div style=&quot;color:#111;&quot;&gt;'
            '&lt;p&gt;이스케이프된 HTML 본문입니다.&lt;/p&gt;'
            '&lt;/div&gt;&lt;/body&gt;&lt;/html&gt;'
        )
        self.email.save(update_fields=['body', 'body_html'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        body_text = response.json()['emails'][0]['bodyText']
        self.assertIn('이스케이프된 HTML 본문입니다.', body_text)
        self.assertNotIn('&lt;html', body_text)
        self.assertNotIn('<html', body_text)

    def test_mailbox_thread_api_uses_sent_email_as_reply_target_when_no_customer_reply(self):
        sent_email = EmailLog.objects.create(
            email_type='sent',
            sender=self.user,
            user=self.user,
            sender_email='sales@example.com',
            recipient_email='waiting@example.com',
            subject='고객 답장 대기',
            body='고객에게 먼저 보낸 메일입니다.',
            body_html='<div>고객에게 먼저 보낸 메일입니다.</div>',
            gmail_message_id='gmail-msg-waiting-1',
            gmail_thread_id='gmail-thread-waiting-1',
            followup=self.followup,
            status='sent',
            sent_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:mailbox_api_thread', args=['gmail-thread-waiting-1']))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNone(payload['thread']['lastReceivedEmailId'])
        self.assertEqual(payload['links']['reply'], reverse('reporting:mailbox_api_reply', args=[sent_email.id]))
        self.assertEqual(payload['emails'][0]['senderEmail'], 'sales@example.com')
        self.assertEqual(payload['emails'][0]['recipientEmail'], 'waiting@example.com')

    def test_mailbox_thread_api_returns_received_attachment_download_links(self):
        import base64

        self.email.attachments_info = [
            {
                'filename': 'business-license.pdf',
                'size': 22,
                'mimetype': 'application/pdf',
                'source': 'imap',
                'contentBase64': base64.b64encode(b'%PDF business license').decode('ascii'),
            }
        ]
        self.email.save(update_fields=['attachments_info'])
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
        )

        self.assertEqual(response.status_code, 200)
        attachment = response.json()['emails'][0]['attachments'][0]
        self.assertEqual(attachment['filename'], 'business-license.pdf')
        self.assertEqual(attachment['downloadHref'], reverse('reporting:mailbox_api_attachment_download', args=[self.email.id, 0]))

        download_response = self.client.get(attachment['downloadHref'])
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.content, b'%PDF business license')
        self.assertIn('business-license.pdf', download_response['Content-Disposition'])

    def test_mailbox_thread_api_refreshes_missing_gmail_attachment_metadata(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.email.attachments_info = []
        self.email.save(update_fields=['attachments_info'])
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.get_message_detail.return_value = {
                'id': self.email.gmail_message_id,
                'attachments': [
                    {
                        'filename': 'request-form.xlsx',
                        'size': 12,
                        'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'source': 'gmail',
                        'gmailAttachmentId': 'gmail-att-1',
                    }
                ],
            }

            response = self.client.get(
                reverse('reporting:mailbox_api_thread', args=['gmail-thread-react-1'])
            )

        self.assertEqual(response.status_code, 200)
        attachment = response.json()['emails'][0]['attachments'][0]
        self.assertEqual(attachment['filename'], 'request-form.xlsx')
        self.assertTrue(attachment['downloadHref'])
        self.email.refresh_from_db()
        self.assertEqual(self.email.attachments_info[0]['gmailAttachmentId'], 'gmail-att-1')

    def test_mailbox_attachment_download_uses_gmail_attachment_api(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.email.attachments_info = [
            {
                'filename': 'incoming.pdf',
                'size': 18,
                'mimetype': 'application/pdf',
                'source': 'gmail',
                'gmailAttachmentId': 'gmail-att-2',
                'gmailMessageId': self.email.gmail_message_id,
            }
        ]
        self.email.save(update_fields=['attachments_info'])
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.get_attachment.return_value = b'%PDF incoming file'

            response = self.client.get(
                reverse('reporting:mailbox_api_attachment_download', args=[self.email.id, 0])
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'%PDF incoming file')
        gmail_service.get_attachment.assert_called_once_with(self.email.gmail_message_id, 'gmail-att-2')

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

    def test_mailbox_send_api_schedules_email_without_immediate_send(self):
        from datetime import timedelta

        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)
        uploaded_file = SimpleUploadedFile('scheduled.txt', b'scheduled attachment', content_type='text/plain')
        scheduled_at = timezone.now() + timedelta(hours=1)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '예약 발송 테스트',
                    'body_text': '예약 발송 본문입니다.',
                    'selected_followup_id': str(self.followup.id),
                    'scheduled_at': scheduled_at.isoformat(),
                    'attachments': uploaded_file,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['scheduled'])
        self.assertEqual(payload['href'], '/mailbox/?box=scheduled')
        gmail_service_class.assert_not_called()
        self.assertFalse(EmailLog.objects.filter(subject='예약 발송 테스트').exists())

        scheduled_email = ScheduledEmail.objects.get(subject='예약 발송 테스트')
        self.assertEqual(scheduled_email.status, 'pending')
        self.assertEqual(scheduled_email.followup, self.followup)
        self.assertEqual(scheduled_email.to_email, 'customer@example.com')
        attachment = ScheduledEmailAttachment.objects.get(scheduled_email=scheduled_email)
        self.addCleanup(attachment.file.delete, False)
        self.assertEqual(attachment.filename, 'scheduled.txt')
        with attachment.file.open('rb') as file_handle:
            self.assertEqual(file_handle.read(), b'scheduled attachment')

        list_response = self.client.get(reverse('reporting:mailbox_api_list'), {'box': 'scheduled'})
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertEqual(list_payload['counts']['scheduled'], 1)
        self.assertEqual(list_payload['emails'][0]['subject'], '예약 발송 테스트')
        self.assertTrue(list_payload['emails'][0]['isScheduled'])
        self.assertIn('/api/mailbox/scheduled/', list_payload['emails'][0]['cancelHref'])

    def test_process_due_scheduled_emails_sends_and_creates_email_log(self):
        from datetime import timedelta
        from reporting.gmail_views import process_due_scheduled_emails

        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        scheduled_email = ScheduledEmail.objects.create(
            user=self.user,
            provider='gmail',
            sender_email='sales@example.com',
            to_email='customer@example.com',
            subject='만기 예약 메일',
            body='지금 발송할 본문입니다.',
            body_html='<div>지금 발송할 본문입니다.</div>',
            followup=self.followup,
            scheduled_at=timezone.now() - timedelta(minutes=5),
            status='pending',
        )
        attachment = ScheduledEmailAttachment.objects.create(
            scheduled_email=scheduled_email,
            file=SimpleUploadedFile('due.txt', b'due attachment', content_type='text/plain'),
            filename='due.txt',
            mimetype='text/plain',
            size=len(b'due attachment'),
            metadata={'filename': 'due.txt', 'size': len(b'due attachment'), 'mimetype': 'text/plain', 'source': 'uploaded'},
        )
        self.addCleanup(attachment.file.delete, False)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-scheduled-sent',
                'thread_id': 'gmail-scheduled-thread',
            }
            result = process_due_scheduled_emails(limit=10)

        self.assertEqual(result, {'processed': 1, 'sent': 1, 'failed': 0})
        sent_kwargs = gmail_service.send_email.call_args.kwargs
        self.assertEqual(sent_kwargs['to_email'], 'customer@example.com')
        self.assertEqual(sent_kwargs['attachments'][0]['content'], b'due attachment')

        scheduled_email.refresh_from_db()
        self.assertEqual(scheduled_email.status, 'sent')
        self.assertIsNotNone(scheduled_email.sent_email)
        email_log = EmailLog.objects.get(gmail_message_id='gmail-scheduled-sent')
        self.assertEqual(email_log.subject, '만기 예약 메일')
        self.assertEqual(email_log.followup, self.followup)
        self.assertEqual(email_log.attachments_info[0]['scheduledAttachmentId'], attachment.id)

    def test_scheduled_email_inline_worker_defaults_on_in_railway_server_process(self):
        import os
        from reporting import scheduled_email_worker

        with patch.object(scheduled_email_worker, '_worker_started', False):
            with patch.object(scheduled_email_worker.sys, 'argv', ['gunicorn', 'sales_project.wsgi:application']):
                with patch.object(scheduled_email_worker.threading, 'Thread') as thread_class:
                    with patch.dict(os.environ, {
                        'RAILWAY_ENVIRONMENT': 'production',
                        'SCHEDULED_EMAIL_INLINE_INTERVAL_SECONDS': '15',
                        'SCHEDULED_EMAIL_INLINE_INITIAL_DELAY_SECONDS': '0',
                    }, clear=False):
                        os.environ.pop('SCHEDULED_EMAIL_INLINE_WORKER', None)
                        scheduled_email_worker.start_scheduled_email_inline_worker()

        thread_class.assert_called_once()
        thread_class.return_value.start.assert_called_once()

    def test_mailbox_send_api_includes_internal_cc_only_when_requested(self):
        self.user.email = 'sales@example.com'
        self.user.save(update_fields=['email'])
        self.other_user.email = 'inside@example.com'
        self.other_user.save(update_fields=['email'])
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)

        list_response = self.client.get(reverse('reporting:mailbox_api_list'), {'box': 'inbox'})
        self.assertEqual(list_response.status_code, 200)
        self.assertIn('inside@example.com', list_response.json()['create']['internalCcEmails'])
        internal_contacts = list_response.json()['create']['internalCcContacts']
        self.assertEqual(internal_contacts[0]['email'], 'inside@example.com')
        self.assertEqual(internal_contacts[0]['name'], 'mail-api-other')

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-internal-cc',
                'thread_id': 'gmail-thread-internal-cc',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'cc_emails': 'manager@example.com',
                    'include_internal_cc': '1',
                    'subject': '참조 테스트',
                    'body_text': '참조 확인 부탁드립니다.',
                    'selected_followup_id': str(self.followup.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_cc = gmail_service.send_email.call_args.kwargs['cc']
        self.assertEqual(sent_cc, ['manager@example.com', 'inside@example.com'])
        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-internal-cc')
        self.assertEqual(email_log.cc_emails, 'manager@example.com, inside@example.com')

    def test_mailbox_send_api_allows_selected_internal_cc_contacts(self):
        self.user.email = 'sales@example.com'
        self.user.save(update_fields=['email'])
        self.other_user.email = 'inside-selected@example.com'
        self.other_user.save(update_fields=['email'])
        third_user = make_user('mail-api-third', company=self.company)
        third_user.email = 'inside-not-selected@example.com'
        third_user.save(update_fields=['email'])
        outside_company = UserCompany.objects.create(name='외부회사')
        outside_user = make_user('mail-api-outside', company=outside_company)
        outside_user.email = 'outside@example.com'
        outside_user.save(update_fields=['email'])
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-selected-internal-cc',
                'thread_id': 'gmail-thread-selected-internal-cc',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'cc_emails': 'manager@example.com',
                    'internal_cc_emails': json.dumps([
                        'inside-selected@example.com',
                        'inside-not-selected@example.com',
                        'outside@example.com',
                    ]),
                    'subject': '선택 참조 테스트',
                    'body_text': '선택한 내부 직원만 참조합니다.',
                    'selected_followup_id': str(self.followup.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_cc = gmail_service.send_email.call_args.kwargs['cc']
        self.assertEqual(sent_cc, [
            'manager@example.com',
            'inside-selected@example.com',
            'inside-not-selected@example.com',
        ])
        self.assertNotIn('outside@example.com', sent_cc)
        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-selected-internal-cc')
        self.assertEqual(
            email_log.cc_emails,
            'manager@example.com, inside-selected@example.com, inside-not-selected@example.com',
        )

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

    def test_mailbox_send_api_excludes_removed_auto_document_attachment(self):
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
            transaction_number='QUOTE-PDF-EXCLUDE-001',
            output_format='pdf',
            file=SimpleUploadedFile('excluded-quote.pdf', b'%PDF excluded', content_type='application/pdf'),
            filename='excluded-quote.pdf',
            file_size=len(b'%PDF excluded'),
        )
        second_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=schedule,
            user=self.user,
            transaction_number='QUOTE-PDF-INCLUDED-001',
            output_format='pdf',
            file=SimpleUploadedFile('included-quote.pdf', b'%PDF included', content_type='application/pdf'),
            filename='included-quote.pdf',
            file_size=len(b'%PDF included'),
        )
        self.addCleanup(first_log.file.delete, False)
        self.addCleanup(second_log.file.delete, False)
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-auto-excluded',
                'thread_id': 'gmail-thread-auto-excluded',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '견적서 일부 제외',
                    'body_text': '견적서 확인 부탁드립니다.',
                    'schedule_id': str(schedule.id),
                    'excluded_auto_attachment_keys': json.dumps([f'log:{first_log.id}']),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual([item['filename'] for item in sent_attachments], ['included-quote.pdf'])
        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-auto-excluded')
        self.assertEqual([item['documentLogId'] for item in email_log.attachments_info], [second_log.id])

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

    def test_mailbox_send_api_generates_transaction_statement_when_delivery_has_no_registered_pdf(self):
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
            activity_type='delivery',
        )
        self.client.force_login(self.user)
        document_response = HttpResponse(b'%PDF generated statement', content_type='application/pdf')
        document_response['X-Filename'] = 'generated-statement.pdf'

        with patch('reporting.views.generate_document_pdf', return_value=document_response) as generate_pdf:
            with patch('reporting.gmail_views.GmailService') as gmail_service_class:
                gmail_service = gmail_service_class.return_value
                gmail_service.send_email.return_value = {
                    'message_id': 'gmail-sent-generated-statement',
                    'thread_id': 'gmail-thread-generated-statement',
                }

                response = self.client.post(
                    reverse('reporting:mailbox_api_send'),
                    {
                        'to_email': 'customer@example.com',
                        'subject': '거래명세서 자동 생성',
                        'body_text': '거래명세서 확인 부탁드립니다.',
                        'schedule_id': str(schedule.id),
                    },
                )

        self.assertEqual(response.status_code, 200)
        generate_pdf.assert_called_once()
        self.assertEqual(generate_pdf.call_args.args[1:], ('transaction_statement', schedule.id, 'pdf'))
        self.assertEqual(generate_pdf.call_args.kwargs, {})
        sent_attachments = gmail_service.send_email.call_args.kwargs['attachments']
        self.assertEqual(sent_attachments[0]['filename'], 'generated-statement.pdf')
        self.assertEqual(sent_attachments[0]['content'], b'%PDF generated statement')

    def test_mailbox_send_api_auto_attaches_registered_transaction_statement_for_delivery_schedule(self):
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
        statement_log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='transaction_statement',
            schedule=schedule,
            user=self.user,
            transaction_number='TS-PDF-001',
            output_format='pdf',
            file=SimpleUploadedFile('statement.pdf', b'%PDF statement', content_type='application/pdf'),
            filename='statement.pdf',
            file_size=len(b'%PDF statement'),
        )
        quote_log = DocumentGenerationLog.objects.create(
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
        self.addCleanup(statement_log.file.delete, False)
        self.addCleanup(quote_log.file.delete, False)
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-delivery-statement',
                'thread_id': 'gmail-thread-delivery-statement',
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
        self.assertEqual([item['filename'] for item in sent_attachments], ['statement.pdf'])
        self.assertEqual(sent_attachments[0]['content'], b'%PDF statement')

        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-delivery-statement')
        self.assertEqual(email_log.attachments_info[0]['source'], 'transaction_statement_document')
        self.assertEqual(email_log.attachments_info[0]['documentType'], 'transaction_statement')
        self.assertEqual(email_log.attachments_info[0]['documentLogId'], statement_log.id)

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

    def test_mailbox_send_api_sends_sanitized_rich_html_body(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-sent-rich-html',
                'thread_id': 'gmail-thread-rich-html',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_send'),
                {
                    'to_email': 'customer@example.com',
                    'subject': '리치 본문 테스트',
                    'body_text': '굵은 안내 링크 사진',
                    'body_html': (
                        '<div style="font-family: Arial; color: #123456;" onclick="alert(1)">'
                        '<strong>굵은 안내</strong> '
                        '<a href="https://example.com/quote" onclick="alert(2)">링크</a>'
                        '<img src="https://example.com/photo.png" onerror="alert(3)" style="max-width:100%;height:auto;">'
                        '<script>alert(4)</script>'
                        '</div>'
                    ),
                    'selected_followup_id': str(self.followup.id),
                },
            )

        self.assertEqual(response.status_code, 200)
        body_html = gmail_service.send_email.call_args.kwargs['body_html']
        self.assertIn('<strong>굵은 안내</strong>', body_html)
        self.assertIn('href="https://example.com/quote"', body_html)
        self.assertIn('src="https://example.com/photo.png"', body_html)
        self.assertIn('font-family: Arial', body_html)
        self.assertNotIn('<script', body_html)
        self.assertNotIn('onclick', body_html)
        self.assertNotIn('onerror', body_html)

        email_log = EmailLog.objects.get(gmail_message_id='gmail-sent-rich-html')
        self.assertEqual(email_log.body_html, body_html)
        self.assertIn('<strong>굵은 안내</strong>', email_log.body)

    def test_mailbox_reply_api_cleans_html_document_pasted_as_text(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        self.client.force_login(self.user)
        pasted_html = (
            '<html><head><style>p{font-size:13px;margin:0;}</style></head>'
            '<body><div style="font-family:Malgun Gothic;color:#111;">'
            '<p>답장 본문입니다.</p><p>견적서 첨부 확인 부탁드립니다.</p>'
            '</div></body></html>'
        )

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-reply-clean-html-text',
                'thread_id': 'gmail-thread-react-1',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_reply', args=[self.email.id]),
                {
                    'to_email': 'customer@example.com',
                    'subject': 'Re: React mailbox inbound',
                    'body_text': pasted_html,
                    'body_html': pasted_html.replace('<', '&lt;').replace('>', '&gt;'),
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_kwargs = gmail_service.send_email.call_args.kwargs
        self.assertEqual(sent_kwargs['body_text'], '답장 본문입니다.\n견적서 첨부 확인 부탁드립니다.')
        self.assertIn('답장 본문입니다.<br>', sent_kwargs['body_html'])
        self.assertNotIn('<html', sent_kwargs['body_html'])
        self.assertNotIn('&lt;html', sent_kwargs['body_html'])
        self.assertNotIn('font-family:Malgun', sent_kwargs['body_html'])

        email_log = EmailLog.objects.get(gmail_message_id='gmail-reply-clean-html-text')
        self.assertEqual(email_log.in_reply_to, self.email)
        self.assertNotIn('<html', email_log.body_html)
        self.assertNotIn('&lt;html', email_log.body_html)

    def test_mailbox_reply_api_can_reply_to_sent_only_thread_recipient_with_rich_format(self):
        profile = self.user.userprofile
        profile.gmail_token = {'access_token': 'test-token'}
        profile.gmail_email = 'sales@example.com'
        profile.save(update_fields=['gmail_token', 'gmail_email'])
        sent_email = EmailLog.objects.create(
            email_type='sent',
            sender=self.user,
            user=self.user,
            sender_email='sales@example.com',
            recipient_email='waiting@example.com',
            subject='고객 답장 대기',
            body='고객에게 먼저 보낸 메일입니다.',
            body_html='<div>고객에게 먼저 보낸 메일입니다.</div>',
            gmail_message_id='gmail-msg-waiting-2',
            gmail_thread_id='gmail-thread-waiting-2',
            followup=self.followup,
            status='sent',
            sent_at=timezone.now(),
        )
        self.client.force_login(self.user)

        with patch('reporting.gmail_views.GmailService') as gmail_service_class:
            gmail_service = gmail_service_class.return_value
            gmail_service.send_email.return_value = {
                'message_id': 'gmail-msg-waiting-reply',
                'thread_id': 'gmail-thread-waiting-2',
            }

            response = self.client.post(
                reverse('reporting:mailbox_api_reply', args=[sent_email.id]),
                {
                    'to_email': 'sales@example.com',
                    'subject': 'Re: 고객 답장 대기',
                    'body_text': '답장 본문입니다.',
                    'body_html': '<p><strong>답장 본문</strong>입니다.</p>',
                },
            )

        self.assertEqual(response.status_code, 200)
        sent_kwargs = gmail_service.send_email.call_args.kwargs
        self.assertEqual(sent_kwargs['to_email'], 'waiting@example.com')
        self.assertIn('<strong>답장 본문</strong>', sent_kwargs['body_html'])
        self.assertEqual(sent_kwargs['in_reply_to'], 'gmail-msg-waiting-2')
        self.assertEqual(sent_kwargs['thread_id'], 'gmail-thread-waiting-2')

        email_log = EmailLog.objects.get(gmail_message_id='gmail-msg-waiting-reply')
        self.assertEqual(email_log.recipient_email, 'waiting@example.com')
        self.assertIn('<strong>답장 본문</strong>', email_log.body_html)
        self.assertEqual(email_log.in_reply_to, sent_email)


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
    """대시보드 legacy URL 전환 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='대시보드테스트회사')
        self.user = make_user('dash_user', role='salesman', company=self.company)

    def test_dashboard_returns_200(self):
        """인증 후 대시보드는 React 대시보드로 이동"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], frontend_url('dashboard/'))

    def test_dashboard_head_redirects_to_react(self):
        """HEAD 요청도 템플릿 렌더링 대신 React로 이동"""
        self.client.force_login(self.user)
        r = self.client.head(reverse('reporting:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], frontend_url('dashboard/'))

    def test_dashboard_unauthenticated_redirects(self):
        """미인증 대시보드 접근 → 로그인 리다이렉트"""
        r = self.client.get(reverse('reporting:dashboard'))
        self.assertIn(r.status_code, [301, 302])
        self.assertIn('login', r.get('Location', ''))

    def test_dashboard_api_still_returns_key_sections(self):
        """대시보드 데이터는 React API에서 계속 제공"""
        self.client.force_login(self.user)
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload['source'], 'django')
        self.assertIn('metrics', payload)
        self.assertEqual(payload['links']['operationalDashboard'], '/dashboard/')


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

    def test_dashboard_summary_api_excludes_stale_quote_submission_followups(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import History

        today = timezone.localdate()
        followup = self._create_customer(
            self.user,
            '견적완료',
            overdue=False,
            today_schedule=False,
        )
        History.objects.filter(followup=followup).update(reviewed_at=timezone.now())
        stale_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='견적서 제출 예정',
            next_action='견적서 및 비교표 제출',
            next_action_date=today - timedelta(days=1),
        )
        active_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='제출된 견적 검토 상황 확인',
            next_action='견적 검토 여부 확인',
            next_action_date=today - timedelta(days=1),
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1200000'),
        )
        DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=quote_schedule,
            user=self.user,
            transaction_number='DASH-ST-Q-001',
            output_format='pdf',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        overdue_ids = {item['id'] for item in payload['overdueActions']}
        self.assertNotIn(stale_history.id, overdue_ids)
        self.assertIn(active_history.id, overdue_ids)
        self.assertEqual(payload['metrics']['overdueActions'], 1)

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

    def test_dashboard_summary_api_includes_year_and_quarter_revenue(self):
        from datetime import date, time
        from decimal import Decimal
        from reporting.models import DeliveryItem, Schedule

        today = timezone.localdate()
        quarter = ((today.month - 1) // 3) + 1
        quarter_start_month = ((quarter - 1) * 3) + 1
        followup = self._create_customer(
            self.user,
            '매출고객',
            overdue=False,
            today_schedule=False,
        )
        coworker_followup = self._create_customer(
            self.coworker,
            '동료매출',
            overdue=False,
            today_schedule=False,
        )

        def create_delivery(owner, target_followup, visit_date, unit_price):
            schedule = Schedule.objects.create(
                user=owner,
                company=owner.userprofile.company,
                followup=target_followup,
                visit_date=visit_date,
                visit_time=time(11, 0),
                status='completed',
                activity_type='delivery',
            )
            DeliveryItem.objects.create(
                schedule=schedule,
                item_name='납품품목',
                quantity=1,
                unit_price=Decimal(str(unit_price)),
            )
            return int(Decimal(str(unit_price)) * Decimal('1.1'))

        expected_year = 0
        expected_quarter = 0
        expected_month = create_delivery(self.user, followup, today, 100000)
        expected_year += expected_month
        expected_quarter += expected_month

        quarter_delivery = create_delivery(
            self.user,
            followup,
            date(today.year, quarter_start_month, 1),
            200000,
        )
        expected_year += quarter_delivery
        expected_quarter += quarter_delivery
        if today.month == quarter_start_month:
            expected_month += quarter_delivery

        if quarter_start_month > 1:
            expected_year += create_delivery(
                self.user,
                followup,
                date(today.year, 1, 15),
                300000,
            )

        create_delivery(self.user, followup, date(today.year - 1, 12, 15), 400000)
        create_delivery(self.coworker, coworker_followup, today, 500000)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['metrics']['yearRevenue'], expected_year)
        self.assertEqual(payload['metrics']['quarterRevenue'], expected_quarter)
        self.assertEqual(payload['metrics']['monthlyRevenue'], expected_month)
        self.assertEqual(payload['revenuePeriod']['year'], today.year)
        self.assertEqual(payload['revenuePeriod']['quarter'], quarter)


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
        company_option = next(option for option in payload['create']['companies'] if option['id'] == own.company_id)
        self.assertTrue(company_option['canManage'])
        self.assertFalse(company_option['canDelete'])
        self.assertEqual(company_option['updateUrl'], reverse('reporting:company_update_api', args=[own.company_id]))
        self.assertEqual(company_option['deleteUrl'], reverse('reporting:company_delete_api', args=[own.company_id]))
        self.assertIn('부서', company_option['deleteMessage'])
        department_option = next(option for option in payload['create']['departments'] if option['id'] == own.department_id)
        self.assertTrue(department_option['canManage'])
        self.assertFalse(department_option['canDelete'])
        self.assertEqual(department_option['updateUrl'], reverse('reporting:department_update_api', args=[own.department_id]))
        self.assertEqual(department_option['deleteUrl'], reverse('reporting:department_delete_api', args=[own.department_id]))
        self.assertIn('담당자', department_option['deleteMessage'])
        self.assertIn('내고객 책임', department_option['searchText'])

    def test_customers_summary_api_returns_department_account_rows(self):
        from datetime import time, timedelta
        from reporting.models import FollowUp, Schedule

        target = self._create_customer(self.user, '계정고객')
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            customer_name='계정고객 추가담당',
            manager='계정고객 추가책임',
            company=target.company,
            department=target.department,
            priority='scheduled',
            pipeline_stage='contact',
        )
        Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=sibling,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(11, 0),
            activity_type='customer_meeting',
            status='scheduled',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        customer_ids = {item['id'] for item in payload['customers']}
        self.assertIn(target.id, customer_ids)
        self.assertIn(sibling.id, customer_ids)
        self.assertEqual(payload['metrics']['totalCustomers'], 2)
        self.assertEqual(payload['metrics']['totalAccounts'], 1)
        self.assertEqual(payload['metrics']['filteredAccounts'], 1)
        self.assertEqual(len(payload['accounts']), 1)
        account = payload['accounts'][0]
        self.assertEqual(account['id'], target.department_id)
        self.assertEqual(account['accountId'], target.department_id)
        self.assertEqual(account['accountType'], 'department')
        self.assertIn(account['representativeCustomerId'], {target.id, sibling.id})
        self.assertEqual(account['customer'], target.department.name)
        self.assertEqual(account['href'], f'/accounts/{target.department_id}/')
        self.assertIn(account['customerHref'], {
            reverse('reporting:followup_detail', args=[target.id]),
            reverse('reporting:followup_detail', args=[sibling.id]),
        })
        self.assertEqual(account['contactCount'], 2)
        self.assertIn('계정고객 담당자', account['contactPreview'])
        self.assertIn('계정고객 추가담당', account['contactPreview'])
        self.assertEqual(account['activityCount'], 1)
        self.assertEqual(account['scheduleCount'], 1)
        self.assertEqual(account['upcomingScheduleCount'], 1)

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
        self.assertEqual(
            customer['upcomingSchedule']['createHistoryHref'],
            f'/notes/?create=1&customer={target.id}&schedule={upcoming.id}',
        )
        self.assertEqual(
            customer['upcomingSchedule']['djangoCreateHistoryHref'],
            reverse('reporting:history_create_from_schedule', args=[upcoming.id]),
        )
        self.assertEqual(payload['metrics']['scheduledCustomers'], 1)

    def test_customers_apis_exclude_stale_quote_submission_overdue_count(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import History, Schedule

        today = timezone.localdate()
        target = self._create_customer(self.user, '견적완료고객')
        History.objects.filter(followup=target).update(reviewed_at=timezone.now())
        stale_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            action_type='customer_meeting',
            content='견적서 제출 예정',
            next_action='견적서 및 비교표 제출',
            next_action_date=today - timedelta(days=1),
        )
        active_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            action_type='customer_meeting',
            content='견적 검토 상황 확인',
            next_action='견적 검토 여부 확인',
            next_action_date=today - timedelta(days=1),
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today,
            visit_time=time(10, 30),
            activity_type='quote',
            status='scheduled',
            expected_revenue=Decimal('770000'),
        )
        DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=quote_schedule,
            user=self.user,
            transaction_number='CUSTOMER-ST-Q-001',
            output_format='pdf',
        )
        self.client.force_login(self.user)

        list_response = self.client.get(self.url)

        self.assertEqual(list_response.status_code, 200)
        customer = next(item for item in list_response.json()['customers'] if item['id'] == target.id)
        self.assertEqual(customer['overdueActionCount'], 1)
        self.assertEqual(customer['nextAction'], '견적 검토 여부 확인')
        self.assertNotEqual(customer['nextAction'], stale_history.next_action)

        detail_response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        overdue_ids = {item['id'] for item in detail_payload['overdueActions']}
        self.assertNotIn(stale_history.id, overdue_ids)
        self.assertIn(active_history.id, overdue_ids)
        self.assertEqual(detail_payload['metrics']['overdueActions'], 1)

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

    def test_company_and_department_manage_apis_update_and_delete_owner_records(self):
        from reporting.models import Company, Department

        company = Company.objects.create(name='수정전 업체', created_by=self.user)
        department_parent = Company.objects.create(name='부서수정 부모업체', created_by=self.user)
        department = Department.objects.create(
            company=department_parent,
            name='수정전 부서',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        company_update = self.client.post(reverse('reporting:company_update_api', args=[company.id]), {
            'name': '수정후 업체',
        })
        department_update = self.client.post(reverse('reporting:department_update_api', args=[department.id]), {
            'name': '수정후 부서',
        })

        self.assertEqual(company_update.status_code, 200)
        self.assertTrue(company_update.json()['success'])
        self.assertEqual(Company.objects.get(id=company.id).name, '수정후 업체')
        self.assertEqual(department_update.status_code, 200)
        self.assertTrue(department_update.json()['success'])
        self.assertEqual(Department.objects.get(id=department.id).name, '수정후 부서')

        department_delete = self.client.post(reverse('reporting:department_delete_api', args=[department.id]))
        company_delete = self.client.post(reverse('reporting:company_delete_api', args=[company.id]))

        self.assertEqual(department_delete.status_code, 200)
        self.assertTrue(department_delete.json()['success'])
        self.assertFalse(Department.objects.filter(id=department.id).exists())
        self.assertEqual(company_delete.status_code, 200)
        self.assertTrue(company_delete.json()['success'])
        self.assertFalse(Company.objects.filter(id=company.id).exists())

    def test_company_and_department_manage_apis_block_manager_and_other_user(self):
        from reporting.models import Company, Department

        company = Company.objects.create(name='수정권한차단 업체', created_by=self.user)
        department = Department.objects.create(
            company=company,
            name='수정권한차단 부서',
            created_by=self.user,
        )

        self.client.force_login(self.manager)
        manager_company_update = self.client.post(reverse('reporting:company_update_api', args=[company.id]), {
            'name': '매니저수정',
        })
        manager_department_delete = self.client.post(reverse('reporting:department_delete_api', args=[department.id]))

        self.assertEqual(manager_company_update.status_code, 403)
        self.assertFalse(manager_company_update.json()['success'])
        self.assertEqual(manager_department_delete.status_code, 403)
        self.assertFalse(manager_department_delete.json()['success'])

        self.client.force_login(self.other_user)
        other_company_delete = self.client.post(reverse('reporting:company_delete_api', args=[company.id]))
        other_department_update = self.client.post(reverse('reporting:department_update_api', args=[department.id]), {
            'name': '타사수정',
        })

        self.assertEqual(other_company_delete.status_code, 403)
        self.assertFalse(other_company_delete.json()['success'])
        self.assertEqual(other_department_update.status_code, 403)
        self.assertFalse(other_department_update.json()['success'])

    def test_company_and_department_delete_apis_block_records_in_use(self):
        target = self._create_customer(self.user, '삭제차단')
        self.client.force_login(self.user)

        company_response = self.client.post(reverse('reporting:company_delete_api', args=[target.company_id]))
        department_response = self.client.post(reverse('reporting:department_delete_api', args=[target.department_id]))

        self.assertEqual(company_response.status_code, 400)
        self.assertFalse(company_response.json()['success'])
        self.assertIn('삭제할 수 없습니다', company_response.json()['error'])
        self.assertEqual(department_response.status_code, 400)
        self.assertFalse(department_response.json()['success'])
        self.assertIn('담당자', department_response.json()['error'])

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
        self.assertEqual(summary['links']['accountPrepayments'], f'/prepayments/account/{target.department_id}/')
        self.assertEqual(summary['links']['customerPrepayments'], f'/prepayments/customer/{target.id}/')
        self.assertTrue(summary['links']['djangoCustomerPrepayments'].endswith(f'/prepayment/customer/{target.id}/'))
        prepayment_ids = {item['id'] for item in summary['recentPrepayments']}
        self.assertIn(first.id, prepayment_ids)
        self.assertIn(second.id, prepayment_ids)
        self.assertNotIn(coworker_prepayment.id, prepayment_ids)

    def test_customer_detail_summary_api_includes_asset_service_calibration_summary(self):
        from django.utils import timezone
        from reporting.models import CalibrationRecord, CustomerAsset, ServiceCase

        target = self._create_customer(self.user, '상세장비', priority='urgent')
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='Pipette Set',
            model_name='P-1000',
            serial_number='SN-001',
            warranty_until=timezone.localdate(),
            created_by=self.user,
        )
        coworker_asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='동료 장비',
            created_by=self.coworker,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=target,
            case_type='repair',
            status='in_progress',
            priority='high',
            received_date=timezone.localdate(),
            due_date=timezone.localdate(),
            symptom='버튼 불량',
            created_by=self.user,
            assigned_to=self.user,
        )
        CalibrationRecord.objects.create(
            asset=asset,
            followup=target,
            calibration_date=timezone.localdate(),
            next_due_date=timezone.localdate(),
            result='pass',
            created_by=self.user,
            performed_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        summary = response.json()['assetSummary']
        self.assertTrue(summary['canManage'])
        self.assertEqual(summary['metrics']['assetCount'], 2)
        self.assertEqual(summary['metrics']['activeAssetCount'], 2)
        self.assertEqual(summary['metrics']['openServiceCaseCount'], 1)
        self.assertEqual(summary['metrics']['dueCalibrationCount'], 1)
        asset_ids = {item['id'] for item in summary['assets']}
        self.assertIn(asset.id, asset_ids)
        self.assertIn(coworker_asset.id, asset_ids)
        first_asset = next(item for item in summary['assets'] if item['id'] == asset.id)
        self.assertEqual(first_asset['assetName'], 'Pipette Set')
        self.assertEqual(first_asset['latestServiceCase']['caseType'], 'repair')
        self.assertEqual(first_asset['latestCalibration']['result'], 'pass')

    def test_customer_detail_summary_api_includes_operational_records_with_payment_source(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from django.utils import timezone
        from reporting.models import (
            CustomerAsset,
            DeliveryItem,
            FollowUp,
            Prepayment,
            PrepaymentUsage,
            Product,
            Quote,
            QuoteItem,
            Schedule,
            ServiceCase,
        )

        today = timezone.localdate()
        target = self._create_customer(self.user, '운영기록고객', priority='urgent')
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            customer_name='운영기록 같은부서 담당자',
            manager='운영기록 같은부서 책임',
            company=target.company,
            department=target.department,
            priority='scheduled',
            pipeline_stage='quote',
        )
        product = Product.objects.create(
            product_code='OP-QUOTE-001',
            standard_price=Decimal('120000'),
            created_by=self.user,
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today - timedelta(days=10),
            visit_time=time(10, 0),
            activity_type='quote',
            status='completed',
            notes='운영 견적 일정',
        )
        quote = Quote.objects.create(
            quote_number='OP-Q-001',
            schedule=quote_schedule,
            followup=target,
            user=self.user,
            valid_until=today + timedelta(days=20),
            stage='sent',
            notes='운영 견적 메모',
        )
        QuoteItem.objects.create(
            quote=quote,
            product=product,
            quantity=2,
            unit_price=Decimal('120000'),
        )
        sibling_quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=sibling,
            visit_date=today - timedelta(days=8),
            visit_time=time(13, 0),
            activity_type='quote',
            status='completed',
            notes='같은 부서 견적 일정',
        )
        Quote.objects.create(
            quote_number='OP-Q-SAME-DEPT',
            schedule=sibling_quote_schedule,
            followup=sibling,
            user=self.user,
            valid_until=today + timedelta(days=20),
            stage='sent',
            notes='같은 부서 견적 메모',
        )
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='운영 서비스 장비',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=target,
            case_type='service',
            status='in_progress',
            priority='high',
            received_date=today - timedelta(days=3),
            symptom='운영 서비스 요청',
            created_by=self.user,
            assigned_to=self.user,
        )
        prepayment = Prepayment.objects.create(
            customer=target,
            company=target.company,
            amount=100000,
            balance=40000,
            payment_date=today - timedelta(days=7),
            payer_name='운영입금자',
            status='active',
            created_by=self.user,
        )
        sibling_prepayment = Prepayment.objects.create(
            customer=sibling,
            company=sibling.company,
            amount=50000,
            balance=50000,
            payment_date=today - timedelta(days=6),
            payer_name='같은부서입금자',
            status='active',
            created_by=self.user,
        )
        prepaid_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today - timedelta(days=2),
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
            notes='구조화된 선결제 차감',
            use_prepayment=True,
            prepayment=prepayment,
            prepayment_amount=Decimal('60000'),
        )
        prepaid_item = DeliveryItem.objects.create(
            schedule=prepaid_schedule,
            item_name='선결제 납품품목',
            quantity=1,
            unit_price=Decimal('60000'),
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=prepaid_schedule,
            schedule_item=prepaid_item,
            product_name='선결제 납품품목',
            quantity=1,
            amount=Decimal('60000'),
            remaining_balance=Decimal('40000'),
        )
        normal_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today - timedelta(days=1),
            visit_time=time(14, 0),
            activity_type='delivery',
            status='completed',
            notes='메모에 선결제라고 써도 구조화 차감 없음',
        )
        DeliveryItem.objects.create(
            schedule=normal_schedule,
            item_name='일반 납품품목',
            quantity=1,
            unit_price=Decimal('30000'),
        )
        sibling_delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=sibling,
            visit_date=today,
            visit_time=time(15, 0),
            activity_type='delivery',
            status='completed',
            notes='같은 부서 납품',
        )
        DeliveryItem.objects.create(
            schedule=sibling_delivery_schedule,
            item_name='같은 부서 납품품목',
            quantity=1,
            unit_price=Decimal('70000'),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        records = payload['operationalRecords']
        self.assertEqual(payload['account']['id'], target.department_id)
        self.assertEqual(payload['account']['type'], 'department')
        self.assertEqual(payload['account']['contactCount'], 2)
        self.assertEqual(payload['account']['ledgerScopeLabel'], '부서/연구실 계정 공유 원장')
        self.assertIn('납품, 견적, 선결제, 장비, 서비스', payload['account']['ledgerScopeDescription'])
        contact_names = {contact['name'] for contact in payload['account']['contacts']}
        self.assertIn('운영기록고객 담당자', contact_names)
        self.assertIn('운영기록 같은부서 담당자', contact_names)
        self.assertEqual(records['metrics']['serviceRecords'], 1)
        self.assertEqual(records['metrics']['quoteRecords'], 2)
        self.assertEqual(records['metrics']['deliveryRecords'], 3)
        self.assertEqual(records['metrics']['prepaymentDeliveryRecords'], 1)
        self.assertEqual(records['metrics']['normalDeliveryRecords'], 2)
        self.assertEqual(records['metrics']['prepaymentRecords'], 2)
        self.assertEqual(payload['prepaymentSummary']['metrics']['totalCount'], 2)
        self.assertEqual(records['serviceRecords'][0]['assetName'], '운영 서비스 장비')
        quote_numbers = {record['quoteNumber'] for record in records['quoteRecords']}
        self.assertIn('OP-Q-001', quote_numbers)
        self.assertIn('OP-Q-SAME-DEPT', quote_numbers)
        delivery_by_id = {item['id']: item for item in records['deliveryRecords']}
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['paymentSource'], 'prepayment')
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['paymentSourceLabel'], '선결제 차감 납품')
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['paymentStatus'], 'prepayment_deduction')
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['paymentStatusLabel'], '선결제 차감 납품')
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['prepaymentAmount'], 60000)
        self.assertEqual(delivery_by_id[prepaid_schedule.id]['prepaymentUsages'][0]['amount'], 60000)
        self.assertEqual(delivery_by_id[normal_schedule.id]['paymentSource'], 'normal')
        self.assertEqual(delivery_by_id[normal_schedule.id]['paymentSourceLabel'], '일반 납품')
        self.assertEqual(delivery_by_id[normal_schedule.id]['paymentStatus'], 'normal')
        self.assertEqual(delivery_by_id[normal_schedule.id]['paymentStatusLabel'], '일반 납품')
        self.assertEqual(delivery_by_id[normal_schedule.id]['prepaymentAmount'], 0)
        self.assertIn('선결제 사용 필드와 PrepaymentUsage 기록이 없습니다.', delivery_by_id[normal_schedule.id]['paymentEvidence'])
        self.assertEqual(delivery_by_id[sibling_delivery_schedule.id]['customerName'], '운영기록 같은부서 담당자')
        payer_names = {record['payerName'] for record in records['prepaymentRecords']}
        self.assertIn('운영입금자', payer_names)
        self.assertIn('같은부서입금자', payer_names)

        account_response = self.client.get(reverse('reporting:account_detail_summary_api', args=[target.department_id]))
        self.assertEqual(account_response.status_code, 200)
        account_payload = account_response.json()
        self.assertEqual(account_payload['links']['accountDetail'], f'/accounts/{target.department_id}/')
        self.assertEqual(account_payload['account']['contactCount'], 2)
        self.assertEqual(account_payload['account']['ledgerScopeLabel'], '부서/연구실 계정 공유 원장')
        self.assertEqual(account_payload['operationalRecords']['metrics']['deliveryRecords'], 3)
        self.assertEqual(account_payload['operationalRecords']['metrics']['prepaymentDeliveryRecords'], 1)
        self.assertEqual(account_payload['operationalRecords']['metrics']['normalDeliveryRecords'], 2)
        self.assertEqual(account_payload['operationalRecords']['metrics']['quoteRecords'], 2)
        self.assertEqual(account_payload['operationalRecords']['metrics']['prepaymentRecords'], 2)

    def test_customer_delivery_records_xlsx_export_downloads_department_shared_deliveries(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from io import BytesIO
        from openpyxl import load_workbook
        from django.utils import timezone
        from reporting.models import DeliveryItem, FollowUp, Prepayment, PrepaymentUsage, Schedule

        today = timezone.localdate()
        target = self._create_customer(self.user, '납품엑셀고객', priority='urgent')
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            customer_name='납품엑셀 같은부서 담당자',
            manager='납품엑셀 같은부서 책임',
            company=target.company,
            department=target.department,
            priority='scheduled',
            pipeline_stage='quote',
        )
        other_target = self._create_customer(self.user, '다른납품고객', priority='urgent')
        prepayment = Prepayment.objects.create(
            customer=target,
            company=target.company,
            amount=Decimal('200000'),
            balance=Decimal('150000'),
            payment_date=today - timedelta(days=3),
            payer_name='엑셀입금자',
            created_by=self.user,
        )
        prepaid_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today - timedelta(days=2),
            visit_time=time(10, 0),
            activity_type='delivery',
            status='completed',
            use_prepayment=True,
            prepayment=prepayment,
            prepayment_amount=Decimal('50000'),
            notes='엑셀 선결제 납품',
        )
        prepaid_item = DeliveryItem.objects.create(
            schedule=prepaid_schedule,
            item_name='엑셀 선결제 품목',
            quantity=2,
            unit='EA',
            unit_price=Decimal('25000'),
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=prepaid_schedule,
            schedule_item=prepaid_item,
            product_name='엑셀 선결제 품목',
            quantity=2,
            amount=Decimal('50000'),
            remaining_balance=Decimal('150000'),
        )
        normal_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=today - timedelta(days=1),
            visit_time=time(14, 0),
            activity_type='delivery',
            status='completed',
            notes='엑셀 일반 납품',
        )
        DeliveryItem.objects.create(
            schedule=normal_schedule,
            item_name='엑셀 일반 품목',
            quantity=1,
            unit='EA',
            unit_price=Decimal('30000'),
        )
        sibling_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=sibling,
            visit_date=today,
            visit_time=time(13, 0),
            activity_type='delivery',
            status='completed',
            notes='같은 부서 납품',
        )
        DeliveryItem.objects.create(
            schedule=sibling_schedule,
            item_name='엑셀 같은부서 품목',
            quantity=1,
            unit='EA',
            unit_price=Decimal('40000'),
        )
        other_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=other_target,
            visit_date=today,
            visit_time=time(15, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=other_schedule,
            item_name='다른 고객 품목',
            quantity=1,
            unit_price=Decimal('99999'),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_delivery_records_xlsx_export_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment;', response['Content-Disposition'])
        workbook = load_workbook(BytesIO(response.content), data_only=True)
        sheet = workbook['납품 기록']
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], '납품일')
        self.assertEqual(rows[0][8], '결제상태')
        item_names = {row[10] for row in rows[1:]}
        self.assertIn('엑셀 선결제 품목', item_names)
        self.assertIn('엑셀 일반 품목', item_names)
        self.assertIn('엑셀 같은부서 품목', item_names)
        self.assertNotIn('다른 고객 품목', item_names)
        customer_names = {row[2] for row in rows[1:]}
        self.assertIn('납품엑셀 같은부서 담당자', customer_names)
        payment_labels = {row[7] for row in rows[1:]}
        self.assertIn('선결제 차감 납품', payment_labels)
        self.assertIn('일반 납품', payment_labels)
        payment_status_labels = {row[8] for row in rows[1:]}
        self.assertIn('선결제 차감 납품', payment_status_labels)
        self.assertIn('일반 납품', payment_status_labels)
        prepaid_row = next(row for row in rows[1:] if row[10] == '엑셀 선결제 품목')
        normal_row = next(row for row in rows[1:] if row[10] == '엑셀 일반 품목')
        self.assertEqual(prepaid_row[9], 50000)
        self.assertIn('PrepaymentUsage 합계=50,000원', prepaid_row[17])
        self.assertEqual(normal_row[9], 0)
        self.assertIn('선결제 사용 필드와 PrepaymentUsage 기록이 없습니다.', normal_row[17])

    def test_customer_delivery_records_xlsx_export_blocks_out_of_scope_customer(self):
        target = self._create_customer(self.other_user, '타사납품엑셀고객')
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_delivery_records_xlsx_export_api', args=[target.id]))

        self.assertEqual(response.status_code, 403)

    def test_customer_delivery_records_xlsx_export_requires_login(self):
        target = self._create_customer(self.user, '익명납품엑셀고객')

        response = self.client.get(reverse('reporting:customer_delivery_records_xlsx_export_api', args=[target.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_customer_asset_service_calibration_apis_create_records(self):
        from django.utils import timezone
        from reporting.models import CalibrationRecord, CustomerAsset, ServiceCase

        target = self._create_customer(self.user, '장비등록', priority='urgent')
        self.client.force_login(self.user)

        asset_response = self.client.post(reverse('reporting:customer_asset_create_api', args=[target.id]), {
            'asset_name': '등록 장비',
            'model_name': 'M-100',
            'serial_number': 'SN-100',
            'purchase_date': timezone.localdate().isoformat(),
            'install_location': '407호',
            'warranty_until': timezone.localdate().isoformat(),
            'status': 'active',
            'notes': '초기 등록',
        })

        self.assertEqual(asset_response.status_code, 200)
        asset_payload = asset_response.json()['asset']
        asset = CustomerAsset.objects.get(id=asset_payload['id'])
        self.assertEqual(asset.company, target.company)
        self.assertEqual(asset.department, target.department)
        self.assertEqual(asset.primary_followup, target)
        self.assertEqual(asset.created_by, self.user)

        service_response = self.client.post(reverse('reporting:customer_service_case_create_api', args=[target.id]), {
            'asset_id': str(asset.id),
            'case_type': 'service',
            'status': 'received',
            'priority': 'urgent',
            'received_date': timezone.localdate().isoformat(),
            'due_date': timezone.localdate().isoformat(),
            'symptom': '점검 요청',
        })
        self.assertEqual(service_response.status_code, 200)
        service_case = ServiceCase.objects.get(id=service_response.json()['serviceCase']['id'])
        self.assertEqual(service_case.asset, asset)
        self.assertEqual(service_case.followup, target)
        self.assertEqual(service_case.priority, 'urgent')

        calibration_response = self.client.post(reverse('reporting:customer_calibration_create_api', args=[target.id]), {
            'asset_id': str(asset.id),
            'calibration_date': timezone.localdate().isoformat(),
            'next_due_date': timezone.localdate().isoformat(),
            'result': 'adjusted',
            'notes': '조정 완료',
        })
        self.assertEqual(calibration_response.status_code, 200)
        calibration = CalibrationRecord.objects.get(id=calibration_response.json()['calibration']['id'])
        self.assertEqual(calibration.asset, asset)
        self.assertEqual(calibration.followup, target)
        self.assertEqual(calibration.result, 'adjusted')

    def test_customer_asset_mutation_blocks_manager_and_other_company(self):
        target = self._create_customer(self.user, '장비권한')
        other_target = self._create_customer(self.other_user, '타사장비')
        payload = {
            'asset_name': '권한 장비',
            'status': 'active',
        }

        self.client.force_login(self.manager)
        manager_response = self.client.post(reverse('reporting:customer_asset_create_api', args=[target.id]), payload)
        self.assertEqual(manager_response.status_code, 403)
        self.assertFalse(manager_response.json()['success'])

        self.client.force_login(self.user)
        other_response = self.client.post(reverse('reporting:customer_asset_create_api', args=[other_target.id]), payload)
        self.assertEqual(other_response.status_code, 403)
        self.assertFalse(other_response.json()['success'])

    def test_customer_assets_summary_api_requires_login_json(self):
        response = self.client.get(reverse('reporting:customer_assets_summary_api'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_customer_assets_summary_api_returns_direct_create_options(self):
        own = self._create_customer(self.user, '장비직접등록')
        coworker = self._create_customer(self.coworker, '동료직접등록')
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_assets_summary_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['canManage'])
        self.assertTrue(payload['create']['canCreate'])
        customer_ids = {item['id'] for item in payload['create']['customers']}
        self.assertIn(own.id, customer_ids)
        self.assertNotIn(coworker.id, customer_ids)
        create_option = next(item for item in payload['create']['customers'] if item['id'] == own.id)
        self.assertEqual(create_option['assetCreateUrl'], reverse('reporting:customer_asset_create_api', args=[own.id]))
        self.assertEqual(create_option['href'], f'/customers/{own.id}/')

        asset_response = self.client.post(create_option['assetCreateUrl'], {
            'asset_name': '디렉터리 직접 등록 장비',
            'status': 'active',
        })

        self.assertEqual(asset_response.status_code, 200)
        asset = CustomerAsset.objects.get(id=asset_response.json()['asset']['id'])
        self.assertEqual(asset.company, own.company)
        self.assertEqual(asset.department, own.department)
        self.assertEqual(asset.primary_followup, own)
        self.assertEqual(asset.created_by, self.user)

    def test_customer_asset_account_search_and_account_first_create_api(self):
        own = self._create_customer(self.user, '계정장비등록')
        coworker = self._create_customer(self.coworker, '동료계정장비등록')
        self.client.force_login(self.user)

        search_response = self.client.get(reverse('reporting:customer_asset_account_search_api'), {
            'q': coworker.department.name,
        })

        self.assertEqual(search_response.status_code, 200)
        search_payload = search_response.json()
        account_ids = {item['departmentId'] for item in search_payload['accounts']}
        self.assertIn(coworker.department_id, account_ids)
        account_payload = next(item for item in search_payload['accounts'] if item['departmentId'] == coworker.department_id)
        self.assertEqual(account_payload['assetCreateUrl'], reverse('reporting:customer_asset_directory_create_api'))
        self.assertEqual(account_payload['href'], f'/accounts/{coworker.department_id}/')
        self.assertTrue(any(contact['id'] == coworker.id for contact in account_payload['contacts']))

        create_response = self.client.post(reverse('reporting:customer_asset_directory_create_api'), {
            'department_id': str(coworker.department_id),
            'primary_followup_id': str(coworker.id),
            'asset_name': '계정 기준 등록 장비',
            'status': 'active',
            'serial_number': 'ACCOUNT-SN-1',
        })

        self.assertEqual(create_response.status_code, 200)
        asset = CustomerAsset.objects.get(id=create_response.json()['asset']['id'])
        self.assertEqual(asset.company, coworker.company)
        self.assertEqual(asset.department, coworker.department)
        self.assertEqual(asset.primary_followup, coworker)
        self.assertEqual(asset.created_by, self.user)
        self.assertEqual(create_response.json()['asset']['accountHref'], f'/accounts/{coworker.department_id}/')
        self.assertTrue(create_response.json()['asset']['contacts'])

        self.client.force_login(self.manager)
        manager_response = self.client.post(reverse('reporting:customer_asset_directory_create_api'), {
            'department_id': str(own.department_id),
            'asset_name': 'Manager 등록 시도',
            'status': 'active',
        })
        self.assertEqual(manager_response.status_code, 403)

    def test_customer_assets_summary_api_uses_manager_scope_and_metrics(self):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import CalibrationRecord, CustomerAsset, ServiceCase

        own = self._create_customer(self.user, '장비목록내고객')
        coworker = self._create_customer(self.coworker, '장비목록동료')
        other = self._create_customer(self.other_user, '장비목록타사')
        own_asset = CustomerAsset.objects.create(
            company=own.company,
            department=own.department,
            primary_followup=own,
            asset_name='Pipette Controller',
            model_name='PC-100',
            serial_number='PC-SN-001',
            created_by=self.user,
        )
        coworker_asset = CustomerAsset.objects.create(
            company=coworker.company,
            department=coworker.department,
            primary_followup=coworker,
            asset_name='동료 원심분리기',
            created_by=self.coworker,
        )
        other_asset = CustomerAsset.objects.create(
            company=other.company,
            department=other.department,
            primary_followup=other,
            asset_name='타사 장비',
            created_by=self.other_user,
        )
        ServiceCase.objects.create(
            asset=own_asset,
            followup=own,
            case_type='repair',
            status='waiting',
            priority='high',
            received_date=timezone.localdate(),
            due_date=timezone.localdate() - timedelta(days=1),
            created_by=self.user,
        )
        CalibrationRecord.objects.create(
            asset=own_asset,
            followup=own,
            calibration_date=timezone.localdate(),
            next_due_date=timezone.localdate() + timedelta(days=10),
            result='pass',
            created_by=self.user,
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:customer_assets_summary_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['canManage'])
        self.assertFalse(payload['create']['canCreate'])
        self.assertEqual(payload['create']['customers'], [])
        asset_ids = {item['id'] for item in payload['assets']}
        self.assertIn(own_asset.id, asset_ids)
        self.assertIn(coworker_asset.id, asset_ids)
        self.assertNotIn(other_asset.id, asset_ids)
        self.assertEqual(payload['metrics']['totalAssets'], 2)
        self.assertEqual(payload['metrics']['filteredAssets'], 2)
        self.assertEqual(payload['metrics']['openServiceAssets'], 1)
        self.assertEqual(payload['metrics']['dueCalibrationAssets'], 1)
        self.assertEqual(payload['metrics']['overdueCalibrationAssets'], 0)
        self.assertEqual(payload['metrics']['noCalibrationAssets'], 1)
        self.assertTrue(payload['scope']['canViewAll'])
        self.assertTrue(any(option['id'] == self.user.id for option in payload['options']['owners']))
        own_payload = next(item for item in payload['assets'] if item['id'] == own_asset.id)
        self.assertEqual(own_payload['customerHref'], f'/customers/{own.id}/')
        self.assertEqual(own_payload['ownerName'], self.user.username)

    def test_customer_assets_summary_api_filters_search_status_service_calibration(self):
        from datetime import timedelta
        from django.utils import timezone
        from reporting.models import CalibrationRecord, CustomerAsset, ServiceCase

        target = self._create_customer(self.user, 'PCR장비고객')
        other = self._create_customer(self.user, '다른장비고객')
        target_asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='PCR Cycler',
            model_name='PCR-200',
            serial_number='SN-PCR-200',
            status='active',
            created_by=self.user,
        )
        CustomerAsset.objects.create(
            company=other.company,
            department=other.department,
            primary_followup=other,
            asset_name='보관 장비',
            model_name='STORE-1',
            serial_number='STORE-001',
            status='inactive',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=target_asset,
            followup=target,
            case_type='inspection',
            status='received',
            priority='normal',
            received_date=timezone.localdate(),
            created_by=self.user,
        )
        CalibrationRecord.objects.create(
            asset=target_asset,
            followup=target,
            calibration_date=timezone.localdate(),
            next_due_date=timezone.localdate() + timedelta(days=20),
            result='pending',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_assets_summary_api'), {
            'q': 'SN-PCR',
            'status': 'active',
            'service': 'open',
            'calibration': 'due30',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['filters']['q'], 'SN-PCR')
        self.assertEqual(payload['filters']['status'], 'active')
        self.assertEqual(payload['filters']['service'], 'open')
        self.assertEqual(payload['filters']['calibration'], 'due30')
        self.assertEqual([item['id'] for item in payload['assets']], [target_asset.id])
        self.assertEqual(payload['assets'][0]['latestServiceCase']['caseType'], 'inspection')
        self.assertEqual(payload['assets'][0]['latestCalibration']['result'], 'pending')

    def test_customer_assets_summary_api_returns_work_queue_and_directory_links(self):
        target = self._create_customer(self.user, '장비큐고객')
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='Queue Pipette',
            model_name='QP-10',
            status='active',
            created_by=self.user,
        )
        ServiceCase.objects.create(
            asset=asset,
            followup=target,
            case_type='repair',
            status='waiting',
            priority='urgent',
            received_date=timezone.localdate() - timedelta(days=3),
            due_date=timezone.localdate() - timedelta(days=1),
            symptom='작동 불량',
            created_by=self.user,
            assigned_to=self.user,
        )
        CalibrationRecord.objects.create(
            asset=asset,
            followup=target,
            calibration_date=timezone.localdate(),
            next_due_date=timezone.localdate() + timedelta(days=5),
            result='pass',
            created_by=self.user,
            performed_by=self.user,
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:customer_assets_summary_api'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        asset_payload = next(item for item in payload['assets'] if item['id'] == asset.id)
        self.assertEqual(asset_payload['updateUrl'], reverse('reporting:customer_asset_directory_update_api', args=[asset.id]))
        self.assertEqual(
            asset_payload['serviceCaseCreateUrl'],
            reverse('reporting:customer_asset_directory_service_case_create_api', args=[asset.id]),
        )
        self.assertEqual(
            asset_payload['calibrationCreateUrl'],
            reverse('reporting:customer_asset_directory_calibration_create_api', args=[asset.id]),
        )
        self.assertTrue(asset_payload['latestServiceCase']['updateUrl'].endswith('/update/'))
        self.assertTrue(asset_payload['latestCalibration']['updateUrl'].endswith('/update/'))
        queue_kinds = {item['kind'] for item in payload['workQueue']}
        self.assertIn('service_overdue', queue_kinds)
        self.assertIn('calibration_due', queue_kinds)
        queue_item = next(item for item in payload['workQueue'] if item['kind'] == 'service_overdue')
        self.assertEqual(queue_item['assetId'], asset.id)
        self.assertEqual(queue_item['href'], f'/assets/?asset={asset.id}')
        self.assertEqual(asset_payload['accountHref'], f'/accounts/{target.department_id}/')
        self.assertTrue(asset_payload['serviceOverdue'])
        self.assertEqual(asset_payload['latestServiceCase']['lifecycleLabel'], '처리 지연')
        self.assertEqual(asset_payload['latestServiceCase']['reportLabel'], '리포트 없음')
        self.assertEqual(asset_payload['latestCalibration']['dueState'], 'due30')
        self.assertEqual(asset_payload['latestCalibration']['certificateLabel'], '성적서 없음')

    def test_customer_asset_directory_mutation_updates_asset_service_and_calibration(self):
        target = self._create_customer(self.user, '장비운영고객')
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='Old Asset',
            status='active',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        asset_response = self.client.post(reverse('reporting:customer_asset_directory_update_api', args=[asset.id]), {
            'asset_name': 'Updated Asset',
            'model_name': 'UA-200',
            'serial_number': 'UA-SN-1',
            'install_location': 'B동 4층',
            'status': 'inactive',
            'notes': '디렉터리에서 수정',
        })
        self.assertEqual(asset_response.status_code, 200)
        asset.refresh_from_db()
        self.assertEqual(asset.asset_name, 'Updated Asset')
        self.assertEqual(asset.status, 'inactive')
        self.assertEqual(asset_response.json()['asset']['updateUrl'], reverse('reporting:customer_asset_directory_update_api', args=[asset.id]))

        report_file = SimpleUploadedFile('service-report.pdf', b'%PDF-1.4 service report', content_type='application/pdf')
        service_response = self.client.post(reverse('reporting:customer_asset_directory_service_case_create_api', args=[asset.id]), {
            'case_type': 'inspection',
            'status': 'received',
            'priority': 'high',
            'received_date': timezone.localdate().isoformat(),
            'due_date': (timezone.localdate() + timedelta(days=2)).isoformat(),
            'symptom': '정기 점검 요청',
            'service_report': report_file,
        })
        self.assertEqual(service_response.status_code, 200)
        service_case = ServiceCase.objects.get(id=service_response.json()['serviceCase']['id'])
        self.assertEqual(service_case.asset, asset)
        self.assertEqual(service_case.followup, target)
        self.assertTrue(service_response.json()['serviceCase']['reportUrl'])

        service_update_response = self.client.post(
            reverse('reporting:customer_asset_directory_service_case_update_api', args=[asset.id, service_case.id]),
            {
                'case_type': 'inspection',
                'status': 'completed',
                'priority': 'normal',
                'received_date': timezone.localdate().isoformat(),
                'completed_date': timezone.localdate().isoformat(),
                'resolution': '점검 완료',
            },
        )
        self.assertEqual(service_update_response.status_code, 200)
        service_case.refresh_from_db()
        self.assertEqual(service_case.status, 'completed')
        self.assertEqual(service_case.priority, 'normal')

        certificate_file = SimpleUploadedFile('calibration-certificate.pdf', b'%PDF-1.4 certificate', content_type='application/pdf')
        calibration_response = self.client.post(reverse('reporting:customer_asset_directory_calibration_create_api', args=[asset.id]), {
            'calibration_date': timezone.localdate().isoformat(),
            'next_due_date': (timezone.localdate() + timedelta(days=365)).isoformat(),
            'result': 'adjusted',
            'notes': '현장 교정',
            'certificate_file': certificate_file,
        })
        self.assertEqual(calibration_response.status_code, 200)
        calibration = CalibrationRecord.objects.get(id=calibration_response.json()['calibration']['id'])
        self.assertEqual(calibration.asset, asset)
        self.assertEqual(calibration.followup, target)
        self.assertTrue(calibration_response.json()['calibration']['certificateUrl'])

        calibration_update_response = self.client.post(
            reverse('reporting:customer_asset_directory_calibration_update_api', args=[asset.id, calibration.id]),
            {
                'calibration_date': timezone.localdate().isoformat(),
                'next_due_date': (timezone.localdate() + timedelta(days=180)).isoformat(),
                'result': 'pass',
                'notes': '재확인 완료',
            },
        )
        self.assertEqual(calibration_update_response.status_code, 200)
        calibration.refresh_from_db()
        self.assertEqual(calibration.result, 'pass')
        self.assertEqual(calibration.notes, '재확인 완료')

        service_case.service_report.delete(save=False)
        calibration.certificate_file.delete(save=False)

    def test_customer_asset_directory_mutation_blocks_manager_and_other_scope(self):
        target = self._create_customer(self.user, '장비디렉터리권한')
        other_target = self._create_customer(self.other_user, '장비디렉터리타사')
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='권한 장비',
            created_by=self.user,
        )
        other_asset = CustomerAsset.objects.create(
            company=other_target.company,
            department=other_target.department,
            primary_followup=other_target,
            asset_name='타사 권한 장비',
            created_by=self.other_user,
        )
        payload = {
            'asset_name': '수정 시도',
            'status': 'active',
        }

        self.client.force_login(self.manager)
        manager_response = self.client.post(reverse('reporting:customer_asset_directory_update_api', args=[asset.id]), payload)
        self.assertEqual(manager_response.status_code, 403)
        self.assertFalse(manager_response.json()['success'])
        manager_service_response = self.client.post(reverse('reporting:customer_asset_directory_service_case_create_api', args=[asset.id]), {
            'case_type': 'service',
            'status': 'received',
            'priority': 'normal',
            'received_date': timezone.localdate().isoformat(),
        })
        self.assertEqual(manager_service_response.status_code, 403)

        self.client.force_login(self.user)
        other_response = self.client.post(reverse('reporting:customer_asset_directory_update_api', args=[other_asset.id]), payload)
        self.assertEqual(other_response.status_code, 404)

    def test_customer_asset_directory_file_downloads_are_scoped(self):
        target = self._create_customer(self.user, '장비파일고객')
        asset = CustomerAsset.objects.create(
            company=target.company,
            department=target.department,
            primary_followup=target,
            asset_name='File Asset',
            created_by=self.user,
        )
        service_case = ServiceCase.objects.create(
            asset=asset,
            followup=target,
            case_type='service',
            status='completed',
            priority='normal',
            received_date=timezone.localdate(),
            created_by=self.user,
            service_report=SimpleUploadedFile('scoped-report.txt', b'service report', content_type='text/plain'),
        )
        calibration = CalibrationRecord.objects.create(
            asset=asset,
            followup=target,
            calibration_date=timezone.localdate(),
            next_due_date=timezone.localdate() + timedelta(days=30),
            result='pass',
            created_by=self.user,
            certificate_file=SimpleUploadedFile('scoped-certificate.txt', b'certificate', content_type='text/plain'),
        )

        self.client.force_login(self.user)
        report_response = self.client.get(reverse('reporting:customer_asset_service_report_download_api', args=[service_case.id]))
        certificate_response = self.client.get(reverse('reporting:customer_asset_calibration_certificate_download_api', args=[calibration.id]))
        self.assertEqual(report_response.status_code, 200)
        self.assertIn('attachment', report_response.get('Content-Disposition', ''))
        self.assertEqual(certificate_response.status_code, 200)
        self.assertIn('attachment', certificate_response.get('Content-Disposition', ''))

        self.client.force_login(self.manager)
        manager_report_response = self.client.get(reverse('reporting:customer_asset_service_report_download_api', args=[service_case.id]))
        self.assertEqual(manager_report_response.status_code, 200)

        self.client.force_login(self.other_user)
        other_report_response = self.client.get(reverse('reporting:customer_asset_service_report_download_api', args=[service_case.id]))
        other_certificate_response = self.client.get(reverse('reporting:customer_asset_calibration_certificate_download_api', args=[calibration.id]))
        self.assertEqual(other_report_response.status_code, 404)
        self.assertEqual(other_certificate_response.status_code, 404)

        report_response.close()
        certificate_response.close()
        manager_report_response.close()
        service_case.service_report.delete(save=False)
        calibration.certificate_file.delete(save=False)

    def test_customer_detail_summary_api_excludes_customer_ai_payload(self):
        target = self._create_customer(self.user, 'AI제거고객', priority='urgent')
        profile = self.user.userprofile
        profile.can_use_ai = True
        profile.save(update_fields=['can_use_ai'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:customer_detail_summary_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn('aiDepartment', payload)
        self.assertIn('customer', payload)
        self.assertIn('assetSummary', payload)
        self.assertIn('recentNotes', payload)

    def test_account_detail_summary_api_includes_management_fields_and_contact_roles(self):
        from reporting.models import FollowUp

        target = self._create_customer(self.user, '계정관리필드', priority='urgent')
        target.department.address = '공용 계정 주소'
        target.department.notes = '공용 계정 메모'
        target.department.save(update_fields=['address', 'notes'])
        target.contact_role = FollowUp.CONTACT_ROLE_PI
        target.save(update_fields=['contact_role'])
        sibling = FollowUp.objects.create(
            user=self.user,
            user_company=self.company,
            customer_name='계정관리필드 세금담당',
            manager='세금 책임',
            company=target.company,
            department=target.department,
            contact_role=FollowUp.CONTACT_ROLE_TAX_INVOICE,
            is_active=False,
            priority='scheduled',
            pipeline_stage='contact',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:account_detail_summary_api', args=[target.department_id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        account = payload['account']
        self.assertEqual(account['address'], '공용 계정 주소')
        self.assertEqual(account['notes'], '공용 계정 메모')
        self.assertEqual(account['piContactName'], target.customer_name)
        self.assertEqual(account['contactCount'], 2)
        self.assertEqual(account['activeContactCount'], 1)
        self.assertEqual(account['inactiveContactCount'], 1)
        self.assertTrue(account['management']['canManage'])
        self.assertEqual(account['management']['accountSubmitUrl'], reverse('reporting:account_update_api', args=[target.department_id]))
        self.assertEqual(account['management']['contactCreateUrl'], reverse('reporting:account_contact_create_api', args=[target.department_id]))
        role_values = {option['value'] for option in account['management']['contactRoles']}
        self.assertEqual(role_values, {'pi', 'practitioner', 'purchasing', 'tax_invoice'})
        contacts = {contact['id']: contact for contact in account['contacts']}
        self.assertEqual(contacts[target.id]['contactRoleLabel'], 'PI')
        self.assertTrue(contacts[target.id]['isActive'])
        self.assertEqual(contacts[sibling.id]['contactRoleLabel'], '세금계산서 담당자')
        self.assertFalse(contacts[sibling.id]['isActive'])
        self.assertTrue(contacts[sibling.id]['updateUrl'].endswith(f'/contacts/{sibling.id}/update/'))

    def test_account_update_api_updates_department_info_and_contact_company(self):
        from reporting.models import Company, Department, FollowUp

        target = self._create_customer(self.user, '계정정보수정', priority='scheduled')
        next_company = Company.objects.create(name='계정정보수정 새회사', created_by=self.user)
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:account_update_api', args=[target.department_id]), {
            'company': str(next_company.id),
            'department_name': '계정정보수정 새연구실',
            'address': '새 계정 주소',
            'notes': '새 계정 메모',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        department = Department.objects.get(id=target.department_id)
        self.assertEqual(department.company, next_company)
        self.assertEqual(department.name, '계정정보수정 새연구실')
        self.assertEqual(department.address, '새 계정 주소')
        self.assertEqual(department.notes, '새 계정 메모')
        self.assertEqual(FollowUp.objects.get(id=target.id).company, next_company)

    def test_account_contact_api_creates_moves_and_inactivates_contact(self):
        from reporting.models import Department, FollowUp

        target = self._create_customer(self.user, '담당자관리', priority='urgent')
        other_department = Department.objects.create(
            company=target.company,
            name='담당자관리 이동연구실',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        create_response = self.client.post(reverse('reporting:account_contact_create_api', args=[target.department_id]), {
            'customer_name': '구매 담당자',
            'contact_role': FollowUp.CONTACT_ROLE_PURCHASING,
            'department': str(target.department_id),
            'priority': 'scheduled',
            'status': 'active',
            'pipeline_stage': 'contact',
            'phone_number': '010-2222-3333',
            'email': 'buyer@example.com',
            'is_active': 'true',
        })

        self.assertEqual(create_response.status_code, 200)
        created = FollowUp.objects.get(id=create_response.json()['followup_id'])
        self.assertEqual(created.department, target.department)
        self.assertEqual(created.contact_role, FollowUp.CONTACT_ROLE_PURCHASING)
        self.assertTrue(created.is_active)

        update_response = self.client.post(reverse('reporting:account_contact_update_api', args=[target.department_id, created.id]), {
            'customer_name': '세금 담당자',
            'contact_role': FollowUp.CONTACT_ROLE_TAX_INVOICE,
            'department': str(other_department.id),
            'priority': 'followup',
            'status': 'paused',
            'pipeline_stage': 'quote',
            'phone_number': '010-4444-5555',
            'email': 'tax@example.com',
            'is_active': 'false',
            'notes': '이동 및 비활성화',
        })

        self.assertEqual(update_response.status_code, 200)
        moved = FollowUp.objects.get(id=created.id)
        self.assertEqual(moved.customer_name, '세금 담당자')
        self.assertEqual(moved.department, other_department)
        self.assertEqual(moved.company, other_department.company)
        self.assertEqual(moved.contact_role, FollowUp.CONTACT_ROLE_TAX_INVOICE)
        self.assertFalse(moved.is_active)
        self.assertEqual(moved.status, 'paused')
        self.assertEqual(moved.pipeline_stage, 'quote')

    def test_account_management_api_blocks_manager(self):
        target = self._create_customer(self.user, '계정관리권한차단', priority='scheduled')
        self.client.force_login(self.manager)

        response = self.client.post(reverse('reporting:account_update_api', args=[target.department_id]), {
            'company': str(target.company_id),
            'department_name': target.department.name,
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

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

    def _create_quote_schedule(self, followup, owner, item_name, unit_price, quote_group=''):
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
            quote_group=quote_group,
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

    def test_quote_items_api_splits_same_schedule_by_quote_group(self):
        from reporting.models import DeliveryItem

        target = self._create_followup(self.user, '구분 선택 고객')
        quote_schedule = self._create_quote_schedule(
            target,
            self.user,
            '보상판매 품목',
            1000000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='수리 품목',
            quantity=1,
            unit_price=2000000,
            quote_group='수리',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['count'], 2)
        options_by_group = {item['quoteGroup']: item for item in payload['quotes']}
        self.assertEqual(set(options_by_group), {'보상판매', '수리'})
        self.assertEqual(options_by_group['보상판매']['optionId'], f'{quote_schedule.id}:보상판매')
        self.assertEqual(options_by_group['수리']['optionId'], f'{quote_schedule.id}:수리')
        self.assertEqual(options_by_group['보상판매']['quoteGroupLabel'], '보상판매')
        self.assertEqual(options_by_group['수리']['quoteGroupLabel'], '수리')
        self.assertEqual(options_by_group['보상판매']['scheduleId'], quote_schedule.id)
        self.assertEqual(options_by_group['수리']['scheduleId'], quote_schedule.id)
        self.assertEqual([item['itemName'] for item in options_by_group['보상판매']['items']], ['보상판매 품목'])
        self.assertEqual([item['itemName'] for item in options_by_group['수리']['items']], ['수리 품목'])

    def test_quote_items_api_returns_react_delivery_import_fields(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import DeliveryItem, Product, Schedule

        target = self._create_followup(self.user, 'React 납품')
        product = Product.objects.create(
            product_code='PIP-1000',
            unit='SET',
            specification='1000ul',
            description='피펫',
            standard_price=150000,
            created_by=self.user,
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            product=product,
            item_name='PIP-1000',
            quantity=3,
            unit_price=120000,
            discount_rate=5,
            tax_invoice_issued=True,
            quote_group='수리',
            notes='오링 교체',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        quote = payload['quotes'][0]
        quote_item = quote['items'][0]
        self.assertEqual(quote['id'], quote_schedule.id)
        self.assertEqual(quote['optionId'], f'{quote_schedule.id}:수리')
        self.assertEqual(quote['scheduleId'], quote_schedule.id)
        self.assertEqual(quote['quoteGroup'], '수리')
        self.assertEqual(quote['quoteGroupLabel'], '수리')
        self.assertEqual(quote['href'], f'/schedules/{quote_schedule.id}/')
        self.assertEqual(quote['djangoHref'], reverse('reporting:schedule_detail', args=[quote_schedule.id]))
        self.assertEqual(quote_item['id'], item.id)
        self.assertEqual(quote_item['itemName'], 'PIP-1000')
        self.assertEqual(quote_item['unit'], 'SET')
        self.assertEqual(quote_item['unitPrice'], 120000.0)
        self.assertEqual(quote_item['discountRate'], 5.0)
        self.assertEqual(quote_item['discountUnitPrice'], 114000.0)
        self.assertEqual(quote_item['effectiveUnitPrice'], 114000.0)
        self.assertEqual(quote_item['productId'], product.id)
        self.assertEqual(quote_item['productCode'], 'PIP-1000')
        self.assertEqual(quote_item['productDescription'], '피펫')
        self.assertEqual(quote_item['sourceQuoteScheduleId'], quote_schedule.id)
        self.assertEqual(quote_item['sourceQuoteItemId'], item.id)
        self.assertTrue(quote_item['taxInvoiceIssued'])
        self.assertEqual(quote_item['quoteGroup'], '수리')
        self.assertEqual(quote_item['quoteGroupLabel'], '수리')
        self.assertEqual(quote_item['notes'], '오링 교체')

    def test_quote_items_api_recovers_unit_price_from_legacy_total_price(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        target = self._create_followup(self.user, '레거시 총액 견적')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='총액만 있는 견적 품목',
            quantity=2,
            unit='EA',
            unit_price=10000,
            quote_group='수리',
        )
        DeliveryItem.objects.filter(pk=item.pk).update(unit_price=None, total_price=110000)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        quote = payload['quotes'][0]
        quote_item = quote['items'][0]
        self.assertEqual(quote['remainingAmount'], 110000.0)
        self.assertEqual(quote_item['totalPrice'], 110000.0)
        self.assertEqual(quote_item['remainingAmount'], 110000.0)
        self.assertEqual(quote_item['unitPrice'], 50000.0)
        self.assertEqual(quote_item['effectiveUnitPrice'], 50000.0)

    def test_quote_items_api_treats_legacy_zero_discount_unit_price_as_blank(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        target = self._create_followup(self.user, '할인단가0 견적')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='SO825.0002',
            quantity=1,
            unit='EA',
            unit_price=379950,
        )
        DeliveryItem.objects.filter(pk=item.pk).update(discount_rate=0, discount_unit_price=0, total_price=0)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        quote_item = payload['quotes'][0]['items'][0]
        self.assertIsNone(quote_item['discountUnitPrice'])
        self.assertEqual(quote_item['discountRate'], 0.0)
        self.assertEqual(quote_item['unitPrice'], 379950.0)
        self.assertEqual(quote_item['effectiveUnitPrice'], 379950.0)
        self.assertEqual(quote_item['totalPrice'], 417945.0)

    def test_quote_items_api_returns_remaining_items_after_partial_delivery_import(self):
        from datetime import time
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        target = self._create_followup(self.user, '부분 납품 고객')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            activity_type='quote',
            status='completed',
        )
        sold_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='판매된 견적 품목',
            quantity=1,
            unit='EA',
            unit_price=30000,
            quote_group='보상판매',
        )
        remaining_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='남은 견적 품목',
            quantity=1,
            unit='EA',
            unit_price=90000,
            quote_group='수리',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate(),
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            source_quote_schedule=quote_schedule,
            source_quote_item=sold_item,
            item_name='판매된 견적 품목',
            quantity=1,
            unit='EA',
            unit_price=30000,
            quote_group='보상판매',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['count'], 1)
        quote = payload['quotes'][0]
        self.assertEqual(quote['quoteGroup'], '수리')
        self.assertEqual(quote['items'][0]['id'], remaining_item.id)
        self.assertEqual(quote['items'][0]['sourceQuoteItemId'], remaining_item.id)

    def test_quote_items_api_exposes_partial_delivery_remaining_quantities(self):
        from datetime import time
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        target = self._create_followup(self.user, '동일 품목 부분 납품 고객')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            activity_type='quote',
            status='completed',
        )
        quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='부분 납품 견적 품목',
            quantity=3,
            unit='EA',
            unit_price=10000,
            quote_group='보상판매',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target,
            visit_date=timezone.localdate(),
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            source_quote_schedule=quote_schedule,
            source_quote_item=quote_item,
            item_name='부분 납품 견적 품목',
            quantity=1,
            unit='EA',
            unit_price=10000,
            quote_group='보상판매',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        quote = payload['quotes'][0]
        item = quote['items'][0]
        self.assertEqual(quote['deliveryStatus'], 'partial')
        self.assertEqual(quote['deliveryStatusLabel'], '부분 납품 잔여')
        self.assertTrue(quote['hasPartialDelivery'])
        self.assertEqual(quote['quotedAmount'], 33000.0)
        self.assertEqual(quote['deliveredAmount'], 11000.0)
        self.assertEqual(quote['remainingAmount'], 22000.0)
        self.assertEqual(item['originalQuantity'], 3.0)
        self.assertEqual(item['deliveredQuantity'], 1.0)
        self.assertEqual(item['remainingQuantity'], 2.0)
        self.assertEqual(item['quantity'], 2)

    def test_quote_items_api_bulk_progress_avoids_per_quote_queries(self):
        from datetime import time
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        target = self._create_followup(self.user, '대량 견적 고객')
        for index in range(8):
            quote_schedule = self._create_quote_schedule(
                target,
                self.user,
                f'완료 견적 품목 {index}',
                10000 + index,
                quote_group='수리',
            )
            quote_schedule.status = 'completed'
            quote_schedule.save(update_fields=['status'])
            quote_item = quote_schedule.delivery_items_set.first()
            quote_item.quantity = 2
            quote_item.save(update_fields=['quantity', 'total_price', 'updated_at'])
            if index % 2 == 0:
                delivery_schedule = Schedule.objects.create(
                    user=self.user,
                    company=self.company,
                    followup=target,
                    visit_date=timezone.localdate(),
                    visit_time=time(11, 0),
                    activity_type='delivery',
                    status='completed',
                )
                DeliveryItem.objects.create(
                    schedule=delivery_schedule,
                    source_quote_schedule=quote_schedule,
                    source_quote_item=quote_item,
                    item_name=quote_item.item_name,
                    quantity=1,
                    unit='EA',
                    unit_price=quote_item.unit_price,
                    quote_group='수리',
                )
        for index in range(4):
            self._create_quote_schedule(
                target,
                self.user,
                f'진행 견적 품목 {index}',
                20000 + index,
                quote_group='보상판매',
            )
        self.client.force_login(self.user)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['count'], 8)
        self.assertLessEqual(len(captured), 20)

    def test_quote_items_api_excludes_completed_quote_schedules(self):
        target = self._create_followup(self.user, '완료 제외 고객')
        completed = self._create_quote_schedule(target, self.user, '완료된 견적 품목', 1000000)
        completed.status = 'completed'
        completed.save(update_fields=['status'])
        scheduled = self._create_quote_schedule(target, self.user, '진행 중 견적 품목', 2000000)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:followup_quote_items_api', args=[target.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        schedule_ids = {item['scheduleId'] for item in payload['quotes']}
        self.assertEqual(schedule_ids, {scheduled.id})

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

    def test_notes_summary_api_labels_service_activity_as_memo(self):
        service_note = self._create_note(self.user, '서비스라벨', action_type='service')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        service_option = next(item for item in payload['options']['actionTypes'] if item['value'] == 'service')
        service_count = next(item for item in payload['actionCounts'] if item['value'] == 'service')
        note = next(item for item in payload['notes'] if item['id'] == service_note.id)
        self.assertEqual(service_option['label'], '메모')
        self.assertEqual(service_count['label'], '메모')
        self.assertEqual(note['actionLabel'], '메모')

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

    def test_notes_create_api_links_schedule_and_uses_schedule_date(self):
        from datetime import time, timedelta
        from reporting.models import History, Schedule

        target = self._create_note(self.user, '일정연결작성')
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=target.followup,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(10, 30),
            activity_type='customer_meeting',
        )
        other_target = self._create_note(self.user, '다른일정')
        other_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=other_target.followup,
            visit_date=timezone.localdate(),
            visit_time=time(11, 0),
            activity_type='customer_meeting',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': target.followup_id,
                'scheduleId': schedule.id,
                'actionType': 'customer_meeting',
                'content': '일정 상세에서 작성한 영업노트',
                'nextAction': '샘플 반응 확인',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        created = History.objects.get(pk=payload['historyId'])
        self.assertEqual(created.schedule_id, schedule.id)
        self.assertEqual(created.followup_id, target.followup_id)
        self.assertEqual(created.meeting_date, schedule.visit_date)
        self.assertEqual(payload['reactHref'], f'/notes/{created.id}/')

        mismatch_response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': target.followup_id,
                'scheduleId': other_schedule.id,
                'actionType': 'customer_meeting',
                'content': '잘못된 일정 연결',
            }),
            content_type='application/json',
        )
        self.assertEqual(mismatch_response.status_code, 400)
        self.assertIn('고객이 일치하지 않습니다', mismatch_response.json()['error'])

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
        self.assertEqual(target.meeting_situation, '')
        self.assertEqual(target.meeting_researcher_quote, '')
        self.assertEqual(target.meeting_confirmed_facts, '')
        self.assertEqual(target.meeting_obstacles, '')
        self.assertEqual(target.meeting_next_action, '')
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
        self.manager = make_user('prepayment_api_manager', role='manager', company=self.company)
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
            department=customer.department,
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

    def test_manager_prepayment_summary_defaults_to_company_scope_read_only(self):
        own = self._create_prepayment(self.user, '매니저회사내선결제', amount=100000, balance=70000, payer='내입금')
        coworker = self._create_prepayment(self.coworker, '매니저동료선결제', amount=200000, balance=50000, payer='동료입금')
        manager_owned = self._create_prepayment(self.manager, '매니저과거선결제', amount=300000, balance=300000, payer='매니저입금')
        other = self._create_prepayment(self.other_user, '매니저타사선결제', amount=999000, balance=999000, payer='타사입금')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['scope']['dataFilter'], 'all')
        self.assertTrue(payload['scope']['isViewingOthers'])
        ids = {item['id'] for item in payload['prepayments']}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertIn(manager_owned.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(payload['links']['create'], '')
        self.assertEqual(payload['metrics']['totalAmount'], 600000)
        owners = {item['ownerId']: item['ownerName'] for item in payload['prepayments']}
        self.assertEqual(owners[self.user.id], self.user.username)
        self.assertEqual(owners[self.coworker.id], self.coworker.username)
        self.assertEqual(owners[self.manager.id], self.manager.username)
        self.assertTrue(all(not item['canManage'] for item in payload['prepayments']))


class PrepaymentDetailApiTests(TestCase):
    """React 선결제 상세/등록/수정 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='선결제상세API회사')
        self.other_company = UserCompany.objects.create(name='선결제상세API타사회사')
        self.user = make_user('prepayment_detail_me', role='salesman', company=self.company)
        self.coworker = make_user('prepayment_detail_coworker', role='salesman', company=self.company)
        self.manager = make_user('prepayment_detail_manager', role='manager', company=self.company)
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
            department=customer.department,
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
            'department': str(customer.department_id),
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
        self.assertEqual(created.department, customer.department)
        self.assertEqual(payload['href'], f'/prepayments/{created.id}/')
        self.assertTrue(
            PrepaymentLedgerEntry.objects.filter(
                prepayment=created,
                department=customer.department,
                entry_type=PrepaymentLedgerEntry.ENTRY_DEPOSIT,
                amount=250000,
            ).exists()
        )

    def test_prepayment_create_api_allows_account_first_without_contact_payload(self):
        from reporting.models import Prepayment

        customer = self._create_customer(self.user, '계정우선등록')
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:prepayment_create_api'), {
            'department': str(customer.department_id),
            'amount': '180000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'payer_name': '계정 입금자',
        })

        self.assertEqual(response.status_code, 201)
        created = Prepayment.objects.get(id=response.json()['prepaymentId'])
        self.assertEqual(created.department, customer.department)
        self.assertEqual(created.customer, customer)
        self.assertEqual(response.json()['prepayment']['departmentId'], customer.department_id)

    def test_manager_cannot_create_or_manage_prepayments_even_when_owner(self):
        from reporting.models import Prepayment

        customer = self._create_customer(self.user, '매니저등록차단')
        self.client.force_login(self.manager)

        create_payload = self.client.get(reverse('reporting:prepayment_create_api')).json()
        self.assertFalse(create_payload['create']['canCreate'])
        self.assertEqual(create_payload['create']['submitUrl'], '')

        response = self.client.post(reverse('reporting:prepayment_create_api'), {
            'department': str(customer.department_id),
            'customer': str(customer.id),
            'amount': '250000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'payer_name': '매니저 입금자',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Prepayment.objects.filter(payer_name='매니저 입금자').exists())

        manager_owned = self._create_prepayment(self.manager, name='매니저과거소유')
        detail = self.client.get(reverse('reporting:prepayment_detail_api', args=[manager_owned.id]))
        self.assertEqual(detail.status_code, 200)
        detail_payload = detail.json()
        self.assertFalse(detail_payload['edit']['canEdit'])
        self.assertFalse(detail_payload['actions']['canCancel'])
        self.assertFalse(detail_payload['actions']['canDelete'])
        self.assertFalse(detail_payload['actions']['canTransfer'])
        self.assertIn('Manager 계정', detail_payload['edit']['message'])

        denied_update = self.client.post(reverse('reporting:prepayment_update_api', args=[manager_owned.id]), {
            'department': str(manager_owned.customer.department_id),
            'customer': str(manager_owned.customer_id),
            'amount': '100000',
            'balance': '70000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'status': 'active',
        })
        self.assertEqual(denied_update.status_code, 403)

        denied_cancel = self.client.post(reverse('reporting:prepayment_cancel_api', args=[manager_owned.id]), {
            'cancel_reason': '매니저 취소 시도',
        })
        self.assertEqual(denied_cancel.status_code, 403)

        denied_delete = self.client.post(reverse('reporting:prepayment_delete_api', args=[manager_owned.id]))
        self.assertEqual(denied_delete.status_code, 403)

        denied_transfer = self.client.post(reverse('reporting:prepayment_transfer_api', args=[manager_owned.id]), {
            'target_user': str(self.coworker.id),
            'reason': '매니저 이관 시도',
        })
        self.assertEqual(denied_transfer.status_code, 403)
        manager_owned.refresh_from_db()
        self.assertEqual(manager_owned.created_by, self.manager)

    def test_prepayment_update_api_only_owner_and_validates_balance(self):
        prepayment = self._create_prepayment(self.user, amount=100000, balance=80000)

        self.client.force_login(self.coworker)
        denied = self.client.post(reverse('reporting:prepayment_update_api', args=[prepayment.id]), {
            'department': str(prepayment.customer.department_id),
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
            'department': str(prepayment.customer.department_id),
            'customer': str(prepayment.customer_id),
            'amount': '100000',
            'balance': '120000',
            'payment_date': '2026-05-10',
            'payment_method': 'transfer',
            'status': 'active',
        })
        self.assertEqual(invalid.status_code, 400)

        response = self.client.post(reverse('reporting:prepayment_update_api', args=[prepayment.id]), {
            'department': str(prepayment.customer.department_id),
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
        self.assertTrue(
            PrepaymentLedgerEntry.objects.filter(
                prepayment=prepayment,
                entry_type=PrepaymentLedgerEntry.ENTRY_ADJUSTMENT,
                balance_before=80000,
                balance_after=70000,
            ).exists()
        )

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
        self.assertTrue(
            PrepaymentLedgerEntry.objects.filter(
                prepayment=prepayment,
                entry_type=PrepaymentLedgerEntry.ENTRY_CANCELLATION,
                memo='React 취소',
            ).exists()
        )

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
        self.assertTrue(
            PrepaymentLedgerEntry.objects.filter(
                prepayment=prepayment,
                entry_type=PrepaymentLedgerEntry.ENTRY_TRANSFER,
                actor=self.user,
                target_user=self.coworker,
            ).exists()
        )

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
            department=customer.department,
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
        self.assertEqual(payload['links']['reactAccount'], f'/prepayments/account/{department.id}/')
        self.assertEqual(payload['links']['reactCustomer'], f'/prepayments/customer/{first.id}/')
        self.assertEqual(payload['links']['accountDetail'], f'/accounts/{department.id}/')
        self.assertEqual(payload['links']['djangoExcel'], reverse('reporting:prepayment_customer_excel', args=[first.id]))
        self.assertEqual(payload['prepayments'][0]['customerPrepaymentHref'], f'/prepayments/account/{department.id}/')

    def test_account_prepayment_api_returns_department_scope_and_metrics(self):
        from datetime import time
        from reporting.models import DeliveryItem, PrepaymentLedgerEntry, PrepaymentUsage, Schedule

        _company, department, first, second = self._create_department_customers()
        first_prepayment = self._create_prepayment(self.user, first, amount=110000, balance=90000, status='active', payer='계정 첫 입금')
        self._create_prepayment(self.user, second, amount=220000, balance=20000, status='active', payer='계정 둘째 입금')
        self._create_prepayment(self.coworker, first, amount=500000, balance=500000, payer='동료 입금')
        schedule = Schedule.objects.create(
            user=self.user,
            followup=first,
            visit_date=timezone.localdate(),
            visit_time=time(10, 30),
            activity_type='delivery',
            status='completed',
            use_prepayment=True,
            prepayment=first_prepayment,
            prepayment_amount=20000,
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='계정 차감 품목',
            quantity=1,
            unit='EA',
            unit_price=20000,
            total_price=20000,
        )
        usage = PrepaymentUsage.objects.create(
            prepayment=first_prepayment,
            schedule=schedule,
            product_name='계정 차감 품목',
            quantity=1,
            amount=20000,
            remaining_balance=90000,
        )
        PrepaymentLedgerEntry.objects.create(
            prepayment=first_prepayment,
            department=department,
            customer=first,
            schedule=schedule,
            usage=usage,
            entry_type=PrepaymentLedgerEntry.ENTRY_DELIVERY_DEDUCTION,
            amount=20000,
            balance_before=110000,
            balance_after=90000,
            actor=self.user,
            memo='계정 차감 테스트',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:prepayment_account_api', args=[department.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['scope']['mode'], 'department')
        self.assertEqual(payload['customer']['departmentId'], department.id)
        self.assertEqual(payload['scope']['targetUserId'], self.user.id)
        self.assertEqual(payload['metrics']['totalAmount'], 330000)
        self.assertEqual(payload['metrics']['totalBalance'], 110000)
        self.assertEqual(payload['metrics']['totalUsed'], 220000)
        self.assertEqual(payload['metrics']['deductionCount'], 1)
        self.assertGreaterEqual(payload['metrics']['ledgerCount'], 1)
        self.assertEqual([item['customerId'] for item in payload['prepayments']], [first.id, second.id])
        self.assertEqual(payload['balanceRows'][0]['departmentId'], department.id)
        self.assertEqual(payload['deductionRows'][0]['amount'], 20000)
        self.assertEqual(payload['deductionRows'][0]['deliveryItems'][0]['itemName'], '계정 차감 품목')
        self.assertEqual(payload['ledgerEntries'][0]['entryType'], PrepaymentLedgerEntry.ENTRY_DELIVERY_DEDUCTION)
        self.assertEqual(payload['links']['reactAccount'], f'/prepayments/account/{department.id}/')
        self.assertEqual(payload['links']['accountDetail'], f'/accounts/{department.id}/')
        self.assertEqual(payload['links']['accountExcel'], reverse('reporting:prepayment_account_excel', args=[department.id]))

        excel_response = self.client.get(reverse('reporting:prepayment_account_excel', args=[department.id]))
        self.assertEqual(excel_response.status_code, 200)
        self.assertIn('spreadsheetml.sheet', excel_response['Content-Type'])

    def test_account_prepayment_api_allows_salesman_with_own_prepayment_and_blocks_unrelated(self):
        _company, department, first, _second = self._create_department_customers(owner=self.coworker)
        self._create_prepayment(self.user, first, amount=90000, balance=50000, payer='계정 접근 허용 입금')

        self.client.force_login(self.user)
        allowed = self.client.get(reverse('reporting:prepayment_account_api', args=[department.id]))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()['metrics']['totalAmount'], 90000)

        self.client.force_login(self.other_user)
        blocked = self.client.get(reverse('reporting:prepayment_account_api', args=[department.id]))
        self.assertEqual(blocked.status_code, 403)

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

    def test_customer_prepayment_api_manager_defaults_to_company_all_users(self):
        _company, _department, first, _second = self._create_department_customers()
        self._create_prepayment(self.user, first, amount=100000, balance=100000, payer='내 입금')
        self._create_prepayment(self.coworker, first, amount=250000, balance=150000, payer='동료 입금')
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:prepayment_customer_api', args=[first.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['scope']['canSelectUser'])
        self.assertTrue(payload['scope']['isAllUsers'])
        self.assertIsNone(payload['scope']['targetUserId'])
        self.assertEqual(payload['metrics']['totalAmount'], 350000)
        owner_ids = {item['ownerId'] for item in payload['prepayments']}
        self.assertEqual(owner_ids, {self.user.id, self.coworker.id})
        self.assertTrue(all(not item['canManage'] for item in payload['prepayments']))

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


class ServiceCasesSummaryApiTests(TestCase):
    """React 서비스 기록 목록 API 검증"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='서비스API회사')
        self.other_company = UserCompany.objects.create(name='서비스API타사회사')
        self.user = make_user('service_api_me', role='salesman', company=self.company)
        self.coworker = make_user('service_api_coworker', role='salesman', company=self.company)
        self.manager = make_user('service_api_manager', role='manager', company=self.company)
        self.other_user = make_user('service_api_other', role='salesman', company=self.other_company)
        self.url = reverse('reporting:service_cases_summary_api')

    def _create_customer_asset(self, owner, name):
        crm_company = Company.objects.create(name=f'{name} 업체', created_by=owner)
        department = Department.objects.create(
            company=crm_company,
            name=f'{name} 연구실',
            created_by=owner,
        )
        followup = FollowUp.objects.create(
            user=owner,
            user_company=owner.userprofile.company,
            customer_name=f'{name} 담당자',
            manager=f'{name} PI',
            company=crm_company,
            department=department,
        )
        asset = CustomerAsset.objects.create(
            company=crm_company,
            department=department,
            primary_followup=followup,
            asset_name=f'{name} 장비',
            model_name=f'{name} 모델',
            serial_number=f'{name}-SN',
            created_by=owner,
        )
        return followup, asset

    def _create_service_case(self, owner, name, status='received', priority='normal', case_type='service'):
        followup, asset = self._create_customer_asset(owner, name)
        return ServiceCase.objects.create(
            asset=asset,
            followup=followup,
            case_type=case_type,
            status=status,
            priority=priority,
            received_date=timezone.localdate(),
            due_date=timezone.localdate() - timedelta(days=1),
            symptom=f'{name} 증상',
            resolution=f'{name} 처리',
            assigned_to=owner,
            created_by=owner,
        )

    def test_service_cases_summary_api_requires_login_json(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'login_required')

    def test_service_cases_summary_api_lists_and_filters_records(self):
        target = self._create_service_case(
            self.user,
            'PCR',
            status='in_progress',
            priority='urgent',
            case_type='repair',
        )
        self._create_service_case(self.user, '다른', status='completed', priority='normal', case_type='service')
        self.client.force_login(self.user)

        response = self.client.get(self.url, {
            'q': 'PCR',
            'status': 'open',
            'priority': 'urgent',
            'case_type': 'repair',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['filters']['q'], 'PCR')
        self.assertEqual(payload['filters']['caseType'], 'repair')
        self.assertEqual(payload['metrics']['filteredCases'], 1)
        self.assertEqual(payload['serviceCases'][0]['id'], target.id)
        self.assertEqual(payload['serviceCases'][0]['assetName'], 'PCR 장비')
        self.assertEqual(payload['serviceCases'][0]['companyName'], 'PCR 업체')
        self.assertTrue(payload['serviceCases'][0]['overdue'])
        self.assertTrue(any(option['value'] == 'open' for option in payload['options']['statuses']))

    def test_service_cases_summary_api_manager_sees_same_company_only(self):
        own = self._create_service_case(self.user, '내서비스')
        coworker = self._create_service_case(self.coworker, '동료서비스')
        other = self._create_service_case(self.other_user, '타사서비스')
        self.client.force_login(self.manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['serviceCases']}
        self.assertIn(own.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(payload['metrics']['totalCases'], 2)
        self.assertTrue(payload['scope']['canViewAll'])


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
        self.personal_create_url = reverse('reporting:personal_schedules_create_api')

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
        self.assertFalse(any(option['value'] == 'service' for option in payload['options']['activityTypes']))
        self.assertEqual(payload['metrics']['filteredSchedules'], 1)

    def test_schedules_summary_api_excludes_service_schedule_type(self):
        self._create_schedule(self.user, '미팅일정', activity_type='customer_meeting')
        service_schedule = self._create_schedule(self.user, '서비스일정', activity_type='service')
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['schedules'] if item['type'] == 'customer'}
        self.assertNotIn(service_schedule.id, ids)
        self.assertFalse(any(option['value'] == 'service' for option in payload['create']['activityTypes']))
        self.assertFalse(any(item['value'] == 'service' for item in payload['activityCounts']))
        self.assertEqual(payload['metrics']['customerSchedules'], 1)

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
        self.assertEqual(own_item['deleteHref'], reverse('reporting:schedule_delete', args=[own.id]))
        self.assertEqual(
            {option['value'] for option in own_item['statusOptions']},
            {'scheduled', 'completed', 'cancelled'},
        )
        self.assertEqual(own_item['reports'][0]['id'], report.id)
        self.assertEqual(own_item['reports'][0]['content'], '캘린더에서 보여줄 미팅 보고 본문')
        self.assertEqual(own_item['reports'][0]['meetingSituation'], 'PCR 장비 도입 검토 중')
        self.assertEqual(own_item['reports'][0]['meetingConfirmedFacts'], '예산 담당자 확인')
        self.assertEqual(own_item['reports'][0]['nextAction'], '견적서 송부')
        self.assertTrue(personal_item['canEdit'])
        self.assertEqual(personal_item['deleteHref'], reverse('reporting:personal_schedules_delete_api', args=[personal.id]))
        self.assertEqual(personal_item['djangoEditHref'], reverse('reporting:personal_schedule_edit', args=[personal.id]))
        self.assertEqual(personal_item['statusOptions'], [])
        self.assertEqual(personal_item['reports'], [])
        self.assertEqual(payload['filters']['start'], '2026-05-01')
        self.assertEqual(payload['filters']['end'], '2026-05-31')
        self.assertEqual(payload['metrics']['totalSchedules'], 2)
        self.assertEqual(payload['links']['calendar'], '/schedules/calendar/')
        self.assertEqual(payload['links']['djangoCalendar'], reverse('reporting:schedule_calendar'))
        self.assertTrue(payload['create']['canCreate'])
        self.assertEqual(payload['create']['submitUrl'], self.create_url)
        self.assertFalse(any(option['value'] == 'service' for option in payload['create']['activityTypes']))
        self.assertEqual(payload['create']['personalSchedule']['submitUrl'], self.personal_create_url)
        self.assertTrue(any(customer['id'] == own.followup_id for customer in payload['create']['customers']))

    def test_schedules_calendar_api_excludes_service_schedule_type(self):
        import datetime

        target_date = datetime.date(2026, 5, 10)
        meeting = self._create_schedule(self.user, '월간미팅', activity_type='customer_meeting', visit_date=target_date)
        service = self._create_schedule(self.user, '월간서비스', activity_type='service', visit_date=target_date)
        self.client.force_login(self.user)

        response = self.client.get(self.calendar_url, {
            'start': '2026-05-01',
            'end': '2026-05-31',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['schedules'] if item['type'] == 'customer'}
        self.assertIn(meeting.id, ids)
        self.assertNotIn(service.id, ids)
        self.assertEqual(payload['metrics']['customerSchedules'], 1)

    def test_schedules_calendar_api_all_filter_uses_same_company_only(self):
        import datetime

        target_date = datetime.date(2026, 5, 10)
        own = self._create_schedule(self.user, '회사내월간일정', visit_date=target_date)
        coworker = self._create_schedule(self.coworker, '동료월간일정', visit_date=target_date)
        own_personal = self._create_personal_schedule(self.user, '회사내개인월간일정', schedule_date=target_date)
        coworker_personal = self._create_personal_schedule(self.coworker, '동료개인월간일정', schedule_date=target_date)
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
        self.assertEqual(coworker_item['deleteHref'], '')
        own_personal_item = next(item for item in payload['schedules'] if item['type'] == 'personal' and item['id'] == own_personal.id)
        coworker_personal_item = next(item for item in payload['schedules'] if item['type'] == 'personal' and item['id'] == coworker_personal.id)
        self.assertTrue(own_personal_item['canEdit'])
        self.assertEqual(own_personal_item['deleteHref'], reverse('reporting:personal_schedules_delete_api', args=[own_personal.id]))
        self.assertFalse(coworker_personal_item['canEdit'])
        self.assertEqual(coworker_personal_item['deleteHref'], '')
        self.assertEqual(payload['scope']['dataFilter'], 'all')
        self.assertTrue(any(option['id'] == self.coworker.id for option in payload['options']['users']))

    def test_schedules_calendar_api_manager_defaults_to_company_scope_without_me_filter(self):
        import datetime

        target_date = datetime.date(2026, 5, 10)
        manager_schedule = self._create_schedule(self.manager, '매니저월간일정', visit_date=target_date)
        coworker = self._create_schedule(self.coworker, '직원월간일정', visit_date=target_date)
        other = self._create_schedule(self.other_user, '타사회사월간일정', visit_date=target_date)
        self.client.force_login(self.manager)

        response = self.client.get(self.calendar_url, {
            'start': '2026-05-01',
            'end': '2026-05-31',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item['id'] for item in payload['schedules'] if item['type'] == 'customer'}
        self.assertIn(manager_schedule.id, ids)
        self.assertIn(coworker.id, ids)
        self.assertNotIn(other.id, ids)
        self.assertEqual(payload['scope']['dataFilter'], 'all')
        self.assertEqual(payload['filters']['dataFilter'], 'all')
        filter_options = payload['options']['dataFilters']
        self.assertEqual(filter_options[0], {'value': 'all', 'label': '직원전체'})
        self.assertFalse(any(option['value'] == 'me' for option in filter_options))
        self.assertFalse(payload['create']['canCreate'])

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

    def test_personal_schedules_create_api_salesman_creates_own_schedule(self):
        import json
        from reporting.models import History, PersonalSchedule

        self.client.force_login(self.user)

        response = self.client.post(
            self.personal_create_url,
            data=json.dumps({
                'title': 'React 개인 일정',
                'content': 'React 개인 일정 내용',
                'scheduleDate': '2026-05-10',
                'scheduleTime': '10:30',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload['success'])
        personal_schedule = PersonalSchedule.objects.get(pk=payload['scheduleId'])
        self.assertEqual(personal_schedule.user, self.user)
        self.assertEqual(personal_schedule.company, self.company)
        self.assertEqual(personal_schedule.title, 'React 개인 일정')
        self.assertEqual(personal_schedule.schedule_date.isoformat(), '2026-05-10')
        self.assertEqual(personal_schedule.schedule_time.strftime('%H:%M'), '10:30')
        self.assertEqual(payload['schedule']['id'], personal_schedule.id)
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(
            payload['edit']['submitUrl'],
            reverse('reporting:personal_schedules_update_api', args=[personal_schedule.id]),
        )
        self.assertTrue(History.objects.filter(
            personal_schedule=personal_schedule,
            parent_history__isnull=True,
            content='개인 일정: React 개인 일정',
        ).exists())

    def test_personal_schedules_create_api_blocks_manager(self):
        import json
        from reporting.models import PersonalSchedule

        self.client.force_login(self.manager)

        response = self.client.post(
            self.personal_create_url,
            data=json.dumps({
                'title': '매니저 개인 일정',
                'scheduleDate': '2026-05-10',
                'scheduleTime': '10:30',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(PersonalSchedule.objects.filter(title='매니저 개인 일정').exists())

    def test_personal_schedules_update_and_delete_api_are_owner_only(self):
        import json
        from reporting.models import History, PersonalSchedule

        personal_schedule = self._create_personal_schedule(self.user, '수정전 개인 일정')
        History.objects.create(
            user=self.user,
            company=self.company,
            personal_schedule=personal_schedule,
            action_type='memo',
            content='개인 일정: 수정전 개인 일정',
            created_by=self.user,
        )
        update_url = reverse('reporting:personal_schedules_update_api', args=[personal_schedule.id])
        delete_url = reverse('reporting:personal_schedules_delete_api', args=[personal_schedule.id])

        self.client.force_login(self.coworker)
        blocked_update = self.client.post(
            update_url,
            data=json.dumps({
                'title': '동료 수정 시도',
                'scheduleDate': '2026-05-11',
                'scheduleTime': '11:30',
            }),
            content_type='application/json',
        )
        self.assertEqual(blocked_update.status_code, 403)
        blocked_delete = self.client.post(delete_url)
        self.assertEqual(blocked_delete.status_code, 403)
        self.assertTrue(PersonalSchedule.objects.filter(pk=personal_schedule.id).exists())

        self.client.force_login(self.user)
        response = self.client.post(
            update_url,
            data=json.dumps({
                'title': '수정후 개인 일정',
                'content': '수정된 개인 일정 내용',
                'scheduleDate': '2026-05-11',
                'scheduleTime': '11:30',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        personal_schedule.refresh_from_db()
        self.assertEqual(personal_schedule.title, '수정후 개인 일정')
        self.assertEqual(personal_schedule.content, '수정된 개인 일정 내용')
        self.assertEqual(personal_schedule.schedule_date.isoformat(), '2026-05-11')
        self.assertEqual(personal_schedule.schedule_time.strftime('%H:%M'), '11:30')
        self.assertEqual(
            History.objects.get(personal_schedule=personal_schedule, parent_history__isnull=True).content,
            '개인 일정: 수정후 개인 일정',
        )

        delete_response = self.client.post(delete_url)
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()['success'])
        self.assertFalse(PersonalSchedule.objects.filter(pk=personal_schedule.id).exists())

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

    def test_schedules_create_api_rejects_service_activity_type(self):
        import json
        from reporting.models import Schedule

        followup = self._create_customer(self.user, '서비스차단')
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            data=json.dumps({
                'followupId': followup.id,
                'activityType': 'service',
                'visitDate': '2026-05-10',
                'visitTime': '10:30',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Schedule.objects.filter(followup=followup, activity_type='service').exists())

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
        self.assertEqual(payload['schedule']['quoteGroupNotes'][0]['notes'], '전체 견적 기타사항')
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
        self.assertEqual(payload['links']['deleteSchedule'], reverse('reporting:schedule_delete', args=[schedule.id]))
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
        self.assertIn('거래명세서 PDF', payload['documents']['autoAttachLabel'])

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
        self.assertIn('견적서 PDF', quote_payload['documents']['autoAttachLabel'])
        self.assertEqual(
            quote_payload['documents']['items'][0]['formats'][1]['href'],
            reverse('reporting:generate_document_pdf_format', args=['quotation', quote_schedule.id, 'xlsx']),
        )
        self.assertFalse(meeting_payload['documents']['canGenerate'])
        self.assertEqual(meeting_payload['documents']['items'], [])
        self.assertEqual(meeting_payload['documents']['autoAttachLabel'], '')

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

    def test_schedules_detail_api_includes_quote_commercial_checks(self):
        import datetime
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        quote_schedule = self._create_schedule(
            self.user,
            '견적정합성',
            activity_type='quote',
            status='completed',
        )
        delivered_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Trade In PCR',
            quantity=2,
            unit='EA',
            unit_price=100000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Repair Buffer',
            quantity=1,
            unit='EA',
            unit_price=50000,
            quote_group='수리',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=quote_schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(11, 0),
            activity_type='delivery',
            status='scheduled',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            source_quote_schedule=quote_schedule,
            source_quote_item=delivered_item,
            item_name='Trade In PCR',
            quantity=1,
            unit='EA',
            unit_price=100000,
            quote_group='보상판매',
        )
        log = DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=quote_schedule,
            user=self.user,
            transaction_number='Q-CHECK-001',
            output_format='pdf',
            file=SimpleUploadedFile('trade-in-quote.pdf', b'%PDF quote', content_type='application/pdf'),
            filename='trade-in-quote.pdf',
            file_size=10,
            quote_group='보상판매',
        )
        self.addCleanup(log.file.delete, False)
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[quote_schedule.id]))

        self.assertEqual(response.status_code, 200)
        checks = response.json()['commercialChecks']
        self.assertTrue(checks['applies'])
        self.assertEqual(checks['kind'], 'quote')
        self.assertEqual(checks['summary']['quoteGroupCount'], 2)
        self.assertEqual(checks['summary']['quoteItemCount'], 2)
        self.assertEqual(checks['summary']['quoteAmount'], 275000)
        self.assertEqual(checks['summary']['deliveredAmount'], 110000)
        self.assertEqual(checks['summary']['remainingAmount'], 165000)
        groups = {group['quoteGroup']: group for group in checks['quoteGroups']}
        self.assertEqual(groups['보상판매']['registeredQuotationCount'], 1)
        self.assertEqual(groups['보상판매']['fulfillmentStatus'], 'partial')
        self.assertEqual(groups['보상판매']['deliveredAmount'], 110000)
        self.assertEqual(groups['보상판매']['remainingAmount'], 110000)
        self.assertEqual(groups['수리']['registeredQuotationCount'], 0)
        codes = [warning['code'] for warning in checks['warnings']]
        self.assertIn('missing_registered_quotation', codes)
        self.assertIn('missing_auto_attach_candidate', codes)
        self.assertIn('completed_quote_still_importable', codes)

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

    def test_schedules_detail_api_includes_delivery_commercial_checks(self):
        from reporting.models import DeliveryItem, History

        schedule = self._create_schedule(self.user, '납품정합성', activity_type='delivery')
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='PCR Kit',
            quantity=2,
            unit='EA',
            unit_price=100000,
            discount_rate=10,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            schedule=schedule,
            action_type='delivery_schedule',
            delivery_items='PCR Kit 2EA',
            delivery_amount=1000,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 200)
        checks = response.json()['commercialChecks']
        self.assertTrue(checks['applies'])
        self.assertEqual(checks['kind'], 'delivery')
        self.assertEqual(checks['summary']['deliveryItemCount'], 1)
        self.assertEqual(checks['summary']['deliveryAmount'], 198000)
        self.assertFalse(checks['summary']['autoAttachReady'])
        self.assertEqual(checks['delivery']['autoAttachStatus'], 'missing')
        self.assertEqual(checks['delivery']['historyAmountMismatches'][0]['noteAmount'], 1000)
        self.assertEqual(checks['delivery']['historyAmountMismatches'][0]['itemAmount'], 198000)
        codes = [warning['code'] for warning in checks['warnings']]
        self.assertIn('missing_auto_attach_candidate', codes)
        self.assertIn('delivery_note_amount_mismatch', codes)

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
        self.assertEqual(response.json()['links']['deleteSchedule'], '')

        self.client.force_login(self.other_user)
        denied = self.client.get(reverse('reporting:schedules_detail_api', args=[schedule.id]))
        self.assertEqual(denied.status_code, 403)

    def test_schedule_delete_ajax_allows_owner_and_removes_related_history(self):
        from reporting.models import History, Schedule

        schedule = self._create_schedule(self.user, '삭제일정', activity_type='delivery')
        related_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            schedule=schedule,
            action_type='delivery_schedule',
            content='삭제될 납품 기록',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedule_delete', args=[schedule.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertFalse(Schedule.objects.filter(pk=schedule.id).exists())
        self.assertFalse(History.objects.filter(pk=related_history.id).exists())

    def test_schedule_delete_ajax_blocks_non_owner(self):
        from reporting.models import Schedule

        schedule = self._create_schedule(self.user, '타인삭제차단')
        self.client.force_login(self.coworker)

        response = self.client.post(
            reverse('reporting:schedule_delete', args=[schedule.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])
        self.assertTrue(Schedule.objects.filter(pk=schedule.id).exists())

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
                'quoteGroupNotes': {
                    '보상판매': '보상판매 기타사항',
                    '수리': '수리 기타사항',
                },
                'items': [
                    {
                        'itemName': 'PCR Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '100000',
                        'discountRate': '10',
                        'taxInvoiceIssued': True,
                        'quoteGroup': '보상판매',
                        'notes': 'PCR 적요',
                    },
                    {
                        'itemName': 'Buffer',
                        'quantity': 3,
                        'unit': 'BOX',
                        'unitPrice': '',
                        'taxInvoiceIssued': False,
                        'quoteGroup': '수리',
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
        self.assertEqual(items[0].quote_group, '보상판매')
        self.assertEqual(items[0].notes, 'PCR 적요')
        self.assertIsNone(items[1].unit_price)
        self.assertEqual(items[1].quote_group, '수리')
        schedule.refresh_from_db()
        self.assertEqual(schedule.quote_extra_notes, '')
        self.assertEqual(
            {
                note.quote_group: note.notes
                for note in ScheduleQuoteGroupNote.objects.filter(schedule=schedule)
            },
            {'보상판매': '보상판매 기타사항', '수리': '수리 기타사항'},
        )
        history.refresh_from_db()
        self.assertIn('PCR Kit', history.delivery_items)
        self.assertIn('Buffer', history.delivery_items)
        self.assertEqual(int(history.delivery_amount), 198000)
        self.assertEqual(payload['deliveryItems'][0]['itemName'], 'PCR Kit')
        self.assertEqual(payload['deliveryItems'][0]['discountRate'], 10.0)
        self.assertEqual(payload['deliveryItems'][0]['discountUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['effectiveUnitPrice'], 90000)
        self.assertEqual(payload['deliveryItems'][0]['totalPrice'], 198000)
        self.assertEqual(payload['deliveryItems'][0]['quoteGroup'], '보상판매')
        self.assertEqual(payload['deliveryItems'][0]['notes'], 'PCR 적요')
        self.assertIsNone(payload['deliveryItems'][1]['unitPrice'])
        self.assertIsNone(payload['deliveryItems'][1]['discountUnitPrice'])
        self.assertEqual(
            {note['quoteGroup']: note['notes'] for note in payload['schedule']['quoteGroupNotes']},
            {'보상판매': '보상판매 기타사항', '수리': '수리 기타사항'},
        )

    def test_schedule_delivery_items_update_api_applies_reapplies_and_restores_prepayment(self):
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Prepayment, PrepaymentUsage

        schedule = self._create_schedule(self.user, '납품품목선결제', activity_type='delivery')
        prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=100000,
            balance=100000,
            payment_date=timezone.localdate(),
            payer_name='선결제입금자',
            created_by=self.user,
        )
        update_url = reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id])
        self.client.force_login(self.user)

        apply_response = self.client.post(
            update_url,
            data=json.dumps({
                'usePrepayment': True,
                'prepayments': [{'id': prepayment.id, 'amount': '60000'}],
                'items': [
                    {
                        'itemName': 'Prepaid Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(apply_response.status_code, 200)
        self.assertIn('선결제를 차감', apply_response.json()['message'])
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 40000)
        self.assertTrue(schedule.use_prepayment)
        self.assertEqual(schedule.prepayment, prepayment)
        self.assertEqual(int(schedule.prepayment_amount), 60000)
        usage = PrepaymentUsage.objects.get(schedule=schedule)
        self.assertEqual(int(usage.amount), 60000)
        self.assertEqual(usage.schedule_item.item_name, 'Prepaid Kit')
        self.assertEqual(apply_response.json()['schedule']['prepaymentUsages'][0]['amount'], 60000)

        reapply_response = self.client.post(
            update_url,
            data=json.dumps({
                'usePrepayment': True,
                'prepayments': [{'id': prepayment.id, 'amount': '30000'}],
                'items': [
                    {
                        'itemName': 'Prepaid Kit Updated',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(reapply_response.status_code, 200)
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 70000)
        self.assertEqual(int(schedule.prepayment_amount), 30000)
        self.assertEqual(PrepaymentUsage.objects.filter(schedule=schedule).count(), 1)
        self.assertEqual(int(PrepaymentUsage.objects.get(schedule=schedule).amount), 30000)

        restore_response = self.client.post(
            update_url,
            data=json.dumps({
                'usePrepayment': False,
                'prepayments': [],
                'items': [
                    {
                        'itemName': 'Prepaid Kit Updated',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(restore_response.status_code, 200)
        self.assertIn('선결제 차감을 해제', restore_response.json()['message'])
        prepayment.refresh_from_db()
        schedule.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 100000)
        self.assertFalse(schedule.use_prepayment)
        self.assertIsNone(schedule.prepayment)
        self.assertEqual(int(schedule.prepayment_amount), 0)
        self.assertFalse(PrepaymentUsage.objects.filter(schedule=schedule).exists())

    def test_schedule_delivery_items_update_api_treats_zero_discount_unit_price_without_rate_as_blank(self):
        import json
        from reporting.models import DeliveryItem

        schedule = self._create_schedule(self.user, '납품할인단가0', activity_type='delivery')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'itemName': 'SO825.0002',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '379950',
                        'discountRate': '',
                        'discountUnitPrice': '0',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        item = DeliveryItem.objects.get(schedule=schedule)
        self.assertIsNone(item.discount_unit_price)
        self.assertEqual(float(item.discount_rate), 0.0)
        self.assertEqual(int(item.get_effective_unit_price()), 379950)
        self.assertEqual(int(item.total_price), 417945)
        self.assertIsNone(payload['deliveryItems'][0]['discountUnitPrice'])
        self.assertEqual(payload['deliveryItems'][0]['effectiveUnitPrice'], 379950)
        self.assertEqual(payload['deliveryItems'][0]['totalPrice'], 417945)

    def test_schedule_delivery_items_update_api_blocks_prepayment_above_delivery_total(self):
        import json
        from django.utils import timezone
        from reporting.models import Prepayment

        schedule = self._create_schedule(self.user, '납품선결제상한서버', activity_type='delivery')
        prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=1000000,
            balance=1000000,
            payment_date=timezone.localdate(),
            payer_name='상한입금자',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'usePrepayment': True,
                'prepayments': [{'id': prepayment.id, 'amount': '60000'}],
                'items': [
                    {
                        'itemName': 'Limit Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('납품 품목 합계', response.json()['error'])
        prepayment.refresh_from_db()
        self.assertEqual(int(prepayment.balance), 1000000)

    def test_schedule_delivery_items_update_api_blocks_over_balance_prepayment_without_saving_items(self):
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Prepayment, PrepaymentUsage

        schedule = self._create_schedule(self.user, '납품품목선결제잔액차단', activity_type='delivery')
        original_item = DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Original Kit',
            quantity=1,
            unit='EA',
            unit_price=1000,
        )
        prepayment = Prepayment.objects.create(
            customer=schedule.followup,
            company=schedule.followup.company,
            amount=1000,
            balance=1000,
            payment_date=timezone.localdate(),
            payer_name='잔액부족입금자',
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'usePrepayment': True,
                'prepayments': [{'id': prepayment.id, 'amount': '2000'}],
                'items': [
                    {
                        'itemName': 'Blocked Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '2000',
                    },
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
        items = list(DeliveryItem.objects.filter(schedule=schedule))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, original_item.id)
        self.assertEqual(items[0].item_name, 'Original Kit')

    def test_schedule_delivery_items_update_api_marks_imported_quote_completed(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '견적불러오기납품', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Quoted PCR Kit',
            quantity=2,
            unit='EA',
            unit_price=50000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'sourceQuoteScheduleIds': [quote_schedule.id],
                'items': [
                    {
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'itemName': 'Quoted PCR Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '50000',
                        'taxInvoiceIssued': False,
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['completedQuoteScheduleIds'], [quote_schedule.id])
        self.assertIn('원본 견적 일정', payload['message'])
        quote_schedule.refresh_from_db()
        self.assertEqual(quote_schedule.status, 'completed')
        self.assertEqual(DeliveryItem.objects.get(schedule=schedule).item_name, 'Quoted PCR Kit')

    def test_schedule_delivery_items_update_api_keeps_partial_imported_quote_scheduled(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, History, Schedule

        schedule = self._create_schedule(self.user, '부분견적불러오기납품', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='completed',
        )
        sold_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Thirty Thousand Kit',
            quantity=1,
            unit='EA',
            unit_price=30000,
            quote_group='보상판매',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Unsold Kit',
            quantity=1,
            unit='EA',
            unit_price=70000,
            quote_group='수리',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'sourceQuoteItemId': sold_item.id,
                        'itemName': 'Thirty Thousand Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '30000',
                        'quoteGroup': '보상판매',
                        'taxInvoiceIssued': False,
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['completedQuoteScheduleIds'], [])
        quote_schedule.refresh_from_db()
        self.assertEqual(quote_schedule.status, 'scheduled')
        delivery_item = DeliveryItem.objects.get(schedule=schedule)
        self.assertEqual(delivery_item.source_quote_schedule_id, quote_schedule.id)
        self.assertEqual(delivery_item.source_quote_item_id, sold_item.id)
        history = History.objects.get(schedule=schedule, action_type='delivery_schedule')
        self.assertIn('Thirty Thousand Kit', history.delivery_items)
        self.assertNotIn('Unsold Kit', history.delivery_items)
        self.assertEqual(int(history.delivery_amount), 33000)

    def test_schedule_delivery_items_update_api_rejects_over_imported_quote_quantity(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '초과견적불러오기납품', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Limited Quote Kit',
            quantity=2,
            unit='EA',
            unit_price=30000,
        )
        previous_delivery = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(11, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=previous_delivery,
            source_quote_schedule=quote_schedule,
            source_quote_item=quote_item,
            item_name='Limited Quote Kit',
            quantity=1,
            unit='EA',
            unit_price=30000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'sourceQuoteItemId': quote_item.id,
                        'itemName': 'Limited Quote Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '30000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('남은 견적 수량은 1EA', response.json()['error'])
        self.assertFalse(DeliveryItem.objects.filter(schedule=schedule).exists())

    def test_schedule_delivery_items_update_api_rejects_duplicate_source_quote_item_rows(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '중복견적품목납품', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Duplicate Guard Kit',
            quantity=2,
            unit='EA',
            unit_price=50000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'sourceQuoteItemId': quote_item.id,
                        'itemName': 'Duplicate Guard Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                    {
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'sourceQuoteItemId': quote_item.id,
                        'itemName': 'Duplicate Guard Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('견적 품목이 중복되었습니다', response.json()['error'])
        self.assertFalse(DeliveryItem.objects.filter(schedule=schedule).exists())

    def test_schedule_delivery_items_update_api_reopens_quote_when_import_link_removed(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '견적연결해제납품', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='completed',
        )
        quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Linked Quote Kit',
            quantity=1,
            unit='EA',
            unit_price=40000,
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            source_quote_schedule=quote_schedule,
            source_quote_item=quote_item,
            item_name='Linked Quote Kit',
            quantity=1,
            unit='EA',
            unit_price=40000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'itemName': 'Manual Replacement Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '10000',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        quote_schedule.refresh_from_db()
        self.assertEqual(quote_schedule.status, 'scheduled')
        delivery_item = DeliveryItem.objects.get(schedule=schedule)
        self.assertEqual(delivery_item.item_name, 'Manual Replacement Kit')
        self.assertIsNone(delivery_item.source_quote_schedule_id)
        self.assertIsNone(delivery_item.source_quote_item_id)

    def test_schedule_delivery_items_update_api_collects_existing_source_quotes_without_distinct_lock(self):
        import datetime
        import json
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '견적원본중복잠금회피', activity_type='delivery')
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='completed',
        )
        quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Existing Linked Kit',
            quantity=2,
            unit='EA',
            unit_price=40000,
        )
        for index in range(2):
            DeliveryItem.objects.create(
                schedule=schedule,
                source_quote_schedule=quote_schedule,
                source_quote_item=quote_item if index == 0 else None,
                item_name=f'Existing Linked Kit {index}',
                quantity=1,
                unit='EA',
                unit_price=40000,
            )
        self.client.force_login(self.user)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.post(
                reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
                data=json.dumps({
                    'items': [
                        {
                            'itemName': 'Manual Replacement Kit',
                            'quantity': 1,
                            'unit': 'EA',
                            'unitPrice': '10000',
                        },
                    ],
                }),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        source_quote_queries = [
            query['sql'].upper()
            for query in captured.captured_queries
            if 'SOURCE_QUOTE_SCHEDULE_ID' in query['sql'].upper()
        ]
        self.assertTrue(source_quote_queries)
        self.assertFalse(any('DISTINCT' in query for query in source_quote_queries))
        quote_schedule.refresh_from_db()
        self.assertEqual(quote_schedule.status, 'scheduled')

    def test_completed_quote_items_do_not_increment_product_sold_count(self):
        from reporting.models import DeliveryItem, Product

        quote_schedule = self._create_schedule(self.user, '완료견적판매수량제외', activity_type='quote', status='completed')
        product = Product.objects.create(
            product_code='QUOTE-NOT-SOLD',
            unit='EA',
            standard_price=30000,
            created_by=self.user,
        )

        DeliveryItem.objects.create(
            schedule=quote_schedule,
            product=product,
            item_name='QUOTE-NOT-SOLD',
            quantity=2,
            unit='EA',
            unit_price=30000,
        )

        product.refresh_from_db()
        self.assertEqual(product.total_sold, 0)

    def test_notes_detail_uses_actual_delivery_schedule_items_over_stale_history_text(self):
        from reporting.models import DeliveryItem, History

        schedule = self._create_schedule(self.user, '실제납품보고', activity_type='delivery', status='completed')
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='Actually Sold Kit',
            quantity=1,
            unit='EA',
            unit_price=30000,
        )
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=schedule.followup,
            schedule=schedule,
            action_type='delivery_schedule',
            delivery_items='Actually Sold Kit: 1EA (33,000원)\nUnsold Kit: 1EA (77,000원)',
            delivery_amount=110000,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:notes_detail_api', args=[history.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['note']['deliveryAmount'], 33000)
        self.assertIn('Actually Sold Kit', payload['note']['deliveryItems'])
        self.assertNotIn('Unsold Kit', payload['note']['deliveryItems'])

    def test_notes_detail_uses_actual_delivery_items_when_delivery_note_is_linked_to_quote_schedule(self):
        import datetime
        from django.utils import timezone
        from reporting.models import DeliveryItem, History, Schedule

        quote_schedule = self._create_schedule(self.user, '견적연결납품노트', activity_type='quote', status='completed')
        sold_quote_item = DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='56722',
            quantity=1,
            unit='EA',
            unit_price=30000,
            discount_unit_price=30000,
            quote_group='수리',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='SO447.100E',
            quantity=1,
            unit='EA',
            unit_price=480000,
            discount_unit_price=336000,
            quote_group='보상판매',
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=quote_schedule.followup,
            visit_date=timezone.localdate() + datetime.timedelta(days=1),
            visit_time=datetime.time(9, 0),
            activity_type='delivery',
            status='completed',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name=sold_quote_item.item_name,
            quantity=1,
            unit=sold_quote_item.unit,
            unit_price=sold_quote_item.unit_price,
            discount_unit_price=sold_quote_item.discount_unit_price,
            quote_group=sold_quote_item.quote_group,
        )
        stale_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=quote_schedule.followup,
            schedule=quote_schedule,
            action_type='delivery_schedule',
            delivery_items='56722: 1EA (33,000원)\nSO447.100E: 1EA (369,600원)',
            delivery_amount=402600,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:notes_detail_api', args=[stale_history.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['note']['deliveryAmount'], 33000)
        self.assertIn('56722', payload['note']['deliveryItems'])
        self.assertNotIn('SO447.100E', payload['note']['deliveryItems'])

    def test_notes_detail_does_not_count_quote_items_as_delivery_without_actual_delivery(self):
        from reporting.models import DeliveryItem, History

        quote_schedule = self._create_schedule(self.user, '견적만있는납품노트', activity_type='quote', status='completed')
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='Unsold Quote Kit',
            quantity=1,
            unit='EA',
            unit_price=70000,
        )
        stale_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=quote_schedule.followup,
            schedule=quote_schedule,
            action_type='delivery_schedule',
            delivery_items='Unsold Quote Kit: 1EA (77,000원)',
            delivery_amount=77000,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:notes_detail_api', args=[stale_history.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['note']['deliveryAmount'], 0)
        self.assertEqual(payload['note']['deliveryItems'], '')

    def test_schedule_delivery_items_update_api_does_not_create_delivery_history_for_quote_schedule(self):
        import json
        from reporting.models import DeliveryItem, History

        quote_schedule = self._create_schedule(self.user, '견적품목저장노트방지', activity_type='quote')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[quote_schedule.id]),
            data=json.dumps({
                'items': [
                    {
                        'itemName': 'Quote Only Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '50000',
                        'quoteGroup': '수리',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(DeliveryItem.objects.filter(schedule=quote_schedule).count(), 1)
        self.assertFalse(
            History.objects.filter(schedule=quote_schedule, action_type='delivery_schedule').exists()
        )

    def test_schedule_update_delivery_items_legacy_does_not_create_delivery_history_for_quote_schedule(self):
        from reporting.models import DeliveryItem, History

        quote_schedule = self._create_schedule(self.user, '레거시견적품목저장노트방지', activity_type='quote')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedule_update_delivery_items', args=[quote_schedule.id]),
            data={
                'delivery_items[0][name]': 'Legacy Quote Only Kit',
                'delivery_items[0][quantity]': '1',
                'delivery_items[0][unit_price]': '50000',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(DeliveryItem.objects.filter(schedule=quote_schedule).count(), 1)
        self.assertFalse(
            History.objects.filter(schedule=quote_schedule, action_type='delivery_schedule').exists()
        )

    def test_schedule_delivery_items_update_api_rejects_coworker_source_quote_completion(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import DeliveryItem, Schedule

        schedule = self._create_schedule(self.user, '동료견적차단납품', activity_type='delivery')
        coworker_quote = Schedule.objects.create(
            user=self.coworker,
            company=self.company,
            followup=schedule.followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        DeliveryItem.objects.create(
            schedule=coworker_quote,
            item_name='Coworker Quote Kit',
            quantity=1,
            unit='EA',
            unit_price=10000,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]),
            data=json.dumps({
                'sourceQuoteScheduleIds': [coworker_quote.id],
                'items': [
                    {
                        'sourceQuoteScheduleId': coworker_quote.id,
                        'itemName': 'Coworker Quote Kit',
                        'quantity': 1,
                        'unit': 'EA',
                        'unitPrice': '10000',
                        'taxInvoiceIssued': False,
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn('본인이 작성한 견적 일정', response.json()['error'])
        coworker_quote.refresh_from_db()
        self.assertEqual(coworker_quote.status, 'scheduled')
        self.assertFalse(DeliveryItem.objects.filter(schedule=schedule).exists())

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
        ScheduleQuoteGroupNote.objects.create(schedule=schedule, quote_group='보상판매', notes='보상판매 조건')
        ScheduleQuoteGroupNote.objects.create(schedule=schedule, quote_group='수리', notes='수리 조건')
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
        self.assertEqual(payload['variables']['견적기타사항'], '수리 조건')
        self.assertEqual(payload['variables']['기타사항'], '수리 조건')
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

    def test_document_item_note_layout_helper_wraps_and_expands_note_rows(self):
        import os
        import tempfile
        import zipfile
        from xml.etree import ElementTree as ET
        from openpyxl import Workbook
        from reporting.views import _expand_xlsx_item_note_rows

        workbook = Workbook()
        sheet = workbook.active
        sheet.column_dimensions['B'].width = 12
        sheet['B5'] = '{{품목1_적요}}'
        long_note = (
            '내부 세척 및 오염 제거 후 정상 볼륨 확인. '
            '오링 마모가 심해 교체가 필요하며 수리 진행 여부 회신 요청.'
        )
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name
        self.addCleanup(lambda: os.path.exists(temp_path) and os.unlink(temp_path))
        workbook.save(temp_path)

        changed = _expand_xlsx_item_note_rows(temp_path, {'품목1_적요': long_note})

        self.assertTrue(changed)
        with zipfile.ZipFile(temp_path, 'r') as archive:
            styles_xml = archive.read('xl/styles.xml').decode('utf-8')
            sheet_root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))

        namespace = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        row = sheet_root.find(".//s:row[@r='5']", namespace)
        cell = sheet_root.find(".//s:c[@r='B5']", namespace)
        self.assertIsNotNone(row)
        self.assertIsNotNone(cell)
        self.assertEqual(row.get('customHeight'), '1')
        self.assertGreater(float(row.get('ht')), 15.0)
        self.assertNotEqual(cell.get('s'), '0')
        self.assertIn('wrapText="1"', styles_xml)

    def test_document_template_text_layout_helper_wraps_long_replaced_text(self):
        import os
        import tempfile
        import zipfile
        from xml.etree import ElementTree as ET
        from openpyxl import Workbook
        from reporting.views import _expand_xlsx_template_text_rows

        workbook = Workbook()
        sheet = workbook.active
        sheet.column_dimensions['B'].width = 10
        sheet['B4'] = '{{업체명}}'
        long_company_name = '아주 긴 학교명 및 산학협력단 공동연구센터 세포분석실'
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name
        self.addCleanup(lambda: os.path.exists(temp_path) and os.unlink(temp_path))
        workbook.save(temp_path)

        changed = _expand_xlsx_template_text_rows(temp_path, {'업체명': long_company_name})

        self.assertTrue(changed)
        with zipfile.ZipFile(temp_path, 'r') as archive:
            styles_xml = archive.read('xl/styles.xml').decode('utf-8')
            sheet_root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))

        namespace = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        row = sheet_root.find(".//s:row[@r='4']", namespace)
        cell = sheet_root.find(".//s:c[@r='B4']", namespace)
        self.assertIsNotNone(row)
        self.assertIsNotNone(cell)
        self.assertEqual(row.get('customHeight'), '1')
        self.assertGreater(float(row.get('ht')), 15.0)
        self.assertNotEqual(cell.get('s'), '0')
        self.assertIn('wrapText="1"', styles_xml)

    def test_document_bold_strip_helper_removes_bold_styles(self):
        import os
        import tempfile
        import zipfile
        from openpyxl import Workbook
        from openpyxl.styles import Font
        from reporting.views import _strip_xlsx_bold_formatting

        workbook = Workbook()
        sheet = workbook.active
        sheet['A1'] = '견적서'
        sheet['A1'].font = Font(bold=True)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_path = temp_file.name
        self.addCleanup(lambda: os.path.exists(temp_path) and os.unlink(temp_path))
        workbook.save(temp_path)

        changed = _strip_xlsx_bold_formatting(temp_path)

        self.assertTrue(changed)
        with zipfile.ZipFile(temp_path, 'r') as archive:
            styles_xml = archive.read('xl/styles.xml').decode('utf-8')
        self.assertNotIn('<b ', styles_xml)
        self.assertNotIn('<b/>', styles_xml)
        self.assertNotIn('<b>', styles_xml)


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

    def _create_prepayment_delivery_split_fixture(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import DeliveryItem, Prepayment, PrepaymentUsage, Schedule

        followup, department = self._create_customer(self.user, '선결제분리')
        today = timezone.localdate()
        prepayment = Prepayment.objects.create(
            customer=followup,
            company=followup.company,
            amount=Decimal('100000'),
            balance=Decimal('60000'),
            payment_date=today - timedelta(days=20),
            payer_name='구조화입금자',
            created_by=self.user,
        )
        prepaid_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today - timedelta(days=7),
            visit_time=time(10, 0),
            status='completed',
            activity_type='delivery',
            expected_revenue=Decimal('40000'),
            use_prepayment=True,
            prepayment=prepayment,
            prepayment_amount=Decimal('40000'),
            notes='실제 선결제 차감 납품',
        )
        DeliveryItem.objects.create(
            schedule=prepaid_schedule,
            item_name='선결제Kit',
            quantity=1,
            unit='EA',
            unit_price=Decimal('40000'),
            total_price=Decimal('40000'),
        )
        PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=prepaid_schedule,
            product_name='선결제Kit',
            quantity=1,
            amount=Decimal('40000'),
            remaining_balance=Decimal('60000'),
        )
        normal_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today - timedelta(days=3),
            visit_time=time(14, 0),
            status='completed',
            activity_type='delivery',
            expected_revenue=Decimal('30000'),
            notes='20,000,000원 견적서 및 선결제 진행 요청 받음',
        )
        DeliveryItem.objects.create(
            schedule=normal_schedule,
            item_name='일반Kit',
            quantity=1,
            unit='EA',
            unit_price=Decimal('30000'),
            total_price=Decimal('30000'),
        )
        return followup, department, prepaid_schedule, normal_schedule

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
        self.assertEqual(payload['actionQueue'], [])
        self.assertEqual(payload['feedbackHistory']['stats']['total'], 0)
        self.assertEqual(payload['dailyBrief']['counts']['totalActions'], 0)
        self.assertIsNone(payload['featuredDepartment'])
        self.assertEqual(payload['metrics']['departmentsWithCustomers'], 0)

    def test_ai_workspace_summary_uses_mini_only_question_model_choices(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['defaultQuestionModel'], 'gpt-5.4-mini')
        self.assertEqual(payload['questionModelChoices'], [
            {'id': 'gpt-5.4-mini', 'label': 'GPT-5.4 mini'},
        ])

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
        self.assertTrue(payload['actionQueue'])
        self.assertEqual(payload['dailyBrief']['counts']['painpointValidations'], 1)

    def test_ai_workspace_summary_api_includes_feedback_history_for_owner_scope(self):
        from reporting.models import AIWorkspaceActionFeedback, History

        followup, department = self._create_customer(self.user, '피드백이력')
        self._create_department_analysis(self.user, department)
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='memo',
            content='[AI 추천 실행 답변] 추가 자료 요청',
            next_action='요청 자료를 메일로 보내기',
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            history=history,
            action_id='quote:feedback-owner',
            action_kind='quote_followup',
            status='next_action',
            feedback='고객이 추가 자료를 메일로 보내달래요',
            ai_result={
                'summary': '추가 자료 요청으로 판단했습니다.',
                'nextAction': '요청 자료를 메일로 보내기',
                'nextActionDate': timezone.localdate().isoformat(),
                'reason': '자료 요청 신호',
                'source': 'fallback',
            },
            action_snapshot={
                'title': '피드백이력 견적 후속',
                'customer': followup.customer_name,
                'company': followup.company.name,
                'department': followup.department.name,
            },
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.coworker,
            action_id='quote:feedback-coworker',
            action_kind='quote_followup',
            status='resolved',
            feedback='동료 고객은 구매하지 않음',
            ai_result={'summary': '동료 기록', 'source': 'fallback'},
            action_snapshot={'title': '동료 기록'},
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        feedback_history = payload['feedbackHistory']
        self.assertEqual(feedback_history['scope']['label'], self.user.username)
        self.assertFalse(feedback_history['scope']['canViewAll'])
        self.assertEqual(feedback_history['stats']['total'], 1)
        self.assertEqual(feedback_history['stats']['nextActions'], 1)
        self.assertEqual(feedback_history['stats']['linkedNotes'], 1)
        self.assertEqual(feedback_history['byKind'][0]['kindLabel'], '견적 후속')
        self.assertEqual(feedback_history['recent'][0]['actionId'], 'quote:feedback-owner')
        self.assertEqual(feedback_history['recent'][0]['statusLabel'], '다음 액션')
        self.assertIn('추가 자료', feedback_history['recent'][0]['feedback'])
        self.assertIn('/reporting/histories/', feedback_history['recent'][0]['historyHref'])
        recent_ids = {item['actionId'] for item in feedback_history['recent']}
        self.assertNotIn('quote:feedback-coworker', recent_ids)

    def test_ai_workspace_summary_promotes_recent_field_feedback_to_recommended_goals(self):
        from datetime import timedelta
        from reporting.models import AIWorkspaceActionFeedback

        followup, department = self._create_customer(self.user, '현장목표')
        self._create_department_analysis(self.user, department)
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            action_id='quote:field-goal',
            action_kind='quote_followup',
            status='next_action',
            feedback='고객이 추가 피드백을 요청했고 월요일 오후에 회신 필요',
            ai_result={
                'intent': 'follow_up_needed',
                'summary': '추가 피드백 요청이 확인되었습니다.',
                'nextAction': '추가 피드백 회수 및 장점 정리',
                'reason': '현장 답변에서 후속 필요가 명확합니다.',
                'prioritySignal': 'high',
                'source': 'fallback',
            },
            action_snapshot={'title': '현장목표 견적 후속'},
        )
        resolved_followup, _resolved_department = self._create_customer(self.user, '종료목표')
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=resolved_followup,
            action_id='quote:resolved-goal',
            action_kind='quote_followup',
            status='resolved',
            feedback='구매 의사 없음으로 정리',
            ai_result={'intent': 'resolved_no_purchase', 'summary': '종료됨'},
            action_snapshot={'title': '종료된 후속'},
        )
        stale_followup, _stale_department = self._create_customer(self.user, '오래된목표')
        stale_feedback = AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=stale_followup,
            action_id='quote:stale-goal',
            action_kind='quote_followup',
            status='next_action',
            feedback='오래된 후속',
            ai_result={'intent': 'follow_up_needed', 'nextAction': '오래된 후속'},
            action_snapshot={'title': '오래된 후속'},
        )
        AIWorkspaceActionFeedback.objects.filter(id=stale_feedback.id).update(
            updated_at=timezone.now() - timedelta(days=45)
        )
        coworker_followup, _coworker_department = self._create_customer(self.coworker, '동료현장목표')
        AIWorkspaceActionFeedback.objects.create(
            user=self.coworker,
            followup=coworker_followup,
            action_id='quote:coworker-goal',
            action_kind='quote_followup',
            status='next_action',
            feedback='동료 후속',
            ai_result={'intent': 'follow_up_needed', 'nextAction': '동료 후속'},
            action_snapshot={'title': '동료 후속'},
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        first_goal = payload['recommendedGoals'][0]
        self.assertEqual(first_goal['source'], 'field_feedback')
        self.assertEqual(first_goal['sourceLabel'], '최근 현장 답변 기반')
        self.assertEqual(first_goal['customer'], '현장목표 담당자')
        self.assertIn('추가 피드백 회수', first_goal['title'])
        self.assertIn('현장 답변', first_goal['reason'])
        goals_text = json.dumps(payload['recommendedGoals'], ensure_ascii=False)
        self.assertNotIn('구매 의사 없음', goals_text)
        self.assertNotIn('오래된 후속', goals_text)
        self.assertNotIn('동료 후속', goals_text)

    def test_ai_workspace_summary_api_feedback_history_uses_manager_company_scope(self):
        from reporting.models import AIWorkspaceActionFeedback

        manager = make_user('ai_workspace_manager', role='manager', can_use_ai=True, company=self.company)
        outsider = make_user('ai_workspace_outsider', role='salesman', can_use_ai=True, company=self.other_company)
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            action_id='quote:team-owner',
            action_kind='quote_followup',
            status='resolved',
            feedback='고객이 안산대요',
            ai_result={'summary': '종료', 'source': 'fallback'},
            action_snapshot={'title': '팀 사용자 기록'},
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.coworker,
            action_id='followup:team-coworker',
            action_kind='customer_followup',
            status='answered',
            feedback='동료가 답변 기록',
            ai_result={'summary': '기록', 'source': 'fallback'},
            action_snapshot={'title': '팀 동료 기록'},
        )
        AIWorkspaceActionFeedback.objects.create(
            user=outsider,
            action_id='quote:outside',
            action_kind='quote_followup',
            status='resolved',
            feedback='타사 기록',
            ai_result={'summary': '타사', 'source': 'fallback'},
            action_snapshot={'title': '타사 기록'},
        )
        self.client.force_login(manager)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        feedback_history = response.json()['feedbackHistory']
        self.assertTrue(feedback_history['scope']['canViewAll'])
        self.assertIn('AI워크스페이스회사', feedback_history['scope']['label'])
        self.assertEqual(feedback_history['stats']['total'], 2)
        self.assertEqual(feedback_history['stats']['resolved'], 1)
        self.assertEqual(feedback_history['stats']['answered'], 1)
        recent_ids = {item['actionId'] for item in feedback_history['recent']}
        self.assertEqual(recent_ids, {'quote:team-owner', 'followup:team-coworker'})

    def test_ai_workspace_detail_feedback_history_scopes_to_department_and_keeps_full_text(self):
        from reporting.models import AIWorkspaceActionFeedback

        selected_followup, selected_department = self._create_customer(self.user, '피드백상세')
        other_followup, _other_department = self._create_customer(self.user, '다른피드백')
        long_feedback = (
            '고객 답변은 장문으로 기록되어야 합니다. '
            '팁 불만의 증상, 사용 제품 규격, 수량, 로트, 사진 여부, 처리 예정 시간까지 모두 적었습니다. '
            * 6
        ) + '피드백 끝문장'
        long_summary = (
            'AI 판단도 장문으로 표시되어야 하며, 상세 페이지에서는 해당 부서 고객의 피드백만 보여야 합니다. '
            * 6
        ) + '판단 끝문장'
        long_next_action = (
            '다음 액션은 증상 확인, 제품 규격 확인, 교체 가능 여부 검토, 고객에게 처리 예정 시간 회신까지 포함합니다. '
            * 6
        ) + '다음 액션 끝문장'
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=selected_followup,
            action_id='followup:feedback-detail-selected',
            action_kind='customer_followup',
            status='next_action',
            feedback=long_feedback,
            ai_result={
                'summary': long_summary,
                'nextAction': long_next_action,
                'reason': '상세 화면 표시 검증',
                'source': 'fallback',
            },
            action_snapshot={
                'title': '피드백상세 후속',
                'customer': selected_followup.customer_name,
                'company': selected_followup.company.name,
                'department': selected_followup.department.name,
            },
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=other_followup,
            action_id='followup:feedback-detail-other',
            action_kind='customer_followup',
            status='answered',
            feedback='다른 부서 피드백',
            ai_result={'summary': '다른 부서 판단', 'source': 'fallback'},
            action_snapshot={'title': '다른피드백 후속'},
        )
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})

        self.assertEqual(detail_response.status_code, 200)
        detail_feedback_history = detail_response.json()['feedbackHistory']
        self.assertEqual(detail_feedback_history['scope']['departmentId'], selected_department.id)
        self.assertIn(selected_department.name, detail_feedback_history['scope']['label'])
        self.assertEqual(detail_feedback_history['stats']['total'], 1)
        self.assertEqual(detail_feedback_history['recent'][0]['actionId'], 'followup:feedback-detail-selected')
        self.assertEqual(detail_feedback_history['recent'][0]['feedback'], long_feedback)
        self.assertEqual(detail_feedback_history['recent'][0]['summary'], long_summary)
        self.assertEqual(detail_feedback_history['recent'][0]['nextAction'], long_next_action)
        self.assertIn('피드백 끝문장', detail_feedback_history['recent'][0]['feedback'])
        self.assertIn('판단 끝문장', detail_feedback_history['recent'][0]['summary'])
        self.assertIn('다음 액션 끝문장', detail_feedback_history['recent'][0]['nextAction'])
        detail_action_ids = {item['actionId'] for item in detail_feedback_history['recent']}
        self.assertNotIn('followup:feedback-detail-other', detail_action_ids)

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['actionId'] for item in general_response.json()['feedbackHistory']['recent']}
        self.assertIn('followup:feedback-detail-selected', general_action_ids)
        self.assertIn('followup:feedback-detail-other', general_action_ids)

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

    def test_ai_workspace_detail_scopes_prompt_targets_to_requested_department(self):
        from ai_chat.models import AIFollowUpAnalysis

        selected_followup, selected_department = self._create_customer(self.user, '상세선택')
        other_followup, other_department = self._create_customer(self.user, '다른추천')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        AIFollowUpAnalysis.objects.create(
            followup=selected_followup,
            user=self.user,
            analysis_data={'customer_summary': '상세선택 고객 전용 후속 질문'},
            meeting_count=1,
        )
        AIFollowUpAnalysis.objects.create(
            followup=other_followup,
            user=self.user,
            analysis_data={'customer_summary': '다른추천 고객 질문은 상세 페이지 제외'},
            meeting_count=1,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': selected_department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['selectedDepartmentId'], selected_department.id)
        prompt_text = '\n'.join(item['prompt'] for item in payload['promptTargets'])
        prompt_titles = '\n'.join(item['title'] for item in payload['promptTargets'])
        self.assertTrue(payload['promptTargets'])
        self.assertIn('상세선택', prompt_text)
        self.assertIn('상세선택', prompt_titles + prompt_text)
        self.assertNotIn('다른추천', prompt_text)
        self.assertNotIn(other_department.name, prompt_text)
        self.assertEqual({target['department'] for target in payload['followupTargets']}, {selected_department.name})

    def test_ai_workspace_detail_feedback_goals_and_prompts_scope_to_requested_department(self):
        from reporting.models import AIWorkspaceActionFeedback

        selected_followup, selected_department = self._create_customer(self.user, '현장상세')
        other_followup, other_department = self._create_customer(self.user, '다른현장')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=selected_followup,
            action_id='followup:selected-feedback',
            action_kind='customer_followup',
            status='next_action',
            feedback='선택 부서 담당자가 샘플 사용 후 장점 정리를 요청',
            ai_result={
                'intent': 'follow_up_needed',
                'summary': '선택 부서의 샘플 피드백 회수가 필요합니다.',
                'nextAction': '선택 부서 샘플 피드백 회수',
                'reason': '선택 부서 현장 답변에서 다음 액션이 확인되었습니다.',
            },
            action_snapshot={'title': '선택 부서 현장 답변'},
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=other_followup,
            action_id='followup:other-feedback',
            action_kind='customer_followup',
            status='next_action',
            feedback='다른 부서 담당자가 견적 재전송을 요청',
            ai_result={
                'intent': 'follow_up_needed',
                'summary': '다른 부서 후속 필요',
                'nextAction': '다른 부서 견적 재전송',
            },
            action_snapshot={'title': '다른 부서 현장 답변'},
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': selected_department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        goals_text = json.dumps(payload['recommendedGoals'], ensure_ascii=False)
        prompt_text = '\n'.join(item['prompt'] for item in payload['promptTargets'])
        self.assertIn('선택 부서 샘플 피드백 회수', goals_text)
        self.assertIn('최근 현장 답변', prompt_text)
        self.assertIn('선택 부서 담당자가 샘플 사용 후 장점 정리를 요청', prompt_text)
        self.assertNotIn('다른 부서 견적 재전송', goals_text)
        self.assertNotIn('다른 부서 담당자가 견적 재전송을 요청', prompt_text)

    def test_ai_workspace_prompt_targets_keep_full_recent_note_text(self):
        from reporting.models import History

        followup, department = self._create_customer(self.user, '문새롬프롬프트')
        self._create_department_analysis(self.user, department)
        long_note = (
            'Thermo 멀티채널 피펫과 Paradigm 팁 호환성 문제를 길게 기록합니다. '
            '팁이 빠지는 상황, 기포가 생기는 상황, 고객이 앞으로 구매가 어렵다고 말한 맥락, '
            '실사용 모델명을 확인하지 못한 점, 다음 방문에서 확인해야 할 항목을 모두 남깁니다. '
            * 5
        ) + '프롬프트 최근 노트 끝문장 모델명 확인 필요'
        long_next_action = (
            '다음 연락에서는 피펫 모델명, 사용 팁 규격, 로트, 사진 여부, 대체품 테스트 가능 여부를 확인합니다. '
            * 4
        ) + '프롬프트 다음 액션 끝문장'
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content=long_note,
            next_action=long_next_action,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        followup_prompt = next(
            item['prompt']
            for item in payload['promptTargets']
            if item['id'] == f'followup-{followup.id}'
        )
        self.assertIn('프롬프트 최근 노트 끝문장 모델명 확인 필요', followup_prompt)
        self.assertIn('프롬프트 다음 액션 끝문장', followup_prompt)
        self.assertNotIn('프롬프트 최근 노트 끝문장 모델명...', followup_prompt)
        self.assertNotIn('프롬프트 다음 액션...', followup_prompt)

    def test_ai_workspace_detail_scopes_action_queue_to_requested_department(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import History, Quote, Schedule

        selected_followup, selected_department = self._create_customer(self.user, '상세액션')
        other_followup, other_department = self._create_customer(self.user, '전체액션')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        today = timezone.localdate()

        selected_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=selected_followup,
            visit_date=today,
            visit_time=time(9, 30),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1200000'),
        )
        selected_quote = Quote.objects.create(
            quote_number='AI-DETAIL-Q-SELECTED',
            schedule=selected_schedule,
            followup=selected_followup,
            user=self.user,
            valid_until=today + timedelta(days=2),
            stage='sent',
            subtotal=Decimal('1200000'),
            probability=70,
        )
        selected_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=selected_followup,
            action_type='customer_meeting',
            content='상세액션 후속 확인',
            next_action='상세액션 고객만 확인',
            next_action_date=today,
        )
        other_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=other_followup,
            visit_date=today,
            visit_time=time(10, 30),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('2200000'),
        )
        other_quote = Quote.objects.create(
            quote_number='AI-DETAIL-Q-OTHER',
            schedule=other_schedule,
            followup=other_followup,
            user=self.user,
            valid_until=today + timedelta(days=1),
            stage='sent',
            subtotal=Decimal('2200000'),
            probability=75,
        )
        other_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=other_followup,
            action_type='customer_meeting',
            content='전체액션 후속 확인',
            next_action='전체액션 고객 확인',
            next_action_date=today,
        )
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        detail_action_ids = {item['id'] for item in detail_payload['actionQueue']}
        self.assertIn(f'quote:{selected_quote.id}', detail_action_ids)
        self.assertIn(f'followup:{selected_history.id}', detail_action_ids)
        self.assertNotIn(f'quote:{other_quote.id}', detail_action_ids)
        self.assertNotIn(f'followup:{other_history.id}', detail_action_ids)
        self.assertTrue(all(
            item.get('department') == selected_department.name or item['kind'] == 'painpoint_validation'
            for item in detail_payload['actionQueue']
        ))
        self.assertNotIn('weekly_report', {item['kind'] for item in detail_payload['actionQueue']})

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['id'] for item in general_response.json()['actionQueue']}
        self.assertIn(f'quote:{selected_quote.id}', general_action_ids)
        self.assertIn(f'quote:{other_quote.id}', general_action_ids)

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

    def test_ai_workspace_summary_department_search_text_includes_own_manager_names_only(self):
        own_followup, own_department = self._create_customer(self.user, 'PI검색')
        own_followup.manager = '김피아이'
        own_followup.save(update_fields=['manager'])
        coworker_followup, _coworker_department = self._create_customer(self.coworker, '동료PI')
        coworker_followup.manager = '외부피아이'
        coworker_followup.save(update_fields=['manager'])
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        department_payload = next(department for department in payload['departments'] if department['id'] == own_department.id)
        self.assertIn('PI검색 담당자', department_payload['searchText'])
        self.assertIn('김피아이', department_payload['searchText'])
        all_search_text = '\n'.join(department.get('searchText', '') for department in payload['departments'])
        self.assertNotIn('외부피아이', all_search_text)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_department_question_answers_last_order_from_delivery_context(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import DeliveryItem, Schedule

        followup, department = self._create_customer(self.user, '마지막주문')
        older_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate() - timedelta(days=30),
            visit_time=time(11, 0),
            status='completed',
            activity_type='delivery',
            expected_revenue=Decimal('120000'),
            notes='이전 납품',
        )
        DeliveryItem.objects.create(
            schedule=older_schedule,
            item_name='Old Buffer',
            quantity=1,
            unit_price=Decimal('120000'),
        )
        latest_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate() - timedelta(days=3),
            visit_time=time(14, 0),
            status='completed',
            activity_type='delivery',
            expected_revenue=Decimal('240000'),
            notes='최근 납품',
        )
        DeliveryItem.objects.create(
            schedule=latest_schedule,
            item_name='qPCR Mix',
            quantity=2,
            unit_price=Decimal('100000'),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '해당 연구실에서 우리에게 마지막으로 주문한 날짜가 언제지?',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        latest_date = latest_schedule.visit_date.isoformat()
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['department']['id'], department.id)
        self.assertEqual(payload['context']['lastDelivery']['date'], latest_date)
        self.assertIn(latest_date, payload['answer']['summary'])
        self.assertIn('qPCR Mix', payload['answer']['summary'])
        evidence_text = ' '.join(item['value'] for item in payload['answer']['evidence'])
        self.assertIn(latest_date, evidence_text)
        self.assertIn('qPCR Mix', evidence_text)

    def test_ai_workspace_question_context_splits_delivery_payment_source_from_structured_prepayment(self):
        from reporting.views import _ai_workspace_department_question_context

        _followup, department, prepaid_schedule, normal_schedule = self._create_prepayment_delivery_split_fixture()

        context = _ai_workspace_department_question_context(department, self.user)

        split = context['deliveryPaymentSplit']
        self.assertEqual(split['source'], 'common_account_ledger')
        self.assertEqual(split['answerMode'], 'deterministic_ledger')
        self.assertFalse(split['usesNotesForClassification'])
        self.assertIn('Schedule.delivery_payment_status', split['evidenceFields'])
        self.assertEqual(split['prepaymentCount'], 1)
        self.assertEqual(split['withoutPrepaymentCount'], 1)
        prepayment_text = json.dumps(split['prepaymentDeliveries'], ensure_ascii=False)
        without_prepayment_text = json.dumps(split['withoutPrepaymentDeliveries'], ensure_ascii=False)
        self.assertIn('선결제Kit', prepayment_text)
        self.assertIn(str(prepaid_schedule.id), prepayment_text)
        self.assertIn('PrepaymentUsage', prepayment_text)
        self.assertIn('선결제 차감 납품', prepayment_text)
        self.assertNotIn('일반Kit', prepayment_text)
        self.assertIn('일반Kit', without_prepayment_text)
        self.assertIn(str(normal_schedule.id), without_prepayment_text)
        self.assertIn('선결제 사용 기록 없음', without_prepayment_text)
        self.assertIn('일반 납품', without_prepayment_text)
        self.assertIn('메모', split['classificationRule'])

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_department_question_ledger_splits_prepayment_deliveries_without_notes_inference(self, mock_client):
        _followup, department, _prepaid_schedule, _normal_schedule = self._create_prepayment_delivery_split_fixture()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '선결제로 납품된거랑 그냥 결제로 납품된거 분리해줘',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'ledger')
        mock_client.assert_not_called()
        split = payload['context']['deliveryPaymentSplit']
        self.assertEqual(split['source'], 'common_account_ledger')
        self.assertFalse(split['usesNotesForClassification'])
        self.assertEqual(split['prepaymentCount'], 1)
        self.assertEqual(split['withoutPrepaymentCount'], 1)
        answer_text = payload['answer']['summary']
        prepayment_section = answer_text.split('2) 일반 납품 / 선결제 사용 기록 없는 납품')[0]
        self.assertIn('선결제Kit', prepayment_section)
        self.assertNotIn('일반Kit', prepayment_section)
        self.assertIn('일반Kit', answer_text)
        self.assertIn('일반 납품', answer_text)
        self.assertIn('메모에 "선결제"', answer_text)
        self.assertIn('선결제 사용 기록 없음', answer_text)
        evidence_text = ' '.join(item['value'] for item in payload['answer']['evidence'])
        self.assertIn('Schedule.delivery_payment_status', evidence_text)
        self.assertIn('PrepaymentUsage', evidence_text)

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_department_question_delivery_payment_split_bypasses_openai_when_client_available(self, mock_client):
        _followup, department, _prepaid_schedule, _normal_schedule = self._create_prepayment_delivery_split_fixture()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '선결제 납품이랑 선결제 없이 납품된거 구분해줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'ledger')
        mock_client.assert_not_called()
        split = payload['context']['deliveryPaymentSplit']
        self.assertEqual(split['prepaymentCount'], 1)
        self.assertEqual(split['withoutPrepaymentCount'], 1)
        self.assertIn('선결제Kit', json.dumps(split['prepaymentDeliveries'], ensure_ascii=False))
        self.assertIn('일반Kit', json.dumps(split['withoutPrepaymentDeliveries'], ensure_ascii=False))
        self.assertEqual(payload['questionLog']['source'], 'ledger')
        self.assertFalse(payload['webSearchUsed'])
        self.assertIn('CRM 공통 원장 데이터 기준으로만 분리했습니다', payload['answer']['summary'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_answers_global_action_search_without_department(self, _mock_client):
        from reporting.models import History

        followup, department = self._create_customer(self.user, '전체액션질문')
        other_followup, other_department = self._create_customer(self.user, '전체액션후보')
        today = timezone.localdate()
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='전체 범위에서 먼저 볼 고객',
            next_action='오늘 샘플 반응 확인',
            next_action_date=today,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=other_followup,
            action_type='customer_meeting',
            content='다른 부서 후속',
            next_action='견적 사용 여부 확인',
            next_action_date=today,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_api'),
            data=json.dumps({
                'question': '전체 부서 중 다음 액션 할만한 곳 찾아줘',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertIsNone(payload['department'])
        self.assertEqual(payload['scope']['type'], 'all')
        self.assertEqual(payload['context']['departmentCount'], 2)
        self.assertEqual(payload['context']['customerCount'], 2)
        answer_text = payload['answer']['summary'] + ' '.join(payload['answer']['bullets'])
        self.assertIn('전체 부서', answer_text)
        self.assertIn(department.name, answer_text)
        self.assertIn(other_department.name, answer_text)
        action_items = payload['answer']['actionItems']
        self.assertGreaterEqual(len(action_items), 2)
        self.assertTrue(any(item['department'] == department.name for item in action_items))
        self.assertTrue(any(item['department'] == other_department.name for item in action_items))
        for item in action_items[:2]:
            self.assertTrue(item['reason'])
            self.assertTrue(item['nextAction'])
            self.assertTrue(item['timing'])
            self.assertIsInstance(item['crmEvidence'], list)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_filters_resolved_verified_memory_from_today_actions(self, _mock_client):
        from reporting.models import AIWorkspaceMemory, History

        resolved_followup, _resolved_department = self._create_customer(self.user, '문새롬')
        active_followup, active_department = self._create_customer(self.user, '박준현')
        today = timezone.localdate()
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=resolved_followup,
            action_type='customer_meeting',
            content='피펫 본체 라벨 사진 필요',
            next_action='문새롬 연구원에게 피펫 본체 라벨 사진 또는 정확한 모델명 확인',
            next_action_date=today,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=active_followup,
            action_type='customer_meeting',
            content='담당 변경 확인 필요',
            next_action='박준현 담당자 접점 확인',
            next_action_date=today,
        )
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=None,
            scope_type='all',
            memory_type='correction',
            title='정정 기억',
            content='나는 이미 문새롬 연구원에게 카톡을 통해 피펫 본체 라벨 사진 또는 정확한 모델명을 물어봤으며 해결되었다는 답변을 받았다',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_api'),
            data=json.dumps({'question': '오늘 내가 해야할 일이 있을까?'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        skipped = payload['context']['actionFilter']['skippedActions']
        self.assertTrue(any(item['reason'] == 'verified_memory_resolved' and item['customer'] == '문새롬 담당자' for item in skipped))
        action_text = json.dumps(payload['answer']['actionItems'], ensure_ascii=False)
        self.assertNotIn('문새롬', action_text)
        self.assertIn(active_department.name, action_text)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_filters_recent_sent_email_from_today_actions(self, _mock_client):
        from reporting.models import EmailLog, History

        followup, _department = self._create_customer(self.user, '이준서')
        today = timezone.localdate()
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='email',
            content='6월 예산 편성 후 결정 예정',
            next_action='이준서 연구원에게 6월 초 예산 편성 확인',
            next_action_date=today,
        )
        EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            followup=followup,
            email_type='sent',
            is_sent=True,
            status='sent',
            provider='gmail',
            subject='6월 예산 편성 관련 확인 메일',
            body='이준서 연구원님께 예산 편성 후 검토 가능 시점을 확인드렸습니다.',
            to_email='junseo@example.com',
            to_name='이준서 연구원',
            recipient_email='junseo@example.com',
            recipient_name='이준서 연구원',
            sent_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_api'),
            data=json.dumps({'question': '오늘 내가 해야할 일이 있을까?'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        skipped = payload['context']['actionFilter']['skippedActions']
        self.assertTrue(any(item['reason'] == 'recent_outbound_email' and item['customer'] == '이준서 담당자' for item in skipped))
        self.assertNotIn('이준서', json.dumps(payload['answer']['actionItems'], ensure_ascii=False))

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_applies_explicit_exclusion_names(self, _mock_client):
        from reporting.models import History

        today = timezone.localdate()
        followups = {}
        for name in ['이다민', '김기윤', '한은영', '박준현']:
            followup, department = self._create_customer(self.user, name)
            followups[name] = (followup, department)
            History.objects.create(
                user=self.user,
                company=self.company,
                followup=followup,
                action_type='customer_meeting',
                content=f'{name} 고객 후속',
                next_action=f'{name} 담당자 후속 확인',
                next_action_date=today,
            )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_api'),
            data=json.dumps({
                'question': '오늘 내가 해야할 일이 있을까?? 이다민 연구원이랑 김기윤연구원 한은영교수 제외하고',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        skipped = payload['context']['actionFilter']['skippedActions']
        skipped_text = json.dumps(skipped, ensure_ascii=False)
        self.assertIn('이다민', skipped_text)
        self.assertIn('김기윤', skipped_text)
        self.assertIn('한은영', skipped_text)
        self.assertTrue(all(item['reason'] == 'question_exclusion' for item in skipped if item['customer'] in {'이다민 담당자', '김기윤 담당자', '한은영 담당자'}))
        action_text = json.dumps(payload['answer']['actionItems'], ensure_ascii=False)
        self.assertNotIn('이다민', action_text)
        self.assertNotIn('김기윤', action_text)
        self.assertNotIn('한은영', action_text)
        self.assertIn(followups['박준현'][1].name, action_text)

    def test_ai_workspace_department_question_normalizes_action_items(self):
        from reporting.views import _ai_workspace_normalize_department_question_answer

        result = _ai_workspace_normalize_department_question_answer({
            'answer': '월요일 오후에는 미완료 후속과 높은 우선순위 작업을 먼저 처리합니다.',
            'bullets': ['긴급 후속 2건을 먼저 확인합니다.'],
            'actionItems': [{
                'rank': 1,
                'title': '이다민 고객 후속',
                'customer': '이다민',
                'company': 'AI워크스페이스회사',
                'department': 'PCR 연구실',
                'priority': '높음',
                'reason': '최근 샘플 피드백이 남아 있고 PainPoint 검증이 아직 열려 있습니다.',
                'nextAction': '추가 피드백을 요청하고 Paradigm Tube의 장점을 짧게 정리해 회신합니다.',
                'timing': '월요일 오후 첫 번째 블록에서 확인합니다.',
                'crmEvidence': [{'label': '추천 작업', 'value': 'PainPoint 검증 및 견적 후속'}],
            }],
            'evidence': [{'label': '전체 범위', 'value': '추천 액션 10건'}],
            'confidence': 'high',
        }, {
            'summary': 'fallback',
            'bullets': [],
            'evidence': [],
            'actionItems': [],
            'confidence': 'low',
        })

        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(result['actionItems'][0]['rank'], 1)
        self.assertEqual(result['actionItems'][0]['customer'], '이다민')
        self.assertIn('Paradigm Tube', result['actionItems'][0]['nextAction'])
        self.assertIn('월요일 오후', result['actionItems'][0]['timing'])
        self.assertEqual(result['actionItems'][0]['crmEvidence'][0]['label'], '추천 작업')

    def test_ai_workspace_department_question_normalizes_decision(self):
        from reporting.views import _ai_workspace_normalize_department_question_answer

        result = _ai_workspace_normalize_department_question_answer({
            'answer': '굳이 다시 묻지 말고 재견적 조건 확인으로 짧게 연결합니다.',
            'decision': {
                'recommendedChoice': '재견적 설명 끝에 조건 확인처럼 짧게만 묻습니다.',
                'rejectedChoice': '샘플 피드백을 별도 질문으로 다시 받으려는 접근은 버립니다.',
                'reason': '이미 답한 내용을 반복하면 고객 부담이 커집니다.',
                'exception': '고객이 샘플 얘기를 먼저 꺼내면 구체적으로 물어봅니다.',
            },
            'confidence': 'high',
        }, {
            'summary': 'fallback',
            'bullets': [],
            'evidence': [],
            'actionItems': [],
            'confidence': 'low',
        })

        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(
            result['decision']['recommendedChoice'],
            '재견적 설명 끝에 조건 확인처럼 짧게만 묻습니다.',
        )
        self.assertIn('별도 질문', result['decision']['rejectedChoice'])
        self.assertIn('고객 부담', result['decision']['reason'])
        self.assertIn('먼저 꺼내면', result['decision']['exception'])

    def test_ai_workspace_department_question_normalizes_perspective(self):
        from reporting.views import _ai_workspace_normalize_department_question_answer

        result = _ai_workspace_normalize_department_question_answer({
            'answer': '재견적은 가격 조건 중심으로 전달하고 샘플 평가는 짧게 확인합니다.',
            'perspective': {
                'customerPerspective': '고객 입장에서는 이미 답한 샘플 평가를 다시 묻는다고 느낄 수 있습니다.',
                'salesJudgment': '지난 피드백은 인정하고 구매 판단 기준 확인으로 전환합니다.',
                'recommendedApproach': '재견적 조건을 먼저 설명한 뒤 추가 반영 조건만 묻습니다.',
                'talkTrack': '지난번 말씀 주신 샘플 의견을 반영해 가격 조건 중심으로 정리했습니다.',
                'caution': '샘플 피드백을 독촉하는 톤은 피합니다.',
            },
            'confidence': 'high',
        }, {
            'summary': 'fallback',
            'bullets': [],
            'evidence': [],
            'actionItems': [],
            'confidence': 'low',
        })

        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(
            result['perspective']['customerPerspective'],
            '고객 입장에서는 이미 답한 샘플 평가를 다시 묻는다고 느낄 수 있습니다.',
        )
        self.assertIn('가격 조건', result['perspective']['talkTrack'])
        self.assertIn('독촉', result['perspective']['caution'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_uses_recent_feedback_as_completed_sample_context(self, _mock_client):
        from reporting.models import AIWorkspaceActionFeedback, History, Schedule

        followup, department = self._create_customer(self.user, '샘플맥락')
        Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='customer_meeting',
            notes='이다민 연구원에게 PCR 소모품 샘플 전달 필요',
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='샘플은 전달 예정이고 풀스커트 플레이트 사용 이유를 나중에 확인하기로 함',
            next_action='샘플 전달',
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            action_id='followup:sample-context',
            action_kind='customer_followup',
            status='answered',
            feedback='샘플 주고 왔습니다. 이다민 연구원 반응만 보면 됩니다.',
            ai_result={
                'summary': '샘플 제공 완료로 판단했습니다.',
                'nextAction': '2-3영업일 뒤 사용 반응 확인',
                'source': 'fallback',
            },
            action_snapshot={
                'title': '샘플 전달',
                'customer': followup.customer_name,
                'company': followup.company.name,
                'department': followup.department.name,
            },
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '샘플 줬는데 반응을 기다릴까?',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['context']['recentFeedbackCount'], 1)
        answer_text = payload['answer']['summary'] + ' '.join(payload['answer']['bullets'])
        self.assertIn('완료', answer_text)
        self.assertIn('2-3영업일', answer_text)
        self.assertNotIn('먼저 샘플이 실제로 전달됐는지 확인', answer_text)
        self.assertIn('perspective', payload['answer'])
        self.assertIn('고객 입장', payload['answer']['perspective']['customerPerspective'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_requote_sample_feedback_uses_customer_perspective(self, _mock_client):
        from reporting.models import AIWorkspaceActionFeedback, History

        followup, department = self._create_customer(self.user, '이다민')
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='quote',
            content='가격 협상 완료 후 이다민 연구원에게 재견적 제공 예정',
            next_action='재견적 제공',
        )
        AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            action_id='followup:sample-requote-perspective',
            action_kind='customer_followup',
            status='answered',
            feedback='고객이 제공된 샘플과 기존 제품의 사용감 차이를 느끼지 못했다고 피드백함.',
            ai_result={
                'summary': '샘플 사용감 피드백 수집 완료',
                'nextAction': '재견적 제공 시 조건 확인',
                'source': 'fallback',
            },
            action_snapshot={
                'title': '재견적 제공 및 샘플 피드백 요청',
                'customer': followup.customer_name,
                'company': followup.company.name,
                'department': followup.department.name,
            },
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '재견적을 줄 때 이다민 연구원에게 샘플드린거 피드백을 자연스럽게 받아내는 것이 좋을까? 아니면 굳이 물어보지 않을까?',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        answer_text = payload['answer']['summary'] + ' '.join(payload['answer']['bullets'])
        decision = payload['answer']['decision']
        perspective = payload['answer']['perspective']
        self.assertIn('재견적', answer_text)
        self.assertIn('다시 캐묻기보다', answer_text)
        self.assertIn('구매 판단 기준', answer_text)
        self.assertIn('다시 캐묻지 말고', decision['recommendedChoice'])
        self.assertIn('버립니다', decision['rejectedChoice'])
        self.assertIn('같은 질문 반복', decision['reason'])
        self.assertIn('고객이 먼저', decision['exception'])
        self.assertIn('고객 입장', perspective['customerPerspective'])
        self.assertIn('이미 샘플 사용감 차이를 말했는데', perspective['customerPerspective'])
        self.assertIn('지난번 샘플', perspective['talkTrack'])
        self.assertIn('독촉', perspective['caution'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_question_scale_up_uses_customer_perspective(self, _mock_client):
        from reporting.models import DeliveryItem, History, Schedule
        from decimal import Decimal

        followup, department = self._create_customer(self.user, '면역제어')
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='delivery',
            status='completed',
            expected_revenue=Decimal('906400'),
            purchase_confirmed=True,
            notes='최근 팁 납품 완료',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='P4235N00',
            quantity=10,
            unit_price=Decimal('41360'),
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='팁류 저희한테 주문하시는데 아직 팁 재고 여유 있는지 여쭤보니 아직 여유 있다고 함',
            next_action='다른 제품 필요성 확인',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '해당 연구실의 주문 물품을 스케일업 하고싶어',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        answer_text = payload['answer']['summary'] + ' '.join(payload['answer']['bullets'])
        decision = payload['answer']['decision']
        perspective = payload['answer']['perspective']
        self.assertIn('소모 속도', answer_text)
        self.assertIn('구매 압박', answer_text)
        self.assertIn('같은 품목 추가 주문을 바로 밀지 말고', decision['recommendedChoice'])
        self.assertIn('즉시 업셀', decision['rejectedChoice'])
        self.assertIn('구매 압박은 낮으므로', decision['reason'])
        self.assertIn('재고가 충분한 품목', perspective['customerPerspective'])
        self.assertIn('동반 구매 품목', perspective['salesJudgment'])
        self.assertIn('바로 추가 주문', perspective['talkTrack'])

    def test_ai_workspace_question_context_includes_product_master_facts(self):
        from decimal import Decimal
        from reporting.models import DeliveryItem, Product, Schedule
        from reporting.views import _ai_workspace_department_question_context

        followup, department = self._create_customer(self.user, '제품근거')
        product = Product.objects.create(
            product_code='P4345N00',
            description='RLD-1250NS, 1250 µL Low Retention Paradigm Refills, Benchtop, 8 x 96 / pk',
            specification='5 pk / CS',
            unit='pk',
            standard_price=Decimal('1000'),
            created_by=self.user,
        )
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=timezone.now().time(),
            activity_type='delivery',
            status='completed',
            expected_revenue=Decimal('1000'),
            purchase_confirmed=True,
            notes='제품 마스터 연결 납품',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            product=product,
            item_name=product.product_code,
            quantity=1,
            unit_price=Decimal('1000'),
        )

        context = _ai_workspace_department_question_context(department, self.user)

        self.assertEqual(context['productFacts'][0]['code'], 'P4345N00')
        self.assertEqual(context['productFacts'][0]['unit'], 'pk')
        self.assertIn('Low Retention Paradigm Refills', context['productFacts'][0]['description'])
        self.assertIn('5 pk / CS', context['productFacts'][0]['label'])
        self.assertIn('P4345N00', context['recentDeliveries'][0]['items'])
        self.assertIn('Low Retention Paradigm Refills', context['recentDeliveries'][0]['items'])

    def test_ai_workspace_question_context_includes_recent_email_history(self):
        from reporting.models import EmailLog
        from reporting.views import _ai_workspace_department_question_context

        followup, department = self._create_customer(self.user, '메일컨텍스트')
        EmailLog.objects.create(
            user=self.user,
            followup=followup,
            email_type='received',
            status='received',
            from_email='customer@example.com',
            sender_email='customer@example.com',
            to_email='sales@example.com',
            recipient_email='sales@example.com',
            subject='샘플 사용 후 추가 견적 요청',
            body='메일 본문: 고객이 팁 샘플은 괜찮고 다음 견적에 10박스를 포함해 달라고 요청했습니다.',
            received_at=timezone.now(),
        )

        context = _ai_workspace_department_question_context(department, self.user)

        self.assertEqual(len(context['recentEmails']), 1)
        self.assertEqual(context['recentEmails'][0]['directionLabel'], '받은 메일')
        self.assertIn('추가 견적 요청', context['recentEmails'][0]['subject'])
        self.assertIn('10박스', context['recentEmails'][0]['body'])
        self.assertEqual(context['recentEmails'][0]['customer'], followup.customer_name)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('no api key'))
    def test_ai_workspace_department_question_fallback_uses_recent_email_when_requested(self, _mock_client):
        from reporting.models import EmailLog

        followup, department = self._create_customer(self.user, '메일질문')
        EmailLog.objects.create(
            user=self.user,
            followup=followup,
            email_type='received',
            status='received',
            from_email='customer@example.com',
            sender_email='customer@example.com',
            to_email='sales@example.com',
            recipient_email='sales@example.com',
            subject='견적서 회신',
            body='메일 본문: 고객이 ResinTech 수지 납기와 견적 유효기간을 다시 확인해 달라고 했습니다.',
            received_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '메일 참고해서 다음 액션을 알려줘',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['context']['recentEmailCount'], 1)
        answer_text = payload['answer']['summary'] + ' '.join(payload['answer']['bullets'])
        self.assertIn('견적서 회신', answer_text)
        self.assertIn('납기', answer_text)
        evidence_text = ' '.join(item['value'] for item in payload['answer']['evidence'])
        self.assertIn('ResinTech 수지', evidence_text)

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_department_question_prompt_includes_recent_email_history(self, mock_client):
        from types import SimpleNamespace
        from reporting.models import EmailLog

        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                content = json.dumps({
                    'answer': '최근 메일 기준으로 납기와 견적 유효기간 회신이 우선입니다.',
                    'bullets': ['메일 본문을 근거로 회신합니다.'],
                    'evidence': [{'label': '메일', 'value': '납기 확인 요청'}],
                    'confidence': 'high',
                })
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        mock_client.return_value = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        followup, department = self._create_customer(self.user, '메일프롬프트')
        EmailLog.objects.create(
            user=self.user,
            followup=followup,
            email_type='received',
            status='received',
            from_email='customer@example.com',
            sender_email='customer@example.com',
            to_email='sales@example.com',
            recipient_email='sales@example.com',
            subject='AI가 반드시 봐야 하는 메일',
            body='메일 본문: 고객이 교정 성적서와 납품 가능일을 먼저 알려달라고 했습니다.',
            received_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '메일 참고해서 어떻게 답할지 알려줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['source'], 'openai')
        prompt_payload = json.loads(captured['messages'][1]['content'])
        self.assertEqual(len(prompt_payload['crmContext']['recentEmails']), 1)
        self.assertIn('반드시 봐야 하는 메일', prompt_payload['crmContext']['recentEmails'][0]['subject'])
        self.assertIn('교정 성적서', prompt_payload['crmContext']['recentEmails'][0]['body'])
        rules_text = '\n'.join(prompt_payload['rules'])
        self.assertIn('crmContext.recentEmails', rules_text)
        self.assertIn('메일/이메일/회신/답장', rules_text)

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_department_question_prompt_request_stays_freeform(self, mock_client):
        from types import SimpleNamespace

        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                content = json.dumps({
                    'answer': (
                        '아래 프롬프트를 외부 AI에 그대로 보내세요.\n\n'
                        '상황: 고객은 내부 비교 검토 중이며 행정 담당자에게 전달할 자료가 필요합니다.\n'
                        '요청: 다음 메일 전략과 확인해야 할 조건을 CRM 맥락 기준으로 제안해 주세요.'
                    ),
                    'confidence': 'high',
                })
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        mock_client.return_value = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        _followup, department = self._create_customer(self.user, '외부프롬프트')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '외부 AI한테 전략 상담받게 보낼 프롬프트 하나 만들어줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'openai')
        self.assertIn('외부 AI에 그대로', payload['answer']['summary'])
        self.assertIn('\n', payload['answer']['summary'])
        self.assertEqual(payload['answer']['actionItems'], [])
        self.assertNotIn('decision', payload['answer'])
        self.assertNotIn('perspective', payload['answer'])

        prompt_payload = json.loads(captured['messages'][1]['content'])
        self.assertEqual(prompt_payload['responseGuidance']['intent'], 'external_ai_prompt')
        rules_text = '\n'.join(prompt_payload['rules'])
        self.assertIn('답변 형식은 질문 의도에 맞게 자유롭게 선택', rules_text)
        self.assertIn('프롬프트 생성 요청에서는 추천 판단', rules_text)

    def test_ai_workspace_department_question_normalizer_does_not_inject_fallback_cards(self):
        from reporting.views import _ai_workspace_normalize_department_question_answer

        result = _ai_workspace_normalize_department_question_answer({
            'answer': '완성형 프롬프트:\n상황과 목표를 넣고 다음 액션 전략을 제안해 달라고 요청하세요.',
            'confidence': 'high',
        }, {
            'summary': 'fallback',
            'bullets': ['fallback bullet'],
            'evidence': [{'label': 'fallback', 'value': 'fallback evidence'}],
            'actionItems': [{
                'rank': 1,
                'title': 'fallback action',
                'nextAction': 'fallback next action',
            }],
            'decision': {'recommendedChoice': 'fallback decision'},
            'perspective': {'recommendedApproach': 'fallback approach'},
            'confidence': 'low',
        })

        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(result['bullets'], [])
        self.assertEqual(result['evidence'], [])
        self.assertEqual(result['actionItems'], [])
        self.assertNotIn('decision', result)
        self.assertNotIn('perspective', result)

    def test_ai_workspace_department_question_answer_adds_readable_line_breaks(self):
        from reporting.views import _ai_workspace_question_answer_text

        raw_answer = (
            '서울대학교 미생물공생및면역연구실 기준으로 보면, 납품 주기는 최근 실적상 평균 약 116일에 1회 수준입니다. '
            '다만 최근에는 2026-02-25 → 2026-04-08로 약 43일 간격입니다. '
            '1) **재구매 가능성이 높은 품목** - **SO3090.0010Tx10**: 최근 3회 납품 모두 연결된 핵심 품목입니다. '
            '2) **추가로 팔 수 있는 가능성이 있는 품목** - **PCR 관련 소모품 샘플 제안품**: 샘플 제안 여지가 있습니다. '
            '3) **거래 가능성 판단** - **높음**: SO3090.0010Tx10 재주문입니다. 정리하면, 재구매 기반이 있는 부서입니다.'
        )

        formatted = _ai_workspace_question_answer_text(raw_answer)

        self.assertIn('\n\n다만 최근에는', formatted)
        self.assertIn('\n\n1) **재구매 가능성이 높은 품목**', formatted)
        self.assertIn('\n- **SO3090.0010Tx10**:', formatted)
        self.assertIn('\n\n2) **추가로 팔 수 있는 가능성이 있는 품목**', formatted)
        self.assertIn('\n- **PCR 관련 소모품 샘플 제안품**:', formatted)
        self.assertIn('\n\n정리하면,', formatted)

    def test_ai_workspace_department_question_answer_preserves_existing_line_breaks(self):
        from reporting.views import _ai_workspace_question_answer_text

        raw_answer = '완성형 프롬프트:\n\n상황: 고객은 내부 비교 검토 중입니다.\n요청: 다음 메일 전략을 제안해 주세요.'

        formatted = _ai_workspace_question_answer_text(raw_answer)

        self.assertIn('완성형 프롬프트:\n\n상황:', formatted)
        self.assertIn('\n요청:', formatted)

    def test_ai_workspace_department_question_product_guard_replaces_unsupported_label(self):
        from reporting.views import _ai_workspace_normalize_department_question_answer

        context = {
            'productFacts': [{
                'code': 'P4345N00',
                'label': 'P4345N00 (RLD-1250NS, 1250 µL Low Retention Paradigm Refills, Benchtop, 8 x 96 / pk, 5 pk / CS, 단위 pk)',
                'description': 'RLD-1250NS, 1250 µL Low Retention Paradigm Refills, Benchtop, 8 x 96 / pk',
                'specification': '5 pk / CS',
                'unit': 'pk',
            }],
        }

        result = _ai_workspace_normalize_department_question_answer({
            'answer': '김혜원 고객의 기존 팁 사용을 기반으로 튜브(P4345N00)와 연계 업셀을 먼저 봅니다.',
            'actionItems': [{
                'rank': 1,
                'title': '튜브(P4345N00) 업셀',
                'customer': '김혜원',
                'department': '제품근거 연구실',
                'reason': '튜브(P4345N00)를 최근 구매했습니다.',
                'nextAction': '튜브(P4345N00) 추가 구매보다 소모 속도를 확인합니다.',
                'timing': '이번 주',
                'crmEvidence': [{'label': '품목', 'value': '튜브(P4345N00)'}],
            }],
            'evidence': [{'label': '납품 품목', 'value': '튜브(P4345N00)'}],
            'confidence': 'high',
        }, {
            'summary': 'fallback',
            'bullets': [],
            'evidence': [],
            'actionItems': [],
            'confidence': 'low',
        }, context)

        result_text = json.dumps(result, ensure_ascii=False)
        self.assertNotIn('튜브(P4345N00)', result_text)
        self.assertIn('P4345N00 (RLD-1250NS', result_text)
        self.assertIn('Low Retention Paradigm Refills', result_text)

    def test_schedule_ai_coach_requires_ai_permission(self):
        from datetime import time

        followup, _department = self._create_customer(self.no_ai_user, '일정코치권한없음')
        schedule = Schedule.objects.create(
            user=self.no_ai_user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        self.client.force_login(self.no_ai_user)

        response = self.client.post(reverse('reporting:schedule_ai_coach_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_schedule_ai_coach_blocks_inaccessible_schedule(self):
        from datetime import time

        outsider = make_user('ai_workspace_schedule_outsider', role='salesman', can_use_ai=True, company=self.other_company)
        followup, _department = self._create_customer(outsider, '일정코치타사회사')
        schedule = Schedule.objects.create(
            user=outsider,
            company=self.other_company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=time(10, 0),
            activity_type='customer_meeting',
            status='scheduled',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:schedule_ai_coach_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_schedule_ai_coach_returns_unsaved_fallback_for_accessible_schedule(self):
        from datetime import time
        from decimal import Decimal
        from reporting.models import AIWorkspaceQuestionLog, DeliveryItem

        followup, _department = self._create_customer(self.user, '일정코치')
        schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=time(14, 30),
            activity_type='delivery',
            status='scheduled',
            expected_revenue=Decimal('330000'),
            notes='납품 품목과 세금계산서 확인 필요',
        )
        DeliveryItem.objects.create(
            schedule=schedule,
            item_name='P1000',
            quantity=3,
            unit='EA',
            unit_price=Decimal('100000'),
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:schedule_ai_coach_api', args=[schedule.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['context']['scheduleId'], schedule.id)
        self.assertFalse(payload['context']['stored'])
        self.assertIn('납품', payload['coach']['summary'])
        self.assertTrue(payload['coach']['afterMeetingNoteDraft']['content'])
        self.assertEqual(payload['coach']['afterMeetingNoteDraft']['actionType'], 'delivery_schedule')
        self.assertEqual(AIWorkspaceQuestionLog.objects.count(), 0)

    def test_ai_workspace_department_question_requires_ai_permission(self):
        _followup, department = self._create_customer(self.no_ai_user, '질문권한없음')
        self.client.force_login(self.no_ai_user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '마지막 주문일 알려줘',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_ai_workspace_department_question_blocks_inaccessible_department(self):
        _own_followup, _own_department = self._create_customer(self.user, '질문내부서')
        _coworker_followup, coworker_department = self._create_customer(self.coworker, '질문동료부서')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': coworker_department.id,
                'question': '마지막 주문일 알려줘',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'department_not_found')

    def test_ai_workspace_department_question_records_question_log(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문기록')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '마지막 주문일 알려줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['questionLog']['department']['id'], department.id)
        self.assertEqual(payload['questionLog']['question'], '마지막 주문일 알려줘')
        self.assertEqual(payload['questionLog']['source'], payload['source'])
        self.assertEqual(payload['model'], 'gpt-5.4-mini')
        self.assertEqual(payload['questionLog']['model'], 'gpt-5.4-mini')

        log = AIWorkspaceQuestionLog.objects.get(user=self.user)
        self.assertEqual(log.department, department)
        self.assertEqual(log.scope_type, 'department')
        self.assertEqual(log.model, 'gpt-5.4-mini')
        self.assertEqual(log.question, '마지막 주문일 알려줘')
        self.assertIn('summary', log.answer_snapshot)

    def test_ai_workspace_department_question_normalizes_legacy_model_to_mini(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문모델정리')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '기존 5.5 선택값이 남아 있어도 답변해줘',
                'model': 'gpt-5.5',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['model'], 'gpt-5.4-mini')
        log = AIWorkspaceQuestionLog.objects.get(user=self.user)
        self.assertEqual(log.model, 'gpt-5.4-mini')

    def test_ai_workspace_department_question_records_all_scope_question_log(self):
        from reporting.models import AIWorkspaceQuestionLog

        self._create_customer(self.user, '전체질문A')
        self._create_customer(self.user, '전체질문B')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'scopeType': 'all',
                'question': '전체 부서에서 오늘 우선 챙길 곳을 찾아줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['scope']['type'], 'all')
        self.assertEqual(payload['scope']['departmentId'], None)
        self.assertEqual(payload['department'], None)
        self.assertEqual(payload['questionLog']['scopeType'], 'all')
        self.assertEqual(payload['questionLog']['department'], None)
        self.assertEqual(payload['model'], 'gpt-5.4-mini')
        self.assertGreaterEqual(payload['context']['departmentCount'], 1)

        log = AIWorkspaceQuestionLog.objects.get(user=self.user)
        self.assertIsNone(log.department)
        self.assertEqual(log.scope_type, 'all')
        self.assertEqual(log.model, 'gpt-5.4-mini')
        self.assertIn('summary', log.answer_snapshot)

    def test_ai_workspace_question_log_detail_api_returns_full_answer_for_owner(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문상세')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='이 부서 재견적은 어떻게 할까?',
            answer_snapshot={
                'summary': '재견적은 바로 보내되, 고객의 샘플 피드백을 먼저 확인하는 조건부 접근이 좋습니다.',
                'bullets': ['견적 회신율을 KPI로 봅니다.', '다음 연락은 2일 안에 잡습니다.'],
                'decision': {
                    'recommendedChoice': '조건부 재견적',
                    'rejectedChoice': '무조건 가격 인하',
                    'reason': '최근 반응이 확인되지 않았기 때문입니다.',
                    'exception': '구매 일정이 확정되어 있으면 바로 견적을 보냅니다.',
                },
                'perspective': {
                    'customerPerspective': '고객은 가격보다 실험 적합성을 먼저 확인하려 할 수 있습니다.',
                    'salesJudgment': '영업 판단상 피드백 확인 후 재견적이 안전합니다.',
                    'recommendedApproach': '샘플 사용 결과를 한 문장으로 확인합니다.',
                    'talkTrack': '샘플 써보신 기준으로 조정할 조건이 있을까요?',
                    'caution': '가격 인하를 먼저 꺼내지 않습니다.',
                },
                'actionItems': [{
                    'rank': 1,
                    'title': '샘플 피드백 확인',
                    'customer': '질문상세 고객',
                    'company': self.company.name,
                    'department': department.name,
                    'priority': 'high',
                    'reason': '재견적 조건을 정해야 합니다.',
                    'nextAction': '담당자에게 샘플 사용 결과와 수량 조건을 확인합니다.',
                    'timing': '오늘 오후',
                    'crmEvidence': [{'label': 'CRM', 'value': '질문상세 기록'}],
                }],
                'evidence': [{'label': '근거', 'value': '최근 견적 기록'}],
                'confidence': 'medium',
            },
            source='openai',
            model='gpt-5.5',
            web_search_used=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:ai_workspace_question_log_detail_api', args=[log.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['questionLog']['id'], log.id)
        self.assertEqual(payload['questionLog']['question'], '이 부서 재견적은 어떻게 할까?')
        self.assertEqual(payload['questionLog']['answer']['summary'], log.answer_snapshot['summary'])
        self.assertEqual(payload['questionLog']['answer']['decision']['recommendedChoice'], '조건부 재견적')
        self.assertEqual(payload['questionLog']['answer']['actionItems'][0]['nextAction'], '담당자에게 샘플 사용 결과와 수량 조건을 확인합니다.')
        self.assertIn(f'department_id={department.id}', payload['links']['aiWorkspace'])

    def test_ai_workspace_question_log_detail_api_blocks_other_users_log(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.coworker, '질문상세동료')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 질문',
            answer_snapshot={'summary': '동료 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:ai_workspace_question_log_detail_api', args=[log.id]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'question_log_not_found')

    def test_ai_workspace_question_log_delete_api_deletes_owner_log(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문삭제')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='삭제할 질문',
            answer_snapshot={'summary': '삭제할 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:ai_workspace_question_log_delete_api', args=[log.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['deletedId'], log.id)
        self.assertIn(f'department_id={department.id}', payload['links']['aiWorkspace'])
        self.assertFalse(AIWorkspaceQuestionLog.objects.filter(id=log.id).exists())

    def test_ai_workspace_question_log_delete_api_blocks_other_users_log(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.coworker, '질문삭제동료')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 삭제 시도',
            answer_snapshot={'summary': '동료 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('reporting:ai_workspace_question_log_delete_api', args=[log.id]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'question_log_not_found')
        self.assertTrue(AIWorkspaceQuestionLog.objects.filter(id=log.id).exists())

    def test_ai_workspace_question_log_delete_api_requires_ai_permission(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.no_ai_user, '질문삭제권한없음')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.no_ai_user,
            department=department,
            scope_type='department',
            question='권한 없는 사용자 기록',
            answer_snapshot={'summary': '권한 없는 사용자 답변'},
            source='fallback',
        )
        self.client.force_login(self.no_ai_user)

        response = self.client.post(reverse('reporting:ai_workspace_question_log_delete_api', args=[log.id]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')
        self.assertTrue(AIWorkspaceQuestionLog.objects.filter(id=log.id).exists())

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_department_question_uses_crm_strategy_system_prompt(self, mock_client):
        from types import SimpleNamespace

        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                content = json.dumps({
                    'answer': '상황 진단: 견적 후속과 고객 반응 확인이 우선입니다.',
                    'bullets': ['KPI는 다음 연락 완료율과 견적 회신율로 봅니다.'],
                    'evidence': [{'label': 'CRM', 'value': '테스트 근거'}],
                    'confidence': 'high',
                })
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        mock_client.return_value = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        _followup, department = self._create_customer(self.user, '전략프롬프트')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '이 부서 CRM 전략 방향을 정리해줘',
                'model': 'gpt-5.4-mini',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['source'], 'openai')
        system_prompt = captured['messages'][0]['content']
        from reporting.views import AI_WORKSPACE_CRM_STRATEGY_SYSTEM_PROMPT
        self.assertEqual(system_prompt, AI_WORKSPACE_CRM_STRATEGY_SYSTEM_PROMPT)
        prompt_payload = json.loads(captured['messages'][1]['content'])
        self.assertNotIn('answerDirection', prompt_payload['crmContext'])
        rules_text = '\n'.join(prompt_payload['rules'])
        self.assertIn('JSON 객체만 반환', rules_text)
        self.assertIn('"answer": string', rules_text)

    def test_ai_workspace_department_question_normalizes_unsupported_model_to_mini(self):
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문모델검증')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_department_question_api'),
            data=json.dumps({
                'departmentId': department.id,
                'question': '마지막 주문일 알려줘',
                'model': 'unsupported-model',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['model'], 'gpt-5.4-mini')
        self.assertEqual(AIWorkspaceQuestionLog.objects.get().model, 'gpt-5.4-mini')

    def test_ai_workspace_summary_includes_department_question_history_with_pagination(self):
        from datetime import timedelta
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '질문이력')
        _other_followup, other_department = self._create_customer(self.user, '다른질문이력')
        now = timezone.now()
        for index in range(7):
            log = AIWorkspaceQuestionLog.objects.create(
                user=self.user,
                department=department,
                scope_type='department',
                question=f'내 질문 {index}',
                answer_snapshot={'summary': f'내 답변 {index}'},
                source='fallback',
            )
            AIWorkspaceQuestionLog.objects.filter(pk=log.pk).update(created_at=now + timedelta(seconds=index))
        AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 질문',
            answer_snapshot={'summary': '동료 답변'},
            source='fallback',
        )
        AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=other_department,
            scope_type='department',
            question='다른 부서 질문',
            answer_snapshot={'summary': '다른 부서 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {
            'department_id': department.id,
            'question_page': 2,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        history = payload['questionHistory']
        self.assertEqual(history['departmentId'], department.id)
        self.assertEqual(history['page'], 2)
        self.assertEqual(history['pageSize'], 5)
        self.assertEqual(history['total'], 7)
        self.assertEqual(history['totalPages'], 2)
        self.assertEqual(len(history['items']), 2)
        history_text = json.dumps(history, ensure_ascii=False)
        self.assertIn('내 질문', history_text)
        self.assertNotIn('동료 질문', history_text)
        self.assertNotIn('다른 부서 질문', history_text)
        self.assertNotIn('answerDirection', payload)

    def test_ai_workspace_summary_includes_all_scope_question_history(self):
        from datetime import timedelta
        from reporting.models import AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '전체질문이력')
        now = timezone.now()
        for index in range(6):
            log = AIWorkspaceQuestionLog.objects.create(
                user=self.user,
                department=None,
                scope_type='all',
                question=f'전체 질문 {index}',
                answer_snapshot={'summary': f'전체 답변 {index}'},
                source='fallback',
                model='gpt-5.5',
            )
            AIWorkspaceQuestionLog.objects.filter(pk=log.pk).update(created_at=now + timedelta(seconds=index))
        AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='부서 질문',
            answer_snapshot={'summary': '부서 답변'},
            source='fallback',
        )
        AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=None,
            scope_type='all',
            question='동료 전체 질문',
            answer_snapshot={'summary': '동료 전체 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {
            'department_id': department.id,
            'question_scope': 'all',
            'question_page': 2,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        history = payload['questionHistory']
        self.assertEqual(history['scopeType'], 'all')
        self.assertEqual(history['departmentId'], None)
        self.assertEqual(history['page'], 2)
        self.assertEqual(history['pageSize'], 5)
        self.assertEqual(history['total'], 6)
        self.assertEqual(history['totalPages'], 2)
        self.assertEqual(len(history['items']), 1)
        history_text = json.dumps(history, ensure_ascii=False)
        self.assertIn('전체 질문', history_text)
        self.assertNotIn('부서 질문', history_text)
        self.assertNotIn('동료 전체 질문', history_text)

    def test_ai_workspace_question_feedback_api_requires_ai_permission(self):
        _followup, department = self._create_customer(self.no_ai_user, '질문피드백권한없음')
        self.client.force_login(self.no_ai_user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_feedback_api'),
            data=json.dumps({
                'departmentId': department.id,
                'scopeType': 'department',
                'question': '재견적 피드백을 물어볼까?',
                'answer': {'summary': '짧게 조건 확인만 하세요.', 'confidence': 'medium'},
                'source': 'fallback',
                'rating': 'helpful',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_ai_workspace_question_feedback_api_records_feedback(self):
        from reporting.models import AIWorkspaceQuestionFeedback

        _followup, department = self._create_customer(self.user, '질문피드백저장')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_feedback_api'),
            data=json.dumps({
                'departmentId': department.id,
                'scopeType': 'department',
                'question': '재견적 피드백을 물어볼까?',
                'answer': {
                    'summary': '샘플 피드백을 다시 캐묻지 말고 조건 확인처럼 짧게 묻습니다.',
                    'decision': {
                        'recommendedChoice': '짧게 확인',
                        'rejectedChoice': '다시 캐묻기',
                    },
                    'confidence': 'medium',
                },
                'source': 'fallback',
                'rating': 'needs_style',
                'comment': '답변 첫 문장은 더 단호하게 추천부터 말해줘.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['feedback']['rating'], 'needs_style')
        self.assertEqual(payload['feedback']['department']['id'], department.id)
        self.assertIn('다음 질문 답변', payload['message'])

        feedback = AIWorkspaceQuestionFeedback.objects.get(user=self.user)
        self.assertEqual(feedback.department, department)
        self.assertEqual(feedback.scope_type, 'department')
        self.assertEqual(feedback.source, 'fallback')
        self.assertIn('더 단호하게', feedback.comment)
        self.assertIn('샘플 피드백', feedback.answer_snapshot['summary'])
        self.assertEqual(feedback.answer_snapshot['decision']['recommendedChoice'], '짧게 확인')

    def test_ai_workspace_question_feedback_api_requires_comment_for_negative_rating(self):
        from reporting.models import AIWorkspaceQuestionFeedback

        _followup, department = self._create_customer(self.user, '질문피드백코멘트')
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_question_feedback_api'),
            data=json.dumps({
                'departmentId': department.id,
                'scopeType': 'department',
                'question': '스케일업을 제안할까?',
                'answer': {'summary': '소모 속도를 먼저 확인하세요.'},
                'source': 'openai',
                'rating': 'incorrect',
                'comment': '',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'missing_comment')
        self.assertEqual(AIWorkspaceQuestionFeedback.objects.count(), 0)

    def test_ai_workspace_memory_create_api_records_verified_memory(self):
        from reporting.models import AIWorkspaceMemory, AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.user, '검수기억저장')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='P4345N00이 튜브야?',
            answer_snapshot={'summary': '잘못된 답변'},
            source='openai',
            model='gpt-5.4-mini',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_memory_create_api'),
            data=json.dumps({
                'departmentId': department.id,
                'scopeType': 'department',
                'questionLogId': log.id,
                'memoryType': 'correction',
                'title': 'P4345N00 품목 정정',
                'content': 'P4345N00은 튜브가 아니라 팁으로 취급한다.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['memory']['memoryType'], 'correction')
        self.assertEqual(payload['memory']['department']['id'], department.id)
        self.assertIn('다음 질문', payload['message'])

        memory = AIWorkspaceMemory.objects.get(user=self.user)
        self.assertEqual(memory.department, department)
        self.assertEqual(memory.source_question_log, log)
        self.assertEqual(memory.scope_type, 'department')
        self.assertEqual(memory.memory_type, 'correction')
        self.assertIn('튜브가 아니라 팁', memory.content)
        self.assertTrue(memory.is_active)

    def test_ai_workspace_memory_create_api_blocks_other_users_question_log(self):
        from reporting.models import AIWorkspaceMemory, AIWorkspaceQuestionLog

        _followup, department = self._create_customer(self.coworker, '동료검수기억')
        log = AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 질문',
            answer_snapshot={'summary': '동료 답변'},
            source='fallback',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_memory_create_api'),
            data=json.dumps({
                'departmentId': department.id,
                'scopeType': 'department',
                'questionLogId': log.id,
                'memoryType': 'correction',
                'content': '동료 기록은 내 기억으로 저장되면 안 됩니다.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'question_log_not_found')
        self.assertEqual(AIWorkspaceMemory.objects.count(), 0)

    def test_ai_workspace_memories_api_lists_only_current_user_with_filters(self):
        from reporting.models import AIWorkspaceMemory

        _followup, department = self._create_customer(self.user, '기억목록')
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            memory_type='correction',
            title='P4345N00 정정',
            content='P4345N00은 튜브가 아니라 팁입니다.',
        )
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=None,
            scope_type='all',
            memory_type='preference',
            title='답변 방식',
            content='제품 마스터 근거를 먼저 보여줍니다.',
            is_active=False,
        )
        AIWorkspaceMemory.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            memory_type='correction',
            title='동료 기억',
            content='동료 기억은 보이면 안 됩니다.',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('reporting:ai_workspace_memories_api'), {
            'status': 'active',
            'scope': 'department',
            'memory_type': 'correction',
            'q': 'P4345',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['counts']['total'], 2)
        self.assertEqual(payload['counts']['active'], 1)
        self.assertEqual(payload['counts']['inactive'], 1)
        self.assertEqual(payload['counts']['filtered'], 1)
        self.assertEqual(payload['pagination']['totalPages'], 1)
        self.assertEqual(len(payload['memories']), 1)
        self.assertEqual(payload['memories'][0]['title'], 'P4345N00 정정')
        payload_text = json.dumps(payload, ensure_ascii=False)
        self.assertIn('튜브가 아니라 팁', payload_text)
        self.assertNotIn('동료 기억', payload_text)
        self.assertNotIn('제품 마스터 근거', payload_text)

    def test_ai_workspace_memories_api_requires_ai_permission(self):
        self.client.force_login(self.no_ai_user)

        response = self.client.get(reverse('reporting:ai_workspace_memories_api'))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_ai_workspace_memory_update_api_updates_current_user_memory(self):
        from reporting.models import AIWorkspaceMemory

        _followup, department = self._create_customer(self.user, '기억수정')
        memory = AIWorkspaceMemory.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            memory_type='fact',
            title='기존 제목',
            content='기존 내용',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_memory_update_api', args=[memory.id]),
            data=json.dumps({
                'scopeType': 'all',
                'memoryType': 'preference',
                'title': '수정된 기억',
                'content': '답변은 결론부터 말하고 근거를 나중에 정리합니다.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['memory']['scopeType'], 'all')
        self.assertEqual(payload['memory']['department'], None)
        self.assertEqual(payload['memory']['memoryType'], 'preference')
        self.assertEqual(payload['memory']['title'], '수정된 기억')

        memory.refresh_from_db()
        self.assertEqual(memory.scope_type, 'all')
        self.assertIsNone(memory.department)
        self.assertEqual(memory.memory_type, 'preference')
        self.assertIn('결론부터', memory.content)

    def test_ai_workspace_memory_update_api_blocks_other_users_memory(self):
        from reporting.models import AIWorkspaceMemory

        _followup, department = self._create_customer(self.coworker, '타인기억수정')
        memory = AIWorkspaceMemory.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            memory_type='fact',
            title='타인 기억',
            content='수정되면 안 됩니다.',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_memory_update_api', args=[memory.id]),
            data=json.dumps({'title': '침범'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'memory_not_found')
        memory.refresh_from_db()
        self.assertEqual(memory.title, '타인 기억')

    def test_ai_workspace_memory_update_api_blocks_inaccessible_department(self):
        from reporting.models import AIWorkspaceMemory

        _followup, department = self._create_customer(self.user, '기억부서수정')
        _coworker_followup, coworker_department = self._create_customer(self.coworker, '기억동료부서')
        memory = AIWorkspaceMemory.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            memory_type='fact',
            title='내 기억',
            content='내 부서 기억입니다.',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_memory_update_api', args=[memory.id]),
            data=json.dumps({
                'scopeType': 'department',
                'departmentId': coworker_department.id,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'department_not_found')
        memory.refresh_from_db()
        self.assertEqual(memory.department, department)

    def test_ai_workspace_memory_toggle_active_controls_question_context(self):
        from reporting.models import AIWorkspaceMemory
        from reporting.views import _ai_workspace_department_question_context

        _followup, department = self._create_customer(self.user, '기억활성토글')
        memory = AIWorkspaceMemory.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            memory_type='correction',
            title='토글 기억',
            content='토글된 기억은 활성일 때만 문맥에 들어갑니다.',
        )
        self.client.force_login(self.user)

        inactive_response = self.client.post(
            reverse('reporting:ai_workspace_memory_toggle_active_api', args=[memory.id]),
            data=json.dumps({'isActive': False}),
            content_type='application/json',
        )
        self.assertEqual(inactive_response.status_code, 200)
        self.assertFalse(inactive_response.json()['memory']['isActive'])
        inactive_context = _ai_workspace_department_question_context(department, self.user)
        self.assertNotIn(
            '토글된 기억',
            json.dumps(inactive_context['verifiedMemories'], ensure_ascii=False),
        )

        active_response = self.client.post(
            reverse('reporting:ai_workspace_memory_toggle_active_api', args=[memory.id]),
            data=json.dumps({'isActive': True}),
            content_type='application/json',
        )
        self.assertEqual(active_response.status_code, 200)
        self.assertTrue(active_response.json()['memory']['isActive'])
        active_context = _ai_workspace_department_question_context(department, self.user)
        self.assertIn(
            '토글된 기억',
            json.dumps(active_context['verifiedMemories'], ensure_ascii=False),
        )

    def test_ai_workspace_question_context_includes_verified_memories_and_recent_question_logs(self):
        from reporting.models import AIWorkspaceMemory, AIWorkspaceQuestionLog
        from reporting.views import _ai_workspace_department_question_context

        _followup, department = self._create_customer(self.user, '검수기억문맥')
        _other_followup, other_department = self._create_customer(self.user, '검수기억다른부서')
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            memory_type='correction',
            title='P4345N00 정정',
            content='P4345N00은 튜브가 아니라 팁으로 판단한다.',
        )
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=None,
            scope_type='all',
            memory_type='preference',
            title='근거 우선',
            content='제품 판단은 제품 마스터와 검수 기억을 먼저 사용한다.',
        )
        AIWorkspaceMemory.objects.create(
            user=self.user,
            department=other_department,
            scope_type='department',
            memory_type='fact',
            title='다른 부서 기억',
            content='다른 부서 기억은 섞이면 안 됩니다.',
        )
        AIWorkspaceMemory.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            memory_type='correction',
            title='동료 기억',
            content='동료 기억은 섞이면 안 됩니다.',
        )
        AIWorkspaceQuestionLog.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='이전 질문',
            answer_snapshot={'summary': '이전 답변', 'decision': {'recommendedChoice': '샘플 확인'}},
            source='openai',
            model='gpt-5.4-mini',
        )
        AIWorkspaceQuestionLog.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 이전 질문',
            answer_snapshot={'summary': '동료 이전 답변'},
            source='fallback',
        )

        context = _ai_workspace_department_question_context(department, self.user)

        memory_text = json.dumps(context['verifiedMemories'], ensure_ascii=False)
        log_text = json.dumps(context['recentQuestionLogs'], ensure_ascii=False)
        self.assertEqual(len(context['verifiedMemories']), 2)
        self.assertIn('튜브가 아니라 팁', memory_text)
        self.assertIn('제품 마스터와 검수 기억', memory_text)
        self.assertNotIn('다른 부서 기억', memory_text)
        self.assertNotIn('동료 기억', memory_text)
        self.assertEqual(len(context['recentQuestionLogs']), 1)
        self.assertIn('이전 질문', log_text)
        self.assertIn('샘플 확인', log_text)
        self.assertNotIn('동료 이전 질문', log_text)

    def test_ai_workspace_question_context_includes_only_own_question_feedback(self):
        from reporting.models import AIWorkspaceQuestionFeedback
        from reporting.views import _ai_workspace_department_question_context

        _followup, department = self._create_customer(self.user, '질문피드백문맥')
        _other_followup, other_department = self._create_customer(self.user, '질문피드백다른부서')
        AIWorkspaceQuestionFeedback.objects.create(
            user=self.user,
            department=department,
            scope_type='department',
            question='이다민 재견적 질문',
            answer_snapshot={'summary': '조건 확인처럼 짧게 묻기'},
            source='fallback',
            rating='needs_style',
            comment='고객 관점 추정과 추천 선택을 먼저 보여줘.',
        )
        AIWorkspaceQuestionFeedback.objects.create(
            user=self.coworker,
            department=department,
            scope_type='department',
            question='동료 질문',
            answer_snapshot={'summary': '동료 답변'},
            source='fallback',
            rating='incorrect',
            comment='동료 코멘트는 섞이면 안 됩니다.',
        )
        AIWorkspaceQuestionFeedback.objects.create(
            user=self.user,
            department=other_department,
            scope_type='department',
            question='다른 부서 질문',
            answer_snapshot={'summary': '다른 부서 답변'},
            source='fallback',
            rating='incorrect',
            comment='다른 부서 코멘트도 제외합니다.',
        )
        AIWorkspaceQuestionFeedback.objects.create(
            user=self.user,
            department=None,
            scope_type='all',
            question='전체 답변 톤',
            answer_snapshot={'summary': '전체 범위 답변'},
            source='openai',
            rating='helpful',
            comment='',
        )

        context = _ai_workspace_department_question_context(department, self.user)

        feedback_text = json.dumps(context['questionFeedbacks'], ensure_ascii=False)
        self.assertEqual(len(context['questionFeedbacks']), 2)
        self.assertIn('고객 관점 추정', feedback_text)
        self.assertIn('전체 범위 답변', feedback_text)
        self.assertNotIn('동료 코멘트', feedback_text)
        self.assertNotIn('다른 부서 코멘트', feedback_text)
        self.assertNotIn('answerDirection', context)

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

    def test_ai_workspace_summary_api_builds_daily_action_queue_from_sales_signals(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import DeliveryItem, History, Quote, Schedule

        followup, department = self._create_customer(self.user, '액션큐')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        in_report_week = week_start + timedelta(days=1)
        week_end = week_start + timedelta(days=4)

        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=in_report_week,
            visit_time=time(9, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('2000000'),
        )
        Quote.objects.create(
            quote_number='AI-ACTION-Q-001',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=week_end,
            stage='sent',
            subtotal=Decimal('2000000'),
            probability=75,
        )
        History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='구매 일정 확인 필요',
            next_action='결재 담당자와 구매 일정을 확인',
            next_action_date=today - timedelta(days=1),
        )
        delivery_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=week_end,
            visit_time=time(13, 0),
            status='scheduled',
            activity_type='delivery',
            expected_revenue=Decimal('550000'),
            notes='납품 서류 확인 필요',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='AI 납품 품목',
            quantity=2,
            unit_price=Decimal('250000'),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        kinds = {item['kind'] for item in payload['actionQueue']}
        self.assertIn('quote_followup', kinds)
        self.assertIn('customer_followup', kinds)
        self.assertIn('delivery_risk', kinds)
        self.assertIn('painpoint_validation', kinds)
        self.assertIn('weekly_report', kinds)
        self.assertGreaterEqual(payload['dailyBrief']['counts']['totalActions'], 5)
        quote_actions = [item for item in payload['actionQueue'] if item['kind'] == 'quote_followup']
        self.assertTrue(any(item['moneyImpact'] and item['moneyImpact'] > 0 for item in quote_actions))
        self.assertTrue(all(item['evidence'] for item in payload['actionQueue']))
        self.assertTrue(any('email' in item['draftTypes'] for item in payload['actionQueue']))

    def test_ai_workspace_action_queue_includes_asset_service_and_calibration_signals(self):
        followup, department = self._create_customer(self.user, '장비액션')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        asset = CustomerAsset.objects.create(
            company=followup.company,
            department=department,
            primary_followup=followup,
            asset_name='Pipette Service Set',
            model_name='PIP-1000',
            serial_number='SN-AI-1000',
            status='active',
            created_by=self.user,
        )
        service_case = ServiceCase.objects.create(
            asset=asset,
            followup=followup,
            case_type='repair',
            status='waiting',
            priority='urgent',
            received_date=today - timedelta(days=2),
            due_date=today - timedelta(days=1),
            symptom='피펫 누액 확인 필요',
            created_by=self.user,
            assigned_to=self.user,
        )
        calibration = CalibrationRecord.objects.create(
            asset=asset,
            followup=followup,
            calibration_date=today - timedelta(days=360),
            next_due_date=today + timedelta(days=7),
            result='pass',
            notes='정기 교정 예정',
            created_by=self.user,
            performed_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        action_ids = {item['id'] for item in payload['actionQueue']}
        self.assertIn(f'service_case:{service_case.id}', action_ids)
        self.assertIn(f'calibration_due:{calibration.id}', action_ids)
        self.assertEqual(payload['dailyBrief']['counts']['serviceCases'], 1)
        self.assertEqual(payload['dailyBrief']['counts']['calibrationDue'], 1)
        service_action = next(item for item in payload['actionQueue'] if item['id'] == f'service_case:{service_case.id}')
        calibration_action = next(item for item in payload['actionQueue'] if item['id'] == f'calibration_due:{calibration.id}')
        self.assertEqual(service_action['kindLabel'], '서비스 후속')
        self.assertEqual(calibration_action['kindLabel'], '교정 예정')
        self.assertIn('/assets/', service_action['hrefs']['assets'])
        self.assertTrue(any(item['label'] == '장비' for item in service_action['evidence']))

    def test_ai_workspace_asset_actions_respect_department_scope(self):
        selected_followup, selected_department = self._create_customer(self.user, '선택장비')
        other_followup, other_department = self._create_customer(self.user, '다른장비')
        today = timezone.localdate()
        selected_asset = CustomerAsset.objects.create(
            company=selected_followup.company,
            department=selected_department,
            primary_followup=selected_followup,
            asset_name='선택 부서 장비',
            status='active',
            created_by=self.user,
        )
        other_asset = CustomerAsset.objects.create(
            company=other_followup.company,
            department=other_department,
            primary_followup=other_followup,
            asset_name='다른 부서 장비',
            status='active',
            created_by=self.user,
        )
        selected_case = ServiceCase.objects.create(
            asset=selected_asset,
            followup=selected_followup,
            status='received',
            priority='high',
            received_date=today,
            due_date=today,
            symptom='선택 부서 서비스',
            created_by=self.user,
            assigned_to=self.user,
        )
        other_case = ServiceCase.objects.create(
            asset=other_asset,
            followup=other_followup,
            status='received',
            priority='high',
            received_date=today,
            due_date=today,
            symptom='다른 부서 서비스',
            created_by=self.user,
            assigned_to=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': selected_department.id})

        self.assertEqual(response.status_code, 200)
        action_ids = {item['id'] for item in response.json()['actionQueue']}
        self.assertIn(f'service_case:{selected_case.id}', action_ids)
        self.assertNotIn(f'service_case:{other_case.id}', action_ids)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_draft_api_supports_asset_actions(self, _mock_client):
        followup, department = self._create_customer(self.user, '장비초안')
        today = timezone.localdate()
        asset = CustomerAsset.objects.create(
            company=followup.company,
            department=department,
            primary_followup=followup,
            asset_name='초안 장비',
            serial_number='DRAFT-ASSET-1',
            status='active',
            created_by=self.user,
        )
        service_case = ServiceCase.objects.create(
            asset=asset,
            followup=followup,
            case_type='service',
            status='in_progress',
            priority='normal',
            received_date=today,
            due_date=today + timedelta(days=1),
            symptom='초안 생성용 서비스 케이스',
            created_by=self.user,
            assigned_to=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_draft_api'),
            data=json.dumps({'actionId': f'service_case:{service_case.id}', 'draftType': 'email'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['action']['kind'], 'service_case')
        self.assertEqual(payload['draftType'], 'email')
        self.assertIn('초안 장비', json.dumps(payload['evidence'], ensure_ascii=False))

    def test_ai_workspace_action_queue_excludes_completed_sold_quotes(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import Quote, Schedule

        followup, department = self._create_customer(self.user, '완료판매')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()

        completed_quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today - timedelta(days=3),
            visit_time=time(10, 0),
            status='completed',
            activity_type='quote',
            expected_revenue=Decimal('1500000'),
        )
        Quote.objects.create(
            quote_number='AI-SOLD-Q-001',
            schedule=completed_quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=14),
            stage='sent',
            subtotal=Decimal('1500000'),
            probability=80,
        )
        completed_quote_without_quote = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today - timedelta(days=2),
            visit_time=time(11, 0),
            status='completed',
            activity_type='quote',
            expected_revenue=Decimal('900000'),
            notes='판매 완료된 견적 일정',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        action_ids = {item['id'] for item in payload['actionQueue']}
        self.assertNotIn(f'quote:{completed_quote_schedule.quotes.first().id}', action_ids)
        self.assertNotIn(f'quote_schedule:{completed_quote_without_quote.id}', action_ids)
        prompt_text = '\n'.join(item['prompt'] for item in payload['promptTargets'])
        self.assertNotIn('AI-SOLD-Q-001', prompt_text)
        self.assertNotIn('판매 완료된 견적 일정', prompt_text)

    def test_ai_workspace_action_queue_excludes_stale_quote_submission_history(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import History

        followup, department = self._create_customer(self.user, '견적제출완료')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        stale_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='견적 제출 준비',
            next_action='견적서 및 비교표 제출',
            next_action_date=today - timedelta(days=1),
        )
        active_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='견적 제출 후 고객 확인 필요',
            next_action='견적 검토 여부 확인',
            next_action_date=today - timedelta(days=1),
        )
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('900000'),
        )
        DocumentGenerationLog.objects.create(
            company=self.company,
            document_type='quotation',
            schedule=quote_schedule,
            user=self.user,
            transaction_number='AI-ST-Q-001',
            output_format='pdf',
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        action_ids = {item['id'] for item in payload['actionQueue']}
        self.assertNotIn(f'followup:{stale_history.id}', action_ids)
        self.assertIn(f'followup:{active_history.id}', action_ids)

    def test_ai_workspace_action_draft_api_requires_ai_permission(self):
        self.client.force_login(self.no_ai_user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_draft_api'),
            data=json.dumps({'actionId': 'painpoint:1', 'draftType': 'questions'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    def test_ai_workspace_action_feedback_api_requires_ai_permission(self):
        self.client.force_login(self.no_ai_user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': 'painpoint:1', 'feedback': '고객이 아직 안산대요'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'permission_denied')

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_draft_api_returns_fallback_without_saving(self, _mock_client):
        from reporting.models import History, WeeklyReport

        followup, department = self._create_customer(self.user, '초안고객')
        analysis = self._create_department_analysis(self.user, department)
        card = analysis.painpoint_cards.first()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_draft_api'),
            data=json.dumps({'actionId': f'painpoint:{card.id}', 'draftType': 'questions'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['requiresHumanApproval'])
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['draftType'], 'questions')
        self.assertTrue(payload['draft']['bullets'])
        self.assertEqual(History.objects.filter(user=self.user).count(), 0)
        self.assertEqual(WeeklyReport.objects.filter(user=self.user).count(), 0)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_records_answer_and_hides_resolved_action(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import AIWorkspaceActionFeedback, History, Quote, Schedule

        followup, department = self._create_customer(self.user, '답변고객')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1300000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-001',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=7),
            stage='sent',
            subtotal=Decimal('1300000'),
            probability=70,
        )
        open_followup_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='견적 후속 확인 예정',
            next_action='견적 검토 여부 확인',
            next_action_date=today - timedelta(days=1),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'quote:{quote.id}', 'feedback': '아 이거 고객이 아직 안산대요'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['hidden'])
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['feedback']['status'], 'resolved')
        self.assertEqual(payload['feedback']['intent'], 'resolved_no_purchase')
        self.assertTrue(payload['crmSync']['applied'])
        self.assertTrue(any(change['label'] == '열린 후속조치 종료' for change in payload['crmSync']['changes']))

        feedback = AIWorkspaceActionFeedback.objects.get(user=self.user, action_id=f'quote:{quote.id}')
        self.assertEqual(feedback.status, 'resolved')
        self.assertEqual(feedback.followup, followup)
        self.assertIsNotNone(feedback.history_id)
        self.assertTrue(
            History.objects.filter(
                id=feedback.history_id,
                user=self.user,
                followup=followup,
                action_type='memo',
                content__contains='아 이거 고객이 아직 안산대요',
            ).exists()
        )
        open_followup_history.refresh_from_db()
        self.assertIsNotNone(open_followup_history.reviewed_at)
        quote.refresh_from_db()
        quote_schedule.refresh_from_db()
        followup.refresh_from_db()
        self.assertEqual(quote.stage, 'rejected')
        self.assertEqual(quote_schedule.status, 'cancelled')
        self.assertEqual(followup.status, 'paused')
        self.assertEqual(followup.pipeline_stage, 'lost')

        summary_response = self.client.get(self.url)
        self.assertEqual(summary_response.status_code, 200)
        action_ids = {item['id'] for item in summary_response.json()['actionQueue']}
        self.assertNotIn(f'quote:{quote.id}', action_ids)

    def test_backfill_ai_feedback_crm_sync_resolved_legacy_updates_customer_priority(self):
        from datetime import time, timedelta
        from decimal import Decimal
        from io import StringIO

        from django.core.management import call_command
        from reporting.models import AIWorkspaceActionFeedback, History, Schedule

        followup, department = self._create_customer(self.user, '레거시종료')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(10, 30),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1500000'),
        )
        open_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            schedule=quote_schedule,
            action_type='customer_meeting',
            content='견적 제출 후 확인 예정',
            next_action='견적서 및 비교표 제출',
            next_action_date=today - timedelta(days=1),
        )
        feedback = AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            action_id=f'quote_schedule:{quote_schedule.id}',
            action_kind='quote_followup',
            status='resolved',
            feedback='고객이 아직 안사겠다고 하고 견적은 참고만 한다고 함',
            ai_result={
                'decision': 'hide',
                'summary': '고객이 현재 구매하지 않겠다고 답했습니다.',
                'nextAction': '추천 목록에서 종료합니다.',
                'reason': '구매 의사가 없습니다.',
                'source': 'openai',
            },
            action_snapshot={
                'id': f'quote_schedule:{quote_schedule.id}',
                'kind': 'quote_followup',
                'title': '레거시종료 견적 일정 후속',
                'followupId': followup.id,
            },
        )

        dry_run_out = StringIO()
        call_command(
            'backfill_ai_feedback_crm_sync',
            '--feedback-id',
            str(feedback.id),
            '--json',
            stdout=dry_run_out,
        )
        open_history.refresh_from_db()
        quote_schedule.refresh_from_db()
        followup.refresh_from_db()
        self.assertIsNone(open_history.reviewed_at)
        self.assertEqual(quote_schedule.status, 'scheduled')
        self.assertEqual(followup.priority, 'urgent')

        apply_out = StringIO()
        call_command(
            'backfill_ai_feedback_crm_sync',
            '--feedback-id',
            str(feedback.id),
            '--apply',
            stdout=apply_out,
        )

        open_history.refresh_from_db()
        quote_schedule.refresh_from_db()
        followup.refresh_from_db()
        feedback.refresh_from_db()
        self.assertIsNotNone(open_history.reviewed_at)
        self.assertEqual(quote_schedule.status, 'cancelled')
        self.assertEqual(followup.status, 'paused')
        self.assertEqual(followup.priority, 'long_term')
        self.assertEqual(followup.pipeline_stage, 'lost')
        self.assertEqual(feedback.ai_result['intent'], 'resolved_no_purchase')
        self.assertTrue(feedback.ai_result['crmSync']['applied'])
        self.assertTrue(any(
            change['label'] == '우선순위 장기 전환'
            for change in feedback.ai_result['crmSync']['changes']
        ))

    def test_backfill_ai_feedback_crm_sync_positive_legacy_uses_explicit_followup_priority(self):
        from datetime import timedelta
        from io import StringIO

        from django.core.management import call_command
        from reporting.models import AIWorkspaceActionFeedback, History

        followup, department = self._create_customer(self.user, '레거시긍정')
        followup.priority = 'scheduled'
        followup.pipeline_stage = 'quote'
        followup.save(update_fields=['priority', 'pipeline_stage', 'updated_at'])
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='견적 검토 중',
            next_action='검토 여부 확인',
            next_action_date=today + timedelta(days=1),
        )
        feedback = AIWorkspaceActionFeedback.objects.create(
            user=self.user,
            followup=followup,
            action_id=f'followup:{history.id}',
            action_kind='overdue_followup',
            status='next_action',
            feedback='고객이 관심 있다고 하고 다음주에 다시 연락달래요',
            ai_result={
                'decision': 'next_action',
                'summary': '고객이 긍정적인 관심을 보였습니다.',
                'nextAction': '다음주 재연락',
                'reason': '구매 관심 표현이 있습니다.',
                'source': 'openai',
            },
            action_snapshot={
                'id': f'followup:{history.id}',
                'kind': 'overdue_followup',
                'title': '레거시긍정 후속 확인',
                'followupId': followup.id,
            },
        )

        call_command(
            'backfill_ai_feedback_crm_sync',
            '--feedback-id',
            str(feedback.id),
            '--apply',
            stdout=StringIO(),
        )

        history.refresh_from_db()
        followup.refresh_from_db()
        feedback.refresh_from_db()
        self.assertEqual(feedback.ai_result['intent'], 'positive_buying_signal')
        self.assertEqual(feedback.ai_result['crmSync']['taskHistoryId'], history.id)
        self.assertIn('다음주 재연락', history.next_action)
        self.assertEqual(followup.priority, 'followup')
        self.assertEqual(feedback.ai_result['prioritySignal']['priority'], 'followup')
        self.assertEqual(followup.pipeline_stage, 'negotiation')

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_keeps_next_action_feedback_visible(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import AIWorkspaceActionFeedback, History, Quote, Schedule

        followup, department = self._create_customer(self.user, '자료요청')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(11, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('2300000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-002',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=5),
            stage='sent',
            subtotal=Decimal('2300000'),
            probability=80,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'quote:{quote.id}', 'feedback': '고객이 추가 자료를 메일로 보내달래요'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['hidden'])
        self.assertEqual(payload['feedback']['status'], 'next_action')
        self.assertEqual(payload['feedback']['intent'], 'follow_up_needed')
        self.assertTrue(payload['crmSync']['applied'])
        self.assertIsNotNone(payload['crmSync']['taskHistoryId'])

        feedback = AIWorkspaceActionFeedback.objects.get(user=self.user, action_id=f'quote:{quote.id}')
        self.assertEqual(feedback.status, 'next_action')
        self.assertTrue(
            History.objects.filter(
                id=payload['crmSync']['taskHistoryId'],
                next_action__contains='요청 자료',
            ).exists()
        )
        self.assertTrue(
            History.objects.filter(
                id=feedback.history_id,
                content__contains='CRM 반영',
                next_action='',
            ).exists()
        )

        summary_response = self.client.get(self.url)
        self.assertEqual(summary_response.status_code, 200)
        action_payload = next(
            item for item in summary_response.json()['actionQueue']
            if item['id'] == f'quote:{quote.id}'
        )
        self.assertEqual(action_payload['feedback']['status'], 'next_action')
        self.assertIn('추가 자료', action_payload['feedback']['feedback'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_applies_explicit_urgent_priority_systemwide(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import AIWorkspaceActionFeedback, Quote, Schedule

        followup, department = self._create_customer(self.user, '긴급보고')
        followup.priority = 'scheduled'
        followup.customer_grade = 'C'
        followup.ai_score = 30
        followup.pipeline_stage = 'quote'
        followup.save(update_fields=['priority', 'customer_grade', 'ai_score', 'pipeline_stage', 'updated_at'])
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(13, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1800000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-URGENT',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=5),
            stage='sent',
            subtotal=Decimal('1800000'),
            probability=70,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'quote:{quote.id}',
                'feedback': '고객이 자료를 요청했고 오늘 중 바로 처리해야 하는 긴급 건입니다',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'follow_up_needed')
        self.assertEqual(payload['feedback']['prioritySignal']['priority'], 'urgent')
        self.assertTrue(any(
            change['label'] == 'AI 보고 우선순위 긴급 반영'
            for change in payload['crmSync']['changes']
        ))

        followup.refresh_from_db()
        self.assertEqual(followup.priority, 'urgent')
        feedback = AIWorkspaceActionFeedback.objects.get(user=self.user, action_id=f'quote:{quote.id}')
        self.assertEqual(feedback.ai_result['prioritySignal']['priority'], 'urgent')

        dashboard_response = self.client.get(reverse('reporting:dashboard_summary_api'))
        self.assertEqual(dashboard_response.status_code, 200)
        priority_customers = dashboard_response.json()['priorityCustomers']
        dashboard_customer = next(item for item in priority_customers if item['id'] == followup.id)
        self.assertEqual(dashboard_customer['priority'], 'urgent')
        self.assertEqual(dashboard_customer['priorityLabel'], '긴급')

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_downgrades_long_term_priority_systemwide(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import Quote, Schedule

        followup, department = self._create_customer(self.user, '장기보고')
        followup.priority = 'urgent'
        followup.customer_grade = 'C'
        followup.ai_score = 25
        followup.pipeline_stage = 'quote'
        followup.save(update_fields=['priority', 'customer_grade', 'ai_score', 'pipeline_stage', 'updated_at'])
        other_priority_customer, _other_department = self._create_customer(self.user, '다른긴급')
        other_priority_customer.customer_grade = 'C'
        other_priority_customer.save(update_fields=['customer_grade', 'updated_at'])
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(14, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('1600000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-LONG',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=10),
            stage='sent',
            subtotal=Decimal('1600000'),
            probability=60,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'quote:{quote.id}',
                'feedback': '고객이 나중에 다음달쯤 다시 보자고 했고 급하지 않음. 장기 보류로 두세요',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'follow_up_needed')
        self.assertEqual(payload['feedback']['prioritySignal']['priority'], 'long_term')
        self.assertTrue(any(
            change['label'] == 'AI 보고 우선순위 장기 반영'
            for change in payload['crmSync']['changes']
        ))

        followup.refresh_from_db()
        self.assertEqual(followup.priority, 'long_term')

        dashboard_response = self.client.get(reverse('reporting:dashboard_summary_api'))
        self.assertEqual(dashboard_response.status_code, 200)
        priority_ids = {item['id'] for item in dashboard_response.json()['priorityCustomers']}
        self.assertIn(other_priority_customer.id, priority_ids)
        self.assertNotIn(followup.id, priority_ids)

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_updates_existing_followup_history_for_positive_signal(self, _mock_client):
        from reporting.models import AIWorkspaceActionFeedback, History

        followup, department = self._create_customer(self.user, '긍정후속')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            action_type='customer_meeting',
            content='초기 후속',
            next_action='견적 검토 여부 확인',
            next_action_date=today,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'followup:{history.id}', 'feedback': '관심 있다고 하고 다음주에 다시 연락달래요'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'positive_buying_signal')
        self.assertEqual(payload['crmSync']['taskHistoryId'], history.id)
        history.refresh_from_db()
        self.assertIsNone(history.reviewed_at)
        self.assertIn('구매 절차', history.next_action)
        self.assertIsNotNone(history.next_action_date)
        followup.refresh_from_db()
        self.assertEqual(followup.priority, 'followup')
        self.assertEqual(followup.pipeline_stage, 'negotiation')
        feedback = AIWorkspaceActionFeedback.objects.get(user=self.user, action_id=f'followup:{history.id}')
        self.assertEqual(feedback.history.action_type, 'memo')
        self.assertEqual(feedback.ai_result['prioritySignal']['priority'], 'followup')
        self.assertIn('기존 후속조치 갱신', feedback.ai_result['crmSync']['changes'][0]['label'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_creates_email_waiting_followup(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import History, Quote, Schedule

        followup, department = self._create_customer(self.user, '메일대기')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(15, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('900000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-EMAIL',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=4),
            stage='sent',
            subtotal=Decimal('900000'),
            probability=65,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'quote:{quote.id}', 'feedback': '메일 보냈는데 아직 답장이 안왔어요'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'email_waiting')
        self.assertEqual(payload['feedback']['status'], 'next_action')
        task_id = payload['crmSync']['taskHistoryId']
        self.assertIsNotNone(task_id)
        task = History.objects.get(id=task_id)
        self.assertEqual(task.followup, followup)
        self.assertIn('메일 회신', task.next_action)
        self.assertIsNotNone(task.next_action_date)

    def test_ai_workspace_action_queue_includes_sent_email_without_received_reply(self):
        from datetime import timedelta
        from reporting.models import EmailLog

        followup, department = self._create_customer(self.user, '메일액션')
        replied_followup, replied_department = self._create_customer(self.user, '메일액션회신')
        self._create_department_analysis(self.user, department)
        self._create_department_analysis(self.user, replied_department)
        sent_at = timezone.now() - timedelta(days=3)
        waiting_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='customer@example.com',
            recipient_email='customer@example.com',
            subject='견적 확인 요청',
            body='견적 확인 부탁드립니다.',
            followup=followup,
            gmail_message_id='gmail-msg-waiting',
            gmail_thread_id='gmail-thread-waiting',
            sent_at=sent_at,
        )
        EmailLog.objects.create(
            user=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='other@example.com',
            recipient_email='other@example.com',
            subject='회신 있는 메일',
            body='회신 있는 메일',
            followup=replied_followup,
            gmail_message_id='gmail-msg-replied',
            gmail_thread_id='gmail-thread-replied',
            sent_at=sent_at,
        )
        EmailLog.objects.create(
            user=self.user,
            provider='gmail',
            email_type='received',
            is_sent=False,
            status='received',
            from_email='other@example.com',
            to_email='sales@example.com',
            subject='Re: 회신 있는 메일',
            body='확인했습니다.',
            followup=replied_followup,
            gmail_message_id='gmail-msg-reply',
            gmail_thread_id='gmail-thread-replied',
            received_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        action_ids = {item['id'] for item in payload['actionQueue']}
        self.assertIn(f'email_waiting:{waiting_email.id}', action_ids)
        self.assertTrue(any(item['kind'] == 'email_waiting' for item in payload['actionQueue']))
        self.assertEqual(payload['dailyBrief']['counts']['emailWaiting'], 1)

    def test_ai_workspace_action_queue_skips_email_waiting_when_same_followup_received_after_sent(self):
        from datetime import timedelta
        from reporting.models import EmailLog

        followup, department = self._create_customer(self.user, '김명환')
        self._create_department_analysis(self.user, department)
        sent_at = timezone.now() - timedelta(days=3)
        sent_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            sender_email='sales@example.com',
            to_email='myeonghwan@example.com',
            recipient_email='myeonghwan@example.com',
            subject='견적 확인 요청',
            body='견적 확인 부탁드립니다.',
            followup=followup,
            gmail_message_id='gmail-msg-kmh-sent',
            gmail_thread_id='gmail-thread-kmh-sent',
            sent_at=sent_at,
        )
        EmailLog.objects.create(
            user=self.user,
            provider='gmail',
            email_type='received',
            is_sent=False,
            status='received',
            from_email='',
            sender_email='',
            to_email='',
            recipient_email='',
            subject='별도 제목으로 온 답장',
            body='확인했습니다. 진행 가능 여부 검토 후 말씀드리겠습니다.',
            followup=followup,
            gmail_message_id='gmail-msg-kmh-received-different-thread',
            gmail_thread_id='gmail-thread-kmh-received-different-thread',
            received_at=timezone.now() - timedelta(days=1),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        action_ids = {item['id'] for item in payload['actionQueue']}
        self.assertNotIn(f'email_waiting:{sent_email.id}', action_ids)
        self.assertFalse(any(
            item['kind'] == 'email_waiting' and item['followupId'] == followup.id
            for item in payload['actionQueue']
        ))

    def test_ai_workspace_action_queue_dedupes_email_waiting_by_thread_or_subject(self):
        from datetime import timedelta
        from reporting.models import EmailLog

        followup, department = self._create_customer(self.user, '김미선')
        self._create_department_analysis(self.user, department)
        sent_at = timezone.now() - timedelta(days=3)
        original_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='misen@example.com',
            recipient_email='misen@example.com',
            subject='[하나과학] 수리 견적 및 보상판매 견적 안내',
            body='수리 견적 및 보상판매 견적 안내',
            followup=followup,
            gmail_message_id='gmail-msg-kim-original',
            gmail_thread_id='gmail-thread-kim-quote-original',
            sent_at=sent_at,
        )
        reply_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='misen@example.com',
            recipient_email='misen@example.com',
            subject='Re: [RE][하나과학] 수리 견적 및 보상판매 견적 안내',
            body='수리 견적 및 보상판매 견적 안내 재발송',
            followup=followup,
            gmail_message_id='gmail-msg-kim-reply-1',
            gmail_thread_id='gmail-thread-kim-quote-reply-1',
            sent_at=sent_at + timedelta(minutes=5),
        )
        latest_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='misen@example.com',
            recipient_email='misen@example.com',
            subject='Re: [RE][하나과학] 수리 견적 및 보상판매 견적 안내',
            body='수리 견적 및 보상판매 견적 안내 최종 발송',
            followup=followup,
            gmail_message_id='gmail-msg-kim-reply-2',
            gmail_thread_id='gmail-thread-kim-quote-reply-2',
            sent_at=sent_at + timedelta(minutes=10),
        )
        other_thread_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='misen@example.com',
            recipient_email='misen@example.com',
            subject='별도 납품 일정 확인',
            body='별도 납품 일정 확인',
            followup=followup,
            gmail_message_id='gmail-msg-kim-other',
            gmail_thread_id='gmail-thread-kim-delivery',
            sent_at=sent_at + timedelta(minutes=20),
        )
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'department_id': department.id})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        email_actions = [
            item for item in payload['actionQueue']
            if item['kind'] == 'email_waiting' and item['followupId'] == followup.id
        ]
        action_ids = {item['id'] for item in email_actions}
        self.assertIn(f'email_waiting:{latest_email.id}', action_ids)
        self.assertIn(f'email_waiting:{other_thread_email.id}', action_ids)
        self.assertNotIn(f'email_waiting:{original_email.id}', action_ids)
        self.assertNotIn(f'email_waiting:{reply_email.id}', action_ids)
        self.assertEqual(
            len([item for item in email_actions if item['evidence'][1]['value'].endswith('보상판매 견적 안내')]),
            1,
        )

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_draft_api_accepts_scoped_quote_missing_from_global_queue(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import Quote, Schedule

        selected_followup, selected_department = self._create_customer(self.user, '스코프견적초안')
        other_followup, other_department = self._create_customer(self.user, '전역견적초안')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        today = timezone.localdate()
        selected_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=selected_followup,
            visit_date=today,
            visit_time=time(10, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('100000'),
        )
        selected_quote = Quote.objects.create(
            quote_number='AI-SCOPED-Q-DRAFT',
            schedule=selected_schedule,
            followup=selected_followup,
            user=self.user,
            valid_until=today + timedelta(days=30),
            stage='sent',
            subtotal=Decimal('100000'),
            probability=30,
        )
        for index in range(10):
            schedule = Schedule.objects.create(
                user=self.user,
                company=self.company,
                followup=other_followup,
                visit_date=today,
                visit_time=time(11, 0),
                status='scheduled',
                activity_type='quote',
                expected_revenue=Decimal('900000'),
            )
            Quote.objects.create(
                quote_number=f'AI-GLOBAL-Q-DRAFT-{index}',
                schedule=schedule,
                followup=other_followup,
                user=self.user,
                valid_until=today + timedelta(days=index + 1),
                stage='sent',
                subtotal=Decimal('900000'),
                probability=70,
            )
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})
        self.assertEqual(detail_response.status_code, 200)
        detail_action_ids = {item['id'] for item in detail_response.json()['actionQueue']}
        self.assertIn(f'quote:{selected_quote.id}', detail_action_ids)

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['id'] for item in general_response.json()['actionQueue']}
        self.assertNotIn(f'quote:{selected_quote.id}', general_action_ids)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_draft_api'),
            data=json.dumps({'actionId': f'quote:{selected_quote.id}', 'draftType': 'note'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertEqual(payload['action']['id'], f'quote:{selected_quote.id}')
        self.assertIn('스코프견적초안', payload['draft']['body'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_accepts_scoped_followup_missing_from_global_queue(self, _mock_client):
        from datetime import timedelta
        from reporting.models import History

        selected_followup, selected_department = self._create_customer(self.user, '스코프후속답변')
        other_followup, other_department = self._create_customer(self.user, '전역후속답변')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        today = timezone.localdate()
        selected_history = History.objects.create(
            user=self.user,
            company=self.company,
            followup=selected_followup,
            action_type='customer_meeting',
            content='스코프 후속',
            next_action='스코프 고객 견적 검토 확인',
            next_action_date=today + timedelta(days=3),
        )
        for index in range(10):
            History.objects.create(
                user=self.user,
                company=self.company,
                followup=other_followup,
                action_type='customer_meeting',
                content=f'전역 후속 {index}',
                next_action=f'전역 고객 후속 {index}',
                next_action_date=today,
            )
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})
        self.assertEqual(detail_response.status_code, 200)
        detail_action_ids = {item['id'] for item in detail_response.json()['actionQueue']}
        self.assertIn(f'followup:{selected_history.id}', detail_action_ids)

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['id'] for item in general_response.json()['actionQueue']}
        self.assertNotIn(f'followup:{selected_history.id}', general_action_ids)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'followup:{selected_history.id}',
                'feedback': '고객이 추가 자료를 메일로 보내달라고 했습니다',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['action']['id'], f'followup:{selected_history.id}')
        self.assertEqual(payload['feedback']['status'], 'next_action')
        self.assertNotEqual(payload['error'] if 'error' in payload else '', 'action_not_found')

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_accepts_scoped_painpoint_missing_from_global_queue(self, _mock_client):
        from ai_chat.models import PainPointCard
        from reporting.models import AIWorkspaceActionFeedback

        selected_followup, selected_department = self._create_customer(self.user, '미생물공생및면역')
        selected_analysis = self._create_department_analysis(self.user, selected_department)
        selected_card = selected_analysis.painpoint_cards.first()
        selected_card.category = 'compatibility'
        selected_card.hypothesis = '현재 사용 중인 튜브가 고속 원심분리 시 깨지거나 뚜껑이 열리는 문제가 있다.'
        selected_card.verification_question = 'Paradigm Tube의 사용감과 15000g에서도 안열리는지 확인했는가?'
        selected_card.confidence = 'med'
        selected_card.confidence_score = 60
        selected_card.save(update_fields=['category', 'hypothesis', 'verification_question', 'confidence', 'confidence_score'])
        for index in range(8):
            _other_followup, other_department = self._create_customer(self.user, f'전역PainPoint{index}')
            other_analysis = self._create_department_analysis(self.user, other_department)
            other_card = other_analysis.painpoint_cards.first()
            other_card.confidence_score = 90 - index
            other_card.save(update_fields=['confidence_score'])
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})
        self.assertEqual(detail_response.status_code, 200)
        detail_action_ids = {item['id'] for item in detail_response.json()['actionQueue']}
        self.assertIn(f'painpoint:{selected_card.id}', detail_action_ids)

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['id'] for item in general_response.json()['actionQueue']}
        self.assertNotIn(f'painpoint:{selected_card.id}', general_action_ids)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'painpoint:{selected_card.id}',
                'feedback': 'Paradigm Tube 샘플을 전달하고 15000g 원심분리 후 뚜껑 열림 여부를 확인하기로 했습니다.',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['action']['id'], f'painpoint:{selected_card.id}')
        self.assertNotEqual(payload['error'] if 'error' in payload else '', 'action_not_found')
        self.assertTrue(AIWorkspaceActionFeedback.objects.filter(
            user=self.user,
            action_id=f'painpoint:{selected_card.id}',
            followup=selected_followup,
        ).exists())
        self.assertTrue(PainPointCard.objects.filter(id=selected_card.id).exists())

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_accepts_scoped_email_missing_from_global_queue(self, _mock_client):
        from datetime import timedelta
        from reporting.models import EmailLog, History

        selected_followup, selected_department = self._create_customer(self.user, '문새롬메일')
        selected_followup.priority = 'scheduled'
        selected_followup.save(update_fields=['priority', 'updated_at'])
        other_followup, other_department = self._create_customer(self.user, '다른메일')
        self._create_department_analysis(self.user, selected_department)
        self._create_department_analysis(self.user, other_department)
        old_sent_at = timezone.now() - timedelta(days=120)
        waiting_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='saerom@example.com',
            recipient_email='saerom@example.com',
            subject='[하나과학] 보상판매 견적 및 제품 간단 안내 드립니다',
            body='보상판매 견적 안내',
            followup=selected_followup,
            gmail_message_id='gmail-msg-scoped-waiting',
            gmail_thread_id='gmail-thread-scoped-waiting',
            sent_at=old_sent_at,
        )
        for index in range(6):
            EmailLog.objects.create(
                user=self.user,
                sender=self.user,
                provider='gmail',
                email_type='sent',
                is_sent=True,
                status='sent',
                from_email='sales@example.com',
                to_email=f'other-{index}@example.com',
                recipient_email=f'other-{index}@example.com',
                subject=f'최근 미회신 메일 {index}',
                body='최근 미회신 메일',
                followup=other_followup,
                gmail_message_id=f'gmail-msg-global-waiting-{index}',
                gmail_thread_id=f'gmail-thread-global-waiting-{index}',
                sent_at=timezone.now() - timedelta(days=3, minutes=index),
            )
        self.client.force_login(self.user)

        detail_response = self.client.get(self.url, {'department_id': selected_department.id})
        self.assertEqual(detail_response.status_code, 200)
        detail_action_ids = {item['id'] for item in detail_response.json()['actionQueue']}
        self.assertIn(f'email_waiting:{waiting_email.id}', detail_action_ids)

        general_response = self.client.get(self.url)
        self.assertEqual(general_response.status_code, 200)
        general_action_ids = {item['id'] for item in general_response.json()['actionQueue']}
        self.assertNotIn(f'email_waiting:{waiting_email.id}', general_action_ids)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'email_waiting:{waiting_email.id}',
                'feedback': (
                    '보상판매 : 교수님께 허락을 못받았다고하여 이건 장기로 분류해야합니다. '
                    '현재는 팁에대한 불만이 있어서 그거 해결하는 것이 급선무 입니다.'
                ),
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'follow_up_needed')
        self.assertEqual(payload['feedback']['status'], 'next_action')
        self.assertEqual(payload['feedback']['prioritySignal']['priority'], 'urgent')
        self.assertIn('팁', payload['feedback']['nextAction'])
        self.assertIn('사용 제품 규격', payload['feedback']['nextAction'])
        self.assertIn('처리 예정 시간', payload['feedback']['nextAction'])
        self.assertIn('보상판매', payload['feedback']['nextAction'])
        selected_followup.refresh_from_db()
        self.assertEqual(selected_followup.priority, 'urgent')
        self.assertTrue(History.objects.filter(id=payload['crmSync']['taskHistoryId'], followup=selected_followup).exists())

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_splits_long_term_issue_followup_without_duplicates(self, _mock_client):
        from datetime import timedelta
        from reporting.models import AIWorkspaceActionFeedback, EmailLog, History

        followup, department = self._create_customer(self.user, '이슈분리')
        followup.priority = 'scheduled'
        followup.save(update_fields=['priority', 'updated_at'])
        self._create_department_analysis(self.user, department)
        waiting_email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='issue-split@example.com',
            recipient_email='issue-split@example.com',
            subject='[하나과학] 보상판매 견적 및 제품 안내',
            body='보상판매 견적 안내',
            followup=followup,
            gmail_message_id='gmail-msg-issue-split',
            gmail_thread_id='gmail-thread-issue-split',
            sent_at=timezone.now() - timedelta(days=3),
        )
        feedback_text = (
            '보상판매 : 교수님께 허락을 못받았다고하여 이건 장기로 분류해야합니다. '
            '현재는 팁에대한 불만이 있어서 그거 해결하는 것이 급선무 입니다.'
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'email_waiting:{waiting_email.id}', 'feedback': feedback_text}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['prioritySignal']['priority'], 'urgent')
        self.assertEqual(len(payload['feedback']['issueFollowups']), 2)
        self.assertEqual(len(payload['crmSync']['issueTaskHistories']), 1)
        self.assertTrue(any(
            change['label'] == '이슈별 장기 후속조치 생성'
            for change in payload['crmSync']['changes']
        ))

        main_task = History.objects.get(id=payload['crmSync']['taskHistoryId'])
        self.assertIn('팁 불만은 오늘', main_task.next_action)
        self.assertNotIn('보상판매 건은 장기 후속', main_task.next_action)
        long_term_task_info = payload['crmSync']['issueTaskHistories'][0]
        self.assertEqual(long_term_task_info['issue'], '보상판매')
        self.assertEqual(long_term_task_info['priority'], 'long_term')
        long_term_task = History.objects.get(id=long_term_task_info['historyId'])
        self.assertNotEqual(long_term_task.id, main_task.id)
        self.assertIn('보상판매 건은 장기 후속', long_term_task.next_action)
        self.assertGreaterEqual(long_term_task.next_action_date, timezone.localdate() + timedelta(days=30))

        feedback = AIWorkspaceActionFeedback.objects.get(user=self.user, action_id=f'email_waiting:{waiting_email.id}')
        self.assertEqual(feedback.ai_result['crmSync']['issueTaskHistories'][0]['historyId'], long_term_task.id)

        second_response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'email_waiting:{waiting_email.id}', 'feedback': feedback_text}),
            content_type='application/json',
        )

        self.assertEqual(second_response.status_code, 200)
        second_payload = second_response.json()
        self.assertEqual(second_payload['crmSync']['issueTaskHistories'][0]['historyId'], long_term_task.id)
        self.assertTrue(any(
            change['label'] == '이슈별 장기 후속조치 갱신'
            for change in second_payload['crmSync']['changes']
        ))
        self.assertEqual(
            History.objects.filter(followup=followup, next_action__icontains='팁 불만은 오늘').count(),
            1,
        )
        self.assertEqual(
            History.objects.filter(followup=followup, next_action__icontains='보상판매 건은 장기 후속').count(),
            1,
        )

    @patch('ai_chat.services.get_openai_client')
    def test_ai_workspace_action_feedback_api_specializes_generic_openai_issue_action(self, mock_client):
        from datetime import timedelta
        from types import SimpleNamespace
        from reporting.models import EmailLog

        class FakeCompletions:
            def create(self, *args, **kwargs):
                content = json.dumps({
                    'decision': 'next_action',
                    'recommendedStatus': 'next_action',
                    'intent': 'follow_up_needed',
                    'shouldHide': False,
                    'summary': '팁에 대한 불만이 있어 해결해야 합니다.',
                    'nextAction': '팁에 대한 불만 사항을 해결하기 위한 조치를 취하세요.',
                    'nextActionDate': None,
                    'reason': '고객 불만이 있습니다.',
                    'suggestedDraftType': 'note',
                    'prioritySignal': {'priority': 'long_term', 'reason': '보상판매는 장기입니다.'},
                })
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        mock_client.return_value = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
        followup, department = self._create_customer(self.user, '문새롬구체화')
        self._create_department_analysis(self.user, department)
        email = EmailLog.objects.create(
            user=self.user,
            sender=self.user,
            provider='gmail',
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='saerom@example.com',
            recipient_email='saerom@example.com',
            subject='[하나과학] 보상판매 견적 및 제품 간단 안내 드립니다',
            body='보상판매 견적 안내',
            followup=followup,
            gmail_message_id='gmail-msg-specific-openai',
            gmail_thread_id='gmail-thread-specific-openai',
            sent_at=timezone.now() - timedelta(days=3),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({
                'actionId': f'email_waiting:{email.id}',
                'feedback': (
                    '보상판매 : 교수님께 허락을 못받았다고하여 이건 장기로 분류해야합니다. '
                    '현재는 팁에대한 불만이 있어서 그거 해결하는 것이 급선무 입니다.'
                ),
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'openai')
        self.assertEqual(payload['feedback']['prioritySignal']['priority'], 'urgent')
        self.assertIn('팁', payload['feedback']['nextAction'])
        self.assertIn('사용 제품 규격', payload['feedback']['nextAction'])
        self.assertIn('처리 예정 시간', payload['feedback']['nextAction'])
        self.assertIn('보상판매', payload['feedback']['nextAction'])

    @patch('ai_chat.services.get_openai_client', side_effect=ValueError('OPENAI_API_KEY missing'))
    def test_ai_workspace_action_feedback_api_needs_review_does_not_change_crm_state(self, _mock_client):
        from datetime import time, timedelta
        from decimal import Decimal
        from reporting.models import Quote, Schedule

        followup, department = self._create_customer(self.user, '검토필요')
        self._create_department_analysis(self.user, department)
        today = timezone.localdate()
        quote_schedule = Schedule.objects.create(
            user=self.user,
            company=self.company,
            followup=followup,
            visit_date=today,
            visit_time=time(16, 0),
            status='scheduled',
            activity_type='quote',
            expected_revenue=Decimal('500000'),
        )
        quote = Quote.objects.create(
            quote_number='AI-FEEDBACK-Q-REVIEW',
            schedule=quote_schedule,
            followup=followup,
            user=self.user,
            valid_until=today + timedelta(days=6),
            stage='sent',
            subtotal=Decimal('500000'),
            probability=55,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('reporting:ai_workspace_action_feedback_api'),
            data=json.dumps({'actionId': f'quote:{quote.id}', 'feedback': '상황을 다시 확인해봐야 할 것 같습니다'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['feedback']['intent'], 'needs_human_review')
        self.assertFalse(payload['crmSync']['applied'])
        quote.refresh_from_db()
        quote_schedule.refresh_from_db()
        followup.refresh_from_db()
        self.assertEqual(quote.stage, 'sent')
        self.assertEqual(quote_schedule.status, 'scheduled')
        self.assertEqual(followup.status, 'active')


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

    def _create_delivery_schedule(self, followup, owner, name, unit_price, quantity=1, days_delta=-1):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Schedule

        schedule = Schedule.objects.create(
            user=owner,
            company=owner.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=days_delta),
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

    def test_pipeline_api_uses_latest_quote_schedule_date_amount(self):
        from datetime import time, timedelta
        from django.utils import timezone
        from reporting.models import Schedule

        followup = self._create_pipeline_customer(self.user, '날짜별견적', stage='quote')
        first_schedule = followup.schedules.first()
        self._create_delivery_item(first_schedule, '과거 견적품목', 1000000)
        second_schedule = Schedule.objects.create(
            user=self.user,
            company=self.user.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=2),
            visit_time=time(14, 0),
            status='scheduled',
            activity_type='quote',
        )
        self._create_delivery_item(second_schedule, '최신 견적품목', 2000000)
        same_day_schedule = Schedule.objects.create(
            user=self.user,
            company=self.user.userprofile.company,
            followup=followup,
            visit_date=timezone.localdate() + timedelta(days=2),
            visit_time=time(15, 0),
            status='scheduled',
            activity_type='quote',
        )
        self._create_delivery_item(same_day_schedule, '같은날 견적품목', 500000)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        deal = next(deal for deal in response.json()['deals'] if deal['id'] == followup.id)
        self.assertEqual(deal['value'], 2750000)
        self.assertEqual(deal['latestQuote']['source'], '견적 일정 2건')
        self.assertIn('외 1건', deal['latestQuote']['number'])
        self.assertEqual(deal['latestQuote']['basisDate'], (timezone.localdate() + timedelta(days=2)).isoformat())

    def test_pipeline_api_uses_latest_delivery_date_amount_for_won(self):
        from datetime import timedelta
        from django.utils import timezone

        followup = self._create_pipeline_customer(self.user, '날짜별수주', stage='won')
        self._create_delivery_schedule(followup, self.user, '과거납품', 1000000, days_delta=-20)
        self._create_delivery_schedule(followup, self.user, '최신납품', 2000000, days_delta=-1)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        deal = next(deal for deal in payload['deals'] if deal['id'] == followup.id)
        self.assertEqual(deal['value'], 2200000)
        self.assertEqual(deal['latestQuote']['source'], '실제 납품 매출')
        self.assertEqual(deal['latestQuote']['basisType'], 'delivery')
        self.assertEqual(deal['latestQuote']['basisDate'], (timezone.localdate() - timedelta(days=1)).isoformat())
        stages = {stage['id']: stage for stage in payload['stages']}
        self.assertEqual(stages['won']['totalValue'], 2200000)

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

    def test_create_api_preserves_blank_lines_between_schedule_blocks(self):
        import datetime
        from reporting.models import WeeklyReport

        activity_notes = (
            '- 05/11(월): 김태균 - 고객 미팅\n'
            '고객/부서: 국민대학교 · 식품기능성연구실\n\n'
            '- 05/15(금): 이다민 - 고객 미팅\n'
            '고객/부서: 서울대학교 · 미생물공생및면역연구실 · 박주홍\n\n'
            '- 05/15(금): 박준현 - 고객 미팅\n'
            '고객/부서: 서울대학교 · 면역제어시스템연구실 · 안광석'
        )

        self.client.force_login(self.salesman)
        response = self.client.post(
            reverse('reporting:weekly_report_create_api'),
            data=json.dumps({
                'weekStart': '2026-05-11',
                'weekEnd': '2026-05-15',
                'title': '일정 블록 빈 줄 테스트',
                'activityNotes': activity_notes,
                'quoteDeliveryNotes': '',
                'otherNotes': '',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        report = WeeklyReport.objects.get(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 11),
        )
        self.assertEqual(report.activity_notes.count('<p>'), 3)
        self.assertIn('</p><p>- 05/15(금): 이다민', report.activity_notes)

        response_report = response.json()['report']
        self.assertEqual(response_report['activityNotes'], activity_notes)
        self.assertEqual(response_report['activityNotesHtml'].count('<p>'), 3)
        self.assertIn('</p><p>- 05/15(금): 이다민', response_report['activityNotesHtml'])

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

    def test_detail_api_preserves_inline_br_html_for_display(self):
        import datetime
        from reporting.models import WeeklyReport

        report = WeeklyReport.objects.create(
            user=self.salesman,
            week_start=datetime.date(2026, 5, 4),
            week_end=datetime.date(2026, 5, 8),
            title='중간 br 줄바꿈 테스트',
            activity_notes='첫 줄<br>둘째 줄<br />셋째 줄',
            quote_delivery_notes='견적 A&lt;br&gt;납품 B',
        )

        self.client.force_login(self.salesman)
        response = self.client.get(reverse('reporting:weekly_report_detail_api', args=[report.id]))

        self.assertEqual(response.status_code, 200)
        data = response.json()['report']
        self.assertIn('첫 줄<br>둘째 줄<br>셋째 줄', data['activityNotesHtml'])
        self.assertNotIn('&lt;br', data['activityNotesHtml'])
        self.assertIn('견적 A<br>납품 B', data['quoteDeliveryNotesHtml'])
        self.assertEqual(data['activityNotes'], '첫 줄\n둘째 줄\n셋째 줄')
        self.assertEqual(data['quoteDeliveryNotes'], '견적 A\n납품 B')

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
        """Salesman: 일정 생성 폼 GET → React 생성 화면"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:schedule_create'))
        self.assertEqual(r.status_code, 302,
                         msg=f"Salesman GET schedule_create: expected 302, got {r.status_code}")
        self.assertEqual(r['Location'], frontend_url('schedules/?create=1'))

    def test_salesman_can_get_followup_create(self):
        """Salesman: 고객 생성 폼 GET → React 생성 화면"""
        self.client.force_login(self.salesman)
        r = self.client.get(reverse('reporting:followup_create'))
        self.assertEqual(r.status_code, 302,
                         msg=f"Salesman GET followup_create: expected 302, got {r.status_code}")
        self.assertEqual(r['Location'], frontend_url('customers/?create=1'))

    # ── 조회는 허용 ─────────────────────────────────────────────────────────

    def test_manager_can_view_history_list(self):
        """Manager: 히스토리 목록 조회 → React 영업노트"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:history_list'))
        self.assertEqual(r.status_code, 302,
                         msg=f"Manager GET history_list: expected 302, got {r.status_code}")
        self.assertEqual(r['Location'], frontend_url('notes/'))

    def test_manager_can_view_schedule_list(self):
        """Manager: 일정 목록 조회 → React 일정"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:schedule_list'))
        self.assertEqual(r.status_code, 302,
                         msg=f"Manager GET schedule_list: expected 302, got {r.status_code}")
        self.assertEqual(r['Location'], frontend_url('schedules/'))

    def test_manager_can_view_followup_list(self):
        """Manager: 고객 목록 조회 → React 고객"""
        self.client.force_login(self.manager)
        r = self.client.get(reverse('reporting:followup_list'))
        self.assertEqual(r.status_code, 302,
                         msg=f"Manager GET followup_list: expected 302, got {r.status_code}")
        self.assertEqual(r['Location'], frontend_url('customers/'))


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


class OperationsHealthTests(TestCase):
    """운영 health/readiness endpoint smoke tests."""

    def test_healthz_returns_public_liveness_without_data(self):
        response = self.client.get('/healthz/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['service'], 'sales-note-backend')
        self.assertNotIn('customers', payload)
        self.assertIn('no-store', response.headers.get('Cache-Control', ''))

    @override_settings(ALLOWED_HOSTS=['healthcheck.railway.app'])
    def test_healthz_accepts_railway_healthcheck_host(self):
        response = self.client.get('/healthz/', HTTP_HOST='healthcheck.railway.app')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_readyz_returns_database_and_migration_status(self):
        response = self.client.get('/readyz/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['checks']['database']['status'], 'ok')
        self.assertEqual(payload['checks']['migrations']['pending'], 0)

    def test_backup_status_does_not_require_email_host_setting(self):
        with patch.object(__import__('django.conf', fromlist=['settings']).settings, 'EMAIL_HOST', None, create=True):
            response = self.client.get('/reporting/backup/status/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])


class OperationsCommandTests(TestCase):
    """운영 자동화 management command smoke tests."""

    @override_settings(DEBUG=True)
    def test_audit_runtime_config_outputs_json_without_secret_values(self):
        from io import StringIO
        from django.conf import settings as django_settings
        from django.core.management import call_command

        output = StringIO()
        call_command('audit_runtime_config', '--json', stdout=output)

        payload = json.loads(output.getvalue())
        self.assertIn(payload['status'], ('ok', 'warning'))
        self.assertNotIn(getattr(django_settings, 'SECRET_KEY', ''), output.getvalue())

    def test_simple_backup_json_writes_retained_artifact(self):
        from tempfile import TemporaryDirectory
        from django.core.management import call_command

        with TemporaryDirectory() as temp_dir:
            call_command('simple_backup', '--format=json', f'--output-dir={temp_dir}', '--keep=1')
            files = os.listdir(temp_dir)

        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith('sales_note_backup_'))
        self.assertTrue(files[0].endswith('.json'))


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


class ProductManagementReactApiTests(TestCase):
    """React 제품관리 API 회귀 테스트"""

    def setUp(self):
        self.client = Client()
        self.company = UserCompany.objects.create(name='제품React회사')
        self.salesman = make_user('product-react-sales', role='salesman', company=self.company)
        self.manager = make_user('product-react-manager', role='manager', company=self.company)
        self.client.force_login(self.salesman)

    def test_product_bulk_upsert_updates_existing_ecount_overlap_and_disables_promo(self):
        import json
        from decimal import Decimal
        from reporting.models import Product

        existing = Product.objects.create(
            product_code='ECOUNT-001',
            description='기존 설명',
            specification='OLD',
            unit='EA',
            standard_price=Decimal('1000'),
            is_promo=True,
            promo_price=Decimal('800'),
            created_by=self.salesman,
        )
        no_description_row = Product.objects.create(
            product_code='ECOUNT-003',
            description='보존할 설명',
            specification='OLD-SPEC',
            unit='EA',
            standard_price=Decimal('3000'),
            created_by=self.salesman,
        )

        response = self.client.post(
            reverse('reporting:products_bulk_upsert_api'),
            data=json.dumps({
                'products': [
                    {
                        'productCode': 'ECOUNT-001',
                        'description': '새 설명',
                        'specification': 'NEW',
                        'unit': 'BOX',
                        'standardPrice': '1500',
                    },
                    {
                        'productCode': 'ECOUNT-002',
                        'description': '신규 설명',
                        'specification': 'SPEC',
                        'unit': 'SET',
                        'standardPrice': '2500',
                    },
                    {
                        'productCode': 'ECOUNT-003',
                        'specification': 'NEW-SPEC',
                        'unit': 'EA',
                        'standardPrice': '3300',
                    },
                ],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['createdCount'], 1)
        self.assertEqual(payload['updatedCount'], 2)
        existing.refresh_from_db()
        self.assertEqual(existing.description, '새 설명')
        self.assertEqual(existing.specification, 'NEW')
        self.assertEqual(existing.unit, 'BOX')
        self.assertEqual(existing.standard_price, Decimal('1500'))
        self.assertFalse(existing.is_promo)
        self.assertIsNone(existing.promo_price)
        no_description_row.refresh_from_db()
        self.assertEqual(no_description_row.description, '보존할 설명')
        self.assertEqual(no_description_row.specification, 'NEW-SPEC')
        self.assertEqual(no_description_row.standard_price, Decimal('3300'))
        created = Product.objects.get(product_code='ECOUNT-002')
        self.assertEqual(created.created_by, self.salesman)

    def test_product_current_price_ignores_legacy_promotion(self):
        from decimal import Decimal
        from reporting.models import Product

        product = Product.objects.create(
            product_code='PROMO-OFF-001',
            standard_price=Decimal('1000'),
            is_promo=True,
            promo_price=Decimal('700'),
            created_by=self.salesman,
        )

        response = self.client.get(reverse('reporting:product_api_list'), {'search': 'PROMO-OFF'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()['products'][0]
        self.assertEqual(payload['current_price'], 1000.0)
        self.assertFalse(payload['is_promo'])
        self.assertEqual(product.get_current_price(), Decimal('1000'))

    def test_product_api_list_supports_limit_and_specification_search(self):
        from reporting.models import Product

        for index in range(5):
            Product.objects.create(
                product_code=f'LIMIT-SEARCH-{index}',
                specification='공통규격',
                standard_price=1000 + index,
                created_by=self.salesman,
            )
        Product.objects.create(
            product_code='LIMIT-SPEC-ONLY',
            specification='특수규격',
            standard_price=2000,
            created_by=self.salesman,
        )

        response = self.client.get(reverse('reporting:product_api_list'), {'search': '특수규격', 'limit': '2'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['totalCount'], 1)
        self.assertFalse(payload['hasMore'])
        self.assertEqual(payload['products'][0]['product_code'], 'LIMIT-SPEC-ONLY')

        response = self.client.get(reverse('reporting:product_api_list'), {'search': 'LIMIT-SEARCH', 'limit': '2'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['count'], 2)
        self.assertEqual(payload['totalCount'], 5)
        self.assertTrue(payload['hasMore'])

    def test_product_management_manager_is_read_only_for_company_products(self):
        import json
        from reporting.models import Product

        product = Product.objects.create(
            product_code='MANAGER-READONLY-001',
            description='manager visible product',
            standard_price=1000,
            created_by=self.salesman,
        )
        other_company = UserCompany.objects.create(name='제품React타사회사')
        other_user = make_user('product-react-other-sales', role='salesman', company=other_company)
        Product.objects.create(
            product_code='MANAGER-READONLY-OTHER',
            standard_price=2000,
            created_by=other_user,
        )
        self.client.force_login(self.manager)

        response = self.client.get(reverse('reporting:products_management_api'), {'q': 'MANAGER-READONLY'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['scope']['canManage'])
        self.assertEqual(payload['links']['save'], '')
        self.assertEqual(payload['links']['bulkUpsert'], '')
        self.assertEqual(payload['links']['bulkDelete'], '')
        product_codes = {item['productCode'] for item in payload['products']}
        self.assertIn(product.product_code, product_codes)
        self.assertNotIn('MANAGER-READONLY-OTHER', product_codes)
        visible = next(item for item in payload['products'] if item['productCode'] == product.product_code)
        self.assertEqual(visible['createdBy'], self.salesman.username)

        save_response = self.client.post(
            reverse('reporting:product_save_api'),
            data=json.dumps({
                'productCode': 'MANAGER-READONLY-NEW',
                'standardPrice': '3000',
            }),
            content_type='application/json',
        )
        self.assertEqual(save_response.status_code, 403)

        edit_response = self.client.post(
            reverse('reporting:product_update_api', args=[product.id]),
            data=json.dumps({
                'productCode': product.product_code,
                'standardPrice': '9999',
            }),
            content_type='application/json',
        )
        self.assertEqual(edit_response.status_code, 403)

        bulk_response = self.client.post(
            reverse('reporting:products_bulk_upsert_api'),
            data=json.dumps({'products': [{'productCode': 'MANAGER-BULK', 'standardPrice': '100'}]}),
            content_type='application/json',
        )
        self.assertEqual(bulk_response.status_code, 403)

        delete_response = self.client.post(
            reverse('reporting:products_bulk_delete_api'),
            data=json.dumps({'productCodes': [product.product_code]}),
            content_type='application/json',
        )
        self.assertEqual(delete_response.status_code, 403)
        product.refresh_from_db()
        self.assertEqual(product.standard_price, 1000)

    def test_product_bulk_delete_deletes_unused_and_blocks_used_product(self):
        import json
        from reporting.models import DeliveryItem, Product

        unused = Product.objects.create(product_code='DELETE-UNUSED', standard_price=1000, created_by=self.salesman)
        used = Product.objects.create(product_code='DELETE-USED', standard_price=2000, created_by=self.salesman)
        DeliveryItem.objects.create(product=used, item_name='사용 제품', quantity=1, unit_price=2000)

        response = self.client.post(
            reverse('reporting:products_bulk_delete_api'),
            data=json.dumps({'productCodes': [unused.product_code, used.product_code, 'DELETE-MISSING']}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['deletedCount'], 1)
        self.assertEqual(payload['blockedCount'], 1)
        self.assertEqual(payload['missingCount'], 1)
        blocked = next(item for item in payload['results'] if item['productCode'] == used.product_code)
        self.assertTrue(blocked['canReplace'])
        self.assertEqual(blocked['deliveryItemCount'], 1)
        self.assertEqual(blocked['referenceCount'], 1)
        self.assertEqual(blocked['references'][0]['referenceType'], 'deliveryItem')
        self.assertEqual(blocked['references'][0]['itemName'], used.product_code)
        self.assertFalse(Product.objects.filter(product_code=unused.product_code).exists())
        self.assertTrue(Product.objects.filter(product_code=used.product_code).exists())

    def test_product_delete_replaces_used_items_one_reference_at_a_time(self):
        import datetime
        import json
        from django.utils import timezone
        from reporting.models import Company, DeliveryItem, Department, FollowUp, Product, Quote, QuoteItem, Schedule

        old = Product.objects.create(
            product_code='DELETE-REPLACE-OLD',
            unit='EA',
            standard_price=2000,
            created_by=self.salesman,
        )
        replacement = Product.objects.create(
            product_code='DELETE-REPLACE-NEW',
            unit='SET',
            standard_price=3000,
            created_by=self.salesman,
        )
        company = Company.objects.create(name='제품대체 고객사', created_by=self.salesman)
        department = Department.objects.create(company=company, name='제품대체 연구실', created_by=self.salesman)
        followup = FollowUp.objects.create(
            user=self.salesman,
            user_company=self.company,
            customer_name='제품대체 담당자',
            company=company,
            department=department,
        )
        schedule = Schedule.objects.create(
            user=self.salesman,
            company=self.company,
            followup=followup,
            visit_date=timezone.localdate(),
            visit_time=datetime.time(10, 0),
            activity_type='quote',
            status='scheduled',
        )
        delivery_item = DeliveryItem.objects.create(
            schedule=schedule,
            product=old,
            item_name=old.product_code,
            quantity=2,
            unit_price=2000,
        )
        quote = Quote.objects.create(
            quote_number='Q-REPLACE-001',
            schedule=schedule,
            followup=followup,
            user=self.salesman,
            valid_until=timezone.localdate() + datetime.timedelta(days=30),
        )
        quote_item = QuoteItem.objects.create(
            quote=quote,
            product=old,
            quantity=1,
            unit_price=2000,
        )

        blocked_response = self.client.post(
            reverse('reporting:products_bulk_delete_api'),
            data=json.dumps({
                'productCodes': [old.product_code],
            }),
            content_type='application/json',
        )

        self.assertEqual(blocked_response.status_code, 200)
        blocked_payload = blocked_response.json()
        self.assertEqual(blocked_payload['deletedCount'], 0)
        self.assertEqual(blocked_payload['blockedCount'], 1)
        blocked = blocked_payload['results'][0]
        self.assertEqual(blocked['referenceCount'], 2)
        reference_ids = {(item['referenceType'], item['referenceId']) for item in blocked['references']}
        self.assertEqual(reference_ids, {('deliveryItem', delivery_item.id), ('quoteItem', quote_item.id)})

        response = self.client.post(
            reverse('reporting:product_replace_reference_api'),
            data=json.dumps({
                'productCode': old.product_code,
                'referenceType': 'deliveryItem',
                'referenceId': delivery_item.id,
                'replacementProductId': replacement.id,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertFalse(payload['deletedOriginal'])
        self.assertEqual(payload['replacementProductCode'], replacement.product_code)
        self.assertEqual(payload['result']['status'], 'blocked')
        self.assertEqual(payload['result']['referenceCount'], 1)
        delivery_item.refresh_from_db()
        self.assertEqual(delivery_item.product, replacement)
        self.assertEqual(delivery_item.item_name, replacement.product_code)
        self.assertEqual(delivery_item.unit, 'SET')

        response = self.client.post(
            reverse('reporting:product_replace_reference_api'),
            data=json.dumps({
                'productCode': old.product_code,
                'referenceType': 'quoteItem',
                'referenceId': quote_item.id,
                'replacementProductId': replacement.id,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['deletedOriginal'])
        self.assertEqual(payload['result']['status'], 'deleted')
        self.assertFalse(Product.objects.filter(product_code=old.product_code).exists())
        quote_item.refresh_from_db()
        self.assertEqual(quote_item.product, replacement)

    def test_product_replace_history_delivery_item_updates_history_summary(self):
        import json
        from reporting.models import Company, DeliveryItem, Department, FollowUp, History, Product

        old = Product.objects.create(
            product_code='DELETE-HISTORY-OLD',
            unit='EA',
            standard_price=2000,
            created_by=self.salesman,
        )
        replacement = Product.objects.create(
            product_code='DELETE-HISTORY-NEW',
            unit='BOX',
            standard_price=3000,
            created_by=self.salesman,
        )
        company = Company.objects.create(name='히스토리대체 고객사', created_by=self.salesman)
        department = Department.objects.create(company=company, name='히스토리대체 부서', created_by=self.salesman)
        followup = FollowUp.objects.create(
            user=self.salesman,
            user_company=self.company,
            customer_name='히스토리대체 담당자',
            company=company,
            department=department,
        )
        history = History.objects.create(
            user=self.salesman,
            company=self.company,
            followup=followup,
            action_type='delivery_schedule',
            content='납품 기록',
        )
        delivery_item = DeliveryItem.objects.create(
            history=history,
            product=old,
            item_name=old.product_code,
            quantity=3,
            unit_price=2000,
        )

        blocked_response = self.client.post(
            reverse('reporting:products_bulk_delete_api'),
            data=json.dumps({'productCodes': [old.product_code]}),
            content_type='application/json',
        )

        self.assertEqual(blocked_response.status_code, 200)
        blocked = blocked_response.json()['results'][0]
        self.assertEqual(blocked['references'][0]['historyId'], history.id)

        response = self.client.post(
            reverse('reporting:product_replace_reference_api'),
            data=json.dumps({
                'productCode': old.product_code,
                'referenceType': 'deliveryItem',
                'referenceId': delivery_item.id,
                'replacementProductId': replacement.id,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['deletedOriginal'])
        self.assertFalse(Product.objects.filter(product_code=old.product_code).exists())
        delivery_item.refresh_from_db()
        history.refresh_from_db()
        self.assertEqual(delivery_item.product, replacement)
        self.assertEqual(delivery_item.item_name, replacement.product_code)
        self.assertEqual(delivery_item.unit, 'BOX')
        self.assertIn(replacement.product_code, history.delivery_items)
        self.assertEqual(int(history.delivery_amount), 6600)

    def test_products_excel_export_returns_xlsx(self):
        from reporting.models import Product

        Product.objects.create(product_code='XLSX-001', description='다운로드', standard_price=1000, created_by=self.salesman)

        response = self.client.get(reverse('reporting:products_excel_export_api'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            response['Content-Type'],
        )
        self.assertIn('products-', response['Content-Disposition'])


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.5: 대시보드 일정 표시 테스트 (Bug 2 & 3)
# ─────────────────────────────────────────────────────────────────────────────

class DashboardScheduleDisplayTests(TestCase):
    """React dashboard API 일정 표시 검증"""

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
        """대시보드 API 200 응답"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        self.assertEqual(r.status_code, 200)

    def test_today_schedules_includes_scheduled(self):
        """today.items에 오늘 예정 일정 포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['today']['items']]
        self.assertIn(self.today_scheduled.pk, ids,
                      '오늘 예정 일정이 today.items에 포함되어야 합니다')

    def test_today_schedules_includes_completed(self):
        """today.items에 오늘 완료된 일정도 포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['today']['items']]
        self.assertIn(self.today_completed.pk, ids,
                      '오늘 완료된 일정도 today.items에 포함되어야 합니다')

    def test_upcoming_includes_tomorrow_scheduled(self):
        """upcomingSchedules에 내일 예정 일정 포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['upcomingSchedules']]
        self.assertIn(self.tomorrow_scheduled.pk, ids,
                      '내일 예정 일정이 upcomingSchedules에 포함되어야 합니다')

    def test_upcoming_includes_completed_within_range(self):
        """upcomingSchedules에 이번 주 완료된 일정도 포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['upcomingSchedules']]
        self.assertIn(self.upcoming_completed.pk, ids,
                      '이번 주 완료된 일정도 upcomingSchedules에 포함되어야 합니다')

    def test_upcoming_excludes_out_of_range(self):
        """upcomingSchedules에 6일 초과 일정은 미포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['upcomingSchedules']]
        self.assertNotIn(self.out_of_range.pk, ids,
                         '6일 초과 일정은 upcomingSchedules에 포함되지 않아야 합니다')

    def test_upcoming_excludes_past_schedules(self):
        """upcomingSchedules에 과거 일정 미포함"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        ids = [s['id'] for s in r.json()['upcomingSchedules']]
        self.assertNotIn(self.yesterday.pk, ids,
                         '어제 일정은 upcomingSchedules에 포함되지 않아야 합니다')

    def test_schedule_count_nonzero_when_schedules_exist(self):
        """일정이 있을 때 API 일정 지표가 0이 아님"""
        r = self.client.get(reverse('reporting:dashboard_summary_api'))
        metrics = r.json()['metrics']
        self.assertGreater(int(metrics['todaySchedules']) + int(metrics['weeklySchedules']), 0)


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
        self.assertIn(r.status_code, [302, 401, 403])

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

