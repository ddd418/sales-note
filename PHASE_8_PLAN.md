# PHASE 8 PLAN — 보안 강화 및 권한/파일 안정화

> **목표**: 새 비즈니스 기능 추가 없이 보안 취약점 수정, 권한 구조 안정화,
> 파일 업로드 안전성 개선, 자동화 회귀 테스트 보강, 배포 준비 점검.
>
> **범위 제한**:
>
> - 비즈니스 기능 추가 금지
> - UI/UX 재설계 금지
> - 보안 요구가 없는 경우 공개 동작 변경 금지
> - 관련 없는 리팩터링 금지
> - 기존 64개 테스트 전부 통과 유지 필수

---

## 1. 현재 `settings_production.py` 보안 설정 요약

| 설정 항목                     | 현재 상태                                    |
| ----------------------------- | -------------------------------------------- |
| `SECRET_KEY`                  | 환경변수 미설정 시 `RuntimeError` 발생 ✅    |
| `DEBUG`                       | 환경변수 `DEBUG=true` 로 제어 ✅             |
| `ALLOWED_HOSTS`               | `*.railway.app` 포함 (와일드카드 미작동) ⚠️  |
| `CSRF_COOKIE_SECURE`          | `not DEBUG` ✅                               |
| `SESSION_COOKIE_SECURE`       | `not DEBUG` ✅                               |
| `EMAIL_ENCRYPTION_KEY`        | 하드코딩 폴백 존재 🔴 **CRITICAL**           |
| `SECURE_HSTS_SECONDS`         | **미설정** ⚠️                                |
| `SECURE_SSL_REDIRECT`         | **미설정** ⚠️                                |
| `SECURE_CONTENT_TYPE_NOSNIFF` | **미설정** ⚠️                                |
| `X_FRAME_OPTIONS`             | Django 기본값 `DENY` (SecurityMiddleware) ✅ |
| `MEDIA_ROOT`                  | `/data/media` (Railway Volume) ✅            |

---

## 2. HTTPS / 보안 헤더 현황

### 미설정 항목

- `SECURE_HSTS_SECONDS` — HSTS 미설정. HTTPS 강제 없음.
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` — 미설정.
- `SECURE_HSTS_PRELOAD` — 미설정.
- `SECURE_SSL_REDIRECT` — 미설정. HTTP → HTTPS 리다이렉트 없음.
- `SECURE_CONTENT_TYPE_NOSNIFF` — 미설정. MIME 스니핑 방지 없음.
- `SECURE_REFERRER_POLICY` — 미설정.

### 설정된 항목

- `X-Frame-Options: DENY` — `django.middleware.security.SecurityMiddleware` 가 기본 제공. ✅
- `CSRF_COOKIE_SECURE = not DEBUG` ✅
- `SESSION_COOKIE_SECURE = not DEBUG` ✅

### Railway 프록시 주의사항

Railway는 HTTPS 종단(termination)을 프록시에서 처리한다.
`SECURE_SSL_REDIRECT = True` 설정 시 리다이렉트 루프가 발생할 수 있으므로
반드시 다음을 함께 설정해야 한다:

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

HSTS는 짧은 유효기간(300초)부터 시작하고 환경변수로 제어하는 것이 안전하다.

---

## 3. HSTS 안전 활성화 판단

### 전제 조건

- Railway가 HTTPS를 프록시 레이어에서 처리하므로 Django 앱까지 HTTP로 도달.
- `SECURE_PROXY_SSL_HEADER` 없이 `SECURE_SSL_REDIRECT` 단독 활성화 → **무한 리다이렉트**.

### 권장 접근법

```python
# settings_production.py 추가 예정
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'

_hsts_seconds = int(os.environ.get('HSTS_SECONDS', '0'))
if _hsts_seconds > 0:
    SECURE_HSTS_SECONDS = _hsts_seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # 프리로드는 별도 신청 필요, 기본 False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

환경변수 예시:

```
SECURE_SSL_REDIRECT=true
HSTS_SECONDS=300        # 초기 짧은 기간 (5분)
```

검증 후:

```
HSTS_SECONDS=31536000   # 1년
```

---

## 4. 현재 역할/권한 구조

### 역할 3종

| 역할     | 코드       | 설명                                                    |
| -------- | ---------- | ------------------------------------------------------- |
| Admin    | `admin`    | 모든 데이터 접근/수정, 사용자 관리                      |
| Manager  | `manager`  | 같은 회사 데이터 조회(읽기 전용), 실무자 계정 생성 가능 |
| Salesman | `salesman` | 본인/같은 회사 고객 조회, 본인 데이터만 수정            |

### 보조 플래그

- `can_download_excel` — 엑셀 내보내기 권한
- `can_use_ai` — AI 분석 기능 권한

### 핵심 권한 헬퍼 (views.py 121행 / 14921행 — 중복 정의됨)

- `role_required(allowed_roles)` — 데코레이터. 미인증 시 login, 역할 불일치 시 dashboard 리다이렉트. `UserProfile.DoesNotExist` 시 salesman 프로필 자동 생성.
- `can_access_user_data(request_user, target_user)` — 자기 자신=True, admin=True, 같은 UserCompany=True, 나머지=False.
- `can_modify_user_data(request_user, target_user)` — admin=True, manager=False(읽기 전용), salesman=자기 자신만 True.

---

## 5. Manager 역할 리스크 평가

### 안전한 부분

- `can_modify_user_data` 에서 manager는 항상 `False` → 쓰기/삭제 불가 ✅
- `role_required(['admin', 'salesman'])` 패턴이 쓰기 뷰에서 manager를 명시 배제 ✅
- `ExportPermissionTests` 에서 manager는 내보내기 가능(200), salesman은 403 확인 ✅

### 잠재적 리스크

- `role_required` 에서 `UserProfile.DoesNotExist` 시 salesman 프로필 자동 생성 → 의도치 않은 권한 상승 가능성 (Django admin에서 생성한 User에게).
- Manager가 같은 회사 salesman 계정을 `manager_user_create` 뷰로 생성 가능 → 생성된 계정의 초기 비밀번호 강도 검증 없음.

---

## 6. 현재 파일 업로드 검증 동작

### `validate_file_upload()` (views.py 14962행)

- 최대 크기: 10MB ✅
- 허용 확장자 화이트리스트: `.pdf .doc .docx .xls .xlsx .ppt .pptx .txt .jpg .jpeg .png .gif .zip .rar .hwp .hwpx` ✅
- **MIME 타입 검사: 없음** ⚠️

### `schedule_file_upload()` (file_views.py)

- 동일한 확장자 화이트리스트 + 10MB + 5파일 제한 ✅
- **MIME 타입 검사: 없음** ⚠️

### `document_template_create()` (views.py)

- 확장자 화이트리스트만 체크
- **MIME 타입 검사: 없음** ⚠️

### FileField 업로드 경로 (models.py)

- `history_files/%Y/%m/`
- `schedule_files/%Y/%m/`
- `document_templates/%Y/`
- `email_attachments/%Y/%m/`
- `business_card_logos/%Y/`

---

## 7. 파일 업로드 리스크

| 리스크                | 설명                                                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| MIME 타입 스푸핑      | `.jpg` 확장자이지만 실제로는 PHP/스크립트 파일 업로드 가능                                                                                 |
| 컨텐츠 인스펙션 없음  | 악성 매크로가 포함된 `.docx/.xlsx` 탐지 불가                                                                                               |
| 미디어 파일 인증 없음 | 파일 URL을 직접 알면 비인증 접근 가능할 수 있음 (file_views.py 가 `can_access_user_data` 로 다운로드 보호하지만 직접 URL 노출 여부 미확인) |

### MIME 검증 구현 방향

Python 표준 라이브러리 `imghdr` 또는 서드파티 `python-magic`을 사용할 수 있으나,
Railway 환경에서 `libmagic` 시스템 패키지 설치 가능 여부를 먼저 확인해야 한다.

대안: `imghdr` + 파일 시그니처(매직 바이트) 수동 비교 방식으로 이미지 파일에 한해 검증.
문서 파일(`.pdf`, `.docx`, `.xlsx`)은 구조 헤더 검사로 최소 확인.

---

## 8. 기존 디버그 엔드포인트

### 발견된 엔드포인트

| URL                              | 뷰 함수                   | 현재 권한      | 위치                        |
| -------------------------------- | ------------------------- | -------------- | --------------------------- |
| `/reporting/debug/user-company/` | `debug_user_company_info` | superuser 전용 | views.py:10057, urls.py:107 |

### 리스크

- `is_superuser` 체크가 있어 일반 사용자는 접근 불가. ✅
- 그러나 **프로덕션 환경에 디버그 엔드포인트가 노출** 자체가 취약점.
- 공격자가 URL 구조를 파악하는 데 사용될 수 있음.
- 비밀번호 무차별 대입 등으로 superuser 권한 탈취 시 내부 정보 노출.

### 처리 방안

1. `urls.py`에서 경로 제거 (권장).
2. 또는 환경변수 `ENABLE_DEBUG_ENDPOINTS`가 설정된 경우만 URL 등록.

---

## 9. 현재 자동화 테스트 커버리지

### 테스트 파일: `reporting/tests.py`

총 **64개 테스트**, 전부 통과 (Ran 64 tests in 62.260s OK)

| 클래스                       | 테스트 수 | 커버 범위                                               |
| ---------------------------- | --------- | ------------------------------------------------------- |
| `AuthenticationSmoke`        | 9         | 로그인/로그아웃 smoke                                   |
| `AnonymousAccessTests`       | 17        | 비인증 시 URL 차단                                      |
| `ExportPermissionTests`      | 8         | CSV/XLSX 내보내기: salesman=403, manager=200, admin=200 |
| `AIPermissionTests`          | 3         | `can_use_ai` 플래그 강제                                |
| `DashboardSmokeTests`        | 3         | 대시보드 200, 비인증 리다이렉트, 핵심 요소              |
| `PermissionIsolationTests`   | 8         | `can_access_user_data`, `can_modify_user_data` 로직     |
| `WeeklyReportTests`          | 4         | 주간 리포트 API 인증/날짜                               |
| `ManagerRolePermissionTests` | 11        | Manager 쓰기 차단, Salesman 쓰기 허용                   |

### 미커버 영역

- 파일 업로드 MIME 스푸핑 테스트
- 디버그 엔드포인트 접근 제어 테스트
- 미디어 파일 직접 URL 인증 보호 테스트
- 보안 헤더 응답 포함 여부 테스트
- `ALLOWED_HOSTS` 와일드카드 동작 테스트
- `EMAIL_ENCRYPTION_KEY` 미설정 시 에러 발생 테스트

---

## 10. 회귀 보호 영역

아래 항목은 Phase 8 작업 중 절대 손상되어서는 안 된다:

1. **기존 64개 테스트 전부 통과** — `python manage.py test reporting` 실패 금지
2. **내보내기 권한** — `ExportPermissionTests` (salesman=403, manager=200, admin=200) 유지
3. **Manager 쓰기 차단** — `ManagerRolePermissionTests` 유지
4. **AI 권한 게이트** — `AIPermissionTests` 유지
5. **비인증 URL 차단** — `AnonymousAccessTests` 유지
6. **`/reporting/*` 라우트 구조** — 기존 URL 변경 없음

---

## 11. 추가해야 할 테스트

### Phase 8에서 새로 작성할 테스트

```python
# 1. 파일 업로드 MIME 스푸핑 테스트
class FileUploadSecurityTests(TestCase):
    def test_jpg_extension_with_script_content_rejected(self): ...
    def test_pdf_extension_with_valid_pdf_accepted(self): ...

# 2. 디버그 엔드포인트 테스트
class DebugEndpointTests(TestCase):
    def test_debug_endpoint_requires_superuser(self): ...
    def test_debug_endpoint_blocked_for_admin_role(self): ...
    def test_debug_endpoint_blocked_for_anonymous(self): ...

# 3. 보안 헤더 테스트 (환경변수 모킹 필요)
class SecurityHeaderTests(TestCase):
    def test_x_content_type_options_header(self): ...
    def test_x_frame_options_deny_header(self): ...

# 4. 암호화 키 설정 테스트
class EncryptionKeyTests(TestCase):
    def test_email_encryption_key_from_env(self): ...
```

---

## 12. 구현 권장 순서

### Priority 1 (즉시, CRITICAL)

**`EMAIL_ENCRYPTION_KEY` 하드코딩 폴백 제거**

- `settings_production.py` 수정: 폴백 기본값 제거, 미설정 시 `RuntimeError` 발생
- Railway 환경변수 `EMAIL_ENCRYPTION_KEY` 설정 필수

### Priority 2 (높음)

**보안 헤더 추가**

- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'`
- `SECURE_PROXY_SSL_HEADER` + `SECURE_SSL_REDIRECT` 환경변수 제어
- `HSTS_SECONDS` 환경변수 제어 (초기 300초)

### Priority 3 (높음)

**`ALLOWED_HOSTS` 와일드카드 수정**

- Django는 `*.railway.app` 형식 미지원
- 실제 Railway 도메인 명시: `['yourapp.railway.app', 'localhost', '127.0.0.1']`
- 또는 환경변수 `RAILWAY_PUBLIC_DOMAIN`으로 동적 설정

### Priority 4 (중간)

**파일 업로드 MIME 타입 검증 추가**

- `validate_file_upload()` 에 파일 시그니처(매직 바이트) 검사 추가
- 이미지 파일 (`.jpg`, `.png`, `.gif`): `imghdr` 또는 매직 바이트 확인
- PDF (`.pdf`): `%PDF-` 시그니처 확인
- Office 파일 (`.docx`, `.xlsx`, `.pptx`): PK 시그니처(ZIP 기반) 확인
- `schedule_file_upload()`, `document_template_create()` 동일 적용

### Priority 5 (중간)

**디버그 엔드포인트 비활성화**

- `reporting/urls.py` 에서 `debug/user-company/` 경로 제거
- 또는 `DEBUG` 모드에서만 등록:
  ```python
  if settings.DEBUG:
      urlpatterns += [path('debug/user-company/', views.debug_user_company_info, ...)]
  ```

### Priority 6 (낮음)

**회귀 테스트 추가**

- 위 11항의 새 테스트 클래스 작성
- 64개 기존 테스트와 함께 CI/CD에서 전부 실행

---

## 13. 변경 예상 파일 목록

| 파일                                   | 변경 내용                                                                          |
| -------------------------------------- | ---------------------------------------------------------------------------------- |
| `sales_project/settings_production.py` | `EMAIL_ENCRYPTION_KEY` 폴백 제거, 보안 헤더 추가, `ALLOWED_HOSTS` 수정, HTTPS 설정 |
| `reporting/views.py`                   | `validate_file_upload()` MIME 검사 추가 (양쪽 중복 정의 모두)                      |
| `reporting/file_views.py`              | `schedule_file_upload()` MIME 검사 추가                                            |
| `reporting/urls.py`                    | `debug/user-company/` 경로 제거 또는 DEBUG 조건 처리                               |
| `reporting/tests.py`                   | `FileUploadSecurityTests`, `DebugEndpointTests`, `SecurityHeaderTests` 추가        |

### 변경하지 않을 파일

- `reporting/models.py` — 스키마 변경 없음
- `reporting/templates/**` — UI 변경 없음
- `ai_chat/views.py` — 권한 구조 이미 적절
- `reporting/migrations/**` — 모델 변경 없음

---

## 14. 필요한 환경변수 (신규)

| 환경변수                | 설명                             | 기본값          | 비고                           |
| ----------------------- | -------------------------------- | --------------- | ------------------------------ |
| `EMAIL_ENCRYPTION_KEY`  | 이메일 암호화 키 (Base64)        | **없음 (필수)** | 기존 Railway 변수 확인 후 설정 |
| `SECURE_SSL_REDIRECT`   | `true`이면 HTTP→HTTPS 리다이렉트 | `False`         | Railway 환경에서만 `true`      |
| `HSTS_SECONDS`          | HSTS 유효기간 (초)               | `0` (비활성)    | 초기 `300`, 검증 후 `31536000` |
| `RAILWAY_PUBLIC_DOMAIN` | Railway 배포 도메인              | 없음            | `ALLOWED_HOSTS` 동적 추가용    |

---

## 15. 검증 명령어

Phase 8 구현 후 반드시 실행해야 할 명령어:

```bash
# 1. Django 시스템 점검
python manage.py check

# 2. 배포 환경 보안 점검
python manage.py check --deploy

# 3. 전체 테스트 실행 (64개 + 신규 테스트 전부 통과 필수)
python manage.py test reporting

# 4. 마이그레이션 변경 없음 확인
python manage.py makemigrations --check --dry-run

# 5. 정적 파일 수집 (배포 전)
python manage.py collectstatic --noinput
```

### 예상 결과

```
System check identified no issues (0 silenced).
...
Ran 70+ tests in X.XXXs
OK
```

---

## 16. 구조적 참고 사항 (Phase 8 범위 외)

### `views.py` 중복 함수 정의 (주의)

`views.py` 약 14921행 부근에 다음 함수들이 **중복 정의**되어 있음:

- `role_required`
- `get_user_profile`
- `can_access_user_data`
- `validate_file_upload`
- `handle_file_uploads`
- `can_modify_user_data`

이는 코드 구조 문제이나, **Phase 8 범위 외** (리팩터링 금지).
`validate_file_upload()` MIME 검사를 추가할 때 **두 위치 모두** 수정해야 한다.
별도 Phase에서 중복 제거를 권장한다.

---

## 17. 알려진 제한 사항 및 리스크

| 항목                        | 내용                                                                                        |
| --------------------------- | ------------------------------------------------------------------------------------------- |
| MIME 검사 라이브러리        | `python-magic` 은 `libmagic` 시스템 패키지 필요 → Railway에서 설치 가능 여부 사전 확인 필요 |
| HSTS 장기 설정 위험         | HSTS를 1년으로 설정한 후 HTTP로 전환 시 브라우저 캐시로 접속 불가 → 단계적 증가 필수        |
| `EMAIL_ENCRYPTION_KEY` 교체 | 기존 암호화된 이메일 데이터가 있다면 키 변경 시 복호화 불가 → 키 순환 계획 필요             |
| 미디어 파일 직접 URL        | Railway Volume의 `/data/media/` 경로가 Nginx 또는 앱을 통해 서빙되는지 확인 필요            |

---

## 18. 다음 Phase 권장 작업

Phase 8 완료 후:

1. **Phase 9 — 성능 최적화**: N+1 쿼리 해결, `select_related`/`prefetch_related` 보강, 대시보드 응답 속도 개선
2. **Phase 10 — CI/CD**: GitHub Actions 또는 Railway 자동 빌드 파이프라인 구성, 테스트 자동 실행
3. **Phase 11 — 모니터링**: Sentry 에러 추적, 로그 구조화, Railway 알림 설정
4. **Phase 12 — `views.py` 분리**: 15,000줄 파일을 기능별 모듈로 분리 (`schedule_views.py`, `history_views.py` 등)

---

_PHASE_8_PLAN.md 작성 기준일: 현재 세션 기준_
_참고: 기존 AGENT_REPORT.md 및 PHASE_7_PLAN.md의 보안 권고사항 반영_
