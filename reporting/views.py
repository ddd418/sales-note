from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # 로그인 요구 데코레이터
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse
from django.db import transaction
from . import vat
from django.db.models import Sum, Count, Q, Prefetch
from django.core.paginator import Paginator  # 페이지네이션 추가
from .models import FollowUp, Schedule, ScheduleFile, ScheduleQuoteGroupNote, History, AIWorkspaceActionFeedback, AIWorkspaceMemory, UserProfile, Company, Department, DepartmentMemo, HistoryFile, DeliveryItem, UserCompany, Prepayment, PrepaymentLedgerEntry, PrepaymentUsage, EmailLog, CustomerCategory, FunnelTarget, Quote, DocumentTemplate, DocumentGenerationLog, CustomerAsset, normalize_probability_to_five
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from functools import wraps
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_http_methods
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from .readonly_api import api_login_required_or_readonly_response
from .services.account_ledger import account_operational_ledger_for_followups, account_followups_for_followup, account_representative_followup, delivery_record_payload as account_delivery_record_payload, prepayment_account_filter, sync_schedule_delivery_payment_type
import os
import mimetypes
import logging
import json
import re
import html
from datetime import date, time, timedelta

# 로거 설정
logger = logging.getLogger(__name__)


def _receivables_only_response():
    return JsonResponse({
        'success': False,
        'error': '세금계산서/외상 상태는 외상고객 메뉴에서만 변경할 수 있습니다.',
        'message': '외상고객 메뉴에서 품목별 외상, 카드결제, 수금완료 상태를 처리하세요.',
        'redirect': '/receivables/',
    }, status=410)


def _prepayment_department_filter(department):
    """Compatibility shim for legacy helpers still living in views.py."""
    return prepayment_account_filter(department=department)


def _prepayment_item_payload(prepayment, actor):
    """Delegate to the split prepayment API module during migration."""
    from reporting.api.prepayments import _prepayment_item_payload as _payload

    return _payload(prepayment, actor)


def _date_one_month_before(value):
    month = value.month - 1
    year = value.year
    if month < 1:
        month = 12
        year -= 1
    if month in {1, 3, 5, 7, 8, 10, 12}:
        last_day = 31
    elif month == 2:
        last_day = 29 if (year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)) else 28
    else:
        last_day = 30
    return value.replace(year=year, month=month, day=min(value.day, last_day))


def _parse_iso_date_or_none(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _prepayment_create_ledger(*args, **kwargs):
    """Delegate to the split prepayment API module during migration."""
    from reporting.api.prepayments import _prepayment_create_ledger as _create

    return _create(*args, **kwargs)

def save_delivery_items(request, instance_obj):
    """납품 품목 데이터를 저장하는 함수 (스케줄 또는 히스토리)"""
    from .models import DeliveryItem
    
    # 인스턴스 타입 확인
    from .models import Schedule, History
    is_schedule = isinstance(instance_obj, Schedule)
    is_history = isinstance(instance_obj, History)
    
    if not (is_schedule or is_history):
        logger.error(f"save_delivery_items: 지원되지 않는 객체 타입: {type(instance_obj)}")
        return
    
    # 기존 품목들 삭제 (수정 시)
    if is_schedule:
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
    else:  # is_history
        existing_count = instance_obj.delivery_items_set.all().count()
        instance_obj.delivery_items_set.all().delete()
    
    # delivery_items 관련 POST 데이터만 필터링
    delivery_items_data = {}
    
    for key, value in request.POST.items():
        if key.startswith('delivery_items[') and '][' in key:
            # delivery_items[0][name] -> index=0, field=name
            try:
                start = key.find('[') + 1
                end = key.find(']')
                index = int(key[start:end])
                
                field_start = key.rfind('[') + 1
                field_end = key.rfind(']')
                field = key[field_start:field_end]
                
                if index not in delivery_items_data:
                    delivery_items_data[index] = {}
                delivery_items_data[index][field] = value
            except (ValueError, IndexError) as e:
                logger.error(f"POST 데이터 파싱 실패: {key} = {value}, 오류: {e}")
                continue
    
    # 납품 품목 저장
    created_count = 0
    
    for index, item_data in delivery_items_data.items():
        item_name = item_data.get('name', '').strip()
        quantity = item_data.get('quantity', '').strip()
        unit_price = item_data.get('unit_price', '').strip()
        discount_rate = item_data.get('discount_rate', '').strip()
        discount_unit_price = item_data.get('discount_unit_price', '').strip()
        notes = item_data.get('notes', '').strip()
        option_description = (
            item_data.get('option_description', '')
            or item_data.get('optionDescription', '')
        ).strip()
        product_id = item_data.get('product_id', '').strip()
        
        if item_name and quantity:
            try:
                delivery_item = DeliveryItem(
                    item_name=item_name,
                    quantity=int(quantity),
                    unit='개',  # 기본값
                )
                
                # 제품 연결
                if product_id:
                    try:
                        from .models import Product
                        delivery_item.product = Product.objects.get(id=int(product_id))
                    except (Product.DoesNotExist, ValueError):
                        pass
                
                # 스케줄 또는 히스토리 연결
                if is_schedule:
                    delivery_item.schedule = instance_obj
                else:
                    delivery_item.history = instance_obj
                
                # unit_price 저장 (빈 문자열, None이 아니면 0 포함 모든 숫자 허용)
                if unit_price != '' and unit_price is not None:
                    from decimal import Decimal, InvalidOperation
                    try:
                        # "0", "0.0", 0 모두 Decimal로 변환
                        delivery_item.unit_price = Decimal(str(unit_price))
                    except (ValueError, InvalidOperation):
                        # 변환 실패 시 None으로 유지
                        pass
                # unit_price가 '' 또는 None이면 unit_price 필드는 None으로 유지
                if discount_rate != '' and discount_rate is not None:
                    from decimal import Decimal, InvalidOperation
                    try:
                        delivery_item.discount_rate = Decimal(str(discount_rate))
                    except (ValueError, InvalidOperation):
                        pass

                if discount_unit_price != '' and discount_unit_price is not None:
                    from decimal import Decimal, InvalidOperation
                    try:
                        delivery_item.discount_unit_price = Decimal(str(discount_unit_price))
                    except (ValueError, InvalidOperation):
                        pass

                delivery_item.notes = notes
                delivery_item.option_description = option_description
                
                delivery_item.save()
                created_count += 1
            except (ValueError, TypeError) as e:
                logger.error(f"납품 품목 저장 실패: {e}")
                continue  # 잘못된 데이터는 무시
    
    return created_count

# 권한 체크 데코레이터
def role_required(allowed_roles):
    """특정 역할을 가진 사용자만 접근할 수 있도록 하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('reporting:login')
            
            try:
                user_profile = request.user.userprofile
                if user_profile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, '이 페이지에 접근할 권한이 없습니다.')
                    return redirect('reporting:dashboard')
            except UserProfile.DoesNotExist:
                messages.error(request, '사용자 프로필이 설정되지 않았습니다. 관리자에게 문의하세요.')
                return redirect('reporting:dashboard')
        return wrapper
    return decorator

def get_user_profile(user):
    """사용자 프로필을 가져오는 헬퍼 함수"""
    try:
        return user.userprofile
    except UserProfile.DoesNotExist:
        # 프로필이 없는 경우 기본 salesman 권한으로 생성
        return UserProfile.objects.create(user=user, role='salesman')

def can_access_user_data(request_user, target_user):
    """현재 사용자가 대상 사용자의 데이터에 접근할 수 있는지 확인"""
    # 자기 자신의 데이터는 항상 접근 가능
    if request_user == target_user:
        return True
    
    user_profile = get_user_profile(request_user)
    target_profile = get_user_profile(target_user)
    
    # Admin은 모든 데이터 접근 가능
    if user_profile.is_admin():
        return True
    
    # 같은 회사 소속이면 조회 가능 (Salesman, Manager 모두)
    if user_profile.company and target_profile.company:
        if user_profile.company == target_profile.company:
            return True
    
    return False

# 파일 업로드 관련 헬퍼 함수들
def validate_file_upload(file):
    """업로드된 파일의 유효성을 검사"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
        '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar',
        '.hwp', '.hwpx',
    ]

    # 파일 크기 검사
    if file.size > MAX_FILE_SIZE:
        return False, f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 업로드 가능합니다."

    # 파일 확장자 검사
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"지원하지 않는 파일 형식입니다. 허용된 확장자: {', '.join(ALLOWED_EXTENSIONS)}"

    # MIME 매직 바이트 검사 (확장자 위장 방지)
    # 파일 포인터를 앞부분으로 이동 후 검사, 마지막에 원위치
    MIME_SIGNATURES = [
        (b'%PDF',           ['.pdf']),
        (b'PK\x03\x04',    ['.docx', '.xlsx', '.pptx', '.zip', '.hwpx']),  # ZIP 계열
        (b'\xff\xd8\xff',  ['.jpg', '.jpeg']),
        (b'\x89PNG\r\n',   ['.png']),
        (b'GIF87a',        ['.gif']),
        (b'GIF89a',        ['.gif']),
        (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE2 구형 MS Office
                            ['.doc', '.xls', '.ppt', '.hwp']),
        (b'Rar!',          ['.rar']),
    ]
    SKIP_MAGIC_EXTENSIONS = ['.txt', '.hwp', '.hwpx', '.rar']  # 매직 검사 제외 (다양한 형식)

    if file_extension not in SKIP_MAGIC_EXTENSIONS:
        try:
            file.seek(0)
            header = file.read(16)
            file.seek(0)

            magic_ok = False
            for signature, allowed_exts in MIME_SIGNATURES:
                if header.startswith(signature):
                    if file_extension in allowed_exts:
                        magic_ok = True
                    else:
                        return False, "파일 형식이 확장자와 일치하지 않습니다."
                    break

            if not magic_ok and header:
                # 알 수 없는 시그니처 — txt나 단순 텍스트는 허용, 나머지는 차단
                if file_extension not in ['.txt']:
                    return False, "파일 형식을 확인할 수 없습니다."
        except Exception:
            # seek 불가 파일(InMemoryUploadedFile 오류 등)은 확장자 검사만으로 통과
            pass

    return True, "유효한 파일입니다."


def can_modify_user_data(request_user, target_user):
    """현재 사용자가 대상 사용자의 데이터를 수정/추가/삭제할 수 있는지 확인"""
    user_profile = get_user_profile(request_user)
    
    # Admin은 모든 데이터 수정 가능
    if user_profile.is_admin():
        return True
    
    # Manager는 읽기만 가능하고 수정 불가
    if user_profile.is_manager():
        return False
    
    # Salesman은 자신의 데이터만 수정 가능
    return request_user == target_user


def manager_core_readonly_message(noun='데이터'):
    return f'Manager 계정은 {noun}를 등록/수정/삭제할 수 없습니다.'


def can_access_followup(request_user, followup):
    """
    고객(FollowUp) 접근 권한 확인
    - 같은 회사(UserCompany) 소속이면 고객 정보 조회 가능
    - 단, 스케줄/히스토리 기록은 본인 것만 접근 가능
    """
    user_profile = get_user_profile(request_user)
    
    # Admin은 모든 데이터 접근 가능
    if user_profile.is_admin():
        return True
    
    # 같은 회사 소속인지 확인
    if user_profile.company and followup.user:
        target_profile = get_user_profile(followup.user)
        if target_profile.company and user_profile.company == target_profile.company:
            return True
    
    # 자신이 추가한 고객은 당연히 접근 가능
    return request_user == followup.user


def get_same_company_users(request_user):
    """같은 회사(UserCompany) 소속 사용자 목록 반환"""
    user_profile = get_user_profile(request_user)
    
    # Admin은 모든 사용자
    if user_profile.is_admin():
        return User.objects.filter(is_active=True)
    
    # 회사가 있으면 같은 회사 사용자들
    if user_profile.company:
        return User.objects.filter(
            is_active=True,
            userprofile__company=user_profile.company
        )
    
    # 회사가 없으면 자기 자신만
    return User.objects.filter(id=request_user.id)


def get_accessible_users(request_user, request=None):
    """
    현재 사용자가 접근할 수 있는 사용자 목록을 반환
    
    Args:
        request_user: 현재 로그인한 사용자
        request: HTTP request 객체 (관리자 필터 확인용)
        
    Returns:
        QuerySet: 접근 가능한 사용자 목록
    """
    user_profile = get_user_profile(request_user)
    
    if user_profile.is_admin():
        # 관리자: 필터링 적용
        if request and hasattr(request, 'admin_filter_user') and request.admin_filter_user:
            # 특정 사용자 선택됨
            return User.objects.filter(id=request.admin_filter_user.id)
        elif request and hasattr(request, 'admin_filter_company') and request.admin_filter_company:
            # 특정 회사 선택됨 - 해당 회사의 모든 실무자
            return User.objects.filter(
                userprofile__company=request.admin_filter_company,
                userprofile__role__in=['salesman', 'manager']
            )
        else:
            # 전체 접근
            return User.objects.all()
            
    elif user_profile.company:
        # Manager와 Salesman 모두 같은 회사의 모든 사용자에 접근 가능
        user_company = user_profile.company
        accessible_profiles = UserProfile.objects.filter(
            role__in=['salesman', 'manager'],
            company=user_company
        )
        return User.objects.filter(userprofile__in=accessible_profiles)
    else:
        # 회사 정보가 없는 경우 자기 자신만 접근 가능
        return User.objects.filter(id=request_user.id)


def get_accessible_products(request):
    """현재 사용자가 조회/선택할 수 있는 활성 제품 목록."""
    from reporting.models import Product

    user_profile = get_user_profile(request.user)
    if user_profile.is_admin():
        return Product.objects.filter(is_active=True)

    if user_profile.company:
        accessible_users = get_accessible_users(request.user, request)
        return Product.objects.filter(
            is_active=True,
        ).filter(
            Q(created_by__in=accessible_users) | Q(created_by__isnull=True)
        )

    return Product.objects.filter(
        is_active=True,
    ).filter(
        Q(created_by=request.user) | Q(created_by__isnull=True)
    )


    


# 여기에 앞으로 팔로우업 상세, 생성, 수정, 삭제 등의 뷰 함수를 추가할 예정입니다.


def _api_login_required_response(request):
    return api_login_required_or_readonly_response(request)


@never_cache
@require_http_methods(["GET"])
def navigation_api(request):
    """React CRM navigation configuration for authenticated users."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    profile = get_user_profile(request.user)
    company = profile.company if profile else None

    items = [
        {'id': 'dashboard', 'label': '대시보드', 'href': '/dashboard/'},
        {'id': 'customers', 'label': '고객', 'href': '/customers/'},
        {'id': 'companies', 'label': '업체/부서', 'href': '/companies/'},
        {'id': 'demos', 'label': '데모관리', 'href': '/demos/'},
        {'id': 'pipeline', 'label': '파이프라인', 'href': '/pipeline/'},
        {'id': 'pipelineSheet', 'label': '파이프라인 시트', 'href': '/pipeline-sheet/'},
        {'id': 'pipelineMeeting', 'label': '아침회의', 'href': '/pipeline-meeting/'},
        {'id': 'notes', 'label': '영업노트', 'href': '/notes/'},
        {'id': 'schedules', 'label': '일정', 'href': '/schedules/calendar/'},
    ]
    if profile.role == 'manager':
        items.append({'id': 'employees', 'label': '직원관리', 'href': '/employees/'})
    if profile.role == 'admin':
        items.append({'id': 'userAdmin', 'label': '사용자관리', 'href': '/employees/'})
    items.extend([
        {'id': 'documents', 'label': '서류', 'href': '/documents/'},
        {'id': 'products', 'label': '제품', 'href': '/products/'},
        {'id': 'receivables', 'label': '외상고객', 'href': '/receivables/'},
        {'id': 'prepayments', 'label': '선결제', 'href': '/prepayments/'},
        {'id': 'profile', 'label': '프로필', 'href': '/profile/'},
    ])

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'currentUser': {
            'id': request.user.id,
            'name': _user_display_name(request.user),
            'username': request.user.username,
            'role': profile.role,
            'roleLabel': profile.get_role_display(),
            'company': company.name if company else '',
            'canUseAi': bool(profile.can_use_ai),
        },
        'capabilities': {
            'canManageEmployees': profile.role in ['admin', 'manager'],
            'canManageUsers': profile.role == 'admin',
            'canManageCompanies': profile.role != 'manager',
            'canUseAi': bool(profile.can_use_ai),
            'canViewAllUsers': bool(profile.can_view_all_users()),
        },
        'items': items,
    })


@never_cache
@require_http_methods(["GET"])
def employees_management_api(request):
    """React user/employee management list API for admin and manager roles."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    profile = get_user_profile(request.user)
    if not (profile.is_admin() or profile.is_manager()):
        return JsonResponse({
            'success': False,
            'source': 'django',
            'error': 'management_required',
            'message': '사용자/직원 관리는 Admin 또는 Manager 계정만 사용할 수 있습니다.',
        }, status=403)
    if profile.is_manager() and not profile.company_id:
        return JsonResponse({
            'success': False,
            'source': 'django',
            'error': 'company_required',
            'message': '소속 회사 정보가 없어 직원관리를 사용할 수 없습니다.',
        }, status=400)

    search_query = (request.GET.get('q') or request.GET.get('search') or '').strip()
    role_filter = (request.GET.get('role') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    company_filter = (request.GET.get('company') or request.GET.get('company_id') or '').strip()
    valid_roles = {'admin', 'manager', 'salesman'} if profile.is_admin() else {'manager', 'salesman'}
    valid_statuses = {'active', 'inactive'}

    users = User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by').filter(
        userprofile__role__in=valid_roles,
    )
    if profile.is_manager():
        users = users.filter(userprofile__company=profile.company)
    elif company_filter.isdigit():
        users = users.filter(userprofile__company_id=int(company_filter))
    else:
        company_filter = ''
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(userprofile__company__name__icontains=search_query)
        )
    if role_filter in valid_roles:
        users = users.filter(userprofile__role=role_filter)
    else:
        role_filter = ''
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    else:
        status_filter = ''

    total_count = users.count()
    active_count = users.filter(is_active=True).count()
    admin_count = users.filter(userprofile__role='admin').count() if profile.is_admin() else 0
    manager_count = users.filter(userprofile__role='manager').count()
    salesman_count = users.filter(userprofile__role='salesman').count()
    users = users.order_by('userprofile__company__name', 'userprofile__role', 'last_name', 'first_name', 'username')

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'canManage': True,
            'mode': 'admin' if profile.is_admin() else 'manager',
            'companyId': profile.company_id,
            'companyName': profile.company.name if profile.company else '',
            'label': '전체 사용자관리' if profile.is_admin() else f'{profile.company.name} 직원관리',
            'canCreate': True,
            'canUpdate': True,
            'canDeactivate': True,
            'canChangeRole': profile.is_admin(),
            'canChangeCompany': profile.is_admin(),
            'canChangeAi': profile.is_admin(),
            'canChangePassword': True,
            'canDelete': False,
        },
        'filters': {
            'q': search_query,
            'role': role_filter,
            'status': status_filter,
            'company': company_filter,
        },
        'metrics': {
            'totalEmployees': total_count,
            'activeEmployees': active_count,
            'inactiveEmployees': max(total_count - active_count, 0),
            'adminCount': admin_count,
            'managerCount': manager_count,
            'salesmanCount': salesman_count,
        },
        'options': {
            'roles': [
                {'value': '', 'label': '전체 권한'},
                *([{'value': 'admin', 'label': 'Admin'}] if profile.is_admin() else []),
                {'value': 'manager', 'label': 'Manager'},
                {'value': 'salesman', 'label': 'SalesMan'},
            ],
            'statuses': [
                {'value': '', 'label': '전체 상태'},
                {'value': 'active', 'label': '활성'},
                {'value': 'inactive', 'label': '비활성'},
            ],
            'companies': [
                {'id': company.id, 'name': company.name}
                for company in UserCompany.objects.order_by('name')
            ] if profile.is_admin() else [
                {'id': profile.company_id, 'name': profile.company.name}
            ],
        },
        'links': {
            'listApi': reverse('reporting:employees_management_api'),
            'createApi': reverse('reporting:employees_create_api'),
            'djangoList': reverse('reporting:user_list') if profile.is_admin() else reverse('reporting:manager_user_list'),
            'create': reverse('reporting:user_create') if profile.is_admin() else reverse('reporting:manager_user_create'),
        },
        'employees': [
            _employee_management_payload(user, request.user)
            for user in users
        ],
    })


def _employees_parse_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}'), None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}, '잘못된 요청 형식입니다.'
    return request.POST, None


def _employee_bool_value(payload, *keys, default=False):
    for key in keys:
        if hasattr(payload, 'get') and key in payload:
            value = payload.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {'true', '1', 'yes', 'on'}:
                    return True
                if lowered in {'false', '0', 'no', 'off'}:
                    return False
            return bool(value)
    return default


def _employee_text_value(payload, *keys):
    for key in keys:
        value = payload.get(key) if hasattr(payload, 'get') else None
        if value is not None:
            return str(value).strip()
    return ''


def _employee_company_from_payload(payload, *, required=False):
    company_id = _employee_text_value(payload, 'companyId', 'company_id', 'company')
    company_name = _employee_text_value(payload, 'companyName', 'company_name')
    if company_id.isdigit():
        company = UserCompany.objects.filter(id=int(company_id)).first()
        if company:
            return company, None
        return None, '선택한 회사를 찾을 수 없습니다.'
    if company_id and not company_name:
        company_name = company_id
    if company_name:
        return UserCompany.objects.get_or_create(name=company_name)[0], None
    if required:
        return None, '소속 회사를 입력하세요.'
    return None, None


def _employee_manage_profile(user):
    return get_user_profile(user)


def _employee_target_for_manager(actor, target_id):
    actor_profile = _employee_manage_profile(actor)
    if actor_profile.is_admin():
        return get_object_or_404(
            User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by'),
            id=target_id,
        )
    if actor_profile.is_manager() and actor_profile.company_id:
        return get_object_or_404(
            User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by'),
            id=target_id,
            userprofile__company=actor_profile.company,
            userprofile__role__in=['manager', 'salesman'],
        )
    raise Http404


def _employee_can_update(actor, target):
    actor_profile = _employee_manage_profile(actor)
    if actor_profile.is_admin():
        return True
    if actor_profile.is_manager():
        target_profile = _employee_manage_profile(target)
        return bool(
            actor_profile.company_id
            and target_profile.company_id == actor_profile.company_id
            and target_profile.role in ['manager', 'salesman']
            and target.id != actor.id
        )
    return False


def _employee_management_payload(user, actor):
    actor_profile = _employee_manage_profile(actor)
    user_profile = _employee_manage_profile(user)
    is_admin_actor = actor_profile.is_admin()
    can_update = _employee_can_update(actor, user)
    can_toggle = can_update and user.id != actor.id
    company = user_profile.company
    return {
        'id': user.id,
        'username': user.username,
        'name': _user_display_name(user),
        'firstName': user.first_name,
        'lastName': user.last_name,
        'email': user.email,
        'role': user_profile.role,
        'roleLabel': user_profile.get_role_display(),
        'companyId': company.id if company else None,
        'company': company.name if company else '',
        'isActive': bool(user.is_active),
        'canDownloadExcel': bool(user_profile.can_download_excel),
        'canUseAi': bool(user_profile.can_use_ai),
        'lastLogin': _datetime_or_none(user.last_login),
        'dateJoined': _datetime_or_none(user.date_joined),
        'createdByName': _user_display_name(user_profile.created_by) if user_profile.created_by_id else '',
        'createdAt': _datetime_or_none(user_profile.created_at),
        'editHref': f'/employees/?employee={user.id}&edit=1' if can_update else '',
        'updateHref': reverse('reporting:employees_update_api', args=[user.id]) if can_update else '',
        'toggleActiveHref': reverse('reporting:employees_toggle_active_api', args=[user.id]) if can_toggle else '',
        'canUpdate': can_update,
        'canToggleActive': can_toggle,
        'canChangeRole': can_update and is_admin_actor,
        'canChangeCompany': can_update and is_admin_actor,
        'canChangeAi': can_update and is_admin_actor,
        'canChangePassword': can_update,
        'canDelete': False,
        'isCurrentUser': user.id == actor.id,
    }


@never_cache
@require_http_methods(["POST"])
def employees_create_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    actor_profile = _employee_manage_profile(request.user)
    if not (actor_profile.is_admin() or actor_profile.is_manager()):
        return JsonResponse({'success': False, 'error': '사용자 생성 권한이 없습니다.'}, status=403)
    if actor_profile.is_manager() and not actor_profile.company_id:
        return JsonResponse({'success': False, 'error': '소속 회사 정보가 없습니다.'}, status=400)

    payload, error = _employees_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    username = _employee_text_value(payload, 'username')
    password = _employee_text_value(payload, 'password', 'password1')
    password_confirm = _employee_text_value(payload, 'passwordConfirm', 'password2')
    if not username:
        return JsonResponse({'success': False, 'error': '사용자 ID를 입력하세요.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': f'사용자 ID "{username}"은 이미 사용 중입니다.'}, status=400)
    if not password:
        return JsonResponse({'success': False, 'error': '비밀번호를 입력하세요.'}, status=400)
    if password_confirm and password != password_confirm:
        return JsonResponse({'success': False, 'error': '비밀번호가 일치하지 않습니다.'}, status=400)

    if actor_profile.is_manager():
        role = 'salesman'
        company = actor_profile.company
        can_use_ai = False
    else:
        role = _employee_text_value(payload, 'role') or 'salesman'
        if role not in {'admin', 'manager', 'salesman'}:
            return JsonResponse({'success': False, 'error': '올바른 권한을 선택하세요.'}, status=400)
        company, company_error = _employee_company_from_payload(payload, required=role != 'admin')
        if company_error:
            return JsonResponse({'success': False, 'error': company_error}, status=400)
        can_use_ai = _employee_bool_value(payload, 'canUseAi', 'can_use_ai')

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=_employee_text_value(payload, 'email'),
            password=password,
            first_name=_employee_text_value(payload, 'firstName', 'first_name'),
            last_name=_employee_text_value(payload, 'lastName', 'last_name'),
        )
        UserProfile.objects.create(
            user=user,
            company=company,
            role=role,
            can_download_excel=_employee_bool_value(payload, 'canDownloadExcel', 'can_download_excel'),
            can_use_ai=can_use_ai,
            created_by=request.user,
        )

    user = User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by').get(pk=user.pk)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'사용자 "{user.username}"을(를) 생성했습니다.',
        'employee': _employee_management_payload(user, request.user),
    }, status=201)


@never_cache
@require_http_methods(["POST"])
def employees_update_api(request, user_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    target = _employee_target_for_manager(request.user, user_id)
    if not _employee_can_update(request.user, target):
        return JsonResponse({'success': False, 'error': '사용자 수정 권한이 없습니다.'}, status=403)

    actor_profile = _employee_manage_profile(request.user)
    target_profile = _employee_manage_profile(target)
    payload, error = _employees_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    username = _employee_text_value(payload, 'username') or target.username
    if User.objects.filter(username=username).exclude(pk=target.pk).exists():
        return JsonResponse({'success': False, 'error': f'사용자 ID "{username}"은 이미 사용 중입니다.'}, status=400)

    password = _employee_text_value(payload, 'password', 'password1')
    password_confirm = _employee_text_value(payload, 'passwordConfirm', 'password2')
    if password_confirm and password and password != password_confirm:
        return JsonResponse({'success': False, 'error': '비밀번호가 일치하지 않습니다.'}, status=400)

    target.username = username
    target.email = _employee_text_value(payload, 'email') if 'email' in payload else target.email
    target.first_name = _employee_text_value(payload, 'firstName', 'first_name') if any(key in payload for key in ['firstName', 'first_name']) else target.first_name
    target.last_name = _employee_text_value(payload, 'lastName', 'last_name') if any(key in payload for key in ['lastName', 'last_name']) else target.last_name
    if password:
        target.set_password(password)
    if any(key in payload for key in ['isActive', 'is_active']):
        requested_active = _employee_bool_value(payload, 'isActive', 'is_active', default=target.is_active)
        if target.id == request.user.id and not requested_active:
            return JsonResponse({'success': False, 'error': '자기 자신의 계정은 비활성화할 수 없습니다.'}, status=400)
        target.is_active = requested_active

    if actor_profile.is_admin():
        role = _employee_text_value(payload, 'role') or target_profile.role
        if role not in {'admin', 'manager', 'salesman'}:
            return JsonResponse({'success': False, 'error': '올바른 권한을 선택하세요.'}, status=400)
        company, company_error = _employee_company_from_payload(payload, required=role != 'admin')
        if company_error:
            return JsonResponse({'success': False, 'error': company_error}, status=400)
        if company is not None or role == 'admin':
            target_profile.company = company
        target_profile.role = role
        target_profile.can_use_ai = _employee_bool_value(payload, 'canUseAi', 'can_use_ai', default=target_profile.can_use_ai)
    target_profile.can_download_excel = _employee_bool_value(
        payload,
        'canDownloadExcel',
        'can_download_excel',
        default=target_profile.can_download_excel,
    )

    with transaction.atomic():
        target.save()
        target_profile.save()

    target = User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by').get(pk=target.pk)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'사용자 "{target.username}" 정보를 수정했습니다.',
        'employee': _employee_management_payload(target, request.user),
    })


@never_cache
@require_http_methods(["POST"])
def employees_toggle_active_api(request, user_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    target = _employee_target_for_manager(request.user, user_id)
    if not _employee_can_update(request.user, target):
        return JsonResponse({'success': False, 'error': '사용자 상태 변경 권한이 없습니다.'}, status=403)
    if target.id == request.user.id:
        return JsonResponse({'success': False, 'error': '자기 자신의 계정은 비활성화할 수 없습니다.'}, status=400)

    payload, error = _employees_parse_payload(request)
    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)
    if any(key in payload for key in ['isActive', 'is_active']):
        target.is_active = _employee_bool_value(payload, 'isActive', 'is_active', default=target.is_active)
    else:
        target.is_active = not target.is_active
    target.save(update_fields=['is_active'])

    target = User.objects.select_related('userprofile', 'userprofile__company', 'userprofile__created_by').get(pk=target.pk)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '사용자를 활성화했습니다.' if target.is_active else '사용자를 비활성화했습니다.',
        'employee': _employee_management_payload(target, request.user),
    })


def _dashboard_scope_users(request, user_profile):
    """React dashboard API에서 사용할 사용자 범위를 기존 대시보드 규칙으로 계산."""
    user_filter = request.GET.get('user') or request.session.get('selected_user_id')
    view_all = request.GET.get('view_all') == 'true'
    selected_user = None

    if user_profile.is_admin():
        if hasattr(request, 'admin_filter_user') and request.admin_filter_user:
            users = User.objects.filter(id=request.admin_filter_user.id)
            selected_user = request.admin_filter_user
        elif hasattr(request, 'admin_filter_company') and request.admin_filter_company:
            users = User.objects.filter(
                userprofile__company=request.admin_filter_company,
                userprofile__role__in=['salesman', 'manager'],
                is_active=True,
            )
        elif user_filter and not view_all:
            try:
                selected_user = User.objects.get(id=user_filter, is_active=True)
                users = User.objects.filter(id=selected_user.id)
            except (User.DoesNotExist, ValueError):
                users = User.objects.filter(is_active=True)
        else:
            users = User.objects.filter(is_active=True)
    elif user_profile.can_view_all_users():
        users = get_accessible_users(request.user, request).filter(is_active=True)
        if user_filter and not view_all:
            selected_user = users.filter(id=user_filter).first()
            if selected_user:
                users = users.filter(id=selected_user.id)
    else:
        users = User.objects.filter(id=request.user.id)

    return users.select_related('userprofile'), selected_user


def _user_display_name(user):
    return user.get_full_name() or user.username


_HANGUL_NAME_PART_RE = re.compile(r'^[가-힣]+$')
_KOREAN_COMPOUND_SURNAMES = {
    '남궁', '황보', '제갈', '사공', '선우', '서문', '독고', '동방',
}


def _is_hangul_name_part(value):
    return bool(value and _HANGUL_NAME_PART_RE.match(value))


def _document_salesperson_name(user):
    first_name = (user.first_name or '').strip()
    last_name = (user.last_name or '').strip()

    if first_name and last_name:
        first_looks_like_surname = (
            _is_hangul_name_part(first_name)
            and _is_hangul_name_part(last_name)
            and (len(first_name) == 1 or first_name in _KOREAN_COMPOUND_SURNAMES)
            and len(last_name) >= 2
        )
        last_looks_like_surname = (
            _is_hangul_name_part(first_name)
            and _is_hangul_name_part(last_name)
            and (len(last_name) == 1 or last_name in _KOREAN_COMPOUND_SURNAMES)
            and len(first_name) >= 2
        )

        if first_looks_like_surname and not last_looks_like_surname:
            return f'{first_name}{last_name}'
        if last_looks_like_surname:
            return f'{last_name}{first_name}'
        return f'{last_name}{first_name}'

    return first_name or last_name or user.username


def _date_or_none(value):
    return value.isoformat() if value else None


def _datetime_or_none(value):
    return timezone.localtime(value).isoformat() if value else None


def _money_int(value):
    return int(value or 0)


def _dashboard_schedule_payload(schedule):
    followup = schedule.followup
    department = schedule.department or (followup.department if followup and followup.department else None)
    company = followup.company if followup and followup.company else (department.company if department and department.company else None)
    customer = (
        followup.customer_name or followup.manager or '고객명 미정'
    ) if followup else '담당자 미등록'
    customer_href = f'/customers/{followup.id}/' if followup else (f'/accounts/{department.id}/' if department else '')
    return {
        'id': schedule.id,
        'type': 'schedule',
        'customer': customer,
        'company': company.name if company else '',
        'department': department.name if department else '',
        'owner': _user_display_name(schedule.user),
        'date': schedule.visit_date.isoformat(),
        'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '',
        'activityType': schedule.activity_type,
        'activityLabel': schedule.get_activity_type_display(),
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'notes': (schedule.notes or '').strip()[:120],
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
        'customerHref': customer_href,
        'djangoCustomerHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
    }


def _dashboard_personal_schedule_payload(schedule):
    return {
        'id': schedule.id,
        'type': 'personal',
        'customer': schedule.title,
        'company': schedule.company.name if schedule.company else '',
        'department': '',
        'owner': _user_display_name(schedule.user),
        'date': schedule.schedule_date.isoformat(),
        'time': schedule.schedule_time.strftime('%H:%M') if schedule.schedule_time else '',
        'activityType': 'personal',
        'activityLabel': '개인 일정',
        'status': 'personal',
        'statusLabel': '개인 일정',
        'notes': (schedule.content or '').strip()[:120],
        'href': reverse('reporting:personal_schedule_detail', args=[schedule.id]),
        'djangoHref': reverse('reporting:personal_schedule_detail', args=[schedule.id]),
        'customerHref': '',
        'djangoCustomerHref': '',
    }


def _dashboard_history_payload(history):
    followup = history.followup
    department = history.department or (followup.department if followup and followup.department else None)
    company = followup.company if followup and followup.company else (department.company if department and department.company else None)
    customer = (
        followup.customer_name or followup.manager or '고객명 미정'
    ) if followup else ('담당자 미등록' if department else '일반 메모')
    return {
        'id': history.id,
        'customer': customer,
        'company': company.name if company else '',
        'department': department.name if department else '',
        'owner': _user_display_name(history.user),
        'actionType': history.action_type,
        'actionLabel': history.get_action_type_display(),
        'summary': (
            history.next_action or history.meeting_next_action or history.content or ''
        ).strip()[:140],
        'nextAction': (history.next_action or history.meeting_next_action or '').strip()[:140],
        'nextActionDate': _date_or_none(history.next_action_date),
        'createdAt': _datetime_or_none(history.created_at),
        'reviewed': bool(history.reviewed_at),
        'href': reverse('reporting:history_detail', args=[history.id]),
        'customerHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else (f'/accounts/{department.id}/' if department else ''),
    }


def _history_requests_quote_submission(history):
    action_text = ' '.join(
        str(value or '')
        for value in [history.next_action, history.meeting_next_action]
    )
    compact = re.sub(r'\s+', '', action_text).lower()
    if not compact:
        return False

    has_quote_document = any(keyword in compact for keyword in ['견적서', '견적', '비교표'])
    has_submission_action = any(
        keyword in compact
        for keyword in ['제출', '발송', '송부', '전달', '보내', '보냈', '메일발송']
    )
    checks_after_submission = any(
        keyword in compact
        for keyword in ['회신', '답장', '검토', '의사결정', '구매', '결재']
    )
    explicit_submission_check = any(
        phrase in compact
        for phrase in ['제출여부', '발송여부', '송부여부', '전달여부']
    )
    if checks_after_submission and not explicit_submission_check:
        return False
    return has_quote_document and has_submission_action


def _history_has_quote_submission_evidence(history):
    if not history or not history.followup_id or not history.user_id:
        return False
    if not _history_requests_quote_submission(history):
        return False

    created_at = history.created_at
    quote_qs = Quote.objects.filter(
        followup_id=history.followup_id,
    ).filter(
        Q(user_id=history.user_id) | Q(schedule__user_id=history.user_id)
    ).exclude(stage__in=['draft', 'rejected', 'expired'])
    if created_at:
        quote_qs = quote_qs.filter(created_at__gte=created_at)
    if quote_qs.exists():
        return True

    document_qs = DocumentGenerationLog.objects.filter(
        schedule__followup_id=history.followup_id,
        schedule__activity_type='quote',
        document_type='quotation',
    ).filter(
        Q(user_id=history.user_id) | Q(schedule__user_id=history.user_id)
    )
    if created_at:
        document_qs = document_qs.filter(created_at__gte=created_at)
    if document_qs.exists():
        return True

    quote_history_qs = History.objects.filter(
        user_id=history.user_id,
        followup_id=history.followup_id,
        parent_history__isnull=True,
        action_type='quote',
    ).exclude(pk=history.pk)
    if created_at:
        quote_history_qs = quote_history_qs.filter(created_at__gte=created_at)
    return quote_history_qs.exists()


def _histories_excluding_stale_quote_submission(histories):
    return [
        history for history in histories
        if not _history_has_quote_submission_evidence(history)
    ]


def _dashboard_followup_payload(followup, latest_history=None, overdue=False):
    return {
        'id': followup.id,
        'customer': followup.customer_name or followup.manager or '고객명 미정',
        'company': followup.company.name if followup.company else '',
        'department': followup.department.name if followup.department else '',
        'owner': _user_display_name(followup.user),
        'priority': followup.priority,
        'priorityLabel': followup.get_priority_display(),
        'status': followup.status,
        'statusLabel': followup.get_status_display(),
        'pipelineStage': followup.pipeline_stage,
        'pipelineLabel': followup.get_pipeline_stage_display(),
        'grade': followup.customer_grade or '',
        'score': float(followup.get_combined_score()),
        'overdue': overdue,
        'lastActivity': _datetime_or_none(latest_history.created_at) if latest_history else None,
        'nextAction': (
            latest_history.next_action or latest_history.meeting_next_action or ''
        ).strip()[:140] if latest_history else '',
        'nextActionDate': _date_or_none(latest_history.next_action_date) if latest_history else None,
        'href': reverse('reporting:followup_detail', args=[followup.id]),
    }


# ----------------------------------------------------------------- 실매출 집계
# 매출은 "완료된 납품 일정 하나당 한 번"만 센다. 금액을 어디서 읽을지는 아래
# 우선순위 체인을 따른다 — 이 저장소의 실제 업무 규칙이라 단순화하면 안 된다.
#
#     일정에 달린 납품품목 → 그 일정에 달린 납품노트의 품목
#                          → 납품노트의 delivery_amount → 일정의 expected_revenue
#
# 왜 체인이 필요한가(운영 데이터에 두 형태가 다 있다):
#   - 일정 177: 일정 품목 0원, 노트 품목 1,053,800원  → 노트에서 읽어야 안 놓친다.
#   - 일정 293: 일정 품목 6,735,300원, 노트 품목도 같은 6,735,300원(같은 납품을
#               양쪽에 적어둔 것) → 더하면 이중계상. 그래서 "먼저 잡히는 하나"만 쓴다.
#
# 어떤 일정을 납품으로 볼지도 activity_type 만으로 판단하지 않는다. 견적 일정에
# 품목을 넣고 납품노트를 달아 출고 처리한 건이 실제로 있다(일정 880/881, 72만원).
# 그래서 `activity_type='delivery'` 이거나 **납품노트가 달린** 완료 일정을 대상으로 한다.
#
# 파이프라인(`funnel_views._delivery_schedule_amount`)이 쓰는 규칙과 같은 것이며,
# 대시보드·매출 드릴다운이 모두 이 함수를 거쳐야 화면끼리 숫자가 갈라지지 않는다.

def delivered_schedule_ids(schedules):
    """`schedules` 중 매출로 볼 완료 일정 id 집합."""
    completed = schedules.filter(status='completed')
    ids = set(completed.filter(activity_type='delivery').values_list('id', flat=True))
    ids |= set(
        History.objects.filter(
            schedule__in=completed,
            action_type='delivery_schedule',
            parent_history__isnull=True,
        ).values_list('schedule_id', flat=True)
    )
    ids.discard(None)
    return ids


def delivered_schedule_amount(schedule):
    """일정 1건의 실매출 금액(위 우선순위 체인). 절대 두 소스를 더하지 않는다."""
    from decimal import Decimal

    item_total = sum(
        (item.total_price or Decimal('0'))
        for item in DeliveryItem.objects.filter(schedule=schedule)
    )
    if item_total > 0:
        return item_total
    for history in History.objects.filter(
        schedule=schedule,
        action_type='delivery_schedule',
        parent_history__isnull=True,
    ).order_by('-created_at'):
        history_items = sum(
            (item.total_price or Decimal('0'))
            for item in DeliveryItem.objects.filter(history=history)
        )
        if history_items > 0:
            return history_items
        if history.delivery_amount:
            return history.delivery_amount
    return schedule.expected_revenue or Decimal('0')


def delivered_revenue_rows(schedules):
    """[(일정, 금액)] — 금액이 0 보다 큰 완료 납품만."""
    ids = delivered_schedule_ids(schedules)
    if not ids:
        return []
    rows = []
    for schedule in Schedule.objects.filter(id__in=ids).select_related(
        'user', 'followup', 'followup__company', 'followup__department',
        'department', 'department__company',
    ):
        amount = delivered_schedule_amount(schedule)
        if amount > 0:
            rows.append((schedule, amount))
    return rows


@never_cache
@require_http_methods(["GET"])
def dashboard_summary_api(request):
    """React CRM dashboard용 읽기 전용 요약 API."""
    from collections import Counter
    from datetime import timedelta
    from django.db.models import Case, IntegerField, Value, When
    from reporting.models import PersonalSchedule

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()
    week_end = today + timedelta(days=6)
    year_start = date(today.year, 1, 1)
    next_year_start = date(today.year + 1, 1, 1)
    quarter = ((today.month - 1) // 3) + 1
    quarter_start_month = ((quarter - 1) * 3) + 1
    quarter_start = date(today.year, quarter_start_month, 1)
    if quarter_start_month == 10:
        quarter_end = date(today.year + 1, 1, 1)
    else:
        quarter_end = date(today.year, quarter_start_month + 3, 1)
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1)
    else:
        month_end = date(today.year, today.month + 1, 1)

    followups = FollowUp.objects.filter(user__in=scope_users)
    schedules = Schedule.objects.filter(user__in=scope_users)
    histories = History.objects.filter(user__in=scope_users, parent_history__isnull=True)
    personal_schedules = PersonalSchedule.objects.filter(user__in=scope_users)

    today_business_schedules_qs = schedules.filter(
        visit_date=today,
    ).exclude(status='cancelled')
    today_personal_qs = personal_schedules.filter(schedule_date=today)
    upcoming_business_schedules_qs = schedules.filter(
        visit_date__gt=today,
        visit_date__lte=week_end,
    ).exclude(status='cancelled')
    upcoming_personal_qs = personal_schedules.filter(
        schedule_date__gt=today,
        schedule_date__lte=week_end,
    )

    today_business_schedules = list(
        today_business_schedules_qs.select_related(
            'user', 'followup', 'followup__company', 'followup__department'
        ).order_by('visit_time')[:8]
    )
    today_personal = list(
        today_personal_qs.select_related('user', 'company').order_by('schedule_time')[:5]
    )
    upcoming_business_schedules = list(
        upcoming_business_schedules_qs.select_related(
            'user', 'followup', 'followup__company', 'followup__department'
        ).order_by('visit_date', 'visit_time')[:8]
    )
    upcoming_personal = list(
        upcoming_personal_qs.select_related('user', 'company').order_by('schedule_date', 'schedule_time')[:5]
    )

    overdue_actions_qs = histories.filter(
        next_action_date__lt=today,
        next_action_date__isnull=False,
        reviewed_at__isnull=True,
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department'
    ).order_by('next_action_date', '-created_at')
    due_today_actions_qs = histories.filter(
        next_action_date=today,
        reviewed_at__isnull=True,
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department'
    ).order_by('-created_at')
    recent_histories_qs = histories.exclude(action_type='memo').select_related(
        'user', 'followup', 'followup__company', 'followup__department'
    ).order_by('-created_at')

    overdue_actions_all = _histories_excluding_stale_quote_submission(list(overdue_actions_qs))
    due_today_actions_all = _histories_excluding_stale_quote_submission(list(due_today_actions_qs))
    overdue_actions = overdue_actions_all[:6]
    due_today_actions = due_today_actions_all[:6]
    recent_histories = list(recent_histories_qs[:8])
    overdue_followup_ids = {
        history.followup_id for history in overdue_actions_all[:100]
        if history.followup_id
    }

    priority_order = Case(
        When(priority='urgent', then=Value(0)),
        When(priority='followup', then=Value(1)),
        When(priority='scheduled', then=Value(2)),
        When(priority='long_term', then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )
    priority_followups = list(
        followups.filter(
            Q(priority__in=['urgent', 'followup']) |
            Q(customer_grade__in=['VIP', 'A']) |
            Q(id__in=overdue_followup_ids)
        ).select_related('user', 'company', 'department').annotate(
            priority_rank=priority_order
        ).order_by('priority_rank', '-ai_score', '-updated_at')[:6]
    )
    if not priority_followups:
        priority_followups = list(
            followups.filter(status='active').select_related(
                'user', 'company', 'department'
            ).annotate(priority_rank=priority_order).order_by(
                'priority_rank', '-ai_score', '-updated_at'
            )[:6]
        )

    latest_history_by_followup = {}
    for followup in priority_followups:
        latest_history_by_followup[followup.id] = followup.histories.filter(
            parent_history__isnull=True,
        ).exclude(action_type='memo').order_by('-created_at').first()

    pipeline_stage_labels = dict(FollowUp.PIPELINE_STAGE_CHOICES)
    pipeline_stage_order = ['potential', 'contact', 'quote', 'negotiation', 'won', 'lost']
    pipeline_counts = {
        item['pipeline_stage']: item['count']
        for item in followups.values('pipeline_stage').annotate(count=Count('id'))
    }
    pipeline_summary = [
        {
            'stage': stage,
            'label': pipeline_stage_labels.get(stage, stage),
            'count': pipeline_counts.get(stage, 0),
        }
        for stage in pipeline_stage_order
    ]

    thirty_days_ago = today - timedelta(days=30)
    pending_review_count = 0
    team_activity = []
    if user_profile.can_view_all_users():
        pending_review_count = histories.filter(
            action_type__in=['customer_meeting', 'delivery_schedule', 'quote', 'service'],
            reviewed_at__isnull=True,
            created_at__date__gte=thirty_days_ago,
        ).exclude(action_type='memo').count()
        team_users = list(scope_users.filter(userprofile__role='salesman')[:8])
        activity_counts = {
            item['user_id']: item['count']
            for item in histories.filter(
                user__in=team_users,
                created_at__date__gte=thirty_days_ago,
            ).exclude(action_type='memo').values('user_id').annotate(count=Count('id'))
        }
        team_overdue_histories = _histories_excluding_stale_quote_submission(list(
            histories.filter(
                user__in=team_users,
                next_action_date__lt=today,
                next_action_date__isnull=False,
                reviewed_at__isnull=True,
            ).exclude(action_type='memo')
        ))
        overdue_counts = Counter(history.user_id for history in team_overdue_histories)
        team_activity = [
            {
                'userId': user.id,
                'name': _user_display_name(user),
                'recentCount': activity_counts.get(user.id, 0),
                'overdueCount': overdue_counts.get(user.id, 0),
            }
            for user in team_users
        ]

    # 완료(completed)된 납품만 "실제 매출"로 센다 — 예정(scheduled)은 아직
    # 실제로 납품되지 않았으니 취소/변경될 수 있어 실매출이 아니다.
    #
    # 선결제는 매출에 넣지 않는다. 선결제는 받아둔 돈일 뿐이고, 매출이 되는
    # 순간은 그 돈으로 실제 납품이 나갈 때다 — 그 납품은 바로 위 완료 납품으로
    # 이미 잡힌다. 예전엔 선결제 등록액을 더해서 같은 돈이 입금 시점과 납품
    # 시점에 두 번 계상됐다. (`reporting/api/revenue_detail.py` 와 같은 기준을
    # 써야 대시보드 숫자와 드릴다운 내역이 어긋나지 않는다.)
    # 일정 1건당 한 번만, 우선순위 체인으로 금액을 읽는다(`delivered_revenue_rows`).
    revenue_rows = delivered_revenue_rows(schedules)

    def _revenue_between(start, end):
        return int(sum(
            amount
            for schedule, amount in revenue_rows
            if schedule.visit_date and start <= schedule.visit_date < end
        ))

    yearly_revenue = _revenue_between(year_start, next_year_start)
    quarterly_revenue = _revenue_between(quarter_start, quarter_end)
    monthly_revenue = _revenue_between(month_start, month_end)
    monthly_activity_count = histories.exclude(action_type='memo').filter(
        created_at__date__gte=month_start,
        created_at__date__lt=month_end,
    ).count()

    scope_user_count = scope_users.count()
    scope_label = '전체'
    if selected_user:
        scope_label = _user_display_name(selected_user)
    elif not user_profile.can_view_all_users():
        scope_label = _user_display_name(request.user)
    elif user_profile.company:
        scope_label = f'{user_profile.company.name} 팀'

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': scope_label,
            'userCount': scope_user_count,
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'currentUser': {
            'id': request.user.id,
            'name': _user_display_name(request.user),
            'role': user_profile.role,
            'roleLabel': user_profile.get_role_display(),
            'company': user_profile.company.name if user_profile.company else '',
        },
        'metrics': {
            'totalCustomers': followups.count(),
            'activeCustomers': followups.filter(status='active').count(),
            'todaySchedules': today_business_schedules_qs.count() + today_personal_qs.count(),
            'weeklySchedules': (
                today_business_schedules_qs.count() +
                today_personal_qs.count() +
                upcoming_business_schedules_qs.count() +
                upcoming_personal_qs.count()
            ),
            'overdueActions': len(overdue_actions_all),
            'dueTodayActions': len(due_today_actions_all),
            'recentNotes': histories.exclude(action_type='memo').count(),
            'pendingReviews': pending_review_count,
            'monthlyActivity': monthly_activity_count,
            'yearRevenue': _money_int(yearly_revenue),
            'quarterRevenue': _money_int(quarterly_revenue),
            'monthlyRevenue': _money_int(monthly_revenue),
        },
        'revenuePeriod': {
            'year': today.year,
            'quarter': quarter,
            'yearStart': year_start.isoformat(),
            'yearEnd': next_year_start.isoformat(),
            'quarterStart': quarter_start.isoformat(),
            'quarterEnd': quarter_end.isoformat(),
            'monthStart': month_start.isoformat(),
            'monthEnd': month_end.isoformat(),
        },
        'links': {
            'operationalDashboard': '/dashboard/',
            'createNote': '/notes/?create=1',
            'customers': '/customers/',
            'customerReport': reverse('reporting:customer_report'),
            'notes': '/notes/',
            'schedules': '/schedules/',
            'calendar': '/schedules/calendar/',
            'pipeline': '/pipeline/',
            'pendingReviews': '/notes/?review=unreviewed',
        },
        'today': {
            'date': today.isoformat(),
            'items': (
                [_dashboard_schedule_payload(schedule) for schedule in today_business_schedules] +
                [_dashboard_personal_schedule_payload(schedule) for schedule in today_personal]
            ),
        },
        'upcomingSchedules': [
            _dashboard_schedule_payload(schedule)
            for schedule in upcoming_business_schedules
        ] + [
            _dashboard_personal_schedule_payload(schedule)
            for schedule in upcoming_personal
        ],
        'overdueActions': [
            _dashboard_history_payload(history)
            for history in overdue_actions
        ],
        'dueTodayActions': [
            _dashboard_history_payload(history)
            for history in due_today_actions
        ],
        'recentActivities': [
            _dashboard_history_payload(history)
            for history in recent_histories
        ],
        'priorityCustomers': [
            _dashboard_followup_payload(
                followup,
                latest_history=latest_history_by_followup.get(followup.id),
                overdue=followup.id in overdue_followup_ids,
            )
            for followup in priority_followups
        ],
        'pipelineSummary': pipeline_summary,
        'teamActivity': team_activity,
    })


def _customers_schedule_payload(schedule):
    followup_id = schedule.followup_id
    return {
        'id': schedule.id,
        'date': _date_or_none(schedule.visit_date),
        'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '',
        'activityType': schedule.activity_type,
        'activityLabel': schedule.get_activity_type_display(),
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'location': schedule.location or '',
        'notes': (schedule.notes or '').strip()[:100],
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
        'createHistoryHref': f'/notes/?create=1&customer={followup_id}&schedule={schedule.id}',
        'djangoCreateHistoryHref': reverse('reporting:history_create_from_schedule', args=[schedule.id]),
    }


def _customers_department_search_text_map(departments, scope_users=None):
    department_ids = [department.id for department in departments if department and department.id]
    if not department_ids:
        return {}

    followups = FollowUp.objects.filter(department_id__in=department_ids)
    if scope_users is not None:
        followups = followups.filter(user__in=scope_users)

    search_map = {department_id: [] for department_id in department_ids}
    for row in followups.values('department_id', 'customer_name', 'manager', 'email', 'phone_number'):
        bucket = search_map.setdefault(row['department_id'], [])
        for term in [row.get('customer_name'), row.get('manager'), row.get('email'), row.get('phone_number')]:
            value = str(term or '').strip()
            if value and value not in bucket:
                bucket.append(value)
    return {
        department_id: ' '.join(terms)
        for department_id, terms in search_map.items()
    }


def _customers_enriched_queryset(queryset, today, priority_order, recent_histories_qs, upcoming_schedules_qs):
    activity_types = [
        value
        for value, _label in History.ACTION_CHOICES
        if value != 'memo'
    ]
    activity_filter = Q(
        histories__parent_history__isnull=True,
        histories__action_type__in=activity_types,
    )
    overdue_filter = Q(
        histories__parent_history__isnull=True,
        histories__next_action_date__lt=today,
        histories__next_action_date__isnull=False,
        histories__reviewed_at__isnull=True,
    )
    upcoming_schedule_filter = Q(
        schedules__status='scheduled',
        schedules__visit_date__gte=today,
    )
    return queryset.select_related('user', 'company', 'department').prefetch_related(
        Prefetch('histories', queryset=recent_histories_qs, to_attr='customer_recent_histories'),
        Prefetch('schedules', queryset=upcoming_schedules_qs, to_attr='customer_upcoming_schedules'),
    ).annotate(
        priority_rank=priority_order,
        activity_count=Count('histories', filter=activity_filter, distinct=True),
        schedule_count=Count('schedules', distinct=True),
        upcoming_schedule_count=Count('schedules', filter=upcoming_schedule_filter, distinct=True),
        overdue_action_count=Count('histories', filter=overdue_filter, distinct=True),
    )


def _customers_followup_payload(followup, today):
    recent_histories = list(getattr(followup, 'customer_recent_histories', []))
    latest_history = recent_histories[0] if recent_histories else None
    visible_histories = _histories_excluding_stale_quote_submission(recent_histories)
    latest_action_history = next(
        (
            history for history in visible_histories
            if (history.next_action or history.meeting_next_action) and not history.reviewed_at
        ),
        None,
    )
    next_action_date = latest_action_history.next_action_date if latest_action_history else None
    overdue_histories = [
        history for history in visible_histories
        if history.next_action_date
        and history.next_action_date < today
        and not history.reviewed_at
    ]
    upcoming_schedules = list(getattr(followup, 'customer_upcoming_schedules', []))
    upcoming_schedule = upcoming_schedules[0] if upcoming_schedules else None
    phone = followup.phone_number or ''
    email = followup.email or ''
    return {
        'id': followup.id,
        'customer': followup.customer_name or followup.manager or '고객명 미정',
        'company': followup.company.name if followup.company else '',
        'companyId': followup.company_id,
        'department': followup.department.name if followup.department else '',
        'departmentId': followup.department_id,
        'manager': followup.manager or '',
        'owner': _user_display_name(followup.user),
        'ownerId': followup.user_id,
        'priority': followup.priority,
        'priorityLabel': followup.get_priority_display(),
        'status': followup.status,
        'statusLabel': followup.get_status_display(),
        'pipelineStage': followup.pipeline_stage,
        'pipelineLabel': followup.get_pipeline_stage_display(),
        'grade': followup.customer_grade or '',
        'score': float(followup.get_combined_score()),
        'phone': phone,
        'email': email,
        'address': followup.address or '',
        'contactSummary': ' · '.join([item for item in [phone, email] if item]),
        'notes': (followup.notes or '').strip()[:140],
        'notesFull': followup.notes or '',
        'lastActivityAt': _datetime_or_none(latest_history.created_at) if latest_history else None,
        'lastActivityLabel': latest_history.get_action_type_display() if latest_history else '',
        'lastActivitySummary': (
            latest_history.content or latest_history.meeting_next_action or latest_history.next_action or ''
        ).strip()[:140] if latest_history else '',
        'nextAction': (
            latest_action_history.next_action or latest_action_history.meeting_next_action or ''
        ).strip()[:140] if latest_action_history else '',
        'nextActionDate': _date_or_none(next_action_date),
        'overdue': bool(next_action_date and next_action_date < today),
        'activityCount': int(getattr(followup, 'activity_count', 0) or 0),
        'scheduleCount': int(getattr(followup, 'schedule_count', 0) or 0),
        'upcomingScheduleCount': int(getattr(followup, 'upcoming_schedule_count', 0) or 0),
        'overdueActionCount': len(overdue_histories),
        'upcomingSchedule': _customers_schedule_payload(upcoming_schedule) if upcoming_schedule else None,
        'href': reverse('reporting:followup_detail', args=[followup.id]),
        'accountHref': f'/accounts/{followup.department_id}/' if followup.department_id else reverse('reporting:followup_detail', args=[followup.id]),
        'companyHref': reverse('reporting:company_detail', args=[followup.company_id]) if followup.company_id else '',
        'createScheduleHref': f"{reverse('reporting:schedule_create')}?followup={followup.id}",
    }


def _customers_empty_account_customer_payload(department, request_user, *, account_row=False):
    owner = department.created_by or getattr(department.company, 'created_by', None) or request_user
    company_href = reverse('reporting:company_detail', args=[department.company_id]) if department.company_id else ''
    return {
        'id': department.id if account_row else 0,
        'accountId': department.id,
        'accountType': 'department',
        'representativeCustomerId': None,
        'customer': '담당자 없음',
        'company': department.company.name if department.company_id else '',
        'companyId': department.company_id,
        'department': department.name,
        'departmentId': department.id,
        'manager': '',
        'owner': _user_display_name(owner),
        'ownerId': owner.id,
        'priority': '',
        'priorityLabel': '',
        'status': '',
        'statusLabel': '',
        'pipelineStage': '',
        'pipelineLabel': '',
        'grade': '',
        'score': 0,
        'phone': '',
        'email': '',
        'address': department.address or '',
        'contactSummary': '',
        'contactCount': 0,
        'contactPreview': [],
        'notes': (department.notes or '').strip()[:140],
        'notesFull': department.notes or '',
        'lastActivityAt': None,
        'lastActivityLabel': '',
        'lastActivitySummary': '',
        'nextAction': '',
        'nextActionDate': None,
        'overdue': False,
        'activityCount': 0,
        'scheduleCount': 0,
        'upcomingScheduleCount': 0,
        'overdueActionCount': 0,
        'upcomingSchedule': None,
        'href': f'/accounts/{department.id}/',
        'accountHref': f'/accounts/{department.id}/',
        'customerHref': '',
        'companyHref': company_href,
        'createScheduleHref': f'/schedules/?create=1&department={department.id}',
    }


def _customers_empty_department_accounts_queryset(request_user, scope_users, filters=None):
    """Return accessible department accounts with no contacts in the current scope."""
    filters = filters or {}
    qs = Department.objects.select_related(
        'company',
        'created_by',
        'company__created_by',
    ).annotate(
        scoped_followup_count=Count(
            'followup_departments',
            filter=Q(followup_departments__user__in=scope_users),
            distinct=True,
        )
    )

    user_profile = get_user_profile(request_user)
    if not user_profile.is_admin():
        qs = qs.filter(
            Q(created_by__in=scope_users) |
            Q(company__created_by__in=scope_users) |
            Q(followup_departments__user__in=scope_users)
        )

    qs = qs.filter(scoped_followup_count=0)

    if any((filters.get(key) or '').strip() for key in ['priority', 'stage', 'grade', 'level']):
        return qs.none()

    q = filters.get('q') or ''
    if q:
        search_terms = [term.strip() for term in q.split(',') if term.strip()]
        if search_terms:
            combined_q = Q()
            for term in search_terms:
                combined_q |= (
                    Q(name__icontains=term) |
                    Q(company__name__icontains=term) |
                    Q(address__icontains=term) |
                    Q(notes__icontains=term)
                )
            qs = qs.filter(combined_q)

    owner = filters.get('owner') or ''
    if owner:
        try:
            owner_id = int(owner)
        except ValueError:
            owner_id = None
        if owner_id and scope_users.filter(id=owner_id).exists():
            qs = qs.filter(Q(created_by_id=owner_id) | Q(company__created_by_id=owner_id))
        else:
            qs = qs.none()

    company = filters.get('company') or ''
    if company:
        try:
            company_id = int(company)
        except ValueError:
            company_id = None
        if company_id:
            qs = qs.filter(company_id=company_id)
        else:
            qs = qs.none()

    return qs.distinct().order_by('company__name', 'name', 'id')


def _customers_priority_rank(priority):
    order = {
        'urgent': 0,
        'followup': 1,
        'scheduled': 2,
        'long_term': 3,
    }
    return order.get(priority, 9)


def _customers_stage_rank(stage):
    order = {
        'negotiation': 0,
        'quote': 1,
        'contact': 2,
        'potential': 3,
        'won': 4,
        'lost': 5,
    }
    return order.get(stage, 9)


def _customers_account_payloads(followups, today, limit=60):
    """FollowUp 담당자 목록을 부서/연구실 계정 단위로 묶는다."""
    rows_by_key = {}
    for followup in followups:
        payload = _customers_followup_payload(followup, today)
        account_key = f'department:{followup.department_id}' if followup.department_id else f'followup:{followup.id}'
        contact_name = payload['customer']
        if account_key not in rows_by_key:
            account_href = payload.get('accountHref') or payload.get('href') or ''
            rows_by_key[account_key] = {
                **payload,
                'id': followup.department_id or followup.id,
                'accountId': followup.department_id,
                'accountType': 'department' if followup.department_id else 'followup',
                'representativeCustomerId': followup.id,
                'customer': followup.department.name if followup.department else payload['customer'],
                'manager': payload['customer'],
                'contactCount': 1,
                'contactPreview': [contact_name] if contact_name else [],
                'ownerNames': [payload['owner']] if payload['owner'] else [],
                'href': account_href,
                'customerHref': payload.get('href') or '',
                'accountHref': account_href,
            }
            continue

        row = rows_by_key[account_key]
        row['activityCount'] += payload['activityCount']
        row['scheduleCount'] += payload['scheduleCount']
        row['upcomingScheduleCount'] += payload['upcomingScheduleCount']
        row['overdueActionCount'] += payload['overdueActionCount']
        row['overdue'] = bool(row['overdue'] or payload['overdue'])
        row['contactCount'] += 1
        if contact_name and contact_name not in row['contactPreview'] and len(row['contactPreview']) < 5:
            row['contactPreview'].append(contact_name)
        if payload['owner'] and payload['owner'] not in row['ownerNames']:
            row['ownerNames'].append(payload['owner'])
        if payload.get('lastActivityAt') and (
            not row.get('lastActivityAt') or payload['lastActivityAt'] > row['lastActivityAt']
        ):
            row['lastActivityAt'] = payload['lastActivityAt']
            row['lastActivityLabel'] = payload['lastActivityLabel']
            row['lastActivitySummary'] = payload['lastActivitySummary']
        if payload.get('nextActionDate'):
            current_next_action_date = row.get('nextActionDate')
            should_replace_action = not row.get('nextActionDate')
            if payload['overdue'] and not row.get('overdue'):
                should_replace_action = True
            elif current_next_action_date and payload['nextActionDate'] < current_next_action_date:
                should_replace_action = True
            if should_replace_action:
                row['nextAction'] = payload['nextAction']
                row['nextActionDate'] = payload['nextActionDate']
        if payload.get('upcomingSchedule'):
            current_schedule = row.get('upcomingSchedule')
            candidate_schedule = payload['upcomingSchedule']
            current_key = (
                current_schedule.get('date') or '',
                current_schedule.get('time') or '',
            ) if current_schedule else None
            candidate_key = (
                candidate_schedule.get('date') or '',
                candidate_schedule.get('time') or '',
            )
            if not current_key or candidate_key < current_key:
                row['upcomingSchedule'] = candidate_schedule
        if _customers_priority_rank(payload['priority']) < _customers_priority_rank(row['priority']):
            row['priority'] = payload['priority']
            row['priorityLabel'] = payload['priorityLabel']
        if _customers_stage_rank(payload['pipelineStage']) < _customers_stage_rank(row['pipelineStage']):
            row['pipelineStage'] = payload['pipelineStage']
            row['pipelineLabel'] = payload['pipelineLabel']
        row['score'] = max(row['score'], payload['score'])

    rows = []
    for row in rows_by_key.values():
        owner_names = row.pop('ownerNames', [])
        if owner_names:
            row['owner'] = owner_names[0] if len(owner_names) == 1 else f'{owner_names[0]} 외 {len(owner_names) - 1}명'
        row['contactSummary'] = ', '.join(row.get('contactPreview') or [])
        rows.append(row)

    rows.sort(
        key=lambda row: (
            row.get('lastActivityAt') or '',
            row.get('overdueActionCount') or 0,
            row.get('score') or 0,
            row.get('id') or 0,
        ),
        reverse=True,
    )
    return rows if limit is None else rows[:limit]


def _customer_score_level_options():
    return [
        {'value': 'critical', 'label': '최우선', 'description': '85점 이상'},
        {'value': 'high', 'label': '높음', 'description': '70-84점'},
        {'value': 'medium', 'label': '중간', 'description': '50-69점'},
        {'value': 'low', 'label': '낮음', 'description': '30-49점'},
        {'value': 'minimal', 'label': '최소', 'description': '30점 미만'},
    ]


def _customer_score_level_match(score, level):
    if level == 'critical':
        return score >= 85
    if level == 'high':
        return 70 <= score < 85
    if level == 'medium':
        return 50 <= score < 70
    if level == 'low':
        return 30 <= score < 50
    if level == 'minimal':
        return score < 30
    return True


def _customer_request_filters(request):
    return {
        'q': (request.GET.get('q') or request.GET.get('search') or '').strip(),
        'owner': (request.GET.get('owner') or request.GET.get('user') or '').strip(),
        'priority': (request.GET.get('priority') or '').strip(),
        'stage': (request.GET.get('stage') or request.GET.get('pipeline_stage') or '').strip(),
        'company': (request.GET.get('company') or request.GET.get('company_id') or '').strip(),
        'grade': (request.GET.get('grade') or request.GET.get('customer_grade') or '').strip(),
        'level': (request.GET.get('level') or request.GET.get('score_level') or '').strip(),
    }


def _apply_customer_followup_filters(followups, filters, scope_users=None):
    q = filters.get('q') or ''
    owner = filters.get('owner') or ''
    priority = filters.get('priority') or ''
    stage = filters.get('stage') or ''
    company = filters.get('company') or ''
    grade = filters.get('grade') or ''
    level = filters.get('level') or ''

    if q:
        search_terms = [term.strip() for term in q.split(',') if term.strip()]
        if search_terms:
            combined_q = Q()
            for term in search_terms:
                combined_q |= (
                    Q(customer_name__icontains=term) |
                    Q(manager__icontains=term) |
                    Q(company__name__icontains=term) |
                    Q(department__name__icontains=term) |
                    Q(email__icontains=term) |
                    Q(phone_number__icontains=term) |
                    Q(notes__icontains=term)
                )
            followups = followups.filter(combined_q).distinct()

    if owner:
        try:
            owner_id = int(owner)
        except ValueError:
            owner_id = None
        if owner_id and (scope_users is None or scope_users.filter(id=owner_id).exists()):
            followups = followups.filter(user_id=owner_id)

    valid_priorities = {value for value, _label in FollowUp.PRIORITY_CHOICES}
    if priority in valid_priorities:
        followups = followups.filter(priority=priority)

    valid_stages = {value for value, _label in FollowUp.PIPELINE_STAGE_CHOICES}
    if stage in valid_stages:
        followups = followups.filter(pipeline_stage=stage)

    if company:
        try:
            company_id = int(company)
        except ValueError:
            company_id = None
        if company_id:
            followups = followups.filter(
                Q(company_id=company_id) | Q(department__company_id=company_id)
            )

    valid_grades = {value for value, _label in FollowUp.CUSTOMER_GRADE_CHOICES}
    if grade in valid_grades:
        followups = followups.filter(customer_grade=grade)

    valid_levels = {option['value'] for option in _customer_score_level_options()}
    if level in valid_levels:
        matching_ids = [
            followup.id
            for followup in followups
            if _customer_score_level_match(float(followup.get_combined_score()), level)
        ]
        followups = followups.filter(id__in=matching_ids)

    return followups


def _customer_company_filter_options(base_followups):
    return [
        {
            'id': row['company_id'],
            'name': row['company__name'],
            'count': row['count'],
        }
        for row in base_followups.exclude(company_id__isnull=True).values(
            'company_id', 'company__name'
        ).annotate(
            count=Count('id', distinct=True)
        ).order_by('company__name')
    ]


def _customer_export_urls(filters):
    from urllib.parse import urlencode

    query = {}
    key_map = {
        'q': 'search',
        'owner': 'user',
        'priority': 'priority',
        'stage': 'pipeline_stage',
        'company': 'company',
        'grade': 'grade',
        'level': 'level',
    }
    for source_key, target_key in key_map.items():
        value = (filters.get(source_key) or '').strip()
        if value:
            query[target_key] = value
    encoded_query = urlencode(query)
    suffix = f'?{encoded_query}' if encoded_query else ''
    return {
        'fullUrl': f"{reverse('reporting:followup_excel_download')}{suffix}",
        'basicUrl': f"{reverse('reporting:followup_basic_excel_download')}{suffix}",
    }


def _account_contact_role_options():
    return [
        {'value': value, 'label': label}
        for value, label in FollowUp.CONTACT_ROLE_CHOICES
    ]


def _parse_form_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on', '활성', 'active'}


def _same_company_manage_user_ids(request_user):
    cache_attr = '_same_company_manage_user_ids_cache'
    cached = getattr(request_user, cache_attr, None)
    if cached is not None:
        return cached
    user_ids = set(get_same_company_users(request_user).values_list('id', flat=True))
    setattr(request_user, cache_attr, user_ids)
    return user_ids


def _can_manage_department_account(request_user, department):
    user_profile = get_user_profile(request_user)
    if user_profile.is_admin():
        return True
    if user_profile.is_manager():
        return False
    scoped_user_ids = _same_company_manage_user_ids(request_user)
    if department.created_by_id and department.created_by_id in scoped_user_ids:
        return True
    company_created_by_id = getattr(department.company, 'created_by_id', None)
    if company_created_by_id and company_created_by_id in scoped_user_ids:
        return True
    return FollowUp.objects.filter(department=department, user_id__in=scoped_user_ids).exists()


def _can_access_department_account(request_user, department, scope_users=None):
    user_profile = get_user_profile(request_user)
    if user_profile.is_admin():
        return True
    scoped_users = get_same_company_users(request_user)
    if FollowUp.objects.filter(department=department, user__in=scoped_users).exists():
        return True
    if department.created_by_id and scoped_users.filter(id=department.created_by_id).exists():
        return True
    company_created_by_id = getattr(department.company, 'created_by_id', None)
    if company_created_by_id and scoped_users.filter(id=company_created_by_id).exists():
        return True
    return False


def _can_manage_customer_company(request_user, company):
    user_profile = get_user_profile(request_user)
    if user_profile.is_admin():
        return True
    if user_profile.is_manager():
        return False
    scoped_user_ids = _same_company_manage_user_ids(request_user)
    if company.created_by_id and company.created_by_id in scoped_user_ids:
        return True
    return (
        FollowUp.objects.filter(
            Q(company=company) | Q(department__company=company),
            user_id__in=scoped_user_ids,
        ).exists()
        or Department.objects.filter(company=company, created_by_id__in=scoped_user_ids).exists()
    )


def _can_manage_customer_department(request_user, department):
    user_profile = get_user_profile(request_user)
    if user_profile.is_admin():
        return True
    if user_profile.is_manager():
        return False
    scoped_user_ids = _same_company_manage_user_ids(request_user)
    if department.created_by_id and department.created_by_id in scoped_user_ids:
        return True
    company_created_by_id = getattr(department.company, 'created_by_id', None)
    if company_created_by_id and company_created_by_id in scoped_user_ids:
        return True
    return FollowUp.objects.filter(department=department, user_id__in=scoped_user_ids).exists()


def _customer_delete_message(blockers):
    active_blockers = [
        f'{label} {count}건'
        for label, count in blockers
        if count
    ]
    if not active_blockers:
        return ''
    return f"연결된 {'/'.join(active_blockers)}이 있어 삭제할 수 없습니다."


def _delete_blocker_payload(blockers):
    return [
        {
            'label': label,
            'count': count,
        }
        for label, count in blockers
        if count
    ]


def _delete_guidance(blockers, *, target_label):
    active_labels = [label for label, count in blockers if count]
    if not active_labels:
        return ''
    if '담당자' in active_labels or '부서' in active_labels:
        return f'{target_label}에 연결된 담당자/계정이 있습니다. 계정 상세에서 이관 대상을 확인한 뒤 삭제하세요.'
    return f'{target_label}에 연결된 운영 기록이 있습니다. 관련 기록을 이관하거나 정리한 뒤 삭제하세요.'


def _related_or_annotated_count(instance, annotated_name, related_name):
    annotated_value = getattr(instance, annotated_name, None)
    if annotated_value is not None:
        return annotated_value
    return getattr(instance, related_name).count()


def _company_delete_blockers(company):
    return [
        ('부서', _related_or_annotated_count(company, 'department_count', 'departments')),
        ('담당자', _related_or_annotated_count(company, 'followup_count', 'followup_companies')),
        ('선결제', _related_or_annotated_count(company, 'prepayment_count', 'prepayment_set')),
    ]


def _department_delete_blockers(department):
    return [
        ('담당자', _related_or_annotated_count(department, 'followup_count', 'followup_departments')),
        ('선결제', _related_or_annotated_count(department, 'prepayment_count', 'prepayments')),
        ('메모', _related_or_annotated_count(department, 'memo_count', 'memos')),
        ('목표', _related_or_annotated_count(department, 'funnel_target_count', 'funnel_targets')),
    ]


def _customer_company_option_payload(company, request_user):
    blockers = _company_delete_blockers(company)
    can_manage = _can_manage_customer_company(request_user, company)
    delete_message = _customer_delete_message(blockers)
    return {
        'id': company.id,
        'name': company.name,
        'canManage': can_manage,
        'canDelete': can_manage and not delete_message,
        'manageMessage': '' if can_manage else '같은 회사 소속 사용자가 등록한 업체/학교만 수정할 수 있습니다.',
        'deleteMessage': delete_message,
        'updateUrl': reverse('reporting:company_update_api', args=[company.id]),
        'deleteUrl': reverse('reporting:company_delete_api', args=[company.id]),
        'departmentCount': blockers[0][1],
        'followupCount': blockers[1][1],
    }


def _customer_department_option_payload(department, request_user, search_text=''):
    blockers = _department_delete_blockers(department)
    can_manage = _can_manage_customer_department(request_user, department)
    delete_message = _customer_delete_message(blockers)
    return {
        'id': department.id,
        'name': department.name,
        'companyId': department.company_id,
        'companyName': department.company.name,
        'searchText': search_text,
        'canManage': can_manage,
        'canDelete': can_manage and not delete_message,
        'manageMessage': '' if can_manage else '같은 회사 소속 사용자가 등록한 부서/연구실만 수정할 수 있습니다.',
        'deleteMessage': delete_message,
        'updateUrl': reverse('reporting:department_update_api', args=[department.id]),
        'deleteUrl': reverse('reporting:department_delete_api', args=[department.id]),
        'followupCount': blockers[0][1],
    }


def _company_management_scope(request, user_profile):
    if user_profile.is_admin():
        scope_users = get_accessible_users(request.user, request)
        if scope_users.count() == User.objects.count():
            companies_qs = Company.objects.all()
            scope_label = '전체 업체/부서'
        else:
            companies_qs = Company.objects.filter(
                Q(created_by__in=scope_users) |
                Q(followup_companies__user__in=scope_users) |
                Q(departments__followup_departments__user__in=scope_users)
            )
            scope_label = '선택된 사용자 범위'
    elif user_profile.company:
        scope_users = User.objects.filter(userprofile__company=user_profile.company)
        companies_qs = Company.objects.filter(
            Q(created_by__in=scope_users) |
            Q(followup_companies__user__in=scope_users) |
            Q(departments__followup_departments__user__in=scope_users)
        )
        scope_label = f'{user_profile.company.name} 팀'
    else:
        scope_users = User.objects.filter(id=request.user.id)
        companies_qs = Company.objects.filter(created_by=request.user)
        scope_label = _user_display_name(request.user)
    return scope_users, companies_qs.distinct(), scope_label


def _count_by_field(queryset, field_name):
    return {
        row[field_name]: row['count'] or 0
        for row in queryset.values(field_name).annotate(count=Count('id'))
        if row[field_name] is not None
    }


def _company_management_search_company_ids(base_company_ids, query):
    if not query:
        return list(base_company_ids)
    if not base_company_ids:
        return []

    company_ids = set(
        Company.objects.filter(id__in=base_company_ids, name__icontains=query).values_list('id', flat=True)
    )
    company_ids.update(
        Department.objects.filter(company_id__in=base_company_ids, name__icontains=query).values_list('company_id', flat=True)
    )
    company_ids.update(
        FollowUp.objects.filter(
            Q(customer_name__icontains=query) | Q(manager__icontains=query),
            company_id__in=base_company_ids,
        ).values_list('company_id', flat=True)
    )
    company_ids.update(
        FollowUp.objects.filter(
            Q(customer_name__icontains=query) | Q(manager__icontains=query),
            department__company_id__in=base_company_ids,
        ).values_list('department__company_id', flat=True)
    )
    return [company_id for company_id in company_ids if company_id]


def _attach_company_management_counts(companies):
    company_ids = [company.id for company in companies]
    if not company_ids:
        return

    count_maps = {
        'department_count': _count_by_field(Department.objects.filter(company_id__in=company_ids), 'company_id'),
        'followup_count': _count_by_field(FollowUp.objects.filter(company_id__in=company_ids), 'company_id'),
        'prepayment_count': _count_by_field(Prepayment.objects.filter(company_id__in=company_ids), 'company_id'),
    }
    for company in companies:
        for attr_name, count_map in count_maps.items():
            setattr(company, attr_name, count_map.get(company.id, 0))


def _attach_department_management_counts(departments):
    department_ids = [department.id for department in departments]
    if not department_ids:
        return

    count_maps = {
        'followup_count': _count_by_field(FollowUp.objects.filter(department_id__in=department_ids), 'department_id'),
        'prepayment_count': _count_by_field(Prepayment.objects.filter(department_id__in=department_ids), 'department_id'),
        'memo_count': _count_by_field(DepartmentMemo.objects.filter(department_id__in=department_ids), 'department_id'),
        'funnel_target_count': _count_by_field(FunnelTarget.objects.filter(department_id__in=department_ids), 'department_id'),
    }
    for department in departments:
        for attr_name, count_map in count_maps.items():
            setattr(department, attr_name, count_map.get(department.id, 0))


def _company_salesmen_payload(company, scope_users):
    salesmen = list(
        FollowUp.objects.filter(
            Q(company=company) | Q(department__company=company),
            user__in=scope_users,
        ).values(
            'user_id',
            'user__username',
            'user__first_name',
            'user__last_name',
            'user__userprofile__role',
        ).annotate(
            contact_count=Count('id', distinct=True),
        ).order_by('user__username')
    )
    return [
        {
            'id': row['user_id'],
            'name': (
                f"{row['user__last_name']}{row['user__first_name']}".strip()
                or row['user__username']
            ),
            'username': row['user__username'],
            'role': row['user__userprofile__role'] or '',
            'contactCount': row['contact_count'] or 0,
        }
        for row in salesmen
    ]


def _company_management_department_payload(department, request_user):
    blockers = _department_delete_blockers(department)
    can_manage = _can_manage_customer_department(request_user, department)
    delete_message = _customer_delete_message(blockers)
    return {
        'id': department.id,
        'name': department.name,
        'companyId': department.company_id,
        'companyName': department.company.name,
        'canManage': can_manage,
        'canDelete': can_manage and not delete_message,
        'manageMessage': '' if can_manage else '같은 회사 소속 사용자가 등록한 부서/연구실만 수정할 수 있습니다.',
        'deleteMessage': delete_message,
        'deleteGuidance': _delete_guidance(blockers, target_label='부서/연구실') if delete_message else '',
        'deleteBlockers': _delete_blocker_payload(blockers),
        'updateUrl': reverse('reporting:department_update_api', args=[department.id]),
        'deleteUrl': reverse('reporting:department_delete_api', args=[department.id]),
        'href': f'/accounts/{department.id}/',
        'djangoEditHref': reverse('reporting:department_edit', args=[department.id]),
        'createdById': department.created_by_id,
        'createdByName': _user_display_name(department.created_by) if department.created_by else '',
        'followupCount': blockers[0][1],
        'prepaymentCount': blockers[1][1],
        'memoCount': blockers[2][1],
        'funnelTargetCount': blockers[3][1],
    }


def _company_management_move_target_payload(company, request_user):
    can_manage = _can_manage_customer_company(request_user, company)
    return {
        'id': company.id,
        'name': company.name,
        'canManage': can_manage,
        'manageMessage': '' if can_manage else '같은 회사 소속 사용자가 등록한 업체/학교로만 이동할 수 있습니다.',
    }


def _company_management_company_payload(company, request_user, scope_users, departments):
    blockers = _company_delete_blockers(company)
    can_manage = _can_manage_customer_company(request_user, company)
    delete_message = _customer_delete_message(blockers)
    return {
        'id': company.id,
        'name': company.name,
        'canManage': can_manage,
        'canDelete': can_manage and not delete_message,
        'manageMessage': '' if can_manage else '같은 회사 소속 사용자가 등록한 업체/학교만 수정할 수 있습니다.',
        'deleteMessage': delete_message,
        'deleteGuidance': _delete_guidance(blockers, target_label='업체/학교') if delete_message else '',
        'deleteBlockers': _delete_blocker_payload(blockers),
        'updateUrl': reverse('reporting:company_update_api', args=[company.id]),
        'deleteUrl': reverse('reporting:company_delete_api', args=[company.id]),
        'createdById': company.created_by_id,
        'createdByName': _user_display_name(company.created_by) if company.created_by else '',
        'departmentCount': blockers[0][1],
        'followupCount': blockers[1][1],
        'prepaymentCount': blockers[2][1],
        'salesmen': _company_salesmen_payload(company, scope_users),
        'departments': departments,
    }


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def companies_management_api(request):
    """React 업체/부서 관리 전용 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, base_companies_qs, scope_label = _company_management_scope(request, user_profile)
    q = (request.GET.get('q') or request.GET.get('search') or '').strip()
    selected_department_id = request.GET.get('department_id') or ''

    base_company_ids = list(base_companies_qs.values_list('id', flat=True).distinct())
    total_company_count = len(base_company_ids)
    total_department_count = Department.objects.filter(company_id__in=base_company_ids).count()
    filtered_company_ids = _company_management_search_company_ids(base_company_ids, q)

    companies = list(
        Company.objects.filter(id__in=filtered_company_ids).select_related('created_by').order_by('name')
    )
    _attach_company_management_counts(companies)
    departments = list(
        Department.objects.filter(company_id__in=filtered_company_ids).select_related(
            'company', 'created_by',
        ).order_by('company__name', 'name')
    )
    _attach_department_management_counts(departments)
    departments_by_company = {}
    for department in departments:
        departments_by_company.setdefault(department.company_id, []).append(
            _company_management_department_payload(department, request.user)
        )
    company_payloads = [
        _company_management_company_payload(
            company,
            request.user,
            scope_users,
            departments_by_company.get(company.id, []),
        )
        for company in companies
    ]
    department_move_companies = [
        _company_management_move_target_payload(company, request.user)
        for company in Company.objects.filter(id__in=base_company_ids).order_by('name')
    ]
    department_payloads = [
        department
        for company in company_payloads
        for department in company['departments']
    ]

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': scope_label,
            'role': user_profile.role,
            'roleLabel': user_profile.get_role_display(),
            'companyName': user_profile.company.name if user_profile.company else '',
            'canViewAll': bool(user_profile.can_view_all_users()),
        },
        'permissions': {
            'canCreateCompany': not user_profile.is_manager(),
            'canCreateDepartment': not user_profile.is_manager(),
            'readOnly': user_profile.is_manager(),
            'readOnlyMessage': 'Manager는 회사 내 업체/부서 데이터를 조회만 할 수 있습니다.' if user_profile.is_manager() else '',
        },
        'filters': {
            'q': q,
            'departmentId': selected_department_id,
        },
        'metrics': {
            'totalCompanies': total_company_count,
            'filteredCompanies': len(company_payloads),
            'totalDepartments': total_department_count,
            'filteredDepartments': len(department_payloads),
            'totalContacts': sum(company['followupCount'] for company in company_payloads),
            'blockedCompanies': sum(1 for company in company_payloads if company['deleteMessage']),
            'blockedDepartments': sum(1 for department in department_payloads if department['deleteMessage']),
        },
        'links': {
            'companies': '/companies/',
            'customers': '/customers/',
            'createCompany': reverse('reporting:company_create_api'),
            'createDepartment': reverse('reporting:department_create_api'),
            'legacyCompanies': reverse('reporting:company_list'),
            'legacyManagerCompanies': reverse('reporting:manager_company_list'),
        },
        'companies': company_payloads,
        'departments': department_payloads,
        'departmentMoveCompanies': department_move_companies,
    })


def _account_management_config(request, user_profile, department, can_manage):
    if user_profile.is_admin():
        companies_qs = Company.objects.all()
    elif user_profile.company:
        company_users = User.objects.filter(userprofile__company=user_profile.company)
        companies_qs = Company.objects.filter(
            Q(created_by__in=company_users) | Q(id=department.company_id)
        )
    else:
        companies_qs = Company.objects.filter(
            Q(created_by=request.user) | Q(id=department.company_id)
        )

    companies_qs = companies_qs.distinct().order_by('name')
    departments_qs = Department.objects.filter(
        Q(company__in=companies_qs) | Q(id=department.id)
    ).select_related('company').distinct().order_by('company__name', 'name')
    departments = list(departments_qs)
    department_search_map = _customers_department_search_text_map(
        departments,
        get_same_company_users(request.user),
    )
    return {
        'canManage': bool(can_manage),
        'message': '' if can_manage else '계정 관리 권한이 없습니다.',
        'accountSubmitUrl': reverse('reporting:account_update_api', args=[department.id]),
        'contactCreateUrl': reverse('reporting:account_contact_create_api', args=[department.id]),
        'contactRoles': _account_contact_role_options(),
        'priorities': [
            {'value': value, 'label': label}
            for value, label in FollowUp.PRIORITY_CHOICES
        ],
        'statuses': [
            {'value': value, 'label': label}
            for value, label in FollowUp.STATUS_CHOICES
        ],
        'stages': [
            {'value': value, 'label': label}
            for value, label in FollowUp.PIPELINE_STAGE_CHOICES
        ],
        'companies': [
            {'id': company.id, 'name': company.name}
            for company in companies_qs
        ],
        'departments': [
            {
                'id': department_option.id,
                'name': department_option.name,
                'companyId': department_option.company_id,
                'companyName': department_option.company.name,
                'searchText': department_search_map.get(department_option.id, ''),
            }
            for department_option in departments
        ],
    }


def _customer_account_contact_payload(followup, can_manage=False):
    phone = followup.phone_number or ''
    email = followup.email or ''
    contact_name = followup.customer_name or followup.manager or '담당자 미정'
    return {
        'id': followup.id,
        'name': contact_name,
        'manager': followup.manager or '',
        'contactRole': followup.contact_role,
        'contactRoleLabel': followup.get_contact_role_display(),
        'isActive': bool(followup.is_active),
        'email': email,
        'phone': phone,
        'contactSummary': ' · '.join([item for item in [phone, email] if item]),
        'ownerName': _user_display_name(followup.user),
        'ownerId': followup.user_id,
        'status': followup.status,
        'statusLabel': followup.get_status_display(),
        'priority': followup.priority,
        'priorityLabel': followup.get_priority_display(),
        'pipelineStage': followup.pipeline_stage,
        'pipelineLabel': followup.get_pipeline_stage_display(),
        'address': followup.address or '',
        'notes': (followup.notes or '').strip()[:140],
        'notesFull': followup.notes or '',
        'canManage': bool(can_manage),
        'manageMessage': '' if can_manage else '이 담당자 수정 권한이 없습니다.',
        'updateUrl': reverse('reporting:account_contact_update_api', args=[followup.department_id, followup.id]) if followup.department_id else '',
        'href': f'/customers/{followup.id}/',
        'djangoHref': reverse('reporting:followup_detail', args=[followup.id]),
    }


def _customer_account_payload(followup, shared_followups, scope_users, request=None, user_profile=None):
    contacts = list(
        shared_followups.filter(user__in=scope_users).select_related(
            'user', 'company', 'department',
        )
    )
    role_order = {
        FollowUp.CONTACT_ROLE_PI: 0,
        FollowUp.CONTACT_ROLE_PRACTITIONER: 1,
        FollowUp.CONTACT_ROLE_PURCHASING: 2,
        FollowUp.CONTACT_ROLE_TAX_INVOICE: 3,
    }
    contacts.sort(
        key=lambda contact: (
            not bool(contact.is_active),
            role_order.get(contact.contact_role, 9),
            contact.customer_name or contact.manager or '',
            contact.id,
        )
    )
    account_id = followup.department_id or followup.id
    account_name = followup.department.name if followup.department else (
        followup.customer_name or followup.manager or '계정명 미정'
    )
    is_department_account = bool(followup.department_id)
    department = followup.department if is_department_account else None
    active_contacts = [contact for contact in contacts if contact.is_active]
    inactive_contacts = [contact for contact in contacts if not contact.is_active]
    pi_contact = next((contact for contact in contacts if contact.contact_role == FollowUp.CONTACT_ROLE_PI and contact.is_active), None)
    can_manage_account = bool(request and department and _can_manage_department_account(request.user, department))
    management = (
        _account_management_config(request, user_profile or get_user_profile(request.user), department, can_manage_account)
        if request and department else {
            'canManage': False,
            'message': '부서/연구실 계정이 없어 계정 관리를 사용할 수 없습니다.',
            'accountSubmitUrl': '',
            'contactCreateUrl': '',
            'contactRoles': _account_contact_role_options(),
            'priorities': [],
            'statuses': [],
            'stages': [],
            'companies': [],
            'departments': [],
        }
    )
    return {
        'id': account_id,
        'type': 'department' if is_department_account else 'followup',
        'name': account_name,
        'companyId': followup.company_id,
        'companyName': followup.company.name if followup.company else '',
        'departmentId': followup.department_id,
        'departmentName': followup.department.name if followup.department else '',
        'address': (department.address if department else '') or followup.address or '',
        'notes': (department.notes if department else '') or followup.notes or '',
        'representativeCustomerId': followup.id,
        'representativeName': followup.customer_name or followup.manager or '대표 담당자 미정',
        'contactCount': len(contacts),
        'activeContactCount': len(active_contacts),
        'inactiveContactCount': len(inactive_contacts),
        'piContactId': pi_contact.id if pi_contact else None,
        'piContactName': (pi_contact.customer_name or pi_contact.manager) if pi_contact else '',
        'ledgerScopeLabel': '부서/연구실 계정 공유 원장' if is_department_account else '담당자 단일 원장',
        'ledgerScopeDescription': (
            '같은 업체/부서/연구실 담당자의 납품, 견적, 선결제, 서비스 기록을 함께 집계합니다.'
            if is_department_account else
            '부서/연구실 연결이 없어 이 담당자에게 연결된 기록만 집계합니다.'
        ),
        'management': management,
        'contacts': [
            _customer_account_contact_payload(
                contact,
                can_manage=bool(request and can_modify_user_data(request.user, contact.user)),
            )
            for contact in contacts
        ],
        'href': f'/accounts/{followup.department_id}/' if followup.department_id else f'/customers/{followup.id}/',
        'djangoRepresentativeHref': reverse('reporting:followup_detail', args=[followup.id]),
    }


def _empty_department_account_payload(department, request, user_profile, can_manage_account):
    return {
        'id': department.id,
        'type': 'department',
        'name': department.name,
        'companyId': department.company_id,
        'companyName': department.company.name if department.company_id else '',
        'departmentId': department.id,
        'departmentName': department.name,
        'address': department.address or '',
        'notes': department.notes or '',
        'representativeCustomerId': None,
        'representativeName': '',
        'contactCount': 0,
        'activeContactCount': 0,
        'inactiveContactCount': 0,
        'piContactId': None,
        'piContactName': '',
        'ledgerScopeLabel': '부서/연구실 계정 공유 원장',
        'ledgerScopeDescription': '같은 업체/부서/연구실 담당자의 납품, 견적, 선결제, 서비스 기록을 함께 집계합니다.',
        'management': _account_management_config(request, user_profile, department, can_manage_account),
        'contacts': [],
        'href': f'/accounts/{department.id}/',
        'djangoRepresentativeHref': '',
    }


def _customers_edit_config(request, user_profile, followup, can_edit):
    """React 고객 상세 수정 폼에 필요한 선택지와 권한 정보를 구성한다."""
    if user_profile.is_admin():
        companies_qs = Company.objects.all()
    elif user_profile.company:
        company_users = User.objects.filter(userprofile__company=user_profile.company)
        companies_qs = Company.objects.filter(
            Q(created_by__in=company_users) | Q(id=followup.company_id)
        )
    else:
        companies_qs = Company.objects.filter(
            Q(created_by=request.user) | Q(id=followup.company_id)
        )

    companies_qs = companies_qs.distinct().order_by('name')
    departments_qs = Department.objects.filter(
        Q(company__in=companies_qs) | Q(id=followup.department_id)
    ).select_related('company').distinct().order_by('company__name', 'name')
    departments = list(departments_qs)
    department_search_map = _customers_department_search_text_map(
        departments,
        get_same_company_users(request.user),
    )

    return {
        'canEdit': bool(can_edit),
        'canDelete': bool(can_edit),
        'message': '' if can_edit else '수정 권한이 없습니다.',
        'submitUrl': reverse('reporting:customer_update_api', args=[followup.id]),
        'deleteUrl': reverse('reporting:customer_delete_api', args=[followup.id]),
        'djangoUrl': reverse('reporting:followup_edit', args=[followup.id]),
        'priorities': [
            {'value': value, 'label': label}
            for value, label in FollowUp.PRIORITY_CHOICES
        ],
        'statuses': [
            {'value': value, 'label': label}
            for value, label in FollowUp.STATUS_CHOICES
        ],
        'stages': [
            {'value': value, 'label': label}
            for value, label in FollowUp.PIPELINE_STAGE_CHOICES
        ],
        'companies': [
            {'id': company.id, 'name': company.name}
            for company in companies_qs
        ],
        'departments': [
            {
                'id': department.id,
                'name': department.name,
                'companyId': department.company_id,
                'companyName': department.company.name,
                'searchText': department_search_map.get(department.id, ''),
            }
            for department in departments
        ],
    }


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def customers_summary_api(request):
    """React CRM customers 화면용 읽기 전용 API."""
    from django.db.models import Case, IntegerField, Value, When

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()

    filters = _customer_request_filters(request)
    q = filters['q']
    owner = filters['owner']
    priority = filters['priority']
    stage = filters['stage']
    company = filters['company']
    grade = filters['grade']
    level = filters['level']
    row_mode = request.GET.get('mode', 'account').strip()
    if row_mode not in {'account', 'contact'}:
        row_mode = 'account'
    try:
        page = int(request.GET.get('page') or 1)
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)
    try:
        page_size = int(request.GET.get('page_size') or request.GET.get('pageSize') or 20)
    except (TypeError, ValueError):
        page_size = 20
    page_size = min(max(page_size, 10), 100)
    base_followups = FollowUp.objects.filter(user__in=scope_users)
    followups = _apply_customer_followup_filters(base_followups, filters, scope_users=scope_users)
    base_empty_departments = _customers_empty_department_accounts_queryset(request.user, scope_users)
    filtered_empty_departments = _customers_empty_department_accounts_queryset(request.user, scope_users, filters)

    priority_order = Case(
        When(priority='urgent', then=Value(0)),
        When(priority='followup', then=Value(1)),
        When(priority='scheduled', then=Value(2)),
        When(priority='long_term', then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )
    recent_histories_qs = History.objects.filter(
        parent_history__isnull=True,
    ).exclude(action_type='memo').order_by('-created_at')
    upcoming_schedules_qs = Schedule.objects.filter(
        status='scheduled',
        visit_date__gte=today,
    ).order_by('visit_date', 'visit_time')

    followups = _customers_enriched_queryset(
        followups,
        today,
        priority_order,
        recent_histories_qs,
        upcoming_schedules_qs,
    ).order_by(
        '-updated_at', '-created_at', '-id'
    )

    filtered_count = followups.count()
    filtered_account_count = (
        followups.filter(department_id__isnull=False).values('department_id').distinct().count()
        + followups.filter(department_id__isnull=True).count()
        + filtered_empty_departments.count()
    )
    total_account_count = (
        base_followups.filter(department_id__isnull=False).values('department_id').distinct().count()
        + base_followups.filter(department_id__isnull=True).count()
        + base_empty_departments.count()
    )

    if row_mode == 'account':
        account_rows_all = _customers_account_payloads(list(followups), today, limit=None)
        account_rows_all.extend(
            _customers_empty_account_customer_payload(department, request.user, account_row=True)
            for department in filtered_empty_departments
        )
        total_rows = len(account_rows_all)
        total_pages = max((total_rows + page_size - 1) // page_size, 1)
        page = min(page, total_pages)
        page_start = (page - 1) * page_size
        page_end = page_start + page_size
        accounts = account_rows_all[page_start:page_end]
        customers = list(followups[:page_size])
    else:
        total_rows = filtered_count
        total_pages = max((total_rows + page_size - 1) // page_size, 1)
        page = min(page, total_pages)
        page_start = (page - 1) * page_size
        page_end = page_start + page_size
        customers = list(followups[page_start:page_end])
        accounts = _customers_account_payloads(list(followups[:200]), today, limit=page_size)

    overdue_followup_histories = _histories_excluding_stale_quote_submission(list(
        History.objects.filter(
            user__in=scope_users,
            next_action_date__lt=today,
            next_action_date__isnull=False,
            parent_history__isnull=True,
            reviewed_at__isnull=True,
        ).order_by('next_action_date', '-created_at')
    ))
    overdue_followup_ids = {
        history.followup_id
        for history in overdue_followup_histories[:200]
        if history.followup_id
    }
    priority_customers = list(
        _customers_enriched_queryset(
            base_followups.filter(
                Q(priority__in=['urgent', 'followup']) |
                Q(customer_grade__in=['VIP', 'A']) |
                Q(id__in=overdue_followup_ids)
            ),
            today,
            priority_order,
            recent_histories_qs,
            upcoming_schedules_qs,
        ).order_by(
            'priority_rank', '-ai_score', '-updated_at'
        )[:10]
    )
    priority_accounts = _customers_account_payloads(priority_customers, today, limit=10)

    owner_options = [
        {
            'id': user.id,
            'name': _user_display_name(user),
        }
        for user in scope_users.order_by('username')
    ]

    scope_label = '전체'
    if selected_user:
        scope_label = _user_display_name(selected_user)
    elif not user_profile.can_view_all_users():
        scope_label = _user_display_name(request.user)
    elif user_profile.company:
        scope_label = f'{user_profile.company.name} 팀'

    active_count = base_followups.filter(status='active').count()
    urgent_count = base_followups.filter(priority='urgent').count()
    followup_count = base_followups.filter(priority='followup').count()
    scheduled_customer_count = base_followups.filter(
        schedules__status='scheduled',
        schedules__visit_date__gte=today,
    ).distinct().count()
    can_create_customer = not user_profile.is_manager()
    create_company_options = []
    create_department_options = []
    if can_create_customer:
        create_users = User.objects.filter(id=request.user.id)
        if user_profile.is_admin():
            create_users = get_accessible_users(request.user, request)
            create_companies_qs = Company.objects.filter(
                Q(created_by__in=create_users) | Q(created_by__isnull=True)
            )
        elif user_profile.company:
            create_users = User.objects.filter(userprofile__company=user_profile.company)
            create_companies_qs = Company.objects.filter(created_by__in=create_users)
        else:
            create_companies_qs = Company.objects.filter(created_by=request.user)

        create_companies_qs = create_companies_qs.distinct().annotate(
            department_count=Count('departments', distinct=True),
            followup_count=Count('followup_companies', distinct=True),
            prepayment_count=Count('prepayment', distinct=True),
        ).order_by('name')
        create_departments_qs = Department.objects.filter(
            company__in=create_companies_qs
        ).select_related('company').annotate(
            followup_count=Count('followup_departments', distinct=True),
            prepayment_count=Count('prepayments', distinct=True),
            memo_count=Count('memos', distinct=True),
            funnel_target_count=Count('funnel_targets', distinct=True),
        ).order_by('company__name', 'name')
        create_departments = list(create_departments_qs)
        create_department_search_map = _customers_department_search_text_map(
            create_departments,
            create_users,
        )
        create_company_options = [
            _customer_company_option_payload(company, request.user)
            for company in create_companies_qs
        ]
        create_department_options = [
            _customer_department_option_payload(
                department,
                request.user,
                create_department_search_map.get(department.id, ''),
            )
            for department in create_departments
        ]

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': scope_label,
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'filters': {
            'q': q,
            'owner': owner,
            'priority': priority,
            'stage': stage,
            'company': company,
            'grade': grade,
            'level': level,
            'mode': row_mode,
        },
        'options': {
            'owners': owner_options,
            'companies': _customer_company_filter_options(base_followups),
            'priorities': [
                {'value': value, 'label': label}
                for value, label in FollowUp.PRIORITY_CHOICES
            ],
            'stages': [
                {'value': value, 'label': label}
                for value, label in FollowUp.PIPELINE_STAGE_CHOICES
            ],
            'grades': [
                {'value': value, 'label': label}
                for value, label in FollowUp.CUSTOMER_GRADE_CHOICES
            ],
            'scoreLevels': _customer_score_level_options(),
            'rowModes': [
                {'value': 'account', 'label': '계정 기준'},
                {'value': 'contact', 'label': '담당자 기준'},
            ],
        },
        'pagination': {
            'rowMode': row_mode,
            'page': min(page, total_pages),
            'pageSize': page_size,
            'totalRows': total_rows,
            'totalPages': total_pages,
            'hasPrevious': page > 1,
            'hasNext': page < total_pages,
            'accountRows': filtered_account_count,
            'contactRows': filtered_count,
        },
        'export': {
            'canDownload': user_profile.can_excel_download(),
            'message': '' if user_profile.can_excel_download() else '엑셀 다운로드 권한이 없습니다.',
            **_customer_export_urls(filters),
        },
        'metrics': {
            'totalCustomers': base_followups.count(),
            'filteredCustomers': filtered_count,
            'totalAccounts': total_account_count,
            'filteredAccounts': filtered_account_count,
            'activeCustomers': active_count,
            'urgentCustomers': urgent_count,
            'followupCustomers': followup_count,
            'scheduledCustomers': scheduled_customer_count,
            'priorityCustomers': len(priority_customers),
            'overdueCustomers': base_followups.filter(id__in=overdue_followup_ids).count(),
            'vipCustomers': base_followups.filter(customer_grade__in=['VIP', 'A']).count(),
        },
        'links': {
            'createCustomer': '/customers/?create=1',
            'customers': '/customers/',
            'companies': reverse('reporting:company_list'),
            'customerReport': reverse('reporting:customer_report'),
            'createNote': '/notes/?create=1',
        },
        'create': {
            'canCreate': can_create_customer,
            'message': '' if can_create_customer else 'Manager는 고객을 생성할 수 없습니다.',
            'submitUrl': reverse('reporting:followup_create_ajax'),
            'companySubmitUrl': reverse('reporting:company_create_api'),
            'departmentSubmitUrl': reverse('reporting:department_create_api'),
            'advancedUrl': reverse('reporting:followup_create'),
            'priorities': [
                {'value': value, 'label': label}
                for value, label in FollowUp.PRIORITY_CHOICES
            ],
            'companies': create_company_options,
            'departments': create_department_options,
        },
        'customers': [
            _customers_followup_payload(followup, today)
            for followup in customers
        ],
        'accounts': accounts,
        'priorityCustomers': [
            _customers_followup_payload(followup, today)
            for followup in priority_customers
        ],
        'priorityAccounts': priority_accounts,
    })


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def followups_summary_api(request):
    """Read-only follow-up action queue for CRM analysis."""
    from django.utils.dateparse import parse_date

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    owner = request.GET.get('owner', '').strip()
    date_from = parse_date(request.GET.get('date_from', '').strip() or '')
    date_to = parse_date(request.GET.get('date_to', '').strip() or '')
    page_size = min(max(int(request.GET.get('page_size') or 50), 1), 100)

    histories = History.objects.filter(
        user__in=scope_users,
        parent_history__isnull=True,
        next_action_date__isnull=False,
    ).select_related(
        'user',
        'followup',
        'followup__company',
        'followup__department',
    )

    if owner:
        try:
            owner_id = int(owner)
        except ValueError:
            owner_id = None
        if owner_id and scope_users.filter(id=owner_id).exists():
            histories = histories.filter(user_id=owner_id)

    if q:
        histories = histories.filter(
            Q(next_action__icontains=q) |
            Q(meeting_next_action__icontains=q) |
            Q(content__icontains=q) |
            Q(followup__customer_name__icontains=q) |
            Q(followup__manager__icontains=q) |
            Q(followup__company__name__icontains=q) |
            Q(followup__department__name__icontains=q)
        )

    if date_from:
        histories = histories.filter(next_action_date__gte=date_from)
    if date_to:
        histories = histories.filter(next_action_date__lte=date_to)

    open_histories = histories.filter(reviewed_at__isnull=True)
    overdue_count = open_histories.filter(next_action_date__lt=today).count()
    due_today_count = open_histories.filter(next_action_date=today).count()
    upcoming_count = open_histories.filter(next_action_date__gt=today).count()
    completed_count = histories.filter(reviewed_at__isnull=False).count()

    if status == 'overdue':
        histories = open_histories.filter(next_action_date__lt=today)
    elif status == 'today':
        histories = open_histories.filter(next_action_date=today)
    elif status == 'upcoming':
        histories = open_histories.filter(next_action_date__gt=today)
    elif status == 'completed':
        histories = histories.filter(reviewed_at__isnull=False)
    else:
        histories = open_histories

    histories = histories.order_by('next_action_date', '-created_at')[:page_size]

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'canManage': not user_profile.is_manager(),
        'message': '' if not user_profile.is_manager() else '장비/A/S 정보는 읽기 전용입니다.',
        'scope': {
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'filters': {
            'q': q,
            'status': status,
            'owner': owner,
            'dateFrom': date_from.isoformat() if date_from else '',
            'dateTo': date_to.isoformat() if date_to else '',
            'pageSize': page_size,
        },
        'metrics': {
            'openCount': open_histories.count(),
            'overdueCount': overdue_count,
            'dueTodayCount': due_today_count,
            'upcomingCount': upcoming_count,
            'completedCount': completed_count,
        },
        'followups': [
            {
                'id': history.id,
                'customerId': history.followup_id,
                'customer': (
                    history.followup.customer_name or history.followup.manager or ''
                ) if history.followup else '',
                'company': history.followup.company.name if history.followup and history.followup.company else '',
                'department': history.followup.department.name if history.followup and history.followup.department else '',
                'owner': _user_display_name(history.user),
                'actionType': history.action_type,
                'actionLabel': history.get_action_type_display(),
                'nextAction': (history.next_action or history.meeting_next_action or history.content or '').strip()[:180],
                'nextActionDate': _date_or_none(history.next_action_date),
                'createdAt': _datetime_or_none(history.created_at),
                'reviewed': bool(history.reviewed_at),
                'risk': 'overdue' if history.next_action_date and history.next_action_date < today else (
                    'today' if history.next_action_date == today else 'upcoming'
                ),
                'href': reverse('reporting:history_detail', args=[history.id]),
                'customerHref': reverse('reporting:followup_detail', args=[history.followup_id]) if history.followup_id else '',
            }
            for history in histories
        ],
    })


def _customer_shared_followups_queryset(followup):
    return account_followups_for_followup(followup)


def _customer_detail_prepayment_summary_payload(followup, scope_users, actor):
    shared_followups = _customer_shared_followups_queryset(followup)
    account_prepayments_href = (
        f'/prepayments/account/{followup.department_id}/'
        if followup.department_id else f'/prepayments/customer/{followup.id}/'
    )
    account_filter = _prepayment_department_filter(followup.department) if followup.department_id else Q(customer=followup)
    base_prepayments = Prepayment.objects.filter(
        account_filter,
        created_by__in=scope_users,
    )
    stats = base_prepayments.aggregate(
        total_amount=Sum('amount'),
        total_balance=Sum('balance'),
        total_count=Count('id'),
        active_count=Count('id', filter=Q(status='active', balance__gt=0)),
        depleted_count=Count('id', filter=Q(status='depleted')),
        cancelled_count=Count('id', filter=Q(status='cancelled')),
    )
    total_amount = _money_int(stats['total_amount'])
    total_balance = _money_int(stats['total_balance'])
    recent_prepayments = list(
        base_prepayments.select_related(
            'department',
            'department__company',
            'company',
            'customer',
            'customer__company',
            'customer__department',
            'created_by',
        ).annotate(
            usage_count=Count('usages', distinct=True),
        ).order_by('-payment_date', '-created_at', '-id')[:5]
    )

    return {
        'metrics': {
            'totalAmount': total_amount,
            'totalBalance': total_balance,
            'totalUsed': max(total_amount - total_balance, 0),
            'totalCount': stats['total_count'] or 0,
            'activeCount': stats['active_count'] or 0,
            'depletedCount': stats['depleted_count'] or 0,
            'cancelledCount': stats['cancelled_count'] or 0,
        },
        'links': {
            'prepayments': '/prepayments/',
            'createPrepayment': '/prepayments/new/',
            'accountPrepayments': account_prepayments_href,
            'customerPrepayments': f'/prepayments/customer/{followup.id}/',
            'djangoCustomerPrepayments': reverse('reporting:prepayment_customer', args=[followup.id]),
        },
        'recentPrepayments': [
            _prepayment_item_payload(prepayment, actor)
            for prepayment in recent_prepayments
        ],
    }


def _customer_account_notes_queryset(scope_users, followups=None, department=None):
    note_scope = Q()
    if followups is not None:
        note_scope |= Q(followup__in=followups)
    if department is not None:
        note_scope |= Q(department=department)
    if not note_scope:
        return History.objects.none()
    return History.objects.filter(
        note_scope,
        user__in=scope_users,
        parent_history__isnull=True,
    ).exclude(action_type='memo').select_related(
        'user',
        'followup',
        'followup__company',
        'followup__department',
        'department',
        'department__company',
        'schedule',
        'personal_schedule',
        'reviewer',
    ).annotate(
        reply_count=Count('reply_memos', distinct=True),
        file_count=Count('files', distinct=True),
    ).distinct().order_by('-created_at', '-id')


def _customer_delivery_record_payload(schedule):
    return account_delivery_record_payload(schedule)


def _customer_delivery_record_payloads(followup, scope_users, limit=50):
    service_history_prefetch = Prefetch(
        'histories',
        queryset=History.objects.filter(parent_history__isnull=True).prefetch_related('delivery_items_set').order_by('-created_at'),
        to_attr='_customer_record_histories',
    )
    shared_followups = _customer_shared_followups_queryset(followup)
    delivery_schedules_qs = Schedule.objects.filter(
        followup__in=shared_followups,
        user__in=scope_users,
        activity_type='delivery',
    ).exclude(status='cancelled').select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'prepayment'
    ).prefetch_related(
        'delivery_items_set',
        service_history_prefetch,
        Prefetch(
            'prepayment_usages',
            queryset=PrepaymentUsage.objects.select_related('prepayment', 'prepayment__customer').order_by('id'),
        ),
    ).order_by('-visit_date', '-visit_time', '-id')
    if limit is not None:
        delivery_schedules_qs = delivery_schedules_qs[:limit]
    return [_customer_delivery_record_payload(schedule) for schedule in list(delivery_schedules_qs)]


def _customer_service_schedule_record_payload(schedule):
    return {
        'id': schedule.id,
        'recordType': 'service_schedule',
        'date': _date_or_none(schedule.visit_date),
        'dueDate': None,
        'completedDate': _date_or_none(schedule.visit_date) if schedule.status == 'completed' else None,
        'customerName': schedule.followup.customer_name or schedule.followup.manager or '',
        'assetName': '',
        'assetModelName': '',
        'ownerName': _user_display_name(schedule.user),
        'assignedTo': '',
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'priority': '',
        'priorityLabel': '',
        'caseType': 'service',
        'caseTypeLabel': schedule.get_activity_type_display(),
        'summary': schedule.notes or '',
        'detail': '',
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
    }


def _customer_operational_records_payload(followup, scope_users, actor):
    shared_followups = _customer_shared_followups_queryset(followup)
    account_ledger = account_operational_ledger_for_followups(
        list(shared_followups.select_related('user', 'company', 'department')),
        scope_users,
        actor=actor,
        record_limit=50,
    )
    ledger_metrics = account_ledger['metrics']
    delivery_records = account_ledger['deliveryRecords']
    quote_records = account_ledger['quoteRecords']

    service_schedules = list(
        Schedule.objects.filter(
            followup__in=shared_followups,
            user__in=scope_users,
            activity_type='service',
        ).select_related('user', 'followup').order_by('-visit_date', '-visit_time', '-id')[:50]
    )
    service_records = [
        *[_customer_service_schedule_record_payload(schedule) for schedule in service_schedules],
    ]
    service_records = sorted(
        service_records,
        key=lambda row: (row.get('date') or '', row.get('id') or 0),
        reverse=True,
    )[:50]

    return {
        'metrics': {
            'serviceRecords': len(service_records),
            'quoteRecords': ledger_metrics['quoteRecords'],
            'deliveryRecords': ledger_metrics['deliveryRecords'],
            'prepaymentDeliveryRecords': ledger_metrics['prepaymentDeliveryRecords'],
            'normalDeliveryRecords': ledger_metrics['normalDeliveryRecords'],
            'prepaymentRecords': ledger_metrics['prepaymentRecords'],
            'deliveryAmount': ledger_metrics['deliveryAmount'],
            'prepaymentDeliveryAmount': ledger_metrics['prepaymentDeliveryAmount'],
            'normalDeliveryAmount': ledger_metrics['normalDeliveryAmount'],
            'prepaymentUsedAmount': ledger_metrics['prepaymentUsedAmount'],
        },
        'serviceRecords': service_records,
        'quoteRecords': quote_records,
        'deliveryRecords': delivery_records,
        'prepaymentRecords': account_ledger['prepaymentRecords'],
        'prepaymentUsageRecords': account_ledger['prepaymentUsageRecords'],
    }


def _customer_detail_note_file_payload(file_obj):
    history = file_obj.history
    followup = history.followup
    source_detail = (_history_activity_content(history) or history.content or '').strip()
    return {
        '_sortAt': file_obj.uploaded_at,
        'id': file_obj.id,
        'fileType': 'note',
        'fileTypeLabel': '영업노트',
        'filename': file_obj.original_filename,
        'size': _file_size_label(file_obj.file_size),
        'uploadedAt': _datetime_or_none(file_obj.uploaded_at),
        'uploadedBy': _user_display_name(file_obj.uploaded_by),
        'sourceId': history.id,
        'sourceLabel': history.get_action_type_display(),
        'sourceDetail': source_detail[:180],
        'sourceOwner': _user_display_name(history.user),
        'sourceDate': _datetime_or_none(history.created_at),
        'sourceHref': f'/notes/{history.id}/',
        'downloadHref': reverse('reporting:file_download', args=[file_obj.id]),
        'customerName': followup.customer_name or followup.manager or '',
    }


def _customer_detail_schedule_file_payload(file_obj):
    schedule = file_obj.schedule
    followup = schedule.followup
    source_detail = ' · '.join([
        part for part in [
            schedule.get_activity_type_display(),
            schedule.get_status_display(),
            schedule.location or '',
        ] if part
    ])
    return {
        '_sortAt': file_obj.uploaded_at,
        'id': file_obj.id,
        'fileType': 'schedule',
        'fileTypeLabel': '일정',
        'filename': file_obj.original_filename,
        'size': _file_size_label(file_obj.file_size),
        'uploadedAt': _datetime_or_none(file_obj.uploaded_at),
        'uploadedBy': _user_display_name(file_obj.uploaded_by),
        'sourceId': schedule.id,
        'sourceLabel': schedule.get_activity_type_display(),
        'sourceDetail': source_detail[:180],
        'sourceOwner': _user_display_name(schedule.user),
        'sourceDate': _date_or_none(schedule.visit_date),
        'sourceHref': f'/schedules/{schedule.id}/',
        'downloadHref': reverse('reporting:schedule_file_download', args=[file_obj.id]),
        'customerName': followup.customer_name or followup.manager or '',
    }


def _customer_detail_attachments_payload(followup, shared_followups, scope_users):
    """고객 상세에서 노트/일정 첨부를 한 곳에서 드릴다운할 수 있게 묶는다."""
    note_files_qs = HistoryFile.objects.filter(
        history__followup__in=shared_followups,
        history__user__in=scope_users,
        history__parent_history__isnull=True,
    ).exclude(
        history__action_type='memo',
    ).select_related(
        'history',
        'history__followup',
        'history__user',
        'uploaded_by',
    ).order_by('-uploaded_at', '-id')
    schedule_files_qs = ScheduleFile.objects.filter(
        schedule__followup__in=shared_followups,
        schedule__user__in=scope_users,
    ).select_related(
        'schedule',
        'schedule__followup',
        'schedule__user',
        'uploaded_by',
    ).order_by('-uploaded_at', '-id')

    recent_files = [
        *[_customer_detail_note_file_payload(file_obj) for file_obj in list(note_files_qs[:8])],
        *[_customer_detail_schedule_file_payload(file_obj) for file_obj in list(schedule_files_qs[:8])],
    ]
    recent_files.sort(key=lambda item: item['_sortAt'], reverse=True)
    for item in recent_files:
        item.pop('_sortAt', None)

    note_file_count = note_files_qs.count()
    schedule_file_count = schedule_files_qs.count()
    return {
        'metrics': {
            'totalFiles': note_file_count + schedule_file_count,
            'noteFiles': note_file_count,
            'scheduleFiles': schedule_file_count,
        },
        'recentFiles': recent_files[:12],
        'links': {
            'notes': f'/notes/?customer={followup.id}',
            'schedules': f'/schedules/?customer={followup.id}',
        },
    }


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def customer_detail_summary_api(request, followup_id):
    """React CRM customer detail 화면용 읽기 전용 API."""
    from datetime import timedelta
    from django.db.models import Case, IntegerField, Value, When

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    followup = get_object_or_404(
        FollowUp.objects.select_related('user', 'company', 'department'),
        pk=followup_id,
    )
    if not can_access_followup(request.user, followup):
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없습니다.',
        }, status=403)

    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()
    shared_followups = _customer_shared_followups_queryset(followup)

    priority_order = Case(
        When(priority='urgent', then=Value(0)),
        When(priority='followup', then=Value(1)),
        When(priority='scheduled', then=Value(2)),
        When(priority='long_term', then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )
    recent_histories_qs = History.objects.filter(
        user__in=scope_users,
        parent_history__isnull=True,
    ).exclude(action_type='memo').order_by('-created_at')
    upcoming_schedules_qs = Schedule.objects.filter(
        user__in=scope_users,
        status='scheduled',
        visit_date__gte=today,
    ).order_by('visit_date', 'visit_time')
    detail_followup = _customers_enriched_queryset(
        FollowUp.objects.filter(pk=followup.pk),
        today,
        priority_order,
        recent_histories_qs,
        upcoming_schedules_qs,
    ).first()
    if detail_followup is None:
        return JsonResponse({
            'success': False,
            'error': '고객을 찾을 수 없습니다.',
        }, status=404)

    notes_qs = _customer_account_notes_queryset(
        scope_users,
        followups=shared_followups,
        department=followup.department if followup.department_id else None,
    )

    overdue_actions_qs = notes_qs.filter(
        next_action_date__lt=today,
        next_action_date__isnull=False,
        reviewed_at__isnull=True,
    ).order_by('next_action_date', '-created_at')
    upcoming_actions_qs = notes_qs.filter(
        next_action_date__gte=today,
        next_action_date__lte=today + timedelta(days=14),
        next_action_date__isnull=False,
        reviewed_at__isnull=True,
    ).order_by('next_action_date', '-created_at')
    overdue_actions = _histories_excluding_stale_quote_submission(list(overdue_actions_qs))
    upcoming_actions = _histories_excluding_stale_quote_submission(list(upcoming_actions_qs))
    upcoming_schedules = Schedule.objects.filter(
        followup__in=shared_followups,
        user__in=scope_users,
        status='scheduled',
        visit_date__gte=today,
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department'
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('visit_date', 'visit_time')
    recent_schedules = Schedule.objects.filter(
        followup__in=shared_followups,
        user__in=scope_users,
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department'
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('-visit_date', '-visit_time')
    can_review_notes = _can_review_notes(user_profile)
    can_edit_customer = can_modify_user_data(request.user, followup.user)
    can_create_activity = bool(request.user.id == followup.user_id and not user_profile.is_manager())
    can_manage_account = bool(followup.department_id and _can_manage_department_account(request.user, followup.department))
    from reporting.api.demos import demo_customer_summary_payload

    demo_summary = demo_customer_summary_payload(
        request,
        scope_users,
        followup=followup,
        can_manage=can_manage_account or can_edit_customer,
    )

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': _user_display_name(selected_user) if selected_user else (
                _user_display_name(request.user) if not user_profile.can_view_all_users()
                else f'{user_profile.company.name} 팀' if user_profile.company else '전체'
            ),
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'customer': _customers_followup_payload(detail_followup, today),
        'account': _customer_account_payload(followup, shared_followups, scope_users, request, user_profile),
        'metrics': {
            'recentNotes': notes_qs.count(),
            'upcomingSchedules': upcoming_schedules.count(),
            'overdueActions': len(overdue_actions),
            'upcomingActions': len(upcoming_actions),
        },
        'links': {
            'customers': '/customers/',
            'accountDetail': f'/accounts/{followup.department_id}/' if followup.department_id else f'/customers/{followup.id}/',
            'accountDeliveryRecordsXlsx': reverse('reporting:account_delivery_records_xlsx_export_api', args=[followup.department_id]) if followup.department_id else reverse('reporting:customer_delivery_records_xlsx_export_api', args=[followup.id]),
            'djangoDetail': reverse('reporting:followup_detail', args=[followup.id]),
            'djangoEdit': reverse('reporting:followup_edit', args=[followup.id]),
            'createSchedule': f'/schedules/?create=1&customer={followup.id}',
            'createNote': f'/notes/?create=1&customer={followup.id}',
            'deliveryRecordsXlsx': reverse('reporting:customer_delivery_records_xlsx_export_api', args=[followup.id]),
            'pipeline': '/pipeline/',
        },
        'permissions': {
            'canCreateNote': can_create_activity,
            'canCreateSchedule': can_create_activity,
            'canManageAccount': can_manage_account,
            'canEditRepresentative': can_edit_customer,
            'canDeleteRepresentative': can_edit_customer,
            'readOnlyMessage': '' if can_manage_account or can_create_activity else '이 계정은 현재 사용자에게 읽기 전용입니다.',
        },
        'prepaymentSummary': _customer_detail_prepayment_summary_payload(followup, scope_users, request.user),
        'operationalRecords': _customer_operational_records_payload(followup, scope_users, request.user),
        'demoSummary': demo_summary,
        'attachments': _customer_detail_attachments_payload(followup, shared_followups, scope_users),
        'edit': _customers_edit_config(request, user_profile, followup, can_edit_customer),
        'recentNotes': [
            _notes_history_payload(note, today, can_review_notes)
            for note in list(notes_qs[:12])
        ],
        'overdueActions': [
            _notes_history_payload(note, today, can_review_notes)
            for note in overdue_actions[:8]
        ],
        'upcomingActions': [
            _notes_history_payload(note, today, can_review_notes)
            for note in upcoming_actions[:8]
        ],
        'upcomingSchedules': [
            _schedules_schedule_payload(schedule, today, _schedules_can_edit(request.user, schedule))
            for schedule in list(upcoming_schedules[:8])
        ],
        'recentSchedules': [
            _schedules_schedule_payload(schedule, today, _schedules_can_edit(request.user, schedule))
            for schedule in list(recent_schedules[:8])
        ],
    })


def _empty_department_account_detail_response(request, department, user_profile, scope_users, selected_user):
    can_manage_account = _can_manage_department_account(request.user, department)
    read_only_message = '' if can_manage_account else '이 계정은 현재 사용자에게 읽기 전용입니다.'
    account_href = f'/accounts/{department.id}/'
    account_prepayments_href = f'/prepayments/account/{department.id}/'
    today = timezone.localdate()
    can_review_notes = _can_review_notes(user_profile)
    notes_qs = _customer_account_notes_queryset(scope_users, department=department)
    from reporting.api.demos import demo_customer_summary_payload

    demo_summary = demo_customer_summary_payload(
        request,
        scope_users,
        department=department,
        can_manage=can_manage_account,
    )
    overdue_actions = _histories_excluding_stale_quote_submission(list(
        notes_qs.filter(
            next_action_date__lt=today,
            next_action_date__isnull=False,
            reviewed_at__isnull=True,
        ).order_by('next_action_date', '-created_at')
    ))
    upcoming_actions = _histories_excluding_stale_quote_submission(list(
        notes_qs.filter(
            next_action_date__gte=today,
            next_action_date__lte=today + timedelta(days=14),
            next_action_date__isnull=False,
            reviewed_at__isnull=True,
        ).order_by('next_action_date', '-created_at')
    ))
    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': _user_display_name(selected_user) if selected_user else (
                _user_display_name(request.user) if not user_profile.can_view_all_users()
                else f'{user_profile.company.name} 팀' if user_profile.company else '전체'
            ),
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'customer': _customers_empty_account_customer_payload(department, request.user),
        'account': _empty_department_account_payload(department, request, user_profile, can_manage_account),
        'metrics': {
            'recentNotes': notes_qs.count(),
            'upcomingSchedules': 0,
            'overdueActions': len(overdue_actions),
            'upcomingActions': len(upcoming_actions),
        },
        'links': {
            'customers': '/customers/',
            'accountDetail': account_href,
            'accountDeliveryRecordsXlsx': reverse('reporting:account_delivery_records_xlsx_export_api', args=[department.id]),
            'djangoDetail': '',
            'djangoEdit': reverse('reporting:department_edit', args=[department.id]),
            'createSchedule': '',
            'createNote': '',
            'deliveryRecordsXlsx': '',
            'pipeline': '/pipeline/',
        },
        'permissions': {
            'canCreateNote': False,
            'canCreateSchedule': False,
            'canManageAccount': can_manage_account,
            'canEditRepresentative': False,
            'canDeleteRepresentative': False,
            'readOnlyMessage': read_only_message,
        },
        'prepaymentSummary': {
            'metrics': {
                'totalAmount': 0,
                'totalBalance': 0,
                'totalUsed': 0,
                'totalCount': 0,
                'activeCount': 0,
                'depletedCount': 0,
                'cancelledCount': 0,
            },
            'links': {
                'prepayments': '/prepayments/',
                'createPrepayment': '/prepayments/new/',
                'accountPrepayments': account_prepayments_href,
                'customerPrepayments': '',
                'djangoCustomerPrepayments': '',
            },
            'recentPrepayments': [],
        },
        'operationalRecords': {
            'metrics': {
                'serviceRecords': 0,
                'quoteRecords': 0,
                'deliveryRecords': 0,
                'prepaymentDeliveryRecords': 0,
                'normalDeliveryRecords': 0,
                'prepaymentRecords': 0,
                'deliveryAmount': 0,
                'prepaymentDeliveryAmount': 0,
                'normalDeliveryAmount': 0,
                'prepaymentUsedAmount': 0,
            },
            'serviceRecords': [],
            'quoteRecords': [],
            'deliveryRecords': [],
            'prepaymentRecords': [],
            'prepaymentUsageRecords': [],
        },
        'demoSummary': demo_summary,
        'attachments': {
            'metrics': {
                'totalFiles': 0,
                'noteFiles': 0,
                'scheduleFiles': 0,
            },
            'recentFiles': [],
            'links': {
                'notes': '/notes/',
                'schedules': '/schedules/',
            },
        },
        'edit': {
            'canEdit': False,
            'canDelete': False,
            'message': '담당자를 먼저 추가하면 담당자 정보를 수정할 수 있습니다.',
            'submitUrl': '',
            'deleteUrl': '',
            'djangoUrl': '',
            'priorities': [{'value': value, 'label': label} for value, label in FollowUp.PRIORITY_CHOICES],
            'statuses': [{'value': value, 'label': label} for value, label in FollowUp.STATUS_CHOICES],
            'stages': [{'value': value, 'label': label} for value, label in FollowUp.PIPELINE_STAGE_CHOICES],
            'companies': [{'id': department.company_id, 'name': department.company.name}] if department.company_id else [],
            'departments': [{
                'id': department.id,
                'name': department.name,
                'companyId': department.company_id,
                'companyName': department.company.name if department.company_id else '',
                'searchText': '',
            }],
        },
        'recentNotes': [
            _notes_history_payload(note, today, can_review_notes)
            for note in list(notes_qs[:12])
        ],
        'overdueActions': [
            _notes_history_payload(note, today, can_review_notes)
            for note in overdue_actions[:8]
        ],
        'upcomingActions': [
            _notes_history_payload(note, today, can_review_notes)
            for note in upcoming_actions[:8]
        ],
        'upcomingSchedules': [],
        'recentSchedules': [],
    })


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def account_detail_summary_api(request, department_id):
    """React CRM department/lab account detail API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    department = get_object_or_404(
        Department.objects.select_related('company', 'created_by', 'company__created_by'),
        pk=department_id,
    )
    representative = account_representative_followup(department, scope_users)
    if representative is None:
        if _can_access_department_account(request.user, department, scope_users):
            return _empty_department_account_detail_response(request, department, user_profile, scope_users, selected_user)
        return JsonResponse({
            'success': False,
            'error': '접근 가능한 부서/연구실 계정이 없습니다.',
        }, status=403)
    return customer_detail_summary_api(request, representative.id)


@never_cache
@require_POST
def account_update_api(request, department_id):
    """React account detail account-level company/department/address/memo update API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, _selected_user = _dashboard_scope_users(request, user_profile)
    department = get_object_or_404(Department.objects.select_related('company'), pk=department_id)
    representative = account_representative_followup(department, scope_users)
    if representative is None:
        if not _can_access_department_account(request.user, department, scope_users):
            return JsonResponse({'success': False, 'error': '접근 가능한 부서/연구실 계정이 없습니다.'}, status=403)
    elif not can_access_followup(request.user, representative):
        return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)
    if not _can_manage_department_account(request.user, department):
        return JsonResponse({'success': False, 'error': '계정 관리 권한이 없습니다.'}, status=403)

    company_id = request.POST.get('company', '').strip()
    department_name = request.POST.get('department_name', '').strip()
    if not company_id:
        return JsonResponse({'success': False, 'error': '업체/학교를 선택해주세요.'}, status=400)
    if not department_name:
        return JsonResponse({'success': False, 'error': '부서/연구실명을 입력해주세요.'}, status=400)

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'error': '선택한 업체가 존재하지 않습니다.'}, status=400)

    management = _account_management_config(request, user_profile, department, True)
    allowed_company_ids = {company_option['id'] for company_option in management['companies']}
    if company.id not in allowed_company_ids:
        return JsonResponse({'success': False, 'error': '접근 권한이 없는 업체입니다.'}, status=403)
    if Department.objects.filter(company=company, name=department_name).exclude(pk=department.id).exists():
        return JsonResponse({'success': False, 'error': '같은 업체에 동일한 부서/연구실명이 이미 있습니다.'}, status=400)

    with transaction.atomic():
        department.company = company
        department.name = department_name
        department.address = request.POST.get('address', '').strip()
        department.notes = request.POST.get('notes', '').strip()
        department.save(update_fields=['company', 'name', 'address', 'notes', 'updated_at'])
        FollowUp.objects.filter(department=department).exclude(company=company).update(company=company)

    return JsonResponse({
        'success': True,
        'departmentId': department.id,
        'href': f'/accounts/{department.id}/',
        'message': '계정 정보를 저장했습니다.',
    })


@never_cache
@require_POST
def account_contact_save_api(request, department_id, followup_id=None):
    """Create/update/move/deactivate a contact from the React account detail screen."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, _selected_user = _dashboard_scope_users(request, user_profile)
    department = get_object_or_404(Department.objects.select_related('company'), pk=department_id)
    representative = account_representative_followup(department, scope_users)
    if representative is None:
        if not _can_access_department_account(request.user, department, scope_users):
            return JsonResponse({'success': False, 'error': '접근 가능한 부서/연구실 계정이 없습니다.'}, status=403)
    elif not can_access_followup(request.user, representative):
        return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)

    contact = None
    is_create = followup_id is None
    if is_create:
        if not _can_manage_department_account(request.user, department):
            return JsonResponse({'success': False, 'error': '담당자 추가 권한이 없습니다.'}, status=403)
    else:
        contact = get_object_or_404(
            FollowUp.objects.select_related('user', 'company', 'department'),
            pk=followup_id,
            department=department,
        )
        if not can_modify_user_data(request.user, contact.user):
            return JsonResponse({'success': False, 'error': '이 담당자 수정 권한이 없습니다.'}, status=403)

    customer_name = request.POST.get('customer_name', '').strip()
    if not customer_name:
        return JsonResponse({'success': False, 'error': '담당자명을 입력해주세요.'}, status=400)

    contact_role = request.POST.get('contact_role', '').strip() or FollowUp.CONTACT_ROLE_PRACTITIONER
    if contact_role not in {value for value, _label in FollowUp.CONTACT_ROLE_CHOICES}:
        return JsonResponse({'success': False, 'error': '올바른 담당자 역할을 선택해주세요.'}, status=400)

    target_department_id = request.POST.get('department', '').strip() or str(department.id)
    try:
        target_department = Department.objects.select_related('company').get(id=target_department_id)
    except Department.DoesNotExist:
        return JsonResponse({'success': False, 'error': '이동할 부서/연구실을 찾을 수 없습니다.'}, status=400)

    management = _account_management_config(request, user_profile, department, True)
    allowed_department_ids = {department_option['id'] for department_option in management['departments']}
    if target_department.id not in allowed_department_ids:
        return JsonResponse({'success': False, 'error': '접근 권한이 없는 부서/연구실입니다.'}, status=403)

    status = request.POST.get('status', '').strip() or 'active'
    pipeline_stage = request.POST.get('pipeline_stage', '').strip() or 'potential'
    if status not in {value for value, _label in FollowUp.STATUS_CHOICES}:
        return JsonResponse({'success': False, 'error': '올바른 상태를 선택해주세요.'}, status=400)
    if pipeline_stage not in {value for value, _label in FollowUp.PIPELINE_STAGE_CHOICES}:
        return JsonResponse({'success': False, 'error': '올바른 파이프라인 단계를 선택해주세요.'}, status=400)

    is_active = _parse_form_bool(request.POST.get('is_active'), True)
    duplicate_qs = FollowUp.objects.filter(
        customer_name=customer_name,
        company=target_department.company,
        department=target_department,
        user=request.user if is_create else contact.user,
    )
    if contact:
        duplicate_qs = duplicate_qs.exclude(pk=contact.pk)
    if duplicate_qs.exists():
        return JsonResponse({'success': False, 'error': '같은 계정에 동일한 담당자가 이미 있습니다.'}, status=400)

    with transaction.atomic():
        if is_create:
            contact = FollowUp(
                user=request.user,
                user_company=user_profile.company,
                company=target_department.company,
                department=target_department,
            )
            contact.priority = 'scheduled'
        contact.customer_name = customer_name
        contact.manager = request.POST.get('manager', '').strip()
        contact.contact_role = contact_role
        contact.phone_number = request.POST.get('phone_number', '').strip()
        contact.email = request.POST.get('email', '').strip()
        contact.address = request.POST.get('address', '').strip()
        contact.notes = request.POST.get('notes', '').strip()
        contact.status = status
        contact.pipeline_stage = pipeline_stage
        contact._stage_change_actor = request.user
        contact.is_active = is_active
        contact.company = target_department.company
        contact.department = target_department
        contact.save()

    return JsonResponse({
        'success': True,
        'followup_id': contact.id,
        'href': f'/customers/{contact.id}/',
        'accountHref': f'/accounts/{target_department.id}/',
        'message': '담당자를 저장했습니다.' if is_create else '담당자 정보를 저장했습니다.',
        'contact': _customer_account_contact_payload(
            contact,
            can_manage=can_modify_user_data(request.user, contact.user),
        ),
    })


def customer_delivery_records_xlsx_export_api(request, followup_id):
    """React 고객 상세의 고객별 납품 기록만 XLSX로 다운로드."""
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from urllib.parse import quote

    user_profile = get_user_profile(request.user)
    followup = get_object_or_404(
        FollowUp.objects.select_related('user', 'company', 'department'),
        pk=followup_id,
    )
    if not can_access_followup(request.user, followup):
        return HttpResponseForbidden('접근 권한이 없습니다.')

    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    delivery_records = _customer_delivery_record_payloads(followup, scope_users, limit=None)

    wb = Workbook()
    ws = wb.active
    ws.title = '납품 기록'

    headers = [
        '납품일', '일정ID', '고객명', '업체/학교', '부서/연구실', '담당자',
        '상태', '납품구분', '결제상태', '선결제차감액', '품목명', '수량', '단위',
        '단가', '품목금액', '일정납품합계', '비고', '구분근거', '일정링크',
    ]
    ws.append(headers)

    header_fill = PatternFill(fill_type='solid', fgColor='1F2937')
    header_font = Font(bold=True, color='FFFFFF')
    thin_side = Side(style='thin', color='D1D5DB')
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    body_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    money_format = '#,##0'

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border

    for record in delivery_records:
        items = record.get('items') or [None]
        for item in items:
            row = [
                record.get('date') or '',
                record.get('id') or '',
                record.get('customerName') or '',
                record.get('companyName') or '',
                record.get('departmentName') or '',
                record.get('ownerName') or '',
                record.get('statusLabel') or '',
                record.get('paymentSourceLabel') or '',
                record.get('paymentStatusLabel') or '',
                record.get('prepaymentAmount') or 0,
                item.get('itemName') if item else '',
                item.get('quantity') if item else '',
                item.get('unit') if item else '',
                item.get('unitPrice') if item and item.get('unitPrice') is not None else '',
                item.get('totalPrice') if item and item.get('totalPrice') is not None else '',
                record.get('totalAmount') or 0,
                record.get('notes') or '',
                record.get('paymentEvidence') or '',
                request.build_absolute_uri(record.get('href') or '') if record.get('href') else '',
            ]
            ws.append(row)

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.border = border
            cell.alignment = body_alignment
        for col_idx in [10, 14, 15, 16]:
            row[col_idx - 1].number_format = money_format

    widths = [12, 10, 18, 22, 20, 12, 12, 18, 16, 14, 24, 10, 8, 12, 14, 16, 32, 46, 42]
    for col_idx, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions

    info = wb.create_sheet(title='다운로드 정보')
    info_rows = [
        ('고객', followup.customer_name or followup.manager or ''),
        ('업체/학교', followup.company.name if followup.company else ''),
        ('부서/연구실', followup.department.name if followup.department else ''),
        ('범위', _user_display_name(selected_user) if selected_user else (
            f'{user_profile.company.name} 팀' if user_profile.company and user_profile.can_view_all_users() else _user_display_name(request.user)
        )),
        ('납품 일정 수', len(delivery_records)),
        ('생성일시', timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')),
        ('생성자', _user_display_name(request.user)),
    ]
    for row in info_rows:
        info.append(row)
    info.column_dimensions['A'].width = 16
    info.column_dimensions['B'].width = 42

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    label = '_'.join([
        part for part in [
            followup.company.name if followup.company else '',
            followup.department.name if followup.department else '',
            followup.customer_name or followup.manager or f'customer_{followup.id}',
        ] if part
    ])
    safe_label = re.sub(r'[\\/:*?"<>|]+', '_', label).strip()[:80] or f'customer_{followup.id}'
    filename = f'{safe_label}_납품기록_{timezone.localdate().strftime("%Y%m%d")}.xlsx'
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    wb.save(response)
    return response


@never_cache
@login_required
@require_http_methods(["GET"])
def account_delivery_records_xlsx_export_api(request, department_id):
    user_profile = get_user_profile(request.user)
    scope_users, _selected_user = _dashboard_scope_users(request, user_profile)
    department = get_object_or_404(Department.objects.select_related('company'), pk=department_id)
    representative = account_representative_followup(department, scope_users)
    if representative is None:
        return HttpResponseForbidden('접근 가능한 부서/연구실 계정이 없습니다.')
    return customer_delivery_records_xlsx_export_api(request, representative.id)


@never_cache
@require_POST
def customer_update_api(request, followup_id):
    """React 고객 상세 화면용 고객 기본정보 수정 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    followup = get_object_or_404(
        FollowUp.objects.select_related('user', 'company', 'department'),
        pk=followup_id,
    )
    if not can_access_followup(request.user, followup):
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없습니다.',
        }, status=403)
    if not can_modify_user_data(request.user, followup.user):
        return JsonResponse({
            'success': False,
            'error': '수정 권한이 없습니다.',
        }, status=403)

    customer_name = request.POST.get('customer_name', '').strip()
    company_id = request.POST.get('company', '').strip()
    department_id = request.POST.get('department', '').strip()
    status = request.POST.get('status', '').strip()
    pipeline_stage = request.POST.get('pipeline_stage', '').strip()

    if not customer_name:
        return JsonResponse({'success': False, 'error': '고객명을 입력해주세요.'}, status=400)
    if not company_id:
        return JsonResponse({'success': False, 'error': '업체/학교를 선택해주세요.'}, status=400)
    if not department_id:
        return JsonResponse({'success': False, 'error': '부서/연구실을 선택해주세요.'}, status=400)
    if status not in {value for value, _label in FollowUp.STATUS_CHOICES}:
        return JsonResponse({'success': False, 'error': '올바른 상태를 선택해주세요.'}, status=400)
    if pipeline_stage not in {value for value, _label in FollowUp.PIPELINE_STAGE_CHOICES}:
        return JsonResponse({'success': False, 'error': '올바른 파이프라인 단계를 선택해주세요.'}, status=400)

    try:
        company = Company.objects.get(id=company_id)
        department = Department.objects.get(id=department_id, company=company)
    except (Company.DoesNotExist, Department.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': '선택한 업체 또는 부서가 존재하지 않습니다.',
        }, status=400)

    user_profile = get_user_profile(request.user)
    edit_config = _customers_edit_config(request, user_profile, followup, True)
    allowed_company_ids = {company_option['id'] for company_option in edit_config['companies']}
    allowed_department_ids = {department_option['id'] for department_option in edit_config['departments']}
    if company.id not in allowed_company_ids or department.id not in allowed_department_ids:
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없는 업체 또는 부서입니다.',
        }, status=403)

    pipeline_changed = followup.pipeline_stage != pipeline_stage
    followup.customer_name = customer_name
    followup.company = company
    followup.department = department
    followup.manager = request.POST.get('manager', '').strip()
    followup.phone_number = request.POST.get('phone_number', '').strip()
    followup.email = request.POST.get('email', '').strip()
    followup.address = request.POST.get('address', '').strip()
    followup.notes = request.POST.get('notes', '').strip()
    followup.status = status
    followup.pipeline_stage = pipeline_stage
    followup._stage_change_actor = request.user
    if pipeline_changed:
        followup.pipeline_manually_set = True
    followup.save(update_fields=[
        'customer_name',
        'company',
        'department',
        'manager',
        'phone_number',
        'email',
        'address',
        'notes',
        'status',
        'pipeline_stage',
        'pipeline_manually_set',
        'updated_at',
    ])

    return JsonResponse({
        'success': True,
        'followup_id': followup.id,
        'href': f'/customers/{followup.id}/',
        'django_href': reverse('reporting:followup_detail', args=[followup.id]),
        'message': '고객 정보가 수정되었습니다.',
    })


@never_cache
@require_POST
def customer_delete_api(request, followup_id):
    """React 고객 상세 화면용 고객 삭제 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    followup = get_object_or_404(
        FollowUp.objects.select_related('user', 'company', 'department'),
        pk=followup_id,
    )
    if not can_access_followup(request.user, followup):
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없습니다.',
        }, status=403)
    if not can_modify_user_data(request.user, followup.user):
        return JsonResponse({
            'success': False,
            'error': '삭제 권한이 없습니다.',
        }, status=403)

    customer_label = followup.customer_name or followup.manager or '고객'
    followup.delete()
    return JsonResponse({
        'success': True,
        'href': '/customers/',
        'message': f'{customer_label} 고객 정보를 삭제했습니다.',
    })


def _history_legacy_meeting_activity_text(history):
    """Return old structured meeting text as a display-only fallback."""
    parts = [
        history.meeting_situation,
        history.meeting_researcher_quote,
        history.meeting_confirmed_facts,
        history.meeting_obstacles,
    ]
    return '\n'.join(str(part).strip() for part in parts if str(part or '').strip())


def _history_activity_content(history):
    content = str(history.content or '').strip()
    if content:
        return content
    return _history_legacy_meeting_activity_text(history)


def _notes_history_payload(history, today, can_review=False):
    followup = history.followup
    department = history.department or (followup.department if followup and followup.department else None)
    company = followup.company if followup and followup.company else (department.company if department and department.company else None)
    customer = (
        followup.customer_name or followup.manager or '고객명 미정'
    ) if followup else ('담당자 미등록' if department else '일반 메모')
    # 노트의 날짜는 "그 활동이 있었던 날"이다 — 연결된 일정이 미래(다음 일정)면
    # 그 날짜를 쓰지 않는다. 쓰면 오늘 적은 노트가 미래 날짜로 표시되고, 목록
    # 정렬/조회 구간에서도 튀어나가 찾을 수 없게 된다. 다음 일정 자체는 일정기록에
    # 남으므로 노트가 그 날짜를 대신 들고 있을 이유가 없다.
    activity_date = history.meeting_date or history.delivery_date
    if not activity_date and history.schedule_id and history.schedule:
        if history.schedule.visit_date and history.schedule.visit_date <= today:
            activity_date = history.schedule.visit_date
    if not activity_date and history.personal_schedule_id and history.personal_schedule:
        if history.personal_schedule.schedule_date and history.personal_schedule.schedule_date <= today:
            activity_date = history.personal_schedule.schedule_date
    if not activity_date:
        # created_at 은 UTC 로 저장된다 — `.date()` 를 그냥 쓰면 한국시간 오전 9시
        # 전에 적은 노트가 어제 날짜로 보인다. 목록 정렬은 ORM 의 `created_at__date`
        # (TIME_ZONE 기준 변환)를 쓰므로 여기서도 로컬 기준으로 맞춰야 어긋나지 않는다.
        activity_date = timezone.localtime(history.created_at).date()

    next_action = (history.next_action or history.meeting_next_action or '').strip()
    next_action_date = history.next_action_date
    next_action_display = next_action or ('후속 예정' if next_action_date else '')
    review_required_types = {'customer_meeting', 'delivery_schedule', 'quote', 'service'}
    review_required = history.action_type in review_required_types
    reviewed_at = history.reviewed_at
    reviewer = history.reviewer
    delivery_summary_text, _delivery_summary_amount = _history_effective_delivery_summary(history)
    activity_content = _history_activity_content(history)

    return {
        'id': history.id,
        'customer': customer,
        'company': company.name if company else '',
        'department': department.name if department else '',
        'departmentId': department.id if department else None,
        'owner': _user_display_name(history.user),
        'ownerId': history.user_id,
        'actionType': history.action_type,
        'actionLabel': history.get_action_type_display(),
        'serviceStatus': history.service_status or '',
        'serviceStatusLabel': history.get_service_status_display() if history.service_status else '',
        'summary': (activity_content or delivery_summary_text or '').strip()[:180],
        'nextAction': next_action[:160],
        'nextActionDisplay': next_action_display[:160],
        'nextActionDate': _date_or_none(next_action_date),
        'overdue': bool(next_action_date and next_action_date < today and not reviewed_at),
        'activityDate': _date_or_none(activity_date),
        'createdAt': _datetime_or_none(history.created_at),
        'reviewed': bool(reviewed_at),
        'reviewedAt': _datetime_or_none(reviewed_at),
        'reviewer': _user_display_name(reviewer) if reviewer else '',
        'reviewRequired': review_required,
        'canReview': bool(can_review and review_required),
        'reviewToggleHref': reverse('reporting:history_toggle_reviewed', args=[history.id]) if can_review and review_required else '',
        'replyCount': int(getattr(history, 'reply_count', 0) or 0),
        'fileCount': int(getattr(history, 'file_count', 0) or 0),
        'href': f'/notes/{history.id}/',
        'djangoHref': reverse('reporting:history_detail', args=[history.id]),
        'customerHref': f'/customers/{followup.id}/' if followup else (f'/accounts/{department.id}/' if department else ''),
        'djangoCustomerHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
        'scheduleHref': f'/schedules/{history.schedule_id}/' if history.schedule_id else '',
        'djangoScheduleHref': reverse('reporting:schedule_detail', args=[history.schedule_id]) if history.schedule_id else '',
    }


def _history_effective_delivery_summary(history):
    if (
        history.action_type == 'delivery_schedule'
        and history.schedule_id
        and history.schedule
    ):
        if history.schedule.activity_type == 'delivery':
            delivery_items = list(history.schedule.delivery_items_set.all().order_by('id'))
            if delivery_items:
                return _product_delivery_items_summary(delivery_items)
        if history.schedule.activity_type == 'quote':
            quote_delivery_text, quote_delivery_amount = _quote_schedule_actual_delivery_summary(history.schedule)
            if quote_delivery_text or quote_delivery_amount:
                return quote_delivery_text, quote_delivery_amount
            return '', 0
    return history.delivery_items or '', _money_int(history.delivery_amount)


def _quantity_label_value(quantity):
    from decimal import Decimal

    parsed = Decimal(str(quantity or 0))
    if parsed == parsed.to_integral_value():
        return str(int(parsed))
    return format(parsed.normalize(), 'f')


def _delivery_item_entries_summary(item_entries):
    from decimal import Decimal

    delivery_lines = []
    total_amount = Decimal('0')
    for item, quantity in item_entries:
        item_total = item.total_price
        if Decimal(str(quantity or 0)) != Decimal(str(item.quantity or 0)):
            item_total = _schedules_quote_item_total_for_quantity(item, quantity)
        elif item_total is None and item.unit_price is not None:
            item_total = vat.item_gross_total(item, unit_price=(item.get_effective_unit_price() or item.unit_price))
        if item_total is not None:
            total_amount += item_total

        quantity_label = f"{_quantity_label_value(quantity)}{item.unit or 'EA'}"
        if item_total is not None:
            delivery_lines.append(f"{item.item_name}: {quantity_label} ({int(item_total):,}원)")
        else:
            delivery_lines.append(f"{item.item_name}: {quantity_label}")

    return '\n'.join(delivery_lines), int(total_amount) if total_amount > 0 else 0


def _quote_schedule_actual_delivery_summary(quote_schedule):
    from decimal import Decimal

    quote_items = list(quote_schedule.delivery_items_set.all().order_by('id'))
    if not quote_items:
        return '', 0

    remaining_by_identity = {}
    for quote_item in quote_items:
        key = _schedules_quote_item_identity(quote_item)
        remaining_by_identity[key] = remaining_by_identity.get(key, Decimal('0')) + Decimal(str(quote_item.quantity or 0))

    delivered_entries = []
    delivered_item_ids = set()

    def add_delivered_item(item, quantity=None, identity_key=None, cap_to_quote=False):
        if item.id in delivered_item_ids:
            return

        key = identity_key or _schedules_quote_item_identity(item)
        parsed_quantity = Decimal(str(quantity if quantity is not None else item.quantity or 0))
        if cap_to_quote:
            remaining_quantity = remaining_by_identity.get(key, Decimal('0'))
            if remaining_quantity <= 0:
                return
            parsed_quantity = min(parsed_quantity, remaining_quantity)
        if parsed_quantity <= 0:
            return

        delivered_entries.append((item, parsed_quantity))
        delivered_item_ids.add(item.id)
        if key in remaining_by_identity:
            remaining_by_identity[key] = max(Decimal('0'), remaining_by_identity[key] - parsed_quantity)

    linked_items = DeliveryItem.objects.filter(
        schedule__activity_type='delivery',
    ).exclude(
        schedule__status='cancelled',
    ).filter(
        Q(source_quote_schedule=quote_schedule) | Q(source_quote_item__in=quote_items),
    ).select_related(
        'schedule',
        'source_quote_item',
    ).order_by('schedule__visit_date', 'schedule__visit_time', 'id')

    for item in linked_items:
        source_item = item.source_quote_item if item.source_quote_item_id else None
        source_key = _schedules_quote_item_identity(source_item) if source_item else _schedules_quote_item_identity(item)
        add_delivered_item(item, identity_key=source_key)

    legacy_delivery_schedules = Schedule.objects.filter(
        user_id=quote_schedule.user_id,
        activity_type='delivery',
    ).exclude(status='cancelled')
    if quote_schedule.followup_id:
        legacy_delivery_schedules = legacy_delivery_schedules.filter(followup_id=quote_schedule.followup_id)
    if quote_schedule.visit_date:
        legacy_delivery_schedules = legacy_delivery_schedules.filter(visit_date__gte=quote_schedule.visit_date)

    legacy_items = DeliveryItem.objects.filter(
        schedule__in=legacy_delivery_schedules,
        source_quote_schedule__isnull=True,
        source_quote_item__isnull=True,
    ).select_related('schedule').order_by('schedule__visit_date', 'schedule__visit_time', 'id')

    for item in legacy_items:
        key = _schedules_quote_item_identity(item)
        if key in remaining_by_identity:
            add_delivered_item(item, identity_key=key, cap_to_quote=True)

    if not delivered_entries:
        return '', 0
    return _delivery_item_entries_summary(delivered_entries)


def _notes_schedule_suggested_action_type(schedule):
    if schedule.activity_type == 'delivery':
        return 'delivery_schedule'
    if schedule.activity_type == 'quote':
        return 'quote'
    if schedule.activity_type == 'service':
        return 'service'
    return 'customer_meeting'


def _notes_schedule_delivery_summary(schedule):
    if not schedule:
        return '', 0
    if schedule.activity_type == 'delivery':
        delivery_items = list(schedule.delivery_items_set.all().order_by('id'))
        if delivery_items:
            return _product_delivery_items_summary(delivery_items)
    if schedule.activity_type == 'quote':
        return _quote_schedule_actual_delivery_summary(schedule)
    return '', 0


def _notes_create_schedule_payload(schedule):
    followup = schedule.followup
    department_obj = schedule.department or (followup.department if followup and followup.department else None)
    company_obj = followup.company if followup and followup.company else (department_obj.company if department_obj and department_obj.company else None)
    customer = (
        followup.customer_name or followup.manager or '고객명 미정'
    ) if followup else '담당자 미등록'
    company = company_obj.name if company_obj else ''
    department = department_obj.name if department_obj else ''
    time_label = schedule.visit_time.strftime('%H:%M') if schedule.visit_time else ''
    delivery_text, delivery_amount = _notes_schedule_delivery_summary(schedule)
    label_parts = [
        _date_or_none(schedule.visit_date),
        time_label,
        schedule.get_activity_type_display(),
        company,
        department,
        customer,
    ]
    return {
        'id': schedule.id,
        'followupId': schedule.followup_id,
        'departmentId': department_obj.id if department_obj else None,
        'label': ' · '.join(str(part) for part in label_parts if part) or f'일정 #{schedule.id}',
        'customer': customer,
        'company': company,
        'department': department,
        'activityType': schedule.activity_type,
        'activityLabel': schedule.get_activity_type_display(),
        'date': _date_or_none(schedule.visit_date),
        'time': time_label,
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'deliveryItems': delivery_text,
        'deliveryAmount': delivery_amount,
        'suggestedActionType': _notes_schedule_suggested_action_type(schedule),
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
    }


def _can_review_notes(user_profile):
    """영업노트 검토는 각 소속 회사의 manager 계정만 처리한다."""
    return bool(user_profile.is_manager() and user_profile.company_id)


def _notes_create_action_types(request):
    excluded_types = {'memo'}
    if not getattr(request, 'is_hanagwahak', False):
        excluded_types.add('service')
    return [
        {'value': value, 'label': label}
        for value, label in History.ACTION_CHOICES
        if value not in excluded_types
    ]


def _department_target_scope_users(user):
    user_profile = get_user_profile(user)
    return get_same_company_users(user) if user_profile.can_view_all_users() else User.objects.filter(id=user.id)


def _department_targets_queryset(user):
    user_profile = get_user_profile(user)
    scope_users = _department_target_scope_users(user)
    qs = Department.objects.select_related('company')
    if not user_profile.is_admin():
        qs = qs.filter(
            Q(created_by__in=scope_users) |
            Q(company__created_by__in=scope_users) |
            Q(followup_departments__user__in=scope_users)
        )
    return qs.annotate(
        customer_count=Count(
            'followup_departments',
            filter=Q(followup_departments__user__in=scope_users),
            distinct=True,
        )
    ).distinct()


def _department_create_targets(user, limit=800):
    return list(_department_targets_queryset(user).order_by('company__name', 'name')[:limit])


def _department_target_for_user(user, department_id):
    try:
        parsed_id = int(department_id or 0)
    except (TypeError, ValueError):
        parsed_id = 0
    if parsed_id <= 0:
        return None
    return _department_targets_queryset(user).filter(id=parsed_id).first()


def _department_has_own_contacts(user, department):
    if not user or not department:
        return False
    return FollowUp.objects.filter(user=user, department=department).exists()


def _department_create_target_search_text_map(user, departments):
    return _customers_department_search_text_map(departments, _department_target_scope_users(user))


def _department_create_target_payload(department, search_text=''):
    company = department.company.name if department.company else ''
    customer_count = int(getattr(department, 'customer_count', 0) or 0)
    label = ' · '.join(part for part in [company, department.name] if part) or f'부서 #{department.id}'
    return {
        'id': department.id,
        'label': label,
        'name': department.name,
        'department': department.name,
        'departmentName': department.name,
        'company': company,
        'companyName': company,
        'customerCount': customer_count,
        'hasCustomers': customer_count > 0,
        'searchText': ' '.join(part for part in [company, department.name, department.notes, search_text] if part),
        'href': f'/accounts/{department.id}/',
    }


def _notes_create_targets(user, limit=120):
    return list(FollowUp.objects.filter(
        user=user,
    ).select_related(
        'company', 'department'
    ).order_by('-updated_at', 'company__name', 'customer_name')[:limit])


def _notes_edit_targets(user, limit=160):
    return list(FollowUp.objects.filter(
        user__in=get_same_company_users(user),
    ).select_related(
        'company', 'department'
    ).order_by('-updated_at', 'company__name', 'customer_name')[:limit])


def _notes_create_target_payload(followup):
    customer = followup.customer_name or followup.manager or '고객명 미정'
    company = followup.company.name if followup.company else ''
    department = followup.department.name if followup.department else ''
    label_parts = [part for part in [company, department, customer] if part]
    return {
        'id': followup.id,
        'departmentId': followup.department_id,
        'companyId': followup.company_id,
        'label': ' · '.join(label_parts) or customer,
        'customer': customer,
        'company': company,
        'department': department,
        'priorityLabel': followup.get_priority_display(),
        'href': f'/customers/{followup.id}/',
        'djangoHref': reverse('reporting:followup_detail', args=[followup.id]),
    }


def _parse_iso_date_or_none(value):
    from datetime import date

    value = str(value or '').strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


_NOTE_FOLLOWUP_SCHEDULE_MARKER = '자동 생성: 영업노트 후속 미팅'
_NOTE_FOLLOWUP_SCHEDULE_TIME = time(9, 0)


def _notes_followup_schedule_notes(history):
    parts = [
        _NOTE_FOLLOWUP_SCHEDULE_MARKER,
        f'원본 노트: /notes/{history.id}/',
    ]
    next_action = (history.next_action or '').strip()
    if next_action:
        parts.append(f'다음 액션: {next_action}')
    return '\n'.join(parts)


def _notes_find_existing_followup_schedule(user, followup, department, next_action_date):
    queryset = Schedule.objects.filter(
        user=user,
        activity_type='customer_meeting',
        status='scheduled',
        visit_date=next_action_date,
    )
    if followup:
        queryset = queryset.filter(followup=followup)
    elif department:
        queryset = queryset.filter(followup__isnull=True, department=department)
    else:
        return None
    return queryset.order_by('visit_time', 'id').first()


def _notes_create_followup_schedule_for_history(history):
    next_action_date = history.next_action_date
    followup = history.followup
    department = history.department or (followup.department if followup and followup.department else None)
    if not next_action_date or (not followup and not department):
        return None, False

    existing_schedule = _notes_find_existing_followup_schedule(
        history.user,
        followup,
        department,
        next_action_date,
    )
    if existing_schedule:
        return existing_schedule, False

    schedule = Schedule.objects.create(
        user=history.user,
        company=history.company,
        followup=followup,
        department=department,
        visit_date=next_action_date,
        visit_time=_NOTE_FOLLOWUP_SCHEDULE_TIME,
        activity_type='customer_meeting',
        status='scheduled',
        notes=_notes_followup_schedule_notes(history),
    )
    return schedule, True


def _notes_action_types_for_edit(request, history):
    action_types = _notes_create_action_types(request)
    action_values = {item['value'] for item in action_types}
    if history.action_type not in action_values:
        action_labels = dict(History.ACTION_CHOICES)
        action_types = [
            {
                'value': history.action_type,
                'label': action_labels.get(history.action_type, history.action_type),
            },
            *action_types,
        ]
    return action_types


def _notes_edit_config(request, history, can_edit):
    editable_history = history.parent_history_id is None and history.action_type != 'memo'
    allowed_customers = _notes_edit_targets(history.user) if can_edit and editable_history else []
    allowed_departments = _department_create_targets(history.user) if can_edit and editable_history else []
    if history.followup_id and can_edit and editable_history:
        allowed_customer_ids = {followup.id for followup in allowed_customers}
        if history.followup_id not in allowed_customer_ids:
            allowed_customers = [history.followup, *allowed_customers]
    if history.department_id and can_edit and editable_history:
        allowed_department_ids = {department.id for department in allowed_departments}
        if history.department_id not in allowed_department_ids and history.department:
            allowed_departments = [history.department, *allowed_departments]
    message = ''
    if not editable_history:
        message = '메모 또는 댓글은 React 영업노트 수정 대상이 아닙니다.'
    elif not can_edit:
        message = '수정 권한이 없습니다.'

    department_search_map = _department_create_target_search_text_map(history.user, allowed_departments) if allowed_departments else {}

    return {
        'canEdit': bool(can_edit and editable_history),
        'message': message,
        'submitUrl': reverse('reporting:notes_update_api', args=[history.id]) if editable_history else '',
        'djangoUrl': reverse('reporting:history_edit', args=[history.id]) if editable_history else '',
        'actionTypes': _notes_action_types_for_edit(request, history),
        'serviceStatuses': [
            {'value': value, 'label': label}
            for value, label in History.SERVICE_STATUS_CHOICES
        ],
        'departments': [
            _department_create_target_payload(department, department_search_map.get(department.id, ''))
            for department in allowed_departments
        ],
        'customers': [_notes_create_target_payload(followup) for followup in allowed_customers],
    }


def _file_size_label(size):
    size = int(size or 0)
    if size < 1024:
        return f'{size} bytes'
    if size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    return f'{size / (1024 * 1024):.1f} MB'


def _notes_can_add_reply(user, history):
    if history.parent_history_id or history.action_type == 'memo':
        return False

    user_profile = get_user_profile(user)
    if user_profile.is_manager():
        return bool(user == history.user or can_access_user_data(user, history.user))

    return user == history.user


def _notes_can_delete_reply(user, reply):
    if reply.action_type != 'memo' or not reply.parent_history_id:
        return False
    if reply.created_by_id:
        return reply.created_by_id == user.id
    return reply.user_id == user.id


def _notes_can_delete_history(user, history):
    return bool(
        can_modify_user_data(user, history.user) and
        history.parent_history_id is None and
        history.action_type != 'memo'
    )


def _notes_reply_payload(request, reply):
    can_delete = _notes_can_delete_reply(request.user, reply)
    is_manager_memo = bool(reply.created_by_id and reply.created_by_id != reply.user_id)
    return {
        'id': reply.id,
        'content': (reply.content or '').strip(),
        'author': _user_display_name(reply.created_by or reply.user),
        'authorRole': '매니저 메모' if is_manager_memo else '댓글',
        'createdAt': _datetime_or_none(reply.created_at),
        'djangoHref': reverse('reporting:history_detail', args=[reply.id]),
        'deleteHref': reverse('reporting:delete_manager_memo_api', args=[reply.id]) if can_delete else '',
        'canDelete': can_delete,
    }


def _notes_detail_payload(request, history, user_profile):
    today = timezone.localdate()
    can_review = _can_review_notes(user_profile)
    can_edit = can_modify_user_data(request.user, history.user)
    detail_can_edit = bool(can_edit and history.parent_history_id is None and history.action_type != 'memo')
    detail_can_delete = _notes_can_delete_history(request.user, history)
    can_add_reply = _notes_can_add_reply(request.user, history)
    history.reply_count = history.reply_memos.count()
    history.file_count = history.files.count()
    note_payload = _notes_history_payload(history, today, can_review)
    followup = history.followup
    department = history.department or (followup.department if followup and followup.department else None)
    schedule = history.schedule
    delivery_summary_text, delivery_summary_amount = _history_effective_delivery_summary(history)

    files = [
        {
            'id': file.id,
            'filename': file.original_filename,
            'size': _file_size_label(file.file_size),
            'downloadHref': reverse('reporting:file_download', args=[file.id]),
            'deleteHref': reverse('reporting:file_delete', args=[file.id]) if detail_can_edit else '',
            'canDelete': detail_can_edit,
            'uploadedAt': _datetime_or_none(file.uploaded_at),
        }
        for file in history.files.all().order_by('-uploaded_at')
    ]
    replies = [
        _notes_reply_payload(request, reply)
        for reply in history.reply_memos.select_related('created_by', 'user').order_by('created_at')
    ]

    detail = {
        **note_payload,
        'content': _history_activity_content(history),
        'createdBy': _user_display_name(history.created_by) if history.created_by else '',
        'followupId': history.followup_id,
        'departmentId': department.id if department else None,
        'scheduleId': history.schedule_id,
        'personalScheduleId': history.personal_schedule_id,
        'meetingDate': _date_or_none(history.meeting_date),
        'meetingSituation': history.meeting_situation or '',
        'meetingResearcherQuote': history.meeting_researcher_quote or '',
        'meetingConfirmedFacts': history.meeting_confirmed_facts or '',
        'meetingObstacles': history.meeting_obstacles or '',
        'meetingNextAction': history.meeting_next_action or '',
        'deliveryDate': _date_or_none(history.delivery_date),
        'deliveryAmount': delivery_summary_amount,
        'deliveryItems': delivery_summary_text,
        'taxInvoiceIssued': bool(history.tax_invoice_issued),
        'files': files,
        'replies': replies,
        'canEdit': detail_can_edit,
        'canDelete': detail_can_delete,
        'deleteHref': reverse('reporting:notes_delete_api', args=[history.id]) if detail_can_delete else '',
    }

    related_notes = []
    if followup:
        related_qs = History.objects.filter(
            followup=followup,
            parent_history__isnull=True,
        ).exclude(
            id=history.id,
        ).exclude(
            action_type='memo',
        ).select_related(
            'user', 'followup', 'followup__company', 'followup__department', 'schedule', 'personal_schedule', 'reviewer'
        ).annotate(
            reply_count=Count('reply_memos', distinct=True),
            file_count=Count('files', distinct=True),
        ).order_by('-created_at')[:8]
        related_notes = [
            _notes_history_payload(related, today, can_review)
            for related in related_qs
            if can_access_user_data(request.user, related.user)
        ]
    elif department:
        related_qs = History.objects.filter(
            department=department,
            parent_history__isnull=True,
        ).exclude(
            id=history.id,
        ).exclude(
            action_type='memo',
        ).select_related(
            'user',
            'followup',
            'followup__company',
            'followup__department',
            'department',
            'department__company',
            'schedule',
            'personal_schedule',
            'reviewer',
        ).annotate(
            reply_count=Count('reply_memos', distinct=True),
            file_count=Count('files', distinct=True),
        ).order_by('-created_at')[:8]
        related_notes = [
            _notes_history_payload(related, today, can_review)
            for related in related_qs
            if can_access_user_data(request.user, related.user)
        ]

    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': _user_display_name(history.user),
            'userCount': 1,
            'canViewAll': user_profile.can_view_all_users(),
            'canReview': can_review,
            'selectedUserId': history.user_id,
        },
        'note': detail,
        'links': {
            'notes': '/notes/',
            'djangoDetail': reverse('reporting:history_detail', args=[history.id]),
            'djangoEdit': reverse('reporting:history_edit', args=[history.id]),
            'customer': f'/customers/{followup.id}/' if followup else (f'/accounts/{department.id}/' if department else ''),
            'djangoCustomer': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
            'schedule': f'/schedules/{schedule.id}/' if schedule else '',
            'djangoSchedule': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
            'createNote': f'/notes/?create=1&customer={followup.id}' if followup else (f'/notes/?create=1&department={department.id}' if department else '/notes/?create=1'),
            'uploadFiles': reverse('reporting:note_file_upload', args=[history.id]) if detail_can_edit else '',
            'deleteNote': reverse('reporting:notes_delete_api', args=[history.id]) if detail_can_delete else '',
        },
        'edit': _notes_edit_config(request, history, can_edit),
        'comments': {
            'canCreate': can_add_reply,
            'message': '' if can_add_reply else '댓글 작성 권한이 없습니다.',
            'submitUrl': reverse('reporting:add_manager_memo_to_history_api', args=[history.id]) if can_add_reply else '',
        },
        'relatedNotes': related_notes,
    }


def _notes_get_detail_history(history_id):
    return get_object_or_404(
        History.objects.select_related(
            'user',
            'created_by',
            'followup',
            'followup__company',
            'followup__department',
            'department',
            'department__company',
            'schedule',
            'schedule__followup',
            'schedule__followup__department',
            'schedule__department',
            'schedule__department__company',
            'personal_schedule',
            'reviewer',
        ).prefetch_related(
            'files',
            'reply_memos__created_by',
            'reply_memos__user',
        ),
        pk=history_id,
    )


@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET"])
def notes_detail_api(request, history_id):
    """React CRM notes 상세 화면용 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    history = _notes_get_detail_history(history_id)
    if not can_access_user_data(request.user, history.user):
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없습니다.',
        }, status=403)

    user_profile = get_user_profile(request.user)
    return JsonResponse(_notes_detail_payload(request, history, user_profile))


def _parse_nonnegative_int_or_none(value):
    value = str(value or '').strip().replace(',', '')
    if not value:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


@never_cache
@require_http_methods(["POST"])
def notes_update_api(request, history_id):
    """React notes 상세 화면용 영업노트 수정 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    history = _notes_get_detail_history(history_id)
    if history.parent_history_id or history.action_type == 'memo':
        return JsonResponse({
            'success': False,
            'error': '메모 또는 댓글은 React 영업노트 수정 대상이 아닙니다.',
        }, status=400)
    if not can_modify_user_data(request.user, history.user):
        return JsonResponse({
            'success': False,
            'error': '수정 권한이 없습니다.',
        }, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    try:
        followup_id = int(payload.get('followupId') or 0)
    except (TypeError, ValueError):
        followup_id = 0

    try:
        department_id = int(payload.get('departmentId') or payload.get('department_id') or 0)
    except (TypeError, ValueError):
        department_id = 0

    followup = None
    department = None
    if followup_id:
        followup = FollowUp.objects.filter(
            id=followup_id,
            user__in=get_same_company_users(history.user),
        ).select_related('company', 'department').first()
        if not followup:
            return JsonResponse({'success': False, 'error': '수정 가능한 고객을 선택하세요.'}, status=403)
        department = followup.department
    elif department_id:
        department = _department_target_for_user(history.user, department_id)
        if not department and history.department_id == department_id:
            department = history.department
        if not department:
            return JsonResponse({'success': False, 'error': '수정 가능한 부서/연구실을 선택하세요.'}, status=403)
        preserving_department_only = bool(
            not history.followup_id and
            history.department_id and
            history.department_id == department.id
        )
        if not preserving_department_only and _department_has_own_contacts(history.user, department):
            return JsonResponse({'success': False, 'error': '담당 고객이 있는 부서/연구실은 고객을 선택하세요.'}, status=400)
    elif not history.followup_id and history.department_id:
        department = history.department
    else:
        return JsonResponse({'success': False, 'error': '고객 또는 부서/연구실을 선택하세요.'}, status=400)

    allowed_action_types = {item['value'] for item in _notes_action_types_for_edit(request, history)}
    action_type = str(payload.get('actionType') or '').strip()
    if action_type not in allowed_action_types or action_type == 'memo':
        return JsonResponse({'success': False, 'error': '활동 유형을 선택하세요.'}, status=400)

    content = str(payload.get('content') or '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': '활동 내용을 입력하세요.'}, status=400)

    activity_date = _parse_iso_date_or_none(payload.get('activityDate'))
    next_action_date = _parse_iso_date_or_none(payload.get('nextActionDate'))
    service_status = str(payload.get('serviceStatus') or '').strip()
    valid_service_statuses = {value for value, _label in History.SERVICE_STATUS_CHOICES}
    if service_status and service_status not in valid_service_statuses:
        return JsonResponse({'success': False, 'error': '상태를 선택하세요.'}, status=400)

    history.followup = followup
    history.department = department
    if history.schedule_id and history.schedule:
        schedule_department = history.schedule.department or (
            history.schedule.followup.department
            if history.schedule.followup_id and history.schedule.followup and history.schedule.followup.department
            else None
        )
        if followup:
            if history.schedule.followup_id != followup.id:
                history.schedule = None
            elif schedule_department and followup.department_id and schedule_department.id != followup.department_id:
                history.schedule = None
        elif department and (not schedule_department or schedule_department.id != department.id):
            history.schedule = None
    history.action_type = action_type
    history.content = content
    history.next_action = str(payload.get('nextAction') or '').strip()
    history.next_action_date = next_action_date
    history.service_status = service_status if action_type == 'service' and service_status else None

    if action_type == 'customer_meeting':
        history.meeting_date = activity_date
        history.meeting_situation = ''
        history.meeting_researcher_quote = ''
        history.meeting_confirmed_facts = ''
        history.meeting_obstacles = ''
        history.meeting_next_action = ''
        history.delivery_date = None
        history.delivery_amount = None
        history.delivery_items = ''
    elif action_type == 'delivery_schedule':
        history.delivery_date = activity_date
        history.delivery_amount = _parse_nonnegative_int_or_none(payload.get('deliveryAmount'))
        history.delivery_items = str(payload.get('deliveryItems') or '').strip()
        history.meeting_date = None
        history.meeting_situation = ''
        history.meeting_researcher_quote = ''
        history.meeting_confirmed_facts = ''
        history.meeting_obstacles = ''
        history.meeting_next_action = ''
    else:
        history.meeting_date = None
        history.meeting_situation = ''
        history.meeting_researcher_quote = ''
        history.meeting_confirmed_facts = ''
        history.meeting_obstacles = ''
        history.meeting_next_action = ''
        history.delivery_date = None
        history.delivery_amount = None
        history.delivery_items = ''

    history.save(update_fields=[
        'followup',
        'department',
        'schedule',
        'action_type',
        'content',
        'next_action',
        'next_action_date',
        'service_status',
        'meeting_date',
        'meeting_situation',
        'meeting_researcher_quote',
        'meeting_confirmed_facts',
        'meeting_obstacles',
        'meeting_next_action',
        'delivery_date',
        'delivery_amount',
        'delivery_items',
    ])

    refreshed = _notes_get_detail_history(history.id)
    return JsonResponse({
        **_notes_detail_payload(request, refreshed, get_user_profile(request.user)),
        'message': '영업노트를 수정했습니다.',
    })


@never_cache
@require_http_methods(["POST"])
def notes_delete_api(request, history_id):
    """React notes 상세 화면용 영업노트 삭제 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    history = _notes_get_detail_history(history_id)
    if not _notes_can_delete_history(request.user, history):
        return JsonResponse({
            'success': False,
            'error': '삭제 권한이 없습니다. Manager는 읽기 전용입니다.',
        }, status=403)

    customer_name = history.followup.customer_name or '고객명 미정' if history.followup else '일반 메모'
    action_display = history.get_action_type_display()
    history.delete()

    return JsonResponse({
        'success': True,
        'message': f'{customer_name} ({action_display}) 활동 기록이 삭제되었습니다.',
        'redirect': '/notes/',
    })


@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET"])
def notes_summary_api(request):
    """React CRM notes 화면용 읽기 전용 API."""
    from django.db.models import Case, DateField, F, When

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    can_review_notes = _can_review_notes(user_profile)
    today = timezone.localdate()

    q = request.GET.get('q', '').strip()
    date_to = _parse_iso_date_or_none(request.GET.get('date_to') or request.GET.get('dateTo')) or today
    date_from = _parse_iso_date_or_none(request.GET.get('date_from') or request.GET.get('dateFrom')) or _date_one_month_before(date_to)
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    owner = request.GET.get('owner', '').strip()
    action_type = request.GET.get('actionType', '').strip()
    review = request.GET.get('review', '').strip()
    next_action = request.GET.get('nextAction', '').strip()

    base_notes = History.objects.filter(
        user__in=scope_users,
        parent_history__isnull=True,
    )
    # 정렬 기준일도 표시용 날짜(`_notes_history_payload`)와 같은 규칙을 쓴다.
    # 연결된 일정이 미래면 그 날짜로 정렬하지 않는다 — 다음 일정을 2027년으로
    # 잡았다고 오늘 적은 노트가 2027년으로 밀려나면 기본 조회 구간(최근 한 달)
    # 에서 사라져 검색이 안 된다. 이미 그렇게 저장된 노트들도 이 규칙으로
    # 조회 시점에 함께 교정된다.
    sort_date_expression = Case(
        When(schedule__visit_date__lte=today, then=F('schedule__visit_date')),
        When(personal_schedule__schedule_date__lte=today, then=F('personal_schedule__schedule_date')),
        default=F('created_at__date'),
        output_field=DateField(),
    )
    ranged_base_notes = base_notes.annotate(sort_date=sort_date_expression).filter(
        sort_date__gte=date_from,
        sort_date__lte=date_to,
    )
    notes = ranged_base_notes.select_related(
        'user',
        'followup',
        'followup__company',
        'followup__department',
        'department',
        'department__company',
        'schedule',
        'schedule__department',
        'schedule__department__company',
        'personal_schedule',
        'reviewer',
    )

    if q:
        notes = notes.filter(
            Q(content__icontains=q) |
            Q(meeting_situation__icontains=q) |
            Q(meeting_next_action__icontains=q) |
            Q(next_action__icontains=q) |
            Q(delivery_items__icontains=q) |
            Q(followup__customer_name__icontains=q) |
            Q(followup__manager__icontains=q) |
            Q(followup__company__name__icontains=q) |
            Q(followup__department__name__icontains=q) |
            Q(department__name__icontains=q) |
            Q(department__company__name__icontains=q) |
            Q(department__followup_departments__customer_name__icontains=q) |
            Q(department__followup_departments__manager__icontains=q) |
            Q(schedule__followup__customer_name__icontains=q) |
            Q(schedule__followup__manager__icontains=q) |
            Q(schedule__department__name__icontains=q) |
            Q(schedule__department__followup_departments__customer_name__icontains=q) |
            Q(schedule__department__followup_departments__manager__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(reviewer__username__icontains=q) |
            Q(reviewer__first_name__icontains=q) |
            Q(reviewer__last_name__icontains=q)
        ).distinct()

    if owner:
        try:
            owner_id = int(owner)
            if scope_users.filter(id=owner_id).exists():
                notes = notes.filter(user_id=owner_id)
        except ValueError:
            pass

    valid_action_types = {value for value, _label in History.ACTION_CHOICES}
    if action_type in valid_action_types:
        notes = notes.filter(action_type=action_type)

    review_required_types = ['customer_meeting', 'delivery_schedule', 'quote', 'service']
    if review == 'unreviewed':
        notes = notes.filter(action_type__in=review_required_types, reviewed_at__isnull=True)
    elif review == 'reviewed':
        notes = notes.filter(reviewed_at__isnull=False)

    if next_action == 'overdue':
        notes = notes.filter(next_action_date__lt=today, next_action_date__isnull=False)
    elif next_action == 'upcoming':
        week_end = today + timedelta(days=7)
        notes = notes.filter(
            next_action_date__gte=today,
            next_action_date__lte=week_end,
            next_action_date__isnull=False,
        )
    elif next_action == 'has_date':
        notes = notes.filter(next_action_date__isnull=False)

    notes = notes.annotate(
        reply_count=Count('reply_memos', distinct=True),
        file_count=Count('files', distinct=True),
    ).order_by('-sort_date', '-created_at')

    owner_options = [
        {
            'id': user.id,
            'name': _user_display_name(user),
        }
        for user in scope_users.order_by('username')
    ]
    can_create_note = not user_profile.is_manager()
    create_targets = _notes_create_targets(request.user) if can_create_note else []
    create_departments = _department_create_targets(request.user) if can_create_note else []
    create_department_search_map = _department_create_target_search_text_map(request.user, create_departments) if create_departments else {}
    create_target_ids = [followup.id for followup in create_targets]
    create_department_ids = [department.id for department in create_departments]
    create_schedules = []
    if can_create_note and (create_target_ids or create_department_ids):
        create_schedules = list(Schedule.objects.filter(
            user=request.user,
        ).filter(
            Q(followup_id__in=create_target_ids) |
            Q(department_id__in=create_department_ids)
        ).exclude(
            status='cancelled',
        ).select_related(
            'followup',
            'followup__company',
            'followup__department',
            'department',
            'department__company',
        ).prefetch_related(
            'delivery_items_set',
        ).order_by('-visit_date', '-visit_time', '-id')[:160])

    scope_label = '전체'
    if selected_user:
        scope_label = _user_display_name(selected_user)
    elif not user_profile.can_view_all_users():
        scope_label = _user_display_name(request.user)
    elif user_profile.company:
        scope_label = f'{user_profile.company.name} 팀'

    filtered_count = notes.count()
    base_non_memo = ranged_base_notes.exclude(action_type='memo')
    unreviewed_count = ranged_base_notes.filter(
        action_type__in=review_required_types,
        reviewed_at__isnull=True,
    ).count()
    overdue_count = ranged_base_notes.filter(
        next_action_date__lt=today,
        next_action_date__isnull=False,
    ).exclude(action_type='memo').count()
    upcoming_count = ranged_base_notes.filter(
        next_action_date__gte=today,
        next_action_date__lte=today + timedelta(days=7),
        next_action_date__isnull=False,
    ).exclude(action_type='memo').count()

    action_counts = {
        item['action_type']: item['count']
        for item in ranged_base_notes.values('action_type').annotate(count=Count('id'))
    }

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': scope_label,
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'canReview': can_review_notes,
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'filters': {
            'q': q,
            'dateFrom': date_from.isoformat(),
            'dateTo': date_to.isoformat(),
            'owner': owner,
            'actionType': action_type,
            'review': review,
            'nextAction': next_action,
        },
        'options': {
            'owners': owner_options,
            'actionTypes': [
                {'value': value, 'label': label}
                for value, label in History.ACTION_CHOICES
            ],
            'reviewStates': [
                {'value': 'unreviewed', 'label': '미검토'},
                {'value': 'reviewed', 'label': '검토 완료'},
            ],
            'nextActionStates': [
                {'value': 'upcoming', 'label': '7일 이내'},
                {'value': 'has_date', 'label': '예정일 있음'},
            ],
        },
        'metrics': {
            'totalNotes': ranged_base_notes.count(),
            'activityNotes': base_non_memo.count(),
            'filteredNotes': filtered_count,
            'unreviewedNotes': unreviewed_count,
            'overdueActions': overdue_count,
            'upcomingActions': upcoming_count,
        },
        'actionCounts': [
            {
                'value': value,
                'label': label,
                'count': action_counts.get(value, 0),
            }
            for value, label in History.ACTION_CHOICES
        ],
        'links': {
            'createNote': '/notes/?create=1',
            'notes': '/notes/',
            'unreviewed': '/notes/?review=unreviewed',
        },
        'create': {
            'canCreate': can_create_note,
            'message': '' if can_create_note else 'Manager는 영업노트를 직접 작성할 수 없습니다.',
            'submitUrl': reverse('reporting:notes_create_api'),
            'actionTypes': _notes_create_action_types(request),
            'departments': [
                _department_create_target_payload(department, create_department_search_map.get(department.id, ''))
                for department in create_departments
            ],
            'customers': [_notes_create_target_payload(followup) for followup in create_targets],
            'schedules': [_notes_create_schedule_payload(schedule) for schedule in create_schedules],
        },
        'notes': [
            _notes_history_payload(note, today, can_review_notes)
            for note in list(notes[:80])
        ],
    })


@never_cache
@require_http_methods(["POST"])
def notes_create_api(request):
    """React notes 화면용 빠른 영업노트 작성 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    if user_profile.is_manager():
        return JsonResponse({
            'success': False,
            'error': 'Manager는 영업노트를 직접 작성할 수 없습니다.',
        }, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    try:
        followup_id = int(payload.get('followupId') or 0)
    except (TypeError, ValueError):
        followup_id = 0

    try:
        department_id = int(payload.get('departmentId') or payload.get('department_id') or 0)
    except (TypeError, ValueError):
        department_id = 0

    followup = None
    department = None
    if followup_id:
        followup = FollowUp.objects.filter(
            id=followup_id,
            user=request.user,
        ).select_related('company', 'department').first()
        if not followup:
            return JsonResponse({'success': False, 'error': '작성 가능한 고객을 선택하세요.'}, status=403)
        department = followup.department
    elif department_id:
        department = _department_target_for_user(request.user, department_id)
        if not department:
            return JsonResponse({'success': False, 'error': '작성 가능한 부서/연구실을 선택하세요.'}, status=403)
        if _department_has_own_contacts(request.user, department):
            return JsonResponse({'success': False, 'error': '담당 고객이 있는 부서/연구실은 고객을 선택하세요.'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': '고객 또는 부서/연구실을 선택하세요.'}, status=400)

    try:
        schedule_id = int(payload.get('scheduleId') or payload.get('schedule_id') or 0)
    except (TypeError, ValueError):
        schedule_id = 0

    linked_schedule = None
    if schedule_id:
        linked_schedule = Schedule.objects.filter(
            id=schedule_id,
            user=request.user,
        ).select_related(
            'followup',
            'followup__department',
            'department',
        ).prefetch_related('delivery_items_set').first()
        if not linked_schedule:
            return JsonResponse({'success': False, 'error': '연결할 수 있는 일정을 찾을 수 없습니다.'}, status=403)
        schedule_department = linked_schedule.department or (
            linked_schedule.followup.department if linked_schedule.followup and linked_schedule.followup.department else None
        )
        if followup:
            if linked_schedule.followup_id and linked_schedule.followup_id != followup.id:
                return JsonResponse({'success': False, 'error': '선택한 고객과 일정의 고객이 일치하지 않습니다.'}, status=400)
            if schedule_department and followup.department_id and schedule_department.id != followup.department_id:
                return JsonResponse({'success': False, 'error': '선택한 고객과 일정의 부서/연구실이 일치하지 않습니다.'}, status=400)
        elif department:
            if not schedule_department or schedule_department.id != department.id:
                return JsonResponse({'success': False, 'error': '선택한 부서/연구실과 일정이 일치하지 않습니다.'}, status=400)
        if not department and schedule_department:
            department = schedule_department

    allowed_action_types = {item['value'] for item in _notes_create_action_types(request)}
    action_type = str(payload.get('actionType') or '').strip()
    if action_type not in allowed_action_types:
        return JsonResponse({'success': False, 'error': '활동 유형을 선택하세요.'}, status=400)

    content = str(payload.get('content') or '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': '활동 내용을 입력하세요.'}, status=400)

    next_action = str(payload.get('nextAction') or '').strip()
    next_action_date = _parse_iso_date_or_none(payload.get('nextActionDate'))
    activity_date = _parse_iso_date_or_none(payload.get('activityDate'))
    if not activity_date and linked_schedule:
        activity_date = linked_schedule.visit_date

    history_kwargs = {
        'user': request.user,
        'company': user_profile.company,
        'followup': followup,
        'department': department,
        'schedule': linked_schedule,
        'action_type': action_type,
        'content': content,
        'next_action': next_action,
        'next_action_date': next_action_date,
        'created_by': request.user,
    }
    if action_type == 'customer_meeting' and activity_date:
        history_kwargs['meeting_date'] = activity_date
    elif action_type == 'delivery_schedule' and activity_date:
        history_kwargs['delivery_date'] = activity_date
        delivery_text, delivery_amount = _notes_schedule_delivery_summary(linked_schedule)
        history_kwargs['delivery_items'] = delivery_text
        history_kwargs['delivery_amount'] = delivery_amount

    with transaction.atomic():
        history = History.objects.create(**history_kwargs)
        # 후속 미팅 일정은 그대로 만든다(일정기록에 남는다). 다만 그걸 노트의
        # `schedule` 로 걸지는 않는다 — 걸면 노트가 자기 작성일 대신 미래의 다음
        # 일정 날짜를 들고 있게 돼서, 목록에서 그 날짜로 표시·정렬되고 기본 조회
        # 구간(최근 한 달~오늘) 밖으로 사라진다. 사용자가 명시적으로 고른 기존
        # 일정(`linked_schedule`)은 실제 활동 일정이므로 위에서 이미 연결돼 있다.
        followup_schedule, followup_schedule_created = _notes_create_followup_schedule_for_history(history)

    followup_schedule_payload = _notes_create_schedule_payload(followup_schedule) if followup_schedule else None
    message = '영업노트를 저장했습니다.'
    if followup_schedule_created:
        message = '영업노트를 저장하고 후속 미팅 일정을 생성했습니다.'
    elif followup_schedule:
        message = '영업노트를 저장하고 기존 후속 미팅 일정에 연결했습니다.'

    return JsonResponse({
        'success': True,
        'message': message,
        'historyId': history.id,
        'href': reverse('reporting:history_detail', args=[history.id]),
        'reactHref': f'/notes/{history.id}/',
        'followupSchedule': followup_schedule_payload,
        'followupScheduleCreated': bool(followup_schedule_created),
        'note': _notes_history_payload(history, timezone.localdate(), False),
    }, status=201)


def _schedules_report_text(value, limit=480):
    text = (value or '').strip()
    if limit and len(text) > limit:
        return f'{text[:limit].rstrip()}...'
    return text


def _schedules_report_payload(history, today):
    activity_date = history.meeting_date or history.delivery_date
    if not activity_date and history.schedule_id and history.schedule:
        activity_date = history.schedule.visit_date
    if not activity_date:
        activity_date = history.created_at.date()

    next_action = (history.next_action or history.meeting_next_action or '').strip()
    summary = (
        history.content
        or history.meeting_situation
        or history.meeting_confirmed_facts
        or history.meeting_next_action
        or ''
    ).strip()
    delivery_summary_text, delivery_summary_amount = _history_effective_delivery_summary(history)
    if not summary:
        summary = delivery_summary_text.strip()

    return {
        'id': history.id,
        'actionType': history.action_type,
        'actionLabel': history.get_action_type_display(),
        'summary': _schedules_report_text(summary, 220),
        'content': _schedules_report_text(history.content, 480),
        'meetingSituation': _schedules_report_text(history.meeting_situation, 360),
        'meetingResearcherQuote': _schedules_report_text(history.meeting_researcher_quote, 360),
        'meetingConfirmedFacts': _schedules_report_text(history.meeting_confirmed_facts, 360),
        'meetingObstacles': _schedules_report_text(history.meeting_obstacles, 360),
        'meetingNextAction': _schedules_report_text(history.meeting_next_action, 360),
        'deliveryItems': _schedules_report_text(delivery_summary_text, 480),
        'deliveryAmount': delivery_summary_amount,
        'nextAction': _schedules_report_text(next_action, 260),
        'nextActionDate': _date_or_none(history.next_action_date),
        'activityDate': _date_or_none(activity_date),
        'createdAt': _datetime_or_none(history.created_at),
        'overdue': bool(history.next_action_date and history.next_action_date < today and not history.reviewed_at),
        'href': f'/notes/{history.id}/',
        'djangoHref': reverse('reporting:history_detail', args=[history.id]),
    }


def _schedules_schedule_reports_payload(schedule, today, limit=3):
    report_histories = getattr(schedule, 'calendar_report_histories', [])
    return [
        _schedules_report_payload(history, today)
        for history in list(report_histories)[:limit]
    ]


def _schedules_schedule_payload(schedule, today, can_edit=None):
    followup = schedule.followup
    department = schedule.department or (followup.department if followup and followup.department else None)
    company = followup.company if followup and followup.company else (department.company if department and department.company else None)
    customer = (
        followup.customer_name or followup.manager or '고객명 미정'
    ) if followup else '담당자 미등록'
    customer_href = f'/customers/{followup.id}/' if followup else (f'/accounts/{department.id}/' if department else '')
    history_count = getattr(schedule, 'history_count', None)
    if can_edit is None:
        can_edit = bool(getattr(schedule, 'can_edit', False))
    return {
        'id': schedule.id,
        'type': 'customer',
        'followupId': followup.id if followup else None,
        'departmentId': department.id if department else None,
        'customer': customer,
        'customerEmail': followup.email if followup else '',
        'title': customer if followup else (department.name if department else '부서 일정'),
        'company': company.name if company else '',
        'department': department.name if department else '',
        'owner': _user_display_name(schedule.user),
        'ownerId': schedule.user_id,
        'date': _date_or_none(schedule.visit_date),
        'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '',
        'activityType': schedule.activity_type,
        'activityLabel': schedule.get_activity_type_display(),
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'location': schedule.location or '',
        'notes': (schedule.notes or '').strip()[:180],
        'notesFull': schedule.notes or '',
        'priority': followup.priority if followup else '',
        'priorityLabel': followup.get_priority_display() if followup else '부서 일정',
        'expectedRevenue': _money_int(schedule.expected_revenue),
        'probability': schedule.probability if schedule.probability is not None else None,
        'expectedCloseDate': _date_or_none(schedule.expected_close_date),
        'purchaseConfirmed': bool(schedule.purchase_confirmed),
        'overdue': bool(schedule.status == 'scheduled' and schedule.visit_date < today),
        'historyCount': history_count if history_count is not None else schedule.histories.count(),
        'reports': _schedules_schedule_reports_payload(schedule, today),
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
        'djangoEditHref': reverse('reporting:schedule_edit', args=[schedule.id]) if can_edit else '',
        'statusUpdateHref': reverse('reporting:schedule_status_update', args=[schedule.id]) if can_edit else '',
        'deleteHref': reverse('reporting:schedules_delete_api', args=[schedule.id]) if can_edit else '',
        'canEdit': bool(can_edit),
        'statusOptions': [
            {'value': value, 'label': label}
            for value, label in _schedules_status_choices_for_activity(schedule.activity_type, schedule.status)
        ] if can_edit else [],
        'customerHref': customer_href,
        'djangoCustomerHref': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
        'createHistoryHref': reverse('reporting:history_create_from_schedule', args=[schedule.id]),
    }


def _schedules_personal_react_href(personal_schedule):
    query = f'personal={personal_schedule.id}'
    date_value = _date_or_none(personal_schedule.schedule_date)
    if date_value:
        query = f'{query}&month={date_value[:7]}'
    return f'/schedules/calendar/?{query}'


def _schedules_personal_payload(personal_schedule, today, can_edit=False):
    return {
        'id': personal_schedule.id,
        'type': 'personal',
        'customer': personal_schedule.title,
        'title': personal_schedule.title,
        'company': personal_schedule.company.name if personal_schedule.company else '',
        'department': '',
        'owner': _user_display_name(personal_schedule.user),
        'ownerId': personal_schedule.user_id,
        'date': _date_or_none(personal_schedule.schedule_date),
        'time': personal_schedule.schedule_time.strftime('%H:%M') if personal_schedule.schedule_time else '',
        'activityType': 'personal',
        'activityLabel': '개인 일정',
        'status': 'personal',
        'statusLabel': '개인 일정',
        'location': '',
        'notes': (personal_schedule.content or '').strip()[:180],
        'notesFull': personal_schedule.content or '',
        'priority': '',
        'priorityLabel': '',
        'expectedRevenue': 0,
        'probability': None,
        'expectedCloseDate': None,
        'purchaseConfirmed': False,
        'overdue': False,
        'historyCount': getattr(personal_schedule, 'history_count', 0),
        'reports': [],
        'followupId': None,
        'href': _schedules_personal_react_href(personal_schedule),
        'djangoHref': reverse('reporting:personal_schedule_detail', args=[personal_schedule.id]),
        'djangoEditHref': reverse('reporting:personal_schedule_edit', args=[personal_schedule.id]) if can_edit else '',
        'statusUpdateHref': '',
        'deleteHref': reverse('reporting:personal_schedules_delete_api', args=[personal_schedule.id]) if can_edit else '',
        'canEdit': bool(can_edit),
        'statusOptions': [],
        'customerHref': '',
        'djangoCustomerHref': '',
        'createHistoryHref': '',
    }


def _schedules_combined_items(schedules, personal_schedules, today, limit=80, latest_first=True, request_user=None):
    items = [
        _schedules_schedule_payload(
            schedule,
            today,
            _schedules_can_edit(request_user, schedule) if request_user else None,
        )
        for schedule in schedules
    ] + [
        _schedules_personal_payload(
            personal_schedule,
            today,
            personal_schedule.user_id == request_user.id if request_user else False,
        )
        for personal_schedule in personal_schedules
    ]
    items.sort(
        key=lambda item: (item['date'] or '', item['time'] or '', item['type'], item['id']),
        reverse=latest_first,
    )
    return items[:limit]


def _schedules_calendar_date_range(request):
    from datetime import timedelta

    today = timezone.localdate()
    start = _parse_iso_date_or_none(request.GET.get('start'))
    end = _parse_iso_date_or_none(request.GET.get('end'))

    if not start:
        start = today.replace(day=1)
    if not end:
        next_month = start.replace(year=start.year + 1, month=1, day=1) if start.month == 12 else start.replace(month=start.month + 1, day=1)
        end = next_month - timedelta(days=1)
    if end < start:
        end = start

    max_end = start + timedelta(days=120)
    if end > max_end:
        end = max_end
    return start, end


def _schedules_calendar_scope(request, user_profile):
    data_filter = request.GET.get('data_filter') or request.GET.get('dataFilter') or 'me'
    filter_user_id = request.GET.get('filter_user') or request.GET.get('filterUser') or ''
    selected_user = None
    is_manager = bool(user_profile and user_profile.is_manager())

    if user_profile and user_profile.company:
        company_users = User.objects.filter(
            userprofile__company=user_profile.company,
            is_active=True,
        ).select_related('userprofile').order_by('username')
    else:
        company_users = User.objects.filter(id=request.user.id).select_related('userprofile')

    if is_manager and data_filter == 'me':
        data_filter = 'all'

    if data_filter == 'all' and user_profile and user_profile.company:
        filter_users = company_users
        scope_label = f'{user_profile.company.name} 전체'
    elif data_filter == 'user' and filter_user_id and user_profile and user_profile.company:
        try:
            selected_user = company_users.get(id=filter_user_id)
            filter_users = User.objects.filter(id=selected_user.id).select_related('userprofile')
            scope_label = _user_display_name(selected_user)
        except (User.DoesNotExist, ValueError):
            filter_user_id = ''
            if is_manager and user_profile and user_profile.company:
                data_filter = 'all'
                filter_users = company_users
                scope_label = f'{user_profile.company.name} 전체'
            else:
                data_filter = 'me'
                filter_users = User.objects.filter(id=request.user.id).select_related('userprofile')
                scope_label = _user_display_name(request.user)
    else:
        filter_user_id = ''
        if is_manager and user_profile and user_profile.company:
            data_filter = 'all'
            filter_users = company_users
            scope_label = f'{user_profile.company.name} 전체'
        else:
            data_filter = 'me'
            filter_users = User.objects.filter(id=request.user.id).select_related('userprofile')
            scope_label = _user_display_name(request.user)

    user_options = [
        {
            'id': user.id,
            'name': _user_display_name(user),
            'username': user.username,
            'role': getattr(getattr(user, 'userprofile', None), 'role', ''),
            'isCurrent': user.id == request.user.id,
        }
        for user in company_users
    ]
    data_filters = []
    if not is_manager:
        data_filters.append({'value': 'me', 'label': '내 일정'})
    if user_profile and user_profile.company:
        data_filters.extend([
            {'value': 'all', 'label': '직원전체' if is_manager else '회사 전체'},
            {'value': 'user', 'label': '직원 선택'},
        ])

    return filter_users, {
        'label': scope_label,
        'dataFilter': data_filter,
        'filterUserId': selected_user.id if selected_user else None,
        'canViewCompany': bool(user_profile and user_profile.company),
    }, {
        'users': user_options,
        'dataFilters': data_filters,
    }


REACT_SCHEDULE_ACTIVITY_TYPES = ('customer_meeting', 'quote', 'delivery')


def _schedules_create_activity_types(request):
    """React schedules only support meeting, quote, and delivery."""
    allowed_types = set(REACT_SCHEDULE_ACTIVITY_TYPES)
    return [
        {'value': value, 'label': label}
        for value, label in Schedule.ACTIVITY_TYPE_CHOICES
        if value in allowed_types
    ]


def _schedules_create_targets(user, limit=120):
    return list(FollowUp.objects.filter(
        user=user,
    ).select_related(
        'company', 'department'
    ).order_by('-updated_at', 'company__name', 'customer_name')[:limit])


def _schedules_edit_targets(user, limit=160):
    return list(FollowUp.objects.filter(
        user__in=get_same_company_users(user),
    ).select_related(
        'company', 'department'
    ).order_by('-updated_at', 'company__name', 'customer_name')[:limit])


def _schedules_create_target_payload(followup):
    customer = followup.customer_name or followup.manager or '고객명 미정'
    company = followup.company.name if followup.company else ''
    department = followup.department.name if followup.department else ''
    label_parts = [part for part in [company, department, customer] if part]
    return {
        'id': followup.id,
        'departmentId': followup.department_id,
        'companyId': followup.company_id,
        'label': ' · '.join(label_parts) or customer,
        'customer': customer,
        'company': company,
        'department': department,
        'priorityLabel': followup.get_priority_display(),
        'href': f'/customers/{followup.id}/',
        'djangoHref': reverse('reporting:followup_detail', args=[followup.id]),
    }


def _parse_time_or_none(value):
    from datetime import time

    value = str(value or '').strip()
    if not value:
        return None
    parts = value.split(':')
    if len(parts) < 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        return time(hour=hour, minute=minute)
    except (TypeError, ValueError):
        return None


def _parse_optional_decimal(value):
    from decimal import Decimal, InvalidOperation

    value = str(value or '').replace(',', '').strip()
    if not value:
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def _parse_optional_probability(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        probability = int(value)
    except (TypeError, ValueError):
        raise ValueError('성공 확률은 0부터 100 사이의 숫자입니다.')
    if probability < 0 or probability > 100:
        raise ValueError('성공 확률은 0부터 100 사이의 숫자입니다.')
    return normalize_probability_to_five(probability)


def _parse_schedule_probability(activity_type, value):
    probability = _parse_optional_probability(value)
    if activity_type == 'quote' and probability is None:
        raise ValueError('견적 성공 확률은 필수입니다.')
    return probability


def _schedule_pipeline_target_stage(schedule):
    if not schedule or not schedule.followup_id:
        return None

    if schedule.activity_type == 'customer_meeting':
        if schedule.status == 'cancelled':
            return None
        return 'contact'

    if schedule.activity_type == 'quote':
        if schedule.status == 'cancelled':
            return 'lost'
        if schedule.purchase_confirmed:
            return 'won'
        return 'quote'

    if schedule.activity_type == 'delivery':
        if schedule.status == 'cancelled':
            return 'lost'
        return 'won'

    return None


def _sync_schedule_pipeline(schedule):
    """Synchronize a customer pipeline card from the schedule state only."""
    try:
        from .funnel_views import _ensure_pipeline_year_reset
        _ensure_pipeline_year_reset()

        target_stage = _schedule_pipeline_target_stage(schedule)
        if not target_stage:
            return False

        followup = schedule.followup
        if followup.pipeline_stage == target_stage and not followup.pipeline_manually_set:
            return False

        followup.pipeline_stage = target_stage
        followup.pipeline_manually_set = False
        followup.save(update_fields=['pipeline_stage', 'pipeline_manually_set'])
        return True
    except Exception:
        logger.exception('Failed to sync schedule pipeline for schedule %s', getattr(schedule, 'id', None))
        return False


def _ai_json_list(value):
    return value if isinstance(value, list) else []


@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET"])
def schedules_summary_api(request):
    """React CRM schedules 화면용 읽기 전용 API."""
    from datetime import timedelta
    from .models import PersonalSchedule

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()
    week_end = today + timedelta(days=7)

    q = request.GET.get('q', '').strip()
    owner = request.GET.get('owner', '').strip()
    status = request.GET.get('status', '').strip()
    activity_type = request.GET.get('activityType', '').strip()
    range_filter = request.GET.get('range', '').strip()

    base_schedules = Schedule.objects.filter(
        user__in=scope_users,
        activity_type__in=REACT_SCHEDULE_ACTIVITY_TYPES,
    )
    base_personal_schedules = PersonalSchedule.objects.filter(user__in=scope_users)
    schedules = base_schedules.select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'department', 'department__company'
    )
    personal_schedules = base_personal_schedules.select_related('user', 'company')

    if q:
        schedules = schedules.filter(
            Q(followup__customer_name__icontains=q) |
            Q(followup__manager__icontains=q) |
            Q(followup__company__name__icontains=q) |
            Q(followup__department__name__icontains=q) |
            Q(department__name__icontains=q) |
            Q(department__company__name__icontains=q) |
            Q(location__icontains=q) |
            Q(notes__icontains=q)
        )
        personal_schedules = personal_schedules.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(company__name__icontains=q)
        )

    if owner:
        try:
            owner_id = int(owner)
            if scope_users.filter(id=owner_id).exists():
                schedules = schedules.filter(user_id=owner_id)
                personal_schedules = personal_schedules.filter(user_id=owner_id)
        except ValueError:
            pass

    include_customer = True
    include_personal = True
    valid_statuses = {value for value, _label in Schedule.STATUS_CHOICES}
    if status in valid_statuses:
        schedules = schedules.filter(status=status)
        include_personal = False
    elif status == 'personal':
        include_customer = False

    valid_activity_types = set(REACT_SCHEDULE_ACTIVITY_TYPES)
    if activity_type in valid_activity_types:
        schedules = schedules.filter(activity_type=activity_type)
        include_personal = False
    elif activity_type == 'personal':
        include_customer = False

    if range_filter == 'today':
        schedules = schedules.filter(visit_date=today)
        personal_schedules = personal_schedules.filter(schedule_date=today)
    elif range_filter == 'week':
        schedules = schedules.filter(visit_date__gte=today, visit_date__lte=week_end)
        personal_schedules = personal_schedules.filter(schedule_date__gte=today, schedule_date__lte=week_end)
    elif range_filter == 'overdue':
        schedules = schedules.filter(visit_date__lt=today, status='scheduled')
        include_personal = False
    elif range_filter == 'past':
        schedules = schedules.filter(visit_date__lt=today)
        personal_schedules = personal_schedules.filter(schedule_date__lt=today)

    if not include_customer:
        schedules = Schedule.objects.none()
    if not include_personal:
        personal_schedules = PersonalSchedule.objects.none()

    schedules = schedules.annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('-visit_date', '-visit_time', '-created_at', '-id')
    personal_schedules = personal_schedules.annotate(
        history_count=Count('histories', distinct=True)
    ).order_by('-schedule_date', '-schedule_time', '-created_at', '-id')

    owner_options = [
        {
            'id': user.id,
            'name': _user_display_name(user),
        }
        for user in scope_users.order_by('username')
    ]
    can_create_schedule = not user_profile.is_manager()
    create_targets = _schedules_create_targets(request.user) if can_create_schedule else []
    create_departments = _department_create_targets(request.user) if can_create_schedule else []
    create_department_search_map = _department_create_target_search_text_map(request.user, create_departments) if create_departments else {}

    scope_label = '전체'
    if selected_user:
        scope_label = _user_display_name(selected_user)
    elif not user_profile.can_view_all_users():
        scope_label = _user_display_name(request.user)
    elif user_profile.company:
        scope_label = f'{user_profile.company.name} 팀'

    status_counts = {
        item['status']: item['count']
        for item in base_schedules.values('status').annotate(count=Count('id'))
    }
    activity_counts = {
        item['activity_type']: item['count']
        for item in base_schedules.values('activity_type').annotate(count=Count('id'))
    }
    personal_count = base_personal_schedules.count()

    today_schedules = base_schedules.filter(visit_date=today).select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'department', 'department__company'
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('-visit_time', '-created_at', '-id')
    today_personal_schedules = base_personal_schedules.filter(schedule_date=today).select_related(
        'user', 'company'
    ).annotate(history_count=Count('histories', distinct=True)).order_by('-schedule_time', '-created_at', '-id')

    upcoming_schedules = base_schedules.filter(
        visit_date__gt=today,
        visit_date__lte=week_end,
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'department', 'department__company'
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('-visit_date', '-visit_time', '-created_at', '-id')
    upcoming_personal_schedules = base_personal_schedules.filter(
        schedule_date__gt=today,
        schedule_date__lte=week_end,
    ).select_related('user', 'company').annotate(
        history_count=Count('histories', distinct=True)
    ).order_by('-schedule_date', '-schedule_time', '-created_at', '-id')

    overdue_schedules = base_schedules.filter(
        visit_date__lt=today,
        status='scheduled',
    ).select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'department', 'department__company'
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('-visit_date', '-visit_time', '-created_at', '-id')[:10]

    filtered_customer_count = schedules.count()
    filtered_personal_count = personal_schedules.count()

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': scope_label,
            'userCount': scope_users.count(),
            'canViewAll': user_profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'filters': {
            'q': q,
            'owner': owner,
            'status': status,
            'activityType': activity_type,
            'range': range_filter,
        },
        'options': {
            'owners': owner_options,
            'statuses': [
                {'value': value, 'label': label}
                for value, label in Schedule.STATUS_CHOICES
            ] + [{'value': 'personal', 'label': '개인 일정'}],
            'activityTypes': _schedules_create_activity_types(request) + [{'value': 'personal', 'label': '개인 일정'}],
            'ranges': [
                {'value': 'today', 'label': '오늘'},
                {'value': 'week', 'label': '7일 이내'},
                {'value': 'overdue', 'label': '지연'},
                {'value': 'past', 'label': '지난 일정'},
            ],
        },
        'metrics': {
            'totalSchedules': base_schedules.count() + personal_count,
            'customerSchedules': base_schedules.count(),
            'personalSchedules': personal_count,
            'filteredSchedules': filtered_customer_count + filtered_personal_count,
            'todaySchedules': base_schedules.filter(visit_date=today).count() + base_personal_schedules.filter(schedule_date=today).count(),
            'weekSchedules': base_schedules.filter(visit_date__gte=today, visit_date__lte=week_end).count() + base_personal_schedules.filter(schedule_date__gte=today, schedule_date__lte=week_end).count(),
            'overdueSchedules': base_schedules.filter(visit_date__lt=today, status='scheduled').count(),
            'scheduledSchedules': base_schedules.filter(status='scheduled').count(),
            'completedSchedules': base_schedules.filter(status='completed').count(),
            'cancelledSchedules': base_schedules.filter(status='cancelled').count(),
        },
        'statusCounts': [
            {
                'value': value,
                'label': label,
                'count': status_counts.get(value, 0),
            }
            for value, label in Schedule.STATUS_CHOICES
        ] + [{'value': 'personal', 'label': '개인 일정', 'count': personal_count}],
        'activityCounts': [
            {
                'value': item['value'],
                'label': item['label'],
                'count': activity_counts.get(item['value'], 0),
            }
            for item in _schedules_create_activity_types(request)
        ] + [{'value': 'personal', 'label': '개인 일정', 'count': personal_count}],
        'links': {
            'createSchedule': reverse('reporting:schedule_create'),
            'createPersonalSchedule': reverse('reporting:personal_schedule_create'),
            'schedules': '/schedules/',
            'djangoSchedules': reverse('reporting:schedule_list'),
            'calendar': '/schedules/calendar/',
            'djangoCalendar': reverse('reporting:schedule_calendar'),
        },
        'create': {
            'canCreate': can_create_schedule,
            'message': '' if can_create_schedule else 'Manager는 일정을 직접 생성할 수 없습니다.',
            'submitUrl': reverse('reporting:schedules_create_api'),
            'activityTypes': _schedules_create_activity_types(request),
            'departments': [
                _department_create_target_payload(department, create_department_search_map.get(department.id, ''))
                for department in create_departments
            ],
            'customers': [_schedules_create_target_payload(followup) for followup in create_targets],
            'personalSchedule': {
                'canCreate': can_create_schedule,
                'message': '' if can_create_schedule else 'Manager는 일정을 직접 생성할 수 없습니다.',
                'submitUrl': reverse('reporting:personal_schedules_create_api'),
                'djangoUrl': reverse('reporting:personal_schedule_create'),
            },
        },
        'today': _schedules_combined_items(today_schedules[:20], today_personal_schedules[:20], today, limit=20, request_user=request.user),
        'upcoming': _schedules_combined_items(upcoming_schedules[:30], upcoming_personal_schedules[:30], today, limit=30, request_user=request.user),
        'overdue': [
            _schedules_schedule_payload(schedule, today, _schedules_can_edit(request.user, schedule))
            for schedule in overdue_schedules
        ],
        'schedules': _schedules_combined_items(schedules[:80], personal_schedules[:80], today, limit=80, request_user=request.user),
    })


@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET"])
def schedules_calendar_api(request):
    """React CRM schedule calendar API."""
    from .models import PersonalSchedule

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    start_date, end_date = _schedules_calendar_date_range(request)
    filter_users, scope_payload, options_payload = _schedules_calendar_scope(request, user_profile)
    today = timezone.localdate()

    base_schedules = Schedule.objects.filter(
        user__in=filter_users,
        visit_date__gte=start_date,
        visit_date__lte=end_date,
        activity_type__in=REACT_SCHEDULE_ACTIVITY_TYPES,
    )
    base_personal_schedules = PersonalSchedule.objects.filter(
        user__in=filter_users,
        schedule_date__gte=start_date,
        schedule_date__lte=end_date,
    )

    calendar_report_qs = History.objects.filter(
        parent_history__isnull=True,
    ).select_related(
        'schedule',
    ).order_by('-created_at')
    schedules = base_schedules.select_related(
        'user', 'followup', 'followup__company', 'followup__department', 'department', 'department__company'
    ).prefetch_related(
        Prefetch('histories', queryset=calendar_report_qs, to_attr='calendar_report_histories')
    ).annotate(
        history_count=Count('histories', filter=Q(histories__parent_history__isnull=True), distinct=True)
    ).order_by('visit_date', 'visit_time')
    personal_schedules = base_personal_schedules.select_related(
        'user', 'company'
    ).annotate(
        history_count=Count('histories', distinct=True)
    ).order_by('schedule_date', 'schedule_time')

    scheduled_count = base_schedules.filter(status='scheduled').count()
    completed_count = base_schedules.filter(status='completed').count()
    cancelled_count = base_schedules.filter(status='cancelled').count()
    overdue_count = base_schedules.filter(visit_date__lt=today, status='scheduled').count()
    can_create_schedule = not user_profile.is_manager()
    create_targets = _schedules_create_targets(request.user) if can_create_schedule else []
    create_departments = _department_create_targets(request.user) if can_create_schedule else []
    create_department_search_map = _department_create_target_search_text_map(request.user, create_departments) if create_departments else {}

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            **scope_payload,
            'userCount': filter_users.count(),
        },
        'filters': {
            'start': _date_or_none(start_date),
            'end': _date_or_none(end_date),
            'dataFilter': scope_payload['dataFilter'],
            'filterUser': str(scope_payload['filterUserId'] or ''),
        },
        'options': options_payload,
        'metrics': {
            'totalSchedules': base_schedules.count() + base_personal_schedules.count(),
            'customerSchedules': base_schedules.count(),
            'personalSchedules': base_personal_schedules.count(),
            'scheduledSchedules': scheduled_count,
            'completedSchedules': completed_count,
            'cancelledSchedules': cancelled_count,
            'overdueSchedules': overdue_count,
        },
        'links': {
            'schedules': '/schedules/',
            'djangoSchedules': reverse('reporting:schedule_list'),
            'calendar': '/schedules/calendar/',
            'djangoCalendar': reverse('reporting:schedule_calendar'),
            'createSchedule': reverse('reporting:schedule_create'),
            'createPersonalSchedule': reverse('reporting:personal_schedule_create'),
        },
        'create': {
            'canCreate': can_create_schedule,
            'message': '' if can_create_schedule else 'Manager는 일정을 직접 생성할 수 없습니다.',
            'submitUrl': reverse('reporting:schedules_create_api'),
            'activityTypes': _schedules_create_activity_types(request),
            'departments': [
                _department_create_target_payload(department, create_department_search_map.get(department.id, ''))
                for department in create_departments
            ],
            'customers': [_schedules_create_target_payload(followup) for followup in create_targets],
            'personalSchedule': {
                'canCreate': can_create_schedule,
                'message': '' if can_create_schedule else 'Manager는 일정을 직접 생성할 수 없습니다.',
                'submitUrl': reverse('reporting:personal_schedules_create_api'),
                'djangoUrl': reverse('reporting:personal_schedule_create'),
            },
        },
        'schedules': _schedules_combined_items(schedules, personal_schedules, today, limit=1000, latest_first=False, request_user=request.user),
    })


@never_cache
@require_http_methods(["POST"])
def schedules_create_api(request):
    """React schedules 화면용 빠른 고객 일정 등록 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    if user_profile.is_manager():
        return JsonResponse({
            'success': False,
            'error': 'Manager는 일정을 직접 생성할 수 없습니다.',
        }, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    try:
        followup_id = int(payload.get('followupId') or 0)
    except (TypeError, ValueError):
        followup_id = 0

    try:
        department_id = int(payload.get('departmentId') or payload.get('department_id') or 0)
    except (TypeError, ValueError):
        department_id = 0

    followup = None
    department = None
    if followup_id:
        followup = FollowUp.objects.filter(
            id=followup_id,
            user=request.user,
        ).select_related('company', 'department').first()
        if not followup:
            return JsonResponse({'success': False, 'error': '일정을 등록할 담당 고객을 선택하세요.'}, status=403)
        department = followup.department
    elif department_id:
        department = _department_target_for_user(request.user, department_id)
        if not department:
            return JsonResponse({'success': False, 'error': '일정을 등록할 부서/연구실을 선택하세요.'}, status=403)
        if _department_has_own_contacts(request.user, department):
            return JsonResponse({'success': False, 'error': '담당 고객이 있는 부서/연구실은 고객을 선택하세요.'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': '고객 또는 부서/연구실을 선택하세요.'}, status=400)

    allowed_activity_types = {item['value'] for item in _schedules_create_activity_types(request)}
    activity_type = str(payload.get('activityType') or '').strip()
    if activity_type not in allowed_activity_types:
        return JsonResponse({'success': False, 'error': '활동 유형을 선택하세요.'}, status=400)

    visit_date = _parse_iso_date_or_none(payload.get('visitDate'))
    if not visit_date:
        return JsonResponse({'success': False, 'error': '방문 날짜를 선택하세요.'}, status=400)

    visit_time = _parse_time_or_none(payload.get('visitTime'))
    if not visit_time:
        return JsonResponse({'success': False, 'error': '방문 시간을 선택하세요.'}, status=400)

    location = str(payload.get('location') or '').strip()[:200]
    notes = str(payload.get('notes') or '').strip()
    expected_revenue = _parse_optional_decimal(payload.get('expectedRevenue'))
    try:
        probability = _parse_schedule_probability(activity_type, payload.get('probability'))
        vat_mode = vat.parse_vat_mode(payload)
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    schedule = Schedule.objects.create(
        user=request.user,
        company=user_profile.company,
        followup=followup,
        department=department,
        visit_date=visit_date,
        visit_time=visit_time,
        location=location,
        status='scheduled',
        activity_type=activity_type,
        notes=notes,
        expected_revenue=expected_revenue,
        probability=probability,
        vat_mode=vat_mode,
    )
    _sync_schedule_pipeline(schedule)

    return JsonResponse({
        'success': True,
        'message': '일정을 등록했습니다.',
        'scheduleId': schedule.id,
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
        'schedule': _schedules_schedule_payload(schedule, timezone.localdate(), True),
    }, status=201)


def _schedules_can_edit(user, schedule):
    user_profile = get_user_profile(user)
    return bool(schedule.user_id == user.id and not user_profile.is_manager())


def _schedules_status_choices_for_activity(activity_type, current_status=''):
    choices = list(Schedule.STATUS_CHOICES)
    if activity_type == 'quote':
        choices = [
            ('scheduled', '예정됨'),
            ('cancelled', '취소됨'),
        ]
        valid_statuses = {value for value, _label in choices}
        if current_status and current_status not in valid_statuses:
            labels = dict(Schedule.STATUS_CHOICES)
            choices = [(current_status, labels.get(current_status, current_status)), *choices]
    return choices


def _schedules_activity_types_for_edit(request, schedule):
    activity_types = _schedules_create_activity_types(request)
    activity_values = {item['value'] for item in activity_types}
    if schedule.activity_type not in activity_values and schedule.activity_type != 'service':
        activity_labels = dict(Schedule.ACTIVITY_TYPE_CHOICES)
        activity_types = [
            {
                'value': schedule.activity_type,
                'label': activity_labels.get(schedule.activity_type, schedule.activity_type),
            },
            *activity_types,
        ]
    return activity_types


def _schedules_edit_config(request, schedule, can_edit):
    allowed_customers = _schedules_edit_targets(schedule.user) if can_edit else []
    allowed_departments = _department_create_targets(schedule.user) if can_edit else []
    if schedule.followup_id and can_edit:
        allowed_customer_ids = {followup.id for followup in allowed_customers}
        if schedule.followup_id not in allowed_customer_ids:
            allowed_customers = [schedule.followup, *allowed_customers]
    if schedule.department_id and can_edit:
        allowed_department_ids = {department.id for department in allowed_departments}
        if schedule.department_id not in allowed_department_ids and schedule.department:
            allowed_departments = [schedule.department, *allowed_departments]

    department_search_map = _department_create_target_search_text_map(schedule.user, allowed_departments) if allowed_departments else {}

    return {
        'canEdit': bool(can_edit),
        'message': '' if can_edit else '수정 권한이 없습니다.',
        'submitUrl': reverse('reporting:schedules_update_api', args=[schedule.id]) if can_edit else '',
        'djangoUrl': reverse('reporting:schedule_edit', args=[schedule.id]) if can_edit else '',
        'activityTypes': _schedules_activity_types_for_edit(request, schedule),
        'statuses': [
            {'value': value, 'label': label}
            for value, label in _schedules_status_choices_for_activity(schedule.activity_type, schedule.status)
        ],
        'departments': [
            _department_create_target_payload(department, department_search_map.get(department.id, ''))
            for department in allowed_departments
        ],
        'customers': [_schedules_create_target_payload(followup) for followup in allowed_customers],
    }


def _quote_group_key(value):
    return str(value or '').strip()[:100]


def _quote_group_label(value):
    return _quote_group_key(value) or '기본 견적서'


def _quote_group_filename_part(value):
    label = _quote_group_label(value)
    cleaned = re.sub(r'[\\/:*?"<>|]+', ' ', label).strip()
    return re.sub(r'\s+', ' ', cleaned)[:80] or '기본 견적서'


def _quote_group_query_suffix(value):
    from urllib.parse import urlencode

    return '?' + urlencode({'quote_group': _quote_group_key(value)})


def _schedule_quote_group_notes_map(schedule):
    notes = {
        _quote_group_key(note.quote_group): note.notes or ''
        for note in schedule.quote_group_notes.all()
    }
    if '' not in notes and schedule.quote_extra_notes:
        notes[''] = schedule.quote_extra_notes or ''
    return notes


def _schedule_quote_group_note_payloads(schedule):
    notes_map = _schedule_quote_group_notes_map(schedule)
    group_keys = []
    seen = set()
    for item in schedule.delivery_items_set.all().order_by('id'):
        group_key = _quote_group_key(getattr(item, 'quote_group', ''))
        if group_key not in seen:
            seen.add(group_key)
            group_keys.append(group_key)
    for group_key in notes_map.keys():
        if group_key not in seen:
            seen.add(group_key)
            group_keys.append(group_key)
    if not group_keys and schedule.quote_extra_notes:
        group_keys = ['']
    return [
        {
            'quoteGroup': group_key,
            'quoteGroupLabel': _quote_group_label(group_key),
            'notes': notes_map.get(group_key, ''),
        }
        for group_key in group_keys
    ]


def _document_quote_extra_notes(schedule, quote_group='', quote_group_selected=False):
    notes_map = _schedule_quote_group_notes_map(schedule)
    if quote_group_selected:
        return notes_map.get(_quote_group_key(quote_group), '')
    return notes_map.get('', schedule.quote_extra_notes or '')


def _parse_quote_group_notes_payload(payload):
    raw_notes = payload.get('quoteGroupNotes')
    if raw_notes is None:
        raw_notes = payload.get('quote_group_notes')
    if raw_notes is None:
        return None

    parsed = {}
    if isinstance(raw_notes, dict):
        iterable = raw_notes.items()
        for group, notes in iterable:
            parsed[_quote_group_key(group)] = str(notes or '').strip()
        return parsed

    if isinstance(raw_notes, list):
        for item in raw_notes:
            if not isinstance(item, dict):
                continue
            group = item.get('quoteGroup')
            if group is None:
                group = item.get('quote_group')
            notes = item.get('notes', '')
            parsed[_quote_group_key(group)] = str(notes or '').strip()
        return parsed

    raise ValueError('견적 기타사항 형식이 올바르지 않습니다.')


def _save_schedule_quote_group_notes(schedule, notes_map):
    if notes_map is None:
        return

    schedule.quote_group_notes.all().delete()
    objects = [
        ScheduleQuoteGroupNote(
            schedule=schedule,
            quote_group=_quote_group_key(group),
            notes=notes,
        )
        for group, notes in notes_map.items()
        if notes
    ]
    if objects:
        ScheduleQuoteGroupNote.objects.bulk_create(objects)
    schedule.quote_extra_notes = notes_map.get('', '')


def _schedules_discount_unit_price_or_none(item):
    """Treat legacy zero discount-unit values without a discount rate as blank."""
    from decimal import Decimal, InvalidOperation

    if item.discount_unit_price is None:
        return None
    try:
        discount_unit_price = Decimal(str(item.discount_unit_price))
        discount_rate = Decimal(str(item.discount_rate or 0))
        unit_price = Decimal(str(item.unit_price or 0)) if item.unit_price is not None else Decimal('0')
    except (InvalidOperation, ValueError):
        return item.discount_unit_price
    if discount_unit_price <= 0 and discount_rate <= 0 and unit_price > 0:
        return None
    return item.discount_unit_price


def _schedules_delivery_item_payload(item):
    product = item.product if item.product_id else None
    effective_unit_price = item.get_effective_unit_price()
    discount_unit_price = _schedules_discount_unit_price_or_none(item)
    return {
        'id': item.id,
        'productId': item.product_id,
        'productCode': product.product_code if product else '',
        'productDescription': (product.description or '') if product else '',
        'itemName': item.item_name,
        'quantity': item.quantity,
        'unit': item.unit or '',
        'unitPrice': _money_int(item.unit_price) if item.unit_price is not None else None,
        'discountRate': float(item.discount_rate or 0),
        'discountUnitPrice': _money_int(discount_unit_price) if discount_unit_price is not None else None,
        'effectiveUnitPrice': _money_int(effective_unit_price) if effective_unit_price is not None else None,
        'totalPrice': _money_int(item.total_price),
        'taxInvoiceIssued': bool(item.tax_invoice_issued),
        'cardPaymentReceived': bool(getattr(item, 'card_payment_received', False)),
        'receivableSettled': bool(getattr(item, 'receivable_settled', False)),
        'receivableSettledAt': _datetime_or_none(getattr(item, 'receivable_settled_at', None)),
        'quoteGroup': item.quote_group or '',
        'quoteGroupLabel': _quote_group_label(item.quote_group),
        'notes': item.notes or '',
        'optionDescription': item.option_description or '',
        'sourceQuoteScheduleId': item.source_quote_schedule_id,
        'sourceQuoteItemId': item.source_quote_item_id,
    }


def _schedules_prepayment_usage_payload(usage):
    prepayment = usage.prepayment
    customer = prepayment.customer if prepayment and prepayment.customer_id else None
    return {
        'id': usage.id,
        'prepaymentId': usage.prepayment_id,
        'paymentDate': _date_or_none(prepayment.payment_date) if prepayment else None,
        'payerName': prepayment.payer_name or '미지정' if prepayment else '미지정',
        'customerName': customer.customer_name or str(customer) if customer else '',
        'productName': usage.product_name or '',
        'quantity': usage.quantity or 1,
        'amount': _money_int(usage.amount),
        'remainingBalance': _money_int(usage.remaining_balance),
        'usedAt': _datetime_or_none(usage.used_at),
        'memo': usage.memo or '',
    }


def _schedules_tax_invoice_payload(schedule, can_edit):
    if schedule.activity_type != 'delivery':
        return {
            'applies': False,
            'status': 'not_applicable',
            'statusLabel': '대상 아님',
            'issuedCount': 0,
            'pendingCount': 0,
            'totalCount': 0,
            'canToggle': False,
            'toggleUrl': '',
            'actionLabel': '',
            'message': '',
        }

    items = list(schedule.delivery_items_set.all())
    total_count = len(items)
    issued_count = sum(1 for item in items if item.tax_invoice_issued)
    pending_count = max(total_count - issued_count, 0)

    if total_count <= 0:
        status = 'empty'
        status_label = '품목 없음'
        action_label = ''
        message = '납품 품목이 등록되면 외상고객 메뉴에서 외상 상태를 관리할 수 있습니다.'
    elif pending_count == 0:
        status = 'issued'
        status_label = '전체 외상 등록'
        action_label = ''
        message = f'외상 등록 {issued_count}건'
    elif issued_count == 0:
        status = 'pending'
        status_label = '전체 미등록'
        action_label = ''
        message = f'외상 미등록 {pending_count}건'
    else:
        status = 'partial'
        status_label = '일부 외상 등록'
        action_label = ''
        message = f'외상 등록 {issued_count}건 / 미등록 {pending_count}건'

    return {
        'applies': True,
        'status': status,
        'statusLabel': status_label,
        'issuedCount': issued_count,
        'pendingCount': pending_count,
        'totalCount': total_count,
        'canToggle': False,
        'toggleUrl': '',
        'actionLabel': action_label,
        'message': f'{message} · 변경은 외상고객 메뉴에서만 가능합니다.',
    }


def _schedules_allowed_prepayments_queryset(actor, followup):
    same_company_users = get_same_company_users(actor)
    if followup.department_id:
        account_filter = Q(department=followup.department) | Q(
            department__isnull=True,
            customer__department=followup.department,
        )
    else:
        account_filter = Q(customer=followup)

    return Prepayment.objects.filter(
        account_filter,
    ).filter(
        Q(created_by__in=same_company_users) | Q(customer__user__in=same_company_users),
    ).select_related('department', 'customer', 'customer__department')


def _schedules_prepayment_option_payload(prepayment, selected_amount=0):
    selected_amount = selected_amount or 0
    available_balance = (prepayment.balance or 0) + selected_amount
    customer = prepayment.customer
    department = prepayment.department or (customer.department if customer and customer.department_id else None)
    payment_date = _date_or_none(prepayment.payment_date)
    payer_name = prepayment.payer_name or '미지정'
    customer_name = customer.customer_name or str(customer) if customer else ''
    return {
        'id': prepayment.id,
        'payment_date': payment_date,
        'paymentDate': payment_date,
        'payer_name': payer_name,
        'payerName': payer_name,
        'customer_name': customer_name,
        'customerName': customer_name,
        'department_name': department.name if department else '',
        'departmentName': department.name if department else '',
        'amount': _money_int(prepayment.amount),
        'balance': _money_int(prepayment.balance),
        'available_balance': _money_int(available_balance),
        'availableBalance': _money_int(available_balance),
        'selected_amount': _money_int(selected_amount),
        'selectedAmount': _money_int(selected_amount),
        'status': prepayment.status,
        'status_label': prepayment.get_status_display(),
        'statusLabel': prepayment.get_status_display(),
    }


def _schedules_prepayment_options(actor, followup, schedule=None):
    usage_totals = {}
    if schedule:
        usage_totals = {
            row['prepayment_id']: row['total'] or 0
            for row in PrepaymentUsage.objects.filter(schedule=schedule)
            .values('prepayment_id')
            .annotate(total=Sum('amount'))
        }

    used_prepayment_ids = set(usage_totals.keys())
    prepayments = _schedules_allowed_prepayments_queryset(actor, followup).filter(
        Q(status='active', balance__gt=0) | Q(id__in=used_prepayment_ids)
    ).order_by('payment_date', 'id')

    return [
        _schedules_prepayment_option_payload(prepayment, usage_totals.get(prepayment.id, 0))
        for prepayment in prepayments
    ]


def _schedules_restore_prepayments(schedule):
    from decimal import Decimal

    usages = list(
        PrepaymentUsage.objects.filter(schedule=schedule)
        .select_related('prepayment')
        .order_by('id')
    )
    if not usages and not schedule.use_prepayment and not schedule.prepayment_id and not schedule.prepayment_amount:
        return Decimal('0')

    restored_total = Decimal('0')
    for usage in usages:
        prepayment = usage.prepayment
        amount = usage.amount or Decimal('0')
        balance_before = prepayment.balance or Decimal('0')
        prepayment.balance = (prepayment.balance or Decimal('0')) + amount
        if prepayment.status == 'depleted' and prepayment.balance > 0:
            prepayment.status = 'active'
        prepayment.save(update_fields=['balance', 'status'])
        _prepayment_create_ledger(
            prepayment,
            PrepaymentLedgerEntry.ENTRY_RESTORE,
            actor=getattr(schedule, 'user', None),
            amount=amount,
            balance_before=balance_before,
            balance_after=prepayment.balance,
            memo=f'일정 선결제 차감 복구: {schedule.visit_date}',
            schedule=schedule,
            usage=usage,
        )
        restored_total += amount

    if usages:
        PrepaymentUsage.objects.filter(id__in=[usage.id for usage in usages]).delete()

    schedule.use_prepayment = False
    schedule.prepayment = None
    schedule.prepayment_amount = Decimal('0')
    schedule.delivery_payment_type = Schedule.DELIVERY_PAYMENT_TYPE_NORMAL
    schedule.delivery_payment_status = Schedule.DELIVERY_PAYMENT_STATUS_NORMAL
    schedule.save(update_fields=[
        'use_prepayment',
        'prepayment',
        'prepayment_amount',
        'delivery_payment_type',
        'delivery_payment_status',
        'updated_at',
    ])
    return restored_total


def _schedules_parse_prepayment_inputs(raw_items):
    if not isinstance(raw_items, list):
        raise ValueError('선결제 선택 목록을 확인하세요.')
    if len(raw_items) > 20:
        raise ValueError('선결제는 최대 20건까지 선택할 수 있습니다.')

    parsed = []
    seen_ids = set()
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f'{index}번째 선결제 형식이 올바르지 않습니다.')
        prepayment_id = raw_item.get('id') or raw_item.get('prepaymentId') or raw_item.get('prepayment_id')
        try:
            prepayment_id = int(prepayment_id)
        except (TypeError, ValueError):
            raise ValueError(f'{index}번째 선결제를 선택하세요.')
        if prepayment_id in seen_ids:
            raise ValueError('같은 선결제를 중복 선택할 수 없습니다.')
        seen_ids.add(prepayment_id)

        amount = _parse_optional_decimal(raw_item.get('amount'))
        if amount is None or amount <= 0:
            raise ValueError(f'{index}번째 선결제 차감 금액을 입력하세요.')
        parsed.append((prepayment_id, amount))

    if not parsed:
        raise ValueError('사용할 선결제를 하나 이상 선택하세요.')
    return parsed


def _schedules_apply_prepayments(schedule, actor, raw_items, enforce_delivery_total=False):
    from decimal import Decimal

    if schedule.activity_type != 'delivery':
        raise ValueError('납품 일정에서만 선결제를 사용할 수 있습니다.')

    selected_items = _schedules_parse_prepayment_inputs(raw_items)
    selected_ids = [prepayment_id for prepayment_id, _amount in selected_items]
    existing_usage_totals = {
        row['prepayment_id']: row['total'] or Decimal('0')
        for row in PrepaymentUsage.objects.filter(schedule=schedule)
        .values('prepayment_id')
        .annotate(total=Sum('amount'))
    }
    existing_ids = set(existing_usage_totals.keys())

    accessible_prepayments = {
        prepayment.id: prepayment
        for prepayment in _schedules_allowed_prepayments_queryset(actor, schedule.followup)
        .select_for_update(of=('self',))
        .filter(Q(status='active', balance__gt=0) | Q(id__in=existing_ids), id__in=selected_ids)
    }
    for prepayment_id, amount in selected_items:
        prepayment = accessible_prepayments.get(prepayment_id)
        if not prepayment:
            raise ValueError('선택한 선결제를 찾을 수 없습니다.')
        available_balance = (prepayment.balance or Decimal('0')) + existing_usage_totals.get(prepayment_id, Decimal('0'))
        if amount > available_balance:
            payer_name = prepayment.payer_name or '미지정'
            raise ValueError(f'{payer_name} 선결제 잔액이 부족합니다.')

    if enforce_delivery_total:
        selected_total = sum((amount for _prepayment_id, amount in selected_items), Decimal('0'))
        _delivery_text, delivery_total = _schedules_delivery_items_summary(schedule)
        if delivery_total <= 0:
            raise ValueError('차감할 납품 품목 합계가 없습니다. 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.')
        if selected_total > Decimal(str(delivery_total)):
            raise ValueError(f'선결제 차감 금액은 납품 품목 합계 {_money_int(delivery_total):,}원까지 입력할 수 있습니다.')

    _schedules_restore_prepayments(schedule)

    first_item = schedule.delivery_items_set.order_by('id').first()
    product_name = first_item.item_name if first_item else schedule.get_activity_type_display()
    quantity = first_item.quantity if first_item else 1
    total_used = Decimal('0')
    first_prepayment = None

    for prepayment_id, amount in selected_items:
        prepayment = Prepayment.objects.select_for_update().get(id=prepayment_id)
        if prepayment.balance < amount:
            payer_name = prepayment.payer_name or '미지정'
            raise ValueError(f'{payer_name} 선결제 잔액이 부족합니다.')

        balance_before = prepayment.balance
        prepayment.balance -= amount
        prepayment.status = 'depleted' if prepayment.balance <= 0 else 'active'
        prepayment.save(update_fields=['balance', 'status'])
        usage = PrepaymentUsage.objects.create(
            prepayment=prepayment,
            schedule=schedule,
            schedule_item=first_item,
            product_name=product_name,
            quantity=quantity,
            amount=amount,
            remaining_balance=prepayment.balance,
            memo=f'React 일정 수정에서 차감: {schedule.visit_date}',
        )
        _prepayment_create_ledger(
            prepayment,
            PrepaymentLedgerEntry.ENTRY_DELIVERY_DEDUCTION,
            actor=actor,
            amount=amount,
            balance_before=balance_before,
            balance_after=prepayment.balance,
            memo=f'납품 일정 차감: {schedule.visit_date}',
            schedule=schedule,
            usage=usage,
        )
        total_used += amount
        if first_prepayment is None:
            first_prepayment = prepayment

    schedule.use_prepayment = total_used > 0
    schedule.prepayment = first_prepayment
    schedule.prepayment_amount = total_used
    schedule.delivery_payment_type = Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT if total_used > 0 else Schedule.DELIVERY_PAYMENT_TYPE_NORMAL
    schedule.delivery_payment_status = (
        Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT
        if total_used > 0 else Schedule.DELIVERY_PAYMENT_STATUS_NORMAL
    )
    schedule.save(update_fields=[
        'use_prepayment',
        'prepayment',
        'prepayment_amount',
        'delivery_payment_type',
        'delivery_payment_status',
        'updated_at',
    ])
    return total_used


def _schedules_parse_positive_id(raw_value, error_message):
    if raw_value in (None, ''):
        return None
    try:
        parsed = int(str(raw_value).strip())
    except (TypeError, ValueError):
        raise ValueError(error_message)
    if parsed <= 0:
        raise ValueError(error_message)
    return parsed


def _schedules_parse_delivery_item_inputs(raw_items, request=None, target_schedule=None):
    from decimal import Decimal, InvalidOperation

    if not isinstance(raw_items, list):
        raise ValueError('납품 품목 목록을 확인하세요.')
    if len(raw_items) > 50:
        raise ValueError('납품 품목은 최대 50개까지 저장할 수 있습니다.')

    cleaned = []
    product_cache = {}
    for index, raw_item in enumerate(raw_items, start=1):
        if not isinstance(raw_item, dict):
            raise ValueError(f'{index}번째 납품 품목 형식이 올바르지 않습니다.')

        item_name = str(raw_item.get('itemName') or raw_item.get('item_name') or raw_item.get('name') or '').strip()
        product_id_raw = raw_item.get('productId')
        if product_id_raw is None:
            product_id_raw = raw_item.get('product_id')
        quantity_raw = raw_item.get('quantity')
        unit_price_raw = raw_item.get('unitPrice')
        if unit_price_raw is None:
            unit_price_raw = raw_item.get('unit_price')
        discount_rate_raw = raw_item.get('discountRate')
        if discount_rate_raw is None:
            discount_rate_raw = raw_item.get('discount_rate')
        discount_unit_price_raw = raw_item.get('discountUnitPrice')
        if discount_unit_price_raw is None:
            discount_unit_price_raw = raw_item.get('discount_unit_price')
        source_quote_schedule_id = _schedules_parse_positive_id(
            raw_item.get('sourceQuoteScheduleId') or raw_item.get('source_quote_schedule_id'),
            '불러온 원본 견적 일정 정보가 올바르지 않습니다.',
        )
        source_quote_item_id = _schedules_parse_positive_id(
            raw_item.get('sourceQuoteItemId') or raw_item.get('source_quote_item_id'),
            '불러온 원본 견적 품목 정보가 올바르지 않습니다.',
        )
        existing_item_id = _schedules_parse_positive_id(
            raw_item.get('id') or raw_item.get('pk'),
            '납품 품목 정보가 올바르지 않습니다.',
        )
        unit = str(raw_item.get('unit') or 'EA').strip()[:50] or 'EA'
        quote_group = str(raw_item.get('quoteGroup') or raw_item.get('quote_group') or '').strip()[:100]
        notes = str(raw_item.get('notes') or '').strip()
        option_description = str(
            raw_item.get('optionDescription')
            or raw_item.get('option_description')
            or ''
        ).strip()

        product_id_text = '' if product_id_raw is None else str(product_id_raw).strip()
        quantity_text = '' if quantity_raw is None else str(quantity_raw).replace(',', '').strip()
        unit_price_text = '' if unit_price_raw is None else str(unit_price_raw).replace(',', '').strip()
        discount_rate_text = '' if discount_rate_raw is None else str(discount_rate_raw).replace(',', '').strip()
        discount_unit_price_text = '' if discount_unit_price_raw is None else str(discount_unit_price_raw).replace(',', '').strip()
        if (
            not product_id_text
            and not item_name
            and not quantity_text
            and not unit_price_text
            and not discount_rate_text
            and not discount_unit_price_text
            and not notes
        ):
            continue

        product = None
        if product_id_text:
            if request is None:
                raise ValueError(f'{index}번째 제품 선택을 확인하세요.')
            try:
                product_id = int(product_id_text)
            except (TypeError, ValueError):
                raise ValueError(f'{index}번째 제품 선택이 올바르지 않습니다.')
            if product_id not in product_cache:
                product_cache[product_id] = get_accessible_products(request).filter(id=product_id).first()
            product = product_cache[product_id]
            if not product:
                raise ValueError(f'{index}번째 선택한 제품을 찾을 수 없습니다.')
            item_name = item_name or product.product_code
            unit = (product.unit or unit)[:50] or 'EA'

        if not item_name:
            raise ValueError(f'{index}번째 품목명을 입력하세요.')
        if len(item_name) > 200:
            raise ValueError(f'{index}번째 품목명은 200자 이하로 입력하세요.')

        try:
            quantity = int(quantity_text)
        except (TypeError, ValueError):
            raise ValueError(f'{index}번째 수량은 1 이상의 숫자로 입력하세요.')
        if quantity <= 0:
            raise ValueError(f'{index}번째 수량은 1 이상이어야 합니다.')

        unit_price = None
        if unit_price_text:
            try:
                unit_price = Decimal(unit_price_text)
            except (InvalidOperation, ValueError):
                raise ValueError(f'{index}번째 단가는 0 이상의 숫자로 입력하세요.')
            if unit_price < 0:
                raise ValueError(f'{index}번째 단가는 0 이상이어야 합니다.')

        discount_rate = Decimal('0')
        if discount_rate_text:
            try:
                discount_rate = Decimal(discount_rate_text)
            except (InvalidOperation, ValueError):
                raise ValueError(f'{index}번째 할인율은 0부터 100 사이의 숫자로 입력하세요.')
            if discount_rate < 0 or discount_rate > 100:
                raise ValueError(f'{index}번째 할인율은 0부터 100 사이의 숫자로 입력하세요.')

        discount_unit_price = None
        if discount_unit_price_text:
            try:
                discount_unit_price = Decimal(discount_unit_price_text)
            except (InvalidOperation, ValueError):
                raise ValueError(f'{index}번째 할인단가는 0 이상의 숫자로 입력하세요.')
            if discount_unit_price < 0:
                raise ValueError(f'{index}번째 할인단가는 0 이상이어야 합니다.')
            if unit_price is not None and discount_unit_price > unit_price:
                raise ValueError(f'{index}번째 할인단가는 기준단가보다 클 수 없습니다.')
            if unit_price is not None and unit_price > 0 and discount_unit_price <= 0 and discount_rate <= 0:
                discount_unit_price = None

        item_data = {
            '_existing_item_id': existing_item_id,
            'item_name': item_name,
            'quantity': quantity,
            'unit': unit,
            'unit_price': unit_price,
            'discount_rate': discount_rate,
            'discount_unit_price': discount_unit_price,
            'tax_invoice_issued': False,
            'quote_group': quote_group,
            'notes': notes,
            'option_description': option_description,
        }
        if product:
            item_data['product'] = product

        source_quote_schedule = None
        source_quote_item = None
        if source_quote_item_id:
            if request is None:
                raise ValueError('불러온 원본 견적 품목 정보가 올바르지 않습니다.')
            source_quote_item = DeliveryItem.objects.select_related(
                'schedule',
                'schedule__followup',
                'schedule__followup__department',
            ).filter(
                id=source_quote_item_id,
                schedule__activity_type='quote',
            ).first()
            if not source_quote_item or not source_quote_item.schedule_id:
                raise ValueError('불러온 원본 견적 품목을 찾을 수 없습니다.')
            source_quote_schedule = source_quote_item.schedule
            if source_quote_schedule_id and source_quote_schedule_id != source_quote_schedule.id:
                raise ValueError('불러온 원본 견적 일정과 품목이 일치하지 않습니다.')
            source_quote_schedule_id = source_quote_schedule.id

        if source_quote_schedule_id and source_quote_schedule is None:
            if request is None:
                raise ValueError('불러온 원본 견적 일정 정보가 올바르지 않습니다.')
            source_quote_schedule = Schedule.objects.select_related(
                'followup',
                'followup__department',
            ).filter(
                id=source_quote_schedule_id,
                activity_type='quote',
            ).first()
            if not source_quote_schedule:
                raise ValueError('불러온 원본 견적 일정을 찾을 수 없습니다.')

        if source_quote_schedule:
            if source_quote_schedule.user_id != request.user.id:
                raise PermissionError('본인이 작성한 견적 일정만 납품으로 불러올 수 있습니다.')
            if target_schedule and not _schedules_quote_matches_delivery_target(source_quote_schedule, target_schedule):
                raise PermissionError('납품 일정과 다른 고객/부서의 견적은 납품으로 불러올 수 없습니다.')
            item_data['source_quote_schedule'] = source_quote_schedule
        if source_quote_item:
            item_data['source_quote_item'] = source_quote_item
        cleaned.append(item_data)

    if not cleaned:
        raise ValueError('품목명과 수량이 있는 납품 품목을 하나 이상 입력하세요.')
    return cleaned


def _schedules_source_quote_id_values(raw_value):
    if raw_value in (None, ''):
        return []
    if isinstance(raw_value, str) and ',' in raw_value:
        return raw_value.split(',')
    if isinstance(raw_value, (list, tuple, set)):
        return list(raw_value)
    return [raw_value]


def _schedules_normalize_source_quote_schedule_ids(raw_values):
    source_ids = []
    seen = set()
    for raw_id in raw_values:
        if raw_id in (None, ''):
            continue
        try:
            source_id = int(str(raw_id).strip())
        except (TypeError, ValueError):
            raise ValueError('불러온 원본 견적 일정 정보가 올바르지 않습니다.')
        if source_id <= 0:
            raise ValueError('불러온 원본 견적 일정 정보가 올바르지 않습니다.')
        if source_id not in seen:
            seen.add(source_id)
            source_ids.append(source_id)
    return source_ids


def _schedules_parse_source_quote_schedule_ids(payload):
    if not isinstance(payload, dict):
        return []

    raw_values = []
    for key in (
        'sourceQuoteScheduleIds',
        'source_quote_schedule_ids',
        'sourceQuoteScheduleId',
        'source_quote_schedule_id',
        'fromQuoteScheduleId',
        'from_quote_schedule_id',
    ):
        raw_values.extend(_schedules_source_quote_id_values(payload.get(key)))

    raw_items = payload.get('items')
    if isinstance(raw_items, list):
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            raw_values.extend(_schedules_source_quote_id_values(raw_item.get('sourceQuoteScheduleId')))
            raw_values.extend(_schedules_source_quote_id_values(raw_item.get('source_quote_schedule_id')))

    return _schedules_normalize_source_quote_schedule_ids(raw_values)


def _schedules_parse_checked_quote_schedule_ids(payload):
    if not isinstance(payload, dict):
        return []

    raw_values = []
    for key in (
        'checkedQuoteScheduleIds',
        'checked_quote_schedule_ids',
        'completedQuoteScheduleIds',
        'completed_quote_schedule_ids',
        'completeQuoteScheduleIds',
        'complete_quote_schedule_ids',
        'deliveredQuoteScheduleIds',
        'delivered_quote_schedule_ids',
    ):
        raw_values.extend(_schedules_source_quote_id_values(payload.get(key)))
    return _schedules_normalize_source_quote_schedule_ids(raw_values)


def _schedules_schedule_target_department_id(schedule):
    if getattr(schedule, 'department_id', None):
        return schedule.department_id
    followup = getattr(schedule, 'followup', None)
    if followup and getattr(followup, 'department_id', None):
        return followup.department_id
    return None


def _schedules_quote_matches_delivery_target(quote_schedule, delivery_schedule):
    if (
        quote_schedule.followup_id
        and delivery_schedule.followup_id
        and quote_schedule.followup_id == delivery_schedule.followup_id
    ):
        return True

    quote_department_id = _schedules_schedule_target_department_id(quote_schedule)
    delivery_department_id = _schedules_schedule_target_department_id(delivery_schedule)
    return bool(
        delivery_department_id
        and quote_department_id
        and quote_department_id == delivery_department_id
    )


def _schedules_quote_item_identity(item):
    return (
        item.product_id or 0,
        (item.item_name or '').strip().lower(),
        (item.unit or '').strip().lower(),
        str(item.unit_price or ''),
        str(item.discount_rate or ''),
        str(item.discount_unit_price or ''),
        _quote_group_key(getattr(item, 'quote_group', '')),
    )


def _schedules_quote_item_total_for_quantity(item, quantity):
    from decimal import Decimal, ROUND_HALF_UP

    if not quantity:
        return Decimal('0')
    unit_price = item.get_effective_unit_price()
    if unit_price is None:
        unit_price = item.unit_price
    if unit_price is None:
        if item.total_price is not None and item.quantity:
            original_quantity = Decimal(str(item.quantity or 0))
            if original_quantity > 0:
                return (
                    Decimal(str(item.total_price or 0)) *
                    Decimal(str(quantity)) /
                    original_quantity
                ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return Decimal('0')
    return vat.item_gross_total(item, unit_price=unit_price, quantity=quantity)


def _schedules_quote_item_imported_quantities(
    quote_schedule,
    quote_items,
    include_legacy_matches=False,
    exclude_delivery_schedule_id=None,
):
    from decimal import Decimal

    quote_item_ids = [item.id for item in quote_items if item.id]
    imported_quantities = {item.id: Decimal('0') for item in quote_items if item.id}
    has_import_activity = False

    if quote_item_ids:
        linked_queryset = DeliveryItem.objects.filter(
            source_quote_item_id__in=quote_item_ids,
            schedule__activity_type='delivery',
        ).exclude(
            schedule__status='cancelled',
        )
        if exclude_delivery_schedule_id:
            linked_queryset = linked_queryset.exclude(schedule_id=exclude_delivery_schedule_id)
        linked_rows = linked_queryset.values('source_quote_item_id').annotate(total=Sum('quantity'))
        for row in linked_rows:
            source_item_id = row['source_quote_item_id']
            if source_item_id in imported_quantities:
                imported_quantities[source_item_id] += Decimal(str(row['total'] or 0))
                if row['total']:
                    has_import_activity = True

    schedule_linked_items = DeliveryItem.objects.filter(
        source_quote_schedule=quote_schedule,
        source_quote_item__isnull=True,
        schedule__activity_type='delivery',
    ).exclude(
        schedule__status='cancelled',
    ).select_related('schedule')
    if exclude_delivery_schedule_id:
        schedule_linked_items = schedule_linked_items.exclude(schedule_id=exclude_delivery_schedule_id)
    if schedule_linked_items.exists():
        has_import_activity = True
        items_by_identity = {}
        for item in quote_items:
            items_by_identity.setdefault(_schedules_quote_item_identity(item), []).append(item)
        for delivered_item in schedule_linked_items:
            for quote_item in items_by_identity.get(_schedules_quote_item_identity(delivered_item), []):
                if quote_item.id in imported_quantities:
                    imported_quantities[quote_item.id] += Decimal(str(delivered_item.quantity or 0))
                    break

    if include_legacy_matches:
        legacy_delivery_schedules = Schedule.objects.filter(
            user_id=quote_schedule.user_id,
            activity_type='delivery',
        ).exclude(status='cancelled')
        if exclude_delivery_schedule_id:
            legacy_delivery_schedules = legacy_delivery_schedules.exclude(id=exclude_delivery_schedule_id)
        if quote_schedule.followup_id:
            legacy_delivery_schedules = legacy_delivery_schedules.filter(followup_id=quote_schedule.followup_id)
        legacy_delivery_items = DeliveryItem.objects.filter(
            schedule__in=legacy_delivery_schedules,
            source_quote_schedule__isnull=True,
            source_quote_item__isnull=True,
        )
        if legacy_delivery_items.exists():
            remaining_by_identity = {}
            for quote_item in quote_items:
                remaining_by_identity.setdefault(_schedules_quote_item_identity(quote_item), []).append(quote_item)
            for delivered_item in legacy_delivery_items:
                candidates = remaining_by_identity.get(_schedules_quote_item_identity(delivered_item), [])
                for quote_item in candidates:
                    if quote_item.id not in imported_quantities:
                        continue
                    quote_quantity = Decimal(str(quote_item.quantity or 0))
                    already_imported = imported_quantities[quote_item.id]
                    if already_imported >= quote_quantity:
                        continue
                    imported_quantities[quote_item.id] += Decimal(str(delivered_item.quantity or 0))
                    has_import_activity = True
                    break

    return imported_quantities, has_import_activity


def _schedules_quote_item_progress_entries(
    quote_schedule,
    include_legacy_matches=False,
    exclude_delivery_schedule_id=None,
):
    from decimal import Decimal

    quote_items = list(quote_schedule.delivery_items_set.all().order_by('id'))
    if not quote_items:
        return [], False, False, {}

    imported_quantities, has_import_activity = _schedules_quote_item_imported_quantities(
        quote_schedule,
        quote_items,
        include_legacy_matches=include_legacy_matches,
        exclude_delivery_schedule_id=exclude_delivery_schedule_id,
    )
    remaining_entries = []
    progress_by_item_id = {}
    has_sold_items = False
    for item in quote_items:
        quantity = Decimal(str(item.quantity or 0))
        imported_quantity = imported_quantities.get(item.id, Decimal('0'))
        if imported_quantity > 0:
            has_sold_items = True
        remaining_quantity = quantity - imported_quantity
        if remaining_quantity > 0:
            if remaining_quantity == int(remaining_quantity):
                remaining_quantity = int(remaining_quantity)
            remaining_entries.append((item, remaining_quantity))
        progress_by_item_id[item.id] = {
            'quotedQuantity': quantity,
            'deliveredQuantity': imported_quantity,
            'remainingQuantity': max(quantity - imported_quantity, Decimal('0')),
        }

    return remaining_entries, has_import_activity, has_sold_items, progress_by_item_id


def _schedules_quote_item_progress_entries_for_schedules(
    quote_schedules,
    include_legacy_matches_for_completed=False,
    exclude_delivery_schedule_id=None,
):
    """Return quote item delivery progress for many quote schedules with bulk queries."""
    from collections import defaultdict
    from decimal import Decimal

    schedules = list(quote_schedules)
    if not schedules:
        return {}

    quote_items_by_schedule_id = {}
    imported_quantities = {}
    item_schedule_id_by_item_id = {}
    identity_items_by_schedule = defaultdict(list)
    has_import_activity_by_schedule_id = {schedule.id: False for schedule in schedules}

    for schedule in schedules:
        quote_items = list(schedule.delivery_items_set.all())
        quote_items.sort(key=lambda item: item.id or 0)
        quote_items_by_schedule_id[schedule.id] = quote_items
        for item in quote_items:
            if not item.id:
                continue
            imported_quantities[item.id] = Decimal('0')
            item_schedule_id_by_item_id[item.id] = schedule.id
            identity_items_by_schedule[(schedule.id, _schedules_quote_item_identity(item))].append(item)

    quote_item_ids = list(imported_quantities)
    if quote_item_ids:
        linked_queryset = DeliveryItem.objects.filter(
            source_quote_item_id__in=quote_item_ids,
            schedule__activity_type='delivery',
        ).exclude(
            schedule__status='cancelled',
        )
        if exclude_delivery_schedule_id:
            linked_queryset = linked_queryset.exclude(schedule_id=exclude_delivery_schedule_id)
        for row in linked_queryset.values('source_quote_item_id').annotate(total=Sum('quantity')):
            source_item_id = row['source_quote_item_id']
            if source_item_id not in imported_quantities:
                continue
            quantity = Decimal(str(row['total'] or 0))
            imported_quantities[source_item_id] += quantity
            schedule_id = item_schedule_id_by_item_id.get(source_item_id)
            if schedule_id and quantity:
                has_import_activity_by_schedule_id[schedule_id] = True

    schedule_ids = [schedule.id for schedule in schedules]
    schedule_linked_items = DeliveryItem.objects.filter(
        source_quote_schedule_id__in=schedule_ids,
        source_quote_item__isnull=True,
        schedule__activity_type='delivery',
    ).exclude(
        schedule__status='cancelled',
    ).select_related('schedule')
    if exclude_delivery_schedule_id:
        schedule_linked_items = schedule_linked_items.exclude(schedule_id=exclude_delivery_schedule_id)
    for delivered_item in schedule_linked_items:
        source_schedule_id = delivered_item.source_quote_schedule_id
        if not source_schedule_id:
            continue
        has_import_activity_by_schedule_id[source_schedule_id] = True
        candidates = identity_items_by_schedule.get((
            source_schedule_id,
            _schedules_quote_item_identity(delivered_item),
        ), [])
        for quote_item in candidates:
            if quote_item.id in imported_quantities:
                imported_quantities[quote_item.id] += Decimal(str(delivered_item.quantity or 0))
                break

    if include_legacy_matches_for_completed:
        completed_schedules = [
            schedule
            for schedule in schedules
            if schedule.status == 'completed' and schedule.followup_id
        ]
        completed_schedule_ids_by_owner_followup = defaultdict(list)
        for schedule in completed_schedules:
            completed_schedule_ids_by_owner_followup[(schedule.user_id, schedule.followup_id)].append(schedule.id)

        if completed_schedule_ids_by_owner_followup:
            owner_ids = {owner_id for owner_id, _followup_id in completed_schedule_ids_by_owner_followup}
            followup_ids = {followup_id for _owner_id, followup_id in completed_schedule_ids_by_owner_followup}
            legacy_delivery_items = DeliveryItem.objects.filter(
                schedule__user_id__in=owner_ids,
                schedule__followup_id__in=followup_ids,
                schedule__activity_type='delivery',
                source_quote_schedule__isnull=True,
                source_quote_item__isnull=True,
            ).exclude(
                schedule__status='cancelled',
            ).select_related('schedule')
            if exclude_delivery_schedule_id:
                legacy_delivery_items = legacy_delivery_items.exclude(schedule_id=exclude_delivery_schedule_id)

            for delivered_item in legacy_delivery_items:
                candidate_schedule_ids = completed_schedule_ids_by_owner_followup.get((
                    delivered_item.schedule.user_id,
                    delivered_item.schedule.followup_id,
                ), [])
                delivered_identity = _schedules_quote_item_identity(delivered_item)
                for schedule_id in candidate_schedule_ids:
                    candidates = identity_items_by_schedule.get((schedule_id, delivered_identity), [])
                    for quote_item in candidates:
                        if quote_item.id not in imported_quantities:
                            continue
                        quote_quantity = Decimal(str(quote_item.quantity or 0))
                        already_imported = imported_quantities[quote_item.id]
                        if already_imported >= quote_quantity:
                            continue
                        imported_quantities[quote_item.id] += Decimal(str(delivered_item.quantity or 0))
                        has_import_activity_by_schedule_id[schedule_id] = True
                        break

    progress_by_schedule_id = {}
    for schedule in schedules:
        remaining_entries = []
        progress_by_item_id = {}
        has_sold_items = False
        for item in quote_items_by_schedule_id.get(schedule.id, []):
            quantity = Decimal(str(item.quantity or 0))
            imported_quantity = imported_quantities.get(item.id, Decimal('0'))
            if imported_quantity > 0:
                has_sold_items = True
            remaining_quantity = quantity - imported_quantity
            if remaining_quantity > 0:
                display_remaining_quantity = remaining_quantity
                if remaining_quantity == int(remaining_quantity):
                    display_remaining_quantity = int(remaining_quantity)
                remaining_entries.append((item, display_remaining_quantity))
            progress_by_item_id[item.id] = {
                'quotedQuantity': quantity,
                'deliveredQuantity': imported_quantity,
                'remainingQuantity': max(quantity - imported_quantity, Decimal('0')),
            }

        progress_by_schedule_id[schedule.id] = {
            'remaining_entries': remaining_entries,
            'has_import_activity': has_import_activity_by_schedule_id.get(schedule.id, False),
            'has_sold_items': has_sold_items,
            'progress_by_item_id': progress_by_item_id,
        }

    return progress_by_schedule_id


def _schedules_remaining_quote_item_entries(quote_schedule, include_legacy_matches=False):
    remaining_entries, has_import_activity, has_sold_items, _progress = _schedules_quote_item_progress_entries(
        quote_schedule,
        include_legacy_matches=include_legacy_matches,
    )
    return remaining_entries, has_import_activity, has_sold_items


def _schedules_quantity_label(value):
    from decimal import Decimal, InvalidOperation

    try:
        quantity = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return str(value)
    if quantity == quantity.to_integral_value():
        return str(int(quantity))
    return format(quantity.normalize(), 'f')


def _schedules_validate_source_quote_item_quantities(delivery_items, target_schedule):
    from decimal import Decimal

    requested_by_item_id = {}
    row_count_by_item_id = {}
    source_items_by_id = {}
    for item_data in delivery_items:
        source_item = item_data.get('source_quote_item')
        if not source_item or not source_item.id:
            continue
        source_item_id = source_item.id
        requested_by_item_id[source_item_id] = (
            requested_by_item_id.get(source_item_id, Decimal('0')) +
            Decimal(str(item_data.get('quantity') or 0))
        )
        row_count_by_item_id[source_item_id] = row_count_by_item_id.get(source_item_id, 0) + 1
        source_items_by_id[source_item_id] = source_item

    for source_item_id, row_count in row_count_by_item_id.items():
        if row_count > 1:
            item = source_items_by_id[source_item_id]
            raise ValueError(
                f'{item.item_name} 견적 품목이 중복되었습니다. 부분 납품은 한 행의 수량을 조정해 저장하세요.'
            )

    if not source_items_by_id:
        return

    quote_items_by_schedule_id = {}
    quote_schedule_by_id = {}
    for source_item in source_items_by_id.values():
        if not source_item.schedule_id:
            continue
        quote_items_by_schedule_id.setdefault(source_item.schedule_id, []).append(source_item)
        quote_schedule_by_id[source_item.schedule_id] = source_item.schedule

    for quote_schedule_id, quote_items in quote_items_by_schedule_id.items():
        quote_schedule = quote_schedule_by_id[quote_schedule_id]
        imported_quantities, _has_import_activity = _schedules_quote_item_imported_quantities(
            quote_schedule,
            quote_items,
            include_legacy_matches=True,
            exclude_delivery_schedule_id=target_schedule.id,
        )
        for source_item in quote_items:
            quoted_quantity = Decimal(str(source_item.quantity or 0))
            already_delivered = imported_quantities.get(source_item.id, Decimal('0'))
            requested_quantity = requested_by_item_id.get(source_item.id, Decimal('0'))
            if already_delivered + requested_quantity > quoted_quantity:
                remaining_quantity = max(quoted_quantity - already_delivered, Decimal('0'))
                unit_label = source_item.unit or ''
                raise ValueError(
                    f'{source_item.item_name} 남은 견적 수량은 '
                    f'{_schedules_quantity_label(remaining_quantity)}{unit_label}입니다. '
                    '요청 수량을 줄이세요.'
                )


def _schedules_mark_source_quote_schedules_completed(
    delivery_schedule,
    actor,
    source_quote_schedule_ids,
    force_complete_source_quote_schedule_ids=None,
):
    force_complete_source_quote_schedule_ids = force_complete_source_quote_schedule_ids or []
    all_source_quote_schedule_ids = []
    for source_id in [*source_quote_schedule_ids, *force_complete_source_quote_schedule_ids]:
        if source_id not in all_source_quote_schedule_ids:
            all_source_quote_schedule_ids.append(source_id)

    if not all_source_quote_schedule_ids or delivery_schedule.activity_type != 'delivery':
        return []

    quote_schedules = Schedule.objects.select_for_update(of=('self',)).select_related(
        'followup',
        'followup__department',
    ).filter(
        id__in=all_source_quote_schedule_ids,
        activity_type='quote',
    )
    quote_by_id = {quote_schedule.id: quote_schedule for quote_schedule in quote_schedules}
    missing_ids = [source_id for source_id in all_source_quote_schedule_ids if source_id not in quote_by_id]
    if missing_ids:
        raise ValueError('불러온 원본 견적 일정을 찾을 수 없습니다.')

    force_complete_source_quote_schedule_ids = set(force_complete_source_quote_schedule_ids)
    completed_ids = []
    for source_id in all_source_quote_schedule_ids:
        quote_schedule = quote_by_id[source_id]
        if quote_schedule.user_id != actor.id:
            raise PermissionError('본인이 작성한 견적 일정만 납품 완료 처리할 수 있습니다.')
        if not _schedules_quote_matches_delivery_target(quote_schedule, delivery_schedule):
            raise PermissionError('납품 일정과 다른 고객/부서의 견적은 완료 처리할 수 없습니다.')
        if source_id not in force_complete_source_quote_schedule_ids:
            remaining_entries, _has_import_activity, _has_sold_items = _schedules_remaining_quote_item_entries(
                quote_schedule,
                include_legacy_matches=True,
            )
            if remaining_entries:
                if quote_schedule.status == 'completed':
                    quote_schedule.status = 'scheduled'
                    quote_schedule.save(update_fields=['status', 'updated_at'])
                continue
        if quote_schedule.status != 'completed':
            quote_schedule.status = 'completed'
            quote_schedule.save(update_fields=['status', 'updated_at'])
            completed_ids.append(quote_schedule.id)
    return completed_ids


def _schedules_delivery_items_summary(schedule):
    from decimal import Decimal

    delivery_lines = []
    total_amount = Decimal('0')
    for item in schedule.delivery_items_set.all().order_by('id'):
        item_total = item.total_price
        if item_total is None and item.unit_price is not None:
            item_total = vat.item_gross_total(item, unit_price=(item.get_effective_unit_price() or item.unit_price))
        if item_total is not None:
            total_amount += item_total

        quantity_label = f"{item.quantity}{item.unit or 'EA'}"
        if item_total is not None:
            delivery_lines.append(f"{item.item_name}: {quantity_label} ({int(item_total):,}원)")
        else:
            delivery_lines.append(f"{item.item_name}: {quantity_label}")

    return '\n'.join(delivery_lines), int(total_amount) if total_amount > 0 else 0


def _schedule_quote_group_summaries(schedule):
    from decimal import Decimal

    groups = {}
    notes_map = _schedule_quote_group_notes_map(schedule)
    for item in schedule.delivery_items_set.all().order_by('id'):
        group_key = _quote_group_key(getattr(item, 'quote_group', ''))
        if group_key not in groups:
            groups[group_key] = {
                'key': group_key,
                'label': _quote_group_label(group_key),
                'notes': notes_map.get(group_key, ''),
                'itemCount': 0,
                'totalAmount': Decimal('0'),
            }
        groups[group_key]['itemCount'] += 1
        if item.quantity:
            groups[group_key]['totalAmount'] += _document_item_prices(item)['effective_unit_price'] * item.quantity

    if not groups:
        groups[''] = {
            'key': '',
            'label': _quote_group_label(''),
            'notes': notes_map.get('', ''),
            'itemCount': 0,
            'totalAmount': Decimal('0'),
        }

    return [
        {
            **group,
            'totalAmount': int(group['totalAmount']),
            'query': _quote_group_query_suffix(group['key']),
        }
        for group in groups.values()
    ]


def _document_generation_file_name(log):
    if log.filename:
        return log.filename
    if log.file:
        return os.path.basename(log.file.name)
    return ''


def _document_generation_file_size(log):
    if log.file_size:
        return log.file_size
    if log.file:
        try:
            return log.file.size
        except Exception:
            return 0
    return 0


def _document_generation_file_payload(log, can_delete=False):
    filename = _document_generation_file_name(log)
    return {
        'id': log.id,
        'filename': filename,
        'size': _file_size_label(_document_generation_file_size(log)),
        'fileSize': _document_generation_file_size(log),
        'transactionNumber': log.transaction_number,
        'documentType': log.document_type,
        'documentTypeLabel': log.get_document_type_display(),
        'outputFormat': log.output_format,
        'outputFormatLabel': log.get_output_format_display(),
        'quoteGroup': log.quote_group or '',
        'quoteGroupLabel': _quote_group_label(log.quote_group),
        'createdAt': _datetime_or_none(log.created_at),
        'createdBy': _user_display_name(log.user) if log.user else '',
        'downloadHref': reverse('reporting:generated_document_download', args=[log.id]) if log.file else '',
        'deleteHref': reverse('reporting:generated_document_delete', args=[log.id]) if can_delete else '',
        'canDelete': bool(can_delete),
    }


def _schedule_registered_documents(schedule):
    return DocumentGenerationLog.objects.filter(
        schedule=schedule,
        output_format='pdf',
        file__isnull=False,
    ).exclude(file='').select_related('user').order_by('-created_at', '-id')


def _schedule_registered_quote_documents(schedule):
    return _schedule_registered_documents(schedule).filter(
        document_type='quotation',
    )


def _schedules_document_actions(schedule, user):
    document_configs = {
        'quotation': {
            'label': '견적서',
            'description': '등록된 품목 정보를 포함한 견적서를 생성합니다.',
        },
        'transaction_statement': {
            'label': '거래명세서',
            'description': '납품 완료 또는 예정 품목의 거래명세서를 생성합니다.',
        },
        'delivery_note': {
            'label': '납품서',
            'description': '납품 예정 품목의 납품서를 생성합니다.',
        },
    }
    activity_documents = {
        'quote': ['quotation'],
        'delivery': ['transaction_statement', 'delivery_note'],
    }
    document_types = activity_documents.get(schedule.activity_type, [])
    company = getattr(getattr(user, 'userprofile', None), 'company', None)
    can_delete_documents = _schedules_can_edit(user, schedule)
    registered_documents = [
        _document_generation_file_payload(log, can_delete=can_delete_documents)
        for log in _schedule_registered_documents(schedule)
    ] if schedule.activity_type in ['quote', 'delivery'] else []
    registered_quotations = [
        _document_generation_file_payload(log, can_delete=can_delete_documents)
        for log in _schedule_registered_quote_documents(schedule)
    ] if schedule.activity_type == 'quote' else []
    registered_transaction_statements = [
        _document_generation_file_payload(log, can_delete=can_delete_documents)
        for log in _schedule_registered_documents(schedule).filter(document_type='transaction_statement')
    ] if schedule.activity_type == 'delivery' else []
    if schedule.activity_type == 'quote':
        auto_attach_label = (
            f'메일 발송 시 견적서 PDF {len(registered_quotations)}개가 자동 첨부됩니다.'
            if registered_quotations else '등록된 견적서 PDF가 없으면 메일 발송 시 새 견적서 PDF를 생성해 자동 첨부합니다.'
        )
    elif schedule.activity_type == 'delivery':
        auto_attach_label = (
            f'메일 발송 시 거래명세서 PDF {len(registered_transaction_statements)}개가 자동 첨부됩니다.'
            if registered_transaction_statements else '등록된 거래명세서 PDF가 없으면 메일 발송 시 새 거래명세서 PDF를 생성해 자동 첨부합니다.'
        )
    else:
        auto_attach_label = ''
    quote_groups = _schedule_quote_group_summaries(schedule) if schedule.activity_type == 'quote' else []

    template_counts = {}
    if company and document_types:
        template_counts = {
            item['document_type']: item['count']
            for item in DocumentTemplate.objects.filter(
                company=company,
                document_type__in=document_types,
                is_active=True,
            ).values('document_type').annotate(count=Count('id'))
        }

    document_items = []
    for document_type in document_types:
        if document_type == 'quotation':
            for group in quote_groups:
                suffix = group['query'] if group['key'] or len(quote_groups) > 1 else ''
                group_label = group['label']
                document_items.append({
                    'type': document_type,
                    'label': group_label if group_label.endswith('견적서') else f'{group_label} 견적서',
                    'description': f'{group_label} 품목 {group["itemCount"]}개를 포함한 견적서를 생성합니다.',
                    'templateCount': template_counts.get(document_type, 0),
                    'previewHref': reverse('reporting:get_document_template_data', args=[document_type, schedule.id]) + suffix,
                    'quoteGroup': group['key'],
                    'quoteGroupLabel': group_label,
                    'itemCount': group['itemCount'],
                    'totalAmount': group['totalAmount'],
                    'formats': [
                        {
                            'format': 'pdf',
                            'label': 'PDF 등록/다운로드',
                            'href': reverse('reporting:generate_document_pdf_format', args=[document_type, schedule.id, 'pdf']) + suffix,
                        },
                        {
                            'format': 'xlsx',
                            'label': 'Excel',
                            'href': reverse('reporting:generate_document_pdf_format', args=[document_type, schedule.id, 'xlsx']) + suffix,
                        },
                    ],
                })
            continue

        document_items.append({
            'type': document_type,
            'label': document_configs[document_type]['label'],
            'description': document_configs[document_type]['description'],
            'templateCount': template_counts.get(document_type, 0),
            'previewHref': reverse('reporting:get_document_template_data', args=[document_type, schedule.id]),
            'quoteGroup': '',
            'quoteGroupLabel': '',
            'itemCount': 0,
            'totalAmount': 0,
            'formats': [
                {
                    'format': 'pdf',
                    'label': 'PDF',
                    'href': reverse('reporting:generate_document_pdf_format', args=[document_type, schedule.id, 'pdf']),
                },
                {
                    'format': 'xlsx',
                    'label': 'Excel',
                    'href': reverse('reporting:generate_document_pdf_format', args=[document_type, schedule.id, 'xlsx']),
                },
            ],
        })

    return {
        'canGenerate': bool(document_types),
        'templateManagerHref': '/documents/',
        'djangoTemplateManagerHref': reverse('reporting:document_template_list'),
        'registeredDocuments': registered_documents,
        'registeredDocumentCount': len(registered_documents),
        'registeredQuotations': registered_quotations,
        'registeredQuotationCount': len(registered_quotations),
        'autoAttachLabel': auto_attach_label,
        'items': document_items,
    }


def _commercial_warning(code, message, severity='warning', context=None):
    warning = {
        'code': code,
        'severity': severity,
        'message': message,
    }
    if context:
        warning['context'] = context
    return warning


def _commercial_status(warnings):
    return 'warning' if warnings else 'ok'


def _commercial_status_label(status):
    return {
        'ok': '정상',
        'warning': '주의 필요',
        'info': '정보',
    }.get(status, status)


def _commercial_item_total(item, quantity=None):
    from decimal import Decimal

    if quantity is None and item.total_price is not None:
        return Decimal(str(item.total_price or 0))
    quantity_value = item.quantity if quantity is None else quantity
    return _schedules_quote_item_total_for_quantity(item, quantity_value)


def _commercial_auto_attach_status(registered_count, template_count):
    if registered_count > 0:
        return 'registered', '등록 PDF 자동첨부'
    if template_count > 0:
        return 'will_generate', '발송 시 생성 가능'
    return 'missing', '자동첨부 후보 없음'


def _commercial_template_counts(user, document_types):
    company = getattr(getattr(user, 'userprofile', None), 'company', None)
    if not company or not document_types:
        return {}
    return {
        row['document_type']: row['count']
        for row in DocumentTemplate.objects.filter(
            company=company,
            document_type__in=document_types,
            is_active=True,
        ).values('document_type').annotate(count=Count('id'))
    }


def _commercial_registered_quote_counts(schedule):
    return {
        _quote_group_key(row['quote_group']): row['count']
        for row in _schedule_registered_quote_documents(schedule)
        .values('quote_group')
        .annotate(count=Count('id'))
    }


def _commercial_quote_checks(schedule, user, documents, email_thread_count):
    from decimal import Decimal

    items = list(schedule.delivery_items_set.all().order_by('id'))
    template_count = _commercial_template_counts(user, ['quotation']).get('quotation', 0)
    registered_quote_counts = _commercial_registered_quote_counts(schedule)
    registered_total = sum(registered_quote_counts.values())
    imported_quantities, has_import_activity = _schedules_quote_item_imported_quantities(
        schedule,
        items,
        include_legacy_matches=True,
    ) if items else ({}, False)

    warnings = []
    groups = {}
    total_quote_amount = Decimal('0')
    total_delivered_amount = Decimal('0')
    total_remaining_amount = Decimal('0')
    total_item_count = 0

    for item in items:
        group_key = _quote_group_key(item.quote_group)
        if group_key not in groups:
            groups[group_key] = {
                'quoteGroup': group_key,
                'quoteGroupLabel': _quote_group_label(group_key),
                'itemCount': 0,
                'quoteAmount': Decimal('0'),
                'deliveredAmount': Decimal('0'),
                'remainingAmount': Decimal('0'),
                'registeredQuotationCount': registered_quote_counts.get(group_key, 0),
                'templateCount': template_count,
                'warnings': [],
            }

        quantity = Decimal(str(item.quantity or 0))
        imported_quantity = imported_quantities.get(item.id, Decimal('0'))
        delivered_quantity = min(imported_quantity, quantity)
        remaining_quantity = max(quantity - delivered_quantity, Decimal('0'))

        item_quote_amount = _commercial_item_total(item)
        item_delivered_amount = _commercial_item_total(item, delivered_quantity)
        item_remaining_amount = _commercial_item_total(item, remaining_quantity)

        groups[group_key]['itemCount'] += 1
        groups[group_key]['quoteAmount'] += item_quote_amount
        groups[group_key]['deliveredAmount'] += item_delivered_amount
        groups[group_key]['remainingAmount'] += item_remaining_amount
        total_item_count += 1
        total_quote_amount += item_quote_amount
        total_delivered_amount += item_delivered_amount
        total_remaining_amount += item_remaining_amount

        if imported_quantity > quantity:
            groups[group_key]['warnings'].append(_commercial_warning(
                'quote_item_overdelivered',
                f'{item.item_name} 납품 수량이 견적 수량보다 큽니다.',
                context={
                    'itemId': item.id,
                    'quotedQuantity': float(quantity),
                    'deliveredQuantity': float(imported_quantity),
                },
            ))

    if not groups and schedule.expected_revenue:
        total_quote_amount = Decimal(str(schedule.expected_revenue or 0))
        groups[''] = {
            'quoteGroup': '',
            'quoteGroupLabel': _quote_group_label(''),
            'itemCount': 0,
            'quoteAmount': total_quote_amount,
            'deliveredAmount': Decimal('0'),
            'remainingAmount': total_quote_amount,
            'registeredQuotationCount': registered_quote_counts.get('', 0),
            'templateCount': template_count,
            'warnings': [],
        }

    for group in groups.values():
        auto_status, auto_label = _commercial_auto_attach_status(
            group['registeredQuotationCount'],
            template_count,
        )
        group['autoAttachStatus'] = auto_status
        group['autoAttachLabel'] = auto_label
        if group['itemCount'] > 0 and group['registeredQuotationCount'] == 0:
            group['warnings'].append(_commercial_warning(
                'missing_registered_quotation',
                f'{group["quoteGroupLabel"]} 품목은 있지만 등록된 견적서 PDF가 없습니다.',
                context={'quoteGroup': group['quoteGroup']},
            ))
        if group['itemCount'] > 0 and auto_status == 'missing':
            group['warnings'].append(_commercial_warning(
                'missing_auto_attach_candidate',
                f'{group["quoteGroupLabel"]} 메일 자동첨부 후보가 없습니다.',
                context={'quoteGroup': group['quoteGroup'], 'documentType': 'quotation'},
            ))
        if group['deliveredAmount'] > 0 and group['remainingAmount'] > 0:
            group['fulfillmentStatus'] = 'partial'
            group['fulfillmentLabel'] = '부분 납품'
        elif group['itemCount'] > 0 and group['remainingAmount'] <= 0:
            group['fulfillmentStatus'] = 'completed'
            group['fulfillmentLabel'] = '납품 반영 완료'
        elif group['itemCount'] > 0:
            group['fulfillmentStatus'] = 'pending'
            group['fulfillmentLabel'] = '미납'
        else:
            group['fulfillmentStatus'] = 'info'
            group['fulfillmentLabel'] = '품목 없음'

        warnings.extend(group['warnings'])

    if schedule.status == 'completed' and total_remaining_amount > 0 and (has_import_activity or total_delivered_amount > 0):
        warnings.append(_commercial_warning(
            'completed_quote_still_importable',
            '완료된 견적에 미납 품목이 남아 견적 불러오기 후보가 될 수 있습니다.',
            context={
                'scheduleId': schedule.id,
                'remainingAmount': int(total_remaining_amount),
            },
        ))

    group_payloads = []
    for group in groups.values():
        group_warnings = group['warnings']
        group_status = _commercial_status(group_warnings)
        group_payloads.append({
            'quoteGroup': group['quoteGroup'],
            'quoteGroupLabel': group['quoteGroupLabel'],
            'itemCount': group['itemCount'],
            'quoteAmount': int(group['quoteAmount']),
            'deliveredAmount': int(group['deliveredAmount']),
            'remainingAmount': int(group['remainingAmount']),
            'registeredQuotationCount': group['registeredQuotationCount'],
            'templateCount': group['templateCount'],
            'autoAttachStatus': group['autoAttachStatus'],
            'autoAttachLabel': group['autoAttachLabel'],
            'fulfillmentStatus': group['fulfillmentStatus'],
            'fulfillmentLabel': group['fulfillmentLabel'],
            'status': group_status,
            'statusLabel': _commercial_status_label(group_status),
            'warnings': group_warnings,
        })

    status = _commercial_status(warnings)
    return {
        'applies': True,
        'kind': 'quote',
        'status': status,
        'statusLabel': _commercial_status_label(status),
        'summary': {
            'quoteGroupCount': len(group_payloads),
            'quoteItemCount': total_item_count,
            'quoteAmount': int(total_quote_amount),
            'deliveredAmount': int(total_delivered_amount),
            'remainingAmount': int(total_remaining_amount),
            'deliveryItemCount': 0,
            'deliveryAmount': 0,
            'registeredDocumentCount': documents.get('registeredDocumentCount', 0),
            'registeredQuotationCount': registered_total,
            'autoAttachReady': bool(registered_total or template_count),
            'emailThreadCount': email_thread_count,
            'warningCount': len(warnings),
        },
        'quoteGroups': group_payloads,
        'delivery': {
            'itemCount': 0,
            'totalAmount': 0,
            'sourceQuoteCount': 0,
            'sourceQuoteItemCount': 0,
            'historyAmountMismatches': [],
            'sourceQuotes': [],
        },
        'documents': {
            'registeredDocumentCount': documents.get('registeredDocumentCount', 0),
            'registeredQuotationCount': documents.get('registeredQuotationCount', 0),
            'autoAttachLabel': documents.get('autoAttachLabel', ''),
        },
        'warnings': warnings,
    }


def _commercial_delivery_checks(schedule, user, documents, email_thread_count):
    from decimal import Decimal

    items = list(schedule.delivery_items_set.all().order_by('id'))
    template_count = _commercial_template_counts(user, ['transaction_statement']).get('transaction_statement', 0)
    registered_statement_count = _schedule_registered_documents(schedule).filter(
        document_type='transaction_statement',
    ).count()
    auto_status, auto_label = _commercial_auto_attach_status(registered_statement_count, template_count)
    total_amount = Decimal('0')
    source_quotes = {}

    for item in items:
        item_amount = _commercial_item_total(item)
        total_amount += item_amount
        if item.source_quote_schedule_id:
            key = (item.source_quote_schedule_id, _quote_group_key(item.quote_group))
            if key not in source_quotes:
                source_quotes[key] = {
                    'sourceQuoteScheduleId': item.source_quote_schedule_id,
                    'quoteGroup': _quote_group_key(item.quote_group),
                    'quoteGroupLabel': _quote_group_label(item.quote_group),
                    'itemCount': 0,
                    'amount': Decimal('0'),
                }
            source_quotes[key]['itemCount'] += 1
            source_quotes[key]['amount'] += item_amount

    history_amount_mismatches = []
    for history in schedule.histories.filter(
        action_type='delivery_schedule',
        delivery_amount__isnull=False,
    ).order_by('-created_at'):
        note_amount = _money_int(history.delivery_amount)
        item_amount = int(total_amount)
        if note_amount != item_amount:
            history_amount_mismatches.append({
                'historyId': history.id,
                'noteAmount': note_amount,
                'itemAmount': item_amount,
                'createdAt': _datetime_or_none(history.created_at),
            })

    warnings = []
    if items and auto_status == 'missing':
        warnings.append(_commercial_warning(
            'missing_auto_attach_candidate',
            '거래명세서 메일 자동첨부 후보가 없습니다.',
            context={'documentType': 'transaction_statement'},
        ))
    if history_amount_mismatches:
        warnings.append(_commercial_warning(
            'delivery_note_amount_mismatch',
            '납품 노트 금액과 실제 납품 품목 합계가 일치하지 않습니다.',
            context={'mismatchCount': len(history_amount_mismatches)},
        ))
    if schedule.activity_type == 'delivery' and not items:
        warnings.append(_commercial_warning(
            'delivery_without_items',
            '납품 일정에 등록된 납품 품목이 없습니다.',
        ))

    source_quote_payloads = [
        {
            **source,
            'amount': int(source['amount']),
        }
        for source in source_quotes.values()
    ]
    status = _commercial_status(warnings)
    return {
        'applies': True,
        'kind': 'delivery',
        'status': status,
        'statusLabel': _commercial_status_label(status),
        'summary': {
            'quoteGroupCount': 0,
            'quoteItemCount': 0,
            'quoteAmount': 0,
            'deliveredAmount': 0,
            'remainingAmount': 0,
            'deliveryItemCount': len(items),
            'deliveryAmount': int(total_amount),
            'registeredDocumentCount': documents.get('registeredDocumentCount', 0),
            'registeredQuotationCount': documents.get('registeredQuotationCount', 0),
            'autoAttachReady': auto_status != 'missing',
            'emailThreadCount': email_thread_count,
            'warningCount': len(warnings),
        },
        'quoteGroups': [],
        'delivery': {
            'itemCount': len(items),
            'totalAmount': int(total_amount),
            'sourceQuoteCount': len({source['sourceQuoteScheduleId'] for source in source_quote_payloads}),
            'sourceQuoteItemCount': len([item for item in items if item.source_quote_item_id]),
            'historyAmountMismatches': history_amount_mismatches,
            'sourceQuotes': source_quote_payloads,
            'registeredStatementCount': registered_statement_count,
            'templateCount': template_count,
            'autoAttachStatus': auto_status,
            'autoAttachLabel': auto_label,
        },
        'documents': {
            'registeredDocumentCount': documents.get('registeredDocumentCount', 0),
            'registeredQuotationCount': documents.get('registeredQuotationCount', 0),
            'autoAttachLabel': documents.get('autoAttachLabel', ''),
        },
        'warnings': warnings,
    }


def _schedules_commercial_checks(schedule, user, documents, email_thread_count):
    if schedule.activity_type == 'quote':
        return _commercial_quote_checks(schedule, user, documents, email_thread_count)
    if schedule.activity_type == 'delivery':
        return _commercial_delivery_checks(schedule, user, documents, email_thread_count)
    return {
        'applies': False,
        'kind': schedule.activity_type,
        'status': 'info',
        'statusLabel': _commercial_status_label('info'),
        'summary': {
            'quoteGroupCount': 0,
            'quoteItemCount': 0,
            'quoteAmount': 0,
            'deliveredAmount': 0,
            'remainingAmount': 0,
            'deliveryItemCount': 0,
            'deliveryAmount': 0,
            'registeredDocumentCount': 0,
            'registeredQuotationCount': 0,
            'autoAttachReady': False,
            'emailThreadCount': email_thread_count,
            'warningCount': 0,
        },
        'quoteGroups': [],
        'delivery': {
            'itemCount': 0,
            'totalAmount': 0,
            'sourceQuoteCount': 0,
            'sourceQuoteItemCount': 0,
            'historyAmountMismatches': [],
            'sourceQuotes': [],
        },
        'documents': {
            'registeredDocumentCount': 0,
            'registeredQuotationCount': 0,
            'autoAttachLabel': '',
        },
        'warnings': [],
    }


def _schedules_sync_delivery_histories(schedule, actor, created_count):
    if schedule.activity_type != 'delivery':
        return

    delivery_text, total_delivery_amount = _schedules_delivery_items_summary(schedule)
    related_histories = schedule.histories.filter(action_type='delivery_schedule')
    delivery_amount = total_delivery_amount if total_delivery_amount > 0 else None

    if related_histories.exists():
        for history in related_histories:
            history.delivery_items = delivery_text
            history.delivery_amount = delivery_amount
            history.save(update_fields=['delivery_items', 'delivery_amount'])
        return

    History.objects.create(
        schedule=schedule,
        user=schedule.user or actor,
        company=schedule.company,
        followup=schedule.followup,
        department=schedule.department or (schedule.followup.department if schedule.followup else None),
        action_type='delivery_schedule',
        delivery_items=delivery_text,
        delivery_amount=delivery_amount,
        content=f'납품 품목 {created_count}개 추가',
        created_by=actor,
    )


def _schedules_detail_payload(request, schedule, user_profile):
    today = timezone.localdate()
    can_review = _can_review_notes(user_profile)
    can_edit = _schedules_can_edit(request.user, schedule)
    schedule.history_count = schedule.histories.filter(parent_history__isnull=True).count()
    schedule_payload = _schedules_schedule_payload(schedule, today, can_edit)
    followup = schedule.followup
    department = schedule.department or (followup.department if followup and followup.department else None)

    files = [
        {
            'id': file.id,
            'filename': file.original_filename,
            'size': _file_size_label(file.file_size),
            'downloadHref': reverse('reporting:schedule_file_download', args=[file.id]),
            'deleteHref': reverse('reporting:schedule_file_delete', args=[file.id]) if can_edit else '',
            'canDelete': can_edit,
            'uploadedAt': _datetime_or_none(file.uploaded_at),
        }
        for file in schedule.files.all().order_by('-uploaded_at')
    ]
    related_notes_qs = History.objects.filter(
        schedule=schedule,
        parent_history__isnull=True,
    ).select_related(
        'user',
        'followup',
        'followup__company',
        'followup__department',
        'schedule',
        'personal_schedule',
        'reviewer',
    ).annotate(
        reply_count=Count('reply_memos', distinct=True),
        file_count=Count('files', distinct=True),
    ).order_by('-created_at')[:10]
    related_notes = [
        _notes_history_payload(history, today, can_review)
        for history in related_notes_qs
        if can_access_user_data(request.user, history.user)
    ]
    delivery_items = [
        _schedules_delivery_item_payload(item)
        for item in schedule.delivery_items_set.all().order_by('id')
    ]
    prepayment_usages = [
        _schedules_prepayment_usage_payload(usage)
        for usage in schedule.prepayment_usages.all().order_by('id')
    ]
    email_thread_count = EmailLog.objects.filter(
        schedule=schedule,
        gmail_thread_id__isnull=False,
    ).exclude(gmail_thread_id='').values('gmail_thread_id').distinct().count()
    documents = _schedules_document_actions(schedule, request.user)
    commercial_checks = _schedules_commercial_checks(
        schedule,
        request.user,
        documents,
        email_thread_count,
    )
    tax_invoice = _schedules_tax_invoice_payload(schedule, can_edit)

    detail = {
        **schedule_payload,
        'createdAt': _datetime_or_none(schedule.created_at),
        'updatedAt': _datetime_or_none(schedule.updated_at),
        'vatMode': schedule.vat_mode,
        'quoteExtraNotes': _document_quote_extra_notes(schedule),
        'quoteGroupNotes': _schedule_quote_group_note_payloads(schedule),
        'usePrepayment': bool(schedule.use_prepayment),
        'prepaymentId': schedule.prepayment_id,
        'prepaymentAmount': _money_int(schedule.prepayment_amount),
        'prepaymentUsages': prepayment_usages,
        'fileCount': len(files),
        'emailThreadCount': email_thread_count,
        'files': files,
        'canEdit': can_edit,
    }

    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': _user_display_name(schedule.user),
            'userCount': 1,
            'canViewAll': user_profile.can_view_all_users(),
            'canReview': can_review,
            'selectedUserId': schedule.user_id,
        },
        'schedule': detail,
        'links': {
            'schedules': '/schedules/',
            'djangoSchedules': reverse('reporting:schedule_list'),
            'calendar': '/schedules/calendar/',
            'djangoDetail': reverse('reporting:schedule_detail', args=[schedule.id]),
            'djangoEdit': reverse('reporting:schedule_edit', args=[schedule.id]),
            'customer': f'/customers/{followup.id}/' if followup else (f'/accounts/{department.id}/' if department else ''),
            'djangoCustomer': reverse('reporting:followup_detail', args=[followup.id]) if followup else '',
            'createNote': (
                f'/notes/?create=1&customer={followup.id}&schedule={schedule.id}'
                if followup else
                f'/notes/?create=1&department={department.id}&schedule={schedule.id}'
                if department else
                f'/notes/?create=1&schedule={schedule.id}'
            ),
            'djangoCreateNote': reverse('reporting:history_create_from_schedule', args=[schedule.id]),
            'deleteSchedule': reverse('reporting:schedules_delete_api', args=[schedule.id]) if can_edit else '',
            'uploadFiles': reverse('reporting:schedule_file_upload', args=[schedule.id]) if can_edit else '',
            'updateDeliveryItems': reverse('reporting:schedules_delivery_items_update_api', args=[schedule.id]) if can_edit else '',
            'toggleTaxInvoice': tax_invoice['toggleUrl'],
            'prepayments': reverse('reporting:prepayment_api_list') if can_edit else '',
        },
        'edit': _schedules_edit_config(request, schedule, can_edit),
        'ai': {
            'canUseAi': bool(user_profile and user_profile.can_use_ai),
            'message': '' if user_profile and user_profile.can_use_ai else 'AI 기능 사용 권한이 없습니다.',
        },
        'documents': documents,
        'commercialChecks': commercial_checks,
        'taxInvoice': tax_invoice,
        'relatedNotes': related_notes,
        'deliveryItems': delivery_items,
    }


def _schedules_get_detail_schedule(schedule_id):
    return get_object_or_404(
        Schedule.objects.select_related(
            'user',
            'company',
            'followup',
            'followup__company',
            'followup__department',
            'department',
            'department__company',
            'opportunity',
        ).prefetch_related(
            'files',
            'delivery_items_set',
            'quote_group_notes',
            Prefetch(
                'prepayment_usages',
                queryset=PrepaymentUsage.objects.select_related('prepayment', 'prepayment__customer').order_by('id'),
            ),
        ),
        pk=schedule_id,
    )


@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET"])
def schedules_detail_api(request, schedule_id):
    """React CRM schedules 상세 화면용 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    schedule = _schedules_get_detail_schedule(schedule_id)
    if not can_access_user_data(request.user, schedule.user):
        return JsonResponse({
            'success': False,
            'error': '접근 권한이 없습니다.',
        }, status=403)

    user_profile = get_user_profile(request.user)
    return JsonResponse(_schedules_detail_payload(request, schedule, user_profile))


@never_cache
@require_http_methods(["POST"])
def schedules_update_api(request, schedule_id):
    """React schedules 상세 화면용 고객 일정 수정 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    schedule = _schedules_get_detail_schedule(schedule_id)
    if not _schedules_can_edit(request.user, schedule):
        return JsonResponse({
            'success': False,
            'error': '본인의 일정만 수정할 수 있습니다.',
        }, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    try:
        followup_id = int(payload.get('followupId') or 0)
    except (TypeError, ValueError):
        followup_id = 0

    try:
        department_id = int(payload.get('departmentId') or payload.get('department_id') or 0)
    except (TypeError, ValueError):
        department_id = 0

    followup = None
    department = None
    if followup_id:
        followup = FollowUp.objects.filter(
            id=followup_id,
            user__in=get_same_company_users(schedule.user),
        ).select_related('company', 'department').first()
        if not followup:
            return JsonResponse({'success': False, 'error': '수정 가능한 고객을 선택하세요.'}, status=403)
        department = followup.department
    elif department_id:
        department = _department_target_for_user(request.user, department_id)
        if not department:
            return JsonResponse({'success': False, 'error': '수정 가능한 부서/연구실을 선택하세요.'}, status=403)
    else:
        return JsonResponse({'success': False, 'error': '고객 또는 부서/연구실을 선택하세요.'}, status=400)

    allowed_activity_types = {item['value'] for item in _schedules_activity_types_for_edit(request, schedule)}
    activity_type = str(payload.get('activityType') or '').strip()
    if activity_type not in allowed_activity_types:
        return JsonResponse({'success': False, 'error': '활동 유형을 선택하세요.'}, status=400)

    valid_statuses = {
        value for value, _label in _schedules_status_choices_for_activity(activity_type, schedule.status)
    }
    status = str(payload.get('status') or '').strip()
    if status not in valid_statuses:
        return JsonResponse({'success': False, 'error': '일정 상태를 선택하세요.'}, status=400)

    visit_date = _parse_iso_date_or_none(payload.get('visitDate'))
    if not visit_date:
        return JsonResponse({'success': False, 'error': '방문 날짜를 선택하세요.'}, status=400)

    visit_time = _parse_time_or_none(payload.get('visitTime'))
    if not visit_time:
        return JsonResponse({'success': False, 'error': '방문 시간을 선택하세요.'}, status=400)

    try:
        probability = _parse_schedule_probability(activity_type, payload.get('probability'))
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    expected_revenue = _parse_optional_decimal(payload.get('expectedRevenue'))
    expected_close_date = _parse_iso_date_or_none(payload.get('expectedCloseDate'))
    purchase_confirmed_raw = payload.get('purchaseConfirmed')
    purchase_confirmed = purchase_confirmed_raw in (True, 'true', 'True', '1', 'on', 'yes', 'Y')
    prepayment_requested = any(key in payload for key in ['usePrepayment', 'use_prepayment', 'prepayments'])
    use_prepayment_raw = payload.get('usePrepayment', payload.get('use_prepayment'))
    use_prepayment = use_prepayment_raw in (True, 'true', 'True', '1', 'on', 'yes', 'Y')

    schedule.followup = followup
    schedule.department = department
    schedule.company = get_user_profile(schedule.user).company
    if schedule.opportunity_id and (not followup or schedule.opportunity.followup_id != followup.id):
        schedule.opportunity = None
    schedule.visit_date = visit_date
    schedule.visit_time = visit_time
    schedule.activity_type = activity_type
    schedule.status = status
    schedule.location = str(payload.get('location') or '').strip()[:200]
    schedule.notes = str(payload.get('notes') or '').strip()
    if 'quoteExtraNotes' in payload or 'quote_extra_notes' in payload:
        schedule.quote_extra_notes = str(payload.get('quoteExtraNotes', payload.get('quote_extra_notes')) or '').strip()
    schedule.expected_revenue = expected_revenue
    schedule.probability = probability
    schedule.expected_close_date = expected_close_date
    schedule.purchase_confirmed = purchase_confirmed
    try:
        previous_vat_mode = schedule.vat_mode
        schedule.vat_mode = vat.parse_vat_mode(payload, current=schedule.vat_mode)
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    try:
        with transaction.atomic():
            schedule.save(update_fields=[
                'followup',
                'department',
                'company',
                'opportunity',
                'visit_date',
                'visit_time',
                'activity_type',
                'status',
                'location',
                'notes',
                'quote_extra_notes',
                'expected_revenue',
                'probability',
                'expected_close_date',
                'purchase_confirmed',
                'vat_mode',
                'updated_at',
            ])
            if schedule.vat_mode != previous_vat_mode:
                # 품목 총액·견적 합계는 저장 시점에 부가세 모드를 반영하므로 다시 계산한다.
                vat.recalculate_schedule_amounts(schedule)
            if prepayment_requested:
                if use_prepayment:
                    _schedules_apply_prepayments(schedule, request.user, payload.get('prepayments'))
                else:
                    _schedules_restore_prepayments(schedule)
            sync_schedule_delivery_payment_type(schedule)
        _sync_schedule_pipeline(schedule)
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    refreshed = _schedules_get_detail_schedule(schedule.id)
    return JsonResponse({
        **_schedules_detail_payload(request, refreshed, get_user_profile(request.user)),
        'message': '일정을 수정했습니다.',
    })


@never_cache
@require_http_methods(["POST"])
def schedules_delivery_items_update_api(request, schedule_id):
    """React schedules 상세 화면용 납품 품목 저장 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    schedule = _schedules_get_detail_schedule(schedule_id)
    if not _schedules_can_edit(request.user, schedule):
        return JsonResponse({
            'success': False,
            'error': '본인의 일정 납품 품목만 수정할 수 있습니다.',
        }, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    try:
        delivery_items = _schedules_parse_delivery_item_inputs(payload.get('items'), request, schedule)
        source_quote_schedule_ids = _schedules_parse_source_quote_schedule_ids(payload)
        checked_quote_schedule_ids = _schedules_parse_checked_quote_schedule_ids(payload)
        for item_data in delivery_items:
            source_quote_schedule = item_data.get('source_quote_schedule')
            if source_quote_schedule and source_quote_schedule.id not in source_quote_schedule_ids:
                source_quote_schedule_ids.append(source_quote_schedule.id)
        quote_group_notes = _parse_quote_group_notes_payload(payload)
        if quote_group_notes is None and ('quoteExtraNotes' in payload or 'quote_extra_notes' in payload):
            quote_group_notes = {
                '': str(payload.get('quoteExtraNotes', payload.get('quote_extra_notes')) or '').strip(),
            }
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    except PermissionError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=403)

    prepayment_requested = any(key in payload for key in ['usePrepayment', 'use_prepayment', 'prepayments'])
    use_prepayment_raw = payload.get('usePrepayment', payload.get('use_prepayment'))
    use_prepayment = use_prepayment_raw in (True, 'true', 'True', '1', 'on', 'yes', 'Y')

    try:
        completed_quote_schedule_ids = []
        prepayment_total = 0
        with transaction.atomic():
            existing_receivable_status = {
                item.id: {
                    'tax_invoice_issued': item.tax_invoice_issued,
                    'card_payment_received': item.card_payment_received,
                    'receivable_settled': item.receivable_settled,
                    'receivable_settled_at': item.receivable_settled_at,
                    'receivable_settled_by': item.receivable_settled_by,
                }
                for item in DeliveryItem.objects.select_for_update().filter(schedule=schedule)
            }
            existing_source_quote_schedule_ids = []
            for source_id in (
                DeliveryItem.objects.select_for_update()
                .filter(schedule=schedule, source_quote_schedule_id__isnull=False)
                .values_list('source_quote_schedule_id', flat=True)
            ):
                if source_id and source_id not in existing_source_quote_schedule_ids:
                    existing_source_quote_schedule_ids.append(source_id)
            for source_id in existing_source_quote_schedule_ids:
                if source_id not in source_quote_schedule_ids:
                    source_quote_schedule_ids.append(source_id)
            _schedules_validate_source_quote_item_quantities(delivery_items, schedule)
            schedule.delivery_items_set.all().delete()
            for item_data in delivery_items:
                existing_item_id = item_data.pop('_existing_item_id', None)
                if existing_item_id in existing_receivable_status:
                    item_data.update(existing_receivable_status[existing_item_id])
                DeliveryItem.objects.create(schedule=schedule, **item_data)
            _save_schedule_quote_group_notes(schedule, quote_group_notes)
            schedule.save(update_fields=['quote_extra_notes', 'updated_at'])
            _schedules_sync_delivery_histories(schedule, request.user, len(delivery_items))
            if prepayment_requested:
                if use_prepayment:
                    prepayment_total = _schedules_apply_prepayments(
                        schedule,
                        request.user,
                        payload.get('prepayments'),
                        enforce_delivery_total=True,
                    )
                else:
                    _schedules_restore_prepayments(schedule)
            sync_schedule_delivery_payment_type(schedule)
            completed_quote_schedule_ids = _schedules_mark_source_quote_schedules_completed(
                schedule,
                request.user,
                source_quote_schedule_ids,
                force_complete_source_quote_schedule_ids=checked_quote_schedule_ids,
            )
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    except PermissionError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=403)
    except Exception as exc:
        logger.error('React 일정 납품 품목 저장 중 오류: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': '납품 품목 저장 중 오류가 발생했습니다.'}, status=500)

    refreshed = _schedules_get_detail_schedule(schedule.id)
    message = '납품 품목을 저장했습니다.'
    if completed_quote_schedule_ids and prepayment_total:
        message = '납품 품목을 저장하고 원본 견적 일정을 완료 처리했으며 선결제를 차감했습니다.'
    elif completed_quote_schedule_ids:
        message = '납품 품목을 저장하고 원본 견적 일정을 완료 처리했습니다.'
    elif prepayment_total:
        message = '납품 품목을 저장하고 선결제를 차감했습니다.'
    elif prepayment_requested and not use_prepayment:
        message = '납품 품목을 저장하고 선결제 차감을 해제했습니다.'
    return JsonResponse({
        **_schedules_detail_payload(request, refreshed, get_user_profile(request.user)),
        'completedQuoteScheduleIds': completed_quote_schedule_ids,
        'message': message,
    })


def _ai_prompt_context(*items):
    return [str(item).strip() for item in items if item not in (None, '') and str(item).strip()]


def _ai_workspace_prompt_excerpt(value, limit=120):
    text = str(value or '').strip()
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[이메일 제거]', text)
    text = re.sub(r'\b01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[연락처 제거]', text)
    text = re.sub(r'\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[연락처 제거]', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + '...'


def _ai_workspace_feedback_display_text(value):
    text = str(value or '').strip()
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[이메일 제거]', text)
    text = re.sub(r'\b01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[연락처 제거]', text)
    text = re.sub(r'\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b', '[연락처 제거]', text)
    text = re.sub(r'[ \t\f\v]+', ' ', text)
    text = re.sub(r' *[\r\n]+ *', '\n', text)
    return text.strip()


def _ai_workspace_followup_ids(followup_ids):
    if not followup_ids:
        return []
    return [followup_id for followup_id in dict.fromkeys(followup_ids) if followup_id]


AI_WORKSPACE_FEEDBACK_GOAL_DAYS = 30
AI_WORKSPACE_FEEDBACK_GOAL_INTENTS = {
    'follow_up_needed',
    'positive_buying_signal',
    'email_waiting',
}


AI_WORKSPACE_DRAFT_TYPES = {'email', 'note', 'questions'}


def _ai_workspace_action_kind_label(kind):
    return {
        'quote_followup': '견적 후속',
        'delivery_risk': '납품 리스크',
        'service_case': '서비스 후속',
        'calibration_due': '교정 예정',
        'email_waiting': '메일 답장 대기',
        'painpoint_validation': 'PainPoint 검증',
        'customer_followup': '고객 후속',
        'data_quality': '데이터 점검',
    }.get(kind, 'AI 액션')


def _ai_workspace_feedback_intent_label(intent):
    return {
        'resolved_no_purchase': '구매 보류/종료',
        'follow_up_needed': '후속조치 필요',
        'positive_buying_signal': '긍정 신호',
        'email_waiting': '메일 답장 대기',
        'needs_human_review': '검토 필요',
    }.get(intent, '검토 필요')


def _ai_workspace_feedback_fallback(action, feedback_text):
    from datetime import timedelta

    normalized = re.sub(r'\s+', '', str(feedback_text or '').lower())
    title = action.get('title') or 'AI 추천 액션'

    lost_keywords = [
        '안산', '안살', '안사', '구매안', '구입안', '필요없', '필요가없', '거절',
        '취소', '실주', '다른업체', '타사', '예산없', '예산이없', '진행안',
    ]
    completed_keywords = [
        '구매완료', '결제완료', '입금완료', '수주', '판매완료', '납품완료',
        '이미샀', '이미구매', '샀대', '샀습니다',
    ]
    hold_keywords = [
        '보류', '나중', '추후', '검토중', '검토해본', '다음달', '내년',
        '대기', '아직결정', '승인대기', '예산확정후', '장기',
        '허락못받', '허락을못받', '승인못받', '결재못받',
    ]
    urgent_issue_keywords = [
        '급선무', '불만', '클레임', '항의', '문제해결', '우선해결',
        '우선처리', '먼저해결', '해결하는것이급', '해결이급',
    ]
    email_waiting_keywords = [
        '메일보냈', '이메일보냈', '메일발송', '이메일발송', '메일은보냈',
        '답장안', '회신안', '답장이안', '회신이안', '답장없', '회신없',
        '답장대기', '회신대기',
    ]
    positive_keywords = [
        '관심있', '관심을보', '구매의향', '살것같', '산다고', '구매하겠',
        '승인예정', '결재예정', '긍정', '진행하자', '주문예정',
    ]
    request_keywords = [
        '자료', '메일', '견적다시', '재견적', '문의', '전화', '방문', '샘플',
        '가격', '납기', '서류',
    ]

    if any(keyword in normalized for keyword in lost_keywords):
        return {
            'decision': 'hide',
            'recommendedStatus': 'resolved',
            'intent': 'resolved_no_purchase',
            'shouldHide': True,
            'summary': '고객이 현재 구매하지 않겠다는 답변으로 기록됐습니다.',
            'nextAction': '추천 목록에서 종료합니다. 장기 추적이 필요하면 고객 상세에서 별도 후속조치를 등록하세요.',
            'nextActionDate': None,
            'reason': '구매 거절 또는 실주 신호가 포함되어 있어 반복 추천하지 않습니다.',
            'suggestedDraftType': '',
        }
    if any(keyword in normalized for keyword in completed_keywords):
        return {
            'decision': 'hide',
            'recommendedStatus': 'resolved',
            'intent': 'positive_buying_signal',
            'shouldHide': True,
            'summary': '이미 구매/수주/납품 완료된 답변으로 기록됐습니다.',
            'nextAction': '추천 목록에서 종료합니다. 필요하면 완료 일정 또는 납품 기록만 점검하세요.',
            'nextActionDate': None,
            'reason': '완료 신호가 포함되어 있어 추가 추천 액션이 필요하지 않습니다.',
            'suggestedDraftType': '',
        }
    if any(keyword in normalized for keyword in urgent_issue_keywords):
        specific = _ai_workspace_specific_issue_feedback(action, feedback_text)
        return {
            'decision': 'next_action',
            'recommendedStatus': 'next_action',
            'intent': 'follow_up_needed',
            'shouldHide': False,
            'summary': specific.get('summary') or '현재 고객 불만 또는 긴급 이슈 해결이 우선인 상태로 기록됐습니다.',
            'nextAction': specific.get('nextAction') or f"{title} 관련 고객 불만 사항을 확인하고 해결 방안과 후속 일정을 안내하세요.",
            'nextActionDate': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'reason': specific.get('reason') or '장기 보류 항목이 있더라도 현재 불만/급선무 표현이 있어 바로 확인할 후속조치로 남깁니다.',
            'suggestedDraftType': 'note',
        }
    if any(keyword in normalized for keyword in email_waiting_keywords):
        return {
            'decision': 'next_action',
            'recommendedStatus': 'next_action',
            'intent': 'email_waiting',
            'shouldHide': False,
            'summary': '메일 발송 후 고객 답장을 기다리는 상태로 기록됐습니다.',
            'nextAction': f"{title} 관련 메일 회신 여부를 확인하고 필요하면 리마인드 메일을 보내세요.",
            'nextActionDate': (timezone.localdate() + timedelta(days=2)).isoformat(),
            'reason': '메일 발송과 미회신 표현이 함께 있어 답장 대기 후속조치로 전환합니다.',
            'suggestedDraftType': 'email',
        }
    if any(keyword in normalized for keyword in positive_keywords):
        return {
            'decision': 'next_action',
            'recommendedStatus': 'next_action',
            'intent': 'positive_buying_signal',
            'shouldHide': False,
            'summary': '고객에게 긍정적인 구매 신호가 있어 다음 단계를 빠르게 확인해야 합니다.',
            'nextAction': f"{title} 건의 구매 절차, 결재 일정, 필요 서류를 확인하세요.",
            'nextActionDate': (timezone.localdate() + timedelta(days=3)).isoformat(),
            'reason': '긍정 신호가 있어 구매 절차 확인 후속조치로 유지합니다.',
            'suggestedDraftType': 'email',
        }
    if any(keyword in normalized for keyword in hold_keywords):
        return {
            'decision': 'next_action',
            'recommendedStatus': 'next_action',
            'intent': 'follow_up_needed',
            'shouldHide': False,
            'summary': '고객이 보류 또는 추후 검토 상태로 답했습니다.',
            'nextAction': f"{title} 건은 검토 일정과 재연락 기준일을 확인하세요.",
            'nextActionDate': (timezone.localdate() + timedelta(days=14)).isoformat(),
            'reason': '보류 신호가 있어 액션을 닫기보다 재확인 후속조치로 남깁니다.',
            'suggestedDraftType': 'email',
        }
    if any(keyword in normalized for keyword in request_keywords):
        return {
            'decision': 'next_action',
            'recommendedStatus': 'next_action',
            'intent': 'follow_up_needed',
            'shouldHide': False,
            'summary': '고객이 추가 자료나 확인이 필요한 상태로 보입니다.',
            'nextAction': f"{title} 관련 요청 자료를 정리하고 다음 연락에서 의사결정 조건을 확인하세요.",
            'nextActionDate': (timezone.localdate() + timedelta(days=3)).isoformat(),
            'reason': '추가 요청 신호가 있어 바로 닫지 않고 실행 가능한 다음 행동으로 전환합니다.',
            'suggestedDraftType': 'email',
        }

    return {
        'decision': 'keep',
        'recommendedStatus': 'answered',
        'intent': 'needs_human_review',
        'shouldHide': False,
        'summary': '현장 답변은 기록했지만 자동으로 CRM 상태를 바꾸기에는 신호가 명확하지 않습니다.',
        'nextAction': '',
        'nextActionDate': None,
        'reason': '구매 종료, 후속 필요, 긍정 신호, 메일 대기 중 어느 쪽인지 확정하기 어렵습니다.',
        'suggestedDraftType': 'questions',
    }


def _ai_workspace_text_has_urgent_issue(feedback_text):
    normalized = re.sub(r'\s+', '', str(feedback_text or '').lower())
    return any(keyword in normalized for keyword in [
        '급선무', '불만', '클레임', '항의', '문제해결', '우선해결',
        '우선처리', '먼저해결', '해결하는것이급', '해결이급',
    ])


def _ai_workspace_clean_issue_label(value):
    label = re.sub(r'^[\s\-\*\u2022]+|[\s\-\*\u2022:：,.;]+$', '', str(value or ''))
    label = re.sub(r'\s+', ' ', label).strip()
    label = re.sub(r'^(현재는|현재|지금은|지금)\s*', '', label)
    label = label.strip(' -:：,.;')
    return _ai_workspace_prompt_excerpt(label, 40)


def _ai_workspace_feedback_issue_label(feedback_text):
    text = str(feedback_text or '')
    patterns = [
        r'(?:현재(?:는)?|지금(?:은)?)?\s*([가-힣A-Za-z0-9+#/\-\s]{1,30}?)(?:에\s*대한|에대한)\s*불만',
        r'(?:현재(?:는)?|지금(?:은)?)?\s*([가-힣A-Za-z0-9+#/\-\s]{1,30}?)\s*불만',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            label = _ai_workspace_clean_issue_label(match.group(1))
            if label:
                return label
    return ''


def _ai_workspace_long_term_topic_label(feedback_text):
    text = str(feedback_text or '')
    patterns = [
        r'([가-힣A-Za-z0-9+#/\-\s]{1,30})\s*[:：][^\n\r]{0,120}?장기',
        r'([가-힣A-Za-z0-9+#/\-\s]{1,30})(?:은|는)[^\n\r]{0,120}?장기',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            label = _ai_workspace_clean_issue_label(match.group(1))
            if label:
                return label
    return ''


def _ai_workspace_issue_followup_key(kind, issue):
    slug = re.sub(r'\s+', '', str(issue or '').lower())
    slug = re.sub(r'[^\w가-힣+#/\-]+', '', slug)
    return f"{kind}:{slug[:40] or 'issue'}"


def _ai_workspace_issue_followups_from_feedback(feedback_text):
    if not _ai_workspace_text_has_urgent_issue(feedback_text):
        return []

    today = timezone.localdate()
    issue = _ai_workspace_feedback_issue_label(feedback_text) or '고객 불만'
    long_term_topic = _ai_workspace_long_term_topic_label(feedback_text)
    primary_next_action = (
        f"{issue} 불만은 오늘 먼저 증상, 사용 제품 규격, 수량/로트, 사진 여부를 확인하고 "
        "교체/대체품/사용법 안내 중 가능한 해결안을 정해 처리 예정 시간을 회신하세요."
    )
    issue_followups = [{
        'key': _ai_workspace_issue_followup_key('urgent_issue', issue),
        'kind': 'urgent_issue',
        'issue': issue,
        'priority': 'urgent',
        'isPrimary': True,
        'nextAction': primary_next_action,
        'nextActionDate': (today + timedelta(days=1)).isoformat(),
    }]
    if long_term_topic:
        issue_followups.append({
            'key': _ai_workspace_issue_followup_key('long_term_issue', long_term_topic),
            'kind': 'long_term_issue',
            'issue': long_term_topic,
            'priority': 'long_term',
            'isPrimary': False,
            'nextAction': f"{long_term_topic} 건은 장기 후속으로 분리해 다음 확인일만 잡으세요.",
            'nextActionDate': (today + timedelta(days=30)).isoformat(),
        })
    return issue_followups


def _ai_workspace_specific_issue_feedback(action, feedback_text):
    issue_followups = _ai_workspace_issue_followups_from_feedback(feedback_text)
    if not issue_followups:
        return {}

    primary = next((item for item in issue_followups if item.get('isPrimary')), issue_followups[0])
    issue = primary.get('issue') or '고객 불만'
    long_term_followups = [item for item in issue_followups if item.get('kind') == 'long_term_issue']
    next_action = primary.get('nextAction') or ''
    if long_term_followups:
        next_action = f"{next_action} {' '.join(item.get('nextAction') or '' for item in long_term_followups).strip()}".strip()

    if long_term_followups:
        long_term_topic = long_term_followups[0].get('issue') or '장기 이슈'
        summary = f"{long_term_topic}는 장기 추적 대상으로 분리하고, 현재 먼저 처리할 일은 {issue} 불만의 원인 확인과 처리 일정 안내입니다."
    else:
        summary = f"현재 먼저 처리할 일은 {issue} 불만의 원인 확인과 처리 일정 안내입니다."

    return {
        'summary': summary,
        'nextAction': next_action,
        'reason': '일반적인 해결 지시가 아니라 현장 확인 항목, 가능한 해결안, 고객 회신 기준을 포함해 실행문을 구체화했습니다.',
        'issueFollowups': issue_followups,
    }


def _ai_workspace_normalize_feedback_result(data, fallback, action=None, feedback_text=''):
    decision = str(data.get('decision') or fallback.get('decision') or 'next_action').strip().lower()
    if decision not in {'keep', 'hide', 'next_action'}:
        decision = fallback.get('decision') or 'next_action'

    intent = str(data.get('intent') or fallback.get('intent') or '').strip()
    if intent not in {
        'resolved_no_purchase',
        'follow_up_needed',
        'positive_buying_signal',
        'email_waiting',
        'needs_human_review',
    }:
        if decision == 'hide':
            intent = 'resolved_no_purchase'
        elif decision == 'next_action':
            intent = fallback.get('intent') or 'follow_up_needed'
        else:
            intent = 'needs_human_review'

    status = str(data.get('recommendedStatus') or data.get('status') or '').strip()
    if status not in {'answered', 'next_action', 'resolved', 'dismissed'}:
        if decision == 'hide':
            status = 'resolved'
        elif decision == 'next_action':
            status = 'next_action'
        else:
            status = 'answered'

    next_action_date = data.get('nextActionDate') or data.get('next_action_date') or None
    if next_action_date and not _parse_iso_date_or_none(next_action_date):
        next_action_date = None

    should_hide = bool(data.get('shouldHide')) or decision == 'hide' or status in {'resolved', 'dismissed'}
    if should_hide and status == 'answered':
        status = 'resolved'

    summary = data.get('summary') or fallback.get('summary')
    next_action = data.get('nextAction') or fallback.get('nextAction')
    reason = data.get('reason') or fallback.get('reason')
    specific = _ai_workspace_specific_issue_feedback(action or {}, feedback_text)
    issue_followups = []
    if specific and status == 'next_action' and not should_hide:
        summary = specific.get('summary') or summary
        next_action = specific.get('nextAction') or next_action
        reason = specific.get('reason') or reason
        issue_followups = specific.get('issueFollowups') or []

    return {
        'decision': decision,
        'recommendedStatus': status,
        'intent': intent,
        'shouldHide': should_hide,
        'summary': _ai_workspace_prompt_excerpt(summary, 260),
        'nextAction': _ai_workspace_prompt_excerpt(next_action, 260),
        'nextActionDate': next_action_date,
        'reason': _ai_workspace_prompt_excerpt(reason, 260),
        'suggestedDraftType': data.get('suggestedDraftType') or fallback.get('suggestedDraftType') or '',
        'issueFollowups': issue_followups,
    }


def _ai_workspace_feedback_status_from_result(result):
    status = result.get('recommendedStatus') or 'answered'
    if status not in {'answered', 'next_action', 'resolved', 'dismissed'}:
        return 'answered'
    return status


def _ai_workspace_empty_crm_sync(intent='needs_human_review'):
    intent = intent or 'needs_human_review'
    return {
        'intent': intent,
        'intentLabel': _ai_workspace_feedback_intent_label(intent),
        'applied': False,
        'message': 'CRM 상태 변경 없이 상황만 기록했습니다.',
        'changes': [],
        'taskHistoryId': None,
        'taskHistoryHref': '',
        'issueTaskHistories': [],
    }


def _ai_workspace_sync_change(label, object_type='', object_id=None, href='', detail=''):
    payload = {
        'label': label,
        'objectType': object_type,
        'objectId': object_id,
        'href': href,
        'detail': _ai_workspace_prompt_excerpt(detail, 220),
    }
    return payload


def _ai_workspace_action_numeric_id(action_id, prefix):
    value = str(action_id or '')
    if not value.startswith(prefix):
        return None
    try:
        return int(value.split(':', 1)[1])
    except (TypeError, ValueError, IndexError):
        return None


def _ai_workspace_owned_followup(user, action):
    followup_id = action.get('followupId')
    if not followup_id:
        return None
    return FollowUp.objects.filter(id=followup_id, user=user).select_related('company', 'department').first()


def _ai_workspace_open_history_qs(user, followup):
    return History.objects.filter(
        user=user,
        followup=followup,
        parent_history__isnull=True,
        reviewed_at__isnull=True,
        next_action__isnull=False,
    ).exclude(next_action='')


def _ai_workspace_target_history(user, action):
    history_id = _ai_workspace_action_numeric_id(action.get('id'), 'followup:')
    if not history_id:
        return None
    return History.objects.filter(
        id=history_id,
        user=user,
        followup_id=action.get('followupId'),
        parent_history__isnull=True,
    ).first()


def _ai_workspace_previous_sync_task(user, action, followup):
    previous = AIWorkspaceActionFeedback.objects.filter(
        user=user,
        action_id=action.get('id') or '',
    ).first()
    if not previous:
        return None
    task_id = ((previous.ai_result or {}).get('crmSync') or {}).get('taskHistoryId')
    if not task_id:
        return None
    return History.objects.filter(
        id=task_id,
        user=user,
        followup=followup,
        parent_history__isnull=True,
    ).first()


def _ai_workspace_previous_issue_sync_tasks(user, action, followup):
    previous = AIWorkspaceActionFeedback.objects.filter(
        user=user,
        action_id=action.get('id') or '',
    ).first()
    if not previous:
        return {}

    issue_rows = ((previous.ai_result or {}).get('crmSync') or {}).get('issueTaskHistories') or []
    id_by_key = {}
    for item in issue_rows:
        if not isinstance(item, dict):
            continue
        key = item.get('key') or ''
        history_id = item.get('historyId')
        if key and history_id:
            id_by_key[key] = history_id
    if not id_by_key:
        return {}

    histories = History.objects.filter(
        id__in=id_by_key.values(),
        user=user,
        followup=followup,
        parent_history__isnull=True,
    )
    history_by_id = {history.id: history for history in histories}
    return {
        key: history_by_id[history_id]
        for key, history_id in id_by_key.items()
        if history_id in history_by_id
    }


def _ai_workspace_mark_histories_reviewed(user, histories, reason):
    now = timezone.now()
    changes = []
    for history in list(histories[:20]):
        if history.reviewed_at:
            continue
        history.reviewed_at = now
        history.reviewer = user
        history.save(update_fields=['reviewed_at', 'reviewer'])
        changes.append(_ai_workspace_sync_change(
            '열린 후속조치 종료',
            'history',
            history.id,
            reverse('reporting:history_detail', args=[history.id]),
            reason or history.next_action or '',
        ))
    return changes


def _ai_workspace_default_next_action(intent, action):
    title = action.get('title') or 'AI 추천 액션'
    if intent == 'email_waiting':
        return f"{title} 관련 메일 회신 여부를 확인하고 필요하면 리마인드 메일을 보내세요."
    if intent == 'positive_buying_signal':
        return f"{title} 건의 구매 절차, 결재 일정, 필요 서류를 확인하세요."
    return action.get('recommendedAction') or f"{title} 후속조치를 진행하세요."


def _ai_workspace_default_next_action_date(intent):
    from datetime import timedelta

    today = timezone.localdate()
    if intent == 'email_waiting':
        return today + timedelta(days=2)
    if intent == 'positive_buying_signal':
        return today + timedelta(days=3)
    return today + timedelta(days=7)


def _ai_workspace_sync_history_content(action, feedback_text, result):
    return "\n".join(_ai_prompt_context(
        f"[AI 상황 동기화 후속조치] {action.get('title') or action.get('kindLabel') or action.get('id')}",
        f"사용자 입력: {feedback_text}",
        f"AI 요약: {result.get('summary') or ''}",
        f"동기화 의도: {_ai_workspace_feedback_intent_label(result.get('intent'))}",
        f"다음 액션: {result.get('nextAction') or ''}",
        f"판단 근거: {result.get('reason') or ''}",
    ))


def _ai_workspace_create_sync_history(user, user_profile, followup, action, feedback_text, result, next_action, next_action_date):
    return History.objects.create(
        user=user,
        company=user_profile.company if user_profile else None,
        followup=followup,
        action_type='memo',
        content=_ai_workspace_sync_history_content(action, feedback_text, result),
        next_action=next_action,
        next_action_date=next_action_date,
        created_by=user,
    )


def _ai_workspace_issue_sync_history_content(action, feedback_text, result, issue_followup):
    return "\n".join(_ai_prompt_context(
        f"[AI 이슈별 후속조치] {issue_followup.get('issue') or action.get('title') or action.get('id')}",
        f"원본 액션: {action.get('title') or action.get('kindLabel') or action.get('id')}",
        f"사용자 입력: {feedback_text}",
        f"AI 요약: {result.get('summary') or ''}",
        f"이슈 구분: {issue_followup.get('kind') or ''}",
        f"다음 액션: {issue_followup.get('nextAction') or ''}",
        f"판단 근거: {result.get('reason') or ''}",
    ))


def _ai_workspace_create_issue_sync_history(user, user_profile, followup, action, feedback_text, result, issue_followup, next_action, next_action_date):
    return History.objects.create(
        user=user,
        company=user_profile.company if user_profile else None,
        followup=followup,
        action_type='memo',
        content=_ai_workspace_issue_sync_history_content(action, feedback_text, result, issue_followup),
        next_action=next_action,
        next_action_date=next_action_date,
        created_by=user,
    )


def _ai_workspace_primary_issue_followup(result):
    issue_followups = result.get('issueFollowups') if isinstance(result.get('issueFollowups'), list) else []
    for item in issue_followups:
        if isinstance(item, dict) and item.get('isPrimary') and item.get('nextAction'):
            return item
    return None


def _ai_workspace_sync_secondary_issue_followups(user, user_profile, followup, action, feedback_text, result, main_history=None):
    issue_followups = result.get('issueFollowups') if isinstance(result.get('issueFollowups'), list) else []
    secondary_followups = [
        item for item in issue_followups
        if isinstance(item, dict) and not item.get('isPrimary') and item.get('nextAction')
    ]
    if not secondary_followups:
        return [], []

    changes = []
    synced = []
    previous_tasks = _ai_workspace_previous_issue_sync_tasks(user, action, followup)
    today = timezone.localdate()
    for item in secondary_followups[:4]:
        key = item.get('key') or _ai_workspace_issue_followup_key(item.get('kind') or 'issue', item.get('issue') or '')
        next_action = item.get('nextAction') or ''
        next_action_date = _parse_iso_date_or_none(item.get('nextActionDate'))
        if not next_action_date:
            next_action_date = today + timedelta(days=30 if item.get('priority') == 'long_term' else 7)

        task_history = previous_tasks.get(key)
        if main_history and task_history and task_history.id == main_history.id:
            task_history = None
        action_label = '이슈별 장기 후속조치' if item.get('priority') == 'long_term' else '이슈별 후속조치'
        if task_history:
            task_history.next_action = next_action
            task_history.next_action_date = next_action_date
            task_history.reviewed_at = None
            task_history.reviewer = None
            task_history.content = _ai_workspace_issue_sync_history_content(action, feedback_text, result, item)
            task_history.save(update_fields=['content', 'next_action', 'next_action_date', 'reviewed_at', 'reviewer'])
            change_label = f'{action_label} 갱신'
        else:
            task_history = _ai_workspace_create_issue_sync_history(
                user,
                user_profile,
                followup,
                action,
                feedback_text,
                result,
                item,
                next_action,
                next_action_date,
            )
            change_label = f'{action_label} 생성'

        href = reverse('reporting:history_detail', args=[task_history.id])
        changes.append(_ai_workspace_sync_change(
            change_label,
            'history',
            task_history.id,
            href,
            next_action,
        ))
        synced.append({
            'key': key,
            'kind': item.get('kind') or '',
            'issue': item.get('issue') or '',
            'priority': item.get('priority') or '',
            'historyId': task_history.id,
            'historyHref': href,
            'nextAction': next_action,
            'nextActionDate': next_action_date.isoformat() if next_action_date else None,
        })
    return changes, synced


def _ai_workspace_update_followup_for_sync(followup, intent, status):
    changes = []
    update_fields = []

    def set_field(field, value, label, detail=None):
        if getattr(followup, field) != value:
            setattr(followup, field, value)
            update_fields.append(field)
            changes.append(_ai_workspace_sync_change(
                label,
                'followup',
                followup.id,
                reverse('reporting:followup_detail', args=[followup.id]),
                detail if detail is not None else str(value),
            ))

    if intent == 'resolved_no_purchase':
        set_field('status', 'paused', '고객 상태 보류')
        if not followup.pipeline_manually_set:
            set_field('pipeline_stage', 'lost', '파이프라인 실주 전환')
    elif intent == 'positive_buying_signal':
        set_field('status', 'active', '고객 상태 진행중 유지')
        if status == 'next_action' and not followup.pipeline_manually_set and followup.pipeline_stage in {'potential', 'contact', 'quote'}:
            set_field('pipeline_stage', 'negotiation', '파이프라인 협상 전환')
    elif intent in {'follow_up_needed', 'email_waiting'}:
        set_field('status', 'active', '고객 상태 진행중 유지')

    if update_fields:
        update_fields.append('updated_at')
        followup.save(update_fields=sorted(set(update_fields)))
    return changes


def _ai_workspace_sync_commercial_state(user, action, intent, status):
    changes = []
    action_id = action.get('id') or ''

    quote_id = _ai_workspace_action_numeric_id(action_id, 'quote:')
    if quote_id:
        quote = Quote.objects.filter(
            id=quote_id,
            user=user,
        ).select_related('schedule').first()
        if quote and intent == 'resolved_no_purchase' and quote.stage not in {'rejected', 'expired', 'converted'}:
            quote.stage = 'rejected'
            quote.save(update_fields=['stage', 'updated_at'])
            changes.append(_ai_workspace_sync_change(
                '견적 상태 거절 처리',
                'quote',
                quote.id,
                reverse('reporting:schedule_detail', args=[quote.schedule_id]) if quote.schedule_id else '',
                quote.quote_number,
            ))
        elif quote and intent == 'positive_buying_signal' and status == 'resolved' and quote.stage not in {'approved', 'converted'}:
            quote.stage = 'approved'
            quote.save(update_fields=['stage', 'updated_at'])
            changes.append(_ai_workspace_sync_change(
                '견적 상태 승인 처리',
                'quote',
                quote.id,
                reverse('reporting:schedule_detail', args=[quote.schedule_id]) if quote.schedule_id else '',
                quote.quote_number,
            ))

        if quote and quote.schedule_id and intent == 'resolved_no_purchase' and quote.schedule.status == 'scheduled':
            quote.schedule.status = 'cancelled'
            quote.schedule.save(update_fields=['status', 'updated_at'])
            changes.append(_ai_workspace_sync_change(
                '견적 일정 취소 처리',
                'schedule',
                quote.schedule_id,
                reverse('reporting:schedule_detail', args=[quote.schedule_id]),
                quote.schedule.visit_date.isoformat() if quote.schedule.visit_date else '',
            ))
        elif quote and quote.schedule_id and intent == 'positive_buying_signal' and status == 'resolved' and quote.schedule.status == 'scheduled':
            quote.schedule.status = 'completed'
            quote.schedule.save(update_fields=['status', 'updated_at'])
            changes.append(_ai_workspace_sync_change(
                '견적 일정 완료 처리',
                'schedule',
                quote.schedule_id,
                reverse('reporting:schedule_detail', args=[quote.schedule_id]),
                quote.schedule.visit_date.isoformat() if quote.schedule.visit_date else '',
            ))
        return changes

    schedule_prefix = None
    if action_id.startswith('quote_schedule:'):
        schedule_prefix = 'quote_schedule:'
    elif action_id.startswith('delivery:'):
        schedule_prefix = 'delivery:'
    if not schedule_prefix:
        return changes

    schedule_id = _ai_workspace_action_numeric_id(action_id, schedule_prefix)
    schedule = Schedule.objects.filter(id=schedule_id, user=user).first()
    if not schedule:
        return changes
    if intent == 'resolved_no_purchase' and schedule.activity_type == 'quote' and schedule.status == 'scheduled':
        schedule.status = 'cancelled'
        schedule.save(update_fields=['status', 'updated_at'])
        changes.append(_ai_workspace_sync_change(
            '견적 일정 취소 처리',
            'schedule',
            schedule.id,
            reverse('reporting:schedule_detail', args=[schedule.id]),
            schedule.visit_date.isoformat() if schedule.visit_date else '',
        ))
    elif intent == 'positive_buying_signal' and status == 'resolved' and schedule.status == 'scheduled':
        schedule.status = 'completed'
        schedule.save(update_fields=['status', 'updated_at'])
        changes.append(_ai_workspace_sync_change(
            '일정 완료 처리',
            'schedule',
            schedule.id,
            reverse('reporting:schedule_detail', args=[schedule.id]),
            schedule.visit_date.isoformat() if schedule.visit_date else '',
        ))
    return changes


def _ai_workspace_apply_crm_state_sync(user, user_profile, action, feedback_text, result):
    intent = result.get('intent') or 'needs_human_review'
    status = _ai_workspace_feedback_status_from_result(result)
    sync = _ai_workspace_empty_crm_sync(intent)
    followup = _ai_workspace_owned_followup(user, action)
    if not followup:
        sync['message'] = '연결된 고객을 찾을 수 없어 CRM 상태 변경 없이 답변만 기록했습니다.'
        return sync

    if intent == 'needs_human_review':
        sync['message'] = '검토 필요로 분류되어 CRM 상태는 자동 변경하지 않았습니다.'
        return sync

    changes = []
    target_history = _ai_workspace_target_history(user, action)

    if intent == 'resolved_no_purchase':
        open_histories = _ai_workspace_open_history_qs(user, followup)
        changes.extend(_ai_workspace_mark_histories_reviewed(
            user,
            open_histories,
            result.get('summary') or 'AI 상황 입력으로 종료 처리',
        ))
        changes.extend(_ai_workspace_sync_commercial_state(user, action, intent, status))
        changes.extend(_ai_workspace_update_followup_for_sync(followup, intent, status))
        sync['message'] = '후속조치 종료/보류가 CRM 상태에 반영됐습니다.'
    elif intent in {'follow_up_needed', 'positive_buying_signal', 'email_waiting'} and status == 'next_action':
        primary_issue = _ai_workspace_primary_issue_followup(result)
        next_action = (
            (primary_issue or {}).get('nextAction')
            or result.get('nextAction')
            or _ai_workspace_default_next_action(intent, action)
        )
        next_action_date = (
            _parse_iso_date_or_none((primary_issue or {}).get('nextActionDate'))
            or _parse_iso_date_or_none(result.get('nextActionDate'))
            or _ai_workspace_default_next_action_date(intent)
        )
        task_history = target_history or _ai_workspace_previous_sync_task(user, action, followup)
        if task_history:
            task_history.next_action = next_action
            task_history.next_action_date = next_action_date
            task_history.reviewed_at = None
            task_history.reviewer = None
            task_history.save(update_fields=['next_action', 'next_action_date', 'reviewed_at', 'reviewer'])
            changes.append(_ai_workspace_sync_change(
                '기존 후속조치 갱신',
                'history',
                task_history.id,
                reverse('reporting:history_detail', args=[task_history.id]),
                next_action,
            ))
        else:
            task_history = _ai_workspace_create_sync_history(
                user,
                user_profile,
                followup,
                action,
                feedback_text,
                result,
                next_action,
                next_action_date,
            )
            changes.append(_ai_workspace_sync_change(
                '새 후속조치 생성',
                'history',
                task_history.id,
                reverse('reporting:history_detail', args=[task_history.id]),
                next_action,
            ))
        issue_changes, issue_task_histories = _ai_workspace_sync_secondary_issue_followups(
            user,
            user_profile,
            followup,
            action,
            feedback_text,
            result,
            task_history,
        )
        changes.extend(issue_changes)
        changes.extend(_ai_workspace_update_followup_for_sync(followup, intent, status))
        sync['taskHistoryId'] = task_history.id
        sync['taskHistoryHref'] = reverse('reporting:history_detail', args=[task_history.id])
        sync['issueTaskHistories'] = issue_task_histories
        if intent == 'email_waiting':
            sync['message'] = '메일 답장 대기 후속조치가 CRM에 반영됐습니다.'
        elif intent == 'positive_buying_signal':
            sync['message'] = '긍정 신호에 맞춰 우선 후속조치가 CRM에 반영됐습니다.'
        elif issue_task_histories:
            sync['message'] = '긴급 이슈와 장기 이슈 후속조치가 CRM에 분리 반영됐습니다.'
        else:
            sync['message'] = '다음 후속조치가 CRM에 반영됐습니다.'
    elif intent == 'positive_buying_signal' and status == 'resolved':
        open_histories = _ai_workspace_open_history_qs(user, followup)
        changes.extend(_ai_workspace_mark_histories_reviewed(
            user,
            open_histories,
            result.get('summary') or '구매/완료 신호로 기존 후속조치 종료',
        ))
        changes.extend(_ai_workspace_sync_commercial_state(user, action, intent, status))
        changes.extend(_ai_workspace_update_followup_for_sync(followup, intent, status))
        sync['message'] = '완료/긍정 상태가 CRM에 반영됐습니다.'
    else:
        sync['message'] = '답변은 기록했지만 자동 상태 변경 조건에 해당하지 않았습니다.'

    sync['changes'] = changes
    sync['applied'] = bool(changes)
    return sync


AI_WORKSPACE_DEPARTMENT_QUESTION_MAX_LENGTH = 600
AI_WORKSPACE_DEPARTMENT_QUESTION_OUTPUT_TOKENS = 2400
AI_WORKSPACE_QUESTION_FEEDBACK_COMMENT_MAX_LENGTH = 1000
AI_WORKSPACE_QUESTION_FEEDBACK_LIMIT = 6
AI_WORKSPACE_QUESTION_HISTORY_PAGE_SIZE = 5
AI_WORKSPACE_MEMORY_TITLE_MAX_LENGTH = 180
AI_WORKSPACE_MEMORY_CONTENT_MAX_LENGTH = 1600
AI_WORKSPACE_MEMORY_LIMIT = 12
AI_WORKSPACE_MEMORY_PAGE_SIZE = 8
AI_WORKSPACE_RECENT_CONVERSATION_LIMIT = 5
AI_WORKSPACE_BRIEFING_SYSTEM_PROMPT = """
너는 내부 영업 CRM의 브리핑 작성자다.

역할:
- 제공된 CRM 데이터만 읽고 현재 상태, 근거, 누락된 정보, 확인 필요 사항을 간결하게 브리핑한다.
- 창작, 전략 수립, 메일/문자/스크립트/프롬프트 작성, 설득 문안, 보고서 초안 작성은 하지 않는다.
- 사용자가 전략, 문안, 초안, 프롬프트를 요청해도 산출물을 만들어 주지 말고, CRM에 기록된 사실과 확인해야 할 데이터만 브리핑한다.

출력 원칙:
- 한국어로 답한다.
- 데이터에 없는 고객 의도, 구매 확정, 다음 행동을 만들어내지 않는다.
- 추정이 필요하면 추정이라고 표시하고 근거를 분리한다.
- 고객/거래처/담당자를 리스트업할 때는 각 행마다 왜 포함했는지 CRM 근거를 함께 쓴다.
- 최근 메일, 일정, 영업노트, 견적, 납품 근거가 있으면 파이프라인 단계보다 그 근거를 우선하고 링크를 evidence에 포함한다.
- 파이프라인/상태만 근거인 고객은 "최근 활동 근거 없음, 단계/상태만 확인됨"이라고 표시한다.
- 답변은 JSON 객체만 반환한다.
- 기본 형태는 {"answer": string, "bullets": string[], "evidence": [{"label": string, "value": string}], "confidence": "high|medium|low"} 이다.
- decision, perspective, actionItems 같은 전략/실행 카드 필드는 만들지 않는다.
""".strip()
AI_WORKSPACE_QUESTION_MODELS = {
    'gpt-5.4-nano': 'GPT-5.4 nano',
}
AI_WORKSPACE_DEFAULT_QUESTION_MODEL = 'gpt-5.4-nano'


def _ai_workspace_question_recent_feedbacks(user, followup_ids, limit=8):
    followup_ids = _ai_workspace_followup_ids(followup_ids)
    if not user or not followup_ids:
        return []

    feedbacks = list(AIWorkspaceActionFeedback.objects.filter(
        user=user,
        followup_id__in=followup_ids,
    ).select_related(
        'followup',
        'followup__company',
        'followup__department',
    ).order_by('-updated_at')[:limit])

    items = []
    for feedback in feedbacks:
        result = feedback.ai_result or {}
        followup = feedback.followup
        items.append({
            'updatedAt': _datetime_or_none(feedback.updated_at),
            'status': feedback.get_status_display(),
            'kind': _ai_workspace_action_kind_label(feedback.action_kind),
            'customer': followup.customer_name if followup else '',
            'company': followup.company.name if followup and followup.company else '',
            'department': followup.department.name if followup and followup.department else '',
            'feedback': _ai_workspace_question_text(feedback.feedback, 420),
            'summary': _ai_workspace_question_text(result.get('summary'), 360),
            'nextAction': _ai_workspace_question_text(result.get('nextAction'), 260),
            'intent': _ai_workspace_feedback_intent_label(result.get('intent')),
            'crmSyncMessage': _ai_workspace_question_text((result.get('crmSync') or {}).get('message'), 260),
        })
    return items


def _ai_workspace_question_text(value, limit=600):
    text = _ai_workspace_feedback_display_text(value)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rstrip() + '...'


def _ai_workspace_memory_type_label(memory_type):
    return {
        'fact': '검수 사실',
        'correction': '정정',
        'preference': '브리핑 선호',
    }.get(memory_type, memory_type or '')


def _ai_workspace_question_model_label(model):
    return AI_WORKSPACE_QUESTION_MODELS.get(model, model or '')


def _ai_workspace_memory_payload(memory):
    department = memory.department
    source_log = memory.source_question_log
    return {
        'id': memory.id,
        'scopeType': memory.scope_type,
        'memoryType': memory.memory_type,
        'memoryTypeLabel': _ai_workspace_memory_type_label(memory.memory_type),
        'title': _ai_workspace_question_text(memory.title, AI_WORKSPACE_MEMORY_TITLE_MAX_LENGTH),
        'content': _ai_workspace_question_text(memory.content, AI_WORKSPACE_MEMORY_CONTENT_MAX_LENGTH),
        'isActive': bool(memory.is_active),
        'department': {
            'id': department.id,
            'name': department.name,
            'company': department.company.name if department.company else '',
        } if department else None,
        'sourceQuestionLogId': source_log.id if source_log else None,
        'sourceQuestion': _ai_workspace_question_text(source_log.question, 360) if source_log else '',
        'createdAt': _datetime_or_none(memory.created_at),
        'updatedAt': _datetime_or_none(memory.updated_at),
    }


def _ai_workspace_verified_memories(user, department_id=None, scope_type='department', limit=AI_WORKSPACE_MEMORY_LIMIT):
    if not user:
        return []

    normalized_scope = 'all' if scope_type == 'all' else 'department'
    queryset = AIWorkspaceMemory.objects.filter(
        user=user,
        is_active=True,
    ).select_related(
        'department',
        'department__company',
        'source_question_log',
    )
    if normalized_scope == 'department':
        queryset = queryset.filter(
            Q(scope_type='all', department__isnull=True) |
            Q(scope_type='department', department_id=department_id)
        )
    else:
        queryset = queryset.filter(scope_type='all', department__isnull=True)

    return [
        _ai_workspace_memory_payload(memory)
        for memory in queryset.order_by('-updated_at')[:limit]
    ]


def _ai_workspace_product_text(value, limit=260):
    return _ai_workspace_question_text(value, limit)


def _ai_workspace_product_fact_lookup(context):
    lookup = {}
    for fact in context.get('productFacts') or []:
        if not isinstance(fact, dict):
            continue
        code = _ai_workspace_product_text(fact.get('code'), 80)
        if code:
            lookup[code] = {
                'code': code,
                'label': _ai_workspace_product_text(fact.get('label'), 320) or code,
                'description': _ai_workspace_product_text(fact.get('description'), 220),
                'specification': _ai_workspace_product_text(fact.get('specification'), 160),
                'unit': _ai_workspace_product_text(fact.get('unit'), 40),
            }
    return lookup


def _ai_workspace_product_type_aliases(fact):
    text = ' '.join(
        _ai_workspace_product_text(fact.get(key), 240)
        for key in ['label', 'description', 'specification']
    ).lower()
    aliases = set()
    if any(keyword in text for keyword in ['tip', 'tips', 'low retention', 'paradigm refill', 'paradigm refills']):
        aliases.update(['팁', 'tip', 'tips', '리필', 'refill', 'refills'])
    if any(keyword in text for keyword in ['tube', 'tubes']):
        aliases.update(['튜브', 'tube', 'tubes'])
    if any(keyword in text for keyword in ['plate', 'plates']):
        aliases.update(['플레이트', 'plate', 'plates'])
    if any(keyword in text for keyword in ['reagent', 'reagents']):
        aliases.update(['시약', 'reagent', 'reagents'])
    if any(keyword in text for keyword in ['buffer', 'buffers']):
        aliases.update(['버퍼', 'buffer', 'buffers'])
    if any(keyword in text for keyword in ['filter', 'filters']):
        aliases.update(['필터', 'filter', 'filters'])
    return aliases


def _ai_workspace_product_label_is_supported(candidate, fact):
    normalized = re.sub(r'\s+', '', str(candidate or '').lower())
    if not normalized:
        return True
    generic_labels = {'품목', '제품', '품번', '코드', 'item', 'product'}
    if normalized in generic_labels:
        return True
    source = re.sub(
        r'\s+',
        '',
        ' '.join(
            _ai_workspace_product_text(fact.get(key), 320)
            for key in ['label', 'description', 'specification', 'unit']
        ).lower(),
    )
    if normalized and normalized in source:
        return True
    return normalized in {re.sub(r'\s+', '', alias.lower()) for alias in _ai_workspace_product_type_aliases(fact)}


def _ai_workspace_guard_product_labels_in_text(text, product_facts):
    guarded = str(text or '')
    if not guarded or not product_facts:
        return guarded

    for code, fact in product_facts.items():
        replacement = fact.get('label') or f'{code} 품목'
        code_pattern = re.escape(code)
        label_before_code = re.compile(
            rf'(?P<label>[A-Za-z가-힣][A-Za-z가-힣0-9+/#._-]{{0,30}})\s*[\(（]\s*{code_pattern}\s*[\)）]'
        )

        def replace_label_before(match):
            candidate = match.group('label')
            if _ai_workspace_product_label_is_supported(candidate, fact):
                return match.group(0)
            return replacement

        guarded = label_before_code.sub(replace_label_before, guarded)
    return guarded


def _ai_workspace_apply_product_fact_guard(value, context):
    product_facts = _ai_workspace_product_fact_lookup(context or {})
    if not product_facts:
        return value
    if isinstance(value, str):
        return _ai_workspace_guard_product_labels_in_text(value, product_facts)
    if isinstance(value, list):
        return [_ai_workspace_apply_product_fact_guard(item, context) for item in value]
    if isinstance(value, dict):
        return {
            key: _ai_workspace_apply_product_fact_guard(item, context)
            for key, item in value.items()
        }
    return value


def _ai_workspace_question_schedule_href(schedule_id):
    return f'/schedules/{schedule_id}/' if schedule_id else ''


def _ai_workspace_question_history_href(history_id):
    return f'/notes/{history_id}/' if history_id else ''


def _ai_workspace_question_customer_href(followup_id):
    return f'/customers/{followup_id}/' if followup_id else ''


def _ai_workspace_question_record_href(record, *, schedule_id=None, history_id=None, followup_id=None):
    if isinstance(record, dict):
        href = _ai_workspace_question_text(
            record.get('href')
            or record.get('url')
            or record.get('link')
            or record.get('scheduleHref')
            or record.get('historyHref')
            or record.get('customerHref'),
            260,
        )
        if href:
            return href
        hrefs = record.get('hrefs')
        if isinstance(hrefs, dict):
            for key in ['schedule', 'note', 'customer', 'assets', 'mailboxThread', 'report', 'ai', 'aiHub']:
                href = _ai_workspace_question_text(hrefs.get(key), 260)
                if href:
                    return href
        for key in ['threadHref', 'emailHref', 'mailboxThreadHref']:
            href = _ai_workspace_question_text(record.get(key), 260)
            if href:
                return href
    if schedule_id:
        return _ai_workspace_question_schedule_href(schedule_id)
    if history_id:
        return _ai_workspace_question_history_href(history_id)
    if followup_id:
        return _ai_workspace_question_customer_href(followup_id)
    return ''


def _ai_workspace_question_evidence_link_label(record, fallback='CRM 열기'):
    if isinstance(record, dict):
        return _ai_workspace_question_text(
            record.get('linkLabel') or record.get('link_label') or record.get('hrefLabel') or record.get('urlLabel'),
            80,
        ) or fallback
    return fallback


def _ai_workspace_question_evidence_payload(items, limit=10, value_limit=700):
    evidence = []
    for item in _ai_json_list(items)[:limit]:
        href = ''
        link_label = ''
        if isinstance(item, dict):
            label = _ai_workspace_question_text(item.get('label') or item.get('title') or '근거', 90)
            value = _ai_workspace_question_text(
                item.get('value') or item.get('text') or item.get('detail') or item.get('summary'),
                value_limit,
            )
            href = _ai_workspace_question_record_href(item)
            link_label = _ai_workspace_question_evidence_link_label(item, '열기')
        else:
            label = '근거'
            value = _ai_workspace_question_text(item, value_limit)
        if label and value:
            payload = {'label': label, 'value': value}
            if href:
                payload['href'] = href
                payload['linkLabel'] = link_label or '열기'
            evidence.append(payload)
    return evidence


def _ai_workspace_email_happened_at(email):
    return email.received_at or email.sent_at or email.created_at


def _ai_workspace_email_followup(email):
    if email.followup_id:
        return email.followup
    if email.schedule_id and getattr(email.schedule, 'followup_id', None):
        return email.schedule.followup
    return None


def _email_thread_identifier(email):
    return email.gmail_thread_id or email.thread_id or email.gmail_message_id or email.message_id or str(email.id)


def _strip_html_style_blocks(value):
    import re

    text = str(value or '')
    text = re.sub(r'(?is)<\s*style\b[^>]*>.*?<\s*/\s*style\s*>', ' ', text)
    text = re.sub(r'(?is)<\s*script\b[^>]*>.*?<\s*/\s*script\s*>', ' ', text)
    return text


def _strip_css_text_artifacts(value):
    import re

    text = str(value or '')
    selector_pattern = r'(?:p|div|span|body|td|table|tr|a|li|ul|ol)'
    css_prop_pattern = r'(?:margin|padding|font|color|line-height|mso-|text-|background|border|white-space)'
    text = re.sub(
        rf'(?im)^\s*{selector_pattern}\s*\{{[^{{}}\n]*{css_prop_pattern}[^{{}}\n]*\}}\s*$',
        '',
        text,
    )
    text = re.sub(
        rf'(?i)\b{selector_pattern}\s*\{{[^{{}}]*(?:margin|padding|font|mso-)[^{{}}]*\}}\s*',
        '',
        text,
    )
    return text


def _looks_like_email_html(value):
    import html
    import re

    text = str(value or '')
    if not text.strip():
        return False
    candidates = [text]
    unescaped = html.unescape(text)
    if unescaped != text:
        candidates.append(unescaped)
    html_pattern = re.compile(
        r'(?is)<\s*(?:!doctype|html|head|body|style|script|meta|div|p|br|span|table|tbody|tr|td|blockquote)\b'
    )
    return any(html_pattern.search(candidate) for candidate in candidates)


def _strip_quoted_html_for_display(raw_html):
    """React 메일 상세 표시에서는 Gmail/Outlook 인용 체인을 숨긴다."""
    import re

    quote_patterns = [
        r'(?is)<div[^>]+class=["\'][^"\']*gmail_quote[^"\']*["\'][^>]*>.*$',
        r'(?is)<div[^>]+id=["\']mail-editor-reference-message-container["\'][^>]*>.*$',
        r'(?is)<div[^>]+class=["\'][^"\']*ms-outlook-mobile-reference-message[^"\']*["\'][^>]*>.*$',
        r'(?is)<blockquote\b[^>]*>.*$',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, raw_html)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return raw_html
    return raw_html[:min(cut_positions)]


def _strip_quoted_text_for_display(text):
    import re

    quote_patterns = [
        r'\n\s*\d{4}년\s+\d{1,2}월\s+\d{1,2}일.{0,500}?(님이 작성:|wrote:)',
        r'\n\s*On .{1,500}? wrote:',
        r'\n\s*-{2,}\s*Original Message\s*-{2,}',
        r'\n\s*-----Original Message-----',
        r'\n\s*보낸 사람\s*:',
        r'\n\s*From\s*:',
        r'\n\s*Sent\s*:',
        r'\n\s*받는 사람\s*:',
        r'\n\s*To\s*:',
        r'\n\s*Get Outlook for',
        r'\n\s*받기 Mac용 Outlook',
    ]
    cut_positions = []
    for pattern in quote_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.start() >= 20:
            cut_positions.append(match.start())

    if not cut_positions:
        return text
    return text[:min(cut_positions)].rstrip()


def _email_html_to_display_text(value, limit=12000, strip_quotes=True):
    import html
    import re
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = html.unescape(str(value or ''))
    raw = _strip_html_style_blocks(raw)
    if strip_quotes:
        raw = _strip_quoted_html_for_display(raw)
    text = re.sub(r'(?i)<\s*br\s*/?\s*>', '\n', raw)
    text = re.sub(r'(?i)<\s*/\s*(p|div|li|tr|h[1-6]|blockquote|section|article|table|head|body|html)\s*>', '\n', text)
    text = re.sub(r'(?i)<\s*li(?:\s[^>]*)?>', '- ', text)
    text = strip_tags(text)
    text = html.unescape(text).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [' '.join(line.split()) for line in text.split('\n')]
    normalized = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append('')
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False
    return Truncator(_strip_quoted_text_for_display('\n'.join(normalized).strip())).chars(limit)


def _email_text_preview(email, limit=160):
    from django.utils.html import strip_tags
    from django.utils.text import Truncator

    raw = email.body_html or email.body or ''
    if email.body_html or _looks_like_email_html(raw):
        text = _email_html_to_display_text(raw, limit=limit)
    else:
        raw = _strip_html_style_blocks(raw)
        text = strip_tags(raw).replace('\xa0', ' ')
        text = _strip_css_text_artifacts(text)
    text = ' '.join(text.split())
    return Truncator(text).chars(limit)


def _email_body_text(email, limit=12000):
    import html
    from django.utils.text import Truncator

    raw = email.body_html or email.body or ''
    if email.body_html or _looks_like_email_html(raw):
        return _email_html_to_display_text(raw, limit=limit)

    text = raw
    text = html.unescape(text).replace('\xa0', ' ')
    text = _strip_css_text_artifacts(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [' '.join(line.split()) for line in text.split('\n')]
    normalized = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append('')
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False

    return Truncator(_strip_quoted_text_for_display('\n'.join(normalized).strip())).chars(limit)


def _ai_workspace_email_context_payload(email):
    body_text = _email_body_text(email, limit=1600)
    preview = _email_text_preview(email, limit=220)
    thread_id = _email_thread_identifier(email)

    followup = _ai_workspace_email_followup(email)
    department = None
    if followup and followup.department_id:
        department = followup.department
    elif email.schedule_id and getattr(email.schedule, 'department_id', None):
        department = email.schedule.department
    company = followup.company if followup and followup.company else (department.company if department and department.company else None)
    happened_at = _ai_workspace_email_happened_at(email)
    attachments = []
    for attachment in (email.attachments_info or [])[:4]:
        if isinstance(attachment, dict) and attachment.get('filename'):
            attachments.append(_ai_workspace_question_text(attachment.get('filename'), 120))

    direction_label = '보낸 메일' if email.email_type == 'sent' else '받은 메일'
    contact = (
        email.recipient_name or email.to_name or email.recipient_email or email.to_email
        if email.email_type == 'sent'
        else email.from_name or email.sender_email or email.from_email
    )
    return {
        'id': email.id,
        'type': email.email_type,
        'directionLabel': direction_label,
        'date': happened_at.isoformat() if happened_at else None,
        'subject': _ai_workspace_question_text(email.subject, 220),
        'contact': _ai_workspace_question_text(contact, 160),
        'sender': _ai_workspace_question_text(email.sender_email or email.from_email, 160),
        'recipient': _ai_workspace_question_text(email.recipient_email or email.to_email, 160),
        'cc': _ai_workspace_question_text(email.cc_emails, 220),
        'preview': _ai_workspace_question_text(preview, 260),
        'body': _ai_workspace_question_text(body_text, 1600),
        'followupId': followup.id if followup else None,
        'departmentId': department.id if department else None,
        'customer': _ai_workspace_question_text(followup.customer_name if followup else '담당자 미등록', 120),
        'company': _ai_workspace_question_text(company.name if company else '', 120),
        'department': _ai_workspace_question_text(department.name if department else '', 120),
        'threadHref': f'/mailbox/thread/{thread_id}/' if thread_id else '',
        'href': f'/mailbox/thread/{thread_id}/' if thread_id else '',
        'linkLabel': '메일 보기',
        'attachments': [item for item in attachments if item],
    }


def _ai_workspace_recent_email_context(user, followup_ids=None, department_id=None, limit=10):
    followup_ids = [item for item in (followup_ids or []) if item]
    owned_q = Q(user=user) | Q(sender=user) | Q(followup__user=user) | Q(schedule__user=user)
    queryset = EmailLog.objects.filter(owned_q, is_trashed=False)

    if followup_ids:
        queryset = queryset.filter(
            Q(followup_id__in=followup_ids) |
            Q(schedule__followup_id__in=followup_ids)
        )
    elif department_id:
        queryset = queryset.filter(
            Q(followup__department_id=department_id) |
            Q(schedule__followup__department_id=department_id) |
            Q(schedule__department_id=department_id)
        )

    emails = list(
        queryset.select_related(
            'followup',
            'followup__company',
            'followup__department',
            'schedule',
            'schedule__department',
            'schedule__department__company',
            'schedule__followup',
            'schedule__followup__company',
            'schedule__followup__department',
        ).distinct().order_by('-received_at', '-sent_at', '-created_at')[:max(limit * 3, limit)]
    )
    emails.sort(key=lambda email: _ai_workspace_email_happened_at(email), reverse=True)
    return [
        _ai_workspace_email_context_payload(email)
        for email in emails[:limit]
    ]


def _ai_workspace_json_from_text(text):
    text = str(text or '').strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _customer_ai_primary_context(followup):
    return {
        'id': followup.id,
        'name': followup.customer_name or followup.manager or '고객명 미정',
        'manager': followup.manager or '',
        'company': followup.company.name if followup.company else '',
        'department': followup.department.name if followup.department else '',
        'status': followup.get_status_display(),
        'grade': followup.customer_grade or '',
        'score': followup.ai_score or 0,
        'pipelineStage': followup.get_pipeline_stage_display(),
        'email': followup.email or '',
        'phone': followup.phone_number or '',
        'notes': _ai_workspace_question_text(followup.notes, 700),
        'href': _ai_workspace_question_customer_href(followup.id),
        'linkLabel': '고객 보기',
    }


SCHEDULE_AI_COACH_OUTPUT_TOKENS = 1400


def _schedule_ai_report_action_type(activity_type):
    if activity_type in {'customer_meeting', 'quote', 'delivery_schedule', 'service'}:
        return activity_type
    return {
        'quote': 'quote',
        'delivery': 'delivery_schedule',
        'service': 'service',
        'customer_meeting': 'customer_meeting',
    }.get(activity_type, 'customer_meeting')


def _schedule_ai_coach_context(schedule, actor):
    followup = schedule.followup
    department = schedule.department or (followup.department if followup and followup.department_id else None)
    email_thread_count = EmailLog.objects.filter(
        schedule=schedule,
        gmail_thread_id__isnull=False,
    ).exclude(gmail_thread_id='').values('gmail_thread_id').distinct().count()
    delivery_text, delivery_total = _schedules_delivery_items_summary(schedule)
    documents = _schedules_document_actions(schedule, actor)
    commercial_checks = _schedules_commercial_checks(
        schedule,
        actor,
        documents,
        email_thread_count,
    )

    related_notes = []
    related_note_filter = Q(schedule=schedule)
    if followup:
        related_note_filter |= Q(followup=followup)
    elif department:
        related_note_filter |= Q(department=department)
    related_note_qs = History.objects.filter(
        related_note_filter,
        user=schedule.user,
        parent_history__isnull=True,
    ).exclude(action_type='memo').select_related('followup', 'department').distinct().order_by('-created_at')[:10]
    for history in related_note_qs:
        activity_date = history.meeting_date or history.delivery_date
        date_label = activity_date.isoformat() if activity_date else timezone.localtime(history.created_at).date().isoformat()
        related_notes.append({
            'id': history.id,
            'date': date_label,
            'type': history.get_action_type_display(),
            'content': _ai_workspace_question_text(_history_activity_content(history), 760),
            'nextAction': _ai_workspace_question_text(history.next_action or history.meeting_next_action, 320),
            'nextActionDate': _date_or_none(history.next_action_date),
            'href': _ai_workspace_question_history_href(history.id),
            'linkLabel': '영업노트',
        })

    return {
        'scope': {
            'type': 'schedule',
            'label': ' · '.join(_ai_prompt_context(
                followup.company.name if followup and followup.company else '',
                department.name if department else '',
                followup.customer_name if followup else '담당자 미등록',
                schedule.get_activity_type_display(),
            )),
            'scheduleId': schedule.id,
            'followupId': followup.id if followup else None,
            'departmentId': department.id if department else None,
            'href': _ai_workspace_question_schedule_href(schedule.id),
            'linkLabel': '일정 보기',
        },
        'schedule': {
            'id': schedule.id,
            'date': _date_or_none(schedule.visit_date),
            'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '',
            'activityType': schedule.activity_type,
            'activityLabel': schedule.get_activity_type_display(),
            'status': schedule.status,
            'statusLabel': schedule.get_status_display(),
            'location': schedule.location or '',
            'notes': _ai_workspace_question_text(schedule.notes, 900),
            'expectedRevenue': _money_int(schedule.expected_revenue),
            'probability': schedule.probability if schedule.probability is not None else None,
            'expectedCloseDate': _date_or_none(schedule.expected_close_date),
            'purchaseConfirmed': bool(schedule.purchase_confirmed),
            'vatMode': schedule.vat_mode,
            'usePrepayment': bool(schedule.use_prepayment),
            'prepaymentAmount': _money_int(schedule.prepayment_amount),
            'href': _ai_workspace_question_schedule_href(schedule.id),
            'linkLabel': f'{schedule.get_activity_type_display()} 일정',
        },
        'customer': _customer_ai_primary_context(followup) if followup else {},
        'deliverySummary': {
            'itemsText': _ai_workspace_question_text(delivery_text, 900),
            'totalAmount': delivery_total,
        },
        'deliveryItems': [
            _schedules_delivery_item_payload(item)
            for item in schedule.delivery_items_set.all().order_by('id')[:12]
        ],
        'commercialChecks': {
            'status': commercial_checks.get('status'),
            'statusLabel': commercial_checks.get('statusLabel'),
            'summary': commercial_checks.get('summary'),
            'warnings': commercial_checks.get('warnings') or [],
        },
        'recentNotes': related_notes,
        'recentEmails': _ai_workspace_recent_email_context(
            schedule.user,
            followup_ids=[followup.id] if followup else [],
            department_id=department.id if department else None,
            limit=8,
        ),
        'recentFeedbacks': _ai_workspace_question_recent_feedbacks(schedule.user, [followup.id] if followup else [], limit=6),
        'verifiedMemories': _ai_workspace_verified_memories(
            actor,
            department_id=department.id if department else None,
            scope_type='department' if department else 'all',
        ),
    }


def _schedule_ai_evidence_from_context(context):
    schedule = context.get('schedule') or {}
    customer = context.get('customer') or {}
    delivery_summary = context.get('deliverySummary') or {}
    evidence = [
        {
            'label': '일정',
            'value': ' · '.join(_ai_prompt_context(
                schedule.get('date'),
                schedule.get('time'),
                schedule.get('activityLabel'),
                schedule.get('statusLabel'),
            )),
            'href': schedule.get('href') or _ai_workspace_question_schedule_href(schedule.get('id')),
            'linkLabel': schedule.get('linkLabel') or '일정 보기',
        },
        {
            'label': '고객',
            'value': ' · '.join(_ai_prompt_context(
                customer.get('company'),
                customer.get('department'),
                customer.get('name'),
                customer.get('pipelineStage'),
            )),
            'href': customer.get('href') or _ai_workspace_question_customer_href(customer.get('id')),
            'linkLabel': customer.get('linkLabel') or '고객 보기',
        },
    ]
    if delivery_summary.get('itemsText'):
        evidence.append({
            'label': '품목',
            'value': delivery_summary.get('itemsText'),
        })
    return _ai_workspace_question_evidence_payload(evidence, limit=5, value_limit=700)


def _schedule_ai_coach_fallback(context):
    schedule = context.get('schedule') or {}
    customer = context.get('customer') or {}
    activity_type = schedule.get('activityType') or ''
    activity_label = schedule.get('activityLabel') or '일정'
    customer_label = customer.get('name') or '고객'
    amount = _money_int(schedule.get('expectedRevenue') or (context.get('deliverySummary') or {}).get('totalAmount') or 0)
    date_label = ' '.join(_ai_prompt_context(schedule.get('date'), schedule.get('time'))) or '일정 시간'
    delivery_items = context.get('deliveryItems') or []

    if activity_type == 'quote':
        summary = f"{customer_label} 견적 일정입니다. 견적 금액, 품목, 의사결정 일정, 다음 회신 기한을 이 일정에서 확정하는 쪽으로 움직이세요."
        talk_track = [
            '이번 견적 기준에서 수량, 납기, 예산 중 어느 조건이 먼저 맞아야 진행 가능한지 확인합니다.',
            '견적서를 보낸 뒤 언제까지 내부 확인이 가능한지 날짜로 받습니다.',
            '가격을 먼저 낮추기보다 변경 가능한 조건과 필수 조건을 분리해 묻습니다.',
        ]
        checklist = ['견적 품목/수량 재확인', '의사결정자와 내부 결재 일정 확인', '견적 유효기간과 다음 회신일 설정']
        recommended_next_action = '견적 전달 후 회신 기한을 CRM 후속일로 잡고, 필요한 수정 조건을 한 번에 정리합니다.'
    elif activity_type == 'delivery':
        summary = f"{customer_label} 납품 일정입니다. 품목, 수량, 세금계산서, 선결제 차감 여부를 현장에서 누락 없이 확인해야 합니다."
        talk_track = [
            '납품 품목과 수량이 맞는지 먼저 같이 확인합니다.',
            '세금계산서 발행 기준과 선결제 차감 여부를 고객에게 명확히 확인합니다.',
            '추가 소모품이나 다음 발주 예상 시점을 짧게 물어 다음 기회를 만듭니다.',
        ]
        checklist = ['납품 품목/수량 확인', '세금계산서와 결제 방식 확인', '다음 사용 예정일과 재주문 가능성 확인']
        recommended_next_action = '납품 완료 여부와 세금계산서/결제 상태를 노트에 남기고 다음 재구매 확인일을 잡습니다.'
    elif activity_type == 'service':
        summary = f"{customer_label} 서비스 일정입니다. 증상, 사용 조건, 서비스 처리 기준, 후속 처리 기준을 분리해 기록하는 것이 핵심입니다."
        talk_track = [
            '현재 증상이 언제부터 어떤 조건에서 반복되는지 확인합니다.',
            '사용 제품, 로트, 사진/동영상 근거가 있는지 확인합니다.',
            '교체, 회수, 추가 확인 중 어떤 처리 방향을 기대하는지 묻습니다.',
        ]
        checklist = ['증상과 발생 조건 확인', '제품/로트/사진 근거 확보', '처리 예정일과 담당자 합의']
        recommended_next_action = '서비스 증상과 처리 예정일을 노트에 남기고 고객에게 다음 안내 시점을 공유합니다.'
    else:
        summary = f"{customer_label} 고객 미팅 일정입니다. 이 일정에서는 고객의 현재 실험/구매 맥락과 다음 제안 조건을 확인하는 데 집중하세요."
        talk_track = [
            '최근 사용 중인 품목과 불편한 점을 먼저 확인합니다.',
            '다음 실험 일정, 예산, 구매 가능 시점을 짧게 물어봅니다.',
            '바로 팔기보다 다음 견적이나 샘플 제안으로 이어질 조건을 찾습니다.',
        ]
        checklist = ['현재 사용 품목 확인', '다음 실험/구매 일정 확인', '견적/샘플 필요 여부 확인']
        recommended_next_action = '미팅에서 확인한 구매 조건과 다음 연락일을 CRM 후속 액션으로 남깁니다.'

    risks = []
    if activity_type in {'quote', 'delivery'} and not delivery_items and not (context.get('deliverySummary') or {}).get('itemsText'):
        risks.append({'level': 'medium', 'label': '품목 누락', 'value': '견적/납품 품목이 비어 있어 현장 확인이나 서류 자동화가 흔들릴 수 있습니다.'})
    if amount <= 0 and activity_type in {'quote', 'delivery'}:
        risks.append({'level': 'low', 'label': '금액 미입력', 'value': '예상 금액이 없어 매출 영향과 실행 필요도 판단이 약합니다.'})
    if not (context.get('recentEmails') or []):
        risks.append({'level': 'low', 'label': '메일 근거 부족', 'value': '최근 연결 메일이 없어 고객의 최신 문면 요청은 확인되지 않았습니다.'})

    note_content = (
        f"[{activity_label}] {date_label} {customer_label} 일정 진행. "
        f"핵심 확인: {' / '.join(checklist[:3])}. "
        f"권장 대응: {recommended_next_action}"
    )
    if schedule.get('notes'):
        note_content += f" 기존 일정 메모: {schedule.get('notes')}"

    return {
        'summary': summary,
        'priority': 'high' if activity_type in {'quote', 'delivery'} else 'medium',
        'talkTrack': talk_track,
        'checklist': checklist,
        'risks': risks,
        'recommendedNextAction': recommended_next_action,
        'afterMeetingNoteDraft': {
            'actionType': _schedule_ai_report_action_type(activity_type),
            'content': '',
            'nextAction': '',
        },
        'mailDraft': {
            'subject': '',
            'body': '',
        },
        'evidence': _schedule_ai_evidence_from_context(context),
        'confidence': 'medium' if context.get('recentNotes') or context.get('deliveryItems') else 'low',
    }


def _schedule_ai_text_list(value, limit=6, text_limit=420):
    return [
        _ai_workspace_question_text(item, text_limit)
        for item in _ai_json_list(value)[:limit]
        if _ai_workspace_question_text(item, text_limit)
    ]


def _schedule_ai_risk_payload(value):
    risks = []
    for item in _ai_json_list(value)[:5]:
        if isinstance(item, dict):
            label = _ai_workspace_question_text(item.get('label') or item.get('title') or item.get('risk'), 160)
            risk_value = _ai_workspace_question_text(item.get('value') or item.get('detail') or item.get('reason'), 520)
            level = _ai_workspace_question_text(item.get('level') or item.get('severity'), 40) or 'medium'
        else:
            label = '주의'
            risk_value = _ai_workspace_question_text(item, 520)
            level = 'medium'
        if label or risk_value:
            risks.append({
                'level': level if level in {'high', 'medium', 'low'} else 'medium',
                'label': label or '주의',
                'value': risk_value,
            })
    return risks


def _normalize_schedule_ai_coach(data, fallback):
    if not isinstance(data, dict):
        return fallback

    note_draft = data.get('afterMeetingNoteDraft') or data.get('reportDraft') or {}
    if not isinstance(note_draft, dict):
        note_draft = {}
    fallback_note = fallback.get('afterMeetingNoteDraft') or {}

    mail_draft = data.get('mailDraft') or data.get('emailDraft') or {}
    if not isinstance(mail_draft, dict):
        mail_draft = {}
    fallback_mail = fallback.get('mailDraft') or {}

    confidence = _ai_workspace_question_text(data.get('confidence') or fallback.get('confidence'), 20).lower()
    if confidence not in {'high', 'medium', 'low'}:
        confidence = fallback.get('confidence') or 'low'

    evidence = _ai_workspace_question_evidence_payload(data.get('evidence'), limit=6, value_limit=700) or fallback.get('evidence', [])
    existing_hrefs = {item.get('href') for item in evidence if isinstance(item, dict) and item.get('href')}
    for item in fallback.get('evidence', []):
        if not isinstance(item, dict):
            continue
        href = item.get('href')
        if href and href not in existing_hrefs and len(evidence) < 6:
            evidence.append(item)
            existing_hrefs.add(href)

    result = {
        'summary': _ai_workspace_question_text(data.get('summary') or data.get('answer'), 1400) or fallback.get('summary', ''),
        'priority': _ai_workspace_question_text(data.get('priority'), 40) or fallback.get('priority', 'medium'),
        'talkTrack': _schedule_ai_text_list(data.get('talkTrack') or data.get('talk_track'), limit=5) or fallback.get('talkTrack', []),
        'checklist': _schedule_ai_text_list(data.get('checklist') or data.get('checks'), limit=7) or fallback.get('checklist', []),
        'risks': _schedule_ai_risk_payload(data.get('risks')) or fallback.get('risks', []),
        'recommendedNextAction': _ai_workspace_question_text(
            data.get('recommendedNextAction') or data.get('nextAction'),
            760,
        ) or fallback.get('recommendedNextAction', ''),
        'afterMeetingNoteDraft': {
            'actionType': _schedule_ai_report_action_type(
                note_draft.get('actionType') or fallback_note.get('actionType') or 'customer_meeting'
            ),
            'content': '',
            'nextAction': '',
        },
        'mailDraft': {
            'subject': '',
            'body': '',
        },
        'evidence': evidence,
        'confidence': confidence,
    }
    return result


def _generate_schedule_ai_coach(context, model=None):
    fallback = _schedule_ai_coach_fallback(context)
    selected_model = model or AI_WORKSPACE_DEFAULT_QUESTION_MODEL
    try:
        from ai_chat.services import create_openai_chat_completion, get_openai_client, get_standard_openai_model

        selected_model = (
            model
            or os.environ.get('OPENAI_MODEL_NANO')
            or os.environ.get('OPENAI_MODEL_SCHEDULE_COACH')
            or os.environ.get('OPENAI_MODEL_AI_WORKSPACE')
            or get_standard_openai_model()
            or AI_WORKSPACE_DEFAULT_QUESTION_MODEL
        )
        client = get_openai_client()
        prompt_payload = {
            'crmContext': context,
            'rules': [
                '제공된 crmContext에 있는 CRM 사실만 사용한다.',
                '일정 상세 화면의 CRM 브리핑만 만든다.',
                '어떻게 말할지, 어떻게 설득할지, 메일/노트 초안은 만들지 않는다.',
                '일정 유형이 견적이면 견적 조건, 금액, 유효기간, 확인되지 않은 정보를 브리핑한다.',
                '일정 유형이 납품이면 품목, 수량, 외상/카드/선결제 등 확인된 결제 맥락만 브리핑한다.',
                '일정 유형이 서비스이면 증상, 근거, 처리 예정일 등 기록된 사실만 브리핑한다.',
                '견적, 납품, 미팅, 방문, 일정, 영업노트 레코드를 언급하면 crmContext의 href를 evidence에 포함한다.',
                'afterMeetingNoteDraft와 mailDraft는 빈 값으로 둔다.',
                '없는 구매 의사, 납품 완료, 고객 마음을 만들어내지 않는다.',
                '웹 검색은 사용하지 않는다.',
                'JSON 객체만 반환한다.',
            ],
            'outputSchema': {
                'summary': 'string',
                'priority': 'high|medium|low',
                'talkTrack': ['string'],
                'checklist': ['string'],
                'risks': [{'level': 'high|medium|low', 'label': 'string', 'value': 'string'}],
                'recommendedNextAction': 'string',
                'afterMeetingNoteDraft': {
                    'actionType': 'customer_meeting|quote|delivery_schedule|service',
                    'content': 'string',
                    'nextAction': 'string',
                },
                'mailDraft': {'subject': 'string', 'body': 'string'},
                'evidence': [{'label': 'string', 'value': 'string', 'href': 'string', 'linkLabel': 'string'}],
                'confidence': 'high|medium|low',
            },
        }
        response = create_openai_chat_completion(
            client,
            'schedule_ai_coach',
            selected_model,
            [
                {
                    'role': 'system',
                    'content': (
                        '너는 B2B 영업 CRM의 일정 브리핑 작성자다. '
                        '현재 일정과 연결 고객 기록만 보고, 확인된 사실과 누락 정보를 한국어로 간결하게 브리핑한다. '
                        '메일, 말문, 노트 초안, 전략 추천은 작성하지 않는다. '
                        '반드시 JSON 객체만 반환한다.'
                    ),
                },
                {
                    'role': 'user',
                    'content': json.dumps(prompt_payload, ensure_ascii=False, cls=DjangoJSONEncoder),
                },
            ],
            response_format={'type': 'json_object'},
            temperature=0.2,
            max_tokens=SCHEDULE_AI_COACH_OUTPUT_TOKENS,
            prompt_cache_key='sales-note:schedule-coach:v1',
        )
        data = _ai_workspace_json_from_text(response.choices[0].message.content)
        return _normalize_schedule_ai_coach(data, fallback), 'openai', selected_model
    except Exception as exc:
        logger.warning('Schedule AI coach fallback used: %s', exc)
        return fallback, 'fallback', selected_model


@never_cache
@require_POST
def schedule_ai_coach_api(request, schedule_id):
    """Generate unsaved execution coaching for one schedule detail screen."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    if not (user_profile and user_profile.can_use_ai):
        return JsonResponse({
            'success': False,
            'error': 'permission_denied',
            'message': 'AI 기능 사용 권한이 없습니다.',
        }, status=403)

    schedule = _schedules_get_detail_schedule(schedule_id)
    if not can_access_user_data(request.user, schedule.user):
        return JsonResponse({
            'success': False,
            'error': 'permission_denied',
            'message': '접근 권한이 없습니다.',
        }, status=403)

    context = _schedule_ai_coach_context(schedule, request.user)
    coach, source, selected_model = _generate_schedule_ai_coach(context)
    return JsonResponse({
        'success': True,
        'source': source,
        'model': selected_model,
        'modelLabel': _ai_workspace_question_model_label(selected_model),
        'generatedAt': timezone.now().isoformat(),
        'scope': context.get('scope') or {},
        'coach': coach,
        'context': {
            'scheduleId': schedule.id,
            'followupId': schedule.followup_id,
            'departmentId': schedule.department_id or (schedule.followup.department_id if schedule.followup else None),
            'recentNoteCount': len(context.get('recentNotes') or []),
            'recentEmailCount': len(context.get('recentEmails') or []),
            'deliveryItemCount': len(context.get('deliveryItems') or []),
            'stored': False,
        },
        'requiresHumanReview': True,
    })


# ============ 일정(Schedule) 관련 뷰들 ============


@login_required
def schedule_update_delivery_items(request, pk):
    """일정의 납품 품목 업데이트"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크: 수정 권한이 있는 경우만 수정 가능
    if not can_modify_user_data(request.user, schedule.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '수정 권한이 없습니다.'}, status=403)
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('reporting:schedule_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # 납품 품목 저장
            created_count = save_delivery_items(request, schedule)
            
            if created_count == 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': '저장된 품목이 없습니다.'}, status=400)
                messages.warning(request, '저장된 품목이 없습니다. 품목명과 수량을 모두 입력했는지 확인해주세요.')
                return redirect('reporting:schedule_detail', pk=pk)
            
            # 새로 저장된 DeliveryItem들을 텍스트로 변환
            delivery_items = schedule.delivery_items_set.all()
            
            delivery_text = ''
            total_delivery_amount = 0
            delivery_items_list = []
            
            if delivery_items.exists():
                delivery_lines = []
                
                for item in delivery_items:
                    # delivery_items_list에 JSON 직렬화 가능한 형태로 추가
                    # unit_price가 None이 아니면 실제 값 사용 (0 포함)
                    item_unit_price = None
                    if item.unit_price is not None:
                        item_unit_price = float(item.unit_price)
                    
                    delivery_items_list.append({
                        'id': item.id,
                        'item_name': item.item_name,
                        'quantity': float(item.quantity),
                        'unit_price': item_unit_price,
                        'product_id': item.product_id
                    })
                    
                    # unit_price가 None이 아니고 0보다 클 때만 금액 표시
                    if item.unit_price is not None and item.unit_price > 0:
                        # 매출 총액 — 일정의 부가세 모드 반영(reporting/vat.py)
                        total_amount = int(vat.item_gross_total(item, unit_price=item.unit_price))
                        total_delivery_amount += total_amount
                        delivery_lines.append(f"{item.item_name}: {item.quantity}개 ({total_amount:,}원)")
                    elif item.unit_price is not None and item.unit_price == 0:
                        # 0원인 경우
                        delivery_lines.append(f"{item.item_name}: {item.quantity}개 (0원)")
                    else:
                        # unit_price가 None인 경우
                        delivery_lines.append(f"{item.item_name}: {item.quantity}개")
                
                delivery_text = '\n'.join(delivery_lines)
                
                if schedule.activity_type == 'delivery':
                    # 관련 History가 있으면 업데이트, 없으면 새로 생성
                    related_histories = schedule.histories.filter(action_type='delivery_schedule')
                    if related_histories.exists():
                        # 기존 History 업데이트
                        for history in related_histories:
                            history.delivery_items = delivery_text
                            if total_delivery_amount > 0:
                                history.delivery_amount = total_delivery_amount
                            history.save(update_fields=['delivery_items', 'delivery_amount'])
                    else:
                        # 새로운 History 생성
                        from .models import History
                        history = History.objects.create(
                            schedule=schedule,
                            user=request.user,
                            action_type='delivery_schedule',
                            delivery_items=delivery_text,
                            delivery_amount=total_delivery_amount if total_delivery_amount > 0 else None,
                            content=f'납품 품목 {created_count}개 추가'
                        )
            
            # AJAX 요청인 경우 JSON 응답 반환
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '납품 품목이 성공적으로 업데이트되었습니다.',
                    'schedule': {
                        'id': schedule.id,
                        'delivery_items': delivery_text,
                        'delivery_items_list': delivery_items_list,
                        'delivery_amount': total_delivery_amount
                    }
                })
            
            messages.success(request, '납품 품목이 성공적으로 업데이트되었습니다.')
        except Exception as e:
            logger.error(f'납품 품목 업데이트 중 오류: {str(e)}', exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'납품 품목 업데이트 중 오류가 발생했습니다: {str(e)}')
        
        return redirect('reporting:schedule_detail', pk=pk)
    
    # GET 요청은 허용하지 않음
    return redirect('reporting:schedule_detail', pk=pk)


@login_required
def schedule_api_view(request):
    """일정 데이터 API (JSON 응답) - 같은 회사 직원 데이터 필터링 + PersonalSchedule 포함"""
    try:
        from .models import PersonalSchedule
        from django.db.models import Prefetch
        from decimal import Decimal
        
        user_profile = get_user_profile(request.user)
        
        # === 데이터 필터: 나 / 전체(같은 회사) / 특정 직원 ===
        data_filter = request.GET.get('data_filter', 'me')
        filter_user_id = request.GET.get('filter_user')
        
        # 필터에 따른 대상 사용자 결정
        if data_filter == 'all' and user_profile and user_profile.company:
            # 같은 회사 전체
            filter_users = User.objects.filter(
                userprofile__company=user_profile.company,
                is_active=True
            )
        elif data_filter == 'user' and filter_user_id and user_profile and user_profile.company:
            # 특정 직원 (같은 회사 확인)
            try:
                target_user = User.objects.get(
                    id=filter_user_id,
                    userprofile__company=user_profile.company,
                    is_active=True
                )
                filter_users = User.objects.filter(id=target_user.id)
            except User.DoesNotExist:
                filter_users = User.objects.filter(id=request.user.id)
        else:
            # 'me' - 본인만
            filter_users = User.objects.filter(id=request.user.id)
        
        # 스케줄 쿼리
        schedules = Schedule.objects.filter(user__in=filter_users)
        
        # 🔥 최적화: 관련 데이터를 한 번에 가져오기
        schedules = schedules.select_related(
            'followup',
            'followup__company',
            'followup__department',
            'user'
        ).prefetch_related(
            'delivery_items_set',  # DeliveryItem 미리 로드
            Prefetch(
                'histories',
                queryset=History.objects.filter(action_type='delivery_schedule').only(
                    'id', 'action_type', 'delivery_items', 'delivery_amount'
                ),
                to_attr='delivery_histories'
            )
        ).only(
            # 필요한 필드만 SELECT (메모리 절약)
            'id', 'visit_date', 'visit_time', 'location', 'status', 
            'activity_type', 'notes', 'expected_revenue', 'probability', 
            'expected_close_date',
            'followup__id', 'followup__customer_name', 'followup__company__id',
            'followup__company__name', 'followup__department__id', 
            'followup__department__name', 'followup__manager', 
            'followup__address', 'followup__priority',
            'user__id', 'user__username'
        )
        
        schedule_data = []
        for schedule in schedules:
            schedule_item = {
                'id': schedule.id,
                'followup_id': schedule.followup.id,  # 팔로우업 ID 추가
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'time': schedule.visit_time.strftime('%H:%M'),
                'customer': schedule.followup.customer_name or '고객명 미정',
                'company': str(schedule.followup.company) if schedule.followup.company else '업체명 미정',
                'department': str(schedule.followup.department) if schedule.followup.department else '부서명 미정',
                'department_id': schedule.followup.department_id if schedule.followup.department else None,
                'manager': schedule.followup.manager or '',
                'address': schedule.followup.address or '',
                'location': schedule.location or '',
                'status': schedule.status,
                'status_display': schedule.get_status_display(),
                'activity_type': schedule.activity_type,
                'activity_type_display': schedule.get_activity_type_display(),
                'notes': schedule.notes or '',
                'user_name': schedule.user.username,
                'priority': schedule.followup.priority,  # 고객 우선순위 추가
                # 펀넬 관련 필드 추가
                'expected_revenue': float(schedule.expected_revenue) if schedule.expected_revenue else 0,
                'probability': schedule.probability if schedule.probability is not None else None,
                'expected_close_date': schedule.expected_close_date.strftime('%Y-%m-%d') if schedule.expected_close_date else '',
            }
            
            # 견적 또는 납품 일정인 경우 품목 정보 추가
            if schedule.activity_type in ['delivery', 'quote']:
                delivery_items_text = ''
                delivery_amount = 0
                has_schedule_items = False  # 스케줄에 직접 등록된 품목이 있는지 여부
                delivery_items_list = []  # 실제 품목 데이터 배열
                
                # 🔥 최적화: prefetch된 데이터 사용 (추가 쿼리 없음)
                schedule_delivery_items = list(schedule.delivery_items_set.all())
                if schedule_delivery_items:
                    has_schedule_items = True
                    delivery_text_parts = []
                    total_amount = 0
                    
                    for item in schedule_delivery_items:
                        # unit_price가 None이면 0으로 처리 (Decimal 타입 유지)
                        unit_price = item.unit_price if item.unit_price is not None else Decimal('0')
                        item_total = item.total_price or vat.item_gross_total(item, unit_price=unit_price)
                        total_amount += item_total
                        
                        # 실제 품목 데이터 추가
                        delivery_items_list.append({
                            'id': item.id,
                            'item_name': item.item_name,
                            'quantity': float(item.quantity),
                            'unit_price': float(unit_price),
                            'product_id': item.product.id if item.product else None,
                        })
                        
                        # 단가가 0이면 금액 표시 생략
                        if unit_price > 0:
                            text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                        else:
                            text_part = f"{item.item_name}: {item.quantity}개"
                        delivery_text_parts.append(text_part)
                    
                    delivery_items_text = '\n'.join(delivery_text_parts)
                    delivery_amount = int(total_amount)
                else:
                    # 🔥 최적화: prefetch된 delivery_histories 사용
                    if hasattr(schedule, 'delivery_histories') and schedule.delivery_histories:
                        delivery_history = schedule.delivery_histories[0]
                        if delivery_history.delivery_items:
                            delivery_items_text = delivery_history.delivery_items.strip()
                            delivery_amount = int(delivery_history.delivery_amount) if delivery_history.delivery_amount else 0
                
                schedule_item.update({
                    'delivery_items': delivery_items_text,
                    'delivery_amount': delivery_amount,
                    'has_schedule_items': has_schedule_items,  # 품목 관리 제한용
                    'delivery_items_list': delivery_items_list,  # 실제 품목 데이터
                })
            
            schedule_data.append(schedule_item)
        
        # ====== PersonalSchedule 데이터 추가 ======
        # 같은 필터 적용
        personal_schedules = PersonalSchedule.objects.filter(user__in=filter_users)
        
        personal_schedules = personal_schedules.select_related('user', 'company').only(
            'id', 'title', 'content', 'schedule_date', 'schedule_time',
            'user__id', 'user__username', 'company__id', 'company__name'
        )
        
        # PersonalSchedule을 schedule_data에 추가 (type='personal' 구분자 추가)
        for ps in personal_schedules:
            personal_item = {
                'id': ps.id,
                'type': 'personal',  # 개인 일정 구분자
                'visit_date': ps.schedule_date.strftime('%Y-%m-%d'),
                'time': ps.schedule_time.strftime('%H:%M'),
                'title': ps.title,
                'content': ps.content or '',
                'user_name': ps.user.username,
                'company': str(ps.company) if ps.company else '',
                # 캘린더 표시용 기본값
                'customer': ps.title,  # 제목을 customer로 사용
                'status': 'personal',
                'status_display': '개인 일정',
                'activity_type': 'personal',
                'activity_type_display': '개인 일정',
                'location': '',
                'notes': ps.content or '',
                'priority': 'medium',
            }
            schedule_data.append(personal_item)
        
        return JsonResponse(schedule_data, safe=False)
    
    except Exception as e:
        # 에러 디버깅을 위한 JSON 응답
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'message': 'schedule_api_view에서 오류가 발생했습니다.'
        }, status=500)# ============ 히스토리(History) 관련 뷰들 ============


@login_required
@require_POST
def history_toggle_reviewed(request, pk):
    """보고서 매니저 검토 완료 토글 (소속 회사 manager만)."""
    history = get_object_or_404(History, pk=pk)
    user_profile = get_user_profile(request.user)
    if not _can_review_notes(user_profile):
        return JsonResponse({'success': False, 'error': '검토 권한이 없습니다.'}, status=403)
    if not can_access_user_data(request.user, history.user):
        return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)
    from django.utils import timezone as tz
    if history.reviewed_at:
        history.reviewed_at = None
        history.reviewer = None
        is_reviewed = False
    else:
        history.reviewed_at = tz.now()
        history.reviewer = request.user
        is_reviewed = True
    history.save(update_fields=['reviewed_at', 'reviewer'])
    return JsonResponse({
        'success': True,
        'is_reviewed': is_reviewed,
        'reviewed_at': history.reviewed_at.strftime('%Y년 %m월 %d일 %H:%M') if is_reviewed else None,
        'reviewer': request.user.get_full_name() or request.user.username if is_reviewed else None,
    })


# ============ API 엔드포인트들 ============

@login_required
def api_followup_schedules(request, followup_pk):
    """특정 팔로우업의 일정 목록을 JSON으로 반환 (AJAX용)"""
    try:
        followup = get_object_or_404(FollowUp, pk=followup_pk)
        
        # 권한 체크 (같은 회사 소속이면 접근 가능)
        if not can_access_followup(request.user, followup):
            return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        # 본인 일정만 조회 (동료 고객이어도 내가 만든 일정만)
        schedules = Schedule.objects.filter(followup=followup, user=request.user)
        schedule_list = []
        
        for schedule in schedules:
            schedule_list.append({
                'id': schedule.id,
                'text': f"{schedule.visit_date} {schedule.visit_time} - {schedule.location or '장소 미정'}",
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d')  # 납품 날짜 자동 설정용
            })
        
        return JsonResponse({'schedules': schedule_list})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def schedule_histories_api(request, schedule_id):
    """특정 일정의 관련 활동 기록을 JSON으로 반환"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        # 해당 일정에 직접 연결된 활동 기록만 조회 (최신순) - 답글 메모 포함
        histories = History.objects.filter(schedule=schedule).prefetch_related(
            'reply_memos__user'
        ).order_by('-created_at')
        
        histories_data = []
        for history in histories:
            # 활동 타입에 따른 추가 정보 포함
            history_data = {
                'id': history.id,
                'action_type': history.action_type,
                'action_type_display': history.get_action_type_display(),
                'content': history.content or '',
                'created_at': history.created_at.strftime('%Y-%m-%d %H:%M'),
                'user': history.user.username,
                'created_by': history.created_by.username if history.created_by else history.user.username,
            }
            
            # 답글 메모(댓글) 정보 추가
            reply_memos_data = []
            for reply_memo in history.reply_memos.all():
                reply_memos_data.append({
                    'id': reply_memo.id,
                    'content': reply_memo.content,
                    'created_at': reply_memo.created_at.strftime('%Y-%m-%d %H:%M'),
                    'user': reply_memo.user.username,
                })
            history_data['reply_memos'] = reply_memos_data
            
            # 첨부파일 정보 추가
            files_data = []
            for file_obj in history.files.all():
                files_data.append({
                    'id': file_obj.id,
                    'filename': file_obj.original_filename,
                    'size': file_obj.get_file_size_display(),
                    'uploaded_at': file_obj.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                    'uploaded_by': file_obj.uploaded_by.username,
                })
            history_data['files'] = files_data
            
            # 납품 일정인 경우 추가 정보
            if history.action_type == 'delivery_schedule':
                # DeliveryItem 모델에서 최신 납품 품목 데이터 가져오기
                delivery_items_text = ''
                delivery_amount = history.delivery_amount or 0
                
                # 1차: History에 연결된 DeliveryItem 확인
                delivery_items = history.delivery_items_set.all().order_by('id')
                if delivery_items.exists():
                    delivery_text_parts = []
                    total_amount = 0
                    
                    for item in delivery_items:
                        item_total = item.total_price or vat.item_gross_total(item, unit_price=item.unit_price)
                        total_amount += item_total
                        text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                        delivery_text_parts.append(text_part)
                    
                    delivery_items_text = '\n'.join(delivery_text_parts)
                    delivery_amount = int(total_amount)
                
                # 2차: History의 schedule에 연결된 DeliveryItem 확인 (fallback)
                elif history.schedule:
                    schedule_delivery_items = history.schedule.delivery_items_set.all().order_by('id')
                    if schedule_delivery_items.exists():
                        delivery_text_parts = []
                        total_amount = 0
                        
                        for item in schedule_delivery_items:
                            item_total = item.total_price or vat.item_gross_total(item, unit_price=item.unit_price)
                            total_amount += item_total
                            text_part = f"{item.item_name}: {item.quantity}개 ({int(item_total):,}원)"
                            delivery_text_parts.append(text_part)
                        
                        delivery_items_text = '\n'.join(delivery_text_parts)
                        delivery_amount = int(total_amount)
                
                # 3차: 기존 텍스트 필드 사용 (최종 fallback)
                if not delivery_items_text and history.delivery_items:
                    delivery_items_text = history.delivery_items
                
                history_data.update({
                    'delivery_amount': delivery_amount,
                    'delivery_items': delivery_items_text,
                    'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
                    'tax_invoice_issued': history.tax_invoice_issued,
                })
            
            # 고객 미팅인 경우 추가 정보
            elif history.action_type == 'customer_meeting':
                history_data.update({
                    'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
                    'meeting_situation': history.meeting_situation or '',
                    'meeting_researcher_quote': history.meeting_researcher_quote or '',
                    'meeting_confirmed_facts': history.meeting_confirmed_facts or '',
                    'meeting_obstacles': history.meeting_obstacles or '',
                    'meeting_next_action': history.meeting_next_action or '',
                })
            
            # 서비스인 경우 추가 정보
            elif history.action_type == 'service':
                history_data.update({
                    'service_status': history.service_status or '',
                    'service_status_display': history.get_service_status_display() if history.service_status else '',
                })
            
            histories_data.append(history_data)
        
        return JsonResponse({
            'success': True,
            'histories': histories_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def followup_histories_api(request, followup_id):
    """특정 팔로우업의 모든 활동 기록을 JSON으로 반환"""
    try:
        followup = get_object_or_404(FollowUp, id=followup_id)
        
        # 권한 체크 - followup.user가 None인 경우를 처리
        if followup.user:
            if not can_access_user_data(request.user, followup.user):
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        else:
            # followup.user가 None인 경우, 현재 사용자가 관리자이거나 매니저인 경우만 접근 허용
            user_profile = get_user_profile(request.user)
            if not (user_profile.is_admin() or user_profile.is_manager()):
                return JsonResponse({'error': '권한이 없습니다.'}, status=403)
        
        # 해당 팔로우업의 모든 활동 기록 조회 (최신순)
        histories = History.objects.filter(followup=followup).select_related('schedule').order_by('-created_at')
        
        histories_data = []
        for history in histories:
            try:
                # 활동 타입에 따른 추가 정보 포함
                history_data = {
                    'id': history.id,
                    'action_type': history.action_type,
                    'action_type_display': history.get_action_type_display(),
                    'content': history.content or '',
                    'created_at': history.created_at.strftime('%Y-%m-%d %H:%M'),
                    'user': history.user.username if history.user else '사용자 미정',
                    'created_by': history.created_by.username if history.created_by else (history.user.username if history.user else '사용자 미정'),
                }
                
                # 납품 일정인 경우 추가 정보 (품목 포함)
                if history.action_type == 'delivery_schedule':
                    # 납품 품목 조회 (DeliveryItem)
                    delivery_items_list = []
                    for item in history.delivery_items_set.all():
                        delivery_items_list.append({
                            'item_name': item.item_name,
                            'quantity': item.quantity,
                            'unit': item.unit or 'EA',
                            'unit_price': float(item.unit_price) if item.unit_price else 0,
                            'total_price': float(item.total_price) if item.total_price else 0,
                        })
                    
                    history_data.update({
                        'delivery_amount': history.delivery_amount,
                        'delivery_items': history.delivery_items or '',
                        'delivery_items_list': delivery_items_list,
                        'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
                        'tax_invoice_issued': history.tax_invoice_issued,
                    })
                
                # 견적 일정인 경우 추가 정보 (품목 포함)
                elif history.action_type == 'quote':
                    quote_items_list = []
                    total_quote_amount = 0
                    
                    # 디버깅: schedule 연결 상태
                    has_schedule = history.schedule is not None
                    schedule_id = history.schedule.id if history.schedule else None
                    
                    # 1. 연결된 스케줄의 견적 조회
                    if history.schedule:
                        # 스케줄에 연결된 DeliveryItem (견적용 품목)
                        for item in history.schedule.delivery_items_set.all():
                            quote_items_list.append({
                                'item_name': item.item_name,
                                'quantity': item.quantity,
                                'unit_price': float(item.unit_price) if item.unit_price else 0,
                                'subtotal': float(item.total_price) if item.total_price else 0,
                            })
                            total_quote_amount += float(item.total_price) if item.total_price else 0
                        
                        # 스케줄에 연결된 Quote 모델의 품목
                        quotes = history.schedule.quotes.all().prefetch_related('items__product')
                        for quote in quotes:
                            for item in quote.items.all():
                                quote_items_list.append({
                                    'item_name': item.product.product_code if item.product else '품목명 없음',
                                    'quantity': item.quantity,
                                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                                    'subtotal': float(item.subtotal) if item.subtotal else 0,
                                })
                            total_quote_amount += float(quote.total_amount) if quote.total_amount else 0
                    
                    # 2. 히스토리에 직접 연결된 DeliveryItem도 확인
                    for item in history.delivery_items_set.all():
                        quote_items_list.append({
                            'item_name': item.item_name,
                            'quantity': item.quantity,
                            'unit_price': float(item.unit_price) if item.unit_price else 0,
                            'subtotal': float(item.total_price) if item.total_price else 0,
                        })
                        total_quote_amount += float(item.total_price) if item.total_price else 0
                    
                    history_data.update({
                        'quote_items_list': quote_items_list,
                        'total_quote_amount': total_quote_amount,
                        'has_schedule': has_schedule,  # 디버깅용
                        'schedule_id': schedule_id,  # 디버깅용
                    })
                
                # 고객 미팅인 경우 추가 정보
                elif history.action_type == 'customer_meeting':
                    history_data.update({
                        'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
                    })
                
                histories_data.append(history_data)
                
            except Exception as history_error:
                # 개별 히스토리 처리 중 에러가 발생해도 계속 진행
                continue
        
        # ===== 스케줄에서 직접 품목 정보 가져오기 (히스토리와 중복되지 않도록) =====
        # 히스토리에 연결되지 않은 스케줄의 품목도 표시
        processed_schedule_ids = set()
        for h in histories:
            if h.schedule:
                processed_schedule_ids.add(h.schedule.id)
        
        schedules_data = []
        schedules = Schedule.objects.filter(
            followup=followup,
            activity_type__in=['quote', 'delivery']
        ).prefetch_related('delivery_items_set').order_by('-visit_date')
        
        for schedule in schedules:
            # 이미 히스토리에서 처리된 스케줄은 건너뛰기
            if schedule.id in processed_schedule_ids:
                continue
            
            items_list = []
            total_amount = 0
            
            for item in schedule.delivery_items_set.all():
                items_list.append({
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit': item.unit or 'EA',
                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                    'total_price': float(item.total_price) if item.total_price else 0,
                })
                total_amount += float(item.total_price) if item.total_price else 0
            
            # 품목이 있는 경우만 추가
            if items_list:
                schedule_data = {
                    'id': f'schedule_{schedule.id}',
                    'type': 'schedule',
                    'action_type': 'delivery_schedule' if schedule.activity_type == 'delivery' else 'quote',
                    'action_type_display': '납품 일정' if schedule.activity_type == 'delivery' else '견적 제출',
                    'content': schedule.notes or '',
                    'created_at': schedule.visit_date.strftime('%Y-%m-%d'),
                    'user': schedule.user.username if schedule.user else '사용자 미정',
                    'items_list': items_list,
                    'total_amount': total_amount,
                    'schedule_id': schedule.id,
                    'status': schedule.get_status_display(),
                }
                schedules_data.append(schedule_data)
        
        return JsonResponse({
            'success': True,
            'customer_name': followup.customer_name or '고객명 미정',
            'company': followup.company.name if followup.company else '업체명 미정',
            'histories': histories_data,
            'schedules': schedules_data,  # 히스토리에 연결되지 않은 스케줄 품목
            'total_count': len(histories_data) + len(schedules_data)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"followup_histories_api error for followup_id={followup_id}: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'서버 에러: {str(e)}'}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8.6-1: 세금계산서 요청 API
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def followup_tax_invoices_api(request, followup_id):
    """거래처별 세금계산서 요청 목록 반환 (GET) 또는 신규 요청 생성 (POST)."""
    from .models import TaxInvoiceRequest
    from decimal import Decimal

    followup = get_object_or_404(FollowUp, pk=followup_id)
    if not can_access_followup(request.user, followup):
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)

    if request.method == 'POST':
        return _receivables_only_response()

        # ── 발행 요청 생성 ────────────────────────────────────────────────────
        schedule_id = request.POST.get('schedule_id') or None
        schedule = None
        if schedule_id:
            try:
                schedule = Schedule.objects.get(pk=schedule_id, followup=followup)
            except Schedule.DoesNotExist:
                return JsonResponse({'error': '해당 일정을 찾을 수 없습니다.'}, status=404)

        # 같은 일정에 이미 요청 중인 건이 있으면 중복 생성 방지
        if schedule:
            existing = TaxInvoiceRequest.objects.filter(
                followup=followup,
                schedule=schedule,
                status__in=['requested', 'on_hold'],
            ).first()
            if existing:
                return JsonResponse({
                    'error': f'이미 {existing.get_status_display()} 상태의 요청이 있습니다.',
                }, status=400)

        # 금액 계산: 납품 품목 기준. total_price 는 일정의 부가세 모드가 반영된 총액이다.
        supply_amount = Decimal('0')
        vat_mode = vat.schedule_vat_mode(schedule)
        if schedule:
            for item in schedule.delivery_items_set.all():
                if item.total_price:
                    supply_amount += vat.supply_from_gross(item.total_price, vat_mode)
        supply_amount = supply_amount.quantize(Decimal('1'))
        tax_amount = Decimal('0') if vat_mode == vat.VAT_NONE else (supply_amount * vat.VAT_RATE).quantize(Decimal('1'))
        total_amount = supply_amount + tax_amount

        tax_req = TaxInvoiceRequest.objects.create(
            followup=followup,
            schedule=schedule,
            status='requested',
            supply_amount=supply_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            requested_by=request.user,
            request_memo=request.POST.get('memo', ''),
        )
        return JsonResponse({
            'success': True,
            'id': tax_req.pk,
            'status': tax_req.status,
            'status_display': tax_req.get_status_display(),
            'message': '발행 요청이 등록되었습니다.',
        })

    # ── GET: 목록 반환 ────────────────────────────────────────────────────────
    qs = (
        TaxInvoiceRequest.objects
        .filter(followup=followup)
        .select_related('schedule', 'requested_by', 'issued_by', 'cancelled_by')
        .order_by('-requested_at')
    )
    items = []
    for r in qs:
        items.append({
            'id': r.pk,
            'status': r.status,
            'status_display': r.get_status_display(),
            'status_badge': r.status_badge_class,
            'schedule_id': r.schedule_id,
            'schedule_date': r.schedule.visit_date.strftime('%Y-%m-%d') if r.schedule else '',
            'supply_amount': int(r.supply_amount),
            'tax_amount': int(r.tax_amount),
            'total_amount': int(r.total_amount),
            'requested_by': r.requested_by.username if r.requested_by else '',
            'requested_at': r.requested_at.strftime('%Y-%m-%d %H:%M'),
            'request_memo': r.request_memo,
            'issued_by': r.issued_by.username if r.issued_by else '',
            'issued_at': r.issued_at.strftime('%Y-%m-%d %H:%M') if r.issued_at else '',
            'issue_memo': r.issue_memo,
            'cancelled_by': r.cancelled_by.username if r.cancelled_by else '',
            'cancelled_at': r.cancelled_at.strftime('%Y-%m-%d %H:%M') if r.cancelled_at else '',
            'cancel_reason': r.cancel_reason,
        })

    # 발행 가능한 납품 일정 목록 (이미 요청 진행 중인 건 제외)
    delivery_schedules = (
        Schedule.objects
        .filter(followup=followup, activity_type='delivery')
        .prefetch_related('delivery_items_set')
        .order_by('-visit_date')
    )
    already_requested = set(
        TaxInvoiceRequest.objects
        .filter(followup=followup, status__in=['requested', 'on_hold', 'issued'])
        .values_list('schedule_id', flat=True)
    )
    schedules_list = []
    for s in delivery_schedules:
        total = sum(
            float(item.total_price or 0)
            for item in s.delivery_items_set.all()
        )
        schedules_list.append({
            'id': s.pk,
            'date': s.visit_date.strftime('%Y-%m-%d'),
            'status': s.get_status_display(),
            'notes': s.notes or '',
            'total_amount': total,
            'has_active_request': s.pk in already_requested,
            'item_count': s.delivery_items_set.count(),
        })

    return JsonResponse({
        'success': True,
        'tax_invoices': items,
        'delivery_schedules': schedules_list,
    })


@login_required
@require_http_methods(["POST"])
def tax_invoice_update_status_api(request, request_id):
    """세금계산서 요청 상태 업데이트 (발행완료 / 발행취소 / 보류)."""
    return _receivables_only_response()

    from .models import TaxInvoiceRequest
    from django.utils import timezone

    tax_req = get_object_or_404(TaxInvoiceRequest, pk=request_id)
    user_profile = get_user_profile(request.user)

    # 접근 권한: followup 접근 가능해야 함
    if not can_access_followup(request.user, tax_req.followup):
        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)

    new_status = request.POST.get('status', '').strip()
    if new_status not in dict(TaxInvoiceRequest.STATUS_CHOICES):
        return JsonResponse({'error': '올바르지 않은 상태값입니다.'}, status=400)

    # 권한별 허용 액션
    can_issue_or_cancel_others = user_profile.is_admin() or user_profile.is_manager()
    is_requester = tax_req.requested_by_id == request.user.pk

    if new_status == 'issued':
        if not can_issue_or_cancel_others:
            return JsonResponse({'error': '발행 완료 처리는 관리자/매니저만 가능합니다.'}, status=403)
        tax_req.issued_by = request.user
        tax_req.issued_at = timezone.now()
        tax_req.issue_memo = request.POST.get('memo', '')

    elif new_status == 'cancelled':
        # 자신의 요청은 취소 가능, 다른 사람 것은 admin/manager만
        if not (is_requester or can_issue_or_cancel_others):
            return JsonResponse({'error': '취소는 요청자 본인 또는 관리자/매니저만 가능합니다.'}, status=403)
        tax_req.cancelled_by = request.user
        tax_req.cancelled_at = timezone.now()
        tax_req.cancel_reason = request.POST.get('memo', '')

    elif new_status == 'on_hold':
        if not can_issue_or_cancel_others:
            return JsonResponse({'error': '보류 처리는 관리자/매니저만 가능합니다.'}, status=403)
        tax_req.cancelled_by = request.user
        tax_req.cancelled_at = timezone.now()
        tax_req.cancel_reason = request.POST.get('memo', '')

    elif new_status == 'requested':
        # 보류→재요청: 요청자 또는 admin/manager
        if not (is_requester or can_issue_or_cancel_others):
            return JsonResponse({'error': '재요청은 요청자 본인 또는 관리자/매니저만 가능합니다.'}, status=403)

    tax_req.status = new_status
    tax_req.save()

    return JsonResponse({
        'success': True,
        'id': tax_req.pk,
        'status': tax_req.status,
        'status_display': tax_req.get_status_display(),
        'status_badge': tax_req.status_badge_class,
        'message': f'상태가 {tax_req.get_status_display()}으로 변경되었습니다.',
    })


# ─────────────────────────────────────────────────────────────────────────────
# [재현] 대시보드 통합 검색 API — Phase 검색 기능
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(["GET"])
def dashboard_search_api(request):
    """키워드로 연구실(Department) 단위 통합 검색.

    납품/견적 품목명, 일정 메모, 활동 내용을 탐색해
    키워드가 연관된 연구실(Department)을 그루핑하여 반환합니다.

    Query params:
        q (str): 검색어 (필수, 2자 이상)

    Returns:
        JSON { success, query, result_count, departments: [ ... ] }
    """
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'error': '검색어를 2자 이상 입력하세요.'}, status=400)

    user_profile = get_user_profile(request.user)

    # ── 사용자의 소속 UserCompany ─────────────────────────────────────────────
    # UserProfile.company → FK to UserCompany
    user_company = user_profile.company
    if not user_company:
        return JsonResponse({'success': True, 'query': q, 'result_count': 0, 'departments': []})

    # 같은 회사 소속 FollowUp으로 검색 범위를 제한
    # (FollowUp.user_company 는 작성자의 소속 회사를 기록)
    base_followups = FollowUp.objects.filter(user_company=user_company)

    # ── 매칭 결과 수집: Department 기준으로 그루핑 ────────────────────────────
    # {department_id → {meta, matches: []}} 딕셔너리 사용
    dept_map = {}

    def _ensure_dept(followup):
        """dept_map에 연구실 엔트리 초기화."""
        if followup is None:
            return None
        dept = followup.department
        if dept is None:
            return None
        dept_id = dept.id
        if dept_id not in dept_map:
            dept_map[dept_id] = {
                'department_id': dept_id,
                'department_name': dept.name,
                'company_name': dept.company.name if dept.company else '',
                'followup_id': followup.id,
                'customer_name': followup.customer_name or '',
                'followup_url': reverse('reporting:followup_detail', args=[followup.id]),
                'match_count': 0,
                'matches': [],
            }
        return dept_id

    def _add_match(dept_id, match_type, snippet, date_str, url=''):
        if dept_id is None:
            return
        entry = dept_map[dept_id]
        entry['match_count'] += 1
        # 스니펫 최대 2개만 표시 (UI 간결성)
        if len(entry['matches']) < 2:
            entry['matches'].append({
                'type': match_type,
                'snippet': snippet[:80] if snippet else '',
                'date': date_str,
                'url': url,
            })

    # ── 1. FollowUp 직접 매칭 (고객명, 회사명, 연구실명) ────────────────────
    matched_followups = base_followups.filter(
        Q(customer_name__icontains=q) |
        Q(company__name__icontains=q) |
        Q(department__name__icontains=q)
    ).select_related('department', 'department__company', 'company')

    for fu in matched_followups:
        dept_id = _ensure_dept(fu)
        if dept_id is not None:
            # 이미 dept_map에 기록됐으므로 match_count만 올림
            dept_map[dept_id]['match_count'] += 1

    # ── 2. 납품/견적 품목명 (DeliveryItem.item_name) ─────────────────────────
    delivery_matches = (
        DeliveryItem.objects
        .filter(item_name__icontains=q)
        .filter(
            Q(schedule__followup__in=base_followups) |
            Q(history__followup__in=base_followups)
        )
        .select_related(
            'schedule__followup__department__company',
            'history__followup__department__company',
        )
        .order_by('-id')[:200]
    )
    for item in delivery_matches:
        fu = None
        if item.schedule_id and item.schedule and item.schedule.followup_id:
            fu = item.schedule.followup
        elif item.history_id and item.history and item.history.followup_id:
            fu = item.history.followup
        if fu is None:
            continue
        dept_id = _ensure_dept(fu)
        date_str = ''
        if item.schedule:
            date_str = item.schedule.visit_date.strftime('%Y-%m-%d') if item.schedule.visit_date else ''
        elif item.history:
            date_str = item.history.created_at.strftime('%Y-%m-%d') if item.history.created_at else ''
        _add_match(dept_id, 'delivery_item', f'{item.item_name} (×{item.quantity})', date_str)

    # ── 3. 일정 메모 (Schedule.notes) ────────────────────────────────────────
    schedule_matches = (
        Schedule.objects
        .filter(notes__icontains=q, followup__in=base_followups)
        .select_related('followup__department__company')
        .order_by('-visit_date')[:100]
    )
    for s in schedule_matches:
        fu = s.followup
        if fu is None:
            continue
        dept_id = _ensure_dept(fu)
        date_str = s.visit_date.strftime('%Y-%m-%d') if s.visit_date else ''
        url = reverse('reporting:schedule_detail', args=[s.id])
        _add_match(dept_id, 'schedule', s.notes, date_str, url)

    # ── 4. 활동 내용 (History.content, History.delivery_items) ───────────────
    history_matches = (
        History.objects
        .filter(
            Q(content__icontains=q) | Q(delivery_items__icontains=q),
            followup__in=base_followups,
            parent_history__isnull=True,
        )
        .select_related('followup__department__company')
        .order_by('-created_at')[:100]
    )
    for h in history_matches:
        fu = h.followup
        if fu is None:
            continue
        dept_id = _ensure_dept(fu)
        date_str = h.created_at.strftime('%Y-%m-%d') if h.created_at else ''
        url = reverse('reporting:followup_detail', args=[fu.id])
        snippet = h.content or h.delivery_items or ''
        _add_match(dept_id, 'history', snippet, date_str, url)

    # ── 결과 정렬: match_count 내림차순, 최대 20개 ───────────────────────────
    departments = sorted(
        dept_map.values(),
        key=lambda x: x['match_count'],
        reverse=True,
    )[:20]

    return JsonResponse({
        'success': True,
        'query': q,
        'result_count': len(departments),
        'departments': departments,
    })


# ─────────────────────────────────────────────────────────────────────────────

# ============ 인증 관련 뷰들 ============


class CustomLoginView(LoginView):
    """커스텀 로그인 뷰 (성공 메시지 추가)"""
    template_name = 'reporting/login.html'
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        from urllib.parse import urljoin

        frontend_base_url = getattr(
            settings,
            'FRONTEND_PIPELINE_URL',
            '/',
        )
        return urljoin(f"{frontend_base_url.rstrip('/')}/", 'dashboard/')

    def get_success_url_allowed_hosts(self):
        from urllib.parse import urlparse

        allowed_hosts = super().get_success_url_allowed_hosts()
        for frontend_base_url in (
            getattr(settings, 'FRONTEND_PIPELINE_URL', ''),
        ):
            frontend_host = urlparse(frontend_base_url).netloc
            if frontend_host:
                allowed_hosts.add(frontend_host)
        return allowed_hosts
    
    def form_valid(self, form):
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """커스텀 로그아웃 뷰 (성공 메시지 추가)"""
    next_page = reverse_lazy('reporting:login')
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# ============ 사용자 관리 뷰들 ============


# ============ 매니저용 사용자 관리 뷰들 ============


@role_required(['manager'])
@never_cache
def manager_dashboard(request):
    """Manager 전용 대시보드 - dashboard_view로 리다이렉트"""
    from django.shortcuts import redirect
    
    # user_id 파라미터가 있으면 그대로 전달, 없으면 기본 대시보드로
    user_id = request.GET.get('user_id')
    if user_id:
        return redirect(f"{reverse('reporting:dashboard')}?user={user_id}")
    else:
        return redirect('reporting:dashboard')


@role_required(['admin'])
@require_POST
def user_toggle_active(request, user_id):
    """사용자 활성화/비활성화 토글 (Admin 전용)"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # 자기 자신은 비활성화할 수 없음
        if user == request.user:
            return JsonResponse({'error': '자기 자신의 계정은 비활성화할 수 없습니다.'}, status=400)
        
        # 상태 토글
        user.is_active = not user.is_active
        user.save()
        
        status_text = "활성화" if user.is_active else "비활성화"
        messages.success(request, f'사용자 "{user.username}"이(가) {status_text}되었습니다.')
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'사용자가 {status_text}되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@role_required(['admin'])
@require_POST
def user_toggle_ai(request, user_id):
    """사용자 AI 권한 토글 (Admin 전용)"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(UserProfile, user=user)

        profile.can_use_ai = not profile.can_use_ai
        profile.save(update_fields=['can_use_ai'])

        status_text = "부여" if profile.can_use_ai else "해제"
        return JsonResponse({
            'success': True,
            'can_use_ai': profile.can_use_ai,
            'message': f'사용자 "{user.username}"의 AI 권한이 {status_text}되었습니다.'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@never_cache
def toggle_tax_invoice(request, history_id):
    """세금계산서 발행 여부 토글 (AJAX)"""
    return _receivables_only_response()

    try:
        history = get_object_or_404(History, id=history_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 토글 가능 (Manager는 읽기 전용)
        try:
            if not can_modify_user_data(request.user, history.user):
                return JsonResponse({
                    'success': False, 
                    'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'
                }, status=403)
        except Exception as e:
            # 권한 체크 실패 시 자신의 히스토리인지만 확인
            if request.user != history.user:
                return JsonResponse({
                    'success': False, 
                    'error': '수정 권한이 없습니다.'
                }, status=403)
        
        # 납품 일정 히스토리인지 확인
        if history.action_type != 'delivery_schedule':
            return JsonResponse({
                'success': False,
                'error': '납품 일정 히스토리만 세금계산서 토글이 가능합니다.'
            }, status=400)
        
        # 토글 실행
        history.tax_invoice_issued = not history.tax_invoice_issued
        history.save()
        
        # 연결된 Schedule의 DeliveryItem들도 동기화
        if history.schedule:
            from reporting.models import DeliveryItem
            DeliveryItem.objects.filter(schedule=history.schedule).update(
                tax_invoice_issued=history.tax_invoice_issued
            )
        
        return JsonResponse({
            'success': True,
            'tax_invoice_issued': history.tax_invoice_issued,
            'message': f'세금계산서 발행 여부가 {"발행완료" if history.tax_invoice_issued else "미발행"}로 변경되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)

@login_required
def toggle_all_tax_invoices(request, followup_id):
    """고객의 모든 미발행 납품을 발행완료로 일괄 변경 (AJAX)"""
    return _receivables_only_response()

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)
    
    try:
        # FollowUp 조회 및 권한 확인
        followup = get_object_or_404(FollowUp, id=followup_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 가능
        if not can_modify_user_data(request.user, followup.user):
            return JsonResponse({
                'success': False, 
                'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'
            }, status=403)
        
        # 미발행 납품 History 조회
        pending_histories = History.objects.filter(
            followup=followup,
            action_type='delivery_schedule',
            tax_invoice_issued=False
        )
        
        # 일괄 업데이트
        updated_count = pending_histories.update(tax_invoice_issued=True)
        
        # 연결된 Schedule의 DeliveryItem들도 동기화
        from reporting.models import DeliveryItem
        schedule_ids = pending_histories.filter(
            schedule__isnull=False
        ).values_list('schedule_id', flat=True)
        
        if schedule_ids:
            DeliveryItem.objects.filter(
                schedule_id__in=schedule_ids
            ).update(tax_invoice_issued=True)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'{updated_count}건의 납품이 발행완료로 변경되었습니다.'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_POST
def schedule_move_api(request, pk):
    """일정을 다른 날짜로 이동하는 API"""
    schedule = get_object_or_404(Schedule, pk=pk)
    
    # 권한 체크: 수정 권한이 있는 경우만 이동 가능 (Manager는 읽기 전용)
    if not can_modify_user_data(request.user, schedule.user):
        return JsonResponse({'success': False, 'error': '이 일정을 이동할 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
    
    try:
        # POST 데이터에서 새로운 날짜 정보 가져오기 (FormData 형식)
        new_date = request.POST.get('new_date')  # 'YYYY-MM-DD' 형식
        
        if not new_date:
            return JsonResponse({'success': False, 'error': '새로운 날짜가 제공되지 않았습니다.'}, status=400)
        
        # 날짜 형식 검증 및 변환
        from datetime import datetime
        try:
            new_visit_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': '잘못된 날짜 형식입니다.'}, status=400)
        
        # 일정 날짜 업데이트
        old_date = schedule.visit_date
        schedule.visit_date = new_visit_date
        schedule.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'일정이 {old_date.strftime("%Y년 %m월 %d일")}에서 {new_visit_date.strftime("%Y년 %m월 %d일")}로 이동되었습니다.',
            'old_date': old_date.strftime('%Y-%m-%d'),
            'new_date': new_visit_date.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'일정 이동 중 오류가 발생했습니다: {str(e)}'}, status=500)

@login_required
@require_POST
def schedules_delete_api(request, pk):
    """일정 삭제(JSON). 본인 일정만.

    예전엔 React 가 레거시 템플릿 뷰 `schedule_delete_view` 에 AJAX POST 해서 지웠다
    (서버가 links.deleteSchedule / 목록 deleteHref 로 그 주소를 내려줬음). 레거시 화면을
    은퇴시키면서 같은 동작을 전용 API 로 옮긴다 — 동작은 그대로:
    선결제 차감을 되돌려 잔액·원장을 복구하고, 이 일정에 달린 활동 기록도 함께 지운다.
    중간에 실패하면 잔액만 복구되고 일정은 남는 일이 없도록 한 트랜잭션으로 묶는다.
    """
    schedule = get_object_or_404(Schedule.objects.select_related('followup'), pk=pk)
    if schedule.user_id != request.user.id:
        return JsonResponse({'success': False, 'error': '본인의 일정만 삭제할 수 있습니다.'}, status=403)

    customer_name = (schedule.followup.customer_name if schedule.followup else '') or '고객명 미정'
    schedule_date = schedule.visit_date.strftime('%Y년 %m월 %d일') if schedule.visit_date else ''

    with transaction.atomic():
        for usage in PrepaymentUsage.objects.select_related('prepayment').filter(schedule=schedule):
            prepayment = usage.prepayment
            old_balance = prepayment.balance
            prepayment.balance += usage.amount
            if old_balance == 0 and prepayment.balance > 0:
                prepayment.status = 'active'
            prepayment.save()
            _prepayment_create_ledger(
                prepayment,
                PrepaymentLedgerEntry.ENTRY_RESTORE,
                actor=request.user,
                amount=usage.amount,
                balance_before=old_balance,
                balance_after=prepayment.balance,
                memo=f'일정 삭제로 선결제 차감 복구: {schedule.visit_date}',
                schedule=schedule,
                usage=usage,
            )
        PrepaymentUsage.objects.filter(schedule=schedule).delete()

        related_histories = schedule.histories.all()
        history_count = related_histories.count()
        if history_count:
            related_histories.delete()
        schedule.delete()

    message = f'{customer_name} ({schedule_date}) 일정이 삭제되었습니다.'
    if history_count:
        message += f' (관련 활동 기록 {history_count}개도 함께 삭제되었습니다.)'
    return JsonResponse({'success': True, 'message': message})


@login_required
@require_POST
def schedule_status_update_api(request, schedule_id):
    """일정 상태 업데이트 API"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 상태 변경 가능 (Manager는 읽기 전용)
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({'error': '수정 권한이 없습니다. Manager는 읽기 전용입니다.'}, status=403)
        
        new_status = request.POST.get('status')
        
        if new_status not in ['scheduled', 'completed', 'cancelled']:
            return JsonResponse({'error': '잘못된 상태값입니다.'}, status=400)
        
        # 견적 일정은 완료로 변경 불가 (취소만 가능)
        if schedule.activity_type == 'quote' and new_status == 'completed':
            return JsonResponse({
                'error': '견적 일정은 완료 상태로 변경할 수 없습니다. 견적은 취소만 가능합니다.'
            }, status=400)
        
        old_status = schedule.status
        
        # 취소 처리 시 추가 작업
        if new_status == 'cancelled' and old_status != 'cancelled':
            from reporting.models import DeliveryItem, History
            
            # 1. 납품 품목 기록은 유지 (삭제하지 않음 - 카운팅에서만 제외)
            delivery_items = DeliveryItem.objects.filter(schedule=schedule)
            
            # 2. 관련 납품 히스토리 삭제 (납품 활동 기록)
            delivery_histories = History.objects.filter(schedule=schedule, action_type='delivery')
            delivery_histories_count = delivery_histories.count()
            
            if delivery_histories_count > 0:
                delivery_histories.delete()
        
        schedule.status = new_status
        schedule.save()
        _sync_schedule_pipeline(schedule)
        
        status_display = {
            'scheduled': '예정됨',
            'completed': '완료됨', 
            'cancelled': '취소됨'
        }
        
        response_data = {
            'success': True,
            'new_status': new_status,
            'status_display': status_display[new_status],
            'message': f'일정 상태가 "{status_display[new_status]}"로 변경되었습니다.',
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"❌ 일정 상태 업데이트 오류: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def schedule_add_memo_api(request, schedule_id):
    """일정에 매니저 메모 추가 API"""
    try:
        schedule = get_object_or_404(Schedule, id=schedule_id)
        user_profile = get_user_profile(request.user)
        
        # 권한 체크: 매니저만 메모 추가 가능하고, 해당 실무자의 일정에만 접근 가능
        if not user_profile.is_manager():
            return JsonResponse({'error': '매니저만 메모를 추가할 수 있습니다.'}, status=403)
        
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'error': '이 일정에 접근할 권한이 없습니다.'}, status=403)
        
        memo_content = request.POST.get('memo', '').strip()
        if not memo_content:
            return JsonResponse({'error': '메모 내용을 입력해주세요.'}, status=400)
        
        # 매니저 메모를 히스토리로 생성
        memo_history = History.objects.create(
            followup=schedule.followup,
            department=schedule.department or (schedule.followup.department if schedule.followup else None),
            user=schedule.user,  # 일정의 원래 담당자를 유지
            action_type='memo',
            content=f"[매니저 메모 - {request.user.username}] {memo_content}",  # 매니저 메모 표시 추가
            created_by=request.user,  # 실제 작성자는 매니저
            schedule=schedule
        )
        
        return JsonResponse({
            'success': True,
            'message': '매니저 메모가 추가되었습니다.',
            'memo': {
                'id': memo_history.id,
                'content': memo_history.content,
                'created_at': memo_history.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': request.user.username
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': f'메모 추가 중 오류가 발생했습니다: {str(e)}'}, status=500)

# 자동완성 API 뷰들
@login_required
def company_autocomplete(request):
    """업체/학교명 자동완성 API"""
    import logging
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Admin 사용자는 모든 업체 검색 가능
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        companies = Company.objects.filter(name__icontains=query).order_by('name')[:10]
    else:
        # 일반 사용자: 같은 회사 소속 사용자들이 생성한 업체만 검색 가능
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        
        if user_company:
            # 미들웨어에서 설정한 user_company 사용
            same_company_users = User.objects.filter(userprofile__company=user_company)
            
            companies = Company.objects.filter(
                name__icontains=query,
                created_by__in=same_company_users
            ).order_by('name')[:10]
            
        elif user_profile and user_profile.company:
            # 백업: UserProfile에서 직접 가져오기
            same_company_users = User.objects.filter(userprofile__company=user_profile.company)
            
            companies = Company.objects.filter(
                name__icontains=query,
                created_by__in=same_company_users
            ).order_by('name')[:10]
        else:
            companies = Company.objects.none()
    
    results = []
    for company in companies:
        results.append({
            'id': company.id,
            'text': company.name
        })
    
    return JsonResponse({'results': results})

@login_required
def department_autocomplete(request):
    """부서/연구실명 자동완성 API"""
    import logging
    logger = logging.getLogger(__name__)
    
    query = request.GET.get('q', '').strip()
    company_id = request.GET.get('company') or request.GET.get('company_id')  # 둘 다 지원
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Admin 사용자는 모든 부서 검색 가능
    if getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin'):
        departments = Department.objects.filter(
            Q(name__icontains=query) |
            Q(followup_departments__manager__icontains=query) |
            Q(followup_departments__customer_name__icontains=query) |
            Q(followup_departments__email__icontains=query)
        )
    else:
        # 일반 사용자: 같은 회사 사용자들이 생성한 업체의 부서만 검색
        user_company = getattr(request, 'user_company', None)
        user_profile = getattr(request.user, 'userprofile', None)
        
        if user_company:
            same_company_users = User.objects.filter(userprofile__company=user_company)
            # 같은 회사 사용자들이 생성한 업체의 부서만 필터링
            departments = Department.objects.filter(
                Q(name__icontains=query) |
                Q(followup_departments__manager__icontains=query) |
                Q(followup_departments__customer_name__icontains=query) |
                Q(followup_departments__email__icontains=query),
                company__created_by__in=same_company_users
            )
        elif user_profile and user_profile.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile.company)
            departments = Department.objects.filter(
                Q(name__icontains=query) |
                Q(followup_departments__manager__icontains=query) |
                Q(followup_departments__customer_name__icontains=query) |
                Q(followup_departments__email__icontains=query),
                company__created_by__in=same_company_users
            )
        else:
            departments = Department.objects.none()
    
    # 회사가 선택된 경우 해당 회사의 부서만 필터링
    if company_id:
        departments = departments.filter(company_id=company_id)
    
    departments = departments.select_related('company').distinct().order_by('company__name', 'name')[:10]
    
    results = []
    for dept in departments:
        results.append({
            'id': dept.id,
            'text': f"{dept.company.name} - {dept.name}",
            'company_id': dept.company.id,
            'company_name': dept.company.name,
            'department_name': dept.name
        })
    
    return JsonResponse({'results': results})

@login_required
def followup_autocomplete(request):
    """팔로우업 자동완성 API (일정 생성용 + 고객별 기록 조회용)"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # 같은 회사 사용자들의 고객 모두 검색 가능
    same_company_users = get_same_company_users(request.user)
    
    # 검색어로 필터링 (고객명, 업체명, 부서명, 책임자명으로 검색)
    followups = FollowUp.objects.filter(user__in=same_company_users).filter(
        Q(customer_name__icontains=query) |
        Q(company__name__icontains=query) |
        Q(department__name__icontains=query) |
        Q(manager__icontains=query)
    ).select_related('company', 'department', 'user').order_by('company__name', 'customer_name')[:15]
    
    results = []
    for followup in followups:
        # 표시 텍스트 구성
        company_name = str(followup.company) if followup.company else '업체명 미정'
        department_name = str(followup.department) if followup.department else '부서명 미정'
        customer_name = followup.customer_name or '고객명 미정'
        manager_name = followup.user.get_full_name() or followup.user.username
        
        display_text = f"{company_name} - {department_name} | {customer_name}"
        
        # 동료 고객인 경우 담당자 표시
        if followup.user != request.user:
            display_text += f" ({manager_name})"
        
        results.append({
            'id': followup.id,
            'text': display_text,
            'customer_name': customer_name,
            'company': company_name,
            'email': followup.email or '',
            'manager': manager_name
        })
    
    return JsonResponse({'results': results})

@login_required
def schedule_activity_type(request):
    """일정의 activity_type을 반환하는 API"""
    schedule_id = request.GET.get('schedule_id')
    if schedule_id:
        try:
            schedule = Schedule.objects.get(id=schedule_id, user=request.user)
            # 일정의 activity_type을 히스토리의 action_type으로 매핑
            activity_mapping = {
                'customer_meeting': 'customer_meeting',
                'delivery': 'delivery_schedule',
                'service': 'service',
            }
            mapped_action = activity_mapping.get(schedule.activity_type, 'customer_meeting')
            return JsonResponse({
                'success': True,
                'activity_type': schedule.activity_type,
                'mapped_action_type': mapped_action
            })
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'error': '일정을 찾을 수 없습니다.'})
    
    return JsonResponse({'success': False, 'error': '일정 ID가 필요합니다.'})

@login_required
@require_POST
def company_create_api(request):
    """새 업체/학교 생성 API"""
    try:
        user_profile = get_user_profile(request.user)
        if user_profile.is_manager():
            return JsonResponse({
                'success': False,
                'error': '권한이 없습니다. Manager는 데이터를 생성할 수 없습니다.',
            }, status=403)

        name = request.POST.get('name', '').strip()
        
        if not name:
            return JsonResponse({'error': '업체/학교명을 입력해주세요.'}, status=400)
        
        # 중복 체크 - 같은 회사 내에서만
        user_profile_obj = getattr(request.user, 'userprofile', None)
        if user_profile_obj and user_profile_obj.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
            if Company.objects.filter(name=name, created_by__in=same_company_users).exists():
                return JsonResponse({'error': '이미 존재하는 업체/학교명입니다.'}, status=400)
        
        company = Company.objects.create(name=name, created_by=request.user)
        
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name
            },
            'message': f'"{name}" 업체/학교가 추가되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"업체 생성 오류: {str(e)} (user={request.user.username})", exc_info=True)
        return JsonResponse({'error': f'업체/학교 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)

@login_required
@require_POST
def department_create_api(request):
    """새 부서/연구실 생성 API"""
    user_profile = get_user_profile(request.user)
    if user_profile.is_manager():
        return JsonResponse({
            'success': False,
            'error': '권한이 없습니다. Manager는 데이터를 생성할 수 없습니다.',
        }, status=403)

    name = request.POST.get('name', '').strip()
    company_id = request.POST.get('company_id')
    
    if not name:
        return JsonResponse({'error': '부서/연구실명을 입력해주세요.'}, status=400)
    
    if not company_id:
        return JsonResponse({'error': '업체/학교를 먼저 선택해주세요.'}, status=400)
    
    try:
        company = Company.objects.get(id=company_id)
        is_admin = getattr(request, 'is_admin', False) or user_profile.is_admin()
        if not is_admin:
            if user_profile.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile.company)
                if company.created_by not in same_company_users:
                    return JsonResponse({'error': '접근 권한이 없는 업체입니다.'}, status=403)
            else:
                return JsonResponse({'error': '회사 정보가 없어 부서를 생성할 수 없습니다.'}, status=403)
        
        # 중복 체크
        if Department.objects.filter(company=company, name=name).exists():
            return JsonResponse({'error': f'{company.name}에 이미 존재하는 부서/연구실명입니다.'}, status=400)
        
        department = Department.objects.create(company=company, name=name, created_by=request.user)
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'company_id': company.id,
                'company_name': company.name
            },
            'message': f'"{company.name} - {name}" 부서/연구실이 추가되었습니다.'
        })
        
    except Company.DoesNotExist:
        return JsonResponse({'error': '존재하지 않는 업체/학교입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'부서/연구실 생성 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
@require_POST
def company_update_api(request, company_id):
    """React 고객 화면용 업체/학교 수정 API."""
    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'error': '존재하지 않는 업체/학교입니다.'}, status=404)

    if not _can_manage_customer_company(request.user, company):
        return JsonResponse({'success': False, 'error': '이 업체/학교를 수정할 권한이 없습니다.'}, status=403)

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': '업체/학교명을 입력해주세요.'}, status=400)
    if Company.objects.filter(name=name).exclude(pk=company.pk).exists():
        return JsonResponse({'success': False, 'error': '이미 존재하는 업체/학교명입니다.'}, status=400)

    company.name = name
    company.save(update_fields=['name', 'updated_at'])
    return JsonResponse({
        'success': True,
        'company': {
            'id': company.id,
            'name': company.name,
        },
        'message': f'"{company.name}" 업체/학교 정보가 수정되었습니다.',
    })


@login_required
@require_POST
def company_delete_api(request, company_id):
    """React 고객 화면용 업체/학교 삭제 API."""
    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        return JsonResponse({'success': False, 'error': '존재하지 않는 업체/학교입니다.'}, status=404)

    if not _can_manage_customer_company(request.user, company):
        return JsonResponse({'success': False, 'error': '이 업체/학교를 삭제할 권한이 없습니다.'}, status=403)

    delete_message = _customer_delete_message(_company_delete_blockers(company))
    if delete_message:
        return JsonResponse({'success': False, 'error': delete_message}, status=400)

    company_name = company.name
    company.delete()
    return JsonResponse({
        'success': True,
        'message': f'"{company_name}" 업체/학교가 삭제되었습니다.',
    })


@login_required
@require_POST
def department_update_api(request, department_id):
    """React 고객 화면용 부서/연구실 수정 API."""
    try:
        department = Department.objects.select_related('company').get(pk=department_id)
    except Department.DoesNotExist:
        return JsonResponse({'success': False, 'error': '존재하지 않는 부서/연구실입니다.'}, status=404)

    if not _can_manage_customer_department(request.user, department):
        return JsonResponse({'success': False, 'error': '이 부서/연구실을 수정할 권한이 없습니다.'}, status=403)

    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': '부서/연구실명을 입력해주세요.'}, status=400)

    target_company_id = (
        request.POST.get('company_id')
        or request.POST.get('companyId')
        or request.POST.get('company')
        or str(department.company_id)
    )
    try:
        target_company = Company.objects.get(pk=target_company_id)
    except (Company.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': '이동할 업체/학교가 존재하지 않습니다.'}, status=400)

    if not _can_manage_customer_company(request.user, target_company):
        return JsonResponse({'success': False, 'error': '이 업체/학교로 부서/연구실을 이동할 권한이 없습니다.'}, status=403)

    if Department.objects.filter(company=target_company, name=name).exclude(pk=department.pk).exists():
        return JsonResponse({'success': False, 'error': f'{target_company.name}에 이미 존재하는 부서/연구실명입니다.'}, status=400)

    old_company_id = department.company_id
    old_company_name = department.company.name
    moved = old_company_id != target_company.id
    related_counts = {
        'followups': 0,
        'assets': 0,
        'prepayments': 0,
    }

    with transaction.atomic():
        department.company = target_company
        department.name = name
        department.save(update_fields=['company', 'name', 'updated_at'])
        if moved:
            now = timezone.now()
            related_counts['followups'] = FollowUp.objects.filter(
                department=department,
            ).exclude(company=target_company).update(company=target_company, updated_at=now)
            related_counts['assets'] = CustomerAsset.objects.filter(
                department=department,
            ).exclude(company=target_company).update(company=target_company, updated_at=now)
            related_counts['prepayments'] = Prepayment.objects.filter(
                _prepayment_department_filter(department),
            ).exclude(company=target_company).update(company=target_company)

    message = f'"{department.company.name} - {department.name}" 부서/연구실 정보가 수정되었습니다.'
    if moved:
        message = (
            f'"{department.name}" 부서/연구실을 "{old_company_name}"에서 '
            f'"{target_company.name}"로 이동했습니다.'
        )
    return JsonResponse({
        'success': True,
        'department': {
            'id': department.id,
            'name': department.name,
            'company_id': department.company_id,
            'company_name': department.company.name,
            'companyId': department.company_id,
            'companyName': department.company.name,
            'moved': moved,
            'previous_company_id': old_company_id,
            'previous_company_name': old_company_name,
            'updated_counts': related_counts,
        },
        'message': message,
    })


@login_required
@require_POST
def department_delete_api(request, department_id):
    """React 고객 화면용 부서/연구실 삭제 API."""
    try:
        department = Department.objects.select_related('company').get(pk=department_id)
    except Department.DoesNotExist:
        return JsonResponse({'success': False, 'error': '존재하지 않는 부서/연구실입니다.'}, status=404)

    if not _can_manage_customer_department(request.user, department):
        return JsonResponse({'success': False, 'error': '이 부서/연구실을 삭제할 권한이 없습니다.'}, status=403)

    delete_message = _customer_delete_message(_department_delete_blockers(department))
    if delete_message:
        return JsonResponse({'success': False, 'error': delete_message}, status=400)

    department_label = f'{department.company.name} - {department.name}'
    department.delete()
    return JsonResponse({
        'success': True,
        'message': f'"{department_label}" 부서/연구실이 삭제되었습니다.',
    })


# ============ 업체/부서 관리 뷰들 ============


# ============ 매니저용 읽기 전용 업체/부서 뷰들 ============


# ============ 추가 API 엔드포인트들 ============

@login_required
def api_company_detail(request, pk):
    """개별 회사 정보 조회 API"""
    try:
        company = get_object_or_404(Company, pk=pk)
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required  
def api_department_detail(request, pk):
    """개별 부서 정보 조회 API"""
    try:
        department = get_object_or_404(Department, pk=pk)
        return JsonResponse({
            'success': True,
            'department': {
                'id': department.id,
                'name': department.name,
                'company_id': department.company.id,
                'company_name': department.company.name
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def history_detail_api(request, history_id):
    """히스토리 상세 정보를 JSON으로 반환하는 API"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 조회 권한 확인 (같은 회사면 조회 가능)
        if history.followup and not can_access_followup(request.user, history.followup):
            return JsonResponse({
                'success': False,
                'error': '이 기록에 접근할 권한이 없습니다.'
            }, status=403)
        
        # 수정 권한 여부도 함께 전달
        can_modify = can_modify_user_data(request.user, history.user)
        
        # 히스토리 데이터 직렬화
        history_data = {
            'id': history.id,
            'content': history.content or '',
            'action_type': history.action_type,
            'action_type_display': history.get_action_type_display(),
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': history.user.get_full_name() or history.user.username,
            'created_by': history.created_by.username if history.created_by else '',
            'can_modify': can_modify,  # 수정 권한 정보 추가
            'followup_id': history.followup.id if history.followup else None,
            'schedule_id': history.schedule.id if history.schedule else None,
            
            # 납품 일정 관련 필드
            'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
            'delivery_amount': history.delivery_amount,
            'delivery_items': history.delivery_items or '',
            'tax_invoice_issued': history.tax_invoice_issued,
            
            # 고객 미팅 관련 필드
            'meeting_date': history.meeting_date.strftime('%Y-%m-%d') if history.meeting_date else '',
            'meeting_situation': history.meeting_situation or '',
            'meeting_researcher_quote': history.meeting_researcher_quote or '',
            'meeting_confirmed_facts': history.meeting_confirmed_facts or '',
            'meeting_obstacles': history.meeting_obstacles or '',
            'meeting_next_action': history.meeting_next_action or '',
            
            # 서비스 관련 필드
            'service_status': history.service_status or '',
            'service_status_display': history.get_service_status_display() if history.service_status else '',
            
            # 첨부파일 정보
            'files': []
        }
        
        # 첨부파일 정보 추가
        for file in history.files.all():
            # 파일 크기를 읽기 쉬운 형태로 변환
            file_size = file.file_size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size/1024:.1f} KB"
            else:
                size_str = f"{file_size/(1024*1024):.1f} MB"
            
            history_data['files'].append({
                'id': file.id,
                'filename': file.original_filename,
                'size': size_str,
                'uploaded_at': file.uploaded_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'히스토리 정보를 불러올 수 없습니다: {str(e)}'
        })

@login_required
@require_POST
def history_update_api(request, history_id):
    """히스토리 업데이트 API"""
    try:
        history = get_object_or_404(History, id=history_id)
        
        # 수정 권한 확인 (본인 데이터만 수정 가능, Manager는 읽기 전용)
        if not can_modify_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '이 기록을 수정할 권한이 없습니다. 본인의 기록만 수정할 수 있습니다.'
            }, status=403)
        
        # 폼 데이터 처리
        content = request.POST.get('content', '').strip()
        
        # 고객 미팅이 아닌 경우 content 필수
        if history.action_type != 'customer_meeting' and not content:
            return JsonResponse({
                'success': False,
                'error': '활동 내용을 입력해주세요.'
            })
        
        # 기본 필드 업데이트
        history.content = content
        
        # 활동 유형별 추가 필드 처리
        if history.action_type == 'delivery_schedule':
            delivery_date = request.POST.get('delivery_date')
            if delivery_date:
                try:
                    from datetime import datetime
                    history.delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
                except ValueError:
                    history.delivery_date = None
            else:
                history.delivery_date = None
            
            delivery_amount = request.POST.get('delivery_amount')
            if delivery_amount:
                try:
                    history.delivery_amount = int(delivery_amount)
                except (ValueError, TypeError):
                    history.delivery_amount = None
            else:
                history.delivery_amount = None
            
            history.delivery_items = request.POST.get('delivery_items', '').strip()
            
        elif history.action_type == 'customer_meeting':
            meeting_date = request.POST.get('meeting_date')
            if meeting_date:
                try:
                    from datetime import datetime
                    history.meeting_date = datetime.strptime(meeting_date, '%Y-%m-%d').date()
                except ValueError:
                    history.meeting_date = None
            else:
                history.meeting_date = None
            
            # 구조화된 미팅 노트 필드 저장
            history.meeting_situation = request.POST.get('meeting_situation', '').strip()
            history.meeting_researcher_quote = request.POST.get('meeting_researcher_quote', '').strip()
            history.meeting_confirmed_facts = request.POST.get('meeting_confirmed_facts', '').strip()
            history.meeting_obstacles = request.POST.get('meeting_obstacles', '').strip()
            history.meeting_next_action = request.POST.get('meeting_next_action', '').strip()
                
        elif history.action_type == 'service':
            history.service_status = request.POST.get('service_status', '')
        
        # 변경사항 저장
        history.save()

        # 기존 파일 삭제 처리
        delete_file_ids = request.POST.getlist('delete_files')
        if delete_file_ids:
            try:
                # 삭제할 파일들 조회 및 삭제
                files_to_delete = HistoryFile.objects.filter(
                    id__in=delete_file_ids,
                    history=history
                )
                for file_obj in files_to_delete:
                    # 실제 파일 삭제
                    if file_obj.file and os.path.exists(file_obj.file.path):
                        os.remove(file_obj.file.path)
                    # DB에서 삭제
                    file_obj.delete()
                    
            except Exception as delete_error:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 삭제 중 오류가 발생했습니다: {str(delete_error)}'
                })
        
        # 새로운 파일 첨부 처리
        uploaded_files = request.FILES.getlist('files')
        if uploaded_files:
            try:
                # 현재 파일 개수 확인 (삭제 후)
                current_file_count = history.files.count()
                total_files_after_upload = current_file_count + len(uploaded_files)
                
                # 파일 개수 제한 (최대 5개)
                if total_files_after_upload > 5:
                    return JsonResponse({
                        'success': False,
                        'error': f'파일은 최대 5개까지만 첨부할 수 있습니다. (현재 {current_file_count}개, 추가 {len(uploaded_files)}개)'
                    })
                
                # 각 파일 유효성 검사 및 저장
                for file in uploaded_files:
                    # 파일 크기 검사 (10MB)
                    if file.size > 10 * 1024 * 1024:
                        return JsonResponse({
                            'success': False,
                            'error': f'파일 {file.name}이 10MB를 초과합니다.'
                        })
                    
                    # 파일 확장자 검사
                    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar']
                    file_extension = os.path.splitext(file.name)[1].lower()
                    if file_extension not in allowed_extensions:
                        return JsonResponse({
                            'success': False,
                            'error': f'파일 {file.name}은 지원되지 않는 형식입니다.'
                        })
                    
                    # 파일 저장
                    history_file = HistoryFile.objects.create(
                        history=history,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        uploaded_by=request.user
                    )
                    
            except Exception as file_error:
                return JsonResponse({
                    'success': False,
                    'error': f'파일 업로드 중 오류가 발생했습니다: {str(file_error)}'
                })
        
        return JsonResponse({
            'success': True,
            'message': '활동 기록이 성공적으로 수정되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'활동 기록 수정 중 오류가 발생했습니다: {str(e)}'
        })

# ============ 메모 관련 뷰들 ============


# ============ 인라인 메모 편집 API ============

@login_required
@require_POST
def history_update_tax_invoice(request, pk):
    """세금계산서 발행 상태 업데이트"""
    return _receivables_only_response()

    try:
        history = get_object_or_404(History, pk=pk)
        
        # 권한 체크
        if not can_modify_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '수정 권한이 없습니다.'
            })
        
        # 납품 일정 타입만 세금계산서 상태 변경 가능
        if history.action_type != 'delivery_schedule':
            return JsonResponse({
                'success': False,
                'error': '납품 일정만 세금계산서 상태를 변경할 수 있습니다.'
            })
        
        # 세금계산서 상태 업데이트
        tax_invoice_issued = request.POST.get('tax_invoice_issued') == 'true'
        history.tax_invoice_issued = tax_invoice_issued
        history.save()
        
        # 연결된 스케줄이 있는 경우 스케줄의 납품 품목과 동기화
        if history.schedule:
            try:
                # 연결된 스케줄의 모든 납품 품목 업데이트
                delivery_items = history.schedule.delivery_items_set.all()
                if delivery_items.exists():
                    delivery_items.update(tax_invoice_issued=tax_invoice_issued)
                
                # 연결된 스케줄에 속한 다른 히스토리들도 함께 업데이트
                related_histories = History.objects.filter(
                    schedule=history.schedule, 
                    action_type='delivery_schedule'
                ).exclude(id=history.id)
                
                if related_histories.exists():
                    related_histories.update(tax_invoice_issued=tax_invoice_issued)
                    
            except Exception as sync_error:
                logger.error(f"연결된 스케줄/히스토리 세금계산서 동기화 실패: {sync_error}")
        
        # sync_schedule 파라미터는 향후 확장용으로 유지
        sync_schedule = request.POST.get('sync_schedule') == 'true'
        
        # silent 모드인 경우 (자동 동기화) 별도 메시지
        is_silent = request.POST.get('silent') == 'true'
        if is_silent:
            message = '세금계산서 상태가 자동으로 동기화되었습니다.'
        else:
            message = '세금계산서 상태가 성공적으로 변경되었습니다.'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'세금계산서 상태 변경 중 오류가 발생했습니다: {str(e)}'
        })

@login_required
@require_POST
def history_update_memo(request, pk):
    """AJAX 요청으로 메모 내용 업데이트"""
    import json
    
    try:
        history = get_object_or_404(History, pk=pk, action_type='memo')
        
        # 권한 체크
        if not can_modify_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '메모 수정 권한이 없습니다.'
            })
        
        # 요청 데이터 파싱
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({
                'success': False,
                'error': '메모 내용을 입력해주세요.'
            })
        
        # 메모 내용 업데이트
        history.content = new_content
        history.save()
        
        return JsonResponse({
            'success': True,
            'message': '메모가 성공적으로 수정되었습니다.'
        })
        
    except History.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '메모를 찾을 수 없습니다.'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '잘못된 요청 형식입니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'메모 수정 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
def followup_excel_download(request):
    """팔로우업 전체 정보 엑셀 다운로드 (부서별 그룹화)"""
    user_profile = get_user_profile(request.user)
    
    # 엑셀 다운로드 권한 체크
    if not user_profile.can_excel_download():
        messages.error(request, '엑셀 다운로드 권한이 없습니다. 관리자에게 문의해주세요.')
        return redirect('reporting:followup_list')
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from decimal import Decimal
    from collections import defaultdict
    import io
    from datetime import datetime
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링 (기존 로직과 동일)
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user, request)
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related(
            'user', 'company', 'department'
        ).prefetch_related('schedules', 'histories')
    else:
        accessible_users = User.objects.filter(id=request.user.id)
        followups = FollowUp.objects.filter(user=request.user).select_related(
            'user', 'company', 'department'
        ).prefetch_related('schedules', 'histories')

    followups = _apply_customer_followup_filters(
        followups,
        _customer_request_filters(request),
        scope_users=accessible_users,
    )
    
    # 우선순위 정렬을 위한 순서 정의 (낮을수록 높은 우선순위)
    PRIORITY_ORDER = {
        'urgent': 1,      # 긴급 - 가장 높음
        'followup': 2,    # 팔로업
        'scheduled': 3,   # 예정
        'long_term': 4,   # 장기 - 가장 낮음
    }
    
    # 부서별로 그룹화
    departments_data = defaultdict(lambda: {
        'company_name': '',
        'department_name': '',
        'followups': [],
        'highest_priority': 99  # 부서 내 가장 높은 우선순위 (낮은 숫자가 높은 우선순위)
    })
    
    for followup in followups.order_by('company__name', 'department__name', 'customer_name'):
        company_name = followup.company.name if followup.company else '업체 미지정'
        department_name = followup.department.name if followup.department else '부서 미지정'
        dept_key = f"{company_name}||{department_name}"
        
        departments_data[dept_key]['company_name'] = company_name
        departments_data[dept_key]['department_name'] = department_name
        departments_data[dept_key]['followups'].append(followup)
        
        # 해당 부서 내 가장 높은 우선순위 업데이트
        priority_value = PRIORITY_ORDER.get(followup.priority, 99)
        if priority_value < departments_data[dept_key]['highest_priority']:
            departments_data[dept_key]['highest_priority'] = priority_value
    
    # 엑셀 파일 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "팔로우업 전체 정보"
    
    # 스타일 정의
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5F8F", end_color="2F5F8F", fill_type="solid")
    dept_header_font = Font(bold=True, color="FFFFFF", size=12)
    dept_header_fill = PatternFill(start_color="4A7C4E", end_color="4A7C4E", fill_type="solid")  # 녹색 계열
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    wrap_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    
    # 최대 히스토리 개수 계산
    max_histories = 0
    for followup in followups:
        history_count = followup.histories.count()
        max_histories = max(max_histories, history_count)
    
    # 헤더 정의
    headers = [
        '고객명', '책임자', '핸드폰 번호', 
        '메일 주소', '상세 주소', '고객 등급', '납품 품목', '총 납품 금액', '상세 내용'
    ]
    
    # 히스토리 컬럼 추가
    for i in range(1, max_histories + 1):
        headers.append(f'관련 활동 히스토리 {i}')
    
    current_row = 1
    
    # 부서별로 데이터 작성 (우선순위 높은 부서가 먼저, 그 다음 회사명/부서명 순)
    sorted_dept_keys = sorted(
        departments_data.keys(),
        key=lambda k: (departments_data[k]['highest_priority'], departments_data[k]['company_name'], departments_data[k]['department_name'])
    )
    
    for dept_key in sorted_dept_keys:
        dept_info = departments_data[dept_key]
        company_name = dept_info['company_name']
        department_name = dept_info['department_name']
        dept_followups = dept_info['followups']
        
        # 부서 구분 행 (회사명 - 부서명)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers))
        dept_cell = ws.cell(row=current_row, column=1, value=f"📁 {company_name} - {department_name} ({len(dept_followups)}명)")
        dept_cell.font = dept_header_font
        dept_cell.fill = dept_header_fill
        dept_cell.alignment = center_alignment
        dept_cell.border = border
        current_row += 1
        
        # 헤더 행
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_alignment
        current_row += 1
        
        # 해당 부서의 고객 데이터 입력
        for followup in dept_followups:
            # 책임자 정보 가져오기 (FollowUp 모델의 manager 필드)
            manager_name = followup.manager or ''
            
            # 고객 등급 (우선순위)
            priority_display = followup.get_priority_display() or '보통'
            
            # 납품 관련 정보 집계
            delivery_histories = followup.histories.filter(action_type='delivery_schedule')
            
            # 납품 품목별 수량 집계용 딕셔너리
            item_quantities = {}
            total_delivery_amount = 0
            
            # 중복 방지를 위해 처리된 Schedule ID들을 추적
            processed_schedule_ids = set()
            
            for history in delivery_histories:
                # 납품 금액 집계 - History 우선
                if history.delivery_amount:
                    total_delivery_amount += history.delivery_amount
                
                # History에 실제 납품 품목 정보가 있는 경우만 Schedule ID 기록
                # (품목 정보가 없으면 Schedule에서 가져와야 함)
                if history.schedule_id and history.delivery_items:
                    processed_schedule_ids.add(history.schedule_id)
                
                # 납품 품목 집계 - History 텍스트에서만 처리 (Schedule DeliveryItem은 나중에 별도 처리)
                if history.delivery_items:
                    # 다양한 줄바꿈 문자 처리
                    processed_items = history.delivery_items
                    processed_items = processed_items.replace('\\n', '\n')
                    processed_items = processed_items.replace('\\r\\n', '\n')
                    processed_items = processed_items.replace('\\r', '\n')
                    processed_items = processed_items.replace('\r\n', '\n')
                    processed_items = processed_items.replace('\r', '\n')
                    processed_items = processed_items.strip()
                    
                    # 다양한 구분자로 분할 시도
                    lines = []
                    # 먼저 줄바꿈으로 분할
                    for line in processed_items.split('\n'):
                        line = line.strip()
                        if line:
                            # 쉼표로도 분할해보기
                            if ',' in line and ':' in line:
                                sub_lines = [sub.strip() for sub in line.split(',') if sub.strip()]
                                lines.extend(sub_lines)
                            else:
                                lines.append(line)
                
                    for line in lines:
                        # 다양한 패턴 시도
                        import re
                        
                        # 패턴 1: "품목명: 수량개 금액원 횟수회" 또는 "품목명 수량개 금액원 횟수회"
                        pattern1 = r'(.+?)[\s:]*([\d,]+)개[\s,]*([\d,]+)원[\s,]*([\d]+)회'
                        match1 = re.search(pattern1, line)
                        
                        if match1:
                            item_name = match1.group(1).replace(':', '').strip()
                            quantity = float(match1.group(2).replace(',', ''))
                            
                            if item_name in item_quantities:
                                item_quantities[item_name] += quantity
                            else:
                                item_quantities[item_name] = quantity
                            continue
                        
                        # 패턴 2: "품목명: 수량개" 또는 "품목명 수량개"
                        pattern2 = r'(.+?)[\s:]*([\d,]+(?:\.\d+)?)개'
                        match2 = re.search(pattern2, line)
                        
                        if match2:
                            item_name = match2.group(1).replace(':', '').strip()
                            quantity = float(match2.group(2).replace(',', ''))
                            
                            if item_name in item_quantities:
                                item_quantities[item_name] += quantity
                            else:
                                item_quantities[item_name] = quantity
                            continue
                        
                        # 패턴 3: 단순 품목명만 있는 경우
                        if line and not any(char in line for char in [':', '개', '원', '회']):
                            item_name = line.strip()
                            
                            if item_name in item_quantities:
                                item_quantities[item_name] += 1
                            else:
                                item_quantities[item_name] = 1
            
            # Schedule 기반 DeliveryItem도 포함 (모든 Schedule 처리)
            all_schedule_deliveries = followup.schedules.filter(
                activity_type='delivery',
                delivery_items_set__isnull=False,
            ).distinct()
            
            # 모든 Schedule 처리 (History에 품목 정보가 없으면 Schedule에서 가져옴)
            for schedule in all_schedule_deliveries:
                # History에서 이미 품목 정보를 처리한 Schedule은 금액만 확인
                if schedule.id in processed_schedule_ids:
                    # 금액만 추가 확인 (History에 없었을 수 있음)
                    schedule_total = 0
                    for item in schedule.delivery_items_set.all():
                        if item.total_price:
                            schedule_total += Decimal(str(item.total_price))
                    
                    if schedule_total > 0:
                        total_delivery_amount += schedule_total
                    continue
                
                # Schedule별 총액 계산 및 품목 집계
                schedule_total = 0
                schedule_items = []
                
                for item in schedule.delivery_items_set.all():
                    # Schedule 기반 품목의 금액 포함
                    if item.total_price:
                        schedule_total += Decimal(str(item.total_price))
                    
                    # 품목 정보 저장
                    schedule_items.append({
                        'name': item.item_name,
                        'quantity': float(item.quantity)
                    })
                
                # Schedule 총액을 전체 납품 금액에 추가 (이미 processed된 경우 위에서 처리됨)
                if schedule.id not in processed_schedule_ids and schedule_total > 0:
                    total_delivery_amount += schedule_total
                
                # Schedule 품목 집계 (모든 Schedule에서)
                for item_info in schedule_items:
                    item_name = item_info['name']
                    quantity = item_info['quantity']
                    
                    # 품목별 수량 누적 (원본 이름 그대로 사용)
                    if item_name in item_quantities:
                        item_quantities[item_name] += quantity
                    else:
                        item_quantities[item_name] = quantity

            
            # 품목 텍스트 생성 (품목명과 총 수량 표시)
            if item_quantities:
                items_list = []
                for item_name, total_qty in sorted(item_quantities.items()):
                    # 소수점이 있으면 그대로, 정수면 정수로 표시
                    if total_qty == int(total_qty):
                        qty_str = str(int(total_qty))
                    else:
                        qty_str = str(total_qty)
                    items_list.append(f"{item_name}: {qty_str}개")
                
                # 모든 품목 표시 (제한 제거)
                items_text = ', '.join(items_list)
            else:
                items_text = '납품 기록 없음'
            
            # 기본 정보 (부서별 그룹화이므로 업체/부서 컬럼 제외)
            data = [
                followup.customer_name or '',
                manager_name,  # FollowUp의 책임자 필드에서 가져오기
                followup.phone_number or '',
                followup.email or '',
                followup.address or '',
                priority_display,  # 고객 등급
                items_text,  # 납품 품목
                f"{total_delivery_amount:,}원" if total_delivery_amount > 0 else '납품 기록 없음',  # 총 납품 금액
                followup.notes or ''
            ]
            
            # 히스토리 정보 추가
            histories = list(followup.histories.all().order_by('-created_at'))
            for i in range(max_histories):
                if i < len(histories):
                    history = histories[i]
                    history_text = f"[{history.created_at.strftime('%Y-%m-%d')}] {history.get_action_type_display()}: {history.content or ''}"
                    data.append(history_text)
                else:
                    data.append('')
            
            # 데이터 셀에 값 입력 및 스타일 적용
            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=current_row, column=col_num, value=value)
                cell.border = border
                cell.alignment = wrap_alignment
            current_row += 1
        
        # 부서 사이에 빈 행 추가
        current_row += 1
    
    # 컬럼 너비 자동 조정 (부서별 그룹화에 맞게 수정)
    column_widths = {
        1: 15,   # 고객명
        2: 12,   # 책임자
        3: 15,   # 핸드폰 번호
        4: 25,   # 메일 주소
        5: 30,   # 상세 주소
        6: 10,   # 고객 등급
        7: 60,   # 납품 품목 (더 넓게 - 모든 품목 표시를 위해)
        8: 15,   # 총 납품 금액
        9: 30,   # 상세 내용
    }
    
    for column in ws.columns:
        column_letter = get_column_letter(column[0].column)
        col_num = column[0].column
        
        # 미리 정의된 너비가 있으면 사용
        if col_num in column_widths:
            ws.column_dimensions[column_letter].width = column_widths[col_num]
        else:
            # 히스토리 컬럼들에 대한 자동 조정
            max_length = 0
            for cell in column:
                try:
                    cell_value = str(cell.value) if cell.value is not None else ''
                    # 한글과 영문의 너비 차이를 고려
                    korean_chars = len([c for c in cell_value if ord(c) > 127])
                    english_chars = len(cell_value) - korean_chars
                    adjusted_length = korean_chars * 2 + english_chars
                    
                    if adjusted_length > max_length:
                        max_length = adjusted_length
                except:
                    pass
            
            # 히스토리 컬럼은 최소 20, 최대 50으로 제한
            adjusted_width = min(max(max_length + 3, 20), 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # 응답 생성
    today = datetime.now().strftime('%Y%m%d')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"팔로우업_전체정보_부서별_{today}.xlsx"
    
    # 한글 파일명을 올바르게 인코딩
    from urllib.parse import quote
    encoded_filename = quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    
    # 엑셀 파일을 메모리에서 저장
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    response.write(excel_file.getvalue())
    
    return response


@login_required
def followup_basic_excel_download(request):
    """팔로우업 기본 정보 엑셀 다운로드 (권한 체크)"""
    user_profile = get_user_profile(request.user)
    
    # 엑셀 다운로드 권한 체크
    if not user_profile.can_excel_download():
        messages.error(request, '엑셀 다운로드 권한이 없습니다. 관리자에게 문의해주세요.')
        return redirect('reporting:followup_list')
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    import io
    from datetime import datetime
    
    user_profile = get_user_profile(request.user)
    
    # 권한에 따른 데이터 필터링 (기존 로직과 동일)
    if user_profile.can_view_all_users():
        accessible_users = get_accessible_users(request.user, request)
        followups = FollowUp.objects.filter(user__in=accessible_users).select_related(
            'user', 'company', 'department'
        )
    else:
        accessible_users = User.objects.filter(id=request.user.id)
        followups = FollowUp.objects.filter(user=request.user).select_related(
            'user', 'company', 'department'
        )

    followups = _apply_customer_followup_filters(
        followups,
        _customer_request_filters(request),
        scope_users=accessible_users,
    )
    
    # 엑셀 파일 생성
    wb = Workbook()
    ws = wb.active
    ws.title = "팔로우업 기본 정보"
    
    # 스타일 정의
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5F8F", end_color="2F5F8F", fill_type="solid")
    department_fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    
    # 헤더 생성 (업체/부서는 그룹 구분행에 표시)
    headers = ['고객명', '책임자', '핸드폰 번호', '메일 주소']
    
    # 헤더 스타일 적용
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = center_alignment
    
    # 우선순위 정렬을 위한 순서 정의 (낮을수록 높은 우선순위)
    PRIORITY_ORDER = {
        'urgent': 1,      # 긴급 - 가장 높음
        'followup': 2,    # 팔로업
        'scheduled': 3,   # 예정
        'long_term': 4,   # 장기 - 가장 낮음
    }
    
    # 부서별로 그룹화
    from collections import defaultdict
    department_groups = defaultdict(lambda: {'followups': [], 'highest_priority': 99})
    for followup in followups:
        company_name = followup.company.name if followup.company else '미지정 업체'
        department_name = followup.department.name if followup.department else '미지정 부서'
        group_key = f"{company_name} / {department_name}"
        department_groups[group_key]['followups'].append(followup)
        
        # 해당 부서 내 가장 높은 우선순위 업데이트
        priority_value = PRIORITY_ORDER.get(followup.priority, 99)
        if priority_value < department_groups[group_key]['highest_priority']:
            department_groups[group_key]['highest_priority'] = priority_value
    
    # 데이터 입력 (우선순위 높은 부서가 먼저, 그 다음 회사명/부서명 순)
    sorted_groups = sorted(
        department_groups.items(),
        key=lambda x: (x[1]['highest_priority'], x[0])
    )
    
    current_row = 2
    for group_key, group_data in sorted_groups:
        group_followups = group_data['followups']
        # 부서 구분 행 추가
        cell = ws.cell(row=current_row, column=1, value=group_key)
        cell.font = Font(bold=True)
        cell.fill = department_fill
        cell.border = border
        cell.alignment = left_alignment
        
        # 나머지 열도 스타일 적용 및 병합
        for col in range(2, 5):
            cell = ws.cell(row=current_row, column=col, value='')
            cell.fill = department_fill
            cell.border = border
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
        current_row += 1
        
        # 해당 부서의 팔로우업 데이터 입력
        for followup in group_followups:
            manager_name = followup.manager or ''
            
            data = [
                followup.customer_name or '',
                manager_name,
                followup.phone_number or '',
                followup.email or ''
            ]
            
            # 데이터 셀에 값 입력 및 스타일 적용
            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=current_row, column=col_num, value=value)
                cell.border = border
                cell.alignment = left_alignment
            
            current_row += 1
    
    # 컬럼 너비 자동 조정 (개선된 버전)
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                cell_value = str(cell.value) if cell.value is not None else ''
                # 한글과 영문의 너비 차이를 고려
                korean_chars = len([c for c in cell_value if ord(c) > 127])
                english_chars = len(cell_value) - korean_chars
                adjusted_length = korean_chars * 2 + english_chars
                
                if adjusted_length > max_length:
                    max_length = adjusted_length
            except:
                pass
        
        # 최소 8, 최대 50 문자로 제한하고, 여유분 추가
        adjusted_width = min(max(max_length + 3, 8), 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # 응답 생성
    today = datetime.now().strftime('%Y%m%d')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"기본정보_{today}.xlsx"
    
    # 한글 파일명을 올바르게 인코딩
    from urllib.parse import quote
    encoded_filename = quote(filename.encode('utf-8'))
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    
    # 엑셀 파일을 메모리에서 저장
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    response.write(excel_file.getvalue())
    
    return response

# 파일 관리 뷰들을 별도 모듈에서 import
from .file_views import (
    file_download_view, file_delete_view, history_files_api, note_file_upload,
    schedule_file_upload, schedule_file_download, schedule_file_delete, schedule_files_api
)

# ============ 고객 리포트 관련 뷰들 ============


@require_http_methods(["POST"])
@login_required
def toggle_schedule_delivery_tax_invoice(request, schedule_id):
    """Schedule의 DeliveryItem 세금계산서 발행여부 일괄 토글 API"""
    return _receivables_only_response()

    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크: 수정 권한이 있는 경우만 가능
        if not can_modify_user_data(request.user, schedule.user):
            return JsonResponse({
                'success': False,
                'error': '세금계산서 상태를 변경할 권한이 없습니다.'
            }, status=403)
        
        # Schedule에 연결된 DeliveryItem들 조회
        delivery_items = schedule.delivery_items_set.all()
        
        if not delivery_items.exists():
            return JsonResponse({
                'success': False,
                'error': '해당 일정에 납품 품목이 없습니다.'
            })
        
        # 현재 상태 확인 (하나라도 미발행이면 모두 발행으로, 모두 발행이면 모두 미발행으로)
        any_not_issued = delivery_items.filter(tax_invoice_issued=False).exists()
        new_status = any_not_issued  # 미발행이 있으면 True(발행)로, 없으면 False(미발행)로
        
        # 일괄 업데이트
        updated_count = delivery_items.update(tax_invoice_issued=new_status)
        
        # 연결된 히스토리들도 함께 업데이트
        try:
            related_histories = History.objects.filter(
                schedule=schedule, 
                action_type='delivery_schedule'
            )
            
            if related_histories.exists():
                history_updated_count = related_histories.update(tax_invoice_issued=new_status)
                
        except Exception as sync_error:
            logger.error(f"스케줄 납품 품목 토글 시 히스토리 동기화 실패: {sync_error}")
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'newStatus': new_status,
            'updated_count': updated_count,
            'updatedCount': updated_count,
            'status_text': '발행됨' if new_status else '미발행',
            'statusText': '발행됨' if new_status else '미발행',
            'message': f'세금계산서 상태를 {"발행됨" if new_status else "미발행"}으로 변경했습니다.',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'세금계산서 상태 변경 중 오류가 발생했습니다: {str(e)}'
        })


@require_http_methods(["DELETE"])
@login_required
def delete_manager_memo_api(request, history_id):
    """댓글 메모 삭제 API - 매니저는 모든 댓글, 실무자는 자신의 댓글만 삭제 가능"""
    try:
        user_profile = get_user_profile(request.user)
        
        # 히스토리 조회
        history = get_object_or_404(History, pk=history_id)
        
        # 메모 타입이고 부모 히스토리가 있는 댓글인지 확인
        if history.action_type != 'memo' or not history.parent_history:
            return JsonResponse({
                'success': False,
                'error': '댓글 메모만 삭제할 수 있습니다.'
            }, status=400)
        
        # 권한 확인 - 모든 사용자는 본인이 작성한 댓글만 삭제 가능
        can_delete = False
        
        # 매니저가 작성한 댓글인지 확인 (created_by가 있는 경우)
        if history.created_by:
            # 매니저 댓글은 작성한 매니저만 삭제 가능
            if history.created_by == request.user:
                can_delete = True
        else:
            # 일반 실무자 댓글은 작성한 실무자만 삭제 가능
            if history.user == request.user:
                can_delete = True
        
        if not can_delete:
            return JsonResponse({
                'success': False,
                'error': '이 댓글을 삭제할 권한이 없습니다.'
            }, status=403)
        
        # 삭제 실행
        history.delete()
        
        return JsonResponse({
            'success': True,
            'message': '댓글이 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Manager memo deletion error: {e}")
        return JsonResponse({
            'success': False,
            'error': '메모 삭제 중 오류가 발생했습니다.'
        }, status=500)


@require_http_methods(["POST"])
@login_required
def add_manager_memo_to_history_api(request, history_id):
    """히스토리에 댓글 메모 추가 API - 매니저와 해당 실무자가 추가 가능"""
    try:
        user_profile = get_user_profile(request.user)
        
        # 부모 히스토리 조회
        parent_history = get_object_or_404(History, pk=history_id)
        if parent_history.action_type == 'memo' or parent_history.parent_history_id:
            return JsonResponse({
                'success': False,
                'error': '댓글에는 다시 댓글을 추가할 수 없습니다.'
            }, status=400)
        
        # 권한 확인 - 매니저이거나 해당 히스토리의 담당자인 경우 허용
        if not (user_profile.is_manager() or request.user == parent_history.user):
            return JsonResponse({
                'success': False,
                'error': '이 히스토리에 댓글을 추가할 권한이 없습니다.'
            }, status=403)
        
        # 매니저가 다른 사용자 데이터에 접근하는 경우 권한 체크
        if user_profile.is_manager() and request.user != parent_history.user:
            if not can_access_user_data(request.user, parent_history.user):
                return JsonResponse({
                    'success': False,
                    'error': '이 히스토리에 접근할 권한이 없습니다.'
                }, status=403)
        
        # 메모 내용 가져오기
        memo_content = request.POST.get('memo', '').strip()
        if not memo_content:
            return JsonResponse({
                'success': False,
                'error': '메모 내용을 입력해주세요.'
            }, status=400)
        
        # 댓글 메모를 부모 히스토리에 연결된 자식 히스토리로 생성
        # 매니저의 경우: created_by에 매니저 정보 저장, user는 원래 실무자 유지
        # 실무자의 경우: created_by는 None, user는 본인
        memo_history = History.objects.create(
            followup=parent_history.followup,
            user=parent_history.user,  # 원래 실무자를 유지
            parent_history=parent_history,  # 부모 히스토리 설정
            action_type='memo',
            content=memo_content,
            created_by=request.user if user_profile.is_manager() else None,  # 매니저인 경우만 created_by 설정
            schedule=parent_history.schedule if parent_history.schedule else None
        )
        
        # 메시지도 역할에 따라 구분
        message = '댓글이 성공적으로 추가되었습니다.'
        if user_profile.is_manager():
            message = '매니저 메모가 성공적으로 추가되었습니다.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'memo': {
                'id': memo_history.id,
                'content': memo_history.content,
                'created_at': memo_history.created_at.strftime('%Y-%m-%d %H:%M'),
                'created_by': request.user.username
            }
        })
        
    except Exception as e:
        logger.error(f"Add manager memo to history error: {e}")
        return JsonResponse({
            'success': False,
            'error': '메모 추가 중 오류가 발생했습니다.'
        }, status=500)

@require_http_methods(["POST"])
@login_required
def customer_priority_update(request, followup_id):
    """Deprecated customer priority API. Pipeline stage is the active workflow."""
    return JsonResponse({
        'success': False,
        'error': '고객 우선순위는 더 이상 사용하지 않습니다. 파이프라인 단계를 사용해주세요.',
    }, status=410)


@login_required
def history_delivery_items_api(request, history_id):
    """History의 DeliveryItem 정보를 가져오는 API"""
    import re
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        history = get_object_or_404(History, pk=history_id)
        
        # 권한 체크: 해당 활동기록을 볼 수 있는 권한이 있는지 확인
        if not can_access_user_data(request.user, history.user):
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # DeliveryItem 정보 가져오기
        delivery_items = history.delivery_items_set.all().order_by('id')
        
        items_data = []
        has_history_items = False
        has_schedule_items = False
        
        # 1. History DeliveryItem 모델이 있는 경우
        if delivery_items.exists():
            has_history_items = True
            for item in delivery_items:
                effective_unit_price = item.get_effective_unit_price() or item.unit_price or 0
                item_total = item.total_price or vat.item_gross_total(item, unit_price=effective_unit_price)
                # History의 세금계산서 상태를 기준으로 함 (동기화)
                items_data.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price or 0),
                    'discount_rate': float(item.discount_rate or 0),
                    'discount_unit_price': (
                        float(_schedules_discount_unit_price_or_none(item))
                        if _schedules_discount_unit_price_or_none(item) is not None
                        else None
                    ),
                    'effective_unit_price': float(effective_unit_price),
                    'total_price': float(item_total),
                    'tax_invoice_issued': history.tax_invoice_issued,  # History 기준으로 강제 설정
                    'notes': item.notes or '',
                    'option_description': item.option_description or '',
                    'optionDescription': item.option_description or '',
                    'source': 'history'  # 출처 표시
                })
        else:
            pass
        
        # 2. History DeliveryItem이 없지만 기존 텍스트 데이터가 있는 경우 (fallback)
        if not has_history_items and history.delivery_items and history.delivery_items.strip():
            has_history_items = True
            # 기존 텍스트 데이터 파싱
            delivery_text = history.delivery_items.strip()
            
            # 줄바꿈으로 분리하여 각 라인 처리
            lines = delivery_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            
            # 만약 줄바꿈이 문자열로 저장되어 있다면 \\n으로도 분리 시도
            if len(lines) == 1 and '\\n' in delivery_text:
                lines = delivery_text.split('\\n')
            
            # 그래도 하나의 라인이면, 품목 패턴을 찾아서 분리
            if len(lines) == 1:
                # 정규식으로 품목 패턴을 모두 찾기
                pattern = r'([A-Z0-9.]+:\s*\d+(?:\.\d+)?개\s*\([0-9,]+원\))'
                matches = re.findall(pattern, delivery_text)
                if len(matches) > 1:
                    lines = matches
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                if not line:
                    continue
                
                # "품목명: 수량개 (금액원)" 패턴 파싱
                match = re.match(r'^(.+?):\s*(\d+(?:\.\d+)?)개\s*\((.+?)원\)$', line)
                if match:
                    item_name = match.group(1).strip()
                    quantity = float(match.group(2))
                    amount_str = match.group(3).replace(',', '').replace(' ', '')
                    
                    try:
                        total_amount = float(amount_str)
                        # 부가세 포함 금액에서 단가 역산 (부가세 포함 / 수량)
                        unit_price = total_amount / quantity if quantity > 0 else 0
                    except ValueError as e:
                        logger.error(f"[HISTORY_DELIVERY_API] 금액 파싱 실패: {e}")
                        total_amount = 0
                        unit_price = 0
                    
                    items_data.append({
                        'id': f'text_{len(items_data)}',  # 임시 ID
                        'item_name': item_name,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_price': total_amount,
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준
                        'source': 'history_text'  # 출처 표시
                    })
                else:
                    # 패턴에 맞지 않는 경우, 전체를 품목명으로 처리
                    items_data.append({
                        'id': f'text_{len(items_data)}',  # 임시 ID
                        'item_name': line,
                        'quantity': 1,
                        'unit_price': 0,
                        'total_price': 0,
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준
                        'source': 'history_text'  # 출처 표시
                    })
        
        # 3. 연결된 Schedule의 DeliveryItem도 항상 확인 (History 기준 세금계산서 상태 적용)
        # History에 DeliveryItem이나 텍스트가 없어도 Schedule DeliveryItem은 항상 확인
        if history.schedule:
            schedule_items = history.schedule.delivery_items_set.all().order_by('id')
            
            if schedule_items.exists():
                has_schedule_items = True
                for item in schedule_items:
                    item_total = item.total_price or vat.item_gross_total(item, unit_price=item.unit_price)
                    
                    items_data.append({
                        'id': f'schedule_{item.id}',
                        'item_name': item.item_name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item_total),
                        'tax_invoice_issued': history.tax_invoice_issued,  # History 기준으로 강제 설정
                        'source': 'schedule'  # 출처 표시
                    })
        else:
            pass
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'history_id': history.id,
            'delivery_date': history.delivery_date.strftime('%Y-%m-%d') if history.delivery_date else '',
            'is_legacy_data': not has_history_items and bool(history.delivery_items),  # 레거시 데이터 여부
            'has_history_items': has_history_items,
            'has_schedule_items': has_schedule_items,
            'tax_invoice_status': history.tax_invoice_issued,  # History 기준 세금계산서 상태
        })
        
    except Exception as e:
        logger.error(f"[HISTORY_DELIVERY_API] API 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'DeliveryItem 정보를 가져오는 중 오류가 발생했습니다.'
        }, status=500)


@login_required
@require_POST
def followup_create_ajax(request):
    """AJAX로 팔로우업을 생성하는 뷰"""
    try:
        # Manager는 데이터 생성 불가 (뷰어 권한)
        _ajax_profile = get_user_profile(request.user)
        if _ajax_profile.is_manager():
            return JsonResponse({'success': False, 'error': '권한이 없습니다. Manager는 데이터를 생성할 수 없습니다.'}, status=403)

        # 필수 필드 검증
        customer_name = request.POST.get('customer_name', '').strip()
        company_id = request.POST.get('company', '').strip()
        department_id = request.POST.get('department', '').strip()
        priority = 'scheduled'
        
        if not customer_name:
            return JsonResponse({
                'success': False,
                'error': '고객명을 입력해주세요.'
            })
        
        if not company_id:
            return JsonResponse({
                'success': False,
                'error': '업체/학교를 선택해주세요.'
            })
            
        if not department_id:
            return JsonResponse({
                'success': False,
                'error': '부서/연구실을 선택해주세요.'
            })
        
        # Company와 Department 객체 가져오기
        try:
            company = Company.objects.get(id=company_id)
            department = Department.objects.get(id=department_id, company=company)
        except (Company.DoesNotExist, Department.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': '선택한 업체 또는 부서가 존재하지 않습니다.'
            })
        
        # 권한 체크: 같은 회사에서 생성된 업체인지 확인
        user_profile_obj = getattr(request.user, 'userprofile', None)
        is_admin = getattr(request, 'is_admin', False) or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'admin')
        
        import logging
        logger = logging.getLogger(__name__)
        
        if not is_admin:
            if user_profile_obj and user_profile_obj.company:
                same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
                if company.created_by not in same_company_users:
                    return JsonResponse({
                        'success': False,
                        'error': '접근 권한이 없는 업체입니다.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '회사 정보가 없어 팔로우업을 생성할 수 없습니다.'
                })
        
        # 같은 담당자로 카드를 여러 개 만드는 것을 막지 않는다.
        # 파이프라인 카드는 "고객"이 아니라 "영업건" 단위다(2026-08-04 건 단위 분리).
        # 같은 사람과 동시에 여러 건을 진행하거나, 한 건이 수주로 끝난 뒤 같은
        # 사람에게 새 건을 시작하는 일이 실제로 있다 — 예: 수주에 김지훈 카드가
        # 있으면서 접촉/미팅에도 다른 김지훈 카드가 있어야 한다. 예전에는
        # (고객명+업체+부서+담당) 중복을 막아 두 번째 카드를 만들 수 없었다.
        
        # 팔로우업 생성
        followup = FollowUp.objects.create(
            user=request.user,
            customer_name=customer_name,
            company=company,
            department=department,
            manager=request.POST.get('manager', '').strip(),
            phone_number=request.POST.get('phone_number', '').strip(),
            email=request.POST.get('email', '').strip(),
            priority=priority,
            address=request.POST.get('address', '').strip(),     # 상세주소 추가
            notes=request.POST.get('notes', '').strip(),
            status='active'
        )
        
        # 사용자 회사 정보 설정
        if user_profile_obj and user_profile_obj.company:
            followup.user_company = user_profile_obj.company
            followup.save(update_fields=['user_company'])
        
        # 성공 응답
        followup_text = f"{followup.customer_name} ({followup.company.name} - {followup.department.name})"
        
        return JsonResponse({
            'success': True,
            'followup_id': followup.id,
            'followup_text': followup_text,
            'href': f'/customers/{followup.id}/',
            'django_href': reverse('reporting:followup_detail', args=[followup.id]),
            'message': '팔로우업이 성공적으로 생성되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"AJAX 팔로우업 생성 오류: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': '서버 오류가 발생했습니다. 다시 시도해주세요.'
        }, status=500)

@login_required
def department_list_ajax(request, company_id):
    """특정 업체의 부서 목록을 AJAX로 반환"""
    try:
        company = get_object_or_404(Company, id=company_id)
        
        # 권한 체크: 같은 회사에서 생성된 업체인지 확인
        user_profile_obj = getattr(request.user, 'userprofile', None)
        if user_profile_obj and user_profile_obj.company:
            same_company_users = User.objects.filter(userprofile__company=user_profile_obj.company)
            if company.created_by not in same_company_users:
                return JsonResponse({
                    'error': '접근 권한이 없는 업체입니다.'
                }, status=403)
        
        departments = Department.objects.filter(company=company).values('id', 'name')
        departments_list = [{'id': dept['id'], 'name': dept['name']} for dept in departments]
        
        return JsonResponse(departments_list, safe=False)
        
    except Exception as e:
        logger.error(f"부서 목록 AJAX 조회 오류: {str(e)}")
        return JsonResponse({
            'error': '부서 목록을 가져오는 중 오류가 발생했습니다.'
        }, status=500)

@login_required
@role_required(['admin', 'salesman'])
@require_POST
def update_tax_invoice_status(request):
    """세금계산서 상태 업데이트 API"""
    return _receivables_only_response()

    try:
        data = json.loads(request.body)
        delivery_type = data.get('type')
        delivery_id = data.get('id')
        tax_invoice_issued = data.get('tax_invoice_issued')
        
        if delivery_type == 'history':
            # History 레코드의 세금계산서 상태 업데이트
            try:
                history = History.objects.get(id=delivery_id)
                
                # 권한 체크
                if not can_access_user_data(request.user, history.user):
                    return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    history_user_profile = getattr(history.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        history_user_profile and history_user_profile.company and
                        user_profile_obj.company != history_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                history.tax_invoice_issued = tax_invoice_issued
                history.save()
                
                # History에 직접 연결된 DeliveryItem들도 함께 업데이트
                history_delivery_items = history.delivery_items_set.all()
                if history_delivery_items.exists():
                    updated_count = history_delivery_items.update(tax_invoice_issued=tax_invoice_issued)
                
                # History와 연결된 Schedule의 모든 DeliveryItem도 함께 업데이트
                if history.schedule:
                    schedule_updated_count = DeliveryItem.objects.filter(schedule=history.schedule).update(
                        tax_invoice_issued=tax_invoice_issued
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': '세금계산서 상태가 업데이트되었습니다.'
                })
                
            except History.DoesNotExist:
                return JsonResponse({'error': '해당 납품 기록을 찾을 수 없습니다.'}, status=404)
                
        elif delivery_type == 'delivery_item':
            # DeliveryItem의 세금계산서 상태 업데이트
            try:
                delivery_item = DeliveryItem.objects.get(id=delivery_id)
                
                # 권한 체크
                if not can_access_user_data(request.user, delivery_item.schedule.user):
                    return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    item_user_profile = getattr(delivery_item.schedule.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        item_user_profile and item_user_profile.company and
                        user_profile_obj.company != item_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                delivery_item.tax_invoice_issued = tax_invoice_issued
                delivery_item.save()
                
                return JsonResponse({
                    'success': True,
                    'message': '세금계산서 상태가 업데이트되었습니다.'
                })
                
            except DeliveryItem.DoesNotExist:
                return JsonResponse({'error': '해당 납품 품목을 찾을 수 없습니다.'}, status=404)
                
        elif delivery_type == 'schedule_bulk':
            # Schedule의 모든 DeliveryItem 일괄 업데이트
            try:
                schedule = Schedule.objects.get(id=delivery_id)
                
                # 권한 체크
                if not can_access_user_data(request.user, schedule.user):
                    return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    schedule_user_profile = getattr(schedule.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        schedule_user_profile and schedule_user_profile.company and
                        user_profile_obj.company != schedule_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
                
                # Schedule의 모든 DeliveryItem 업데이트
                updated_count = DeliveryItem.objects.filter(schedule=schedule).update(
                    tax_invoice_issued=tax_invoice_issued
                )
                
                # 연결된 History도 함께 업데이트
                History.objects.filter(schedule=schedule).update(
                    tax_invoice_issued=tax_invoice_issued
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'세금계산서 상태가 업데이트되었습니다. (품목 {updated_count}개)',
                    'updated_count': updated_count
                })
                
            except Schedule.DoesNotExist:
                return JsonResponse({'error': '해당 일정을 찾을 수 없습니다.'}, status=404)
        
        else:
            return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"세금계산서 상태 업데이트 오류: {str(e)}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)

@login_required
@role_required(['admin', 'salesman', 'manager'])
def schedule_delivery_items_api(request, schedule_id):
    """Schedule의 DeliveryItem 정보를 반환하는 API"""
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        # 권한 체크: Schedule의 followup을 통해 사용자 확인
        if schedule.followup and schedule.followup.user:
            if not can_access_user_data(request.user, schedule.followup.user):
                return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
            
            # Manager는 회사 체크를 건너뜀 (모든 데이터 조회 가능)
            user_profile = get_user_profile(request.user)
            if not user_profile.is_manager():
                # 하나과학이 아닌 경우 같은 회사 체크
                if not getattr(request, 'is_hanagwahak', False):
                    user_profile_obj = getattr(request.user, 'userprofile', None)
                    schedule_user_profile = getattr(schedule.followup.user, 'userprofile', None)
                    if (user_profile_obj and user_profile_obj.company and 
                        schedule_user_profile and schedule_user_profile.company and
                        user_profile_obj.company != schedule_user_profile.company):
                        return JsonResponse({'error': '접근 권한이 없습니다.'}, status=403)
        
        # DeliveryItem 정보 가져오기
        items = []
        for item in schedule.delivery_items_set.all():
            effective_unit_price = item.get_effective_unit_price() or item.unit_price or 0
            items.append({
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price or 0),
                'discount_rate': float(item.discount_rate or 0),
                'discount_unit_price': (
                    float(_schedules_discount_unit_price_or_none(item))
                    if _schedules_discount_unit_price_or_none(item) is not None
                    else None
                ),
                'effective_unit_price': float(effective_unit_price),
                'total_price': float(item.total_price or 0),
                'tax_invoice_issued': item.tax_invoice_issued,
                'notes': item.notes or '',
                'option_description': item.option_description or '',
                'optionDescription': item.option_description or '',
            })
        
        return JsonResponse({
            'success': True,
            'items': items,
            'schedule_id': schedule.id,
            'visit_date': schedule.visit_date.strftime('%Y-%m-%d')
        })
        
    except Schedule.DoesNotExist:
        return JsonResponse({'error': '해당 일정을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        logger.error(f"Schedule 납품 품목 API 오류: {str(e)}")
        return JsonResponse({'error': '서버 오류가 발생했습니다.'}, status=500)


# ============ Admin 전용 API 뷰들 ============

@role_required(['admin'])
@require_http_methods(["GET"])
def api_users_list(request):
    """사용자 목록 API (Admin 전용)"""
    try:
        users = User.objects.select_related('userprofile', 'userprofile__company').all()
        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'company': None
            }
            
            if hasattr(user, 'userprofile') and user.userprofile.company:
                user_data['company'] = user.userprofile.company.name
            
            users_data.append(user_data)
        
        return JsonResponse({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        logger.error(f"사용자 목록 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@role_required(['admin'])
@require_http_methods(["POST"])
def api_change_company_creator(request):
    """업체 생성자 변경 API (Admin 전용)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        company_id = request.POST.get('company_id')
        new_creator_id = request.POST.get('new_creator_id')
        
        if not company_id or not new_creator_id:
            return JsonResponse({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }, status=400)
        
        # 업체 조회
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '존재하지 않는 업체입니다.'
            }, status=404)
        
        # 새 생성자 조회
        try:
            new_creator = User.objects.select_related('userprofile', 'userprofile__company').get(id=new_creator_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '존재하지 않는 사용자입니다.'
            }, status=404)
        
        # 기존 생성자 정보 로깅
        old_creator = company.created_by
        old_creator_info = 'None'
        if old_creator:
            old_creator_company = 'Unknown'
            if hasattr(old_creator, 'userprofile') and old_creator.userprofile.company:
                old_creator_company = old_creator.userprofile.company.name
            old_creator_info = f"{old_creator.username} ({old_creator_company})"
        
        # 새 생성자 정보
        new_creator_company = 'Unknown'
        if hasattr(new_creator, 'userprofile') and new_creator.userprofile.company:
            new_creator_company = new_creator.userprofile.company.name
        new_creator_info = f"{new_creator.username} ({new_creator_company})"
        
        # 업체 생성자 변경
        company.created_by = new_creator
        company.save()
        
        # 응답 데이터
        response_data = {
            'success': True,
            'message': '업체 생성자가 성공적으로 변경되었습니다.',
            'new_creator': {
                'id': new_creator.id,
                'username': new_creator.username,
                'company': new_creator_company
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"업체 생성자 변경 API 에러: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_company_departments(request, company_id):
    """업체별 부서 목록 API"""
    try:
        # 업체 조회 및 접근 권한 확인
        company = get_object_or_404(Company, pk=company_id)
        
        # 접근 권한 확인
        same_company_users = User.objects.filter(
            userprofile__company=request.user.userprofile.company
        )
        
        # 업체가 사용자의 회사와 연결되어 있는지 확인
        if company.created_by not in same_company_users:
            return JsonResponse({'success': False, 'message': '접근 권한이 없습니다.'}, status=403)
        
        # 해당 업체의 부서 목록 조회
        departments = Department.objects.filter(
            company=company
        ).order_by('name')
        
        departments_data = []
        for dept in departments:
            # 각 부서별 고객 수 직접 계산
            followup_count = FollowUp.objects.filter(department=dept).count()
            
            dept_data = {
                'id': dept.id,
                'name': dept.name,
                'followup_count': followup_count,
                'created_date': dept.created_at.strftime('%Y-%m-%d'),
                'created_by': dept.created_by.username if dept.created_by else '정보 없음'
            }
            departments_data.append(dept_data)
        
        return JsonResponse({
            'success': True,
            'company_name': company.name,
            'departments': departments_data,
            'total_count': len(departments_data)
        })
        
    except Exception as e:
        logger.error(f"업체별 부서 목록 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_company_customers(request, company_id):
    """업체별 고객 정보 목록 API"""
    try:
        # 업체 조회 및 접근 권한 확인
        company = get_object_or_404(Company, pk=company_id)
        
        # 접근 권한 확인
        same_company_users = User.objects.filter(
            userprofile__company=request.user.userprofile.company
        )
        
        # 업체가 사용자의 회사와 연결되어 있는지 확인
        if company.created_by not in same_company_users:
            return JsonResponse({'success': False, 'message': '접근 권한이 없습니다.'}, status=403)
        
        # 해당 업체의 고객 정보들 조회
        followups = FollowUp.objects.filter(
            company=company
        ).select_related('department')
        
        customers_data = []
        for followup in followups:
            customer_data = {
                'id': followup.id,
                'customer_name': followup.customer_name or '고객명 미정',
                'phone': followup.phone_number or '-',
                'email': followup.email or '-',
                'position': followup.manager or '-',
                'department_name': followup.department.name if followup.department else '-',
                'created_date': followup.created_at.strftime('%Y-%m-%d'),
                'last_contact': followup.updated_at.strftime('%Y-%m-%d') if followup.updated_at else '연락 없음'
            }
            customers_data.append(customer_data)
        
        return JsonResponse({
            'success': True,
            'company_name': company.name,
            'customers': customers_data,
            'total_count': len(customers_data)
        })
        
    except Exception as e:
        logger.error(f"업체별 고객 정보 API 에러: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ============ 프로필 관리 뷰들 ============


def _react_request_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return {}
    return request.POST


def _profile_api_payload(request):
    user = request.user
    profile = get_user_profile(user)
    company = profile.company
    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'user': {
            'id': user.id,
            'username': user.username,
            'firstName': user.first_name or '',
            'lastName': user.last_name or '',
            'fullName': _user_display_name(user),
            'email': user.email or '',
            'dateJoined': user.date_joined.isoformat() if user.date_joined else None,
            'lastLogin': user.last_login.isoformat() if user.last_login else None,
        },
        'profile': {
            'role': profile.role,
            'roleLabel': profile.get_role_display(),
            'company': company.name if company else '',
            'canUseAi': bool(profile.can_use_ai),
            'canDownloadExcel': bool(profile.can_excel_download()),
        },
        'links': {
            'update': reverse('reporting:profile_api_update'),
            'password': reverse('reporting:profile_api_password'),
            'legacy': reverse('reporting:profile'),
            'legacyEdit': reverse('reporting:profile_edit'),
            'dashboard': '/dashboard/',
        },
    }


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def profile_api(request):
    """React 프로필 화면용 조회 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    return JsonResponse(_profile_api_payload(request), encoder=DjangoJSONEncoder)


@never_cache
@require_http_methods(["POST"])
def profile_update_api(request):
    """React 프로필 기본 정보 수정 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    payload = _react_request_payload(request)
    username = (payload.get('username') or '').strip()
    first_name = (payload.get('firstName') or payload.get('first_name') or '').strip()
    last_name = (payload.get('lastName') or payload.get('last_name') or '').strip()
    email_value = (payload.get('email') or '').strip()

    errors = {}
    if not username:
        errors['username'] = '사용자명을 입력하세요.'
    elif User.objects.exclude(pk=request.user.pk).filter(username=username).exists():
        errors['username'] = '이미 사용 중인 사용자명입니다.'
    if email_value:
        email_field = forms.EmailField(required=False)
        try:
            email_field.clean(email_value)
        except forms.ValidationError:
            errors['email'] = '올바른 이메일 주소를 입력하세요.'
    if errors:
        return JsonResponse({'success': False, 'errors': errors, 'error': '입력값을 확인하세요.'}, status=400)

    user = request.user
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email_value
    user.save(update_fields=['username', 'first_name', 'last_name', 'email'])
    response_payload = _profile_api_payload(request)
    response_payload['message'] = '프로필 정보를 저장했습니다.'
    return JsonResponse(response_payload, encoder=DjangoJSONEncoder)


@never_cache
@require_http_methods(["POST"])
def profile_password_api(request):
    """React 프로필 비밀번호 변경 API."""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm

    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    payload = _react_request_payload(request)
    form = PasswordChangeForm(request.user, {
        'old_password': payload.get('oldPassword') or payload.get('old_password') or '',
        'new_password1': payload.get('newPassword1') or payload.get('new_password1') or '',
        'new_password2': payload.get('newPassword2') or payload.get('new_password2') or '',
    })
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': '비밀번호 입력값을 확인하세요.',
            'errors': {field: [str(error) for error in values] for field, values in form.errors.items()},
        }, status=400)

    user = form.save()
    update_session_auth_hash(request, user)
    return JsonResponse({
        'success': True,
        'message': '비밀번호를 변경했습니다.',
    })


@login_required
def followup_quote_items_api(request, followup_id):
    """
    특정 팔로우업의 견적 품목을 가져오는 API
    납품 일정 생성 시 견적에서 품목을 불러오기 위해 사용
    같은 부서/연구실에 연결된 본인 견적 일정도 함께 불러옴
    """
    from decimal import Decimal

    try:
        followup = get_object_or_404(FollowUp, pk=followup_id)
        
        # 권한 체크 (같은 회사 소속이면 접근 가능)
        if not can_access_followup(request.user, followup):
            return JsonResponse({
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        if followup.department_id:
            quote_followups = FollowUp.objects.filter(
                department_id=followup.department_id,
                user__in=get_accessible_users(request.user, request),
            )
        else:
            quote_followups = FollowUp.objects.filter(pk=followup.pk)

        # 같은 부서의 본인 견적 일정 조회. 완료된 견적이라도 일부 품목만 납품된
        # 경우에는 남은 품목을 다시 선택할 수 있어야 하므로 품목 단위로 걸러낸다.
        quote_items_queryset = DeliveryItem.objects.select_related('product').order_by('id')
        quote_schedules = list(Schedule.objects.filter(
            followup__in=quote_followups,
            activity_type='quote',
            status__in=['scheduled', 'completed'],
            user=request.user,
        ).select_related('followup', 'followup__company', 'followup__department').prefetch_related(
            Prefetch('delivery_items_set', queryset=quote_items_queryset),
        ).order_by('-visit_date', '-visit_time', '-created_at'))
        
        if not quote_schedules:
            return JsonResponse({
                'error': '이 부서에 대한 본인 작성 견적이 없습니다.'
            })
        
        # 모든 견적 정보 수집 (납품되지 않은 것만)
        quotes_data = []
        progress_by_schedule_id = _schedules_quote_item_progress_entries_for_schedules(
            quote_schedules,
            include_legacy_matches_for_completed=True,
        )
        
        for quote_schedule in quote_schedules:
            logger.info(f"[QUOTE_ITEMS_API] Schedule ID: {quote_schedule.id}, visit_date: {quote_schedule.visit_date}")

            schedule_progress = progress_by_schedule_id.get(quote_schedule.id, {})
            remaining_entries = schedule_progress.get('remaining_entries', [])
            has_import_activity = schedule_progress.get('has_import_activity', False)
            has_sold_items = schedule_progress.get('has_sold_items', False)
            progress_by_item_id = schedule_progress.get('progress_by_item_id', {})
            if quote_schedule.status == 'completed' and not (has_import_activity or has_sold_items):
                continue

            if remaining_entries:
                grouped_quote_items = {}
                quote_total = Decimal('0')
                for item, remaining_quantity in remaining_entries:
                    progress = progress_by_item_id.get(item.id, {})
                    quoted_quantity = progress.get('quotedQuantity', Decimal(str(item.quantity or 0)))
                    delivered_quantity = progress.get('deliveredQuantity', Decimal('0'))
                    remaining_quantity_decimal = progress.get('remainingQuantity', Decimal(str(remaining_quantity or 0)))
                    item_total = _schedules_quote_item_total_for_quantity(item, remaining_quantity)
                    item_quoted_total = _schedules_quote_item_total_for_quantity(item, quoted_quantity)
                    item_delivered_total = _schedules_quote_item_total_for_quantity(item, delivered_quantity)
                    fallback_effective_unit_price = None
                    if item_total > 0 and Decimal(str(remaining_quantity or 0)) > 0:
                        from decimal import ROUND_HALF_UP

                        fallback_effective_unit_price = (
                            vat.supply_from_gross(item_total, vat.item_vat_mode(item)) / Decimal(str(remaining_quantity or 0))
                        ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    product = item.product if item.product_id else None
                    unit_price = float(
                        item.unit_price
                        if item.unit_price is not None
                        else fallback_effective_unit_price or 0
                    )
                    normalized_discount_unit_price = _schedules_discount_unit_price_or_none(item)
                    discount_unit_price = (
                        float(normalized_discount_unit_price)
                        if normalized_discount_unit_price is not None
                        else None
                    )
                    effective_unit_price = float(item.get_effective_unit_price() or item.unit_price or fallback_effective_unit_price or 0)
                    unit = item.unit or (product.unit if product else '') or 'EA'
                    quote_group = _quote_group_key(item.quote_group)
                    item_data = {
                        'id': item.id,
                        'source_quote_item_id': item.id,
                        'sourceQuoteItemId': item.id,
                        'item_name': item.item_name,
                        'itemName': item.item_name,
                        'original_quantity': float(quoted_quantity),
                        'originalQuantity': float(quoted_quantity),
                        'delivered_quantity': float(delivered_quantity),
                        'deliveredQuantity': float(delivered_quantity),
                        'remaining_quantity': float(remaining_quantity_decimal),
                        'remainingQuantity': float(remaining_quantity_decimal),
                        'quantity': remaining_quantity,
                        'unit': unit,
                        'unit_price': unit_price,
                        'unitPrice': unit_price,
                        'discount_rate': float(item.discount_rate or 0),
                        'discountRate': float(item.discount_rate or 0),
                        'discount_unit_price': discount_unit_price,
                        'discountUnitPrice': discount_unit_price,
                        'effective_unit_price': effective_unit_price,
                        'effectiveUnitPrice': effective_unit_price,
                        'total_price': float(item_total),
                        'totalPrice': float(item_total),
                        'remaining_amount': float(item_total),
                        'remainingAmount': float(item_total),
                        'quoted_amount': float(item_quoted_total),
                        'quotedAmount': float(item_quoted_total),
                        'delivered_amount': float(item_delivered_total),
                        'deliveredAmount': float(item_delivered_total),
                        'product_id': item.product_id,
                        'productId': item.product_id,
                        'product_code': product.product_code if product else '',
                        'productCode': product.product_code if product else '',
                        'product_description': (product.description or '') if product else '',
                        'productDescription': (product.description or '') if product else '',
                        'source_quote_schedule_id': quote_schedule.id,
                        'sourceQuoteScheduleId': quote_schedule.id,
                        'tax_invoice_issued': bool(item.tax_invoice_issued),
                        'taxInvoiceIssued': bool(item.tax_invoice_issued),
                        'quote_group': quote_group,
                        'quoteGroup': quote_group,
                        'quote_group_label': _quote_group_label(quote_group),
                        'quoteGroupLabel': _quote_group_label(quote_group),
                        'notes': item.notes or '',
                        'option_description': item.option_description or '',
                        'optionDescription': item.option_description or '',
                    }
                    if quote_group not in grouped_quote_items:
                        grouped_quote_items[quote_group] = {
                            'label': _quote_group_label(quote_group),
                            'items': [],
                        'total': Decimal('0'),
                        'quoted_total': Decimal('0'),
                        'delivered_total': Decimal('0'),
                    }
                    grouped_quote_items[quote_group]['items'].append(item_data)
                    grouped_quote_items[quote_group]['total'] += item_total
                    grouped_quote_items[quote_group]['quoted_total'] += item_quoted_total
                    grouped_quote_items[quote_group]['delivered_total'] += item_delivered_total
                    quote_total += item_total
                quote_groups = [
                    {
                        'key': group_key,
                        'label': group_data['label'],
                        'items': group_data['items'],
                        'total': group_data['total'],
                        'quoted_total': group_data['quoted_total'],
                        'delivered_total': group_data['delivered_total'],
                    }
                    for group_key, group_data in grouped_quote_items.items()
                ]
            else:
                if quote_schedule.status != 'scheduled':
                    continue
                quote_total = quote_schedule.expected_revenue or Decimal('0')
                quote_groups = [{
                    'key': '',
                    'label': _quote_group_label(''),
                    'items': [],
                    'total': quote_total,
                    'quoted_total': quote_total,
                    'delivered_total': Decimal('0'),
                }]

            if remaining_entries or quote_total > 0:
                quote_followup = quote_schedule.followup

                for group_data in quote_groups:
                    group_key = group_data['key']
                    group_label = group_data['label']
                    option_id = f"{quote_schedule.id}:{group_key or 'default'}"
                    delivered_amount = group_data.get('delivered_total', Decimal('0'))
                    remaining_amount = group_data.get('total', Decimal('0'))
                    quoted_amount = group_data.get('quoted_total', remaining_amount + delivered_amount)
                    has_partial_delivery = delivered_amount > 0 and remaining_amount > 0
                    delivery_status = 'partial' if has_partial_delivery else 'pending'
                    delivery_status_label = '부분 납품 잔여' if has_partial_delivery else '미납 견적'
                    quote_data = {
                        'id': quote_schedule.id,
                        'option_id': option_id,
                        'optionId': option_id,
                        'schedule_id': quote_schedule.id,
                        'scheduleId': quote_schedule.id,
                        'quote_group': group_key,
                        'quoteGroup': group_key,
                        'quote_group_label': group_label,
                        'quoteGroupLabel': group_label,
                        'quote_date': quote_schedule.visit_date.strftime('%Y-%m-%d'),
                        'quoteDate': quote_schedule.visit_date.strftime('%Y-%m-%d'),
                        'expected_revenue': float(group_data['total']),
                        'expectedRevenue': float(group_data['total']),
                        'quoted_amount': float(quoted_amount),
                        'quotedAmount': float(quoted_amount),
                        'delivered_amount': float(delivered_amount),
                        'deliveredAmount': float(delivered_amount),
                        'remaining_amount': float(remaining_amount),
                        'remainingAmount': float(remaining_amount),
                        'delivery_status': delivery_status,
                        'deliveryStatus': delivery_status,
                        'delivery_status_label': delivery_status_label,
                        'deliveryStatusLabel': delivery_status_label,
                        'has_partial_delivery': has_partial_delivery,
                        'hasPartialDelivery': has_partial_delivery,
                        'customer_name': quote_followup.customer_name or quote_followup.manager or '고객명 미정',
                        'customerName': quote_followup.customer_name or quote_followup.manager or '고객명 미정',
                        'company_name': quote_followup.company.name if quote_followup.company else '',
                        'companyName': quote_followup.company.name if quote_followup.company else '',
                        'department_name': quote_followup.department.name if quote_followup.department else '',
                        'departmentName': quote_followup.department.name if quote_followup.department else '',
                        'href': f'/schedules/{quote_schedule.id}/',
                        'djangoHref': reverse('reporting:schedule_detail', args=[quote_schedule.id]),
                        'items': group_data['items'],
                    }
                    quotes_data.append(quote_data)

        if not quotes_data:
            return JsonResponse({
                'error': '불러올 수 있는 견적 품목이 없습니다.'
            })
        
        return JsonResponse({
            'success': True,
            'quotes': quotes_data,  # 모든 견적 반환
            'count': len(quotes_data),
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'오류가 발생했습니다: {str(e)}'
        }, status=500)


# ============================================
# 제품 관리 뷰
# ============================================


def _product_scope_queryset(request, include_inactive=True):
    """제품관리 화면에서 현재 사용자가 볼 수 있는 제품 범위."""
    from reporting.models import Product

    user_profile = get_user_profile(request.user)
    if user_profile.is_admin():
        products = Product.objects.all()
    elif user_profile.company:
        accessible_users = get_accessible_users(request.user, request)
        products = Product.objects.filter(Q(created_by__in=accessible_users) | Q(created_by__isnull=True))
    else:
        products = Product.objects.filter(Q(created_by=request.user) | Q(created_by__isnull=True))

    if not include_inactive:
        products = products.filter(is_active=True)
    return products


def _product_usage_annotations(queryset):
    from django.db.models import Count, Value
    from django.db.models.functions import Coalesce

    return queryset.annotate(
        quote_count=Count(
            'delivery_items__schedule',
            distinct=True,
            filter=Q(
                delivery_items__schedule__isnull=False,
                delivery_items__schedule__activity_type='quote',
            ),
        ),
        completed_schedule_count=Count(
            'delivery_items__schedule',
            distinct=True,
            filter=Q(
                delivery_items__schedule__status='completed',
                delivery_items__schedule__activity_type='delivery',
            ),
        ),
        history_count=Count(
            'delivery_items__history',
            distinct=True,
            filter=Q(delivery_items__history__isnull=False),
        ),
    ).annotate(
        delivery_count=Coalesce('completed_schedule_count', Value(0)) + Coalesce('history_count', Value(0)),
    )


def _product_can_manage(request, product=None):
    user_profile = get_user_profile(request.user)
    if user_profile.is_manager():
        return False
    if user_profile.is_admin():
        return True
    if product is None:
        return True
    if product.created_by_id is None:
        return user_profile.role in ['admin', 'manager']
    return _product_scope_queryset(request, include_inactive=True).filter(id=product.id).exists()


def _product_manage_denied_message(request):
    if get_user_profile(request.user).is_manager():
        return 'Manager 계정은 제품을 등록/수정/삭제할 수 없습니다.'
    return '이 제품을 등록/수정/삭제할 권한이 없습니다.'


def _product_payload(product):
    return {
        'id': product.id,
        'productCode': product.product_code,
        'product_code': product.product_code,
        'name': product.product_code,
        'description': product.description or '',
        'unit': product.unit or 'EA',
        'specification': product.specification or '',
        'standardPrice': int(product.standard_price or 0),
        'standard_price': int(product.standard_price or 0),
        'currentPrice': int(product.standard_price or 0),
        'current_price': int(product.standard_price or 0),
        'isActive': product.is_active,
        'is_active': product.is_active,
        'isPromo': False,
        'is_promo': False,
        'quoteCount': int(getattr(product, 'quote_count', 0) or 0),
        'deliveryCount': int(getattr(product, 'delivery_count', 0) or 0),
        'createdBy': _user_display_name(product.created_by) if product.created_by else '공용',
        'createdAt': _datetime_or_none(product.created_at),
        'updatedAt': _datetime_or_none(product.updated_at),
        'djangoEditHref': reverse('reporting:product_edit', args=[product.id]),
    }


def _normalize_product_excel_header(value):
    return re.sub(r'[\s_\-()]+', '', str(value or '').strip().lower())


PRODUCT_EXCEL_HEADER_ALIASES = {
    'product_code': {'품번', '품목코드', '제품코드', '제품번호', '코드', 'productcode', 'code', 'sku'},
    'description': {'제품설명', '품목명', '제품명', '설명', 'description', 'name'},
    'specification': {'규격', '사양', 'specification', 'spec', 'model'},
    'unit': {'단위', 'unit', 'uom'},
    'standard_price': {'기준단가', '출고단가', '단가', '가격', '정상가', 'standardprice', 'price', 'unitprice'},
    'is_active': {'상태', '활성', '판매가능', '사용여부', 'isactive', 'active', 'status'},
}


def _product_excel_header_map(row):
    normalized = [_normalize_product_excel_header(cell) for cell in row]
    header_map = {}
    for index, header in enumerate(normalized):
        if not header:
            continue
        for field, aliases in PRODUCT_EXCEL_HEADER_ALIASES.items():
            if header in aliases and field not in header_map:
                header_map[field] = index
                break
    return header_map


def _product_excel_cell(value):
    if value is None:
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _product_excel_active_value(value):
    text = _product_excel_cell(value).lower()
    if not text:
        return True
    if text in {'false', '0', 'n', 'no', 'inactive', 'disabled', '비활성', '중지', '사용안함', '판매중지'}:
        return False
    return True


def _product_excel_payload_from_row(row, header_map=None):
    cells = [_product_excel_cell(value) for value in row]
    if not any(cells):
        return None

    if header_map:
        return {
            'productCode': cells[header_map['product_code']] if 'product_code' in header_map and header_map['product_code'] < len(cells) else '',
            'description': cells[header_map['description']] if 'description' in header_map and header_map['description'] < len(cells) else '',
            'specification': cells[header_map['specification']] if 'specification' in header_map and header_map['specification'] < len(cells) else '',
            'unit': cells[header_map['unit']] if 'unit' in header_map and header_map['unit'] < len(cells) else 'EA',
            'standardPrice': cells[header_map['standard_price']] if 'standard_price' in header_map and header_map['standard_price'] < len(cells) else '0',
            'isActive': _product_excel_active_value(cells[header_map['is_active']]) if 'is_active' in header_map and header_map['is_active'] < len(cells) else True,
        }

    if len(cells) >= 5:
        product_code, description, specification, unit, price = cells[:5]
    elif len(cells) >= 4:
        product_code, specification, unit, price = cells[:4]
        description = ''
    elif len(cells) >= 3:
        product_code, specification, price = cells[:3]
        description = ''
        unit = 'EA'
    else:
        return None
    return {
        'productCode': product_code,
        'description': description,
        'specification': specification,
        'unit': unit or 'EA',
        'standardPrice': price or '0',
        'isActive': True,
    }


def _product_delete_usage_counts(product):
    return {
        'deliveryItemCount': product.delivery_items.count(),
        'quoteItemCount': product.quoteitems.count(),
    }


def _product_delivery_items_summary(items):
    from decimal import Decimal

    delivery_lines = []
    total_amount = Decimal('0')
    for item in items:
        item_total = item.total_price
        if item_total is None and item.unit_price is not None:
            item_total = vat.item_gross_total(item, unit_price=(item.get_effective_unit_price() or item.unit_price))
        if item_total is not None:
            total_amount += item_total

        quantity_label = f"{item.quantity}{item.unit or 'EA'}"
        if item_total is not None:
            delivery_lines.append(f"{item.item_name}: {quantity_label} ({int(item_total):,}원)")
        else:
            delivery_lines.append(f"{item.item_name}: {quantity_label}")

    return '\n'.join(delivery_lines), int(total_amount) if total_amount > 0 else 0


def _product_delete_reference_payloads(product, limit=200):
    from reporting.models import DeliveryItem, QuoteItem

    references = []
    delivery_items = (
        DeliveryItem.objects
        .select_related(
            'schedule',
            'schedule__followup',
            'schedule__followup__company',
            'schedule__followup__department',
            'history',
            'history__followup',
            'history__followup__company',
            'history__followup__department',
        )
        .filter(product=product)
        .order_by('id')[:limit]
    )
    for item in delivery_items:
        schedule = item.schedule
        history = item.history
        followup = None
        if schedule and schedule.followup_id:
            followup = schedule.followup
        elif history and history.followup_id:
            followup = history.followup
        schedule_date = ''
        if schedule and schedule.visit_date:
            schedule_date = schedule.visit_date.strftime('%Y-%m-%d')
        elif history and history.delivery_date:
            schedule_date = history.delivery_date.strftime('%Y-%m-%d')
        elif history and history.meeting_date:
            schedule_date = history.meeting_date.strftime('%Y-%m-%d')
        elif history and history.created_at:
            schedule_date = timezone.localtime(history.created_at).strftime('%Y-%m-%d')
        schedule_type = schedule.activity_type if schedule else (history.action_type if history else '')
        schedule_type_label = (
            schedule.get_activity_type_display()
            if schedule
            else (history.get_action_type_display() if history else '납품/견적 품목')
        )
        references.append({
            'referenceType': 'deliveryItem',
            'referenceId': item.id,
            'itemName': item.item_name or product.product_code,
            'quantity': item.quantity,
            'unit': item.unit or '',
            'unitPrice': float(item.unit_price or 0),
            'quoteGroup': item.quote_group or '',
            'quoteGroupLabel': _quote_group_label(item.quote_group),
            'scheduleId': schedule.id if schedule else None,
            'historyId': history.id if history else None,
            'scheduleType': schedule_type,
            'scheduleTypeLabel': schedule_type_label,
            'scheduleDate': schedule_date,
            'customerName': (followup.customer_name or followup.manager or '') if followup else '',
            'companyName': followup.company.name if followup and followup.company_id else '',
            'departmentName': followup.department.name if followup and followup.department_id else '',
        })

    remaining_limit = max(limit - len(references), 0)
    if remaining_limit:
        quote_items = (
            QuoteItem.objects
            .select_related('quote', 'quote__followup', 'quote__followup__company', 'quote__followup__department', 'quote__schedule')
            .filter(product=product)
            .order_by('id')[:remaining_limit]
        )
        for item in quote_items:
            quote = item.quote
            followup = quote.followup if quote and quote.followup_id else None
            schedule = quote.schedule if quote and quote.schedule_id else None
            references.append({
                'referenceType': 'quoteItem',
                'referenceId': item.id,
                'itemName': product.product_code,
                'quantity': item.quantity,
                'unit': product.unit or '',
                'unitPrice': float(item.unit_price or 0),
                'quoteGroup': '',
                'quoteGroupLabel': '',
                'quoteId': quote.id if quote else None,
                'quoteNumber': quote.quote_number if quote else '',
                'scheduleId': schedule.id if schedule else None,
                'scheduleType': schedule.activity_type if schedule else 'quote',
                'scheduleTypeLabel': schedule.get_activity_type_display() if schedule else '레거시 견적',
                'scheduleDate': schedule.visit_date.strftime('%Y-%m-%d') if schedule and schedule.visit_date else '',
                'customerName': (followup.customer_name or followup.manager or '') if followup else '',
                'companyName': followup.company.name if followup and followup.company_id else '',
                'departmentName': followup.department.name if followup and followup.department_id else '',
            })

    return references


def _product_blocked_delete_result(product, message, can_replace=True):
    usage_counts = _product_delete_usage_counts(product)
    reference_count = usage_counts['deliveryItemCount'] + usage_counts['quoteItemCount']
    references = _product_delete_reference_payloads(product) if can_replace else []
    return {
        'productCode': product.product_code,
        'status': 'blocked',
        'message': message,
        'canReplace': bool(can_replace),
        'references': references,
        'referenceCount': reference_count,
        'hasMoreReferences': reference_count > len(references),
        **usage_counts,
    }


def _resolve_product_replacement(scope, replacement_value):
    replacement_text = str(replacement_value or '').strip()
    if not replacement_text:
        return None
    try:
        replacement_id = int(replacement_text)
    except (TypeError, ValueError):
        replacement_id = None
    replacement = scope.filter(id=replacement_id, is_active=True).first() if replacement_id else None
    if replacement is None:
        replacement = scope.filter(product_code=replacement_text, is_active=True).first()
    return replacement


def _replace_single_product_reference(request, product, reference_type, reference_id, replacement_product):
    """제품 참조 1건만 대체 제품으로 이동하고, 남은 참조가 없으면 원제품을 삭제한다."""
    from reporting.models import DeliveryItem, History, Product, QuoteItem, Schedule

    reference_type = str(reference_type or '').strip()
    touched_delivery_schedule_id = None
    touched_history_id = None
    replaced_reference = None

    with transaction.atomic():
        locked_product = Product.objects.select_for_update().get(pk=product.pk)
        if reference_type in ['deliveryItem', 'delivery_item', 'delivery']:
            item = (
                DeliveryItem.objects
                .select_for_update()
                .filter(id=reference_id, product=locked_product)
                .first()
            )
            if not item:
                raise ValueError('대체할 납품/견적 품목을 찾을 수 없습니다.')
            replaced_reference = {
                'referenceType': 'deliveryItem',
                'referenceId': item.id,
                'itemName': item.item_name,
            }
            if item.schedule_id:
                schedule_type = (
                    Schedule.objects
                    .filter(id=item.schedule_id)
                    .values_list('activity_type', flat=True)
                    .first()
                )
                if schedule_type == 'delivery':
                    touched_delivery_schedule_id = item.schedule_id
            if item.history_id:
                touched_history_id = item.history_id
            item.product = replacement_product
            item.item_name = replacement_product.product_code
            item.unit = replacement_product.unit or item.unit or 'EA'
            item.save()
        elif reference_type in ['quoteItem', 'quote_item', 'quote']:
            item = (
                QuoteItem.objects
                .select_for_update()
                .select_related('quote')
                .filter(id=reference_id, product=locked_product)
                .first()
            )
            if not item:
                raise ValueError('대체할 레거시 견적 품목을 찾을 수 없습니다.')
            replaced_reference = {
                'referenceType': 'quoteItem',
                'referenceId': item.id,
                'itemName': locked_product.product_code,
            }
            item.product = replacement_product
            item.save(update_fields=['product', 'subtotal'])
        else:
            raise ValueError('알 수 없는 품목 참조 유형입니다.')

        has_remaining_refs = (
            DeliveryItem.objects.filter(product=locked_product).exists()
            or QuoteItem.objects.filter(product=locked_product).exists()
        )
        product_code = locked_product.product_code
        if not has_remaining_refs:
            locked_product.delete()
            deleted_original = True
        else:
            deleted_original = False

    if touched_delivery_schedule_id:
        schedule = Schedule.objects.filter(id=touched_delivery_schedule_id).first()
        if schedule:
            _schedules_sync_delivery_histories(
                schedule,
                request.user,
                schedule.delivery_items_set.count(),
            )
    elif touched_history_id:
        history = History.objects.filter(id=touched_history_id).first()
        if history:
            delivery_text, total_delivery_amount = _product_delivery_items_summary(
                history.delivery_items_set.all().order_by('id')
            )
            history.delivery_items = delivery_text
            history.delivery_amount = total_delivery_amount if total_delivery_amount > 0 else None
            history.save(update_fields=['delivery_items', 'delivery_amount'])

    if deleted_original:
        product_result = {
            'productCode': product_code,
            'status': 'deleted',
            'message': '마지막 품목 대체 후 제품 삭제 완료',
            'canReplace': False,
            'deliveryItemCount': 0,
            'quoteItemCount': 0,
            'referenceCount': 0,
            'references': [],
            'hasMoreReferences': False,
            'replacedCount': 1,
        }
    else:
        product.refresh_from_db()
        product_result = _product_blocked_delete_result(product, '품목 1건 대체 완료. 남은 품목을 계속 대체하세요.')
        product_result['replacedCount'] = 1

    return {
        'success': True,
        'productCode': product_code,
        'deletedOriginal': deleted_original,
        'replacementProductId': replacement_product.id,
        'replacementProductCode': replacement_product.product_code,
        'replacedReference': replaced_reference,
        'result': product_result,
        'message': product_result['message'],
    }


def _parse_product_price(value):
    from decimal import Decimal, InvalidOperation

    normalized = str(value if value is not None else '').replace(',', '').strip()
    if not normalized:
        return Decimal('0')
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise ValueError('기준단가는 숫자로 입력해야 합니다.')


def _product_payload_from_dict(data):
    product_code = str(data.get('productCode') or data.get('product_code') or data.get('code') or '').strip()
    if not product_code:
        raise ValueError('품번은 필수입니다.')

    description = str(
        data.get('description')
        or data.get('productName')
        or data.get('product_name')
        or data.get('name')
        or ''
    ).strip()
    specification = str(data.get('specification') or data.get('spec') or '').strip()
    unit = str(data.get('unit') or 'EA').strip() or 'EA'
    standard_price = _parse_product_price(
        data.get('standardPrice')
        if data.get('standardPrice') is not None
        else data.get('standard_price')
        if data.get('standard_price') is not None
        else data.get('price')
    )
    is_active = data.get('isActive', data.get('is_active', True))
    if isinstance(is_active, str):
        is_active = is_active.strip().lower() not in ['false', '0', 'no', 'off', '비활성']

    return {
        'product_code': product_code,
        'description': description,
        'specification': specification,
        'unit': unit,
        'standard_price': standard_price,
        'is_active': bool(is_active),
    }


def _upsert_product_from_payload(request, payload):
    from reporting.models import Product

    if not _product_can_manage(request):
        return None, False, False, ['권한 없음']

    existing = Product.objects.filter(product_code=payload['product_code']).first()
    changed_fields = []

    if existing:
        if not _product_can_manage(request, existing):
            return None, False, False, ['권한 없음']

        field_map = {
            'specification': payload['specification'],
            'unit': payload['unit'],
            'standard_price': payload['standard_price'],
            'is_active': payload['is_active'],
        }
        if payload['description']:
            field_map['description'] = payload['description']
        for field, value in field_map.items():
            if getattr(existing, field) != value:
                setattr(existing, field, value)
                changed_fields.append(field)
        if existing.is_promo or existing.promo_price or existing.promo_start or existing.promo_end:
            existing.is_promo = False
            existing.promo_price = None
            existing.promo_start = None
            existing.promo_end = None
            changed_fields.extend(['is_promo', 'promo_price', 'promo_start', 'promo_end'])
        if changed_fields:
            existing.save(update_fields=sorted(set(changed_fields + ['updated_at'])))
            return existing, False, True, sorted(set(changed_fields))
        return existing, False, False, []

    product = Product.objects.create(
        product_code=payload['product_code'],
        description=payload['description'] or payload['product_code'],
        specification=payload['specification'],
        unit=payload['unit'],
        standard_price=payload['standard_price'],
        is_active=payload['is_active'],
        is_promo=False,
        promo_price=None,
        promo_start=None,
        promo_end=None,
        created_by=request.user,
    )
    return product, True, False, ['created']


@never_cache
@require_http_methods(["GET"])
def products_management_api(request):
    """React 제품관리 목록 API."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    can_manage = _product_can_manage(request)
    products = _product_scope_queryset(request, include_inactive=True)
    search_query = request.GET.get('q') or request.GET.get('search') or ''
    status = request.GET.get('status') or ''

    total_count = products.count()
    active_count = products.filter(is_active=True).count()
    inactive_count = total_count - active_count

    if search_query:
        products = products.filter(
            Q(product_code__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(specification__icontains=search_query)
        )
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)

    products = _product_usage_annotations(products)
    filtered_count = products.count()

    sort_by = request.GET.get('sort') or 'code'
    sort_order = request.GET.get('order') or 'asc'
    sort_fields = {
        'code': 'product_code',
        'description': 'description',
        'specification': 'specification',
        'unit': 'unit',
        'price': 'standard_price',
        'status': 'is_active',
        'quoteCount': 'quote_count',
        'deliveryCount': 'delivery_count',
        'updatedAt': 'updated_at',
    }
    order_field = sort_fields.get(sort_by, 'product_code')
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    products = products.order_by(order_field, 'product_code')

    try:
        page_size = min(max(int(request.GET.get('page_size', 50)), 10), 200)
    except (TypeError, ValueError):
        page_size = 50
    paginator = Paginator(products, page_size)
    page_obj = paginator.get_page(request.GET.get('page') or 1)
    page_products = list(page_obj)
    try:
        selected_product_id = int(request.GET.get('selected_product_id') or request.GET.get('product') or 0)
    except (TypeError, ValueError):
        selected_product_id = 0
    if selected_product_id and all(product.id != selected_product_id for product in page_products):
        selected_product = _product_usage_annotations(
            _product_scope_queryset(request, include_inactive=True).filter(id=selected_product_id),
        ).first()
        if selected_product:
            page_products.insert(0, selected_product)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'scope': {
            'canManage': can_manage,
            'label': '전체 제품' if get_user_profile(request.user).is_admin() else '접근 가능 제품',
        },
        'metrics': {
            'totalProducts': total_count,
            'activeProducts': active_count,
            'inactiveProducts': inactive_count,
            'filteredProducts': filtered_count,
        },
        'products': [_product_payload(product) for product in page_products],
        'pagination': {
            'page': page_obj.number,
            'pageSize': page_size,
            'totalPages': paginator.num_pages,
            'totalCount': filtered_count,
            'hasNext': page_obj.has_next(),
            'hasPrevious': page_obj.has_previous(),
        },
        'links': {
            'djangoList': reverse('reporting:product_list'),
            'excelDownload': reverse('reporting:products_excel_export_api'),
            'bulkUpsert': reverse('reporting:products_bulk_upsert_api') if can_manage else '',
            'bulkDelete': reverse('reporting:products_bulk_delete_api') if can_manage else '',
            'save': reverse('reporting:product_save_api') if can_manage else '',
            'excelImport': reverse('reporting:products_excel_import_api') if can_manage else '',
        },
    })


@login_required
@require_POST
def product_save_api(request, product_id=None):
    """React 제품 단일 생성/수정 API."""
    from reporting.models import Product

    if not _product_can_manage(request):
        return JsonResponse({'success': False, 'error': _product_manage_denied_message(request)}, status=403)

    try:
        payload = _product_payload_from_dict(json.loads(request.body or '{}'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'}, status=400)
    except ValueError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    if product_id is None:
        product, created, updated, changed_fields = _upsert_product_from_payload(request, payload)
        if product is None:
            return JsonResponse({'success': False, 'error': '이 제품을 저장할 권한이 없습니다.'}, status=403)
    else:
        product = get_object_or_404(Product, id=product_id)
        if not _product_can_manage(request, product):
            return JsonResponse({'success': False, 'error': '이 제품을 수정할 권한이 없습니다.'}, status=403)
        duplicate = Product.objects.filter(product_code=payload['product_code']).exclude(id=product.id).first()
        if duplicate:
            return JsonResponse({'success': False, 'error': f'품번 "{payload["product_code"]}"은(는) 이미 등록되어 있습니다.'}, status=400)

        changed_fields = []
        for field in ['product_code', 'description', 'specification', 'unit', 'standard_price', 'is_active']:
            if getattr(product, field) != payload[field]:
                setattr(product, field, payload[field])
                changed_fields.append(field)
        if product.is_promo or product.promo_price or product.promo_start or product.promo_end:
            product.is_promo = False
            product.promo_price = None
            product.promo_start = None
            product.promo_end = None
            changed_fields.extend(['is_promo', 'promo_price', 'promo_start', 'promo_end'])
        if changed_fields:
            product.save(update_fields=sorted(set(changed_fields + ['updated_at'])))
        created = False
        updated = bool(changed_fields)

    product = _product_usage_annotations(Product.objects.filter(id=product.id)).first()
    return JsonResponse({
        'success': True,
        'created': created,
        'updated': updated,
        'changedFields': changed_fields,
        'product': _product_payload(product),
        'message': '제품이 등록되었습니다.' if created else ('제품이 수정되었습니다.' if updated else '변경된 내용이 없습니다.'),
    })


@login_required
@require_POST
def products_bulk_upsert_api(request):
    """Ecount/Excel 붙여넣기 기반 제품 일괄 등록 및 갱신 API."""
    if not _product_can_manage(request):
        return JsonResponse({'success': False, 'error': _product_manage_denied_message(request)}, status=403)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'}, status=400)

    items = body.get('products') or body.get('items') or []
    if not items:
        return JsonResponse({'success': False, 'error': '등록할 제품 데이터가 없습니다.'}, status=400)

    created_count = 0
    updated_count = 0
    unchanged_count = 0
    error_count = 0
    results = []

    for index, item in enumerate(items, start=1):
        try:
            payload = _product_payload_from_dict(item)
            product, created, updated, changed_fields = _upsert_product_from_payload(request, payload)
            if product is None:
                raise PermissionError('권한 없음')
            if created:
                created_count += 1
                status = 'created'
            elif updated:
                updated_count += 1
                status = 'updated'
            else:
                unchanged_count += 1
                status = 'unchanged'
            results.append({
                'row': index,
                'productCode': payload['product_code'],
                'status': status,
                'changedFields': changed_fields,
            })
        except Exception as exc:
            error_count += 1
            results.append({
                'row': index,
                'productCode': str(item.get('productCode') or item.get('product_code') or item.get('code') or '').strip(),
                'status': 'error',
                'error': str(exc),
            })

    return JsonResponse({
        'success': error_count == 0,
        'createdCount': created_count,
        'updatedCount': updated_count,
        'unchangedCount': unchanged_count,
        'errorCount': error_count,
        'results': results[:200],
        'message': f'등록 {created_count}건, 수정 {updated_count}건, 변경 없음 {unchanged_count}건, 오류 {error_count}건',
    }, status=200 if error_count == 0 else 207)


@require_http_methods(["POST"])
def products_excel_import_api(request):
    """Uploaded XLSX product import using the same upsert rules as React paste."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    if not _product_can_manage(request):
        return JsonResponse({'success': False, 'error': _product_manage_denied_message(request)}, status=403)

    uploaded_file = request.FILES.get('file') or request.FILES.get('excel') or request.FILES.get('xlsx')
    if not uploaded_file:
        return JsonResponse({'success': False, 'error': '업로드할 엑셀 파일을 선택하세요.'}, status=400)
    if not str(uploaded_file.name).lower().endswith('.xlsx'):
        return JsonResponse({'success': False, 'error': '제품 업로드는 .xlsx 파일만 지원합니다.'}, status=400)

    workbook = None
    try:
        from openpyxl import load_workbook

        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
        worksheet = workbook.active
        rows = list(worksheet.iter_rows(values_only=True))
    except Exception as exc:
        logger.error('제품 엑셀 업로드 파싱 실패: %s', exc, exc_info=True)
        return JsonResponse({'success': False, 'error': '엑셀 파일을 읽지 못했습니다.'}, status=400)
    finally:
        if workbook:
            try:
                workbook.close()
            except Exception:
                pass

    if not rows:
        return JsonResponse({'success': False, 'error': '엑셀 파일에 제품 데이터가 없습니다.'}, status=400)

    first_row_map = _product_excel_header_map(rows[0])
    has_header = 'product_code' in first_row_map and 'standard_price' in first_row_map
    header_map = first_row_map if has_header else None
    data_rows = rows[1:] if has_header else rows

    created_count = 0
    updated_count = 0
    unchanged_count = 0
    error_count = 0
    results = []

    for row_offset, row in enumerate(data_rows, start=2 if has_header else 1):
        raw_payload = _product_excel_payload_from_row(row, header_map=header_map)
        if raw_payload is None:
            continue
        try:
            payload = _product_payload_from_dict(raw_payload)
            product, created, updated, changed_fields = _upsert_product_from_payload(request, payload)
            if product is None:
                raise PermissionError('권한 없음')
            if created:
                created_count += 1
                status = 'created'
            elif updated:
                updated_count += 1
                status = 'updated'
            else:
                unchanged_count += 1
                status = 'unchanged'
            results.append({
                'row': row_offset,
                'productCode': payload['product_code'],
                'status': status,
                'changedFields': changed_fields,
            })
        except Exception as exc:
            error_count += 1
            results.append({
                'row': row_offset,
                'productCode': str(raw_payload.get('productCode') or '').strip(),
                'status': 'error',
                'error': str(exc),
            })

    if not results:
        return JsonResponse({'success': False, 'error': '엑셀 파일에서 제품 행을 찾지 못했습니다.'}, status=400)

    return JsonResponse({
        'success': error_count == 0,
        'createdCount': created_count,
        'updatedCount': updated_count,
        'unchangedCount': unchanged_count,
        'errorCount': error_count,
        'results': results[:500],
        'message': f'엑셀 반영: 등록 {created_count}건, 수정 {updated_count}건, 변경 없음 {unchanged_count}건, 오류 {error_count}건',
    }, status=200 if error_count == 0 else 207)


@login_required
@require_POST
def products_bulk_delete_api(request):
    """붙여넣은 품번 기준 제품 일괄 삭제 API."""
    if not _product_can_manage(request):
        return JsonResponse({'success': False, 'error': _product_manage_denied_message(request)}, status=403)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'}, status=400)

    product_codes = body.get('productCodes') or body.get('product_codes') or []
    normalized_codes = []
    for code in product_codes:
        value = str(code or '').strip()
        if value and value not in normalized_codes:
            normalized_codes.append(value)
    if not normalized_codes:
        return JsonResponse({'success': False, 'error': '삭제할 품번이 없습니다.'}, status=400)

    scope = _product_scope_queryset(request, include_inactive=True)
    deleted_count = 0
    blocked_count = 0
    missing_count = 0
    replaced_count = 0
    results = []

    for code in normalized_codes:
        product = scope.filter(product_code=code).first()
        if not product:
            missing_count += 1
            results.append({
                'productCode': code,
                'status': 'missing',
                'message': '제품 없음 또는 권한 없음',
                'canReplace': False,
                'deliveryItemCount': 0,
                'quoteItemCount': 0,
            })
            continue
        if not _product_can_manage(request, product):
            blocked_count += 1
            results.append({
                'productCode': code,
                'status': 'blocked',
                'message': '권한 없음',
                'canReplace': False,
                **_product_delete_usage_counts(product),
            })
            continue
        if product.delivery_items.exists() or product.quoteitems.exists():
            blocked_count += 1
            results.append(_product_blocked_delete_result(product, '견적/납품에 사용된 제품입니다. 아래 품목별로 대체 제품을 선택하세요.'))
            continue

        product.delete()
        deleted_count += 1
        results.append({
            'productCode': code,
            'status': 'deleted',
            'message': '삭제 완료',
            'canReplace': False,
            'deliveryItemCount': 0,
            'quoteItemCount': 0,
            'replacedCount': 0,
        })

    return JsonResponse({
        'success': True,
        'deletedCount': deleted_count,
        'blockedCount': blocked_count,
        'missingCount': missing_count,
        'replacedCount': replaced_count,
        'results': results[:300],
        'message': f'삭제 {deleted_count}건, 대체 {replaced_count}건, 차단 {blocked_count}건, 없음 {missing_count}건',
    })


@login_required
@require_POST
def product_replace_reference_api(request):
    """제품 삭제 차단 참조 1건을 사용자가 선택한 대체 제품으로 이동한다."""
    if not _product_can_manage(request):
        return JsonResponse({'success': False, 'error': _product_manage_denied_message(request)}, status=403)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'}, status=400)

    product_code = str(body.get('productCode') or body.get('product_code') or '').strip()
    reference_type = body.get('referenceType') or body.get('reference_type') or ''
    reference_id_raw = body.get('referenceId') or body.get('reference_id')
    replacement_value = (
        body.get('replacementProductId')
        or body.get('replacement_product_id')
        or body.get('replacementProductCode')
        or body.get('replacement_product_code')
    )
    if not product_code:
        return JsonResponse({'success': False, 'error': '대체할 원제품 품번이 없습니다.'}, status=400)
    try:
        reference_id = int(reference_id_raw)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': '대체할 품목을 선택하세요.'}, status=400)

    scope = _product_scope_queryset(request, include_inactive=True)
    product = scope.filter(product_code=product_code).first()
    if not product:
        return JsonResponse({'success': False, 'error': '원제품을 찾을 수 없거나 권한이 없습니다.'}, status=404)
    if not _product_can_manage(request, product):
        return JsonResponse({'success': False, 'error': '제품 삭제/대체 권한이 없습니다.'}, status=403)

    replacement = _resolve_product_replacement(scope, replacement_value)
    if not replacement:
        return JsonResponse({'success': False, 'error': '대체 제품을 찾을 수 없거나 비활성 상태입니다.'}, status=400)
    if replacement.id == product.id:
        return JsonResponse({'success': False, 'error': '삭제할 제품 자신은 대체 제품으로 사용할 수 없습니다.'}, status=400)

    try:
        result = _replace_single_product_reference(
            request,
            product,
            reference_type,
            reference_id,
            replacement,
        )
    except Exception as exc:
        logger.error('제품 참조 1건 대체 실패 (%s -> %s): %s', product_code, replacement.product_code, exc, exc_info=True)
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)

    return JsonResponse(result)


@login_required
def products_excel_export_api(request):
    """접근 가능한 전체 제품 XLSX 다운로드."""
    from django.http import HttpResponse
    from openpyxl import Workbook

    products = _product_usage_annotations(
        _product_scope_queryset(request, include_inactive=True),
    ).order_by('product_code')

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'products'
    headers = ['품번', '제품설명', '규격', '단위', '기준단가', '상태', '견적횟수', '판매횟수', '등록자', '수정일']
    sheet.append(headers)
    for product in products:
        sheet.append([
            product.product_code,
            product.description or '',
            product.specification or '',
            product.unit or 'EA',
            int(product.standard_price or 0),
            '활성' if product.is_active else '비활성',
            int(getattr(product, 'quote_count', 0) or 0),
            int(getattr(product, 'delivery_count', 0) or 0),
            _user_display_name(product.created_by) if product.created_by else '공용',
            timezone.localtime(product.updated_at).strftime('%Y-%m-%d %H:%M') if product.updated_at else '',
        ])

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or '')) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 10), 40)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"products-{timezone.localdate().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


@never_cache
@require_http_methods(["GET"])
def product_api_list(request):
    """제품 목록 API (AJAX용) - 견적/납품 작성 시 제품 선택"""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    search = request.GET.get('search', '')
    products = get_accessible_products(request)
    
    if search:
        products = products.filter(
            Q(product_code__icontains=search) |
            Q(description__icontains=search) |
            Q(specification__icontains=search)
        )
    
    total_count = products.count()
    products = products.order_by('product_code')
    try:
        limit = int(request.GET.get('limit') or 0)
    except (TypeError, ValueError):
        limit = 0
    if limit > 0:
        limit = min(max(limit, 1), 500)
        products = products[:limit]
    
    products_data = [{
        'id': p.id,
        'product_code': p.product_code,
        'name': p.product_code,
        'description': p.description,  # description 필드 추가
        'unit': p.unit or 'EA',
        'specification': p.specification or '',
        'standard_price': float(p.standard_price),
        'current_price': float(p.standard_price),
        'is_promo': False,
    } for p in products]
    
    return JsonResponse({
        'products': products_data,
        'count': len(products_data),
        'totalCount': total_count,
        'hasMore': bool(limit and total_count > len(products_data)),
    })


# ============================================================
# 서류 템플릿 관리 뷰
# ============================================================

def _document_template_user_can_manage(user, template=None):
    if user.is_superuser:
        return True
    user_profile = get_user_profile(user)
    if user_profile.role not in ['admin', 'manager']:
        return False
    if template is None:
        return bool(user_profile.company)
    return template.company_id == getattr(user_profile.company, 'id', None)


def _document_template_user_can_access(user, template):
    if user.is_superuser:
        return True
    user_profile = get_user_profile(user)
    return template.company_id == getattr(user_profile.company, 'id', None)


def _document_template_queryset_for_user(user):
    queryset = DocumentTemplate.objects.filter(is_active=True).select_related('created_by', 'company')
    if user.is_superuser:
        return queryset
    user_profile = get_user_profile(user)
    if not user_profile.company:
        return queryset.none()
    return queryset.filter(company=user_profile.company)


def _document_template_file_name(template):
    if not template.file:
        return ''
    return os.path.basename(template.file.name)


def _document_template_payload(template, actor):
    return {
        'id': template.id,
        'documentType': template.document_type,
        'documentTypeLabel': template.get_document_type_display(),
        'name': template.name,
        'description': template.description or '',
        'fileType': template.file_type,
        'fileName': _document_template_file_name(template),
        'isDefault': template.is_default,
        'isActive': template.is_active,
        'company': {
            'id': template.company_id,
            'name': template.company.name if template.company else '',
        },
        'createdBy': _user_display_name(template.created_by) if template.created_by else '',
        'createdAt': _datetime_or_none(template.created_at),
        'updatedAt': _datetime_or_none(template.updated_at),
        'downloadHref': reverse('reporting:document_template_download', args=[template.id]),
        'toggleDefaultUrl': reverse('reporting:document_template_api_toggle_default', args=[template.id]),
        'updateUrl': reverse('reporting:document_template_api_update', args=[template.id]),
        'deleteUrl': reverse('reporting:document_template_api_delete', args=[template.id]),
        'djangoEditHref': reverse('reporting:document_template_edit', args=[template.id]),
        'canManage': _document_template_user_can_manage(actor, template),
        'canToggleDefault': _document_template_user_can_access(actor, template),
    }


def _document_generation_log_queryset_for_user(user):
    queryset = DocumentGenerationLog.objects.select_related(
        'company',
        'user',
        'schedule',
        'schedule__followup',
        'schedule__followup__company',
        'schedule__followup__department',
    )
    if user.is_superuser:
        return queryset
    user_profile = get_user_profile(user)
    if not user_profile.company:
        return queryset.none()
    return queryset.filter(company=user_profile.company)


def _document_generation_log_payload(log):
    schedule = log.schedule
    followup = schedule.followup if schedule else None
    file_payload = _document_generation_file_payload(log) if log.file else None
    return {
        'id': log.id,
        'documentType': log.document_type,
        'documentTypeLabel': log.get_document_type_display(),
        'transactionNumber': log.transaction_number,
        'outputFormat': log.output_format,
        'outputFormatLabel': log.get_output_format_display(),
        'quoteGroup': log.quote_group or '',
        'quoteGroupLabel': _quote_group_label(log.quote_group),
        'filename': file_payload['filename'] if file_payload else '',
        'fileSize': file_payload['fileSize'] if file_payload else 0,
        'downloadHref': file_payload['downloadHref'] if file_payload else '',
        'createdAt': _datetime_or_none(log.created_at),
        'createdBy': _user_display_name(log.user) if log.user else '',
        'company': {
            'id': log.company_id,
            'name': log.company.name if log.company else '',
        },
        'schedule': {
            'id': schedule.id if schedule else None,
            'visitDate': _date_or_none(schedule.visit_date) if schedule else None,
            'activityType': schedule.activity_type if schedule else '',
            'activityTypeLabel': schedule.get_activity_type_display() if schedule else '',
            'status': schedule.status if schedule else '',
            'statusLabel': schedule.get_status_display() if schedule else '',
            'href': f'/schedules/{schedule.id}/' if schedule else '',
            'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        },
        'customerName': followup.customer_name if followup else '',
        'customerCompany': followup.company.name if followup and followup.company else '',
        'departmentName': followup.department.name if followup and followup.department else '',
    }


def _document_template_document_types_payload():
    return [
        {'value': value, 'label': label}
        for value, label in DocumentTemplate.DOCUMENT_TYPE_CHOICES
    ]


def _document_template_variable_groups_payload():
    groups = [
        ('기본 정보', ['년', '월', '일', '거래번호', '발행일', '날짜', '일정날짜', '유효일+30']),
        ('고객 / 거래처 정보', ['고객명', '담당자', '업체명', '학교명', '부서명', '연구실', '이메일', '담당자이메일', '연락처', '전화번호']),
        ('영업담당자', ['실무자', '영업담당자', '담당영업', '영업담당자이메일']),
        ('회사 / 견적 정보', ['회사명', '견적번호', '견적구분', '견적명', '견적제목', '메모', '기타사항', '견적기타사항']),
        ('금액', ['공급가액', '소계', '부가세액', '부가세', '총액', '합계', '총액한글', '한글금액']),
        (
            '품목 (N = 1, 2, 3 ... 순번)',
            [
                '품목N_이름',
                '품목N_품목명',
                '품목N_수량',
                '품목N_단위',
                '품목N_규격',
                '품목N_설명',
                '품목N_옵션',
                '품목N_옵션설명',
                '품목N_적요',
                '품목N_비고',
                '품목N_기준단가',
                '품목N_할인율',
                '품목N_할인단가',
                '품목N_단가',
                '품목N_공급가액',
                '품목N_부가세액',
                '품목N_금액',
                '품목N_총액',
            ],
        ),
    ]
    return [
        {
            'label': label,
            'variables': [
                {
                    'key': key,
                    'token': '{{' + key.replace('N', '1') + '}}' if key.startswith('품목N_') else '{{' + key + '}}',
                    'display': '{{' + key + '}}',
                }
                for key in keys
            ],
        }
        for label, keys in groups
    ]


def _document_template_can_create_payload(request, user_profile):
    can_manage = request.user.is_superuser or user_profile.role in ['admin', 'manager']
    has_company = request.user.is_superuser or bool(user_profile.company)
    if not can_manage:
        message = '서류 템플릿 등록은 관리자 또는 매니저만 가능합니다.'
    elif not has_company:
        message = '소속 회사가 설정되어 있지 않습니다.'
    else:
        message = ''
    return can_manage and has_company, message


def _document_template_api_context(request, templates):
    user_profile = get_user_profile(request.user)
    base_queryset = _document_template_queryset_for_user(request.user)
    valid_types = {value for value, _label in DocumentTemplate.DOCUMENT_TYPE_CHOICES}
    document_type_filter = request.GET.get('type', '')
    log_queryset = _document_generation_log_queryset_for_user(request.user)
    if document_type_filter in valid_types:
        log_queryset = log_queryset.filter(document_type=document_type_filter)
    elif document_type_filter:
        log_queryset = log_queryset.none()
    type_counts = {
        item['document_type']: item['count']
        for item in base_queryset.values('document_type').annotate(count=Count('id'))
    }
    default_counts = {
        item['document_type']: item['count']
        for item in base_queryset.filter(is_default=True).values('document_type').annotate(count=Count('id'))
    }
    can_create, create_message = _document_template_can_create_payload(request, user_profile)
    companies = []
    if request.user.is_superuser:
        companies = [
            {'id': company.id, 'name': company.name}
            for company in UserCompany.objects.order_by('name')
        ]

    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'currentUser': {
            'id': request.user.id,
            'name': _user_display_name(request.user),
            'role': user_profile.role,
            'roleLabel': user_profile.get_role_display(),
            'company': user_profile.company.name if user_profile.company else '',
            'isSuperuser': request.user.is_superuser,
        },
        'filters': {
            'type': request.GET.get('type', ''),
        },
        'documentTypes': _document_template_document_types_payload(),
        'templateVariableGroups': _document_template_variable_groups_payload(),
        'summary': {
            'totalTemplates': base_queryset.count(),
            'defaultTemplates': base_queryset.filter(is_default=True).count(),
            'generatedToday': log_queryset.filter(created_at__date=timezone.localdate()).count(),
            'recentGenerationCount': log_queryset.count(),
            'byType': [
                {
                    'type': value,
                    'label': label,
                    'count': type_counts.get(value, 0),
                    'defaultCount': default_counts.get(value, 0),
                }
                for value, label in DocumentTemplate.DOCUMENT_TYPE_CHOICES
            ],
        },
        'create': {
            'canCreate': can_create,
            'message': create_message,
            'submitUrl': reverse('reporting:document_template_api_create'),
            'djangoCreateHref': reverse('reporting:document_template_create'),
            'companies': companies,
        },
        'links': {
            'self': '/documents/',
            'djangoList': reverse('reporting:document_template_list'),
            'scheduleList': '/schedules/',
            'scheduleCalendar': '/schedules/calendar/',
        },
        'templates': [
            _document_template_payload(template, request.user)
            for template in templates
        ],
        'recentGenerations': [
            _document_generation_log_payload(log)
            for log in log_queryset.order_by('-created_at')[:10]
        ],
    }


def _document_template_validate_file(file, required=False):
    if not file:
        if required:
            return None, JsonResponse({'success': False, 'error': '파일을 선택해주세요.'}, status=400)
        return None, None
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in ['.xlsx', '.xls']:
        return None, JsonResponse({'success': False, 'error': '엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.'}, status=400)
    return 'xlsx', None


def _document_template_company_from_request(request):
    if request.user.is_superuser:
        company_id = request.POST.get('companyId') or request.POST.get('company')
        if not company_id:
            return None, JsonResponse({'success': False, 'error': '회사를 선택해주세요.'}, status=400)
        try:
            return UserCompany.objects.get(pk=company_id), None
        except (UserCompany.DoesNotExist, ValueError):
            return None, JsonResponse({'success': False, 'error': '올바른 회사를 선택해주세요.'}, status=400)
    user_profile = get_user_profile(request.user)
    if not user_profile.company:
        return None, JsonResponse({'success': False, 'error': '소속 회사가 설정되어 있지 않습니다.'}, status=400)
    return user_profile.company, None


def _document_template_mutation_values(request, require_file=False):
    document_type = (request.POST.get('documentType') or request.POST.get('document_type') or '').strip()
    valid_types = {value for value, _label in DocumentTemplate.DOCUMENT_TYPE_CHOICES}
    if document_type not in valid_types:
        return None, JsonResponse({'success': False, 'error': '서류 종류를 선택해주세요.'}, status=400)

    name = (request.POST.get('name') or '').strip()
    if not name:
        return None, JsonResponse({'success': False, 'error': '서류명을 입력해주세요.'}, status=400)

    file = request.FILES.get('file')
    file_type, error_response = _document_template_validate_file(file, required=require_file)
    if error_response:
        return None, error_response

    return {
        'document_type': document_type,
        'name': name,
        'description': request.POST.get('description', ''),
        'is_default': str(request.POST.get('isDefault') or request.POST.get('is_default') or '').lower() in ['1', 'true', 'on', 'yes'],
        'file': file,
        'file_type': file_type,
    }, None


@never_cache
@require_http_methods(["GET"])
def document_templates_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    templates = _document_template_queryset_for_user(request.user)
    document_type = request.GET.get('type')
    valid_types = {value for value, _label in DocumentTemplate.DOCUMENT_TYPE_CHOICES}
    if document_type and document_type in valid_types:
        templates = templates.filter(document_type=document_type)
    elif document_type:
        templates = templates.none()

    templates = templates.order_by('-is_default', '-created_at')
    return JsonResponse(_document_template_api_context(request, templates))


@require_http_methods(["POST"])
def document_template_create_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    if not _document_template_user_can_manage(request.user):
        return JsonResponse({'success': False, 'error': '서류 템플릿 등록 권한이 없습니다.'}, status=403)

    company, error_response = _document_template_company_from_request(request)
    if error_response:
        return error_response
    values, error_response = _document_template_mutation_values(request, require_file=True)
    if error_response:
        return error_response

    template = DocumentTemplate.objects.create(
        company=company,
        document_type=values['document_type'],
        name=values['name'],
        description=values['description'],
        is_default=values['is_default'],
        file=values['file'],
        file_type=values['file_type'],
        created_by=request.user,
    )

    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'서류 "{template.name}"이(가) 등록되었습니다.',
        'template': _document_template_payload(template, request.user),
    })


@require_http_methods(["POST"])
def document_template_update_api(request, pk):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    template = get_object_or_404(DocumentTemplate, pk=pk, is_active=True)
    if not _document_template_user_can_manage(request.user, template):
        return JsonResponse({'success': False, 'error': '서류 템플릿 수정 권한이 없습니다.'}, status=403)

    values, error_response = _document_template_mutation_values(request, require_file=False)
    if error_response:
        return error_response

    template.document_type = values['document_type']
    template.name = values['name']
    template.description = values['description']
    template.is_default = values['is_default']
    if values['file']:
        template.file = values['file']
        template.file_type = values['file_type']
    template.save()

    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'서류 "{template.name}"이(가) 수정되었습니다.',
        'template': _document_template_payload(template, request.user),
    })


@require_http_methods(["POST"])
def document_template_delete_api(request, pk):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    template = get_object_or_404(DocumentTemplate, pk=pk, is_active=True)
    if not _document_template_user_can_manage(request.user, template):
        return JsonResponse({'success': False, 'error': '서류 템플릿 삭제 권한이 없습니다.'}, status=403)

    template.is_active = False
    template.save(update_fields=['is_active', 'updated_at'])

    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': f'서류 "{template.name}"이(가) 삭제되었습니다.',
    })


@require_http_methods(["POST"])
def document_template_toggle_default_api(request, pk):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    template = get_object_or_404(DocumentTemplate, pk=pk, is_active=True)
    if not _document_template_user_can_access(request.user, template):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

    template.is_default = not template.is_default
    template.save()

    return JsonResponse({
        'success': True,
        'source': 'django',
        'isDefault': template.is_default,
        'template': _document_template_payload(template, request.user),
    })


@login_required
def document_template_download(request, pk):
    """서류 템플릿 다운로드"""
    from reporting.models import DocumentTemplate
    from django.http import FileResponse
    from django.shortcuts import redirect as django_redirect
    import os
    
    template = get_object_or_404(DocumentTemplate, pk=pk)
    
    # 권한 체크 (관리자는 모든 서류 다운로드 가능)
    if not request.user.is_superuser:
        if template.company != request.user.userprofile.company:
            messages.error(request, '다른 회사의 서류는 다운로드할 수 없습니다.')
            return django_redirect('reporting:document_template_list')
    
    if not template.file:
        messages.error(request, '파일이 존재하지 않습니다.')
        return django_redirect('reporting:document_template_list')
    
    try:
        # CloudinaryField는 URL로 리다이렉트, FileField는 파일 다운로드
        if hasattr(template.file, 'public_id'):
            # CloudinaryField - URL로 리다이렉트
            return django_redirect(template.file.url)
        else:
            # FileField - 로컬 파일 다운로드
            file_path = template.file.path
            file_name = os.path.basename(file_path)
            
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=file_name
            )
            return response
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {e}")
        messages.error(request, '파일 다운로드에 실패했습니다.')
        return django_redirect('reporting:document_template_list')


@login_required
def generated_document_download(request, log_id):
    """생성/등록된 서류 파일 다운로드."""
    from urllib.parse import quote

    log = get_object_or_404(
        DocumentGenerationLog.objects.select_related('company', 'schedule', 'schedule__user'),
        pk=log_id,
    )

    if log.schedule:
        if not can_access_user_data(request.user, log.schedule.user):
            return HttpResponseForbidden('접근 권한이 없습니다.')
    elif not request.user.is_superuser:
        user_profile = get_user_profile(request.user)
        if not user_profile.company or log.company_id != user_profile.company_id:
            return HttpResponseForbidden('접근 권한이 없습니다.')

    if not log.file:
        raise Http404('등록된 파일이 없습니다.')

    filename = _document_generation_file_name(log) or os.path.basename(log.file.name)
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    response = FileResponse(log.file.open('rb'), content_type=content_type)
    encoded_filename = quote(filename)
    response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
    response['X-Filename'] = encoded_filename
    response['Access-Control-Expose-Headers'] = 'X-Filename'
    return response


@login_required
@require_POST
def generated_document_delete(request, log_id):
    """일정에 등록된 생성 서류 파일을 삭제한다."""
    log = get_object_or_404(
        DocumentGenerationLog.objects.select_related('company', 'schedule', 'schedule__user'),
        pk=log_id,
    )

    if not log.schedule or not _schedules_can_edit(request.user, log.schedule):
        return JsonResponse({'success': False, 'error': '등록 서류 삭제 권한이 없습니다.'}, status=403)

    filename = _document_generation_file_name(log) or '등록 서류'
    if log.file:
        try:
            log.file.delete(save=False)
        except Exception as exc:
            logger.warning(f"[서류삭제] 생성 서류 파일 삭제 실패 - log_id={log.id}: {exc}")
    log.delete()
    return JsonResponse({
        'success': True,
        'message': f'{filename}를 삭제했습니다.',
    })


def _document_money(value):
    return f"{int(value or 0):,}"


def _document_truthy_request_option(request, *names):
    truthy_values = {'1', 'true', 'yes', 'on'}
    for source in (getattr(request, 'GET', None), getattr(request, 'POST', None)):
        if not source:
            continue
        for name in names:
            if name in source:
                return str(source.get(name)).strip().lower() in truthy_values
    return False


def _document_hide_base_unit_price(request, document_type):
    if document_type != 'quotation':
        return False
    return _document_truthy_request_option(
        request,
        'hide_base_unit_price',
        'hideBaseUnitPrice',
        'hide_standard_price',
        'hideStandardPrice',
    )


def _document_base_unit_price_display(price_info, hide_base_unit_price=False, document_type='quotation'):
    if document_type != 'quotation':
        return _document_money(price_info['effective_unit_price'])
    if hide_base_unit_price:
        return ''
    return _document_money(price_info['base_unit_price'])


def _document_item_prices(item):
    from decimal import Decimal, ROUND_HALF_UP

    base_unit_price = Decimal(str(item.unit_price or 0))
    effective_unit_price = item.get_effective_unit_price() or base_unit_price
    discount_rate = Decimal(str(item.discount_rate or 0))
    discount_unit_price = _schedules_discount_unit_price_or_none(item)
    if discount_unit_price is not None and base_unit_price > 0 and discount_rate <= 0:
        discount_rate = (
            (Decimal('1') - (effective_unit_price / base_unit_price)) * Decimal('100')
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    has_discount = (
        discount_unit_price is not None
        or discount_rate > 0
        or effective_unit_price < base_unit_price
    )
    return {
        'base_unit_price': base_unit_price,
        'effective_unit_price': effective_unit_price,
        'discount_unit_price': effective_unit_price if has_discount else None,
        'discount_rate': discount_rate if has_discount else Decimal('0'),
        'has_discount': has_discount,
    }


def _document_discount_rate_label(value):
    value = value or 0
    if not value:
        return ''
    text = f"{value:.2f}".rstrip('0').rstrip('.')
    return f"{text}%"


def _document_quote_group_selection(request, explicit_quote_group=None):
    if explicit_quote_group is not None:
        return _quote_group_key(explicit_quote_group), True

    for source in (getattr(request, 'GET', None), getattr(request, 'POST', None)):
        if not source:
            continue
        if 'quote_group' in source:
            return _quote_group_key(source.get('quote_group')), True
        if 'quoteGroup' in source:
            return _quote_group_key(source.get('quoteGroup')), True
    return '', False


def _document_delivery_items_queryset(schedule, document_type, quote_group='', quote_group_selected=False):
    queryset = DeliveryItem.objects.filter(schedule=schedule).select_related('product').order_by('id')
    if document_type == 'quotation' and quote_group_selected:
        queryset = queryset.filter(quote_group=_quote_group_key(quote_group))
    return queryset


def _ensure_xlsx_a4_print_layout(xlsx_path):
    """PDF 변환 전 XLSX 워크시트를 A4 1페이지 너비에 맞게 인쇄 설정한다."""
    import os
    import shutil
    import zipfile
    from xml.etree import ElementTree as ET

    spreadsheet_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', spreadsheet_ns)

    def qname(name):
        return f'{{{spreadsheet_ns}}}{name}'

    def ensure_child(parent, name):
        child = parent.find(qname(name))
        if child is None:
            child = ET.Element(qname(name))
            parent.append(child)
        return child

    def ensure_sheet_pr(root):
        child = root.find(qname('sheetPr'))
        if child is None:
            child = ET.Element(qname('sheetPr'))
            root.insert(0, child)
        return child

    def ensure_root_child(root, name, after_name=None):
        child = root.find(qname(name))
        if child is not None:
            return child

        child = ET.Element(qname(name))
        insert_index = len(root)
        if after_name:
            after = root.find(qname(after_name))
            if after is not None:
                insert_index = list(root).index(after) + 1
        root.insert(insert_index, child)
        return child

    temp_output = xlsx_path.replace('.xlsx', '_a4_print.xlsx')
    changed = False

    with zipfile.ZipFile(xlsx_path, 'r') as zip_in:
        with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for item in zip_in.infolist():
                data = zip_in.read(item.filename)

                if item.filename.startswith('xl/worksheets/sheet') and item.filename.endswith('.xml'):
                    try:
                        root = ET.fromstring(data)
                        sheet_pr = ensure_sheet_pr(root)
                        page_setup_pr = ensure_child(sheet_pr, 'pageSetUpPr')
                        page_setup_pr.set('fitToPage', '1')

                        page_margins = ensure_root_child(root, 'pageMargins')
                        page_margins.set('left', '0.25')
                        page_margins.set('right', '0.25')
                        page_margins.set('top', '0.35')
                        page_margins.set('bottom', '0.35')
                        page_margins.set('header', '0.2')
                        page_margins.set('footer', '0.2')

                        page_setup = ensure_root_child(root, 'pageSetup', after_name='pageMargins')
                        page_setup.set('paperSize', '9')  # A4
                        page_setup.set('fitToWidth', '1')
                        page_setup.set('fitToHeight', '0')
                        page_setup.set('orientation', page_setup.get('orientation') or 'portrait')
                        page_setup.attrib.pop('scale', None)

                        data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                        changed = True
                    except Exception as sheet_error:
                        logger.warning(f"[서류생성] A4 인쇄 설정 적용 실패({item.filename}): {sheet_error}")

                zip_out.writestr(item, data)

    if changed:
        os.unlink(xlsx_path)
        shutil.move(temp_output, xlsx_path)
    else:
        try:
            os.unlink(temp_output)
        except OSError:
            pass

    return changed


def _strip_xlsx_bold_formatting(xlsx_path):
    """견적/거래명세서 출력물에서는 템플릿의 굵게 서식을 제거한다."""
    import os
    import shutil
    import zipfile
    from xml.etree import ElementTree as ET

    spreadsheet_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', spreadsheet_ns)

    def qname(name):
        return f'{{{spreadsheet_ns}}}{name}'

    temp_output = xlsx_path.replace('.xlsx', '_no_bold.xlsx')
    changed = False

    with zipfile.ZipFile(xlsx_path, 'r') as zip_in:
        with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for item in zip_in.infolist():
                data = zip_in.read(item.filename)
                if item.filename in {'xl/styles.xml', 'xl/sharedStrings.xml'}:
                    try:
                        root = ET.fromstring(data)
                        parent_map = {child: parent for parent in root.iter() for child in parent}
                        for bold_node in list(root.iter(qname('b'))):
                            parent = parent_map.get(bold_node)
                            if parent is not None:
                                parent.remove(bold_node)
                                changed = True
                        data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                    except Exception as bold_error:
                        logger.warning(f"[서류생성] 굵게 서식 제거 실패({item.filename}): {bold_error}")

                zip_out.writestr(item, data)

    if changed:
        os.unlink(xlsx_path)
        shutil.move(temp_output, xlsx_path)
    else:
        try:
            os.unlink(temp_output)
        except OSError:
            pass
    return changed


def _hide_xlsx_template_columns(xlsx_path, token_patterns):
    """템플릿 토큰이 들어있는 열을 숨겨 Excel/PDF 출력에서 열 자체를 제외한다."""
    import os
    import re
    import shutil
    import zipfile
    from xml.etree import ElementTree as ET

    compiled_patterns = [re.compile(pattern) for pattern in token_patterns]
    if not compiled_patterns:
        return False

    spreadsheet_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', spreadsheet_ns)

    def qname(name):
        return f'{{{spreadsheet_ns}}}{name}'

    cell_ref_pattern = re.compile(r'^([A-Z]+)(\d+)$')

    def split_cell_ref(ref):
        normalized = str(ref or '').replace('$', '').upper()
        match = cell_ref_pattern.match(normalized)
        if not match:
            return None
        col_letters, row_text = match.groups()
        col_idx = 0
        for char in col_letters:
            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
        return col_idx, int(row_text)

    def text_content(node):
        return ''.join(text_node.text or '' for text_node in node.iter(qname('t')))

    def cell_text(cell, shared_strings):
        if cell.get('t') == 's':
            value_node = cell.find(qname('v'))
            if value_node is not None:
                return shared_strings.get(value_node.text or '', '')
        if cell.get('t') == 'inlineStr':
            return text_content(cell)
        value_node = cell.find(qname('v'))
        return value_node.text or '' if value_node is not None else ''

    def text_matches(text):
        return any(pattern.search(text or '') for pattern in compiled_patterns)

    def ensure_cols_node(root):
        cols_node = root.find(qname('cols'))
        if cols_node is not None:
            return cols_node

        cols_node = ET.Element(qname('cols'))
        children = list(root)
        insert_index = 0
        for preferred_name in ('sheetPr', 'dimension', 'sheetViews', 'sheetFormatPr'):
            preferred = root.find(qname(preferred_name))
            if preferred is not None:
                insert_index = max(insert_index, children.index(preferred) + 1)
        sheet_data = root.find(qname('sheetData'))
        if sheet_data is not None:
            insert_index = min(insert_index, children.index(sheet_data))
        root.insert(insert_index, cols_node)
        return cols_node

    def clone_col(original, min_col, max_col, hidden=False):
        attrs = dict(original.attrib) if original is not None else {}
        attrs['min'] = str(min_col)
        attrs['max'] = str(max_col)
        if hidden:
            attrs['hidden'] = '1'
            attrs['customWidth'] = attrs.get('customWidth') or '1'
        return ET.Element(qname('col'), attrs)

    def contiguous_ranges(values):
        ordered = sorted(values)
        if not ordered:
            return []
        ranges = []
        start = previous = ordered[0]
        for value in ordered[1:]:
            if value == previous + 1:
                previous = value
                continue
            ranges.append((start, previous))
            start = previous = value
        ranges.append((start, previous))
        return ranges

    def rebuild_cols_node(root, target_cols):
        cols_node = ensure_cols_node(root)
        old_nodes = list(cols_node.findall(qname('col')))
        covered_targets = set()
        new_nodes = []

        for old_node in old_nodes:
            try:
                min_col = int(old_node.get('min'))
                max_col = int(old_node.get('max'))
            except (TypeError, ValueError):
                new_nodes.append(old_node)
                continue

            targets_in_range = {col for col in target_cols if min_col <= col <= max_col}
            if not targets_in_range:
                new_nodes.append(old_node)
                continue

            covered_targets.update(targets_in_range)
            non_targets = set(range(min_col, max_col + 1)) - targets_in_range
            for start, end in contiguous_ranges(non_targets):
                new_nodes.append(clone_col(old_node, start, end, hidden=False))
            for start, end in contiguous_ranges(targets_in_range):
                new_nodes.append(clone_col(old_node, start, end, hidden=True))

        for start, end in contiguous_ranges(target_cols - covered_targets):
            new_nodes.append(clone_col(None, start, end, hidden=True))

        new_nodes.sort(key=lambda node: (int(node.get('min') or 0), int(node.get('max') or 0)))
        for old_node in old_nodes:
            cols_node.remove(old_node)
        for new_node in new_nodes:
            cols_node.append(new_node)
        return True

    temp_output = xlsx_path.replace('.xlsx', '_hidden_columns.xlsx')
    changed = False

    with zipfile.ZipFile(xlsx_path, 'r') as zip_in:
        files = {item.filename: zip_in.read(item.filename) for item in zip_in.infolist()}
        infos = zip_in.infolist()

    shared_strings = {}
    shared_strings_data = files.get('xl/sharedStrings.xml')
    if shared_strings_data:
        try:
            shared_root = ET.fromstring(shared_strings_data)
            for index, shared_item in enumerate(shared_root.findall(qname('si'))):
                shared_strings[str(index)] = text_content(shared_item)
        except Exception as shared_error:
            logger.warning(f"[서류생성] 숨김 열 sharedStrings 분석 실패: {shared_error}")

    for filename, data in list(files.items()):
        if not (filename.startswith('xl/worksheets/sheet') and filename.endswith('.xml')):
            continue
        try:
            root = ET.fromstring(data)
            target_cols = set()
            for row in root.findall(f'.//{qname("row")}'):
                for cell in row.findall(qname('c')):
                    if not text_matches(cell_text(cell, shared_strings)):
                        continue
                    parsed_ref = split_cell_ref(cell.get('r'))
                    if parsed_ref:
                        target_cols.add(parsed_ref[0])
            if not target_cols:
                continue
            rebuild_cols_node(root, target_cols)
            files[filename] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            changed = True
        except Exception as sheet_error:
            logger.warning(f"[서류생성] 템플릿 열 숨김 실패({filename}): {sheet_error}")

    if not changed:
        return False

    with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for item in infos:
            zip_out.writestr(item, files[item.filename])

    os.unlink(xlsx_path)
    shutil.move(temp_output, xlsx_path)
    return True


def _hide_xlsx_base_unit_price_columns(xlsx_path):
    return _hide_xlsx_template_columns(xlsx_path, [r'\{\{품목\d+_기준단가\}\}'])


def _insert_xlsx_quote_item_option_rows(xlsx_path, data_map):
    """견적 품목 옵션/설명이 있으면 해당 품목 행 아래에 별도 옵션 행을 삽입한다."""
    import math
    import os
    import re
    import shutil
    import unicodedata
    import zipfile
    from xml.etree import ElementTree as ET

    option_values = {}
    for key, value in (data_map or {}).items():
        match = re.fullmatch(r'품목(\d+)_옵션설명', str(key))
        text = str(value or '').strip()
        if match and text:
            option_values[int(match.group(1))] = text
    if not option_values:
        return False

    spreadsheet_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', spreadsheet_ns)

    def qname(name):
        return f'{{{spreadsheet_ns}}}{name}'

    cell_ref_pattern = re.compile(r'^([A-Z]+)(\d+)$')
    item_token_pattern = re.compile(
        r'\{\{품목(\d+)_(이름|품목명|수량|단위|규격|설명|기준단가|할인율|할인단가|단가|공급가액|부가세액|금액|총액)\}\}'
    )

    def split_cell_ref(ref):
        normalized = str(ref or '').replace('$', '').upper()
        match = cell_ref_pattern.match(normalized)
        if not match:
            return None
        col_letters, row_text = match.groups()
        col_idx = 0
        for char in col_letters:
            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
        return col_idx, int(row_text)

    def column_letters(col_idx):
        letters = []
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            letters.append(chr(ord('A') + remainder))
        return ''.join(reversed(letters)) or 'A'

    def update_cell_ref(ref, row_delta_at):
        parsed = split_cell_ref(ref)
        if not parsed:
            return ref
        col_idx, row_idx = parsed
        if row_idx >= row_delta_at:
            row_idx += 1
        return f'{column_letters(col_idx)}{row_idx}'

    def text_content(node):
        return ''.join(text_node.text or '' for text_node in node.iter(qname('t')))

    def cell_text(cell, shared_strings):
        if cell.get('t') == 's':
            value_node = cell.find(qname('v'))
            if value_node is not None:
                return shared_strings.get(value_node.text or '', '')
        if cell.get('t') == 'inlineStr':
            return text_content(cell)
        value_node = cell.find(qname('v'))
        return value_node.text or '' if value_node is not None else ''

    def parse_merge_ref(ref):
        parts = str(ref or '').split(':')
        if len(parts) != 2:
            return None
        start = split_cell_ref(parts[0])
        end = split_cell_ref(parts[1])
        if not start or not end:
            return None
        return start[0], start[1], end[0], end[1]

    def merge_ref(start_col, start_row, end_col, end_row):
        return f'{column_letters(start_col)}{start_row}:{column_letters(end_col)}{end_row}'

    def shift_merge_ref(ref, insert_at):
        parsed = parse_merge_ref(ref)
        if not parsed:
            return ref
        start_col, start_row, end_col, end_row = parsed
        if start_row >= insert_at:
            start_row += 1
            end_row += 1
        elif end_row >= insert_at:
            end_row += 1
        return merge_ref(start_col, start_row, end_col, end_row)

    def display_width(text):
        width = 0
        for char in str(text or ''):
            width += 2 if unicodedata.east_asian_width(char) in {'F', 'W'} else 1
        return width

    def estimated_option_height(text, merged_width):
        line_count = 0
        chars_per_line = max(int(merged_width * 1.15), 16)
        for line in str(text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n') or ['']:
            line_count += max(1, math.ceil(display_width(line) / chars_per_line))
        return min(120.0, max(18.0, line_count * 16.5 + 3.0))

    def sheet_column_widths(root):
        widths = []
        cols_node = root.find(qname('cols'))
        if cols_node is not None:
            for col in cols_node.findall(qname('col')):
                try:
                    widths.append((int(col.get('min')), int(col.get('max')), float(col.get('width') or 8.43)))
                except (TypeError, ValueError):
                    continue
        sheet_format = root.find(qname('sheetFormatPr'))
        try:
            default_width = float(sheet_format.get('defaultColWidth')) if sheet_format is not None and sheet_format.get('defaultColWidth') else 8.43
        except ValueError:
            default_width = 8.43

        def width_for_col(col_idx):
            for min_col, max_col, width in widths:
                if min_col <= col_idx <= max_col:
                    return width
            return default_width

        return width_for_col

    def ensure_merge_cells(root):
        merge_cells = root.find(qname('mergeCells'))
        if merge_cells is not None:
            return merge_cells
        merge_cells = ET.Element(qname('mergeCells'), {'count': '0'})
        sheet_data = root.find(qname('sheetData'))
        children = list(root)
        insert_index = children.index(sheet_data) + 1 if sheet_data is not None and sheet_data in children else len(children)
        root.insert(insert_index, merge_cells)
        return merge_cells

    def add_option_merge(root, start_col, row_idx, end_col):
        if end_col <= start_col:
            return
        merge_cells = ensure_merge_cells(root)
        merge_cells.append(ET.Element(qname('mergeCell'), {'ref': merge_ref(start_col, row_idx, end_col, row_idx)}))
        merge_cells.set('count', str(len(merge_cells.findall(qname('mergeCell')))))

    def shift_sheet(root, insert_at):
        sheet_data = root.find(qname('sheetData'))
        if sheet_data is None:
            return
        for row in reversed(sheet_data.findall(qname('row'))):
            try:
                row_idx = int(row.get('r') or 0)
            except ValueError:
                row_idx = 0
            if row_idx < insert_at:
                continue
            row.set('r', str(row_idx + 1))
            for cell in row.findall(qname('c')):
                cell.set('r', update_cell_ref(cell.get('r'), insert_at))

        dimension = root.find(qname('dimension'))
        if dimension is not None and dimension.get('ref'):
            parts = dimension.get('ref').split(':')
            shifted = []
            for ref in parts:
                parsed = split_cell_ref(ref)
                if parsed:
                    col_idx, row_idx = parsed
                    if row_idx >= insert_at:
                        row_idx += 1
                    shifted.append(f'{column_letters(col_idx)}{row_idx}')
                else:
                    shifted.append(ref)
            dimension.set('ref', ':'.join(shifted))

        merge_cells = root.find(qname('mergeCells'))
        if merge_cells is not None:
            for merge_cell in merge_cells.findall(qname('mergeCell')):
                merge_cell.set('ref', shift_merge_ref(merge_cell.get('ref'), insert_at))

    def row_insert_index(sheet_data, insert_at):
        for index, row in enumerate(list(sheet_data)):
            try:
                row_idx = int(row.get('r') or 0)
            except ValueError:
                row_idx = 0
            if row_idx >= insert_at:
                return index
        return len(list(sheet_data))

    def make_inline_string_cell(ref, style_id, text):
        attrs = {'r': ref, 't': 'inlineStr'}
        if style_id not in (None, ''):
            attrs['s'] = str(style_id)
        cell = ET.Element(qname('c'), attrs)
        inline = ET.SubElement(cell, qname('is'))
        text_node = ET.SubElement(inline, qname('t'))
        text_node.text = text
        return cell

    def make_blank_cell(ref, style_id):
        attrs = {'r': ref}
        if style_id not in (None, ''):
            attrs['s'] = str(style_id)
        return ET.Element(qname('c'), attrs)

    def create_option_row(target):
        row_idx = target['row'] + 1
        text = f"옵션: {target['option']}"
        merged_width = target['mergedWidth']
        row = ET.Element(qname('row'), {
            'r': str(row_idx),
            'ht': f"{estimated_option_height(text, merged_width):.1f}".rstrip('0').rstrip('.'),
            'customHeight': '1',
        })
        for col_idx in range(target['startCol'], target['endCol'] + 1):
            ref = f'{column_letters(col_idx)}{row_idx}'
            style_id = target['styles'].get(col_idx, target['textStyle'])
            if col_idx == target['startCol']:
                row.append(make_inline_string_cell(ref, style_id, text))
            else:
                row.append(make_blank_cell(ref, style_id))
        return row

    files = {}
    infos = []
    with zipfile.ZipFile(xlsx_path, 'r') as zip_in:
        for item in zip_in.infolist():
            infos.append(item)
            files[item.filename] = zip_in.read(item.filename)

    shared_strings = {}
    shared_strings_data = files.get('xl/sharedStrings.xml')
    if shared_strings_data:
        try:
            shared_root = ET.fromstring(shared_strings_data)
            for index, shared_item in enumerate(shared_root.findall(qname('si'))):
                shared_strings[str(index)] = text_content(shared_item)
        except Exception as shared_error:
            logger.warning(f"[서류생성] 옵션 행 sharedStrings 분석 실패: {shared_error}")

    changed = False
    for filename, data in list(files.items()):
        if not (filename.startswith('xl/worksheets/sheet') and filename.endswith('.xml')):
            continue
        try:
            root = ET.fromstring(data)
            sheet_data = root.find(qname('sheetData'))
            if sheet_data is None:
                continue
            width_for_col = sheet_column_widths(root)
            targets = []
            for row in sheet_data.findall(qname('row')):
                try:
                    row_idx = int(row.get('r') or 0)
                except ValueError:
                    continue
                cells = list(row.findall(qname('c')))
                cell_infos = []
                row_text_parts = []
                for cell in cells:
                    parsed = split_cell_ref(cell.get('r'))
                    if not parsed:
                        continue
                    text = cell_text(cell, shared_strings)
                    row_text_parts.append(text)
                    cell_infos.append({
                        'cell': cell,
                        'col': parsed[0],
                        'style': cell.get('s'),
                        'text': text,
                    })
                row_text = '\n'.join(row_text_parts)
                item_numbers = sorted({
                    int(match.group(1))
                    for match in item_token_pattern.finditer(row_text)
                    if int(match.group(1)) in option_values
                })
                if not item_numbers or not cell_infos:
                    continue
                min_col = min(info['col'] for info in cell_infos)
                max_col = max(info['col'] for info in cell_infos)
                styles = {info['col']: info['style'] for info in cell_infos}
                for item_number in item_numbers:
                    preferred_cell = None
                    for field in ('설명', '품목명', '이름'):
                        token = f'{{{{품목{item_number}_{field}}}}}'
                        preferred_cell = next((info for info in cell_infos if token in info['text']), None)
                        if preferred_cell:
                            break
                    start_col = preferred_cell['col'] if preferred_cell else (min_col + 1 if max_col > min_col else min_col)
                    text_style = preferred_cell['style'] if preferred_cell else styles.get(start_col)
                    targets.append({
                        'row': row_idx,
                        'startCol': start_col,
                        'endCol': max_col,
                        'styles': styles,
                        'textStyle': text_style,
                        'option': option_values[item_number],
                        'mergedWidth': sum(width_for_col(col_idx) for col_idx in range(start_col, max_col + 1)),
                    })
            if not targets:
                continue
            for target in sorted(targets, key=lambda value: value['row'], reverse=True):
                insert_at = target['row'] + 1
                shift_sheet(root, insert_at)
                option_row = create_option_row(target)
                sheet_data.insert(row_insert_index(sheet_data, insert_at), option_row)
                add_option_merge(root, target['startCol'], insert_at, target['endCol'])
                changed = True
            files[filename] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        except Exception as sheet_error:
            logger.warning(f"[서류생성] 견적 옵션 행 삽입 실패({filename}): {sheet_error}")

    if not changed:
        return False

    temp_output = xlsx_path.replace('.xlsx', '_quote_option_rows.xlsx')
    with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for item in infos:
            zip_out.writestr(item, files[item.filename])

    os.unlink(xlsx_path)
    shutil.move(temp_output, xlsx_path)
    return True


def _expand_xlsx_template_text_rows(xlsx_path, data_map):
    """치환될 텍스트가 셀 폭보다 길면 줄바꿈과 행 높이를 보정한다."""
    import copy
    import math
    import os
    import re
    import shutil
    import unicodedata
    import zipfile
    from xml.etree import ElementTree as ET

    variable_values = {
        key: str(value or '')
        for key, value in (data_map or {}).items()
        if str(value or '').strip()
    }
    if not variable_values:
        return False

    spreadsheet_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', spreadsheet_ns)

    def qname(name):
        return f'{{{spreadsheet_ns}}}{name}'

    variable_token_pattern = re.compile(r'\{\{([^{}]+)\}\}')
    cell_ref_pattern = re.compile(r'^([A-Z]+)(\d+)$')

    def text_content(node):
        return ''.join(text_node.text or '' for text_node in node.iter(qname('t')))

    def numeric_like(text):
        cleaned = re.sub(r'[\s,.%+\-원₩()]+', '', str(text or ''))
        return bool(cleaned) and cleaned.isdigit()

    def render_template_text(text):
        replaced = False

        def replace_token(match):
            nonlocal replaced
            key = match.group(1)
            if key not in variable_values:
                return match.group(0)
            replaced = True
            return variable_values.get(key, '')

        rendered = variable_token_pattern.sub(replace_token, text or '').strip()
        if not replaced or not rendered:
            return ''
        if numeric_like(rendered) and '\n' not in rendered:
            return ''
        return rendered

    def split_cell_ref(ref):
        normalized = str(ref or '').replace('$', '').upper()
        match = cell_ref_pattern.match(normalized)
        if not match:
            return None
        col_letters, row_text = match.groups()
        col_idx = 0
        for char in col_letters:
            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
        return col_idx, int(row_text)

    def display_width(text):
        width = 0
        for char in str(text or ''):
            width += 2 if unicodedata.east_asian_width(char) in {'F', 'W'} else 1
        return width

    def estimated_row_height(text, width):
        normalized = str(text or '').replace('\r\n', '\n').replace('\r', '\n')
        chars_per_line = max(int(width * 1.05), 8)
        line_count = 0
        for line in normalized.split('\n') or ['']:
            line_count += max(1, math.ceil(display_width(line) / chars_per_line))
        return min(409.0, max(15.0, line_count * 16.5 + 3.0))

    def should_wrap_text(text, width):
        normalized = str(text or '').replace('\r\n', '\n').replace('\r', '\n').strip()
        if not normalized:
            return False
        if '\n' in normalized:
            return True
        chars_per_line = max(int(width * 1.05), 8)
        return display_width(normalized) > chars_per_line

    def parse_merge_ref(ref):
        parts = str(ref or '').split(':')
        if len(parts) != 2:
            return None
        start = split_cell_ref(parts[0])
        end = split_cell_ref(parts[1])
        if not start or not end:
            return None
        return start[0], start[1], end[0], end[1]

    def sheet_column_widths(root):
        widths = []
        cols_node = root.find(qname('cols'))
        if cols_node is not None:
            for col in cols_node.findall(qname('col')):
                try:
                    widths.append((
                        int(col.get('min')),
                        int(col.get('max')),
                        float(col.get('width') or 8.43),
                    ))
                except (TypeError, ValueError):
                    continue
        sheet_format = root.find(qname('sheetFormatPr'))
        try:
            default_width = float(sheet_format.get('defaultColWidth')) if sheet_format is not None and sheet_format.get('defaultColWidth') else 8.43
        except ValueError:
            default_width = 8.43

        def width_for_col(col_idx):
            for min_col, max_col, width in widths:
                if min_col <= col_idx <= max_col:
                    return width
            return default_width

        return width_for_col

    def sheet_merge_ranges(root):
        ranges = []
        merge_cells = root.find(qname('mergeCells'))
        if merge_cells is not None:
            for merge_cell in merge_cells.findall(qname('mergeCell')):
                parsed = parse_merge_ref(merge_cell.get('ref'))
                if parsed:
                    ranges.append(parsed)
        return ranges

    def effective_cell_width(col_idx, row_idx, width_for_col, merge_ranges):
        for start_col, start_row, end_col, end_row in merge_ranges:
            if start_col <= col_idx <= end_col and start_row <= row_idx <= end_row:
                return sum(width_for_col(col) for col in range(start_col, end_col + 1))
        return width_for_col(col_idx)

    def target_text_for_cell(cell, shared_string_targets):
        if cell.get('t') == 's':
            value_node = cell.find(qname('v'))
            if value_node is not None:
                return shared_string_targets.get(value_node.text or '')
        if cell.get('t') == 'inlineStr':
            return render_template_text(text_content(cell))
        return ''

    files = {}
    infos = []
    with zipfile.ZipFile(xlsx_path, 'r') as zip_in:
        for item in zip_in.infolist():
            infos.append(item)
            files[item.filename] = zip_in.read(item.filename)

    shared_string_targets = {}
    shared_strings_data = files.get('xl/sharedStrings.xml')
    if shared_strings_data:
        try:
            shared_root = ET.fromstring(shared_strings_data)
            for index, shared_item in enumerate(shared_root.findall(qname('si'))):
                rendered = render_template_text(text_content(shared_item))
                if rendered:
                    shared_string_targets[str(index)] = rendered
        except Exception as shared_error:
            logger.warning(f"[서류생성] 템플릿 텍스트 sharedStrings 분석 실패: {shared_error}")

    sheet_targets = {}
    base_style_ids = set()
    for filename, data in files.items():
        if not (filename.startswith('xl/worksheets/sheet') and filename.endswith('.xml')):
            continue
        try:
            root = ET.fromstring(data)
        except Exception as sheet_error:
            logger.warning(f"[서류생성] 템플릿 텍스트 워크시트 분석 실패({filename}): {sheet_error}")
            continue

        targets = []
        width_for_col = sheet_column_widths(root)
        merge_ranges = sheet_merge_ranges(root)
        for row in root.findall(f'.//{qname("row")}'):
            for cell in row.findall(qname('c')):
                rendered_text = target_text_for_cell(cell, shared_string_targets)
                if not rendered_text:
                    continue
                parsed_ref = split_cell_ref(cell.get('r'))
                if not parsed_ref:
                    continue
                cell_width = effective_cell_width(parsed_ref[0], parsed_ref[1], width_for_col, merge_ranges)
                if not should_wrap_text(rendered_text, cell_width):
                    continue
                try:
                    style_id = int(cell.get('s') or 0)
                except ValueError:
                    style_id = 0
                base_style_ids.add(style_id)
                targets.append({
                    'ref': cell.get('r'),
                    'row': parsed_ref[1],
                    'col': parsed_ref[0],
                    'style': style_id,
                    'text': rendered_text,
                })
        if targets:
            sheet_targets[filename] = targets

    if not sheet_targets:
        return False

    style_map = {style_id: style_id for style_id in base_style_ids}
    styles_data = files.get('xl/styles.xml')
    if styles_data:
        try:
            styles_root = ET.fromstring(styles_data)
            cell_xfs = styles_root.find(qname('cellXfs'))
            if cell_xfs is not None:
                existing_xfs = list(cell_xfs.findall(qname('xf')))
                for style_id in sorted(base_style_ids):
                    base_index = style_id if 0 <= style_id < len(existing_xfs) else 0
                    if not existing_xfs:
                        continue
                    wrapped_xf = copy.deepcopy(existing_xfs[base_index])
                    wrapped_xf.set('applyAlignment', '1')
                    alignment = wrapped_xf.find(qname('alignment'))
                    if alignment is None:
                        alignment = ET.Element(qname('alignment'))
                        wrapped_xf.append(alignment)
                    alignment.set('wrapText', '1')
                    alignment.set('vertical', 'top')
                    cell_xfs.append(wrapped_xf)
                    style_map[style_id] = len(cell_xfs.findall(qname('xf'))) - 1
                cell_xfs.set('count', str(len(cell_xfs.findall(qname('xf')))))
                files['xl/styles.xml'] = ET.tostring(styles_root, encoding='utf-8', xml_declaration=True)
        except Exception as style_error:
            logger.warning(f"[서류생성] 템플릿 텍스트 줄바꿈 스타일 생성 실패: {style_error}")

    for filename, targets in sheet_targets.items():
        try:
            root = ET.fromstring(files[filename])
            width_for_col = sheet_column_widths(root)
            merge_ranges = sheet_merge_ranges(root)
            targets_by_ref = {target['ref']: target for target in targets}
            target_heights = {}

            for target in targets:
                cell_width = effective_cell_width(target['col'], target['row'], width_for_col, merge_ranges)
                target_heights[target['row']] = max(
                    target_heights.get(target['row'], 15.0),
                    estimated_row_height(target['text'], cell_width),
                )

            for row in root.findall(f'.//{qname("row")}'):
                try:
                    row_idx = int(row.get('r') or 0)
                except ValueError:
                    row_idx = 0
                if row_idx in target_heights:
                    try:
                        current_height = float(row.get('ht') or 15.0)
                    except ValueError:
                        current_height = 15.0
                    row.set('ht', f"{max(current_height, target_heights[row_idx]):.1f}".rstrip('0').rstrip('.'))
                    row.set('customHeight', '1')

                for cell in row.findall(qname('c')):
                    target = targets_by_ref.get(cell.get('r'))
                    if not target:
                        continue
                    cell.set('s', str(style_map.get(target['style'], target['style'])))

            files[filename] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        except Exception as sheet_error:
            logger.warning(f"[서류생성] 템플릿 텍스트 행 높이 적용 실패({filename}): {sheet_error}")

    temp_output = xlsx_path.replace('.xlsx', '_note_rows.xlsx')
    with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        for item in infos:
            zip_out.writestr(item, files[item.filename])

    os.unlink(xlsx_path)
    shutil.move(temp_output, xlsx_path)
    return True


def _expand_xlsx_item_note_rows(xlsx_path, data_map):
    """기존 호출 호환용: 품목 적요/비고 행 높이 보정."""
    note_data_map = {
        key: value
        for key, value in (data_map or {}).items()
        if re.fullmatch(r'품목\d+_(적요|비고|옵션|옵션설명)', str(key))
    }
    return _expand_xlsx_template_text_rows(xlsx_path, note_data_map)


@login_required
def get_document_template_data(request, document_type, schedule_id):
    """
    클라이언트에서 xlwings로 처리하기 위한 템플릿 URL과 변수 데이터 반환
    
    Returns:
        JSON {
            template_url: Cloudinary URL,
            template_filename: 원본 파일명,
            variables: {변수명: 값} 딕셔너리,
            file_info: {파일명, 회사명, 고객명 등}
        }
    """
    from reporting.models import Schedule, DocumentTemplate
    from decimal import Decimal
    import pytz
    
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, schedule.user):
            return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)

        quote_group, quote_group_selected = _document_quote_group_selection(request)
        quote_group_label = _quote_group_label(quote_group) if quote_group_selected else ''
        hide_base_unit_price = _document_hide_base_unit_price(request, document_type)
        
        # 해당 회사의 기본 서류 템플릿 찾기
        company = request.user.userprofile.company
        
        document_template = DocumentTemplate.objects.filter(
            company=company,
            document_type=document_type,
            is_active=True,
            is_default=True
        ).first()
        
        if not document_template:
            document_template = DocumentTemplate.objects.filter(
                company=company,
                document_type=document_type,
                is_active=True
            ).first()
        
        if not document_template:
            doc_type_names = {
                'quotation': '견적서',
                'transaction_statement': '거래명세서',
                'delivery_note': '납품서',
            }
            doc_type_name = doc_type_names.get(document_type, '서류')
            
            return JsonResponse({
                'success': False,
                'error': f'{doc_type_name} 템플릿이 등록되어 있지 않습니다.'
            }, status=404)
        
        if not document_template.file:
            return JsonResponse({
                'success': False,
                'error': '서류 템플릿 파일을 찾을 수 없습니다.'
            }, status=404)
        
        # 납품/견적 품목 조회. 견적서는 quote_group query가 있으면 해당 묶음만 출력한다.
        delivery_items = _document_delivery_items_queryset(
            schedule,
            document_type,
            quote_group=quote_group,
            quote_group_selected=quote_group_selected,
        )
        
        # 총액 계산 — 일정의 부가세 모드 반영(실제 서류 생성과 같은 규칙, reporting/vat.py)
        _vat_mode = vat.schedule_vat_mode(schedule)
        subtotal, tax, total = vat.split_amount(sum([
            _document_item_prices(item)['effective_unit_price'] * item.quantity
            for item in delivery_items
        ], Decimal('0')), _vat_mode)
        
        # 총액을 한글로 변환
        def number_to_korean(number):
            num = int(number)
            if num == 0:
                return '영'
            
            units = ['', '만', '억', '조']
            digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
            
            result = []
            unit_idx = 0
            
            while num > 0:
                segment = num % 10000
                if segment > 0:
                    segment_str = []
                    
                    if segment >= 1000:
                        d = segment // 1000
                        if d > 1:
                            segment_str.append(digits[d])
                        segment_str.append('천')
                        segment %= 1000
                    
                    if segment >= 100:
                        d = segment // 100
                        if d > 1:
                            segment_str.append(digits[d])
                        segment_str.append('백')
                        segment %= 100
                    
                    if segment >= 10:
                        d = segment // 10
                        if d > 1:
                            segment_str.append(digits[d])
                        segment_str.append('십')
                        segment %= 10
                    
                    if segment > 0:
                        segment_str.append(digits[segment])
                    
                    if unit_idx > 0:
                        segment_str.append(units[unit_idx])
                    
                    result.insert(0, ''.join(segment_str))
                
                num //= 10000
                unit_idx += 1
            
            return ''.join(result)
        
        total_korean = number_to_korean(total)
        
        # 거래번호 생성
        korea_tz = pytz.timezone('Asia/Seoul')
        today = timezone.now().astimezone(korea_tz)
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        from reporting.models import DocumentGenerationLog
        today_count = DocumentGenerationLog.objects.filter(
            company=company,
            created_at__gte=today_start,
            created_at__lte=today_end
        ).count() + 1
        
        transaction_number = f"{today.strftime('%Y')}-{today.strftime('%m')}-{today.strftime('%d')}-{today_count:03d}"
        
        # 담당자 정보
        salesman_name = _document_salesperson_name(schedule.user)
        
        # 연결된 견적번호 자동 채움
        _linked_quote = schedule.quotes.order_by('-created_at').first()
        _quote_number = _linked_quote.quote_number if _linked_quote else ''
        quote_extra_notes = _document_quote_extra_notes(schedule, quote_group, quote_group_selected)

        # 데이터 매핑
        data_map = {
            '년': today.strftime('%Y'),
            '월': today.strftime('%m'),
            '일': today.strftime('%d'),
            '거래번호': transaction_number,
            
            '고객명': schedule.followup.customer_name,
            '업체명': str(schedule.followup.company) if schedule.followup.company else '',
            '학교명': str(schedule.followup.company) if schedule.followup.company else '',
            '부서명': str(schedule.followup.department) if schedule.followup.department else '',
            '연구실': str(schedule.followup.department) if schedule.followup.department else '',
            '담당자': schedule.followup.customer_name,
            '이메일': schedule.followup.email or '',
            '담당자이메일': schedule.followup.email or '',
            '연락처': schedule.followup.phone_number or '',
            '전화번호': schedule.followup.phone_number or '',
            
            '실무자': salesman_name,
            '영업담당자': salesman_name,
            '담당영업': salesman_name,
            '영업담당자이메일': schedule.user.email or '',
            
            '일정날짜': schedule.visit_date.strftime('%Y년 %m월 %d일'),
            '날짜': schedule.visit_date.strftime('%Y년 %m월 %d일'),
            '발행일': today.strftime('%Y년 %m월 %d일'),

            # 견적 정보 (자동 채움)
            '견적번호': _quote_number,
            '견적구분': quote_group_label,
            '견적명': quote_group_label,
            '견적제목': f'{quote_group_label} 견적서' if quote_group_label else '견적서',
            '메모': schedule.notes or '',
            '기타사항': quote_extra_notes,
            '견적기타사항': quote_extra_notes,
            
            '회사명': company.name,
            
            '공급가액': f"{int(subtotal):,}",
            '소계': f"{int(subtotal):,}",
            '부가세액': f"{int(tax):,}",
            '부가세': f"{int(tax):,}",
            '총액': f"{int(total):,}",
            '합계': f"{int(total):,}",
            '총액한글': f"금 {total_korean}원정",
            '한글금액': f"금 {total_korean}원정",
        }
        
        # 품목 데이터 추가
        items_data = []
        for idx, item in enumerate(delivery_items, 1):
            price_info = _document_item_prices(item)
            item_subtotal = price_info['effective_unit_price'] * item.quantity
            item_unit = item.unit if item.unit else (item.product.unit if item.product and item.product.unit else 'EA')
            item_option_description = item.option_description or ''
            
            item_data = {
                f'품목{idx}_이름': item.item_name,
                f'품목{idx}_품목명': item.item_name,
                f'품목{idx}_수량': str(item.quantity),
                f'품목{idx}_단위': item_unit,
                f'품목{idx}_규격': item.product.specification if item.product and item.product.specification else '',
                f'품목{idx}_설명': item.product.description if item.product and item.product.description else '',
                f'품목{idx}_옵션': item_option_description,
                f'품목{idx}_옵션설명': item_option_description,
                f'품목{idx}_적요': item.notes or '',
                f'품목{idx}_비고': item.notes or '',
                f'품목{idx}_기준단가': _document_base_unit_price_display(
                    price_info,
                    hide_base_unit_price,
                    document_type,
                ),
                f'품목{idx}_할인율': _document_discount_rate_label(price_info['discount_rate']),
                f'품목{idx}_할인단가': _document_money(price_info['discount_unit_price']) if price_info['discount_unit_price'] is not None else '',
                f'품목{idx}_공급가액': f"{int(vat.split_amount(item_subtotal, _vat_mode)[0]):,}",
                f'품목{idx}_단가': _document_money(price_info['effective_unit_price']),
                f'품목{idx}_부가세액': f"{int(vat.split_amount(item_subtotal, _vat_mode)[1]):,}",
                f'품목{idx}_금액': f"{int(item_subtotal):,}",
                f'품목{idx}_총액': f"{int(vat.split_amount(item_subtotal, _vat_mode)[2]):,}",
            }
            data_map.update(item_data)
            items_data.append({
                'index': idx,
                'name': item.item_name,
                'quantity': item.quantity,
                'unit': item_unit,
                'unit_price': int(price_info['effective_unit_price']),
                'unitPrice': int(price_info['effective_unit_price']),
                'base_unit_price': None if hide_base_unit_price else int(price_info['base_unit_price']),
                'baseUnitPrice': None if hide_base_unit_price else int(price_info['base_unit_price']),
                'base_unit_price_hidden': hide_base_unit_price,
                'baseUnitPriceHidden': hide_base_unit_price,
                'discountUnitPrice': int(price_info['discount_unit_price']) if price_info['discount_unit_price'] is not None else None,
                'discountRate': float(price_info['discount_rate']),
                'quoteGroup': item.quote_group or '',
                'quoteGroupLabel': _quote_group_label(item.quote_group),
                'notes': item.notes or '',
                'optionDescription': item_option_description,
                'subtotal': int(item_subtotal)
            })
        
        # 유효일 계산용 기준일
        base_date = schedule.visit_date.strftime('%Y-%m-%d')
        
        # 파일명 정보
        doc_type_names = {
            'quotation': '견적서',
            'transaction_statement': '거래명세서',
            'delivery_note': '납품서',
        }
        doc_name = doc_type_names.get(document_type, document_template.name)
        if document_type == 'quotation' and quote_group_label:
            doc_name = quote_group_label if quote_group_label.endswith('견적서') else f'{quote_group_label} 견적서'
        customer_company = schedule.followup.company.name if schedule.followup.company else schedule.followup.customer_name
        
        return JsonResponse({
            'success': True,
            'template_url': document_template.file.url,
            'template_filename': document_template.file.name,
            'variables': data_map,
            'file_info': {
                'company_name': company.name,
                'customer_company': customer_company,
                'doc_name': doc_name,
                'today_str': today.strftime('%Y%m%d'),
                'base_date': base_date,
                'transaction_number': transaction_number,
                'quote_group': quote_group,
                'quote_group_label': quote_group_label,
            },
            'items': items_data,
            'item_count': len(delivery_items),
            'quote_group': quote_group,
            'quote_group_label': quote_group_label,
            'hide_base_unit_price': hide_base_unit_price,
        })
        
    except Exception as e:
        logger.error(f"서류 데이터 조회 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'서류 데이터 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def generate_document_pdf(request, document_type, schedule_id, output_format='xlsx', quote_group=None):
    """
    일정 기반 서류 생성 및 다운로드
    - 업로드된 서류 템플릿에 실제 데이터를 채워서 다운로드
    - 견적서 (quotation)
    - 거래명세서 (transaction_statement)
    
    output_format:
    - 'xlsx': 엑셀 파일로 다운로드 (기본값)
    - 'pdf': PDF 파일로 다운로드
    
    템플릿 파일 형식:
    - 엑셀: {{고객명}}, {{업체명}}, {{품목1_이름}}, {{품목1_수량}}, {{품목1_단가}}, {{품목1_금액}} 등의 변수 사용
    """
    
    from reporting.models import Schedule, DocumentTemplate
    from django.http import HttpResponse, FileResponse
    from urllib.parse import quote
    from decimal import Decimal
    import os
    import re
    
    try:
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        
        # 권한 체크
        if not can_access_user_data(request.user, schedule.user):
            logger.warning(f"[서류생성] 권한 없음 - 사용자: {request.user.username}")
            return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)

        quote_group, quote_group_selected = _document_quote_group_selection(request, quote_group)
        quote_group_label = _quote_group_label(quote_group) if quote_group_selected else ''
        hide_base_unit_price = _document_hide_base_unit_price(request, document_type)
        
        # 해당 회사의 기본 서류 템플릿 찾기
        company = request.user.userprofile.company
        
        document_template = DocumentTemplate.objects.filter(
            company=company,
            document_type=document_type,
            is_active=True,
            is_default=True
        ).first()
        
        if not document_template:
            # 기본이 없으면 활성화된 첫 번째 템플릿
            document_template = DocumentTemplate.objects.filter(
                company=company,
                document_type=document_type,
                is_active=True
            ).first()
        
        if not document_template:
            logger.error(f"[서류생성] 템플릿 없음 - 회사: {company.name}, 타입: {document_type}")
            # 서류 종류 이름 매핑
            doc_type_names = {
                'quotation': '견적서',
                'transaction_statement': '거래명세서',
                'delivery_note': '납품서',
            }
            doc_type_name = doc_type_names.get(document_type, '서류')
            
            return JsonResponse({
                'success': False,
                'error': f'{doc_type_name} 템플릿이 등록되어 있지 않습니다. 서류 관리 메뉴에서 먼저 템플릿을 등록해주세요.'
            }, status=404)
        
        
        # 파일이 존재하는지 확인 (Cloudinary 지원)
        if not document_template.file:
            logger.error(f"[서류생성] 파일 없음 - 템플릿 ID: {document_template.id}")
            return JsonResponse({
                'success': False,
                'error': '서류 템플릿 파일을 찾을 수 없습니다.'
            }, status=404)
        
        # Cloudinary 또는 로컬 파일 시스템에서 파일 가져오기
        import tempfile
        import requests
        
        # CloudinaryField인 경우 직접 URL 사용
        if hasattr(document_template.file, 'public_id'):
            # CloudinaryField - public_id와 URL 직접 사용
            public_id = document_template.file.public_id
            file_url = document_template.file.url
            
            # URL이 이미 http(s)로 시작하면 바로 다운로드
            if file_url.startswith('http://') or file_url.startswith('https://'):
                response = requests.get(file_url)
                if response.status_code != 200:
                    logger.error(f"[서류생성] 다운로드 실패 - 상태코드: {response.status_code}")
                    return JsonResponse({
                        'success': False,
                        'error': '서류 템플릿 파일을 다운로드할 수 없습니다.'
                    }, status=500)
                
                # 임시 파일에 저장
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    template_file_path = tmp_file.name
            else:
                logger.error(f"[서류생성] Cloudinary URL이 상대 경로: {file_url}")
                return JsonResponse({
                    'success': False,
                    'error': '서류 템플릿 파일 URL이 올바르지 않습니다.'
                }, status=500)
        else:
            # FileField - 로컬 파일 경로 사용
            template_file_path = document_template.file.path
        
        # 납품/견적 품목 조회. 견적서는 quote_group query가 있으면 해당 묶음만 출력한다.
        delivery_items = _document_delivery_items_queryset(
            schedule,
            document_type,
            quote_group=quote_group,
            quote_group_selected=quote_group_selected,
        )
        
        # 원본 파일 확장자 확인 (CloudinaryField는 public_id 사용)
        if hasattr(document_template.file, 'public_id'):
            # CloudinaryField - URL에서 확장자 추출 (public_id는 확장자가 없을 수 있음)
            file_url = document_template.file.url
            original_ext = os.path.splitext(file_url.split('?')[0])[1].lower()  # 쿼리 스트링 제거 후 확장자 추출
        else:
            # FileField - name 속성 사용
            original_ext = os.path.splitext(document_template.file.name)[1].lower()
        
        
        # 엑셀 파일인 경우 데이터 채우기
        if original_ext in ['.xlsx', '.xls', '.xlsm']:
            try:
                # ZIP 레벨에서 직접 처리 (한글 완벽 보존 + 이미지 보존)
                import shutil
                import zipfile
                
                # template_file_path를 사용 (이미 Cloudinary에서 다운로드되었거나 로컬 경로)
                # 원본 파일을 임시 위치에 복사
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
                    shutil.copy2(template_file_path, tmp_file.name)
                    temp_path = tmp_file.name
                
                
                # 총액 계산 (부가세 모드 반영)
                _raw_subtotal = sum([
                    _document_item_prices(item)['effective_unit_price'] * item.quantity
                    for item in delivery_items
                ], Decimal('0'))
                _vat_mode = vat.schedule_vat_mode(schedule)
                subtotal, tax, total = vat.split_amount(_raw_subtotal, _vat_mode)
                
                # 총액을 한글로 변환
                def number_to_korean(number):
                    """숫자를 한글로 변환 (예: 11633600 -> 일천백육십삼만삼천육백)"""
                    num = int(number)
                    if num == 0:
                        return '영'
                    
                    units = ['', '만', '억', '조']
                    digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
                    sub_units = ['', '십', '백', '천']
                    
                    result = []
                    unit_idx = 0
                    
                    while num > 0:
                        segment = num % 10000  # 4자리씩 끊기
                        if segment > 0:
                            segment_str = []
                            
                            # 천의 자리
                            if segment >= 1000:
                                d = segment // 1000
                                if d > 1:
                                    segment_str.append(digits[d])
                                segment_str.append('천')
                                segment %= 1000
                            
                            # 백의 자리
                            if segment >= 100:
                                d = segment // 100
                                if d > 1:
                                    segment_str.append(digits[d])
                                segment_str.append('백')
                                segment %= 100
                            
                            # 십의 자리
                            if segment >= 10:
                                d = segment // 10
                                if d > 1:
                                    segment_str.append(digits[d])
                                segment_str.append('십')
                                segment %= 10
                            
                            # 일의 자리
                            if segment > 0:
                                segment_str.append(digits[segment])
                            
                            # 만/억/조 단위 추가
                            if unit_idx > 0:
                                segment_str.append(units[unit_idx])
                            
                            result.insert(0, ''.join(segment_str))
                        
                        num //= 10000
                        unit_idx += 1
                    
                    return ''.join(result)
                
                total_korean = number_to_korean(total)
                
                # 거래번호 생성 (년-월-일-순번) - 한국 시간대 사용
                import pytz
                korea_tz = pytz.timezone('Asia/Seoul')
                today = timezone.now().astimezone(korea_tz)
                today_str = today.strftime('%Y%m%d')
                
                # 오늘 생성된 모든 서류(견적서 + 거래명세서) 개수 + 1
                from reporting.models import DocumentGenerationLog
                
                # 오늘 자정 시각 계산
                today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # 같은 날짜에 생성된 서류 개수 (견적서 + 거래명세서 모두 포함)
                today_count = DocumentGenerationLog.objects.filter(
                    company=company,
                    created_at__gte=today_start,
                    created_at__lte=today_end
                ).count() + 1
                
                transaction_number = f"{today.strftime('%Y')}-{today.strftime('%m')}-{today.strftime('%d')}-{today_count:03d}"
                
                # 데이터 매핑
                from datetime import timedelta
                
                # 담당자(실무자) 정보
                salesman_name = _document_salesperson_name(schedule.user)
                
                # 연결된 견적번호 자동 채움
                _linked_quote = schedule.quotes.order_by('-created_at').first()
                _quote_number = _linked_quote.quote_number if _linked_quote else ''
                quote_extra_notes = _document_quote_extra_notes(schedule, quote_group, quote_group_selected)

                data_map = {
                    # 기본 정보
                    '년': today.strftime('%Y'),
                    '월': today.strftime('%m'),
                    '일': today.strftime('%d'),
                    '거래번호': transaction_number,
                    
                    # 고객 정보
                    '고객명': schedule.followup.customer_name,
                    '업체명': str(schedule.followup.company) if schedule.followup.company else '',
                    '학교명': str(schedule.followup.company) if schedule.followup.company else '',
                    '부서명': str(schedule.followup.department) if schedule.followup.department else '',
                    '연구실': str(schedule.followup.department) if schedule.followup.department else '',
                    '담당자': schedule.followup.customer_name,
                    '이메일': schedule.followup.email or '',
                    '담당자이메일': schedule.followup.email or '',
                    '연락처': schedule.followup.phone_number or '',
                    '전화번호': schedule.followup.phone_number or '',
                    
                    # 실무자(영업담당자) 정보
                    '실무자': salesman_name,
                    '영업담당자': salesman_name,
                    '담당영업': salesman_name,
                    '영업담당자이메일': schedule.user.email or '',
                    # 날짜 정보
                    '일정날짜': schedule.visit_date.strftime('%Y년 %m월 %d일'),
                    '날짜': schedule.visit_date.strftime('%Y년 %m월 %d일'),
                    '발행일': today.strftime('%Y년 %m월 %d일'),
                    
                    # 회사 정보
                    '회사명': company.name,

                    # 견적 정보 (자동 채움)
                    '견적번호': _quote_number,
                    '견적구분': quote_group_label,
                    '견적명': quote_group_label,
                    '견적제목': f'{quote_group_label} 견적서' if quote_group_label else '견적서',
                    '메모': schedule.notes or '',
                    '기타사항': quote_extra_notes,
                    '견적기타사항': quote_extra_notes,
                    
                    # 금액 정보
                    '공급가액': f"{int(subtotal):,}",
                    '소계': f"{int(subtotal):,}",
                    '부가세액': f"{int(tax):,}",
                    '부가세': f"{int(tax):,}",
                    '총액': f"{int(total):,}",
                    '합계': f"{int(total):,}",
                    '총액한글': f"금 {total_korean}원정",
                    '한글금액': f"금 {total_korean}원정",
                }
                
                # 품목 데이터 추가
                for idx, item in enumerate(delivery_items, 1):
                    price_info = _document_item_prices(item)
                    item_subtotal = price_info['effective_unit_price'] * item.quantity
                    # 단위 결정: DeliveryItem에 있으면 사용, 없으면 Product에서, 그것도 없으면 'EA'
                    item_unit = item.unit if item.unit else (item.product.unit if item.product and item.product.unit else 'EA')
                    item_option_description = item.option_description or ''

                    # 품목별 부가세 계산 (schedule의 vat_mode 반영)
                    _item_supply_display, _item_tax, _item_total = vat.split_amount(item_subtotal, _vat_mode)

                    data_map[f'품목{idx}_이름'] = item.item_name
                    data_map[f'품목{idx}_품목명'] = item.item_name
                    data_map[f'품목{idx}_수량'] = str(item.quantity)
                    data_map[f'품목{idx}_단위'] = item_unit
                    data_map[f'품목{idx}_규격'] = item.product.specification if item.product and item.product.specification else ''
                    data_map[f'품목{idx}_설명'] = item.product.description if item.product and item.product.description else ''
                    data_map[f'품목{idx}_옵션'] = item_option_description
                    data_map[f'품목{idx}_옵션설명'] = item_option_description
                    data_map[f'품목{idx}_적요'] = item.notes or ''
                    data_map[f'품목{idx}_비고'] = item.notes or ''
                    data_map[f'품목{idx}_기준단가'] = _document_base_unit_price_display(
                        price_info,
                        hide_base_unit_price,
                        document_type,
                    )
                    data_map[f'품목{idx}_할인율'] = _document_discount_rate_label(price_info['discount_rate'])
                    data_map[f'품목{idx}_할인단가'] = _document_money(price_info['discount_unit_price']) if price_info['discount_unit_price'] is not None else ''
                    data_map[f'품목{idx}_공급가액'] = f"{int(_item_supply_display):,}"
                    data_map[f'품목{idx}_단가'] = _document_money(price_info['effective_unit_price'])
                    data_map[f'품목{idx}_부가세액'] = f"{int(_item_tax):,}"
                    data_map[f'품목{idx}_금액'] = f"{int(_item_supply_display):,}"
                    data_map[f'품목{idx}_총액'] = f"{int(_item_total):,}"

                try:
                    _expand_xlsx_template_text_rows(temp_path, data_map)
                except Exception as text_layout_error:
                    logger.warning(f"[서류생성] 템플릿 텍스트 행 높이 보정 실패: {text_layout_error}")

                if document_type == 'quotation':
                    try:
                        _insert_xlsx_quote_item_option_rows(temp_path, data_map)
                    except Exception as option_row_error:
                        logger.warning(f"[서류생성] 견적 옵션 행 삽입 실패: {option_row_error}")

                if hide_base_unit_price:
                    try:
                        _hide_xlsx_base_unit_price_columns(temp_path)
                    except Exception as hide_column_error:
                        logger.warning(f"[서류생성] 기준단가 열 숨김 실패: {hide_column_error}")
                
                # 1단계: ZIP에서 이미지/차트/미디어 파일 백업
                media_files = {}  # {filename: (ZipInfo, data)}
                
                try:
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        for file_info in zip_ref.infolist():
                            # 이미지, 차트, 미디어 파일 백업
                            if (file_info.filename.startswith('xl/media/') or 
                                file_info.filename.startswith('xl/drawings/') or 
                                file_info.filename.startswith('xl/charts/')):
                                media_files[file_info.filename] = (file_info, zip_ref.read(file_info.filename))
                except Exception as zip_error:
                    logger.error(f"[서류생성] ZIP 파일 열기 실패: {zip_error}")
                    raise
                
                
                # 2단계: ZIP 레벨에서 직접 sharedStrings.xml 수정 (한글 보존)
                import re
                from datetime import timedelta
                
                temp_modified = temp_path.replace('.xlsx', '_modified.xlsx')
                replaced_count = 0

                def replace_document_tokens(xml_str):
                    nonlocal replaced_count

                    for key, value in data_map.items():
                        pattern = f'{{{{{key}}}}}'
                        if pattern in xml_str:
                            xml_str = xml_str.replace(pattern, html.escape(str(value), quote=False))
                            replaced_count += 1

                    valid_date_pattern = r'\{\{유효일\+(\d+)\}\}'
                    valid_matches = re.findall(valid_date_pattern, xml_str)
                    for days_str in set(valid_matches):
                        days = int(days_str)
                        valid_date = schedule.visit_date + timedelta(days=days)
                        pattern = f'{{{{유효일+{days_str}}}}}'
                        formatted_date = valid_date.strftime('%Y년 %m월 %d일')
                        xml_str = xml_str.replace(pattern, html.escape(formatted_date, quote=False))
                        replaced_count += 1

                    item_patterns = re.findall(r'\{\{품목(\d+)_\w+\}\}', xml_str)
                    for item_pattern in set(item_patterns):
                        item_num = int(item_pattern)
                        if item_num > len(delivery_items):
                            pattern = r'\{\{품목' + str(item_num) + r'_\w+\}\}'
                            xml_str = re.sub(pattern, '', xml_str)
                    return xml_str
                
                with zipfile.ZipFile(temp_path, 'r') as zip_in:
                    with zipfile.ZipFile(temp_modified, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                        for item in zip_in.infolist():
                            data = zip_in.read(item.filename)
                            
                            # sharedStrings.xml 및 inlineStr 워크시트 처리 (한글 변수 치환)
                            if item.filename == 'xl/sharedStrings.xml' or (
                                item.filename.startswith('xl/worksheets/sheet')
                                and item.filename.endswith('.xml')
                            ):
                                try:
                                    xml_str = data.decode('utf-8')
                                    xml_str = replace_document_tokens(xml_str)
                                    # UTF-8로 인코딩 (한글 그대로)
                                    data = xml_str.encode('utf-8')
                                    
                                    # 수정된 내용 일부 로그
                                except Exception as xml_error:
                                    logger.warning(f"[서류생성] XLSX 텍스트 치환 처리 오류({item.filename}): {xml_error}")
                                    import traceback
                                    logger.error(traceback.format_exc())
                            
                            zip_out.writestr(item, data)
                
                # 원본 삭제하고 수정본으로 교체
                os.unlink(temp_path)
                shutil.move(temp_modified, temp_path)
                
                
                # 3단계: ZIP으로 미디어 파일 복원
                if media_files:
                    temp_output = temp_path.replace('.xlsx', '_with_media.xlsx')
                    
                    with zipfile.ZipFile(temp_path, 'r') as zip_in:
                        with zipfile.ZipFile(temp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                            # 기존 파일 모두 복사
                            for item in zip_in.infolist():
                                # 미디어 파일은 나중에 덮어쓰기
                                if item.filename not in media_files:
                                    data = zip_in.read(item.filename)
                                    zip_out.writestr(item, data)
                            
                            # 백업한 미디어 파일 복원 (원본 ZipInfo 사용)
                            for filename, (file_info, data) in media_files.items():
                                zip_out.writestr(file_info, data)
                    
                    # 원본 삭제하고 새 파일로 교체
                    os.unlink(temp_path)
                    shutil.move(temp_output, temp_path)
                
                if document_type in ['quotation', 'transaction_statement']:
                    try:
                        _strip_xlsx_bold_formatting(temp_path)
                    except Exception as bold_error:
                        logger.warning(f"[서류생성] 굵게 서식 제거 실패: {bold_error}")

                try:
                    _ensure_xlsx_a4_print_layout(temp_path)
                except Exception as layout_error:
                    logger.warning(f"[서류생성] A4 PDF 인쇄 설정 보정 실패: {layout_error}")
                
                # 파일명에 사용할 정보 준비
                import pytz
                korea_tz = pytz.timezone('Asia/Seoul')
                today_for_filename = timezone.now().astimezone(korea_tz)
                today_str = today_for_filename.strftime('%Y%m%d')
                company_name = company.name
                customer_company = schedule.followup.company.name if schedule.followup.company else schedule.followup.customer_name
                # 서류 종류 한글명
                doc_type_names = {
                    'quotation': '견적서',
                    'transaction_statement': '거래명세서',
                    'delivery_note': '납품서',
                }
                doc_name = doc_type_names.get(document_type, document_template.name)
                if document_type == 'quotation' and quote_group_label:
                    doc_name = quote_group_label if quote_group_label.endswith('견적서') else f'{quote_group_label} 견적서'
                
                # 출력 형식에 따라 저장
                if output_format.lower() == 'pdf':
                    # PDF로 변환 (unoconv 사용)
                    pdf_path = temp_path.replace('.xlsx', '.pdf')
                    
                    try:
                        import subprocess
                        result = subprocess.run([
                            'unoconv',
                            '-f', 'pdf',
                            '-o', pdf_path,
                            temp_path
                        ], capture_output=True, timeout=30, check=True)
                        
                        
                        # PDF 파일 읽기
                        with open(pdf_path, 'rb') as f:
                            output_data = f.read()
                        
                        # 임시 파일 삭제
                        try:
                            os.unlink(temp_path)
                            os.unlink(pdf_path)
                        except:
                            pass
                        
                        # 파일명 및 Content-Type
                        file_name = f"[{company_name}] {customer_company}_{doc_name}({today_str}).pdf"
                        content_type = 'application/pdf'
                        
                    except Exception as pdf_error:
                        logger.warning(f"[서류생성] PDF 변환 실패: {pdf_error}. Excel 파일로 반환합니다.")
                        # PDF 변환 실패 시 Excel 파일 반환
                        with open(temp_path, 'rb') as f:
                            output_data = f.read()
                        
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                        
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        file_name = f"[{company_name}] {customer_company}_{doc_name}({today_str}).xlsx"
                    
                else:
                    # Excel 파일로 저장
                    
                    # 저장된 파일을 읽어서 반환
                    with open(temp_path, 'rb') as f:
                        output_data = f.read()
                    
                    # 임시 파일 삭제
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    # Content-Type 결정
                    if original_ext == '.xlsm':
                        content_type = 'application/vnd.ms-excel.sheet.macroEnabled.12'
                    elif original_ext == '.xls':
                        content_type = 'application/vnd.ms-excel'
                    else:  # .xlsx
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    
                    # 파일명 설정
                    file_name = f"[{company_name}] {customer_company}_{doc_name}({today_str}).xlsx"
                
                encoded_filename = quote(file_name)
                
                # 서류 생성 로그 저장. PDF는 일정 상세의 등록 서류 목록에서 재사용한다.
                from reporting.models import DocumentGenerationLog
                from django.core.files.base import ContentFile

                generation_log = DocumentGenerationLog(
                    company=company,
                    document_type=document_type,
                    schedule=schedule,
                    user=request.user,
                    transaction_number=transaction_number,
                    output_format=output_format,
                    filename=file_name[:255],
                    file_size=len(output_data),
                    quote_group=quote_group if quote_group_selected else '',
                )
                if content_type == 'application/pdf':
                    storage_name = f'{transaction_number}_{document_type}.pdf'
                    if document_type == 'quotation' and quote_group_selected:
                        storage_name = f'{transaction_number}_{_quote_group_filename_part(quote_group)}_{document_type}.pdf'
                    generation_log.file.save(storage_name, ContentFile(output_data), save=False)
                generation_log.save()
                
                # 응답
                response = HttpResponse(
                    output_data,
                    content_type=content_type
                )
                response['Content-Disposition'] = 'attachment'
                response['X-Filename'] = encoded_filename
                response['Access-Control-Expose-Headers'] = 'X-Filename'
                
                return response
                
            except Exception as excel_error:
                logger.error(f"엑셀 처리 오류: {excel_error}")
                import traceback
                logger.error(traceback.format_exc())
                
                # 정리
                try:
                    if 'temp_path' in locals() and os.path.exists(temp_path):
                        os.unlink(temp_path)
                    # Cloudinary에서 다운로드한 임시 파일 정리
                    if 'file_url' in locals() and ('cloudinary' in file_url or file_url.startswith('http')):
                        if os.path.exists(template_file_path):
                            os.unlink(template_file_path)
                except Exception as cleanup_error:
                    logger.error(f"정리 오류: {cleanup_error}")
                
                return JsonResponse({
                    'success': False,
                    'error': f'엑셀 파일 처리 중 오류가 발생했습니다: {str(excel_error)}'
                }, status=500)
            
            # 성공 시에도 Cloudinary 임시 파일 정리
            finally:
                try:
                    if 'file_url' in locals() and ('cloudinary' in file_url or file_url.startswith('http')):
                        if 'template_file_path' in locals() and os.path.exists(template_file_path):
                            os.unlink(template_file_path)
                except Exception as cleanup_error:
                    logger.error(f"최종 정리 오류: {cleanup_error}")
            
        else:
            # PDF 등 다른 형식은 그대로 다운로드 (향후 PDF 편집 기능 추가 예정)
            # CloudinaryField는 path 속성이 없으므로 template_file_path 사용
            file_path = template_file_path
            file_name = f"{document_template.name}_{schedule.followup.customer_name}_{timezone.now().strftime('%Y%m%d')}{original_ext}"
            
            content_type_map = {
                '.pdf': 'application/pdf',
            }
            content_type = content_type_map.get(original_ext, 'application/octet-stream')
            
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            
            encoded_filename = quote(file_name)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"; filename*=UTF-8\'\'{encoded_filename}'
            
            return response
        
    except Exception as e:
        logger.error(f"서류 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== 관리자 필터 API ====================

@login_required
@require_POST
def set_admin_filter(request):
    """
    관리자 필터 설정 (회사/사용자 선택)
    
    POST /reporting/set-admin-filter/
    Body: {
        "company_id": "1",
        "user_id": "2"
    }
    """
    # 관리자만 접근 가능
    if not request.is_admin:
        return JsonResponse({'success': False, 'error': '관리자만 접근 가능합니다.'}, status=403)
    
    try:
        data = json.loads(request.body)
        company_id = data.get('company_id', '')
        user_id = data.get('user_id', '')
        
        # 세션에 저장
        if company_id:
            request.session['admin_selected_company'] = int(company_id)
        else:
            request.session.pop('admin_selected_company', None)
        
        if user_id:
            request.session['admin_selected_user'] = int(user_id)
        else:
            request.session.pop('admin_selected_user', None)
        
        request.session.modified = True
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"관리자 필터 설정 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_company_users(request, company_id):
    """
    특정 회사의 사용자 목록 반환 (관리자용)
    
    GET /reporting/get-company-users/<company_id>/
    """
    # 관리자만 접근 가능
    if not request.is_admin:
        return JsonResponse({'success': False, 'error': '관리자만 접근 가능합니다.'}, status=403)
    
    try:
        users = User.objects.filter(
            userprofile__company_id=company_id
        ).select_related('userprofile')
        
        user_list = [{
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'username': user.username,
            'role': user.userprofile.get_role_display() if hasattr(user, 'userprofile') else ''
        } for user in users]
        
        return JsonResponse({'success': True, 'users': user_list})
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 오류: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# 법적 문서 뷰
# ============================================

def privacy_policy_view(request):
    """개인정보처리방침 페이지"""
    return render(request, 'reporting/privacy_policy.html')


def terms_of_service_view(request):
    """서비스 이용약관 페이지"""
    return render(request, 'reporting/terms_of_service.html')


@login_required
def customer_records_api(request, followup_id):
    """고객 부서의 전체 납품기록 및 견적기록을 가져오는 API (본인 기록만, 부서 기준)"""
    from decimal import Decimal
    
    try:
        followup = get_object_or_404(FollowUp, pk=followup_id)
        
        # 권한 체크 (같은 회사 고객도 접근 가능)
        if not can_access_followup(request.user, followup):
            return JsonResponse({
                'success': False,
                'error': '접근 권한이 없습니다.'
            }, status=403)
        
        # 본인 고객인지 확인
        is_own_customer = (request.user == followup.user)
        
        # 부서가 있는 경우 부서 내 모든 고객, 없으면 해당 고객만
        if followup.department:
            # 같은 부서의 모든 고객
            department_followups = FollowUp.objects.filter(department=followup.department)
            # 납품 기록 조회 (본인 기록만 - user 필터 + 부서 기준)
            delivery_schedules = Schedule.objects.filter(
                followup__in=department_followups,
                user=request.user,  # 본인 기록만
                activity_type='delivery'
            ).select_related('followup').prefetch_related('delivery_items_set').order_by('-visit_date')
        else:
            # 부서 정보가 없으면 해당 고객만
            delivery_schedules = Schedule.objects.filter(
                followup=followup,
                user=request.user,  # 본인 기록만
                activity_type='delivery'
            ).select_related('followup').prefetch_related('delivery_items_set').order_by('-visit_date')
        
        deliveries = []
        total_delivery_amount = Decimal('0')
        for schedule in delivery_schedules:
            items = []
            schedule_total = Decimal('0')
            
            # 1. 먼저 Schedule에 직접 연결된 delivery_items 확인
            delivery_items = list(schedule.delivery_items_set.all())
            
            # 2. Schedule에 없으면 연결된 History에서 가져오기
            if not delivery_items:
                from reporting.models import History
                related_history = History.objects.filter(schedule=schedule).first()
                if related_history:
                    delivery_items = list(related_history.delivery_items_set.all())
            
            for item in delivery_items:
                if item.total_price:
                    item_total = Decimal(str(item.total_price))
                else:
                    unit_price = item.unit_price if item.unit_price else Decimal('0')
                    item_total = vat.item_gross_total(item, unit_price=unit_price)
                items.append({
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                    'total_price': float(item_total),
                })
                schedule_total += item_total
            
            total_delivery_amount += schedule_total
            deliveries.append({
                'id': schedule.id,
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'customer_name': schedule.followup.customer_name if schedule.followup else '-',  # 고객명 추가
                'status': schedule.get_status_display(),
                'status_code': schedule.status,
                'items': items,
                'total_amount': float(schedule_total),
                'notes': schedule.notes or '',
            })
        
        # 견적 기록 조회 (본인 기록만 - user 필터 + 부서 기준)
        from reporting.models import Quote, History
        if followup.department:
            # 같은 부서의 모든 고객
            quote_records = Quote.objects.filter(
                followup__in=department_followups,
                user=request.user  # 본인 기록만
            ).select_related('schedule', 'followup').prefetch_related('items__product').order_by('-created_at')
        else:
            # 부서 정보가 없으면 해당 고객만
            quote_records = Quote.objects.filter(
                followup=followup,
                user=request.user  # 본인 기록만
            ).select_related('schedule', 'followup').prefetch_related('items__product').order_by('-created_at')
        
        quotes = []
        total_quote_amount = Decimal('0')
        quote_schedule_ids_from_models = set()
        for quote in quote_records:
            items = []
            quote_total = Decimal('0')
            if quote.schedule_id:
                quote_schedule_ids_from_models.add(quote.schedule_id)
            for item in quote.items.all():
                if item.subtotal:
                    item_total = Decimal(str(item.subtotal))
                else:
                    item_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                
                # 제품명 가져오기
                item_name = item.product.name if item.product else '제품명 없음'
                
                items.append({
                    'item_name': item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item_total),
                })
                quote_total += item_total
            
            total_quote_amount += quote_total
            
            # 견적 상태 결정
            status_display = quote.get_status_display() if hasattr(quote, 'get_status_display') else '견적'
            status_code = quote.status if hasattr(quote, 'status') else 'quote'
            
            # 날짜 결정 (schedule이 있으면 schedule의 날짜, 없으면 생성일)
            visit_date = quote.schedule.visit_date.strftime('%Y-%m-%d') if quote.schedule else quote.created_at.strftime('%Y-%m-%d')
            
            quotes.append({
                'id': quote.schedule.id if quote.schedule else quote.id,
                'visit_date': visit_date,
                'customer_name': quote.followup.customer_name if quote.followup else '-',  # 고객명 추가
                'status': status_display,
                'status_code': status_code,
                'items': items,
                'total_amount': float(quote_total),
                'notes': quote.notes or '',
            })

        if followup.department:
            quote_schedules = Schedule.objects.filter(
                followup__in=department_followups,
                user=request.user,
                activity_type='quote',
            )
        else:
            quote_schedules = Schedule.objects.filter(
                followup=followup,
                user=request.user,
                activity_type='quote',
            )
        quote_schedules = quote_schedules.exclude(
            id__in=quote_schedule_ids_from_models
        ).select_related('followup').prefetch_related(
            'delivery_items_set',
            Prefetch(
                'histories',
                queryset=History.objects.filter(
                    action_type='quote',
                    parent_history__isnull=True,
                ).prefetch_related('delivery_items_set').order_by('-created_at'),
                to_attr='quote_histories_for_records',
            ),
        ).order_by('-visit_date', '-visit_time')

        for schedule in quote_schedules:
            items = []
            schedule_total = Decimal('0')
            delivery_items = list(schedule.delivery_items_set.all())
            if not delivery_items:
                related_history = (
                    schedule.quote_histories_for_records[0]
                    if getattr(schedule, 'quote_histories_for_records', [])
                    else None
                )
                if related_history:
                    delivery_items = list(related_history.delivery_items_set.all())

            for item in delivery_items:
                if item.total_price:
                    item_total = Decimal(str(item.total_price))
                else:
                    unit_price = item.unit_price if item.unit_price else Decimal('0')
                    item_total = vat.item_gross_total(item, unit_price=unit_price)
                items.append({
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price) if item.unit_price else 0,
                    'total_price': float(item_total),
                })
                schedule_total += item_total

            if schedule_total <= 0 and schedule.expected_revenue:
                schedule_total = Decimal(str(schedule.expected_revenue))

            total_quote_amount += schedule_total
            quotes.append({
                'id': schedule.id,
                'visit_date': schedule.visit_date.strftime('%Y-%m-%d'),
                'customer_name': schedule.followup.customer_name if schedule.followup else '-',
                'status': schedule.get_activity_type_display(),
                'status_code': schedule.status,
                'items': items,
                'total_amount': float(schedule_total),
                'notes': schedule.notes or '',
                'source': 'quote_schedule',
            })
        
        # 응답 데이터 구성
        response_data = {
            'success': True,
            'customer': {
                'id': followup.id,
                'customer_name': followup.customer_name or '-',
                'company_name': followup.company.name if followup.company else '-',
                'department_name': followup.department.name if followup.department else '-',
            },
            'deliveries': deliveries,
            'delivery_count': len(deliveries),
            'total_delivery_amount': float(total_delivery_amount),
            'quotes': quotes,
            'quote_count': len(quotes),
            'total_quote_amount': float(total_quote_amount),
            'is_own_customer': is_own_customer,
        }
        
        # 동료 고객이고 기록이 없는 경우 안내 메시지 추가
        if not is_own_customer and len(deliveries) == 0 and len(quotes) == 0:
            response_data['message'] = '이 고객에 대한 본인의 납품/견적 기록이 없습니다.'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Customer records API error: {e}")
        return JsonResponse({
            'success': False,
            'error': '고객 기록을 가져오는 중 오류가 발생했습니다.'
        }, status=500)


@login_required
def category_create(request):
    """카테고리 생성"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            parent_id = request.POST.get('parent_id', '').strip()
            color = request.POST.get('color', '#007bff')
            description = request.POST.get('description', '').strip()
            order = int(request.POST.get('order', 0))
            
            if not name:
                return JsonResponse({'success': False, 'error': '카테고리명을 입력하세요.'})
            
            # 상위 카테고리 처리
            parent = None
            if parent_id and parent_id != '':
                try:
                    parent = CustomerCategory.objects.get(id=parent_id, user=request.user)
                except CustomerCategory.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '상위 카테고리를 찾을 수 없습니다.'})
            
            # 중복 체크
            if CustomerCategory.objects.filter(user=request.user, name=name, parent=parent).exists():
                return JsonResponse({'success': False, 'error': '이미 존재하는 카테고리명입니다.'})
            
            # 생성
            category = CustomerCategory.objects.create(
                user=request.user,
                name=name,
                parent=parent,
                color=color,
                description=description,
                order=order
            )
            
            return JsonResponse({
                'success': True,
                'category_id': category.id,
                'message': '카테고리가 생성되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def category_update(request, category_id):
    """카테고리 수정"""
    if request.method == 'POST':
        try:
            category = CustomerCategory.objects.get(id=category_id, user=request.user)
            
            name = request.POST.get('name', '').strip()
            parent_id = request.POST.get('parent_id', '').strip()
            color = request.POST.get('color', '#007bff')
            description = request.POST.get('description', '').strip()
            order = int(request.POST.get('order', 0))
            
            if not name:
                return JsonResponse({'success': False, 'error': '카테고리명을 입력하세요.'})
            
            # 상위 카테고리 처리
            parent = None
            if parent_id and parent_id != '':
                try:
                    parent = CustomerCategory.objects.get(id=parent_id, user=request.user)
                    # 자기 자신을 부모로 설정할 수 없음
                    if parent.id == category_id:
                        return JsonResponse({'success': False, 'error': '자기 자신을 상위 카테고리로 설정할 수 없습니다.'})
                    # 자신의 하위 카테고리를 부모로 설정할 수 없음 (순환 참조 방지)
                    if parent.parent_id == category_id:
                        return JsonResponse({'success': False, 'error': '하위 카테고리를 상위 카테고리로 설정할 수 없습니다.'})
                except CustomerCategory.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '상위 카테고리를 찾을 수 없습니다.'})
            
            # 중복 체크 (본인 제외)
            if CustomerCategory.objects.filter(user=request.user, name=name, parent=parent).exclude(id=category_id).exists():
                return JsonResponse({'success': False, 'error': '이미 존재하는 카테고리명입니다.'})
            
            # 수정
            category.name = name
            category.parent = parent
            category.color = color
            category.description = description
            category.order = order
            category.save()
            
            return JsonResponse({
                'success': True,
                'message': '카테고리가 수정되었습니다.'
            })
            
        except CustomerCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': '카테고리를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def department_assign_category(request, department_id):
    """부서에 카테고리 빠르게 할당"""
    if request.method == 'POST':
        try:
            department = Department.objects.get(id=department_id)
            
            # 권한 체크 - 부서에 속한 고객들의 담당자 확인
            followups = FollowUp.objects.filter(department=department)
            if followups.exists():
                # 첫 번째 고객의 담당자 권한으로 체크
                first_followup = followups.first()
                if not can_modify_user_data(request.user, first_followup.user):
                    return JsonResponse({'success': False, 'error': '수정 권한이 없습니다.'})
            elif not _can_access_department_account(request.user, department):
                # 연락처가 없는 부서는 계정 접근 권한으로 확인 (무검사 갭 차단)
                return JsonResponse({'success': False, 'error': '수정 권한이 없습니다.'})
            
            category_id = request.POST.get('category_id', '').strip()
            
            if category_id and category_id != '':
                try:
                    category = CustomerCategory.objects.get(id=category_id, user=request.user)
                    department.category = category
                except CustomerCategory.DoesNotExist:
                    return JsonResponse({'success': False, 'error': '카테고리를 찾을 수 없습니다.'})
            else:
                department.category = None
            
            department.save()
            
            return JsonResponse({
                'success': True,
                'message': '부서에 카테고리가 할당되었습니다.',
                'category_name': department.category.get_full_path() if department.category else '없음',
                'category_color': department.category.color if department.category else '#6c757d'
            })
            
        except Department.DoesNotExist:
            return JsonResponse({'success': False, 'error': '부서를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def category_delete(request, category_id):
    """카테고리 삭제"""
    if request.method == 'POST':
        try:
            category = CustomerCategory.objects.get(id=category_id, user=request.user)
            category_name = category.name
            
            # 이 카테고리를 사용하는 부서들의 카테고리를 None으로 변경
            Department.objects.filter(category=category).update(category=None)
            
            # 카테고리 삭제
            category.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'"{category_name}" 카테고리가 삭제되었습니다.'
            })
            
        except CustomerCategory.DoesNotExist:
            return JsonResponse({'success': False, 'error': '카테고리를 찾을 수 없습니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# ============================================
# 부서 메모 API
# ============================================

@login_required
@require_http_methods(["GET", "POST"])
def department_memo_api(request, department_id):
    """부서 메모 조회/저장 API"""
    from reporting.models import DepartmentMemo, Department

    department = get_object_or_404(Department, pk=department_id)

    # 권한 확인: 접근 가능한 계정(부서)만 조회/저장 가능 (교차 테넌트 차단)
    if not _can_access_department_account(request.user, department):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

    if request.method == 'GET':
        memo = department.memos.order_by('-updated_at').first()
        if memo:
            return JsonResponse({
                'success': True,
                'content': memo.content,
                'updated_at': memo.updated_at.strftime('%Y-%m-%d %H:%M'),
                'updated_by': memo.created_by.get_full_name() or memo.created_by.username,
            })
        return JsonResponse({'success': True, 'content': '', 'updated_at': None, 'updated_by': None})
    
    # POST: 저장 (기존 메모 업데이트 또는 신규 생성)
    content = request.POST.get('content', '').strip()
    
    memo = department.memos.order_by('-updated_at').first()
    if memo:
        memo.content = content
        memo.created_by = request.user
        memo.save()
    else:
        memo = DepartmentMemo.objects.create(
            department=department,
            content=content,
            created_by=request.user,
        )
    
    return JsonResponse({
        'success': True,
        'content': memo.content,
        'updated_at': memo.updated_at.strftime('%Y-%m-%d %H:%M'),
        'updated_by': request.user.get_full_name() or request.user.username,
    })

