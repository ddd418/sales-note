# PHASE_7_PLAN.md

## Phase 7 — 보안 강화 / 권한 검증 / 회귀 테스트 / 배포 준비

**날짜**: 2026-04-27  
**상태**: 계획 수립 (코드 미변경)  
**범위**: 보안, 권한, 회귀 테스트, 배포 안정성  
**명시적 비범위**: 신규 비즈니스 기능, UI 리디자인, 마케팅 페이지, 관련 없는 리팩터

---

## 1. 현재 보안 / 권한 구조

### 1.1 인증 구조

| 구성 요소              | 현황                                                                               |
| ---------------------- | ---------------------------------------------------------------------------------- |
| 인증 방식              | Django 기본 세션 인증 (`django.contrib.auth`)                                      |
| 로그인 URL             | `/reporting/login/`                                                                |
| 로그인 후 리다이렉트   | `/reporting/dashboard/`                                                            |
| 커스텀 인증 백엔드     | `reporting.auth_backends.OptimizedAuthBackend` (UserProfile select_related 최적화) |
| 로그아웃 후 리다이렉트 | `/reporting/login/`                                                                |
| CSRF                   | `CsrfViewMiddleware` 활성화, `CSRF_COOKIE_SECURE = not DEBUG`                      |
| 세션 쿠키              | `SESSION_COOKIE_SECURE = not DEBUG`                                                |

### 1.2 권한 계층

| 역할     | role 값      | 설명                                               |
| -------- | ------------ | -------------------------------------------------- |
| Admin    | `'admin'`    | 모든 데이터 읽기/쓰기, 사용자 관리, 엑셀 항상 허용 |
| Manager  | `'manager'`  | 같은 회사 데이터 읽기만 가능, 수정 불가            |
| Salesman | `'salesman'` | 자신의 데이터만 읽기/쓰기                          |

**추가 플래그**

| 플래그               | 기본값  | 비고                                  |
| -------------------- | ------- | ------------------------------------- |
| `can_download_excel` | `False` | Admin은 항상 허용, 나머지는 개별 설정 |
| `can_use_ai`         | `False` | 개별 설정 필요                        |

### 1.3 핵심 권한 함수

| 함수                                              | 위치                      | 역할                                                            |
| ------------------------------------------------- | ------------------------- | --------------------------------------------------------------- |
| `can_access_user_data(request_user, target_user)` | `reporting/views.py:150`  | 데이터 조회 권한 (Admin: 전체, Manager/Salesman: 같은 회사)     |
| `can_modify_user_data(request_user, target_user)` | `reporting/views.py:220`  | 데이터 수정 권한 (Admin: 전체, Manager: 불가, Salesman: 본인만) |
| `can_access_followup(request_user, followup)`     | `reporting/views.py:237`  | 고객 접근 권한                                                  |
| `ai_permission_required` 데코레이터               | `ai_chat/views.py:21`     | `can_use_ai` 플래그 체크                                        |
| `UserProfile.can_excel_download()`                | `reporting/models.py:171` | 엑셀 다운로드 권한                                              |

### 1.4 데코레이터 사용 현황

- `@login_required`: `reporting/views.py` 전체 사용자 접근 뷰에 적용됨 (확인 완료)
- `@login_required` + `@ai_permission_required`: `ai_chat/views.py` 모든 AI 뷰에 적용됨
- `@require_POST`: API 뷰 중 일부에 적용됨 (toggle, sync 등)

### 1.5 회사 필터링 미들웨어

`CompanyFilterMiddleware` (`reporting/middleware.py`):

- Admin: 전체 접근 (세션에서 필터 선택 가능)
- Manager/Salesman: `request.user_company`에 소속 회사 주입
- 세션 캐시 적용 (DB 조회 최소화)

---

## 2. 현재 테스트 커버리지

### 2.1 기존 테스트 (9개 — `reporting/tests.py`)

| 테스트                                            | 클래스                | 내용                      |
| ------------------------------------------------- | --------------------- | ------------------------- |
| `test_login_page_returns_200`                     | `AuthenticationSmoke` | 로그인 페이지 접근        |
| `test_unauthenticated_followup_list_redirects`    | `AuthenticationSmoke` | 비인증 거래처 목록 → 302  |
| `test_login_success`                              | `AuthenticationSmoke` | 올바른 자격으로 로그인    |
| `test_login_fail_wrong_password`                  | `AuthenticationSmoke` | 잘못된 비밀번호 실패      |
| `test_followup_list_authenticated`                | `AuthenticationSmoke` | 인증 후 거래처 목록 200   |
| `test_opportunity_list_authenticated`             | `AuthenticationSmoke` | 인증 후 영업기회 목록 200 |
| `test_opportunity_list_unauthenticated_redirects` | `AuthenticationSmoke` | 비인증 영업기회 → 302     |
| `test_schedule_list_authenticated`                | `AuthenticationSmoke` | 인증 후 일정 목록 200     |
| `test_history_list_authenticated`                 | `AuthenticationSmoke` | 인증 후 활동 목록 200     |

### 2.2 커버리지 분석

**현재 커버된 영역**:

- 로그인/로그아웃 기본 플로우
- 주요 목록 뷰 인증 여부

**현재 미커버 영역** (Phase 7에서 추가 필요):

| 기능 영역     | 미커버 항목                                    |
| ------------- | ---------------------------------------------- |
| 대시보드      | 영업 노트 모달 AJAX, `@never_cache` 동작       |
| 일정/캘린더   | schedule detail 페이지, memo 추가, 파일 업로드 |
| 파이프라인    | auto-sync, manual move, 권한 체크              |
| 주간보고      | 일정 불러오기 API, 매니저 코멘트 권한          |
| 문서          | template data API, document 생성 권한 체크     |
| AI 분석       | `can_use_ai=False` 차단, 권한 없는 부서 접근   |
| 내보내기      | CSV/XLSX admin/manager 전용 권한 체크          |
| 파일 다운로드 | 권한 체크, company 격리                        |
| 선결제        | 고객 엑셀 권한 체크                            |
| 관리자 기능   | is_manager 전용 뷰 salesman 차단               |

---

## 3. Phase 6.5 / 6.6 이후 고위험 영역

### 3.1 Phase 6.5에서 추가된 기능 (위험 우선순위: 높음)

| 기능                         | 위험 항목                                                                 |
| ---------------------------- | ------------------------------------------------------------------------- |
| AI 분석에 선결제 데이터 포함 | 다른 회사 데이터가 분석에 포함될 수 있음                                  |
| analytics CSV/XLSX export    | role 체크가 문자열 비교 `('admin', 'manager', 'superadmin')`로 하드코딩됨 |
| 주간보고 AI 초안 생성        | `can_use_ai` 체크는 있으나, 다른 사용자 데이터 격리 미확인                |
| 파이프라인 sync API          | POST 전용 + login_required 있음, CSRF 동작 확인 필요                      |

### 3.2 Phase 6.6에서 추가된 기능 (위험 우선순위: 중간)

| 기능                                     | 위험 항목                                                              |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| 대시보드 영업 노트 모달                  | AJAX CSRF 토큰 처리 방식 (폴백 경로 존재)                              |
| schedule_detail.html `previewDocument()` | XSS 수정 완료 (Phase 6.6 QA)                                           |
| `get_document_template_data`             | 회사별 template 격리 (company 필터 있음), schedule.user 권한 체크 있음 |
| `weekly_report_load_schedules`           | `user=request.user` 필터 있음, 타인 데이터 격리 확인 필요              |

### 3.3 기존 구조 위험 항목

| 항목                                                      | 위치                           | 위험 수준                                                   |
| --------------------------------------------------------- | ------------------------------ | ----------------------------------------------------------- |
| `debug_user_company_info` 뷰                              | `views.py:10026`               | 낮음 (superuser 전용이나 디버그용 엔드포인트 존재)          |
| `settings.py` 개발용 `SECRET_KEY` 하드코딩                | `sales_project/settings.py:13` | 중간 (개발 전용이지만 코드에 노출)                          |
| `EMAIL_ENCRYPTION_KEY` 환경변수 미설정 시 Base64 fallback | `settings_production.py:243`   | 높음 (fallback이 고정값이면 암호화 무력화)                  |
| `CSRF_COOKIE_HTTPONLY = False`                            | `settings_production.py:53`    | 중간 (JS에서 CSRF 토큰 읽기 위한 것이지만 XSS 시 노출 위험) |
| `SECURE_HSTS_SECONDS` 미설정                              | `settings_production.py`       | 중간 (HTTPS 강제 미설정)                                    |
| `followup_basic_excel_download` 권한 체크                 | `views.py:7843`                | 확인 필요                                                   |
| Manager가 타사 데이터 접근 가능한지                       | `can_access_user_data`         | `같은 회사` 조건 있으나, company=None인 경우 처리 확인 필요 |
| `schedule_file_download` 응답 error 문자열 노출           | `file_views.py:213`            | 낮음 (내부 에러 메시지 HTTP 응답에 포함)                    |

---

## 4. 회귀 테스트 계획

### 4.1 대시보드 영업 노트 모달 테스트

**테스트 목표**: Phase 6.6-1 수정 이후 모달 정상 작동 확인

| 테스트 케이스                                                      | 기대 결과                       |
| ------------------------------------------------------------------ | ------------------------------- |
| GET `/reporting/dashboard/` → 200 응답                             | ✅                              |
| 응답에 `dashboardNoteModal` 포함                                   | ✅                              |
| 응답에 `block modals` 중복 없음                                    | ✅ (Phase 6.6 QA에서 수정 완료) |
| POST `/reporting/histories/create-from-schedule/<id>/` — 인증 없이 | 302 리다이렉트                  |
| POST 노트 AJAX — CSRF 토큰 누락                                    | 403 응답                        |

**구현 위치**: `reporting/tests.py` → `DashboardSmokeTests` 클래스

---

### 4.2 캘린더 일정 / 메모 테스트

**테스트 목표**: schedule_detail 접근 권한 및 memo 추가 권한 확인

| 테스트 케이스                                             | 기대 결과                      |
| --------------------------------------------------------- | ------------------------------ |
| 자신의 schedule_detail 200 응답                           | ✅                             |
| 타 사용자 schedule_detail — Salesman 접근                 | 403 또는 404                   |
| 같은 회사 Manager가 타 Salesman schedule_detail           | 200 (읽기 허용)                |
| `schedule_add_memo_api` — Manager가 POST                  | 200 (manager만 memo 추가 가능) |
| `schedule_add_memo_api` — Salesman이 타인 schedule에 POST | 403                            |

**구현 위치**: `reporting/tests.py` → `SchedulePermissionTests` 클래스

---

### 4.3 파이프라인 auto-generation / manual movement 테스트

**테스트 목표**: Phase 6.6-2 `funnel_pipeline_sync` 정상 동작 확인

| 테스트 케이스                                                       | 기대 결과                  |
| ------------------------------------------------------------------- | -------------------------- |
| GET `/reporting/funnel/pipeline/` — 인증 후 200                     | ✅                         |
| POST `/reporting/funnel/api/pipeline-sync/` — 인증 없이             | 302                        |
| POST `/reporting/funnel/api/pipeline-sync/` — 인증 후               | 200 JSON                   |
| POST `/reporting/funnel/api/pipeline-move/` — 타 사용자 opportunity | 403 또는 permission denied |

**구현 위치**: `reporting/tests.py` → `PipelineTests` 클래스

---

### 4.4 주간보고 일정/히스토리 불러오기 테스트

**테스트 목표**: Phase 6.6-3 `weekly_report_load_schedules` 데이터 격리 확인

| 테스트 케이스                                                                         | 기대 결과                     |
| ------------------------------------------------------------------------------------- | ----------------------------- |
| GET `/reporting/weekly-reports/load-schedules/?week_start=...&week_end=...` — 인증 후 | 200 JSON, `schedules` 키 있음 |
| 응답 data에 타 사용자 일정 포함 여부                                                  | 타 사용자 일정 없어야 함      |
| 날짜 파라미터 누락 또는 잘못된 값                                                     | 400 오류                      |
| POST `/reporting/weekly-reports/manager-comment/<pk>/` — Manager가                    | 200                           |
| POST `/reporting/weekly-reports/manager-comment/<pk>/` — Salesman이                   | 403                           |

**구현 위치**: `reporting/tests.py` → `WeeklyReportTests` 클래스

---

### 4.5 문서 생성 및 파일 업로드 테스트

**테스트 목표**: Phase 6.6-4 `get_document_template_data` 권한 및 데이터 격리 확인

| 테스트 케이스                                                              | 기대 결과     |
| -------------------------------------------------------------------------- | ------------- |
| GET `/reporting/documents/template-data/quotation/<id>/` — 자신의 schedule | 200 JSON      |
| GET 타 사용자(다른 회사) schedule id로 접근                                | 403           |
| `document_template_download` — 타 회사 template pk로 접근                  | 에러 또는 403 |
| `schedule_file_upload` — 자신의 schedule에 파일 업로드                     | 200           |
| `schedule_file_upload` — 타인의 schedule에 Salesman이 접근                 | 403           |
| 허용 확장자 외 파일 업로드 시도                                            | 400           |
| 10MB 초과 파일 업로드 시도                                                 | 400           |

**구현 위치**: `reporting/tests.py` → `DocumentTests` 클래스

---

### 4.6 AI 분석 및 선결제 데이터 테스트

**테스트 목표**: AI 기능 권한 차단 및 데이터 격리 확인

| 테스트 케이스                                        | 기대 결과                      |
| ---------------------------------------------------- | ------------------------------ |
| `can_use_ai=False` 사용자가 `/ai/departments/` 접근  | 대시보드로 리다이렉트 + 메시지 |
| `can_use_ai=True` 사용자가 `/ai/departments/` 접근   | 200                            |
| `run_analysis` — 자신의 department에                 | 200 JSON                       |
| `run_analysis` — 타 사용자 department에              | 403 또는 NotFound              |
| `weekly_report_ai_draft` — `can_use_ai=False` 사용자 | 403                            |
| AI 분석 데이터에 타 회사 고객 포함 여부              | 타 회사 데이터 없어야 함       |

**구현 위치**: `reporting/tests.py` → `AIPermissionTests` 클래스

---

### 4.7 analytics / CSV / XLSX export 테스트

**테스트 목표**: admin/manager 전용 export 권한 차단 확인

| 테스트 케이스                                                           | 기대 결과                  |
| ----------------------------------------------------------------------- | -------------------------- |
| GET `/reporting/analytics/` — Salesman 접근                             | 200 (본인 데이터만)        |
| GET `/reporting/analytics/activity-csv/` — Salesman 접근                | 403                        |
| GET `/reporting/analytics/activity-csv/` — Manager 접근                 | 200, CSV 파일              |
| GET `/reporting/analytics/activity-xlsx/` — Admin 접근                  | 200, XLSX 파일             |
| GET `/reporting/analytics/pipeline-csv/` — Salesman 접근                | 403                        |
| GET `/reporting/followups/excel-download/` — `can_download_excel=False` | 거래처 목록으로 리다이렉트 |
| GET `/reporting/followups/excel-download/` — Admin 접근                 | 200, XLSX 파일             |

**구현 위치**: `reporting/tests.py` → `ExportPermissionTests` 클래스

---

## 5. 권한 테스트 계획

### 5.1 익명(Anonymous) 사용자

| URL                                  | 기대 결과                 |
| ------------------------------------ | ------------------------- |
| `/`                                  | 302 → `/reporting/login/` |
| `/reporting/dashboard/`              | 302 → 로그인              |
| `/reporting/followups/`              | 302 → 로그인              |
| `/reporting/histories/`              | 302 → 로그인              |
| `/reporting/schedules/`              | 302 → 로그인              |
| `/reporting/opportunities/`          | 302 → 로그인              |
| `/reporting/weekly-reports/`         | 302 → 로그인              |
| `/reporting/analytics/`              | 302 → 로그인              |
| `/reporting/funnel/pipeline/`        | 302 → 로그인              |
| `/reporting/documents/`              | 302 → 로그인              |
| `/reporting/analytics/activity-csv/` | 302 → 로그인              |
| `/ai/departments/`                   | 302 → 로그인              |

---

### 5.2 일반 영업 사용자 (role='salesman', `can_use_ai=False`, `can_download_excel=False`)

| 기능                           | 기대 결과                            |
| ------------------------------ | ------------------------------------ |
| 대시보드 접근                  | 200, 본인 데이터 표시                |
| 타 사용자 history_detail 접근  | 같은 회사면 200, 다른 회사면 403/404 |
| 타 사용자 schedule_detail 접근 | 같은 회사면 200, 다른 회사면 403/404 |
| 타 사용자 history 수정         | 403 또는 리다이렉트                  |
| AI 기능 (`/ai/departments/`)   | 대시보드 리다이렉트                  |
| analytics CSV export           | 403                                  |
| followup excel download        | 리다이렉트                           |
| manager comment POST           | 403                                  |
| schedule add_memo POST         | 403                                  |

---

### 5.3 매니저 사용자 (role='manager')

| 기능                                 | 기대 결과                              |
| ------------------------------------ | -------------------------------------- |
| 타 사용자(같은 회사) history_detail  | 200                                    |
| 타 사용자(같은 회사) schedule_detail | 200                                    |
| 타 사용자 history 수정               | 403 (manager는 수정 불가)              |
| analytics CSV/XLSX export            | 200 (manager 허용)                     |
| followup excel download              | 200 (manager는 admin 수준) — 확인 필요 |
| schedule add_memo POST               | 200 (manager만 memo 추가 가능)         |
| weekly report manager comment        | 200                                    |
| 다른 회사 데이터 접근                | 403/404                                |

---

### 5.4 어드민 사용자 (role='admin')

| 기능                                     | 기대 결과                |
| ---------------------------------------- | ------------------------ |
| 모든 회사 데이터 조회                    | 200                      |
| 모든 회사 데이터 수정                    | 200                      |
| 사용자 생성/편집                         | 200                      |
| excel download (can_download_excel 무관) | 200                      |
| analytics export                         | 200                      |
| debug_user_company_info                  | 200 (superuser인 경우만) |

---

## 6. 데이터 노출 위험

### 6.1 높은 위험

| 항목                                                  | 설명                                                                                       | 권장 조치                         |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------- |
| `can_access_user_data`에서 `company=None` 사용자 처리 | 두 사용자 모두 `company=None`이면 `None == None`이 True → 크로스 접근 가능                 | 명시적 None 체크 추가             |
| AI 분석 `gather_meeting_data`에서 user 필터만 적용    | 같은 회사의 다른 사용자 데이터는 포함되지 않음 → 비정상적이지는 않지만 검증 필요           | 회사 격리 로직 검토               |
| `EMAIL_ENCRYPTION_KEY` fallback 고정값                | 환경변수 미설정 시 Base64 하드코딩 키로 IMAP/SMTP 비밀번호 암호화 → 실질적으로 평문과 동일 | 환경변수 강제 요구 또는 경고 로그 |
| `followup_basic_excel_download` 권한 체크 미확인      | 별도 권한 체크 없이 login만으로 접근 가능한지 확인 필요                                    | 뷰 코드 검토 및 권한 체크 추가    |

### 6.2 중간 위험

| 항목                                      | 설명                                                                   | 권장 조치                                       |
| ----------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------- |
| `CSRF_COOKIE_HTTPONLY = False`            | JS에서 CSRF 토큰 읽기 위한 설정이지만, XSS 발생 시 CSRF 토큰 탈취 가능 | 현재 운영 필요로 유지하되, XSS 방지 강화로 보완 |
| `SECURE_HSTS_SECONDS` 미설정              | HTTPS 강제 미설정 → HTTP downgrade 공격 가능                           | 배포 환경 확인 후 설정                          |
| 개발 `SECRET_KEY` 코드 노출               | `settings.py:13`에 `django-insecure-...` 하드코딩                      | `.env` 파일로 분리 또는 주석으로 명확화         |
| `debug_user_company_info` 엔드포인트 존재 | superuser 전용이나 내부 시스템 정보 노출 가능                          | 필요 없으면 제거, 필요하면 유지                 |

### 6.3 낮은 위험

| 항목                                                     | 설명                                                         | 권장 조치               |
| -------------------------------------------------------- | ------------------------------------------------------------ | ----------------------- |
| `schedule_file_download` 에러 메시지 HTTP 응답 직접 노출 | `HttpResponse(f'...{str(e)}...')` → 내부 스택 정보 노출 가능 | 일반 에러 메시지로 대체 |
| 로그인 실패 응답에서 사용자 존재 여부 추론               | 현재 django 기본 메시지 사용 — 표준이라 괜찮지만 확인 필요   | 확인만                  |

---

## 7. 파일 업로드 및 문서 접근 위험

| 위험 항목                                     | 위치                                                 | 현황                                                                       | 권장 조치                                                                    |
| --------------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 파일 확장자 화이트리스트                      | `validate_file_upload()` / `schedule_file_upload()`  | 양쪽에 허용 확장자 목록이 별도 정의되어 일관성 문제                        | `validate_file_upload()` 단일 소스로 통일 (이미 Phase 5에서 시작, 확인 필요) |
| MIME 타입 검증 없음                           | `validate_file_upload()`                             | 확장자만 체크, 실제 파일 내용 미확인                                       | `python-magic` 또는 파일 시그니처 검증 추가 권장                             |
| 파일 크기 제한 이중 적용                      | `validate_file_upload()` vs `schedule_file_upload()` | 10MB 동일하지만 별도 구현                                                  | 통일화                                                                       |
| Cloudinary URL 직접 리다이렉트                | `document_template_download()`                       | 인증 없이 Cloudinary URL 접근 가능한지                                     | Cloudinary 설정으로 제어 (Django 외부)                                       |
| 로컬 파일 `FileResponse(open(...))` 경로 노출 | `file_views.py`, `document_template_download()`      | Django `get_object_or_404`로 pk 먼저 검증하므로 직접 path traversal은 없음 | 확인 수준                                                                    |
| `ScheduleFile.file.read()` 전체 메모리 로드   | `file_views.py:208`                                  | 큰 파일의 경우 메모리 이슈                                                 | `FileResponse`로 변경 권장                                                   |

---

## 8. CSV / XLSX export 위험

| 위험 항목                                 | 위치                                 | 현황                                                                                      | 권장 조치                                          |
| ----------------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------- | -------------------------------------------------- |
| role 체크 하드코딩 문자열                 | `analytics_activity_csv_export()` 등 | `role not in ('admin', 'manager', 'superadmin')` — superadmin role이 모델에 정의되지 않음 | `is_admin()` / `is_manager()` 메서드 사용으로 통일 |
| `followup_basic_excel_download` 권한 체크 | `views.py:7843`                      | 별도 권한 체크 확인 필요                                                                  | 코드 검토 후 `can_excel_download()` 적용           |
| CSV/XLSX 파일명 인코딩                    | `Content-Disposition` 헤더           | 한국어 파일명 포함, RFC 5987 `filename*` 인코딩 미사용                                    | 호환성 확인                                        |
| 데이터 필터링 보장                        | Manager가 다른 회사 데이터 export    | `user_profile.company` 기반 필터링 확인 필요                                              | 각 export 뷰의 쿼리 검토                           |

---

## 9. AI 분석 프라이버시 위험

| 위험 항목                                | 현황                                  | 권장 조치                                                  |
| ---------------------------------------- | ------------------------------------- | ---------------------------------------------------------- |
| 외부 OpenAI API로 고객 데이터 전송       | 고객명, 미팅 내용, 견적 정보 포함     | 전송 전 민감 데이터 마스킹 정책 필요 (현재 없음)           |
| AI 분석 결과의 회사 격리                 | `AIDepartmentAnalysis.user` 기반 조회 | 다른 회사 user가 같은 department에 접근 가능한지 확인 필요 |
| `gather_meeting_data` 타 사용자 데이터   | `user=request.user` 필터 있음         | 정상이나 department별 전체 데이터 분석 시 격리 확인        |
| `gather_quote_delivery_data` 데이터 범위 | department 기준 필터                  | department가 여러 회사에 걸쳐 있을 경우 확인 필요          |
| AI 응답 오류 메시지                      | `ValueError` 포함한 에러 client 반환  | OpenAI 내부 메시지 노출 방지 필요                          |

---

## 10. 배포 준비 체크리스트

### 10.1 보안 설정

| 항목                                 | 현황                                                            | 조치                                         |
| ------------------------------------ | --------------------------------------------------------------- | -------------------------------------------- |
| `SECRET_KEY` 환경변수 강제           | ✅ `settings_production.py`에서 미설정 시 `RuntimeError`        | 완료                                         |
| `DEBUG=False` (프로덕션)             | ✅ `DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'` | 완료                                         |
| `ALLOWED_HOSTS` 와일드카드 제거      | ✅ Railway 도메인만 허용                                        | 완료                                         |
| `CSRF_COOKIE_SECURE`                 | ✅ `not DEBUG`                                                  | 완료                                         |
| `SESSION_COOKIE_SECURE`              | ✅ `not DEBUG`                                                  | 완료                                         |
| `SECURE_HSTS_SECONDS`                | ❌ 미설정                                                       | 권장: `31536000` (1년)                       |
| `SECURE_SSL_REDIRECT`                | ❌ 미설정                                                       | Railway에서 HTTPS 강제 여부 확인 후 설정     |
| `SECURE_CONTENT_TYPE_NOSNIFF`        | ❌ 미설정                                                       | 권장 추가                                    |
| `X_FRAME_OPTIONS`                    | Django 기본 `DENY` (미들웨어 포함)                              | ✅                                           |
| `EMAIL_ENCRYPTION_KEY` fallback 제거 | ❌ Base64 하드코딩 fallback 존재                                | 환경변수 없을 때 RuntimeError 또는 경고 필요 |

### 10.2 정적 파일 / 미디어

| 항목               | 현황                                      | 조치                      |
| ------------------ | ----------------------------------------- | ------------------------- |
| `collectstatic`    | ✅ 완료                                   | —                         |
| WhiteNoise 설정    | ✅ `CompressedManifestStaticFilesStorage` | 완료                      |
| 미디어 파일 저장소 | Railway Volume `/data/media`              | Volume mount 확인 필요    |
| Cloudinary 연동    | ✅ 문서 템플릿용                          | API 키 환경변수 설정 확인 |

### 10.3 데이터베이스

| 항목                      | 현황                                             | 조치                              |
| ------------------------- | ------------------------------------------------ | --------------------------------- |
| PostgreSQL 연결 (Railway) | ✅ `dj_database_url` 사용                        | `DATABASE_URL` 환경변수 설정 확인 |
| 마이그레이션 상태         | ✅ 최신 (`0090_add_weekly_report_review_fields`) | 배포 시 `migrate` 실행 확인       |
| `conn_max_age=600`        | ✅ 연결 재사용 설정                              | 완료                              |

### 10.4 운영 안정성

| 항목                              | 현황                              | 조치                           |
| --------------------------------- | --------------------------------- | ------------------------------ |
| 로깅 설정                         | ✅ console handler, INFO 레벨     | 완료                           |
| 에러 추적 (Sentry 등)             | ❌ 미설정                         | 권장: Sentry DSN 환경변수 설정 |
| `PerformanceMonitoringMiddleware` | 프로덕션에서 주석 처리됨          | 필요 시 활성화                 |
| Celery (비동기 태스크)            | `celery_settings_append.txt` 존재 | 실제 Celery 사용 여부 확인     |

### 10.5 기능 검증

| 항목                               | 조치                          |
| ---------------------------------- | ----------------------------- |
| `python manage.py check`           | Phase 7 구현 전후로 실행      |
| `python manage.py migrate --check` | 미적용 마이그레이션 확인      |
| 전체 테스트 스위트                 | 테스트 추가 후 모두 통과 확인 |

---

## 11. 권장 구현 순서

### Priority 1 — 고위험 보안 수정 (즉시)

1. **`can_access_user_data` company=None 처리**: 두 사용자 모두 `company=None`이면 다른 사람인데도 같은 회사로 판단되는 버그 수정
2. **`EMAIL_ENCRYPTION_KEY` fallback 제거**: 환경변수 미설정 시 경고 + fallback 제거
3. **analytics export role 체크 통일**: `role not in ('admin','manager','superadmin')` → `user_profile.is_admin() or user_profile.is_manager()`
4. **`followup_basic_excel_download` 권한 체크 확인/추가**

### Priority 2 — 테스트 작성 (핵심)

5. **회귀 테스트 클래스 추가** (`DashboardSmokeTests`, `SchedulePermissionTests`, `PipelineTests`, `WeeklyReportTests`, `DocumentTests`, `AIPermissionTests`, `ExportPermissionTests`)
6. **익명 사용자 전체 URL 차단 테스트**
7. **Manager/Salesman 권한 분리 테스트**

### Priority 3 — 배포 보안 강화 (배포 전)

8. **`SECURE_HSTS_SECONDS` / `SECURE_SSL_REDIRECT` / `SECURE_CONTENT_TYPE_NOSNIFF` 설정**
9. **`ScheduleFile.file.read()` → `FileResponse` 변경** (메모리 이슈 방지)
10. **파일 업로드 확장자 검증 단일 소스 통일** (schedule_file_upload에서 `validate_file_upload` 함수 사용)

### Priority 4 — 선택적 개선

11. **에러 응답 메시지 표준화** (내부 에러 미노출)
12. **debug_user_company_info 제거 또는 관리 UI로 이동**
13. **AI 분석 전송 데이터 마스킹 정책 수립**

---

## 12. 변경 예상 파일

| 파일                                   | 예상 변경 내용                                                            |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `reporting/tests.py`                   | 회귀 테스트 클래스 7개 추가                                               |
| `reporting/views.py`                   | `can_access_user_data` company=None 처리, analytics export role 체크 통일 |
| `reporting/file_views.py`              | `schedule_file_download` → `FileResponse` 변경, 에러 메시지 표준화        |
| `sales_project/settings_production.py` | HSTS/SSL 보안 헤더 추가, EMAIL_ENCRYPTION_KEY fallback 제거               |
| `reporting/views.py`                   | `followup_basic_excel_download` 권한 체크 확인/추가                       |

---

## 13. 검증 명령어

```bash
# 1. Django 시스템 체크
python manage.py check

# 2. 마이그레이션 체크 (모델 변경 없음 확인)
python manage.py makemigrations --check --dry-run

# 3. 전체 테스트 실행
python manage.py test reporting.tests --verbosity=2

# 4. 특정 테스트 클래스 실행 (추가 후)
python manage.py test reporting.tests.PermissionTests --verbosity=2
python manage.py test reporting.tests.ExportPermissionTests --verbosity=2

# 5. 보안 배포 체크 (프로덕션 설정 기준)
RAILWAY_ENVIRONMENT=1 python manage.py check --deploy

# 6. 정적 파일 수집
python manage.py collectstatic --noinput
```

---

## 14. 알려진 제한 사항

1. **MIME 타입 실제 검증 없음**: 파일 확장자만으로 체크 → 악성 파일 업로드 위험은 남아 있음
2. **Cloudinary URL 직접 접근**: Django 인증 외부에서 Cloudinary URL이 노출되면 파일 다운로드 가능
3. **AI 분석 외부 API 전송**: OpenAI로 고객 데이터 전송에 대한 데이터 처리 정책 문서 없음
4. **`superadmin` role**: 코드에서 참조되지만 `ROLE_CHOICES`에 없음 (`'admin'`으로 통일 필요)

---

## 15. 다음 Phase 준비 참고

Phase 7 완료 기준:

- [ ] Priority 1 버그 4개 수정 완료
- [ ] 테스트 30개 이상 통과
- [ ] `manage.py check --deploy` 경고 0개
- [ ] AGENT_REPORT.md Phase 7 섹션 업데이트 완료
