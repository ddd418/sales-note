# PHASE 8.5 PLAN — 긴급 실사용 버그 수정 및 세금계산서/VAT 기능 설계

> **목표**: 실사용 중 발견된 4개 버그를 수정하고, 세금계산서 발행 상태 관리 및 VAT 계산 모드 기능을 설계한다.
>
> **범위 제한**:
>
> - 명시된 버그 수정 외 비즈니스 기능 추가 금지
> - 페이지 재설계 금지
> - Phase 9 보안 강화 작업 대기
> - 기존 64개 테스트 전부 통과 유지 필수
> - 마이그레이션 필요 여부 사전 명시

---

## 1. 버그 분석: 제품 규격(specification) 저장 안 됨

### 근본 원인

`reporting/views.py`에 위치한 `product_create()` 및 `product_edit()` 뷰에서 `specification` 필드가 누락된다.

#### product_create() — 일반 폼 제출 경로 (비-AJAX)

라인 ~11820: `Product()` 인스턴스 생성 시 `specification` 및 `unit`을 처리하는 코드가 없다.

```python
# 현재 (버그):
product = Product(
    product_code=product_code,
    standard_price=...,
    is_active=...,
    created_by=...,
)
if request.POST.get('description'):
    product.description = ...
# specification, unit 저장 코드 없음 ← 버그
```

AJAX 경로(라인 ~11750)는 `specification`과 `unit`을 올바르게 저장한다. 일반 폼 제출 경로만 누락되어 있다.

#### product_edit() — 수정 시

라인 ~11990: POST 처리 블록 전체에 `specification`과 `unit` 저장 코드가 없다.

```python
# 현재 (버그):
product.product_code = ...
product.standard_price = ...
product.is_active = ...
product.description = request.POST.get('description', '')
# specification, unit 저장 코드 없음 ← 버그
product.save()
```

### 수정 방법

**파일**: `reporting/views.py`

1. `product_create()` 비-AJAX 경로: `description` 처리 이후에 추가:

   ```python
   product.specification = request.POST.get('specification', '')
   product.unit = request.POST.get('unit', 'EA') or 'EA'
   ```

2. `product_edit()` POST 처리: `description` 처리 이후에 추가:
   ```python
   product.specification = request.POST.get('specification', '')
   product.unit = request.POST.get('unit', 'EA') or 'EA'
   ```

### 마이그레이션 필요 여부

불필요. 모델 변경 없음. `specification`과 `unit` 필드는 이미 `Product` 모델에 존재.

---

## 2. 버그 분석: 대시보드 이번 주 일정 미로드

### 근본 원인

`dashboard_view()`에서 `upcoming_schedules_dash`는 `status='scheduled'`이고 `visit_date__gt=today`인 항목만 반환한다. 오늘 이후 이번 주 일정이 없거나 모두 `completed`/`cancelled`이면 섹션이 아예 숨겨진다.

```python
# 현재 (라인 ~2278):
week_later = today + timedelta(days=7)
upcoming_schedules_dash = schedules.filter(
    visit_date__gt=today,          # 오늘 제외 (tomorrow+)
    visit_date__lte=week_later,    # 7일 롤링, 이번 주 Mon-Sun 아님
    status='scheduled'             # 완료된 일정 제외
)
```

**두 가지 문제**:

1. **날짜 범위**: `visit_date__gt=today`는 오늘 이후 7일(롤링). "이번 주(Mon-Sun)" 개념과 다름. 수요일 기준이면 이번 주 월~화 일정은 포함되지 않음.

2. **상태 필터**: `status='scheduled'`만 포함. 완료된(`completed`) 이번 주 일정은 표시 안 됨. `today_schedules`는 `status__in=['scheduled', 'completed']`를 사용하는데 불일치.

3. **템플릿 조건**: `{% if upcoming_schedules_dash or upcoming_personal_schedules_dash %}` — 둘 다 비어있으면 카드 전체가 숨겨짐.

### 수정 방법

**파일**: `reporting/views.py`, `reporting/templates/reporting/dashboard.html`

1. "이번 주" 범위를 이번 주 월요일~일요일로 변경:

   ```python
   from datetime import timedelta
   week_start_date = today - timedelta(days=today.weekday())  # 이번 주 월요일
   week_end_date = week_start_date + timedelta(days=6)        # 이번 주 일요일

   upcoming_schedules_dash = schedules.filter(
       visit_date__gte=week_start_date,
       visit_date__lte=week_end_date,
       status__in=['scheduled', 'completed'],  # 완료 포함
   ).exclude(visit_date=today)  # 오늘은 today_schedules에서 표시
   ```

2. 또는 더 직관적으로 — 오늘 포함 이번 주 전체를 하나의 카드로 병합:
   - `today_schedules`와 `upcoming_schedules_dash`를 합쳐 "이번 주 일정" 하나로 표시

3. 템플릿: 빈 경우에도 카드 표시(내용 없음 메시지 표시)로 변경 권장.

### 마이그레이션 필요 여부

불필요. 뷰 로직 및 템플릿 변경만 필요.

---

## 3. 버그 분석: 대시보드 일정 수 0 표시

### 근본 원인

`schedule_count`는 `status='scheduled'`인 항목만 집계한다. 오늘 완료된(`completed`) 일정들은 `today_schedules` 섹션에는 보이지만 카운트에는 포함되지 않는다.

```python
# 현재:
schedule_count = Schedule.objects.filter(user=target_user, status='scheduled').count()
```

- 사용자에게 일정이 표시되면서(완료 포함) 카운트는 0으로 보이는 불일치 발생.
- 빠른 통계 카드가 "처리해야 할 예정된 일정"을 의미하지만 레이블이 불명확.

### 수정 방법

**파일**: `reporting/views.py`, `reporting/templates/reporting/dashboard.html`

옵션 A (권장): `schedule_count`를 이번 주 전체 일정(완료 포함)으로 변경, 레이블도 "이번 주 일정"으로 수정:

```python
# 이번 주 전체 일정 수 (상태 무관)
week_start_date = today - timedelta(days=today.weekday())
week_end_date = week_start_date + timedelta(days=6)
schedule_count = schedules.filter(
    visit_date__gte=week_start_date,
    visit_date__lte=week_end_date,
).count()
```

옵션 B: 두 가지 카운트 분리:

- `schedule_count`: 예정된 미완료 일정 수 (현재 방식, 레이블 명확화)
- `this_week_schedule_count`: 이번 주 전체 일정 수 (신규)

템플릿에서 카운트 레이블을 "예정된 일정" → "이번 주 일정"으로 명확히 표시.

### 마이그레이션 필요 여부

불필요.

---

## 4. 버그 분석: 주간보고 일정/견적 가져오기 효과 없음

### 근본 원인

`reporting/templates/reporting/weekly_report/form.html`의 `insertSelected()` JavaScript 함수에서 잘못된 element ID를 참조한다.

```javascript
// 현재 (버그):
function insertSelected(category) {
  const checked = document.querySelectorAll(
    `.schedule-check[data-category="${category}"]:checked`,
  );
  if (checked.length === 0) return;

  const lines = Array.from(checked).map((cb) => buildInsertText(cb));
  const insertText = lines.join("\n");

  // 버그: 이 ID는 존재하지 않음!
  const targetId =
    category === "quote_delivery" ? "quoteDeliveryNotes" : "activityNotes";
  const ta = document.getElementById(targetId);
  if (!ta) return; // ← 항상 여기서 종료됨

  ta.value = cur ? cur + "\n" + insertText : insertText; // 도달 불가
}
```

실제 폼 HTML에 존재하는 ID:

- `activityNotesEditor` — Quill 에디터 컨테이너 div
- `activityNotesInput` — 폼 제출용 hidden input
- `quoteDeliveryNotesEditor` — Quill 에디터 컨테이너 div
- `quoteDeliveryNotesInput` — 폼 제출용 hidden input

`activityNotes`나 `quoteDeliveryNotes` ID는 존재하지 않으므로 `document.getElementById()`가 `null`을 반환하고, `if (!ta) return;`으로 즉시 함수가 종료된다.

### 수정 방법

**파일**: `reporting/templates/reporting/weekly_report/form.html`

`insertSelected()` 함수를 Quill 인스턴스(`window.quillActivity`, `window.quillQuoteDelivery`)를 사용하도록 변경:

```javascript
function insertSelected(category) {
  const checked = document.querySelectorAll(
    `.schedule-check[data-category="${category}"]:checked`,
  );
  if (checked.length === 0) return;

  const lines = Array.from(checked).map((cb) => buildInsertText(cb));
  const insertText = lines.join("\n");

  // Quill 인스턴스 직접 사용
  const quill =
    category === "quote_delivery"
      ? window.quillQuoteDelivery
      : window.quillActivity;
  if (!quill) return;

  const currentText = quill.getText().trim();
  const insertHtml = (currentText ? "\n" : "") + insertText;
  // 플레인텍스트를 HTML <p> 줄로 변환하여 삽입
  const len = quill.getLength();
  quill.setSelection(len - 1);
  if (currentText) {
    quill.insertText(len - 1, "\n" + insertText, "user");
  } else {
    quill.clipboard.dangerouslyPasteHTML(plainToHtml(insertText), "user");
  }

  // 체크박스 해제
  checked.forEach((cb) => {
    cb.checked = false;
  });
  updateInsertBtns();
}
```

`plainToHtml` 헬퍼가 AI 초안 생성 코드에 이미 존재하므로 재사용 가능.

### 마이그레이션 필요 여부

불필요. JavaScript 전용 수정.

---

## 5. 버그 수정 권장 구현 순서

| 우선순위 | 버그                         | 영향 범위                | 난이도 | 예상 소요 |
| -------- | ---------------------------- | ------------------------ | ------ | --------- |
| 1        | 주간보고 일정 가져오기       | JavaScript 1개 함수 수정 | 쉬움   | 10분      |
| 2        | 제품 규격 저장               | Python 뷰 2개 수정       | 쉬움   | 10분      |
| 3        | 대시보드 일정 수 0           | Python 뷰 + 템플릿 수정  | 보통   | 20분      |
| 4        | 대시보드 이번 주 일정 미로드 | Python 뷰 + 템플릿 수정  | 보통   | 20분      |

버그 1, 2는 단순 코드 누락 수정이므로 먼저 처리. 버그 3, 4는 로직 변경이 필요하므로 연계하여 처리.

---

## 6. 세금계산서 발행 상태 관리 기능 설계

### 6.1 현재 상태

- `History.tax_invoice_issued`: `BooleanField` — 단순 발행/미발행 (발행일, 요청자 없음)
- `DeliveryItem.tax_invoice_issued`: `BooleanField` — 품목별 발행/미발행
- `schedule_delivery_tax_invoice_api.py`: `DeliveryItem` 일괄 토글 API (권한: `can_modify_user_data`)
- 감사 이력(audit trail) 없음
- 요청/승인 워크플로우 없음

### 6.2 제안 데이터 모델

#### 옵션 A (권장): `TaxInvoiceRequest` 신규 모델

요청 → 처리 워크플로우를 별도 모델로 분리. 기존 `DeliveryItem.tax_invoice_issued`는 최종 발행 여부 플래그로 유지.

```python
class TaxInvoiceRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', '요청됨'),      # 실무자가 요청
        ('issued', '발행됨'),         # 관리자가 발행 처리
        ('cancelled', '취소됨'),      # 요청 취소 또는 거절
    ]

    # 연결 대상 (납품 일정 기준)
    schedule = models.ForeignKey(
        'Schedule', on_delete=models.CASCADE,
        related_name='tax_invoice_requests',
        verbose_name="관련 납품 일정"
    )
    followup = models.ForeignKey(
        'FollowUp', on_delete=models.CASCADE,
        related_name='tax_invoice_requests',
        verbose_name="관련 거래처"
    )

    # 상태
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='requested', verbose_name="상태"
    )

    # 금액 스냅샷 (발행 시점 기록)
    supply_amount = models.DecimalField(
        max_digits=15, decimal_places=0,
        verbose_name="공급가액"
    )
    tax_amount = models.DecimalField(
        max_digits=15, decimal_places=0,
        verbose_name="부가세"
    )
    total_amount = models.DecimalField(
        max_digits=15, decimal_places=0,
        verbose_name="합계금액"
    )

    # 요청 정보
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='tax_invoice_requests_made',
        verbose_name="요청자"
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="요청일시")
    request_memo = models.TextField(blank=True, verbose_name="요청 메모")

    # 발행 정보
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tax_invoices_issued',
        verbose_name="발행 처리자"
    )
    issued_at = models.DateTimeField(null=True, blank=True, verbose_name="발행 처리일시")
    issue_memo = models.TextField(blank=True, verbose_name="발행 메모")

    # 취소 정보
    cancelled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tax_invoices_cancelled',
        verbose_name="취소 처리자"
    )
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="취소일시")
    cancel_reason = models.TextField(blank=True, verbose_name="취소 사유")

    class Meta:
        verbose_name = "세금계산서 요청"
        verbose_name_plural = "세금계산서 요청 목록"
        ordering = ['-requested_at']
```

#### 옵션 B (경량): `DeliveryItem`에 상태 필드 추가

기존 `DeliveryItem.tax_invoice_issued` BooleanField를 `tax_invoice_status` CharField로 교체.
단순하지만 이력 추적이 어렵고 `tax_invoice_issued`를 사용하는 기존 코드 전체 수정 필요.

**권장**: 옵션 A. 기존 코드 호환성 유지, 감사 이력 지원, 확장성 우수.

### 6.3 상태 값

| 상태   | 코드        | 설명                | 행위자                |
| ------ | ----------- | ------------------- | --------------------- |
| 요청됨 | `requested` | 실무자가 발행 요청  | 실무자(salesman)      |
| 발행됨 | `issued`    | 관리자가 발행 처리  | 관리자(admin/manager) |
| 취소됨 | `cancelled` | 요청 취소 또는 거절 | 요청자 또는 관리자    |

기존 `DeliveryItem.tax_invoice_issued = True`는 `issued` 상태에 대응.

### 6.4 권한 설계

| 액션      | salesman         | manager      | admin   |
| --------- | ---------------- | ------------ | ------- |
| 요청 생성 | 자신 데이터만 ✅ | 팀원 포함 ✅ | 전체 ✅ |
| 요청 취소 | 자신 요청만 ✅   | 팀원 포함 ✅ | 전체 ✅ |
| 발행 처리 | ❌               | ✅           | ✅      |
| 발행 취소 | ❌               | ✅           | ✅      |
| 조회      | 자신 데이터만 ✅ | 팀원 포함 ✅ | 전체 ✅ |

기존 `can_modify_user_data()` 및 `can_access_user_data()` 헬퍼 함수 재사용.

### 6.5 캘린더 모달 메모 사이드패널 UI 설계

현재 구조:

- 캘린더 클릭 시 일정 모달 열림
- `#deptMemoOffcanvas`: 부서 메모 패널 (Offcanvas)
- `#customerHistoryOffcanvas`: 고객 활동기록 패널 (Offcanvas)

**추가할 세금계산서 탭**:

`#customerHistoryOffcanvas` Offcanvas body에 Bootstrap nav-tabs 추가:

```
[활동기록] [납품 이력] [세금계산서]
```

세금계산서 탭 내용:

- 해당 거래처(FollowUp) 또는 부서의 납품 이력 목록
- 각 납품 건의 세금계산서 요청/발행 현재 상태 배지
- 요청 버튼 (실무자: `status='requested'`로 신규 생성)
- 발행/취소 버튼 (관리자: `status='issued'`/'cancelled'로 업데이트)

AJAX 엔드포인트 (신규):

- `GET /reporting/api/followup/<id>/tax-invoice-status/` — 거래처별 세금계산서 현황
- `POST /reporting/api/tax-invoice/request/<schedule_id>/` — 요청 생성
- `POST /reporting/api/tax-invoice/issue/<request_id>/` — 발행 처리
- `POST /reporting/api/tax-invoice/cancel/<request_id>/` — 취소

### 6.6 납품/문서 연계

- `TaxInvoiceRequest`는 `Schedule`(납품 일정)에 연결됨
- 납품 일정 상세(`schedule_detail.html`)에서 요청/발행 상태 표시
- 납품 품목(`DeliveryItem`) 목록에 세금계산서 상태 컬럼 추가 (기존 토글 버튼 개선)
- 거래명세서 생성 시 `TaxInvoiceRequest`가 없으면 생성 유도 안내 표시

### 6.7 감사/이력 고려사항

- `TaxInvoiceRequest` 모델 자체가 감사 이력 역할 수행
- `requested_at`, `issued_at`, `cancelled_at` + 각 담당자 FK 저장
- Django Admin에 `TaxInvoiceRequest` 등록 (읽기 전용 이력 조회)
- 삭제 금지: 취소(`cancelled`) 상태로 유지, 물리 삭제 불가

---

## 7. VAT 계산 모드 설계

### 7.1 현재 상태

`DeliveryItem.save()`에서 항상 10% 부가세를 강제 적용:

```python
# 현재 (models.py ~790):
self.total_price = subtotal * Decimal('1.1')  # 부가세 10% 추가
```

`Quote.save()`도 마찬가지:

```python
# 현재 (models.py ~915):
self.tax_amount = taxable_amount * Decimal('0.1')
self.total_amount = taxable_amount + self.tax_amount
```

`generate_document_pdf()` 뷰에서도 고정 10% 계산:

```python
# 현재 (views.py ~12455):
tax = subtotal * Decimal('0.1')
total = subtotal + tax
```

### 7.2 VAT 모드 정의

| 모드        | 코드           | 설명                                     | 계산 방식                                      |
| ----------- | -------------- | ---------------------------------------- | ---------------------------------------------- |
| 부가세 별도 | `vat_excluded` | 공급가액 기준 표시, 부가세 10% 별도 추가 | `total = subtotal × 1.1` (현재 방식)           |
| 부가세 포함 | `vat_included` | 입력 금액에 부가세 이미 포함             | `supply = total ÷ 1.1`, `tax = total - supply` |
| 부가세 없음 | `vat_none`     | 부가세 0원 (비과세, 수출 등)             | `total = subtotal`, `tax = 0`                  |

### 7.3 모델 변경 설계

#### Schedule 모델에 vat_mode 필드 추가

문서(견적서/거래명세서) 생성 단위가 납품 일정(Schedule)이므로 Schedule에 추가:

```python
# models.py — Schedule 클래스에 추가
VAT_MODE_CHOICES = [
    ('vat_excluded', '부가세 별도 (공급가액 + 10%)'),
    ('vat_included', '부가세 포함 (입력 금액에 포함)'),
    ('vat_none', '부가세 없음 (0원)'),
]
vat_mode = models.CharField(
    max_length=20,
    choices=VAT_MODE_CHOICES,
    default='vat_excluded',
    verbose_name="부가세 계산 방식",
    help_text="견적서/거래명세서 생성 시 적용되는 부가세 방식"
)
```

#### DeliveryItem.save() 수정

`vat_mode`를 Schedule에서 읽어 계산:

```python
def save(self, *args, **kwargs):
    ...
    if self.unit_price is not None and self.quantity:
        from decimal import Decimal
        subtotal = self.unit_price * self.quantity

        # vat_mode 결정
        vat_mode = 'vat_excluded'
        if self.schedule and hasattr(self.schedule, 'vat_mode'):
            vat_mode = self.schedule.vat_mode

        if vat_mode == 'vat_included':
            # 입력 금액에 부가세 이미 포함 — total_price = 입력값 그대로
            self.total_price = subtotal
        elif vat_mode == 'vat_none':
            # 부가세 없음
            self.total_price = subtotal
        else:
            # vat_excluded (기본): 부가세 10% 추가
            self.total_price = subtotal * Decimal('1.1')
    super().save(*args, **kwargs)
```

> **주의**: `DeliveryItem.save()`에서 `self.schedule`을 참조하므로 `schedule`이 없는 History 연결 품목은 기존 방식(`vat_excluded`) 유지.

### 7.4 영향을 받는 파일

| 파일                                                       | 변경 내용                                                 |
| ---------------------------------------------------------- | --------------------------------------------------------- |
| `reporting/models.py`                                      | `Schedule.vat_mode` 필드 추가, `DeliveryItem.save()` 수정 |
| `reporting/views.py` — `generate_document_data()` (~12400) | `vat_mode`에 따라 subtotal/tax/total 계산 분기            |
| `reporting/views.py` — `generate_document_pdf()` (~12644)  | 동일하게 vat_mode 분기 적용                               |
| `reporting/templates/reporting/schedule_detail.html`       | VAT 모드 표시 및 변경 UI                                  |
| `reporting/templates/reporting/schedule_form.html`         | VAT 모드 선택 드롭다운 추가                               |
| `reporting/templates/reporting/funnel/` 관련               | 필요 시 견적 VAT 모드 표시                                |

### 7.5 Quote 모델 VAT 모드

Quote는 현재 `subtotal`, `tax_amount`, `total_amount` 필드를 별도 저장. Quote에도 `vat_mode` 추가 가능하나 Quote와 Document 생성이 Schedule 기반이므로 **Schedule의 `vat_mode`를 우선 적용**하고 Quote는 다음 단계에서 검토.

### 7.6 하위 호환성

- `Schedule.vat_mode` default='vat_excluded'로 기존 데이터는 현재 방식 유지
- 기존 마이그레이션으로 인해 기존 데이터는 영향 없음
- `DeliveryItem.save()`에서 `schedule`이 없으면 기존 10% 방식 fallback

---

## 8. 변경 대상 파일 목록

### 버그 수정 (Bug Fixes)

| 파일                                                    | 변경 이유                                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `reporting/views.py`                                    | Bug 1: `product_create()` 비-AJAX 경로에 specification/unit 추가                     |
| `reporting/views.py`                                    | Bug 2: `product_edit()` POST에 specification/unit 추가                               |
| `reporting/views.py`                                    | Bug 3, 4: `dashboard_view()`에서 schedule_count 및 upcoming_schedules_dash 로직 수정 |
| `reporting/templates/reporting/dashboard.html`          | Bug 3, 4: 카운트 레이블 및 이번 주 일정 섹션 조건부 렌더링 수정                      |
| `reporting/templates/reporting/weekly_report/form.html` | Bug 4: `insertSelected()` 함수에서 Quill 인스턴스 사용으로 변경                      |

### 세금계산서 기능 (New Feature)

| 파일                                                   | 변경 이유                             |
| ------------------------------------------------------ | ------------------------------------- |
| `reporting/models.py`                                  | `TaxInvoiceRequest` 신규 모델 추가    |
| `reporting/views.py`                                   | 세금계산서 요청/발행/취소 API 뷰 추가 |
| `reporting/urls.py`                                    | 세금계산서 API URL 등록               |
| `reporting/admin.py`                                   | `TaxInvoiceRequest` 관리자 등록       |
| `reporting/templates/reporting/schedule_calendar.html` | 세금계산서 탭 추가                    |
| `reporting/templates/reporting/schedule_detail.html`   | 세금계산서 요청/상태 섹션 추가        |

### VAT 계산 모드 (New Feature)

| 파일                                                 | 변경 이유                                                      |
| ---------------------------------------------------- | -------------------------------------------------------------- |
| `reporting/models.py`                                | `Schedule.vat_mode` 필드 추가, `DeliveryItem.save()` 수정      |
| `reporting/views.py`                                 | `generate_document_data()`, `generate_document_pdf()` VAT 분기 |
| `reporting/templates/reporting/schedule_form.html`   | VAT 모드 선택 필드 추가                                        |
| `reporting/templates/reporting/schedule_detail.html` | VAT 모드 표시                                                  |

---

## 9. 마이그레이션 필요 여부

| 변경 내용                       | 마이그레이션 필요                         |
| ------------------------------- | ----------------------------------------- |
| Bug 1-4 (뷰/템플릿/JS)          | ❌ 불필요                                 |
| `TaxInvoiceRequest` 신규 모델   | ✅ **필요**                               |
| `Schedule.vat_mode` 필드 추가   | ✅ **필요** (default='vat_excluded' 안전) |
| `DeliveryItem.save()` 로직 수정 | ❌ 불필요 (모델 필드 변경 없음)           |

**마이그레이션 전 확인**:

```bash
python manage.py makemigrations --dry-run --check
python manage.py check
```

**피처 구현 전 실행**:

```bash
python manage.py makemigrations reporting --name phase_8_5_tax_invoice_vat
python manage.py migrate
```

---

## 10. 추가 또는 업데이트할 테스트

### 신규 테스트 케이스 (reporting/tests.py 추가)

#### 버그 수정 테스트

```python
class ProductSpecificationSaveTest(TestCase):
    """Bug 1: product_create/edit에서 specification 저장 테스트"""

    def test_product_create_saves_specification(self):
        """일반 폼 제출로 제품 생성 시 specification이 저장되는지 확인"""
        ...

    def test_product_create_ajax_saves_specification(self):
        """AJAX 제품 생성 시 specification이 저장되는지 확인"""
        ...

    def test_product_edit_saves_specification(self):
        """제품 수정 시 specification이 저장되는지 확인"""
        ...

    def test_product_edit_saves_unit(self):
        """제품 수정 시 unit이 저장되는지 확인"""
        ...


class DashboardScheduleCountTest(TestCase):
    """Bug 2, 3: 대시보드 일정 수 및 이번 주 일정 로드 테스트"""

    def test_schedule_count_includes_this_week(self):
        """이번 주 일정이 있으면 schedule_count > 0 확인"""
        ...

    def test_upcoming_schedules_includes_completed(self):
        """완료된 이번 주 일정도 upcoming_schedules에 포함되는지 확인"""
        ...


class WeeklyReportInsertTest(TestCase):
    """Bug 4: 주간보고 일정 가져오기 관련 API 테스트"""

    def test_load_schedules_returns_categorized(self):
        """weekly_report_load_schedules API가 categorized 데이터를 반환하는지"""
        ...

    def test_load_schedules_includes_histories_and_quotes(self):
        """일정에 연결된 히스토리와 견적도 반환되는지 확인"""
        ...
```

#### 세금계산서 기능 테스트

```python
class TaxInvoiceRequestTest(TestCase):
    """세금계산서 요청/발행/취소 워크플로우 테스트"""

    def test_salesman_can_request(self):
        """실무자가 요청 생성 가능한지 확인"""
        ...

    def test_salesman_cannot_issue(self):
        """실무자가 발행 처리 불가한지 확인"""
        ...

    def test_manager_can_issue(self):
        """관리자가 발행 처리 가능한지 확인"""
        ...

    def test_cancel_preserves_record(self):
        """취소 시 레코드가 삭제되지 않고 상태 변경만 되는지"""
        ...

    def test_cross_company_access_denied(self):
        """다른 회사 데이터에 접근 불가한지 확인"""
        ...
```

#### VAT 모드 테스트

```python
class VatModeTest(TestCase):
    """VAT 계산 모드 테스트"""

    def test_vat_excluded_adds_10_percent(self):
        """vat_excluded 모드: total = subtotal × 1.1"""
        ...

    def test_vat_included_preserves_total(self):
        """vat_included 모드: total = 입력 금액 그대로"""
        ...

    def test_vat_none_no_tax(self):
        """vat_none 모드: tax = 0, total = subtotal"""
        ...

    def test_backward_compat_default_is_excluded(self):
        """기존 일정은 default='vat_excluded'로 동작"""
        ...
```

---

## 11. 검증 명령

### 버그 수정 후 실행

```bash
# Django 시스템 체크
python manage.py check

# 모델 변경 없음 확인 (버그 수정만)
python manage.py makemigrations --check --dry-run

# 기존 테스트 회귀 확인
python manage.py test reporting --verbosity=2

# 구체적 테스트 클래스
python manage.py test reporting.tests.ProductSpecificationSaveTest
python manage.py test reporting.tests.DashboardScheduleCountTest
python manage.py test reporting.tests.WeeklyReportInsertTest
```

### 피처 구현 후 실행

```bash
# 마이그레이션 dry-run (모델 변경 후)
python manage.py makemigrations --dry-run

# 실제 마이그레이션 생성 및 적용
python manage.py makemigrations reporting --name phase_8_5_tax_invoice_vat
python manage.py migrate

# 전체 테스트
python manage.py test reporting --verbosity=2

# URL 확인
python manage.py show_urls | grep tax-invoice
python manage.py show_urls | grep weekly
```

---

## 12. 위험 요소

| 위험                              | 설명                                                      | 완화 방법                                           |
| --------------------------------- | --------------------------------------------------------- | --------------------------------------------------- |
| VAT 소급 적용                     | vat_mode 추가 시 기존 데이터에 영향                       | `default='vat_excluded'`로 기존 동작 유지           |
| DeliveryItem.save() 변경          | schedule 없는 History 연결 품목에 영향                    | schedule 없을 때 fallback 로직 유지                 |
| Tax Invoice Request 삭제 금지     | admin에서 실수 삭제 위험                                  | `has_delete_permission = False` 설정                |
| 대시보드 schedule_count 의미 변경 | 기존에 "예정된 일정 수"였던 것을 "이번 주 일정 수"로 변경 | 템플릿 레이블 명확히 변경                           |
| Quill insertText 버전 호환성      | Quill 2.x API가 1.x와 다름                                | `dangerouslyPasteHTML` 사용하는 기존 코드 패턴 따름 |

---

## 13. 권장 다음 단계

1. **Phase 8.5 버그 수정** (즉시): 4개 버그 수정, 기존 테스트 통과 확인
2. **Phase 8.5 세금계산서** (단기): `TaxInvoiceRequest` 모델 + 기본 요청/발행 API + 캘린더 탭 UI
3. **Phase 8.5 VAT 모드** (단기): `Schedule.vat_mode` 필드 + 문서 생성 연동
4. **Phase 9 보안 강화** (중기): Phase 8 계획에 따른 보안 헤더, HSTS, 파일 업로드 안전성
