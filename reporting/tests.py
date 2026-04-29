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

