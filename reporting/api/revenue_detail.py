"""'진짜 매출' 드릴다운 API.

대시보드 상단 "당해년도 전체 매출"/"현재 분기 매출" 카드를 클릭했을 때 이동하는
화면의 데이터 소스. `dashboard_summary_api`와 **완전히 같은 기간 경계·완료 기준**으로
계산해서, 여기서 보여주는 내역 합계가 대시보드 상단 숫자와 항상 일치하게 한다.

매출로 세는 것은 **완료(completed)된 납품뿐**이다.
- 예정(scheduled) 납품은 아직 일어나지 않아 취소·변경될 수 있으므로 제외한다.
- **선결제는 그 자체로 매출이 아니다**(받아둔 돈일 뿐이다). 선결제가 매출이 되는
  순간은 그 돈으로 실제 납품이 나갈 때이고, 그 납품은 이미 완료 납품으로 여기
  잡힌다. 예전에는 선결제 등록액을 여기에 더해서, 같은 돈이 입금 시점과 납품
  시점에 **두 번 계상**됐다(프로덕션 확인 결과 선결제 차감 38건 전부가
  `납품·완료` 일정에 걸려 있어, 선결제 항목을 빼도 누락되는 매출은 없다).
"""

from datetime import date, timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from reporting.models import DeliveryItem, Schedule
from reporting.views import (
    _api_login_required_response,
    delivered_revenue_rows,
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
    """대시보드 매출 카드가 가리키는 실제 내역 — 완료된 납품만."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response

    user_profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, user_profile)
    today = timezone.localdate()
    period = request.GET.get('period') if request.GET.get('period') in ('year', 'quarter', 'month') else 'year'
    start, end, period_label = _period_bounds(period, today)

    # 대시보드와 **같은 함수**로 집계한다. 여기서 행을 품목 단위로 만들면, 금액을
    # 노트에서 읽어온 일정(품목 행이 없는 일정)은 내역에 아예 안 나와 합계가
    # 대시보드와 어긋난다. 그래서 행도 일정 단위로 맞춘다.
    rows = delivered_revenue_rows(Schedule.objects.filter(user__in=scope_users))

    items = []
    delivery_total = 0
    for schedule, raw_amount in rows:
        if not schedule.visit_date or not (start <= schedule.visit_date < end):
            continue
        followup = schedule.followup if schedule.followup_id else None
        department = (
            followup.department if followup is not None and followup.department_id
            else (schedule.department if schedule.department_id else None)
        )
        amount = _money_int(raw_amount)
        delivery_total += amount
        detail_items = list(DeliveryItem.objects.filter(schedule=schedule))
        if not detail_items:
            detail_items = list(DeliveryItem.objects.filter(history__schedule=schedule))
        names = [item.item_name for item in detail_items if item.item_name]
        if names:
            item_name = names[0] if len(names) == 1 else f'{names[0]} 외 {len(names) - 1}건'
        else:
            item_name = '납품'
        items.append({
            'kind': 'delivery',
            'date': schedule.visit_date.isoformat(),
            'accountLabel': _account_label(followup, department),
            'itemName': item_name,
            'quantity': sum(item.quantity or 0 for item in detail_items) or None,
            'amount': amount,
            'owner': _user_display_name(schedule.user) if schedule.user_id else '',
            'href': f'/schedules/{schedule.id}/',
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
            'total': delivery_total,
            'deliveryTotal': delivery_total,
            'itemCount': len(items),
        },
        'items': items,
    })
