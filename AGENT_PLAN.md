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

**Phase 7 계획 중** (2026-04-25)

권장 실행 순서: Phase 7C (빠른 정리) → Phase 7A (영업기회 CRUD) → Phase 7B (테스트)
