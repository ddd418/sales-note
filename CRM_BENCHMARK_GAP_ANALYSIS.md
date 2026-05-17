# CRM Benchmark Gap Analysis

작성일: 2026-05-18

## 1. 목적

사용자가 제공한 글로벌 CRM 조사 보고서를 기준으로 현재 Sales Note / Sales Management System을 비교했다. 기준은 12개 CRM 축이며, 평가는 현재 코드와 React 네비게이션에서 확인되는 실제 구현을 기준으로 한다.

이번 문서는 런타임 변경 없이 다음 구현 우선순위를 정하기 위한 갭 분석 산출물이다.

## 2. 핵심 결론

현재 시스템은 단순 영업노트 도구보다 이미 넓은 CRM 골격을 갖고 있다. 고객, 부서/연구실, 활동 기록, 일정, 파이프라인, 제품, 견적, 납품, 서류, 메일, 선결제, 주간보고, AI Workspace가 구현되어 있다.

글로벌 CRM 보고서와 비교했을 때 가장 큰 벤치마킹 기회는 생명과학 유통/기술영업 특화 영역이다.

1. 고객별 보유 장비, 모델명, 시리얼번호, 구매일, 보증기간
2. A/S 케이스, 클레임, 수리, SLA, 서비스 리포트
3. 피펫/장비 교정 주기, 다음 교정 예정일, 성적서, 부품 교체 이력
4. 제품 마스터와 AI 답변의 근거 연결 강화
5. 캠페인/수신동의, 감사 로그, 개인정보 보존 정책

따라서 다음 큰 기능은 일반적인 리드 관리보다 **고객 보유 장비 + A/S/교정 모듈**을 우선 검토하는 것이 맞다. 보고서에서도 이 영역이 하나과학 같은 생명과학 유통/기술영업 조직의 차별화 포인트로 제시되어 있고, 현재 코드에서도 독립 모델이 발견되지 않는다.

## 3. 현재 구현 근거

현재 확인된 주요 모델:

| 영역 | 현재 구현 근거 |
| --- | --- |
| 고객/거래처 | `Company`, `Department`, `FollowUp`, `CustomerCategory` |
| 담당자/연락처 | `FollowUp.customer_name`, `manager`, `phone_number`, `email`, `address` |
| 활동/일정 | `Schedule`, `History`, `HistoryFile`, `ScheduleFile` |
| 파이프라인 | `FunnelStage`, `OpportunityTracking`, `OpportunityLabel`, `FunnelTarget` |
| 제품/견적/납품 | `Product`, `Quote`, `QuoteItem`, `DeliveryItem`, `ScheduleQuoteGroupNote` |
| 서류 | `DocumentTemplate`, `DocumentGenerationLog` |
| 메일 | `EmailLog`, Gmail/IMAP/SMTP 관련 view/util |
| 결제/세금계산서 | `Prepayment`, `PrepaymentUsage`, `TaxInvoiceRequest` |
| 보고 | `WeeklyReport`, dashboard/pipeline APIs |
| AI | `AIWorkspaceQuestionLog`, `AIWorkspaceQuestionFeedback`, `AIWorkspaceAnswerDirection`, `AIWorkspaceActionFeedback` |
| 권한 | `UserProfile`, role 기반 view/API 권한 체크 |

React 기본 네비게이션:

`대시보드`, `고객`, `파이프라인`, `영업노트`, `일정`, `메일`, `주간보고`, `서류`, `제품`, `선결제`, `AI`

현재 검색에서 독립 모델로 발견되지 않은 축:

`Contact`, `Lead`, `Campaign`, `Asset`, `Equipment`, `ServiceCase`, `Ticket`, `Calibration`, `AuditLog`

단, `Lead`는 별도 모델은 없지만 `OpportunityTracking.current_stage='lead'` 단계로 일부 대체되고, `Service`는 `Schedule.activity_type='service'`와 `History.service_status`로 일부 대체된다.

## 4. 글로벌 12축 갭 분석표

| CRM 축 | 현재 커버리지 | 현재 구현 | 주요 갭/리스크 | 권장 우선순위 |
| --- | --- | --- | --- | --- |
| 1. 거래처·고객·담당자 통합 DB | 부분 구현 | `Company`, `Department`, `FollowUp` | 담당자가 독립 `Contact`가 아니라 `FollowUp` 안에 포함되어 담당자 변경 이력, 복수 담당자, 구매/기술/세금계산서 역할 분리가 약하다. | P0 보강 |
| 2. 리드·영업기회·파이프라인 | 부분 구현 | `OpportunityTracking`, `FunnelStage`, `FollowUp.pipeline_stage` | 별도 `Lead` 모델과 리드 출처/전환율/자동 배정은 없다. 파이프라인은 있으나 리드 소스 관리가 약하다. | P1 |
| 3. 방문·전화·이메일·미팅 활동 이력 | 강함 | `Schedule`, `History`, `EmailLog`, files, next action | 활동 기록과 이메일은 강하지만 통화 로그, 캘린더 외부 연동, 모바일 현장 입력 고도화는 추가 여지 있다. | 유지/P1 |
| 4. 견적·가격·할인·승인 | 부분 구현 | `Product`, `Quote`, `QuoteItem`, `DeliveryItem`, document templates | 견적/할인 계산은 있으나 공급가/마진, 할인 승인 워크플로, 고객별 특가, 승인 로그는 약하다. | P1 |
| 5. 제품·재고·주문·ERP 연동 | 부분 구현 | `Product`, `DeliveryItem`, `TaxInvoiceRequest`, prepayment | 제품 마스터와 납품은 있으나 재고, 주문 상태, ERP/회계 실시간 연동, 품절/대체품 추천은 없다. | P1 |
| 6. A/S·클레임·티켓·SLA | 약함 | `Schedule.activity_type='service'`, `History.service_status` | 서비스가 활동 유형 수준이다. 독립 케이스 번호, 우선순위, SLA, 원인 분류, 처리 시간, 재발 방지, 고객 서명 리포트가 없다. | P0 |
| 7. 장비/자산·시리얼·보증·교정 | 없음 | 독립 모델 없음 | 생명과학 유통 핵심 영역인데 고객별 장비 대장, 시리얼번호, 구매일, 보증기간, 교정 주기, 성적서, 부품 이력이 없다. | P0 |
| 8. 마케팅 캠페인·세그먼트·동의 | 약함 | `EmailLog`, AI 프롬프트 일부 | 캠페인, 세미나, 뉴스레터, 수신동의, 수신거부, 캠페인 ROI 모델이 없다. 개인정보/마케팅 동의는 초기에 구조를 잡아야 한다. | P1 |
| 9. 대시보드·매출 예측·성과 분석 | 부분 구현 | dashboard API, `OpportunityTracking.weighted_revenue`, `FunnelTarget`, `WeeklyReport` | 영업 대시보드는 있으나 서비스/교정/장비 KPI, 캠페인 KPI, 예측 정확도, 경영진용 고정 KPI 체계는 보강 필요하다. | P1 |
| 10. 자동화·알림·승인 워크플로 | 부분 구현 | next action, overdue, AI action feedback, manager review | 규칙 기반 알림은 일부 있으나 노코드 조건, 할인/반품/무상수리 승인, SLA 초과 알림은 없다. | P1 |
| 11. AI 보조 기능 | 강함 | AI Workspace, question logs, feedback, answer direction, product-code grounding tests | AI 기능은 강하지만 답변마다 근거/불확실성/제품 마스터 근거를 더 명확히 보여줘야 한다. 제품 코드 오분류 방지는 계속 핵심 품질 과제로 둔다. | P0 유지 |
| 12. 보안·권한·감사·개인정보·API | 부분 구현 | `UserProfile`, role checks, login protection, privacy/terms pages, permission tests | 인증/권한은 적극적으로 구현되어 있으나 도메인 감사 로그, 2FA, 개인정보 보유기간/삭제 요청, 수신동의 이력은 없다. | P1, 감사 로그는 P0 후보 |

## 5. 벤치마킹해서 가져올 기능

### 5.1 최우선: 고객별 장비/교정/A/S 축

가장 먼저 벤치마킹할 기능은 Salesforce Service Cloud, Dynamics Customer Service류의 일반 케이스 관리가 아니라, 생명과학 유통 업무에 맞춘 **고객별 장비 대장 + 교정/서비스 이력**이다.

권장 v1 범위:

| 기능 | v1 범위 |
| --- | --- |
| 고객 보유 장비 | 고객/부서 연결, 장비명, 모델명, 시리얼번호, 구매일, 설치장소, 보증 종료일 |
| 서비스 케이스 | 케이스 유형, 접수일, 상태, 담당자, 우선순위, 고객 증상, 처리 내용 |
| 교정 이력 | 교정일, 다음 교정 예정일, 결과, 성적서 파일, 비고 |
| 고객 상세 연결 | 고객 상세 화면에서 보유 장비, 진행 중 서비스, 교정 만료 예정 표시 |
| 영업 연결 | 교정 만료/보증 만료/소모품 재구매를 AI와 파이프라인 추천 신호로 사용 |

이 기능은 현재 시스템의 강점인 고객, 일정, 히스토리, 제품, AI Workspace와 자연스럽게 연결된다.

### 5.2 AI 답변 품질 벤치마크

최근 확인된 `P4345N00` 제품 오분류 같은 문제는 CRM AI에서 반드시 막아야 한다. AI가 제품 코드를 보고 임의로 "튜브", "팁", "장비" 같은 라벨을 붙이면 영업 판단이 흔들린다.

권장 방향:

- 제품 코드는 항상 `Product.description`, `specification`, `unit`, 견적/납품 품목 근거와 함께 전달한다.
- 답변 UI에 제품 추천 근거와 데이터 출처를 표시한다.
- 제품 마스터에 없는 품목 유형은 답변에서 확정 표현하지 않는다.
- 사용자의 부정 피드백은 같은 사용자 답변 컨텍스트에 반영하되, CRM 사실로 취급하지 않는다.

### 5.3 견적/가격/승인 보강

현재 견적과 납품 품목 계산은 존재한다. 글로벌 CRM/CPQ 관점에서 다음 단계는 할인 승인, 마진 확인, 고객별 특가, 견적 유효기간/상태 추적 강화다.

권장 방향:

- 일정 할인율 이상은 관리자 승인 필요
- 견적별 마진/공급가 입력 구조 검토
- 고객/부서별 과거 견적 가격 비교
- 견적 후 follow-up 자동 리마인드

### 5.4 감사 로그와 개인정보/동의

내부 CRM은 고객 연락처, 영업기밀, 견적 정보를 다룬다. 현재 role 기반 권한과 테스트는 강점이지만, 누가 어떤 고객/견적/가격 정보를 언제 수정했는지 남기는 도메인 감사 로그는 별도 축으로 필요하다.

권장 방향:

- 고객, 견적, 제품 가격, 선결제, 서비스 케이스 변경 이력부터 감사 로그화
- 마케팅 수신동의/수신거부/동의 출처/동의일 관리
- 퇴사자 계정 비활성화와 고객 소유권 이전 흐름 정리

## 6. 권장 로드맵

### Phase A: 장비/서비스/교정 CRM v1

목표: 고객별 보유 장비와 서비스/교정 이력을 CRM 핵심 데이터로 편입한다.

권장 구현 순서:

1. 데이터 모델 설계: 고객 보유 장비, 서비스 케이스, 교정 이력
2. Django JSON API와 권한 규칙 추가
3. React 고객 상세 화면에 보유 장비/서비스/교정 섹션 추가
4. 서비스/교정 목록 화면 또는 필터 추가
5. AI Workspace와 대시보드에 교정 만료/서비스 미처리 신호 연결

### Phase B: AI 제품 근거와 견적 품질 강화

목표: AI가 제품/견적/납품 사실을 정확히 말하게 하고, 견적 후속 액션을 더 안정적으로 추천하게 한다.

권장 구현 순서:

1. 답변 UI에 근거 제품/견적/납품 라인 표시
2. 제품 마스터 불일치/불확실 항목 경고
3. 견적 후 follow-up 자동 후보 강화
4. 할인/마진/승인 워크플로 설계

### Phase C: 감사/동의/캠페인

목표: 글로벌 CRM 수준의 운영 안정성과 마케팅 확장 기반을 만든다.

권장 구현 순서:

1. 고객/견적/가격/선결제 변경 감사 로그
2. 담당자별 마케팅 수신동의/거부
3. 캠페인/세미나/뉴스레터 출처 관리
4. 캠페인별 리드/견적/수주 연결

## 7. 다음 구현 후보

가장 추천하는 다음 작업은 **고객 보유 장비 + 서비스/교정 모듈 v1 설계와 구현**이다.

이유:

- 글로벌 CRM 보고서에서 생명과학 유통/피펫/장비 서비스 조직의 핵심 차별화 기능으로 강조된다.
- 현재 시스템에는 해당 독립 모델이 없다.
- 기존 고객, 일정, 히스토리, 제품, AI Workspace와 연결성이 높다.
- 영업적으로 교정 만료, 보증 만료, 소모품 재구매, 장비 교체 시점 추천까지 확장할 수 있다.

다음 구현 전 결정해야 할 사항:

1. 장비를 고객 개인(`FollowUp`) 기준으로 볼지, 부서/연구실(`Department`) 기준으로 볼지, 둘 다 연결할지
2. 서비스 케이스와 교정 이력을 하나의 케이스 모델로 묶을지, 별도 모델로 둘지
3. 성적서/서비스 리포트 파일을 기존 `ScheduleFile`/`HistoryFile`과 연결할지, 장비/케이스 전용 파일 모델을 둘지
4. 첫 화면을 고객 상세 내 섹션으로 시작할지, 독립 `서비스/장비` React 메뉴로 시작할지

권장 기본값은 고객 상세 내 섹션부터 시작하는 것이다. 별도 메뉴보다 현장 영업 사용성이 높고, 기존 고객 상세/AI 컨텍스트와 연결하기 쉽다.
