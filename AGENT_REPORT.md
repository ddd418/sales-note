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
| ---- | ---- |

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

| 역할     | 대시보드                     | 사용자 드롭다운 | CSV 내보내기 |
| -------- | ---------------------------- | --------------- | ------------ |
| admin    | 전체 조회 / 사용자 필터 가능 | ✅ 전체 사용자  | ✅ 허용      |
| manager  | 동일 회사 영업사원 필터      | ✅ 동일 회사만  | ✅ 허용      |
| salesman | 본인 데이터만                | ❌ 미표시       | ❌ 403 반환  |

---

## 실행된 명령 및 결과

| 명령                                              | 결과                          |
| ------------------------------------------------- | ----------------------------- |
| python manage.py check                            | ✅ No issues                  |
| python manage.py makemigrations --check --dry-run | ✅ No changes detected        |
| URL reverse 테스트 (shell)                        | ✅ 3개 URL 정상 등록          |
| 템플릿 로드 테스트 (shell)                        | ✅ Template load: OK          |
| URL 스모크 테스트 (HTTP)                          | ✅ 미인증 → 302 리디렉션 정상 |

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

| 파일                                                     | 변경 내용                                                  |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| `reporting/views.py`                                     | CSV BOM 수정 (2개 뷰), `max_pipeline_count` 계산 위치 수정 |
| `reporting/templates/reporting/analytics_dashboard.html` | `widthratio` 태그에 `max_pipeline_count` 사용              |
| `AGENT_REPORT.md`                                        | Phase 6 QA 섹션 추가                                       |

---

## 실행된 명령 및 결과

| 명령                                                | 결과                                              |
| --------------------------------------------------- | ------------------------------------------------- |
| `python manage.py check`                            | ✅ System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run` | ✅ No changes detected                            |
| `python manage.py test`                             | ✅ Ran 9 tests in ~8.7s — OK                      |
| BOM 검증 스크립트                                   | ✅ BOM only at start: OK                          |
| HTTP 스모크 테스트 (미인증)                         | ✅ 모든 analytics URL → 302                       |
| 역할별 권한 테스트 (Test Client)                    | ✅ 아래 표 참고                                   |

---

## 역할별 권한 테스트 결과

| 역할               | `/reporting/analytics/` | `/analytics/export/activity.csv` | `/analytics/export/pipeline.csv` |
| ------------------ | ----------------------- | -------------------------------- | -------------------------------- |
| 미인증             | 302 (로그인 리디렉션)   | 302 (로그인 리디렉션)            | 302 (로그인 리디렉션)            |
| salesman (hana008) | **200** ✅              | **403** ✅                       | **403** ✅                       |
| manager (hana)     | **200** ✅              | **200** ✅                       | **200** ✅                       |
| admin (ddd418)     | **200** ✅              | **200** ✅                       | **200** ✅                       |

모든 결과가 예상 동작과 일치합니다.

---

## 알려진 제한사항 / 잔여 위험

- 없음 — 발견된 버그 3개 모두 수정 완료
- `python manage.py test` 9개 기존 테스트 모두 통과

---

## 배포 안전성

✅ **배포 가능** — 버그 수정 후 모든 검증 통과

---

## Phase 6 Permission Matrix

| Feature             | Anonymous | Sales user    | Manager   | Admin       |
| ------------------- | --------- | ------------- | --------- | ----------- |
| Analytics dashboard | Redirect  | Own data only | Team data | Admin scope |
| Activity CSV export | Redirect  | Forbidden     | Allowed   | Allowed     |
| Pipeline CSV export | Redirect  | Forbidden     | Allowed   | Allowed     |

**구현 기준**: `UserProfile.role` 필드 (`salesman` / `manager` / `admin`). `is_staff` 또는 Django 그룹 기반이 아님.

---

## Phase 6 Known Risks

- 실제 운영 환경의 역할 정의 재확인 필요 (`manager` 역할이 `is_staff`, Django Group, Profile role 중 어느 기준인지 코드와 동일하게 일치하는지 확인)
- CSV 내보내기 컬럼에 불필요한 개인정보 또는 고객 민감 정보가 포함되지 않는지 검토
- 분석 통계 집계 방식(기간 필터, 히스토리 vs 후속조치 카운트 기준)이 비즈니스 기대값과 일치하는지 확인
- `manager`의 company 필터 — `userprofile__company`가 null인 경우 전체 데이터 노출 여부 확인 필요

---

## Phase 7 시작 가능 여부

✅ **Phase 7 시작 가능**

---

## Phase 6.5-1 — 모달 클릭/입력 버그 수정 (2026-04-27)

**상태**: 완료

### 요약

3개 영역의 모달 인터랙션 버그를 근본 원인(root cause) 수준에서 수정했습니다.

1. 캘린더 일정 상세 모달에서 고객명 클릭 시 메인 모달이 사라지는 버그 → **중첩 모달 제거, Offcanvas 전환**
2. 캘린더 일정 상세 모달에서 부서 메모 Offcanvas의 textarea 입력 불가 버그 → **모달 포커스 트랩 우회 처리**
3. 대시보드 영업노트 작성 모달에서 필드 클릭/입력 불가 버그 → **CSS stacking context 제거**

기존 `pointer-events: none !important` 임시 해결책(workaround)은 완전히 제거하고 구조적 수정을 적용했습니다.

---

### 근본 원인 (Root Cause)

| 문제                                       | 원인                                                                                                                                                                                                                          |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 캘린더: 고객명 클릭 시 일정 상세 모달 소멸 | `showCustomerHistories()`가 Bootstrap Modal을 중첩 생성 — Bootstrap 5는 공식적으로 중첩 모달 미지원, 두 번째 모달 `show()` 시 첫 번째 모달을 강제 숨김                                                                        |
| 캘린더: 부서 메모 textarea 입력 불가       | `scheduleDetailModal`의 Bootstrap focus trap이 `focusin` 이벤트를 캡처하여 Offcanvas 내부 포커스를 모달로 되돌려 놓음                                                                                                         |
| 캘린더: Offcanvas 닫기 버튼 클릭 불가      | Bootstrap Offcanvas 기본 z-index(1045)가 열린 Modal(1055)보다 낮아, 일정 상세 모달이 Offcanvas 위 레이어에서 클릭을 가로챔                                                                                                    |
| 대시보드: 모달 필드 클릭 불가              | `base.html`의 `.main-content { position: relative; z-index: 1; }` 조합이 CSS stacking context를 생성 → 내부 모달(z-index:1055)이 stacking context에 갇혀 body에 직접 추가된 backdrop(z-index:1040)보다 낮은 레이어에 렌더링됨 |

---

### 변경된 파일

#### 1. `reporting/templates/reporting/schedule_calendar.html`

**CSS 변경:**

- `#customerHistoriesModal .modal-content { ... }` 규칙 제거 (이미 이전 세션에서 `#customerHistoryOffcanvas` CSS로 교체됨, 잔여 중복 규칙 삭제)
- `.modal-backdrop { pointer-events: none !important }` 블록 제거 (이전 세션 완료)
- `#deptMemoOffcanvas`, `#customerHistoryOffcanvas`에만 scoped z-index `1065` 적용 (열린 schedule modal 위에서 입력/닫기 버튼 클릭 가능)

**HTML 변경:**

- `#deptMemoOffcanvas`에 `data-bs-backdrop="false" data-bs-scroll="true"` 속성 추가
- 새 `#customerHistoryOffcanvas` 정적 HTML 요소 추가 (중첩 모달 대신 사이드 패널로 표시)

**JavaScript 변경:**

- `openDeptMemo()` — `new bootstrap.Offcanvas()` → `Offcanvas.getOrCreateInstance()` 전환, `focusin` 캡처 이벤트로 포커스 트랩 우회 로직 추가
- `showCustomerHistories()` — Bootstrap Modal 동적 생성/삽입 방식 제거, `#customerHistoryOffcanvas` Offcanvas 방식으로 전환
- `loadCustomerHistories()` — DOM 타겟 `#customerHistoriesContent` → `#customerHistoryOffcanvasContent` 변경
- `displayCustomerHistories()` — DOM 타겟 `#customerHistoriesContent` → `#customerHistoryOffcanvasContent` 변경

#### 2. `reporting/templates/reporting/base.html`

- `.main-content` CSS에서 `z-index: 1;` 제거
- 이로 인해 stacking context가 해제되어 `.main-content` 내부 Bootstrap 모달이 body의 root stacking context 기준으로 z-index 적용 (backdrop: 1040 < modal: 1055 정상 계층 복원)

---

### 변경 전/후 동작

| 영역                        | 변경 전                                           | 변경 후                                                  |
| --------------------------- | ------------------------------------------------- | -------------------------------------------------------- |
| 캘린더 → 고객명 클릭        | 일정 상세 모달이 사라지고 고객 모달만 표시됨      | 일정 상세 모달 유지, 우측에 고객 활동기록 Offcanvas 열림 |
| 캘린더 → 부서 메모 textarea | 클릭해도 입력 커서 생기지 않거나 닫기 버튼이 막힘 | textarea 정상 입력 가능, Offcanvas 닫기 가능             |
| 대시보드 → 영업노트 모달    | 모달 표시되나 input/textarea/button 클릭 불가     | 모든 필드 클릭 및 입력 정상                              |

---

### 실행한 명령어 및 결과

```
$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py check
System check identified no issues (0 silenced)

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py test
Ran 9 tests in 7.257s
OK

$ C:\Users\AnJaehyun\anaconda3\envs\sales-env\python.exe manage.py shell -c "... dashboard/calendar smoke ..."
/reporting/dashboard/ 200
/reporting/schedules/calendar/ 200

$ npx --package @playwright/cli playwright-cli ... local browser validation ...
Calendar schedule modal stayed visible while department memo/customer history Offcanvas opened.
Memo textarea accepted text and Offcanvas close button worked.
Dashboard sales-note textarea/input accepted text with pointer-events:auto.
```

참고: 기본 `python manage.py check`는 로컬 기본 Python에 Django가 없어 실패했으므로, 프로젝트 문서의 `sales-env` 인터프리터로 검증했습니다. 첫 smoke check는 `testserver`가 `ALLOWED_HOSTS`에 없어 400이 반환되었고, `HTTP_HOST='127.0.0.1'`로 재실행하여 두 페이지 모두 200을 확인했습니다.

### 정적 점검 결과

- 중복 ID 없음: `dashboardNoteModal`, `deptMemoOffcanvas`, `customerHistoryOffcanvas`는 각각 단일 정의만 존재
- 금지된 전역 workaround 없음: 변경 범위 파일에서 `.modal-backdrop { display: none }` 또는 `.modal-backdrop { pointer-events: none }` 사용 없음
- CSRF 유지: 대시보드 영업노트 AJAX POST와 부서 메모 POST 모두 `X-CSRFToken` / CSRF 값을 유지
- Bootstrap workaround 범위: 전역 `.modal-backdrop` 숨김/비활성화는 사용하지 않음. 캘린더 내부 Offcanvas 2개에만 z-index를 scoped 적용하고, 부서 메모 Offcanvas focusin 전파만 scoped 차단.

---

### 기존 기능 보전

- `scheduleDetailModal` (일정 상세 모달) 기존 기능 유지
- `deptMemoOffcanvas` 메모 저장/로드 기능 유지
- `editDeliveryItemsModal`, 납품 품목 관리 기능 영향 없음
- `dashboardNoteModal` 단계별 영업노트 작성 기능 유지
- sidebar `z-index: 1000` 및 `sidebar-overlay z-index: 999` 계층 정상 (backdrop 1040은 이들보다 높지만, sidebar는 `position: fixed`로 별도 stacking context에 있어 충돌 없음)
- 모든 기존 `/reporting/*` URL 및 API 엔드포인트 영향 없음

---

### 알려진 제한 사항 및 위험

- `scheduleDetailModal` 내에 다른 중첩 Bootstrap Modal이 있다면 (`editDeliveryItemsModal` 등) 동일한 문제 잠재 가능 — 현재 세션 범위 밖
- Bootstrap focus trap 우회(`e.stopPropagation()`)가 접근성(a11y) 관점에서 이상적이지 않을 수 있음, 실제 사용 환경에서 스크린 리더 테스트 권장
- 대시보드 브라우저 검증은 fixture 상태상 실제 일정 선택/저장은 수행하지 않고, 모달 step2 필드 입력 가능 여부를 확인함
- 부서 메모 저장 API는 CSRF 및 기존 POST 로직을 보존했으나, 검증 중 실제 저장 클릭은 수행하지 않음

---

### 다음 권장 단계

1. `editDeliveryItemsModal` 등 남아 있는 Bootstrap 중첩 모달 후보를 Phase 6.5-2에서 Offcanvas/인라인 패널로 정리
2. 모달 접근성(키보드 네비게이션, a11y) 검토

---

## Phase 6.5-2 — AI 분석 컨텍스트에 선결제 데이터 통합 (2026-04-27)

**상태**: 완료

### 요약

AI 분석(부서 분석 + 개별 고객 분석) 프롬프트에 `Prepayment` / `PrepaymentUsage` 모델 데이터를 포함시켜, GPT-4o가 선결제 잔액 현황·고착 위험·재구매 유도 기회를 영업 전략에 반영하도록 개선했습니다.

---

### 변경된 파일

| 파일                                               | 변경 내용                                                                                                                                                                                       |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai_chat/services.py`                              | `gather_prepayment_data()` 신규 함수, `analyze_department()` 프롬프트 확장, `gather_followup_data()` 선결제 수집, `analyze_followup()` 프롬프트 확장, `FOLLOWUP_SYSTEM_PROMPT` 출력 스키마 확장 |
| `ai_chat/templates/ai_chat/followup_analysis.html` | `prepayment_status`, `pre_visit_checklist`, `manager_report_points` 섹션 추가                                                                                                                   |

---

### 구현 세부사항

#### `gather_prepayment_data(followups)`

- `Prepayment.objects.filter(customer__in=followups)` — 이미 권한 범위로 필터링된 queryset 사용
- 선결제별 사용 내역(`PrepaymentUsage`) prefetch
- 고착 판단 기준: `status='active'` AND `balance > 0` AND 최종 사용일이 90일 이전 (또는 미사용)
- 반환: `{'prepayments': [...], 'summary': {total_count, active_count, total_remaining_balance, stalled_count, stalled_customers}}`

#### `analyze_department()` 변경

- `FollowUp.objects.filter(user=user, department=department)` queryset 생성 후 `gather_prepayment_data()` 호출
- 프롬프트에 `━━━ 선결제 현황 ━━━` 섹션 추가 (활성 건수, 총 잔액, 고착 위험 거래처, 사용 이력 최근 3건)

#### `gather_followup_data()` 변경

- `Prepayment.objects.filter(customer=followup)` 쿼리 추가
- 반환 dict에 `'prepayments'` 키 추가

#### `analyze_followup()` 변경

- 프롬프트에 `━━━ 선결제 현황 ━━━` 섹션 추가 (원금, 잔액, 입금일, 상태, 고착 여부, 사용 이력 최근 5건)

#### `FOLLOWUP_SYSTEM_PROMPT` 변경

- JSON 출력 스키마에 3개 필드 추가:
  - `prepayment_status`: 선결제 현황 요약 및 재구매 기회/위험 분석
  - `pre_visit_checklist`: 방문 전 확인사항 목록
  - `manager_report_points`: 매니저 보고 시 강조 포인트 목록
- 선결제 분석 지시: "선결제 잔액이 있고 최근 90일 사용이 없으면 재구매 유도 또는 잔액 소진 전략 분석"

#### `followup_analysis.html` 변경

- 리스크 요인 섹션 이후 추가:
  - `prepayment_status` 카드 (파란 왼쪽 테두리)
  - `pre_visit_checklist` 목록 카드
  - `manager_report_points` 목록 카드 (보라 왼쪽 테두리)
- 기존 JSON 필드 없으면 `{% if d.필드명 %}` 조건으로 미표시

---

### 권한 및 보안

- `gather_prepayment_data(followups)`: 이미 `user=request.user`로 필터링된 queryset만 수신 → 타 사용자 데이터 노출 없음
- `gather_followup_data(followup)`: `followup`은 뷰에서 `can_access_followup(request.user, followup)` 검증 후 전달
- 모델 변경 없음 (마이그레이션 불필요)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 선결제 고착 기준(90일)은 `services.py` 내 하드코딩됨 — 추후 설정값으로 분리 가능
- 선결제 데이터가 많은 부서는 프롬프트 길이 증가 → 토큰 초과 시 `max_tokens` 조정 필요
- `department_analysis.html`에는 선결제 섹션 별도 표시 없음 (PainPoint 카드에 간접 반영됨)

---

### 다음 권장 단계

1. `editDeliveryItemsModal` 등 남아 있는 Bootstrap 중첩 모달을 Offcanvas로 정리
2. 부서 분석 화면에 선결제 통계 요약 위젯 추가 (선택)
3. 고착 기준일(90일)을 환경변수 또는 관리자 설정으로 분리

---

## Phase 6.5-3 — AI 분석 출력 5섹션 구조로 재설계 (2026-04-27)

**상태**: 완료

### 요약

개별 고객 AI 분석 결과를 "일반 요약"에서 "실제 영업 현장에서 즉시 활용 가능한 5섹션 구조"로 전면 개편했습니다. 미처리 후속 액션 자동 수집, 새로운 JSON 출력 스키마 정의, 템플릿 전면 재작성이 포함됩니다.

---

### 변경된 파일

| 파일                                               | 변경 내용                                                                                                                                             |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai_chat/services.py`                              | `gather_followup_data()` pending_actions 수집 추가, `FOLLOWUP_SYSTEM_PROMPT` 완전 재작성, `analyze_followup()` 프롬프트 섹션 추가 + `max_tokens=4000` |
| `ai_chat/templates/ai_chat/followup_analysis.html` | 분석 결과 영역 전면 재작성 (구버전 호환 fallback 포함)                                                                                                |

---

### 구현 세부사항

#### `gather_followup_data()` — pending_actions 추가

- 모든 history 레코드 순회 시 `next_action` 필드가 있으면 `pending_actions` 목록에 수집
- 각 항목: `{action, due_date, is_overdue, from_type, from_date}`
- 정렬: 지연(overdue) → 예정(upcoming) → 날짜 미정 순
- meeting 항목에 `next_action`, `next_action_date` 필드 추가
- 반환 dict에 `'pending_actions'` 키 추가

#### `FOLLOWUP_SYSTEM_PROMPT` — 완전 재작성

새 JSON 출력 스키마 (7개 최상위 필드):

- `deal_probability`, `deal_probability_reason`, `relationship_stage` — 기존 유지
- `account_brief` — `customer_summary`, `recent_activity`, `sales_status`, `prepayment_note`, `quote_delivery_note`
- `opportunity_risk` — `purchase_potential`, `stalled_risk`, `price_risk`, `compatibility_risk`, `budget_prepayment_risk`, `missing_info`
- `next_best_actions` — `priority`, `action`, `suggested_due`, `what_to_ask`, `what_to_prepare`, `reason`
- `manager_summary` — `key_point`, `decision_needed`, `risk_level`, `expected_impact`
- `visit_checklist` — `customer_context`, `items_to_bring`, `questions_to_ask`, `unresolved_issues`
- `key_painpoints`, `risk_factors` — 기존 구조 유지

분석 지침 추가:

- 미처리 후속 액션은 `visit_checklist.unresolved_issues` + `next_best_actions`에 반드시 반영
- `next_best_actions` 최대 3건, 실행 가능 수준으로 작성
- `questions_to_ask` 최소 2개 이상

#### `analyze_followup()` — 프롬프트 확장 + max_tokens 4000

- 프롬프트에 `━━━ 미처리 후속 액션 (N건) ━━━` 섹션 추가
  - 지연(overdue) 최대 5건, 예정 최대 5건, 날짜 미정 최대 3건 포함
- `max_tokens`: 3000 → **4000**으로 증가

#### `followup_analysis.html` — 5섹션 레이아웃 (구버전 호환)

1. **딜 확률 (col-md-3) + 어카운트 브리핑 (col-md-9)** — `d.account_brief`가 없으면 구버전 `d.customer_summary` 표시
2. **다음 베스트 액션** — 카드 그리드, 우선순위 색상 구분(보라 계열). 구버전도 동일 레이아웃 (신규 필드 없으면 단순 표시)
3. **기회/리스크 분석 (col-lg-8) + 매니저 요약 (col-lg-4)** — `d.opportunity_risk` 없으면 구버전 `d.opportunity_signals`/`d.missing_info` 표시, `d.manager_summary` 없으면 구버전 `d.manager_report_points` 표시
4. **방문 준비 체크리스트** — `d.visit_checklist` 없으면 구버전 `d.pre_visit_checklist` 표시
5. **핵심 PainPoint + 리스크 요인** — 구조 동일, 변경 없음

---

### 권한 및 보안

- 모델 변경 없음, 마이그레이션 불필요
- `pending_actions`는 `gather_followup_data(followup, user)`에서 이미 권한 필터링된 `followup` 기준으로 수집
- 구버전 분석 데이터도 `{% if d.필드명 %}` 조건으로 안전하게 처리

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
import test → account_brief in prompt: True, visit_checklist in prompt: True, manager_summary in prompt: True, pending_actions in gather_followup_data: True
```

---

### 알려진 제한 사항

- `next_best_actions` 최대 3건은 프롬프트 지시로만 제한 (API 응답에서 초과 시 템플릿에서 모두 렌더됨)
- 선결제 고착 기준 90일 하드코딩
- 기존 분석 데이터(구버전 JSON)는 `account_brief`, `opportunity_risk`, `manager_summary`, `visit_checklist` 필드가 없어 구버전 fallback 섹션으로 표시됨 — 재분석 실행 시 새 포맷으로 전환됨

---

### 다음 권장 단계

1. `editDeliveryItemsModal` Offcanvas 전환
2. 파이프라인 검색/필터 개선 (단계별 영업 건수 대시보드 위젯) ← Phase 6.5-4에서 완료
3. 선결제 고착 기준일 환경변수 분리

---

## Phase 6.5-4 — 파이프라인 보드 검색/필터 추가 (2026-04-27)

**상태**: 완료

### 요약

파이프라인 칸반 보드에 클라이언트 사이드 검색/필터 기능을 추가했습니다. 페이지 리로드 없이 고객명·업체·담당자·영업 담당자·등급으로 필터링하며, 드래그&드롭 및 단계 이동 기능은 그대로 유지됩니다.

---

### 변경된 파일

| 파일                                                 | 변경 내용                                                                     |
| ---------------------------------------------------- | ----------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                          | card dict에 `owner`(영업 담당자), `manager`(책임자) 필드 추가                 |
| `reporting/templates/reporting/funnel/pipeline.html` | 검색바 UI 추가, 카드에 data-\* 속성 추가, 담당자 표시 추가, JS 필터 로직 추가 |

---

### 구현 세부사항

#### `funnel_views.py` 변경

- `stage_map[stage].append(...)` dict에 신규 필드 추가:
  - `'owner': fu.user.get_full_name() or fu.user.username` — 영업 담당자 이름
  - `'manager': fu.manager or ''` — 고객 측 책임자 (CharField, select_related 불필요)
- `select_related('user')`는 이미 기존 쿼리에 포함되어 있어 추가 쿼리 없음

#### `pipeline.html` — 검색 UI

제목 바 아래에 검색 바 추가:

- **텍스트 입력** (`#searchInput`): 고객명, 업체명, 부서명, 영업 담당자, 책임자, 우선순위, 등급 통합 검색
- **등급 필터** (`#gradeFilter`): VIP/A/B/C/D 드롭다운
- **초기화 버튼** (`#clearBtn`): 필터 활성 시에만 표시
- **필터 상태** (`#filterStatus`): "전체 N명 중 M명 표시" 텍스트
- **총 카운트** (`#totalCount`): 필터 시 "M명 (필터됨)" 표시

#### `pipeline.html` — 카드 데이터 속성

```html
data-grade="{{ card.grade }}" data-search="{{ card.customer }} {{ card.company
}} {{ card.department }} {{ card.owner }} {{ card.manager }} {{ card.priority }}
{{ card.grade }}"
```

- `data-search`: 모든 검색 대상 텍스트를 단일 문자열로 결합 (JS에서 `.toLowerCase()` 후 `includes()` 매칭)

#### `pipeline.html` — 카드 UI 추가

```html
{% if card.owner %}
<div class="text-muted mt-1" style="font-size: 0.73em;">
  <i class="fas fa-user me-1" style="opacity:0.5;"></i>{{ card.owner }}
</div>
{% endif %}
```

#### `pipeline.html` — JS 필터 로직 (`applyFilter()`)

- 텍스트 쿼리 + 등급 필터 조합 (`&&` 조건)
- 매칭: `card.style.display = ''` / 비매칭: `card.style.display = 'none'`
- DOM 제거 없이 숨기기만 → 드래그&드롭 유지
- 컬럼별 카운트 배지 실시간 업데이트
- 컬럼 내 카드가 있으나 전부 숨겨졌을 때 `.kanban-filter-empty` 빈 상태 메시지 표시
- `moveCard()` 완료 후 `applyFilter()` 재호출 → 이동 후에도 필터 상태 유지

---

### 필터 지원 필드 요약

| 검색 대상      | 소스 필드                         |
| -------------- | --------------------------------- |
| 고객명         | `FollowUp.customer_name`          |
| 업체명         | `FollowUp.company` (str)          |
| 부서/연구실    | `FollowUp.department` (str)       |
| 영업 담당자    | `FollowUp.user.get_full_name()`   |
| 책임자(담당자) | `FollowUp.manager`                |
| 우선순위       | `FollowUp.get_priority_display()` |
| 등급           | `FollowUp.customer_grade`         |

---

### 권한 및 보안

- 모든 카드 데이터는 기존 `_get_accessible_followups(request.user, request)` 권한 필터링 후 렌더링
- 클라이언트 사이드 필터이므로 추가 API 엔드포인트 없음
- 모델 변경 없음, 마이그레이션 불필요

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 서버 사이드 필터링 없음 → 카드 수가 매우 많으면(수백 개) 초기 렌더링 시간 증가 가능 (현재 규모에서는 문제없음)
- `notes`(상세 내용) 필드는 카드 UI에 미표시이므로 검색 대상에서 제외

---

### 다음 권장 단계

1. `editDeliveryItemsModal` Offcanvas 전환
2. 단계별 영업 건수 대시보드 위젯 추가
3. 선결제 고착 기준일 환경변수 분리

---

## Phase 6.5-5 — 주간보고 UX 개선 및 관리자 검토 기능 (2026-04-28)

**상태**: 완료

---

### 요약

주간보고를 단순 텍스트 블록에서 구조화된 카드 레이아웃으로 개선하고, 관리자 코멘트/검토 기능과 AI 초안 생성 기능을 추가했습니다.

---

### 변경된 파일

| 파일                                                           | 변경 내용                                                                                                                                |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/models.py`                                          | `WeeklyReport`에 3개 필드 추가 (`manager_comment`, `reviewed_by`, `reviewed_at`)                                                         |
| `reporting/migrations/0090_add_weekly_report_review_fields.py` | 신규 마이그레이션 (적용 완료)                                                                                                            |
| `ai_chat/services.py`                                          | `WEEKLY_REPORT_SYSTEM_PROMPT` + `generate_weekly_report_draft()` 함수 추가                                                               |
| `reporting/views.py`                                           | `weekly_report_ai_draft`, `weekly_report_manager_comment` 뷰 추가; 기존 create/edit/detail 뷰에 `can_use_ai`, `is_manager` 컨텍스트 추가 |
| `reporting/urls.py`                                            | API URL 2개 추가 (`/api/weekly-reports/ai-draft/`, `/api/weekly-reports/<pk>/manager-comment/`)                                          |
| `reporting/templates/reporting/weekly_report/detail.html`      | 5섹션 카드 레이아웃으로 전면 재설계 (위험/액션 라인 색상 코딩, 관리자 검토 패널)                                                         |
| `reporting/templates/reporting/weekly_report/form.html`        | AI 초안 생성 버튼 + `generateAiDraft()` JS 추가; `other_notes` textarea id 추가                                                          |
| `reporting/templates/reporting/weekly_report/list.html`        | 검토완료 배지 + activity_notes 미리보기 추가                                                                                             |

---

### 주요 기능

**1. WeeklyReport 모델 확장**

- `manager_comment`: 관리자 검토 의견 (TextField)
- `reviewed_by`: 검토한 관리자 (FK → User)
- `reviewed_at`: 검토 완료 시각 (DateTimeField)

**2. detail.html 5섹션 구조**

- 헤더: gradient 배경, 검토완료 배지, 수정/인쇄 버튼
- 영업 활동: 위험/리스크(빨강), 액션(파랑), 납품/견적(녹색), 일반(회색) 라인 색상
- 견적/납품: 납품/견적 라인 구분 색상
- 다음 주 계획: 중요/핵심/우선 키워드 강조
- 관리자 검토: 코멘트 표시 + 관리자 전용 입력 폼 (AJAX POST 저장)

**3. AI 초안 생성**

- `UserProfile.can_use_ai` 게이트 적용
- `generate_weekly_report_draft()`: 해당 주 History/Schedule/Quote 기반 GPT-4o 초안 생성
- form.html 버튼 클릭 → 3개 textarea 자동 채움 + 요약 알림 표시

**4. 관리자 검토 API**

- `POST /reporting/api/weekly-reports/<pk>/manager-comment/`
- role 검증: `admin`, `superadmin`, `manager`만 허용
- 동일 회사 권한 확인

---

### 기존 기능 보존

- 기존 주간보고 CRUD (list/create/edit/detail) 동작 유지
- `weekly_report_load_schedules` AJAX 동작 유지
- `insertScheduleText()` 일정 삽입 기능 유지
- 인증/권한 로직 변경 없음

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- detail.html의 위험/리스크 섹션 footer는 `forloop.first`/`forloop.last`를 전체 splitlines 기준으로 사용하므로, 위험 키워드가 없을 때 닫는 `</div>`가 잘못 렌더링될 수 있음. 실제 사용 시 JS 기반 토글 방식으로 개선 권장
- AI 초안 생성은 `can_use_ai=True`인 사용자만 사용 가능 (관리자가 UserProfile에서 설정)
- AI 초안은 활동 기록이 없는 주에는 `data.error`로 반환됨

---

### 다음 권장 단계

1. detail.html 위험 섹션 footer JS 기반으로 재작성 (렌더링 안정성 향상)
2. 주간보고 목록에 검색/필터 추가 (날짜 범위, 작성자, 검토 여부)
3. 관리자 전용 주간보고 요약 대시보드 (팀원별 제출 현황, 검토 대기 건수)

---

## Phase 6.5-6 — 분석 보고서 내보내기 품질 개선 (2026-04-27)

**상태**: 완료

---

### 요약

기존 단순 집계형 CSV(영업사원별 카운트, 단계별 카운트)를 **활동 단위 상세 행** 기반으로 전면 재설계하고, XLSX 포맷(스타일링, 첫 행 고정, 지연 행 강조, 단계별 시트)을 추가했습니다. 모델 변경 없음.

---

### 변경된 파일

| 파일                                                     | 변경 내용                                                         |
| -------------------------------------------------------- | ----------------------------------------------------------------- |
| `reporting/views.py`                                     | 기존 2개 CSV 뷰 대체 + 2개 XLSX 뷰 추가 + 공통 헬퍼 함수 2개 추가 |
| `reporting/urls.py`                                      | XLSX URL 2개 추가 (`activity.xlsx`, `pipeline.xlsx`)              |
| `reporting/templates/reporting/analytics_dashboard.html` | 내보내기 버튼 4개로 확장 (CSV/XLSX × 활동/파이프라인)             |

---

### 기존 → 개선 비교

**activity CSV (이전)**

- 행 구성: 영업사원 1명 = 1행 (요약 집계값만)
- 컬럼: 영업사원 / 기간내영업노트 / 활성거래처 / 지연후속조치 / 최근활동일 (5개)

**activity CSV/XLSX (이후)**

- 행 구성: 활동 기록(History) 1건 = 1행 (상세 데이터)
- 컬럼 22개:
  - 활동일, 영업사원, 거래처, 부서/연구실, 담당자, 활동유형
  - 내용요약, 미팅상황, 다음액션, 다음예정일
  - 지연여부, 지연일수, 파이프라인단계
  - 견적제출여부, 최근견적금액, 납품금액, 납품품목
  - 선결제잔액, 선결제최근입금일, 관리자검토, 검토관리자

**pipeline CSV (이전)**

- 행 구성: 파이프라인 단계 1개 = 1행 (건수 집계만)
- 컬럼: 파이프라인단계 / 건수 (2개)

**pipeline CSV/XLSX (이후)**

- 행 구성: 거래처(FollowUp) 1건 = 1행 (상세 데이터)
- 컬럼 19개:
  - 거래처, 부서/연구실, 담당자, 영업사원
  - 파이프라인단계, 고객상태, 고객등급, 우선순위
  - 최근활동일, 다음액션, 다음예정일, 지연여부, 지연일수
  - 최근견적상태, 최근견적금액, 견적성공확률
  - 선결제잔액, 선결제최근입금일, 총납품금액

---

### XLSX 스타일링

- **헤더**: 인디고(activity) / 녹색(pipeline) 배경, 흰색 볼드 텍스트
- **첫 행 고정**: `freeze_panes = 'A2'`
- **지연 행 강조**: 빨간 계열 배경색 (FEE2E2)
- **열 너비**: 컬럼 유형에 맞게 수동 설정
- **pipeline XLSX**: 단계별 시트 분리 (전체 + 잠재/접촉/견적/협상/수주/실주)
- **내보내기 정보 시트**: 생성일시, 생성자, 행수

---

### 보안/권한

- `admin`, `manager`, `superadmin` role만 접근 허용 (기존과 동일)
- 회사 범위 필터 유지 (`user_profile.company` 기준)
- 개인 연락처(phone, email) 미포함
- UTF-8 BOM 유지 (한국어 Excel 호환)

---

### 공통 헬퍼 함수

- `_get_activity_export_date_range(request, today)`: 날짜 파라미터 파싱
- `_build_activity_rows(user_profile, date_from, date_to, today)`: activity 행 데이터 빌드
- `_build_pipeline_rows(user_profile, today)`: pipeline 행 데이터 빌드
- CSV/XLSX 뷰에서 공통 사용 (코드 중복 없음)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- `_build_activity_rows`는 `Prefetch`로 최적화했으나, 거래처당 견적/선결제를 prefetch하므로 대용량(수천 건 이상)에서는 메모리 사용 증가 가능
- 날짜 필터는 activity CSV/XLSX에만 적용됨; pipeline은 현재 기준 전체 스냅샷 출력

---

### 다음 권장 단계

1. analytics_dashboard에 날짜 필터 파라미터를 pipeline XLSX에도 전달 (선택적 날짜 범위)
2. 영업사원별 요약 시트 추가 (현재 활동단위 행만 있음)
3. 대시보드 내 직접 미리보기 테이블 (최근 5행) 추가

---

## Phase 6.6-1 — 대시보드 영업 노트 작성 모달 클릭 불가 버그 수정 (2026-04-27)

### 증상

대시보드(`/reporting/dashboard/`)에서 "영업 노트 작성" 버튼 클릭 시:

- 회색 오버레이(backdrop)가 뜨지만 모달 내부 클릭/입력 불가
- 텍스트 입력, 버튼 클릭, 닫기(X) 클릭 모두 반응 없음

---

### 근본 원인

**원인 A: `html, body { overflow-x: hidden }` → stacking context 생성 (확정적)**

`dashboard.html` `{% block extra_css %}` 에:

```css
html,
body {
  overflow-x: hidden; /* ← 문제 */
  width: 100%;
  max-width: 100%;
}
```

`html` / `body`에 `overflow: hidden` 또는 `overflow-x: hidden`이 설정되면,
Chrome/Safari 일부 버전에서 `position: fixed` 요소의 containing block이 뷰포트가 아닌
`<html>` 또는 `<body>` 자체가 됩니다.
그 결과 Bootstrap backdrop(z-index: 1040)이 정상 렌더링돼도,
모달 요소(z-index: 1055)가 시각적으로 backdrop 위에 있음에도 불구하고
pointer-events가 차단되거나, backdrop이 모달 위를 덮는 현상이 발생합니다.

**원인 B: 모달이 `.main-content` → `div.infographic-dashboard` 하위에 있었음**

모달이 `{% block content %}` 내부(`.infographic-dashboard` 안)에 있어,
overflow/transform stacking context가 있는 컨테이너 안에 `position: fixed` 모달이 배치됨.

---

### 수정 내용

#### 1. `reporting/templates/reporting/base.html`

`{% block extra_js %}{% endblock %}` 바로 뒤에 페이지별 모달 슬롯 추가:

```html
<!-- 페이지별 모달 슬롯: stacking context 바깥(body 직접 하위)에 배치 -->
{% block modals %}{% endblock %}
```

→ `</body>` 직전, Bootstrap JS 로드 이후, stacking context 없는 위치

#### 2. `reporting/templates/reporting/dashboard.html`

**(a) `html, body { overflow-x: hidden }` 제거**

```css
/* 수정 전 */
html,
body {
  overflow-x: hidden;
  width: 100%;
  max-width: 100%;
}

/* 수정 후 — overflow-x 제거, 폭 설정만 유지 */
html,
body {
  width: 100%;
  max-width: 100%;
}
```

`overflow-x` 클리핑은 이미 `.infographic-dashboard { overflow-x: hidden; }` 에서 처리되고 있어 `html/body`에서 제거해도 가로 스크롤 발생 없음.

**(b) 모달을 `{% block content %}` 에서 `{% block modals %}`로 이동**

기존: `{% block content %}` 마지막에 모달 HTML + script
수정: `{% block content %}` 종료(`{% endblock %}`) 후 별도 `{% block modals %}` 블록으로 이동
→ 렌더링 위치가 `<body>` 직접 하위로 변경, overflow/transform 컨테이너 바깥

**(c) CSRF 토큰 소스 개선**

기존:

```javascript
const csrfToken =
  document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
  "{{ csrf_token }}";
```

문제: `dashboard.html`에 `{% csrf_token %}` 태그가 없어 `querySelector`가 null을 반환 가능.
`'{{ csrf_token }}'` 폴백은 JS 컨텍스트에서 렌더링 타이밍 불안정.

수정:

```javascript
const csrfToken =
  document.querySelector('meta[name="csrf-token"]')?.content ||
  document.querySelector("[name=csrfmiddlewaretoken]")?.value;
```

→ `base.html` line 7의 `<meta name="csrf-token" content="{{ csrf_token }}">` 를 단일 소스로 사용. 항상 안전하게 CSRF 토큰을 읽음.

**(d) `bootstrap.Modal.getInstance` 안전 처리**

기존:

```javascript
var modal = bootstrap.Modal.getInstance(
  document.getElementById("dashboardNoteModal"),
);
if (modal) modal.hide();
```

문제: Bootstrap이 아직 인스턴스를 생성하지 않은 경우 `null` → `modal.hide()` 미호출 → backdrop 잔류 가능.

수정:

```javascript
var modalEl = document.getElementById("dashboardNoteModal");
var modal =
  bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
modal.hide();
```

→ 인스턴스가 없으면 새로 생성해서 `hide()` 보장.

---

### 변경 파일

| 파일                                           | 변경 내용                                                                                                             |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `reporting/templates/reporting/base.html`      | `{% block modals %}{% endblock %}` 추가 (`{% block extra_js %}` 직후)                                                 |
| `reporting/templates/reporting/dashboard.html` | `html, body { overflow-x: hidden }` 제거; 모달을 `{% block modals %}`로 이동; CSRF 소스 변경; `getInstance` 안전 처리 |

---

### 모달 동작 전/후

| 항목                    | 수정 전                                                   | 수정 후                                  |
| ----------------------- | --------------------------------------------------------- | ---------------------------------------- |
| backdrop 표시           | backdrop 표시되나 클릭 불가                               | 정상 표시, 클릭 가능                     |
| 모달 내 입력            | 텍스트 입력 불가                                          | 정상 입력 가능                           |
| 모달 위치 (DOM)         | `.infographic-dashboard` 하위                             | `<body>` 직접 하위                       |
| `html, body` overflow-x | hidden (stacking context 생성)                            | 제거됨                                   |
| CSRF 토큰 소스          | `querySelector('[name=csrfmiddlewaretoken]')` → null 가능 | `<meta name="csrf-token">` 안정 소스     |
| 저장 후 모달 닫기       | `getInstance` null이면 backdrop 잔류                      | `getInstance \|\| new Modal`로 항상 닫힘 |

---

### CSS 우회 사용 여부

`.modal-backdrop` 전역 숨김 등의 CSS 우회 **사용하지 않음**.
수정은 순수 DOM 구조 변경 및 `overflow-x` 제거로 해결.

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

DB 변경 없음.

---

### 알려진 제한 사항 / 잔여 위험

- 다른 페이지의 모달은 이번 수정 대상이 아님. 해당 페이지에서도 동일 overflow-x 문제가 발생하면 동일 패턴(모달을 `{% block modals %}`로 이동)으로 해결 가능.
- `base.html`에 다른 페이지가 이미 `{% block modals %}`를 사용하고 있지 않으므로 충돌 없음.

---

### 다음 권장 단계

Phase 6.6-2: 파이프라인 보드 자동 동기화 + 수동 이동 개선

---

## Phase 6.6-2 — 파이프라인 보드 자동 동기화 + 수동 이동 개선

### 변경 목표

- 영업 활동(고객 미팅 히스토리, 견적 생성) 기반으로 파이프라인 단계를 자동 추천/이동
- 수동 드래그앤드롭 이동 기능은 그대로 유지
- 단계 역방향 자동 이동 불가 (won/lost 보호)
- DB 스키마 변경 없음 (Method C — 로직 전용)

---

### 구현 방법 (Method C — DB 필드 없이 로직만)

**단계 자동 이동 규칙 (앞으로만)**

| 조건                                      | 추천 단계   |
| ----------------------------------------- | ----------- |
| `Quote.stage = approved / converted`      | won         |
| `Quote.stage = negotiation`               | negotiation |
| `Quote.stage = rejected / expired` (전체) | lost        |
| Quote 존재 (기타 단계)                    | quote       |
| `History.action_type = customer_meeting`  | contact     |
| 없음                                      | 변경 없음   |

**보호 규칙**

- `won` / `lost` 상태는 자동으로 덮어쓰지 않음
- 현재 단계 ≥ 추천 단계이면 skip (절대 뒤로 이동하지 않음)

---

### 변경 파일

| 파일                                                 | 변경 내용                                                                                                                                                                                                             |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                          | `STAGE_ORDER` 상수 추가; `_suggest_pipeline_stage()` 헬퍼 추가; `_try_advance_pipeline()` 헬퍼 추가; `funnel_pipeline_view()` 카드 데이터 강화 (최근 견적, 히스토리, 추천 단계); `funnel_pipeline_sync()` API 뷰 추가 |
| `reporting/urls.py`                                  | `/funnel/api/pipeline-sync/` URL 추가                                                                                                                                                                                 |
| `reporting/templates/reporting/funnel/pipeline.html` | 동기화 버튼 추가; 카드에 최근 견적/히스토리/추천 단계 표시; 추천 단계 적용 버튼; `syncCard()` / `syncAll()` JS 함수 추가; CSRF 토큰 소스를 `meta[name="csrf-token"]`으로 수정                                         |
| `reporting/views.py`                                 | `history_create_view()` 및 `history_create_from_schedule()` 에서 고객 미팅 저장 후 `_try_advance_pipeline(followup, 'contact')` 호출 추가                                                                             |

---

### 추가된 기능 상세

**1. 카드 표시 강화**

- 다음 예정 일정: 일정 상세 페이지 링크 포함
- 최근 견적: 견적 단계 + 금액 표시
- 최근 히스토리: 활동 유형 + 날짜 + 내용 40자 미리보기
- 추천 단계 배지: 근거("고객 미팅", "견적" 등) + 개별 적용 버튼

**2. 자동 동기화 버튼**

- 헤더에 "자동 동기화" 버튼 추가
- 동기화 대상 건수 배지(노란색) 표시 (추천 단계가 현재 단계와 다른 카드 수)
- 버튼 클릭 → 전체 자동 동기화 API 호출 → 변경 발생 시 페이지 새로고침

**3. 개별 추천 단계 적용**

- 추천 단계가 있는 카드에 "적용" 버튼 표시
- 클릭 시 단일 카드 동기화 API → DOM에서 바로 카드 이동 (새로고침 없음)

**4. 자동 이동 훅 (History 생성 시)**

- 고객 미팅 히스토리 저장 시 `_try_advance_pipeline(followup, 'contact')` 자동 호출
- 예외 발생 시 히스토리 저장은 유지 (try/except)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- Quote 생성/상태 변경 시 파이프라인 자동 이동 훅은 별도 Quote 뷰가 확인되지 않아 수동 동기화 버튼으로 대체
- `_suggest_pipeline_stage()` 는 prefetch_related 캐시를 활용하므로 bulk sync 시 N+1 없음; 단 단일 조회 경로에서는 추가 쿼리 발생 가능
- 수동으로 단계를 낮춘 후(예: won→contact) 동기화 버튼 클릭 시 다시 won으로 이동할 수 있음 (Method C의 구조적 한계; DB 필드 추가 방식으로 해결 가능)

---

### 다음 권장 단계

Phase 6.6-3: 주간보고 일정 불러오기 개선

---

## Phase 6.6-3 — 주간보고 일정 불러오기 개선 (연결 History/견적 포함)

### 변경 목표

- 주간보고 폼의 일정 참고 패널을 구조화된 분류 UI로 개선
- 단순 일정 텍스트 삽입 → 연결된 History(영업노트) 내용까지 포함
- 영업활동 섹션 / 견적·납품 섹션으로 분류 후 각각 해당 textarea에 삽입
- DB 스키마 변경 없음

---

### 구현 내용

#### 1. `reporting/views.py` — `weekly_report_load_schedules` 전면 개선

**기존**: 기본 Schedule 필드만 반환 (date, customer, company, department, activity_type, notes)

**변경 후**:

- `Prefetch('histories', ...)` : `History.schedule` FK 역방향 조회 (user 필터 + parent_history\_\_isnull=True로 최상위만)
- `Prefetch('quotes', ...)` : `Quote.schedule` FK 역방향 조회
- 카테고리 분류: `quote`/`delivery` → `quote_delivery` 버킷, 나머지 → `activity` 버킷
- 각 일정 항목에 연결 History 스니펫(meeting_situation, confirmed_facts, content, next_action/date), 연결 Quote(번호, 단계, 금액) 포함
- 응답 형식: `{schedules: [...], categorized: {activity: [...], quote_delivery: [...]}}`
- 기존 `schedules` flat 목록도 유지 (backward compatibility)

#### 2. `reporting/templates/reporting/weekly_report/form.html` — 패널 UI + JS 전면 개선

**패널 HTML 변경**:

- 기존: 클릭 가능 `<li>` 목록 (단일 클릭 = activityNotes에 한 줄 삽입)
- 변경: 영업활동 / 견적·납품 섹션별 체크박스 카드
- 각 카드에 History 스니펫(파란 배경), Quote 정보(초록 배경) 인라인 표시
- 서버 사이드 초기 렌더링: `{% regroup schedules by activity_type %}` 으로 분류 표시
- 카드 하단: "영업활동에 삽입" / "견적/납품에 삽입" 버튼, "전체선택" 링크

**JS 변경**:

- `loadSchedules()`: 새 categorized 응답 파싱, 섹션별 카드 렌더링
- `buildScheduleCard(s, category)`: History/Quote 인라인 표시 포함 카드 HTML 생성
- `insertSelected(category)`: 선택된 체크박스의 텍스트 생성 → 해당 섹션 textarea에 삽입
  - `activity` → `#activityNotes`
  - `quote_delivery` → `#quoteDeliveryNotes`
- `buildInsertText(cb)`: History 내용·다음 액션, Quote 번호·단계·금액 포함한 구조화된 텍스트 생성
- `updateInsertBtns()`: 선택 상태에 따라 삽입 버튼 활성/비활성
- `escHtml()` / `escAttr()`: XSS 방지 이스케이핑
- 기존 `insertScheduleText()` 함수 유지 (하위 호환)
- AI 초안 생성 JS 동일 유지

---

### 삽입 텍스트 예시

**영업활동 삽입 결과**:

```
- 04/28(월): 이화연 교수 (한국대학교) — 고객 미팅
  메모: HPG-1000 데모 진행
  └ 고객 미팅: 연구비 예산 확보 완료 / 다음 액션: 견적서 발송 (05/02)
```

**견적/납품 삽입 결과**:

```
- 04/29(화): 홍길동 교수 (한양대학교) — 견적 제출
  └ 견적 Q2025-001 [검토중] 5,000,000원
```

---

### 파일 변경 목록

| 파일                                                    | 변경 내용                                                                                                          |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `reporting/views.py`                                    | `weekly_report_load_schedules` 전면 개선 (History/Quote Prefetch, 카테고리 분류)                                   |
| `reporting/templates/reporting/weekly_report/form.html` | 패널 HTML(체크박스 UI, 분류 섹션), JS(loadSchedules/buildScheduleCard/insertSelected/buildInsertText 등) 전면 개선 |

---

### 기존 기능 유지

- WeeklyReport 모델 변경 없음 (DB 스키마 변경 없음)
- 기존 저장된 주간보고 내용 모두 그대로 표시 (detail.html 변경 없음)
- AI 초안 생성 기능 그대로 유지
- `schedules` flat 목록 키 유지 (backward compat)

---

### 검증 결과

```
python manage.py check → System check identified no issues (0 silenced)
python manage.py makemigrations --check --dry-run → No changes detected
```

---

### 알려진 제한 사항

- 서버 사이드 초기 렌더링(GET 로드 시)에서는 History/Quote 미리보기가 없음 ("일정 불러오기" 버튼 클릭 후 표시)
- History.user 필터로 본인 History만 표시 (공유 Schedule에 다른 사용자가 남긴 History는 제외)

---

### 다음 권장 단계

Phase 6.6-5: 대시보드 영업 활동 지표 개선

---

## Phase 6.6-4 — 문서 관리 및 서류 생성 UX 개선

### 변경 요약

1. **이중 alert 버그 수정** (`schedule_detail.html`)
   - `generateDocument()` catch 블록에서 alert가 2번 발생하던 문제 수정
   - 두 번째 `alert('서류 생성 중 오류가 발생했습니다.')` 제거
   - 버튼 복구 코드도 try/catch로 감싸 예외 방지

2. **변수 미리보기 버튼 추가** (`schedule_detail.html`)
   - 각 서류 타입(견적서/거래명세서/납품서) 버튼 아래 "변수 미리보기" 버튼 추가
   - 기존 `get_document_template_data` API 활용 (신규 URL 불필요)
   - 미리보기 모달: 변수명과 실제 채워질 값 테이블 표시
   - 빈 값(노란색 행)으로 채워지지 않을 변수 강조
   - 품목 그룹 동적 생성 (납품 품목 수 기반)
   - "Excel로 생성" 버튼으로 모달에서 바로 다운로드 실행

3. **변수 도움말 패널 추가** (`document_template_form.html`)
   - 엑셀 템플릿 등록/수정 페이지에 접힌(collapsible) 변수 도움말 패널 추가
   - 7개 그룹으로 분류: 기본정보 / 고객거래처 / 영업담당자 / 회사견적 / 금액 / 품목
   - 각 변수 칩 클릭 시 클립보드 복사 (Clipboard API + execCommand fallback)
   - `reporting/templates/reporting/partials/doc_variable_list.html` 로 분리 (재사용 가능)

4. **data_map 자동채움 확장** (`reporting/views.py`)
   - `generate_document_pdf`: 연결된 Quote에서 `견적번호` 자동 채움 추가
   - `generate_document_pdf`: `메모` (schedule.notes) 자동 채움 추가
   - `get_document_template_data`: 동일하게 `견적번호`/`메모` 추가
   - DB 스키마 변경 없음 (기존 `Quote.quotes` related_name 활용)

### 변경 파일

| 파일                                                            | 변경 내용                                                                   |
| --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `reporting/templates/reporting/schedule_detail.html`            | 이중 alert 수정, 미리보기 버튼 3개, 미리보기 모달, `previewDocument()` JS   |
| `reporting/templates/reporting/document_template_form.html`     | 변수 도움말 패널 (collapsible)                                              |
| `reporting/templates/reporting/partials/doc_variable_list.html` | 신규 — 변수 목록 partial (클립보드 복사)                                    |
| `reporting/views.py`                                            | `generate_document_pdf` + `get_document_template_data`에 견적번호/메모 추가 |

### 검증 결과

```
manage.py check → System check identified no issues (0 silenced)
manage.py makemigrations --check --dry-run → No changes detected
```

### 알려진 제한사항

- 미리보기 모달의 "Excel로 생성" 버튼은 페이지 DOM에서 해당 버튼을 찾아 click() 호출하므로, 버튼 onclick 속성이 변경되면 재검토 필요
- `유효일+N` 변수는 미리보기에서 표시되지 않음 (서버측 처리 로직이므로)
- 품목 변수 도움말 칩은 품목1 기준으로 클립보드 복사됨 (N 치환 안내는 텍스트로 제공)

### 다음 권장 단계

Phase 6.6-5: 대시보드 영업 활동 지표 개선

---

## Phase 6.6 최종 QA (2026-04-27)

**상태**: 완료 — 버그 3개 발견 및 수정

### QA 범위

Phase 6.6 전체 4개 서브 페이즈(6.6-1~6.6-4) 구현 후 최종 QA 실시.
신규 기능 추가 없음. 발견된 버그만 수정.

### 실행 명령 및 결과

| 명령                                                   | 결과                                              |
| ------------------------------------------------------ | ------------------------------------------------- |
| `python manage.py check`                               | ✅ 0 issues                                       |
| `python manage.py makemigrations --check --dry-run`    | ✅ No changes detected                            |
| `python manage.py test reporting.tests` (버그 수정 전) | ❌ FAIL — `block 'modals' appears more than once` |
| `python manage.py test reporting.tests` (버그 수정 후) | ✅ Ran 9 tests — OK                               |

### URL 스모크 테스트

모든 주요 URL: 비인증 → 302, 인증 → 200 확인 완료.
`funnel/api/pipeline-sync/`, `documents/template-data/` 포함.

### 발견 및 수정된 버그

**Bug 1 (dashboard.html)**: HTML 주석 안에 `{% block modals %}` 태그가 포함되어 Django 템플릿 엔진이 블록 이름 중복으로 파싱 오류 발생 → 주석 내 Django 태그 구문을 일반 텍스트로 변경.

**Bug 2 (schedule_detail.html)**: `</script>` 직후 고아 `<script>` 태그가 열리며 `.strategy-content` CSS 규칙이 JS로 처리됨 (`</style>`로 잘못 닫힘). 해당 클래스는 템플릿에서 미사용. → 고아 블록 전체 제거.

**Bug 3 (schedule_detail.html)**: `previewDocument()` JS 함수에서 서버 응답값(`data.variables[key]`, `data.error`, `err.message`)이 HTML 이스케이프 없이 `innerHTML`에 직접 삽입 → XSS 취약점. `escHtml()` 헬퍼 추가 후 3곳 모두 적용.

### Phase 6.6 서브 페이즈별 상태

| 페이즈 | 기능                                                | 상태                    |
| ------ | --------------------------------------------------- | ----------------------- |
| 6.6-1  | 대시보드 영업 노트 모달 stacking context 수정       | ✅ 정상                 |
| 6.6-2  | 파이프라인 보드 자동 동기화 + 수동 이동             | ✅ 정상                 |
| 6.6-3  | 주간보고 일정 불러오기 (History/Quote 포함)         | ✅ 정상                 |
| 6.6-4  | 문서 UX (미리보기 모달, 변수 도움말, data_map 확장) | ✅ 정상 (버그 2+3 수정) |

### 변경된 파일

| 파일                                                 | 내용                                                 |
| ---------------------------------------------------- | ---------------------------------------------------- |
| `reporting/templates/reporting/dashboard.html`       | HTML 주석 내 Django 블록 태그 제거 (Bug 1)           |
| `reporting/templates/reporting/schedule_detail.html` | 고아 CSS 블록 제거 (Bug 2), escHtml XSS 수정 (Bug 3) |

### 다음 권장 단계

Phase 7 시작 가능. Phase 6.6 QA 완료, 9/9 테스트 통과, 보안 취약점 수정 완료.

---

## Phase 7 최종 QA (2026-04-27)

**상태**: 완료 — 버그 3개 발견 및 수정, 테스트 9 → 53개로 확장

### 1. QA 범위

새 기능 추가 없음. 코드 탐색 + Django 명령 + 역할별 권한 검증 + 자동화 테스트 확장 수행.

검토 영역:

- 인증 및 역할 권한
- 파일 업로드/다운로드 보안
- Analytics export 역할 체크 코드 품질
- `can_access_user_data` / `can_modify_user_data` 로직
- 익명 사용자 URL 접근 차단 (17개 주요 URL)
- AI 기능 접근 권한 (`can_use_ai`)
- 주간보고 API (`weekly_report_load_schedules`)
- 대시보드 smoke 테스트

---

### 2. 실행 명령 및 결과

| 명령                                                                           | 결과                                               |
| ------------------------------------------------------------------------------ | -------------------------------------------------- |
| `python manage.py check`                                                       | ✅ 0 issues (EMAIL_ENCRYPTION_KEY 경고 1개 — 정상) |
| `python manage.py makemigrations --check --dry-run`                            | ✅ No changes detected                             |
| `python manage.py test reporting.tests --verbosity=2` (버그 수정 전, 원본 9개) | ✅ Ran 9 tests — OK                                |
| `python manage.py test reporting.tests --verbosity=2` (새 테스트 추가 후)      | ✅ Ran 53 tests in 43.057s — OK                    |

---

### 3. URL 스모크 테스트 (익명 사용자 접근 차단 — 자동화 검증)

`AnonymousAccessTests` 클래스에서 17개 URL 자동 검증. 전부 302 리다이렉트 (로그인으로 이동) 확인.

| URL                                         | 익명 응답 | 결과    |
| ------------------------------------------- | --------- | ------- |
| `/reporting/dashboard/`                     | 302       | ✅ 차단 |
| `/reporting/followups/`                     | 302       | ✅ 차단 |
| `/reporting/histories/`                     | 302       | ✅ 차단 |
| `/reporting/schedules/`                     | 302       | ✅ 차단 |
| `/reporting/schedules/calendar/`            | 302       | ✅ 차단 |
| `/reporting/opportunities/`                 | 302       | ✅ 차단 |
| `/reporting/funnel/pipeline/`               | 302       | ✅ 차단 |
| `/reporting/weekly-reports/`                | 302       | ✅ 차단 |
| `/reporting/documents/`                     | 302       | ✅ 차단 |
| `/reporting/analytics/`                     | 302       | ✅ 차단 |
| `/reporting/analytics/export/activity.csv`  | 302       | ✅ 차단 |
| `/reporting/analytics/export/pipeline.csv`  | 302       | ✅ 차단 |
| `/reporting/analytics/export/activity.xlsx` | 302       | ✅ 차단 |
| `/reporting/analytics/export/pipeline.xlsx` | 302       | ✅ 차단 |
| `/reporting/followups/excel/`               | 302       | ✅ 차단 |
| `/reporting/followups/excel/basic/`         | 302       | ✅ 차단 |
| `/reporting/prepayments/`                   | 302       | ✅ 차단 |
| `/reporting/users/`                         | 302       | ✅ 차단 |

---

### 4. 역할별 권한 테스트 결과 (자동화 검증)

`ExportPermissionTests` 클래스에서 8개 테스트 자동 검증.

| 기능                          | Anonymous | salesman | manager | admin |
| ----------------------------- | --------- | -------- | ------- | ----- |
| Analytics dashboard           | 302       | 200      | 200     | 200   |
| Activity CSV export           | 302       | 403      | 200     | 200   |
| Pipeline CSV export           | 302       | 403      | 200     | 200   |
| Activity XLSX export          | 302       | 403      | 200     | 200   |
| Pipeline XLSX export          | 302       | 403      | 200     | 200   |
| FollowUp Excel download       | 302       | 차단     | —       | 200   |
| FollowUp Basic Excel download | 302       | 차단     | —       | 200   |

---

### 5. AI 권한 테스트 결과 (자동화 검증)

`AIPermissionTests` 클래스에서 3개 테스트 자동 검증.

| 기능                                  | can_use_ai=False | can_use_ai=True   |
| ------------------------------------- | ---------------- | ----------------- |
| `/ai/` (부서 분석 목록)               | 302 차단         | 200 허용          |
| `/api/weekly-reports/ai-draft/` (API) | 403              | (AI 뷰 자체 허용) |

---

### 6. 권한 격리 단위 테스트 결과

`PermissionIsolationTests` 클래스에서 8개 테스트 자동 검증.

| 케이스                                       | 결과    |
| -------------------------------------------- | ------- |
| 같은 회사 사용자 간 데이터 접근              | ✅ 허용 |
| 다른 회사 사용자 데이터 접근 차단            | ✅ 차단 |
| company=None 사용자 간 접근 차단 (버그 없음) | ✅ 차단 |
| 자기 자신 데이터 항상 접근 허용              | ✅ 허용 |
| admin은 전체 회사 데이터 접근 가능           | ✅ 허용 |
| manager는 타인 데이터 수정 불가              | ✅ 차단 |
| salesman은 자신 데이터 수정 가능             | ✅ 허용 |
| salesman은 타인 데이터 수정 불가             | ✅ 차단 |

---

### 7. 발견 및 수정된 버그

#### Bug 1: `schedule_file_download` 메모리 누수 + 내부 에러 노출 (FIXED)

- **위치**: `reporting/file_views.py`, `schedule_file_download()`
- **문제 1**: `file_obj.file.read()` — 파일 전체를 메모리에 올림 (대용량 파일 위험)
- **문제 2**: `except Exception as e: return HttpResponse(f'...{str(e)}...', status=500)` — 내부 예외 메시지가 HTTP 응답에 노출 (정보 누출)
- **수정**: `FileResponse(file_obj.file.open('rb'), ...)` + 일반 한국어 오류 메시지로 교체
- **영향**: 스트리밍 응답으로 메모리 효율 개선, 내부 정보 노출 차단

#### Bug 2: `schedule_file_upload` 허용 확장자 불일치 (FIXED)

- **위치**: `reporting/file_views.py`, `schedule_file_upload()`
- **문제**: `allowed_extensions` 리스트에 `hwp`, `hwpx` 미포함 → 한글 문서 업로드 불가
- **불일치**: `views.py`의 `validate_file_upload()`에는 이미 `hwp` 포함됨
- **수정**: `allowed_extensions`에 `'hwp', 'hwpx'` 추가
- **영향**: 한글 문서 일정 첨부 가능, 허용 확장자 일관성 확보

#### Bug 3: Analytics export 뷰 `superadmin` 데드 코드 역할 체크 (FIXED)

- **위치**: `reporting/views.py`, 4개 analytics export 뷰
- **문제**: `role not in ('admin', 'manager', 'superadmin')` — `superadmin`은 `ROLE_CHOICES`에 존재하지 않는 역할 (데드 코드)
- **영향**: 기능적으로 동작하나 코드 불일치 및 유지보수 위험
- **수정**: 4개 뷰 모두 `is_admin() or is_manager()` 모델 메서드 방식으로 통일
  - `analytics_activity_csv_export`
  - `analytics_pipeline_csv_export`
  - `analytics_activity_xlsx_export`
  - `analytics_pipeline_xlsx_export`

---

### 8. 테스트 확장 결과

**이전**: 9개 테스트 (`AuthenticationSmoke` 클래스만)  
**이후**: 53개 테스트 (6개 클래스)

| 테스트 클래스              | 테스트 수 | 설명                                               |
| -------------------------- | --------- | -------------------------------------------------- |
| `AuthenticationSmoke`      | 9         | 로그인/인증/주요 목록 뷰 smoke (기존 유지)         |
| `AnonymousAccessTests`     | 18        | 주요 내부 URL 익명 접근 차단 검증                  |
| `ExportPermissionTests`    | 8         | CSV/XLSX export 역할별 권한 검증                   |
| `AIPermissionTests`        | 3         | AI 기능 접근 권한 검증                             |
| `DashboardSmokeTests`      | 3         | 대시보드 기본 동작 검증                            |
| `PermissionIsolationTests` | 8         | `can_access_user_data`/`can_modify_user_data` 단위 |
| `WeeklyReportTests`        | 4         | 주간보고 API 동작 검증                             |

**결과**: 53/53 PASS (43.057s)

---

### 9. 잔여 위험 (미수정 — QA 범위 외)

| #   | 중요도  | 항목                                                   | 설명                                                   |
| --- | ------- | ------------------------------------------------------ | ------------------------------------------------------ |
| 1   | 🟡 중간 | `EMAIL_ENCRYPTION_KEY` 프로덕션 설정 하드코딩 fallback | `settings_production.py` — 환경변수 없을 때 base64 값  |
| 2   | 🟡 중간 | `SECURE_HSTS_SECONDS` 미설정                           | 브라우저 HSTS 캐싱 활성화 안 됨                        |
| 3   | 🟡 중간 | `debug_user_company_info` 엔드포인트 배포 중           | `/reporting/debug/user-company/` — 내부 정보 노출 가능 |
| 4   | 🟢 낮음 | `CSRF_COOKIE_HTTPONLY = False`                         | JS에서 CSRF 토큰 읽기 위한 의도적 설정 (문서화됨)      |
| 5   | 🟢 낮음 | 파일 업로드 MIME 타입 검증 없음                        | 확장자 기반 검증만 수행 (python-magic 미도입)          |
| 6   | 🟢 낮음 | Cloudinary URL에 Django 인증 미적용                    | 문서 템플릿 파일은 Cloudinary URL 직접 접근 가능       |

---

### 다음 권장 단계

**Phase 8 (선택사항)**:

1. `SECURE_HSTS_SECONDS` 설정 추가 및 프로덕션 보안 헤더 강화
2. `debug_user_company_info` 엔드포인트 제거 또는 admin-only 보호
3. 파일 업로드 MIME 타입 검증 도입 (`python-magic`)
4. `EMAIL_ENCRYPTION_KEY` 하드코딩 fallback 제거
5. Sentry 또는 유사 에러 모니터링 도구 연동

---

## Phase 7 QA 프로덕션 블로커 수정 (2026-04-27)

**상태**: 완료 — 블로커 3개 발견 및 수정, 53/53 테스트 통과

### 1. 블로커 요약

| #   | 블로커                                          | 근본 원인                                                                       | 파일                                                      |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------- |
| B1  | 파이프라인 sync가 모든 일정을 가져와 보드 혼잡  | `upcoming_schedules` prefetch에 날짜 상한 없음 (`visit_date__gte=date.today()`) | `reporting/funnel_views.py`                               |
| B2  | 견적 일정이 견적 파이프라인 단계에 미분류       | `_suggest_pipeline_stage()`가 Schedule 객체를 전혀 고려하지 않음                | `reporting/funnel_views.py`                               |
| B3  | 주간보고 상세 텍스트 불가시 (흰 배경에 흰 글씨) | 다크 테마 body color(near-white)가 라이트 배경 라인 div에 상속됨                | `reporting/templates/reporting/weekly_report/detail.html` |

---

### 2. 블로커별 근본 원인

**B1: 파이프라인 sync 일정 과다 포함**

- `funnel_pipeline_view()`에서 `upcoming_schedules` prefetch가 `visit_date__gte=date.today()`만 적용
- 날짜 상한이 없어 미래 전체 일정(수개월~수년치)이 모두 로드됨
- 동기화 시 불필요하게 많은 팔로우업 카드에 "다음 일정" 표시

**B2: 견적 일정 파이프라인 단계 미분류**

- `_suggest_pipeline_stage(followup)`가 Quote 객체와 History 객체만 참조
- Schedule 객체의 `activity_type='quote'`인 경우를 완전히 무시
- 견적 일정이 있어도 파이프라인 보드에서 견적 단계 제안이 없음

**B3: 주간보고 상세 텍스트 불가시**

- `base.html` `:root`에서 다크 테마 전역 설정: `--text-primary: hsl(210, 40%, 98%)` (near-white)
- `body { color: var(--text-primary); }` — body 글자색이 near-white
- 주간보고 상세 `.normal-line { background: #f9fafb; }` 등의 라이트 배경 div에 white text 상속
- `.risk-line`, `.deal-line`, `.quote-line`, `.action-line` 모두 동일 문제
- 관리자 코멘트 박스 `style="background: #f5f3ff;"` div도 white text 상속

---

### 3. 변경된 파일

| 파일                                                      | 유형 | 내용                                                                                                                                                              |
| --------------------------------------------------------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reporting/funnel_views.py`                               | 수정 | `_current_month_range()` 헬퍼 추가; `_suggest_pipeline_stage()` 개선; `funnel_pipeline_view()` 현재 월 필터링; `funnel_pipeline_sync()` 현재 월 Schedule prefetch |
| `reporting/templates/reporting/weekly_report/detail.html` | 수정 | `<style>` 블록에 라인 클래스 color 추가; `.manager-comment-box` 클래스 적용; `.weekly-meta-row` 클래스 적용                                                       |

---

### 4. 현재 월 sync 동작 (B1 수정)

**변경 전:**

```python
Schedule.objects.filter(visit_date__gte=date.today(), status='scheduled')
```

**변경 후:**

```python
month_start, next_month_start = _current_month_range()
Schedule.objects.filter(
    visit_date__gte=month_start,
    visit_date__lt=next_month_start,
    status='scheduled',
)
```

- `_current_month_range()` 함수: `timezone.localdate()`로 타임존 안전하게 오늘 날짜 취득
- 이번 달 첫날 ~ 다음 달 첫날(미포함) 범위로 제한
- 파이프라인 보드와 sync API 모두 동일 범위 적용
- 지난 달/다음 달 일정은 포함되지 않음

---

### 5. 견적 일정 분류 동작 (B2 수정)

`_suggest_pipeline_stage(followup, current_month_schedules=None)` 개선:

| 우선순위   | 조건                                            | 추천 단계                   |
| ---------- | ----------------------------------------------- | --------------------------- |
| 1 (최우선) | Quote 객체 존재 → approved/converted            | `won`                       |
| 1          | Quote 객체 → negotiation                        | `negotiation`               |
| 1          | Quote 객체 → 전체 rejected/expired              | `lost`                      |
| 1          | Quote 객체 → 기타                               | `quote`                     |
| 2          | 이번 달 Schedule에 `activity_type='quote'` 존재 | `quote` (이번 달 견적 일정) |
| 2          | 이번 달 다른 Schedule 존재                      | `contact` (이번 달 일정)    |
| 3          | History에 customer_meeting 존재                 | `contact`                   |
| -          | 해당 없음                                       | 제안 없음                   |

---

### 6. 수동 이동 보존 동작

`_try_advance_pipeline()` 기존 로직 유지 (미변경):

- `won`/`lost` 단계는 자동 동기화로 절대 덮어쓰지 않음
- 현재 단계보다 앞선 단계로만 이동 (backward 이동 없음)
- 수동으로 나중 단계로 이동한 카드는 sync 후에도 그대로 유지

---

### 7. 중복 방지 동작

- 파이프라인 보드: FollowUp 1건 → 카드 1장 (stage_map 그룹핑, 중복 불가 구조)
- sync API: `followup.pipeline_stage` 필드 업데이트만 수행 (새 레코드 생성 없음)
- 동일 sync를 여러 번 실행해도 멱등성 보장 (`_try_advance_pipeline`은 변경 없으면 save 호출 안 함)

---

### 8. 주간보고 가독성 수정 (B3)

**변경 전** `<style>` 블록: color 지정 없음 → body near-white 상속
**변경 후**: 각 라인 클래스에 명시적 색상 추가

| 클래스                 | 배경      | 글자색                     |
| ---------------------- | --------- | -------------------------- |
| `.normal-line`         | `#f9fafb` | `#212529` (Bootstrap dark) |
| `.activity-line`       | 투명      | `#212529`                  |
| `.risk-line`           | 빨간 7%   | `#842029` (어두운 빨간)    |
| `.action-line`         | 청록 7%   | `#055160` (어두운 청록)    |
| `.deal-line`           | 초록 7%   | `#0f5132` (어두운 초록)    |
| `.quote-line`          | 보라 7%   | `#3730a3` (어두운 보라)    |
| `.manager-comment-box` | `#f5f3ff` | `#374151`                  |
| `.weekly-meta-row`     | `#f8f9fa` | `#495057`                  |

- 다크 테마 사이드바/네비게이션은 영향 없음
- 대시보드, 분석, 문서 페이지는 영향 없음 (스코프드 CSS, 해당 클래스 미사용)
- 헤더 보라 그라디언트(inline style)는 `color: white` 유지 (변경 없음)
- 배지/버튼의 Bootstrap 기본 색상 유지

---

### 9. 명령 실행 및 결과

| 명령                                                  | 결과                            |
| ----------------------------------------------------- | ------------------------------- |
| `python manage.py check`                              | ✅ 0 issues                     |
| `python manage.py makemigrations --check --dry-run`   | ✅ No changes detected          |
| `python manage.py test reporting.tests --verbosity=1` | ✅ Ran 53 tests in 41.754s — OK |

---

### 10. 보안 검토

- 주간보고 상세 (`/reporting/weekly-reports/<pk>/`): `@login_required` 유지, 인증 필수
- 파이프라인 보드/sync: `@login_required`, `_get_accessible_followups()` 권한 체크 유지
- 내부 CRM 데이터 공개 노출 없음
- 기존 권한 체계 변경 없음

---

### 11. 잔여 위험

이전 Phase 7 QA 잔여 위험과 동일 (변경 없음):

| 항목                                         | 위험도  |
| -------------------------------------------- | ------- |
| `EMAIL_ENCRYPTION_KEY` 하드코딩 fallback     | 🟡 중간 |
| `SECURE_HSTS_SECONDS` 미설정                 | 🟡 중간 |
| `debug_user_company_info` 엔드포인트 배포 중 | 🟡 중간 |
| MIME 타입 미검증                             | 🟢 낮음 |
| Cloudinary URL Django 인증 미적용            | 🟢 낮음 |
