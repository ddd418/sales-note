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
  
  "next_action_feedback": {
    "original_action": "영업 담당자가 작성한 다음 액션 원문 (없으면 빈 문자열)",
    "evaluation": "good|weak|risky|missing",
    "feedback": "다음 액션에 대한 구체적 피드백 (1-3문장). 좋은 점, 보완할 점, 빠진 것을 짚어준다.",
    "suggested_actions": ["PainPoint 분석 기반으로 추천하는 구체적 다음 액션 1", "추천 액션 2", "추천 액션 3"]
  },
  
  "missing_info": {
    "items": ["누락 항목"],
    "questions": ["확인 질문"]
  }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━
다음 액션 피드백 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━

미팅록에 "다음 액션"이 있으면 반드시 next_action_feedback을 작성한다:
- **good**: 구체적이고 PainPoint 해소에 직접 연결된 액션
- **weak**: 방향은 맞으나 구체성 부족 (예: "다시 방문" → 언제, 무엇을 가지고?)
- **risky**: PainPoint를 악화시키거나 역효과 가능성이 있는 액션
- **missing**: 다음 액션이 비어있거나, 발견된 PainPoint 대비 누락된 대응이 있음

suggested_actions에는 분석된 PainPoint 기반으로 **영업 담당자가 바로 실행 가능한** 구체적 액션을 3개까지 제안한다.
예: "○○ 연구원에게 pH 측정 정확도 비교 자료(A사 vs 당사) PDF 전달" 수준의 구체성.

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


# ================================================
# 채팅 전용 시스템 프롬프트 (영업 코칭)
# ================================================

CHAT_SYSTEM_PROMPT = """너는 B2B 연구실 영업을 돕는 전문 영업 코치 AI다.

━━━ 역할 ━━━
- 이미 분석된 PainPoint 카드와 미팅록을 바탕으로, 영업 담당자의 **후속 질문에 실용적으로 답변**한다.
- 새로운 미팅 정보가 추가되면 기존 분석을 업데이트하거나 보완한다.

━━━ 핵심 원칙 ━━━
1. **팩트 기반**: 기존 분석/미팅록에서 확인된 사실만 근거로 사용
2. **실행 가능**: "~하세요"가 아니라 "다음 방문 시 이렇게 말하세요: ..." 수준의 구체적 액션
3. **간결함**: 핵심만 3-5문장으로 답변. 불필요한 반복 금지
4. **한국어**: 자연스러운 한국어로 대화

━━━ 답변 가능 주제 ━━━
- PainPoint별 대응 전략 / 화법 제안
- 다음 방문 시나리오 / 질문 리스트
- 경쟁사 대응 전략
- 견적/샘플 진행 조언
- CRM 스테이지 판단 근거
- 고객의 구매 신호 해석

━━━ 금지 사항 ━━━
- 미팅록에 없는 연구원 발언을 만들어내지 않는다
- 확인 안 된 고객 상황을 사실처럼 말하지 않는다
- JSON 형식으로 출력하지 않는다 (자연어 대화만)

━━━ 추가 미팅 정보가 입력된 경우 ━━━
사용자가 새로운 미팅/통화 내용을 공유하면:
1. 기존 PainPoint와의 연관성을 짚어준다
2. 확신도 변화가 있으면 알려준다 (예: "앞서 Low였던 budget PainPoint가 이번 발언으로 Med로 올라갈 수 있습니다")
3. 새롭게 발견된 PainPoint가 있으면 간단히 제안한다
"""


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
    영업 코칭 대화 - 기존 PainPoint 분석 결과를 컨텍스트로 활용
    자연어 대화로 후속 질문 / 전략 조언 제공
    """
    from ai_chat.models import AIChatMessage, PainPointCard
    
    client = get_openai_client()
    model = os.environ.get('OPENAI_MODEL_STANDARD', 'gpt-4o')

    # ---- 기존 분석 컨텍스트 구성 ----
    context_parts = []

    # 1) 고객 정보
    followup = room.followup
    context_parts.append(f"[고객 정보] {followup.customer_name} / {followup.department.name if followup.department else '부서 미정'} / {followup.company.name if followup.company else '회사 미정'}")

    # 2) 기존 PainPoint 카드 요약
    cards = PainPointCard.objects.filter(room=room).order_by('-confidence_score')
    if cards.exists():
        context_parts.append("\n[기존 PainPoint 분석 결과]")
        for card in cards:
            status_map = {'unverified': '미검증', 'confirmed': '✅확인', 'denied': '❌부정'}
            status = status_map.get(card.verification_status, '미검증')
            note = f" (메모: {card.verification_note})" if card.verification_note else ""
            context_parts.append(
                f"- [{card.get_category_display()}] {card.hypothesis} "
                f"(확신도: {card.confidence_score}점, {status}{note})"
            )
            if card.evidence:
                for ev in card.evidence[:2]:
                    context_parts.append(f"  근거: {ev.get('text', '')}")

    # 3) 최초 미팅록 분석의 원본 데이터 (첫 assistant 메시지의 structured_data)
    first_analysis = AIChatMessage.objects.filter(
        room=room, role='assistant', structured_data__isnull=False
    ).order_by('created_at').first()
    if first_analysis and first_analysis.structured_data:
        sd = first_analysis.structured_data
        if sd.get('summary_3lines'):
            context_parts.append("\n[미팅 3줄 요약]")
            for line in sd['summary_3lines']:
                context_parts.append(f"- {line}")
        if sd.get('signals', {}).get('researcher_quotes'):
            context_parts.append("\n[연구원 발언]")
            for q in sd['signals']['researcher_quotes'][:5]:
                context_parts.append(f"- 「{q.get('text', '')}」")
        if sd.get('missing_info', {}).get('items'):
            context_parts.append("\n[아직 확인 안 된 정보]")
            for item in sd['missing_info']['items']:
                context_parts.append(f"- {item}")

    context_text = "\n".join(context_parts)

    # ---- 이전 대화 히스토리 (최근 10개) ----
    previous_messages = AIChatMessage.objects.filter(
        room=room
    ).order_by('-created_at')[:10]

    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": f"[분석 컨텍스트]\n{context_text}\n\n위 분석 결과를 참고하여 이후 대화에 답변해주세요. 이 메시지에는 답변하지 말고, 다음 질문을 기다리세요."},
        {"role": "assistant", "content": "네, 분석 결과를 숙지했습니다. 질문해주세요."},
    ]

    # 이전 대화 추가 (역순 → 정순)
    for msg in reversed(list(previous_messages)):
        # 첫 분석 메시지(JSON)는 이미 컨텍스트로 포함했으므로 건너뜀
        if msg.role == 'assistant' and msg.structured_data and msg == first_analysis:
            continue
        messages.append({
            "role": msg.role,
            "content": msg.content if len(msg.content) < 2000 else msg.content[:2000] + "...(생략)"
        })

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
        )

        ai_text = response.choices[0].message.content
        token_usage = response.usage.total_tokens if response.usage else 0

        return ai_text, None, token_usage

    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {str(e)}")
        raise
