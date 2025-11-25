"""
OpenAI GPT API 통합 유틸리티
- 이메일 자동 생성/변환
- 고객 분석 및 요약
- 일정 추천
- 감정 분석

모델 선택 전략:
- GPT-4o-mini: 일상 이메일, 짧은 문구, 요약, 팔로우업, 내부용 기록 (빠르고 저렴)
- GPT-4o: 외부 고객 보고서, 장문 생성, 전문 기술 설명 (고품질)
"""
from openai import OpenAI
from django.conf import settings
import logging
import json
from typing import Dict, List, Optional, Literal

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 (lazy initialization)
_client = None

def get_openai_client():
    """OpenAI 클라이언트 가져오기 (lazy initialization)"""
    global _client
    if _client is None:
        # API 키 확인
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        # 최소한의 인자만 사용하여 초기화
        _client = OpenAI(api_key=api_key)
        logger.info(f"OpenAI client initialized with key: {api_key[:20]}...")
    return _client

# 모델 선택 상수 (환경 변수에서 로드)
MODEL_MINI = settings.OPENAI_MODEL_MINI  # 빠르고 저렴, 일반 용도
MODEL_STANDARD = settings.OPENAI_MODEL_STANDARD  # 고품질, 전문 문서

# 톤 설정
TONE_PROMPTS = {
    'formal': """현대적이고 전문적인 비즈니스 어조를 사용합니다. 
    - 인사: "안녕하세요 [고객명]님" (존경하는 X, 귀하 같은 구시대 표현 금지)
    - 마무리: "[발신자명] 드림." (올림 X)
    - 정중하되 자연스럽고 읽기 편한 문장
    - 과도한 겸양 표현 지양
    - 문단 사이 줄바꿈은 한 줄만 (<br> 한 번, <br><br><br><br> 같은 과도한 줄바꿈 금지)
    - 2020년대 B2B 이메일 표준 준수""",
    
    'casual': """친근하면서도 프로페셔널한 어조로 작성합니다.
    - 과도한 존댓말은 줄이고 대화하듯 자연스럽게
    - 문장을 간결하게 연결
    - 접근하기 쉬운 톤이지만 신뢰성은 유지
    - "안녕하세요", "~입니다", "~주세요" 수준의 존댓말""",
    
    'simple': """핵심만 간결하게 전달하는 명확한 어조입니다.
    - 불필요한 수식어와 인사말 최소화
    - 짧고 명확한 문장 사용
    - 요점만 빠르게 전달
    - 기본 예의는 유지"""
}


def check_ai_permission(user) -> bool:
    """사용자의 AI 기능 사용 권한 확인"""
    try:
        return user.userprofile.can_use_ai
    except AttributeError:
        return False


def generate_email(
    purpose: str,
    context: Dict,
    tone: Literal['formal', 'casual', 'simple'] = 'formal',
    user=None
) -> Dict[str, str]:
    """
    이메일 자동 생성
    
    Args:
        purpose: 이메일 목적 ('compose', 'reply')
        context: 컨텍스트 정보 (고객명, 회사명, 제품, 일정 등)
        tone: 어조 선택
        user: 요청 사용자
    
    Returns:
        {'subject': 제목, 'body': 본문}
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    tone_instruction = TONE_PROMPTS.get(tone, TONE_PROMPTS['formal'])
    
    # 발신자 정보 (현재 로그인한 사용자)
    sender_name = ""
    if user:
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            sender_name = f"{user.first_name}{user.last_name}"
        if not sender_name:
            sender_name = user.username
    
    if purpose == 'compose':
        system_prompt = f"""당신은 2020년대 한국 B2B 과학 장비 영업 전문가입니다.
과학 장비 및 실험실 제품을 판매하는 영업사원의 이메일을 작성해주세요.

{tone_instruction}

절대 금지 사항:
- 구시대 표현: "존경하는", "귀하", "귀사", "~올림", "~배상"
- 임의의 이름 생성 (김영수, 이철수 등)
- 과도한 줄바꿈 (<br><br><br><br> 금지, 문단 사이 <br> 한 번만)

필수 준수:
- 인사: "안녕하세요 [실제 고객명]님," (고객명이 제공된 경우)
- 마무리: "{sender_name} 드림." (반드시 이 이름 사용)
- 문단 간격: 한 줄 (<br> 한 번)

이메일은 한국어로 작성하며, 제목과 본문을 명확히 구분해주세요.
응답은 JSON 형식으로 제공해야 합니다."""

        user_prompt = f"""
다음 정보를 바탕으로 영업 이메일을 작성해주세요:

고객명: {context.get('customer_name', '고객')}
회사명: {context.get('company_name', '')}
제품/서비스: {context.get('product', '')}
일정 내용: {context.get('schedule_content', '')}
추가 메모: {context.get('notes', '')}

중요: 
- 고객명이 제공된 경우 반드시 실제 고객명을 사용하세요. [이름], [직함] 같은 플레이스홀더를 절대 사용하지 마세요.
- 발신자명은 반드시 "{sender_name}"을 사용하세요. 다른 이름을 만들어내지 마세요.
- 줄바꿈은 문단 사이 한 줄만 사용하세요. 과도한 공백을 만들지 마세요.

응답은 반드시 다음 JSON 형식으로 작성하세요:
{{
  "subject": "이메일 제목",
  "body": "이메일 본문 (HTML 형식, 자연스러운 문단 구성)"
}}
"""
    
    elif purpose == 'reply':
        
        system_prompt = f"""당신은 2020년대 한국 B2B 영업 전문가입니다.
받은 이메일에 대한 답장을 작성해주세요.

{tone_instruction}

절대 금지 사항:
- 구시대 표현: "존경하는", "귀하", "~올림"
- 임의의 이름 생성 (김영수, 이철수 등)
- 과도한 줄바꿈 (<br><br><br><br> 금지, 문단 사이 <br> 한 번만)

필수 준수:
- 인사: "안녕하세요 [실제 고객명]님," (고객명이 제공된 경우)
- 마무리: "{sender_name} 드림." (반드시 이 이름 사용)
- 문단 간격: 한 줄 (<br> 한 번)

답장은 한국어로 작성하며, 제목과 본문을 명확히 구분해주세요.
응답은 JSON 형식으로 제공해야 합니다."""

        # 고객 정보 구성
        customer_info = ""
        if context.get('customer_name'):
            customer_info += f"고객명: {context.get('customer_name')}\n"
        if context.get('company_name'):
            customer_info += f"회사명: {context.get('company_name')}\n"
        if context.get('product'):
            customer_info += f"제품: {context.get('product')}\n"

        user_prompt = f"""
다음 이메일에 대한 답장을 작성해주세요:

{customer_info if customer_info else ""}원본 제목: {context.get('original_subject', '')}
원본 내용: {context.get('original_body', '')}
답장 포인트: {context.get('reply_points', '긍정적으로 답변')}

중요: 
- 고객명이 제공된 경우 반드시 실제 고객명을 사용하세요. [이름], [직함] 같은 플레이스홀더를 절대 사용하지 마세요.
- 발신자명은 반드시 "{sender_name}"을 사용하세요. 다른 이름을 만들어내지 마세요.
- 줄바꿈은 문단 사이 한 줄만 사용하세요. 과도한 공백을 만들지 마세요.

응답은 반드시 다음 JSON 형식으로 작성하세요:
{{
  "subject": "Re: 제목",
  "body": "답장 본문 (HTML 형식)"
}}
"""
    
    else:
        raise ValueError(f"Unknown purpose: {purpose}")
    
    # 외부 고객 이메일은 고품질 모델 사용
    model = MODEL_STANDARD if tone == 'formal' else MODEL_MINI
    
    try:
        response = get_openai_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Email generated successfully for {purpose} using {model}")
        return result
    
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise


def transform_email(
    original_content: str,
    tone: Literal['formal', 'casual', 'simple'] = 'formal',
    instructions: Optional[str] = None,
    user=None
) -> str:
    """
    기존 이메일 내용을 다른 톤으로 변환
    
    Args:
        original_content: 원본 이메일 내용
        tone: 변환할 어조
        instructions: 추가 지시사항
        user: 요청 사용자
    
    Returns:
        변환된 이메일 본문
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    tone_instruction = TONE_PROMPTS.get(tone, TONE_PROMPTS['formal'])
    
    system_prompt = f"""당신은 2020년대 한국 B2B 과학 장비 영업 전문가입니다.
주어진 이메일 내용을 다음 스타일로 다시 작성해주세요:

{tone_instruction}

절대 금지 표현:
- "존경하는 OOO", "귀하", "귀사", "~올림", "~배상" 같은 구시대 표현
- 과도하게 겸손하거나 고루한 표현

권장 표현:
- 인사: "안녕하세요 [이름] [직함]님"
- 마무리: "[이름] 드림."
- 자연스럽고 현대적인 존댓말

중요: 
- 원본의 핵심 내용, 구조, 전문성은 반드시 유지
- B2B 비즈니스 맥락에 맞는 적절한 격식 수준 유지
- 과도한 줄바꿈 지양, 자연스러운 문단 구성
- 불필요한 수식어만 제거하고 필수 정보는 모두 포함
응답은 JSON 형식으로 제공해야 합니다."""

    user_prompt = f"""
다음 이메일을 재작성해주세요:

{original_content}

{f'추가 요청사항: {instructions}' if instructions else ''}

응답은 반드시 다음 JSON 형식으로 작성하세요:
{{
  "body": "변환된 이메일 본문 (HTML 형식, <p> 태그 사용, 적절한 줄바꿈)"
}}
"""
    
    # 포멀 톤 변환은 고품질 모델 사용
    model = MODEL_STANDARD if tone == 'formal' else MODEL_MINI
    
    try:
        response = get_openai_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Email transformed successfully using {model}")
        return result.get('body', '')
    
    except Exception as e:
        logger.error(f"Error transforming email: {e}")
        raise


def generate_customer_summary(customer_data: Dict, user=None) -> str:
    """
    고객 정보를 분석하여 요약 리포트 생성
    
    Args:
        customer_data: 고객 데이터 (히스토리, 견적, 구매 등)
        user: 요청 사용자
    
    Returns:
        마크다운 형식의 고객 요약 리포트
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 B2B 과학실험실 장비 영업 분석 전문가입니다.
10년 이상의 영업 경력을 바탕으로 고객 데이터를 분석하여 실질적이고 구체적인 인사이트를 제공합니다.

다음 항목을 포함한 요약 리포트를 작성해주세요:
1. 고객 개요
2. 최근 활동 요약
3. 구매 가능성 평가 (구체적인 근거 포함)
4. 주요 장애 요인 또는 리스크
5. 추천 팔로우업 액션 (실전 영업 전략)

**추천 팔로우업 액션 작성 시 주의사항:**
- 뻔한 조언(이메일 보내기, 정기 미팅 등)은 피하세요
- 고객의 구매 패턴과 업종 특성을 반영한 타이밍 전략을 제시하세요
- 구체적인 상품/서비스 제안이나 프로모션 아이디어를 포함하세요
- 경쟁사 대비 우위를 점할 수 있는 차별화된 접근법을 제안하세요
- 고객의 예산 주기(학교/연구소는 회계연도 등)를 고려한 전략을 제시하세요
- 실제 영업 현장에서 바로 실행 가능한 구체적인 액션을 3-4개로 압축하세요

마크다운 형식으로 작성하고, 구체적인 날짜와 수치를 포함해주세요."""

    user_prompt = f"""
다음 고객 정보를 분석해주세요:

고객명: {customer_data.get('name', '')}
회사: {customer_data.get('company', '')}
업종: {customer_data.get('industry', '')} (대학/연구소는 회계연도 예산 특성 고려 필요)

최근 6개월 활동:
- 미팅 횟수: {customer_data.get('meeting_count', 0)}회
- 견적 횟수: {customer_data.get('quote_count', 0)}회  
- 구매 횟수: {customer_data.get('purchase_count', 0)}회
- 총 구매액: {customer_data.get('total_purchase', 0):,}원
- 마지막 연락일: {customer_data.get('last_contact', '정보 없음')}
- 이메일 교환: {customer_data.get('email_count', 0)}건

견적 내역: {customer_data.get('quotes', [])}
미팅 노트: {customer_data.get('meeting_notes', [])}

현재 고객 등급: {customer_data.get('customer_grade', '미분류')}
"""
    
    # 선결제 정보 추가 (있는 경우만)
    prepayment = customer_data.get('prepayment')
    if prepayment:
        user_prompt += f"""
선결제 현황:
- 총 잔액: {prepayment['total_balance']:,}원
- 선결제 건수: {prepayment['count']}건
- 최근 내역:
"""
        for detail in prepayment['details']:
            user_prompt += f"  * {detail['date']}: {detail['amount']:,}원 입금, 잔액 {detail['balance']:,}원"
            if detail['memo']:
                user_prompt += f" ({detail['memo']})"
            user_prompt += "\n"
    
    user_prompt += """
**분석 시 고려사항:**
- 구매 주기 패턴 (연구비 지급 시기, 학기 시작/종료 등)
- 견적 대비 구매 전환율
- 고객 응대 온도 변화 (미팅 노트 분석)
- Cross-selling/Up-selling 기회"""
    
    if prepayment:
        user_prompt += "\n- 선결제 잔액 활용 전략 (잔액 소진 유도, 추가 입금 제안 등)"

    
    # 고객 리포트는 외부 공유 가능성이 있으므로 고품질 모델 사용
    try:
        logger.info(f"Generating customer summary for {customer_data.get('name')}")
        logger.info(f"Using model: {MODEL_STANDARD}")
        
        response = get_openai_client().chat.completions.create(
            model=MODEL_STANDARD,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=0.7  # 창의적이고 실질적인 전략 제안을 위해 약간 높임
        )
        
        result = response.choices[0].message.content
        logger.info(f"Customer summary generated for {customer_data.get('name')} using {MODEL_STANDARD}")
        return result
    
    except Exception as e:
        logger.error(f"Error generating customer summary: {e}")
        logger.error(f"Customer data: {customer_data}")
        raise


def analyze_email_sentiment(email_content: str, user=None) -> Dict:
    """
    이메일 감정 분석 및 구매 가능성 예측
    
    Args:
        email_content: 이메일 내용
        user: 요청 사용자
    
    Returns:
        {
            'sentiment': 'positive'/'neutral'/'negative',
            'purchase_probability': 'high'/'medium'/'low',
            'urgency': 'immediate'/'soon'/'later',
            'keywords': [...],
            'recommendation': '추천 액션'
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 B2B 영업 커뮤니케이션 분석 전문가입니다.
이메일 내용을 분석하여 다음을 평가해주세요:
1. 감정 톤 (긍정/중립/부정)
2. 구매 가능성 (높음/중간/낮음)
3. 긴급도 (즉시/곧/나중)
4. 핵심 키워드
5. 추천 팔로우업 액션"""

    user_prompt = f"""
다음 이메일을 분석해주세요:

{email_content}

응답 형식 (JSON):
{{
  "sentiment": "positive|neutral|negative",
  "purchase_probability": "high|medium|low",
  "urgency": "immediate|soon|later",
  "keywords": ["키워드1", "키워드2", ...],
  "recommendation": "추천 액션 설명"
}}
"""
    
    # 감정 분석은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,  # 분석은 더 정확하게
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Email sentiment analyzed successfully using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing email sentiment: {e}")
        raise


def suggest_follow_ups(customer_list: List[Dict], user=None) -> List[Dict]:
    """
    고객 목록을 분석하여 팔로우업 우선순위 제안
    
    Args:
        customer_list: 고객 정보 리스트
        user: 요청 사용자
    
    Returns:
        우선순위가 매겨진 팔로우업 제안 리스트
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 영업 전략 컨설턴트입니다.
고객 데이터를 분석하여 팔로우업 우선순위를 제안해주세요.
다음 요소를 고려하세요:
1. 마지막 접촉 이후 경과 시간
2. 고객 등급 및 거래 규모
3. 진행 중인 기회 단계
4. 과거 구매 이력"""

    # 고객 정보를 간결하게 요약
    customer_summary = []
    for c in customer_list[:20]:  # 최대 20개만 분석
        customer_summary.append({
            'name': c.get('name'),
            'grade': c.get('grade'),
            'last_contact': c.get('last_contact'),
            'stage': c.get('stage'),
            'value': c.get('potential_value')
        })
    
    user_prompt = f"""
다음 고객들의 팔로우업 우선순위를 정해주세요:

{json.dumps(customer_summary, ensure_ascii=False, indent=2)}

응답 형식 (JSON):
{{
  "suggestions": [
    {{
      "customer_name": "고객명",
      "priority": "high|medium|low",
      "reason": "이유",
      "recommended_action": "추천 액션",
      "timing": "언제"
    }},
    ...
  ]
}}
"""
    
    # 팔로우업 제안은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Follow-up suggestions generated for {len(customer_list)} customers using {MODEL_MINI}")
        return result.get('suggestions', [])
    
    except Exception as e:
        logger.error(f"Error generating follow-up suggestions: {e}")
        raise


def natural_language_search(query: str, search_type: str = 'all', user=None) -> Dict:
    """
    자연어 검색 쿼리를 SQL 필터 조건으로 변환
    
    Args:
        query: 자연어 검색 쿼리 (예: "지난달 견적 준 고객 보여줘")
        search_type: 검색 대상 ('customers', 'schedules', 'opportunities', 'all')
        user: 요청 사용자
    
    Returns:
        {
            'filters': {...},  # Django ORM 필터 조건
            'interpretation': '쿼리 해석 설명'
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 CRM 시스템의 검색 쿼리 변환 전문가입니다.
사용자의 자연어 검색 요청을 Django ORM 필터 조건으로 변환해주세요.

사용 가능한 필드:
- 고객: name, company, customer_grade, last_contact_date
- 일정: schedule_type, start_date, end_date, content
- 기회: stage, potential_value, created_at
"""

    user_prompt = f"""
다음 검색 요청을 필터 조건으로 변환해주세요:
"{query}"

검색 대상: {search_type}

응답 형식 (JSON):
{{
  "filters": {{
    "field_name__lookup": "value",
    ...
  }},
  "interpretation": "쿼리 해석 설명"
}}

예시:
입력: "지난달 견적 준 고객"
출력:
{{
  "filters": {{
    "schedules__schedule_type": "quote",
    "schedules__created_at__gte": "2024-10-01",
    "schedules__created_at__lt": "2024-11-01"
  }},
  "interpretation": "2024년 10월에 견적 일정이 있는 고객을 검색합니다."
}}
"""
    
    # 검색 쿼리 변환은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Natural language query converted: {query} using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error converting natural language query: {e}")
        raise


def recommend_products(customer_data: Dict, user=None) -> List[Dict]:
    """
    고객의 구매 이력과 미팅 노트를 분석하여 상품 추천
    
    Args:
        customer_data: 고객 정보 (구매 이력, 미팅 노트, 관심사 등)
        user: 요청 사용자
    
    Returns:
        추천 상품 리스트
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 과학 장비 및 실험실 제품 전문가입니다.
고객의 구매 패턴과 관심사를 분석하여 관련 상품을 추천해주세요.
추천 이유를 명확히 설명하고, 우선순위를 매겨주세요."""

    user_prompt = f"""
다음 고객에게 추천할 상품을 제안해주세요:

고객명: {customer_data.get('name', '')}
업종: {customer_data.get('industry', '')}

과거 구매 내역:
{json.dumps(customer_data.get('purchase_history', []), ensure_ascii=False, indent=2)}

최근 미팅 노트:
{customer_data.get('meeting_notes', '')}

관심 키워드:
{customer_data.get('interest_keywords', [])}

응답 형식 (JSON):
{{
  "recommendations": [
    {{
      "product_name": "상품명",
      "category": "카테고리",
      "reason": "추천 이유",
      "priority": "high|medium|low",
      "cross_sell_items": ["관련 소모품1", "관련 소모품2"]
    }},
    ...
  ]
}}
"""
    
    # 상품 추천은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Product recommendations generated for {customer_data.get('name')} using {MODEL_MINI}")
        return result.get('recommendations', [])
    
    except Exception as e:
        logger.error(f"Error generating product recommendations: {e}")
        raise


def summarize_meeting_notes(meeting_notes: str, user=None) -> Dict:
    """
    미팅 노트 자동 요약 및 키워드 추출
    
    Args:
        meeting_notes: 미팅 기록 텍스트
        user: 요청 사용자
    
    Returns:
        {
            'summary': '3줄 요약',
            'key_points': [...],
            'action_items': [...],
            'keywords': {...}
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 영업 미팅 분석 전문가입니다.
미팅 노트를 분석하여 다음을 추출해주세요:
1. 3줄 요약 (핵심만)
2. 주요 포인트
3. 액션 아이템
4. 키워드 (예산, 납기, 결정권자, 문제점 등)"""

    user_prompt = f"""
다음 미팅 노트를 분석해주세요:

{meeting_notes}

응답 형식 (JSON):
{{
  "summary": "3줄 요약 텍스트",
  "key_points": ["포인트1", "포인트2", ...],
  "action_items": ["할일1", "할일2", ...],
  "keywords": {{
    "budget": "예산 관련 내용",
    "deadline": "납기 관련 내용",
    "decision_maker": "결정권자 정보",
    "pain_points": "고객의 문제점",
    "competitors": "경쟁사 언급"
  }}
}}
"""
    
    # 미팅 노트 요약은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Meeting notes summarized successfully using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error summarizing meeting notes: {e}")
        raise


def analyze_email_thread(emails: List[Dict], user=None) -> Dict:
    """
    일정별 이메일 왕복 분석
    
    Args:
        emails: 이메일 리스트 [{'sender': ..., 'body': ..., 'date': ...}, ...]
        user: 요청 사용자
    
    Returns:
        {
            'thread_summary': '전체 대화 요약',
            'customer_intent': '고객 의도 분석',
            'response_quality': '응답 품질 평가',
            'suggested_next_action': '다음 액션 제안',
            'sentiment_timeline': [...],
            'key_topics': [...]
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 이메일 커뮤니케이션 분석 전문가입니다.
이메일 왕복 내역을 분석하여:
1. 전체 대화 흐름 요약
2. 고객의 진짜 의도 파악
3. 우리의 응답 품질 평가
4. 다음에 취해야 할 액션
5. 감정 변화 추이
6. 주요 논의 주제"""

    # 이메일 스레드를 읽기 쉽게 포맷팅
    formatted_emails = []
    for i, email in enumerate(emails[:10], 1):  # 최대 10개
        formatted_emails.append(f"""
이메일 #{i}
발신: {email.get('sender', 'Unknown')}
날짜: {email.get('date', '')}
내용: {email.get('body', '')[:500]}  # 500자만
""")
    
    user_prompt = f"""
다음 이메일 왕복 내역을 분석해주세요:

{chr(10).join(formatted_emails)}

응답 형식 (JSON):
{{
  "thread_summary": "전체 대화 요약 (3-5문장)",
  "customer_intent": "고객의 진짜 의도",
  "response_quality": {{
    "score": 1-10,
    "feedback": "응답 품질 평가"
  }},
  "suggested_next_action": "다음 액션 제안",
  "sentiment_timeline": [
    {{"email_num": 1, "sentiment": "positive|neutral|negative", "note": "이유"}},
    ...
  ],
  "key_topics": ["주제1", "주제2", ...]
}}
"""
    
    # 이메일 스레드 분석은 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Email thread analyzed ({len(emails)} emails) using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing email thread: {e}")
        raise


def update_customer_grade_with_ai(customer_data: Dict, user=None) -> Dict:
    """
    GPT를 사용하여 고객 등급 업데이트
    
    Args:
        customer_data: 고객의 모든 활동 데이터
        user: 요청 사용자
    
    Returns:
        {
            'grade': 'A+|A|B|C|D',
            'score': 0-100,
            'reasoning': '등급 산정 이유',
            'factors': {
                'engagement': 0-100,
                'purchase_potential': 0-100,
                'relationship': 0-100,
                'responsiveness': 0-100
            }
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 B2B 고객 등급 평가 전문가입니다.
다음 기준으로 고객을 평가하고 A+, A, B, C, D 등급을 매겨주세요:

평가 요소:
1. Engagement (참여도): 미팅, 이메일 응답 빈도
2. Purchase Potential (구매 가능성): 과거 구매, 견적 진행 상황
3. Relationship (관계): 커뮤니케이션 품질, 장기 거래 가능성
4. Responsiveness (반응성): 응답 속도, 적극성

등급 기준:
- A+ (90-100): VIP, 즉시 구매 가능성 높음
- A (80-89): 우수 고객, 단기 구매 가능성
- B (60-79): 양호 고객, 중기 육성 필요
- C (40-59): 보통 고객, 장기 관리
- D (0-39): 저조 고객, 재검토 필요"""

    user_prompt = f"""
다음 고객의 등급을 평가해주세요:

고객명: {customer_data.get('name', '')}
회사: {customer_data.get('company', '')}

활동 내역 (최근 6개월):
- 미팅: {customer_data.get('meeting_count', 0)}회
- 이메일 교환: {customer_data.get('email_count', 0)}건
- 견적: {customer_data.get('quote_count', 0)}건
- 구매: {customer_data.get('purchase_count', 0)}회
- 총 구매액: {customer_data.get('total_purchase', 0):,}원
- 마지막 접촉: {customer_data.get('last_contact', '없음')}

커뮤니케이션 분석:
- 평균 응답 시간: {customer_data.get('avg_response_time', '알 수 없음')}
- 이메일 감정 톤: {customer_data.get('email_sentiment', '중립')}
- 미팅 노트 요약: {customer_data.get('meeting_summary', '')}

현재 진행 중인 기회:
{json.dumps(customer_data.get('opportunities', []), ensure_ascii=False, indent=2)}

응답 형식 (JSON):
{{
  "grade": "A+|A|B|C|D",
  "score": 0-100,
  "reasoning": "등급 산정 상세 이유 (3-5문장)",
  "factors": {{
    "engagement": 0-100,
    "purchase_potential": 0-100,
    "relationship": 0-100,
    "responsiveness": 0-100
  }},
  "recommendations": [
    "추천 액션1",
    "추천 액션2",
    ...
  ]
}}
"""
    
    # 고객 등급 평가는 내부용이므로 빠른 mini 모델 사용
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.4,  # 등급 평가는 일관성 중요
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Customer grade updated via AI for {customer_data.get('name')}: {result.get('grade')} using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error updating customer grade with AI: {e}")
        raise
