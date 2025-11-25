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
        
        # Railway 환경에서 프록시 문제 해결을 위해 http_client 명시적 설정
        try:
            import httpx
            # 프록시 설정 없이 httpx 클라이언트 생성
            http_client = httpx.Client(
                timeout=60.0,
                follow_redirects=True
            )
            _client = OpenAI(
                api_key=api_key,
                http_client=http_client
            )
            logger.info(f"OpenAI client initialized with custom http_client")
        except Exception as e:
            # httpx 설정 실패 시 기본 클라이언트 사용
            logger.warning(f"Failed to create custom http_client: {e}, using default")
            _client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI client initialized with default settings")
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
        # 관리자는 AI 기능 사용 불가
        if hasattr(user, 'userprofile') and user.userprofile.role == 'admin':
            return False
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


def suggest_follow_ups(customer_list: List[Dict], user=None) -> List[Dict]:
    """
    여러 고객 데이터를 분석하여 팔로우업 우선순위 제안
    
    Args:
        customer_list: 고객 데이터 리스트 [
            {
                'id': 고객 ID,
                'name': 고객명,
                'company': 회사명,
                'last_contact': 마지막 연락일,
                'meeting_count': 미팅 횟수,
                'quote_count': 견적 횟수,
                'purchase_count': 구매 횟수,
                'total_purchase': 총 구매액,
                'grade': 고객 등급,
                'opportunities': 진행 중인 기회,
                'prepayment_balance': 선결제 잔액
            },
            ...
        ]
        user: 요청 사용자
    
    Returns:
        우선순위 정렬된 고객 리스트 [
            {
                'customer_id': 고객 ID,
                'customer_name': 고객명,
                'priority_score': 우선순위 점수 (1-100),
                'priority_level': 'urgent'/'high'/'medium'/'low',
                'reason': 우선순위 이유,
                'suggested_action': 제안 액션,
                'best_contact_time': 최적 연락 시간
            },
            ...
        ]
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 B2B 영업 전략 전문가입니다.
고객 데이터를 분석하여 오늘 우선적으로 연락해야 할 고객을 추천해주세요.

**우선순위 평가 기준:**
1. 마지막 연락 경과 시간 (장기 미접촉 고객)
2. 진행 중인 기회의 단계 (클로징 단계 우선)
3. 구매 패턴 및 예상 재구매 시기
4. 고객 등급 (VIP, A 등급 우선)
5. 선결제 잔액 (소진 유도 필요)
6. 견적 후 미구매 기간

**연락 타이밍 전략:**
- 대학/연구소: 학기 시작 전, 예산 집행 시기
- 일반 기업: 분기 초, 회계연도 초
- 긴급한 경우: 즉시 연락
- 일반적인 경우: 오전 10-11시, 오후 2-3시 추천

응답 형식 (JSON 배열):
[
  {
    "customer_id": 고객ID,
    "customer_name": "고객명",
    "priority_score": 85,
    "priority_level": "urgent|high|medium|low",
    "reason": "우선순위 이유 (구체적으로)",
    "suggested_action": "제안 액션 (구체적으로)",
    "best_contact_time": "최적 연락 시간"
  },
  ...
]

우선순위 점수가 높은 순으로 정렬해서 반환하세요."""

    # 고객 데이터를 요약 형식으로 변환
    customer_summary = []
    for customer in customer_list[:20]:  # 최대 20명만 분석
        summary = f"""
고객 ID: {customer.get('id')}
고객명: {customer.get('name', '미정')}
회사: {customer.get('company', '미정')}
마지막 연락: {customer.get('last_contact', '정보 없음')}
미팅: {customer.get('meeting_count', 0)}회
견적: {customer.get('quote_count', 0)}회
구매: {customer.get('purchase_count', 0)}회
총 구매액: {customer.get('total_purchase', 0):,}원
등급: {customer.get('grade', '미분류')}
진행 중인 기회: {len(customer.get('opportunities', []))}건
선결제 잔액: {customer.get('prepayment_balance', 0):,}원
"""
        customer_summary.append(summary)
    
    user_prompt = f"""
다음 {len(customer_list)}명의 고객 중 오늘 우선적으로 연락해야 할 고객을 추천해주세요:

{chr(10).join(customer_summary)}

우선순위가 높은 순서대로 최대 10명을 추천해주세요.
"""
    
    # 우선순위 제안은 빠른 mini 모델 사용
    try:
        logger.info(f"Suggesting follow-up priorities for {len(customer_list)} customers")
        
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
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # 결과가 배열이 아니라 객체로 래핑되어 있을 수 있음
        if isinstance(result, dict) and 'recommendations' in result:
            suggestions = result['recommendations']
        elif isinstance(result, dict) and 'priorities' in result:
            suggestions = result['priorities']
        elif isinstance(result, list):
            suggestions = result
        else:
            suggestions = []
        
        logger.info(f"Generated {len(suggestions)} follow-up suggestions")
        return suggestions
    
    except Exception as e:
        logger.error(f"Error suggesting follow-ups: {e}")
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


def analyze_email_thread(emails: List[Dict], user=None) -> Dict:
    """
    이메일 스레드 전체를 분석하여 고객 온도와 구매 가능성 측정
    
    Args:
        emails: 이메일 리스트 [
            {
                'date': '2024-01-01',
                'from': '발신자',
                'subject': '제목',
                'body': '내용'
            },
            ...
        ]
        user: 요청 사용자
    
    Returns:
        {
            'overall_sentiment': 'positive'/'neutral'/'negative',
            'temperature': 'hot'/'warm'/'cold',  # 고객 온도
            'purchase_probability': 'high'/'medium'/'low',
            'engagement_level': 'high'/'medium'/'low',  # 참여도
            'key_topics': [...],  # 주요 논의 주제
            'concerns': [...],  # 우려사항
            'opportunities': [...],  # 기회
            'next_action': '다음 액션 제안',
            'summary': '스레드 요약'
        }
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    system_prompt = """당신은 B2B 영업 커뮤니케이션 분석 전문가입니다.
이메일 스레드를 분석하여 고객 관계의 현재 상태와 구매 가능성을 평가해주세요.

**분석 요소:**
1. 감정 톤 변화 (시간 경과에 따라)
2. 고객 온도 (hot/warm/cold)
   - Hot: 적극적, 빠른 응답, 구체적 질문
   - Warm: 관심 있음, 정보 수집 단계
   - Cold: 반응 느림, 소극적, 회피적
3. 구매 신호 감지 (가격 문의, 일정 협의, 결정권자 언급 등)
4. 우려사항 및 장애요인
5. Cross-selling/Up-selling 기회

응답 형식 (JSON):
{
  "overall_sentiment": "positive|neutral|negative",
  "temperature": "hot|warm|cold",
  "purchase_probability": "high|medium|low",
  "engagement_level": "high|medium|low",
  "key_topics": ["주제1", "주제2", ...],
  "concerns": ["우려1", "우려2", ...],
  "opportunities": ["기회1", "기회2", ...],
  "next_action": "구체적인 다음 액션 제안",
  "summary": "스레드 전체 요약 (3-5문장)"
}"""

    # 이메일 스레드를 시간순으로 정렬하여 텍스트로 변환
    thread_text = ""
    for email in sorted(emails, key=lambda x: x.get('date', '')):
        thread_text += f"""
날짜: {email.get('date', '날짜 없음')}
발신: {email.get('from', '발신자 없음')}
제목: {email.get('subject', '제목 없음')}
내용:
{email.get('body', '내용 없음')}

---
"""
    
    user_prompt = f"""
다음 이메일 스레드를 분석해주세요 (총 {len(emails)}개 메일):

{thread_text}

고객과의 관계 온도, 구매 가능성, 다음 액션을 평가해주세요.
"""
    
    # 스레드 분석은 중요하므로 standard 모델 사용
    try:
        logger.info(f"Analyzing email thread with {len(emails)} emails")
        
        response = get_openai_client().chat.completions.create(
            model=MODEL_STANDARD,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Email thread analyzed successfully using {MODEL_STANDARD}")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing email thread: {e}")
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
    
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    system_prompt = f"""당신은 CRM 시스템의 검색 쿼리 변환 전문가입니다.
사용자의 자연어 검색 요청을 Django ORM 필터 조건으로 변환해주세요.

🔍 현재 날짜: {current_date}

📋 사용 가능한 모델 필드 (실제 DB 스키마):

**FollowUp (고객) 모델:**
- customer_name (고객명)
- company (관계: Company 객체)
- customer_grade (등급: A+, A, B, C, D)
- email, phone_number, address
- manager (담당자명)
- priority (우선순위)
- created_at, updated_at

**Schedule (일정) 모델:**
- followup (관계: FollowUp 객체)
- activity_type (활동 유형: 'customer_meeting', 'quote', 'delivery', 'call', 'email' 등)
- visit_date (방문/일정 날짜)
- visit_time (시간)
- notes (노트/메모)
- status (상태)
- created_at, updated_at

**OpportunityTracking (영업기회) 모델:**
- followup (관계: FollowUp 객체)
- title (제목)
- current_stage (현재 단계: 'lead', 'contact', 'quote', 'closing', 'won', 'lost')
- expected_revenue (예상 금액)
- expected_close_date (예상 종료일)
- probability (확률)
- created_at, updated_at

⚠️ 중요 규칙:
1. **필드명은 위에 명시된 것만 사용** (예: last_contact_date 같은 존재하지 않는 필드 사용 금지)
2. 날짜 조회는 관련 모델을 통해 접근:
   - "최근 연락": schedules__visit_date__gte 사용 (고객 모델에서)
   - "마지막 견적": schedules__activity_type='quote' + schedules__visit_date 조합 (고객 모델에서)
   - 일정 모델에서는 schedules__ 접두사 없이 visit_date 직접 사용
3. 관계 조회는 던더스코어(__) 사용:
   - 고객의 일정: schedules__field_name (FollowUp 모델에서만!)
   - 일정의 고객: followup__field_name
4. 날짜 lookup: __gte (이상), __lte (이하), __range (범위)
5. 문자열 lookup: __icontains (포함), __exact (정확히), __iexact (대소문자 무시)
6. **검색 대상에 따라 다른 필터 사용**:
   - customers 검색: schedules__ 접두사 사용 가능
   - schedules 검색: schedules__ 접두사 사용 불가 (직접 필드명만)
   - opportunities 검색: followup__ 접두사로 고객 정보 접근
"""

    user_prompt = f"""
다음 검색 요청을 Django ORM 필터 조건으로 변환해주세요:
"{query}"

검색 대상: {search_type}

응답 형식 (JSON):
{{
  "filters": {{
    "field_name__lookup": "value",
    ...
  }},
  "interpretation": "쿼리 해석 설명 (한국어)"
}}

예시 1 - 고객 검색:
입력: "지난달 견적 준 고객"
출력:
{{
  "filters": {{
    "schedules__activity_type": "quote",
    "schedules__visit_date__gte": "2024-10-01",
    "schedules__visit_date__lt": "2024-11-01"
  }},
  "interpretation": "2024년 10월에 견적 일정이 있는 고객을 검색합니다."
}}

예시 2 - 기간 검색:
입력: "3개월 이상 연락 안 한 A등급 고객"
출력:
{{
  "filters": {{
    "customer_grade": "A",
    "schedules__visit_date__lt": "2024-08-25"
  }},
  "interpretation": "A등급 고객 중 2024년 8월 25일 이전에 마지막으로 연락한 고객을 검색합니다."
}}

예시 3 - 활동 유형 (고객 검색):
입력: "저번에 견적 드렸는데 아직 연락 없는 고객"
출력:
{{
  "filters": {{
    "schedules__activity_type": "quote"
  }},
  "interpretation": "견적 일정이 있는 고객을 검색합니다."
}}

예시 4 - 일정 직접 검색:
입력: "이번 달 견적 일정"
출력:
{{
  "filters": {{
    "activity_type": "quote",
    "visit_date__gte": "2024-11-01",
    "visit_date__lt": "2024-12-01"
  }},
  "interpretation": "2024년 11월의 견적 일정을 검색합니다."
}}

⚠️ 주의:
- 고객(customers) 검색할 때만 schedules__ 접두사 사용
- 일정(schedules) 검색할 때는 schedules__ 사용 안 함
- __isnull 같은 복잡한 lookup은 사용하지 말 것
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
    고객의 구매 이력, 미팅 노트, 견적 이력을 종합 분석하여 상품 추천
    구매 이력이 없어도 미팅/견적 내용을 기반으로 추천 가능
    
    Args:
        customer_data: 고객 정보 (구매 이력, 미팅 노트, 견적 이력, 관심사 등)
        user: 요청 사용자
    
    Returns:
        추천 상품 리스트
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    # 데이터 유형 확인
    has_purchases = len(customer_data.get('purchase_history', [])) > 0
    has_quotes = len(customer_data.get('quote_history', [])) > 0
    has_meetings = bool(customer_data.get('meeting_notes', '').strip())
    
    # 추천 전략 결정
    if has_purchases:
        strategy = "구매 이력 기반 + 소모품/업그레이드 추천"
    elif has_quotes:
        strategy = "견적 이력 기반 + 관련 제품 추천"
    elif has_meetings:
        strategy = "미팅 내용 기반 + 니즈 분석 추천"
    else:
        strategy = "업종/부서 기반 + 일반 추천"
    
    system_prompt = f"""당신은 20년 경력의 과학 장비 및 실험실 제품 영업 전문가입니다.

**추천 전략**: {strategy}

**전문 분야**:
- HPLC, GC, LC-MS 등 분석 장비
- 실험실 소모품 (컬럼, 시약, 필터 등)
- 연구용 기기 및 악세사리

**추천 원칙**:
1. 구매 이력이 있으면: 소모품 교체 주기, 업그레이드, 관련 제품 추천
2. 견적 이력만 있으면: 견적 제품의 필수 악세사리, 대체품, 업그레이드 옵션 추천
3. 미팅 노트만 있으면: 논의된 니즈/문제점 해결 제품, 연구 목적에 맞는 제품 추천
4. 아무것도 없으면: 업종/부서 특성에 맞는 일반적인 필수 제품 추천

**우선순위 기준**:
- high: 즉시 구매 가능성 높음 (교체 주기 도래, 명확한 니즈 확인)
- medium: 제안 가치 있음 (관련성 높음, 업그레이드 기회)
- low: 장기 육성 (미래 니즈, 일반 추천)"""

    # 고객 데이터 포맷팅
    purchase_info = "없음"
    if has_purchases:
        purchase_info = json.dumps(customer_data.get('purchase_history', []), ensure_ascii=False, indent=2)
    
    quote_info = "없음"
    if has_quotes:
        quote_info = json.dumps(customer_data.get('quote_history', []), ensure_ascii=False, indent=2)
    
    meeting_info = customer_data.get('meeting_notes', '').strip() or "없음"
    
    # 실제 제품 카탈로그
    available_products = customer_data.get('available_products', [])
    product_catalog_text = "없음 (제품 데이터베이스 없음)"
    if available_products:
        product_catalog_text = json.dumps(available_products[:50], ensure_ascii=False, indent=2)  # 최대 50개만
    
    user_prompt = f"""
다음 고객에게 추천할 상품을 제안해주세요:

**고객 기본 정보**
- 이름: {customer_data.get('name', '')}
- 회사: {customer_data.get('company', '')}
- 부서/업종: {customer_data.get('industry', '')}

**구매 이력** (최근 2년):
{purchase_info}

**견적 이력** (최근 6개월):
{quote_info}

**미팅 노트** (최근 내용):
{meeting_info}

**관심 키워드**:
{customer_data.get('interest_keywords', [])}

**🔥 중요: 우리 회사 제품 카탈로그 (이 중에서만 추천하세요!)**
{product_catalog_text}

---

**⚠️ 필수 규칙**:
- 반드시 위의 "우리 회사 제품 카탈로그"에 있는 product_code만 추천하세요
- 존재하지 않는 제품명이나 일반적인 제품명 절대 금지
- product_name은 반드시 카탈로그의 product_code를 그대로 사용하세요
- 최대 5개 제품 추천
- 각 제품마다 구체적인 추천 이유 설명 (200자 이내)

응답 형식 (JSON):
{{
  "recommendations": [
    {{
      "product_name": "제품 카탈로그의 정확한 product_code",
      "category": "카테고리 (예: 분석장비, 소모품, 시약 등)",
      "reason": "추천 이유 - 구매/견적/미팅 히스토리와 연결하여 설명",
      "priority": "high|medium|low",
      "expected_timing": "제안 시기 (예: 즉시, 1-3개월 내, 3-6개월 내)",
      "cross_sell_items": ["카탈로그에 있는 관련 제품 product_code들"]
    }}
  ],
  "analysis_summary": "고객의 구매 패턴 또는 니즈 요약 (2-3문장)"
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
            max_tokens=2500,
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Product recommendations generated for {customer_data.get('name')} using {MODEL_MINI} (strategy: {strategy})")
        return result
    
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

    # 이전 등급 정보 추가
    previous_grade_info = ""
    if customer_data.get('current_grade') and customer_data.get('current_score') is not None:
        previous_grade_info = f"""
📌 현재 등급: {customer_data.get('current_grade')} ({customer_data.get('current_score')}점)
   → 활동 데이터에 큰 변화가 없다면 현재 등급을 유지하세요.
   → 명확한 변화가 있을 때만 등급을 조정하세요.
"""

    user_prompt = f"""
다음 고객의 등급을 평가해주세요:

고객명: {customer_data.get('name', '')}
회사: {customer_data.get('company', '')}
{previous_grade_info}
📊 전체 활동 내역:
- 총 구매 횟수: {customer_data.get('purchase_count', 0)}회
- 총 구매 금액: {customer_data.get('total_purchase', 0):,.0f}원
- 선결제 건수: {customer_data.get('prepayment_count', 0)}건
- 선결제 금액: {customer_data.get('total_prepayment', 0):,.0f}원

📅 최근 6개월 활동:
- 미팅: {customer_data.get('meeting_count', 0)}회
- 이메일 교환: {customer_data.get('email_count', 0)}건
- 견적: {customer_data.get('quote_count', 0)}건
- 최근 구매: {customer_data.get('recent_purchase_count', 0)}회
- 최근 구매액: {customer_data.get('recent_total_purchase', 0):,.0f}원
- 마지막 접촉: {customer_data.get('last_contact', '없음')}

💬 커뮤니케이션 분석:
- 평균 응답 시간: {customer_data.get('avg_response_time', '알 수 없음')}
- 이메일 감정 톤: {customer_data.get('email_sentiment', '중립')}

📝 최근 미팅 요약:
{chr(10).join(customer_data.get('meeting_summary', []) or ['없음'])}

🎯 현재 진행 중인 영업 기회:
{json.dumps(customer_data.get('opportunities', []), ensure_ascii=False, indent=2) if customer_data.get('opportunities') else '없음'}

⚠️ 중요: 
- 전체 구매 이력과 선결제는 고객의 신뢰도와 장기 관계를 나타냅니다
- 최근 6개월 활동은 현재 참여도를 나타냅니다
- 구매 실적이 있는 고객은 최소 C등급 이상이어야 합니다
- 선결제가 있는 고객은 신뢰도가 높으므로 가산점을 주세요

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
            temperature=0.2,  # 등급 평가는 일관성이 매우 중요 (0.4 → 0.2로 낮춤)
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Customer grade updated via AI for {customer_data.get('name')}: {result.get('grade')} using {MODEL_MINI}")
        return result
    
    except Exception as e:
        logger.error(f"Error updating customer grade with AI: {e}")
        raise


def suggest_follow_ups(customer_list: List[Dict], user) -> List[Dict]:
    """
    AI로 팔로우업 우선순위 제안
    
    Args:
        customer_list: 고객 정보 리스트
        user: 현재 사용자
        
    Returns:
        우선순위순으로 정렬된 고객 리스트 (최대 20명)
    """
    from datetime import datetime
    
    system_prompt = """당신은 20년 경력의 B2B 영업 전문가이자 세일즈 코치입니다.
고객 데이터를 심층 분석하여 실제 매출로 연결될 가능성이 높은 고객을 찾아내세요.

🎯 핵심 분석 원칙:

1. **매출 전환 신호 포착** (최우선)
   - 견적 후 2주 경과: 결정 임박 또는 경쟁사 검토 중 (긴급 팔로우업)
   - 미팅 후 견적 없음: 기회 상실 위험 (즉시 견적 발송)
   - 구매 후 3개월 경과: 재구매/소모품 필요 시점 (크로스셀 기회)
   - 선결제 잔액 보유: 신뢰 관계 기반, 추가 구매 확률 높음

2. **위험 고객 선별** (매출 손실 방지)
   - A/B등급 고객 30일+ 무응답: 경쟁사 전환 위험
   - 진행 중인 기회 있으나 연락 끊김: Deal 증발 직전
   - 과거 구매 고객의 장기 미접촉: 관계 단절 위험

3. **영업 효율성 극대화**
   - 단순 "연락 안 한 지 오래됨"은 낮은 우선순위
   - 구매 이력 없는 D등급 + 장기 미접촉 = 우선순위 제외
   - 최근 연락한 고객 중 Next Step이 명확한 경우만 포함

4. **전략적 타이밍**
   - 견적 후 Follow-up: 7-10일 (결정 촉진)
   - 미팅 후 견적: 1-3일 (열기 유지)
   - 구매 후 재접촉: 90일 (소모품/추가 수요)
   - Cold 고객 재활성화: 90일+ (low priority)

우선순위 레벨 기준:
- **urgent (긴급)**: 지금 안 하면 매출 손실 확실 (예: A등급, 견적 후 2주, 진행 기회 있음)
- **high (높음)**: 이번 주 내 처리 필수 (예: B등급, 구매 후 3개월, 미팅 후 견적 필요)
- **medium (보통)**: 계획적 접근 (예: C등급, 견적 후 1개월, 잠재 수요 있음)
- **low (낮음)**: 여유 있을 때 (예: D등급, 구매 없음, 특별 이슈 없음)

⚠️ 주의사항:
- 최근 1주일 내 연락한 고객은 특별한 이유 없으면 제외
- 구매 이력 없는 D등급은 특별한 기회 요소 없으면 우선순위 낮춤
- 이유는 반드시 "왜 지금 연락해야 매출이 나는지" 중심으로 작성
- 추상적인 표현 금지, 구체적인 숫자와 날짜 활용
"""
    
    user_prompt = f"""다음 고객들의 팔로우업 우선순위를 분석해주세요.

📊 분석 대상: {len(customer_list)}명
📅 현재 날짜: {datetime.now().strftime('%Y-%m-%d')}

고객 데이터:
{json.dumps(customer_list, ensure_ascii=False, indent=2)}

응답 형식 (JSON):
{{
  "suggestions": [
    {{
      "customer_id": 고객ID,
      "customer_name": "고객명",
      "company": "회사명",
      "priority_score": 1-100,
      "priority_level": "urgent|high|medium|low",
      "reason": "매출 관점에서 지금 연락해야 하는 구체적 이유 (숫자 포함, 2-3문장)",
      "suggested_action": "구체적 액션 + 대화 주제 (예: '전화로 견적 검토 진행 상황 확인 후 의사결정 시점 재확인')",
      "best_contact_time": "업종과 직급 고려한 최적 시간 (예: '대학 교수 - 오후 3-5시, 기업 구매담당 - 오전 10-11시')",
      "customer_grade": "A+|A|B|C|D"
    }}
  ]
}}

규칙:
1. 우선순위 점수는 차등 분배 (100점 만점을 소수에게만, 60점 이하 다수)
2. urgent/high는 전체의 20% 이내만 선정
3. 매출 전환 가능성이 낮으면 과감히 낮은 점수 부여
4. 우선순위순 정렬, 최대 20명
5. "최근 연락함"은 이유가 아님, 구체적 비즈니스 맥락 필요
"""
    
    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_MINI,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.4,  # 창의적 분석 필요하므로 적당한 온도
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        suggestions = result.get('suggestions', [])
        
        logger.info(f"Follow-up suggestions generated for {len(suggestions)} customers using {MODEL_MINI}")
        return suggestions[:20]  # 최대 20명
    
    except Exception as e:
        logger.error(f"Error suggesting follow-ups with AI: {e}")
        raise
