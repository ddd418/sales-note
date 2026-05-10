# AGENT_PLAN.md

## 프로젝트 개요

**세일즈 노트** — 한국 영업팀을 위한 내부 CRM/SFA 시스템 (Django 5.2.3)

이 시스템은 **공개 마케팅 사이트가 아닙니다**.  
제품 카탈로그, 브랜드 페이지, 공개 홈페이지는 이 프로젝트의 범위 밖입니다.

---

## Current task — React 선결제 상세/등록/수정 전환

**목표**: 기존 Django `/reporting/prepayment/*` 화면을 유지하면서 React CRM에서 선결제 상세 조회, 신규 등록, 기본 정보 수정을 처리할 수 있게 한다.

### 확인된 상태

- React `/prepayments/` 목록 화면과 `/reporting/api/prepayments/` 목록 API는 이미 배포되어 있다.
- 기존 Django 선결제 상세/등록/수정/삭제/이관 URL은 운영 fallback으로 유지해야 한다.
- 선결제 모델은 `Prepayment`와 `PrepaymentUsage`이며, 이번 작업에서 DB 필드 추가는 필요하지 않다.
- 기존 Django 수정 정책은 본인이 등록한 선결제만 수정 가능하고, 같은 회사 사용자의 선결제는 조회만 가능하다.

### 구현 계획

- `/reporting/api/prepayments/<id>/` 단건 조회 API를 추가한다.
  - 같은 회사/접근 가능 사용자 범위만 조회 허용.
  - 기본 정보, 금액 요약, 사용 내역, Django fallback 링크, 수정 가능 여부, 폼 옵션을 반환한다.
- `/reporting/api/prepayments/create/` 등록 API를 추가한다.
  - 기존 Django 등록과 동일하게 고객, 금액, 결제일, 결제방법, 입금자, 메모를 저장한다.
  - 초기 잔액은 입금액과 동일하게 설정한다.
  - 고객 선택 범위는 기존 회사/사용자 접근 범위를 유지한다.
- `/reporting/api/prepayments/<id>/update/` 수정 API를 추가한다.
  - 본인이 등록한 선결제만 수정 가능하게 유지한다.
  - 금액, 잔액, 결제일, 결제방법, 상태, 메모를 검증한다.
  - 사용 내역이 있는 선결제도 기존 Django처럼 기본 정보 수정은 허용하되, 잔액이 금액을 초과하지 않게 서버 검증한다.
- React 라우팅을 확장한다.
  - `/prepayments/new/`: React 선결제 등록 화면.
  - `/prepayments/<id>/`: React 선결제 상세 화면.
  - `/prepayments/<id>/edit/`: React 선결제 수정 화면.
  - 목록 행의 `상세`, `수정`, 상단 `선결제 등록`은 React 경로로 이동하고 Django 원본 링크는 별도 fallback으로 유지한다.
- 신규 migration은 만들지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentDetailApiTests reporting.tests.PrepaymentsSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1`
- `python -m py_compile reporting\views.py reporting\tests.py`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Previous task — React 선결제 목록 전환

**목표**: 기존 Django 선결제 관리 화면을 유지하면서 React CRM에 `/prepayments/` 읽기 전용 선결제 현황 화면을 추가한다.

### 확인된 상태

- Django 선결제 원본 화면은 `/reporting/prepayment/` 이하에서 동작한다.
- 일정 상세 React 편집 패널은 이미 `/reporting/api/prepayments/?customer_id=...&schedule_id=...`를 사용해 고객/일정별 선결제 선택 목록을 불러온다.
- React CRM 좌측 내비게이션에는 아직 선결제 현황 진입점이 없다.

### 구현 계획

- 기존 `/reporting/api/prepayments/` API를 확장한다.
  - `customer_id`가 있으면 기존 일정 편집용 응답을 그대로 유지한다.
  - `customer_id`가 없으면 React 선결제 목록용 요약/필터/목록 payload를 반환한다.
- 목록 API는 기존 Django 선결제 목록의 데이터 범위 규칙을 보존한다.
  - 기본값은 본인 등록 선결제.
  - `data_filter=all` 또는 `data_filter=user`는 기존 Django 화면과 같은 회사 사용자 기준으로 처리한다.
- React `/prepayments/` 화면을 추가한다.
  - 총 선결제 금액, 잔액, 사용 금액, 활성 건수 요약
  - 검색, 상태, 데이터 범위 필터
  - 선결제 행별 고객/부서/업체/입금자/금액/잔액/상태/담당자/원본 상세 링크
  - Django 선결제 등록/목록/엑셀 링크 유지
- 신규 DB 필드와 migration은 추가하지 않는다.

### 검증 계획

- `python manage.py test reporting.tests.PrepaymentsSummaryApiTests --verbosity=1`
- `python manage.py test reporting.tests.SchedulesSummaryApiTests.test_prepayment_api_list_includes_same_department_and_existing_usage --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `git diff --check`

---

## Current urgent task — Django 일정 캘린더 운영 진입점 복구

**목표**: React 통합 완료 전까지 기존 Django 일정 캘린더(`/reporting/schedules/calendar/`)를 운영자가 계속 가장 쉽게 사용할 수 있게 한다.

### 확인된 문제

- Django 일정 캘린더는 존재하지만 공통 사이드바의 `일정` 메뉴가 일정 목록(`/reporting/schedules/`)을 우선 열고 있다.
- 일정 캘린더가 실제 운영에서 가장 많이 쓰이는 화면이므로, 전환 기간에는 Django 메뉴의 일정 주 진입점을 캘린더로 유지해야 한다.

### 구현 계획

- Django 공통 사이드바의 `일정` 주 메뉴를 `schedule_calendar`로 변경한다.
- 상단 빠른 작업에도 `일정 캘린더` 링크를 노출한다.
- 일정 목록 화면에는 캘린더로 돌아가는 버튼을 추가해 목록과 캘린더를 같이 사용할 수 있게 한다.
- 일정 목록 URL과 기존 Django 기능은 유지하고, 인증/권한/DB 모델은 변경하지 않는다.
- 회귀 테스트로 인증된 사용자의 캘린더 접근과 Django 메뉴 링크를 검증한다.

---

## Previous urgent task — 고객 AI 분석 견적/납품 컨텍스트 누락 수정

**목표**: React 고객 상세(`/customers/<id>/`)에서 실행하는 부서 AI 분석이 실제 CRM의 견적/납품 기록을 빠짐없이 입력 컨텍스트로 사용하게 한다.

### 확인된 문제

- 기존 부서 AI 분석 수집 로직은 `Quote` 모델과 `History(action_type='delivery_schedule')` 위주로 견적/납품을 읽는다.
- 운영 데이터에는 견적/납품이 `Schedule(activity_type='quote'/'delivery')`와 `DeliveryItem(schedule=...)` 조합으로 저장되는 경우가 있다.
- 이 경우 고객 상세 AI 분석 프롬프트에 견적/납품 금액과 품목이 누락되어 GPT가 이미 나간 견적을 모르는 문제가 발생한다.

### 구현 계획

- `ai_chat.services.gather_quote_delivery_data()`를 확장해 다음 소스를 함께 수집한다.
  - `Quote` + `QuoteItem`
  - 견적 일정(`Schedule.activity_type='quote'`) + 일정 품목(`DeliveryItem.schedule`)
  - 견적 히스토리(`History.action_type='quote'`) + 히스토리 품목(`DeliveryItem.history`)
  - 납품 히스토리(`History.action_type='delivery_schedule'`) + 히스토리/일정 품목
  - 납품 일정(`Schedule.activity_type='delivery'`) + 일정 품목
- 이미 히스토리와 연결된 납품 일정은 중복 집계하지 않는다.
- 개별 고객 AI 분석(`gather_followup_data`)도 같은 수집 경로를 사용하게 맞춘다.
- DB 모델 변경 및 마이그레이션은 하지 않는다.
- 테스트는 일정 기반 견적/납품 품목이 AI 프롬프트에 포함되는지 검증한다.
- React 통합 완료 전까지 Django 기존 메뉴/페이지는 계속 접근 가능하게 유지한다. Django 사이드바의 고객/일정/영업노트/AI/파이프라인 메뉴는 Django URL을 가리키고, React CRM은 별도 진입 링크로 유지한다.

---

## Phase 0 — 보안 정리 및 잘못된 앱 제거 ✅ 완료

### 완료 내용

- ✅ `public_site` 앱 완전 제거 (디렉터리, INSTALLED_APPS, urls.py)
- ✅ 루트 URL `/` → `reporting:dashboard` 리디렉션
- ✅ `@csrf_exempt` 브라우저 AJAX 뷰 전체 제거
- ✅ `reporting/backup_api.py` — Bearer Token 인증 API는 @csrf_exempt 유지 (적절)

---

## Phase 1+2 — 대시보드 위젯 개선 + 영업보고 UX ✅ 완료

- ✅ 오늘 일정, 미검토 보고서, 지연 후속 조치 위젯
- ✅ `History` 모델: `next_action`, `next_action_date`, `reviewed_at`, `reviewer` 필드 추가
- ✅ 관리자 검토 완료 버튼 (AJAX 토글, `history_toggle_reviewed`)

---

## Phase 3 — 검색/필터/정렬 개선 ✅ 완료

- ✅ 거래처 목록: q, priority, grade, pipeline_stage, company, user 필터
- ✅ 영업보고 목록: 날짜 범위, 거래처, 담당자, 활동 유형 필터
- ✅ 일정 캘린더 뷰 (`/schedules/calendar/`)

---

## Phase 4 — 폼 UX 개선 ✅ 완료

- ✅ 다크모드 CSS 변수 (`var(--primary)`, `var(--surface)`) 전체 템플릿 적용
- ✅ 전역 JS `is-invalid` 클래스 자동 적용 (base.html)
- ✅ 한국어 에러 라벨 (`schedule_form.html`, `user_edit.html` 등)
- ✅ 필수 필드 `*` 빨간 표시 (user_edit.html)

---

## Phase 5 — 보안/개인정보 검토 ✅ 완료

- ✅ `SECRET_KEY` 하드코딩 fallback → RuntimeError
- ✅ 프로덕션 템플릿 `debug: True` 제거
- ✅ `ALLOWED_HOSTS` 와일드카드 `"*"` 제거 (개발환경)
- ✅ `validate_file_upload()` 단일 소스 — `.hwp/.hwpx` 추가, 인라인 코드 통일

---

## Phase 6 — 최종 QA 검토 ✅ 완료

- ✅ `manage.py check` → 0 이슈
- ✅ `manage.py test` → Ran 0 tests (스텁만 존재, 정상)
- ✅ `makemigrations --check` → No changes
- ✅ `collectstatic` → 완료
- 잔여 이슈 7개 기록 (아래 Phase 7에서 해결 예정)

---

## 1. 현재 Django 앱 구조

| 앱          | 설명                                           | 마운트 경로    |
| ----------- | ---------------------------------------------- | -------------- |
| `reporting` | 핵심 CRM 앱 — 영업보고, 거래처, 일정, 히스토리 | `/reporting/*` |
| `todos`     | 할 일 관리                                     | `/todos/*`     |
| `ai_chat`   | AI 채팅 및 분석                                | `/ai/*`        |

**제거된 앱**: `public_site` — Phase 0에서 완전 제거 (INSTALLED_APPS, urls.py, 디렉터리)

---

## 2. 기존 /reporting/\* CRM 기능

### FollowUp (고객/거래처)

- 고객 목록, 상세, 생성, 수정, 삭제
- 고객별 영업 히스토리 연결
- 우선순위, 단계, 등급, AI 점수 관리
- Excel 다운로드

### History (영업보고/활동)

- 영업보고 목록, 상세, 생성, 수정, 삭제
- 매니저 검토 (`reviewed_at`, `reviewer`) 기능
- 구조화된 회의 메모 (상황, 견적, 사실, 장애물, 다음 액션)
- 파일 첨부 (HistoryFile)
- 다음 액션/다음 연락일 필드

### Schedule (일정)

- 일정 목록, 달력, 상세, 생성, 수정, 삭제
- 활동 유형: 방문/통화/이메일/미팅/견적/납품/서비스
- 납품 항목 (DeliveryItem) 관리
- 파일 첨부 (ScheduleFile)

### Company/Department (고객사/부서)

- 고객사 목록, 상세, 생성, 수정
- 부서/연구실 관리
- 메모 기능

### Opportunity/Funnel (영업기회)

- 기회 목록, 상세 조회
- FunnelStage: lead→contact→quote→closing→won→quote_lost→excluded
- ⚠️ 생성/수정 프론트엔드 없음 (admin 전용)

### Quote (견적)

- Quote 모델 존재 (quote_number, stage, amounts)
- 8개 단계: draft→sent→review→negotiation→approved→rejected→expired→converted
- ⚠️ 독립 CRUD 뷰 없음 (API 전용)

### 기타

- 선결제(Prepayment) 관리
- 제품(Product) 목록
- 주간보고(WeeklyReport)
- 문서 템플릿 (PDF 변환 포함)
- Gmail OAuth2 / IMAP 이메일 통합
- 관리자 대시보드, 매니저 대시보드
- AI 고객 등급 분석

---

## 3. 현재 URL 동작

```
/ → reporting:dashboard (미인증 시 /reporting/login/ 리디렉션)
```

| 경로                             | 뷰                      | 역할            |
| -------------------------------- | ----------------------- | --------------- |
| `/reporting/login/`              | CustomLoginView         | 로그인          |
| `/reporting/dashboard/`          | dashboard_view          | 메인 대시보드   |
| `/reporting/followups/`          | followup_list_view      | 거래처 목록     |
| `/reporting/followups/<pk>/`     | followup_detail_view    | 거래처 상세     |
| `/reporting/followups/create/`   | followup_create_view    | 거래처 등록     |
| `/reporting/histories/`          | history_list_view       | 영업보고 목록   |
| `/reporting/histories/<pk>/`     | history_detail_view     | 영업보고 상세   |
| `/reporting/schedules/`          | schedule_list_view      | 일정 목록       |
| `/reporting/schedules/calendar/` | schedule_calendar_view  | 캘린더 뷰       |
| `/reporting/opportunities/`      | opportunity_list_view   | 영업기회 목록   |
| `/reporting/opportunities/<pk>/` | opportunity_detail_view | 영업기회 상세   |
| `/reporting/companies/`          | company_list_view       | 고객사 목록     |
| `/reporting/manager/`            | manager_dashboard       | 관리자 대시보드 |

---

## 4. public_site 영향도

**현황**: ✅ 완전 제거됨 (Phase 0 완료)

- `public_site` 디렉터리 없음
- INSTALLED_APPS에 없음
- `sales_project/urls.py`에서 제거됨
- 루트 `/`는 `reporting:dashboard`로 리디렉션

**영향**: 없음

---

## 5. 기존 모델 및 폼

### 핵심 모델

| 모델                  | 주요 필드                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------------------------- |
| `UserProfile`         | role(admin/manager/salesman), company(FK), can_download_excel                                                 |
| `Company`             | name, created_by, created_at                                                                                  |
| `Department`          | company(FK), name, category(FK)                                                                               |
| `FollowUp`            | user, company, department, customer_name, manager, status, priority, pipeline_stage, customer_grade, ai_score |
| `Schedule`            | followup(FK), visit_date, activity_type, status, expected_revenue                                             |
| `History`             | followup(FK), schedule(FK), action_type, content, next_action, next_action_date, reviewed_at, reviewer        |
| `HistoryFile`         | history(FK), file, original_filename, file_size                                                               |
| `Quote`               | followup(FK), quote_number, stage, subtotal, discount_rate, tax_amount, total_amount                          |
| `QuoteItem`           | quote(FK), product(FK), quantity, unit_price, discount_rate, subtotal                                         |
| `OpportunityTracking` | followup(FK), current_stage, backlog_amount, probability, expected_close_date                                 |
| `FunnelStage`         | name, order, color                                                                                            |
| `Prepayment`          | company(FK?), amount, remaining, created_date                                                                 |
| `Product`             | product_code, name, unit, standard_price, is_active                                                           |

### 폼 클래스 (views.py 내)

- `FollowUpForm` — 거래처 생성/수정, `clean_company()` + `clean_department()` 서버 검증
- `HistoryForm` — 영업보고 생성/수정
- `ScheduleForm` — 일정 생성/수정
- `CompanyForm` — 고객사 생성/수정
- `UserEditForm` — 사용자 수정

---

## 6. 기존 영업노트/보고 워크플로우

### 영업보고 작성 흐름

1. 사용자 로그인 → 대시보드
2. 거래처(FollowUp) 선택 또는 일정(Schedule)에서 바로 보고 작성
3. History 생성: 활동 유형, 내용, 결과, 다음 액션, 다음 연락일 입력
4. 파일 첨부 가능 (10MB 이하, `.pdf/.doc/.xls/.hwp/.hwpx` 등 14종)
5. 매니저가 `history_toggle_reviewed`로 검토 완료 표시 (POST, admin/manager 전용)

### 거래처 관리 흐름

1. `/reporting/followups/` 목록에서 검색/필터
2. 상세 페이지: 고객 정보 + 관련 Schedule + History 목록
3. 빠른 새 보고 작성 버튼

---

## 7. 기존 대시보드/목록/상세/생성/수정 페이지

| 페이지             | 템플릿                  | 상태                                              |
| ------------------ | ----------------------- | ------------------------------------------------- |
| 메인 대시보드      | dashboard.html          | ✅ 완비 (역할별 필터링, 통계 카드, 모바일 반응형) |
| 매니저 대시보드    | manager_dashboard.html  | ✅ 완비                                           |
| 거래처 목록        | followup_list.html      | ✅ 완비 (검색+필터+empty-state)                   |
| 거래처 상세        | followup_detail.html    | ✅ 완비                                           |
| 거래처 생성/수정   | followup_form.html      | ✅ 완비                                           |
| 영업보고 목록      | history_list.html       | ⚠️ empty-state 없음                               |
| 영업보고 상세      | history_detail.html     | ✅ 완비                                           |
| 영업보고 작성      | history_form.html       | ✅ 완비                                           |
| 일정 목록          | schedule_list.html      | ⚠️ empty-state 없음                               |
| 일정 달력          | schedule_calendar.html  | ✅ 완비                                           |
| 일정 생성/수정     | schedule_form.html      | ✅ 완비                                           |
| 영업기회 목록      | opportunity_list.html   | ✅ 완비                                           |
| 영업기회 상세      | opportunity_detail.html | ✅ 완비                                           |
| 영업기회 생성/수정 | (없음)                  | ❌ 미구현                                         |
| 고객사 목록        | company_list.html       | ✅ 완비                                           |
| 로그인             | login.html              | ✅ 완비                                           |

---

## 8. 현재 인증/권한 동작

### 인증

- Django `LoginView` 서브클래스 (`CustomLoginView`)
- 모든 내부 뷰: `@login_required` 적용 (100+ 뷰)
- 미인증 접근: `/reporting/login/?next=...` 리디렉션
- 세션 쿠키: 프로덕션에서 `SESSION_COOKIE_SECURE=True`

### 권한 체계

| 역할       | 접근 범위                                              |
| ---------- | ------------------------------------------------------ |
| `admin`    | 전체 — 모든 사용자 데이터, 설정, 사용자 관리           |
| `manager`  | 팀 — 같은 회사 팀원 데이터, 매니저 대시보드, 검토 기능 |
| `salesman` | 본인 — 본인이 작성한 보고서와 담당 거래처              |

### 권한 헬퍼

| 함수                                  | 역할                                 |
| ------------------------------------- | ------------------------------------ |
| `role_required(roles)`                | 뷰 데코레이터 — 역할 기반 접근 제어  |
| `can_access_user_data(user, target)`  | 소속 회사 기반 데이터 접근 허용 여부 |
| `can_modify_user_data(user, target)`  | 수정/삭제 권한                       |
| `can_access_followup(user, followup)` | 거래처 접근 권한                     |
| `can_excel_download(user)`            | Excel 다운로드 권한                  |

### 보안 현황 (Phase 5 완료)

- `SECRET_KEY` 하드코딩 제거 → RuntimeError
- 프로덕션 템플릿 `debug:True` 제거
- `ALLOWED_HOSTS` 와일드카드 제거
- `validate_file_upload()` 단일 소스 (`.hwp/.hwpx` 포함)
- `subprocess.run()`: `shell=False`, 사용자 입력 없음
- CSRF: 미들웨어 전체 적용, `@csrf_exempt` 없음

---

## 9. 권장 다음 단계 — Phase 7

> **주의**: 이 시스템은 내부 영업관리 시스템입니다.  
> 제품 카탈로그, 브랜드 상세, 공개 페이지는 추가하지 않습니다.

### Phase 7C — 잔여 이슈 정리 (빠른 작업, 먼저 권장)

- [ ] `history_list.html` — `{% empty %}` + `.empty-state-card` 추가
- [ ] `schedule_list.html` — `{% empty %}` + `.empty-state-card` 추가
- [ ] `railway.toml` startCommand에서 `fix_quote_770.py`, `reset_ai_chat_tables.py` 제거 또는 one-time job 분리
- [ ] `css/dist/styles.css` 중복 경고 해결 (STATICFILES_DIRS 경로 정리)

### Phase 7A — 영업기회 CRUD 프론트엔드 구현

**목표**: 영업담당자가 Django admin 없이도 영업기회를 생성/수정할 수 있게 한다.

**작업 목록**:

- [ ] `OpportunityForm` 폼 클래스 작성 (views.py 내)
- [ ] `opportunity_create_view` 구현
- [ ] `opportunity_edit_view` 구현
- [ ] 템플릿 `opportunity_form.html` 작성 (다크모드 CSS 변수 적용)
- [ ] `reporting/urls.py`에 create/edit URL 추가
- [ ] `followup_detail.html` — "영업기회 추가" 버튼 연결
- [ ] `opportunity_detail.html` — "편집" 버튼 추가

**폼 필드 (OpportunityTracking)**:

| 필드                | 설명                 | 필수 |
| ------------------- | -------------------- | ---- |
| followup            | 거래처 연결 (FK)     | ✅   |
| current_stage       | FunnelStage 선택     | ✅   |
| backlog_amount      | 예상 금액 (원)       | -    |
| probability         | 수주 가능성 (%)      | -    |
| expected_close_date | 예상 계약일          | -    |
| product             | 연결 제품 (optional) | -    |
| quote               | 연결 견적 (optional) | -    |

**추가 URL**:

```
opportunities/create/          → opportunity_create_view
opportunities/<pk>/edit/       → opportunity_edit_view
```

**DB 변경**: 없음 (`OpportunityTracking` 모델 이미 존재)

### Phase 7B — 기본 자동화 테스트 작성

**목표**: CI 안전망 확보 (현재 `Ran 0 tests`)

**작업 목록**:

- [ ] `reporting/tests.py`:
  - 로그인/로그아웃 smoke test
  - 미인증 시 login 리디렉션 확인
  - `followup_list_view` 200 응답 확인
  - `followup_create` POST 성공 케이스
  - `validate_file_upload()` 단위 테스트 (허용/차단 확장자)
  - 권한 없는 사용자 접근 차단 (salesman→admin 전용 뷰)

---

## 10. 변경 예정 파일

### Phase 7C

| 파일                                               | 변경 | 내용                 |
| -------------------------------------------------- | ---- | -------------------- |
| `reporting/templates/reporting/history_list.html`  | 수정 | empty-state 추가     |
| `reporting/templates/reporting/schedule_list.html` | 수정 | empty-state 추가     |
| `railway.toml`                                     | 수정 | 일회성 스크립트 제거 |

### Phase 7A

| 파일                                                    | 변경 | 내용                                   |
| ------------------------------------------------------- | ---- | -------------------------------------- |
| `reporting/views.py`                                    | 수정 | `OpportunityForm`, create/edit 뷰 추가 |
| `reporting/urls.py`                                     | 수정 | create/edit URL 패턴 추가              |
| `reporting/templates/reporting/opportunity_form.html`   | 신규 | 생성/수정 폼 템플릿                    |
| `reporting/templates/reporting/followup_detail.html`    | 수정 | "영업기회 추가" 버튼                   |
| `reporting/templates/reporting/opportunity_detail.html` | 수정 | "편집" 버튼                            |

### Phase 7B

| 파일                 | 변경 | 내용            |
| -------------------- | ---- | --------------- |
| `reporting/tests.py` | 수정 | smoke test 추가 |

---

## 11. 검증 명령어

```bash
# 기본 체크
python manage.py check
python manage.py makemigrations --check --dry-run

# 테스트 (Phase 7B 이후)
python manage.py test

# 정적 파일
python manage.py collectstatic --noinput

# 배포 사전 체크
python pre_deployment_check.py
```

---

## 완료된 Phase 이력

| Phase     | 내용                                              | 날짜       |
| --------- | ------------------------------------------------- | ---------- |
| Phase 0   | 보안 정리 — public_site 제거, @csrf_exempt 제거   | 2026-04-25 |
| Phase 1+2 | 대시보드 위젯 개선 + 영업보고 UX                  | 2026-04-25 |
| Phase 3   | 검색/필터/정렬 개선                               | 2026-04-25 |
| Phase 4   | 폼 UX 개선 — 다크모드, 한국어 에러 라벨           | 2026-04-25 |
| Phase 5   | 보안/개인정보 검토 — SECRET_KEY, 파일 업로드 통일 | 2026-04-25 |
| Phase 6   | 최종 QA 검토                                      | 2026-04-25 |

---

## 기술 스택

| 항목      | 값                                                       |
| --------- | -------------------------------------------------------- |
| Framework | Django 5.2.3                                             |
| DB (prod) | PostgreSQL (Railway)                                     |
| DB (dev)  | SQLite                                                   |
| CSS       | Bootstrap 5.3.0 (CDN), Font Awesome 6.4.0                |
| 다크모드  | CSS 변수 (`var(--primary)`, `var(--surface)` 등)         |
| Async     | Celery + Redis                                           |
| Media     | Cloudinary (prod) / FileSystem (dev)                     |
| Email     | Gmail OAuth2 + IMAP/SMTP (Fernet 암호화)                 |
| AI        | OpenAI GPT                                               |
| Deploy    | Railway (nixpacks.toml, gunicorn)                        |
| Python    | `C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe` |

---

## 현재 단계

**Phase 6.5-1 완료** (2026-04-27)

### Phase 6.5-1 — 모달 클릭/입력 버그 수정

**목표**: Bootstrap 중첩 모달 및 stacking context 문제로 인한 입력 불가/모달 소멸 문제 해결.

**작업 범위**:

- 캘린더 일정 상세 모달의 고객 활동 기록: 중첩 Bootstrap Modal 제거, Offcanvas/인라인 패널 방식 사용
- 캘린더 일정 상세 모달의 부서 메모: 일정 상세 모달을 유지한 상태로 메모 입력 가능하게 처리
- 대시보드 영업노트 작성 모달: backdrop/z-index/focus 문제로 필드 클릭이 막히지 않게 처리

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DepartmentMemo` 모델과 API를 그대로 사용.

**검증 계획**:

- `python manage.py check` — 완료
- `python manage.py makemigrations --check --dry-run` — 완료, 변경 없음
- `python manage.py test` — 완료, 9개 통과
- 템플릿 정적 점검 — 완료: 중첩 모달 제거, 중복 ID 없음, 전역 backdrop 숨김 없음, CSRF 제출 유지
- Playwright 브라우저 점검 — 완료: 캘린더 일정 모달 유지 상태에서 부서 메모/고객 활동기록 Offcanvas 입력 및 닫기 가능, 대시보드 영업노트 모달 필드 입력 가능

---

**다음 권장 단계**: Phase 7 계획 재개

권장 실행 순서: Phase 7C (빠른 정리) → Phase 7A (영업기회 CRUD) → Phase 7B (테스트)

---

## Phase 10 — 서버 응답 속도 개선 1차

**목표**: 모델 변경 없이 현재 주요 화면의 반복 쿼리를 줄여 개발/운영 서버 응답 시간을 안정화한다.

**작업 범위**:

- `/ai/` 부서 선택 허브의 부서별 팔로우업 조회 N+1 제거
- `/reporting/followups/` 업체 필터 목록의 업체별 팔로우업 카운트 N+1 제거
- `/reporting/dashboard/` 반복 집계 일부를 날짜/월 단위 grouped query로 축소

**DB 변경 필요 여부**: 없음. 이번 단계는 view/query 최적화만 수행하며 migration은 만들지 않는다.

**검증 계획**:

- 최적화 전후 URL별 응답 시간/쿼리 수 비교: `/ai/`, `/reporting/followups/`, `/reporting/dashboard/`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test ai_chat`
- `python manage.py test reporting`
- `python manage.py test`
- `git diff --check`

**2차 추가 범위**:

- 대시보드 월간/연간 일정 카운트를 `aggregate()` 결과로 재사용
- 대시보드 선결제 통계를 단일 aggregate로 축소
- 오늘/이번 주 일정 목록은 리스트 평가 결과 길이를 사용해 추가 count 제거
- 고객사별 매출 분포의 전체 합계를 별도 aggregate 없이 기존 grouped query 결과에서 계산

---

## Phase 11 — 주요 CRM 조회 경로 DB 인덱스 추가

**목표**: Phase 10에서 남은 체감 지연 가능 구간을 줄이기 위해 대시보드, 팔로우업, AI 부서 허브에서 반복적으로 사용하는 필터 조합에 복합 인덱스를 추가한다.

**작업 범위**:

- `Schedule`: 사용자/방문일/상태/활동유형 기반 대시보드 집계와 오늘·이번 주 일정 조회 최적화
- `History`: 사용자/작성일/활동유형/다음 액션 기반 최근 활동, 지연 후속, 팀 활동 조회 최적화
- `FollowUp`: 사용자/생성일/파이프라인/부서 기반 고객 목록, 대시보드, AI 부서 허브 조회 최적화
- `Prepayment`: 등록자/결제일/상태 기반 선결제 월간·요약 조회 최적화
- `PersonalSchedule`: 사용자/일정일/시간 기반 대시보드 개인 일정 조회 최적화

**DB 변경 필요 여부**: 있음. 신규 필드 없이 `models.Index`만 추가하며 migration을 생성한다.

**검증 계획**:

- `python manage.py makemigrations --check --dry-run`로 migration 상태 확인
- `python manage.py migrate --plan`으로 적용 계획 확인
- `python manage.py check`
- `python manage.py test reporting`
- `python manage.py test`
- 주요 URL 쿼리 수 재측정: `/reporting/dashboard/`, `/reporting/followups/`, `/ai/`
- `git diff --check`

**추가 확인된 병목**:

- `/reporting/dashboard/` 첫 요청 지연은 쿼리 수가 아니라 URL resolver가 `ai_chat.services`, Gmail/IMAP view 모듈을 한꺼번에 import하는 cold start 비용이 큼.
- `ai_chat.services`는 OpenAI 관련 의존성을 포함하므로 `/reporting/dashboard/` 요청에서는 즉시 필요하지 않음.
- Gmail/IMAP view는 대시보드 요청과 무관하므로 URL 매칭 시점까지 lazy import로 늦춘다.

**추가 작업 범위**:

- `ai_chat.views`: AI 분석 실행 함수에서만 `ai_chat.services`를 import하도록 변경
- `reporting.urls`: Gmail/IMAP view callable을 lazy wrapper로 연결해 대시보드 cold start import 비용 축소

---

## Hotfix — 영업기회 목록 기본 데이터 범위 제한

**목표**: `/reporting/opportunities/`에서 기본 목록은 현재 로그인 사용자 담당 영업기회만 보여주고, 같은 회사 직원의 영업기회는 사용자가 담당자를 명시 선택했을 때만 보여준다.

**작업 범위**:

- `opportunity_list_view` 기본 필터를 접근 가능 사용자 전체가 아니라 `request.user`로 변경
- 같은 회사/접근 가능 사용자 선택 드롭다운 제공
- `data_filter=all` 우회 요청도 영업기회 목록에서는 기본 `me`로 처리
- 단계/마감/페이지네이션 링크가 선택된 데이터 범위를 유지하도록 수정
- 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. view/template/test 변경만 수행한다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.OpportunityListDataScopeTests`
- `python manage.py test`
- `git diff --check`

---

## Hotfix — 별도 영업기회 화면 제거 및 상단 파이프라인 진입점 정리

**목표**: 최종 영업 흐름을 `/reporting/funnel/` 파이프라인 화면으로 단일화하고, 별도 `/reporting/opportunities/` 화면과 관련 UI를 제거한다.

**작업 범위**:

- `/reporting/opportunities/` 및 하위 생성/상세/수정 URL 제거
- 영업기회 전용 view/form/template 제거
- 상단 quick action의 `견적` 버튼을 `/reporting/funnel/`로 이동하는 `파이프라인` 버튼으로 변경
- 팔로우업 상세의 영업기회 생성/상세/수정 링크를 제거하고 파이프라인 목록 안내로 대체
- `/reporting/opportunities/` 제거와 상단 파이프라인 링크 회귀 테스트 추가/수정

**DB 변경 필요 여부**: 없음. `OpportunityTracking` 데이터/모델은 파이프라인 및 기존 자동 동기화에서 사용할 수 있으므로 삭제하지 않는다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests`
- `python manage.py test`
- `git diff --check`

---

## Frontend Pilot — React 파이프라인 Command Center 시안

**목표**: Django template의 디자인 자유도 한계를 줄이기 위해 별도 `/frontend` Vite React 파일럿을 만들고, `/reporting/funnel/` 대체 후보가 될 파이프라인 Command Center mock 화면을 구현한다.

**작업 범위**:

- `/frontend` 독립 Vite + React + TypeScript 프로젝트 생성
- Django API 연결 전 mock data 기반 파이프라인 화면 구현
- 좌측 CRM 내비게이션, 상단 검색/액션, KPI strip, 파이프라인 board/list 전환, 고객 상세 패널 구성
- 내부 CRM 업무툴 기준의 밝고 정돈된 디자인 시스템 적용
- 기존 Django 라우트/DB/권한/모델은 변경하지 않음

**DB 변경 필요 여부**: 없음. 이번 단계는 프론트 시안 프로젝트만 추가한다.

**검증 계획**:

- `npm install`
- `npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Prepayment Editing — 일정 선결제 입력 전환

**목표**: React `/schedules/<id>/` 일정 상세 수정 패널에서 납품 일정의 선결제 선택과 차감 금액을 저장하게 만들어 Django 일정 수정 폼 왕복을 줄인다.

**시간 단위 진행 루트**:

- 0~1시간: 기존 `Schedule`, `Prepayment`, `PrepaymentUsage` 모델과 Django 일정 생성/수정 폼의 선결제 복원/차감 흐름을 확인한다.
- 1~2시간: 작업 범위, DB 변경 여부, 검증 계획을 `AGENT_PLAN.md`에 기록한다.
- 2~4시간: 일정 상세/수정 API에 선결제 사용 여부, 선택 목록, 잔액 검증, 기존 사용분 복원 후 재차감 로직을 추가한다.
- 4~6시간: React 일정 상세 수정 패널에 선결제 사용 체크, 선택 가능한 선결제 목록, 차감 금액 입력, 합계 표시를 연결한다.
- 6~7시간: Django API 테스트, React build, Django check, migration check, diff check를 실행한다.
- 7~8시간: `AGENT_REPORT.md`를 갱신하고 커밋/푸시 후 Railway `web`과 `sales-note-frontend` 운영 배포 및 번들/API 보호 상태를 확인한다.

**작업 범위**:

- `/reporting/api/prepayments/` 응답에 React 편집에 필요한 기존 선택 금액과 사용 가능 잔액을 추가한다.
- `/reporting/api/schedules/<id>/` 상세 API에 선결제 사용 내역과 선결제 목록 URL을 제공한다.
- `/reporting/api/schedules/<id>/update/`가 `usePrepayment`, `prepayments` payload를 받아 기존 사용분을 복원한 뒤 선택 금액을 재차감한다.
- 선결제는 기존 정책대로 납품 일정에서만 사용하고, 같은 부서 고객의 활성 선결제 및 현재 일정에서 이미 사용 중인 선결제만 선택 가능하게 한다.
- React 수정 패널은 선결제 사용 체크박스, 선택 목록, 금액 입력, 납품 합계 대비 차감/실결제 금액을 표시한다.
- 기존 Django 선결제 목록/상세/일정 수정 화면과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `Prepayment`, `PrepaymentUsage`, `DeliveryItem` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Department AI Analysis — 고객 상세 부서 AI 분석 연결

**목표**: React `/customers/<id>/` 고객 상세 화면에서 해당 고객의 부서 AI 분석 상태를 확인하고, 권한이 있는 사용자는 고객 화면에서 바로 분석을 실행하거나 결과 화면으로 이동할 수 있게 한다.

**시간 단위 진행 루트**:

- 0~1시간: 기존 고객 상세 API/UI와 `ai_chat` 부서 분석 조회/실행 URL을 확인한다.
- 1~2시간: 작업 범위, DB 변경 여부, 검증 계획을 `AGENT_PLAN.md`에 기록한다.
- 2~4시간: 고객 상세 API에 부서 AI 분석 가능 여부, 분석 요약, 실행 URL, 결과 URL을 추가한다.
- 4~6시간: React 고객 상세 사이드 영역에 부서 AI 분석 카드, 실행 버튼, 결과 이동 링크, 실행 상태 메시지를 추가한다.
- 6~7시간: 고객 상세 API 테스트, React build, Django check, migration check, diff check를 실행한다.
- 7~8시간: `AGENT_REPORT.md`를 갱신하고 커밋/푸시 후 Railway `web`과 `sales-note-frontend` 운영 배포 및 번들/API 보호 상태를 확인한다.

**작업 범위**:

- 기존 `ai_chat:department_analysis`, `ai_chat:run_analysis`, `ai_chat:department_list` URL을 재사용한다.
- 고객 상세 API가 고객의 `department` 기준으로 AI 분석 상태와 링크를 내려준다.
- 기존 AI 권한 정책을 유지해 `can_use_ai` 권한이 없거나 해당 부서에 본인 담당 고객이 없는 사용자는 실행 버튼을 비활성화한다.
- React 고객 상세에 부서명, 분석 여부, 최근 요약, 미팅/견적/납품/PainPoint 카운트, 분석 실행/결과 보기 액션을 표시한다.
- 기존 Django AI 분석 화면, 고객 상세 화면, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `Department`, `AIDepartmentAnalysis`, `PainPointCard` 모델만 조회/사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 읽기 API 연결

**목표**: React 파일럿이 mock data만 사용하는 상태에서 벗어나, 기존 Django 권한 정책을 타는 읽기 전용 파이프라인 API를 우선 조회하도록 연결한다.

**작업 범위**:

- `/reporting/api/pipeline/` GET API 추가
- `funnel_views._get_accessible_followups()`를 재사용해 현재 사용자 권한 범위만 반환
- API 응답에 stages, deals, metrics, priorityTasks 포함
- Vite dev server에서 `/reporting/*` 요청을 Django `127.0.0.1:8000`으로 proxy
- React 파일럿은 API 성공 시 실제 데이터, 실패/미로그인/서버 미실행 시 mock fallback 사용
- API 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. 읽기 전용 endpoint와 프론트 연결만 수행한다.

**검증 계획**:

- `npm run build`
- `npm audit --audit-level=moderate`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests`
- `git diff --check`

---

## Frontend Pilot — 잠재 고객 컬럼 밀도 축소

**목표**: 파이프라인 보드에서 `잠재` 고객이 과도하게 많아지는 문제를 줄이기 위해, DB 단계 변경 없이 API/프론트에서 우선순위 높은 잠재 고객만 먼저 보여준다.

**작업 범위**:

- API deal payload에 `attentionScore`, `attentionReason`, `isPotentialOverflow` 추가
- 잠재 고객은 점수순으로 정렬하고 보드에서는 TOP 10만 기본 노출
- React 보드의 `잠재` 컬럼은 기본 접힘 상태로 표시
- 접힌 상태에서는 우선 대응 잠재 고객 요약과 펼치기 버튼 제공
- 리스트 탭에서는 전체 잠재 고객 유지

**DB 변경 필요 여부**: 없음. 기존 `pipeline_stage` 값을 그대로 사용하고 화면/API 표현만 조정한다.

**검증 계획**:

- `npm run build`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 상세 패널 확장

**목표**: 카드 클릭 시 우측 상세 패널이 단순 금액/다음 액션을 넘어서, 실제 영업 판단에 필요한 최근 활동·견적·일정 요약과 기존 Django 상세 바로가기를 제공하도록 개선한다.

**작업 범위**:

- API deal payload에 `recentActivities`, `latestQuote`, `nextSchedule`, `stageLabel` 추가
- 우측 상세 패널에 핵심 상태, 다음 액션, 최근 활동, 최근 견적, 다음 일정, 기존 고객 상세 링크 표시
- mock data에도 상세 패널용 필드 추가
- API 테스트에서 상세 필드 응답 검증

**DB 변경 필요 여부**: 없음. 기존 prefetch된 History/Quote/Schedule 데이터만 읽는다.

**검증 계획**:

- `npm run build`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — 파이프라인 단계 변경 API 연결

**목표**: React 파일럿 상세 패널에서 기존 Django 파이프라인 단계 이동 API를 호출해, 선택 고객의 영업 단계를 변경하고 최신 파이프라인 데이터를 다시 불러온다.

**작업 범위**:

- React API helper에 CSRF 토큰 포함 POST 함수 추가
- 상세 패널에 단계 변경 버튼과 저장 상태/오류 메시지 표시
- Django API 데이터 연결 상태에서만 단계 변경 활성화, mock fallback 상태에서는 비활성 안내
- 기존 `reporting:funnel_pipeline_move` 권한 정책과 수동 단계 설정 로직 재사용
- 파이프라인 이동 API 회귀 테스트 추가

**DB 변경 필요 여부**: 없음. 기존 `FollowUp.pipeline_stage`, `pipeline_manually_set` 필드만 갱신한다.

**검증 계획**:

- `npm run build`
- `npm audit --audit-level=moderate`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — Railway 프론트 서비스 배포 준비

**목표**: React 파일럿을 Railway 별도 프론트 서비스로 배포할 수 있도록, 정적 파일 서빙과 기존 Django `/reporting/*` proxy를 제공하는 최소 Node 서버를 추가한다.

**작업 범위**:

- `frontend/server.mjs` 추가
- `npm start`로 Railway `$PORT`에서 React `dist` 정적 파일 서빙
- `/reporting/*` 요청은 기존 Django Railway 서버로 proxy
- 프론트 README에 Railway build/start/env 설정 기록
- Railway CLI 인증 상태 확인 및 서비스 생성 시도

**DB 변경 필요 여부**: 없음.

**검증 계획**:

- `npm run build`
- `node --check server.mjs`
- `npm audit --audit-level=moderate`
- 로컬 `node server.mjs`로 `/`, `/reporting/login/` 200 확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `git diff --check`

---

## Frontend Pilot — Django 대시보드 디자인 톤 정렬

**목표**: React 파이프라인 파일럿이 기존 `/reporting/dashboard/`와 다른 별도 제품처럼 보이지 않도록, Django 대시보드의 다크 CRM 디자인 시스템을 따라간다.

**작업 범위**:

- `reporting/base.html` 및 `dashboard.html`의 핵심 토큰을 기준으로 프론트 색상 체계 정리
- 다크 남색 배경, 다크 사이드바, 표면 카드, 파란색/보라색 그라데이션 포인트 반영
- KPI 카드, 필터 rail, 파이프라인 보드, 우측 상세 패널의 border/shadow/hover 톤 정렬
- 기존 클릭 동작, Django proxy, 파이프라인 API 연결은 유지

**DB 변경 필요 여부**: 없음. CSS 중심의 프론트 디자인 변경이다.

**검증 계획**:

- `npm run build`
- `node --check server.mjs`
- 로컬 또는 배포 URL smoke 확인
- `git diff --check`

---

## Frontend Pilot — 라이트 CRM 톤 재정렬 및 백엔드 복귀 링크

**목표**: React 파이프라인 화면을 운영 `/reporting/dashboard/`에 적용된 CRM light UI 토큰과 맞추고, Django 백엔드 화면에서 React 파이프라인으로 돌아오는 명확한 동선을 추가한다.

**작업 범위**:

- React 파이프라인 CSS를 `crm-ui.css` 기준의 화이트 모드로 재정렬
- 카드, 사이드바, 보드, 상세 패널, 상태 배지의 white-on-light/low contrast 여부 점검
- Django 공통 context에 프론트 파이프라인 URL 제공
- Django 사이드바와 상단 빠른 액션에 `신규 파이프라인` 링크 추가
- 기존 `/reporting/*` 라우트, 인증, CSRF, 파이프라인 API는 유지

**DB 변경 필요 여부**: 없음. UI/CSS와 template/context 설정 변경만 수행한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 배포 URL smoke 확인

---

## Frontend Hotfix — 프록시된 Django 정적 자산 라우팅

**목표**: 프론트 Railway 도메인에서 `/reporting/*` Django 화면으로 이동했을 때 `crm-ui.css` 라이트 테마가 정상 로드되어 모든 CRM 화면이 화이트 모드로 보이게 한다.

**원인**:

- `frontend/server.mjs`는 `/reporting/*`와 `/ai/*` HTML/API 요청만 Django로 proxy한다.
- Django 템플릿이 참조하는 `/static/reporting/css/crm-ui.css` 요청은 프론트 React fallback으로 처리되어 CSS 대신 `index.html`이 내려간다.
- 그 결과 `base.html`의 기존 inline dark token만 적용되고 schedules 화면이 다크 모드로 보인다.

**작업 범위**:

- 프론트 Node 서버에서 `/static/*` 요청을 Django 백엔드로 proxy한다.
- 첨부/업로드 자산을 위해 `/media/*` 요청도 Django 백엔드로 proxy한다.
- React 빌드 자산인 `/assets/*`는 기존처럼 프론트 서비스가 직접 서빙한다.
- DB, migration, Django 인증/CSRF 정책은 변경하지 않는다.

**검증 계획**:

- `cd frontend && node --check server.mjs`
- `cd frontend && npm run build`
- 로컬 프론트 서버에서 `/static/reporting/css/crm-ui.css`가 HTML이 아니라 CSS로 반환되는지 확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- Railway 프론트 배포 후 운영 프론트 도메인의 `/static/reporting/css/crm-ui.css`와 `/reporting/login/` smoke 확인

---

## UI Hotfix — 프로필 화면 라이트 CRM 테마 정리

**목표**: `/reporting/profile/`와 `/reporting/profile/edit/`가 공통 CRM 라이트 테마를 따르도록 페이지 전용 다크 CSS를 제거한다.

**원인**:

- `profile.html`과 `profile_edit.html`에 `hsl(222, 47%, 14%)`, `hsl(210, 40%, 98%)` 기반의 페이지 전용 다크 모드 CSS가 남아 있다.
- 이 스타일이 공통 `crm-ui.css` 라이트 토큰보다 늦게 적용되어 프로필 카드/입력 필드가 다크 모드로 보인다.

**작업 범위**:

- 프로필 보기 화면의 카드, 본문, 읽기 전용 필드, 이메일 연동 카드, alert 스타일을 라이트 CRM 토큰으로 변경한다.
- 프로필 수정 화면의 카드, 폼 필드, 안내 alert, 계정 정보 필드를 라이트 CRM 토큰으로 변경한다.
- 인증/권한, view, model, migration은 변경하지 않는다.

**검증 계획**:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- 로그인된 로컬 클라이언트로 `/reporting/profile/`, `/reporting/profile/edit/` 200 확인
- 템플릿에 프로필 전용 다크 HSL 토큰이 남지 않았는지 확인
- `git diff --check`

---

## UI Hotfix — 화이트 모드 잔여 흰 텍스트/다크 토큰 정리

**목표**: CRM이 화이트 모드로 확정된 상태에서 라이트 배경 위 흰 텍스트 또는 다크 모드 잔여 토큰이 보이는 화면을 정리한다.

**작업 범위**:

- `base.html`의 기본 CSS 변수와 Bootstrap 변수 기본값을 라이트 CRM 토큰으로 정규화한다.
- `crm-ui.css`에 페이지별 다크 CSS, Select2, Quill, 파일 input, 인라인 다크 HSL 스타일을 라이트 표면/텍스트로 보정하는 공통 규칙을 추가한다.
- 팔로우업 삭제/상세 화면처럼 인라인 다크 스타일이 강한 템플릿은 직접 라이트 스타일로 교체한다.
- 버튼, 배지, 위험/성공 헤더처럼 색상 배경 위에서 흰 텍스트가 필요한 요소는 유지한다.

**DB 변경 필요 여부**: 없음. CSS/template 표시 수정만 수행한다.

**검증 계획**:

- 흰 텍스트/다크 HSL 패턴 재스캔
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## UI Hotfix — 고객 리포트 흰 텍스트 정리

**목표**: `/reporting/customer-report/` 화면의 고객명 배지에서 라이트 배경 위 흰 텍스트가 남는 문제를 수정한다.

**원인**:

- `customer_report_list.html`에 `.badge.bg-secondary.text-decoration-none { color: #ffffff !important; }` 규칙이 남아 있다.
- 공통 `crm-ui.css`는 `bg-secondary` 배지를 라이트 배경으로 바꾸지만, 페이지 전용 selector의 specificity가 더 높아 흰 텍스트가 유지된다.

**작업 범위**:

- 고객명 링크 배지를 라이트 회색 배경/슬레이트 텍스트/hover 상태로 변경한다.
- 버튼/활성 드롭다운처럼 색상 배경 위 흰 텍스트가 필요한 요소는 유지한다.

**DB 변경 필요 여부**: 없음. 템플릿 CSS 수정만 수행한다.

**검증 계획**:

- `customer_report_list.html` 흰 텍스트 패턴 재확인
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `git diff --check`

---

## Frontend Migration — CRM Shell 단일 진입점 1차 정리

**목표**: React 프론트를 CRM의 메인 진입점으로 세우고, 대시보드/고객/파이프라인/영업노트/일정/AI 핵심 메뉴를 프론트 Shell에서 소유하게 한다.

**작업 범위**:

- React 앱에 `/dashboard/`, `/customers/`, `/pipeline/`, `/notes/`, `/schedules/`, `/ai-workspace/` 라우트형 화면을 추가한다.
- 아직 완전 이관 전인 기능은 프론트 Shell 안에서 운영 Django 화면으로 이어지는 명확한 작업 버튼을 제공한다.
- Django context에 프론트 핵심 메뉴 URL을 공통 제공한다.
- Django sidebar의 핵심 CRM 메뉴는 프론트 URL로 연결하고, 중복되는 Django 메뉴 노출을 줄인다.
- 기존 Django `/reporting/*`, `/ai/*` route, 인증, CSRF, API, DB 모델은 유지한다.

**DB 변경 필요 여부**: 없음. 프론트 라우팅/UI와 Django template/context 변경만 수행한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Dashboard 실제 데이터 연결

**목표**: React `/dashboard/` placeholder를 Django CRM 데이터 기반 업무 대시보드로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/dashboard/` JSON API를 추가한다.
- API는 기존 `FollowUp`, `Schedule`, `History`, `PersonalSchedule` 데이터를 사용해 KPI, 오늘 일정, 이번 주 일정, 지연 후속조치, 최근 영업노트, 우선순위 고객, 파이프라인 요약을 반환한다.
- 권한 범위는 기존 대시보드/파이프라인 패턴을 따른다. Salesman은 본인 데이터, Manager는 같은 회사 실무자, Admin은 기존 관리자 필터가 있으면 필터를 반영하고 없으면 전체 데이터를 본다.
- React `/dashboard/`는 새 API를 호출해 실제 KPI/오늘 일정/최근 활동/우선 고객을 표시하고, 저장/상세 작업은 기존 Django 운영 화면 링크로 연결한다.
- `/customers/`, `/notes/`, `/schedules/`, `/ai-workspace/`는 이번 작업에서 확장하지 않는다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Customers 실제 데이터 연결

**목표**: React `/customers/` placeholder를 Django CRM 고객 데이터 기반 화면으로 교체한다.

**작업 범위**:

- 대시보드 API의 미로그인 HTML 200 문제를 방지하기 위해 React용 JSON API는 미인증 시 401 JSON을 반환하도록 보정한다.
- Django에 인증이 필요한 읽기 전용 `/reporting/api/customers/` JSON API를 추가한다.
- API는 기존 `FollowUp`, `Company`, `Department`, `History` 데이터를 사용해 고객 목록, 우선순위 고객, 검색/담당자/우선순위 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 기존 dashboard API와 동일하게 유지한다.
- React `/customers/`는 고객 검색, 담당자 필터, 우선순위 필터, 우선 고객 리스트, 실제 고객 리스트를 표시하고 기존 Django 상세/등록/리포트 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Notes 실제 데이터 연결

**목표**: React `/notes/` placeholder를 Django CRM 영업노트/활동 히스토리 데이터 기반 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/notes/` JSON API를 추가한다.
- API는 기존 `History`, `FollowUp`, `Schedule`, `User` 데이터를 사용해 영업노트 목록, 지연/예정 다음 액션, 미검토 노트, 활동 유형/담당자 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 dashboard/customers API와 동일하게 유지한다.
- React `/notes/`는 키워드 검색, 담당자 필터, 활동 유형 필터, 검토 상태 필터, 다음 액션 필터와 실제 영업노트 목록을 표시하고 기존 Django 상세/작성 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React Schedules 실제 데이터 연결

**목표**: React `/schedules/` placeholder를 Django CRM 일정 데이터 기반 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/schedules/` JSON API를 추가한다.
- API는 기존 `Schedule`, `PersonalSchedule`, `FollowUp`, `History`, `User` 데이터를 사용해 일정 목록, 오늘 일정, 이번 주 일정, 지연 일정, 상태/활동유형/담당자 필터 옵션, 기본 KPI를 반환한다.
- 권한 범위는 dashboard/customers/notes API와 동일하게 유지한다.
- React `/schedules/`는 키워드 검색, 담당자 필터, 상태 필터, 활동 유형 필터, 기간 필터와 실제 일정 목록을 표시하고 기존 Django 상세/등록/캘린더/보고 작성 화면으로 연결한다.
- 기존 `/reporting/*`, `/ai/*`, 파이프라인 API, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 현재 `/schedules/` 실제 데이터 연결 및 검증: 약 1~2시간.
- 로그인된 운영 브라우저 왕복 동선 확인과 배포까지 포함하면 추가 20~40분.
- `/schedules/` 이후 남은 React shell 전환 핵심 작업은 `/ai-workspace/`이며, 범위 확정 후 약 2~4시간 예상.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Frontend Migration — React AI Workspace 실제 데이터 연결

**목표**: React `/ai-workspace/` placeholder를 기존 Django AI 운영 기능 상태를 보여주는 실제 업무 화면으로 교체한다.

**작업 범위**:

- Django에 인증이 필요한 읽기 전용 `/reporting/api/ai-workspace/` JSON API를 추가한다.
- API는 기존 `ai_chat`의 `AIDepartmentAnalysis`, `PainPointCard`, `AIFollowUpAnalysis`와 reporting의 `FollowUp`, `WeeklyReport` 데이터를 사용한다.
- 권한은 기존 AI 정책을 유지한다. 로그인은 필수이며, `can_use_ai=False` 사용자는 AI 데이터 없이 권한 없음 상태만 받는다.
- React `/ai-workspace/`는 AI 권한 상태, 부서 분석 대상, 분석 완료 현황, 미검증 PainPoint, 고객 분석 대상, 주간보고 AI 초안 링크를 표시하고 기존 Django AI 운영 화면으로 연결한다.
- 새 AI 생성/외부 API 호출은 하지 않는다. 분석 실행, 프롬프트 생성, 주간보고 초안 생성은 기존 Django 운영 화면/API로 연결한다.
- 기존 `/ai/*`, `/reporting/*`, 인증, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 현재 `/ai-workspace/` 실제 데이터 연결 및 검증: 약 2~4시간.
- 운영 로그인 세션에서 AI 권한 사용자/비권한 사용자 육안 확인과 배포까지 포함하면 추가 30~60분.
- 이 작업 완료 후 목표한 React shell 핵심 메뉴 실제 데이터 연결은 1차 완료 상태로 볼 수 있다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test ai_chat --verbosity=1`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Pipeline Pricing — 견적/협상/수주 단계 가격 반영

**목표**: React 파이프라인과 Django 파이프라인 보드에서 견적 제출, 협상, 수주 단계 고객의 금액을 기존 Quote 데이터에서 정확히 끌어온다.

**작업 범위**:

- `/reporting/api/pipeline/`가 파이프라인 단계에 맞는 Quote를 가격 기준으로 선택하도록 보정한다.
- `quote` 단계는 발송/검토/초안 등 진행 중 견적을 우선 사용한다.
- `negotiation` 단계는 협상중 견적을 우선 사용한다.
- `won` 단계는 계약전환/승인/납품전환 견적을 우선 사용한다.
- 최신 견적이 거절/만료 등 현재 단계와 맞지 않아도 단계에 맞는 견적 금액이 있으면 그 금액을 우선 반영한다.
- 기존 `/reporting/funnel/pipeline/` Django 보드도 같은 가격 기준을 사용한다.
- 인증, 권한 범위, 기존 `/reporting/*` 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Quote` 필드만 조회하므로 migration은 만들지 않는다.

**예상 소요**:

- 구현 및 테스트: 약 1~2시간.
- 운영 배포 및 미로그인/로그인 smoke 포함: 추가 20~40분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `python manage.py test reporting --verbosity=1`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Schedules Navigation — 일정 캘린더 우선 동선

**목표**: 프론트 `/schedules/` 진입 시 목록 화면 대신 기존 Django 일정 캘린더를 기본 업무 화면으로 연다.

**작업 범위**:

- 프론트 운영 서버에서 `/schedules/`와 `/schedules` 요청을 `/reporting/schedules/calendar/`로 리디렉션한다.
- React 런타임에서도 `/schedules/` 진입 시 일정 캘린더로 이동하게 보정한다.
- 일정 메뉴의 문구와 README를 캘린더 우선 동선으로 정리한다.
- 기존 Django 일정 목록, 일정 API, 일정 등록/상세/캘린더 기능은 유지한다.

**DB 변경 필요 여부**: 없음.

**예상 소요**:

- 구현 및 검증: 약 30~60분.
- 운영 배포 및 smoke 포함: 추가 20~40분.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- 운영/로컬에서 `/schedules/`가 `/reporting/schedules/calendar/`로 이동하는지 확인

---

## Pipeline Pricing — 실제 견적/납품 품목 기준 보강

**목표**: React 파이프라인과 Django 파이프라인 보드의 카드 금액을 운영에서 실제 입력하는 견적/납품 품목 데이터 기준으로 표시한다.

**작업 범위**:

- `quote`, `negotiation` 단계는 `Schedule(activity_type='quote')`의 `DeliveryItem` 금액을 우선 사용한다.
- 견적 일정에 품목 금액이 없으면 `History(action_type='quote')`에 직접 연결된 `DeliveryItem` 금액을 사용한다.
- 위 실제 업무 품목 데이터가 없을 때만 기존 `Quote` 모델 금액으로 fallback한다.
- `won` 단계는 완료된 납품 일정의 `DeliveryItem` 금액을 우선 합산한다.
- 납품 일정 품목이 없으면 연결된 납품 히스토리의 `DeliveryItem` 또는 `delivery_amount`를 사용한다.
- 일정 없이 등록된 납품 히스토리 품목/금액도 실제 납품 매출로 합산한다.
- 기존 `/reporting/*` 운영 화면, 인증/권한, CSRF 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 필드만 조회한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Pipeline Won Cards — 견적 대비 실제 납품 매출 차이 표시

**목표**: 수주 단계 카드에서 대표 금액은 실제 납품 매출로 유지하되, 기준 견적 금액과 차액/차이율을 함께 보여준다.

**작업 범위**:

- `won` 단계 카드에 실제 납품 매출과 비교할 기준 견적 데이터를 계산한다.
- 기준 견적은 기존 운영 데이터 우선순위를 따른다: 견적 일정 품목 → 견적 히스토리 품목 → 승인/전환된 Quote → 진행/최근 Quote fallback.
- React `/` 파이프라인 상세 패널과 리스트, Django `/reporting/funnel/pipeline/` 보드에 견적 대비 차이를 표시한다.
- API 응답에 `quoteComparison`을 추가해 `quotedAmount`, `actualAmount`, `deltaAmount`, `deltaRate`, `status`, `source`를 내려준다.
- 기존 파이프라인 대표 금액, 단계 이동, 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 조회만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 배포와 운영 smoke까지 포함하면 추가 30~60분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Customers Page — 실제 고객 데이터 연결 보강

**목표**: React `/customers/` 화면을 기존 Django 고객/팔로우업 운영 데이터에 더 직접 연결해, 검색/담당자/우선순위 필터뿐 아니라 실제 활동 이력과 예정 일정까지 한 화면에서 확인한다.

**작업 범위**:

- `/reporting/api/customers/` payload에 고객별 활동 수, 일정 수, 예정 일정 수, 지연 후속 수, 다음 예정 일정 정보를 추가한다.
- 고객 목록에서 연락처, 최근 활동, 다음 액션, 예정 일정, 활동/일정 카운트를 함께 표시한다.
- 우선 고객 패널에서 지연 후속과 예정 일정 정보를 바로 볼 수 있게 한다.
- 기존 고객 상세, 고객 등록, 일정 등록, 고객 리포트 링크는 Django 운영 화면으로 유지한다.
- 인증/권한 범위는 기존 대시보드 scope 규칙을 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `History`, `Schedule` 조회와 annotate/prefetch만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Quote Loading — 부서 내 여러 견적 누락 보정

**목표**: 같은 부서/연구실에 견적이 여러 건 있을 때 한 건만 불러오는 문제를 해결한다.

**작업 범위**:

- 납품 일정 작성의 `견적에서 품목 불러오기` API가 선택 고객 1명 기준이 아니라 같은 부서의 접근 가능한 본인 견적 일정 전체를 반환하게 한다.
- 같은 부서의 여러 견적을 구분할 수 있도록 고객명, 업체/부서명, 일정 ID, 견적일, 금액을 payload와 모달에 표시한다.
- 고객 기록 API도 `Quote` 모델뿐 아니라 견적 일정의 품목/예상금액까지 포함해 부서 기준 견적 목록을 누락 없이 보여준다.
- 파이프라인 가격 기준은 동일 고객에 여러 견적 일정/견적 활동/Quote가 있으면 대표 1건이 아니라 같은 우선순위 소스의 금액을 합산해 표시한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `History`, `DeliveryItem`, `Quote` 조회만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 고객 화면 배포와 함께 운영 smoke까지 포함하면 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.PipelineApiTests reporting.tests.QuoteItemsApiTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Notes Page — 미검토/지연 노트 검토 동선 보강

**목표**: React `/notes/` 화면에서 단순 조회를 넘어, 관리자/매니저가 미검토 영업노트를 빠르게 확인하고 검토 완료 처리까지 할 수 있게 한다.

**작업 범위**:

- `/reporting/api/notes/` payload에 검토 가능 여부, 검토자/검토 시각, 검토 토글 URL, 첨부/댓글 수를 추가한다.
- React 노트 목록에 첨부/댓글 수, 검토 상태 상세, 검토 처리 버튼을 표시한다.
- 관리자/매니저 권한이 있는 경우에만 React에서 검토 완료/해제 POST를 노출한다.
- 검토 처리 후 현재 필터 조건으로 노트 데이터를 다시 불러와 미검토/지연 지표를 갱신한다.
- 기존 Django 영업노트 상세, 작성, 관리자 메모 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `HistoryFile`, `reply_memos`, `reviewed_at`, `reviewer` 조회와 기존 검토 토글 view만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1~2시간.
- 전체 테스트와 운영 배포/smoke 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test reporting --verbosity=1`
- `python manage.py test --verbosity=1`
- `git diff --check`

---

## Notes Review Permission — 회사별 매니저 기준 보정

**목표**: React `/notes/` 검토 완료/해제 권한을 최고권한자/admin이 아니라 각 소속 회사의 `manager` 계정 기준으로 제한한다.

**작업 범위**:

- `/reporting/api/notes/`의 `scope.canReview`, 노트별 `canReview`, `reviewToggleHref`를 `UserProfile.is_manager()` 기준으로 보정한다.
- `history_toggle_reviewed` POST도 `manager` 역할만 허용하고, 기존 같은 회사 접근 검사를 유지한다.
- React 문구 중 노트 검토 저장 뷰의 "관리자 검토" 표현을 "매니저 검토"로 수정한다.
- admin, salesman, 타회사 manager 차단 테스트를 추가한다.

**DB 변경 필요 여부**: 없음. 권한 조건과 테스트만 수정한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 30~60분.
- 배포와 운영 smoke 포함: 추가 30~60분.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI Workspace — 실제 대상 기반 프롬프트 큐 추가

**목표**: React `/ai-workspace/`가 단순 현황판이 아니라, 실제 부서/고객/PainPoint 데이터를 골라 외부 AI 작업에 바로 사용할 수 있는 프롬프트 큐를 제공하게 한다.

**작업 범위**:

- `/reporting/api/ai-workspace/`에 `promptTargets` payload를 추가한다.
- 부서 분석, 고객 분석, 미검증 PainPoint를 실제 데이터 기반 프롬프트 후보로 생성한다.
- React `/ai-workspace/`에 프롬프트 큐 패널과 복사 버튼을 추가한다.
- AI 권한이 없는 사용자는 기존처럼 빈 상태와 권한 안내만 받게 유지한다.
- 기존 `ai_chat` 분석 화면, 주간보고 AI 초안 API, 고객/노트 링크는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `AIDepartmentAnalysis`, `AIFollowUpAnalysis`, `PainPointCard` 조회 결과만 사용한다.

**예상 소요**:

- 구현 및 회귀 테스트: 약 1.5~3시간.
- 전체 빌드/check와 운영 배포 포함: 추가 40~80분.

**검증 계획**:

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI Workspace — 프롬프트 문맥 확장

**목표**: `/ai-workspace/`의 AI 작업 큐 프롬프트가 실제 최근 활동과 금액 맥락을 더 잘 반영하도록 보강한다.

**작업 범위**:

- 부서/고객/PainPoint 프롬프트에 최근 영업노트 최대 3건을 추가한다.
- 열린 견적 건수/금액과 수주 금액 요약을 프롬프트에 추가한다.
- 열린 견적은 기존 `Quote`와 견적 일정의 `expected_revenue`를 사용하되, 동일 `Quote`가 있는 일정 금액은 중복 집계하지 않는다.
- 수주 금액은 `OpportunityTracking.current_stage='won'`의 실제 매출을 우선 사용하고, 없으면 전환 견적/납품 기록을 fallback으로 사용한다.
- React 화면 구조와 기존 AI 분석/주간보고 링크는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `Quote`, `Schedule`, `OpportunityTracking` 조회만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.AIWorkspaceSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## Frontend Auth Redirect — 미로그인 루트 진입 차단

**목표**: `https://sales-note-frontend-production.up.railway.app/`에 미로그인 상태로 접속하면 React mock/fallback 화면을 보여주지 않고 Django 로그인 화면으로 이동시킨다.

**작업 범위**:

- 프론트 API 호출이 Django 로그인 페이지로 리다이렉트된 HTML 응답을 받으면 `/reporting/login/`으로 이동한다.
- JSON API가 `401 {"error": "login_required"}`를 반환해도 동일하게 로그인 화면으로 이동한다.
- 루트 파이프라인뿐 아니라 dashboard/customers/notes/schedules/AI workspace API에도 같은 인증 처리 helper를 적용한다.
- 백엔드 인증/권한 정책은 변경하지 않는다.

**DB 변경 필요 여부**: 없음. 프론트 인증 응답 처리만 변경한다.

**검증 계획**:

- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## CRM Shell Navigation — 프론트 중심 동선 안정화

**목표**: React 프론트와 Django 템플릿을 오가며 사용자가 길을 잃는 문제를 줄이고, 프론트를 주 CRM Shell로 고정한다.

**작업 범위**:

- 로그인 성공 기본 이동지를 Django 대시보드가 아니라 프론트 `/dashboard/`로 변경한다.
- Django 백엔드 루트(`/`)도 인증된 사용자는 프론트 대시보드로 보낸다.
- Django 공통 상단 바에 "프론트 CRM" 복귀 버튼과 "Django 작업 화면" 표시를 추가한다.
- React 상단/route 액션에서 Django 대시보드로 불필요하게 이동시키는 링크를 프론트 화면 중심으로 정리한다.
- 기존 Django 작성/상세/관리 화면은 유지하고, 저장/작성 작업에 필요한 링크만 Django로 남긴다.

**DB 변경 필요 여부**: 없음. URL/템플릿/프론트 링크 정리만 수행한다.

**검증 계획**:

- `python manage.py test reporting.tests.AuthenticationSmoke reporting.tests.DashboardSmokeTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Notes Create — 영업노트 빠른 작성

**목표**: React `/notes/` 화면에서 기본 영업노트를 바로 작성하게 만들어 Django 대시보드 모달 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/notes/`에 React 작성 폼용 고객/활동유형/저장 URL 정보를 추가한다.
- `/reporting/api/notes/create/` POST API를 추가한다.
- 작성 권한은 기존 정책을 보존해 manager는 차단하고, salesman/admin은 본인 담당 고객에만 작성 가능하게 제한한다.
- React `/notes/`에 빠른 작성 패널을 추가하고 저장 후 목록/지표를 새로고침한다.
- 첨부파일, 납품 품목, 상세 일정 기반 작성은 기존 Django 화면을 계속 사용한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedules List — 일정 화면 프론트 전환

**목표**: `/schedules/`를 기존 Django 캘린더로 즉시 이동시키지 않고 React 일정 목록 화면으로 열어 프론트 중심 CRM Shell을 강화한다.

**작업 범위**:

- React `SchedulesPage`가 이미 가진 필터/목록/오늘 일정/지연 일정 UI를 실제 `/reporting/api/schedules/` 데이터에 연결한다.
- 프론트 서버의 `/schedules/` 강제 Django 캘린더 리다이렉트를 제거한다.
- 기존 Django 일정 캘린더, 일정 등록, 개인 일정 등록, 일정 상세/보고 작성 링크는 React 화면의 보조 작업 링크로 유지한다.
- `/reporting/*` 경로와 기존 Django 일정 기능은 삭제하지 않는다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `PersonalSchedule`, `History`, `FollowUp` 조회 API만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedules Quick Create — 일정 빠른 등록

**목표**: React `/schedules/` 화면에서 기본 고객 일정을 바로 등록하게 만들어 Django 일정 생성 폼 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/schedules/`에 React 빠른 등록 폼용 고객/활동유형/저장 URL 정보를 추가한다.
- `/reporting/api/schedules/create/` POST API를 추가한다.
- 작성 권한은 기존 정책을 보존해 manager는 차단하고, salesman/admin은 본인 담당 고객 일정만 빠르게 등록하게 제한한다.
- React `/schedules/`에 빠른 등록 패널을 추가하고 저장 후 일정 목록/지표를 새로고침한다.
- 납품 품목, 선결제, 첨부, 고급 편집은 기존 Django 일정 폼을 계속 사용한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Detail — 고객 상세/이력 프론트 전환

**목표**: 고객 목록에서 Django 상세 화면으로 바로 넘어가지 않고 React 안에서 고객별 최근 영업노트, 예정 일정, 지연 후속을 확인하게 만든다.

**작업 범위**:

- `/reporting/api/customers/<id>/` 고객 상세 요약 API를 추가한다.
- API는 기존 권한 규칙을 유지해 로그인/회사/담당자 범위 밖 고객 데이터 노출을 막는다.
- React `/customers/<id>/` route를 추가하고 고객 요약, 최근 노트, 예정 일정, 지연 후속, Django 상세 링크를 표시한다.
- 고객 목록/우선 고객 링크를 React 상세 route로 변경한다.
- 일정 빠른 등록 저장 후 Django 일정 상세로 들어갈 수 있는 링크를 성공 메시지에 표시한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `History`, `Schedule` 조회만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Notes Customer Prefill — 고객 상세 노트 작성 연결

**목표**: React 고객 상세에서 영업노트 작성으로 바로 이동하고, `/notes/?create=1&customer=<id>` 진입 시 해당 고객을 빠른 작성 폼에 자동 선택한다.

**작업 범위**:

- React 고객 상세 상단 작업에 `노트 작성` 링크를 추가한다.
- React 노트 빠른 작성 폼이 `customer` query parameter를 읽어 허용된 고객이면 우선 선택한다.
- 저장 후 폼 초기화에서도 고객 상세에서 넘어온 고객 선택을 유지한다.
- 기존 Django 영업노트 상세/작성 기능과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp` 모델과 노트 생성 API만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Quick Create — 고객 빠른 등록

**목표**: React `/customers/` 목록에서 Django 고객 생성 폼으로 빠지지 않고 기본 고객 정보를 바로 등록한다.

**작업 범위**:

- `/reporting/api/customers/`에 고객 빠른 등록용 업체/부서/우선순위/저장 URL 정보를 추가한다.
- 기존 `/reporting/api/followups/create/` AJAX 생성 API를 React에서 재사용한다.
- Manager 생성 차단과 업체 접근 권한 검증은 기존 정책을 유지한다.
- React 고객 화면에 빠른 등록 패널을 추가하고 저장 후 고객 목록/지표를 새로고침한다.
- 업체/부서 신규 생성, 고급 필드, 삭제/수정은 기존 Django 화면을 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Company`, `Department`, `FollowUp` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Inline Company/Department Create — 고객 등록 업체/부서 연결

**목표**: React 고객 빠른 등록 화면에서 기존 업체/부서가 없을 때 Django 관리 화면으로 이동하지 않고 바로 업체와 부서를 추가한다.

**작업 범위**:

- 기존 `/reporting/api/companies/create/`, `/reporting/api/departments/create/` API를 React에서 호출한다.
- 회사/부서 생성 API도 Manager 생성 차단과 업체 접근 권한을 보강한다.
- React 고객 빠른 등록 패널에 새 업체/학교, 새 부서/연구실 입력과 추가 버튼을 배치한다.
- 업체/부서 추가 후 고객 등록 폼 선택값을 방금 만든 항목으로 자동 갱신한다.
- 기존 Django 업체/부서 관리 화면은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Company`, `Department` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer Detail Edit — 고객 상세 수정 전환

**목표**: React `/customers/<id>/` 상세 화면에서 Django 고객 수정 화면으로 이동하지 않고 고객 기본정보를 바로 수정한다.

**작업 범위**:

- `/reporting/api/customers/<id>/` 상세 API에 수정 가능 여부, 저장 URL, 업체/부서/상태/우선순위/파이프라인 옵션을 추가한다.
- `/reporting/api/customers/<id>/update/` POST API를 추가해 고객명, 업체, 부서, 책임자, 연락처, 이메일, 주소, 메모, 상태, 우선순위, 파이프라인 단계를 저장한다.
- 기존 권한 정책을 유지해 manager는 수정 불가, salesman은 본인 고객만 수정 가능, admin은 수정 가능하게 한다.
- React 고객 상세에 수정 패널을 추가하고 저장 후 상세 데이터를 다시 불러온다.
- 기존 Django `/reporting/followups/<id>/edit/` 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `FollowUp`, `Company`, `Department` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Sales Note Detail Edit — 영업노트 상세/수정 전환

**목표**: React `/notes/<id>/`에서 영업노트 상세를 확인하고, 권한이 있는 사용자는 Django 수정 화면으로 이동하지 않고 주요 노트 내용을 바로 수정한다.

**작업 범위**:

- `/reporting/api/notes/<id>/` 상세 API를 추가해 기존 `History` 기반 영업노트 상세, 고객/일정 연결, 검토 상태, 첨부/댓글 요약, 수정 옵션을 제공한다.
- `/reporting/api/notes/<id>/update/` POST API를 추가해 활동 유형, 고객, 활동일, 내용, 다음 액션, 다음 예정일, 미팅/납품/서비스 관련 필드를 저장한다.
- 기존 권한 정책을 유지해 manager는 상세 조회와 검토만 가능하고 수정은 차단하며, salesman은 본인 노트만 수정 가능하게 한다.
- React `/notes/<id>/` route를 추가하고 목록/고객 상세의 영업노트 링크가 React 상세로 이어지게 한다.
- 기존 Django `/reporting/histories/<id>/` 상세/수정 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History`, `FollowUp`, `Schedule`, `HistoryFile` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Detail Edit — 일정 상세/수정 전환

**목표**: React `/schedules/<id>/`에서 고객 일정 상세를 확인하고, 권한이 있는 사용자는 Django 수정 화면으로 이동하지 않고 주요 일정 정보를 바로 수정한다.

**작업 범위**:

- `/reporting/api/schedules/<id>/` 상세 API를 추가해 기존 `Schedule` 기반 일정 상세, 연결 고객/영업노트/납품 항목, 수정 옵션을 제공한다.
- `/reporting/api/schedules/<id>/update/` POST API를 추가해 고객 연결, 일정일/시간, 활동 유형, 상태, 장소, 메모, 예상 매출, 확률, 예상 종료일을 저장한다.
- 기존 권한 정책을 유지해 manager는 상세 조회만 가능하고 수정은 차단하며, salesman은 본인 일정만 수정 가능하게 한다.
- React `/schedules/<id>/` route를 추가하고 일정 목록의 고객 일정 링크가 React 상세로 이어지게 한다.
- 기존 Django `/reporting/schedules/<id>/` 상세/수정 화면은 보조 경로로 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Schedule`, `FollowUp`, `History`, `DeliveryItem` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Attachments — 일정 상세 첨부파일 전환

**목표**: React `/schedules/<id>/` 상세 화면에서 일정 첨부파일을 업로드하고 삭제하게 만들어 Django 상세 화면 왕복을 줄인다.

**작업 범위**:

- 일정 상세 API에 첨부파일 업로드 URL과 파일별 삭제 URL을 제공한다.
- 기존 일정 파일 업로드/삭제 뷰의 권한을 React 일정 수정 정책과 맞춰 manager는 조작 불가, 담당자는 본인 일정만 조작 가능하게 보강한다.
- React 일정 상세의 첨부파일 섹션에 다중 파일 업로드, 삭제 버튼, 진행/성공/오류 상태를 추가한다.
- 기존 Django `/reporting/schedules/<id>/files/upload/`, 다운로드, 삭제 URL과 `/reporting/*` 상세 기능은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `ScheduleFile` 모델과 파일 저장 정책만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Note Attachments — 영업노트 상세 첨부파일 전환

**목표**: React `/notes/<id>/` 상세 화면에서 영업노트 첨부파일을 업로드하고 삭제하게 만들어 Django 영업노트 수정 화면 왕복을 줄인다.

**작업 범위**:

- 영업노트 상세 API에 첨부파일 업로드 URL과 파일별 삭제 URL을 제공한다.
- `/reporting/api/notes/<id>/files/upload/` POST API를 추가해 기존 `HistoryFile` 모델로 다중 파일 업로드를 처리한다.
- 기존 파일 다운로드/삭제 URL은 유지하고 React 파일 목록에서 다운로드 링크와 삭제 버튼을 분리한다.
- 권한은 기존 영업노트 수정 정책을 유지해 manager는 파일 조작 불가, salesman은 본인 노트만 조작 가능하게 한다.
- 기존 Django `/reporting/histories/<id>/` 상세/수정과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `HistoryFile` 모델과 파일 검증 정책만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Note Replies — 영업노트 댓글/매니저 메모 전환

**목표**: React `/notes/<id>/` 상세 화면에서 댓글과 매니저 메모를 작성·삭제하게 만들어 Django 영업노트 상세 화면 왕복을 줄인다.

**작업 범위**:

- 영업노트 상세 API에 댓글 작성 URL, 댓글별 삭제 URL, 삭제 가능 여부를 제공한다.
- 기존 `/reporting/api/histories/<id>/add-manager-memo/`, `/reporting/api/histories/<id>/delete-manager-memo/` API를 React에서 호출한다.
- 기존 권한 정책을 유지해 manager는 같은 회사 노트에 매니저 메모를 작성할 수 있고, 실무자는 본인 노트에 댓글을 작성할 수 있게 한다.
- 댓글 삭제는 기존 정책대로 작성자 본인만 가능하게 유지한다.
- 기존 Django `/reporting/histories/<id>/` 상세와 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `History.parent_history` 댓글 구조를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.NotesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Delivery Items — 일정 납품 품목 편집 전환

**목표**: React `/schedules/<id>/` 상세 화면에서 납품 품목을 추가/수정/삭제하게 만들어 Django 일정 상세 모달 왕복을 줄인다.

**작업 범위**:

- `/reporting/api/schedules/<id>/delivery-items/update/` POST API를 추가해 기존 `DeliveryItem` 모델을 저장한다.
- 기존 권한 정책을 유지해 manager는 편집 불가, salesman은 본인 일정만 편집 가능하게 한다.
- 납품 품목 저장 후 연결된 납품 History의 `delivery_items`/`delivery_amount` 요약도 기존 Django 흐름처럼 동기화한다.
- React 일정 상세 API에 납품 품목 저장 URL을 내려준다.
- React `/schedules/<id>/` 납품 품목 섹션에 편집 패널, 품목 추가, 행 삭제, 세금계산서 체크, 저장 상태를 추가한다.
- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 상세/수정 화면과 `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `DeliveryItem`, `Schedule`, `History` 모델만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Schedule Delivery Product Selection — 납품 품목 제품 마스터 선택 전환

**목표**: React `/schedules/<id>/` 납품 품목 편집 패널에서 기존 제품 마스터를 검색·선택해 품번, 단위, 현재 단가를 자동 반영하게 만든다.

**작업 범위**:

- 기존 `/reporting/api/products/` 응답에 React 납품 품목 편집에 필요한 단위와 규격 정보를 포함한다.
- 제품 목록 조회와 저장 권한은 기존 회사/부서/담당자 접근 범위를 유지한다.
- `/reporting/api/schedules/<id>/delivery-items/update/` 저장 payload에 `productId`를 허용하고 접근 가능한 제품만 연결한다.
- 제품을 선택한 납품 품목은 기존 `DeliveryItem.product` 관계를 저장하고, 모델의 기존 저장 정책대로 품번/단위/현재 단가를 반영한다.
- React 납품 품목 편집 행에 제품 검색/선택 UI를 추가하고, 수기 품목 입력 흐름은 유지한다.
- 기존 Django `/reporting/schedules/<id>/update-delivery-items/`, 제품 관리 화면, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 `Product`와 `DeliveryItem.product` 필드를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.SchedulesSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## React Customer AI Result Verification — 고객 상세 AI 결과/검증 전환

**목표**: React `/customers/<id>/` 고객 상세 화면에서 부서 AI 분석 실행 후 결과 요약, 추천 액션, PainPoint 카드 검증까지 이어서 처리하게 만든다.

**작업 범위**:

- 기존 `AIDepartmentAnalysis`, `PainPointCard` 모델만 사용하고 신규 DB 필드는 추가하지 않는다.
- 고객 상세 API의 `aiDepartment` payload에 분석 기간, 미팅/견적/납품 인사이트, 추천 액션, 확인 필요 사항, PainPoint 카드 목록을 추가한다.
- PainPoint 검증 저장은 기존 `ai_chat:verify_card` POST API를 React에서 호출하도록 연결한다.
- 검증 권한은 기존 `can_use_ai` + 본인 담당 부서 분석 소유자 정책을 유지한다.
- React 고객 상세의 부서 AI 카드에서 결과를 펼쳐보고 미검증 PainPoint를 확인/부정 처리할 수 있게 한다.
- 기존 Django `/ai/department/<id>/`, `/ai/card/<id>/verify/`, `/reporting/*` 경로는 유지한다.

**DB 변경 필요 여부**: 없음. 기존 AI 분석/카드 모델과 검증 상태 필드를 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`

---

## AI PainPoint Verification Memory — 재분석 검증 메모리 반영

**목표**: 부서 AI 재분석 시 기존 PainPoint 검증 상태와 검증 메모를 GPT 입력 컨텍스트에 포함해 이미 확인/부정한 내용을 다시 묻지 않게 한다.

**작업 범위**:

- 기존 `PainPointCard.verification_status`, `verification_note`, `verified_at` 필드를 메모리 소스로 사용한다.
- 기존 `AIDepartmentAnalysis.analysis_data` JSON에 검증 메모리 사본을 저장해 재분석 후에도 다음 분석에서 사용할 수 있게 한다.
- 부서 분석 프롬프트에 `기존 PainPoint 검증 메모리` 섹션을 추가한다.
- 재분석 시 미검증 카드만 교체하고, 확인됨/부정됨 카드는 기존 검증 결과와 메모를 보존한다.
- GPT가 같은 가설/질문을 다시 반환해도 기존 검증 메모리와 중복되는 카드는 저장하지 않는다.
- 신규 DB 필드나 migration은 추가하지 않는다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드와 JSON payload만 사용한다.

**검증 계획**:

- `python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 배포 및 운영 `/reporting/api/customers/454/` login 보호 smoke check

---

## AI Verification-Based Insights — 검증 메모 분석 반영 강화

**목표**: 사용자가 PainPoint 검증 때 남긴 메모를 단순 저장/중복 방지용이 아니라 GPT의 요약, PainPoint, 다음 액션, 추가 검증 질문에 반영되는 분석 근거로 승격한다.

**작업 범위**:

- 기존 `PainPointCard.verification_status`, `verification_note`, `verified_at`와 `AIDepartmentAnalysis.analysis_data` JSON만 사용한다.
- 부서 AI 프롬프트에서 검증 메모리를 미팅 기록과 동급의 분석 근거로 명시한다.
- GPT 응답 계약에 `verification_insights`를 추가하고, GPT가 누락해도 서버에서 검증 메모 기반 fallback 인사이트/다음 액션/추가 질문을 저장한다.
- 고객 상세 API의 `aiDepartment` payload에 `verificationInsights`를 추가한다.
- React 고객 상세 AI 결과에 `검증 기반 인사이트` 섹션을 추가해 검증 메모가 다음 검증/액션으로 이어지는지 확인할 수 있게 한다.
- 기존 Django `/ai/*`, React 고객 상세, `/reporting/*` 인증/권한 정책은 유지한다.

**DB 변경 필요 여부**: 없음. 기존 모델 필드와 JSON payload만 사용한다.

**검증 계획**:

- `python manage.py test ai_chat.tests.AIDepartmentAnalysisMemoryTests --verbosity=1`
- `python manage.py test reporting.tests.CustomersSummaryApiTests --verbosity=1`
- `python manage.py test ai_chat.tests --verbosity=1`
- `cd frontend && npm run build`
- `cd frontend && node --check server.mjs`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web`, `sales-note-frontend` 배포 및 운영 smoke check

---

## Project Direction Documentation — React 단일 CRM 프론트 목표 문서화

**목표**: 프로젝트의 최종 방향을 "React 단일 CRM 프론트 + Django 백엔드/API"로 명확히 문서화하고, 작업마다 Railway 배포 후 사용자 수동검수를 받는 운영 방식을 표준화한다.

**작업 범위**:

- `AGENTS.md`, `.github/copilot-instructions.md`에 최종 아키텍처와 작업 후 Railway 배포/수동검수 규칙을 추가한다.
- `PROJECT_BRIEF.md`에 React CRM 통일, Django backend-only, Django 템플릿 최종 삭제 방향을 추가한다.
- `SALES_CRM_SPEC.md`에 React 마이그레이션 요구사항과 UI 방향을 명시한다.
- `QA_CHECKLIST.md`에 React migration, React build, Railway deployment, manual server test 항목을 추가한다.
- `AGENT_REPORT.md`에 문서 업데이트와 배포 상태를 기록한다.

**DB 변경 필요 여부**: 없음. 문서 변경만 수행한다.

**검증 계획**:

- `git diff --check`
- `python manage.py check`
- `cd frontend && npm run build` (현재 작업 트리에 React runtime 변경도 포함되어 있어 함께 확인)
- Railway 배포가 필요한 runtime 변경이 포함된 경우 `web`, `sales-note-frontend` 배포 후 운영 smoke check

---

## Urgent Weekly Report Quote/Delivery Amount Loading — 주간보고 견적/납품 금액 포함

**목표**: 운영 주간보고 작성 화면(`/reporting/weekly-reports/create/`)에서 `일정 불러오기`로 견적 제출 및 납품 기록을 가져올 때 금액도 카드와 삽입 텍스트에 함께 포함한다.

**작업 범위**:

- 기존 `weekly_report_load_schedules` JSON API에 견적/납품 일정 금액 필드를 추가한다.
- 견적 금액은 연결 `Quote.total_amount`를 우선 사용하고, 견적 일정에 Quote가 없으면 `DeliveryItem` 합계 또는 `Schedule.expected_revenue`를 fallback으로 사용한다.
- 납품 금액은 연결 `DeliveryItem.total_price` 합계를 우선 사용하고, 없으면 연결 `History.delivery_amount`, 없으면 `Schedule.expected_revenue`를 fallback으로 사용한다.
- 기존 인증 조건(`@login_required`)과 본인 일정만 조회하는 데이터 범위를 유지한다.
- 기존 Django 템플릿 화면에서 API로 받은 금액을 카드에 표시하고, 선택 삽입 시 `견적 금액`/`납품 금액` 줄을 포함한다.
- 페이지 최초 진입 시에도 최신 API 기반 카드가 렌더링되도록 초기 로드에서 `loadSchedules()`를 실행한다.

**DB 변경 필요 여부**: 없음. 기존 `Quote`, `DeliveryItem`, `History`, `Schedule.expected_revenue`만 사용한다.

**검증 계획**:

- `python manage.py test reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 서비스 배포 및 운영 `/reporting/weekly-reports/create/` 수동검수 절차 제공

---

## Urgent Weekly Report Rich Text HTML Normalization — 주간보고 HTML 이중 escape 방지

**목표**: 주간보고 작성/수정 저장 시 Quill HTML이 `<p>&lt;p&gt;...` 형태로 이중 escape되어 저장/표시되는 문제를 막는다.

**작업 범위**:

- 주간보고 HTML 정화 유틸에 escaped rich text 입력을 정상 HTML로 되돌리는 정규화 단계를 추가한다.
- `<p>&lt;p&gt;...&lt;/p&gt;</p>`처럼 이미 깨진 저장값도 상세 렌더링 시 정상 문단으로 보정한다.
- `bleach` fallback 환경에서도 HTML 태그 문자열이 그대로 보이지 않도록 plain text 문단으로 변환한다.
- 주간보고 생성 POST 회귀 테스트로 저장값과 상세 렌더링에 `&lt;p&gt;`가 남지 않는지 검증한다.

**DB 변경 필요 여부**: 없음. 기존 `WeeklyReport` 텍스트 필드와 HTML 정화 유틸만 수정한다.

**검증 계획**:

- `python manage.py test reporting.tests.WeeklyReportTests reporting.tests.WeeklyReportLoadSchedulesExtendedTests --verbosity=1`
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `git diff --check`
- 커밋/푸시 후 Railway `web` 서비스 배포 및 운영 `/reporting/weekly-reports/create/` 수동검수 절차 제공
