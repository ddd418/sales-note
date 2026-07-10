"""Sales Note 쓰기용 기계 인증 (write MCP proxy 대응).

reporting/readonly_api.py 를 구조적으로 미러링하되, GET 읽기 대신 **작은
POST 전용 화이트리스트**의 쓰기 엔드포인트에 대해, 기계 호출자(예: 쓰기 MCP
프록시)를 **실재하는 비-특권 유저**로 인증한다. 브라우저/세션 호출자의 인증은
절대 약화하지 않는다.

핵심 불변식:
- ``Authorization: Bearer <SALES_NOTE_WRITE_TOKEN>`` 가 유효하고, url_name 이
  화이트리스트에 있으며, 쓰기 메서드(POST)일 때만 이 경로가 동작한다.
- 그런 요청에 한해서만 CSRF 검사를 건너뛴다(기계 호출자는 CSRF 쿠키를 얻을 수
  없음). 세션/쿠키 요청은 CSRF 가 그대로 강제된다.
- acting 유저는 SALES_NOTE_WRITE_USER_ID 로 해석하며, 반드시 활성·비-staff·
  비-superuser·비-admin 이어야 한다. 그래야 뷰의 기존 역할/scope 검사
  (can_modify_user_data, scope_users, per-object 권한)가 브라우저 세션과
  동일하게 발동한다. (readonly 의 admin 폴백은 절대 재사용하지 않는다.)

배포/노출은 WRITE_PROXY_DESIGN.md 의 계층(Tier A/B/C)을 따른다.
"""
import os
import secrets
from functools import wraps

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import resolve, Resolver404


# 쓰기 토큰이 도달할 수 있는 POST 전용 url_name. 반드시 작고 명시적으로 유지한다.
# 와일드카드 금지. 계층(Tier A→B) 확장은 의도적으로만.
WRITE_ALLOWED_URL_NAMES = {
    # Tier A — 저위험, self-scoped, 되돌리기 쉬움
    "notes_create_api",
    "schedules_create_api",
    "schedule_move_api",
}

# 쓰기 토큰에 허용되는 HTTP 메서드. 이 코드베이스는 create/update/delete 모두
# POST 를 쓰므로 POST 만 허용한다(PATCH/DELETE 라우트가 실제로 생기기 전엔 추가 금지).
WRITE_ALLOWED_METHODS = {"POST"}


def get_write_api_user():
    """쓰기 토큰의 acting 유저를 해석한다.

    get_readonly_api_user() 와 달리 admin/superuser 폴백이 **없다**. 쓰기 신원이
    admin 으로 매핑되면 can_modify_user_data / scope 검사를 무조건 통과해 모든
    per-user 권한이 붕괴한다. 따라서 반드시 명시적으로 설정된 비-특권 유저여야 한다.
    """
    user_id = os.environ.get("SALES_NOTE_WRITE_USER_ID", "").strip()
    if not user_id:
        return None

    user = (
        User.objects.filter(
            pk=user_id, is_active=True, is_staff=False, is_superuser=False
        )
        .select_related("userprofile")
        .first()
    )
    if not user:
        return None

    # 쓰기 신원이 admin 역할이면 거부(scope 우회 방지).
    profile = getattr(user, "userprofile", None)
    if profile is not None and getattr(profile, "role", None) == "admin":
        return None

    return user


def _resolve_url_name(request):
    try:
        match = resolve(request.path_info)
    except Resolver404:
        return None
    return match.url_name


def authenticate_write_bearer(request):
    """유효한 쓰기 토큰 + 화이트리스트 POST 엔드포인트면 request.user 를 acting
    유저로 세팅하고 True 를 반환한다. 그 외에는 False."""
    if request.method not in WRITE_ALLOWED_METHODS:
        return False

    url_name = _resolve_url_name(request)
    if url_name not in WRITE_ALLOWED_URL_NAMES:
        return False

    expected_token = os.environ.get("SALES_NOTE_WRITE_TOKEN", "").strip()
    if not expected_token:
        return False

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return False

    supplied_token = auth_header.split(None, 1)[1].strip()
    if not secrets.compare_digest(supplied_token, expected_token):
        return False

    user = get_write_api_user()
    if not user:
        return False

    request.user = user
    request.salesnote_write_api = True
    return True


class WriteBearerMiddleware:
    """URL 라우팅/CSRF 검사 전에 기계 쓰기 토큰을 인증하는 미들웨어.

    배치: AuthenticationMiddleware **뒤**(유효 토큰일 때만 실제 세션 유저를
    교체) + reporting.middleware.CompanyFilterMiddleware **앞**(request.is_admin
    / admin_filter_* / user_company 가 acting 유저 기준으로 계산되도록).

    이 요청-단계 코드는 모든 process_view 훅보다 먼저 실행되므로, 여기서 세팅한
    request._dont_enforce_csrf_checks 를 CsrfViewMiddleware 가 존중한다.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 값싼 사전 필터: bearer 를 단 POST 만 후보. 일반 트래픽엔 사실상 무비용.
        auth_header = request.headers.get("Authorization", "")
        if (
            request.method in WRITE_ALLOWED_METHODS
            and auth_header.lower().startswith("bearer ")
        ):
            if authenticate_write_bearer(request):
                # 기계 호출자는 CSRF 쿠키를 얻을 수 없으므로 이 요청에 한해 CSRF 를
                # 건너뛴다. 세션/쿠키 요청은 이 분기에 절대 들어오지 않는다.
                request._dont_enforce_csrf_checks = True
        return self.get_response(request)


def write_bearer_or_login_required(view_func):
    """심층 방어 데코레이터: 토큰 인증된 요청이면 url_name 이 화이트리스트에 있는지
    다시 확인해, 미들웨어 설정이 흘러도 표면이 조용히 넓어지지 않게 한다. 세션
    유저는 그대로 통과."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if getattr(request, "salesnote_write_api", False):
            resolver_match = getattr(request, "resolver_match", None)
            url_name = getattr(resolver_match, "url_name", None)
            if url_name not in WRITE_ALLOWED_URL_NAMES:
                return JsonResponse(
                    {"success": False, "error": "forbidden"}, status=403
                )
        return view_func(request, *args, **kwargs)

    return _wrapped
