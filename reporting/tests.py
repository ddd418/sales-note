from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from reporting.models import UserProfile, UserCompany


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
        """올바른 자격 증명으로 로그인 가능"""
        response = self.client.post(
            reverse('reporting:login'),
            {'username': 'testuser', 'password': 'TestPass123!'},
            follow=True,
        )
        self.assertTrue(response.context['user'].is_authenticated)

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

    def test_opportunity_list_authenticated(self):
        """인증 후 영업 기회 목록 200 응답"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reporting:opportunity_list'))
        self.assertEqual(response.status_code, 200)

    def test_opportunity_list_unauthenticated_redirects(self):
        """미인증 상태에서 영업 기회 목록 접근 시 리다이렉트"""
        response = self.client.get(reverse('reporting:opportunity_list'))
        self.assertIn(response.status_code, [302, 301])

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

    def test_opportunity_list_blocked(self):
        self._assert_redirects_to_login(reverse('reporting:opportunity_list'))

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

