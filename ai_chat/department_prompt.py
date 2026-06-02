"""Department prompt helpers for external AI tools."""

from __future__ import annotations

import re

GENERAL_GOALS = [
    "상황 요약",
    "문제 원인 정리",
    "실행계획 작성",
    "보고서 초안 작성",
    "체크리스트 생성",
    "아이디어 도출",
]


DEPARTMENT_GOALS = {
    "영업팀": [
        "진행 고객 현황 정리",
        "후속 연락 스크립트 작성",
        "견적 후속 전략 작성",
        "고객 이탈 위험 분석",
        "미팅 준비 질문 리스트 생성",
        "영업 보고서 초안 작성",
    ],
    "마케팅팀": [
        "캠페인 아이디어 도출",
        "고객 세그먼트 정리",
        "콘텐츠 주제 추천",
        "랜딩페이지 카피 작성",
        "광고 메시지 개선",
        "경쟁사 비교 자료 작성",
    ],
    "고객지원팀": [
        "고객 문의 답변 초안 작성",
        "클레임 원인 정리",
        "FAQ 생성",
        "응대 스크립트 작성",
        "이슈 처리 순서 분류",
        "재발 방지 체크리스트 작성",
    ],
    "구매팀": [
        "공급업체 비교 기준 작성",
        "견적 비교표 생성",
        "구매 의사결정 기준 정리",
        "납기 리스크 분석",
        "원가 절감 아이디어 도출",
        "내부 승인 요청서 초안 작성",
    ],
    "연구개발/R&D": [
        "실험 계획 초안 작성",
        "문헌 조사 질문 생성",
        "결과 해석 프레임 작성",
        "리스크 체크리스트 작성",
        "연구 보고서 구조 작성",
        "실험 변수 정리",
    ],
    "품질/QC": [
        "검사 기준 정리",
        "이상 원인 분석 질문 작성",
        "품질 이슈 보고서 초안 작성",
        "재발 방지 대책 정리",
        "체크리스트 생성",
        "감사 대응 자료 구조 작성",
    ],
    "생산/운영": [
        "작업 표준서 초안 작성",
        "병목 원인 분석",
        "일정 지연 리스크 정리",
        "공정 개선 아이디어 도출",
        "작업 체크리스트 생성",
        "일일 보고서 초안 작성",
    ],
    "경영/관리": [
        "의사결정 기준 정리",
        "회의 아젠다 작성",
        "보고서 구조 작성",
        "KPI 점검표 생성",
        "부서별 이슈 요약",
        "실행계획 로드맵 작성",
    ],
    "기타": GENERAL_GOALS,
}


DEPARTMENT_ALIASES = {
    "영업": "영업팀",
    "세일즈": "영업팀",
    "마케팅": "마케팅팀",
    "고객지원": "고객지원팀",
    "cs": "고객지원팀",
    "구매": "구매팀",
    "연구개발": "연구개발/R&D",
    "r&d": "연구개발/R&D",
    "rnd": "연구개발/R&D",
    "품질": "품질/QC",
    "qc": "품질/QC",
    "생산": "생산/운영",
    "운영": "생산/운영",
    "경영": "경영/관리",
    "관리": "경영/관리",
}


KEYWORD_GOAL_PRIORITIES = {
    "견적": ["견적 후속 전략 작성", "견적 비교표 생성", "구매 의사결정 기준 정리"],
    "후속": ["후속 연락 스크립트 작성", "진행 고객 현황 정리"],
    "연락": ["후속 연락 스크립트 작성", "응대 스크립트 작성"],
    "이탈": ["고객 이탈 위험 분석", "진행 고객 현황 정리"],
    "미팅": ["미팅 준비 질문 리스트 생성", "회의 아젠다 작성"],
    "보고서": ["영업 보고서 초안 작성", "보고서 초안 작성", "보고서 구조 작성"],
    "클레임": ["클레임 원인 정리", "재발 방지 체크리스트 작성"],
    "faq": ["FAQ 생성", "고객 문의 답변 초안 작성"],
    "납기": ["납기 리스크 분석", "일정 지연 리스크 정리"],
    "원가": ["원가 절감 아이디어 도출", "공급업체 비교 기준 작성"],
    "실험": ["실험 계획 초안 작성", "실험 변수 정리"],
    "품질": ["품질 이슈 보고서 초안 작성", "검사 기준 정리"],
    "감사": ["감사 대응 자료 구조 작성", "체크리스트 생성"],
    "병목": ["병목 원인 분석", "공정 개선 아이디어 도출"],
    "kpi": ["KPI 점검표 생성", "부서별 이슈 요약"],
}


def _goal_key_for_department(department: str) -> str:
    normalized = (department or "").strip()
    if normalized in DEPARTMENT_GOALS:
        return normalized

    lowered = normalized.lower()
    for alias, goal_key in DEPARTMENT_ALIASES.items():
        if alias in lowered:
            return goal_key
    return "기타"


def suggest_goals(department: str, situation: str = "", problem: str = "") -> list[str]:
    """
    Return stable fallback goal candidates using department and keyword rules.

    This function never calls an external AI API.
    """
    goal_key = _goal_key_for_department(department)
    goals = list(DEPARTMENT_GOALS.get(goal_key, GENERAL_GOALS))
    text = f"{situation or ''} {problem or ''}".lower()

    prioritized: list[str] = []
    for keyword, candidates in KEYWORD_GOAL_PRIORITIES.items():
        if keyword in text:
            for candidate in candidates:
                if candidate in goals and candidate not in prioritized:
                    prioritized.append(candidate)

    return prioritized + [goal for goal in goals if goal not in prioritized]

DEFAULT_DEPARTMENT_GOALS = [
    "진행 고객 현황 정리",
    "견적 후속 연락 전략 작성",
    "고객 이탈 위험 분석",
    "이번 주 영업 보고서 초안 작성",
    "미팅 준비 질문 리스트 생성",
    "담당자별 액션 아이템 정리",
]


PAINPOINT_GOAL_TEMPLATES = {
    "budget": {
        "title": "예산/가격 대응 전략 작성",
        "description": "가격 부담이나 예산 이슈가 있는 고객에게 제시할 대응 방향을 정리합니다.",
    },
    "purchase_process": {
        "title": "구매/결재 프로세스 대응 계획 작성",
        "description": "구매 승인 지연이나 결재 단계에서 막힌 고객의 다음 대응 절차를 정리합니다.",
    },
    "switching_cost": {
        "title": "전환 장벽 해소 전략 작성",
        "description": "기존 제품, 재고, 사용 습관 때문에 전환이 어려운 고객의 설득 포인트를 정리합니다.",
    },
    "performance": {
        "title": "성능 우려 검증 질문 리스트 생성",
        "description": "성능, 정확도, 결과 품질에 대한 우려를 다음 미팅에서 확인할 질문으로 정리합니다.",
    },
    "compatibility": {
        "title": "호환성/사용성 확인 체크리스트 작성",
        "description": "사용 환경, 기존 장비, 운영 방식과 맞는지 확인할 체크리스트를 만듭니다.",
    },
    "delivery": {
        "title": "납기/재고 리스크 대응 전략 작성",
        "description": "납기, 재고, 일정 지연 가능성을 줄이기 위한 대응 순서와 안내 문구를 정리합니다.",
    },
    "trust": {
        "title": "신뢰 리스크 완화 액션 정리",
        "description": "고객의 신뢰 우려를 낮추기 위한 근거 자료, 확인 항목, 후속 액션을 정리합니다.",
    },
    "priority": {
        "title": "고객 관심도 신호 정리",
        "description": "고객의 관심도, 보류 사유, 다음 확인 사항을 정리합니다.",
    },
}


def sanitize_external_prompt_text(value: object) -> str:
    """Remove common sensitive fragments before building a copy-ready prompt."""
    text = str(value or "").strip()
    if not text:
        return ""

    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[이메일 제거]", text)
    text = re.sub(r"\b01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}\b", "[연락처 제거]", text)
    text = re.sub(r"\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b", "[연락처 제거]", text)
    text = re.sub(r"(?:₩\s*)?[\d,]+(?:\.\d+)?\s*원", "[금액 제거]", text)
    return text


def _as_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def _truncate(value: object, limit: int = 120) -> str:
    text = sanitize_external_prompt_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _line(label: str, value: object) -> str:
    text = sanitize_external_prompt_text(value)
    return f"- {label}: {text}" if text else ""


def _department_display(analysis) -> str:
    department = analysis.department
    company_name = getattr(getattr(department, "company", None), "name", "")
    department_name = getattr(department, "name", "") or "해당 부서"
    if company_name:
        return f"{company_name} / {department_name}"
    return department_name


def recommend_output_format(goal: str) -> str:
    """Recommend an output format from the selected goal text."""
    text = (goal or "").lower()
    rules = [
        (("우선순위", "순서", "먼저"), "실행 순서 표(대상/이슈/근거/다음 액션/기한)와 실행 체크리스트"),
        (("견적",), "견적 후속 실행 순서 표 + 고객별 연락 방향 + 메시지 초안"),
        (("연락", "스크립트", "메시지", "문구"), "상황별 후속 연락 메시지 초안 + 톤별 대안 + 실행 체크리스트"),
        (("보고서", "보고", "요약"), "보고서 목차 + 핵심 요약문 + 표 형식 액션 아이템"),
        (("분석", "원인", "이탈", "리스크"), "원인/영향/대응 표 + 확인 필요 사항"),
        (("체크리스트", "점검"), "체크리스트"),
        (("전략", "로드맵", "계획"), "실행 로드맵(실행 순서/담당/기한) + 리스크 대응표"),
        (("미팅", "질문", "준비"), "질문 리스트 + 미팅 준비자료 + 확인 체크리스트"),
    ]
    for keywords, output_format in rules:
        if any(keyword in text for keyword in keywords):
            return output_format
    return "표와 체크리스트 중심"


def summarize_department_analysis(analysis) -> dict:
    """Extract prompt-ready summary sections from an AIDepartmentAnalysis."""
    data = analysis.analysis_data or {}
    quote_data = analysis.quote_delivery_data or {}
    qd_insights = data.get("quote_delivery_insights") or {}

    current_situation = []
    if data.get("department_summary"):
        current_situation.append(sanitize_external_prompt_text(data["department_summary"]))

    for insight in _as_list(data.get("meeting_insights"))[:3]:
        if not isinstance(insight, dict):
            continue
        theme = insight.get("theme")
        details = insight.get("details")
        frequency = insight.get("frequency")
        text = " / ".join(
            sanitize_external_prompt_text(part)
            for part in (theme, details, frequency)
            if sanitize_external_prompt_text(part)
        )
        if text:
            current_situation.append(text)

    for key, label in (
        ("conversion_analysis", "견적 전환"),
        ("delivery_cycle", "납품 주기"),
        ("product_trends", "제품 트렌드"),
    ):
        line = _line(label, qd_insights.get(key))
        if line:
            current_situation.append(line)

    pain_points = []
    cards = list(analysis.painpoint_cards.order_by("-confidence_score", "-created_at")[:5])
    for card in cards:
        label = card.get_category_display() if hasattr(card, "get_category_display") else card.category
        pain_points.append(
            f"- {label}: {_truncate(card.hypothesis, 160)} "
            f"(확신도 {card.confidence_score})"
        )

    if not pain_points:
        for item in _as_list(data.get("painpoint_cards"))[:5]:
            if isinstance(item, dict) and item.get("hypothesis"):
                pain_points.append(f"- {_truncate(item.get('hypothesis'), 160)}")

    for stalled in _as_list(qd_insights.get("stalled_quotes"))[:3]:
        if not isinstance(stalled, dict):
            continue
        reason = stalled.get("possible_reason") or "확인 필요"
        suggestion = stalled.get("suggestion") or ""
        pain_points.append(f"- 미전환 견적: {_truncate(reason, 120)} / {_truncate(suggestion, 120)}")

    reference_conditions = []
    if analysis.analysis_period_start and analysis.analysis_period_end:
        reference_conditions.append(
            f"- 분석 기간: {analysis.analysis_period_start:%Y-%m-%d} ~ {analysis.analysis_period_end:%Y-%m-%d}"
        )
    reference_conditions.append(f"- 분석 데이터: 미팅 {analysis.meeting_count}건, 견적 {analysis.quote_count}건, 납품 {analysis.delivery_count}건")

    total_quotes = quote_data.get("total_quotes")
    converted_quotes = quote_data.get("converted_quotes")
    conversion_rate = quote_data.get("conversion_rate")
    total_deliveries = quote_data.get("total_deliveries")
    if total_quotes is not None:
        reference_conditions.append(
            f"- 견적/납품 현황: 총 견적 {total_quotes}건, 납품 전환 {converted_quotes or 0}건, 전환율 {conversion_rate or 0}%"
        )
    if total_deliveries is not None:
        reference_conditions.append(f"- 총 납품 기록: {total_deliveries}건")
    if quote_data.get("avg_delivery_interval_days"):
        reference_conditions.append(f"- 평균 납품 간격: {quote_data['avg_delivery_interval_days']}일")

    product_stats = quote_data.get("product_stats") or {}
    if isinstance(product_stats, dict) and product_stats:
        product_names = ", ".join(sanitize_external_prompt_text(name) for name in list(product_stats.keys())[:5])
        if product_names:
            reference_conditions.append(f"- 주요 제품 패턴 참고: {product_names}")

    missing_info = data.get("missing_info") or {}
    missing_items = _as_list(missing_info.get("items")) if isinstance(missing_info, dict) else []
    if missing_items:
        reference_conditions.append("- 확인 필요 정보: " + "; ".join(_truncate(item, 80) for item in missing_items[:4]))

    recommended_actions = []
    for action in _as_list(data.get("next_actions"))[:5]:
        if not isinstance(action, dict):
            continue
        action_text = action.get("action")
        reason = action.get("reason")
        priority = action.get("priority")
        parts = [
            sanitize_external_prompt_text(action_text),
            f"실행 필요도 {sanitize_external_prompt_text(priority)}" if priority else "",
            sanitize_external_prompt_text(reason),
        ]
        text = " / ".join(part for part in parts if part)
        if text:
            recommended_actions.append(f"- {text}")

    if not current_situation:
        current_situation.append("저장된 분석 요약이 부족합니다. 아래 참고 조건과 Pain Point를 기준으로 판단해 주세요.")
    if not pain_points:
        pain_points.append("- 명확한 Pain Point가 부족합니다. 확인 필요 사항을 먼저 정리해야 합니다.")
    if not reference_conditions:
        reference_conditions.append("- 참고 조건이 부족합니다. 분석 데이터 범위를 먼저 확인해야 합니다.")

    return {
        "department_name": _department_display(analysis),
        "current_situation": current_situation,
        "pain_points": pain_points,
        "reference_conditions": reference_conditions,
        "recommended_actions": recommended_actions,
    }


def _goal_from_painpoint(card) -> dict:
    hypothesis = sanitize_external_prompt_text(card.hypothesis)
    lowered = hypothesis.lower()
    if "견적" in lowered:
        title = "견적 후속 연락 전략 작성"
        description = "견적 요청 후 아직 발주로 이어지지 않은 고객에게 보낼 후속 연락 방향을 정리합니다."
    elif "미팅" in lowered or "질문" in lowered:
        title = "미팅 준비 질문 리스트 생성"
        description = "다음 미팅에서 확인해야 할 질문과 준비자료를 정리합니다."
    elif "우선" in lowered or "관심" in lowered:
        title = "고객 관심도 신호 정리"
        description = "고객의 관심도와 다음 확인 항목을 기준별로 정리합니다."
    else:
        template = PAINPOINT_GOAL_TEMPLATES.get(card.category, {})
        title = template.get("title", "핵심 문제 대응 액션 정리")
        description = template.get("description", "AI가 발견한 핵심 문제를 실행 가능한 액션으로 정리합니다.")

    return {
        "title": title,
        "description": description,
        "reason": f"{_truncate(hypothesis, 120)} 이슈가 확인되었기 때문입니다.",
        "source": "painpoint",
    }


def _goal_from_action(action: dict) -> dict | None:
    action_text = sanitize_external_prompt_text(action.get("action"))
    if not action_text:
        return None
    reason = sanitize_external_prompt_text(action.get("reason")) or "AI 분석의 추천 액션에 포함되어 있기 때문입니다."
    customer = sanitize_external_prompt_text(
        action.get("customer") or
        action.get("customer_name") or
        action.get("customerName")
    )
    title = _truncate(action_text, 46)
    if not any(keyword in title for keyword in ("작성", "정리", "분석", "생성", "계획", "전략")):
        title = f"{title} 실행계획 작성"
    return {
        "title": title,
        "description": "추천 액션을 바로 실행할 수 있도록 단계, 실행 필요도, 확인 항목을 정리합니다.",
        "reason": _truncate(reason, 140),
        "customer": customer,
        "source": "next_action",
    }


def _clean_customer_names(customer_names: object) -> list[str]:
    names = []
    for name in _as_list(customer_names):
        text = sanitize_external_prompt_text(name)
        if text and text not in names:
            names.append(text)
    return names


def _goal_customer(goal: dict, customer_names: list[str]) -> str:
    explicit = sanitize_external_prompt_text(
        goal.get("customer") or
        goal.get("customer_name") or
        goal.get("customerName") or
        goal.get("target_customer") or
        goal.get("targetCustomer")
    )
    if explicit:
        return explicit

    searchable = " ".join([
        sanitize_external_prompt_text(goal.get("title")),
        sanitize_external_prompt_text(goal.get("description")),
        sanitize_external_prompt_text(goal.get("reason")),
    ])
    for name in customer_names:
        if name and name in searchable:
            return name
    return customer_names[0] if customer_names else ""


def _goal_from_ai_recommendation(item: dict) -> dict | None:
    title = sanitize_external_prompt_text(item.get("title") or item.get("goal"))
    customer = sanitize_external_prompt_text(
        item.get("customer") or item.get("customer_name") or item.get("customerName")
    )
    if not title and customer:
        title = f"{customer} 후속 실행계획 작성"
    if not title:
        return None
    return {
        "title": title,
        "description": sanitize_external_prompt_text(item.get("description")) or "AI 분석이 추천한 고객별 목표입니다.",
        "reason": sanitize_external_prompt_text(item.get("reason")) or "AI 분석 결과에서 후속 확인 대상으로 판단되었습니다.",
        "customer": customer,
        "source": item.get("source", "ai_recommendation"),
    }


def suggest_goals_from_department_analysis(analysis, limit: int = 6, customer_names: object = None) -> list[dict]:
    """Create goal cards from PainPointCard, next_actions, and fallbacks."""
    cards: list[dict] = []
    seen: set[str] = set()
    customer_names = _clean_customer_names(customer_names)

    def add_goal(goal: dict):
        title = sanitize_external_prompt_text(goal.get("title"))
        customer = _goal_customer(goal, customer_names)
        if customer and customer not in title:
            title = f"{customer} - {title}"
        seen_key = f"{customer}|{title}"
        if not title or seen_key in seen:
            return
        seen.add(seen_key)
        cards.append({
            "title": title,
            "description": sanitize_external_prompt_text(goal.get("description")),
            "reason": sanitize_external_prompt_text(goal.get("reason")),
            "customer": customer,
            "source": goal.get("source", "fallback"),
        })

    data = analysis.analysis_data or {}
    for item in _as_list(data.get("recommended_goals")):
        if isinstance(item, dict):
            goal = _goal_from_ai_recommendation(item)
            if goal:
                add_goal(goal)

    for card in analysis.painpoint_cards.order_by("-confidence_score", "-created_at")[:limit]:
        add_goal(_goal_from_painpoint(card))

    for action in _as_list(data.get("next_actions")):
        if not isinstance(action, dict):
            continue
        goal = _goal_from_action(action)
        if goal:
            add_goal(goal)

    qd_insights = data.get("quote_delivery_insights") or {}
    if _as_list(qd_insights.get("stalled_quotes")):
        add_goal({
            "title": "견적 후속 연락 전략 작성",
            "description": "미전환 견적의 후속 연락 방향과 다음 액션을 정리합니다.",
            "reason": "미전환 견적 또는 확인 필요 견적이 분석 결과에 포함되어 있기 때문입니다.",
            "source": "quote_delivery",
        })

    department_name = getattr(analysis.department, "name", "")
    for title in suggest_goals(department_name):
        add_goal({
            "title": title,
            "description": "부서 업무 흐름에 맞춰 바로 사용할 수 있는 산출물을 만듭니다.",
            "reason": f"{sanitize_external_prompt_text(department_name) or '해당 부서'} 업무에 일반적으로 유용한 목표입니다.",
            "source": "department_fallback",
        })

    for title in DEFAULT_DEPARTMENT_GOALS:
        add_goal({
            "title": title,
            "description": "영업 분석 결과를 실무 액션으로 바꾸기 위한 기본 목표입니다.",
            "reason": "분석 데이터가 부족할 때도 사용할 수 있는 기본 추천 목표입니다.",
            "source": "general_fallback",
        })

    return cards[:limit]


def build_prompt_from_department_analysis(analysis, selected_goal=None, custom_goal=None) -> str:
    """Build a copy-ready prompt from stored department AI analysis."""
    custom_goal = sanitize_external_prompt_text(custom_goal)
    selected_goal = sanitize_external_prompt_text(selected_goal)
    goal = custom_goal or selected_goal
    if not goal:
        raise ValueError("selected_goal 또는 custom_goal이 필요합니다.")

    summary = summarize_department_analysis(analysis)
    output_format = recommend_output_format(goal)

    def join_lines(lines: list[str]) -> str:
        return "\n".join(sanitize_external_prompt_text(line) for line in lines if sanitize_external_prompt_text(line))

    return f"""# 역할
너는 {summary['department_name']} 업무를 이해하는 B2B 업무 컨설턴트이자 실무 지원 AI다.

# 부서 분석 요약
{join_lines(summary['current_situation'])}

# 핵심 문제
{join_lines(summary['pain_points'])}

# 참고 조건
{join_lines(summary['reference_conditions'])}

# 목표
{goal}

# 요청사항
위 분석 내용을 바탕으로 목표를 수행해줘.

# 출력 형식
{output_format}

# 주의사항
- 추측은 구분해서 표시해줘.
- 실행 가능한 항목 위주로 작성해줘.
- 표나 체크리스트를 활용해줘.
- 바로 실무에 사용할 수 있게 작성해줘.
- 외부 AI에 붙여넣기 전 고객 개인정보, 연락처, 계약금액 등 민감정보는 제거해야 한다."""
