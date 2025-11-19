# 0원(Zero Value) 처리 가이드

> **작성일**: 2025년 11월 19일  
> **난이도**: ⭐⭐⭐⭐⭐ (매우 어려움)  
> **주의**: Python/JavaScript에서 0은 falsy 값입니다!

## 문제 개요

품목 단가를 **0원으로 저장**하려고 할 때, 원래 가격(예: 515,000원)으로 되돌아가는 버그가 발생했습니다.

### 핵심 원인

- **JavaScript**: `||` 연산자와 `if (value)` 체크가 0을 무시
- **Python**: `if not value:` 조건이 0을 True로 처리
- **결과**: 0을 입력해도 제품의 기본 가격으로 덮어씀

---

## 수정된 파일 목록

### 1. Python 백엔드 (3개 파일)

#### `reporting/models.py` - DeliveryItem.save() ⭐ 가장 중요

```python
# ❌ 문제 코드
if not self.unit_price:  # 0이 falsy 처리되어 True → 제품 가격으로 덮어씀!
    self.unit_price = self.product.get_current_price()

# ✅ 수정 코드
if self.unit_price is None:  # None만 True, 0은 False
    self.unit_price = self.product.get_current_price()

# 총액 계산도 수정
# ❌ if self.unit_price and self.quantity:
# ✅ if self.unit_price is not None and self.quantity:
```

#### `reporting/views.py` - save_delivery_items (line ~82-112)

```python
# ❌ 문제 코드
if unit_price != '':
    delivery_item.unit_price = Decimal(str(unit_price))

# ✅ 수정 코드
if unit_price != '' and unit_price is not None:
    try:
        delivery_item.unit_price = Decimal(str(unit_price))
    except (ValueError, decimal.InvalidOperation):
        pass  # 유효하지 않은 값은 무시
```

#### `reporting/views.py` - schedule_update_delivery_items (line ~2762-2788)

```python
# ✅ 올바른 코드 (이미 0 처리됨)
item_unit_price = None
if item.unit_price is not None:
    item_unit_price = float(item.unit_price)  # 0도 0.0으로 변환

delivery_items_list.append({
    'unit_price': item_unit_price,  # None은 None, 0은 0.0
})
```

---

### 2. JavaScript 프론트엔드 (6곳)

#### `schedule_calendar.html` - saveCalendarDeliveryItems (line ~4115-4175)

```javascript
// ❌ 문제 코드
const unitPrice = parseFloat(value) || 0; // 0이 falsy 처리
formData.append("unit_price", unitPrice || ""); // 0이 ''로 전송됨

// ✅ 수정 코드
const unitPriceRaw = input.value;
let unitPrice = unitPriceRaw === "" ? "" : parseFloat(unitPriceRaw);

if (unitPrice === "") {
  formData.append(`delivery_items[${validIndex}][unit_price]`, "");
} else {
  // 0 포함 모든 숫자를 문자열로 명시적 변환
  formData.append(
    `delivery_items[${validIndex}][unit_price]`,
    String(unitPrice)
  );
}
```

#### `schedule_calendar.html` - calculateCalendarItemTotal (line ~3924-3970)

```javascript
// ❌ 문제 코드
const quantity = parseFloat(quantityInput.value) || 0;
const unitPrice = parseFloat(unitPriceInput.value) || 0;

// ✅ 수정 코드
const quantityRaw = quantityInput?.value;
const quantity = quantityRaw === "" ? 0 : parseFloat(quantityRaw);

const unitPriceRaw = unitPriceInput?.value;
const unitPrice = unitPriceRaw === "" ? 0 : parseFloat(unitPriceRaw);
```

#### `schedule_calendar.html` - addCalendarDeliveryItem (line ~3867)

```javascript
// ❌ 문제 코드
<input value="${itemData.unit_price || ''}">

// ✅ 수정 코드
<input value="${itemData.unit_price ?? ''}">  // ?? 연산자 사용
```

#### `schedule_calendar.html` - forceUpdateScheduleModal (line ~4377)

```javascript
// ❌ 문제 코드
const rawAmount = parseInt(amount) || 0;

// ✅ 수정 코드
const rawAmount = parseInt(amount ?? 0) || 0;
```

#### `schedule_calendar.html` - 템플릿 리터럴 (line ~5827)

```javascript
// ❌ 문제 코드
${schedule.delivery_amount ? ... : ...}

// ✅ 수정 코드
${schedule.delivery_amount !== null && schedule.delivery_amount !== undefined ?
  parseInt(schedule.delivery_amount).toLocaleString() + '원' :
  '미정'}
```

---

## 핵심 원칙

### ✅ DO (해야 할 것)

```javascript
// JavaScript
value ?? defaultValue        // Nullish coalescing
value === '' ? 0 : parseFloat(value)
if (value !== null && value !== undefined)

// Python
if value is None:
if value is not None:
```

### ❌ DON'T (하지 말아야 할 것)

```javascript
// JavaScript
value || defaultValue        // 0을 falsy 처리
parseFloat(value) || 0       // 0이 0으로 변환 후 다시 falsy
if (value)                   // 0을 false로 간주

// Python
if not value:                # 0을 True로 처리
if value:                    # 0을 False로 처리
```

---

## 테스트 시나리오

### 시나리오 1: 새 품목에 0원 입력

1. 품목 모달 열기
2. 제품 선택 (product_id 설정됨)
3. 단가를 0원으로 입력
4. 저장 버튼 클릭
5. **기대 결과**: DB에 0 저장, 모달 재오픈 시 0원 표시

### 시나리오 2: 기존 품목을 0원으로 수정

1. 기존 품목(예: 515,000원) 모달 열기
2. 단가를 0원으로 변경
3. 저장 버튼 클릭
4. **기대 결과**: 515,000원 → 0원 변경, 재오픈 시 0원 유지

### 시나리오 3: 0원 품목을 양수로 수정

1. 0원 품목 모달 열기
2. 단가를 10,000원으로 변경
3. 저장 버튼 클릭
4. **기대 결과**: 0원 → 10,000원 변경, 총액 계산 정상

---

## 디버깅 팁

### JavaScript 콘솔 로그 추가

```javascript
console.log("unitPrice type:", typeof unitPrice, "value:", unitPrice);
console.log("is zero?", unitPrice === 0);
console.log("is falsy?", !unitPrice); // 0일 때 true → 문제!
```

### Python 디버깅

```python
print(f"unit_price: {unit_price}, is None: {unit_price is None}, truthy: {bool(unit_price)}")
# unit_price: 0, is None: False, truthy: False → if not 조건에서 문제 발생
```

### DB 확인

```sql
SELECT id, item_name, unit_price, product_id FROM reporting_deliveryitem
WHERE schedule_id = 123 ORDER BY created_at DESC;
```

---

## 관련 파일

- `reporting/models.py` - DeliveryItem 모델 save() 메서드
- `reporting/views.py` - save_delivery_items, schedule_update_delivery_items
- `reporting/templates/reporting/schedule_calendar.html` - 품목 모달 전체 로직

---

## 추가 주의사항

### 1. FormData 전송 시

```javascript
// 0을 전송할 때는 문자열 "0"으로 명시적 변환
formData.append("price", String(0)); // "0"
formData.append("price", 0); // "0" (자동 변환되지만 명시적이 좋음)
formData.append("price", ""); // 빈 문자열 (None 의미)
```

### 2. Django에서 수신 시

```python
unit_price = request.POST.get('unit_price', '').strip()
if unit_price == '':
    # None으로 처리
    item.unit_price = None
elif unit_price == '0':
    # 0으로 처리
    item.unit_price = Decimal('0')
else:
    item.unit_price = Decimal(unit_price)
```

### 3. JSON 응답 시

```python
# None과 0을 구분하여 응답
{
    'unit_price': None,      # null로 전송
    'unit_price': 0,         # 0으로 전송
    'unit_price': 0.0,       # 0.0으로 전송
}
```

---

## 체크리스트

다른 필드에서 0을 처리할 때 이 체크리스트를 확인하세요:

- [ ] JavaScript: `||` 대신 `??` 또는 명시적 체크 사용
- [ ] JavaScript: `if (value)` 대신 `if (value !== null && value !== undefined)` 사용
- [ ] Python: `if not value:` 대신 `if value is None:` 사용
- [ ] FormData: 숫자 0을 `String(0)`으로 명시적 변환
- [ ] Django: `value == ''`와 `value == '0'` 구분
- [ ] 모델 save(): truthy 체크 대신 `is None` 체크
- [ ] 총액 계산: 0원도 유효한 금액으로 처리

---

## 결론

**0은 유효한 값입니다!**

프로그래밍 언어의 falsy/truthy 동작에 의존하지 말고, 항상 **명시적으로 `None`/`null`/`undefined`와 `0`을 구분**하세요.

이 가이드를 참고하여 비슷한 버그를 사전에 방지하시기 바랍니다.
