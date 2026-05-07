# AGENT_PLAN.md

## 프로젝트 개요

**세일즈 노트** — 한국 영업팀을 위한 내부 CRM/SFA 시스템 (Django 5.2.3)

이 시스템은 **공개 마케팅 사이트가 아닙니다**.  
제품 카탈로그, 브랜드 페이지, 공개 홈페이지는 이 프로젝트의 범위 밖입니다.

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
