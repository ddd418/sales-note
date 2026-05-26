"""Credit customer receivables APIs.

The system does not issue real tax invoices here. The existing tax-invoice flag is
used as an internal receivable marker for delivered items.
"""

import json
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from reporting.models import DeliveryItem, History, Schedule
from reporting.views import (
    _api_login_required_response,
    _date_or_none,
    _datetime_or_none,
    _money_int,
    _user_display_name,
    can_access_user_data,
    can_modify_user_data,
    get_accessible_users,
    get_user_profile,
)


RECEIVABLE_STATUSES = {'open', 'all', 'settled', 'unregistered', 'card'}
RECEIVABLE_SORTS = {'outstanding', 'customer', 'date', 'amount'}
RECEIVABLE_ORDERS = {'asc', 'desc'}


def _receivables_bool_payload(payload, *keys):
    for key in keys:
        if key in payload:
            value = payload.get(key)
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            return str(value).strip().lower() in {'1', 'true', 'on', 'yes', 'y'}
    return None


def _receivables_item_amount(item):
    if item.total_price is not None:
        return _money_int(item.total_price)
    try:
        unit_price = item.get_effective_unit_price()
        if unit_price is None:
            unit_price = item.unit_price or 0
        return _money_int(Decimal(str(unit_price)) * Decimal(str(item.quantity or 0)) * Decimal('1.1'))
    except Exception:
        return 0


def _receivables_item_context(item):
    schedule = item.schedule
    history = item.history
    followup = schedule.followup if schedule and schedule.followup_id else history.followup if history else None
    owner = schedule.user if schedule and schedule.user_id else history.user if history else None
    department = followup.department if followup and followup.department_id else None
    company = followup.company if followup and followup.company_id else department.company if department and department.company_id else None
    delivery_date = schedule.visit_date if schedule else history.delivery_date if history else None

    if department:
        account_key = f'department:{department.id}'
        account_id = department.id
        account_type = 'department'
        customer_label = department.name or ''
    elif followup:
        account_key = f'followup:{followup.id}'
        account_id = followup.id
        account_type = 'followup'
        customer_label = followup.customer_name or str(followup)
    else:
        account_key = f'item:{item.id}'
        account_id = None
        account_type = 'item'
        customer_label = '고객 미지정'

    company_name = company.name if company else ''
    department_name = department.name if department else ''
    customer_name = followup.customer_name or str(followup) if followup else ''
    account_label = ' / '.join(part for part in [company_name, department_name or customer_name] if part) or customer_label
    return {
        'schedule': schedule,
        'history': history,
        'followup': followup,
        'owner': owner,
        'delivery_date': delivery_date,
        'account_key': account_key,
        'account_id': account_id,
        'account_type': account_type,
        'account_label': account_label,
        'company_name': company_name,
        'department_name': department_name,
        'customer_name': customer_name,
    }


def _receivables_item_payment_schedule(item):
    if item.schedule_id:
        return item.schedule
    if item.history_id and getattr(item.history, 'schedule_id', None):
        return item.history.schedule
    return None


def _receivables_schedule_uses_prepayment(schedule):
    if not schedule:
        return False
    if (
        getattr(schedule, 'use_prepayment', False)
        or getattr(schedule, 'prepayment_id', None)
        or _money_int(getattr(schedule, 'prepayment_amount', None)) > 0
        or getattr(schedule, 'delivery_payment_type', '') == Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT
        or getattr(schedule, 'delivery_payment_status', '') == Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT
    ):
        return True
    return schedule.prepayment_usages.exists()


def _receivables_item_uses_prepayment(item):
    schedule = _receivables_item_payment_schedule(item)
    if _receivables_schedule_uses_prepayment(schedule):
        return True
    try:
        return item.prepaymentusage_set.exists()
    except Exception:
        return False


def _receivables_item_status_label(item):
    if item.card_payment_received:
        return '카드결제 완료'
    if item.receivable_settled:
        return '수금완료'
    if item.tax_invoice_issued:
        return '외상 진행중'
    return '미등록'


def _receivables_item_payload(item, request_user=None):
    context = _receivables_item_context(item)
    amount = _receivables_item_amount(item)
    outstanding_amount = amount if item.tax_invoice_issued and not item.receivable_settled and not item.card_payment_received else 0
    schedule = context['schedule']
    history = context['history']
    owner = context['owner']
    can_edit = bool(owner and request_user and can_modify_user_data(request_user, owner))
    return {
        'id': item.id,
        'itemName': item.item_name or '',
        'quantity': int(item.quantity or 0),
        'unit': item.unit or '',
        'unitPrice': _money_int(item.unit_price) if item.unit_price is not None else None,
        'totalPrice': amount,
        'outstandingAmount': outstanding_amount,
        'taxInvoiceIssued': bool(item.tax_invoice_issued),
        'cardPaymentReceived': bool(item.card_payment_received),
        'receivableSettled': bool(item.receivable_settled),
        'receivableSettledAt': _datetime_or_none(item.receivable_settled_at),
        'receivableSettledBy': _user_display_name(item.receivable_settled_by) if item.receivable_settled_by_id else '',
        'statusLabel': _receivables_item_status_label(item),
        'deliveryDate': _date_or_none(context['delivery_date']),
        'scheduleId': schedule.id if schedule else None,
        'scheduleHref': f'/schedules/{schedule.id}/' if schedule else '',
        'djangoScheduleHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        'historyId': history.id if history else None,
        'historyHref': f'/notes/{history.id}/' if history else '',
        'accountKey': context['account_key'],
        'accountId': context['account_id'],
        'accountType': context['account_type'],
        'accountLabel': context['account_label'],
        'companyName': context['company_name'],
        'departmentName': context['department_name'],
        'customerName': context['customer_name'],
        'ownerName': _user_display_name(owner) if owner else '',
        'canEdit': can_edit,
        'links': {
            'update': reverse('reporting:receivable_item_status_api', args=[item.id]) if can_edit else '',
            'schedule': f'/schedules/{schedule.id}/' if schedule else '',
            'history': f'/notes/{history.id}/' if history else '',
        },
    }


def _receivables_sync_history(item):
    schedule = item.schedule
    if not schedule:
        if item.history_id:
            item.history.tax_invoice_issued = bool(item.tax_invoice_issued)
            item.history.save(update_fields=['tax_invoice_issued'])
        return

    delivery_items = list(schedule.delivery_items_set.all())
    schedule_issued = bool(delivery_items) and all(delivery_item.tax_invoice_issued for delivery_item in delivery_items)
    History.objects.filter(schedule=schedule, action_type='delivery_schedule').update(tax_invoice_issued=schedule_issued)


def _receivables_scope_users(request):
    profile = get_user_profile(request.user)
    if profile.can_view_all_users():
        return get_accessible_users(request.user, request)
    return get_accessible_users(request.user, request).filter(id=request.user.id)


def _receivables_queryset(request):
    scope_users = _receivables_scope_users(request)
    prepayment_filter = (
        Q(schedule__use_prepayment=True)
        | Q(schedule__prepayment__isnull=False)
        | Q(schedule__prepayment_amount__gt=0)
        | Q(schedule__delivery_payment_type=Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT)
        | Q(schedule__delivery_payment_status=Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT)
        | Q(schedule__prepayment_usages__isnull=False)
        | Q(history__schedule__use_prepayment=True)
        | Q(history__schedule__prepayment__isnull=False)
        | Q(history__schedule__prepayment_amount__gt=0)
        | Q(history__schedule__delivery_payment_type=Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT)
        | Q(history__schedule__delivery_payment_status=Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT)
        | Q(history__schedule__prepayment_usages__isnull=False)
    )
    return (
        DeliveryItem.objects
        .select_related(
            'schedule',
            'schedule__user',
            'schedule__followup',
            'schedule__followup__company',
            'schedule__followup__department',
            'schedule__followup__department__company',
            'history',
            'history__schedule',
            'history__user',
            'history__followup',
            'history__followup__company',
            'history__followup__department',
            'history__followup__department__company',
            'receivable_settled_by',
        )
        .filter(
            Q(schedule__activity_type='delivery', schedule__user__in=scope_users)
            | Q(schedule__isnull=True, history__action_type='delivery_schedule', history__user__in=scope_users)
        )
        .exclude(prepayment_filter)
        .distinct()
    )


def _receivables_status_filter(queryset, status):
    if status == 'open':
        return queryset.filter(tax_invoice_issued=True, card_payment_received=False, receivable_settled=False)
    if status == 'settled':
        return queryset.filter(tax_invoice_issued=True).filter(Q(receivable_settled=True) | Q(card_payment_received=True))
    if status == 'unregistered':
        return queryset.filter(tax_invoice_issued=False, card_payment_received=False, receivable_settled=False)
    if status == 'card':
        return queryset.filter(card_payment_received=True)
    return queryset


def _receivables_apply_query_filter(items, query):
    if not query:
        return items
    normalized = query.lower()
    filtered = []
    for item in items:
        haystack = ' '.join([
            item.get('accountLabel') or '',
            item.get('companyName') or '',
            item.get('departmentName') or '',
            item.get('customerName') or '',
            item.get('itemName') or '',
            item.get('ownerName') or '',
        ]).lower()
        if normalized in haystack:
            filtered.append(item)
    return filtered


def _receivables_sort_items(items, sort_key, order):
    reverse_order = order == 'desc'

    def sort_value(item):
        if sort_key == 'customer':
            return item.get('accountLabel') or ''
        if sort_key == 'date':
            return item.get('deliveryDate') or ''
        if sort_key == 'amount':
            return item.get('totalPrice') or 0
        return item.get('outstandingAmount') or 0

    return sorted(items, key=sort_value, reverse=reverse_order)


def _receivables_customer_rows(items):
    customers = {}
    for item in items:
        key = item['accountKey']
        row = customers.setdefault(key, {
            'key': key,
            'id': item['accountId'],
            'type': item['accountType'],
            'label': item['accountLabel'],
            'companyName': item['companyName'],
            'departmentName': item['departmentName'],
            'customerName': item['customerName'],
            'ownerNames': [],
            'itemCount': 0,
            'openItemCount': 0,
            'settledItemCount': 0,
            'cardItemCount': 0,
            'totalAmount': 0,
            'outstandingAmount': 0,
            'lastDeliveryDate': '',
            'href': f"/customers/{item['accountId']}/" if item['accountType'] == 'followup' and item['accountId'] else '',
        })
        if item['ownerName'] and item['ownerName'] not in row['ownerNames']:
            row['ownerNames'].append(item['ownerName'])
        row['itemCount'] += 1
        row['totalAmount'] += item['totalPrice'] or 0
        row['outstandingAmount'] += item['outstandingAmount'] or 0
        if item['taxInvoiceIssued'] and not item['receivableSettled'] and not item['cardPaymentReceived']:
            row['openItemCount'] += 1
        if item['receivableSettled']:
            row['settledItemCount'] += 1
        if item['cardPaymentReceived']:
            row['cardItemCount'] += 1
        if item['deliveryDate'] and item['deliveryDate'] > row['lastDeliveryDate']:
            row['lastDeliveryDate'] = item['deliveryDate']
    return sorted(customers.values(), key=lambda row: row['outstandingAmount'], reverse=True)


@never_cache
@require_http_methods(["GET"])
def receivables_api(request):
    """List credit customers and delivery-item receivable status."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    status = (request.GET.get('status') or 'open').strip()
    if status not in RECEIVABLE_STATUSES:
        status = 'open'
    sort_key = (request.GET.get('sort') or 'outstanding').strip()
    if sort_key not in RECEIVABLE_SORTS:
        sort_key = 'outstanding'
    order = (request.GET.get('order') or 'desc').strip()
    if order not in RECEIVABLE_ORDERS:
        order = 'desc'
    query = (request.GET.get('q') or request.GET.get('query') or '').strip()

    queryset = _receivables_status_filter(_receivables_queryset(request), status).order_by('-created_at')
    item_payloads = [_receivables_item_payload(item, request.user) for item in queryset[:1000]]
    item_payloads = _receivables_apply_query_filter(item_payloads, query)
    item_payloads = _receivables_sort_items(item_payloads, sort_key, order)
    customer_rows = _receivables_customer_rows(item_payloads)

    total_outstanding = sum(item['outstandingAmount'] or 0 for item in item_payloads)
    total_credit_amount = sum(item['totalPrice'] or 0 for item in item_payloads if item['taxInvoiceIssued'])
    settled_amount = sum(item['totalPrice'] or 0 for item in item_payloads if item['receivableSettled'] or item['cardPaymentReceived'])

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'summary': {
            'totalOutstanding': total_outstanding,
            'totalCreditAmount': total_credit_amount,
            'settledAmount': settled_amount,
            'customerCount': len([row for row in customer_rows if row['outstandingAmount'] > 0]),
            'itemCount': len(item_payloads),
            'openItemCount': len([
                item for item in item_payloads
                if item['taxInvoiceIssued'] and not item['receivableSettled'] and not item['cardPaymentReceived']
            ]),
        },
        'filters': {
            'status': status,
            'query': query,
            'sort': sort_key,
            'order': order,
            'statuses': [
                {'value': 'open', 'label': '외상 진행중'},
                {'value': 'all', 'label': '외상 관리 대상 전체'},
                {'value': 'unregistered', 'label': '미등록'},
                {'value': 'settled', 'label': '수금완료'},
                {'value': 'card', 'label': '카드결제'},
            ],
            'sorts': [
                {'value': 'outstanding', 'label': '외상금액'},
                {'value': 'customer', 'label': '고객명'},
                {'value': 'date', 'label': '납품일'},
                {'value': 'amount', 'label': '품목금액'},
            ],
        },
        'customers': customer_rows,
        'items': item_payloads,
        'links': {
            'self': reverse('reporting:receivables_api'),
        },
    }, encoder=DjangoJSONEncoder)


@never_cache
@require_http_methods(["POST"])
def receivable_item_status_api(request, item_id):
    """Update one delivered item's internal receivable status."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'success': False, 'error': '잘못된 요청 형식입니다.'}, status=400)

    with transaction.atomic():
        item = (
            DeliveryItem.objects
            .select_for_update()
            .filter(id=item_id)
            .first()
        )
        if not item:
            return JsonResponse({'success': False, 'error': '납품 품목을 찾을 수 없습니다.'}, status=404)

        owner = item.schedule.user if item.schedule_id else item.history.user if item.history_id else None
        if not owner or not can_access_user_data(request.user, owner):
            return JsonResponse({'success': False, 'error': '접근 권한이 없습니다.'}, status=403)
        if not can_modify_user_data(request.user, owner):
            return JsonResponse({'success': False, 'error': '외상 상태를 변경할 권한이 없습니다.'}, status=403)
        if _receivables_item_uses_prepayment(item):
            return JsonResponse({
                'success': False,
                'error': '선결제 차감 납품은 외상고객에서 처리할 수 없습니다.',
                'message': '선결제 사용 내역은 선결제 메뉴에서 확인하세요.',
                'redirect': '/prepayments/',
            }, status=409)

        tax_value = _receivables_bool_payload(payload, 'taxInvoiceIssued', 'tax_invoice_issued')
        card_value = _receivables_bool_payload(payload, 'cardPaymentReceived', 'card_payment_received')
        settled_value = _receivables_bool_payload(payload, 'receivableSettled', 'receivable_settled')

        if tax_value is not None:
            item.tax_invoice_issued = tax_value
            if not tax_value:
                item.card_payment_received = False
                item.receivable_settled = False
                item.receivable_settled_at = None
                item.receivable_settled_by = None

        if card_value is not None:
            item.card_payment_received = card_value
            if card_value:
                item.tax_invoice_issued = True
                item.receivable_settled = True
                item.receivable_settled_at = timezone.now()
                item.receivable_settled_by = request.user
            elif settled_value is None:
                item.receivable_settled = False
                item.receivable_settled_at = None
                item.receivable_settled_by = None

        if settled_value is not None:
            item.receivable_settled = settled_value
            if settled_value:
                item.tax_invoice_issued = True
                item.receivable_settled_at = timezone.now()
                item.receivable_settled_by = request.user
            else:
                item.card_payment_received = False
                item.receivable_settled_at = None
                item.receivable_settled_by = None

        if item.card_payment_received and not item.receivable_settled:
            item.receivable_settled = True
            item.receivable_settled_at = item.receivable_settled_at or timezone.now()
            item.receivable_settled_by = item.receivable_settled_by or request.user

        item.save(update_fields=[
            'tax_invoice_issued',
            'card_payment_received',
            'receivable_settled',
            'receivable_settled_at',
            'receivable_settled_by',
            'updated_at',
        ])
        _receivables_sync_history(item)
        item = _receivables_queryset(request).get(id=item.id)

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'message': '외상 상태를 저장했습니다.',
        'item': _receivables_item_payload(item, request.user),
    }, encoder=DjangoJSONEncoder)
