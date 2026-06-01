"""Demo management JSON APIs."""

import json

from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from reporting.models import DemoRecord, Department, FollowUp, Product
from reporting.views import (
    _api_login_required_response,
    _can_manage_department_account,
    _dashboard_scope_users,
    _parse_iso_date_or_none,
    _user_display_name,
    can_modify_user_data,
    get_accessible_products,
    get_user_profile,
    manager_core_readonly_message,
)


def _demo_int(value, default=None):
    try:
        if value in [None, '']:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _demo_json_payload(request):
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _demo_status_options():
    return [{'value': value, 'label': label} for value, label in DemoRecord.STATUS_CHOICES]


def _demo_product_payload(product):
    return {
        'id': product.id,
        'productCode': product.product_code,
        'name': product.product_code,
        'description': product.description or '',
        'unit': product.unit or 'EA',
        'specification': product.specification or '',
        'standardPrice': int(product.standard_price or 0),
        'currentPrice': int(product.get_current_price() or 0),
        'isPromo': bool(product.is_promo),
    }


def _demo_scope_users(request):
    user_profile = get_user_profile(request.user)
    return _dashboard_scope_users(request, user_profile)


def _demo_accessible_departments(scope_users):
    return (
        Department.objects.filter(
            Q(created_by__in=scope_users)
            | Q(company__created_by__in=scope_users)
            | Q(followup_departments__user__in=scope_users)
        )
        .select_related('company', 'created_by')
        .distinct()
    )


def _demo_records_queryset(scope_users):
    return (
        DemoRecord.objects.filter(
            Q(created_by__in=scope_users)
            | Q(owner__in=scope_users)
            | Q(followup__user__in=scope_users)
            | Q(department__created_by__in=scope_users)
            | Q(company__created_by__in=scope_users)
        )
        .select_related(
            'company',
            'department',
            'followup',
            'followup__user',
            'product',
            'owner',
            'created_by',
        )
        .distinct()
    )


def _demo_can_manage_record(actor, record):
    profile = get_user_profile(actor)
    if profile.is_admin():
        return True
    if profile.is_manager():
        return False
    return bool(
        record.created_by_id == actor.id
        or record.owner_id == actor.id
        or record.followup_id and record.followup.user_id == actor.id
        or record.department_id and record.department.created_by_id == actor.id
        or record.company_id and record.company.created_by_id == actor.id
    )


def _demo_account_payload(department, contacts_by_department=None):
    contacts = contacts_by_department.get(department.id, []) if contacts_by_department else []
    contact_names = [contact.customer_name for contact in contacts if contact.customer_name]
    return {
        'departmentId': department.id,
        'departmentName': department.name,
        'companyId': department.company_id,
        'companyName': department.company.name if department.company_id else '',
        'label': ' / '.join(part for part in [
            department.company.name if department.company_id else '',
            department.name,
        ] if part),
        'contactCount': len(contacts),
        'contacts': [
            {
                'id': contact.id,
                'name': contact.customer_name or '이름 없음',
                'ownerName': _user_display_name(contact.user),
            }
            for contact in contacts[:8]
        ],
        'searchText': ' '.join([
            department.company.name if department.company_id else '',
            department.name,
            ' '.join(contact_names),
            ' '.join(_user_display_name(contact.user) for contact in contacts),
        ]).strip(),
    }


def _demo_options_payload(request, scope_users):
    departments = list(_demo_accessible_departments(scope_users).order_by('company__name', 'name')[:500])
    department_ids = [department.id for department in departments]
    contacts_by_department = {}
    for contact in (
        FollowUp.objects.filter(department_id__in=department_ids, user__in=scope_users)
        .select_related('user')
        .order_by('customer_name', 'id')[:1200]
    ):
        contacts_by_department.setdefault(contact.department_id, []).append(contact)

    products = list(get_accessible_products(request).order_by('product_code')[:500])
    return {
        'accounts': [_demo_account_payload(department, contacts_by_department) for department in departments],
        'products': [_demo_product_payload(product) for product in products],
        'owners': [
            {
                'id': user.id,
                'name': _user_display_name(user),
                'username': user.username,
            }
            for user in scope_users.order_by('first_name', 'last_name', 'username')
        ],
        'statuses': _demo_status_options(),
    }


def _demo_record_payload(record, actor=None):
    product_label = ''
    product_code = ''
    if record.product_id:
        product_code = record.product.product_code
        product_label = product_code
    product_label = product_label or record.product_name or '제품 미지정'
    return {
        'id': record.id,
        'companyId': record.company_id,
        'companyName': record.company.name if record.company_id else '',
        'departmentId': record.department_id,
        'departmentName': record.department.name if record.department_id else '',
        'customerId': record.followup_id,
        'customerName': record.followup.customer_name if record.followup_id else '',
        'customerHref': f'/customers/{record.followup_id}/' if record.followup_id else '',
        'accountHref': f'/accounts/{record.department_id}/' if record.department_id else '',
        'productId': record.product_id,
        'productCode': product_code,
        'productName': product_label,
        'serialNumber': record.serial_number or '',
        'quantity': record.quantity,
        'status': record.status,
        'statusLabel': record.get_status_display(),
        'startDate': record.start_date.isoformat() if record.start_date else '',
        'expectedReturnDate': record.expected_return_date.isoformat() if record.expected_return_date else '',
        'returnedDate': record.returned_date.isoformat() if record.returned_date else '',
        'ownerId': record.owner_id,
        'ownerName': _user_display_name(record.owner) if record.owner_id else '',
        'notes': record.notes or '',
        'createdByName': _user_display_name(record.created_by) if record.created_by_id else '',
        'createdAt': record.created_at.isoformat() if record.created_at else '',
        'updatedAt': record.updated_at.isoformat() if record.updated_at else '',
        'canManage': _demo_can_manage_record(actor, record) if actor else False,
    }


def _demo_apply_filters(queryset, request):
    query = (request.GET.get('q') or '').strip()
    if query:
        queryset = queryset.filter(
            Q(company__name__icontains=query)
            | Q(department__name__icontains=query)
            | Q(followup__customer_name__icontains=query)
            | Q(product__product_code__icontains=query)
            | Q(product_name__icontains=query)
            | Q(serial_number__icontains=query)
            | Q(notes__icontains=query)
        )

    status = (request.GET.get('status') or '').strip()
    if status and status != 'all':
        queryset = queryset.filter(status=status)

    product_id = _demo_int(request.GET.get('product'))
    if product_id:
        queryset = queryset.filter(product_id=product_id)

    owner_id = _demo_int(request.GET.get('owner'))
    if owner_id:
        queryset = queryset.filter(Q(owner_id=owner_id) | Q(created_by_id=owner_id) | Q(followup__user_id=owner_id))

    customer_id = _demo_int(request.GET.get('customer'))
    if customer_id:
        queryset = queryset.filter(followup_id=customer_id)

    department_id = _demo_int(request.GET.get('department'))
    if department_id:
        queryset = queryset.filter(department_id=department_id)

    return queryset


def _demo_sorted_queryset(queryset, request):
    sort_key = (request.GET.get('sort') or 'updated').strip()
    direction = '' if (request.GET.get('order') or 'desc') == 'asc' else '-'
    sort_map = {
        'account': ['company__name', 'department__name'],
        'product': ['product__product_code', 'product_name'],
        'status': ['status', '-updated_at'],
        'startDate': ['start_date', '-updated_at'],
        'expectedReturnDate': ['expected_return_date', '-updated_at'],
        'updated': ['updated_at', 'id'],
    }
    fields = sort_map.get(sort_key, sort_map['updated'])
    ordered_fields = []
    for field in fields:
        if field.startswith('-'):
            ordered_fields.append(field[1:] if direction else field)
        else:
            ordered_fields.append(f'{direction}{field}')
    return queryset.order_by(*ordered_fields)


def _demo_summary_payload(queryset):
    today = timezone.localdate()
    stats = queryset.aggregate(
        total=Count('id', distinct=True),
        scheduled=Count('id', filter=Q(status=DemoRecord.STATUS_SCHEDULED), distinct=True),
        active=Count('id', filter=Q(status=DemoRecord.STATUS_ACTIVE), distinct=True),
        returned=Count('id', filter=Q(status=DemoRecord.STATUS_RETURNED), distinct=True),
        converted=Count('id', filter=Q(status=DemoRecord.STATUS_CONVERTED), distinct=True),
        cancelled=Count('id', filter=Q(status=DemoRecord.STATUS_CANCELLED), distinct=True),
        overdue=Count(
            'id',
            filter=Q(
                status__in=[DemoRecord.STATUS_SCHEDULED, DemoRecord.STATUS_ACTIVE],
                expected_return_date__lt=today,
            ),
            distinct=True,
        ),
    )
    return {key: int(value or 0) for key, value in stats.items()}


@ensure_csrf_cookie
@never_cache
@require_http_methods(["GET"])
def demo_records_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    scope_users, selected_user = _demo_scope_users(request)
    base_queryset = _demo_records_queryset(scope_users)
    filtered_queryset = _demo_apply_filters(base_queryset, request)
    rows = list(_demo_sorted_queryset(filtered_queryset, request)[:500])
    profile = get_user_profile(request.user)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'scope': {
            'label': _user_display_name(selected_user) if selected_user else (
                _user_display_name(request.user) if not profile.can_view_all_users()
                else f'{profile.company.name} 팀' if profile.company else '전체'
            ),
            'userCount': scope_users.count(),
            'canViewAll': profile.can_view_all_users(),
            'selectedUserId': selected_user.id if selected_user else None,
        },
        'summary': _demo_summary_payload(filtered_queryset),
        'demos': [_demo_record_payload(record, request.user) for record in rows],
        'options': _demo_options_payload(request, scope_users),
        'links': {
            'self': reverse('reporting:demo_records_api'),
            'create': reverse('reporting:demo_record_create_api'),
        },
        'permissions': {
            'canCreate': not profile.is_manager(),
            'readOnlyMessage': '' if not profile.is_manager() else manager_core_readonly_message('데모 기록'),
        },
    })


def _demo_resolve_mutation_payload(request, payload, existing=None):
    scope_users, _selected_user = _demo_scope_users(request)
    profile = get_user_profile(request.user)
    if profile.is_manager():
        return None, JsonResponse({
            'success': False,
            'error': manager_core_readonly_message('데모 기록'),
        }, status=403)

    department_id = _demo_int(payload.get('departmentId') or payload.get('department_id'))
    if not department_id and existing:
        department_id = existing.department_id
    department = _demo_accessible_departments(scope_users).filter(pk=department_id).first()
    if not department:
        return None, JsonResponse({
            'success': False,
            'error': '접근 가능한 부서/연구실을 선택하세요.',
        }, status=400)
    if not _can_manage_department_account(request.user, department) and not profile.is_admin():
        return None, JsonResponse({
            'success': False,
            'error': '이 계정의 데모 기록을 수정할 권한이 없습니다.',
        }, status=403)

    followup_id = _demo_int(payload.get('customerId') or payload.get('followupId') or payload.get('followup_id'))
    followup = None
    if followup_id:
        followup = FollowUp.objects.filter(
            pk=followup_id,
            department=department,
            user__in=scope_users,
        ).select_related('user').first()
        if not followup:
            return None, JsonResponse({
                'success': False,
                'error': '선택한 고객이 해당 계정에 없습니다.',
            }, status=400)
        if not can_modify_user_data(request.user, followup.user):
            return None, JsonResponse({
                'success': False,
                'error': '선택한 고객의 데모 기록을 수정할 권한이 없습니다.',
            }, status=403)

    product_id = _demo_int(payload.get('productId') or payload.get('product_id'))
    product = None
    product_name = (payload.get('productName') or payload.get('product_name') or '').strip()
    if product_id:
        product = get_accessible_products(request).filter(pk=product_id).first()
        if not product and existing and existing.product_id == product_id:
            product = Product.objects.filter(pk=product_id).first()
        if not product:
            return None, JsonResponse({
                'success': False,
                'error': '접근 가능한 제품을 선택하세요.',
            }, status=400)
        product_name = product.product_code
    if not product and not product_name:
        return None, JsonResponse({
            'success': False,
            'error': '제품을 선택하거나 제품명을 입력하세요.',
        }, status=400)

    owner_id = _demo_int(payload.get('ownerId') or payload.get('owner_id'), request.user.id)
    owner = scope_users.filter(pk=owner_id).first() if owner_id else request.user
    if owner_id and not owner:
        return None, JsonResponse({
            'success': False,
            'error': '접근 가능한 담당자를 선택하세요.',
        }, status=400)

    status = (payload.get('status') or (existing.status if existing else DemoRecord.STATUS_ACTIVE)).strip()
    valid_statuses = {value for value, _label in DemoRecord.STATUS_CHOICES}
    if status not in valid_statuses:
        return None, JsonResponse({
            'success': False,
            'error': '데모 상태를 확인하세요.',
        }, status=400)

    quantity = _demo_int(payload.get('quantity'), existing.quantity if existing else 1)
    if not quantity or quantity < 1:
        quantity = 1

    return {
        'company': department.company,
        'department': department,
        'followup': followup,
        'product': product,
        'product_name': product_name,
        'serial_number': (payload.get('serialNumber') or payload.get('serial_number') or '').strip(),
        'quantity': quantity,
        'status': status,
        'start_date': _parse_iso_date_or_none(payload.get('startDate') or payload.get('start_date')),
        'expected_return_date': _parse_iso_date_or_none(
            payload.get('expectedReturnDate') or payload.get('expected_return_date')
        ),
        'returned_date': _parse_iso_date_or_none(payload.get('returnedDate') or payload.get('returned_date')),
        'owner': owner,
        'notes': (payload.get('notes') or '').strip(),
    }, None


@never_cache
@require_http_methods(["POST"])
@transaction.atomic
def demo_record_create_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    payload = _demo_json_payload(request)
    if payload is None:
        return JsonResponse({'success': False, 'error': '요청 형식을 확인하세요.'}, status=400)

    values, error_response = _demo_resolve_mutation_payload(request, payload)
    if error_response:
        return error_response

    record = DemoRecord.objects.create(created_by=request.user, **values)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '데모 기록을 등록했습니다.',
        'demo': _demo_record_payload(record, request.user),
    }, status=201)


@never_cache
@require_http_methods(["POST"])
@transaction.atomic
def demo_record_update_api(request, demo_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    scope_users, _selected_user = _demo_scope_users(request)
    record = get_object_or_404(_demo_records_queryset(scope_users), pk=demo_id)
    if not _demo_can_manage_record(request.user, record):
        return JsonResponse({'success': False, 'error': '이 데모 기록을 수정할 권한이 없습니다.'}, status=403)

    payload = _demo_json_payload(request)
    if payload is None:
        return JsonResponse({'success': False, 'error': '요청 형식을 확인하세요.'}, status=400)

    values, error_response = _demo_resolve_mutation_payload(request, payload, existing=record)
    if error_response:
        return error_response

    for field, value in values.items():
        setattr(record, field, value)
    record.save()
    record = _demo_records_queryset(scope_users).get(pk=record.pk)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '데모 기록을 저장했습니다.',
        'demo': _demo_record_payload(record, request.user),
    })


@never_cache
@require_http_methods(["POST"])
@transaction.atomic
def demo_record_delete_api(request, demo_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    scope_users, _selected_user = _demo_scope_users(request)
    record = get_object_or_404(_demo_records_queryset(scope_users), pk=demo_id)
    if not _demo_can_manage_record(request.user, record):
        return JsonResponse({'success': False, 'error': '이 데모 기록을 삭제할 권한이 없습니다.'}, status=403)
    record.delete()
    return JsonResponse({
        'success': True,
        'source': 'django',
        'message': '데모 기록을 삭제했습니다.',
    })


def demo_customer_summary_payload(request, scope_users, *, followup=None, department=None, can_manage=False):
    target_department = department or (followup.department if followup and followup.department_id else None)
    base_queryset = _demo_records_queryset(scope_users)
    if target_department:
        queryset = base_queryset.filter(department=target_department)
    elif followup:
        queryset = base_queryset.filter(followup=followup)
    else:
        queryset = base_queryset.none()

    rows = list(queryset.order_by('-updated_at', '-created_at')[:12])
    query_key = f'department={target_department.id}' if target_department else (
        f'customer={followup.id}' if followup else ''
    )
    demos_href = f'/demos/?{query_key}' if query_key else '/demos/'
    create_href = f'/demos/?create=1&{query_key}' if query_key and can_manage else ''

    return {
        'canManage': bool(can_manage),
        'message': '' if can_manage else '데모 현황은 읽기 전용입니다.',
        'metrics': _demo_summary_payload(queryset),
        'links': {
            'demos': demos_href,
            'createDemo': create_href,
        },
        'options': {
            'statuses': _demo_status_options(),
        },
        'demos': [_demo_record_payload(record, request.user) for record in rows],
    }
