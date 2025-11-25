"""
회사별 접근 권한을 제어하는 데코레이터들
"""
from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect

def get_filtered_user(request):
    """
    관리자가 필터링한 사용자 또는 현재 로그인 사용자 반환
    
    Returns:
        User: 관리자가 선택한 사용자 또는 현재 로그인 사용자
    """
    if request.is_admin and hasattr(request, 'admin_filter_user') and request.admin_filter_user:
        return request.admin_filter_user
    return request.user

def get_filtered_company(request):
    """
    관리자가 필터링한 회사 또는 현재 사용자의 회사 반환
    
    Returns:
        UserCompany or None: 관리자가 선택한 회사 또는 현재 사용자의 회사
    """
    if request.is_admin and hasattr(request, 'admin_filter_company') and request.admin_filter_company:
        return request.admin_filter_company
    return getattr(request, 'user_company', None)

def hanagwahak_only(view_func):
    """
    하나과학 회사 사용자만 접근할 수 있는 데코레이터
    서비스 관련 기능에 적용됩니다.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 로그인하지 않은 사용자는 접근 불가
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        # request.is_hanagwahak은 CompanyFilterMiddleware에서 설정됨
        if not getattr(request, 'is_hanagwahak', False):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX 요청인 경우
                return JsonResponse({
                    'error': '서비스 기능은 하나과학 소속 사용자만 이용할 수 있습니다.',
                    'redirect': reverse('reporting:dashboard')
                }, status=403)
            else:
                # 일반 요청인 경우
                messages.error(request, '서비스 기능은 하나과학 소속 사용자만 이용할 수 있습니다.')
                return redirect('reporting:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def filter_service_for_non_hanagwahak(queryset, request):
    """
    하나과학이 아닌 회사의 사용자에게는 서비스 관련 데이터를 필터링하는 함수
    """
    if not getattr(request, 'is_hanagwahak', False):
        # 하나과학이 아니면 서비스 관련 데이터 제외
        return queryset.exclude(action_type='service').exclude(activity_type='service')
    return queryset

def get_allowed_action_types(request):
    """
    사용자의 회사에 따라 허용되는 action_type 목록을 반환
    """
    if getattr(request, 'is_hanagwahak', False):
        # 하나과학은 모든 액션 타입 허용
        return [
            ('customer_meeting', '고객 미팅'),
            ('delivery_schedule', '납품 일정'),
            ('service', '서비스'),
            ('memo', '메모'),
        ]
    else:
        # 다른 회사는 서비스 제외
        return [
            ('customer_meeting', '고객 미팅'),
            ('delivery_schedule', '납품 일정'),
            ('memo', '메모'),
        ]

def get_allowed_activity_types(request):
    """
    사용자의 회사에 따라 허용되는 activity_type 목록을 반환
    """
    if getattr(request, 'is_hanagwahak', False):
        # 하나과학은 모든 활동 타입 허용
        return [
            ('customer_meeting', '고객 미팅'),
            ('delivery', '납품 일정'),
            ('service', '서비스'),
        ]
    else:
        # 다른 회사는 서비스 제외
        return [
            ('customer_meeting', '고객 미팅'),
            ('delivery', '납품 일정'),
        ]