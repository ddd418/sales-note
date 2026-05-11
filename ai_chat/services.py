"""
AI 부서 분석 서비스
부서별 6개월 미팅 종합 분석 + 견적/납품 패턴 분석
"""
import json
import os
import logging
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_openai_client():
    """OpenAI 클라이언트 생성"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


# ================================================
# 데이터 수집
# ================================================

def gather_meeting_data(department, user, months=6):
    """부서 전체의 최근 N개월 미팅 데이터 수집"""
    from reporting.models import History, FollowUp

    cutoff = timezone.now().date() - timedelta(days=months * 30)

    followups = FollowUp.objects.filter(
        department=department
    )

    meetings = History.objects.filter(
        followup__in=followups,
        action_type='customer_meeting',
    ).filter(
        created_at__date__gte=cutoff
    ).select_related(
        'followup',
        'followup__user',
    ).order_by('-created_at')

    meeting_list = []
    for m in meetings:
        entry = {
            'date': (m.meeting_date or m.created_at.date()).strftime('%Y-%m-%d'),
            'customer': m.followup.customer_name if m.followup else '미정',
        }
        owner = getattr(m.followup, 'user', None) if m.followup else None
        if owner:
            entry['owner'] = owner.get_full_name() or owner.username
        parts = []
        if m.meeting_situation:
            parts.append(f"[상황] {m.meeting_situation}")
        if m.meeting_researcher_quote:
            parts.append(f"[연구원 발언] {m.meeting_researcher_quote}")
        if m.meeting_confirmed_facts:
            parts.append(f"[확인된 사실] {m.meeting_confirmed_facts}")
        if m.meeting_obstacles:
            parts.append(f"[장애물] {m.meeting_obstacles}")
        if m.meeting_next_action:
            parts.append(f"[다음 액션] {m.meeting_next_action}")
        if not parts and m.content:
            parts.append(m.content)
        entry['content'] = '\n'.join(parts)
        meeting_list.append(entry)

    return meeting_list


def _money_to_int(value):
    if value is None:
        return 0
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return 0


def _delivery_item_total_value(item):
    if item.total_price is not None:
        return Decimal(str(item.total_price))
    if item.unit_price is not None and item.quantity:
        return Decimal(str(item.unit_price)) * Decimal(str(item.quantity)) * Decimal('1.1')
    return None


def _delivery_item_name(item):
    product = getattr(item, 'product', None)
    if product and getattr(product, 'product_code', None):
        return product.product_code
    return getattr(item, 'item_name', '') or '미정'


def _delivery_items_payload(items, amount_key='total_price'):
    payload = []
    total = Decimal('0')
    has_amount = False
    for item in items:
        item_total = _delivery_item_total_value(item)
        if item_total is not None:
            total += item_total
            has_amount = True
        payload.append({
            'product': _delivery_item_name(item),
            'quantity': item.quantity or 0,
            'unit_price': _money_to_int(item.unit_price),
            amount_key: _money_to_int(item_total),
        })
    return payload, total, has_amount


def _quote_items_payload(items):
    payload = []
    for item in items:
        product = getattr(item, 'product', None)
        payload.append({
            'product': product.product_code if product else '미정',
            'quantity': item.quantity,
            'unit_price': _money_to_int(item.unit_price),
            'subtotal': _money_to_int(item.subtotal),
        })
    return payload


def _quote_delivery_items_text(items):
    labels = []
    for item in items:
        amount = item.get('subtotal')
        if amount is None:
            amount = item.get('total_price')
        amount_label = f", {int(amount):,}원" if amount else ''
        labels.append(f"{item.get('product') or '미정'}({item.get('quantity') or 0}개{amount_label})")
    return ', '.join(labels)


def _empty_quote_delivery_data():
    return {
        'quotes': [],
        'deliveries': [],
        'summary': {
            'total_quotes': 0,
            'converted_quotes': 0,
            'conversion_rate': 0,
            'total_deliveries': 0,
            'total_quote_amount': 0,
            'total_delivery_amount': 0,
            'avg_delivery_interval_days': None,
            'product_stats': {},
        }
    }


def _gather_quote_delivery_data_for_followup_ids(followup_ids, user):
    """견적/납품 관련 모델과 일정 품목 데이터를 하나의 AI 입력으로 통합한다."""
    from reporting.models import Quote, History, Schedule

    followup_ids = [followup_id for followup_id in dict.fromkeys(followup_ids or []) if followup_id]
    if not followup_ids:
        return _empty_quote_delivery_data()

    quote_list = []
    delivery_list = []

    quotes = Quote.objects.filter(
        user=user,
        followup_id__in=followup_ids,
    ).select_related(
        'followup',
        'schedule',
    ).prefetch_related(
        'items__product',
        'schedule__delivery_items_set__product',
    ).order_by('-quote_date', '-created_at')

    quote_schedule_ids = set()
    for q in quotes:
        if q.schedule_id:
            quote_schedule_ids.add(q.schedule_id)

        items = _quote_items_payload(q.items.all())
        schedule_items = []
        schedule_total = Decimal('0')
        schedule_has_amount = False
        if q.schedule_id and q.schedule:
            schedule_items, schedule_total, schedule_has_amount = _delivery_items_payload(
                q.schedule.delivery_items_set.all(),
                amount_key='subtotal',
            )
        if not items and schedule_items:
            items = schedule_items

        total_amount = _money_to_int(q.total_amount)
        if total_amount == 0 and schedule_has_amount:
            total_amount = _money_to_int(schedule_total)

        quote_list.append({
            'quote_number': q.quote_number,
            'date': q.quote_date.strftime('%Y-%m-%d') if q.quote_date else '',
            'customer': q.followup.customer_name if q.followup else '미정',
            'stage': q.get_stage_display(),
            'total_amount': total_amount,
            'converted_to_delivery': q.converted_to_delivery,
            'items': items,
            'source': '견적서',
            'schedule_id': q.schedule_id,
            'notes': q.notes or q.customer_feedback or '',
        })

    quote_histories = History.objects.filter(
        user=user,
        followup_id__in=followup_ids,
        action_type='quote',
        parent_history__isnull=True,
    ).select_related(
        'followup',
        'schedule',
    ).prefetch_related(
        'delivery_items_set__product',
        'schedule__delivery_items_set__product',
    ).order_by('-created_at')

    quote_history_schedule_ids = set()
    for history in quote_histories:
        if history.schedule_id:
            quote_history_schedule_ids.add(history.schedule_id)

        items, item_total, has_item_amount = _delivery_items_payload(
            history.delivery_items_set.all(),
            amount_key='subtotal',
        )
        if not items and history.schedule_id and history.schedule:
            items, item_total, has_item_amount = _delivery_items_payload(
                history.schedule.delivery_items_set.all(),
                amount_key='subtotal',
            )

        quote_date = history.meeting_date or history.created_at.date()
        quote_list.append({
            'quote_number': f"활동-{history.pk}",
            'date': quote_date.strftime('%Y-%m-%d') if quote_date else '',
            'customer': history.followup.customer_name if history.followup else '미정',
            'stage': history.get_action_type_display(),
            'total_amount': _money_to_int(item_total) if has_item_amount else 0,
            'converted_to_delivery': False,
            'items': items,
            'source': '견적 활동',
            'schedule_id': history.schedule_id,
            'notes': history.content or '',
        })

    excluded_quote_schedule_ids = quote_schedule_ids | quote_history_schedule_ids
    quote_schedules = Schedule.objects.filter(
        user=user,
        followup_id__in=followup_ids,
        activity_type='quote',
    ).exclude(
        status='cancelled',
    ).exclude(
        id__in=excluded_quote_schedule_ids,
    ).select_related(
        'followup',
    ).prefetch_related(
        'delivery_items_set__product',
    ).order_by('-visit_date', '-visit_time')

    for schedule in quote_schedules:
        items, item_total, has_item_amount = _delivery_items_payload(
            schedule.delivery_items_set.all(),
            amount_key='subtotal',
        )
        total_amount = item_total if has_item_amount else schedule.expected_revenue
        quote_list.append({
            'quote_number': f"견적일정-{schedule.pk}",
            'date': schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '',
            'customer': schedule.followup.customer_name if schedule.followup else '미정',
            'stage': schedule.get_status_display(),
            'total_amount': _money_to_int(total_amount),
            'converted_to_delivery': bool(schedule.purchase_confirmed),
            'items': items,
            'source': '견적 일정',
            'schedule_id': schedule.pk,
            'notes': schedule.notes or '',
        })

    delivery_histories = History.objects.filter(
        user=user,
        followup_id__in=followup_ids,
        action_type='delivery_schedule',
        parent_history__isnull=True,
    ).select_related(
        'followup',
        'schedule',
    ).prefetch_related(
        'delivery_items_set__product',
        'schedule__delivery_items_set__product',
    ).order_by('-created_at')

    delivery_history_schedule_ids = set()
    for history in delivery_histories:
        if history.schedule_id:
            delivery_history_schedule_ids.add(history.schedule_id)

        items, item_total, has_item_amount = _delivery_items_payload(
            history.delivery_items_set.all(),
            amount_key='total_price',
        )
        if not items and history.schedule_id and history.schedule:
            items, item_total, has_item_amount = _delivery_items_payload(
                history.schedule.delivery_items_set.all(),
                amount_key='total_price',
            )

        amount = history.delivery_amount
        if amount is None and has_item_amount:
            amount = item_total
        if amount is None and history.schedule_id and history.schedule:
            amount = history.schedule.expected_revenue

        delivery_date = history.delivery_date or history.created_at.date()
        delivery_list.append({
            'date': delivery_date.strftime('%Y-%m-%d') if delivery_date else '',
            'customer': history.followup.customer_name if history.followup else '미정',
            'amount': _money_to_int(amount),
            'items': items,
            'source': '납품 활동',
            'schedule_id': history.schedule_id,
            'notes': history.content or '',
        })

    delivery_schedules = Schedule.objects.filter(
        user=user,
        followup_id__in=followup_ids,
        activity_type='delivery',
    ).exclude(
        status='cancelled',
    ).exclude(
        id__in=delivery_history_schedule_ids,
    ).select_related(
        'followup',
    ).prefetch_related(
        'delivery_items_set__product',
    ).order_by('-visit_date', '-visit_time')

    for schedule in delivery_schedules:
        items, item_total, has_item_amount = _delivery_items_payload(
            schedule.delivery_items_set.all(),
            amount_key='total_price',
        )
        amount = item_total if has_item_amount else schedule.expected_revenue
        delivery_list.append({
            'date': schedule.visit_date.strftime('%Y-%m-%d') if schedule.visit_date else '',
            'customer': schedule.followup.customer_name if schedule.followup else '미정',
            'amount': _money_to_int(amount),
            'items': items,
            'source': '납품 일정',
            'schedule_id': schedule.pk,
            'notes': schedule.notes or '',
        })

    quote_list.sort(key=lambda item: item.get('date') or '', reverse=True)
    delivery_list.sort(key=lambda item: item.get('date') or '', reverse=True)

    total_quotes = len(quote_list)
    converted_quotes = sum(1 for q in quote_list if q['converted_to_delivery'])
    conversion_rate = round(converted_quotes / total_quotes * 100, 1) if total_quotes > 0 else 0

    delivery_dates = sorted([d['date'] for d in delivery_list if d['date']])
    avg_delivery_interval_days = None
    if len(delivery_dates) >= 2:
        from datetime import datetime
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in delivery_dates]
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        intervals = [abs(iv) for iv in intervals if iv != 0]
        if intervals:
            avg_delivery_interval_days = round(sum(intervals) / len(intervals))

    product_stats = {}
    for q in quote_list:
        for item in q['items']:
            name = item['product']
            if name not in product_stats:
                product_stats[name] = {'quoted': 0, 'delivered': 0, 'quote_amount': 0, 'delivery_amount': 0}
            product_stats[name]['quoted'] += 1
            product_stats[name]['quote_amount'] += item.get('subtotal', 0) or 0
    for d in delivery_list:
        for item in d['items']:
            name = item['product']
            if name not in product_stats:
                product_stats[name] = {'quoted': 0, 'delivered': 0, 'quote_amount': 0, 'delivery_amount': 0}
            product_stats[name]['delivered'] += 1
            product_stats[name]['delivery_amount'] += item.get('total_price', 0) or 0

    return {
        'quotes': quote_list,
        'deliveries': delivery_list,
        'summary': {
            'total_quotes': total_quotes,
            'converted_quotes': converted_quotes,
            'conversion_rate': conversion_rate,
            'total_deliveries': len(delivery_list),
            'total_quote_amount': sum(q.get('total_amount') or 0 for q in quote_list),
            'total_delivery_amount': sum(d.get('amount') or 0 for d in delivery_list),
            'avg_delivery_interval_days': avg_delivery_interval_days,
            'product_stats': product_stats,
        }
    }


def gather_quote_delivery_data(department, user):
    """부서의 견적/납품 데이터 수집 및 패턴 분석"""
    from reporting.models import FollowUp

    followups = FollowUp.objects.filter(user=user, department=department)
    followup_ids = list(followups.values_list('id', flat=True))
    return _gather_quote_delivery_data_for_followup_ids(followup_ids, user)


def _email_log_datetime(email):
    return email.received_at or email.sent_at or email.created_at


def _email_log_address(email, primary, fallback):
    return _compact_memory_text(getattr(email, primary, '') or getattr(email, fallback, ''), 120)


def _email_log_body_text(email, limit=700):
    body = email.body or ''
    if not body and email.body_html:
        body = re.sub(r'<[^>]+>', ' ', email.body_html)
    return _compact_memory_text(body, limit)


def _email_log_is_inbound(email):
    return email.email_type == 'received' or (email.email_type != 'sent' and not email.is_sent)


def gather_email_data_for_followups(followups, user, months=6, limit=20):
    """고객과 주고받은 메일을 AI 입력용으로 수집한다.

    기존 EmailLog의 FollowUp/Schedule 연결만 사용하며, 고객이 보낸 수신 메일을 우선한다.
    """
    from django.db.models import Q
    from reporting.models import EmailLog

    followup_list = list(followups)
    followup_ids = [followup.id for followup in followup_list if followup and followup.id]
    if not followup_ids:
        return {
            'emails': [],
            'summary': {
                'total': 0,
                'inbound_count': 0,
                'outbound_count': 0,
            },
        }

    cutoff_dt = timezone.now() - timedelta(days=months * 30)
    qs = EmailLog.objects.filter(
        Q(followup_id__in=followup_ids)
        | Q(schedule__followup_id__in=followup_ids)
    ).filter(
        Q(received_at__gte=cutoff_dt)
        | Q(sent_at__gte=cutoff_dt)
        | Q(created_at__gte=cutoff_dt)
    ).filter(
        Q(followup__user=user)
        | Q(schedule__followup__user=user)
        | Q(user=user)
        | Q(sender=user)
    ).exclude(
        is_trashed=True,
    ).select_related(
        'followup',
        'schedule',
        'schedule__followup',
    ).distinct().order_by('-received_at', '-sent_at', '-created_at')[:max(limit * 3, limit)]

    rows = []
    for email in qs:
        linked_followup = email.followup or (email.schedule.followup if email.schedule_id and email.schedule else None)
        if not linked_followup:
            continue
        occurred_at = _email_log_datetime(email)
        inbound = _email_log_is_inbound(email)
        body = _email_log_body_text(email)
        subject = _compact_memory_text(email.subject, 180)
        if not subject and not body:
            continue
        rows.append({
            'date': timezone.localtime(occurred_at).strftime('%Y-%m-%d') if occurred_at else '',
            'customer': linked_followup.customer_name or '고객명 미정',
            'followup_id': linked_followup.id,
            'direction': 'inbound' if inbound else 'outbound',
            'direction_label': '고객→영업' if inbound else '영업→고객',
            'subject': subject or '(제목 없음)',
            'from_email': _email_log_address(email, 'from_email', 'sender_email'),
            'to_email': _email_log_address(email, 'to_email', 'recipient_email'),
            'body': body,
            'thread_id': _compact_memory_text(email.thread_id or email.gmail_thread_id, 120),
        })

    inbound_rows = [row for row in rows if row['direction'] == 'inbound']
    outbound_rows = [row for row in rows if row['direction'] != 'inbound']
    selected_inbound = inbound_rows[:limit]
    selected = (selected_inbound + outbound_rows[:max(limit - len(selected_inbound), 0)])[:limit]
    selected.sort(key=lambda row: (row['date'] or ''), reverse=True)

    return {
        'emails': selected,
        'summary': {
            'total': len(selected),
            'inbound_count': len([row for row in selected if row['direction'] == 'inbound']),
            'outbound_count': len([row for row in selected if row['direction'] != 'inbound']),
        },
    }


def gather_email_data(department, user, months=6, limit=20):
    """부서 소속 고객과 주고받은 최근 메일 수집."""
    from reporting.models import FollowUp

    followups = FollowUp.objects.filter(user=user, department=department)
    return gather_email_data_for_followups(followups, user, months=months, limit=limit)


def format_email_context_for_prompt(email_data):
    summary = email_data.get('summary') or {}
    emails = email_data.get('emails') or []
    lines = [
        f"\n━━━ 고객 메일/답장 컨텍스트 ({summary.get('total', len(emails))}건, 고객 수신 {summary.get('inbound_count', 0)}건) ━━━",
        "고객→영업 수신 메일은 고객이 직접 보낸 최신 의도/장애물/요청이므로 PainPoint와 다음 액션의 우선 근거로 사용하라.",
    ]
    if not emails:
        lines.append("(연결된 최근 고객 메일 없음)")
        return lines

    for i, email in enumerate(emails, 1):
        lines.append(
            f"\n[메일 #{i}] {email['date']} | {email['direction_label']} | {email['customer']} | 제목: {email['subject']}"
        )
        if email.get('from_email') or email.get('to_email'):
            lines.append(f"발신/수신: {email.get('from_email') or '-'} → {email.get('to_email') or '-'}")
        if email.get('body'):
            lines.append(f"본문 요약: {email['body']}")
    return lines


def _count_by_customer(rows, key='customer'):
    counts = {}
    for row in rows or []:
        name = row.get(key) or '고객명 미정'
        counts[name] = counts.get(name, 0) + 1
    return counts


def _followup_stage_context(followup, quote_count=0, meeting_count=0, inbound_email_count=0, outbound_email_count=0):
    stage = followup.pipeline_stage or 'potential'
    stage_label = followup.get_pipeline_stage_display()
    if stage == 'won':
        context_type = 'won_locked'
        context_label = '락인/수주 고객'
        focus = '수주 이후 납품 일정, 후속 발주, 재구매, 사용 확대, 이탈 방지 액션을 우선 보고'
    elif stage in ('quote', 'negotiation') or quote_count > 0:
        context_type = 'quote'
        context_label = '견적 고객'
        focus = '견적 내용, 미팅 내용, 고객 메일 답장을 함께 분석해 견적 수정/조건 확인/의사결정 일정 액션을 보고'
    elif meeting_count > 0:
        context_type = 'meeting_only'
        context_label = '미팅만 진행 고객'
        focus = '미팅 내용과 고객 메일 답장을 분석해 요구사항 정리, 자료 전달, 다음 미팅 또는 견적화 액션을 보고'
    else:
        context_type = 'early'
        context_label = '초기/잠재 고객'
        focus = '첫 접촉 목적, 관심 제품, 다음 미팅 필요 여부를 확인'

    return {
        'followup_id': followup.id,
        'customer': followup.customer_name or '고객명 미정',
        'pipeline_stage': stage,
        'pipeline_stage_label': stage_label,
        'context_type': context_type,
        'context_label': context_label,
        'quote_count': quote_count,
        'meeting_count': meeting_count,
        'inbound_email_count': inbound_email_count,
        'outbound_email_count': outbound_email_count,
        'analysis_focus': focus,
    }


def build_customer_stage_context(followups, meetings=None, qd_data=None, email_data=None, limit=12):
    """고객별 단계에 맞는 AI 다음 액션 기준을 만든다."""
    followup_list = list(followups)
    meeting_counts = _count_by_customer(meetings or [])
    quote_counts = _count_by_customer((qd_data or {}).get('quotes') or [])

    inbound_email_counts = {}
    outbound_email_counts = {}
    for email in (email_data or {}).get('emails') or []:
        name = email.get('customer') or '고객명 미정'
        if email.get('direction') == 'inbound':
            inbound_email_counts[name] = inbound_email_counts.get(name, 0) + 1
        else:
            outbound_email_counts[name] = outbound_email_counts.get(name, 0) + 1

    contexts = []
    for followup in followup_list:
        name = followup.customer_name or '고객명 미정'
        contexts.append(_followup_stage_context(
            followup,
            quote_count=quote_counts.get(name, 0),
            meeting_count=meeting_counts.get(name, 0),
            inbound_email_count=inbound_email_counts.get(name, 0),
            outbound_email_count=outbound_email_counts.get(name, 0),
        ))

    priority = {'won_locked': 0, 'quote': 1, 'meeting_only': 2, 'early': 3}
    contexts.sort(key=lambda item: (priority.get(item['context_type'], 9), item['customer']))
    return contexts[:limit]


def build_single_followup_stage_context(followup, data):
    emails = data.get('emails') or []
    inbound_count = len([email for email in emails if email.get('direction') == 'inbound'])
    outbound_count = len(emails) - inbound_count
    return _followup_stage_context(
        followup,
        quote_count=len(data.get('quotes') or []),
        meeting_count=len(data.get('meetings') or []),
        inbound_email_count=inbound_count,
        outbound_email_count=outbound_count,
    )


def format_customer_stage_context_for_prompt(stage_contexts):
    lines = [
        f"\n━━━ 고객 단계별 다음 액션 기준 ({len(stage_contexts)}명) ━━━",
        "AI는 각 고객의 현재 단계에 맞춰 다음 액션을 반드시 보고해야 한다.",
        "- 락인/수주 고객: 수주 관련 후속 납품, 재구매, 추가 발주, 리텐션 액션을 만든다.",
        "- 견적 고객: 견적 내용, 미팅 내용, 고객 메일 답장을 함께 분석해 다음 액션을 만든다.",
        "- 미팅만 진행 고객: 미팅 내용과 고객 메일 답장을 분석해 자료 전달, 다음 미팅, 견적화 액션을 만든다.",
        "- 분석 후에는 검증 메모리의 메모 내용을 읽고 AI가 직접 판단해 다음 액션에 반영한다.",
    ]
    if not stage_contexts:
        lines.append("(단계별 고객 없음)")
        return lines

    for item in stage_contexts:
        lines.append(
            f"- {item['customer']} | {item['context_label']}({item['pipeline_stage_label']}) | "
            f"미팅 {item['meeting_count']}건, 견적 {item['quote_count']}건, 고객메일 {item['inbound_email_count']}건 | "
            f"분석 기준: {item['analysis_focus']}"
        )
    return lines


def build_stage_next_actions_from_context(stage_contexts, verification_memory=None, limit=6):
    actions = []
    has_verification = bool(verification_memory)
    verification_note = ' 검증 메모리의 메모 내용을 읽고 AI가 직접 판단해 반영해야 합니다.' if has_verification else ''

    for item in stage_contexts or []:
        label = item.get('context_label') or '고객'
        customer = item.get('customer') or '고객'
        counts = (
            f"미팅 {item.get('meeting_count', 0)}건, 견적 {item.get('quote_count', 0)}건, "
            f"고객 수신 메일 {item.get('inbound_email_count', 0)}건"
        )
        if item.get('context_type') == 'won_locked':
            action = f"{customer} 수주/락인 후속으로 납품 일정, 추가 발주 가능 품목, 재구매 시점을 확인하세요."
        elif item.get('context_type') == 'quote':
            action = f"{customer} 견적 건은 견적 내용, 미팅 이슈, 고객 메일 답장을 기준으로 수정 견적/조건 조정/결정 일정을 확인하세요."
        elif item.get('context_type') == 'meeting_only':
            action = f"{customer} 미팅 후속으로 요구사항 정리, 자료 전달, 다음 미팅 또는 견적 전환 여부를 확인하세요."
        else:
            action = f"{customer} 초기 접촉 목적과 관심 제품을 확인하고 다음 미팅 필요 여부를 정리하세요."
        actions.append({
            'action': action,
            'priority': 'high' if item.get('context_type') in ('won_locked', 'quote') else 'medium',
            'reason': f"고객 단계별 분석 기준: {label}, {counts}.{verification_note}",
        })
        if len(actions) >= limit:
            break
    return actions


def apply_stage_action_context_to_analysis_result(analysis_result, stage_contexts, verification_memory=None):
    if not isinstance(analysis_result, dict):
        return analysis_result

    analysis_result['customer_stage_context'] = stage_contexts or []
    analysis_result['stage_action_guidance'] = [
        {
            'customer': item.get('customer'),
            'context_label': item.get('context_label'),
            'analysis_focus': item.get('analysis_focus'),
        }
        for item in (stage_contexts or [])
    ]

    next_actions = analysis_result.get('next_actions')
    if not isinstance(next_actions, list):
        next_actions = []
    existing = {
        _compact_memory_text(action.get('action'), 220).lower()
        for action in next_actions
        if isinstance(action, dict)
    }
    for action in build_stage_next_actions_from_context(stage_contexts, verification_memory=verification_memory):
        key = _compact_memory_text(action.get('action'), 220).lower()
        if key and key not in existing:
            next_actions.append(action)
            existing.add(key)
    analysis_result['next_actions'] = next_actions[:10]
    return analysis_result


def apply_followup_stage_context_to_analysis_result(analysis_result, stage_context):
    if not isinstance(analysis_result, dict):
        return analysis_result
    if not stage_context:
        return analysis_result

    analysis_result['stage_action_guidance'] = stage_context
    next_actions = analysis_result.get('next_best_actions')
    if not isinstance(next_actions, list):
        next_actions = []

    fallback = build_stage_next_actions_from_context([stage_context])
    existing = {
        _compact_memory_text(action.get('action'), 220).lower()
        for action in next_actions
        if isinstance(action, dict)
    }
    for item in fallback:
        key = _compact_memory_text(item.get('action'), 220).lower()
        if not key or key in existing:
            continue
        next_actions.append({
            'priority': len(next_actions) + 1,
            'action': item['action'],
            'suggested_due': '다음 영업 접점 전',
            'what_to_ask': _followup_stage_question(stage_context),
            'what_to_prepare': _followup_stage_preparation(stage_context),
            'reason': item['reason'],
        })
        existing.add(key)
    analysis_result['next_best_actions'] = next_actions[:8]
    return analysis_result


def _followup_stage_question(stage_context):
    context_type = stage_context.get('context_type')
    if context_type == 'won_locked':
        return '다음 납품/재구매 일정과 추가 발주 가능 품목이 있나요?'
    if context_type == 'quote':
        return '견적 검토 일정, 조정이 필요한 조건, 의사결정 기준은 무엇인가요?'
    if context_type == 'meeting_only':
        return '미팅 후 필요한 자료와 견적 검토 가능 시점은 언제인가요?'
    return '관심 제품과 다음 미팅 필요 여부를 확인할 수 있을까요?'


def _followup_stage_preparation(stage_context):
    context_type = stage_context.get('context_type')
    if context_type == 'won_locked':
        return '납품/사용 이력, 재구매 후보 품목, 추가 발주 제안'
    if context_type == 'quote':
        return '기존 견적서, 수정 조건안, 고객 메일 답장 요약, 미팅 이슈'
    if context_type == 'meeting_only':
        return '미팅 요약, 요청 자료, 견적 초안 또는 샘플 제안'
    return '회사/부서 기본 정보, 관심 제품 질문 리스트'


def gather_prepayment_data(followups):
    """
    팔로우업 목록(queryset)에 대한 선결제 데이터 수집.
    followups: FollowUp queryset (이미 권한 범위 내로 필터링됨)
    """
    from reporting.models import Prepayment
    from datetime import date, timedelta

    prepayments = Prepayment.objects.filter(
        customer__in=followups
    ).select_related('customer').prefetch_related('usages').order_by('-payment_date')

    result = []
    today = date.today()
    stale_threshold = today - timedelta(days=90)

    for p in prepayments:
        usages = p.usages.all().order_by('-used_at')
        usage_list = []
        for u in usages:
            usage_list.append({
                'product': u.product_name,
                'quantity': u.quantity,
                'amount': int(u.amount),
                'remaining_after': int(u.remaining_balance),
                'used_at': u.used_at.strftime('%Y-%m-%d'),
            })
        last_usage = usages.first()
        last_used_date = last_usage.used_at.date() if last_usage else None
        days_since_use = (today - last_used_date).days if last_used_date else None
        is_stalled = (
            p.status == 'active'
            and p.balance > 0
            and (last_used_date is None or last_used_date < stale_threshold)
        )
        result.append({
            'customer': p.customer.customer_name,
            'original_amount': int(p.amount),
            'balance': int(p.balance),
            'used_amount': int(p.amount - p.balance),
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'status': p.status,
            'status_display': p.get_status_display(),
            'payer_name': p.payer_name,
            'last_used_date': last_used_date.strftime('%Y-%m-%d') if last_used_date else None,
            'days_since_last_use': days_since_use,
            'is_stalled': is_stalled,
            'usages': usage_list,
        })

    active = [p for p in result if p['status'] == 'active']
    stalled = [p for p in active if p['is_stalled']]
    return {
        'prepayments': result,
        'summary': {
            'total_count': len(result),
            'active_count': len(active),
            'total_remaining_balance': sum(p['balance'] for p in active),
            'stalled_count': len(stalled),
            'stalled_customers': [p['customer'] for p in stalled],
        }
    }


def _compact_memory_text(value, limit=500):
    """검증 메모리 프롬프트에 넣을 텍스트를 짧고 안정적으로 정리한다."""
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    if len(text) > limit:
        return text[:limit].rstrip() + '...'
    return text


def _verification_memory_key(item):
    category = _compact_memory_text(item.get('category'), 60).lower()
    hypothesis = _compact_memory_text(item.get('hypothesis'), 180).lower()
    question = _compact_memory_text(item.get('verification_question'), 140).lower()
    return '|'.join([category, hypothesis, question])


def _verification_memory_from_card(card):
    raw_status = card.verification_status or 'unverified'
    note = _compact_memory_text(card.verification_note, 700)
    if raw_status == 'unverified' and not note:
        return None
    status = 'checked'

    verified_at = timezone.localtime(card.verified_at).isoformat() if card.verified_at else None
    return {
        'source': 'painpoint_card',
        'card_id': card.id,
        'category': card.category,
        'category_label': card.get_category_display(),
        'hypothesis': _compact_memory_text(card.hypothesis, 500),
        'confidence': card.confidence,
        'confidence_score': card.confidence_score,
        'attribution': card.attribution,
        'verification_question': _compact_memory_text(card.verification_question, 500),
        'verification_status': status,
        'verification_status_label': '검증 메모',
        'verification_note': note,
        'verified_at': verified_at,
        'action_if_yes': _compact_memory_text(card.action_if_yes, 500),
        'action_if_no': _compact_memory_text(card.action_if_no, 500),
    }


def collect_painpoint_verification_memory(analysis, limit=30):
    """이전 PainPoint 검증 결과를 재분석용 장기 메모리로 수집한다."""
    if not analysis or not analysis.pk:
        return []

    memory = []
    seen = set()

    def append(item):
        if not isinstance(item, dict):
            return
        raw_status = _compact_memory_text(
            item.get('verification_status') or item.get('verificationStatus'),
            30,
        )
        note = _compact_memory_text(
            item.get('verification_note') or item.get('verificationNote'),
            700,
        )
        status = 'checked' if raw_status != 'unverified' or note else 'unverified'
        status_label = '검증 메모' if status == 'checked' else '미검증'
        normalized = {
            'source': _compact_memory_text(item.get('source') or 'analysis_data', 80),
            'card_id': item.get('card_id'),
            'category': _compact_memory_text(item.get('category'), 60),
            'category_label': _compact_memory_text(item.get('category_label') or item.get('categoryLabel'), 80),
            'hypothesis': _compact_memory_text(item.get('hypothesis'), 500),
            'confidence': _compact_memory_text(item.get('confidence'), 20),
            'confidence_score': item.get('confidence_score') if item.get('confidence_score') is not None else item.get('confidenceScore'),
            'attribution': _compact_memory_text(item.get('attribution'), 40),
            'verification_question': _compact_memory_text(
                item.get('verification_question') or item.get('verificationQuestion'),
                500,
            ),
            'verification_status': status,
            'verification_status_label': status_label,
            'verification_note': note,
            'verified_at': _compact_memory_text(item.get('verified_at') or item.get('verifiedAt'), 80),
            'action_if_yes': _compact_memory_text(item.get('action_if_yes') or item.get('actionIfYes'), 500),
            'action_if_no': _compact_memory_text(item.get('action_if_no') or item.get('actionIfNo'), 500),
        }
        if not normalized['hypothesis'] and not normalized['verification_note']:
            return
        key = _verification_memory_key(normalized)
        if key in seen:
            return
        seen.add(key)
        memory.append(normalized)

    for card in analysis.painpoint_cards.exclude(
        verification_status='unverified',
    ).order_by('-verified_at', '-created_at')[:limit]:
        item = _verification_memory_from_card(card)
        if item:
            append(item)

    stored_memory = []
    if isinstance(analysis.analysis_data, dict):
        raw_memory = analysis.analysis_data.get('verification_memory', [])
        if isinstance(raw_memory, list):
            stored_memory = raw_memory

    for item in stored_memory:
        append(item)
        if len(memory) >= limit:
            break

    return memory[:limit]


def format_painpoint_verification_memory_for_prompt(memory, limit=20):
    """이전 검증 결과를 GPT가 읽기 쉬운 프롬프트 섹션으로 변환한다."""
    if not memory:
        return []

    lines = [
        f"\n━━━ 기존 PainPoint 검증 메모리 ({min(len(memory), limit)}건) ━━━",
        "아래 내용은 사용자가 이전 분석에서 남긴 검증 메모이며 미팅 기록과 동급의 분석 근거다.",
        "요약, 미팅 인사이트, PainPoint, 다음 액션, missing_info는 반드시 이 검증 메모리를 함께 반영하라.",
        "검증 메모의 상태값으로 의미를 고정하지 말고, 메모 본문만 읽어 AI가 사실 확인, 반박, 대체 원인을 판단하라.",
        "새 PainPoint를 만들 때는 기존 검증 메모에서 한 단계 더 나아간 검증 질문을 만들어라.",
        "예: 승인자 관련 메모가 있으면 다음에는 승인 일정/예산/필요 서류처럼 다음 단계 질문을 만든다. 같은 질문을 그대로 반복하지 않는다.",
    ]

    for index, item in enumerate(memory[:limit], start=1):
        status_label = item.get('verification_status_label') or item.get('verification_status') or '검증됨'
        category_label = item.get('category_label') or item.get('category') or '카테고리 미정'
        hypothesis = item.get('hypothesis') or '가설 없음'
        lines.append(f"{index}. [{status_label}] {category_label}: {hypothesis}")
        if item.get('verification_note'):
            lines.append(f"   - 사용자 검증 메모: {item['verification_note']}")
        if item.get('verification_question'):
            lines.append(f"   - 기존 질문: {item['verification_question']}")
        if item.get('verified_at'):
            lines.append(f"   - 검증일: {item['verified_at']}")

    return lines


def build_verification_insights_from_memory(memory, limit=6):
    """검증 메모리를 분석 결과에 직접 노출할 수 있는 인사이트로 변환한다."""
    insights = []
    for item in memory[:limit]:
        status = 'checked'
        status_label = '검증 메모'
        hypothesis = item.get('hypothesis') or 'PainPoint'
        note = item.get('verification_note') or ''
        question = item.get('verification_question') or ''
        insight = f"사용자 검증 메모가 있는 '{hypothesis}' 가설은 메모 내용을 기준으로 AI가 다시 판단해야 합니다."
        impact = note or "검증 메모 본문을 기준으로 후속 확인과 다음 액션을 판단해야 합니다."
        next_verification = "검증 메모를 기준으로 다음 단계 확인 질문을 구체화하세요."

        insights.append({
            'status': status,
            'status_label': status_label,
            'hypothesis': hypothesis,
            'insight': insight,
            'impact': impact,
            'previous_question': question,
            'next_verification': next_verification,
            'verified_at': item.get('verified_at') or None,
        })

    return insights


def build_verification_summary_from_memory(memory, existing_summary='', limit=3):
    """검증 메모리 핵심을 department_summary에 넣을 짧은 문장으로 만든다."""
    existing_summary = _compact_memory_text(existing_summary, 1400)
    summary_items = []

    for item in memory[:limit]:
        note = _compact_memory_text(item.get('verification_note'), 260)
        hypothesis = _compact_memory_text(item.get('hypothesis'), 160)
        if not note and not hypothesis:
            continue
        if note and note in existing_summary:
            continue

        content = note or hypothesis
        summary_items.append(f"검증 메모: {content}")

    if not summary_items:
        return ''
    return '검증 메모 반영 - ' + '; '.join(summary_items)


def apply_verification_memory_to_analysis_result(analysis_result, verification_memory):
    """
    GPT 응답이 검증 메모리를 빠뜨려도 저장 결과와 React payload에 반영되도록 보정한다.
    GPT가 작성한 요약/액션을 대체하지 않고, 검증 기반 요약/인사이트와 보조 next action을 추가한다.
    """
    if not isinstance(analysis_result, dict):
        return analysis_result

    analysis_result['verification_memory'] = verification_memory
    if not verification_memory:
        analysis_result.setdefault('verification_insights', [])
        return analysis_result

    fallback_insights = build_verification_insights_from_memory(verification_memory)
    summary_appendix = build_verification_summary_from_memory(
        verification_memory,
        analysis_result.get('department_summary') or analysis_result.get('summary') or '',
    )
    if summary_appendix:
        current_summary = _compact_memory_text(analysis_result.get('department_summary'), 1200)
        analysis_result['department_summary'] = (
            f"{current_summary} {summary_appendix}".strip()
            if current_summary else summary_appendix
        )

    existing_insights = analysis_result.get('verification_insights')
    if not isinstance(existing_insights, list):
        existing_insights = []

    existing_keys = {
        _verification_memory_key({
            'category': item.get('category', ''),
            'hypothesis': item.get('hypothesis', ''),
            'verification_question': item.get('previous_question') or item.get('verification_question') or '',
        })
        for item in existing_insights
        if isinstance(item, dict)
    }
    for insight in fallback_insights:
        key = _verification_memory_key({
            'category': '',
            'hypothesis': insight.get('hypothesis'),
            'verification_question': insight.get('previous_question'),
        })
        if key not in existing_keys:
            existing_insights.append(insight)
            existing_keys.add(key)
    analysis_result['verification_insights'] = existing_insights[:8]

    next_actions = analysis_result.get('next_actions')
    if not isinstance(next_actions, list):
        next_actions = []
    action_reasons = ' '.join(
        str(item.get('reason', ''))
        for item in next_actions
        if isinstance(item, dict)
    )
    for insight in fallback_insights[:3]:
        note = insight.get('impact') or ''
        if note and note in action_reasons:
            continue
        next_actions.append({
            'action': insight.get('next_verification') or '검증 메모리 기반 후속 확인',
            'priority': 'medium',
            'reason': f"검증 메모리 반영: {note}",
        })
    analysis_result['next_actions'] = next_actions[:8]

    missing_info = analysis_result.get('missing_info')
    if not isinstance(missing_info, dict):
        missing_info = {}
    questions = missing_info.get('questions')
    if not isinstance(questions, list):
        questions = []
    for insight in fallback_insights:
        next_question = insight.get('next_verification')
        if next_question and next_question not in questions:
            questions.append(next_question)
    missing_info['questions'] = questions[:8]
    missing_info.setdefault('items', [])
    analysis_result['missing_info'] = missing_info

    return analysis_result


# ================================================
# 시스템 프롬프트
# ================================================

SYSTEM_PROMPT = """너는 B2B 연구실 영업 CRM의 "부서 종합 분석" AI다.
영업 담당자가 특정 부서(연구실)에 대한 최근 6개월 미팅 내역 + 견적/납품 데이터를 제공하면,
이를 종합 분석하여 객관적인 PainPoint와 영업 인사이트를 도출한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 규칙 (소설 금지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 입력 데이터에 **명시적으로 적혀있는 내용**만 근거(Evidence)로 사용한다.
2. 입력에 없는 실험, 장비, 상황, 감정을 **절대 추측하거나 만들어내지 않는다**.
3. 추측은 반드시 「사용자 추측」으로 표시하고, 확신도를 Low로 내린다.
4. 근거가 1개도 없는 PainPoint는 **생성하지 않는다**.
5. Evidence 인용 시 반드시 따옴표(「」)로 원문을 짧게 인용하고 날짜를 표시한다.
6. 입력에 "기존 PainPoint 검증 메모리"가 있으면 반드시 기억으로 사용한다.
   - 검증 메모의 상태값으로 의미를 고정하지 말고, 메모 본문을 읽고 AI가 직접 판단한다.
   - 기존 검증 메모와 충돌하는 새 가설은 새 근거가 명확할 때만 제시하고, 왜 달라졌는지 설명한다.
   - 기존 질문을 그대로 반복하지 말고 검증 메모 다음 단계의 질문을 만든다.
7. "기존 PainPoint 검증 메모리"는 미팅 기록과 동급의 입력 근거다.
   - department_summary에는 검증 메모에서 AI가 판단한 핵심 내용을 반영한다.
   - meeting_insights에는 미팅 기록만이 아니라 검증 메모에서 드러난 패턴도 포함한다.
   - next_actions에는 검증 메모 이후 해야 할 다음 확인/자료 준비/의사결정 액션을 포함한다.
   - missing_info.questions에는 이미 물어본 질문을 반복하지 말고, 검증 메모 다음 단계 질문을 넣는다.
8. "고객 메일/답장 컨텍스트"가 있으면 고객이 직접 보낸 고객→영업 수신 메일을 최우선 최신 신호로 사용한다.
   - 메일 답장에 가격, 납기, 조건, 검토 일정, 거절 사유가 있으면 next_actions와 PainPoint에 반영한다.
   - 영업→고객 발신 메일은 맥락 보조로만 사용하고, 고객 의도는 고객→영업 메일에서 우선 판단한다.
9. "고객 단계별 다음 액션 기준"을 반드시 따른다.
   - 락인/수주 고객은 수주 이후 납품, 추가 발주, 재구매, 리텐션, 확장 판매 액션을 보고한다.
   - 견적 고객은 견적 내용, 미팅 내용, 고객 메일 답장을 함께 분석해 수정 견적/조건 확인/의사결정 일정 액션을 보고한다.
   - 미팅만 진행 고객은 미팅 내용과 고객 메일 답장을 분석해 자료 전달, 다음 미팅, 견적화 액션을 보고한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
확신도 기준 (엄격 적용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- **High (70-100)**: 여러 미팅에서 반복 확인된 패턴 + 직접 인용 존재
- **Med (40-69)**: 1-2회 언급 또는 간접 시그널
- **Low (0-39)**: 단일 단서 또는 추측 비중 큼

━━━━━━━━━━━━━━━━━━━━━━━━━━━
PainPoint 카테고리 (고정 8종)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. budget: 예산/가격
2. purchase_process: 결재/구매 프로세스
3. switching_cost: 전환 비용/재고 고착
4. performance: 성능/정확도
5. compatibility: 호환성/사용성
6. delivery: 납기/재고
7. trust: 신뢰/리스크
8. priority: 우선순위/관심

━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 (반드시 JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

```json
{
  "department_summary": "부서(연구실) 전체 상황을 3-5문장으로 요약",

  "meeting_insights": [
    {
      "theme": "반복 발견된 주요 테마/패턴 (한 줄)",
      "details": "구체적 설명 (어떤 미팅에서 어떤 내용이 반복되는지)",
      "frequency": "해당 내용이 등장한 미팅 횟수 또는 비율"
    }
  ],

  "quote_delivery_insights": {
    "conversion_analysis": "견적→납품 전환율 분석 및 의미 해석",
    "delivery_cycle": "납품 주기 패턴 설명 (예: 평균 N일 간격, 특정 시기 집중 등)",
    "product_trends": "제품별 견적/납품 트렌드 분석",
    "stalled_quotes": [
      {
        "quote_info": "전환 안 된 견적 정보",
        "possible_reason": "미팅록 기반 추정 원인 (근거 없으면 '확인 필요' 명시)",
        "suggestion": "대응 제안"
      }
    ]
  },

  "verification_insights": [
    {
      "status": "checked",
      "hypothesis": "이전 PainPoint 가설",
      "insight": "검증 메모 본문을 AI가 판단해 정리한 내용",
      "impact": "이 검증 결과가 요약, 리스크, 영업전략에 주는 영향",
      "previous_question": "이미 물어본 검증 질문",
      "next_verification": "이제 새로 확인해야 할 다음 단계 질문 또는 실행 확인"
    }
  ],

  "painpoint_cards": [
    {
      "category": "budget|purchase_process|switching_cost|performance|compatibility|delivery|trust|priority",
      "hypothesis": "가설 한 줄",
      "confidence": "high|med|low",
      "confidence_score": 75,
      "evidence": [
        {"type": "quote|fact|verification|guess", "text": "「원문 인용 또는 사용자 검증 메모」", "source_section": "[2024-01-15 미팅] 또는 [검증 메모]"}
      ],
      "attribution": "individual|lab|purchase_route|institution",
      "verification_question": "다음 방문에서 확인할 질문",
      "action_if_yes": "맞으면 실행할 대응",
      "action_if_no": "아니면 다음 단계",
      "caution": "주의사항"
    }
  ],

  "next_actions": [
    {
      "action": "구체적 실행 액션",
      "priority": "high|medium|low",
      "reason": "왜 이 액션이 필요한지 (데이터 근거)"
    }
  ],

  "missing_info": {
    "items": ["확인 안 된 중요 정보"],
    "questions": ["다음 방문에서 확인할 질문"]
  }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━
최종 자기검증
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Evidence의 모든 인용이 실제 입력 데이터에 존재하는가?
2. 견적/납품 수치가 입력 데이터와 일치하는가?
3. 입력에 없는 내용을 만들어낸 부분은 없는가?
4. 기존 검증 메모리의 메모 본문을 AI가 직접 판단해 요약, PainPoint, 다음 액션, missing_info에 반영했는가?
5. 기존 검증 질문을 그대로 반복하지 않았는가?
6. 고객 메일 답장, 특히 고객→영업 수신 메일을 다음 액션 판단에 반영했는가?
7. 락인/수주, 견적, 미팅만 진행 고객의 단계에 맞는 다음 액션을 각각 보고했는가?
"""


# ================================================
# AI 분석 실행
# ================================================

def analyze_department(analysis, department, user):
    """
    부서 종합 분석 실행

    1. 미팅 데이터 수집 (6개월)
    2. 견적/납품 데이터 수집
    3. OpenAI API 호출
    4. 결과 저장

    Returns: (analysis_data, quote_delivery_data, token_usage)
    """
    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')

    # 데이터 수집
    meetings = gather_meeting_data(department, user)
    qd_data = gather_quote_delivery_data(department, user)
    from reporting.models import FollowUp as _FollowUp
    _followups = _FollowUp.objects.filter(user=user, department=department)
    prepayment_data = gather_prepayment_data(_followups)
    email_data = gather_email_data_for_followups(_followups, user)
    stage_contexts = build_customer_stage_context(
        _followups,
        meetings=meetings,
        qd_data=qd_data,
        email_data=email_data,
    )
    verification_memory = collect_painpoint_verification_memory(analysis)

    # 프롬프트 조립
    prompt_parts = []
    prompt_parts.append(f"[분석 대상] {department.company.name} / {department.name}")
    prompt_parts.append(f"[분석 기간] 최근 6개월")
    prompt_parts.append("")

    # 미팅 데이터
    prompt_parts.append(f"━━━ 미팅 기록 ({len(meetings)}건) ━━━")
    if meetings:
        for i, m in enumerate(meetings, 1):
            owner_label = f" | 담당자: {m['owner']}" if m.get('owner') else ''
            prompt_parts.append(f"\n[미팅 #{i}] {m['date']} - {m['customer']}{owner_label}")
            prompt_parts.append(m['content'])
    else:
        prompt_parts.append("(미팅 기록 없음)")

    # 견적 데이터
    prompt_parts.append(f"\n━━━ 견적 데이터 ({len(qd_data['quotes'])}건) ━━━")
    if qd_data['quotes']:
        for q in qd_data['quotes']:
            items_str = _quote_delivery_items_text(q['items'])
            converted = '✅납품전환' if q['converted_to_delivery'] else '❌미전환'
            source = f" | {q['source']}" if q.get('source') else ''
            notes = f" | 메모: {str(q.get('notes') or '')[:120]}" if q.get('notes') else ''
            prompt_parts.append(
                f"- {q['date']} | {q['quote_number']} | {q['customer']} | "
                f"{q['stage']} | {q['total_amount']:,}원 | {converted}{source}{notes} | 품목: {items_str}"
            )
    else:
        prompt_parts.append("(견적 데이터 없음)")

    # 납품 데이터
    prompt_parts.append(f"\n━━━ 납품 데이터 ({len(qd_data['deliveries'])}건) ━━━")
    if qd_data['deliveries']:
        for d in qd_data['deliveries']:
            items_str = _quote_delivery_items_text(d['items'])
            source = f" | {d['source']}" if d.get('source') else ''
            notes = f" | 메모: {str(d.get('notes') or '')[:120]}" if d.get('notes') else ''
            prompt_parts.append(
                f"- {d['date']} | {d['customer']} | {d['amount']:,}원{source}{notes} | 품목: {items_str}"
            )
    else:
        prompt_parts.append("(납품 데이터 없음)")

    # 이미 계산된 통계 첨부
    summary = qd_data['summary']
    prompt_parts.append(f"\n━━━ 견적/납품 통계 (참고) ━━━")
    prompt_parts.append(f"견적→납품 전환율: {summary['conversion_rate']}% ({summary['converted_quotes']}/{summary['total_quotes']})")
    if summary['avg_delivery_interval_days']:
        prompt_parts.append(f"평균 납품 간격: {summary['avg_delivery_interval_days']}일")
    if summary['product_stats']:
        prompt_parts.append("제품별 현황:")
        for name, stats in summary['product_stats'].items():
            prompt_parts.append(
                f"  - {name}: 견적 {stats['quoted']}회({stats['quote_amount']:,}원) / "
                f"납품 {stats['delivered']}회({stats['delivery_amount']:,}원)"
            )

    # 선결제 현황
    pp_sum = prepayment_data['summary']
    prompt_parts.append(f"\n━━━ 선결제 현황 ({pp_sum['total_count']}건) ━━━")
    if prepayment_data['prepayments']:
        prompt_parts.append(
            f"활성: {pp_sum['active_count']}건 | 총 잔액: ₩{pp_sum['total_remaining_balance']:,}"
        )
        if pp_sum['stalled_count'] > 0:
            prompt_parts.append(
                f"⚠️ 고착 위험 ({pp_sum['stalled_count']}건): {', '.join(pp_sum['stalled_customers'])}"
            )
        for p in prepayment_data['prepayments']:
            stalled_note = " ⚠️고착위험" if p['is_stalled'] else ""
            days_note = (
                f" / 최종사용 {p['days_since_last_use']}일전"
                if p['days_since_last_use'] is not None
                else " / 미사용"
            )
            prompt_parts.append(
                f"- {p['customer']} | 원금 ₩{p['original_amount']:,} | "
                f"잔액 ₩{p['balance']:,} | 입금일 {p['payment_date']} | {p['status_display']}{stalled_note}{days_note}"
            )
            for u in p['usages'][:3]:
                prompt_parts.append(
                    f"  └ {u['used_at']} {u['product']}×{u['quantity']} "
                    f"₩{u['amount']:,} (잔액→₩{u['remaining_after']:,})"
                )
    else:
        prompt_parts.append("(선결제 데이터 없음)")

    prompt_parts.extend(format_email_context_for_prompt(email_data))
    prompt_parts.extend(format_customer_stage_context_for_prompt(stage_contexts))
    prompt_parts.extend(format_painpoint_verification_memory_for_prompt(verification_memory))

    prompt_parts.append("\n위 데이터만 근거로 사용하라. 없는 정보는 '확인 필요'로 처리하라.")
    if verification_memory:
        prompt_parts.append("기존 PainPoint 검증 메모리는 상태값으로 의미를 고정하지 말고, 메모 본문을 읽어 AI가 직접 판단하라. 같은 PainPoint 검증 질문은 반복하지 말라.")

    user_prompt = "\n".join(prompt_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        try:
            analysis_result = json.loads(ai_text)
            analysis_result = apply_verification_memory_to_analysis_result(
                analysis_result,
                verification_memory,
            )
            analysis_result['email_context'] = email_data
            analysis_result = apply_stage_action_context_to_analysis_result(
                analysis_result,
                stage_contexts,
                verification_memory=verification_memory,
            )
        except json.JSONDecodeError:
            analysis_result = None
            logger.error(f"AI 응답 JSON 파싱 실패: {ai_text[:200]}")

        return analysis_result, qd_data, token_usage

    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {str(e)}")
        raise


# ================================================
# 개별 고객(FollowUp) 분석
# ================================================

FOLLOWUP_SYSTEM_PROMPT = """너는 B2B 영업 CRM의 "개별 고객 영업 분석" AI다.
영업 담당자가 특정 고객(거래처 담당자)과의 모든 활동 기록, 견적, 납품, 선결제 이력,
미처리 후속 액션을 제공하면, 이를 종합 분석하여 실제 영업 활동에 즉시 활용 가능한
분석 결과를 제공한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 규칙 (소설 금지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 입력 데이터에 **명시적으로 적혀있는 내용**만 근거로 사용한다.
2. 입력에 없는 사실, 제품명, 장비, 상황, 감정을 **절대 추측하거나 만들어내지 않는다**.
3. 정보가 없으면 반드시 null 또는 "확인 필요"로 표시한다.
4. 인용 시 「」로 감싸고 날짜를 표시한다.
5. 추측 시 반드시 "(추정)" 표시하고 근거를 명시한다.
6. 고객 메일/답장 기록이 있으면 고객→영업 수신 메일을 고객의 최신 의도/장애물/요청으로 우선 사용한다.
7. 현재 고객 분석 기준을 반드시 따른다.
   - 락인/수주 고객: 수주 이후 납품, 추가 발주, 재구매, 리텐션, 확장 판매 액션을 만든다.
   - 견적 고객: 견적 내용, 미팅 내용, 고객 메일 답장을 함께 분석해 수정 견적/조건 확인/의사결정 일정 액션을 만든다.
   - 미팅만 진행 고객: 미팅 내용과 고객 메일 답장을 분석해 자료 전달, 다음 미팅, 견적화 액션을 만든다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 (반드시 JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "deal_probability": 65,
  "deal_probability_reason": "확률 산출 근거 (데이터 기반, 1-2문장)",
  "relationship_stage": "cold|warm|active|loyal|at_risk",

  "account_brief": {
    "customer_summary": "이 고객과의 관계 및 현황을 2-3문장으로 요약",
    "recent_activity": "가장 최근 활동 내용 요약 (날짜 포함)",
    "sales_status": "현재 영업 단계 및 진행 상황",
    "prepayment_note": "선결제 잔액 현황 요약 및 활용 전략 (없으면 null)",
    "quote_delivery_note": "최근 견적/납품 현황 요약 (없으면 null)"
  },

  "opportunity_risk": {
    "purchase_potential": "구매 가능성 분석 (미팅/견적/납품 데이터 기반, 1-2문장)",
    "stalled_risk": "정체 위험 여부 및 원인 (없으면 null)",
    "price_risk": "가격 경쟁 또는 예산 리스크 (없으면 null)",
    "compatibility_risk": "제품 호환성 또는 사용 적합성 리스크 (없으면 null)",
    "budget_prepayment_risk": "예산 제약 또는 선결제 잔액 고착 리스크 (없으면 null)",
    "missing_info": ["확인이 필요한 정보 항목 (없으면 빈 배열)"]
  },

  "next_best_actions": [
    {
      "priority": 1,
      "action": "구체적 실행 액션 (무엇을, 어떻게)",
      "suggested_due": "YYYY-MM-DD 형식 또는 '다음 방문 시' 같은 표현",
      "what_to_ask": "고객에게 확인할 핵심 질문 한 줄",
      "what_to_prepare": "준비할 자료, 샘플, 견적서 (없으면 null)",
      "reason": "이 액션이 필요한 이유 (데이터 근거)"
    }
  ],

  "manager_summary": {
    "key_point": "매니저에게 보고할 핵심 사항 1-2줄",
    "decision_needed": "의사결정 또는 지원 요청 사항 (없으면 null)",
    "risk_level": "high|med|low",
    "expected_impact": "예상 비즈니스 영향 (수주 가능성, 금액 등)"
  },

  "visit_checklist": {
    "customer_context": "방문 전 파악할 고객 현황 (1-2문장)",
    "items_to_bring": ["지참할 자료, 샘플, 견적서 목록 (없으면 빈 배열)"],
    "questions_to_ask": ["방문 시 반드시 확인할 질문 (최소 2개)"],
    "unresolved_issues": ["미해결 이슈 또는 후속 미확인 사항 (없으면 빈 배열)"]
  },

  "key_painpoints": [
    {
      "painpoint": "핵심 불편/필요 사항",
      "evidence": "근거 (날짜 + 인용)",
      "confidence": "high|med|low"
    }
  ],

  "risk_factors": [
    {
      "risk": "위험 요인",
      "severity": "high|med|low",
      "mitigation": "대응 방법"
    }
  ]
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
deal_probability 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 90-100: 구매 확정 또는 반복 납품 중
- 70-89: 적극적 검토 + 견적 전환 이력 있음
- 50-69: 관심 있으나 결정 장애물 존재
- 30-49: 초기 접촉 단계 또는 장기 검토
- 0-29: 구매 신호 없음 또는 명시적 거절

━━━━━━━━━━━━━━━━━━━━━━━━━━━
분석 지침
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 미처리 후속 액션(특히 지연된 것)은 visit_checklist.unresolved_issues와
  next_best_actions에 반드시 반영한다.
- 선결제 잔액이 있고 최근 90일 사용 없으면 account_brief.prepayment_note와
  next_best_actions에 재구매 유도 또는 잔액 소진 전략을 포함한다.
- next_best_actions은 우선순위 순으로 최대 3건 제시하고, 각 항목은 실제 영업
  현장에서 바로 실행할 수 있는 수준으로 작성한다.
- visit_checklist.questions_to_ask는 최소 2개 이상 제시한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
최종 자기검증
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 모든 분석이 입력 데이터에 명시된 내용에만 근거하는가?
2. 없는 사실을 만들어낸 부분은 없는가?
3. next_best_actions이 실제 영업 활동에 즉시 활용 가능한 수준인가?
4. 선결제 및 미처리 후속 액션이 적절히 반영되었는가?
5. 고객 메일 답장, 특히 고객→영업 수신 메일을 다음 액션 판단에 반영했는가?
6. 락인/수주, 견적, 미팅만 진행 상태에 맞는 다음 액션을 만들었는가?
"""


def gather_followup_data(followup, user):
    """특정 고객(FollowUp)의 전체 히스토리 수집"""
    from reporting.models import History, Schedule

    # 미팅 기록 (전체)
    histories = History.objects.filter(
        followup=followup,
    ).select_related('user', 'schedule').order_by('-created_at')

    import datetime as _dt
    _today = _dt.date.today()
    meeting_list = []
    pending_actions = []
    for h in histories:
        # 후속 액션 수집 (모든 활동 유형)
        if h.next_action and h.next_action.strip():
            pending_actions.append({
                'action': h.next_action.strip(),
                'due_date': h.next_action_date.strftime('%Y-%m-%d') if h.next_action_date else None,
                'is_overdue': (h.next_action_date < _today) if h.next_action_date else False,
                'from_type': h.get_action_type_display(),
                'from_date': (h.meeting_date or h.created_at.date()).strftime('%Y-%m-%d'),
            })
        if h.action_type == 'customer_meeting':
            parts = []
            if h.meeting_situation:
                parts.append(f"[상황] {h.meeting_situation}")
            if h.meeting_researcher_quote:
                parts.append(f"[고객 발언] {h.meeting_researcher_quote}")
            if h.meeting_confirmed_facts:
                parts.append(f"[확인된 사실] {h.meeting_confirmed_facts}")
            if h.meeting_obstacles:
                parts.append(f"[장애물] {h.meeting_obstacles}")
            if h.meeting_next_action:
                parts.append(f"[다음 액션] {h.meeting_next_action}")
            if not parts and h.content:
                parts.append(h.content)
            meeting_list.append({
                'date': (h.meeting_date or h.created_at.date()).strftime('%Y-%m-%d'),
                'content': '\n'.join(parts),
                'by': h.user.get_full_name() or h.user.username,
                'next_action': h.next_action or '',
                'next_action_date': h.next_action_date.strftime('%Y-%m-%d') if h.next_action_date else '',
            })
    # 지연 > 예정 > 날짜미정 순으로 정렬
    pending_actions.sort(key=lambda x: (x['due_date'] is None, not x['is_overdue'], x['due_date'] or ''))

    qd_data = _gather_quote_delivery_data_for_followup_ids([followup.id], user)
    quote_list = [
        {
            'date': q.get('date') or '',
            'number': q.get('quote_number') or '',
            'stage': q.get('stage') or '',
            'total': int(q.get('total_amount') or 0),
            'converted': bool(q.get('converted_to_delivery')),
            'items': _quote_delivery_items_text(q.get('items') or []),
            'source': q.get('source') or '',
            'notes': q.get('notes') or '',
        }
        for q in qd_data['quotes']
    ]
    delivery_list = [
        {
            'date': d.get('date') or '',
            'amount': int(d.get('amount') or 0),
            'items': _quote_delivery_items_text(d.get('items') or []),
            'source': d.get('source') or '',
            'notes': d.get('notes') or '',
        }
        for d in qd_data['deliveries']
    ]

    # 예정 일정
    upcoming = Schedule.objects.filter(
        followup=followup,
        status='scheduled',
        visit_date__gte=__import__('datetime').date.today(),
    ).order_by('visit_date')

    upcoming_list = [{
        'date': s.visit_date.strftime('%Y-%m-%d'),
        'type': s.get_activity_type_display(),
        'notes': s.notes or '',
    } for s in upcoming]

    # 선결제 기록
    from reporting.models import Prepayment
    from datetime import date, timedelta

    pp_qs = Prepayment.objects.filter(
        customer=followup
    ).prefetch_related('usages').order_by('-payment_date')

    today = date.today()
    stale_threshold = today - timedelta(days=90)
    prepayment_list = []
    for p in pp_qs:
        usages = p.usages.all().order_by('-used_at')
        usage_list = []
        for u in usages:
            usage_list.append({
                'product': u.product_name,
                'quantity': u.quantity,
                'amount': int(u.amount),
                'remaining_after': int(u.remaining_balance),
                'used_at': u.used_at.strftime('%Y-%m-%d'),
            })
        last_usage = usages.first()
        last_used_date = last_usage.used_at.date() if last_usage else None
        days_since_use = (today - last_used_date).days if last_used_date else None
        is_stalled = (
            p.status == 'active'
            and p.balance > 0
            and (last_used_date is None or last_used_date < stale_threshold)
        )
        prepayment_list.append({
            'original_amount': int(p.amount),
            'balance': int(p.balance),
            'used_amount': int(p.amount - p.balance),
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'status': p.status,
            'status_display': p.get_status_display(),
            'last_used_date': last_used_date.strftime('%Y-%m-%d') if last_used_date else None,
            'days_since_last_use': days_since_use,
            'is_stalled': is_stalled,
            'usages': usage_list,
        })

    email_data = gather_email_data_for_followups([followup], user, limit=12)
    stage_context = build_single_followup_stage_context(
        followup,
        {
            'meetings': meeting_list,
            'quotes': quote_list,
            'emails': email_data['emails'],
        },
    )

    return {
        'meetings': meeting_list,
        'quotes': quote_list,
        'deliveries': delivery_list,
        'upcoming': upcoming_list,
        'prepayments': prepayment_list,
        'pending_actions': pending_actions,
        'emails': email_data['emails'],
        'email_summary': email_data['summary'],
        'stage_context': stage_context,
    }


def analyze_followup(analysis, followup, user):
    """
    개별 고객 AI 분석 실행
    Returns: (analysis_data, meeting_count, token_usage)
    """
    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')

    data = gather_followup_data(followup, user)

    # 프롬프트 조립
    parts = []
    company_str = str(followup.company) if followup.company else ''
    dept_str = str(followup.department) if followup.department else ''
    parts.append(f"[고객 정보]")
    parts.append(f"이름: {followup.customer_name}")
    parts.append(f"소속: {company_str} / {dept_str}")
    parts.append(f"등급: {followup.customer_grade} | 우선순위: {followup.get_priority_display()}")
    parts.append(f"파이프라인 단계: {followup.get_pipeline_stage_display()}")
    parts.append("")

    parts.append(f"━━━ 미팅 기록 ({len(data['meetings'])}건) ━━━")
    if data['meetings']:
        for i, m in enumerate(data['meetings'], 1):
            parts.append(f"\n[미팅 #{i}] {m['date']} (담당: {m['by']})")
            parts.append(m['content'])
    else:
        parts.append("(미팅 기록 없음)")

    parts.append(f"\n━━━ 견적 기록 ({len(data['quotes'])}건) ━━━")
    if data['quotes']:
        for q in data['quotes']:
            converted = '✅납품전환' if q['converted'] else '❌미전환'
            source = f" | {q['source']}" if q.get('source') else ''
            notes = f" | 메모: {str(q.get('notes') or '')[:120]}" if q.get('notes') else ''
            parts.append(f"- {q['date']} | {q['number']} | {q['stage']} | {q['total']:,}원 | {converted}{source}{notes}")
            if q['items']:
                parts.append(f"  품목: {q['items']}")
    else:
        parts.append("(견적 기록 없음)")

    parts.append(f"\n━━━ 납품 기록 ({len(data['deliveries'])}건) ━━━")
    if data['deliveries']:
        for d in data['deliveries']:
            source = f" | {d['source']}" if d.get('source') else ''
            notes = f" | 메모: {str(d.get('notes') or '')[:120]}" if d.get('notes') else ''
            parts.append(f"- {d['date']} | {d['amount']:,}원{source}{notes} | {d['items']}")
    else:
        parts.append("(납품 기록 없음)")

    if data['upcoming']:
        parts.append(f"\n━━━ 예정 일정 ━━━")
        for s in data['upcoming']:
            parts.append(f"- {s['date']} {s['type']}: {s['notes']}")

    # 미처리 후속 액션
    pending = data.get('pending_actions', [])
    if pending:
        overdue = [a for a in pending if a['is_overdue']]
        upcoming_acts = [a for a in pending if not a['is_overdue'] and a['due_date']]
        no_date = [a for a in pending if not a['due_date']]
        parts.append(f"\n━━━ 미처리 후속 액션 ({len(pending)}건) ━━━")
        if overdue:
            parts.append(f"⚠️ 지연 ({len(overdue)}건):")
            for a in overdue[:5]:
                parts.append(f"  - 예정:{a['due_date']} | {a['action'][:120]} (기록:{a['from_type']} {a['from_date']})")
        if upcoming_acts:
            parts.append(f"예정 ({len(upcoming_acts)}건):")
            for a in upcoming_acts[:5]:
                parts.append(f"  - 예정:{a['due_date']} | {a['action'][:120]}")
        if no_date:
            parts.append(f"날짜 미정 ({len(no_date)}건):")
            for a in no_date[:3]:
                parts.append(f"  - {a['action'][:120]}")

    # 선결제 현황
    pp_list = data.get('prepayments', [])
    parts.append(f"\n━━━ 선결제 현황 ({len(pp_list)}건) ━━━")
    if pp_list:
        for p in pp_list:
            stalled_note = " ⚠️고착위험(90일이상미사용)" if p['is_stalled'] else ""
            days_note = (
                f" / 최종사용 {p['days_since_last_use']}일전"
                if p['days_since_last_use'] is not None
                else " / 미사용"
            )
            parts.append(
                f"원금 ₩{p['original_amount']:,} | 잔액 ₩{p['balance']:,} | "
                f"입금일 {p['payment_date']} | {p['status_display']}{stalled_note}{days_note}"
            )
            for u in p['usages'][:5]:
                parts.append(
                    f"  └ {u['used_at']} {u['product']}×{u['quantity']} ₩{u['amount']:,} (잔액→₩{u['remaining_after']:,})"
                )
    else:
        parts.append("(선결제 데이터 없음)")

    parts.extend(format_email_context_for_prompt({
        'emails': data.get('emails') or [],
        'summary': data.get('email_summary') or {},
    }))

    stage_context = data.get('stage_context') or {}
    parts.append("\n━━━ 현재 고객 분석 기준 ━━━")
    if stage_context:
        parts.append(
            f"{stage_context['context_label']}({stage_context['pipeline_stage_label']}) | "
            f"미팅 {stage_context['meeting_count']}건, 견적 {stage_context['quote_count']}건, "
            f"고객메일 {stage_context['inbound_email_count']}건"
        )
        parts.append(f"다음 액션 기준: {stage_context['analysis_focus']}")
    else:
        parts.append("(고객 단계 기준 없음)")

    parts.append("\n위 데이터만 근거로 사용하라. 없는 정보는 missing_info에 기록하라.")

    messages = [
        {"role": "system", "content": FOLLOWUP_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(parts)},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        try:
            analysis_result = json.loads(ai_text)
            analysis_result = apply_followup_stage_context_to_analysis_result(
                analysis_result,
                data.get('stage_context') or {},
            )
            analysis_result['email_context'] = {
                'emails': data.get('emails') or [],
                'summary': data.get('email_summary') or {},
            }
        except json.JSONDecodeError:
            analysis_result = None
            logger.error(f"AI 응답 JSON 파싱 실패: {ai_text[:200]}")

        return analysis_result, len(data['meetings']), token_usage

    except Exception as e:
        logger.error(f"FollowUp AI 분석 실패: {str(e)}")
        raise


# ================================================
# 주간보고 AI 초안 생성
# ================================================

WEEKLY_REPORT_SYSTEM_PROMPT = """너는 B2B 영업 CRM의 "주간보고 초안 작성" AI다.
영업 담당자의 해당 주 미팅·견적·납품 활동 기록을 받아서
주간보고서 초안 3개 섹션을 작성한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 입력 데이터에 명시된 내용만 사용한다.
2. 없는 활동, 고객명, 금액을 만들어내지 않는다.
3. 없는 정보는 "(확인 필요)" 또는 생략한다.
4. 한국어 영업 실무 문체로 작성한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 (반드시 JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "activity_notes": "영업 활동 내용 초안 (줄 구분하여 작성, 날짜별·고객별 활동 요약)",
  "quote_delivery_notes": "견적/납품 내용 초안 (없으면 빈 문자열)",
  "other_notes": "다음 주 예정 계획 및 특이사항 초안 (없으면 빈 문자열)",
  "summary": {
    "total_meetings": 미팅 건수 (정수),
    "total_quotes": 견적 건수 (정수),
    "total_deliveries": 납품 건수 (정수),
    "key_customers": ["주요 고객명 목록"],
    "risks": ["위험 요인 목록 (없으면 빈 배열)"],
    "next_week_priorities": ["다음 주 중점 사항 목록 (없으면 빈 배열)"]
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
activity_notes 작성 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 날짜 순 또는 고객별로 그룹화
- 각 활동을 "- [날짜] [고객명] ([소속]): [활동 유형] — [핵심 내용] / 다음 액션: [내용]" 형식
- 고객 발언 또는 핵심 정보는 "(직접 인용)" 표시
- 위험 요인이나 장애물은 ⚠️ 표시

━━━━━━━━━━━━━━━━━━━━━━━━━━━
quote_delivery_notes 작성 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 견적: "- [고객명]: [견적번호] 제출, 금액 [N원], 단계: [단계]"
- 납품: "- [고객명]: [금액] 납품 완료, 품목: [목록]"
- 전환율/금액 합계 있으면 마지막 줄에 요약

━━━━━━━━━━━━━━━━━━━━━━━━━━━
other_notes 작성 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 다음 주 예정 활동 목록
- 미해결 이슈 또는 후속 필요 사항
- 특이사항
"""


def generate_weekly_report_draft(user, week_start, week_end):
    """
    주간보고 AI 초안 생성
    Args:
        user: Django User 인스턴스
        week_start: datetime.date
        week_end: datetime.date
    Returns:
        dict: {activity_notes, quote_delivery_notes, other_notes, summary}
        또는 None (데이터 없음)
    """
    import datetime as _dt
    from django.utils import timezone as _tz
    from reporting.models import History, Schedule, Quote

    # 해당 주 미팅 기록 (meeting_date 기준)
    meetings = History.objects.filter(
        user=user,
        action_type__in=['customer_meeting', 'quote', 'delivery_schedule'],
        meeting_date__gte=week_start,
        meeting_date__lte=week_end,
    ).select_related(
        'followup', 'followup__company', 'followup__department'
    ).order_by('meeting_date', 'created_at')

    # meeting_date 없는 항목도 created_at 기준으로 포함
    start_dt = _tz.make_aware(_dt.datetime.combine(week_start, _dt.time.min))
    end_dt = _tz.make_aware(_dt.datetime.combine(week_end, _dt.time.max))
    extra_meetings = History.objects.filter(
        user=user,
        action_type__in=['customer_meeting', 'quote', 'delivery_schedule'],
        meeting_date__isnull=True,
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    ).select_related(
        'followup', 'followup__company', 'followup__department'
    ).order_by('created_at')

    all_histories = list(meetings) + list(extra_meetings)

    # 해당 주 일정 (참고용)
    schedules = Schedule.objects.filter(
        user=user,
        visit_date__gte=week_start,
        visit_date__lte=week_end,
    ).select_related(
        'followup', 'followup__company'
    ).order_by('visit_date')

    # 해당 주 견적
    quotes = Quote.objects.filter(
        followup__user=user,
        quote_date__gte=week_start,
        quote_date__lte=week_end,
    ).select_related('followup', 'followup__company').prefetch_related('items__product')

    # 데이터 없으면 None 반환
    if not all_histories and not schedules and not quotes:
        return None

    # 프롬프트 조립
    parts = []
    parts.append(f"[보고 기간] {week_start.strftime('%Y년 %m월 %d일')} ~ {week_end.strftime('%Y년 %m월 %d일')}")
    parts.append(f"[작성자] {user.get_full_name() or user.username}")
    parts.append("")

    # 미팅·납품 기록
    parts.append(f"━━━ 영업 활동 기록 ({len(all_histories)}건) ━━━")
    if all_histories:
        for h in all_histories:
            fu = h.followup
            customer = fu.customer_name if fu else '-'
            company = str(fu.company) if fu and fu.company else ''
            dept = str(fu.department) if fu and fu.department else ''
            date_str = (h.meeting_date or h.created_at.date()).strftime('%m/%d')
            act_type = h.get_action_type_display()

            entry_parts = []
            if h.meeting_situation:
                entry_parts.append(f"상황: {h.meeting_situation}")
            if h.meeting_researcher_quote:
                entry_parts.append(f"고객 발언: 「{h.meeting_researcher_quote}」")
            if h.meeting_confirmed_facts:
                entry_parts.append(f"확인된 사실: {h.meeting_confirmed_facts}")
            if h.meeting_obstacles:
                entry_parts.append(f"⚠️ 장애물: {h.meeting_obstacles}")
            if h.meeting_next_action:
                entry_parts.append(f"다음 액션: {h.meeting_next_action}")
            if h.content and not entry_parts:
                entry_parts.append(h.content)
            if h.next_action:
                entry_parts.append(f"후속 예정: {h.next_action}" +
                                   (f" ({h.next_action_date.strftime('%m/%d')})" if h.next_action_date else ""))
            if h.delivery_amount:
                entry_parts.append(f"납품금액: {int(h.delivery_amount):,}원")
            if h.delivery_items:
                entry_parts.append(f"납품품목: {h.delivery_items}")

            content_str = " / ".join(entry_parts) if entry_parts else "(내용 없음)"
            co_str = f" ({company}{' · ' + dept if dept else ''})" if (company or dept) else ""
            parts.append(f"- [{date_str}] {customer}{co_str} — {act_type}: {content_str}")
    else:
        parts.append("(기록 없음)")

    # 일정 (미팅 기록 없는 경우 보완)
    if schedules:
        parts.append(f"\n━━━ 해당 주 일정 참고 ({schedules.count()}건) ━━━")
        for s in schedules:
            fu = s.followup
            customer = fu.customer_name if fu else '-'
            company = str(fu.company) if fu and fu.company else ''
            parts.append(
                f"- [{s.visit_date.strftime('%m/%d')}] {customer}"
                f"{' (' + company + ')' if company else ''} — {s.get_activity_type_display()}"
                f"{': ' + s.notes if s.notes else ''}"
            )

    # 견적 기록
    parts.append(f"\n━━━ 해당 주 견적 ({quotes.count()}건) ━━━")
    if quotes:
        for q in quotes:
            fu = q.followup
            customer = fu.customer_name if fu else '-'
            company = str(fu.company) if fu and fu.company else ''
            items_str = ', '.join([
                f"{it.product.product_code if it.product else '미정'}({it.quantity}개)"
                for it in q.items.all()
            ])
            converted = '→납품전환' if q.converted_to_delivery else '미전환'
            parts.append(
                f"- {customer}{' (' + company + ')' if company else ''}: "
                f"{q.quote_number} | {q.get_stage_display()} | "
                f"{int(q.total_amount or 0):,}원 | {converted}"
                f"{' | 품목: ' + items_str if items_str else ''}"
            )
    else:
        parts.append("(해당 주 견적 없음)")

    parts.append("\n위 데이터만 사용하여 주간보고 초안을 작성하라.")
    user_prompt = "\n".join(parts)

    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')

    messages = [
        {"role": "system", "content": WEEKLY_REPORT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )
        ai_text = response.choices[0].message.content
        try:
            result = json.loads(ai_text)
        except json.JSONDecodeError:
            logger.error(f"주간보고 AI 응답 JSON 파싱 실패: {ai_text[:200]}")
            return None
        return result
    except Exception as e:
        logger.error(f"주간보고 AI 초안 생성 실패: {str(e)}")
        raise
