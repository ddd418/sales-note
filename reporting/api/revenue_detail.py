"""'진짜 매출' 드릴다운 API.

대시보드 상단 "당해년도 전체 매출"/"현재 분기 매출" 카드를 클릭했을 때 이동하는
화면의 데이터 소스. `dashboard_summary_api`와 **완전히 같은 기간 경계·완료 기준**으로
계산해서, 여기서 보여주는 내역 합계가 대시보드 상단 숫자와 항상 일치하게 한다.
완료(completed)된 납품과 선결제만 "실제 매출"로 센다 — 예정(scheduled) 납품은
아직 실제로 일어나지 않아 취소·변경될 수 있으므로 제외한다.
"""

from datetime import date, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from reporting.models import DeliveryItem, Prepayment, Schedule
from reporting.views import (
    _api_login_required_response,
    _dashboard_scope_users,
    _money_int,
    _user_display_name,
    get_user_profile,
)


def _period_bounds(period, today):
    if period == 'month':
        start = date(today.year, today.month, 1)
        end = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)
        label = f'{today.year}년 {today.month}월'
    elif period == 'quarter':
        quarter = ((today.month - 1) // 3) + 1
        quarter_start_month = ((quarter - 1) * 3) + 1
        start = date(today.year, quarter_start_month, 1)
        end = (
            date(today.year + 1, 1, 1)
            if quarter_start_month == 10
            else date(today.year, quarter_start_month + 3, 1)
        )
        label = f'{today.year}년 {quarter}분기'
    else:
        start = date(today.year, 1, 1)
        end = date(today.year + 1, 1, 1)
        label = f'{today.year}년'
    return start, end, label


def _account_label(followup, department):
    company = None
    if department is not None and department.company_id:
        company = department.company
    elif followup is not None and followup.company_id:
        company = followup.company
    company_name = company.name if company else ''
    department_name = department.name if department is not None else ''
    customer_name = (followup.customer_name or str(followup)) if followup is not None else ''
    return ' / '.join(part for part in [company_name, department_name or customer_name] if part) or '고객 미지정'


@never_cache
@require_http_methods(["GET"])
def revenue_detail_api(request):
    """대시보드 매출 카드가 가리키는 실제 내역 — 완료 납품 + 선결제만."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()
    period = request.GET.get('period') if request.GET.get('period') in ('year', 'quarter', 'month') else 'year'
    start, end, period_label = _period_bounds(period, today)

    delivery_items = DeliveryItem.objects.filter(
        schedule__in=Schedule.objects.filter(user__in=scope_users),
        schedule__activity_type='delivery',
        schedule__status='completed',
        schedule__visit_date__gte=start,
        schedule__visit_date__lt=end,
    ).select_related(
        'schedule', 'schedule__user',
        'schedule__followup', 'schedule__followup__company', 'schedule__followup__department',
        'schedule__department', 'schedule__department__company',
    )

    prepayments = Prepayment.objects.filter(
        created_by__in=scope_users,
        payment_date__gte=start,
        payment_date__lt=end,
    ).exclude(status='cancelled').select_related(
        'customer', 'customer__company', 'customer__department', 'company', 'department', 'created_by',
    )

    items = []
    delivery_total = 0
    for delivery_item in delivery_items:
        schedule = delivery_item.schedule
        followup = schedule.followup if schedule.followup_id else None
        department = (
            followup.department if followup is not None and followup.department_id
            else (schedule.department if schedule.department_id else None)
        )
        amount = _money_int(delivery_item.total_price)
        delivery_total += amount
        items.append({
            'kind': 'delivery',
            'date': schedule.visit_date.isoformat() if schedule.visit_date else None,
            'accountLabel': _account_label(followup, department),
            'itemName': delivery_item.item_name,
            'quantity': delivery_item.quantity,
            'amount': amount,
            'owner': _user_display_name(schedule.user) if schedule.user_id else '',
            'href': f'/schedules/{schedule.id}/',
        })

    prepayment_total = 0
    for prepayment in prepayments:
        followup = prepayment.customer if prepayment.customer_id else None
        department = (
            prepayment.department if prepayment.department_id
            else (followup.department if followup is not None and followup.department_id else None)
        )
        amount = _money_int(prepayment.amount)
        prepayment_total += amount
        items.append({
            'kind': 'prepayment',
            'date': prepayment.payment_date.isoformat() if prepayment.payment_date else None,
            'accountLabel': _account_label(followup, department),
            'itemName': f'선결제 · {prepayment.get_payment_method_display()}',
            'quantity': None,
            'amount': amount,
            'owner': _user_display_name(prepayment.created_by) if prepayment.created_by_id else '',
            'href': f'/prepayments/{prepayment.id}/',
        })

    items.sort(key=lambda entry: entry['date'] or '', reverse=True)

    scope_label = (
        _user_display_name(selected_user) if selected_user
        else (f'{user_profile.company.name} 팀' if user_profile.company else '전체')
    )

    return JsonResponse({
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'period': {
            'value': period,
            'label': period_label,
            'start': start.isoformat(),
            'end': (end - timedelta(days=1)).isoformat(),
        },
        'scope': {'label': scope_label},
        'summary': {
            'total': delivery_total + prepayment_total,
            'deliveryTotal': delivery_total,
            'prepaymentTotal': prepayment_total,
            'itemCount': len(items),
        },
        'items': items,
    })
