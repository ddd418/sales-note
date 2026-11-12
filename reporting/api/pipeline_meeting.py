"""아침회의 모드 API — 지난주에 무엇이 달라졌고 오늘 무엇을 정할지 한 번에.

파이프라인(현재 상태)과 파이프라인 시트(활동 목록)를 다시 보여주는 게 아니라, 회의 흐름인
다섯 장면에 맞춰 묶는다: 요약 → 서비스 → 활동 → 지난주 약속 → 이번 주 계획.

숫자 원칙: 매출은 대시보드와 같은 헬퍼·같은 범위(`delivered_revenue_rows`,
`_dashboard_scope_users`), 주 경계와 견적 금액은 파이프라인 시트와 같은 규칙을 쓴다.
회의 화면 숫자가 다른 화면과 갈라지면 발표 자료로 쓸 수 없기 때문이다.
"""

import json
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Max, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from reporting.api.pipeline_sheet import (
    STAGE_LABELS,
    WEEKDAY_LABELS,
    _account_rows,
    _parse_week_start,
    _schedule_amount,
    _scope_payload,
    _week_options,
    _weekly_rows,
    week_bounds,
)
from reporting.funnel_views import (
    _money_int,
    _pipeline_account_followup,
    _pipeline_account_stage,
    _select_pipeline_pricing,
    pipeline_followups_queryset,
)
from reporting.api.services import can_edit_case, case_title, visible_service_cases
from reporting.models import DeliveryItem, FollowUp, History, MeetingActionItem, MeetingDismissedNote, PipelineStageChange, Schedule, ServiceCase
from reporting.views import (
    _api_login_required_response,
    _dashboard_scope_users,
    _user_display_name,
    delivered_revenue_rows,
    get_user_profile,
)

# 뒤로 갔는지 판단하는 순서. 실주는 순서 밖이라 따로 분류한다.
STAGE_RANK = {'potential': 0, 'contact': 1, 'quote': 2, 'negotiation': 3, 'won': 4}
OPEN_STAGES = ('contact', 'quote', 'negotiation')

MOVEMENT_LIMIT = 12


def _customer_label(followup):
    if followup is None:
        return ''
    return followup.customer_name or followup.manager or '담당자 미정'


def _company_label(followup):
    if followup is None or not followup.company:
        return ''
    return str(followup.company)


def _local_day_range(start_day, days):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(start_day, time.min), tz)
    return start, start + timedelta(days=days)


# ------------------------------------------------------------------ 1. 요약

def _summary(request, scope_users, today, week_start, week_end):
    year_start = date(today.year, 1, 1)
    last_year_start = date(today.year - 1, 1, 1)
    last_year_end = date(today.year - 1, 12, 31)
    previous_start = week_start - timedelta(days=7)
    previous_end = week_end - timedelta(days=7)

    rows = delivered_revenue_rows(
        Schedule.objects.filter(user__in=scope_users, visit_date__gte=min(last_year_start, previous_start))
    )

    def between(first, last):
        return sum(
            (amount for schedule, amount in rows if schedule.visit_date and first <= schedule.visit_date <= last),
            0,
        )

    week_rows = [s for s, _a in rows if s.visit_date and week_start <= s.visit_date <= week_end]
    week_revenue = between(week_start, week_end)
    previous_revenue = between(previous_start, previous_end)
    year_revenue = between(year_start, date(today.year, 12, 31))
    last_year_revenue = between(last_year_start, last_year_end)

    base_rows = _account_rows(request, today)
    sheet_rows, quote_amount, _delivery_amount = _weekly_rows(request, week_start, week_end, base_rows)

    return {
        'yearRevenue': _money_int(year_revenue),
        'lastYearRevenue': _money_int(last_year_revenue),
        'weekRevenue': _money_int(week_revenue),
        'previousWeekRevenue': _money_int(previous_revenue),
        'weekDelta': _money_int(week_revenue) - _money_int(previous_revenue),
        'deliveryCount': len(week_rows),
        'quoteAmount': quote_amount,
        'activeAccounts': sum(1 for row in sheet_rows if row['activityCount'] > 0),
    }


# --------------------------------------------------------------- 카드 공통

def _card_rows(request, today, scope_users):
    """파이프라인 보드와 같은 방식으로 건별 금액·단계를 만든다."""
    cards = []
    for raw in pipeline_followups_queryset(request, today).filter(user__in=scope_users):
        stage = _pipeline_account_stage([raw])
        followup = _pipeline_account_followup([raw], stage)
        cards.append((followup, stage, _money_int(_select_pipeline_pricing(followup, stage)['amount'])))
    return cards


# --------------------------------------------------------------- 2. 움직임

def _classify_movement(from_stage, to_stage):
    if to_stage == 'won':
        return 'won'
    if to_stage == 'lost':
        return 'lost'
    if not from_stage:
        return 'created'
    if from_stage == 'lost':
        return 'advanced'
    return 'advanced' if STAGE_RANK.get(to_stage, 0) > STAGE_RANK.get(from_stage, 0) else 'regressed'


def _movement(scope_users, week_start, cards):
    start, end = _local_day_range(week_start, 7)
    amounts = {followup.id: amount for followup, _stage, amount in cards}

    first_last = {}
    restored = False
    changes = (
        PipelineStageChange.objects
        .filter(followup__user__in=scope_users, followup__pipeline_hidden=False, changed_at__gte=start, changed_at__lt=end)
        .select_related('followup', 'followup__company', 'followup__department', 'followup__user')
        .order_by('changed_at', 'id')
    )
    for change in changes:
        restored = restored or change.source == PipelineStageChange.SOURCE_BACKFILL
        entry = first_last.setdefault(change.followup_id, {'first': change, 'last': change})
        entry['last'] = change

    groups = {'won': [], 'advanced': [], 'regressed': [], 'lost': [], 'created': []}
    for entry in first_last.values():
        from_stage = entry['first'].from_stage
        to_stage = entry['last'].to_stage
        if from_stage == to_stage:
            continue  # 한 주 안에 갔다가 돌아온 건은 변화가 아니다
        followup = entry['first'].followup
        groups[_classify_movement(from_stage, to_stage)].append({
            'followupId': followup.id,
            'customer': _customer_label(followup),
            'company': _company_label(followup),
            'owner': _user_display_name(followup.user),
            'ownerId': followup.user_id,
            'fromStage': from_stage,
            'fromLabel': STAGE_LABELS.get(from_stage, '신규') if from_stage else '신규',
            'toStage': to_stage,
            'toLabel': STAGE_LABELS.get(to_stage, to_stage),
            'amount': amounts.get(followup.id, 0),
            'href': f'/customers/{followup.id}/',
        })

    payload = {}
    for key, rows in groups.items():
        rows.sort(key=lambda row: (-row['amount'], row['company'], row['customer']))
        payload[key] = {
            'count': len(rows),
            'amount': sum(row['amount'] for row in rows),
            'items': rows[:MOVEMENT_LIMIT],
        }

    first_record = PipelineStageChange.objects.order_by('changed_at').values_list('changed_at', flat=True).first()
    tracking_since = timezone.localtime(first_record).date() if first_record else None
    return {
        **payload,
        'trackingSince': tracking_since.isoformat() if tracking_since else None,
        # 기록을 켜기 전 주는 "변화 없음"이 아니라 "알 수 없음"이다. 화면이 구분해서 말해야 한다.
        'tracked': bool(tracking_since and tracking_since <= week_start + timedelta(days=6)),
        # 일정 근거로 채운 주는 직접 옮긴 건이 빠졌을 수 있다. 화면이 그렇게 밝혀야 한다.
        'restored': restored,
    }


# ------------------------------------------------------------ 3. 지난주 약속

def _action_item_payload(item, viewer, scope_user_ids, today):
    followup = item.followup
    return {
        'id': item.id,
        'kind': item.kind,
        'title': item.title,
        'ownerId': item.owner_id,
        'owner': _user_display_name(item.owner),
        'dueDate': item.due_date.isoformat() if item.due_date else None,
        'overdue': bool(item.status == MeetingActionItem.STATUS_OPEN and item.due_date and item.due_date < today),
        # 보고 기한이 되면 회의 화면이 맨 위로 올리고 탭에 건수를 띄운다(완료할 때까지 유지)
        'dueReached': bool(item.status == MeetingActionItem.STATUS_OPEN and item.due_date and item.due_date <= today),
        'status': item.status,
        'customer': _customer_label(followup),
        'company': _company_label(followup),
        'followupId': item.followup_id,
        'href': f'/customers/{item.followup_id}/' if item.followup_id else '',
        # 몇 번째 회의까지 넘어온 약속인지 — 이월이 쌓이면 회의에서 바로 보이게 한다
        'carriedWeeks': max((today - timezone.localtime(item.created_at).date()).days // 7, 0),
        'canEdit': item.owner_id in scope_user_ids or item.created_by_id == viewer.id,
    }


def _action_items(request, scope_users, today, week_start):
    start, _end = _local_day_range(week_start, 7)
    items = (
        MeetingActionItem.objects
        .filter(Q(owner__in=scope_users) | Q(created_by=request.user))
        .filter(Q(status=MeetingActionItem.STATUS_OPEN) | Q(done_at__gte=start))
        .select_related('owner', 'followup', 'followup__company')
        .order_by('status', 'due_date', 'id')
    )
    ids = set(scope_users.values_list('id', flat=True))
    return [_action_item_payload(item, request.user, ids, today) for item in items]


def _next_action_promises(scope_users, today, week_start):
    """지난주까지 하기로 적어 둔 다음 액션과, 그 뒤 실제로 후속 기록이 있는지."""
    notes = list(
        History.objects
        .filter(
            user__in=scope_users,
            parent_history__isnull=True,
            followup__isnull=False,
            meeting_dismissal__isnull=True,
            next_action_date__gte=week_start,
            next_action_date__lte=week_start + timedelta(days=6),
        )
        .exclude(Q(next_action__isnull=True) | Q(next_action=''), Q(meeting_next_action__isnull=True) | Q(meeting_next_action=''))
        .select_related('user', 'followup', 'followup__company')
        .order_by('next_action_date', 'id')
    )
    followup_ids = {note.followup_id for note in notes}
    later_notes = {}
    for followup_id, created_at in (
        History.objects.filter(followup_id__in=followup_ids, parent_history__isnull=True)
        .values_list('followup_id', 'created_at')
    ):
        later_notes.setdefault(followup_id, []).append(created_at)
    # 다음 일정은 노트 저장 때 함께 만들어지기도 하므로 "생성"이 아니라 "완료"만 후속으로 친다
    completed_visits = {}
    for followup_id, visit_date in (
        Schedule.objects.filter(followup_id__in=followup_ids, status='completed', visit_date__lte=today)
        .values_list('followup_id', 'visit_date')
    ):
        completed_visits.setdefault(followup_id, []).append(visit_date)

    rows = []
    for note in notes:
        note_day = timezone.localtime(note.created_at).date()
        followed = (
            any(created_at > note.created_at for created_at in later_notes.get(note.followup_id, []))
            or any(visit > note_day for visit in completed_visits.get(note.followup_id, []))
        )
        rows.append({
            'id': note.id,
            'customer': _customer_label(note.followup),
            'company': _company_label(note.followup),
            'owner': _user_display_name(note.user),
            'ownerId': note.user_id,
            'text': (note.next_action or note.meeting_next_action or '').strip().split('\n')[0][:120],
            'dueDate': note.next_action_date.isoformat(),
            'followedUp': followed,
            'href': f'/notes/{note.id}/',
        })
    rows.sort(key=lambda row: (row['followedUp'], row['dueDate']))
    return rows


# ---------------------------------------------------------------- 서비스

def _service_payload(case, viewer, scope_user_ids):
    return {
        'id': case.id,
        'institution': case.institution or (_company_label(case.followup) if case.followup_id else ''),
        'content': case_title(case),
        'customer': _customer_label(case.followup) if case.followup_id else '',
        'statusLabel': case.get_status_display(),
        'typeLabel': case.get_case_type_display(),
        'href': f'/services/{case.id}/',
        'createdAt': timezone.localtime(case.created_at).date().isoformat(),
        'canEdit': can_edit_case(case, viewer, scope_user_ids),
    }


def _week_cases(request, scope_users, week_start):
    # 서비스 메뉴와 같은 범위·같은 기록. 그 주(월~일)에 한 서비스를 보여준다.
    return visible_service_cases(request, scope_users).filter(
        received_date__gte=week_start, received_date__lte=week_start + timedelta(days=6),
    )


def _service_records(request, scope_users, week_start):
    cases = (
        _week_cases(request, scope_users, week_start)
        .select_related('followup', 'followup__company')
        .order_by('meeting_position', 'received_date', 'id')
    )
    ids = set(scope_users.values_list('id', flat=True))
    return [_service_payload(case, request.user, ids) for case in cases]


# --------------------------------------------------------------- 5. 계획

def _plan(scope_users, plan_start):
    plan_end = plan_start + timedelta(days=6)
    schedules = (
        Schedule.objects
        .filter(user__in=scope_users, visit_date__gte=plan_start, visit_date__lte=plan_end)
        .exclude(status='cancelled')
        .select_related('user', 'followup', 'followup__company')
        # _schedule_amount 가 읽는 이름으로 미리 불러온다(없으면 금액이 조용히 0 이 된다)
        .prefetch_related(
            Prefetch('delivery_items_set', queryset=DeliveryItem.objects.order_by('id'), to_attr='linked_delivery_items'),
            Prefetch('histories', queryset=History.objects.filter(parent_history__isnull=True), to_attr='linked_histories'),
        )
        .order_by('visit_date', 'visit_time', 'id')
    )
    owners = {}
    total = 0
    for schedule in schedules:
        total += 1
        owner = owners.setdefault(schedule.user_id, {
            'ownerId': schedule.user_id,
            'owner': _user_display_name(schedule.user),
            'items': [],
        })
        owner['items'].append({
            'id': schedule.id,
            'date': schedule.visit_date.isoformat(),
            'weekday': WEEKDAY_LABELS[schedule.visit_date.weekday()],
            'time': schedule.visit_time.strftime('%H:%M') if schedule.visit_time else '',
            'type': schedule.activity_type,
            'typeLabel': schedule.get_activity_type_display(),
            'customer': _customer_label(schedule.followup),
            'company': _company_label(schedule.followup),
            'amount': _schedule_amount(schedule) if schedule.activity_type in ('quote', 'delivery') else 0,
            'href': f'/schedules/{schedule.id}/',
        })
    return {
        'start': plan_start.isoformat(),
        'end': plan_end.isoformat(),
        'total': total,
        'byOwner': sorted(owners.values(), key=lambda owner: (-len(owner['items']), owner['owner'])),
    }


# ------------------------------------------------------------------- 응답

def _meeting_payload(request):
    profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, profile)
    today = timezone.localdate()
    week_start = _parse_week_start(request.GET.get('week'), today)
    week_end = week_start + timedelta(days=4)
    plan_start = week_start + timedelta(days=7)
    cards = _card_rows(request, today, scope_users)
    movement = _movement(scope_users, week_start, cards)
    summary = _summary(request, scope_users, today, week_start, week_end)
    # 기록이 없는 주의 실주 금액은 0 이 아니라 '알 수 없음'이다
    summary['lostAmount'] = movement['lost']['amount'] if movement['tracked'] else None

    return {
        'success': True,
        'source': 'django',
        'generatedAt': timezone.now().isoformat(),
        'week': {
            'start': week_start.isoformat(),
            'end': week_end.isoformat(),
            'isCurrent': week_start == week_bounds(today)[0],
        },
        'weekOptions': _week_options(today),
        'scope': _scope_payload(request, profile, scope_users, selected_user),
        'summary': summary,
        'movement': movement,
        'promises': {
            'actionItems': _action_items(request, scope_users, today, week_start),
            'nextActions': _next_action_promises(scope_users, today, week_start),
        },
        'services': _service_records(request, scope_users, week_start),
        'plan': _plan(scope_users, plan_start),
        'form': {
            'institutions': sorted({_company_label(followup) for followup, _stage, _amount in cards} - {''}),
            'owners': [
                {'id': user.id, 'name': _user_display_name(user)}
                for user in scope_users.order_by('username')
            ],
            'customers': sorted(
                (
                    {'id': followup.id, 'label': f'{_company_label(followup)} · {_customer_label(followup)}'.strip(' ·')}
                    for followup, stage, _amount in cards if stage != 'lost'
                ),
                key=lambda option: option['label'],
            ),
        },
    }


@never_cache
@ensure_csrf_cookie
@require_GET
def pipeline_meeting_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    return JsonResponse(_meeting_payload(request))


# ------------------------------------------------------------ 약속 입력·완료

def _error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _parse_payload(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _editable_item_or_error(request, item_id):
    profile = get_user_profile(request.user)
    scope_users, _selected = _dashboard_scope_users(request, profile)
    item = get_object_or_404(MeetingActionItem, pk=item_id)
    ids = set(scope_users.values_list('id', flat=True))
    if item.owner_id not in ids and item.created_by_id != request.user.id:
        return None, _error('이 약속을 변경할 권한이 없습니다.', status=403), ids
    return item, None, ids


@require_POST
def meeting_action_create_api(request):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')

    title = str(payload.get('title') or '').strip()
    if not title:
        return _error('약속 내용을 입력하세요.')
    if len(title) > 200:
        return _error('약속 내용은 200자 이내로 입력하세요.')

    kind = str(payload.get('kind') or MeetingActionItem.KIND_PROMISE)
    if kind not in dict(MeetingActionItem.KIND_CHOICES):
        return _error('종류를 다시 선택하세요.')

    profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, profile)
    if payload.get('ownerId'):
        try:
            owner = scope_users.filter(pk=int(payload['ownerId'])).first()
        except (TypeError, ValueError):
            owner = None
        if owner is None:
            return _error('담당자를 다시 선택하세요.')
    else:
        owner = selected_user or request.user

    due_date = None
    if payload.get('dueDate'):
        try:
            due_date = date.fromisoformat(str(payload['dueDate']))
        except ValueError:
            return _error('기한 형식이 올바르지 않습니다.')
    if kind == MeetingActionItem.KIND_REPORT and due_date is None:
        return _error('보고 기한을 선택하세요.')

    followup = None
    if payload.get('followupId'):
        try:
            followup = FollowUp.objects.filter(user__in=scope_users, pk=int(payload['followupId'])).first()
        except (TypeError, ValueError):
            followup = None
        if followup is None:
            return _error('고객을 다시 선택하세요.')

    item = MeetingActionItem.objects.create(
        kind=kind, owner=owner, followup=followup, title=title, due_date=due_date, created_by=request.user,
    )
    ids = set(scope_users.values_list('id', flat=True))
    return JsonResponse(
        {'success': True, 'item': _action_item_payload(item, request.user, ids, timezone.localdate())},
        status=201,
    )


@require_POST
def meeting_action_toggle_api(request, item_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    item, error, ids = _editable_item_or_error(request, item_id)
    if error:
        return error
    if item.status == MeetingActionItem.STATUS_OPEN:
        item.status = MeetingActionItem.STATUS_DONE
        item.done_at = timezone.now()
    else:
        item.status = MeetingActionItem.STATUS_OPEN
        item.done_at = None
    item.save(update_fields=['status', 'done_at'])
    return JsonResponse({'success': True, 'item': _action_item_payload(item, request.user, ids, timezone.localdate())})


@require_POST
def meeting_action_update_api(request, item_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    item, error, ids = _editable_item_or_error(request, item_id)
    if error:
        return error
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')
    title = str(payload.get('title') or '').strip()
    if not title:
        return _error('내용을 입력하세요.')
    if len(title) > 200:
        return _error('내용은 200자 이내로 입력하세요.')
    item.title = title
    item.save(update_fields=['title'])
    return JsonResponse({'success': True, 'item': _action_item_payload(item, request.user, ids, timezone.localdate())})


@require_POST
def meeting_action_delete_api(request, item_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    item, error, _ids = _editable_item_or_error(request, item_id)
    if error:
        return error
    item.delete()
    return JsonResponse({'success': True})


# ------------------------------------------------- 다음 액션 숨기기(회의 목록에서만)

def _note_in_scope_or_error(request, note_id):
    profile = get_user_profile(request.user)
    scope_users, _selected = _dashboard_scope_users(request, profile)
    note = get_object_or_404(History, pk=note_id, parent_history__isnull=True)
    if not scope_users.filter(pk=note.user_id).exists():
        return None, _error('이 항목을 변경할 권한이 없습니다.', status=403)
    return note, None


@require_POST
def meeting_next_action_dismiss_api(request, note_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    note, error = _note_in_scope_or_error(request, note_id)
    if error:
        return error
    MeetingDismissedNote.objects.get_or_create(history=note, defaults={'dismissed_by': request.user})
    return JsonResponse({'success': True})


@require_POST
def meeting_next_action_restore_api(request, note_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    note, error = _note_in_scope_or_error(request, note_id)
    if error:
        return error
    MeetingDismissedNote.objects.filter(history=note).delete()
    return JsonResponse({'success': True})


# -------------------------------------------------------- 서비스 입력·삭제

@require_POST
def meeting_service_create_api(request):
    """회의 중 빠른 기록. 서비스 메뉴에 그대로 쌓이고, 고객·장비·부품은 나중에 채운다."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')

    institution = str(payload.get('institution') or '').strip()
    content = str(payload.get('content') or '').strip()
    if not institution:
        return _error('기관을 입력하세요.')
    if len(institution) > 100:
        return _error('기관은 100자 이내로 입력하세요.')
    if not content:
        return _error('서비스 내용을 입력하세요.')
    if not payload.get('week'):
        return _error('기준 주가 없습니다.')

    profile = get_user_profile(request.user)
    scope_users, selected_user = _dashboard_scope_users(request, profile)
    today = timezone.localdate()
    week_start = _parse_week_start(str(payload['week']), today)
    # 회의에 보고하는 서비스는 이미 한 일이다. 이번 주면 오늘, 지난 주면 그 주 월요일로 둔다.
    service_date = today if week_start <= today <= week_start + timedelta(days=6) else week_start
    last_position = (
        _week_cases(request, scope_users, week_start).aggregate(last=Max('meeting_position'))['last'] or 0
    )
    case = ServiceCase.objects.create(
        institution=institution,
        title=content[:200],
        resolution=content if len(content) > 200 else '',
        case_type='service',
        status='completed',
        received_date=service_date,
        completed_date=service_date,
        assigned_to=selected_user or request.user,
        created_by=request.user,
        meeting_position=last_position + 1,
    )
    ids = set(scope_users.values_list('id', flat=True))
    return JsonResponse({'success': True, 'record': _service_payload(case, request.user, ids)}, status=201)


def _editable_service_or_error(request, record_id):
    profile = get_user_profile(request.user)
    scope_users, _selected = _dashboard_scope_users(request, profile)
    case = get_object_or_404(visible_service_cases(request, scope_users).select_related('followup', 'followup__company'), pk=record_id)
    ids = set(scope_users.values_list('id', flat=True))
    if not can_edit_case(case, request.user, ids):
        return None, _error('이 기록을 변경할 권한이 없습니다.', status=403), ids
    return case, None, ids


@require_POST
def meeting_service_delete_api(request, record_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    case, error, _ids = _editable_service_or_error(request, record_id)
    if error:
        return error
    case.delete()
    return JsonResponse({'success': True})


@require_POST
def meeting_service_update_api(request, record_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    case, error, ids = _editable_service_or_error(request, record_id)
    if error:
        return error
    payload = _parse_payload(request)
    if payload is None:
        return _error('잘못된 요청 형식입니다.')
    institution = str(payload.get('institution') or '').strip()
    content = str(payload.get('content') or '').strip()
    if not institution:
        return _error('기관을 입력하세요.')
    if len(institution) > 100:
        return _error('기관은 100자 이내로 입력하세요.')
    if not content:
        return _error('서비스 내용을 입력하세요.')
    case.institution = institution
    case.title = content[:200]
    case.save(update_fields=['institution', 'title', 'updated_at'])
    return JsonResponse({'success': True, 'record': _service_payload(case, request.user, ids)})


@require_POST
def meeting_service_reorder_api(request):
    """화면에서 끌어 놓은 순서를 저장한다. 볼 수 없는 기록의 id 는 무시한다."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    payload = _parse_payload(request)
    if payload is None or not isinstance(payload.get('ids'), list) or not payload.get('week'):
        return _error('잘못된 요청 형식입니다.')
    try:
        ordered_ids = [int(value) for value in payload['ids']]
    except (TypeError, ValueError):
        return _error('잘못된 요청 형식입니다.')

    profile = get_user_profile(request.user)
    scope_users, _selected = _dashboard_scope_users(request, profile)
    week_start = _parse_week_start(str(payload['week']), timezone.localdate())
    cases = {case.id: case for case in _week_cases(request, scope_users, week_start).filter(pk__in=ordered_ids)}
    changed = []
    for position, case_id in enumerate(ordered_ids, start=1):
        case = cases.get(case_id)
        if case is not None:
            case.meeting_position = position
            changed.append(case)
    with transaction.atomic():
        ServiceCase.objects.bulk_update(changed, ['meeting_position'])
    return JsonResponse({'success': True})
