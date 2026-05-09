import json

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from reporting.models import (
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

    def test_history_list_authenticated(self):
        """인증 후 영업 활동 목록 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:history_list'))
        self.assertEqual(response.status_code, 200)

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
        self.assertTrue(any(option['id'] == own.department_id for option in payload['create']['departments']))

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
        self.assertTrue(payload['edit']['canEdit'])
        self.assertEqual(payload['edit']['submitUrl'], reverse('reporting:schedules_update_api', args=[schedule.id]))
        self.assertEqual(payload['relatedNotes'][0]['id'], schedule.histories.first().id)
        self.assertEqual(payload['deliveryItems'][0]['itemName'], 'PCR Kit')
        self.assertEqual(payload['links']['uploadFiles'], reverse('reporting:schedule_file_upload', args=[schedule.id]))
        self.assertEqual(payload['links']['updateDeliveryItems'], reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]))
        self.assertEqual(payload['schedule']['files'][0]['id'], schedule_file.id)
        self.assertEqual(payload['schedule']['files'][0]['deleteHref'], reverse('reporting:schedule_file_delete', args=[schedule_file.id]))

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
                'items': [
                    {
                        'itemName': 'PCR Kit',
                        'quantity': 2,
                        'unit': 'EA',
                        'unitPrice': '100000',
                        'taxInvoiceIssued': True,
                        'notes': '1차 납품',
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
        self.assertEqual(int(items[0].total_price), 220000)
        self.assertTrue(items[0].tax_invoice_issued)
        self.assertEqual(items[0].notes, '1차 납품')
        self.assertIsNone(items[1].unit_price)
        history.refresh_from_db()
        self.assertIn('PCR Kit', history.delivery_items)
        self.assertIn('Buffer', history.delivery_items)
        self.assertEqual(int(history.delivery_amount), 220000)
        self.assertEqual(payload['deliveryItems'][0]['itemName'], 'PCR Kit')
        self.assertEqual(payload['deliveryItems'][0]['totalPrice'], 220000)

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

        analysis = AIDepartmentAnalysis.objects.create(
            user=owner,
            department=department,
            analysis_data={
                'department_summary': '후속 연락이 지연되고 있어 견적 대응이 필요합니다.',
                'next_actions': [{'action': '견적 후속 연락', 'priority': 'high'}],
            },
            quote_delivery_data={'total_quotes': 2, 'total_deliveries': 1},
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
        self.assertTrue(payload['recommendedGoals'])

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

