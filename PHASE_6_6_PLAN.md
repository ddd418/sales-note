# PHASE_6_6_PLAN.md

## 개요

Phase 7 QA 전 해결해야 할 실제 사용 이슈 4종 계획서.
모델 변경 필요 여부, 구현 순서, 보안 리스크 포함.

---

## 1. 대시보드 → 영업 노트 작성 모달 이슈 근본 원인 분석

### 1.1 현재 구조 파악

**모달 위치**

- `dashboard.html` 최하단 (`{% block content %}` 내부 마지막)
- ID: `dashboardNoteModal` (단일, 중복 없음)
- 트리거 버튼: 2곳 (`data-bs-toggle="modal" data-bs-target="#dashboardNoteModal"`)
- Bootstrap 5 `.modal.fade` 구조, 별도 `bootstrap.Modal.getInstance()` 사용

**base.html z-index 스택**
| 요소 | z-index |
|------|---------|
| `.sidebar` | 1000 |
| `.mobile-toggle` | 1001 |
| `.sidebar-overlay` | 999 |
| `.main-content` | **없음** (기존 z-index:1 제거됨) |
| Bootstrap 모달 backdrop | 1040 (Bootstrap 기본) |
| Bootstrap 모달 자체 | 1055 (Bootstrap 기본) |

### 1.2 실제 원인 분석

#### 원인 A: `overflow-x: hidden` → stacking context 생성 (최우선 의심)

```css
/* dashboard.html */
html,
body {
  overflow-x: hidden; /* ← 이 선언이 문제 */
  width: 100%;
  max-width: 100%;
}
```

- `html` 또는 `body`에 `overflow: hidden` / `overflow-x: hidden`이 설정되면
  일부 브라우저(Chrome, Safari)에서 `position: fixed` 요소의 containing block이
  `<html>` 또는 `<body>`로 고정되지 않고 해당 요소 자체가 됨
- 그 결과 Bootstrap backdrop(z-index: 1040)이 제대로 렌더링돼도,
  모달 요소가 `overflow: hidden` 컨테이너에 시각적으로 갇히거나
  배경 클릭이 차단됨
- **모달이 열리지만 배경 흐림(backdrop)이 표시되지 않거나,
  백드롭이 모달 위에 덮여 상호작용 불가 상태가 됨**

#### 원인 B: `.main-content` — overflow:hidden이 있는 자식 요소 내부에 모달 위치

```css
/* dashboard.html */
.card,
.stat-card,
.performance-card,
.chart-container {
  overflow: hidden; /* ← 카드에 overflow hidden */
}
```

- 모달이 `{% block content %}` 내에 위치하며, `main-content > div.container-fluid` 하위에 렌더링됨
- `overflow: hidden`인 ancestor가 `position: relative`이면 fixed child가 클리핑될 수 있음
- **단, Bootstrap 5는 모달을 `position: fixed`로 처리하므로 일반적으로는 클리핑되지 않음**
  → 예외: `transform`, `filter`, `perspective` 속성이 있는 조상 요소

#### 원인 C: CSS `transform`이 stacking context 생성 (확정적 위험)

```css
/* dashboard.html 카드 hover 효과 */
.stat-card:hover {
  transform: translateY(-6px); /* ← stacking context 생성 */
}
.performance-card:hover {
  transform: translateY(-4px);
}
```

- CSS `transform`이 적용된 요소는 `position: fixed` child의 containing block이 됨
- hover 상태에서 카드가 stacking context를 가지면, 그 안의 `position: fixed` 요소
  (Bootstrap 모달)가 의도와 다르게 동작할 수 있음
- **단, 모달은 hover 시점에 이미 열려 있으므로 동적 변경은 위험**

#### 원인 D: CSRF 토큰 조회 방식 (기능 이슈)

```javascript
const csrfToken =
  document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
  "{{ csrf_token }}";
```

- dashboard.html 에는 `{% csrf_token %}` 태그가 없음
- `document.querySelector('[name=csrfmiddlewaretoken]')` → `null`이 될 수 있음
- `|| '{{ csrf_token }}'` 폴백으로 처리되지만, 템플릿 렌더링 시 `{{ csrf_token }}`이
  올바르게 치환되는지 확인 필요
- base.html의 form (line 1800) 에 `{% csrf_token %}`이 있어 실제로는 작동하지만,
  모달 폼이 base.html 폼보다 나중에 DOM에 로드되면 문제될 수 있음

#### 원인 E: 모달 초기화 타이밍 — `bootstrap.Modal.getInstance()` 사용 오류 가능성

```javascript
var modal = bootstrap.Modal.getInstance(
  document.getElementById("dashboardNoteModal"),
);
if (modal) modal.hide();
```

- `getInstance`는 이미 초기화된 인스턴스만 반환, 없으면 `null`
- 저장 성공 후 `modal.hide()`가 `null`이면 모달이 닫히지 않음
- 이후 `location.reload()`로 강제 리로드되지만, 그 전에 backdrop이 남아있을 수 있음

### 1.3 권장 수정 방향

**금지 접근**: `global .modal-backdrop { display: none !important; }` 사용 금지
→ 다른 모달의 backdrop도 모두 제거되어 UX 파괴

**수정 1 (최우선)**: `html, body { overflow-x: hidden }` 제거 또는 대체

```css
/* 대체 방법: overflow-x를 html/body 대신 wrapper div에만 적용 */
.page-wrapper {
  overflow-x: hidden;
}
/* html, body는 overflow 속성 제거 */
```

**수정 2**: 모달을 `<body>` 직접 하위로 이동

```html
<!-- {% block content %} 외부 또는 base.html 내 body 닫기 태그 직전 -->
{% block modals %}{% endblock %}
```

→ dashboard.html에서 `{% block modals %}` 블록으로 모달을 `main-content` 외부에 배치

**수정 3**: CSRF 토큰 안전하게 처리

```html
<!-- 모달 내부 또는 기존 hidden form에 추가 -->
<input type="hidden" id="dashboard-csrf" value="{{ csrf_token }}" />
```

```javascript
const csrfToken =
  document.getElementById("dashboard-csrf")?.value ||
  document.querySelector('meta[name="csrf-token"]')?.content;
```

**수정 4**: `bootstrap.Modal.getInstance` 안전 처리

```javascript
let modal = bootstrap.Modal.getInstance(el);
if (!modal) modal = new bootstrap.Modal(el);
modal.hide();
```

**수정 5**: hover transform을 모달 요소 외부에서만 적용 (선택적)

```css
/* 카드가 hover 시 transform이 있어도 모달은 body 하위에 있으면 문제없음 */
/* 수정 2 적용 후 이 항목은 자동 해결됨 */
```

### 1.4 DB 변경 필요 여부

없음 — 순수 HTML/CSS/JS 수정

---

## 2. 파이프라인 자동/수동 계획

### 2.1 현재 파이프라인 구조

**모델**: `FollowUp.pipeline_stage`

- `CharField`, choices: potential / contact / quote / negotiation / won / lost
- 기본값: `potential`
- `FollowUp`은 고객/거래처 단위 레코드 (고객 1명 = FollowUp 1건 원칙)

**뷰**: `funnel_pipeline_view` (reporting/funnel_views.py:710)

- `FollowUp` 전체를 `pipeline_stage`별로 그룹핑
- 칸반 보드(`funnel/pipeline.html`)로 렌더링

**이동 API**: `funnel_pipeline_move` (funnel_views.py:762)

- `POST /reporting/funnel/api/pipeline-move/`
- `followup.pipeline_stage = new_stage; save(update_fields=['pipeline_stage'])`
- 권한: `can_access_user_data()` 확인 후 저장

**현재 자동화 없음**

- 어떤 이벤트(견적 제출, 수주, 실주 등)에서도 `pipeline_stage`를 자동 변경하는 코드 없음
- 사용자가 칸반 드래그 또는 드롭다운으로 수동 이동만 가능
- Schedule/History/Quote 생성 시 pipeline_stage는 변경되지 않음

**관련 모델 관계**

```
FollowUp ← pipeline_stage (수동)
  └── Schedule (related_name: 'schedules')
  └── History (related_name: 'histories')
  └── Quote (related_name: 'quotes')
```

### 2.2 자동화 연동 설계

**자동 이동 트리거 규칙** (추천)

| 이벤트                  | 현재 단계           | 자동 이동 대상 | 조건                                |
| ----------------------- | ------------------- | -------------- | ----------------------------------- |
| 견적(Quote) 생성        | potential / contact | → quote        | Quote 첫 생성 시                    |
| 수주(Quote.status=won)  | 모든 단계           | → won          | Quote.is_won=True 또는 status 변경  |
| 실주(Quote.status=lost) | 모든 단계           | → lost         | Quote.is_lost=True 또는 status 변경 |
| 미팅/방문 기록(History) | potential           | → contact      | action_type=customer_meeting/visit  |
| 협상 기록               | quote               | → negotiation  | action_type=negotiation (현재 없음) |

**수동 이동 보호 설계**

현재 문제: 자동화 도입 시 사용자가 수동으로 이동한 단계가 덮어씌워짐

**해결 방법 A**: `pipeline_stage_locked` 필드 추가 (DB 변경 필요)

```python
pipeline_stage_locked = models.BooleanField(
    default=False,
    verbose_name="파이프라인 단계 잠금",
    help_text="True이면 자동 동기화가 이 단계를 덮어쓰지 않음"
)
```

- 사용자가 수동으로 이동하면 `pipeline_stage_locked=True` 자동 설정
- 자동화 코드는 `pipeline_stage_locked=False`인 경우에만 단계 변경
- 관리자가 잠금 해제 가능

**해결 방법 B**: `pipeline_stage_source` 필드 추가 (DB 변경 필요)

```python
STAGE_SOURCE_CHOICES = [('auto', '자동'), ('manual', '수동')]
pipeline_stage_source = models.CharField(
    max_length=10, choices=STAGE_SOURCE_CHOICES, default='auto'
)
pipeline_stage_updated_at = models.DateTimeField(auto_now=True)
```

- 수동 이동: `source='manual'` 저장
- 자동 동기화: `source='manual'`이면 skip

**해결 방법 C**: DB 변경 없이 로직으로만 처리 (추천: 1차 구현)

- 자동 이동은 단방향(앞으로만): `potential → contact`, `contact → quote`
- 이미 더 진행된 단계(`quote`, `negotiation`, `won`, `lost`)는 자동 이동하지 않음
- 사용자가 단계를 낮추면(예: `won → contact`) 그 상태를 유지
- 규칙: `current_stage >= trigger_target_stage` → skip

### 2.3 자동 동기화 실행 시점

**옵션 A**: Signal 기반 (즉시 반영)

```python
# reporting/signals.py
@receiver(post_save, sender=Quote)
def sync_pipeline_on_quote(sender, instance, **kwargs):
    if instance.is_won:
        _try_advance_pipeline(instance.followup, 'won')
    elif instance.is_lost:
        _try_advance_pipeline(instance.followup, 'lost')
```

**옵션 B**: 뷰 레이어에서 명시적 호출 (추천: 예측 가능, 디버깅 쉬움)

```python
# Quote 생성/수정 뷰에서
if quote_created:
    advance_pipeline_stage(followup, 'quote', source='auto')
```

**옵션 C**: 관리자 수동 일괄 동기화 버튼 (가장 안전, 1차 구현)

- 분석 페이지 또는 파이프라인 보드 상단에 "파이프라인 동기화" 버튼
- 클릭 시 전체 FollowUp의 Quote/History 기반으로 단계 추천 계산
- 사용자가 확인 후 적용

### 2.4 DB 변경 필요 여부

| 방법                 | DB 변경    | 마이그레이션                              |
| -------------------- | ---------- | ----------------------------------------- |
| 방법 A (locked 필드) | 필요       | `pipeline_stage_locked BooleanField` 추가 |
| 방법 B (source 필드) | 필요       | 2개 필드 추가                             |
| 방법 C (로직만)      | **불필요** | 없음                                      |

**권장**: 1차 구현은 방법 C (로직 기반, DB 변경 없음), 2차에서 방법 A 도입

---

## 3. 주간보고 일정 불러오기 개선 계획

### 3.1 현재 일정 불러오기 동작

**API**: `weekly_report_load_schedules` (views.py)

- `GET /reporting/api/weekly-reports/schedules/?week_start=&week_end=`
- `Schedule.objects.filter(user=request.user, visit_date__range=(week_start, week_end))`
- 반환 필드: `date, customer, company, department, activity_type, notes`
- History(실제 활동 기록)는 반환하지 않음

**UI**: `form.html`

- 오른쪽 패널에 일정 목록 표시 (`schedulePanel`)
- 항목 클릭 → `insertScheduleText()` → `activityNotes` textarea에 한 줄 텍스트 삽입
- 삽입 형식: `- [m/d] 고객명 (업체명) — 활동유형: 메모`
- **분류 없음**: 견적/미팅/납품/활동 구분 없이 평탄하게 나열

**현재 문제**

1. 일정만 불러오고, 그 일정에 연결된 영업노트(History)는 불러오지 않음
2. 활동 유형 분류 없이 나열 → 관리자가 보기 어려움
3. 텍스트 삽입만 가능 → 자동 구조화 불가
4. 견적 제출, 납품 완료 등의 정보가 빠짐
5. `Schedule.notes`만 포함되고 `History.content`는 없음

### 3.2 일정 분류 기준

**Schedule.activity_type → 분류 매핑**

| activity_type 값   | 분류      | 주간보고 섹션  |
| ------------------ | --------- | -------------- |
| `customer_meeting` | 미팅      | 영업 활동 내용 |
| `visit`            | 방문      | 영업 활동 내용 |
| `call`             | 전화 상담 | 영업 활동 내용 |
| `email`            | 이메일    | 영업 활동 내용 |
| `demo`             | 데모      | 영업 활동 내용 |
| `quote_submission` | 견적 제출 | 견적/납품 내용 |
| `delivery`         | 납품      | 견적/납품 내용 |
| `follow_up`        | 후속조치  | 다음 주 계획   |
| `presentation`     | 발표/PT   | 영업 활동 내용 |
| (기타)             | 활동      | 영업 활동 내용 |

**연결된 History도 함께 불러오기**

```python
# 개선된 weekly_report_load_schedules
schedules = Schedule.objects.filter(
    user=request.user,
    visit_date__gte=week_start,
    visit_date__lte=week_end,
).select_related(
    'followup', 'followup__company', 'followup__department'
).prefetch_related(
    Prefetch('histories',  # HistoryとScheduleがリンクしている場合
             queryset=History.objects.filter(is_deleted=False).order_by('created_at'),
             to_attr='linked_histories')
).order_by('visit_date')
```

현재 History → Schedule 관계 확인 필요:

```python
# models.py
class History(models.Model):
    followup = models.ForeignKey(FollowUp, ...)
    schedule = models.ForeignKey(Schedule, null=True, blank=True, ...)
    # schedule FK 존재 여부에 따라 연결 방식 결정
```

### 3.3 개선 UI 설계

**현재**: 클릭 → 텍스트 삽입 (단순)

**개선안**: 체크박스 선택 후 "선택 항목 삽입" 버튼 클릭

```
┌──────────────────────────────────────────────────┐
│ 이번 주 일정 & 활동 기록                          │
├──────────────────────────────────────────────────┤
│ [분류: 영업활동]                                  │
│ ☐ 04/28(월) 한국대 이화연 — 고객 미팅           │
│    └ 영업노트: HPG 제품 설명 완료, 관심 보임      │
│ ☐ 04/30(수) 서울대 김철수 — 방문                │
│                                                  │
│ [분류: 견적/납품]                                 │
│ ☐ 04/29(화) 한양대 홍길동 — 견적 제출           │
│    └ 견적번호: Q-20250429-001 / 500만원          │
│ ☐ 04/30(수) 연세대 박연구 — 납품 완료           │
│                                                  │
│ [분류: 후속조치]                                  │
│ ☐ 04/28(월) 성균관대 이교수 — 팔로업            │
├──────────────────────────────────────────────────┤
│ [영업활동 섹션에 삽입] [견적/납품 섹션에 삽입]    │
└──────────────────────────────────────────────────┘
```

**자동 삽입 포맷 (관리자 가독성)**

```
[영업활동 내용에 삽입]
- 04/28(월): 한국대학교 이화연 교수 고객 미팅
  → HPG 제품 설명 완료, 관심 표명, 견적 요청
- 04/30(수): 서울대학교 김철수 교수 방문
  → [영업노트 없음]

[견적/납품 내용에 삽입]
- 04/29(화): 한양대학교 홍길동 교수 — 견적 제출 (견적 500만원)
- 04/30(수): 연세대학교 박연구 교수 — 납품 완료
```

### 3.4 API 개선 설계

```python
def weekly_report_load_schedules(request):
    # 기존: schedules + notes만 반환
    # 개선: schedules + linked histories + connected quotes 반환
    data = {
        'schedules': [],  # 기존 형식 유지
        'categorized': {
            'activity': [],    # 영업활동 섹션용
            'quote_delivery': [],  # 견적/납품 섹션용
            'followup': [],    # 후속조치 섹션용
        }
    }
```

### 3.5 DB 변경 필요 여부

- History에 `schedule` FK가 없으면: **마이그레이션 필요** (nullable ForeignKey 추가)
- History에 이미 `schedule` FK가 있으면: 변경 없음
- 현재 `History.followup` → FollowUp → Schedule 관계로 조회 가능 (FK 없어도 조회 가능)

**즉시 확인 필요**:

```python
# reporting/models.py의 History 모델에 schedule FK가 있는지 확인
```

---

## 4. 문서 관리 및 서류 생성 개선 계획

### 4.1 현재 구조

**서류 생성 흐름**

1. 일정 상세(`schedule_detail.html`) → "견적서 생성" / "거래명세서 생성" 버튼 클릭
2. `generateDocument(documentType, scheduleId, outputFormat)` JS 함수 실행
3. `POST /reporting/documents/generate/{type}/{schedule_id}/{format}/`
4. `generate_document_pdf` 뷰 실행:
   - Schedule → FollowUp에서 고객 정보 추출
   - DeliveryItem에서 품목 목록 추출
   - DocumentTemplate(회사별 활성 XLSX 템플릿) 로드
   - `{{변수명}}` 패턴을 실제 값으로 치환 (ZIP XML 레벨 직접 수정)
   - XLSX 파일 다운로드 반환

**지원 변수 목록** (data_map 기준)

```
년, 월, 일, 거래번호,
고객명, 업체명, 학교명, 부서명, 연구실, 담당자, 이메일, 연락처, 전화번호,
실무자, 영업담당자, 담당영업,
일정날짜, 날짜, 발행일,
회사명,
공급가액, 소계, 부가세액, 부가세, 총액, 합계, 총액한글, 한글금액,
품목N_이름, 품목N_품목명, 품목N_수량, 품목N_단위, 품목N_규격, 품목N_설명,
품목N_공급가액, 품목N_단가, 품목N_부가세액, 품목N_금액, 품목N_총액
```

**템플릿 파일 저장**: Cloudinary (프로덕션) 또는 로컬 파일 시스템 (로컬)

### 4.2 현재 불편 사항

**1. 변수 입력 UX 없음**

- 사용자가 XLSX 템플릿에 `{{변수명}}` 형식으로 직접 작성해야 함
- 어떤 변수명을 사용해야 하는지 알 수 없음
- 템플릿 업로드 후 실제 생성 전까지 변수 치환 결과 미리보기 불가

**2. 자동 채움 누락 데이터**

- `유효일+N일` 형식은 지원하지만, 사용자가 추가로 원하는 커스텀 날짜 계산 불가
- 고객 회사의 사업자등록번호, 대표자명, 주소 등 빠진 필드 있음 (FollowUp에 없음)
- Quote 연결 정보(견적 번호 등) 자동 채움 없음

**3. 서류 생성 버튼 접근성**

- schedule_detail.html 페이지에만 버튼 있음
- 거래처(FollowUp) 상세 페이지나 견적(Quote) 페이지에서는 접근 불가

**4. 에러 처리 중복**

```javascript
// schedule_detail.html:1906-1908 — alert이 두 번 호출됨
alert("서류 생성 실패: " + error.message);
// ...
alert("서류 생성 중 오류가 발생했습니다."); // 중복!
```

**5. Cloudinary 임시 파일 처리**

- 매번 `requests.get(url)` → 임시 파일 생성 → 처리 → 삭제
- 네트워크 의존성 높음, Railway 환경에서 타임아웃 가능

### 4.3 개선 방향

#### A. 변수 도움말 패널 추가 (템플릿 업로드 화면)

`document_template_create.html` / `document_template_edit.html` 개선:

- "사용 가능한 변수 목록" 토글 패널 추가
- 클릭하면 변수명이 클립보드에 복사
- 변수를 카테고리별로 표시 (기본정보 / 고객정보 / 품목정보 / 금액정보)

```html
<div class="collapse" id="varHelpPanel">
  <table class="table table-sm">
    <tr>
      <td><code>{{고객명}}</code></td>
      <td>고객 담당자명</td>
    </tr>
    <tr>
      <td><code>{{업체명}}</code></td>
      <td>거래처/학교명</td>
    </tr>
    <tr>
      <td><code>{{품목1_이름}}</code></td>
      <td>첫 번째 품목명</td>
    </tr>
    ...
  </table>
</div>
```

#### B. 미리보기 기능 추가

schedule_detail.html에 "미리보기" 버튼 추가:

- `GET /reporting/documents/preview/{type}/{schedule_id}/` 엔드포인트 신설
- XLSX를 직접 다운로드하지 않고, 치환될 주요 값을 JSON으로 반환
- 모달로 "이 값들이 채워집니다" 미리보기 표시

```json
{
  "preview": {
    "고객명": "이화연",
    "업체명": "한국대학교",
    "총액": "5,500,000",
    "품목1_이름": "HPG-1000",
    "품목1_수량": "2"
  },
  "missing_fields": ["사업자번호", "대표자명"]
}
```

#### C. 자동 채움 필드 확장

현재 누락된 자동 채움 필드 추가:

- `견적번호`: Schedule에 연결된 최근 Quote.quote_number
- `유효일`: 발행일 + N일 (이미 `{{유효일+30}}` 패턴 지원)
- `메모`: Schedule.notes

FollowUp 모델에 추가할 수 있는 필드 (optional):

- `business_registration_number`: 사업자등록번호
- `representative_name`: 대표자명
- `address`: 이미 있음

**DB 변경 판단**: 사업자등록번호, 대표자명 필드가 없으면 마이그레이션 필요.
현재 Company 모델 확인 후 결정.

#### D. 저장 프리셋 기능 (선택적)

- 자주 쓰는 품목 조합을 "프리셋"으로 저장
- 일정 생성 또는 서류 생성 시 프리셋 선택 → 품목 자동 채움
- DB 변경 필요: `DocumentPreset` 모델 신설

#### E. 에러 처리 버그 수정 (즉시 수정 가능)

```javascript
// 현재 (버그: alert 두 번)
alert("서류 생성 실패: " + error.message);
// ...
alert("서류 생성 중 오류가 발생했습니다.");

// 수정
console.error("서류 생성 오류:", error);
alert("서류 생성 실패: " + error.message);
// 두 번째 alert 제거
```

### 4.4 의존성 현황

| 의존성                 | 현재 상태       | 비고                   |
| ---------------------- | --------------- | ---------------------- |
| openpyxl               | 설치됨 (3.1.2)  | XLSX 생성용            |
| requests               | 설치됨          | Cloudinary 다운로드용  |
| python-docx            | 미설치          | DOCX 생성 필요 시 추가 |
| reportlab / weasyprint | 미설치          | PDF 생성 필요 시 추가  |
| Cloudinary             | 프로덕션 연결됨 | 파일 저장소            |

**현재 코드베이스는 XLSX 생성만 지원. PDF는 별도 의존성 필요.**

### 4.5 DB 변경 필요 여부

| 개선 항목                        | DB 변경  | 내용                     |
| -------------------------------- | -------- | ------------------------ |
| 변수 도움말 패널                 | 없음     | 순수 UI                  |
| 미리보기 기능                    | 없음     | 뷰/URL 추가만            |
| 자동 채움 필드 확장 (Quote 연결) | 없음     | 기존 FK로 조회           |
| 사업자등록번호/대표자명          | **필요** | Company 모델에 필드 추가 |
| 저장 프리셋                      | **필요** | DocumentPreset 신규 모델 |
| 에러 처리 버그 수정              | 없음     | JS 수정만                |

---

## 5. 권장 구현 순서

| 순서 | 작업                                | 우선순위 | DB 변경 | 예상 난이도 |
| ---- | ----------------------------------- | -------- | ------- | ----------- |
| 1    | 대시보드 모달 이슈 수정             | 긴급     | 없음    | 낮음        |
| 2    | 서류 생성 에러 처리 버그 수정       | 높음     | 없음    | 낮음        |
| 3    | 문서 템플릿 변수 도움말 패널        | 높음     | 없음    | 낮음        |
| 4    | 주간보고 일정 분류 + History 연결   | 높음     | 낮음\*  | 중간        |
| 5    | 파이프라인 자동화 (로직 기반 C방법) | 중간     | 없음    | 중간        |
| 6    | 서류 생성 미리보기 기능             | 중간     | 없음    | 중간        |
| 7    | 파이프라인 수동 보호 필드 (A방법)   | 낮음     | 필요    | 중간        |
| 8    | 저장 프리셋 기능                    | 낮음     | 필요    | 높음        |

_\* History에 schedule FK 없을 경우만 마이그레이션 필요_

---

## 6. 변경 예상 파일

### 즉시 수정 (모달 이슈)

- `reporting/templates/reporting/base.html` — `overflow-x: hidden` 처리
- `reporting/templates/reporting/dashboard.html` — 모달 위치 이동, CSRF 개선
- `reporting/templates/reporting/schedule_detail.html` — 에러 처리 alert 중복 제거

### 주간보고 개선

- `reporting/views.py` — `weekly_report_load_schedules` 개선
- `reporting/templates/reporting/weekly_report/form.html` — UI 개선 (분류 표시, 체크박스)

### 파이프라인 자동화

- `reporting/funnel_views.py` — `advance_pipeline_stage()` 헬퍼 추가
- `reporting/views.py` — Quote 저장 시 pipeline 연동 호출
- `reporting/templates/reporting/funnel/pipeline.html` — "파이프라인 동기화" 버튼 (선택적)

### 문서 관리

- `reporting/views.py` — `document_preview` 뷰 추가 (선택적)
- `reporting/urls.py` — preview URL 추가 (선택적)
- `reporting/templates/reporting/document_template_create.html` — 변수 도움말 패널
- `reporting/templates/reporting/document_template_edit.html` — 변수 도움말 패널

---

## 7. 보안 및 권한 리스크

| 항목                     | 리스크                             | 완화 방법                                                                              |
| ------------------------ | ---------------------------------- | -------------------------------------------------------------------------------------- |
| 모달 CSRF                | CSRF 토큰 `None`이 되는 엣지케이스 | `<meta name="csrf-token">` 폴백 사용 (base.html:7에 이미 있음)                         |
| 파이프라인 이동 API      | 타 사용자 FollowUp 이동 가능성     | `_get_accessible_followups()` 필터 이미 적용됨. 유지 필수                              |
| 서류 생성                | 타 회사 일정/템플릿 접근           | `can_access_user_data()` 이미 적용됨. 유지 필수                                        |
| Cloudinary 파일 다운로드 | 임시 파일 삭제 누락                | `tempfile.NamedTemporaryFile` delete=False 사용 중. `finally:` 블록에서 삭제 보장 필요 |
| 주간보고 History 조회    | 타 사용자 History 노출 가능성      | `user=request.user` 필터 유지 필수                                                     |
| 파이프라인 자동화 Signal | Signal 재귀 가능성                 | `update_fields=['pipeline_stage']` 명시, Signal 내에서 save() 호출 금지                |

**Cloudinary 임시 파일 미삭제 취약점** (현재 존재):

```python
# 현재 코드 (views.py ~12800)
with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
    tmp_file.write(response.content)
    template_file_path = tmp_file.name
# ← 예외 발생 시 tmp_file 미삭제
```

```python
# 수정 필요
import os
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    # ... 처리 ...
finally:
    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)
```

---

## 8. 검증 명령어

각 구현 단계 완료 후:

```powershell
# 1. Django 시스템 체크
C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py check

# 2. 스키마 변경 없음 확인 (DB 변경 없는 작업 완료 후)
C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py makemigrations --check --dry-run

# 3. 마이그레이션 필요 시
C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py makemigrations --name=<설명적 이름>
C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py migrate

# 4. 모달 동작 확인
# - /reporting/dashboard/ 접속
# - "영업 노트 작성" 버튼 클릭
# - Step 1 → 일정 선택 → Step 2 표시 확인
# - backdrop 정상 표시, 모달 클릭 가능 확인

# 5. 파이프라인 이동 확인
# - /reporting/funnel/pipeline/ 접속
# - 카드 드래그 앤 드롭 또는 드롭다운으로 단계 변경
# - DB 변경 확인: FollowUp.pipeline_stage 값 변경됨

# 6. 주간보고 일정 불러오기 확인
# - /reporting/weekly-reports/create/ 접속
# - "일정 불러오기" 클릭 → 분류별 표시 확인
# - 항목 선택 후 삽입 버튼 클릭 → 올바른 섹션에 삽입 확인

# 7. 서류 생성 확인
# - /reporting/schedule/{pk}/ 접속
# - "견적서 생성" 버튼 클릭 → XLSX 다운로드 확인
# - 에러 시 alert 한 번만 표시되는지 확인
```

---

## 부록: History 모델 schedule FK 확인

구현 전 아래 확인 필요:

```bash
C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe -c "
from reporting.models import History
import django
django.setup()
for f in History._meta.get_fields():
    print(f.name, type(f).__name__)
"
```

`schedule` 필드가 ForeignKey로 존재하면 → 주간보고 History 연결 직접 가능  
없으면 → `History.followup` → `FollowUp.schedules` 역참조로 연결 (별도 로직 필요)
