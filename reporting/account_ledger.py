"""Shared account-ledger helpers for department/lab based CRM views."""

from decimal import Decimal, InvalidOperation

from django.db.models import QuerySet

from .models import FollowUp, PrepaymentUsage, Schedule


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
