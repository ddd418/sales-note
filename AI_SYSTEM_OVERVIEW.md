# Sales-Note AI 시스템 전체 구조 및 프롬프트 분석

## 📋 프로젝트 개요

**Sales-Note**는 B2B 과학실험실 장비 영업을 위한 CRM 시스템입니다.

- Django 5.2.3 기반 웹 애플리케이션
- PostgreSQL 데이터베이스
- OpenAI GPT API 통합 (GPT-4o, GPT-4o-mini)

---

## 🤖 AI 기능 목록

### 1. 이메일 생성 (`generate_email`)

| 항목            | 내용                                                                      |
| --------------- | ------------------------------------------------------------------------- |
| **목적**        | 영업 이메일 자동 생성 (신규 작성/답장)                                    |
| **사용 모델**   | formal 톤: GPT-4o / casual, simple 톤: GPT-4o-mini                        |
| **입력 데이터** | 고객명, 회사명, 제품, 일정 내용, 메모, 일정 히스토리, 원본 이메일(답장시) |
| **출력 형식**   | JSON: `{subject, body}` (HTML 형식 본문)                                  |

**시스템 프롬프트 핵심:**

```
너는 B2B 영업 20년차의 이메일 작성 전문가이며,
히스토리 데이터(History Log)를 기반으로 해당 고객에게 보낼 최적의 이메일 초안을 작성

금지 규칙:
- 한국어만 사용
- 마크다운/장식 금지
- 의미를 임의로 확장하거나 다른 스토리를 만들지 말 것 (오직 히스토리 기반 내용만 활용)
```

**톤 설정:**

- `formal`: 현대적이고 전문적인 비즈니스 어조 (존경하는, 귀하 금지)
- `casual`: 친근하면서도 프로페셔널한 어조
- `simple`: 핵심만 간결하게 전달

---

### 2. 이메일 변환 (`transform_email`)

| 항목            | 내용                                               |
| --------------- | -------------------------------------------------- |
| **목적**        | 기존 이메일을 다른 톤으로 변환                     |
| **사용 모델**   | formal 톤: GPT-4o / casual, simple 톤: GPT-4o-mini |
| **입력 데이터** | 원본 이메일, 변환 톤, 추가 지시사항                |
| **출력 형식**   | JSON: `{body}`                                     |

**시스템 프롬프트 핵심:**

```
너는 B2B 영업 20년 경력의 '세일즈 이메일 리라이팅 전문가'

⚠️ 절대 규칙: 이것은 반드시 비즈니스 이메일이어야 한다!
- 수신자는 고객, 교수, 연구원, 병원 관계자 등 비즈니스 파트너
- 전문성과 신뢰감을 유지하면서 톤만 조정
```

---

### 3. 고객 인사이트/요약 (`generate_customer_summary`)

| 항목            | 내용                                         |
| --------------- | -------------------------------------------- |
| **목적**        | 고객 정보 종합 분석 및 영업 전략 리포트 생성 |
| **사용 모델**   | GPT-4o (외부 공유 가능성 고려)               |
| **Temperature** | 0.7 (창의적 전략 제안)                       |
| **입력 데이터** | 아래 상세                                    |
| **출력 형식**   | 마크다운 형식 리포트                         |

**입력 데이터 상세:**

```python
customer_data = {
    'name': 고객명,
    'company': 회사명,
    'department': 부서/연구실명,
    'customer_notes': 영업담당자 메모,
    'history_text': 히스토리 기록 (최근 20개),
    'industry': 업종 (기본값: '과학/실험실'),
    'meeting_count': 미팅 횟수 (12개월),
    'quote_count': 견적 횟수,
    'purchase_count': 구매 횟수,
    'total_purchase': 총 구매액,
    'last_contact': 마지막 연락일,
    'quotes': 견적 내역 (최근 5개),
    'meeting_notes': 미팅 노트 (최근 5개),
    'email_count': 이메일 교환 건수,
    'customer_grade': 고객 등급 (A+/A/B/C/D),
    'prepayment': 선결제 정보 {total_balance, count, details[]},
    'email_conversations': 이메일 내용 (최근 10건),
    'recommended_products': 추천하고 싶은 제품 목록,
    # 부서 전체 데이터 (최근 추가)
    'department_summary': {
        'total_customers': 부서 내 총 고객 수,
        'other_customers': [{name, meeting_count, delivery_count, total_purchase, grade}],
        'total_meeting_count': 부서 전체 미팅,
        'total_quote_count': 부서 전체 견적,
        'total_purchase_count': 부서 전체 구매,
        'total_purchase_amount': 부서 전체 구매액,
        'total_email_count': 부서 전체 이메일,
        'meeting_notes': 부서 전체 미팅 노트,
        'history_text': 부서 전체 히스토리,
    }
}
```

**시스템 프롬프트 출력 구조:**

```
## 1. 고객 개요
## 2. 최근 활동 요약
## 3. 🧪 실험/연구 분야 분석 및 제품 추천
   - 예상 연구 분야 및 실험 유형
   - 사용 가능성 있는 용매/시약 분석
   - 🎯 맞춤 제품 추천
   - ⚠️ 비추천 제품/기능
## 4. 구매 가능성 평가
## 5. 주요 장애 요인 또는 리스크
## 6. 추천 팔로우업 액션 (실전 영업 전략)
```

---

### 4. 고객 등급 평가 (`update_customer_grade_with_ai`)

| 항목            | 내용                                            |
| --------------- | ----------------------------------------------- |
| **목적**        | AI 기반 고객 등급 자동 산정                     |
| **사용 모델**   | GPT-4o-mini (내부용)                            |
| **Temperature** | 0.2 (일관성 중요)                               |
| **입력 데이터** | 고객 활동 통계, 구매 이력, 미팅 요약, 영업 기회 |
| **출력 형식**   | JSON                                            |

**입력 데이터:**

```python
customer_data = {
    'name': 고객명,
    'company': 회사명,
    'department': 부서/연구실,
    'meeting_count': 미팅 횟수,
    'email_count': 이메일 건수,
    'quote_count': 견적 횟수,
    'purchase_count': 총 구매 횟수,
    'recent_purchase_count': 최근 구매 횟수,
    'total_purchase': 총 구매 금액,
    'recent_total_purchase': 최근 구매액,
    'prepayment_count': 선결제 건수,
    'total_prepayment': 선결제 금액,
    'last_contact': 마지막 접촉일,
    'avg_response_time': 평균 응답 시간,
    'email_sentiment': 이메일 감정 톤,
    'meeting_summary': 최근 미팅 요약 리스트,
    'opportunities': 진행 중인 영업 기회,
    # 부서 전체 데이터
    'department_summary': {total_customers, total_purchase_count, total_purchase_amount}
}
```

**출력 형식:**

```json
{
  "grade": "A+|A|B|C|D",
  "score": 0-100,
  "reasoning": "등급 산정 이유 (3-5문장)",
  "factors": {
    "engagement": 0-100,
    "purchase_potential": 0-100,
    "relationship": 0-100,
    "responsiveness": 0-100
  },
  "recommendations": ["추천 액션1", "추천 액션2"]
}
```

**등급 기준:**

- A+ (90-100점): VIP 고객, 즉시 구매 가능성 높음
- A (80-89점): 우수 고객, 단기 구매 가능성
- B (60-79점): 양호 고객, 중기 육성 필요
- C (40-59점): 보통 고객, 장기 관리
- D (0-39점): 저조 고객, 재검토 필요

---

### 5. 이메일 스레드 분석 (`analyze_email_thread`)

| 항목            | 내용                                             |
| --------------- | ------------------------------------------------ |
| **목적**        | 이메일 대화 분석으로 구매 온도 및 영업 전략 수립 |
| **사용 모델**   | GPT-4o                                           |
| **Temperature** | 0.4                                              |
| **입력 데이터** | 이메일 리스트 [{date, from, subject, body}]      |
| **출력 형식**   | JSON                                             |

**출력 형식:**

```json
{
  "purchase_temperature": 8, // 0~10점
  "temperature_reason": "구매 온도 판단 근거",
  "hidden_intent": ["숨은 의도/제한조건 리스트"],
  "customer_status": "CRM 상태 라벨",
  "recommended_actions": ["추천 후속 액션"],
  "followup_email_draft": "후속 이메일 초안",
  "latent_needs": ["잠재 니즈 예측"],
  "summary": "스레드 요약"
}
```

**구매 온도 기준:**

- 8~10점: 즉시 구매 가능 (결재 진행, 납품 일정 협의)
- 5~7점: 관심 있으나 조건/예산 확인 필요
- 3~4점: 탐색 단계 (정보 수집 중)
- 0~2점: 구매 의사 없음 또는 거절

---

### 6. 상품 추천 (`recommend_products`)

| 항목            | 내용                                      |
| --------------- | ----------------------------------------- |
| **목적**        | 고객 맞춤 상품 추천                       |
| **사용 모델**   | GPT-4o-mini                               |
| **Temperature** | 0.6                                       |
| **입력 데이터** | 구매 이력, 견적 이력, 미팅 노트, 히스토리 |
| **출력 형식**   | JSON                                      |

**입력 데이터:**

```python
customer_data = {
    'name': 고객명,
    'company': 회사명,
    'industry': 부서/업종,
    'purchase_history': 구매 이력 (최근 2년),
    'quote_history': 견적 이력 (최근 6개월),
    'meeting_notes': 미팅 노트,
    'history_notes': 실무자 히스토리,
    'interest_keywords': 관심 키워드
}
```

**출력 형식:**

```json
{
  "recommendations": [
    {
      "product_name": "제품명",
      "category": "카테고리",
      "reason": "추천 이유",
      "priority": "high|medium|low",
      "expected_timing": "제안 시기",
      "estimated_price_range": "예상 가격대",
      "related_products": ["관련 제품"]
    }
  ],
  "analysis_summary": "고객 분석 요약"
}
```

---

### 7. 미팅 노트 요약 (`summarize_meeting_notes`)

| 항목            | 내용                               |
| --------------- | ---------------------------------- |
| **목적**        | 미팅 기록 자동 요약 및 키워드 추출 |
| **사용 모델**   | GPT-4o-mini                        |
| **입력 데이터** | 미팅 노트 텍스트                   |
| **출력 형식**   | JSON                               |

**출력 형식:**

```json
{
  "summary": "3줄 요약",
  "key_points": ["주요 포인트"],
  "action_items": ["액션 아이템"],
  "keywords": {"예산": "값", "납기": "값", ...}
}
```

---

### 8. 팔로우업 제안 (`suggest_follow_ups`)

| 항목            | 내용                                     |
| --------------- | ---------------------------------------- |
| **목적**        | 고객 목록 분석 및 팔로우업 우선순위 제안 |
| **사용 모델**   | GPT-4o-mini                              |
| **Temperature** | 0.5                                      |
| **입력 데이터** | 고객 리스트 (최대 20명)                  |
| **출력 형식**   | JSON                                     |

**입력 데이터:**

```python
customer_list = [{
    'id': 고객ID,
    'name': 고객명,
    'company': 회사명,
    'last_contact': 마지막 연락일,
    'meeting_count': 미팅 횟수,
    'quote_count': 견적 횟수,
    'purchase_count': 구매 횟수,
    'total_purchase': 총 구매액,
    'grade': 고객 등급,
    'opportunities': 진행 중인 기회,
    'prepayment_balance': 선결제 잔액,
    'history_notes': 히스토리 메모,
    'recent_emails': 최근 이메일 내용
}]
```

**출력 형식:**

```json
{
  "suggestions": [
    {
      "customer_name": "고객명",
      "priority": "high|medium|low",
      "reason": "우선순위 이유",
      "recommended_action": "추천 액션",
      "timing": "언제"
    }
  ]
}
```

---

### 9. 이메일 감정 분석 (`analyze_email_sentiment`)

| 항목            | 내용                                 |
| --------------- | ------------------------------------ |
| **목적**        | 이메일 감정 분석 및 구매 가능성 예측 |
| **사용 모델**   | GPT-4o-mini                          |
| **Temperature** | 0.3                                  |
| **입력 데이터** | 이메일 내용                          |
| **출력 형식**   | JSON                                 |

**출력 형식:**

```json
{
  "sentiment": "positive|neutral|negative",
  "purchase_probability": "high|medium|low",
  "urgency": "immediate|soon|later",
  "keywords": ["키워드"],
  "recommendation": "추천 액션"
}
```

---

### 10. 자연어 검색 (`natural_language_search`)

| 항목            | 내용                                           |
| --------------- | ---------------------------------------------- |
| **목적**        | 자연어 검색 쿼리를 Django ORM 필터로 변환      |
| **사용 모델**   | GPT-4o-mini                                    |
| **입력 데이터** | 자연어 쿼리 (예: "지난달 견적 준 고객 보여줘") |
| **출력 형식**   | JSON (Django 필터 조건)                        |

**시스템 프롬프트에 포함된 DB 스키마:**

- FollowUp (고객): customer_name, company, customer_grade, email, phone_number, etc.
- Schedule (일정): followup, activity_type, visit_date, notes, status
- EmailLog (이메일): followup, email_type, sender, subject, sent_at
- DeliveryItem (납품 상품): schedule, product, item_name, quantity
- Prepayment (선결제): followup, amount, remaining_amount
- OpportunityTracking (영업기회): followup, current_stage, expected_revenue

---

### 11. 미팅 전략 (`generate_meeting_strategy`)

| 항목            | 내용                                             |
| --------------- | ------------------------------------------------ |
| **목적**        | 일정 기반 AI 미팅 전략 추천                      |
| **사용 모델**   | GPT-4o                                           |
| **Temperature** | 0.7                                              |
| **입력 데이터** | 일정 정보, 고객 히스토리, 선결제 잔액, 납품 품목 |
| **출력 형식**   | 마크다운                                         |

**입력 데이터:**

- 일정 정보 (유형, 날짜, 시간, 장소, 메모)
- 일정 관련 히스토리 (본인 기록만)
- 고객 전체 히스토리 (최근 20개)
- 선결제 잔액 및 내역
- 납품 품목 (납품 일정인 경우)

**출력 구조:**

```
📊 상황 분석
 - 고객 정보
 - 히스토리 기반 니즈
 - 선결제 잔액

🎯 미팅 전략
 - 핵심 주제 TOP 3
 - 상황 공감 기반 접근
 - 시연 중심 접근
 - 예산 최적화 관점 접근
 - 제안 포인트

📋 실행 체크리스트
 - 준비물
 - 확인 사항
```

**핵심 원칙:**

- 질문형 대화 전략 금지 - 고객이 스스로 니즈를 느끼도록 유도
- 판매 의도가 티나는 직설적인 질문 절대 금지
- 시연을 통해 고객이 스스로 문제를 느끼도록 유도

---

### 12. 펀넬 대시보드 분석 (`analyze_funnel_performance`)

| 항목            | 내용                                                                  |
| --------------- | --------------------------------------------------------------------- |
| **목적**        | 영업 파이프라인 분석 및 실전 세일즈 전략 수립                         |
| **사용 모델**   | GPT-4o                                                                |
| **Temperature** | 0.7                                                                   |
| **입력 데이터** | 펀넬 데이터 (파이프라인 요약, 단계별 분포, 상위 기회, 수주/실주 현황) |
| **출력 형식**   | 마크다운 (7개 필수 항목)                                              |

**입력 데이터:**

```python
funnel_data = {
    'pipeline_summary': {
        'total_opportunities': 총 기회 건수,
        'total_expected_revenue': 예상 매출,
        'total_weighted_revenue': 가용 매출,
        'conversion_rate': 전환율,
        'win_rate': 승률
    },
    'stage_breakdown': [{stage, count, total_value, weighted_value}],
    'top_opportunities': [{
        'customer_name', 'company_name', 'current_stage',
        'expected_revenue', 'probability', 'priority', 'customer_grade'
    }],
    'won_lost_summary': {won_count, won_revenue, lost_count, lost_revenue}
}
```

**필수 출력 구조 (7개 항목):**

```
1️⃣ 전체 펀넬 체력 평가 🏥
2️⃣ 금주 TOP 5 액션 아이템 🎯
3️⃣ 단계별 전략 제안 📊
4️⃣ 고객별 맞춤 전략 🎯
5️⃣ 매출 예측 & 갭 분석 💰
6️⃣ 영업 리스크 관리 ⚠️
7️⃣ 업무 효율화 전략 ⚡
```

**영업 단계 정의:**

1. 리드 (Lead): 첫 미팅 예정 - 예상 매출 0원
2. 컨텍 (Contact): 미팅 완료, 니즈 파악됨 - 예상 매출 0원
3. 견적 (Quote): 견적서 발송/검토 중 - 예상 매출 발생
4. 수주예정 (Closing): 계약 확정 직전
5. 수주 (Won) / 실주 (Lost): 최종 결과

---

## 🔧 모델 선택 전략

| 모델            | 용도                   | 특징                                                  |
| --------------- | ---------------------- | ----------------------------------------------------- |
| **GPT-4o-mini** | 내부용, 빠른 응답 필요 | 일상 이메일, 요약, 팔로우업, 등급 평가, 상품 추천     |
| **GPT-4o**      | 고품질, 외부 공유 가능 | 고객 리포트, 미팅 전략, 펀넬 분석, 이메일 스레드 분석 |

---

## 📊 데이터 모델 (주요)

### FollowUp (고객)

```python
- customer_name: 고객명
- company: ForeignKey(Company)
- department: ForeignKey(Department)
- manager: 담당자명
- email, phone_number, address
- priority: 우선순위 (high/medium/low)
- customer_grade: 고객 등급 (A+/A/B/C/D)
- notes: 메모
```

### Schedule (일정)

```python
- followup: ForeignKey(FollowUp)
- activity_type: 활동 유형 (customer_meeting/quote/delivery/call/email 등)
- visit_date, visit_time, location
- notes: 메모
- status: 상태
```

### History (히스토리)

```python
- followup: ForeignKey(FollowUp)
- schedule: ForeignKey(Schedule, optional)
- user: 작성자
- action_type: 활동 유형
- content: 내용
- meeting_date: 미팅 날짜
```

### Prepayment (선결제)

```python
- customer: ForeignKey(FollowUp)
- amount: 입금액
- balance: 잔액
- payment_date: 입금일
- memo: 메모
- status: 상태 (active/completed)
```

### OpportunityTracking (영업기회)

```python
- followup: ForeignKey(FollowUp)
- current_stage: 현재 단계 (lead/contact/quote/closing/won/lost)
- expected_revenue: 예상 매출
- probability: 성공 확률
- priority: 우선순위
```

---

## 🎯 개편 시 고려사항

### 현재 구조의 특징

1. **부서 중심 데이터 모델**: 최근 고객 → 부서 중심으로 전환
2. **본인 기록만 분석**: AI 분석 시 현재 로그인 사용자가 작성한 기록만 사용
3. **과학/실험실 도메인 특화**: 피펫, 용매, 시약, HPLC 등 전문 용어 사용
4. **실전 영업 중심**: 질문형 전략 금지, 시연 중심 접근

### 개선 포인트 제안

1. 프롬프트 최적화 (토큰 효율성)
2. 응답 일관성 향상 (Temperature 조정)
3. 도메인 지식 강화 (제품 카탈로그 연동)
4. 다국어 지원 가능성
5. 피드백 루프 (AI 응답 품질 평가)

---

## 📁 파일 구조

```
reporting/
├── ai_utils.py      # AI 유틸리티 함수들 (프롬프트, API 호출)
├── ai_views.py      # AI 관련 뷰 (엔드포인트)
├── models.py        # 데이터 모델
├── views.py         # 일반 뷰
└── urls.py          # URL 라우팅
```

---

**이 문서를 기반으로 AI 시스템 개편을 진행해주세요.**
