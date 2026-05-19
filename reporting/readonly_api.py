import os
import secrets
from functools import wraps

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import reverse


READONLY_ALLOWED_URL_NAMES = {
    "dashboard_summary_api",
    "reports_summary_api",
    "customers_summary_api",
    "followups_summary_api",
    "pipeline_command_center_api",
}


def authenticate_readonly_bearer(request, allowed_url_names=None):
    """Allow the Sales Note analysis token on a small GET-only API surface."""
    if request.method != "GET":
        return False

    resolver_match = getattr(request, "resolver_match", None)
    url_name = getattr(resolver_match, "url_name", None)
    allowed = set(allowed_url_names or READONLY_ALLOWED_URL_NAMES)
    if url_name not in allowed:
        return False

    expected_token = os.environ.get("SALES_NOTE_READONLY_TOKEN", "").strip()
    if not expected_token:
        return False

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return False

    supplied_token = auth_header.split(None, 1)[1].strip()
    if not secrets.compare_digest(supplied_token, expected_token):
        return False

    user = get_readonly_api_user()
    if not user:
        return False

    request.user = user
    request.salesnote_readonly_api = True
    return True


def get_readonly_api_user():
    user_id = os.environ.get("SALES_NOTE_READONLY_USER_ID", "").strip()
    username = os.environ.get("SALES_NOTE_READONLY_USERNAME", "").strip()

    if user_id:
        user = User.objects.filter(pk=user_id, is_active=True).first()
        if user:
            return user

    if username:
        user = User.objects.filter(username=username, is_active=True).first()
        if user:
            return user

    return (
        User.objects.filter(is_active=True, userprofile__role="admin")
        .select_related("userprofile")
        .order_by("id")
        .first()
        or User.objects.filter(is_active=True, is_superuser=True).order_by("id").first()
    )


def api_login_required_or_readonly_response(request):
    if request.user.is_authenticated:
        return None
    if authenticate_readonly_bearer(request):
        return None
    return JsonResponse(
        {
            "success": False,
            "error": "login_required",
            "message": "로그인이 필요합니다.",
            "loginUrl": reverse("reporting:login"),
        },
        status=401,
    )


def readonly_bearer_or_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated or authenticate_readonly_bearer(request):
            return view_func(request, *args, **kwargs)
        return JsonResponse(
            {
                "success": False,
                "error": "login_required",
                "message": "로그인이 필요합니다.",
                "loginUrl": reverse("reporting:login"),
            },
            status=401,
        )

    return _wrapped
