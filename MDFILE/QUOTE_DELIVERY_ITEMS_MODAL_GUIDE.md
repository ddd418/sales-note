# 견적/납품 품목 관리 모달 통합 가이드

## 개요

견적 제출과 납품 일정에서 품목을 관리할 때 하나의 공용 모달을 사용하여 코드 중복을 제거하고 유지보수성을 향상시킨 구조입니다.

## 핵심 개념

### 1. 컨텍스트 기반 모달 시스템

- **하나의 모달, 두 가지 용도**: `scheduleDeliveryItemsModal`을 견적과 납품 양쪽에서 사용
- **컨텍스트 변수**: `currentItemsContext` ('quote' 또는 'delivery')로 현재 모드 구분
- **동적 UI**: 컨텍스트에 따라 모달 헤더 색상과 텍스트 자동 변경

## 주요 구성 요소

### 1. 전역 변수

```javascript
let scheduleDeliveryItemsData = []; // 품목 데이터 배열 (견적/납품 공용)
let currentItemsContext = null; // 현재 컨텍스트: 'quote' 또는 'delivery'
let scheduleDeliveryItemIndex = 0; // 품목 인덱스
```

### 2. 모달 열기 함수

```javascript
function openScheduleDeliveryModal(context) {
  currentItemsContext = context; // 컨텍스트 설정

  const isQuote = context === "quote";
  const headerClass = isQuote ? "bg-info text-white" : "bg-warning text-dark";
  const headerTitle = isQuote ? "견적 품목 관리" : "납품 품목 관리";
  const headerIcon = isQuote ? "fa-file-invoice" : "fa-boxes";

  // 모달 HTML 생성
  const modalHtml = `
    <div class="modal fade" id="scheduleDeliveryItemsModal" tabindex="-1">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header ${headerClass}">
            <h5 class="modal-title">
              <i class="fas ${headerIcon} me-2"></i>${headerTitle}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 품목 목록 컨테이너 -->
            <div id="schedule-delivery-items-container"></div>
            <!-- 품목 추가 버튼 -->
            <button type="button" class="btn btn-success" onclick="addScheduleDeliveryItem()">
              <i class="fas fa-plus me-1"></i>품목 추가
            </button>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
            <button type="button" class="btn btn-primary" onclick="saveScheduleDeliveryItems()">저장</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // 모달 표시 및 기존 데이터 로드
  // ...
}
```

### 3. 품목 추가 함수

```javascript
function addScheduleDeliveryItem(itemData = {}) {
  const container = document.getElementById(
    "schedule-delivery-items-container"
  );
  const newItem = document.createElement("div");
  newItem.className = "delivery-item row mb-3 p-3 border rounded bg-light";

  newItem.innerHTML = `
    <div class="col-md-4">
      <label class="form-label fw-bold">품목명 <span class="text-danger">*</span></label>
      <div class="input-group">
        <input type="text" class="form-control item-name" value="${
          itemData.item_name || ""
        }" readonly>
        <!-- 제품 검색 버튼 -->
        <button class="btn btn-primary" type="button" onclick="openProductSearchModal(this)">
          <i class="fas fa-search"></i>
        </button>
        <!-- 새 제품 추가 버튼 -->
        <button class="btn btn-success" type="button" onclick="openDeliveryProductModal(this)">
          <i class="fas fa-plus"></i>
        </button>
      </div>
      <input type="hidden" class="product-id" value="${
        itemData.product_id || ""
      }">
    </div>
    <div class="col-md-2">
      <label class="form-label fw-bold">수량 <span class="text-danger">*</span></label>
      <input type="number" class="form-control quantity-input" min="1" value="${
        itemData.quantity || ""
      }" required>
    </div>
    <div class="col-md-2">
      <label class="form-label fw-bold">단가 (부가세 별도)</label>
      <input type="text" class="form-control unit-price-display" 
             value="${
               itemData.unit_price
                 ? parseInt(itemData.unit_price).toLocaleString()
                 : ""
             }" 
             oninput="updateDeliveryUnitPrice(this)">
      <input type="hidden" class="unit-price-input" value="${
        itemData.unit_price || ""
      }">
    </div>
    <div class="col-md-3">
      <label class="form-label fw-bold">금액 (부가세 포함)</label>
      <div class="form-control-plaintext">
        <span class="item-total fw-bold text-primary">0원</span>
      </div>
    </div>
    <div class="col-md-1 d-flex align-items-end">
      <button type="button" class="btn btn-danger btn-sm w-100" onclick="removeScheduleDeliveryItem(this)">
        <i class="fas fa-trash"></i>
      </button>
    </div>
  `;

  container.appendChild(newItem);

  // 이벤트 리스너 추가
  const quantityInput = newItem.querySelector(".quantity-input");
  const unitPriceInput = newItem.querySelector(".unit-price-input");

  quantityInput.addEventListener("input", calculateScheduleItemTotal);
  unitPriceInput.addEventListener("input", calculateScheduleItemTotal);
}
```

### 4. 품목 저장 함수

```javascript
function saveScheduleDeliveryItems() {
  const items = document.querySelectorAll(
    "#schedule-delivery-items-container .delivery-item"
  );

  // 품목 데이터 수집
  scheduleDeliveryItemsData = [];
  items.forEach((item) => {
    const itemName = item.querySelector(".item-name").value.trim();
    const quantity =
      parseFloat(item.querySelector(".quantity-input").value) || 0;
    const unitPrice =
      parseFloat(item.querySelector(".unit-price-input").value) || 0;
    const productId = item.querySelector(".product-id").value.trim();

    if (itemName && quantity > 0) {
      scheduleDeliveryItemsData.push({
        item_name: itemName,
        name: itemName,
        quantity: quantity,
        unit_price: unitPrice,
        product_id: productId,
      });
    }
  });

  // 컨텍스트에 따라 다른 필드에 저장
  const context = currentItemsContext || "delivery";

  if (context === "delivery") {
    // 납품 품목 표시 영역
    const displayField = document.getElementById(
      "schedule-delivery-items-display"
    );
    const totalField = document.getElementById(
      "schedule-delivery-total-amount"
    );

    if (displayField && scheduleDeliveryItemsData.length > 0) {
      const displayText = scheduleDeliveryItemsData
        .map((item) => `${item.item_name} x ${item.quantity}개`)
        .join(", ");
      displayField.value = displayText;

      // 총액 계산
      const total = scheduleDeliveryItemsData.reduce(
        (sum, item) => sum + item.quantity * item.unit_price * 1.1,
        0
      );
      totalField.value = Math.round(total);
    }
  } else if (context === "quote") {
    // 견적 품목 표시 영역
    const quoteDisplayField = document.getElementById("quote-items-display");
    const quoteTotalField = document.getElementById("quote-total-amount");

    if (quoteDisplayField && scheduleDeliveryItemsData.length > 0) {
      const displayText = scheduleDeliveryItemsData
        .map((item) => `${item.item_name} x ${item.quantity}개`)
        .join(", ");
      quoteDisplayField.value = displayText;

      // 총액 계산
      const total = scheduleDeliveryItemsData.reduce(
        (sum, item) => sum + item.quantity * item.unit_price * 1.1,
        0
      );
      quoteTotalField.value = Math.round(total);
    }
  }

  // 모달 닫기
  const modalElement = document.getElementById("scheduleDeliveryItemsModal");
  const modalInstance = bootstrap.Modal.getInstance(modalElement);
  if (modalInstance) {
    modalInstance.hide();
  }
}
```

### 5. 금액 계산 함수

```javascript
function calculateScheduleItemTotal(event) {
  const item = event.target.closest(".delivery-item");
  const quantity = parseFloat(item.querySelector(".quantity-input").value) || 0;
  const unitPrice =
    parseFloat(item.querySelector(".unit-price-input").value) || 0;

  // 부가세 포함 계산: (단가 * 수량) * 1.1
  const total = Math.round(quantity * unitPrice * 1.1);

  // 개별 품목 금액 표시
  const totalDisplay = item.querySelector(".item-total");
  totalDisplay.textContent = total.toLocaleString() + "원";

  // 전체 합계 계산
  calculateScheduleTotal();
}

function calculateScheduleTotal() {
  const items = document.querySelectorAll(
    "#schedule-delivery-items-container .delivery-item"
  );
  let grandTotal = 0;

  items.forEach((item) => {
    const quantity =
      parseFloat(item.querySelector(".quantity-input").value) || 0;
    const unitPrice =
      parseFloat(item.querySelector(".unit-price-input").value) || 0;
    grandTotal += quantity * unitPrice * 1.1;
  });

  // 모달 내 총액 표시
  const totalDisplay = document.getElementById("schedule-delivery-modal-total");
  if (totalDisplay) {
    totalDisplay.textContent = Math.round(grandTotal).toLocaleString() + "원";
  }
}
```

### 6. 제품 검색 모달 연동

```javascript
function openProductSearchModal(button) {
  const deliveryItem = button.closest(".delivery-item");

  // 제품 데이터 가져오기 및 모달 표시
  // ...

  // 제품 선택 시
  item.onclick = function () {
    const productId = this.dataset.productId;
    const productCode = this.dataset.productCode;
    const productPrice = this.dataset.productPrice;

    // 품목 정보 입력
    deliveryItem.querySelector(".product-id").value = productId;
    deliveryItem.querySelector(".item-name").value = productCode;
    deliveryItem.querySelector(".unit-price-input").value = productPrice;
    deliveryItem.querySelector(".unit-price-display").value =
      parseInt(productPrice).toLocaleString();

    // 수량이 비어있으면 1로 설정
    const quantityInput = deliveryItem.querySelector(".quantity-input");
    if (!quantityInput.value) {
      quantityInput.value = 1;
    }

    // 금액 자동 계산
    calculateScheduleItemTotal({ target: quantityInput });

    // 모달 닫기
    const modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) {
      modalInstance.hide();
    }
  };
}
```

## 폼에서 사용하는 방법

### HTML 구조

```html
<!-- 견적 제출 일정 -->
<div class="card" id="quote-items-card">
  <div
    class="card-header bg-info text-white d-flex justify-content-between align-items-center"
  >
    <h5 class="mb-0"><i class="fas fa-file-invoice me-2"></i>견적 품목</h5>
    <!-- 품목 관리 버튼 - context='quote' 전달 -->
    <button
      type="button"
      class="btn btn-primary btn-sm"
      onclick="openScheduleDeliveryModal('quote')"
    >
      <i class="fas fa-edit me-1"></i>품목 관리
    </button>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-8">
        <label class="form-label fw-bold">품목 내역</label>
        <textarea
          id="quote-items-display"
          class="form-control"
          rows="3"
          readonly
          placeholder="'품목 관리' 버튼을 클릭하여 견적 품목을 추가하세요."
        ></textarea>
      </div>
      <div class="col-md-4">
        <label class="form-label fw-bold">총 금액 (부가세 포함)</label>
        <div class="input-group">
          <input
            type="number"
            id="quote-total-amount"
            class="form-control"
            readonly
            value="0"
          />
          <span class="input-group-text">원</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- 납품 일정 -->
<div class="card" id="delivery-items-card">
  <div
    class="card-header bg-warning text-dark d-flex justify-content-between align-items-center"
  >
    <h5 class="mb-0"><i class="fas fa-boxes me-2"></i>납품 품목</h5>
    <!-- 품목 관리 버튼 - context='delivery' 전달 -->
    <button
      type="button"
      class="btn btn-warning btn-sm"
      onclick="openScheduleDeliveryModal('delivery')"
    >
      <i class="fas fa-edit me-1"></i>품목 관리
    </button>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-8">
        <label class="form-label fw-bold">품목 내역</label>
        <textarea
          id="schedule-delivery-items-display"
          class="form-control"
          rows="3"
          readonly
          placeholder="'품목 관리' 버튼을 클릭하여 납품 품목을 추가하세요."
        ></textarea>
      </div>
      <div class="col-md-4">
        <label class="form-label fw-bold">총 금액 (부가세 포함)</label>
        <div class="input-group">
          <input
            type="number"
            id="schedule-delivery-total-amount"
            class="form-control"
            readonly
            value="0"
          />
          <span class="input-group-text">원</span>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 서버로 전송 (saveAllItems 함수)

```javascript
function saveAllItems(form) {
  let savedCount = 0;

  // 1. 납품 품목 우선 저장 (scheduleDeliveryItemsData에서)
  const deliveryContainer = document.getElementById(
    "schedule-delivery-items-container"
  );
  if (
    deliveryContainer &&
    deliveryContainer.querySelectorAll(".delivery-item").length > 0
  ) {
    // 납품 품목이 모달에서 입력된 경우
    // scheduleDeliveryItemsData 배열에서 저장
  }

  // 2. 견적 품목 저장 (scheduleDeliveryItemsData에서)
  // context가 'quote'였다면 scheduleDeliveryItemsData를 사용
  if (
    scheduleDeliveryItemsData &&
    scheduleDeliveryItemsData.length > 0 &&
    savedCount === 0
  ) {
    scheduleDeliveryItemsData.forEach((itemData, index) => {
      // hidden input 생성하여 delivery_items[index][name] 등으로 저장
      const nameInput = document.createElement("input");
      nameInput.type = "hidden";
      nameInput.name = `delivery_items[${index}][name]`;
      nameInput.value = itemData.name || itemData.item_name;
      form.appendChild(nameInput);

      // quantity, unit_price, product_id도 동일하게 추가
      // ...

      savedCount++;
    });
  }

  // 3. 폴백: 기존 items-container 방식 (하위 호환성)
  const quoteContainer = document.getElementById("items-container");
  if (quoteContainer && savedCount === 0) {
    // 기존 방식으로 입력된 품목 저장
  }
}
```

## 장점

### 1. 코드 재사용성

- 하나의 모달 시스템을 견적/납품 양쪽에서 사용
- 제품 검색, 품목 추가, 삭제 등 모든 기능 공유
- 코드 중복 최소화

### 2. 유지보수성

- 버그 수정 시 한 곳만 수정하면 양쪽 모두 적용
- 새 기능 추가 시 자동으로 양쪽에서 사용 가능
- 일관된 사용자 경험 제공

### 3. 확장성

- 새로운 일정 유형 추가 시 context만 추가하면 됨
- 같은 패턴으로 다른 폼에도 적용 가능

## 다른 폼에 적용하는 방법

### 1단계: HTML 구조 추가

```html
<!-- 새로운 일정 유형 카드 -->
<div class="card" id="new-type-items-card">
  <div class="card-header bg-success text-white">
    <h5 class="mb-0"><i class="fas fa-icon me-2"></i>새로운 유형 품목</h5>
    <!-- context에 새 유형 전달 -->
    <button
      type="button"
      class="btn btn-success btn-sm"
      onclick="openScheduleDeliveryModal('newType')"
    >
      <i class="fas fa-edit me-1"></i>품목 관리
    </button>
  </div>
  <div class="card-body">
    <textarea
      id="new-type-items-display"
      class="form-control"
      rows="3"
      readonly
    ></textarea>
    <input
      type="number"
      id="new-type-total-amount"
      class="form-control"
      readonly
    />
  </div>
</div>
```

### 2단계: openScheduleDeliveryModal 함수 수정

```javascript
function openScheduleDeliveryModal(context) {
  currentItemsContext = context;

  let headerClass, headerTitle, headerIcon;

  if (context === "quote") {
    headerClass = "bg-info text-white";
    headerTitle = "견적 품목 관리";
    headerIcon = "fa-file-invoice";
  } else if (context === "delivery") {
    headerClass = "bg-warning text-dark";
    headerTitle = "납품 품목 관리";
    headerIcon = "fa-boxes";
  } else if (context === "newType") {
    headerClass = "bg-success text-white";
    headerTitle = "새로운 유형 품목 관리";
    headerIcon = "fa-icon";
  }

  // 모달 생성 및 표시
  // ...
}
```

### 3단계: saveScheduleDeliveryItems 함수 수정

```javascript
function saveScheduleDeliveryItems() {
  // 품목 데이터 수집
  // ...

  const context = currentItemsContext || "delivery";

  if (context === "delivery") {
    // 납품 저장
  } else if (context === "quote") {
    // 견적 저장
  } else if (context === "newType") {
    // 새 유형 저장
    const displayField = document.getElementById("new-type-items-display");
    const totalField = document.getElementById("new-type-total-amount");

    if (displayField && scheduleDeliveryItemsData.length > 0) {
      displayField.value = scheduleDeliveryItemsData
        .map((item) => `${item.item_name} x ${item.quantity}개`)
        .join(", ");

      const total = scheduleDeliveryItemsData.reduce(
        (sum, item) => sum + item.quantity * item.unit_price * 1.1,
        0
      );
      totalField.value = Math.round(total);
    }
  }

  // 모달 닫기
  // ...
}
```

## 주의사항

1. **컨텍스트 일관성**: `openScheduleDeliveryModal(context)` 호출 시 정확한 컨텍스트 문자열 전달
2. **필드 ID 일치**: 각 일정 유형마다 고유한 display field와 total field ID 사용
3. **데이터 초기화**: 모달 열 때 기존 데이터 로드, 닫을 때 초기화 필요
4. **금액 계산 트리거**: 제품 선택 시 `calculateScheduleItemTotal` 자동 호출로 즉시 금액 표시

## 참고 파일

- `reporting/templates/reporting/schedule_form.html`: 전체 구현 코드
- 라인 3300-3700: 모달 관련 함수들
- 라인 3766-3846: saveAllItems 함수 (서버 전송)
- 라인 4187-4317: 제품 검색 모달

## 작성일

2025년 11월 19일
