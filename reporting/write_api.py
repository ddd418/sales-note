"""Sales Note 쓰기용 기계 인증 (write MCP proxy 대응).

reporting/readonly_api.py 의 쓰기 버전. 기계 호출자(쓰기 MCP 프록시 또는 이 세션의
Claude)를 **실재하는 비-특권 유저**로 인증한다. 브라우저/세션 호출자의 인증은 절대
약화하지 않는다.

권한 모델 (사용자가 명시적으로 선택한 "전부 쓰기 + 위험액션 확인" 정책):
- **전부 쓰기**: 아래 WRITE_DENY_URL_NAMES 에 없는 모든 POST 쓰기 엔드포인트에 도달 가능.
  실제 데이터 보호는 acting 유저의 역할/scope 검사(뷰 계층)가 담당한다. acting 유저가
  salesman 이면 자기 소유 데이터에만 쓰기가 되고, admin/manager 전용 액션은 뷰에서 403.
- **deny**: 로그인/세션/백업/유저·권한관리/자격증명 연결은 토큰으로 절대 도달 불가.
- **확인 필요(428)**: 되돌릴 수 없거나 외부로 나가는 액션(삭제/메일발송/금액취소/파괴적
  대량변경)은 `X-Salesnote-Write-Confirm: yes` 헤더가 있어야 실행. 없으면 428 로 거부하고
  아무것도 바꾸지 않는다(호출자가 사람에게 확인 후 재요청).

불변식:
- acting 유저는 SALES_NOTE_WRITE_USER_ID 로 해석하며, 반드시 활성·비-staff·비-superuser·
  비-admin (권한 붕괴 방지, readonly 의 admin 폴백 미복사).
- 유효한 쓰기 토큰 요청에 한해서만 CSRF 를 건너뛴다. 세션/쿠키 요청은 CSRF 그대로.

배포/노출 계층은 WRITE_PROXY_DESIGN.md 참고.
"""
import os
import secrets
from functools import wraps

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import resolve, Resolver404


# 쓰기 토큰에 허용되는 HTTP 메서드 (이 코드베이스는 create/update/delete 모두 POST).
WRITE_ALLOWED_METHODS = {"POST"}

# 확인 헤더 (값이 'yes' 여야 위험 액션 실행).
CONFIRM_HEADER = "X-Salesnote-Write-Confirm"

# 토큰으로 절대 도달 불가한 url_name. (대부분 acting 이 salesman 이면 뷰에서 role-block
# 되지만, 방어적으로 명시 차단한다. 자격증명/세션/시스템 표면.)
WRITE_DENY_URL_NAMES = {
    # 인증/세션/시스템
    "login", "logout", "set_admin_filter",
    "backup_database_api", "backup_status_api",
    # 유저/권한 관리
    "employees_management_api", "employees_create_api", "employees_update_api",
    "employees_toggle_active_api", "user_create", "user_edit", "user_delete",
    "user_toggle_active", "user_toggle_ai", "manager_user_create",
    "manager_user_edit", "manager_user_list", "api_change_company_creator",
    # 메일/자격증명 연결 (자격증명 쓰기)
    "gmail_callback", "gmail_disconnect", "imap_connect", "imap_disconnect",
    "profile_imap_connect_api", "profile_email_disconnect_api", "profile_api_password",
}

# 되돌릴 수 없거나 외부로 나가는 액션 — 확인 헤더 필요.
# (1) 키워드 매칭: 이름에 아래 조각이 들어가면 자동으로 확인 대상(누락 시 fail-safe).
_CONFIRM_KEYWORDS = (
    "delete", "cancel", "transfer", "remove", "trash", "send", "reply",
)
# (2) 키워드로 안 잡히는 고위험/파괴적 액션 명시.
WRITE_CONFIRM_URL_NAMES = {
    "schedules_delivery_items_update_api",  # 납품품목 전체 삭제+재생성, 선결제 소모
    "schedule_status_update",               # cancelled 시 납품 히스토리 삭제
    "account_update_api",                   # 계정 회사 이동(연락처 재부모)
    "department_update_api",                # 부서 회사 이동 캐스케이드
    "products_bulk_upsert_api",             # 제품 대량 변경
    "products_excel_import_api",            # 파일 기반 대량 변경
    "product_replace_reference_api",        # 과거 납품/견적 품목 FK 재작성
    "data_quality_contact_assign_account_api",  # 연락처 계정 재배치
    "receivable_item_status_api",           # 정산/카드수금(금액 관련) 플래그
}


def get_write_api_user():
    """쓰기 토큰의 acting 유저. admin/superuser/staff 는 거부(scope 붕괴 방지)."""
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


def requires_write_confirmation(url_name):
    """되돌릴 수 없는/외부로 나가는 액션인지 (확인 헤더 필요)."""
    if not url_name:
        return False
    if url_name in WRITE_CONFIRM_URL_NAMES:
        return True
    return any(kw in url_name for kw in _CONFIRM_KEYWORDS)


def authenticate_write_bearer(request):
    """유효한 쓰기 토큰 + (deny 아닌) 쓰기 POST 면 request.user 를 acting 유저로
    세팅하고 True 를 반환한다. 확인 게이트는 미들웨어가 별도로 처리한다."""
    if request.method not in WRITE_ALLOWED_METHODS:
        return False

    url_name = _resolve_url_name(request)
    if url_name is None or url_name in WRITE_DENY_URL_NAMES:
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
    request.salesnote_write_url_name = url_name
    return True


class WriteBearerMiddleware:
    """URL 라우팅/CSRF 검사 전에 기계 쓰기 토큰을 인증하는 미들웨어.

    배치: AuthenticationMiddleware 뒤 + CompanyFilterMiddleware 앞. 요청-단계에서
    실행되므로 여기서 세팅한 request._dont_enforce_csrf_checks 를 CsrfViewMiddleware
    가 존중한다. 위험 액션은 확인 헤더가 없으면 428 로 즉시 거부(뷰 미실행).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization", "")
        if (
            request.method in WRITE_ALLOWED_METHODS
            and auth_header.lower().startswith("bearer ")
            and authenticate_write_bearer(request)
        ):
            url_name = getattr(request, "salesnote_write_url_name", None)
            if requires_write_confirmation(url_name):
                confirm = request.headers.get(CONFIRM_HEADER, "").strip().lower()
                if confirm != "yes":
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "confirmation_required",
                            "message": (
                                "되돌릴 수 없거나 외부로 나가는 작업입니다. 사용자 확인 후 "
                                f"'{CONFIRM_HEADER}: yes' 헤더로 재요청하세요."
                            ),
                            "url_name": url_name,
                        },
                        status=428,
                    )
            # 여기까지 왔으면 실행. 기계 호출자는 CSRF 쿠키가 없으므로 이 요청만 우회.
            request._dont_enforce_csrf_checks = True
        return self.get_response(request)


def write_bearer_or_login_required(view_func):
    """심층 방어 데코레이터: 토큰 인증 요청이면 url_name 이 deny 가 아님을 재확인.
    세션 유저는 그대로 통과."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if getattr(request, "salesnote_write_api", False):
            resolver_match = getattr(request, "resolver_match", None)
            url_name = getattr(resolver_match, "url_name", None)
            if url_name is None or url_name in WRITE_DENY_URL_NAMES:
                return JsonResponse(
                    {"success": False, "error": "forbidden"}, status=403
                )
        return view_func(request, *args, **kwargs)

    return _wrapped
