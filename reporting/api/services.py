"""서비스 메뉴 API — A/S·수리·점검·교정 기록을 모으고, 고객 연락과 수리완료보고서에 쓴다.

범위 규칙은 아침회의와 같다(`_dashboard_scope_users`): 영업사원은 자기 것, 매니저는 팀.
매니저 본인은 영업담당 범위에 안 들어갈 수 있으므로 직접 적은 기록은 항상 보이고 고칠 수 있다.
유상 서비스 금액은 서비스 현황용이며 매출 집계(`delivered_revenue_rows`)에는 넣지 않는다.
"""

import json
from collections import Counter
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from reporting.models import FollowUp, ServiceCase, ServiceEquipment, ServicePart
from reporting.views import (
    _api_login_required_response,
    _dashboard_scope_users,
    _user_display_name,
    can_access_followup,
    get_accessible_products,
    get_same_company_users,
    get_user_profile,
)

OPEN_STATUSES = ('received', 'in_progress', 'waiting')
LIST_LIMIT = 500
RELATED_LIMIT = 10
CUSTOMER_SEARCH_LIMIT = 20
PRODUCT_SEARCH_LIMIT = 20
MAX_PARTS = 50
MAX_EQUIPMENTS = 30


def _error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _parse_payload(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _parse_amount(value):
    if value in (None, ''):
        return None
    try:
        amount = Decimal(str(value).replace(',', '')).quantize(Decimal('1'))
    except (InvalidOperation, ValueError):
        raise ValueError('금액은 숫자로 입력하세요.')
    if amount < 0:
        raise ValueError('금액은 0 이상이어야 합니다.')
    return amount


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value) if value != '' else None
    except (TypeError, ValueError):
        return None


def _money(value):
    return int(value) if value is not None else None


def _scope(request):
    profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, profile)
    return scope_users, selected_user, set(scope_users.values_list('id', flat=True))


def visible_service_cases(request, scope_users):
    """화면에 보여줄 서비스 케이스. 아침회의도 이 범위를 쓴다."""
    return ServiceCase.objects.filter(Q(assigned_to__in=scope_users) | Q(created_by=request.user)).distinct()


def can_edit_case(case, viewer, scope_user_ids):
    return case.assigned_to_id in scope_user_ids or case.created_by_id == viewer.id


def case_title(case):
    """목록·회의에 보이는 요약. 비어 있으면 증상·처리 내용 첫 줄로 대신한다(회의에서 적은 여러 줄은 그대로)."""
    if (case.title or '').strip():
        return case.title.strip()
    for text in (case.symptom, case.resolution, case.diagnosis):
        line = (text or '').strip().splitlines()[0].strip() if (text or '').strip() else ''
        if line:
            return line[:200]
    return case.get_case_type_display()


def _customer_name(followup):
    if followup is None:
        return ''
    return followup.customer_name or followup.manager or '담당자 미정'


def _customer_payload(followup):
    if followup is None:
        return None
    return {
        'id': followup.id,
        'name': _customer_name(followup),
        'company': followup.company.name if followup.company_id else '',
        'department': followup.department.name if followup.department_id else '',
        'phone': followup.phone_number or '',
        'email': followup.email or '',
        'href': f'/customers/{followup.id}/',
    }


def _requester_payload(case):
    """업체가 맡긴 건의 의뢰처. 사용자(엔드유저)와 같으면 None."""
    followup = case.requester_followup if case.requester_followup_id else None
    if followup is None and not case.requester_name and not case.requester_contact:
        return None
    name = case.requester_name or (followup.company.name if followup is not None and followup.company_id else '')
    return {
        'name': name,
        'contact': case.requester_contact,
        'customer': _customer_payload(followup),
    }


def _equipments(case):
    """장비 목록(prefetch 그대로). 장비 목록이 없는 옛 기록은 케이스 칸·연결 장비로 한 줄을 만든다."""
    rows = list(case.equipments.all())
    if rows:
        return rows
    name = case.equipment_name or (case.asset.asset_name if case.asset_id else '')
    brand = case.brand
    serial = case.serial_number or (case.asset.serial_number if case.asset_id else '')
    if name or brand or serial:
        return [ServiceEquipment(name=name, brand=brand, serial_number=serial)]
    return []


def _single_label(equipment):
    # "브랜드 장비명" 순서로 읽는다(예: Eppendorf 원심분리기)
    return ' '.join(part for part in (equipment.brand, equipment.name) if part)


def _equipment_label(case, equipments=None):
    equipments = _equipments(case) if equipments is None else equipments
    if not equipments:
        return ''
    first = equipments[0]
    label = _single_label(first) or (f'S/N {first.serial_number}' if first.serial_number else '장비')
    return f'{label} 외 {len(equipments) - 1}대' if len(equipments) > 1 else label


def _serials(equipments):
    seen = []
    for equipment in equipments:
        serial = (equipment.serial_number or '').strip()
        if serial and serial not in seen:
            seen.append(serial)
    return seen


def case_equipments_payload(case):
    """아침회의처럼 장비 목록만 보여주는 곳용."""
    return [_equipment_payload(equipment) for equipment in _equipments(case)]


def _equipment_payload(equipment):
    return {
        'id': equipment.id,
        'name': equipment.name,
        'brand': equipment.brand,
        'serialNumber': equipment.serial_number,
        'note': equipment.note,
    }


def _parts(case):
    # prefetch 한 목록을 그대로 쓴다(목록 화면에서 건마다 쿼리가 나가지 않게)
    return list(case.parts.all())


def _parts_total(parts):
    """부품 공급가 합계(단가는 부가세 별도)."""
    return sum(int(part.unit_price) * part.quantity for part in parts if part.unit_price is not None)


def _with_vat(amount):
    """공급가 → 부가세 10% 포함 금액(원 단위 반올림)."""
    return int((Decimal(amount) * Decimal('1.1')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def case_summary_payload(case, viewer, scope_user_ids):
    parts = _parts(case)
    equipments = _equipments(case)
    serials = _serials(equipments)
    return {
        'id': case.id,
        'date': case.received_date.isoformat() if case.received_date else None,
        'completedDate': case.completed_date.isoformat() if case.completed_date else None,
        'status': case.status,
        'statusLabel': case.get_status_display(),
        'type': case.case_type,
        'typeLabel': case.get_case_type_display(),
        'title': case_title(case),
        'institution': case.institution or (case.followup.company.name if case.followup_id and case.followup.company_id else ''),
        'customer': _customer_payload(case.followup),
        'requester': _requester_payload(case),
        'equipment': _equipment_label(case, equipments),
        'equipmentCount': len(equipments),
        'serialNumber': serials[0] if serials else '',
        'serialNumbers': serials,
        'ownerId': case.assigned_to_id,
        'owner': _user_display_name(case.assigned_to) if case.assigned_to_id else '',
        'chargeType': case.charge_type,
        'chargeLabel': case.get_charge_type_display(),
        'chargeAmount': _money(case.charge_amount),
        'partsCount': sum(part.quantity for part in parts),
        'partNames': [part.name for part in parts],
        'canEdit': can_edit_case(case, viewer, scope_user_ids),
        'href': f'/services/{case.id}/',
    }


def _part_payload(part):
    return {
        'id': part.id,
        'productId': part.product_id,
        'name': part.name,
        'partNumber': part.part_number,
        'quantity': part.quantity,
        'unitPrice': _money(part.unit_price),
        'amount': int(part.unit_price) * part.quantity if part.unit_price is not None else None,
    }


def _case_queryset(queryset):
    return queryset.select_related(
        'followup', 'followup__company', 'followup__department',
        'requester_followup', 'requester_followup__company', 'requester_followup__department',
        'assigned_to', 'created_by', 'asset',
    ).prefetch_related(
        Prefetch('parts', queryset=ServicePart.objects.order_by('position', 'id')),
        Prefetch('equipments', queryset=ServiceEquipment.objects.order_by('position', 'id')),
    )


def _report_company(case):
    owner = case.assigned_to or case.created_by
    profile = get_user_profile(owner) if owner else None
    company = getattr(profile, 'company', None) if profile else None
    return company.name if company else ''


def case_detail_payload(case, viewer, scope_user_ids, related):
    payload = case_summary_payload(case, viewer, scope_user_ids)
    parts = _parts(case)
    equipments = _equipments(case)
    payload.update({
        'rawTitle': case.title,
        'equipments': [_equipment_payload(equipment) for equipment in equipments],
        'equipmentName': equipments[0].name if equipments else '',
        'brand': equipments[0].brand if equipments else '',
        'symptom': case.symptom,
        'diagnosis': case.diagnosis,
        'resolution': case.resolution,
        'dueDate': case.due_date.isoformat() if case.due_date else None,
        'parts': [_part_payload(part) for part in parts],
        'partsAmount': _parts_total(parts),  # 공급가 합계
        'partsVat': _with_vat(_parts_total(parts)) - _parts_total(parts),
        'partsTotal': _with_vat(_parts_total(parts)),  # 부가세 포함 합계
        'createdBy': _user_display_name(case.created_by) if case.created_by_id else '',
        'createdAt': timezone.localtime(case.created_at).date().isoformat(),
        'updatedAt': timezone.localtime(case.updated_at).isoformat(),
        'reportCompany': _report_company(case),
        'related': related,
    })
    return payload


def _related_cases(request, scope_users, case):
    """같은 장비(시리얼)를 먼저, 없으면 같은 고객의 다른 서비스. 연락할 때 지난 이력을 같이 보려는 용도.
    장비가 여러 대면 그중 어느 시리얼이든 겹치는 기록을 모은다."""
    serials = _serials(_equipments(case))
    base = visible_service_cases(request, scope_users).exclude(pk=case.pk)
    if serials:
        queryset = base.filter(Q(equipments__serial_number__in=serials) | Q(serial_number__in=serials)).distinct()
        basis = 'serial'
    elif case.followup_id:
        queryset, basis = base.filter(followup_id=case.followup_id), 'customer'
    elif case.institution:
        queryset, basis = base.filter(institution=case.institution), 'institution'
    else:
        return {'basis': '', 'items': []}
    rows = queryset.select_related('assigned_to').order_by('-received_date', '-id')[:RELATED_LIMIT]
    return {
        'basis': basis,
        'items': [
            {
                'id': row.id,
                'date': row.received_date.isoformat() if row.received_date else None,
                'typeLabel': row.get_case_type_display(),
                'statusLabel': row.get_status_display(),
                'title': case_title(row),
                'diagnosis': (row.diagnosis or '').strip()[:200],
                'href': f'/services/{row.id}/',
            }
            for row in rows
        ],
    }


# ------------------------------------------------------------------ 목록·현황

def _year_summary(cases, year):
    months = [0] * 12
    types = Counter()
    institutions = Counter()
    serials = {}
    open_count = completed = paid_count = paid_amount = parts_count = 0
    for case in cases:
        if case.received_date:
            months[case.received_date.month - 1] += 1
        types[(case.case_type, case.get_case_type_display())] += 1
        institution = case.institution or (case.followup.company.name if case.followup_id and case.followup.company_id else '')
        if institution:
            institutions[institution] += 1
        if case.status == 'completed':
            completed += 1
        elif case.status in OPEN_STATUSES:
            open_count += 1
        if case.charge_type == ServiceCase.CHARGE_PAID:
            paid_count += 1
            paid_amount += int(case.charge_amount or 0)
        parts_count += sum(part.quantity for part in _parts(case))
        equipments = _equipments(case)
        for serial in _serials(equipments):
            label = next((_single_label(row) for row in equipments if (row.serial_number or '').strip() == serial), '')
            entry = serials.setdefault(serial, {'serialNumber': serial, 'equipment': label, 'count': 0})
            entry['count'] += 1
            if not entry['equipment']:
                entry['equipment'] = label
    return {
        'year': year,
        'total': len(cases),
        'completed': completed,
        'open': open_count,
        'paidCount': paid_count,
        'paidAmount': paid_amount,
        'partsCount': parts_count,
        'byMonth': months,
        'byType': [
            {'type': key, 'label': label, 'count': count}
            for (key, label), count in types.most_common()
        ],
        'topInstitutions': [{'name': name, 'count': count} for name, count in institutions.most_common(5)],
        'repeatSerials': sorted(
            (entry for entry in serials.values() if entry['count'] >= 2),
            key=lambda entry: -entry['count'],
        )[:5],
    }


def _matches(case, query):
    haystack = ' '.join([
        case.title, case.institution,
        ' '.join(f'{row.brand} {row.name} {row.serial_number} {row.note}' for row in _equipments(case)),
        case.symptom, case.diagnosis, case.resolution,
        _customer_name(case.followup) if case.followup_id else '',
        case.requester_name, case.requester_contact,
        _customer_name(case.requester_followup) if case.requester_followup_id else '',
        ' '.join(part.name for part in _parts(case)),
    ]).lower()
    return all(term in haystack for term in query.lower().split())


@never_cache
@ensure_csrf_cookie
@require_GET
def services_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    scope_users, _selected, scope_ids = _scope(request)
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year') or today.year)
    except ValueError:
        year = today.year

    visible = visible_service_cases(request, scope_users)
    year_cases = list(_case_queryset(visible.filter(received_date__year=year)).order_by('-received_date', '-id'))
    summary = _year_summary(year_cases, year)

    status = request.GET.get('status') or ''
    case_type = request.GET.get('type') or ''
    owner_id = _int_or_none(request.GET.get('owner'))
    query = (request.GET.get('q') or '').strip()
    rows = year_cases
    if status == 'open':
        rows = [case for case in rows if case.status in OPEN_STATUSES]
    elif status:
        rows = [case for case in rows if case.status == status]
    if case_type:
        rows = [case for case in rows if case.case_type == case_type]
    if owner_id:
        rows = [case for case in rows if case.assigned_to_id == owner_id]
    if query:
        rows = [case for case in rows if _matches(case, query)]

    years = sorted({d.year for d in visible.dates('received_date', 'year')} | {today.year}, reverse=True)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'year': year,
        'years': years,
        'summary': summary,
        'items': [case_summary_payload(case, request.user, scope_ids) for case in rows[:LIST_LIMIT]],
        'truncated': len(rows) > LIST_LIMIT,
        'form': _form_options(scope_users),
    })


def _form_options(scope_users):
    return {
        'types': [{'value': value, 'label': label} for value, label in ServiceCase.CASE_TYPE_CHOICES],
        'statuses': [{'value': value, 'label': label} for value, label in ServiceCase.STATUS_CHOICES],
        'charges': [{'value': value, 'label': label} for value, label in ServiceCase.CHARGE_CHOICES],
        'owners': [{'id': user.id, 'name': _user_display_name(user)} for user in scope_users.order_by('username')],
    }


@never_cache
@ensure_csrf_cookie
@require_GET
def service_form_api(request):
    """새 서비스 기록 화면의 선택 항목(유형·상태·담당자)."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    scope_users, _selected, _scope_ids = _scope(request)
    return JsonResponse({'success': True, 'source': 'django', 'form': _form_options(scope_users), 'viewerId': request.user.id})


def _visible_case_or_404(request, scope_users, case_id):
    return get_object_or_404(_case_queryset(visible_service_cases(request, scope_users)), pk=case_id)


@never_cache
@ensure_csrf_cookie
@require_GET
def service_detail_api(request, case_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    scope_users, _selected, scope_ids = _scope(request)
    case = _visible_case_or_404(request, scope_users, case_id)
    return JsonResponse({
        'success': True,
        'source': 'django',
        'item': case_detail_payload(case, request.user, scope_ids, _related_cases(request, scope_users, case)),
        'form': _form_options(scope_users),
    })


@never_cache
@require_GET
def service_customer_search_api(request):
    """서비스 기록에 연결할 고객 검색. 같은 회사 영업사원의 고객까지 찾는다(고객 정보 조회 규칙과 같음)."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'success': True, 'items': []})
    followups = FollowUp.objects.filter(user__in=get_same_company_users(request.user)).select_related('company', 'department')
    for term in query.split():
        followups = followups.filter(
            Q(customer_name__icontains=term) | Q(manager__icontains=term)
            | Q(company__name__icontains=term) | Q(department__name__icontains=term)
        )
    rows = followups.order_by('company__name', 'department__name', 'customer_name')[:CUSTOMER_SEARCH_LIMIT]
    return JsonResponse({'success': True, 'items': [_customer_payload(followup) for followup in rows]})


def product_part_payload(product):
    """제품을 교체 부품 줄로 옮길 때 쓰는 값. 제품 코드가 품번, 설명 첫 줄이 부품명.

    단가는 제품 정상가(부가세 별도) 그대로. 부가세는 합계에서 붙인다(`_with_vat`).
    """
    description = (product.description or '').strip().splitlines()[0].strip() if (product.description or '').strip() else ''
    return {
        'id': product.id,
        'code': product.product_code,
        'name': (description or product.product_code)[:200],
        'specification': product.specification or '',
        'unit': product.unit or 'EA',
        'price': int(product.standard_price or 0),
    }


@never_cache
@require_GET
def service_product_search_api(request):
    """교체 부품으로 고를 제품 검색(제품 메뉴에서 볼 수 있는 활성 제품)."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    query = (request.GET.get('q') or '').strip()
    if not query:
        return JsonResponse({'success': True, 'items': []})
    products = get_accessible_products(request)
    for term in query.split():
        products = products.filter(
            Q(product_code__icontains=term) | Q(description__icontains=term) | Q(specification__icontains=term)
        )
    rows = products.order_by('product_code')[:PRODUCT_SEARCH_LIMIT]
    return JsonResponse({'success': True, 'items': [product_part_payload(product) for product in rows]})


# ------------------------------------------------------------------ 저장

def _accessible_followup(request, value, message):
    followup_id = _int_or_none(value)
    if not followup_id:
        return None
    followup = FollowUp.objects.select_related('company').filter(pk=followup_id).first()
    if followup is None or not can_access_followup(request.user, followup):
        raise ValueError(message)
    return followup


def _part_products(request, case, raw_parts):
    """부품 줄에 붙은 제품 id → 제품. 볼 수 없는 제품이면 ValueError.
    이미 이 기록에 붙어 있던 제품은 (나중에 비활성이 됐어도) 그대로 둘 수 있다."""
    ids = {_int_or_none(raw.get('productId')) for raw in raw_parts if isinstance(raw, dict)} - {None}
    if not ids:
        return {}
    products = {product.id: product for product in get_accessible_products(request).filter(pk__in=ids)}
    if case.pk:
        for part in case.parts.select_related('product').filter(product_id__in=ids - set(products)):
            products[part.product_id] = part.product
    if ids - set(products):
        raise ValueError('고를 수 없는 제품이 있습니다.')
    return products


def _apply_payload(case, payload, request, scope_ids, *, creating):
    """payload 를 case 에 옮긴다. 잘못된 값이면 ValueError(사용자에게 보여줄 문장)."""
    followup = _accessible_followup(request, payload.get('customerId'), '연결할 수 없는 고객입니다.')
    requester = _accessible_followup(request, payload.get('requesterId'), '연결할 수 없는 의뢰처입니다.')

    institution = str(payload.get('institution') or '').strip()
    if not institution and followup is not None and followup.company_id:
        institution = followup.company.name
    if not institution:
        raise ValueError('기관을 입력하거나 고객을 연결하세요.')

    texts = {
        'title': str(payload.get('title') or '').strip(),
        'symptom': str(payload.get('symptom') or '').strip(),
        'diagnosis': str(payload.get('diagnosis') or '').strip(),
        'resolution': str(payload.get('resolution') or '').strip(),
    }
    if not any(texts.values()):
        raise ValueError('요약이나 증상·점검·조치 중 하나는 입력하세요.')

    case_type = str(payload.get('type') or 'service')
    if case_type not in dict(ServiceCase.CASE_TYPE_CHOICES):
        raise ValueError('서비스 유형이 올바르지 않습니다.')
    status = str(payload.get('status') or 'received')
    if status not in dict(ServiceCase.STATUS_CHOICES):
        raise ValueError('상태가 올바르지 않습니다.')
    charge_type = str(payload.get('chargeType') or ServiceCase.CHARGE_FREE)
    if charge_type not in dict(ServiceCase.CHARGE_CHOICES):
        raise ValueError('유상/무상 값이 올바르지 않습니다.')

    service_date = _parse_date(payload.get('date')) or timezone.localdate()
    completed_date = _parse_date(payload.get('completedDate'))
    if status == 'completed':
        completed_date = completed_date or service_date
        if completed_date < service_date:
            raise ValueError('완료일은 서비스일보다 빠를 수 없습니다.')
    else:
        completed_date = None

    owner_id = _int_or_none(payload.get('ownerId'))
    if owner_id and owner_id in scope_ids:
        case.assigned_to_id = owner_id
    elif creating:
        case.assigned_to_id = request.user.id

    raw_parts = payload.get('parts') or []
    raw_parts = raw_parts if isinstance(raw_parts, list) else []
    products = _part_products(request, case, raw_parts)
    parts = []
    for index, raw in enumerate(raw_parts):
        if not isinstance(raw, dict):
            continue
        product = products.get(_int_or_none(raw.get('productId')))
        name = str(raw.get('name') or '').strip() or (product_part_payload(product)['name'] if product else '')
        if not name:
            continue
        try:
            quantity = int(raw.get('quantity') or 1)
        except (TypeError, ValueError):
            raise ValueError('부품 수량은 숫자로 입력하세요.')
        if quantity < 1:
            raise ValueError('부품 수량은 1 이상이어야 합니다.')
        parts.append(ServicePart(
            product=product,
            name=name[:200],
            part_number=(str(raw.get('partNumber') or '').strip() or (product.product_code if product else ''))[:100],
            quantity=quantity,
            unit_price=_parse_amount(raw.get('unitPrice')),  # 부가세 별도 단가
            position=index,
        ))
    if len(parts) > MAX_PARTS:
        raise ValueError(f'부품은 {MAX_PARTS}개까지 입력할 수 있습니다.')

    raw_equipments = payload.get('equipments')
    if raw_equipments is None:
        # 예전 형식(장비 한 대)도 받는다
        raw_equipments = [{
            'name': payload.get('equipmentName'),
            'brand': payload.get('brand'),
            'serialNumber': payload.get('serialNumber'),
        }]
    equipments = []
    for raw in raw_equipments if isinstance(raw_equipments, list) else []:
        if not isinstance(raw, dict):
            continue
        row = ServiceEquipment(
            name=str(raw.get('name') or '').strip()[:200],
            brand=str(raw.get('brand') or '').strip()[:200],
            serial_number=str(raw.get('serialNumber') or '').strip()[:120],
            note=str(raw.get('note') or '').strip()[:300],
        )
        if row.name or row.brand or row.serial_number or row.note:
            row.position = len(equipments)
            equipments.append(row)
    if len(equipments) > MAX_EQUIPMENTS:
        raise ValueError(f'장비는 {MAX_EQUIPMENTS}대까지 입력할 수 있습니다.')

    case.followup = followup
    case.institution = institution[:100]
    case.requester_followup = requester
    case.requester_name = str(payload.get('requesterName') or '').strip()[:200]
    case.requester_contact = str(payload.get('requesterContact') or '').strip()[:200]
    case.title = texts['title'][:200]
    case.symptom = texts['symptom']
    case.diagnosis = texts['diagnosis']
    case.resolution = texts['resolution']
    # 첫 장비는 케이스 칸에도 둔다(장비 하나만 보여주는 화면용)
    first = equipments[0] if equipments else None
    case.equipment_name = first.name if first else ''
    case.brand = first.brand if first else ''
    case.serial_number = first.serial_number if first else ''
    case.case_type = case_type
    case.status = status
    case.received_date = service_date
    case.completed_date = completed_date
    case.charge_type = charge_type
    case.charge_amount = _parse_amount(payload.get('chargeAmount')) if charge_type == ServiceCase.CHARGE_PAID else None
    if charge_type == ServiceCase.CHARGE_PAID and case.charge_amount is None:
        # 유상인데 청구 금액을 비우면 부품 합계에 부가세를 더해 넣는다. 단가 적힌 부품이 없으면 비워 둔다.
        priced = [part for part in parts if part.unit_price is not None]
        case.charge_amount = _with_vat(_parts_total(priced)) if priced else None
    return parts, equipments


def _save_with_parts(case, children):
    """케이스와 부품·장비 목록을 한 번에 저장한다(목록은 통째로 바꾼다)."""
    parts, equipments = children
    with transaction.atomic():
        case.save()
        case.parts.all().delete()
        case.equipments.all().delete()
        for row in [*parts, *equipments]:
            row.case = case
        ServicePart.objects.bulk_create(parts)
        ServiceEquipment.objects.bulk_create(equipments)


def _write_guard(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    if not request.user.is_authenticated:
        return _error('로그인이 필요합니다.', status=401)
    return None


@require_POST
def service_create_api(request):
    guard = _write_guard(request)
    if guard:
        return guard
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')
    scope_users, _selected, scope_ids = _scope(request)
    case = ServiceCase(created_by=request.user)
    try:
        children = _apply_payload(case, payload, request, scope_ids, creating=True)
    except ValueError as exc:
        return _error(str(exc))
    _save_with_parts(case, children)
    case = _visible_case_or_404(request, scope_users, case.pk)
    return JsonResponse({
        'success': True,
        'item': case_detail_payload(case, request.user, scope_ids, _related_cases(request, scope_users, case)),
    }, status=201)


def _editable_case_or_error(request, case_id):
    scope_users, _selected, scope_ids = _scope(request)
    case = _visible_case_or_404(request, scope_users, case_id)
    if not can_edit_case(case, request.user, scope_ids):
        return None, _error('이 서비스 기록을 변경할 권한이 없습니다.', status=403), scope_users, scope_ids
    return case, None, scope_users, scope_ids


@require_POST
def service_update_api(request, case_id):
    guard = _write_guard(request)
    if guard:
        return guard
    case, error, scope_users, scope_ids = _editable_case_or_error(request, case_id)
    if error:
        return error
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')
    try:
        children = _apply_payload(case, payload, request, scope_ids, creating=False)
    except ValueError as exc:
        return _error(str(exc))
    _save_with_parts(case, children)
    case = _visible_case_or_404(request, scope_users, case.pk)
    return JsonResponse({
        'success': True,
        'item': case_detail_payload(case, request.user, scope_ids, _related_cases(request, scope_users, case)),
    })


@require_POST
def service_delete_api(request, case_id):
    guard = _write_guard(request)
    if guard:
        return guard
    case, error, _scope_users, _scope_ids = _editable_case_or_error(request, case_id)
    if error:
        return error
    case.delete()
    return JsonResponse({'success': True})
