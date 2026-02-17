"""
AI PainPoint 생성기 - OpenAI 서비스
팩트 기반 분석을 강제하는 시스템 프롬프트 + API 호출
"""
import json
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# ================================================
# 시스템 프롬프트 (핵심: 소설 금지, 팩트 강제)
# ================================================

SYSTEM_PROMPT = """너는 B2B 연구실 영업 CRM의 "PainPoint 생성기" AI다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 규칙 (소설 금지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 입력 텍스트에 **명시적으로 적혀있는 문장**만 근거(Evidence)로 사용한다.
2. 입력에 없는 실험, 장비, 상황, 감정을 **절대 추측하거나 만들어내지 않는다**.
3. "~일 수 있다", "~할 가능성이 있다" 같은 추측은 반드시 「사용자 추측」으로 표시하고, 확신도를 Low로 내린다.
4. 근거가 1개도 없는 PainPoint는 **생성하지 않는다**.
5. 검증 질문은 연구원 앞에서 그대로 읽었을 때 "저희는 안 그런데요?"라는 반응이 나오지 않도록, **입력 텍스트에서 직접 확인된 사실만** 기반으로 작성한다.
6. Evidence 인용 시 반드시 따옴표(「」)로 원문을 짧게 인용하고, 어떤 섹션에서 왔는지 표시한다.
   예: 「재고가 너무 많이 쌓여...」 ← [연구원이 한 말]

━━━━━━━━━━━━━━━━━━━━━━━━━━━
확신도 기준 (엄격 적용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- **High (70-100)**: 직접 인용 + 사실 이벤트가 **동시에** 존재하고 반복 패턴이 명확
- **Med (40-69)**: 한 쪽만 강하거나 간접 시그널만 있음
- **Low (0-39)**: 단서가 약하거나 추측 비중이 큼. 반드시 "누락/확인 필요"에도 기재

━━━━━━━━━━━━━━━━━━━━━━━━━━━
PainPoint 카테고리 (고정 8종, 새 범주 생성 금지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. budget: 예산/가격
2. purchase_process: 결재/구매 프로세스(거래처/세금계산서/구매담당)
3. switching_cost: 전환 비용/재고 고착(이미 많이 쌓여있음/표준 고착)
4. performance: 성능/정확도(분주 오차/재현성/누수/끝맺힘)
5. compatibility: 호환성/사용성(팁 타이트/샤프트 마모/손목 피로)
6. delivery: 납기/재고(품절/긴급/대체 필요)
7. trust: 신뢰/리스크(인증/근거자료/책임소재/안전)
8. priority: 우선순위/관심(바쁨/관심 낮음/담당자 부재)

━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRM 스테이지 정의 (고정)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

신규접점 / 샘플대기 / 견적발송 / 결재대기 / 재방문예정 / 보류 / 종료

━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식 (반드시 이 순서, JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

반드시 아래 JSON 형식으로만 응답한다. JSON 외의 텍스트를 추가하지 않는다.

```json
{
  "summary_3lines": ["요약1", "요약2", "요약3"],
  
  "entities": {
    "people_org": ["연구원명/랩명 등"],
    "products": ["제품/브랜드/모델"],
    "volumes": ["볼륨대"],
    "competitors": ["경쟁사/현재 사용품"],
    "events": ["이벤트(샘플/견적/서비스 등)"],
    "channel_datetime": ["채널/일시"]
  },
  
  "signals": {
    "researcher_quotes": [
      {"text": "직접 인용 원문", "source_section": "연구원이 한 말"}
    ],
    "confirmed_facts": [
      {"text": "확인된 사실", "source_section": "내가 확인한 사실"}
    ],
    "user_guesses": [
      {"text": "추측/해석 내용", "source_section": "오늘 상황"}
    ]
  },
  
  "painpoint_cards": [
    {
      "category": "budget|purchase_process|switching_cost|performance|compatibility|delivery|trust|priority",
      "hypothesis": "가설 한 줄",
      "confidence": "high|med|low",
      "confidence_score": 75,
      "evidence": [
        {"type": "quote", "text": "「원문 인용」", "source_section": "[연구원이 한 말]"},
        {"type": "fact", "text": "확인된 사실", "source_section": "[내가 확인한 사실]"}
      ],
      "attribution": "individual|lab|purchase_route|institution",
      "verification_question": "다음 방문에서 그대로 읽을 질문",
      "action_if_yes": "맞으면 실행할 대응 패키지",
      "action_if_no": "아니면 다음 단계",
      "caution": "하면 역효과인 행동"
    }
  ],
  
  "crm_update": {
    "stage": "CRM 스테이지",
    "tags": ["태그1", "태그2"],
    "must_get_next_visit": "다음 방문에서 반드시 확보할 1개",
    "reminder": "리마인더/할 일"
  },
  
  "missing_info": {
    "items": ["누락 항목"],
    "questions": ["확인 질문"]
  }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━
최종 자기검증 (출력 전 반드시 체크)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

출력하기 전에 각 PainPoint 카드에 대해:
1. Evidence의 모든 인용이 실제 입력 텍스트에 존재하는가? → 없으면 삭제
2. 검증 질문을 연구원에게 그대로 읽었을 때 "안 그런데요?"라고 할 가능성은? → 높으면 수정 또는 확신도 Low로 하향
3. 입력에 없는 장비/실험/상황을 내가 만들어낸 부분은? → 있으면 삭제
"""


def get_openai_client():
    """OpenAI 클라이언트 생성"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


def build_user_prompt(followup, meeting_data):
    """
    미팅록 데이터로 유저 프롬프트 생성
    
    meeting_data는 딕셔너리:
    - situation: 오늘 상황
    - researcher_quote: 연구원이 한 말
    - confirmed_facts: 내가 확인한 사실
    - obstacles: 장애물/반대
    - next_action: 다음 액션
    - free_text: 자유 입력 (위 섹션들이 없을 때)
    - channel: 방문/통화/메일 등
    - visit_date: 방문일 (문자열)
    """
    researcher = followup.customer_name or '미정'
    lab = followup.department.name if followup.department else '미정'
    company = followup.company.name if followup.company else '미정'
    channel = meeting_data.get('channel', '방문')
    visit_date = meeting_data.get('visit_date', '')

    sections = []
    sections.append(f"연구원/랩: {researcher}, {lab} ({company})")
    sections.append(f"채널: {channel}")
    sections.append(f"일시: {visit_date}")
    sections.append("")
    sections.append("미팅록:")

    # 구조화된 섹션이 있으면 사용
    situation = meeting_data.get('situation', '').strip()
    researcher_quote = meeting_data.get('researcher_quote', '').strip()
    confirmed_facts = meeting_data.get('confirmed_facts', '').strip()
    obstacles = meeting_data.get('obstacles', '').strip()
    next_action = meeting_data.get('next_action', '').strip()
    free_text = meeting_data.get('free_text', '').strip()

    if situation:
        sections.append(f"\n오늘 상황:\n{situation}")
    if researcher_quote:
        sections.append(f"\n연구원이 한 말(직접 인용):\n{researcher_quote}")
    if confirmed_facts:
        sections.append(f"\n내가 확인한 사실:\n{confirmed_facts}")
    if obstacles:
        sections.append(f"\n장애물/반대:\n{obstacles}")
    if next_action:
        sections.append(f"\n다음 액션:\n{next_action}")

    # 구조화된 섹션이 모두 비어있으면 자유 텍스트 사용
    if not any([situation, researcher_quote, confirmed_facts, obstacles, next_action]):
        if free_text:
            sections.append(f"\n{free_text}")
        else:
            sections.append("\n(미팅록 내용 없음)")

    sections.append("\n주의: 위 텍스트 안에서만 근거를 찾아라. 없는 정보는 '누락/확인 필요'로 처리해라.")

    return "\n".join(sections)


def build_context_prompt(room):
    """이전 PainPoint 카드 + 검증 결과를 컨텍스트로 주입"""
    from ai_chat.models import PainPointCard
    
    previous_cards = PainPointCard.objects.filter(
        room=room
    ).exclude(
        verification_status='unverified'
    ).order_by('-created_at')[:5]

    if not previous_cards:
        return ""

    lines = ["\n━━━ 이전 분석 히스토리 (참고용) ━━━"]
    for card in previous_cards:
        status_map = {'confirmed': '✅확인됨', 'denied': '❌부정됨'}
        status = status_map.get(card.verification_status, '')
        lines.append(
            f"- [{card.get_category_display()}] {card.hypothesis} → {status}"
            f"{f' (메모: {card.verification_note})' if card.verification_note else ''}"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def analyze_meeting(room, meeting_data, followup):
    """
    미팅록을 분석하여 PainPoint 카드 생성
    
    Returns: (ai_response_text, structured_data, token_usage)
    """
    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')
    
    user_prompt = build_user_prompt(followup, meeting_data)
    context_prompt = build_context_prompt(room)
    
    if context_prompt:
        user_prompt = user_prompt + "\n" + context_prompt

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,  # 낮은 temperature = 더 팩트 기반
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        # JSON 파싱
        try:
            structured = json.loads(ai_text)
        except json.JSONDecodeError:
            structured = None
            logger.error(f"AI 응답 JSON 파싱 실패: {ai_text[:200]}")

        return ai_text, structured, token_usage

    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {str(e)}")
        raise


def chat_with_ai(room, user_message):
    """
    자유 대화 (미팅록 분석이 아닌 일반 질문)
    이전 대화 컨텍스트를 포함하여 전송
    """
    from ai_chat.models import AIChatMessage
    
    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')

    # 이전 대화 히스토리 (최근 20개)
    previous_messages = AIChatMessage.objects.filter(
        room=room
    ).order_by('-created_at')[:20]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 역순으로 가져왔으니 다시 정렬
    for msg in reversed(list(previous_messages)):
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
        )

        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        # JSON인지 판별
        structured = None
        try:
            structured = json.loads(ai_text)
        except (json.JSONDecodeError, TypeError):
            pass

        return ai_text, structured, token_usage

    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {str(e)}")
        raise
