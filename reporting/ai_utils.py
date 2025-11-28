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
MODEL_PREMIUM = settings.OPENAI_MODEL_PREMIUM  # 최고 품질, AI 미팅 준비
MAX_TOKENS = settings.OPENAI_MAX_TOKENS  # 최대 토큰 수

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
        context: 컨텍스트 정보 (고객명, 회사명, 제품, 일정, schedule_id 등)
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
    
    # 일정 히스토리 가져오기 (schedule_id가 있는 경우)
    schedule_history = ""
    if context.get('schedule_id'):
        try:
            from reporting.models import Schedule, History
            schedule = Schedule.objects.get(pk=context['schedule_id'])
            
            # 관련 히스토리 조회 (최근 10개)
            histories = History.objects.filter(
                schedule=schedule
            ).order_by('-created_at')[:10]
            
            if histories.exists():
                schedule_history = "\n\n**일정 히스토리:**\n"
                for hist in histories:
                    schedule_history += f"- [{hist.created_at.strftime('%Y-%m-%d %H:%M')}] "
                    schedule_history += f"{hist.get_action_type_display()}"
                    if hist.memo:
                        schedule_history += f": {hist.memo}"
                    schedule_history += "\n"
        except Exception as e:
            logger.warning(f"Failed to fetch schedule history: {e}")
    
    if purpose == 'compose':
        system_prompt = f"""너는 B2B 영업 20년차의 이메일 작성 전문가이며,
내가 제공하는 **히스토리 데이터(History Log)**를 기반으로
해당 고객에게 보낼 최적의 이메일 초안을 작성하는 역할을 수행한다.

1. 입력 데이터 구성

내가 아래 두 가지를 동일한 메시지에서 제공한다:

히스토리 데이터(History)
- CRM 기록
- 고객의 요청/이슈
- 방문 내용
- 구매 가능성
- 미팅 메모·대화 로그
- 과거 주문/AS/클레임 기록
- 담당자 성향

이메일 목적(Purpose)
- 예: "방문 일정 조율", "견적 전달", "AS 결과 안내", "샘플 후속", "이벤트 안내", "팔로우업" 등

너는 이 두 정보를 모두 분석하여 이메일을 작성해야 한다.

2. 이메일 생성 규칙

아래 조건을 모두 충족해야 한다:
- 상황을 정확히 반영해 자연스러운 문맥으로 구성할 것
- 불필요한 내용 없이 목적 중심 구조로 정리
- 고객의 성향(교수/연구원/담당자)에 맞는 톤을 자동 적용
- 히스토리에서 중요한 포인트는 반드시 자연스럽게 포함
- 과한 미사여구 없이 영업 현장에서 바로 쓸 수 있는 형식으로 구성
- 매끄러운 흐름을 위해 문장 순서는 재배치 가능
- 전문성·신뢰·정확성을 높이는 최소한의 표현만 추가
- 마지막 줄에는 부담 없는 CTA 포함
  (예: "편하신 때 회신 부탁드립니다", "문의 있으시면 언제든 연락주세요" 등)

3. 금지 규칙

- 한국어만 사용할 것
- 초안 형태로 작성할 것 (완벽하지만 지나친 공식문 불가)
- 마크다운/장식 금지
- 의미를 임의로 확장하거나 다른 스토리를 만들지 말 것
  (오직 히스토리 기반 내용만 활용)

4. 출력 형식

응답은 반드시 다음 JSON 형식으로 작성하세요:
{{
  "subject": "이메일 제목",
  "body": "이메일 본문 (HTML 형식)"
}}"""

        user_prompt = f"""
다음 정보를 바탕으로 영업 이메일을 작성해주세요:

고객명: {context.get('customer_name', '고객')}
회사명: {context.get('company_name', '')}
제품/서비스: {context.get('product', '')}
일정 내용: {context.get('schedule_content', '')}
추가 메모: {context.get('notes', '')}{schedule_history}

중요: 
- 고객명이 제공된 경우 반드시 실제 고객명을 사용하세요. [이름], [직함] 같은 플레이스홀더를 절대 사용하지 마세요.
- 발신자명은 반드시 "{sender_name}"을 사용하세요. 다른 이름을 만들어내지 마세요.
- 일정 히스토리가 제공된 경우, 과거 활동 내역을 자연스럽게 참고하여 이메일을 작성하세요.
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
    
    # 톤 매핑
    tone_korean = {
        'formal': '정중',
        'casual': '캐주얼',
        'simple': '간단'
    }.get(tone, '정중')
    
    system_prompt = f"""너는 B2B 영업 20년 경력의 '세일즈 이메일 리라이팅 전문가'이다.
나는 "이메일 초안"과 "수정 톤 유형(정중/캐주얼/간단)"을 제공한다.
너의 역할은 다음 조건들을 모두 충족하여 최적의 리라이팅 버전 1개를 작성하는 것이다.

⚠️ 절대 규칙: 이것은 반드시 비즈니스 이메일이어야 한다!
- 수신자는 고객, 교수, 연구원, 병원 관계자 등 비즈니스 파트너이다.
- 친구나 가족에게 보내는 사적인 이메일이 아니다.
- 영업, 견적, 납품, 미팅, 제품 문의 등 비즈니스 목적의 이메일이다.
- 전문성과 신뢰감을 유지하면서 톤만 조정한다.

1. 핵심 목표

- 초안의 의미는 유지하되, 전달력·명확성·세일즈 효과를 극대화한다.
- B2B 연구자·교수·병원·기업 고객에게 통하는 실제 영업 스타일을 반영한다.
- 문장 길이는 필요 시 줄이고, 중복·군더더기는 과감히 제거한다.

2. 톤 선택 규칙 (반드시 지켜야 함)

내가 지시하는 tone 옵션은 다음 셋 중 하나이다:

- 정중: 격식, 간결함, 부담 없는 공손함. (교수/연구책임자용) - 비즈니스 공식 이메일
- 캐주얼: 친근하지만 예의는 유지. 짧고 편안. (연구원/담당자용) - 비즈니스 친근 이메일
- 간단: 중요한 문장만 남겨 초간단 구조로. (신속 안내/반복메일용) - 비즈니스 간략 이메일

너는 반드시 내가 선택한 tone으로 1가지 버전만 작성한다.
어떤 톤이든 비즈니스 이메일의 기본 예의와 전문성은 유지해야 한다.

3. 세일즈 관점 최적화 규칙

- 읽는 사람이 부담 없도록 요점 → 목적 → 요청 구조 유지
- "행동 유도 문장(CTA)"를 자연스럽게 삽입
  (예: "확인 후 회신 부탁드립니다", "편하실 때 알려주세요" 등)
- 필요 시 실무자가 놓친 부분을 감지하여 논리·흐름을 자연스럽게 재배치
- 전문성·신뢰감을 주는 선택적 최소 표현 추가 가능
  (예: "점검 결과 기준에 부합했습니다", "필요 시 추가 안내드리겠습니다")

4. 금지 규칙

- 초안의 의미를 바꾸지 말 것
- 과한 미사여구 금지
- 한국어만 사용
- 마크다운/띄어쓰기 장식 금지 (순수 텍스트)
- 비즈니스에 부적절한 표현 사용 금지 (은어, 이모티콘, 줄임말 등)

5. 출력 형식

응답은 반드시 다음 JSON 형식으로 작성하세요:
{{
  "body": "수정본 이메일 전체 (HTML 형식)"
}}"""

    user_prompt = f"""
다음 이메일을 "{tone_korean}" 톤으로 재작성해주세요:

{original_content}

{f'추가 요청사항: {instructions}' if instructions else ''}
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
    logger.info(f"[인사이트] 함수 시작 - 고객: {customer_data.get('name')}")
    
    if user and not check_ai_permission(user):
        logger.warning(f"[인사이트] 권한 없음 - 사용자: {user}")
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    logger.info(f"[인사이트] 프롬프트 생성 중... (미팅: {customer_data.get('meeting_count', 0)}건, 견적: {customer_data.get('quote_count', 0)}건)")
    
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

이메일 커뮤니케이션 내용:
{customer_data.get('email_conversations', '이메일 기록 없음')}

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
        logger.info(f"[인사이트] AI 호출 시작 - 모델: {MODEL_STANDARD}")
        logger.info(f"[인사이트] 프롬프트 길이 - 시스템: {len(system_prompt)}자, 사용자: {len(user_prompt)}자")
        
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
        logger.info(f"[인사이트] AI 응답 완료 - 응답 길이: {len(result)}자")
        logger.info(f"[인사이트] 토큰 사용 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}, 총: {response.usage.total_tokens}")
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

**고객 구분별 접근 전략:**
- **교수**: 의사결정권자로 연구비 집행권한 보유. 직접 컨택 가능하며 장기 관계 구축 중요
- **연구원**: 실무 담당자로 교수에게 보고 필요. 교수 소개나 추천 확보가 중요
- **대표**: 의사결정권자로 구매 권한 보유. 직접 컨택으로 빠른 결정 가능
- **실무자**: 업무 담당자로 대표에게 보고 필요. 대표 연결이나 추천 확보가 중요

**우선순위 평가 기준:**
1. 마지막 연락 경과 시간 (장기 미접촉 고객)
2. 진행 중인 기회의 단계 (클로징 단계 우선)
3. 구매 패턴 및 예상 재구매 시기
4. 고객 등급 (VIP, A 등급 우선)
5. 선결제 잔액 (소진 유도 필요)
6. 견적 후 미구매 기간
7. 고객 구분 (교수/대표는 높은 우선순위, 연구원/실무자는 의사결정자 연결 전략 필요)

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
    "reason": "우선순위 이유 (고객 구분 고려)",
    "suggested_action": "제안 액션 (고객 구분별 전략 반영)",
    "best_contact_time": "최적 연락 시간"
  },
  ...
]

우선순위 점수가 높은 순으로 정렬해서 반환하세요."""

    # 고객 데이터를 요약 형식으로 변환
    customer_summary = []
    for customer in customer_list[:20]:  # 최대 20명만 분석
        customer_type = customer.get('customer_type', '미정')
        history_notes = customer.get('history_notes', [])
        history_text = '\n'.join([f"- {note}" for note in history_notes]) if history_notes else '없음'
        
        summary = f"""
고객 ID: {customer.get('id')}
고객명: {customer.get('name', '미정')} ({customer_type})
회사: {customer.get('company', '미정')}
마지막 연락: {customer.get('last_contact', '정보 없음')}
미팅: {customer.get('meeting_count', 0)}회
견적: {customer.get('quote_count', 0)}회
구매: {customer.get('purchase_count', 0)}회
총 구매액: {customer.get('total_purchase', 0):,}원
등급: {customer.get('grade', '미분류')}
진행 중인 기회: {len(customer.get('opportunities', []))}건
선결제 잔액: {customer.get('prepayment_balance', 0):,}원
최근 히스토리 메모:
{history_text}
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
    
    from datetime import datetime, timedelta
    current_date = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    current_year = datetime.now().year
    current_month = datetime.now().month
    last_month = (datetime.now().replace(day=1) - timedelta(days=1))
    last_month_start = last_month.replace(day=1).strftime('%Y-%m-%d')
    last_month_end = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
    current_month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
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

**EmailLog (이메일 발송 이력) 모델:**
- followup (관계: FollowUp 객체)
- schedule (관계: Schedule 객체)
- email_type (유형: 'sent', 'received')
- sender (발신자: User 객체)
- recipient_email (수신자)
- subject (제목)
- sent_at (발송 일시)
- created_at

**DeliveryItem (납품 상품) 모델:**
- schedule (관계: Schedule 객체, activity_type='delivery'인 일정만)
- product (관계: Product 객체)
- item_name (상품명)
- quantity (수량)
- unit_price (단가)
- 관계 접근: schedule__followup (고객 정보)

**QuoteItem (견적 상품) 모델:**
- quote (관계: Quote 객체)
- product (관계: Product 객체)
- 관계 접근: quote__followup (고객 정보)

**Product (상품) 모델:**
- product_code (상품 코드 - 예: SO826.1000, HPLC-C18-100 등)
- product_name (상품명)
- category (카테고리)
- specification (규격)

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
   - 납품 상품의 고객: schedule__followup__field_name
   - 견적 상품의 고객: quote__followup__field_name
   - 이메일 발송 이력의 고객: emaillogs__field_name (FollowUp 모델에서!)
4. 상품 검색:
   - 상품 코드 검색: product__product_code__icontains="826"
   - 상품명 검색: product__product_name__icontains="HPLC"
   - item_name은 직접 문자열이므로: item_name__icontains="826"
5. 이메일 발송 이력 검색:
   - 이메일 보낸 고객: emaillogs__email_type="sent"
   - 특정 날짜 이메일 보낸 고객: emaillogs__sent_at__date="2024-11-27"
   - 특정 기간 이메일 보낸 고객: emaillogs__sent_at__gte="2024-11-01"
6. 날짜 lookup: __gte (이상), __lte (이하), __range (범위), __date (날짜만)
7. 문자열 lookup: __icontains (포함), __exact (정확히), __iexact (대소문자 무시)
8. **검색 대상에 따라 다른 필터 사용**:
   - customers 검색: schedules__, deliveryitems__, emaillogs__ 접두사 사용 가능
   - schedules 검색: schedules__ 접두사 사용 불가 (직접 필드명만)
   - opportunities 검색: followup__ 접두사로 고객 정보 접근
   - products 검색: DeliveryItem 또는 QuoteItem 모델 기준으로 검색

🔍 상품 관련 검색 패턴:
- "826이 포함된 상품을 구매한 고객" → customers 검색 + deliveryitems__product__product_code__icontains="826"
- "HPLC를 구매한 고객" → customers 검색 + deliveryitems__item_name__icontains="HPLC"
- "SO826.1000 구매 고객" → customers 검색 + deliveryitems__product__product_code__icontains="SO826.1000"

📧 이메일 발송 이력 검색 패턴:
- "어제 메일 나눈 고객" → customers 검색 + emaillogs__sent_at__date="{yesterday}" (email_type 지정 없음 = 보낸것+받은것 모두)
- "11월 27일에 메일 보낸 고객" → customers 검색 + emaillogs__email_type="sent" + emaillogs__sent_at__date="2025-11-27"
- "지난주 이메일 받은 고객" → customers 검색 + emaillogs__email_type="received" + emaillogs__sent_at__gte="지난주 월요일"
- "이번 달 이메일 주고받은 고객" → customers 검색 + emaillogs__sent_at__gte="{current_month_start}" (email_type 없이)

⚠️ 이메일 검색 중요 규칙:
- "메일 나눈", "메일 주고받은", "메일 교환한" = email_type 필터 없음 (보낸것+받은것 모두 포함)
- "메일 보낸" = email_type="sent" 명시
- "메일 받은" = email_type="received" 명시
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
    "schedules__visit_date__gte": "{last_month_start}",
    "schedules__visit_date__lt": "{current_month_start}"
  }},
  "interpretation": "지난달에 견적 일정이 있는 고객을 검색합니다."
}}

예시 2 - 기간 검색:
입력: "3개월 이상 연락 안 한 A등급 고객"
출력:
{{
  "filters": {{
    "customer_grade": "A",
    "schedules__visit_date__lt": "{three_months_ago}"
  }},
  "interpretation": "A등급 고객 중 3개월 이전에 마지막으로 연락한 고객을 검색합니다."
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

예시 5 - 상품 코드로 구매 고객 검색:
입력: "826이 포함된 상품을 구매한 고객"
출력:
{{
  "filters": {{
    "deliveryitems__product__product_code__icontains": "826"
  }},
  "interpretation": "상품 코드에 826이 포함된 제품을 구매한 고객을 검색합니다."
}}

예시 6 - 상품명으로 구매 고객 검색:
입력: "HPLC 구매한 고객"
출력:
{{
  "filters": {{
    "deliveryitems__item_name__icontains": "HPLC"
  }},
  "interpretation": "HPLC가 포함된 상품을 구매한 고객을 검색합니다."
}}

예시 7 - 특정 상품 코드 완전 일치:
입력: "SO826.1000 구매 고객"
출력:
{{
  "filters": {{
    "deliveryitems__product__product_code__icontains": "SO826.1000"
  }},
  "interpretation": "상품 코드 SO826.1000을 구매한 고객을 검색합니다."
}}

예시 8 - 이메일 발송 이력 검색 (보낸 것만):
입력: "11월 27일에 메일 보낸 고객"
출력:
{{
  "filters": {{
    "emaillogs__email_type": "sent",
    "emaillogs__sent_at__date": "{current_year}-11-27"
  }},
  "interpretation": "{current_year}년 11월 27일에 이메일을 보낸 고객을 검색합니다."
}}

예시 9 - 이메일 발송 이력 (주고받은 것 모두):
입력: "어제 메일 나눈 고객"
출력:
{{
  "filters": {{
    "emaillogs__sent_at__date": "{yesterday}"
  }},
  "interpretation": "어제({yesterday})에 이메일을 주고받은 고객을 검색합니다 (보낸것+받은것 모두 포함)."
}}

예시 10 - 이메일 발송 이력 (기간, 주고받은 것):
입력: "이번 달 이메일 주고받은 고객"
출력:
{{
  "filters": {{
    "emaillogs__sent_at__gte": "{current_month_start}"
  }},
  "interpretation": "{current_year}년 {current_month}월 이후에 이메일을 주고받은 고객을 검색합니다 (보낸것+받은것 모두 포함)."
}}

⚠️ 주의:
- 고객(customers) 검색할 때만 schedules__, deliveryitems__, emaillogs__ 접두사 사용
- 일정(schedules) 검색할 때는 schedules__ 사용 안 함
- 상품 관련 검색은 반드시 deliveryitems__ 또는 quoteitems__ 사용
- 이메일 발송 이력 검색은 emaillogs__ 사용
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
    logger.info(f"[상품추천] 함수 시작 - 고객: {customer_data.get('name')}")
    
    if user and not check_ai_permission(user):
        logger.warning(f"[상품추천] 권한 없음 - 사용자: {user}")
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    # 데이터 유형 확인
    has_purchases = len(customer_data.get('purchase_history', [])) > 0
    has_quotes = len(customer_data.get('quote_history', [])) > 0
    has_meetings = bool(customer_data.get('meeting_notes', '').strip())
    
    logger.info(f"[상품추천] 데이터 확인 - 구매: {has_purchases}, 견적: {has_quotes}, 미팅: {has_meetings}")
    
    # 추천 전략 결정
    if has_purchases:
        strategy = "구매 이력 기반 + 소모품/업그레이드 추천"
    elif has_quotes:
        strategy = "견적 이력 기반 + 관련 제품 추천"
    elif has_meetings:
        strategy = "미팅 내용 기반 + 니즈 분석 추천"
    else:
        strategy = "업종/부서 기반 + 일반 추천"
    
    logger.info(f"[상품추천] 추천 전략: {strategy}")
    
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
        logger.info(f"[상품추천] 카탈로그 제품 수: {len(available_products)}개")
        product_catalog_text = json.dumps(available_products[:50], ensure_ascii=False, indent=2)  # 최대 50개만
        # 각 제품 로그 (처음 5개만)
        for i, prod in enumerate(available_products[:5], 1):
            logger.info(f"[상품추천] 제품 {i}: {prod.get('product_code', '')} - {prod.get('product_name', '')}")
    
    # 실무자 히스토리 정보
    history_info = customer_data.get('history_notes', '').strip() or "없음"
    
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

**📝 실무자 히스토리** (담당자가 작성한 메모/활동 내역):
{history_info}

**관심 키워드**:
{customer_data.get('interest_keywords', [])}

**🔥 중요: 우리 회사 제품 카탈로그 (1순위 추천 대상)**
{product_catalog_text}

---

**추천 방식**:

**1순위: 우리 회사 제품 추천 (필수)**
- 위의 "우리 회사 제품 카탈로그"에 있는 product_code만 추천
- 고객의 구매/견적/미팅 히스토리와 연결하여 추천
- 최대 3-5개 제품 추천

**2순위: 고객에게 필요한 추가 제품 (선택적)**
- 카탈로그에 없더라도 고객이 꼭 필요할 것으로 판단되는 제품
- 고객의 연구/업무 환경에 필수적이라고 판단되는 경우만
- 최대 1-2개만 추천

**⚠️ 필수 규칙**:
- 1순위 추천의 product_name은 반드시 카탈로그의 product_code를 그대로 사용
- 2순위 추천의 product_name은 일반적인 제품명 사용 (예: "딥프리저", "초저온냉동고")
- 각 제품의 source 필드로 구분: "company_catalog" 또는 "additional_need"
- 각 제품마다 구체적인 추천 이유 설명 (200자 이내)

응답 형식 (JSON):
{{
  "recommendations": [
    {{
      "product_name": "제품 카탈로그의 정확한 product_code 또는 일반 제품명",
      "source": "company_catalog 또는 additional_need",
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
        logger.info(f"[상품추천] AI 호출 시작 - 모델: {MODEL_MINI}")
        logger.info(f"[상품추천] 프롬프트 길이 - 시스템: {len(system_prompt)}자, 사용자: {len(user_prompt)}자")
        
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
        logger.info(f"[상품추천] AI 응답 완료 - 추천: {len(result.get('recommendations', []))}개")
        logger.info(f"[상품추천] 토큰 사용 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}, 총: {response.usage.total_tokens}")
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
    logger.info(f"[등급평가] 함수 시작 - 고객: {customer_data.get('name')}")
    
    if user and not check_ai_permission(user):
        logger.warning(f"[등급평가] 권한 없음 - 사용자: {user}")
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    logger.info(f"[등급평가] 데이터 확인 - 구매: {customer_data.get('purchase_count', 0)}건, 선결제: {customer_data.get('prepayment_count', 0)}건")
    
    system_prompt = """당신은 B2B 고객 등급 평가 전문가입니다.
다음 기준으로 고객을 평가하고 A+, A, B, C, D 등급을 매겨주세요:

평가 요소:
1. Engagement (참여도): 미팅, 이메일 응답 빈도
2. Purchase Potential (구매 가능성): 과거 구매, 견적 진행 상황
3. Relationship (관계): 커뮤니케이션 품질, 장기 거래 가능성
4. Responsiveness (반응성): 응답 속도, 적극성

등급 기준 (점수가 높을수록 좋은 등급):
- A+ (90-100점): VIP 고객, 즉시 구매 가능성 높음, 최우선 관리
- A (80-89점): 우수 고객, 단기 구매 가능성, 우선 관리
- B (60-79점): 양호 고객, 중기 육성 필요, 정기 관리
- C (40-59점): 보통 고객, 장기 관리, 지속 접촉
- D (0-39점): 저조 고객, 재검토 필요, 선택적 관리"""

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
- **점수가 높을수록 좋은 등급입니다** (A+ > A > B > C > D)
- 구매 실적이 있는 고객은 최소 60점(B등급) 이상이어야 합니다
- 선결제가 있는 고객은 신뢰도가 높으므로 가산점을 주세요
- 활동이 거의 없는 고객은 39점 이하(D등급)로 평가하세요

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
        logger.info(f"[등급평가] AI 호출 시작 - 모델: {MODEL_MINI}")
        logger.info(f"[등급평가] 프롬프트 길이 - 시스템: {len(system_prompt)}자, 사용자: {len(user_prompt)}자")
        
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
        logger.info(f"[등급평가] AI 응답 완료 - 등급: {result.get('grade')}, 점수: {result.get('score')}")
        logger.info(f"[등급평가] 토큰 사용 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}, 총: {response.usage.total_tokens}")
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
    
    logger.info(f"[팔로우업] 함수 시작 - 고객 수: {len(customer_list)}명")
    
    # 각 고객 이름 로그 (처음 10명만)
    for i, customer in enumerate(customer_list[:10], 1):
        logger.info(f"[팔로우업] 고객 {i}: {customer.get('customer_name', '')} ({customer.get('company', '')})")
    
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
        logger.info(f"[팔로우업] AI 호출 시작 - 모델: {MODEL_MINI}")
        logger.info(f"[팔로우업] 프롬프트 길이 - 시스템: {len(system_prompt)}자, 사용자: {len(user_prompt)}자")
        
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
        
        logger.info(f"[팔로우업] AI 응답 완료 - 추천: {len(suggestions)}건")
        logger.info(f"[팔로우업] 토큰 사용 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}, 총: {response.usage.total_tokens}")
        
        # 중복 제거 (같은 customer_id는 한 번만)
        seen_ids = set()
        unique_suggestions = []
        for suggestion in suggestions:
            customer_id = suggestion.get('customer_id')
            if customer_id not in seen_ids:
                seen_ids.add(customer_id)
                unique_suggestions.append(suggestion)
        
        logger.info(f"[팔로우업] 중복 제거 완료 - 최종: {len(unique_suggestions)}건")
        return unique_suggestions[:20]  # 최대 20명
    
    except Exception as e:
        logger.error(f"Error suggesting follow-ups with AI: {e}")
        raise


def generate_meeting_strategy(schedule_id: int, user=None) -> str:
    """
    일정 기반 AI 미팅 전략 추천 (간소화 버전)
    - 해당 일정 정보
    - 일정 관련 히스토리 (실무자가 남긴 글)
    - 선결제 잔액
    
    Args:
        schedule_id: 일정 ID
        user: 요청 사용자
    
    Returns:
        AI가 생성한 미팅 전략 (Markdown 형식)
    """
    from reporting.models import Schedule, History, Prepayment
    from decimal import Decimal
    
    logger.info(f"[미팅전략] 함수 시작 - 일정 ID: {schedule_id}")
    
    if user and not check_ai_permission(user):
        logger.warning(f"[미팅전략] 권한 없음 - 사용자: {user}")
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    logger.info(f"[미팅전략] 일정 조회 중...")
    try:
        schedule = Schedule.objects.select_related('followup', 'followup__company', 'followup__department').get(id=schedule_id)
        logger.info(f"[미팅전략] 일정 조회 완료 - 고객: {schedule.followup.customer_name}")
    except Schedule.DoesNotExist:
        logger.error(f"[미팅전략] 일정 없음 - ID: {schedule_id}")
        raise ValueError(f"일정 ID {schedule_id}를 찾을 수 없습니다.")
    
    customer = schedule.followup
    
    logger.info(f"[미팅전략] 1단계: 히스토리 메모 수집 중...")
    # 1. 고객의 전체 히스토리 (실무자 작성 글)
    history_notes = History.objects.filter(
        followup=customer
    ).exclude(
        content__isnull=True
    ).exclude(
        content=''
    ).values('created_at', 'action_type', 'content', 'meeting_date').order_by('-created_at')[:20]
    
    history_records = []
    for hn in history_notes:
        action_type_display = dict(History.ACTION_CHOICES).get(hn['action_type'], hn['action_type'])
        date = hn['meeting_date'] or hn['created_at'].date()
        history_records.append(f"[{date}] {action_type_display}: {hn['content']}")
    
    logger.info(f"[미팅전략] 히스토리 메모 수집 완료 - {len(history_records)}건")
    
    logger.info(f"[미팅전략] 2단계: 일정 컨텍스트 수집 중...")
    # 2. 이 일정과 연결된 히스토리 찾기
    schedule_histories = History.objects.filter(schedule=schedule).exclude(
        content__isnull=True
    ).exclude(content='').values('content', 'action_type', 'created_at').order_by('-created_at')
    
    schedule_context = []
    for sh in schedule_histories:
        action_type_display = dict(History.ACTION_CHOICES).get(sh['action_type'], sh['action_type'])
        schedule_context.append(f"[{action_type_display}] {sh['content']}")
    
    logger.info(f"[미팅전략] 일정 컨텍스트 수집 완료 - {len(schedule_context)}건")
    
    logger.info(f"[미팅전략] 3단계: 선결제 잔액 확인 중...")
    # 3. 선결제 잔액
    prepayments = Prepayment.objects.filter(
        customer=customer,
        status='active'
    ).order_by('-payment_date')
    
    total_prepayment_balance = Decimal('0')
    prepayment_details = []
    for prepayment in prepayments:
        total_prepayment_balance += prepayment.balance
        prepayment_details.append({
            'date': prepayment.payment_date.strftime('%Y-%m-%d'),
            'amount': f"{prepayment.amount:,.0f}원",
            'balance': f"{prepayment.balance:,.0f}원",
            'memo': prepayment.memo or ''
        })
    
    logger.info(f"[미팅전략] 선결제 잔액 확인 완료 - 총 {total_prepayment_balance:,.0f}원 ({len(prepayment_details)}건)")
    
    logger.info(f"[미팅전략] 4단계: 프롬프트 생성 및 AI 호출 준비...")
    
    # System Prompt (간소화 버전)
    system_prompt = """당신은 20년 이상 B2B 생명과학·의료·연구장비 시장에서 활동한 최고 수준의 세일즈 컨설팅 전문가입니다.
다음 미팅에서 어떤 전략을 활용해야 가장 높은 확률로 영업 성과를 만들 수 있을지 컨설팅하는 것입니다.

**핵심 원칙:**
1. 절대 모호하거나 원론적인 내용 금지
2. 반드시 데이터 기반으로 구체적인 전략을 작성
3. 실무자가 현장에서 바로 사용할 수 있는 형태로 제시
4. 피펫·팁·디스펜서 등 연구장비 중심의 세일즈 특성을 반영

**답변 형식:**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 상황 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【고객 정보】
• 이름/소속: [정보]
• 히스토리 기반 니즈: [실무자가 남긴 글에서 파악한 고객의 관심사/문제점]
• 선결제 잔액: [잔액 정보 및 활용 전략]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 미팅 전략
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【핵심 주제 TOP 3】
1. [구체적 주제] - 근거: [히스토리 내용]
2. [구체적 주제] - 근거: [히스토리 내용]
3. [구체적 주제] - 근거: [히스토리 내용]

【대화 전략】
▶ 오프닝: "[히스토리 기반 자연스러운 인사]"
▶ 니즈 확인 질문:
• [히스토리 기반 질문 1]
• [히스토리 기반 질문 2]
• [히스토리 기반 질문 3]

【제안 포인트】
• [히스토리에서 파악한 니즈에 맞는 제안 1]
• [히스토리에서 파악한 니즈에 맞는 제안 2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 실행 체크리스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【준비물】
□ [필요 자료/샘플]
□ [선결제 활용 가능 여부 확인]

【확인 사항】
□ [히스토리 기반 확인 사항]
□ [예산/타이밍 관련]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # User Prompt (간소화 버전)
    activity_type_display = dict(Schedule.ACTIVITY_TYPE_CHOICES).get(schedule.activity_type, schedule.activity_type)
    
    user_prompt = f"""
**📅 이번 일정 정보:**
- **유형**: {activity_type_display}
- **날짜/시간**: {schedule.visit_date} {schedule.visit_time}
- **장소**: {schedule.location or '미정'}
- **메모**: {schedule.notes or '없음'}

**이 일정과 관련된 히스토리:**
{chr(10).join(schedule_context) if schedule_context else '연결된 히스토리 없음'}

---

**👤 고객 정보:**
- **이름**: {customer.customer_name}
- **소속**: {customer.company.name if customer.company else '미등록'} - {customer.department.name if customer.department else '미등록'}
- **담당자/책임자**: {customer.manager or '미등록'}
- **등급**: {customer.get_customer_grade_display()}

---

**💰 선결제 잔액:**
- **총 잔액**: {total_prepayment_balance:,.0f}원 ({len(prepayment_details)}건)
"""

    if prepayment_details:
        user_prompt += "\n**선결제 내역:**\n"
        for p in prepayment_details[:5]:
            user_prompt += f"- {p['date']}: {p['amount']} 입금, 잔액 {p['balance']}"
            if p['memo']:
                user_prompt += f" ({p['memo']})"
            user_prompt += "\n"
    
    user_prompt += f"""
---

**📝 고객 히스토리 (실무자가 남긴 메모, 최근 20개):**

{chr(10).join(history_records) if history_records else '히스토리 기록 없음'}

---

위 데이터를 바탕으로, **{activity_type_display}** 일정에 대한 구체적이고 실행 가능한 전략을 작성해주세요.
특히 이 일정과 연결된 히스토리가 있다면 이를 우선적으로 활용하고, 전체 히스토리에서 고객의 니즈와 관심사를 파악하세요.
"""

    try:
        logger.info(f"[미팅전략] AI 호출 시작 - 모델: {MODEL_PREMIUM}")
        logger.info(f"[미팅전략] 프롬프트 길이 - 시스템: {len(system_prompt)}자, 사용자: {len(user_prompt)}자")
        logger.info(f"[미팅전략] 수집된 데이터 - 히스토리: {len(history_records)}건, 일정 컨텍스트: {len(schedule_context)}건, 선결제: {len(prepayment_details)}건")
        
        response = get_openai_client().chat.completions.create(
            model=MODEL_PREMIUM,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,  # 간소화 버전이므로 1500으로 충분
            temperature=0.7
        )
        
        strategy = response.choices[0].message.content
        logger.info(f"[미팅전략] AI 응답 완료 - 응답 길이: {len(strategy)}자")
        logger.info(f"[미팅전략] 토큰 사용 - 입력: {response.usage.prompt_tokens}, 출력: {response.usage.completion_tokens}, 총: {response.usage.total_tokens}")
        
        return strategy
    
    except Exception as e:
        logger.error(f"Error generating meeting strategy: {e}")
        raise


def generate_meeting_advice(context: dict, user=None) -> str:
    """
    [DEPRECATED] 기존 AI 미팅 준비 함수 (하위 호환성 유지)
    새로운 generate_meeting_strategy() 사용 권장
    
    Args:
        context: 미팅 및 고객 정보
            - schedule: 일정 정보 (type, date, time, location, notes)
            - customer: 고객 정보 (name, company, type, manager, grade)
            - history_notes: 히스토리 메모 리스트
            - delivery_history: 구매 이력
            - quote_history: 견적 이력
            - meeting_notes: 과거 미팅 메모
            - email_history: 이메일 주고받은 내역
            - user_question: 실무자의 질문
        user: 요청 사용자
    
    Returns:
        AI가 생성한 미팅 조언 (Markdown 형식)
    """
    if user and not check_ai_permission(user):
        raise PermissionError("AI 기능 사용 권한이 없습니다.")
    
    # 컨텍스트 요약 생성
    schedule_info = context.get('schedule', {})
    customer_info = context.get('customer', {})
    history_notes = context.get('history_notes', [])
    delivery_history = context.get('delivery_history', [])
    quote_history = context.get('quote_history', [])
    meeting_notes = context.get('meeting_notes', [])
    email_history = context.get('email_history', [])
    user_question = context.get('user_question', '')
    
    # 히스토리 요약
    history_summary = '\n'.join(history_notes[:10]) if history_notes else '기록 없음'
    
    # 구매 이력 요약
    total_purchase = sum(d['amount'] for d in delivery_history)
    purchase_summary = f"총 {len(delivery_history)}건, {total_purchase:,.0f}원" if delivery_history else '없음'
    
    # 견적 이력 요약
    total_quote = sum(q['amount'] for q in quote_history)
    quote_summary = f"총 {len(quote_history)}건, {total_quote:,.0f}원" if quote_history else '없음'
    
    # 미팅 메모 요약
    meeting_summary = '\n'.join(meeting_notes) if meeting_notes else '기록 없음'
    
    # 이메일 이력 요약
    email_summary = '\n\n'.join(email_history[:10]) if email_history else '기록 없음'
    
    system_prompt = f"""당신은 20년 경력의 B2B 영업 전문가입니다.
고객과의 모든 과거 거래 내역을 완벽히 파악하고 있으며, 이를 바탕으로 전략적인 조언을 제공합니다.

**핵심 원칙:**
1. **고객 데이터를 구체적으로 활용** - 추상적 조언 금지
   - "지난 X월 X일 미팅에서..."
   - "최근 견적서 금액 XXX원을 기준으로..."
   - "과거 구매 패턴상 주로 XX 제품을..."
   - "이전 히스토리 기록에 따르면..."
   
2. **실무자의 질문에 데이터 기반 답변** - 고객 정보를 반드시 인용
3. **영업 전문가처럼 전략적 조언** - 단순 답변이 아닌 전문가 수준의 인사이트
4. **구체적 수치와 날짜 활용** - 제공된 거래 금액, 미팅 날짜, 견적 내역 등을 답변에 포함
5. **고객 맥락 고려** - 고객 유형(교수/연구원/대표/실무자), 등급, 과거 행동 패턴 반영

**답변 스타일:**
- 첫 문장에 핵심 답변
- 구체적인 과거 데이터 인용 (날짜, 금액, 제품명 등)
- "~하면 좋습니다" → "XX 데이터를 보면 이렇게 접근하세요:"
- 실제 사용 가능한 스크립트와 예시 제공

**응답 구조:**
1. 💡 **핵심 답변** - 질문에 대한 명확한 답변 (과거 데이터 기반)
2. 📊 **데이터 분석** - 제공된 고객 정보에서 발견한 패턴과 인사이트
   - 구매 패턴: "지난 6개월간 총 X건, X원 거래"
   - 미팅 히스토리: "최근 X월 X일 미팅에서 언급된 내용"
   - 견적 이력: "XX 제품에 주로 관심, 평균 예산 X만원"
3. 📋 **구체적 실행 방안** - 데이터 기반 단계별 전략
4. 💬 **실전 스크립트** (필요시)
   - 고객 데이터를 언급하는 오프닝 멘트
   - 과거 거래를 활용한 제안 멘트
5. 📧 **이메일/문서 샘플** (필요시) - 실제 데이터를 넣은 샘플
6. 🎯 **전략적 팁** - 고객 특성 기반 추가 조언

**중요: 제공된 모든 고객 정보(히스토리, 구매 이력, 견적, 미팅 메모, 이메일)를 최대한 활용하여 답변하세요.**
**단순히 정보를 나열하지 말고, 이를 분석하여 인사이트를 도출하세요.**"""

    user_prompt = f"""
**🎯 실무자의 질문:**
{user_question}

---

**📋 고객 종합 정보 (이 데이터를 반드시 활용하세요):**

**미팅 일정:**
- 유형: {schedule_info.get('type', '미정')} | 날짜: {schedule_info.get('date', '미정')} {schedule_info.get('time', '미정')}
- 장소: {schedule_info.get('location', '미정')}
- 일정 메모: {schedule_info.get('notes', '없음')}

**고객 프로필:**
- {customer_info.get('name', '미정')} ({customer_info.get('type', '미정')}) | 등급: {customer_info.get('grade', 'C')}
- {customer_info.get('company', '미정')} - {customer_info.get('department', '미정')}
- 책임자: {customer_info.get('manager', '미정')}

**거래 실적 (구체적 수치):**
- 구매 이력: {purchase_summary}
- 견적 이력: {quote_summary}

**상세 거래 내역:**
구매 내역: {delivery_history if delivery_history else '없음'}
견적 내역: {quote_history if quote_history else '없음'}

**과거 활동 기록:**

히스토리 메모 (최근 10개):
{history_summary}

과거 미팅 메모:
{meeting_summary}

이메일 주고받은 내역 (최근 10개):
{email_summary}

---

**💡 답변 요구사항:**

1. **고객 데이터를 구체적으로 인용하여 답변하세요**
   - "지난 X월 X일 미팅에서..."
   - "최근 견적 금액 XXX원 기준..."
   - "과거 구매 패턴을 보면..."
   
2. **영업 전문가 수준의 전략적 인사이트 제공**
   - 데이터에서 발견한 패턴
   - 고객의 관심사와 구매 성향
   - 예상되는 이슈와 대응 방안

3. **실무자가 바로 사용할 수 있는 구체적 가이드**
   - 실제 데이터를 언급하는 대화 스크립트
   - 고객 히스토리를 활용한 제안 방법
   - 구체적인 숫자와 근거 포함

4. **고객 맥락 반영**
   - 고객 유형과 등급에 맞는 접근법
   - 과거 커뮤니케이션 패턴 고려

위의 모든 정보를 최대한 활용하여, 실무자가 "이 AI는 정말 우리 고객을 잘 알고 있구나"라고 느낄 수 있도록 답변해주세요.
"""

    try:
        response = get_openai_client().chat.completions.create(
            model=MODEL_PREMIUM,  # AI 미팅 준비는 프리미엄 모델 사용 (환경 변수로 설정 가능)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS,  # settings.OPENAI_MAX_TOKENS 사용
            temperature=0.7  # 창의적이면서도 실용적인 조언
        )
        
        advice = response.choices[0].message.content
        logger.info(f"Meeting advice generated for customer {customer_info.get('name')} using {MODEL_PREMIUM} (data-driven approach)")
        return advice
    
    except Exception as e:
        logger.error(f"Error generating meeting advice: {e}")
        raise


def analyze_funnel_performance(funnel_data: Dict, user=None) -> str:
    """
    펀넬 대시보드 전체 분석 및 실전 세일즈 전략 수립
    
    Args:
        funnel_data: 펀넬 데이터 (pipeline_summary, stage_breakdown, top_opportunities, won_lost_summary 등)
        user: 현재 사용자 (로그용)
        
    Returns:
        str: AI가 생성한 실전 세일즈 전략 (마크다운 형식)
    """
    system_prompt = """당신은 **20년 경력의 B2B 영업 전략 디렉터**입니다. 
실험실 소모품/장비 영업 조직의 세일즈 파이프라인을 분석하고, 매출 목표 달성을 위한 **실전 중심 액션 플랜**을 제시합니다.

---

## 💼 당신의 역할

**① 영업 관리자** - 팀 전체 파이프라인 건강도 평가, 병목 구간 진단  
**② 전략 컨설턴트** - 단계별 전환율 개선 방안, 예산 갭 해소 로드맵  
**③ 실전 코치** - 개별 고객별 즉시 실행 가능한 액션 아이템 제시

---

## 📋 필수 출력 구조 (반드시 7개 항목 모두 포함)

### **1️⃣ 전체 펀넬 체력 평가 🏥**

**현재 건강도:**  
- 전체 파이프라인 규모 (기회 건수, 예상 매출, 가용 매출)  
- 전환율 현황 (리드→컨택→견적→수주)  
- 승률 (Won/Total)  
- **종합 진단:** 🟢 건강함 / 🟡 주의 필요 / 🔴 위험

**병목 구간:**  
특정 단계에 고객이 몰려있거나, 전환율이 낮은 구간 지적  
예) "견적 단계에 30건 집중, 협상 전환율 낮음 → 견적 후속 관리 강화 필요"

**리스크 요인:**  
- 파이프라인 건수 부족  
- 특정 단계 정체  
- 승률 저하  
- 실주(Lost) 비율 증가

---

### **2️⃣ 금주 TOP 5 액션 아이템 🎯**

**⚠️ 중요: 반드시 제공된 실제 고객 데이터만 사용하세요. 가상의 고객명이나 데이터를 절대 만들지 마세요.**

**실제 데이터가 5개 미만인 경우:**
- 있는 만큼만 표시 (예: 고객이 2명이면 TOP 2만 표시)
- 부족한 부분은 "신규 리드 확보 필요" 같은 일반적인 제안으로 채우지 말 것
- 절대로 "(주)한화", "XX대학교" 같은 예시 고객명을 사용하지 말 것

| 순위 | 고객명 | 액션 | 복붙 가능한 멘트/메일 제목 |
|------|--------|------|----------------------------|
| 1 | [실제 고객명] | [실제 단계 기반 액션] | "[실제 상황 기반 멘트]" |
| 2 | [실제 고객명] | [실제 단계 기반 액션] | "[실제 상황 기반 멘트]" |
| ... | ... | ... | ... |

**우선순위 기준:**  
- 예상 매출액 큰 고객  
- 가용 매출률(Probability) 높은 고객  
- 오래 머물러 있는 고객 (단계별 평균 체류 시간 초과)

**실제 데이터 예시:**
- 제공된 상위 영업 기회 목록에서 고객명, 단계, 예상 매출 확인
- 각 고객의 현재 상태에 맞는 구체적 액션 제시

---

### **3️⃣ 단계별 전략 제안 📊**

**각 단계별 (리드→컨택→견적→협상→클로징→수주/실주) 현황 + 액션:**

예시:
**견적 단계 (30건, 예상 매출 3억)**  
- 현황: 건수 많으나 협상 전환율 낮음  
- 문제: 견적 발송 후 2주 이상 응답 없는 고객 다수  
- 액션:  
  1. 견적 발송 후 3일 이내 후속 전화 (스크립트: "견적서 잘 받으셨나요? 궁금한 점...")  
  2. 견적서 유효기간 명시 (긴급성 부여)  
  3. 경쟁사 대응 자료 첨부

**협상 단계 (10건, 예상 매출 2억)**  
- 현황: 가격 네고 진행 중  
- 액션: 번들 상품 제안, 장기 계약 할인 옵션 제시

---

### **4️⃣ 고객별 맞춤 전략 🎯**

**⚠️ 중요: 반드시 제공된 실제 고객 데이터만 사용하세요.**

**실제 상위 영업 기회 고객 3~5명에 대해:**

**[고객명: 실제 제공된 고객명]**  
- 온도: 🔥 Hot / 🟡 Warm / 🔵 Cold (실제 가용 매출률 기준)
- 예상 매출: [실제 금액]
- 현재 단계: [실제 단계]
- 우선순위: [실제 우선순위]
- **즉시 실행 액션:**  
  1. [실제 상황 기반 액션 1]
  2. [실제 상황 기반 액션 2]
  3. [실제 상황 기반 액션 3]
- **예상 전환 확률:** [실제 probability 기반]

**데이터가 없으면:**
- "현재 상위 영업 기회 데이터가 부족합니다" 라고 명시
- 가상의 고객이나 예시를 절대 만들지 말 것

---

### **5️⃣ 매출 예측 & 갭 분석 💰**

**예상 매출 vs 목표:**  
- 현재 파이프라인 예상 매출: X억  
- 가용 매출 (확률 반영): Y억  
- 목표 매출 (월/분기): Z억  
- **갭:** (Z - Y)억 부족

**갭 해소 전략:**  
- 신규 리드 확보 필요량: XX건  
- 기존 기회 전환율 향상 목표: +X%  
- 고액 기회 집중 공략: 예상 매출 상위 10% 고객 중점 관리

**포트폴리오 전략:**  
- Short-term Win (이번 달 수주 가능): 협상/클로징 단계 고객  
- Mid-term Pipeline (다음 달): 견적 단계 고객  
- Long-term Seed (3개월 후): 신규 리드

---

### **6️⃣ 영업 리스크 관리 ⚠️**

**취소/지연 가능성 높은 고객:**  
- (주)XX: 예산 승인 지연 (액션: 재무팀 직접 컨택)  
- YY연구소: 프로젝트 연기 (액션: 대안 제품 제안)

**경쟁사 이슈:**  
특정 고객에서 경쟁사 제안 확인된 경우 → 차별화 포인트 강조, 가격 재조정

**오래 정체된 기회:**  
3개월 이상 같은 단계에 머문 고객 → Lost 전환 또는 재접근 전략 수립

---

### **7️⃣ 업무 효율화 전략 ⚡**

**미팅 루틴 최적화:**  
- 주간 파이프라인 리뷰 회의 (30분)  
- 일일 TOP 3 고객 집중 관리  
- 단계별 체크리스트 활용

**팔로우업 템플릿:**  
- 견적 발송 후 3일차: "검토 상황 확인" 전화  
- 미팅 후 24시간 이내: 감사 이메일 + 추가 자료 발송  
- 협상 중: 주 1회 정기 체크인

**성과 추적 KPI:**  
- 주간 신규 리드 건수  
- 단계별 전환율  
- 평균 영업 사이클 기간

---

## ✅ 출력 규칙

1. **실제 데이터만 사용** - 제공된 고객명, 금액, 단계만 사용. 가상 데이터 절대 금지
2. **복붙 가능한 멘트/이메일 제목** - 실무자가 즉시 사용 가능  
3. **수치 중심** - "많다/적다" X, "30건, 전환율 15%" O  
4. **액션 중심** - "~해야 한다" X, "오늘 오후 3시까지 전화" O  
5. **이모지 활용** - 가독성 향상 (🎯 🏥 💰 ⚠️ 등)
6. **데이터 부족 시** - "현재 데이터 부족" 명시, 예시/가상 데이터로 채우지 말 것

---

**⚠️ 절대 금지 사항:**
- "(주)한화", "XX대학교", "YY연구소" 같은 가상 고객명 사용 금지
- 제공되지 않은 데이터를 임의로 만들지 말 것
- 예시나 샘플로 테이블을 채우지 말 것
- 실제 제공된 고객 목록에 없는 고객을 언급하지 말 것

**중요: 제공된 펀넬 데이터를 최대한 활용하여, 실무자가 "이 AI는 우리 영업 상황을 정확히 파악하고 있다"고 느낄 수 있도록 분석하세요.**"""

    # 펀넬 데이터 포맷팅
    pipeline = funnel_data.get('pipeline_summary', {})
    stages = funnel_data.get('stage_breakdown', [])
    opportunities = funnel_data.get('top_opportunities', [])
    won_lost = funnel_data.get('won_lost_summary', {})
    
    # 단계별 데이터 포맷팅
    stage_info = "\n".join([
        f"- {s.get('stage_display', s.get('stage', ''))}: {s.get('count', 0)}건, "
        f"예상 매출 {s.get('expected_revenue', 0):,.0f}원, "
        f"가용 매출 {s.get('weighted_revenue', 0):,.0f}원"
        for s in stages
    ]) if stages else "단계별 데이터 없음"
    
    # 상위 기회 포맷팅
    opportunity_info = "\n".join([
        f"- {opp.get('customer_name', '미정')}: {opp.get('stage_display', opp.get('current_stage', ''))} 단계, "
        f"예상 매출 {opp.get('expected_revenue', 0):,.0f}원, "
        f"가용 매출률 {opp.get('probability', 0)}%, "
        f"우선순위 {opp.get('priority', 'C')}, "
        f"등급 {opp.get('grade', 'C')}"
        for opp in opportunities[:10]  # 상위 10개만
    ]) if opportunities else "영업 기회 데이터 없음"
    
    user_prompt = f"""
**📊 현재 세일즈 파이프라인 데이터:**

**전체 파이프라인 요약:**
- 총 기회 건수: {pipeline.get('total_opportunities', 0)}건
- 예상 매출: {pipeline.get('total_expected_revenue', 0):,.0f}원
- 가용 매출 (확률 반영): {pipeline.get('total_weighted_revenue', 0):,.0f}원
- 평균 전환율: {pipeline.get('conversion_rate', 0):.1f}%
- 승률 (Won Rate): {pipeline.get('win_rate', 0):.1f}%

**단계별 분포:**
{stage_info}

**수주/실주 현황:**
- 수주: {won_lost.get('won_count', 0)}건, {won_lost.get('won_revenue', 0):,.0f}원
- 실주: {won_lost.get('lost_count', 0)}건, {won_lost.get('lost_revenue', 0):,.0f}원

**상위 영업 기회 (Top 10):**
{opportunity_info}

---

**위 데이터를 기반으로 7가지 필수 항목을 모두 포함하여 실전 세일즈 전략을 수립해주세요:**

1️⃣ 전체 펀넬 체력 평가 🏥
2️⃣ 금주 TOP 5 액션 아이템 🎯
3️⃣ 단계별 전략 제안 📊
4️⃣ 고객별 맞춤 전략 🎯
5️⃣ 매출 예측 & 갭 분석 💰
6️⃣ 영업 리스크 관리 ⚠️
7️⃣ 업무 효율화 전략 ⚡

**실무자가 오늘 당장 실행할 수 있는, 구체적이고 데이터 기반의 전략을 제시해주세요.**
"""

    try:
        logger.info(f"[펀넬 분석] AI 호출 시작 - 모델: {MODEL_STANDARD}, 사용자: {user}")
        
        response = get_openai_client().chat.completions.create(
            model=MODEL_STANDARD,  # GPT-4o 사용 (실전 전략 수립)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.7  # 창의적이면서도 실용적인 조언
        )
        
        analysis = response.choices[0].message.content
        logger.info(f"Funnel analysis generated using {MODEL_STANDARD}")
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing funnel performance: {e}")
        raise

