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

