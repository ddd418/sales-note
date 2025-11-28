# AI 프로그레스 모달 구현 가이드

## 개요

AI 기능 실행 시 사용자에게 진행 상황을 보여주는 프로그레스 모달을 구현하는 방법입니다.
`base.html`에 정의된 공용 함수들을 사용합니다.

---

## 핵심 함수 (base.html에 정의됨)

### 1. `runAITaskWithDetails(taskName, apiUrl, requestData, detailsCallback, onSuccess, onError)`

AI 작업을 실행하는 래퍼 함수입니다.

| 파라미터          | 타입            | 설명                               |
| ----------------- | --------------- | ---------------------------------- |
| `taskName`        | string          | 모달 제목에 표시될 작업 이름       |
| `apiUrl`          | string          | API 엔드포인트 URL                 |
| `requestData`     | object          | POST 요청에 보낼 데이터            |
| `detailsCallback` | async function  | 로그 메시지를 표시하는 비동기 함수 |
| `onSuccess`       | function(data)  | 성공 시 호출되는 콜백              |
| `onError`         | function(error) | 에러 시 호출되는 콜백              |

### 2. `showAILoading(title, message)`

AI 로딩 모달을 표시합니다.

```javascript
showAILoading("AI 분석", "분석 중입니다...");
```

### 3. `hideAILoading()`

AI 로딩 모달을 숨깁니다.

### 4. `addAILog(message, type)`

터미널 스타일 로그를 추가합니다.

| type        | 색상             |
| ----------- | ---------------- |
| `'info'`    | 녹색 (#00ff00)   |
| `'warning'` | 노란색 (#ffff00) |
| `'error'`   | 빨간색 (#ff6b6b) |
| `'success'` | 청록색 (#00ffff) |

### 5. `updateProgress(percent)`

진행률 바를 업데이트합니다. (0~100)

### 6. `sleep(ms)`

지정된 시간(밀리초) 동안 대기합니다.

---

## 구현 예시

### 기본 패턴

```javascript
async function myAIFunction(param) {
  const resultsDiv = document.getElementById("resultsDiv");
  const btn = document.getElementById("myButton");

  resultsDiv.style.display = "none";
  btn.disabled = true;

  await runAITaskWithDetails(
    "AI 기능 이름", // 모달 제목
    "/api/endpoint/", // API URL
    { param: param }, // 요청 데이터

    // 상세 로그 콜백 (async 필수)
    async function () {
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      addAILog("🎯 작업 시작", "info");
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      await sleep(300);
      addAILog("📊 1단계 분석 중...", "info");
      await sleep(300);
      addAILog("🔍 2단계 처리 중...", "info");
      await sleep(300);
      addAILog("✨ 3단계 생성 중...", "info");
    },

    // 성공 콜백
    function (data) {
      btn.disabled = false;
      if (data.result) {
        displayResults(data.result);
        resultsDiv.style.display = "block";
      }
    },

    // 에러 콜백
    function (error) {
      btn.disabled = false;
      resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>오류:</strong> ${error.message}
                </div>
            `;
      resultsDiv.style.display = "block";
    }
  );
}
```

---

## 실제 사용 예시

### 1. AI 팔로우업 우선순위 제안 (followup_list.html)

```javascript
async function suggestFollowUpPriorities() {
  await runAITaskWithDetails(
    "팔로우업 우선순위 제안",
    "/reporting/ai/suggest-follow-ups/",
    {},
    async function () {
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      addAILog("🎯 팔로우업 우선순위 분석 시작", "info");
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      await sleep(300);
      addAILog("🔍 고객별 활동 이력 분석 중...", "info");
      await sleep(300);
      addAILog("📈 영업 기회 상태 분석 중...", "info");
      await sleep(300);
      addAILog("⏰ 마지막 연락 시점 계산 중...", "info");
      await sleep(300);
      addAILog("💰 예상 매출 계산 중...", "info");
      await sleep(300);
      addAILog("🤖 AI 우선순위 모델 실행 중...", "info");
    },
    function (data) {
      if (data.suggestions) {
        displayFollowUpSuggestions(data.suggestions);
      }
    },
    function (error) {
      showNotification("오류: " + error.message, "error");
    }
  );
}
```

### 2. AI 이메일 영업 분석 (thread_detail.html)

```javascript
async function analyzeEmailThread(threadId) {
  const resultsDiv = document.getElementById("threadAnalysisResults");
  const analyzeBtn = document.getElementById("analyzeThreadBtn");

  resultsDiv.style.display = "none";
  analyzeBtn.disabled = true;

  await runAITaskWithDetails(
    "이메일 영업 분석",
    "/reporting/ai/analyze-email-thread/",
    { thread_id: threadId },
    async function () {
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      addAILog("📧 이메일 영업 분석 시작", "info");
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      await sleep(300);
      addAILog("📬 이메일 스레드 수집 중...", "info");
      await sleep(300);
      addAILog("🌡️ 고객 구매 온도 분석 중...", "info");
      await sleep(300);
      addAILog("🔍 숨은 의도/제한조건 파악 중...", "info");
      await sleep(300);
      addAILog("🏷️ 고객 상태 라벨 분류 중...", "info");
      await sleep(300);
      addAILog("✉️ 후속 이메일 초안 생성 중...", "info");
      await sleep(300);
      addAILog("💡 잠재 니즈 예측 중...", "info");
    },
    function (data) {
      analyzeBtn.disabled = false;
      if (data.analysis) {
        displayThreadAnalysisResults(data.analysis);
        resultsDiv.style.display = "block";
      }
    },
    function (error) {
      analyzeBtn.disabled = false;
      resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    <strong>오류:</strong> ${error.message}
                </div>
            `;
      resultsDiv.style.display = "block";
    }
  );
}
```

### 3. AI 미팅 전략 (schedule_detail_modal.html 내 인라인)

```javascript
async function showMeetingStrategy(scheduleId) {
  await runAITaskWithDetails(
    "미팅 전략 생성",
    "/reporting/ai/meeting-strategy/",
    { schedule_id: scheduleId },
    async function () {
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      addAILog("🎯 미팅 전략 생성 시작", "info");
      addAILog("━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info");
      await sleep(300);
      addAILog("📅 일정 정보 수집 중...", "info");
      await sleep(300);
      addAILog("👤 고객 정보 분석 중...", "info");
      await sleep(300);
      addAILog("📊 과거 거래 이력 분석 중...", "info");
      await sleep(300);
      addAILog("🎯 맞춤 전략 생성 중...", "info");
    },
    function (data) {
      if (data.strategy) {
        displayMeetingStrategy(data.strategy);
      }
    },
    function (error) {
      showNotification("전략 생성 실패: " + error.message, "error");
    }
  );
}
```

---

## 로그 메시지 이모지 가이드

| 이모지 | 용도           |
| ------ | -------------- |
| 🎯     | 작업 시작/목표 |
| 🔍     | 분석/검색      |
| 📊     | 데이터/통계    |
| 📧     | 이메일 관련    |
| 📅     | 일정 관련      |
| 👤     | 고객/사용자    |
| 💰     | 금액/매출      |
| ⏰     | 시간/기한      |
| 🤖     | AI 처리        |
| ✨     | 생성/완료      |
| 💡     | 아이디어/제안  |
| 🌡️     | 온도/상태      |
| 🏷️     | 라벨/분류      |
| ✉️     | 메시지/초안    |
| ━      | 구분선         |

---

## 주의사항

1. **async/await 필수**: `detailsCallback`은 반드시 `async function`이어야 합니다.

2. **sleep 사용**: 로그 메시지 사이에 `await sleep(300)`을 넣어 사용자가 진행 상황을 볼 수 있게 합니다.

3. **버튼 비활성화**: 작업 시작 시 버튼을 `disabled = true`로, 완료/에러 시 `false`로 설정합니다.

4. **에러 처리**: `onError` 콜백에서 반드시 사용자에게 에러 메시지를 표시합니다.

5. **CSRF 토큰**: `runAITaskWithDetails`가 자동으로 처리하므로 별도 설정 불필요합니다.

---

## base.html 모달 HTML 구조 (참고용)

```html
<!-- AI 로딩 모달 -->
<div
  class="modal fade"
  id="aiLoadingModal"
  tabindex="-1"
  data-bs-backdrop="static"
>
  <div class="modal-dialog modal-dialog-centered">
    <div
      class="modal-content"
      style="border: none; box-shadow: 0 10px 40px rgba(0,0,0,0.2);"
    >
      <div
        class="modal-header"
        style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"
      >
        <h5 class="modal-title" id="aiLoadingTitle">
          <i class="fas fa-robot fa-spin me-2"></i>AI 분석 중
        </h5>
      </div>
      <div class="modal-body" style="padding: 2rem;">
        <p id="aiLoadingMessage" class="text-center mb-3">분석 중입니다...</p>
        <div class="progress" style="height: 30px; border-radius: 15px;">
          <div
            id="aiProgressBar"
            class="progress-bar progress-bar-striped progress-bar-animated"
            style="width: 0%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);"
          >
            0%
          </div>
        </div>
        <div
          id="aiLogContainer"
          class="mt-3"
          style="max-height: 200px; overflow-y: auto; font-family: monospace; 
                            background-color: #1a1a1a; color: #0f0; padding: 1rem; border-radius: 8px;"
        ></div>
      </div>
    </div>
  </div>
</div>
```

---

## 버전 히스토리

| 날짜       | 변경 내용                             |
| ---------- | ------------------------------------- |
| 2025-01-29 | 최초 작성 - AI 프로그레스 모달 가이드 |
