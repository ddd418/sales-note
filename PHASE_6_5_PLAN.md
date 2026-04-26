# PHASE_6_5_PLAN.md

## Phase 6.5 — 실사용 교정 및 AI/보고서 개선 계획

**날짜**: 2026-04-26  
**상태**: 계획 수립  
**범위**: 코드 변경 없음 — 계획 문서만

---

## 1. 현재 AI 분석 플로우

```
사용자 (can_use_ai=True 권한 필요)
  │
  └─ /ai/departments/               ← department_list view
       └─ 부서 선택
           │
           └─ /ai/departments/<id>/  ← department_analysis view
               │
               ├─ [분석 없음] → "분석 실행" 버튼
               └─ [분석 있음] → PainPoint 카드 목록 표시
                                  └─ 검증 상태 업데이트 가능

  POST /ai/departments/<id>/analyze/  ← run_analysis view
       │
       ├─ gather_meeting_data(department, user, months=6)
       │    └─ action_type='customer_meeting' 히스토리만
       │
       ├─ gather_quote_delivery_data(department, user)
       │    └─ Quote, QuoteItem, DeliveryItem, History(delivery_schedule)
       │
       └─ analyze_department(analysis, department, user)
            └─ OpenAI API 호출 (GPT 모델)
                 └─ SYSTEM_PROMPT + 미팅 데이터 + 견적/납품 데이터
                      └─ JSON 응답 파싱
                           └─ AIDepartmentAnalysis + PainPointCard 저장
```

**AIFollowUpAnalysis** 모델도 존재하지만 현재 뷰에서 어떻게 사용되는지는 별도 뷰 확인 필요.

---

## 2. 현재 AI 분석에 전달되는 데이터

### 미팅 데이터 (`gather_meeting_data`)

| 필드                           | 포함 여부 | 비고                    |
| ------------------------------ | --------- | ----------------------- |
| meeting_date / created_at      | ✅        | 날짜                    |
| customer_name (followup)       | ✅        | 고객명                  |
| meeting_situation              | ✅        | 상황                    |
| meeting_researcher_quote       | ✅        | 연구원 발언             |
| meeting_confirmed_facts        | ✅        | 확인된 사실             |
| meeting_obstacles              | ✅        | 장애물                  |
| meeting_next_action            | ✅        | 다음 액션               |
| content (fallback)             | ✅        | 일반 내용               |
| next_action / next_action_date | ❌        | 미포함                  |
| pipeline_stage (followup)      | ❌        | 미포함                  |
| 선결제 데이터                  | ❌        | 미포함 (아래 섹션 참고) |

### 견적/납품 데이터 (`gather_quote_delivery_data`)

| 필드                                    | 포함 여부 | 비고   |
| --------------------------------------- | --------- | ------ |
| quote_number, quote_date                | ✅        |        |
| quote stage, total_amount               | ✅        |        |
| converted_to_delivery                   | ✅        |        |
| QuoteItem (product_code, qty, price)    | ✅        |        |
| delivery_date, delivery_amount          | ✅        |        |
| DeliveryItem (product_code, qty, price) | ✅        |        |
| 전환율, 평균 납품 주기                  | ✅        | 계산됨 |
| 제품별 집계                             | ✅        | 계산됨 |
| 선결제 잔액/사용 내역                   | ❌        | 미포함 |

---

## 3. 선결제(Prepayment) 데이터 현황

### 모델 위치

- `reporting/models.py` — `Prepayment`, `PrepaymentUsage` 클래스

### Prepayment 주요 필드

| 필드           | 타입         | 설명                      |
| -------------- | ------------ | ------------------------- |
| customer       | FK(FollowUp) | 거래처/고객 연결          |
| company        | FK(Company)  | 업체/학교                 |
| amount         | Decimal      | 선결제 원금               |
| balance        | Decimal      | 현재 잔액                 |
| payment_date   | Date         | 입금일                    |
| payment_method | CharField    | 현금/계좌이체/카드        |
| payer_name     | CharField    | 입금자명                  |
| status         | CharField    | active/depleted/cancelled |

### PrepaymentUsage 주요 필드

| 필드              | 타입             | 설명           |
| ----------------- | ---------------- | -------------- |
| prepayment        | FK(Prepayment)   |                |
| schedule          | FK(Schedule)     | 납품 일정 연결 |
| schedule_item     | FK(DeliveryItem) | 납품 품목      |
| product_name      | CharField        | 품목명         |
| quantity          | Integer          |                |
| amount            | Decimal          | 차감 금액      |
| remaining_balance | Decimal          | 사용 후 잔액   |

### Schedule 연결 필드 (선결제 관련)

- `Schedule.use_prepayment` (BooleanField) — 선결제 차감 여부
- `Schedule.prepayment` (FK → Prepayment) — 사용한 선결제
- `Schedule.prepayment_amount` (Decimal) — 차감 금액

---

## 4. 선결제 데이터의 AI 컨텍스트 추가 방안

### 왜 필요한가

- 선결제 보유 거래처는 재구매 의향이 높은 신호 (trust 지표)
- 잔액 고착 상태 (balance > 0 but no recent usage)는 영업 후속 액션 필요 신호
- 납품→선결제 차감 패턴은 구매 주기 분석에 유용

### 추가 방법: `gather_quote_delivery_data` 확장

```python
def gather_prepayment_data(department, user):
    from reporting.models import Prepayment, PrepaymentUsage

    followups = FollowUp.objects.filter(user=user, department=department)

    prepayments = Prepayment.objects.filter(
        customer__in=followups
    ).prefetch_related('usages').order_by('-payment_date')

    result = []
    for p in prepayments:
        usages = []
        for u in p.usages.all():
            usages.append({
                'product': u.product_name,
                'amount': int(u.amount),
                'remaining_after': int(u.remaining_balance),
                'used_at': u.used_at.strftime('%Y-%m-%d'),
            })
        result.append({
            'customer': p.customer.customer_name,
            'amount': int(p.amount),
            'balance': int(p.balance),
            'payment_date': p.payment_date.strftime('%Y-%m-%d'),
            'status': p.status,
            'usages': usages,
        })

    # 요약
    total_prepayment = sum(p['amount'] for p in result)
    total_remaining = sum(p['balance'] for p in result if p['status'] == 'active')
    stalled = [p for p in result if p['status'] == 'active' and p['balance'] > 0 and not p['usages']]

    return {
        'prepayments': result,
        'summary': {
            'total_prepayment_amount': total_prepayment,
            'total_remaining_balance': total_remaining,
            'stalled_count': len(stalled),
            'stalled_customers': [p['customer'] for p in stalled],
        }
    }
```

### 프롬프트 추가 섹션

```
[선결제 현황]
- 활성 선결제 거래처 수: N
- 총 잔액: ₩X,XXX,000
- 잔액 고착 거래처: [고객명1, 고객명2]
- 상세: (각 거래처별 원금, 잔액, 사용 내역)
```

### DB 변경 필요 여부

❌ 없음 — 기존 `Prepayment`, `PrepaymentUsage` 모델 활용

---

## 5. 권장 AI 분석 기능 개선

### 5.1 현재 분석 범위 제한 사항

- `action_type='customer_meeting'`인 History만 수집 → 전화상담, 이메일, 방문 기록 제외
- `user` 기준으로만 필터 → 팀 전체 분석 불가
- 단일 부서(Department) 단위만 지원 → 거래처(FollowUp) 전체 분석 뷰 없음

### 5.2 권장 기능 추가 목록

| 기능                                      | 우선순위 | DB 변경 |
| ----------------------------------------- | -------- | ------- |
| 활동 유형 필터 확장 (meeting → all types) | 높음     | ❌      |
| 선결제 데이터를 AI 컨텍스트에 포함        | 높음     | ❌      |
| 거래처(FollowUp) 단위 AI 분석 뷰          | 중간     | ❌      |
| next_action / next_action_date 포함       | 중간     | ❌      |
| pipeline_stage 변화 이력 포함             | 낮음     | ❌      |
| 팀 전체 종합 분석 (admin/manager)         | 낮음     | ❌      |
| 재분석 시 이전 분석과 diff 표시           | 낮음     | ❌      |

---

## 6. 캘린더 모달 및 메모 모달 근본 원인 분석

### 6.1 현재 모달 구조

`schedule_calendar.html`에 존재하는 모달:

1. `#scheduleDetailModal` — 일정 상세 (메인 모달, line ~6639)
2. `#customerHistoriesModal` — 고객 활동 기록 (JS로 동적 생성, line ~7053)
3. `#deptMemoOffcanvas` — 부서 메모 (Bootstrap Offcanvas, line ~7712)

현재 CSS 상태:

```css
/* line 9-14 */
.modal-backdrop {
  z-index: 1040 !important;
  pointer-events: none !important; /* ← 위험 패턴 */
  opacity: 0.5 !important;
  background-color: rgba(0, 0, 0, 0.5) !important;
}
.modal {
  z-index: 1055 !important;
}
.modal-dialog {
  z-index: 1056 !important;
}
.modal-content {
  z-index: 1057 !important;
}
```

### 6.2 근본 원인 분석

**문제 유형: 중첩 모달 (Nested Modal)**

`scheduleDetailModal`이 열린 상태에서 사용자가 고객명을 클릭하면
`customerHistoriesModal`이 `document.body`에 동적 삽입되어 두 번째 모달이 열림.

Bootstrap 5는 **공식적으로 중첩 모달을 지원하지 않는다**.
두 번째 모달이 열릴 때:

- 두 번째 `.modal-backdrop`이 생성됨
- 첫 번째 모달의 backdrop과 z-index 충돌
- 포커스 트랩(focus trap)이 두 번째 모달에 걸려 첫 번째 모달이 응답 불가

**현재 임시 해결책**: `pointer-events: none !important`를 backdrop에 적용

- 이는 backdrop을 클릭해도 닫히지 않게 만드는 부작용
- 모달 닫기 트리거 오작동 가능성 있음
- Bootstrap 업그레이드 시 깨질 수 있음

**추가 원인**: `customerHistoriesModal`이 `show()` 후 `hidden.bs.modal`에서 `this.remove()` 처리하지만,
첫 번째 모달의 backdrop이 남아있는 경우 화면이 어두운 상태로 고착되는 버그 가능성.

### 6.3 권장 구조적 해결책

**Option A (권장): `customerHistoriesModal`을 `scheduleDetailModal` 내부 인라인 패널로 전환**

```html
<!-- scheduleDetailModal 내부에 슬라이딩 패널 추가 -->
<div id="scheduleDetailModal" ...>
  <div class="modal-dialog modal-xl">
    <div class="modal-content d-flex flex-row">
      <!-- 기존 일정 상세 (좌측) -->
      <div id="sched-main-panel" class="flex-grow-1">...</div>
      <!-- 고객 활동 기록 (우측 슬라이드 패널, 기본 hidden) -->
      <div
        id="customer-history-panel"
        class="border-start"
        style="width:380px; display:none;"
      >
        <div class="p-3">
          <h6>고객 활동 기록</h6>
          <div id="customer-history-content"></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

- Bootstrap 모달 1개만 사용 → backdrop 충돌 없음
- 두 번째 모달 없음 → focus trap 문제 없음

**Option B: Offcanvas 전환 (부서 메모와 동일 패턴)**

이미 `#deptMemoOffcanvas`가 Offcanvas 패턴으로 구현됨.
`customerHistoriesModal`도 동일하게 Offcanvas(`offcanvas-end`)로 전환.

```html
<div
  class="offcanvas offcanvas-end"
  id="customerHistoryOffcanvas"
  style="width:420px"
>
  <div class="offcanvas-header">...</div>
  <div class="offcanvas-body" id="customerHistoryContent"></div>
</div>
```

- Offcanvas는 backdrop을 별도 관리 → 모달 backdrop과 충돌 없음

**Option C: 전역 `modal-backdrop { display:none }` — 사용 금지**

이 방식은 Bootstrap의 UX 의도(배경 클릭으로 닫기, 포커스 강조)를 완전히 파괴함.
응급 패치로는 사용 가능하나 영구 해결책이 아님.

---

## 7. 대시보드 영업노트 모달 근본 원인 분석

### 7.1 현재 구조

`dashboard.html` — `#dashboardNoteModal`

- 단일 모달, 중첩 없음
- Step 1 (일정 선택) → Step 2 (노트 작성) 전환 방식
- AJAX POST → `history_create_from_schedule`
- 저장 성공 시 `location.reload()`

### 7.2 알려진 잠재 문제점

1. **일정 목록 정적 렌더링**: 페이지 로드 시점의 일정만 표시
   - 새 일정을 추가해도 대시보드를 새로고침해야 목록 갱신
   - `today_schedules`, `upcoming_schedules_dash` 컨텍스트 변수 기반

2. **Step 전환 시 DOM 조작**: `display:none / block` 방식
   - 미세한 레이아웃 점프 가능
   - `modal-body` 높이 변화로 스크롤바 깜빡임 가능

3. **성공 시 `location.reload()`**: 대시보드 전체 새로고침
   - 느린 연결 환경에서 UX 나쁨
   - 더 나은 방법: 모달 닫고 해당 카드만 부분 업데이트

4. **중첩 모달 없음** → backdrop 충돌 문제 없음
   - 캘린더 페이지와 달리 대시보드 모달은 구조적으로 안전

### 7.3 개선 포인트 (선택적)

- 일정 없을 때 "일정 추가" 링크만 표시 → 현재 올바르게 구현됨
- Step 2 폼에 `meeting_situation`, `meeting_obstacles` 등 미팅 필드 추가 고려
  (현재는 단순 content + next_action + next_action_date만)

---

## 8. Bootstrap 모달 이슈 원인 분류

| 원인                     | 해당 여부      | 상세                                                            |
| ------------------------ | -------------- | --------------------------------------------------------------- |
| 중첩 모달 (Nested Modal) | ✅ **주 원인** | `scheduleDetailModal` 내에서 `customerHistoriesModal` 동적 생성 |
| Backdrop 충돌            | ✅             | 두 번째 모달 열릴 때 두 번째 backdrop 생성                      |
| z-index 충돌             | ✅ (파생)      | CSS `!important` 오버라이드로 임시 우회 중                      |
| 중복 ID                  | ❌             | `customerHistoriesModal`은 열기 전 기존 제거 후 새로 삽입       |
| 포커스 트랩 (Focus Trap) | ✅             | 두 번째 모달이 포커스 독점 시 첫 번째 모달 키보드 응답 불가     |
| 이벤트 핸들러 누적       | 낮음           | `once:true` 옵션으로 부분 방어 중                               |
| `data-bs-toggle` 충돌    | ❌             | 캘린더 모달은 JS로만 제어, 속성 충돌 없음                       |

**결론**: 구조적 문제(중첩 모달). CSS z-index 오버라이드는 증상 억제일 뿐.  
Option A(인라인 패널) 또는 Option B(Offcanvas) 구조 교체가 필요.

---

## 9. 파이프라인 보드 검색 구현 계획

### 9.1 현재 상태

- `reporting/templates/reporting/funnel/pipeline.html` — Kanban 보드
- 검색/필터 기능 **없음**
- 드래그앤드롭 단계 이동만 존재
- URL: `/reporting/pipeline/` (뷰 확인 필요)

### 9.2 구현 계획

**프론트엔드 실시간 필터 (JS, DB 쿼리 없음)**

```html
<!-- 파이프라인 보드 상단에 추가 -->
<div class="d-flex gap-2 px-3 mb-2">
  <input
    type="text"
    id="pipelineSearch"
    class="form-control form-control-sm"
    placeholder="고객명, 업체명, 부서명 검색..."
    style="max-width:280px;"
  />
  <select
    id="pipelineGradeFilter"
    class="form-select form-select-sm"
    style="max-width:120px;"
  >
    <option value="">전체 등급</option>
    <option value="A">A등급</option>
    <option value="B">B등급</option>
    <option value="C">C등급</option>
  </select>
</div>
```

```javascript
function applyPipelineFilter() {
  const q = document.getElementById("pipelineSearch").value.toLowerCase();
  const grade = document.getElementById("pipelineGradeFilter").value;

  document.querySelectorAll(".kanban-card").forEach((card) => {
    const text = card.textContent.toLowerCase();
    const cardGrade = card.dataset.grade || "";
    const show = (!q || text.includes(q)) && (!grade || cardGrade === grade);
    card.style.display = show ? "" : "none";
  });

  // 빈 컬럼 empty 메시지 업데이트
  document.querySelectorAll(".kanban-col").forEach((col) => {
    const stage = col.dataset.stage;
    const visibleCards = col.querySelectorAll(
      '.kanban-card:not([style*="display: none"])',
    );
    const emptyMsg = col.querySelector(`#empty-${stage}`);
    if (emptyMsg)
      emptyMsg.style.display = visibleCards.length === 0 ? "" : "none";
  });
}

["input", "change"].forEach((evt) => {
  document
    .getElementById("pipelineSearch")
    .addEventListener(evt, applyPipelineFilter);
  document
    .getElementById("pipelineGradeFilter")
    .addEventListener(evt, applyPipelineFilter);
});
```

**카드에 data 속성 추가 필요** (뷰에서 렌더링):

```html
<div
  class="kanban-card"
  data-grade="{{ card.grade }}"
  data-customer="{{ card.customer }}"
  ...
></div>
```

### 9.3 DB 변경 필요 여부

❌ 없음 — 프론트엔드 필터만 추가

---

## 10. 주간보고 UX 개선 계획

### 10.1 현재 상태

- `weekly_report/form.html` — 자유 텍스트 textarea 3개
  1. `activity_notes` — 영업 활동 내용
  2. `quote_delivery_notes` — 견적/납품 내용
  3. `other_notes` — 기타
- "일정 불러오기" AJAX 버튼 있음 → `weekly_report_load_schedules` API
- 결과를 textarea에 텍스트로 삽입하는 것으로 추정

### 10.2 개선 포인트

| 문제점                                  | 개선 방향                                   |
| --------------------------------------- | ------------------------------------------- |
| 자유 textarea → 검토자가 읽기 어려움    | 구조화된 활동 목록 UI (날짜별 accordion)    |
| "일정 불러오기" 결과를 수동 편집해야 함 | 불러온 일정을 체크박스로 선택 후 자동 삽입  |
| 목록 페이지에서 미리보기 없음           | 목록에 활동 건수 + 첫 줄 미리보기 표시      |
| 관리자 검토/승인 UI 없음                | 관리자 코멘트 필드 + 읽음 확인 기능         |
| 주간보고 ↔ History 연결 없음            | 주간보고 내 활동 항목을 History로 연결 표시 |
| 주 기간 자동 계산 없음                  | 현재 주 월~금 자동 채우기 버튼              |

### 10.3 즉시 적용 가능한 개선 (DB 변경 없음)

1. **주 자동 계산** — JS로 오늘 날짜 기준 이번 주 월/금 자동 입력
2. **일정 불러오기 UX** — 텍스트 삽입 대신 테이블로 미리보기 후 확인
3. **목록 페이지 개선** — 기간 + 활동 건수 + 상태 배지

### 10.4 DB 변경이 필요한 개선

| 기능          | 필요 변경                                           |
| ------------- | --------------------------------------------------- |
| 관리자 검토   | `WeeklyReport.reviewed_by`, `reviewed_at` 필드 추가 |
| 관리자 코멘트 | `WeeklyReport.manager_comment` 필드 추가            |

`WeeklyReport` 모델 필드 먼저 확인 후 결정 필요.

---

## 11. CSV/XLSX 보고서 개선 계획

### 11.1 현재 상태

- `analytics_activity_csv_export` — 영업사원별 활동 CSV
- `analytics_pipeline_csv_export` — 파이프라인 단계별 CSV
- 모두 UTF-8 BOM CSV (Excel 호환)
- XLSX 포맷 없음

### 11.2 개선 포인트

| 항목              | 현재                                         | 개선안                            |
| ----------------- | -------------------------------------------- | --------------------------------- |
| 파일 포맷         | CSV only                                     | XLSX 옵션 추가 (`openpyxl`)       |
| 활동 CSV 컬럼     | 5개 (영업사원, 노트, 거래처, 지연, 최근활동) | 파이프라인 단계별 건수 컬럼 추가  |
| 파이프라인 CSV    | 단계+건수만                                  | 금액(견적 총액) 컬럼 추가         |
| 거래처별 상세 CSV | 없음                                         | 거래처별 활동 이력 상세 CSV 추가  |
| 다운로드 버튼 UX  | 별도 링크                                    | 날짜 필터 파라미터 포함 여부 확인 |

### 11.3 XLSX 추가 방법

```python
# requirements.txt에 openpyxl 추가 여부 확인 필요
# pip show openpyxl

import openpyxl
from django.http import HttpResponse

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "영업사원별 활동"
ws.append(['영업사원', '영업노트', '활성 거래처', '지연 후속조치', '최근 활동일'])
# ... 데이터 추가 ...

response = HttpResponse(
    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
response['Content-Disposition'] = 'attachment; filename="activity_report.xlsx"'
wb.save(response)
return response
```

### 11.4 DB 변경 필요 여부

❌ 없음 — 기존 모델 활용

---

## 12. 보안 및 권한 위험 사항

### 12.1 Known Risks (Phase 6 QA에서 식별)

| 위험                   | 설명                                                                                         | 심각도 |
| ---------------------- | -------------------------------------------------------------------------------------------- | ------ |
| manager.company = None | 회사 미설정 manager가 전체 데이터 조회 가능                                                  | 중간   |
| can_use_ai 권한        | `UserProfile.can_use_ai` 미설정 사용자 AI 접근 불가 처리됨 → OK                              | 낮음   |
| AI 분석 결과 소유자    | `AIDepartmentAnalysis.unique_together = ['user', 'department']` → 타 사용자 분석 결과 격리됨 | 낮음   |
| CSV 내보내기 컬럼      | 현재 이름/카운트만 포함, 개인정보 최소화 → OK                                                | 낮음   |

### 12.2 추가 검토 필요 사항

- `customerHistoriesModal`의 `/reporting/api/followup/<id>/histories/` 엔드포인트
  → followup_id가 로그인 사용자 소속인지 검증하는지 확인 필요
- AI 분석의 `gather_meeting_data`: `user` 파라미터로 격리되지만
  department 접근 권한 검증이 `has_followups` 체크에만 의존 — OK

---

## 13. 변경 가능성이 높은 파일

| 파일                                                     | 변경 이유                                     |
| -------------------------------------------------------- | --------------------------------------------- |
| `reporting/templates/reporting/schedule_calendar.html`   | 캘린더 모달 구조 교체 (중첩→인라인/Offcanvas) |
| `reporting/templates/reporting/funnel/pipeline.html`     | 파이프라인 검색 필터 추가                     |
| `reporting/templates/reporting/weekly_report/form.html`  | 주간보고 UX 개선                              |
| `reporting/templates/reporting/weekly_report/list.html`  | 목록 미리보기 개선                            |
| `ai_chat/services.py`                                    | 선결제 데이터 수집 함수 추가, 프롬프트 확장   |
| `ai_chat/views.py`                                       | 거래처 단위 AI 분석 뷰 추가 (선택적)          |
| `reporting/views.py`                                     | XLSX 내보내기, 파이프라인 뷰 필터 추가        |
| `reporting/templates/reporting/analytics_dashboard.html` | CSV 다운로드 버튼 XLSX 옵션 추가              |

---

## 14. DB 변경 필요 여부 요약

| 작업                    | DB 변경 필요                                  |
| ----------------------- | --------------------------------------------- |
| 캘린더 모달 구조 교체   | ❌                                            |
| 파이프라인 보드 검색    | ❌                                            |
| AI 선결제 컨텍스트 추가 | ❌                                            |
| AI 활동 유형 확장       | ❌                                            |
| 주간보고 자동 주 계산   | ❌                                            |
| 주간보고 관리자 검토    | ✅ (`WeeklyReport` 모델 필드 추가)            |
| CSV → XLSX 추가         | ❌ (`openpyxl` 패키지 추가 필요)              |
| 거래처 단위 AI 분석     | ❌ (기존 `AIFollowUpAnalysis` 모델 활용 가능) |

---

## 15. 권장 구현 순서

### Priority 1 — 안정성 (버그 수정 성격)

1. **캘린더 모달 구조 교체**
   - `scheduleDetailModal` 내부에 고객 활동 인라인 패널 추가
   - `customerHistoriesModal` 동적 생성 제거
   - `pointer-events: none` CSS 임시 픽스 제거
   - 예상 소요: 중간 (템플릿만 변경, JS 일부 수정)

### Priority 2 — 실사용 개선 (즉시 가치)

2. **파이프라인 보드 검색 필터**
   - 프론트엔드 JS 필터 (DB 변경 없음)
   - 예상 소요: 낮음 (JS + HTML만)

3. **주간보고 UX 개선**
   - 주 자동 계산 JS
   - 일정 불러오기 UX 개선 (테이블 미리보기)
   - 예상 소요: 낮음~중간

### Priority 3 — AI 개선

4. **선결제 데이터 AI 컨텍스트 추가**
   - `gather_prepayment_data` 함수 추가
   - `analyze_department` 함수 확장
   - 프롬프트 섹션 추가
   - DB 변경 없음

5. **AI 활동 유형 필터 확장**
   - `gather_meeting_data`에서 `customer_meeting` 외 타입 포함 옵션

### Priority 4 — 보고서 개선

6. **XLSX 내보내기 추가**
   - `openpyxl` 패키지 확인 후 추가
   - 기존 CSV 뷰 옆에 XLSX 뷰 추가

7. **주간보고 관리자 검토 기능**
   - DB 변경 포함 → 마이그레이션 필요
   - 별도 Phase로 분리 권장

---

## 16. 검증 명령

각 작업 완료 후 실행:

```bash
# Django 시스템 검사
python manage.py check

# 모델 변경 감지 (DB 변경 없는 작업 후)
python manage.py makemigrations --check --dry-run

# 마이그레이션 (DB 변경 있는 작업 후)
python manage.py makemigrations
python manage.py migrate

# 기존 테스트
python manage.py test

# 정적 파일
python manage.py collectstatic --noinput

# URL 스모크 테스트 (로컬 서버 기동 후)
# Invoke-WebRequest http://localhost:8020/reporting/pipeline/ -MaximumRedirection 0
# Invoke-WebRequest http://localhost:8020/reporting/analytics/ -MaximumRedirection 0

# 모달 구조 교체 후 브라우저 테스트 체크리스트
# 1. 캘린더 페이지 로드 → 일정 클릭 → scheduleDetailModal 정상 표시
# 2. scheduleDetailModal 내 고객명 클릭 → 인라인 패널 or Offcanvas 표시 (별도 모달 없음)
# 3. 두 번째 패널 닫기 → 첫 번째 모달 정상 유지
# 4. ESC 키 → 모달만 닫힘, backdrop 잔재 없음
# 5. 모달 외부 클릭 → 정상 닫힘
```

---

## 17. 참고: 현재 Bootstrap 버전

`base.html`에서 Bootstrap 5.3.0 + FontAwesome 6.4.0 확인됨.

Bootstrap 5.3은 중첩 모달 미지원이 공식 문서에 명시됨.  
참고: https://getbootstrap.com/docs/5.3/components/modal/#how-it-works

> "Nesting modals is not supported."

이 제약은 Phase 6.5의 캘린더 모달 구조 교체의 핵심 근거임.
