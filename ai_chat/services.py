"""
AI 부서 분석 서비스
부서별 6개월 미팅 종합 분석 + 견적/납품 패턴 분석
"""
import json
import os
import logging
from datetime import timedelta
from decimal import Decimal
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
    """부서의 최근 N개월 미팅 데이터 수집"""
    from reporting.models import History, FollowUp

    cutoff = timezone.now().date() - timedelta(days=months * 30)

    followups = FollowUp.objects.filter(
        user=user, department=department
    )

    meetings = History.objects.filter(
        followup__in=followups,
        action_type='customer_meeting',
    ).filter(
        created_at__date__gte=cutoff
    ).order_by('-created_at')

    meeting_list = []
    for m in meetings:
        entry = {
            'date': (m.meeting_date or m.created_at.date()).strftime('%Y-%m-%d'),
            'customer': m.followup.customer_name if m.followup else '미정',
        }
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


def gather_quote_delivery_data(department, user):
    """부서의 견적/납품 데이터 수집 및 패턴 분석"""
    from reporting.models import Quote, QuoteItem, History, FollowUp, DeliveryItem

    followups = FollowUp.objects.filter(user=user, department=department)
    followup_ids = list(followups.values_list('id', flat=True))

    # 견적 데이터
    quotes = Quote.objects.filter(
        followup_id__in=followup_ids
    ).select_related('followup').prefetch_related('items__product').order_by('-quote_date')

    quote_list = []
    for q in quotes:
        items = []
        for item in q.items.all():
            items.append({
                'product': item.product.product_code if item.product else '미정',
                'quantity': item.quantity,
                'unit_price': int(item.unit_price) if item.unit_price else 0,
                'subtotal': int(item.subtotal) if item.subtotal else 0,
            })
        quote_list.append({
            'quote_number': q.quote_number,
            'date': q.quote_date.strftime('%Y-%m-%d') if q.quote_date else '',
            'customer': q.followup.customer_name if q.followup else '미정',
            'stage': q.get_stage_display(),
            'total_amount': int(q.total_amount) if q.total_amount else 0,
            'converted_to_delivery': q.converted_to_delivery,
            'items': items,
        })

    # 납품 데이터
    deliveries = History.objects.filter(
        followup_id__in=followup_ids,
        action_type='delivery_schedule',
    ).order_by('-created_at')

    delivery_list = []
    for d in deliveries:
        d_items = DeliveryItem.objects.filter(history=d).select_related('product')
        items = []
        for di in d_items:
            items.append({
                'product': di.product.product_code if di.product else di.item_name,
                'quantity': di.quantity,
                'unit_price': int(di.unit_price) if di.unit_price else 0,
                'total_price': int(di.total_price) if di.total_price else 0,
            })
        delivery_list.append({
            'date': d.delivery_date.strftime('%Y-%m-%d') if d.delivery_date else d.created_at.strftime('%Y-%m-%d'),
            'customer': d.followup.customer_name if d.followup else '미정',
            'amount': int(d.delivery_amount) if d.delivery_amount else 0,
            'items': items,
        })

    # 패턴 계산
    total_quotes = len(quote_list)
    converted_quotes = sum(1 for q in quote_list if q['converted_to_delivery'])
    conversion_rate = round(converted_quotes / total_quotes * 100, 1) if total_quotes > 0 else 0

    # 납품 주기 계산
    delivery_dates = sorted([d['date'] for d in delivery_list if d['date']])
    avg_delivery_interval_days = None
    if len(delivery_dates) >= 2:
        from datetime import datetime
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in delivery_dates]
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        intervals = [abs(iv) for iv in intervals if iv != 0]
        if intervals:
            avg_delivery_interval_days = round(sum(intervals) / len(intervals))

    # 제품별 집계
    product_stats = {}
    for q in quote_list:
        for item in q['items']:
            name = item['product']
            if name not in product_stats:
                product_stats[name] = {'quoted': 0, 'delivered': 0, 'quote_amount': 0, 'delivery_amount': 0}
            product_stats[name]['quoted'] += 1
            product_stats[name]['quote_amount'] += item['subtotal']
    for d in delivery_list:
        for item in d['items']:
            name = item['product']
            if name not in product_stats:
                product_stats[name] = {'quoted': 0, 'delivered': 0, 'quote_amount': 0, 'delivery_amount': 0}
            product_stats[name]['delivered'] += 1
            product_stats[name]['delivery_amount'] += item['total_price']

    return {
        'quotes': quote_list,
        'deliveries': delivery_list,
        'summary': {
            'total_quotes': total_quotes,
            'converted_quotes': converted_quotes,
            'conversion_rate': conversion_rate,
            'total_deliveries': len(delivery_list),
            'avg_delivery_interval_days': avg_delivery_interval_days,
            'product_stats': product_stats,
        }
    }


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

  "painpoint_cards": [
    {
      "category": "budget|purchase_process|switching_cost|performance|compatibility|delivery|trust|priority",
      "hypothesis": "가설 한 줄",
      "confidence": "high|med|low",
      "confidence_score": 75,
      "evidence": [
        {"type": "quote", "text": "「원문 인용」", "source_section": "[2024-01-15 미팅]"}
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

    # 프롬프트 조립
    prompt_parts = []
    prompt_parts.append(f"[분석 대상] {department.company.name} / {department.name}")
    prompt_parts.append(f"[분석 기간] 최근 6개월")
    prompt_parts.append("")

    # 미팅 데이터
    prompt_parts.append(f"━━━ 미팅 기록 ({len(meetings)}건) ━━━")
    if meetings:
        for i, m in enumerate(meetings, 1):
            prompt_parts.append(f"\n[미팅 #{i}] {m['date']} - {m['customer']}")
            prompt_parts.append(m['content'])
    else:
        prompt_parts.append("(미팅 기록 없음)")

    # 견적 데이터
    prompt_parts.append(f"\n━━━ 견적 데이터 ({len(qd_data['quotes'])}건) ━━━")
    if qd_data['quotes']:
        for q in qd_data['quotes']:
            items_str = ', '.join([f"{it['product']}({it['quantity']}개)" for it in q['items']])
            converted = '✅납품전환' if q['converted_to_delivery'] else '❌미전환'
            prompt_parts.append(
                f"- {q['date']} | {q['quote_number']} | {q['customer']} | "
                f"{q['stage']} | {q['total_amount']:,}원 | {converted} | 품목: {items_str}"
            )
    else:
        prompt_parts.append("(견적 데이터 없음)")

    # 납품 데이터
    prompt_parts.append(f"\n━━━ 납품 데이터 ({len(qd_data['deliveries'])}건) ━━━")
    if qd_data['deliveries']:
        for d in qd_data['deliveries']:
            items_str = ', '.join([f"{it['product']}({it['quantity']}개)" for it in d['items']])
            prompt_parts.append(
                f"- {d['date']} | {d['customer']} | {d['amount']:,}원 | 품목: {items_str}"
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

    prompt_parts.append("\n위 데이터만 근거로 사용하라. 없는 정보는 '확인 필요'로 처리하라.")

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

FOLLOWUP_SYSTEM_PROMPT = """너는 B2B 영업 CRM의 "개별 고객 분석" AI다.
영업 담당자가 특정 고객(연구원/담당자)과의 모든 미팅 기록, 견적, 납품 이력을 제공하면,
이를 종합 분석하여 이 고객과의 관계 현황 및 최적의 영업 전략을 제안한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 입력 데이터에 명시된 내용만 근거로 사용한다.
2. 추측 시 반드시 "(추정)" 표시하고 confidence를 low로 설정한다.
3. 근거 없는 painpoint는 생성하지 않는다.
4. 인용 시 「」로 감싸고 날짜를 표시한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 (반드시 JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "customer_summary": "이 고객과의 관계를 2-3문장으로 요약",
  "relationship_stage": "현재 관계 단계 (cold/warm/active/loyal/at_risk 중 하나 + 한 줄 이유)",
  "key_painpoints": [
    {
      "painpoint": "핵심 불편/필요 사항",
      "evidence": "근거 (미팅 날짜 + 인용)",
      "confidence": "high|med|low"
    }
  ],
  "next_best_actions": [
    {
      "action": "구체적 실행 액션 (what + when)",
      "reason": "왜 이 액션이 필요한지",
      "priority": 1
    }
  ],
  "risk_factors": [
    {
      "risk": "위험 요인",
      "severity": "high|med|low",
      "mitigation": "대응 방법"
    }
  ],
  "opportunity_signals": ["기회 신호 (미팅/견적 데이터에서 발견된 긍정 시그널)"],
  "deal_probability": 65,
  "deal_probability_reason": "확률 산출 근거 (최근 미팅 빈도, 견적 전환율, 관계 단계 등)",
  "missing_info": ["확인이 필요한 정보 항목"]
}

deal_probability 기준:
- 90-100: 구매 확정 또는 반복 납품 중
- 70-89: 적극적 검토 + 견적 전환 이력 있음
- 50-69: 관심 있으나 결정 장애물 존재
- 30-49: 초기 접촉 단계 또는 장기 검토
- 0-29: 구매 신호 없음 또는 명시적 거절
"""


def gather_followup_data(followup, user):
    """특정 고객(FollowUp)의 전체 히스토리 수집"""
    from reporting.models import History, Schedule, Quote, DeliveryItem

    # 미팅 기록 (전체)
    histories = History.objects.filter(
        followup=followup,
    ).select_related('user', 'schedule').order_by('-created_at')

    meeting_list = []
    for h in histories:
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
            })

    # 견적 기록
    quotes = Quote.objects.filter(
        followup=followup
    ).prefetch_related('items__product').order_by('-quote_date')

    quote_list = []
    for q in quotes:
        items_str = ', '.join([
            f"{it.product.product_code if it.product else '미정'}({it.quantity}개, {int(it.subtotal or 0):,}원)"
            for it in q.items.all()
        ])
        quote_list.append({
            'date': q.quote_date.strftime('%Y-%m-%d') if q.quote_date else '',
            'number': q.quote_number,
            'stage': q.get_stage_display(),
            'total': int(q.total_amount or 0),
            'converted': q.converted_to_delivery,
            'items': items_str,
        })

    # 납품 기록
    deliveries = History.objects.filter(
        followup=followup,
        action_type='delivery_schedule',
    ).order_by('-created_at')

    delivery_list = []
    for d in deliveries:
        d_items = DeliveryItem.objects.filter(history=d).select_related('product')
        items_str = ', '.join([
            f"{di.product.product_code if di.product else di.item_name}({di.quantity}개)"
            for di in d_items
        ])
        delivery_list.append({
            'date': d.delivery_date.strftime('%Y-%m-%d') if d.delivery_date else d.created_at.strftime('%Y-%m-%d'),
            'amount': int(d.delivery_amount or 0),
            'items': items_str,
        })

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

    return {
        'meetings': meeting_list,
        'quotes': quote_list,
        'deliveries': delivery_list,
        'upcoming': upcoming_list,
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
            parts.append(f"- {q['date']} | {q['number']} | {q['stage']} | {q['total']:,}원 | {converted}")
            if q['items']:
                parts.append(f"  품목: {q['items']}")
    else:
        parts.append("(견적 기록 없음)")

    parts.append(f"\n━━━ 납품 기록 ({len(data['deliveries'])}건) ━━━")
    if data['deliveries']:
        for d in data['deliveries']:
            parts.append(f"- {d['date']} | {d['amount']:,}원 | {d['items']}")
    else:
        parts.append("(납품 기록 없음)")

    if data['upcoming']:
        parts.append(f"\n━━━ 예정 일정 ━━━")
        for s in data['upcoming']:
            parts.append(f"- {s['date']} {s['type']}: {s['notes']}")

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
            max_tokens=3000,
            response_format={"type": "json_object"},
        )
        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        try:
            analysis_result = json.loads(ai_text)
        except json.JSONDecodeError:
            analysis_result = None
            logger.error(f"AI 응답 JSON 파싱 실패: {ai_text[:200]}")

        return analysis_result, len(data['meetings']), token_usage

    except Exception as e:
        logger.error(f"FollowUp AI 분석 실패: {str(e)}")
        raise
