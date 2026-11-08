"""아침회의 모드 API — 지난주에 무엇이 달라졌고 오늘 무엇을 정할지 한 번에.

파이프라인(현재 상태)과 파이프라인 시트(활동 목록)를 다시 보여주는 게 아니라, 회의 흐름인
다섯 장면에 맞춰 묶는다: 요약 → 움직임 → 지난주 약속 → 막힌 건 → 이번 주 계획.

숫자 원칙: 매출은 대시보드와 같은 헬퍼·같은 범위(`delivered_revenue_rows`,
`_dashboard_scope_users`), 주 경계와 견적 금액은 파이프라인 시트와 같은 규칙을 쓴다.
회의 화면 숫자가 다른 화면과 갈라지면 발표 자료로 쓸 수 없기 때문이다.
"""

import hashlib
import json
import logging
from datetime import date, datetime, time, timedelta

from django.db.models import Prefetch, Q
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
    _activity_body,
    _parse_week_start,
    _schedule_amount,
    _scope_payload,
    _week_options,
    _weekly_rows,
    week_bounds,
)
from reporting.funnel_views import (
    _history_pricing_date,
    _money_int,
    _pipeline_account_followup,
    _pipeline_account_stage,
    _pipeline_contact_label,
    _select_pipeline_pricing,
    pipeline_followups_queryset,
)
from reporting.models import DeliveryItem, FollowUp, History, MeetingActionItem, PipelineNoteBrief, PipelineStageChange, Schedule
from reporting.views import (
    _api_login_required_response,
    _dashboard_scope_users,
    _user_display_name,
    delivered_revenue_rows,
    get_user_profile,
)

logger = logging.getLogger(__name__)

# 뒤로 갔는지 판단하는 순서. 실주는 순서 밖이라 따로 분류한다.
STAGE_RANK = {'potential': 0, 'contact': 1, 'quote': 2, 'negotiation': 3, 'won': 4}
OPEN_STAGES = ('contact', 'quote', 'negotiation')

STALE_DAYS = 14          # 다음 일정 없이 이만큼 조용하면 "막힌 건"으로 본다
OBSTACLE_WINDOW_DAYS = 30  # 이보다 오래된 장애물 기록은 이미 지난 얘기로 본다
BLOCKED_LIMIT = 3        # 회의에서 다룰 건 수. 많이 띄우면 아무것도 결정하지 못한다
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
        'totalActivities': sum(row['activityCount'] for row in sheet_rows),
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
    changes = (
        PipelineStageChange.objects
        .filter(followup__user__in=scope_users, followup__pipeline_hidden=False, changed_at__gte=start, changed_at__lt=end)
        .select_related('followup', 'followup__company', 'followup__department', 'followup__user')
        .order_by('changed_at', 'id')
    )
    for change in changes:
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
        payload[key] = {'count': len(rows), 'items': rows[:MOVEMENT_LIMIT]}

    first_record = PipelineStageChange.objects.order_by('changed_at').values_list('changed_at', flat=True).first()
    tracking_since = timezone.localtime(first_record).date() if first_record else None
    return {
        **payload,
        'trackingSince': tracking_since.isoformat() if tracking_since else None,
        # 기록을 켜기 전 주는 "변화 없음"이 아니라 "알 수 없음"이다. 화면이 구분해서 말해야 한다.
        'tracked': bool(tracking_since and tracking_since <= week_start + timedelta(days=6)),
    }


# ------------------------------------------------------------ 3. 지난주 약속

def _action_item_payload(item, viewer, scope_user_ids, today):
    followup = item.followup
    return {
        'id': item.id,
        'title': item.title,
        'ownerId': item.owner_id,
        'owner': _user_display_name(item.owner),
        'dueDate': item.due_date.isoformat() if item.due_date else None,
        'overdue': bool(item.status == MeetingActionItem.STATUS_OPEN and item.due_date and item.due_date < today),
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
        .filter(owner__in=scope_users)
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


# -------------------------------------------------------------- 4. 막힌 건

def _blocked(cards, today):
    rows = []
    obstacle_since = today - timedelta(days=OBSTACLE_WINDOW_DAYS)
    for followup, stage, amount in cards:
        if stage not in OPEN_STAGES:
            continue
        histories = getattr(followup, 'all_histories', [])
        dates = [d for d in (_history_pricing_date(h) for h in histories) if d and d <= today]
        dates += [s.visit_date for s in getattr(followup, 'recent_schedules', []) if s.visit_date <= today]
        last_activity = max(dates) if dates else timezone.localtime(followup.created_at).date()
        idle_days = (today - last_activity).days
        has_next_step = bool(getattr(followup, 'upcoming_schedules', []))

        obstacle_note = next(
            (
                h for h in histories
                if (h.meeting_obstacles or '').strip()
                and (_history_pricing_date(h) or date.min) >= obstacle_since
            ),
            None,
        )
        stale = not has_next_step and idle_days >= STALE_DAYS
        if not obstacle_note and not stale:
            continue

        rows.append({
            'followupId': followup.id,
            'customer': _pipeline_contact_label(followup) or _customer_label(followup),
            'company': _company_label(followup),
            'owner': _user_display_name(followup.user),
            'ownerId': followup.user_id,
            'stage': stage,
            'stageLabel': STAGE_LABELS.get(stage, stage),
            'amount': amount,
            'idleDays': idle_days,
            'hasNextStep': has_next_step,
            'obstacle': (obstacle_note.meeting_obstacles or '').strip().split('\n')[0][:160] if obstacle_note else '',
            'noteId': histories[0].id if histories else None,
            'href': f'/customers/{followup.id}/',
        })
    rows.sort(key=lambda row: (-row['amount'], -row['idleDays']))
    return {'total': len(rows), 'items': rows[:BLOCKED_LIMIT]}


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
        'canUseAi': bool(profile.can_use_ai),
        'summary': _summary(request, scope_users, today, week_start, week_end),
        'movement': _movement(scope_users, week_start, cards),
        'promises': {
            'actionItems': _action_items(request, scope_users, today, week_start),
            'nextActions': _next_action_promises(scope_users, today, week_start),
        },
        'blocked': _blocked(cards, today),
        'plan': _plan(scope_users, plan_start),
        'form': {
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

    profile = get_user_profile(request.user)
    scope_users, _selected = _dashboard_scope_users(request, profile)
    try:
        owner = scope_users.filter(pk=int(payload.get('ownerId') or request.user.id)).first()
    except (TypeError, ValueError):
        owner = None
    if owner is None:
        return _error('담당자를 다시 선택하세요.')

    due_date = None
    if payload.get('dueDate'):
        try:
            due_date = date.fromisoformat(str(payload['dueDate']))
        except ValueError:
            return _error('기한 형식이 올바르지 않습니다.')

    followup = None
    if payload.get('followupId'):
        try:
            followup = FollowUp.objects.filter(user__in=scope_users, pk=int(payload['followupId'])).first()
        except (TypeError, ValueError):
            followup = None
        if followup is None:
            return _error('고객을 다시 선택하세요.')

    item = MeetingActionItem.objects.create(
        owner=owner, followup=followup, title=title, due_date=due_date, created_by=request.user,
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
def meeting_action_delete_api(request, item_id):
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    item, error, _ids = _editable_item_or_error(request, item_id)
    if error:
        return error
    item.delete()
    return JsonResponse({'success': True})


# ------------------------------------------------------------- AI 한 줄 요약

BRIEF_NOTE_LIMIT = 5
BRIEF_SOURCE_CHARS = 4000
BRIEF_SYSTEM_PROMPT = (
    "당신은 B2B 영업 회의를 돕는 비서입니다. 영업노트를 읽고 회의에서 바로 말할 수 있게 요약합니다. "
    "노트에 없는 사실을 만들지 마세요. 해당 내용이 노트에 없으면 빈 문자열로 두세요. "
    '각 항목은 40자 이내의 한국어 한 문장으로, JSON 으로만 답하세요: '
    '{"situation": "현재 상황", "blocker": "막힌 점", "next_step": "다음 할 일"}'
)


def _note_source_text(note):
    parts = [
        ('내용', _activity_body(note)),
        ('장애물', note.meeting_obstacles),
        ('다음 액션', note.next_action or note.meeting_next_action),
    ]
    return '\n'.join(f'[{label}] {text.strip()}' for label, text in parts if (text or '').strip())[:BRIEF_SOURCE_CHARS]


def _brief_payload(brief):
    return {'situation': brief.situation, 'blocker': brief.blocker, 'nextStep': brief.next_step}


def _generate_brief(note, source, content_hash):
    from ai_chat.services import create_openai_chat_completion, get_openai_client, get_standard_openai_model

    response = create_openai_chat_completion(
        get_openai_client(),
        'pipeline_meeting_brief',
        get_standard_openai_model(),
        [
            {'role': 'system', 'content': BRIEF_SYSTEM_PROMPT},
            {'role': 'user', 'content': source},
        ],
        response_format={'type': 'json_object'},
        temperature=0.2,
        max_tokens=300,
    )
    parsed = json.loads(response.choices[0].message.content or '{}')
    brief, _created = PipelineNoteBrief.objects.update_or_create(
        history=note,
        defaults={
            'content_hash': content_hash,
            'situation': str(parsed.get('situation') or '').strip()[:200],
            'blocker': str(parsed.get('blocker') or '').strip()[:200],
            'next_step': str(parsed.get('next_step') or '').strip()[:200],
        },
    )
    return brief


@require_POST
def meeting_briefs_api(request):
    """막힌 건의 최근 노트를 한 줄로 요약한다. 실패한 건은 빠지고 화면은 원문 첫 줄을 쓴다."""
    auth_response = _api_login_required_response(request)
    if auth_response:
        return auth_response
    profile = get_user_profile(request.user)
    if not profile.can_use_ai:
        return _error('AI 기능 사용 권한이 없습니다.', status=403)
    payload = _parse_payload(request)
    if payload is None or not isinstance(payload.get('noteIds'), list):
        return _error('잘못된 요청 형식입니다.')
    try:
        note_ids = [int(value) for value in payload['noteIds']][:BRIEF_NOTE_LIMIT]
    except (TypeError, ValueError):
        return _error('잘못된 요청 형식입니다.')

    scope_users, _selected = _dashboard_scope_users(request, profile)
    briefs = {}
    notes = History.objects.filter(pk__in=note_ids, user__in=scope_users).select_related('meeting_brief')
    for note in notes:
        source = _note_source_text(note)
        if not source:
            continue
        content_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()
        cached = getattr(note, 'meeting_brief', None)
        if cached and cached.content_hash == content_hash:
            briefs[str(note.id)] = _brief_payload(cached)
            continue
        try:
            briefs[str(note.id)] = _brief_payload(_generate_brief(note, source, content_hash))
        except Exception:
            logger.exception('Failed to generate meeting brief for note %s', note.id)
    return JsonResponse({'success': True, 'briefs': briefs})
