"""Shared account-ledger helpers for department/lab based CRM views."""

from decimal import Decimal, InvalidOperation

from django.db.models import Count, Prefetch, Q, QuerySet
from django.urls import reverse
from django.utils import timezone

from .models import FollowUp, History, Prepayment, PrepaymentUsage, Quote, Schedule


DELIVERY_PAYMENT_NORMAL = Schedule.DELIVERY_PAYMENT_TYPE_NORMAL
DELIVERY_PAYMENT_PREPAYMENT = Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT
DELIVERY_PAYMENT_STATUS_NORMAL = Schedule.DELIVERY_PAYMENT_STATUS_NORMAL
DELIVERY_PAYMENT_STATUS_PREPAYMENT = Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT
DELIVERY_PAYMENT_STATUS_NEEDS_REVIEW = Schedule.DELIVERY_PAYMENT_STATUS_NEEDS_REVIEW
DELIVERY_PAYMENT_STATUS_SETTLED = Schedule.DELIVERY_PAYMENT_STATUS_SETTLED
DELIVERY_PAYMENT_STATUS_CANCELLED_RETURNED = Schedule.DELIVERY_PAYMENT_STATUS_CANCELLED_RETURNED


DELIVERY_PAYMENT_STATUS_LABELS = dict(Schedule.DELIVERY_PAYMENT_STATUS_CHOICES)
DELIVERY_PAYMENT_STATUS_AUTO_VALUES = {
    DELIVERY_PAYMENT_STATUS_NORMAL,
    DELIVERY_PAYMENT_STATUS_PREPAYMENT,
}


def money_int(value) -> int:
    if value in (None, ''):
        return 0
    try:
        return int(Decimal(str(value)).quantize(Decimal('1')))
    except (InvalidOperation, ValueError, TypeError):
        return 0


def date_or_none(value):
    if isinstance(value, str):
        return value or None
    return value.isoformat() if value else None


def datetime_or_none(value):
    return timezone.localtime(value).isoformat() if value else None


def user_display_name(user) -> str:
    if not user:
        return ''
    return user.get_full_name() or user.username


def account_key_for_followup(followup) -> str:
    return f'department:{followup.department_id}' if followup and followup.department_id else f'followup:{followup.id}'


def prepayment_account_department(prepayment):
    customer = getattr(prepayment, 'customer', None)
    if getattr(prepayment, 'department_id', None):
        return prepayment.department
    if customer and customer.department_id:
        return customer.department
    return None


def prepayment_account_company(prepayment):
    department = prepayment_account_department(prepayment)
    customer = getattr(prepayment, 'customer', None)
    if getattr(prepayment, 'company_id', None):
        return prepayment.company
    if department and department.company_id:
        return department.company
    if customer and customer.company_id:
        return customer.company
    return None


def prepayment_account_filter(department=None, followup=None, followup_ids=None):
    if department is not None:
        return Q(department=department) | Q(
            department__isnull=True,
            customer__department=department,
        )
    if followup is not None:
        return Q(customer=followup)
    followup_ids = [item for item in (followup_ids or []) if item]
    return Q(customer_id__in=followup_ids)


def account_followups_for_followup(followup) -> QuerySet:
    """Return the department/lab account members for a FollowUp compatibility route."""
    if followup and followup.department_id:
        return FollowUp.objects.filter(department_id=followup.department_id)
    return FollowUp.objects.filter(pk=followup.pk)


def account_followups_for_department(department) -> QuerySet:
    return FollowUp.objects.filter(department=department)


def account_representative_followup(department, scope_users):
    return (
        account_followups_for_department(department)
        .filter(user__in=scope_users)
        .select_related('user', 'company', 'department')
        .order_by('-is_active', '-updated_at', '-created_at', '-id')
        .first()
    )


def _quote_group_label(value):
    return str(value or '').strip()[:100] or '기본 견적서'


def _product_label(product, fallback_name=''):
    if not product:
        return str(fallback_name or '').strip()
    code = str(product.product_code or '').strip()
    details = [
        str(value or '').strip()
        for value in [
            product.description,
            product.specification,
            f'단위 {product.unit}' if product.unit else '',
        ]
        if str(value or '').strip()
    ]
    if not code:
        return str(fallback_name or '').strip()
    return f"{code} ({', '.join(details[:3])})" if details else code


def _delivery_item_discount_unit_price_or_none(item):
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


def delivery_item_payload(item):
    product = item.product if item.product_id else None
    effective_unit_price = item.get_effective_unit_price()
    discount_unit_price = _delivery_item_discount_unit_price_or_none(item)
    return {
        'id': item.id,
        'productId': item.product_id,
        'productCode': product.product_code if product else '',
        'productDescription': (product.description or '') if product else '',
        'productSpecification': (product.specification or '') if product else '',
        'productUnit': (product.unit or '') if product else item.unit or '',
        'productLabel': _product_label(product, item.item_name),
        'itemName': item.item_name,
        'quantity': item.quantity,
        'unit': item.unit or '',
        'unitPrice': money_int(item.unit_price) if item.unit_price is not None else None,
        'discountRate': float(item.discount_rate or 0),
        'discountUnitPrice': money_int(discount_unit_price) if discount_unit_price is not None else None,
        'effectiveUnitPrice': money_int(effective_unit_price) if effective_unit_price is not None else None,
        'totalPrice': money_int(item.total_price),
        'taxInvoiceIssued': bool(item.tax_invoice_issued),
        'quoteGroup': item.quote_group or '',
        'quoteGroupLabel': _quote_group_label(item.quote_group),
        'notes': item.notes or '',
        'optionDescription': item.option_description or '',
        'sourceQuoteScheduleId': item.source_quote_schedule_id,
        'sourceQuoteItemId': item.source_quote_item_id,
    }


def prepayment_usage_payload(usage):
    prepayment = usage.prepayment
    customer = prepayment.customer if prepayment and prepayment.customer_id else None
    return {
        'id': usage.id,
        'prepaymentId': usage.prepayment_id,
        'paymentDate': date_or_none(prepayment.payment_date) if prepayment else None,
        'payerName': prepayment.payer_name or '미지정' if prepayment else '미지정',
        'customerName': customer.customer_name or str(customer) if customer else '',
        'productName': usage.product_name or '',
        'quantity': usage.quantity or 1,
        'amount': money_int(usage.amount),
        'remainingBalance': money_int(usage.remaining_balance),
        'usedAt': datetime_or_none(usage.used_at),
        'memo': usage.memo or '',
    }


def schedule_items(schedule, history_action_type='delivery_schedule'):
    items = list(schedule.delivery_items_set.all().order_by('id'))
    if items:
        return items

    prefetched_histories = getattr(schedule, '_account_ledger_histories', None)
    if prefetched_histories is None:
        prefetched_histories = list(
            History.objects.filter(
                schedule=schedule,
                action_type=history_action_type,
                parent_history__isnull=True,
            ).prefetch_related('delivery_items_set').order_by('-created_at')
        )
    for history in prefetched_histories:
        history_items = list(history.delivery_items_set.all().order_by('id'))
        if history_items:
            return history_items
    return []


def schedule_items_total(items) -> int:
    total_amount = Decimal('0')
    for item in items:
        item_total = item.total_price
        if item_total is None and item.unit_price is not None:
            item_total = (item.get_effective_unit_price() or item.unit_price) * item.quantity * Decimal('1.1')
        if item_total is not None:
            total_amount += item_total
    return money_int(total_amount)


def schedule_fallback_history_amount(schedule, history_action_type='delivery_schedule') -> int:
    prefetched_histories = getattr(schedule, '_account_ledger_histories', None)
    if prefetched_histories is None:
        prefetched_histories = History.objects.filter(
            schedule=schedule,
            action_type=history_action_type,
            parent_history__isnull=True,
        ).order_by('-created_at')
    for history in prefetched_histories:
        amount = money_int(getattr(history, 'delivery_amount', 0))
        if amount:
            return amount
    return 0


def delivery_payment_record_payload(schedule):
    payload = delivery_payment_payload(schedule)
    return {
        'paymentSource': payload['paymentSource'],
        'paymentSourceLabel': payload['paymentSourceLabel'],
        'paymentType': payload['paymentType'],
        'paymentTypeLabel': payload['paymentTypeLabel'],
        'paymentStatus': payload['paymentStatus'],
        'paymentStatusLabel': payload['paymentStatusLabel'],
        'paymentStatusEvidence': payload['paymentStatusEvidence'],
        'prepaymentId': payload['prepaymentId'],
        'prepaymentAmount': payload['prepaymentAmount'],
        'prepaymentUsages': [
            prepayment_usage_payload(usage)
            for usage in payload['usages']
        ],
        'paymentEvidence': payload['paymentEvidence'],
    }


def delivery_record_payload(schedule):
    items = schedule_items(schedule, 'delivery_schedule')
    total_amount = schedule_items_total(items)
    if total_amount <= 0:
        total_amount = schedule_fallback_history_amount(schedule, 'delivery_schedule')
    payment_payload = delivery_payment_record_payload(schedule)
    return {
        'id': schedule.id,
        'recordType': 'delivery_schedule',
        'date': date_or_none(schedule.visit_date),
        'time': schedule.visit_time.isoformat(timespec='minutes') if schedule.visit_time else None,
        'customerName': schedule.followup.customer_name or schedule.followup.manager or '',
        'companyName': schedule.followup.company.name if schedule.followup and schedule.followup.company else '',
        'departmentName': schedule.followup.department.name if schedule.followup and schedule.followup.department else '',
        'ownerName': user_display_name(schedule.user),
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'activityLabel': schedule.get_activity_type_display(),
        'items': [delivery_item_payload(item) for item in items],
        'itemCount': len(items),
        'totalAmount': total_amount,
        'amount': total_amount,
        'notes': schedule.notes or '',
        'source': '납품 일정',
        'ledgerSource': 'common_account_ledger',
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
        'schedule_id': schedule.id,
        **payment_payload,
    }


def quote_item_payload(item):
    product = item.product if item.product_id else None
    return {
        'id': item.id,
        'productId': item.product_id,
        'productCode': product.product_code if product else '',
        'productDescription': (product.description or '') if product else '',
        'productSpecification': (product.specification or '') if product else '',
        'productUnit': (product.unit or '') if product else '',
        'productLabel': _product_label(product, product.product_code if product else ''),
        'itemName': product.product_code if product else '제품명 없음',
        'quantity': item.quantity,
        'unit': product.unit if product else '',
        'unitPrice': money_int(item.unit_price),
        'discountRate': float(item.discount_rate or 0),
        'discountUnitPrice': None,
        'effectiveUnitPrice': money_int(item.unit_price),
        'totalPrice': money_int(item.subtotal),
        'taxInvoiceIssued': False,
        'quoteGroup': '',
        'quoteGroupLabel': _quote_group_label(''),
        'notes': item.description or '',
        'optionDescription': item.description or '',
        'sourceQuoteScheduleId': None,
        'sourceQuoteItemId': None,
    }


def quote_record_payload(quote):
    items = [quote_item_payload(item) for item in quote.items.all().order_by('order', 'id')]
    total_amount = money_int(quote.total_amount) or sum(item['totalPrice'] for item in items)
    schedule = quote.schedule
    return {
        'id': quote.id,
        'recordType': 'quote',
        'scheduleId': schedule.id if schedule else None,
        'quoteNumber': quote.quote_number,
        'date': date_or_none(quote.quote_date or (schedule.visit_date if schedule else None)),
        'validUntil': date_or_none(quote.valid_until),
        'customerName': quote.followup.customer_name or quote.followup.manager or '',
        'companyName': quote.followup.company.name if quote.followup and quote.followup.company else '',
        'departmentName': quote.followup.department.name if quote.followup and quote.followup.department else '',
        'ownerName': user_display_name(quote.user),
        'status': quote.stage,
        'statusLabel': quote.get_stage_display(),
        'stage': quote.get_stage_display(),
        'items': items,
        'itemCount': len(items),
        'totalAmount': total_amount,
        'total_amount': total_amount,
        'converted_to_delivery': bool(quote.converted_to_delivery),
        'notes': quote.notes or quote.customer_feedback or '',
        'source': '견적서',
        'ledgerSource': 'common_account_ledger',
        'href': f'/schedules/{schedule.id}/' if schedule else '',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
    }


def quote_schedule_record_payload(schedule):
    items = schedule_items(schedule, 'quote')
    total_amount = schedule_items_total(items)
    if total_amount <= 0 and schedule.expected_revenue:
        total_amount = money_int(schedule.expected_revenue)
    return {
        'id': schedule.id,
        'recordType': 'quote_schedule',
        'scheduleId': schedule.id,
        'quoteNumber': '',
        'date': date_or_none(schedule.visit_date),
        'validUntil': None,
        'customerName': schedule.followup.customer_name or schedule.followup.manager or '',
        'companyName': schedule.followup.company.name if schedule.followup and schedule.followup.company else '',
        'departmentName': schedule.followup.department.name if schedule.followup and schedule.followup.department else '',
        'ownerName': user_display_name(schedule.user),
        'status': schedule.status,
        'statusLabel': schedule.get_status_display(),
        'stage': schedule.get_status_display(),
        'items': [delivery_item_payload(item) for item in items],
        'itemCount': len(items),
        'totalAmount': total_amount,
        'total_amount': total_amount,
        'converted_to_delivery': bool(schedule.purchase_confirmed),
        'notes': schedule.notes or schedule.quote_extra_notes or '',
        'source': '견적 일정',
        'ledgerSource': 'common_account_ledger',
        'href': f'/schedules/{schedule.id}/',
        'djangoHref': reverse('reporting:schedule_detail', args=[schedule.id]),
    }


def prepayment_item_payload(prepayment, actor=None):
    customer = prepayment.customer
    company = prepayment_account_company(prepayment)
    department = prepayment_account_department(prepayment)
    owner = prepayment.created_by
    amount = money_int(prepayment.amount)
    balance = money_int(prepayment.balance)
    used_amount = max(amount - balance, 0)
    owner_id_matches = bool(actor and prepayment.created_by_id == actor.id)
    try:
        actor_is_manager = bool(actor and actor.userprofile.role == 'manager')
    except Exception:
        actor_is_manager = False
    can_manage = owner_id_matches and not actor_is_manager
    usage_count = getattr(prepayment, 'usage_count', None)
    if usage_count is None:
        usage_count = prepayment.usages.count()

    return {
        'id': prepayment.id,
        'customerId': customer.id if customer else None,
        'customerName': customer.customer_name if customer else '',
        'companyId': company.id if company else None,
        'companyName': company.name if company else '',
        'departmentId': department.id if department else None,
        'departmentName': department.name if department else '',
        'payerName': prepayment.payer_name or '',
        'paymentDate': date_or_none(prepayment.payment_date),
        'paymentMethod': prepayment.payment_method,
        'paymentMethodLabel': prepayment.get_payment_method_display(),
        'amount': amount,
        'balance': balance,
        'usedAmount': used_amount,
        'usageCount': usage_count,
        'status': prepayment.status,
        'statusLabel': prepayment.get_status_display(),
        'ownerId': prepayment.created_by_id,
        'ownerName': user_display_name(owner),
        'memo': (prepayment.memo or '')[:220],
        'createdAt': datetime_or_none(prepayment.created_at),
        'cancelledAt': datetime_or_none(prepayment.cancelled_at),
        'cancelReason': (prepayment.cancel_reason or '')[:220],
        'canManage': can_manage,
        'href': reverse('reporting:prepayment_detail', args=[prepayment.id]),
        'editHref': reverse('reporting:prepayment_edit', args=[prepayment.id]) if can_manage else '',
        'deleteHref': reverse('reporting:prepayment_delete', args=[prepayment.id]) if can_manage else '',
        'transferHref': reverse('reporting:prepayment_transfer', args=[prepayment.id]) if can_manage else '',
        'customerHref': f'/customers/{customer.id}/' if customer else '',
        'djangoCustomerHref': reverse('reporting:followup_detail', args=[customer.id]) if customer else '',
        'customerPrepaymentHref': (
            f'/prepayments/account/{department.id}/'
            if department else f'/prepayments/customer/{customer.id}/' if customer else ''
        ),
        'djangoCustomerPrepaymentHref': reverse('reporting:prepayment_customer', args=[customer.id]) if customer else '',
    }


def prepayment_usage_drilldown_payload(usage):
    prepayment = usage.prepayment
    customer = prepayment.customer if prepayment and prepayment.customer_id else None
    department = prepayment_account_department(prepayment) if prepayment else None
    schedule = usage.schedule
    delivery_items = []
    if schedule:
        delivery_items = [
            {
                'id': item.id,
                'itemName': item.item_name,
                'quantity': item.quantity,
                'unit': item.unit or '',
                'unitPrice': money_int(item.unit_price),
                'totalPrice': money_int(item.total_price),
            }
            for item in schedule.delivery_items_set.all().order_by('id')
        ]

    return {
        'id': usage.id,
        'prepaymentId': usage.prepayment_id,
        'paymentDate': date_or_none(prepayment.payment_date) if prepayment else None,
        'payerName': prepayment.payer_name or '미지정' if prepayment else '미지정',
        'customerId': customer.id if customer else None,
        'customerName': customer.customer_name if customer else '',
        'departmentId': department.id if department else None,
        'departmentName': department.name if department else '',
        'usedAt': datetime_or_none(usage.used_at),
        'productName': usage.product_name or '',
        'quantity': int(usage.quantity or 0),
        'amount': money_int(usage.amount),
        'remainingBalance': money_int(usage.remaining_balance),
        'memo': usage.memo or '',
        'scheduleId': schedule.id if schedule else None,
        'scheduleDate': date_or_none(schedule.visit_date) if schedule else None,
        'scheduleHref': f'/schedules/{schedule.id}/' if schedule else '',
        'djangoScheduleHref': reverse('reporting:schedule_detail', args=[schedule.id]) if schedule else '',
        'deliveryItems': delivery_items,
    }


def _empty_account_ledger():
    return {
        'metrics': {
            'deliveryRecords': 0,
            'deliveryCount': 0,
            'deliveryAmount': 0,
            'normalDeliveryRecords': 0,
            'normalDeliveryCount': 0,
            'normalDeliveryAmount': 0,
            'prepaymentDeliveryRecords': 0,
            'prepaymentDeliveryCount': 0,
            'prepaymentDeliveryAmount': 0,
            'prepaymentUsedAmount': 0,
            'quoteRecords': 0,
            'quoteCount': 0,
            'quoteAmount': 0,
            'quoteItemCount': 0,
            'prepaymentRecords': 0,
            'prepaymentCount': 0,
            'prepaymentAmount': 0,
            'prepaymentBalance': 0,
            'prepaymentUsedTotal': 0,
            'prepaymentUsageRecords': 0,
            'prepaymentUsageCount': 0,
            'prepaymentUsageAmount': 0,
            'lastDeliveryDate': None,
            'lastQuoteDate': None,
            'lastPrepaymentDate': None,
            'lastActivityDate': None,
        },
        'deliveryRecords': [],
        'quoteRecords': [],
        'prepaymentRecords': [],
        'prepaymentUsageRecords': [],
    }


def _update_latest(metrics, field, value):
    candidate = date_or_none(value)
    if candidate and (not metrics.get(field) or candidate > metrics[field]):
        metrics[field] = candidate
    if candidate and (not metrics.get('lastActivityDate') or candidate > metrics['lastActivityDate']):
        metrics['lastActivityDate'] = candidate


def _append_limited(rows, record, limit):
    if limit is None or len(rows) < limit:
        rows.append(record)


def _date_filter_kwargs(field_name, date_from=None, date_to=None):
    filters = {}
    if date_from:
        filters[f'{field_name}__gte'] = date_from
    if date_to:
        filters[f'{field_name}__lte'] = date_to
    return filters


def account_operational_ledgers_for_followups(
    followups,
    scope_users,
    *,
    date_from=None,
    date_to=None,
    actor=None,
    record_limit=50,
):
    """Build shared delivery/quote/prepayment ledgers keyed by department account."""
    followups = list(followups)
    followup_ids = [followup.id for followup in followups]
    account_key_by_followup_id = {
        followup.id: account_key_for_followup(followup)
        for followup in followups
    }
    ledgers = {
        account_key_for_followup(followup): _empty_account_ledger()
        for followup in followups
    }
    if not followup_ids:
        return ledgers

    service_history_prefetch = Prefetch(
        'histories',
        queryset=History.objects.filter(
            parent_history__isnull=True,
        ).prefetch_related('delivery_items_set').order_by('-created_at'),
        to_attr='_account_ledger_histories',
    )

    delivery_schedules = list(
        Schedule.objects.filter(
            followup_id__in=followup_ids,
            user__in=scope_users,
            activity_type='delivery',
            **_date_filter_kwargs('visit_date', date_from, date_to),
        ).exclude(status='cancelled').select_related(
            'user', 'followup', 'followup__company', 'followup__department', 'prepayment',
        ).prefetch_related(
            'delivery_items_set__product',
            service_history_prefetch,
            Prefetch(
                'prepayment_usages',
                queryset=PrepaymentUsage.objects.select_related(
                    'prepayment', 'prepayment__customer',
                ).order_by('id'),
            ),
        ).order_by('-visit_date', '-visit_time', '-id')
    )
    for schedule in delivery_schedules:
        ledger = ledgers.get(account_key_by_followup_id.get(schedule.followup_id))
        if not ledger:
            continue
        record = delivery_record_payload(schedule)
        metrics = ledger['metrics']
        total_amount = record.get('totalAmount') or 0
        metrics['deliveryRecords'] += 1
        metrics['deliveryCount'] += 1
        metrics['deliveryAmount'] += total_amount
        _update_latest(metrics, 'lastDeliveryDate', schedule.visit_date)
        if record.get('paymentSource') == 'prepayment':
            metrics['prepaymentDeliveryRecords'] += 1
            metrics['prepaymentDeliveryCount'] += 1
            metrics['prepaymentDeliveryAmount'] += total_amount
            metrics['prepaymentUsedAmount'] += record.get('prepaymentAmount') or 0
        else:
            metrics['normalDeliveryRecords'] += 1
            metrics['normalDeliveryCount'] += 1
            metrics['normalDeliveryAmount'] += total_amount
        _append_limited(ledger['deliveryRecords'], record, record_limit)

    quote_schedules_by_id = set()
    quote_records = list(
        Quote.objects.filter(
            followup_id__in=followup_ids,
            user__in=scope_users,
            **_date_filter_kwargs('quote_date', date_from, date_to),
        ).select_related(
            'schedule', 'followup', 'followup__company', 'followup__department', 'user',
        ).prefetch_related('items__product').order_by('-quote_date', '-created_at', '-id')
    )
    for quote in quote_records:
        ledger = ledgers.get(account_key_by_followup_id.get(quote.followup_id))
        if not ledger:
            continue
        if quote.schedule_id:
            quote_schedules_by_id.add(quote.schedule_id)
        record = quote_record_payload(quote)
        metrics = ledger['metrics']
        metrics['quoteRecords'] += 1
        metrics['quoteCount'] += 1
        metrics['quoteAmount'] += record.get('totalAmount') or 0
        metrics['quoteItemCount'] += record.get('itemCount') or 0
        _update_latest(metrics, 'lastQuoteDate', quote.quote_date)
        _append_limited(ledger['quoteRecords'], record, record_limit)

    quote_schedules = list(
        Schedule.objects.filter(
            followup_id__in=followup_ids,
            user__in=scope_users,
            activity_type='quote',
            **_date_filter_kwargs('visit_date', date_from, date_to),
        ).exclude(
            id__in=quote_schedules_by_id,
        ).select_related(
            'user', 'followup', 'followup__company', 'followup__department',
        ).prefetch_related(
            'delivery_items_set__product',
            service_history_prefetch,
        ).order_by('-visit_date', '-visit_time', '-id')
    )
    for schedule in quote_schedules:
        ledger = ledgers.get(account_key_by_followup_id.get(schedule.followup_id))
        if not ledger:
            continue
        record = quote_schedule_record_payload(schedule)
        metrics = ledger['metrics']
        metrics['quoteRecords'] += 1
        metrics['quoteCount'] += 1
        metrics['quoteAmount'] += record.get('totalAmount') or 0
        metrics['quoteItemCount'] += record.get('itemCount') or 0
        _update_latest(metrics, 'lastQuoteDate', schedule.visit_date)
        _append_limited(ledger['quoteRecords'], record, record_limit)

    department_ids = [followup.department_id for followup in followups if followup.department_id]
    prepayments = list(
        Prepayment.objects.filter(
            created_by__in=scope_users,
        ).filter(
            Q(customer_id__in=followup_ids) | Q(department_id__in=department_ids)
        ).select_related(
            'department', 'department__company', 'company',
            'customer', 'customer__company', 'customer__department', 'created_by',
        ).annotate(
            usage_count=Count('usages', distinct=True),
        ).distinct().order_by('-payment_date', '-created_at', '-id')
    )
    for prepayment in prepayments:
        account_key = (
            f'department:{prepayment.department_id}'
            if prepayment.department_id else account_key_by_followup_id.get(prepayment.customer_id)
        )
        ledger = ledgers.get(account_key)
        if not ledger:
            continue
        record = prepayment_item_payload(prepayment, actor or prepayment.created_by)
        metrics = ledger['metrics']
        metrics['prepaymentRecords'] += 1
        metrics['prepaymentCount'] += 1
        metrics['prepaymentAmount'] += record.get('amount') or 0
        metrics['prepaymentBalance'] += record.get('balance') or 0
        metrics['prepaymentUsedTotal'] += record.get('usedAmount') or 0
        _update_latest(metrics, 'lastPrepaymentDate', prepayment.payment_date)
        _append_limited(ledger['prepaymentRecords'], record, record_limit)

    usages = list(
        PrepaymentUsage.objects.filter(
            Q(prepayment__department_id__in=department_ids) |
            Q(prepayment__department__isnull=True, prepayment__customer_id__in=followup_ids),
            prepayment__created_by__in=scope_users,
        ).select_related(
            'prepayment', 'prepayment__customer', 'prepayment__department', 'schedule',
        ).prefetch_related('schedule__delivery_items_set').order_by('-used_at', '-id')
    )
    for usage in usages:
        prepayment = usage.prepayment
        account_key = (
            f'department:{prepayment.department_id}'
            if prepayment and prepayment.department_id else account_key_by_followup_id.get(prepayment.customer_id if prepayment else None)
        )
        ledger = ledgers.get(account_key)
        if not ledger:
            continue
        record = prepayment_usage_drilldown_payload(usage)
        metrics = ledger['metrics']
        metrics['prepaymentUsageRecords'] += 1
        metrics['prepaymentUsageCount'] += 1
        metrics['prepaymentUsageAmount'] += record.get('amount') or 0
        _append_limited(ledger['prepaymentUsageRecords'], record, record_limit)

    return ledgers


def account_operational_ledger_for_followups(
    followups,
    scope_users,
    *,
    date_from=None,
    date_to=None,
    actor=None,
    record_limit=50,
):
    """Return one combined ledger for a department account or a supplied followup set."""
    ledgers = account_operational_ledgers_for_followups(
        followups,
        scope_users,
        date_from=date_from,
        date_to=date_to,
        actor=actor,
        record_limit=record_limit,
    )
    combined = _empty_account_ledger()
    for ledger in ledgers.values():
        for key, value in ledger['metrics'].items():
            if isinstance(value, int):
                combined['metrics'][key] += value
            elif value and key.startswith('last'):
                _update_latest(combined['metrics'], key, value)
        for section in ['deliveryRecords', 'quoteRecords', 'prepaymentRecords', 'prepaymentUsageRecords']:
            combined[section].extend(ledger.get(section) or [])
    combined['deliveryRecords'].sort(key=lambda row: (row.get('date') or '', row.get('id') or 0), reverse=True)
    combined['quoteRecords'].sort(key=lambda row: (row.get('date') or '', row.get('id') or 0), reverse=True)
    combined['prepaymentRecords'].sort(key=lambda row: (row.get('paymentDate') or '', row.get('id') or 0), reverse=True)
    combined['prepaymentUsageRecords'].sort(key=lambda row: (row.get('usedAt') or '', row.get('id') or 0), reverse=True)
    if record_limit is not None:
        for section in ['deliveryRecords', 'quoteRecords', 'prepaymentRecords', 'prepaymentUsageRecords']:
            combined[section] = combined[section][:record_limit]
    return combined


def structured_prepayment_usage(schedule, usages=None) -> dict:
    if usages is None:
        usages = list(schedule.prepayment_usages.all().order_by('id'))
    else:
        usages = list(usages)
    usage_total = sum(money_int(usage.amount) for usage in usages)
    direct_amount = money_int(getattr(schedule, 'prepayment_amount', None))
    prepayment_id = getattr(schedule, 'prepayment_id', None) or (usages[0].prepayment_id if usages else None)
    uses_prepayment = bool(
        getattr(schedule, 'use_prepayment', False)
        or prepayment_id
        or direct_amount > 0
        or usage_total > 0
    )
    evidence_parts = []
    if uses_prepayment and getattr(schedule, 'delivery_payment_type', '') == DELIVERY_PAYMENT_PREPAYMENT:
        evidence_parts.append('Schedule.delivery_payment_type=prepayment_deduction')
    if getattr(schedule, 'use_prepayment', False):
        evidence_parts.append('Schedule.use_prepayment=True')
    if prepayment_id:
        evidence_parts.append(f'Schedule.prepayment_id={prepayment_id}')
    if direct_amount > 0:
        evidence_parts.append(f'Schedule.prepayment_amount={direct_amount:,}원')
    if usage_total > 0:
        evidence_parts.append(f'PrepaymentUsage 합계={usage_total:,}원')
    return {
        'usages': usages,
        'usage_total': usage_total,
        'direct_amount': direct_amount,
        'prepayment_id': prepayment_id,
        'prepayment_amount': usage_total or direct_amount,
        'uses_prepayment': uses_prepayment,
        'evidence_parts': evidence_parts,
    }


def infer_delivery_payment_type(schedule, usages=None) -> str:
    if structured_prepayment_usage(schedule, usages).get('uses_prepayment'):
        return DELIVERY_PAYMENT_PREPAYMENT
    return DELIVERY_PAYMENT_NORMAL


def infer_delivery_payment_status(schedule, usages=None) -> str:
    if getattr(schedule, 'activity_type', '') == 'delivery' and getattr(schedule, 'status', '') == 'cancelled':
        return DELIVERY_PAYMENT_STATUS_CANCELLED_RETURNED
    usage_info = structured_prepayment_usage(schedule, usages)
    if usage_info.get('uses_prepayment') or getattr(schedule, 'delivery_payment_type', '') == DELIVERY_PAYMENT_PREPAYMENT:
        return DELIVERY_PAYMENT_STATUS_PREPAYMENT
    return DELIVERY_PAYMENT_STATUS_NORMAL


def delivery_payment_status_label(status) -> str:
    return DELIVERY_PAYMENT_STATUS_LABELS.get(status) or DELIVERY_PAYMENT_STATUS_LABELS[DELIVERY_PAYMENT_STATUS_NORMAL]


def sync_schedule_delivery_payment_type(schedule, *, save=True) -> str:
    payment_type = infer_delivery_payment_type(schedule)
    if getattr(schedule, 'activity_type', '') != 'delivery':
        payment_type = DELIVERY_PAYMENT_NORMAL
    inferred_status = infer_delivery_payment_status(schedule)
    current_status = getattr(schedule, 'delivery_payment_status', None) or DELIVERY_PAYMENT_STATUS_NORMAL
    should_sync_status = (
        current_status in DELIVERY_PAYMENT_STATUS_AUTO_VALUES
        or inferred_status == DELIVERY_PAYMENT_STATUS_CANCELLED_RETURNED
    )
    payment_status = inferred_status if should_sync_status else current_status
    updates = []
    if getattr(schedule, 'delivery_payment_type', None) != payment_type:
        schedule.delivery_payment_type = payment_type
        updates.append('delivery_payment_type')
    if getattr(schedule, 'delivery_payment_status', None) != payment_status:
        schedule.delivery_payment_status = payment_status
        updates.append('delivery_payment_status')
    if updates:
        if save:
            schedule.save(update_fields=[*updates, 'updated_at'])
    return payment_type


def delivery_payment_payload(schedule, usages=None) -> dict:
    usage_info = structured_prepayment_usage(schedule, usages)
    schedule_id = getattr(schedule, 'id', None)
    inferred_status = infer_delivery_payment_status(schedule, usage_info['usages'])
    stored_status = getattr(schedule, 'delivery_payment_status', None) or inferred_status
    if stored_status not in DELIVERY_PAYMENT_STATUS_LABELS:
        stored_status = inferred_status
    if stored_status == DELIVERY_PAYMENT_STATUS_NORMAL and inferred_status != DELIVERY_PAYMENT_STATUS_NORMAL:
        payment_status = inferred_status
    else:
        payment_status = stored_status
    payment_status_label = delivery_payment_status_label(payment_status)
    uses_prepayment = bool(
        usage_info['uses_prepayment']
        or getattr(schedule, 'delivery_payment_type', '') == DELIVERY_PAYMENT_PREPAYMENT
        or payment_status == DELIVERY_PAYMENT_STATUS_PREPAYMENT
    )
    payment_status_evidence = (
        f"Schedule #{schedule_id}: Schedule.delivery_payment_status={payment_status}"
    )
    if payment_status != inferred_status:
        payment_status_evidence = (
            f"{payment_status_evidence}, 구조화 선결제/취소 필드 기준 자동 상태={inferred_status}"
        )

    if uses_prepayment:
        evidence = ', '.join(usage_info['evidence_parts']) or '구조화 선결제 사용 내역 확인'
        return {
            'paymentSource': 'prepayment',
            'paymentSourceLabel': '선결제 차감 납품',
            'paymentType': DELIVERY_PAYMENT_PREPAYMENT,
            'paymentTypeLabel': '선결제 차감 납품',
            'paymentStatus': payment_status,
            'paymentStatusLabel': payment_status_label,
            'paymentStatusEvidence': payment_status_evidence,
            'prepaymentId': usage_info['prepayment_id'],
            'prepaymentAmount': usage_info['prepayment_amount'],
            'paymentEvidence': f'Schedule #{schedule_id}: {evidence}; delivery_payment_status={payment_status}',
            'usages': usage_info['usages'],
        }

    return {
        'paymentSource': 'normal',
        'paymentSourceLabel': '일반 납품',
        'paymentType': DELIVERY_PAYMENT_NORMAL,
        'paymentTypeLabel': '일반 납품',
        'paymentStatus': payment_status,
        'paymentStatusLabel': payment_status_label,
        'paymentStatusEvidence': payment_status_evidence,
        'prepaymentId': None,
        'prepaymentAmount': 0,
        'paymentEvidence': (
            f'Schedule #{schedule_id}: Schedule.delivery_payment_type=normal, '
            f'Schedule.delivery_payment_status={payment_status}, '
            '선결제 사용 필드와 PrepaymentUsage 기록이 없습니다.'
        ),
        'usages': usage_info['usages'],
    }


def backfill_delivery_payment_type_queryset(queryset):
    usage_schedule_ids = PrepaymentUsage.objects.filter(
        schedule_id__isnull=False,
    ).values_list('schedule_id', flat=True)
    queryset.filter(
        activity_type='delivery',
    ).filter(
        use_prepayment=True,
    ).update(
        delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT,
        delivery_payment_status=DELIVERY_PAYMENT_STATUS_PREPAYMENT,
    )
    queryset.filter(
        activity_type='delivery',
        prepayment_id__isnull=False,
    ).update(
        delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT,
        delivery_payment_status=DELIVERY_PAYMENT_STATUS_PREPAYMENT,
    )
    queryset.filter(
        activity_type='delivery',
        prepayment_amount__gt=0,
    ).update(
        delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT,
        delivery_payment_status=DELIVERY_PAYMENT_STATUS_PREPAYMENT,
    )
    queryset.filter(
        activity_type='delivery',
        id__in=usage_schedule_ids,
    ).update(
        delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT,
        delivery_payment_status=DELIVERY_PAYMENT_STATUS_PREPAYMENT,
    )
