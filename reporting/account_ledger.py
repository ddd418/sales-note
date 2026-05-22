"""Shared account-ledger helpers for department/lab based CRM views."""

from decimal import Decimal, InvalidOperation

from django.db.models import QuerySet

from .models import FollowUp, PrepaymentUsage, Schedule


DELIVERY_PAYMENT_NORMAL = Schedule.DELIVERY_PAYMENT_TYPE_NORMAL
DELIVERY_PAYMENT_PREPAYMENT = Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT


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
        .order_by('-updated_at', '-created_at', '-id')
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


def sync_schedule_delivery_payment_type(schedule, *, save=True) -> str:
    payment_type = infer_delivery_payment_type(schedule)
    if getattr(schedule, 'activity_type', '') != 'delivery':
        payment_type = DELIVERY_PAYMENT_NORMAL
    if getattr(schedule, 'delivery_payment_type', None) != payment_type:
        schedule.delivery_payment_type = payment_type
        if save:
            schedule.save(update_fields=['delivery_payment_type', 'updated_at'])
    return payment_type


def delivery_payment_payload(schedule, usages=None) -> dict:
    usage_info = structured_prepayment_usage(schedule, usages)
    schedule_id = getattr(schedule, 'id', None)
    if usage_info['uses_prepayment']:
        evidence = ', '.join(usage_info['evidence_parts']) or '구조화 선결제 사용 내역 확인'
        return {
            'paymentSource': 'prepayment',
            'paymentSourceLabel': '선결제 차감 납품',
            'paymentType': DELIVERY_PAYMENT_PREPAYMENT,
            'paymentTypeLabel': '선결제 차감 납품',
            'prepaymentId': usage_info['prepayment_id'],
            'prepaymentAmount': usage_info['prepayment_amount'],
            'paymentEvidence': f'Schedule #{schedule_id}: {evidence}',
            'usages': usage_info['usages'],
        }

    return {
        'paymentSource': 'normal',
        'paymentSourceLabel': '일반 납품',
        'paymentType': DELIVERY_PAYMENT_NORMAL,
        'paymentTypeLabel': '일반 납품',
        'prepaymentId': None,
        'prepaymentAmount': 0,
        'paymentEvidence': (
            f'Schedule #{schedule_id}: Schedule.delivery_payment_type=normal, '
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
    ).update(delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT)
    queryset.filter(
        activity_type='delivery',
        prepayment_id__isnull=False,
    ).update(delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT)
    queryset.filter(
        activity_type='delivery',
        prepayment_amount__gt=0,
    ).update(delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT)
    queryset.filter(
        activity_type='delivery',
        id__in=usage_schedule_ids,
    ).update(delivery_payment_type=DELIVERY_PAYMENT_PREPAYMENT)
