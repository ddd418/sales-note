# Bootstrap 모달 사용 가이드

## 개요

Bootstrap 5 모달을 올바르게 설정하여 ESC 키, 외부 클릭, X 버튼으로 모두 닫을 수 있도록 하는 방법입니다.

## 핵심 설정

### 1. CSS 설정 (backdrop 표시)

**올바른 설정:**

```css
/* backdrop 표시하여 모달 외부 클릭 감지 가능하게 */
.modal-backdrop {
  background-color: rgba(0, 0, 0, 0.5) !important; /* 반투명 검은 배경 */
  z-index: 1050 !important;
}

/* 모달은 backdrop보다 높게 */
.modal {
  z-index: 1055 !important;
}

/* 모달 다이얼로그 */
.modal-dialog {
  z-index: 1056 !important;
}

/* 모달 컨텐츠 */
.modal-content {
  position: relative;
  z-index: 1057 !important;
  background-color: #fff;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 0.3rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
```

**❌ 피해야 할 설정:**

```css
/* 이렇게 하면 외부 클릭이 작동하지 않음 */
.modal-backdrop {
  display: none !important; /* backdrop 숨김 */
}

.modal {
  pointer-events: none !important; /* 클릭 이벤트 차단 */
}
```

### 2. JavaScript 모달 생성

**권장 방법 (모든 닫기 방법 활성화):**

```javascript
const modal = new bootstrap.Modal(modalElement, {
  backdrop: true, // 외부 클릭 시 모달 닫기 활성화
  keyboard: true, // ESC 키로 모달 닫기 활성화
});
modal.show();
```

**옵션 설명:**

- `backdrop: true` - 외부 클릭 시 모달 닫기 (기본값)
- `backdrop: 'static'` - 외부 클릭 불가, ESC만 가능
- `backdrop: false` - backdrop 없음 (외부 클릭 불가)
- `keyboard: true` - ESC 키로 닫기 (기본값)
- `keyboard: false` - ESC 키로 닫기 불가

## 실제 사용 예제

### 예제 1: 기본 모달

```javascript
function openMyModal() {
  const modalHtml = `
    <div class="modal fade" id="myModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">모달 제목</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            모달 내용
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
            <button type="button" class="btn btn-primary">저장</button>
          </div>
        </div>
      </div>
    </div>
  `;

  // 기존 모달 제거
  const existingModal = document.getElementById("myModal");
  if (existingModal) {
    existingModal.remove();
  }

  // 새 모달 추가
  document.body.insertAdjacentHTML("beforeend", modalHtml);

  // 모달 인스턴스 생성 및 표시
  const modal = new bootstrap.Modal(document.getElementById("myModal"), {
    backdrop: true, // 외부 클릭으로 닫기
    keyboard: true, // ESC 키로 닫기
  });
  modal.show();
}
```

### 예제 2: 기존 모달 인스턴스 재사용

```javascript
function openExistingModal() {
  const modalElement = document.getElementById("existingModal");

  // 기존 인스턴스가 있으면 재사용, 없으면 새로 생성
  const modalInstance =
    bootstrap.Modal.getInstance(modalElement) ||
    new bootstrap.Modal(modalElement, {
      backdrop: true,
      keyboard: true,
    });

  modalInstance.show();
}
```

### 예제 3: 모달 닫기 (프로그래밍 방식)

```javascript
function closeModal() {
  const modalElement = document.getElementById("myModal");
  const modalInstance = bootstrap.Modal.getInstance(modalElement);

  if (modalInstance) {
    modalInstance.hide();
  }
}
```

### 예제 4: 모달 이벤트 처리

```javascript
const modalElement = document.getElementById("myModal");

// 모달이 완전히 표시된 후 실행
modalElement.addEventListener("shown.bs.modal", function () {
  console.log("모달 열림");
  // 예: 입력 필드에 포커스
  document.getElementById("modalInput").focus();
});

// 모달이 완전히 숨겨진 후 실행
modalElement.addEventListener("hidden.bs.modal", function () {
  console.log("모달 닫힘");
  // 예: DOM에서 모달 제거
  modalElement.remove();
});

// 모달이 닫히기 시작할 때 실행 (취소 가능)
modalElement.addEventListener("hide.bs.modal", function (event) {
  if (!confirm("정말 닫으시겠습니까?")) {
    event.preventDefault(); // 모달 닫기 취소
  }
});
```

## 모달 닫기 방법 정리

### 1. X 버튼으로 닫기

```html
<button type="button" class="btn-close" data-bs-dismiss="modal"></button>
```

### 2. 닫기 버튼으로 닫기

```html
<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
  닫기
</button>
```

### 3. ESC 키로 닫기

```javascript
// keyboard: true 옵션 필요
const modal = new bootstrap.Modal(modalElement, {
  keyboard: true,
});
```

### 4. 모달 외부(backdrop) 클릭으로 닫기

```javascript
// backdrop: true 옵션 필요
const modal = new bootstrap.Modal(modalElement, {
  backdrop: true,
});
```

### 5. 프로그래밍 방식으로 닫기

```javascript
const modalInstance = bootstrap.Modal.getInstance(modalElement);
modalInstance.hide();
```

## 특수 케이스

### 케이스 1: 외부 클릭으로 닫히지 않게 하기

```javascript
const modal = new bootstrap.Modal(modalElement, {
  backdrop: "static", // 외부 클릭 불가
  keyboard: true, // ESC는 가능
});
```

### 케이스 2: ESC 키로 닫히지 않게 하기

```javascript
const modal = new bootstrap.Modal(modalElement, {
  backdrop: true, // 외부 클릭 가능
  keyboard: false, // ESC 불가
});
```

### 케이스 3: 모든 방법으로 닫히지 않게 하기 (강제 입력)

```javascript
const modal = new bootstrap.Modal(modalElement, {
  backdrop: "static", // 외부 클릭 불가
  keyboard: false, // ESC 불가
});
// X 버튼과 닫기 버튼도 제거해야 함
```

## 중첩 모달 처리

### z-index 관리

```css
/* 첫 번째 모달 */
.modal:nth-of-type(1) {
  z-index: 1055;
}
.modal-backdrop:nth-of-type(1) {
  z-index: 1050;
}

/* 두 번째 모달 (중첩) */
.modal:nth-of-type(2) {
  z-index: 1065;
}
.modal-backdrop:nth-of-type(2) {
  z-index: 1060;
}

/* 세 번째 모달 (중첩) */
.modal:nth-of-type(3) {
  z-index: 1075;
}
.modal-backdrop:nth-of-type(3) {
  z-index: 1070;
}
```

### 중첩 모달 열기 예제

```javascript
function openNestedModal() {
  const nestedModalHtml = `
    <div class="modal fade" id="nestedModal" tabindex="-1" style="z-index: 1065;">
      <div class="modal-dialog">
        <div class="modal-content">
          <!-- 모달 내용 -->
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML("beforeend", nestedModalHtml);

  const nestedModal = new bootstrap.Modal(
    document.getElementById("nestedModal"),
    {
      backdrop: true,
      keyboard: true,
    }
  );

  nestedModal.show();

  // 중첩 모달이 닫힐 때 DOM에서 제거
  document.getElementById("nestedModal").addEventListener(
    "hidden.bs.modal",
    function () {
      this.remove();
    },
    { once: true }
  );
}
```

## 문제 해결

### 문제 1: 모달이 외부 클릭으로 닫히지 않음

**해결 방법:**

1. CSS에서 `backdrop`이 `display: none`으로 숨겨져 있지 않은지 확인
2. `pointer-events: none`으로 클릭이 차단되지 않았는지 확인
3. JavaScript에서 `backdrop: true` 옵션 설정 확인

### 문제 2: ESC 키로 닫히지 않음

**해결 방법:**

1. JavaScript에서 `keyboard: true` 옵션 설정 확인
2. 다른 이벤트 리스너가 ESC 키를 가로채지 않는지 확인

### 문제 3: 모달 뒤의 페이지가 스크롤됨

**해결 방법:**

```css
/* Bootstrap 기본 동작이 이미 처리하지만, 필요 시 추가 */
body.modal-open {
  overflow: hidden;
}
```

### 문제 4: 모달이 화면 밖으로 나감

**해결 방법:**

```javascript
// 모달을 화면 중앙에 배치
const modal = new bootstrap.Modal(modalElement, {
  backdrop: true,
  keyboard: true,
});

modalElement.addEventListener("shown.bs.modal", function () {
  const modalDialog = this.querySelector(".modal-dialog");
  modalDialog.style.marginTop = "50px"; // 상단 여백 조정
});
```

## 프로젝트 적용 체크리스트

- [ ] CSS에서 `.modal-backdrop` 표시 설정 확인
- [ ] CSS에서 `pointer-events` 차단 제거 확인
- [ ] 모달 생성 시 `backdrop: true` 옵션 추가
- [ ] 모달 생성 시 `keyboard: true` 옵션 추가
- [ ] HTML에서 X 버튼에 `data-bs-dismiss="modal"` 속성 추가
- [ ] 닫기 버튼에 `data-bs-dismiss="modal"` 속성 추가
- [ ] 모달 이벤트 리스너 설정 (필요 시)
- [ ] 중첩 모달 z-index 조정 (필요 시)

## 참고 자료

### Bootstrap 5 모달 옵션 전체 목록

```javascript
const modal = new bootstrap.Modal(element, {
  backdrop: true, // true | 'static' | false
  keyboard: true, // true | false
  focus: true, // 모달이 열릴 때 포커스
  animation: true, // 페이드 애니메이션 사용
});
```

### Bootstrap 5 모달 메서드

```javascript
const modalInstance = bootstrap.Modal.getInstance(element);

modalInstance.show(); // 모달 열기
modalInstance.hide(); // 모달 닫기
modalInstance.toggle(); // 모달 토글
modalInstance.dispose(); // 모달 인스턴스 제거
```

### Bootstrap 5 모달 이벤트

```javascript
// show.bs.modal    - 모달이 표시되기 시작할 때
// shown.bs.modal   - 모달이 완전히 표시된 후
// hide.bs.modal    - 모달이 숨겨지기 시작할 때
// hidden.bs.modal  - 모달이 완전히 숨겨진 후

modalElement.addEventListener("shown.bs.modal", function () {
  // 모달 열림 후 동작
});
```

## 실제 프로젝트 적용 예시

### 일정 캘린더 모달 (schedule_calendar.html)

```javascript
// 일정 상세 모달
const modal = new bootstrap.Modal(
  document.getElementById("scheduleDetailModal"),
  {
    backdrop: true, // 외부 클릭으로 닫기
    keyboard: true, // ESC 키로 닫기
  }
);
modal.show();

// 제품 검색 모달
const productModal = new bootstrap.Modal(
  document.getElementById("productSearchModal"),
  {
    backdrop: true,
    keyboard: true,
  }
);
productModal.show();

// 납품 품목 모달
const deliveryModal = new bootstrap.Modal(
  document.getElementById("deliveryItemsModal"),
  {
    backdrop: true,
    keyboard: true,
  }
);
deliveryModal.show();
```

## 작성일

2025년 11월 19일

## 관련 파일

- `reporting/templates/reporting/schedule_calendar.html` (라인 13-40: CSS 설정)
- `reporting/templates/reporting/schedule_calendar.html` (라인 1703-1710, 3703-3710, 등: 모달 생성)
