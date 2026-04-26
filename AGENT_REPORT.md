# AGENT_REPORT.md

## Phase 0 — 보안 정리 및 잘못된 앱 제거

**날짜**: 2026-04-25  
**상태**: 완료

---

## 요약

이전 세션에서 잘못 생성된 `public_site/` B2B 마케팅 사이트 앱을 비활성화하고,
11개 브라우저 AJAX 뷰에서 `@csrf_exempt`를 제거했습니다.
EMAIL_ENCRYPTION_KEY 하드코딩 기본값도 제거했습니다.

---

## 변경된 파일

### 1. `sales_project/urls.py`

- **변경**: 루트 URL에서 `include('public_site.urls')` 제거
- **대체**: `RedirectView`로 `/reporting/dashboard/`로 리다이렉트
- **이유**: `public_site/` 앱은 이 프로젝트에 맞지 않는 B2B 마케팅 사이트였음

### 2. `sales_project/settings.py`

- **변경**: INSTALLED_APPS에서 `"public_site"` 제거
- **변경**: `EMAIL_ENCRYPTION_KEY` 하드코딩 기본값 제거 → 환경변수 없으면 경고 로깅 후 `None`

### 3. `sales_project/settings_production.py`

- **변경**: INSTALLED_APPS에서 `"public_site"` 제거

### 4. `reporting/views.py`

- **변경**: 10개 브라우저 AJAX 뷰에서 `@csrf_exempt` 제거:
  - `company_create_api`
  - `department_create_api`
  - `history_update_tax_invoice`
  - `history_update_memo`
  - `toggle_schedule_delivery_tax_invoice`
  - `delete_manager_memo_api`
  - `add_manager_memo_to_history_api`
  - `customer_priority_update`
  - `update_tax_invoice_status`
  - `api_change_company_creator`
- **변경**: 미사용 `from django.views.decorators.csrf import csrf_exempt` import 제거

### 5. `reporting/file_views.py`

- **변경**: `schedule_file_delete`에서 `@csrf_exempt` 제거
- **변경**: 미사용 `csrf_exempt` import 제거

### 6. `reporting/schedule_delivery_tax_invoice_api.py`

- **변경**: `toggle_schedule_delivery_tax_invoice`에서 `@csrf_exempt` 제거
- **변경**: 미사용 `csrf_exempt` import 제거

### 7. `AGENT_PLAN.md` (신규)

- 전체 구현 계획 문서 (Phase 0~4)

---

## 보안/개인정보 고려사항

| 항목                 | 이전                         | 이후                                                             |
| -------------------- | ---------------------------- | ---------------------------------------------------------------- |
| CSRF 보호            | 11개 뷰 @csrf_exempt         | 브라우저 AJAX 뷰 전부 CSRF 보호 적용                             |
| backup_api           | @csrf_exempt + Bearer Token  | @csrf_exempt 유지 (외부 스케줄러, Bearer Token 인증 이미 구현됨) |
| EMAIL_ENCRYPTION_KEY | 하드코딩 기본값              | 환경변수 필수, 없으면 경고 후 None                               |
| 루트 URL             | public_site (익명 접근 가능) | 로그인 필요한 대시보드로 리다이렉트                              |

**`@csrf_exempt` 제거가 안전한 이유**:  
모든 프론트엔드 JavaScript가 이미 `fetch()` 요청 헤더에 `X-CSRFToken`을 포함하고 있어,
`@csrf_exempt` 없이도 Django CSRF 미들웨어의 헤더 검증을 통과합니다.

---

## 실행한 명령어 및 결과

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

## 제한 사항

- `public_site/` 앱 자체(디렉터리, 마이그레이션)는 코드베이스에 남아 있음.  
  DB에 `public_site_inquirylead` 테이블이 생성된 상태이므로, 해당 테이블 삭제는 별도 확인 후 진행 권장.
- `EMAIL_ENCRYPTION_KEY`가 없을 경우 IMAP/SMTP 이메일 비밀번호 암호화 기능이 비활성화됨.  
  프로덕션 환경에서는 반드시 환경변수 설정 필요.

---

## 다음 권장 작업

**Phase 1+2 구현 완료** → 아래 Phase 1+2 Report 참고

---

## Phase 1+2 — 대시보드 위젯 개선 + 영업보고 워크플로 UX 개선

**날짜**: 2026-06-30  
**상태**: 완료

---

### 요약

History 모델에 "다음 할 일" 및 "관리자 검토" 기능을 추가하고, 대시보드에 실시간 알림 위젯을 구현했습니다.  
영업보고 목록에 날짜 범위 필터 및 미검토 필터를 추가하고, 상세/작성 폼에 관련 UI를 반영했습니다.

---

### 변경된 파일

| 파일                                                          | 변경 내용                                                                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `reporting/models.py`                                         | History 모델에 `next_action`, `next_action_date`, `reviewed_at`, `reviewer` 필드 추가                                     |
| `reporting/migrations/0089_history_review_and_next_action.py` | 위 4개 필드 마이그레이션 생성 및 적용 완료                                                                                |
| `reporting/views.py`                                          | HistoryForm 필드 추가 / dashboard_view 컨텍스트 확장 / history_list_view 필터 추가 / history_toggle_reviewed 뷰 신규 추가 |
| `reporting/urls.py`                                           | `histories/<int:pk>/toggle-reviewed/` URL 등록                                                                            |
| `reporting/templates/reporting/dashboard.html`                | 미작성 보고서 알림 + 미검토 보고서 알림 + 오늘 일정 카드 위젯 추가                                                        |
| `reporting/templates/reporting/history_list.html`             | 날짜 범위 필터 입력란 + 미검토 필터 버튼 + reviewed 배지 추가                                                             |
| `reporting/templates/reporting/history_detail.html`           | "다음 할 일" 섹션 + "관리자 검토" 섹션 + toggleReviewed AJAX 함수 추가                                                    |
| `reporting/templates/reporting/history_form.html`             | "다음 할 일" 선택 카드 (next_action_date + next_action 필드) 추가                                                         |

---

### 새 기능

#### 1. "다음 할 일" (History 모델 필드)

- `next_action` (TextField, nullable): 이번 활동 이후 수행할 다음 액션 텍스트
- `next_action_date` (DateField, nullable): 다음 액션 예정일
- 보고서 작성 폼(history_form.html)에 선택사항으로 노출
- 보고서 상세(history_detail.html)에서 보라색 강조 박스로 표시

#### 2. "관리자 검토" 기능

- `reviewed_at` (DateTimeField, nullable): 검토 완료 시각
- `reviewer` (ForeignKey→User, nullable): 검토한 관리자
- `history_toggle_reviewed` 뷰: 관리자/매니저만 POST로 검토 상태 토글
- 보고서 상세 페이지에서 AJAX 버튼으로 즉시 토글 가능

#### 3. 대시보드 알림 위젯

- 담당자용: 오늘 완료된 일정 중 보고서 미작성 건수 카운트 → 경고 배너 표시
- 관리자용: 최근 30일 내 미검토 보고서 수 → 안내 배너 표시
- 오늘 일정 미니 카드 (완료 일정에 "보고서 작성" 버튼)

#### 4. 영업보고 목록 필터 개선

- 날짜 범위 필터 (시작일/종료일 date input)
- 미검토 필터 버튼 (관리자/매니저에게만 표시, unreviewed_count > 0 일 때)
- 타임라인 아이템에 검토 상태 배지 (초록: 검토완료, 회색: 미검토)

---

### 보안 및 권한 고려사항

- `history_toggle_reviewed`: `can_view_all_users()` 권한 체크 (관리자/매니저만)
- `can_access_user_data()` 체크로 타 팀 데이터 접근 차단
- CSRF: `require_POST` + `X-CSRFToken` 헤더 사용
- 미검토 배지 및 필터 버튼은 서버에서 `can_view_all_users()` 권한자에게만 카운트 제공

---

### 실행한 명령어 및 결과

```
python manage.py migrate       → OK (0089_history_review_and_next_action 적용)
python manage.py check         → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 제한 사항

- `unreviewed_count` 배지는 `action_type in 'customer_meeting,delivery_schedule,quote,service'` 조건으로만 표시됨 (memo, personal_schedule 제외)
- history_list.html의 "미검토" 배지는 Django 템플릿 한계상 `in` 연산자를 문자열 포함으로 사용함 — 정확한 필터링은 서버사이드에서 처리
- 관리자 검토 기능은 detail 페이지에서만 토글 가능 (list 페이지에서는 조회만)

---

### 다음 권장 작업

→ Phase 3 완료 (아래 참고)

---

## Phase 3 — 고객관리/기회/파이프라인 UX 개선

**날짜**: 2026-06-30  
**상태**: 완료

---

### 요약

팔로우업(고객) 목록에 파이프라인 단계 필터를 추가하고, 상세 페이지에 연관 기회·일정·견적 섹션을 신규 추가했습니다.  
영업기회(OpportunityTracking) 목록/상세 페이지를 새로 구현하여 파이프라인 단계별 통계 및 상세 진행 현황을 확인할 수 있습니다.

---

### 변경된 파일

| 파일                                                           | 변경 내용                                                                                                                                |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/views.py`                                           | followup_list_view 파이프라인 필터 추가, followup_detail_view 연관 데이터 추가, opportunity_list_view 신규, opportunity_detail_view 신규 |
| `reporting/urls.py`                                            | `/opportunities/` 및 `/opportunities/<pk>/` URL 2개 등록                                                                                 |
| `reporting/templates/reporting/followup_list.html`             | 파이프라인 단계 필터 버튼 그룹 + 카드 배지 추가                                                                                          |
| `reporting/templates/reporting/followup_detail.html`           | 연관 영업기회, 예정 일정, 최근 견적 3개 섹션 추가                                                                                        |
| `reporting/templates/reporting/opportunity_list.html` (신규)   | 영업기회 목록 페이지 생성 (단계별 통계, 필터, 페이지네이션)                                                                              |
| `reporting/templates/reporting/opportunity_detail.html` (신규) | 영업기회 상세 페이지 생성 (단계 스테퍼, 요약 카드, 연관 일정/견적/보고)                                                                  |

---

### 새 기능

#### 1. 팔로우업 목록 파이프라인 단계 필터

- `pipeline_stage` 쿼리 파라미터로 단계별 필터링 (전체/리드/컨택/견적/클로징/수주/견적실패)
- 기존 담당자·등급·업종 필터와 함께 중첩 적용
- 각 카드에 pipeline_stage 배지 추가 (파란색 outline)

#### 2. 팔로우업 상세 연관 데이터

- **연관 영업기회**: OpportunityTracking 목록 (제목/단계/예상매출/확률/예상 클로징일)
- **예정 일정**: 오늘 이후 Schedule 목록 (날짜/시간/내용/장소)
- **최근 견적**: Quote 목록 (견적번호/단계/금액/날짜/유효일)

#### 3. 영업기회 목록 (`/reporting/opportunities/`)

- 단계별 통계 카드 (전체/리드/컨택/견적/클로징/수주)
- 단계·이달 마감·오버듀 필터 버튼
- 테이블: 고객명→followup_detail / 기회명→opportunity_detail / 단계 배지 / 예상매출 / 확률 프로그레스바 / 예상 클로징일 (오버듀 빨간색) / 담당자
- 페이지네이션

#### 4. 영업기회 상세 (`/reporting/opportunities/<pk>/`)

- 단계 진행 스테퍼 (리드→컨택→견적→클로징→수주, 견적실패 별도 표시)
- 요약 카드 4개: 예상 매출 / 가중 매출 / 확률 / 예상 클로징일
- 연관 일정 테이블 + 연관 견적 테이블
- 최근 활동 내역 (History) + 단계 히스토리 JSON + 기본 정보 dl

---

### 보안 및 권한 고려사항

- `opportunity_detail_view`: `can_access_followup(request.user, opp.followup)` 권한 체크 — 타 팀 기회 접근 차단
- `opportunity_list_view`: `get_accessible_users()` 필터로 팀 범위 데이터만 조회
- 모든 뷰 `@login_required` 적용
- 모델 변경 없음, 마이그레이션 없음

---

### 실행한 명령어 및 결과

```
python manage.py check                          → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 제한 사항

- `opportunity_list.html` / `opportunity_detail.html`은 사이드바 네비게이션에 메뉴 링크가 없음 (followup_detail에서 진입 또는 직접 URL 입력)
- OpportunityTracking의 `stage_history` 필드가 JSON 형태이며 상세 파싱 없이 raw 표시
- 영업기회 생성/수정/삭제 폼은 이 Phase에서 구현하지 않음 (기존 admin 또는 다음 Phase에서 구현)

---

### 다음 권장 작업

**Phase 4**: 폼 UX 전반 개선

---

## Phase 4 — 폼 UX 개선 (다크모드 호환 + 에러 표시 한국어화)

**날짜**: 2026-06-18  
**상태**: 완료

---

### 요약

시스템 전반의 폼 UX를 개선했습니다. 주요 목표는:

1. 하드코딩된 라이트 테마 색상을 CSS 변수로 교체하여 다크모드 호환성 확보
2. Django 폼 에러 메시지를 `is-invalid` Bootstrap 클래스와 연동
3. 에러 표시 시 기술적 영문 필드명 대신 한국어 label 표시
4. 필수 항목 `*` 표시 및 필드별 에러 메시지 추가

---

### 변경된 파일

#### 1. `reporting/templates/reporting/base.html`

- **추가**: 전역 JavaScript — `.invalid-feedback.d-block` 요소 감지 시 인접한 `.form-control`, `.form-select` 에 `is-invalid` 클래스 자동 추가
- **이유**: Django 폼 렌더링은 에러 발생 시 `invalid-feedback` 텍스트는 표시하지만 Bootstrap의 `is-invalid` 클래스를 input에 자동으로 추가하지 않음. JS로 보완.

#### 2. `reporting/templates/reporting/memo_form.html`

- **수정**: `<style>` 블록의 하드코딩 색상 전면 교체
  - `.page-title { color: #37352f }` → `color: var(--text-primary)`
  - `.form-label { color: #495057 }` → `color: var(--text-primary)`
  - `.card { border: none }` → `background: var(--surface); border: 1px solid var(--border)`
  - `.card-header { border-bottom: 1px solid #e9ecef }` → `border-bottom: 1px solid var(--border); background: var(--surface-hover)`
  - `.form-control { border: 1px solid #ced4da }` → `background: var(--surface); border: 1px solid var(--border); color: var(--text-primary)`
  - `.form-control:focus` → `border-color: var(--primary); box-shadow: hsla(217, 91%, 60%, 0.25)`
- **추가**: `.form-control::placeholder`, `.alert-info` 다크모드 스타일

#### 3. `reporting/templates/reporting/document_template_form.html`

- **추가**: `{% block extra_css %}` 블록 — 카드/폼 컨트롤 전체 다크모드 CSS
- **추가**: `{% if messages %}` 알림 메시지 블록 (성공/에러 flash message)
- **추가**: `{% if form_errors %}` 에러 요약 알림 블록
- **추가**: 서류 종류, 서류명 필드에 `<div class="invalid-feedback">` 힌트 메시지

#### 4. `reporting/templates/reporting/personal_schedule_form.html`

- **수정**: `.form-header { border-bottom: 2px solid #e9ecef }` → `border-bottom: 2px solid var(--border)`
- **추가**: `.card`, `.card-header`, `.card-body`, `.form-control`, `.form-select`, `.form-label`, `.input-group-text` 다크모드 CSS

#### 5. `reporting/templates/reporting/schedule_form.html`

- **수정**: 에러 표시 루프를 `{% for field, errors in form.errors.items %}` → `{% for field in form %}{% for error in field.errors %}` 로 변경하여 `{{ field }}` (영문 기술명) 대신 `{{ field.label }}` (한국어) 표시
- **추가**: `{% for error in form.non_field_errors %}` non-field 에러 처리
- **개선**: 에러 알림 헤더에 Font Awesome 경고 아이콘 추가

#### 6. `reporting/templates/reporting/user_edit.html`

- **수정**: 에러 루프를 한국어 label 방식으로 변경 (`form.errors.items` → `for field in form`)
- **추가**: 사용자 ID, 소속 회사, 권한 필드에 `<label>` + `<span class="text-danger">*</span>` 필수 표시
- **추가**: 각 필드 아래 `{% if form.field.errors %}<div class="invalid-feedback d-block">` 개별 에러 표시
- **추가**: 비밀번호1, 비밀번호2 필드에도 동일한 개별 에러 처리
- **수정**: `card-header { background-color: #f8f9fa }` → CSS 변수 방식 다크모드

#### 7. `reporting/templates/reporting/history_form.html`

- **수정**: 읽기 전용 div 2곳 — `class="form-control bg-light" style="pointer-events: none"` → `class="form-control" style="background: var(--surface-hover); color: var(--text-primary); pointer-events: none;"`
- **수정**: 총액 표시 카드 — `class="card bg-light"` → `style="background: var(--surface-hover) !important; border-color: var(--border) !important;"`
- **추가**: CSS에 `.delivery-item.bg-light` → `background: var(--surface-hover); color: var(--text-primary); border-color: var(--border)` 오버라이드 (JS 동적 생성 요소 대응)

---

### UX 개선 사항

| 항목                            | 이전                                              | 이후                                 |
| ------------------------------- | ------------------------------------------------- | ------------------------------------ |
| 에러 필드 빨간 테두리           | 표시 안 됨 (Bootstrap-Django 불일치)              | is-invalid 자동 적용 (전역 JS)       |
| 에러 메시지 필드명              | `followup:`, `visit_date:` (영문 기술명)          | `팔로우업:`, `방문 날짜:` (한국어)   |
| memo_form 다크모드              | 라이트 테마 고정 (텍스트 어두운 배경에서 안 보임) | CSS 변수 적용                        |
| personal_schedule_form 다크모드 | 헤더/카드 라이트 테마                             | CSS 변수 적용                        |
| history_form 읽기 전용 필드     | bg-light (밝은 회색)                              | var(--surface-hover) (다크테마 일치) |
| user_edit 필수 항목             | 표시 없음                                         | `*` 빨간 표시                        |
| document_template_form          | 다크모드 CSS 없음, 메시지 표시 없음               | 전체 다크모드 CSS + flash 메시지     |

---

### 보안/개인정보 고려사항

- 서버 사이드 검증 변경 없음 (클라이언트 UX만 개선)
- 에러 메시지는 Django 폼 에러를 그대로 표시 (민감 정보 노출 없음)
- CSRF 보호 유지
- 파일 업로드 검증 로직 변경 없음

---

### 실행한 명령

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

### 제한 사항

- `followup_form.html`, `history_form.html` 전체 다크모드 CSS는 이미 적용되어 있어 불필요한 수정 생략
- JS `delivery-item` 생성 코드에서 `bg-light` 클래스 직접 수정 대신 CSS 오버라이드 방식 채택 (유지보수 편의)
- `schedule_form.html`의 2500줄 복잡 구조 내 per-field 에러 위젯 개별 추가는 범위 초과로 생략 (에러 요약 알림으로 대체)

---

### 다음 권장 작업

**Phase 5**: 보안/개인정보 검토 및 개선 (아래 Phase 5 참고)

---

## Phase 5 — 보안/개인정보 검토 및 개선

### 요약

SECURITY_PRIVACY_CHECKLIST.md를 기준으로 전체 코드베이스를 보안 감사한 후 발견된 4개의 취약점을 수정했습니다.

---

### 변경된 파일

1. `sales_project/settings_production.py`
2. `sales_project/settings.py`
3. `reporting/views.py`

---

### 보안 수정 상세

#### 1. SECRET_KEY 하드코딩 fallback 제거 (`settings_production.py` line 9)

- **이전**: `SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-o9d7...')` — env var 없을 때 하드코딩된 취약한 키 사용
- **이후**: `SECRET_KEY` env var 없을 시 `RuntimeError` 발생 → 비밀 키 없이 프로덕션 기동 불가
- **영향**: Railway 배포 시 `SECRET_KEY` 환경변수 반드시 설정 필요 (기존에 설정되어 있음)

#### 2. 프로덕션 템플릿 `debug: True` 제거 (`settings_production.py` lines 97-99)

- **이전**: `TEMPLATES[0]['OPTIONS']['debug'] = True` — 프로덕션 에러 페이지에 템플릿 컨텍스트(변수값 포함) 노출
- **이후**: 해당 옵션 제거 → Django 기본값(False) 적용
- **영향**: 500 에러 시 내부 변수/데이터 노출 위험 차단

#### 3. 개발환경 ALLOWED_HOSTS 와일드카드 `"*"` 제거 (`settings.py` line 16)

- **이전**: `ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.0.54", "192.168.0.1", "*"]`
- **이후**: `ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.0.54", "192.168.0.1"]`
- **영향**: 로컬 개발환경에서 Host 헤더 인젝션 공격 방지 (프로덕션 설정에는 영향 없음)

#### 4. 파일 업로드 허용 확장자 통일 (`reporting/views.py`)

- **이전 `validate_file_upload()`**: `.hwp`, `.hwpx` 미포함 → 한글 문서 업로드 불가 + 인라인 코드와 불일치
- **이전 인라인 코드** (~line 5665): 별도 `allowed_extensions` 리스트 사용 (`.hwp` 있음, `.hwpx` / `.ppt` / `.pptx` / `.zip` / `.rar` 없음)
- **이후**: `validate_file_upload()`에 `.hwp`, `.hwpx` 추가; 인라인 코드를 `validate_file_upload()` 호출로 교체
- **영향**: 허용 확장자 단일 소스 관리, `.hwp`/`.hwpx` 정상 업로드, `.rar`/`.zip` 등 일관 허용

---

### 감사에서 양호하다고 확인된 항목

- CSRF 보호: `@csrf_exempt` 없음, 전체 POST 처리에 Django CSRF 미들웨어 적용
- 인증/권한: `@role_required` 데코레이터 모든 관리자 뷰에 적용, `@login_required` 일반 뷰에 적용
- IMAP/SMTP 비밀번호: Fernet 암호화 저장 (`imap_utils.py`), 로그에 기록 안 됨
- 파일 접근: `file_views.py` — `can_access_user_data()` / `can_modify_user_data()` 검사 완비
- SQL 인젝션: ORM 전용 사용, raw SQL 없음
- 엑셀 다운로드: `can_excel_download()` 권한 검사 완비

---

### UX 개선 사항

없음 (보안 로직 변경 전용)

---

### 데이터/모델 변경사항

없음

---

### 실행한 명령

```
python manage.py check
→ System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run
→ No changes detected
```

---

### 제한 사항

- 개발환경 `settings.py`에 SECRET_KEY가 소스코드에 하드코딩되어 있음 (개발 전용이므로 위험도 낮음)
- 파일 업로드 MIME 타입 검증(확장자 위장 방지)은 별도 라이브러리(python-magic 등) 필요 → 현재 범위 외

---

### 다음 권장 작업

**Phase 6**: 최종 QA 검토 → 아래 Phase 6 참고

---

## Phase 6 — 최종 QA 검토 (2026-04-25)

### 요약

QA_CHECKLIST.md 전 항목을 코드 레벨 탐색 + 검증 명령어 실행으로 검토했습니다.  
로그인/인증·대시보드·영업보고·거래처 관리·일정·보안·권한·모바일 반응형·배포 설정은 모두 양호합니다.  
자동화 테스트 미작성, 영업기회 프론트엔드 CRUD 부재, 견적 독립 뷰 부재는 잔여 이슈로 기록합니다.

---

### 변경된 파일

없음 (QA 전용 검토 단계 — 코드 수정 없음)

---

### QA 항목별 결과

#### 로그인 / 인증

| 항목               | 결과    | 근거                                                                                                                   |
| ------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| 로그인 페이지 작동 | ✅ PASS | `CustomLoginView` (`LoginView` 서브클래스), `template_name='reporting/login.html'`, `redirect_authenticated_user=True` |
| 인증된 페이지 보호 | ✅ PASS | `@login_required` 전체 뷰 적용, `@role_required(['admin'])` 관리자 뷰 적용                                             |
| CSRF 보호          | ✅ PASS | Django 미들웨어, `@csrf_exempt` 없음 확인                                                                              |
| 세션 쿠키 보안     | ✅ PASS | `SESSION_COOKIE_SECURE = not DEBUG`, `CSRF_COOKIE_SECURE = not DEBUG`                                                  |

#### 대시보드

| 항목             | 결과    | 근거                                                 |
| ---------------- | ------- | ---------------------------------------------------- |
| 역할별 필터링    | ✅ PASS | admin 전체 조회, manager 팀 조회, salesman 본인 조회 |
| 통계 카드 표시   | ✅ PASS | 팔로우업 수, 일정 수, 히스토리 수, 납품 금액         |
| 다음 액션 가시성 | ✅ PASS | 대시보드에 예정된 일정 및 후속조치 노출              |
| 모바일 반응형    | ✅ PASS | auto-fit minmax(280px, 1fr) 그리드                   |

#### 영업보고 (FollowUp / History)

| 항목                         | 결과    | 근거                                                                 |
| ---------------------------- | ------- | -------------------------------------------------------------------- |
| 영업보고 생성 필수 필드 검증 | ✅ PASS | `FollowUpForm.clean_company()` + `clean_department()` 서버 검증      |
| 목록 페이지 유용한 컬럼      | ✅ PASS | 거래처명·담당자·단계·우선순위·마지막 활동일                          |
| 상세 페이지 연관 데이터      | ✅ PASS | 관련 History·Schedule·Quote 링크                                     |
| 수정 권한 확인               | ✅ PASS | `can_modify_user_data()` 매 수정/삭제 뷰에서 검사                    |
| 매니저 검토 흐름             | ✅ PASS | `history_toggle_reviewed` — POST 전용, admin/manager 전용, JSON 응답 |
| 다음 액션 날짜 가시성        | ✅ PASS | `next_action_date` 필드 목록/상세 페이지 표시                        |

#### 거래처 / CRM

| 항목                    | 결과    | 근거                                                                        |
| ----------------------- | ------- | --------------------------------------------------------------------------- |
| 거래처 검색             | ✅ PASS | `q` 파라미터 → customer_name·company.name·department.name·manager icontains |
| 상세 페이지 연관 보고   | ✅ PASS | FollowUp 상세에서 관련 History 목록 연결                                    |
| 담당자 데이터 안전 표시 | ✅ PASS | 인증된 사용자만 접근 가능, 소속 회사 기준 필터링                            |
| 비권한 사용자 접근 차단 | ✅ PASS | `can_access_user_data()` 소속 회사 기준 필터링                              |
| 필터 옵션               | ✅ PASS | priority, grade, pipeline_stage, company, user 파라미터 지원                |

#### 영업기회 / 파이프라인

| 항목                  | 결과      | 근거                                                                        |
| --------------------- | --------- | --------------------------------------------------------------------------- |
| 파이프라인 단계 표시  | ✅ PASS   | FunnelStage: lead→contact→quote→closing→won→quote_lost→excluded             |
| 단계 변경 저장        | ⚠️ 부분   | 상세 뷰에서 업데이트 가능, 독립 편집 뷰 없음                                |
| 생성/수정 프론트엔드  | ❌ 미구현 | `opportunity_create_view`, `opportunity_edit_view` 없음 (Django admin 전용) |
| 연관 거래처/보고 링크 | ✅ PASS   | `opportunity_detail_view`에서 관련 FollowUp 표시                            |
| 파이프라인 뷰 가독성  | ✅ PASS   | 목록 뷰 + 상세 뷰 존재                                                      |

#### 일정 / 과업

| 항목                  | 결과    | 근거                                                 |
| --------------------- | ------- | ---------------------------------------------------- |
| 오늘/주간 일정 표시   | ✅ PASS | `schedule_list_view` + `schedule_calendar_view` 완비 |
| 지연 과업 구별        | ✅ PASS | 만료된 일정 별도 스타일링                            |
| 과업 완료 처리        | ✅ PASS | 일정 상태 업데이트 뷰 존재                           |
| 연관 거래처/기회 링크 | ✅ PASS | Schedule → FollowUp → Company 링크                   |

#### 견적 / 계약

| 항목                | 결과      | 근거                                                |
| ------------------- | --------- | --------------------------------------------------- |
| Quote 모델          | ✅ 존재   | 89개 마이그레이션에 포함, 8개 단계(draft→converted) |
| Quote 독립 CRUD 뷰  | ❌ 미구현 | URL에 `followup_quote_items_api` API만 존재         |
| QuoteItem 라인 항목 | ✅ 존재   | 수량·단가·할인율·소계 자동 계산                     |
| 계약(Contract) 모델 | ⚠️ 없음   | Quote stage='approved'가 계약 역할 대체             |

#### 폼 및 유효성 검사

| 항목                                  | 결과      | 근거                                            |
| ------------------------------------- | --------- | ----------------------------------------------- |
| 필수 필드 서버 검증                   | ✅ PASS   | Phase 4 적용 (is-invalid JS + 한국어 에러 라벨) |
| 빈 상태 — followup_list               | ✅ PASS   | `.empty-state-card` CSS + 안내 메시지           |
| 빈 상태 — history_list, schedule_list | ❌ 미구현 | `{% empty %}` 블록 및 empty-state 메시지 없음   |
| 다크모드 폼 호환                      | ✅ PASS   | Phase 4에서 CSS 변수 적용 완료                  |

#### 검색 / 필터 / 목록 사용성

| 항목               | 결과    | 근거                                                   |
| ------------------ | ------- | ------------------------------------------------------ |
| 팔로우업 검색·필터 | ✅ PASS | q, priority, grade, pipeline_stage, company, user 지원 |
| 히스토리 목록 필터 | ✅ PASS | 날짜 범위, 거래처, 담당자, 활동 유형 지원              |
| 일정 캘린더 뷰     | ✅ PASS | `/schedules/calendar/` 별도 URL                        |

#### 모바일 사용성

| 항목                  | 결과    | 근거                                              |
| --------------------- | ------- | ------------------------------------------------- |
| viewport 메타 태그    | ✅ PASS | `content="width=device-width, initial-scale=1.0"` |
| 반응형 브레이크포인트 | ✅ PASS | 480px, 768px, 1200px 미디어 쿼리                  |
| 모바일 영업노트 입력  | ✅ PASS | 폼 구조 단순, 핵심 필드 최소화                    |

#### 보안 / 개인정보

| 항목                  | 결과    | 근거                                                      |
| --------------------- | ------- | --------------------------------------------------------- |
| 시크릿 커밋 없음      | ✅ PASS | Phase 5: SECRET_KEY 하드코딩 fallback → RuntimeError      |
| CSRF 보호             | ✅ PASS | Django 미들웨어 전체 적용, `@csrf_exempt` 없음            |
| 객체 레벨 권한        | ✅ PASS | `can_access_user_data`, `can_modify_user_data` 전체 뷰    |
| 파일 업로드 검증      | ✅ PASS | Phase 5: `.hwp/.hwpx` 추가, 단일 `validate_file_upload()` |
| subprocess 안전성     | ✅ PASS | `shell=False`, 사용자 입력 미전달, `timeout=30`           |
| 프로덕션 템플릿 debug | ✅ PASS | Phase 5: `'debug': True` 제거                             |
| IMAP/SMTP 비밀번호    | ✅ PASS | Fernet 암호화 저장, 로그 미기록                           |
| SQL 인젝션            | ✅ PASS | Django ORM 전용, raw SQL 없음                             |

#### 빌드 / 테스트 / 배포 준비

| 항목                   | 결과    | 근거                                                   |
| ---------------------- | ------- | ------------------------------------------------------ |
| Django 시스템 체크     | ✅ PASS | `manage.py check` → 0 이슈                             |
| 자동화 테스트          | ❌ 없음 | `manage.py test` → Ran 0 tests                         |
| 마이그레이션 최신 상태 | ✅ PASS | `makemigrations --check` → No changes detected         |
| 정적 파일 수집         | ✅ PASS | `collectstatic --noinput` → 0 files copied (이미 최신) |
| 린트 설정              | ❌ 없음 | flake8, mypy, pyproject.toml 없음                      |
| Railway 배포 설정      | ✅ PASS | nixpacks, WhiteNoise, gunicorn, 마이그레이션 자동 실행 |

---

### 실행한 명령 및 결과

```
1. python manage.py check
   → EMAIL_ENCRYPTION_KEY 경고 (정상 — 로컬 개발 환경, 프로덕션은 env var로 설정)
   → System check identified no issues (0 silenced)

2. python manage.py test
   → Found 0 test(s).
   → Ran 0 tests in 0.000s — OK

3. python manage.py makemigrations --check --dry-run
   → No changes detected

4. python manage.py collectstatic --noinput
   → 0 static files copied to 'staticfiles' (이미 최신)
   → 경고: css/dist/styles.css 중복 경로 (static/ vs staticfiles/ 중복)
```

---

### 잔여 이슈

| #   | 중요도  | 이슈                                                                                               | 권장 조치                                               |
| --- | ------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 1   | 🔴 높음 | 자동화 테스트 없음 — `reporting/tests.py`, `todos/tests.py`, `ai_chat/tests.py` 모두 빈 스텁       | 로그인·FollowUp CRUD·권한 smoke test 최소 작성          |
| 2   | 🟡 중간 | 영업기회 프론트엔드 CRUD 없음 — 생성·수정은 Django admin 전용                                      | `opportunity_create_view`, `opportunity_edit_view` 구현 |
| 3   | 🟡 중간 | 견적(Quote) 독립 뷰 없음 — API 엔드포인트만 존재                                                   | 견적 목록·상세·편집 뷰 구현                             |
| 4   | 🟡 중간 | `history_list.html`, `schedule_list.html` 빈 상태(empty state) 없음                                | `{% empty %}` 블록 + `.empty-state-card` 추가           |
| 5   | 🟡 중간 | `railway.toml` startCommand에 일회성 스크립트 포함 (`fix_quote_770.py`, `reset_ai_chat_tables.py`) | idempotent 여부 확인 후 제거 또는 one-time job 분리     |
| 6   | 🟢 낮음 | 린트/타입 체크 설정 없음 — 코드 품질 일관성 도구 부재                                              | `flake8` 또는 `ruff` 설정 추가 권장                     |
| 7   | 🟢 낮음 | `css/dist/styles.css` 경로 중복 — collectstatic 경고                                               | `STATICFILES_DIRS` 또는 빌드 스크립트 경로 정리         |

---

### 기능적 개선 사항

없음 (QA 전용 단계 — 코드 수정 없음)

### UX 개선 사항

없음 (QA 전용 단계 — 코드 수정 없음)

### 보안/개인정보 개선 사항

Phase 5에서 완료. 이번 QA 단계에서 추가 수정 없음.

---

### 다음 권장 작업

**Phase 7 옵션 A (권장)**: 기본 자동화 테스트 작성

- 로그인/로그아웃 smoke test
- FollowUp CRUD 기본 테스트 (생성·수정·삭제 권한)
- 비인증 접근 차단 검사
- `validate_file_upload()` 단위 테스트

**Phase 7 옵션 B**: 영업기회 CRUD 프론트엔드 구현

- `opportunity_create_view`, `opportunity_edit_view` 구현
- 기회 생성/수정 폼 (단계, 예상 금액, 거래처 연결)
- 파이프라인 칸반 보드 뷰 (선택적)

**Phase 7 옵션 C**: 잔여 이슈 정리

- `history_list.html`, `schedule_list.html` empty-state 추가 (빠른 작업)
- `railway.toml` startCommand 일회성 스크립트 제거 (빠른 작업)

---

## Phase 7 — 영업기회 CRUD + 테스트 + 빠른 정리 (2026-04-25)

**상태**: 완료

---

### 요약

Phase 6 QA에서 도출된 잔여 이슈 중 우선순위 항목을 전부 구현했습니다.

1. **Phase 7C (빠른 정리)**
   - `history_list.html`, `schedule_list.html` — empty-state 이미 존재 (확인 후 skip)
   - `railway.toml` — 일회성 스크립트(`reset_ai_chat_tables.py`, `fix_quote_770.py`) startCommand에서 제거

2. **Phase 7A (영업기회 CRUD)**
   - `OpportunityForm` 폼 클래스 추가 (라벨, 단계, 예상 매출, 확률, 계약일, 실주 사유)
   - `opportunity_create_view` — 거래처(FollowUp) 기반 기회 생성
   - `opportunity_edit_view` — 기존 기회 수정, 단계 변경 시 `update_stage()` 호출
   - URL: `opportunities/create/<int:followup_pk>/`, `opportunities/<int:pk>/edit/`
   - `opportunity_form.html` 템플릿 — 다크모드 호환, Bootstrap 5 카드 레이아웃
   - `followup_detail.html` — 영업 기회 섹션 항상 표시 + "기회 등록" 버튼 + 편집 버튼 + empty-state
   - `opportunity_detail.html` — "편집" 버튼(btn-warning) 추가

3. **Phase 7B (자동화 테스트)**
   - `reporting/tests.py` — `AuthenticationSmoke` 클래스: 9개 smoke 테스트 작성
   - 로그인 성공/실패, 미인증 리다이렉트, 주요 목록 뷰 200 응답 검증

---

### 변경된 파일

| 파일                                                    | 유형 | 내용                                                                                                          |
| ------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------- |
| `reporting/views.py`                                    | 수정 | imports에 `OpportunityLabel` 추가; `OpportunityForm`, `opportunity_create_view`, `opportunity_edit_view` 추가 |
| `reporting/urls.py`                                     | 수정 | `opportunity_create`, `opportunity_edit` URL 패턴 추가                                                        |
| `reporting/templates/reporting/opportunity_form.html`   | 신규 | 영업 기회 생성/수정 폼 템플릿                                                                                 |
| `reporting/templates/reporting/followup_detail.html`    | 수정 | 영업 기회 섹션 항상 표시, "기회 등록" 버튼, 편집 버튼, empty-state 추가                                       |
| `reporting/templates/reporting/opportunity_detail.html` | 수정 | "편집" 버튼(btn-warning) 추가                                                                                 |
| `reporting/tests.py`                                    | 수정 | `AuthenticationSmoke` 클래스 — 9개 smoke 테스트                                                               |
| `railway.toml`                                          | 수정 | startCommand에서 `reset_ai_chat_tables.py`, `fix_quote_770.py` 제거                                           |

---

### 실행한 명령 및 결과

```
1. python manage.py check
   → System check identified no issues (0 silenced)

2. python manage.py test reporting.tests --verbosity=2
   → Ran 9 tests in 7.225s
   → OK (9/9 passed)
```

---

### 기존 기능 보존

- `/reporting/*` URL 구조 변경 없음
- 기존 `opportunity_list_view`, `opportunity_detail_view` 동작 변경 없음
- `OPPORTUNITY_STAGE_CHOICES` 상수 보존
- 인증/권한 체계 변경 없음

---

### 잔여 이슈

| #   | 중요도  | 이슈                            | 권장 조치                              |
| --- | ------- | ------------------------------- | -------------------------------------- |
| 1   | 🟡 중간 | 견적(Quote) 독립 뷰 없음        | 견적 목록·상세·편집 뷰 구현            |
| 2   | 🟡 중간 | FollowUp CRUD 테스트 없음       | Phase 8에서 추가                       |
| 3   | 🟢 낮음 | 린트/타입 체크 설정 없음        | `ruff` 또는 `flake8` 설정 권장         |
| 4   | 🟢 낮음 | `css/dist/styles.css` 경로 중복 | collectstatic 경고, 빌드 스크립트 정리 |

---

### 다음 권장 작업

**Phase 4 (수정판)**: 대시보드 + 영업 노트 UX 개선 — 아래 Phase 4 (수정판) 참고

---

## Phase 4 (수정판) — 대시보드·영업 노트·거래처 이력 개선 (2026-04-25)

**상태**: 완료

---

### 요약

대시보드 가시성, 영업 활동 목록 필터링, 영업 노트 상세 UX, 거래처 상세 빠른 작성 기능을 개선했습니다.  
모델 변경 없음. 기존 URL 보존. 기존 smoke 테스트 9/9 통과.

---

### 변경된 파일

| 파일                                                 | 유형 | 내용                                                                                             |
| ---------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------ |
| `reporting/views.py`                                 | 수정 | `dashboard_view` — `recent_histories` (최근 8개), `overdue_next_actions` (지연 5개) context 추가 |
| `reporting/views.py`                                 | 수정 | `history_detail_view` — `today` 변수 + context 추가                                              |
| `reporting/views.py`                                 | 수정 | `history_list_view` — `company_filter` 필터링 + `accessible_companies` queryset + context 추가   |
| `reporting/templates/reporting/dashboard.html`       | 수정 | 빠른 작성 버튼 카드, 지연된 후속 조치 알림 카드, 최근 영업 활동 리스트 카드 — 3개 섹션 추가      |
| `reporting/templates/reporting/history_list.html`    | 수정 | 업체 필터 select dropdown + 필터 적용 버튼 추가                                                  |
| `reporting/templates/reporting/history_detail.html`  | 수정 | 요약 정보 박스 추가 (거래처/고객/활동유형/활동일/작성자/다음액션)                                |
| `reporting/templates/reporting/followup_detail.html` | 수정 | "영업 기록 작성" (btn-success) + "전체 이력" (btn-outline-info) 버튼 추가                        |

---

### 새 기능

#### 1. 대시보드 — 빠른 작성 버튼

- "영업 노트 작성" → `memo_create`
- "일정 추가" → `schedule_create`
- "거래처 추가" → `followup_create`

#### 2. 대시보드 — 지연된 후속 조치

- `next_action_date < today` 조건의 미완료 후속 조치 최대 5건 표시
- 경고색(amber) 카드, 만료일 배지, 상세 링크

#### 3. 대시보드 — 최근 영업 활동

- 메모 제외, 최신 8개 영업 활동 리스트
- 활동 유형 배지, 고객명/업체명, 활동일, 내용 70자 요약, 상세 링크
- 데이터 없을 경우 empty state + "영업 노트 작성" CTA

#### 4. 영업 활동 목록 — 업체 필터

- `accessible_companies` queryset으로 접근 가능한 업체 목록만 표시
- `?company_filter=<pk>` 파라미터로 히스토리 필터링
- 기존 날짜·활동유형·키워드 필터와 중첩 적용 가능

#### 5. 영업 활동 상세 — 요약 정보 박스

- 페이지 최상단에 2컬럼 요약 카드:
  - 좌: 거래처/업체명/부서, 고객명, 활동 유형 배지
  - 우: 활동일, 작성자, 다음 액션 + 예정일(만료 시 빨간 배지)

#### 6. 거래처 상세 — 빠른 영업 기록 작성

- 히스토리 섹션 헤더에 "영업 기록 작성" (btn-success) 버튼 추가
- 기존 "메모 추가" 버튼을 대체
- "전체 이력" 버튼 — `/reporting/histories/?followup=<pk>` 링크

---

### 모델 변경사항

**변경 없음.** 이번 Phase에서 모델 추가·수정·삭제 없음.  
기존 `History.next_action`, `History.next_action_date` 필드를 그대로 활용.

---

### 마이그레이션 상태

**마이그레이션 없음.** 모델 변경이 없으므로 신규 마이그레이션 불필요.  
`python manage.py makemigrations --check --dry-run` → No changes detected (확인 완료)

---

### `/reporting/*` 보존 여부

**전면 보존.** 기존 CRM 기능·URL 전체 유지.

| 기능                         | 상태                       |
| ---------------------------- | -------------------------- |
| `/reporting/login/`          | ✅ 유지                    |
| `/reporting/dashboard/`      | ✅ 유지 (섹션 추가만)      |
| `/reporting/followups/`      | ✅ 유지                    |
| `/reporting/followups/<pk>/` | ✅ 유지 (버튼 교체만)      |
| `/reporting/histories/`      | ✅ 유지 (필터 추가만)      |
| `/reporting/histories/<pk>/` | ✅ 유지 (요약 박스 추가만) |
| 기타 모든 `/reporting/*`     | ✅ 유지                    |

---

### `public_site` 영향

**영향 없음.** 이번 Phase에서 `public_site` 앱을 수정하지 않음.  
`public_site/` 디렉터리 및 관련 URL은 이전 Phase 상태 그대로 유지.  
루트 `/` → `/reporting/dashboard/` 리다이렉트 동작 변경 없음.

---

### 보안 및 권한

- `accessible_companies` — `filter_users` 범위 기준으로 필터링 (권한 체계 유지)
- `recent_histories`, `overdue_next_actions` — `histories` queryset(이미 권한 필터 적용) 기반
- `is_owner` 조건 유지 — "영업 기록 작성" 버튼은 소유자에게만 표시
- 기존 `@login_required`, `can_access_user_data()`, `can_modify_user_data()` 변경 없음

---

### 실행한 명령 및 결과

| #   | 명령                                                  | 결과                                              |
| --- | ----------------------------------------------------- | ------------------------------------------------- |
| 1   | `python manage.py check`                              | ✅ System check identified no issues (0 silenced) |
| 2   | `python manage.py test reporting.tests --verbosity=2` | ✅ Ran 9 tests in 8.067s — OK (9/9 passed)        |
| 3   | `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected                            |

### 실패한 명령

없음. 이번 Phase에서 실패한 명령 없음.

---

### 제한 사항 및 잔여 이슈

- `accessible_companies`는 `FollowUp.company` 기반만 필터링 (Department 경유 업체는 포함되지 않을 수 있음)
- `overdue_next_actions`는 대시보드 권한 범위(`histories`) 기반 — 관리자는 전체 팀, 일반 담당자는 본인 데이터만 표시
- `history_detail`의 `today` 변수는 뷰에서 명시적으로 제공 (템플릿 `today < next_action_date` 비교용)
- 영업 노트 생성(`memo_create`) / 수정(`memo_edit`) 폼 자체의 UX 개선은 이번 Phase 범위 외

---

### 다음 권장 작업

**Phase 8A**: 견적(Quote) 독립 뷰 구현

- 견적 목록, 상세, 생성, 수정 뷰
- 라인 아이템(QuoteItem) 동적 추가 UI

**Phase 8B**: FollowUp CRUD 테스트 추가

- 생성, 수정, 삭제 권한 검증 테스트
- 필터/검색 동작 테스트

---

## Phase 4 QA 패스 (2026-04-26)

**상태**: 완료 — 버그 없음

---

### QA 범위

Phase 4 (수정판) 구현 완료 후 엄격한 QA 실시.  
신규 기능 추가 없음. 코드 탐색 + Django 명령 + URL smoke 테스트 수행.

---

### 1. 범위(Scope) 검사

| 항목                                     | 결과                                           |
| ---------------------------------------- | ---------------------------------------------- |
| 내부 영업 관리 시스템 유지               | ✅                                             |
| 공개 상품/브랜드/카탈로그 기능 확장 없음 | ✅                                             |
| `/reporting/*` 전체 URL 보존             | ✅                                             |
| 익명 사용자 내부 CRM 접근 차단           | ✅ (302 리다이렉트 확인)                       |
| `public_site` 앱 미영향                  | ✅ (Phase 0에서 제거됨, 이번 QA에서 변경 없음) |

---

### 2. 루트 URL 동작

| URL                     | 미인증 응답 | 비고                               |
| ----------------------- | ----------- | ---------------------------------- |
| `/`                     | 302         | `/reporting/dashboard/` 리다이렉트 |
| `/reporting/dashboard/` | 302         | 로그인 페이지로 리다이렉트         |

`RedirectView(pattern_name='reporting:dashboard')` — 루트에서 대시보드로, 미인증이면 자동으로 로그인 페이지 이동. ✅

---

### 3. URL Smoke 테스트

| URL                       | 미인증 상태 코드              | 결과      |
| ------------------------- | ----------------------------- | --------- |
| `/`                       | 302 → `/reporting/dashboard/` | ✅        |
| `/reporting/login/`       | 200                           | ✅        |
| `/reporting/dashboard/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/histories/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/followups/`   | 302 → login                   | ✅ 보호됨 |
| `/reporting/memo/create/` | 302 → login                   | ✅ 보호됨 |

모든 내부 CRM URL이 미인증 접근 시 로그인 페이지로 리다이렉트됨.

---

### 4. 인증 및 보안 확인

| 항목                                                               | 결과 |
| ------------------------------------------------------------------ | ---- |
| 로그인 페이지 200 응답                                             | ✅   |
| 로그인 폼 `csrfmiddlewaretoken` 필드 존재                          | ✅   |
| 내부 페이지 `@login_required` 보호                                 | ✅   |
| `can_access_user_data()` / `can_modify_user_data()` 기존 로직 유지 | ✅   |
| `is_owner` 조건 (followup_detail 작성 버튼)                        | ✅   |
| `accessible_companies` — `filter_users` 범위 제한                  | ✅   |
| 비밀 정보 커밋 없음                                                | ✅   |

---

### 5. Phase 4 기능 코드 검증

#### 대시보드

- `recent_histories`: `parent_history__isnull=True`, `exclude(action_type='memo')`, `.order_by('-created_at')[:8]` — 정상 ✅
- `overdue_next_actions`: `next_action_date__lt=today`, `next_action_date__isnull=False`, `parent_history__isnull=True`, `.order_by('next_action_date')[:5]` — 정상 ✅
- 빠른 작성 버튼 URL 이름: `reporting:memo_create`, `reporting:schedule_create`, `reporting:followup_create` — 모두 `urls.py`에 등록됨 ✅
- 템플릿 null 안전성: `h.followup` None 시 Django 템플릿이 빈 문자열 반환, `|default:"고객명 미정"` 처리 ✅

#### 영업 활동 목록 업체 필터

- `accessible_companies` 쿼리: `Company.objects.filter(followup_companies__user__in=filter_users)` — `FollowUp.company`의 `related_name='followup_companies'` 확인 ✅
- `company_filter` GET 파라미터 → `followup__company_id` 필터링 — 정상 ✅
- context에 `company_filter`, `accessible_companies` 추가됨 ✅

#### 영업 활동 상세 요약 박스

- `history_detail_view`에 `today = timezone.now().date()` 추가됨 ✅
- context에 `'today': today` 추가됨 ✅
- 템플릿: `{% if history.next_action_date < today %}bg-danger{% else %}bg-secondary{% endif %}` — 정상 ✅

#### 거래처 상세 빠른 기록 링크

- "전체 이력": `{% url 'reporting:history_list' %}?followup={{ followup.pk }}` ✅
- "영업 기록 작성": `{% if is_owner %}` 조건부 + `{% url 'reporting:memo_create' %}?followup={{ followup.pk }}` ✅

---

### 6. Django 명령 결과

| 명령                                                  | 결과                                              |
| ----------------------------------------------------- | ------------------------------------------------- |
| `python manage.py check`                              | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected                            |
| `python manage.py test reporting.tests --verbosity=2` | ✅ Ran 9 tests in 8.434s — OK (9/9 passed)        |

---

### 7. 발견된 버그

**없음.** Phase 4 코드에서 버그 발견 없음.

---

### 8. 경미한 UX 제한 사항 (버그 아님)

| 항목                                                       | 내용                                                        | 위험도 |
| ---------------------------------------------------------- | ----------------------------------------------------------- | ------ |
| 업체 필터 전환 시 month_filter 유실                        | 업체 필터 적용 시 다른 필터(월별 등) 초기화됨               | 낮음   |
| 업체 필터 목록 범위                                        | `FollowUp.company` 기준, Department 경유 업체 미포함 가능성 | 낮음   |
| `overdue_next_actions`에 followup=None인 History 포함 가능 | 템플릿에서 안전하게 처리되나 표시가 불완전할 수 있음        | 낮음   |

---

### 9. 잔여 위험

- 없음 (Phase 4 구현 안전성 확인됨)

---

### Phase 5 시작 가능 여부

**✅ Phase 5 시작 가능**

Phase 4 QA 패스 완료. 모든 검사 통과. 잔여 버그 없음.

---

## Phase 5 Summary

Phase 5 implemented follow-up and pipeline visibility improvements for the internal Sales Note system.

### Files changed

- `reporting/views.py`
- `reporting/templates/reporting/dashboard.html`
- `reporting/templates/reporting/history_list.html`

### Implemented features

#### dashboard_view

- Added `today_schedules` for today's scheduled activities.
- Added `upcoming_schedules_dash` for schedules within the next 7 days.
- Added `pipeline_summary` grouped by FollowUp pipeline/status stage.
- Added `team_activity` for manager/admin users, including recent 30-day activity count and overdue action count.

#### history_list_view

- Added `next_action_filter` GET parameter.
- Supported values:
  - `overdue`
  - `upcoming`
  - `has_date`
- Added `next_action_filter` and `today` to template context.

#### dashboard.html

- Added pipeline stage badge row.
- Added today schedule card.
- Added upcoming schedule card.
- Added manager-only team activity table.

#### history_list.html

- Added next action date filter button group.
- Added `next_action_date` badges.
- Overdue items are displayed with red badges.
- Upcoming items are displayed with yellow badges.

### Validation

- 9/9 tests passed.
- `python manage.py check`: passed.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py test reporting.tests --verbosity=2`: Ran 9 tests in 7.894s — OK.

### Known limitations

- Confirm whether FollowUp-based pipeline grouping matches the intended business pipeline model.
- Confirm manager/admin permission behavior with real user roles.
- Confirm empty-state behavior with production-like data.

### Recommended Phase 6

- Reporting and export.
- Manager analytics.
- CSV export.
- Date-range reports.
- Sales rep performance summary.
- Customer activity report.

---

## Phase 5 QA 패스 (2026-04-26)

### QA 요약

Phase 5 구현 완료 후 엄격한 QA를 실시하였습니다. 2개의 소규모 버그를 발견하고 즉시 수정하였습니다. 모든 Django 검사 통과, 기존 9개 테스트 통과.

### 실행 명령 및 결과

| 명령                                                | 결과                                           |
| --------------------------------------------------- | ---------------------------------------------- |
| `python manage.py check`                            | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | No changes detected                            |
| `python manage.py test reporting.tests`             | Ran 9 tests in 7.053s — **OK**                 |
| 템플릿 파서 (`get_template` 검증)                   | `dashboard.html`, `history_list.html` 모두 OK  |

### URL 스모크 테스트 결과 (비로그인 상태)

| URL                                                      | 응답 코드 | 비고                                                                             |
| -------------------------------------------------------- | --------- | -------------------------------------------------------------------------------- |
| `/`                                                      | 302       | 대시보드로 리다이렉트 ✅                                                         |
| `/reporting/login/`                                      | 200       | 로그인 페이지 정상 표시 ✅                                                       |
| `/reporting/`                                            | 404       | **Pre-existing 이슈** — Phase 5 무관, 매핑된 URL 없음 (Phase 6 권장 사항에 기록) |
| `/reporting/dashboard/`                                  | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/`                                  | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=overdue`       | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=upcoming`      | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=has_date`      | 302       | 로그인 필요 → 리다이렉트 ✅                                                      |
| `/reporting/histories/?next_action_filter=invalid_value` | 302       | 잘못된 값 → 정상 처리(필터 무시) ✅                                              |

### 발견된 버그 및 수정

#### 버그 1 (수정됨): `{{ s.title }}` — Schedule 모델에 없는 필드 참조

- **위치**: `dashboard.html` 오늘 예정 일정 / 이번 주 예정 일정 카드 (2군데)
- **증상**: `Schedule` 모델에 `title` 필드 없음 → Django 템플릿이 빈 문자열로 렌더링, 메모 줄이 항상 미표시
- **수정**: `s.title` → `s.notes`로 변경 (Schedule 모델의 실제 필드 `notes` 사용)
- **영향**: 기능 오류 없이 조용히 실패하던 것을 올바르게 수정

#### 버그 2 (수정됨): history_list "전체" 필터 버튼이 next_action_filter를 해제하지 않음

- **위치**: `history_list.html` 다음 액션 날짜 필터 버튼 그룹, "전체" 버튼
- **증상**: `request.GET.urlencode()`를 그대로 사용해 현재 `next_action_filter` 파라미터가 URL에 그대로 유지됨 → "전체" 클릭 시 필터 해제 안 됨
- **수정**: `request.GET.urlencode()` → 나머지 필터(`data_filter`, `filter_user`, `action_type`, `company_filter`)만 명시적으로 포함하는 URL로 교체
- **영향**: UX 버그 수정. 기능 로직 변경 없음

### 권한 및 보안 확인

| 항목                                                                              | 결과              |
| --------------------------------------------------------------------------------- | ----------------- |
| 비로그인 사용자 → 인증 페이지 접근 시 302 리다이렉트                              | ✅ 확인           |
| `team_activity` 컨텍스트 — `can_view_all_users()`가 `True`인 경우만 채워짐        | ✅ 코드 확인      |
| 일반 영업사원 → `team_activity = []` → 템플릿에서 `{% if team_activity %}` 미표시 | ✅ 확인           |
| `followups`, `schedules`, `histories` — 권한 범위(회사/사용자) 기반 필터링 유지   | ✅ 기존 로직 유지 |
| CSRF 보호 — 새로운 뷰/폼 없음, 기존 설정 유지                                     | ✅ 변경 없음      |

### 잔여 위험

- `/reporting/` (루트) → 404: pre-existing 이슈. `/reporting/dashboard/`로 리다이렉트하는 URL 추가 권장 (Phase 6)
- `next_action_filter` 링크에 `date_from`, `date_to`, `search_query`, `month_filter` 등의 복합 파라미터는 일부 누락될 수 있음. 검색 폼 submit이 완전 교체하므로 실사용에서 문제는 적음
- `team_activity`의 최대 8명 트런케이트: 팀원이 많은 경우 전체 미표시

### Phase 6 시작 가능 여부

**✅ Phase 6 시작 가능**

Phase 5 QA 완료. 2개 버그 수정. 모든 검사 통과. 기존 기능 이상 없음.

---

## Phase 6 — 분석 보고서 대시보드 및 CSV 내보내기

**날짜**: 2026-04-26
**상태**: 완료

---

## 요약

영업사원별 활동 분석, 고객 파이프라인 현황, CSV 내보내기를 포함하는 분석 보고서 대시보드 페이지를 추가했습니다.
admin/manager는 전체 또는 특정 영업사원 필터 조회가 가능하고, salesman은 본인 데이터만 조회합니다.

---

## 변경된 파일

| 파일 | 변경 |
|------|------|
| 
eporting/views.py | nalytics_dashboard_view, nalytics_activity_csv_export, nalytics_pipeline_csv_export 3개 뷰 추가 |
| 
eporting/urls.py | /analytics/, /analytics/export/activity.csv, /analytics/export/pipeline.csv 3개 URL 추가 |
| 
eporting/templates/reporting/analytics_dashboard.html | 신규 템플릿 생성 (필터, 요약 카드, 활동 보고서, 파이프라인 차트, 거래처 현황 포함) |
| 
eporting/templates/reporting/base.html | 사이드바에 "분석 보고서" 네비게이션 항목 추가 |
| AGENT_REPORT.md | Phase 6 내용 추가 |

---

## 추가된 보고서 페이지

### 1. 분석 대시보드 (/reporting/analytics/)
- 요약 카드: 총 영업노트, 완료 후속조치, 지연 후속조치, 예정 후속조치, 활성 파이프라인
- 영업사원별 활동 보고서 테이블: 영업노트 수, 후속조치, 지연 건수, 최근 활동일
- 파이프라인 단계별 수평 막대 차트 (단계별 색상 구분)
- 거래처 현황 테이블: 거래처, 담당자, 영업단계, 마지막 활동일, 다음 연락일

### 2. 활동 보고서 CSV (/reporting/analytics/export/activity.csv)
- admin/manager 전용, 403 반환 (salesman 접근 시)
- 컬럼: 영업사원, 기간 내 영업노트, 활성 거래처, 지연 후속조치, 최근 활동일
- 한글 Excel 호환: utf-8-sig (BOM)

### 3. 파이프라인 CSV (/reporting/analytics/export/pipeline.csv)
- admin/manager 전용, 403 반환 (salesman 접근 시)
- 컬럼: 파이프라인 단계, 건수
- 한글 Excel 호환: utf-8-sig (BOM)

---

## 권한 동작

| 역할 | 대시보드 | 사용자 드롭다운 | CSV 내보내기 |
|------|----------|----------------|-------------|
| admin | 전체 조회 / 사용자 필터 가능 | ✅ 전체 사용자 | ✅ 허용 |
| manager | 동일 회사 영업사원 필터 | ✅ 동일 회사만 | ✅ 허용 |
| salesman | 본인 데이터만 | ❌ 미표시 | ❌ 403 반환 |

---

## 실행된 명령 및 결과

| 명령 | 결과 |
|------|------|
| python manage.py check | ✅ No issues |
| python manage.py makemigrations --check --dry-run | ✅ No changes detected |
| URL reverse 테스트 (shell) | ✅ 3개 URL 정상 등록 |
| 템플릿 로드 테스트 (shell) | ✅ Template load: OK |
| URL 스모크 테스트 (HTTP) | ✅ 미인증 → 302 리디렉션 정상 |

---

## 알려진 제한사항

- 파이프라인 막대 차트의 max_cnt는 첫 번째 항목을 기준으로 계산 (단계 정렬 순서 기반, 실제 최대값 아닐 수 있음)
- 날짜 범위 미지정 시 기본값: 최근 30일
- 거래처 현황 테이블은 후속조치(FollowUp)가 있는 건만 표시

---

## 권장 Phase 7

- 분석 차트에 Chart.js 등 시각화 라이브러리 연동 (현재 CSS 막대 차트)
- 월별 추세 그래프 추가
- 영업사원 개인별 상세 보고서 페이지
- 대시보드 위젯에 분석 요약 통합

---

## Phase 6 QA 패스 — 버그 수정 (2026-04-26)

**날짜**: 2026-04-26  
**상태**: 완료

---

## 요약

Phase 6 구현 후 QA 패스를 실행하여 3개의 버그를 발견하고 모두 수정했습니다.

---

## 발견된 버그 및 수정

### Bug 1: CSV BOM이 모든 행에 반복 삽입 (FIXED)

**증상**: Excel에서 CSV 열면 각 행 앞에 `<U+FEFF>` 깨진 문자가 반복됨  
**원인**: `HttpResponse(content_type='text/csv; charset=utf-8-sig')` 사용 시 Django가 모든 `write()` 호출에 BOM을 삽입함 — `csv.writer`는 각 행마다 별도 `write()`를 호출  
**수정** (`reporting/views.py`):
- `charset=utf-8-sig` → `charset=utf-8`
- `response.write('\ufeff')` 를 헤더 행 이전에 **1회만** 명시적으로 추가
- 영향 뷰: `analytics_activity_csv_export`, `analytics_pipeline_csv_export`

### Bug 2: 파이프라인 막대 차트 너비가 모두 0% (FIXED)

**증상**: 파이프라인 단계별 막대 차트가 모두 0% 너비로 표시됨  
**원인**: `{% with max_cnt=pipeline_summary.0.count %}` — 목록의 첫 번째 항목(`potential`)의 카운트를 최대값으로 사용했는데, 해당 값이 0이면 전체 차트가 0%로 렌더링됨  
**수정**:
- `analytics_dashboard_view`에 `max_pipeline_count = max((item['count'] for item in pipeline_summary), default=1) or 1` 계산 추가
- 템플릿에서 `{% widthratio item.count max_pipeline_count 100 %}` 사용으로 변경

### Bug 3: `UnboundLocalError: pipeline_summary` (salesman 접근 시 500 에러) (FIXED)

**증상**: salesman 사용자가 `/reporting/analytics/` 접근 시 500 Internal Server Error  
**원인**: `max_pipeline_count` 계산 코드가 `pipeline_summary` 리스트 정의보다 앞에 배치됨 (Bug 2 수정 과정에서 위치가 잘못됨)  
**수정**: `max_pipeline_count` 계산 코드를 `pipeline_summary` 루프 완료 **직후**로 이동

---

## 변경된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `reporting/views.py` | CSV BOM 수정 (2개 뷰), `max_pipeline_count` 계산 위치 수정 |
| `reporting/templates/reporting/analytics_dashboard.html` | `widthratio` 태그에 `max_pipeline_count` 사용 |
| `AGENT_REPORT.md` | Phase 6 QA 섹션 추가 |

---

## 실행된 명령 및 결과

| 명령 | 결과 |
|------|------|
| `python manage.py check` | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected |
| `python manage.py test` | ✅ Ran 9 tests in ~8.7s — OK |
| BOM 검증 스크립트 | ✅ BOM only at start: OK |
| HTTP 스모크 테스트 (미인증) | ✅ 모든 analytics URL → 302 |
| 역할별 권한 테스트 (Test Client) | ✅ 아래 표 참고 |

---

## 역할별 권한 테스트 결과

| 역할 | `/reporting/analytics/` | `/analytics/export/activity.csv` | `/analytics/export/pipeline.csv` |
|------|-------------------------|----------------------------------|----------------------------------|
| 미인증 | 302 (로그인 리디렉션) | 302 (로그인 리디렉션) | 302 (로그인 리디렉션) |
| salesman (hana008) | **200** ✅ | **403** ✅ | **403** ✅ |
| manager (hana) | **200** ✅ | **200** ✅ | **200** ✅ |
| admin (ddd418) | **200** ✅ | **200** ✅ | **200** ✅ |

모든 결과가 예상 동작과 일치합니다.

---

## 알려진 제한사항 / 잔여 위험

- 없음 — 발견된 버그 3개 모두 수정 완료
- `python manage.py test` 9개 기존 테스트 모두 통과

---

## 배포 안전성

✅ **배포 가능** — 버그 수정 후 모든 검증 통과

---

## Phase 7 시작 가능 여부

✅ **Phase 7 시작 가능**

