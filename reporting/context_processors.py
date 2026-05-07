"""
Context processors for the reporting app.
"""

from urllib.parse import urljoin

from django.conf import settings


DEFAULT_FRONTEND_PIPELINE_URL = "https://sales-note-frontend-production.up.railway.app/"


def _frontend_url(base_url, path=""):
    normalized_base = f"{base_url.rstrip('/')}/"
    return urljoin(normalized_base, path.lstrip("/"))


def manager_filter_context(request):
    """
    매니저가 모든 페이지에서 실무자 필터를 사용할 수 있도록 컨텍스트 제공
    """
    frontend_base_url = getattr(
        settings,
        "FRONTEND_PIPELINE_URL",
        DEFAULT_FRONTEND_PIPELINE_URL,
    )
    context = {
        "frontend_pipeline_url": _frontend_url(frontend_base_url),
        "frontend_dashboard_url": _frontend_url(frontend_base_url, "dashboard/"),
        "frontend_customers_url": _frontend_url(frontend_base_url, "customers/"),
        "frontend_notes_url": _frontend_url(frontend_base_url, "notes/"),
        "frontend_schedules_url": _frontend_url(frontend_base_url, "schedules/"),
        "frontend_ai_url": _frontend_url(frontend_base_url, "ai-workspace/"),
    }
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            
            # 매니저인 경우에만 실무자 목록 제공
            if user_profile.role == 'manager':
                from django.contrib.auth.models import User
                from reporting.models import UserProfile
                
                # URL 파라미터로 사용자 선택 시 세션에 저장
                user_filter = request.GET.get('user')
                if user_filter:
                    request.session['manager_selected_user'] = user_filter
                
                # 같은 회사의 실무자(salesman) 목록
                if user_profile.company:
                    accessible_salesmen = User.objects.filter(
                        userprofile__company=user_profile.company,
                        userprofile__role='salesman'
                    ).select_related('userprofile').order_by('username')
                else:
                    # 회사가 없는 경우 빈 쿼리셋
                    accessible_salesmen = User.objects.none()
                
                context['accessible_salesmen'] = accessible_salesmen
                
                # 세션에 저장된 선택 사용자가 있으면 컨텍스트에 추가
                if 'manager_selected_user' in request.session:
                    context['manager_selected_user_id'] = request.session['manager_selected_user']
        except:
            pass
    
    return context
