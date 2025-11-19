# 날짜/시간 입력 필드 UX 가이드

## 개요

고객 미팅 일정 폼(`schedule_form.html`)과 개인 일정 폼(`personal_schedule_form.html`)의 날짜/시간 입력 필드 UX 구현 가이드입니다.

## 요구사항

사용자가 원하는 동작:

1. **아이콘 버튼 클릭 시에만** 달력/시간 선택 드롭다운이 열림
2. **키보드 입력은 자유롭게** 가능 (화살표 키, 숫자 키패드 등)
3. 필드 전체를 클릭해도 자동으로 picker가 열리지 않음

## 구현 방법

### 1. HTML 구조 (schedule_form.html)

```html
<!-- 방문 날짜 -->
<div class="mb-3">
  {{ form.visit_date.label_tag }}
  <div class="input-group">
    {{ form.visit_date }}
    <button
      type="button"
      class="btn btn-outline-secondary"
      id="visit-date-picker-btn"
    >
      <i class="fas fa-calendar-alt"></i>
    </button>
  </div>
</div>

<!-- 방문 시간 -->
<div class="mb-3">
  {{ form.visit_time.label_tag }}
  <div class="input-group">
    {{ form.visit_time }}
    <button
      type="button"
      class="btn btn-outline-secondary"
      id="visit-time-picker-btn"
    >
      <i class="fas fa-clock"></i>
    </button>
  </div>
</div>
```

**핵심 포인트:**

- `input-group` 클래스로 input과 버튼을 그룹화
- 아이콘 버튼에 고유 ID 부여 (`visit-date-picker-btn`, `visit-time-picker-btn`)
- 버튼 타입은 `button` (submit 방지)

### 2. JavaScript 구현

```javascript
document.addEventListener("DOMContentLoaded", function () {
  const visitDateField = document.querySelector('input[name="visit_date"]');
  const visitTimeField = document.querySelector('input[name="visit_time"]');

  const visitDateBtn = document.getElementById("visit-date-picker-btn");
  const visitTimeBtn = document.getElementById("visit-time-picker-btn");

  // 1) input은 키보드 입력 가능하게 (readonly 제거)
  if (visitDateField) {
    visitDateField.removeAttribute("readonly");
    visitDateField.style.cursor = "text";
  }
  if (visitTimeField) {
    visitTimeField.removeAttribute("readonly");
    visitTimeField.style.cursor = "text";
  }

  // 2) 오른쪽 아이콘 클릭했을 때만 picker 열기
  if (visitDateField && visitDateBtn) {
    visitDateBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof safeShowPicker === "function") {
        safeShowPicker(visitDateField);
      } else if (visitDateField.showPicker) {
        try {
          visitDateField.showPicker();
        } catch (err) {
          console.warn("showPicker failed:", err);
        }
      }
    });
  }

  if (visitTimeField && visitTimeBtn) {
    visitTimeBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (typeof safeShowPicker === "function") {
        safeShowPicker(visitTimeField);
      } else if (visitTimeField.showPicker) {
        try {
          visitTimeField.showPicker();
        } catch (err) {
          console.warn("showPicker failed:", err);
        }
      }
    });
  }
});
```

**핵심 포인트:**

- `readonly` 속성을 **제거**하여 키보드 입력 허용
- 커서를 `text`로 설정하여 입력 가능한 필드임을 표시
- 아이콘 버튼 클릭 시에만 `showPicker()` 호출
- `safeShowPicker` 함수 우선 사용 (fallback으로 `showPicker()`)

### 3. 제거해야 할 안티패턴

❌ **다음과 같은 코드는 제거해야 함:**

```javascript
// ❌ 이런 코드가 있으면 안 됨 - 필드 전체 클릭 시 자동으로 열림
dateField.addEventListener("click", function (e) {
  e.preventDefault();
  safeShowPicker(this);
});

// ❌ 포커스 시 자동으로 열림
dateField.addEventListener("focus", function (e) {
  setTimeout(() => {
    safeShowPicker(this);
  }, 150);
});

// ❌ readonly 속성은 키보드 입력을 막음
dateField.readOnly = true;
dateField.setAttribute("readonly", "readonly");

// ❌ 클릭/포커스 이벤트를 막으면 안 됨
dateField.addEventListener("click", function (e) {
  e.stopPropagation(); // 이것도 제거
});
```

## 동작 방식

### 사용자 행동별 동작

| 사용자 행동              | 결과                         |
| ------------------------ | ---------------------------- |
| 날짜 필드 클릭           | 커서만 표시, picker 안 열림  |
| 시간 필드 클릭           | 커서만 표시, picker 안 열림  |
| 캘린더 아이콘 클릭       | 📅 날짜 picker 드롭다운 표시 |
| 시계 아이콘 클릭         | 🕐 시간 picker 드롭다운 표시 |
| 시간 필드에서 ↑/↓ 화살표 | 오전/오후 또는 시간 증감     |
| 숫자 키패드 입력         | 직접 입력 가능               |
| Tab 키                   | 다음 필드로 이동             |

## 폼 위젯 설정 (views.py)

```python
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        widgets = {
            'visit_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'visit_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }
```

**중요:** `type='date'`와 `type='time'`을 설정하여 브라우저 네이티브 picker 활성화

## 개인 일정 폼 (personal_schedule_form.html)

개인 일정은 더 단순한 구조를 사용합니다:

```javascript
// 개인 일정은 아이콘 버튼 없이 단순하게
const dateInput = document.querySelector(
  "#{{ form.schedule_date.id_for_label }}"
);
if (dateInput) {
  dateInput.setAttribute("type", "date");
}

const timeInput = document.querySelector(
  "#{{ form.schedule_time.id_for_label }}"
);
if (timeInput) {
  timeInput.setAttribute("type", "time");
}
```

개인 일정은 브라우저 기본 동작을 그대로 사용합니다.

## 예상 계약일 필드

고객 미팅 폼에는 `expected_close_date` 필드도 있습니다. 이 필드도 같은 방식으로 처리할 수 있습니다:

```html
<div class="input-group">
  {{ form.expected_close_date }}
  <button
    type="button"
    class="btn btn-outline-secondary"
    id="expected-close-date-picker-btn"
  >
    <i class="fas fa-calendar-alt"></i>
  </button>
</div>
```

## 트러블슈팅

### 문제: 아이콘 클릭 시 picker가 안 열림

- `showPicker()` API 지원 확인 (Chrome 99+, Edge 99+, Safari 16+)
- `safeShowPicker` 함수가 정의되어 있는지 확인
- 브라우저 콘솔에서 에러 메시지 확인

### 문제: 키보드 입력이 안 됨

- `readonly` 속성이 제거되었는지 확인
- `keydown` 이벤트에 `preventDefault()`가 없는지 확인

### 문제: 필드 클릭 시 자동으로 picker가 열림

- 기존 `click`, `focus` 이벤트 리스너 제거 확인
- DOMContentLoaded 안에서 중복 이벤트 등록 여부 확인

## 참고사항

- Bootstrap 5 `input-group` 스타일 사용
- Font Awesome 아이콘 (`fa-calendar-alt`, `fa-clock`)
- 브라우저 호환성: 모던 브라우저에서 `showPicker()` API 지원 필요
- 모바일에서는 브라우저 네이티브 picker 자동 표시

## 파일 위치

- 고객 미팅 폼: `reporting/templates/reporting/schedule_form.html`
- 개인 일정 폼: `reporting/templates/reporting/personal_schedule_form.html`
- 폼 정의: `reporting/views.py` (ScheduleForm)
- 개인 일정 폼 정의: `reporting/personal_schedule_views.py` (PersonalScheduleForm)

## 마지막 업데이트

2025년 11월 19일 - 아이콘 버튼 방식 구현 완료
