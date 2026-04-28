# PHASE 9 PLAN — 프로덕션 하드닝 및 배포 준비

> **목표**: 코드 변경을 최소화하면서 Railway 프로덕션 환경의 보안 설정을 안전하게 완성한다.
>
> **범위 제한**:
>
> - 비즈니스 기능 추가 금지
> - UI/UX 변경 금지
> - 관련 없는 리팩터링 금지
> - Phase 8까지 통과한 75개 테스트 전부 유지 필수
> - 코드 변경은 `settings_production.py`와 `imap_utils.py`로 국한

---

## 1. 현재 프로덕션 보안 설정 현황

### `settings_production.py` 전체 보안 설정 요약

| 설정 항목                     | 현재 값 / 상태                                       | 평가             |
| ----------------------------- | ---------------------------------------------------- | ---------------- |
| `SECRET_KEY`                  | 환경변수 필수 — 없으면 `RuntimeError`                | ✅               |
| `DEBUG`                       | 환경변수 `DEBUG=true`로만 활성화 (기본 `False`)      | ✅               |
| `ALLOWED_HOSTS`               | 명시적 Railway 도메인 + 무효 와일드카드 혼재         | ⚠️ 정리 필요     |
| `CSRF_COOKIE_SECURE`          | `not DEBUG` (프로덕션에서 True)                      | ✅               |
| `CSRF_COOKIE_HTTPONLY`        | `False` (JavaScript CSRF 토큰 접근 허용)             | ✅ (의도적)      |
| `SESSION_COOKIE_SECURE`       | `not DEBUG` (프로덕션에서 True)                      | ✅               |
| `SECURE_PROXY_SSL_HEADER`     | `('HTTP_X_FORWARDED_PROTO', 'https')` 설정됨         | ✅               |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True`                                               | ✅               |
| `SECURE_REFERRER_POLICY`      | `strict-origin-when-cross-origin`                    | ✅               |
| `SECURE_SSL_REDIRECT`         | 환경변수 `SECURE_SSL_REDIRECT`로 제어 (기본 `False`) | ✅               |
| `SECURE_HSTS_SECONDS`         | **미설정** (기본 비활성화)                           | ⚠️ 활성화 권장   |
| `SECURE_HSTS_PRELOAD`         | **미설정**                                           | ✅ (의도적)      |
| `EMAIL_ENCRYPTION_KEY`        | 환경변수 없으면 하드코딩 Base64 fallback + 경고 로그 | 🔴 제거 필요     |
| `MEDIA_ROOT`                  | `/data/media` (Railway Volume)                       | ✅               |
| `DEFAULT_FILE_STORAGE`        | `FileSystemStorage`                                  | ✅               |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | **프로덕션 미설정** (로컬에는 25MB)                  | ⚠️ 추가 권장     |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | **프로덕션 미설정** (로컬에는 25MB)                  | ⚠️ 추가 권장     |
| `BACKUP_API_TOKEN`            | 환경변수 (`backup_api.py`에서 참조)                  | ✅               |
| `SITE_DOMAIN`                 | 하드코딩 `web-production-5096.up.railway.app`        | ⚠️ 환경변수 권장 |

---

## 2. ALLOWED_HOSTS 현재 동작 및 권장 수정

### 현재 코드 (`settings_production.py:20–48`)

```python
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.0.54',
    '192.168.0.1',
    'web-production-5096.up.railway.app',  # 명시적 도메인 ← 이것만 동작
    '*.railway.app',                       # Django는 ALLOWED_HOSTS 와일드카드 미지원 → 무시됨
    '*.up.railway.app',                    # 무시됨
]

# Railway 환경 감지 블록
if 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_STATIC_URL' in os.environ:
    ALLOWED_HOSTS.extend(['*.railway.app', '*.up.railway.app'])  # 역시 무시됨
    if 'RAILWAY_PUBLIC_DOMAIN' in os.environ:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        ALLOWED_HOSTS.append(railway_domain)  # ← 이것만 효과적
```

### 문제

Django `ALLOWED_HOSTS`는 `*.railway.app` 형식 와일드카드를 지원하지 않는다.
현재 `'web-production-5096.up.railway.app'`가 명시적으로 하드코딩되어 있어
Railway 배포가 정상 동작하고 있지만, 와일드카드 항목은 효과가 없어 코드를 오해시킨다.

### 권장 수정

```python
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'web-production-5096.up.railway.app',  # 실제 Railway 도메인 (명시적)
]

# Railway 환경에서 동적 도메인 추가
if 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_STATIC_URL' in os.environ:
    if 'RAILWAY_PUBLIC_DOMAIN' in os.environ:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(railway_domain)
```

- `192.168.0.54`, `192.168.0.1` 제거: 프로덕션 서버에서 불필요한 LAN 주소
  (단, 사내 개발자가 LAN으로 접근하는 경우라면 유지)
- `*.railway.app` 와일드카드 전부 제거
- `CSRF_TRUSTED_ORIGINS`의 와일드카드는 Django 4.0+에서 지원하므로 유지

### 위험도

- 현재는 `'web-production-5096.up.railway.app'` 명시 항목이 있어 **실제 장애 없음**
- 와일드카드 제거 자체는 무결하고 코드 명확성만 향상

---

## 3. EMAIL_ENCRYPTION_KEY 현재 동작 및 권장 수정

### 현재 코드 (`settings_production.py` 마지막 블록)

```python
_email_encryption_key = os.environ.get('EMAIL_ENCRYPTION_KEY')
if not _email_encryption_key:
    import logging as _logging
    _logging.getLogger(__name__).warning('EMAIL_ENCRYPTION_KEY 환경변수가 설정되지 않았습니다...')
EMAIL_ENCRYPTION_KEY = (_email_encryption_key or 'YXNkZmFzZGZhc2RmYXNkZmFzZGZhc2RmYXNkZmFzZGY=').encode()
```

### 현재 `imap_utils.py` 동작 (`EmailEncryption.get_cipher()`)

```python
key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', Fernet.generate_key())
```

- `settings.EMAIL_ENCRYPTION_KEY`가 `None`이면 → 매번 새 랜덤 키 생성 → 저장된 암호 복호화 불가
- `settings.EMAIL_ENCRYPTION_KEY`가 하드코딩 fallback bytes이면 → 복호화는 되지만 보안 취약

### 핵심 위험

| 시나리오                                 | 결과                                                           |
| ---------------------------------------- | -------------------------------------------------------------- |
| 환경변수 있음                            | ✅ 정상 암호화/복호화                                          |
| 환경변수 없음, 기존 배포 (fallback 동일) | 복호화 가능하지만 키 노출됨 🔴                                 |
| 환경변수 없음, `settings.py` 로컬 (None) | `imap_utils.py`가 매번 랜덤 키 생성 → 저장 암호 복호화 불가 🔴 |
| 키 변경 후 배포                          | 기존 저장된 암호 모두 복호화 불가 ⚠️                           |

### 권장 수정 — 단계적 접근

#### 단계 1: 즉시 가능 — Railway에 환경변수 설정

```bash
# Railway에서 Fernet 키 생성
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Railway 대시보드 → Variables → EMAIL_ENCRYPTION_KEY 추가
```

> ⚠️ **주의**: 기존 배포에서 하드코딩 fallback 키로 암호화된 비밀번호가 DB에 있다면,
> 키를 변경하기 전에 모든 IMAP/SMTP 비밀번호를 재입력해야 한다.

#### 단계 2: 코드 정리 (환경변수 설정 후)

```python
# settings_production.py — 하드코딩 fallback 제거
_email_encryption_key = os.environ.get('EMAIL_ENCRYPTION_KEY')
if not _email_encryption_key:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        'EMAIL_ENCRYPTION_KEY 환경변수가 설정되지 않았습니다. '
        'IMAP/SMTP 이메일 비밀번호 기능이 비활성화됩니다.'
    )
EMAIL_ENCRYPTION_KEY = _email_encryption_key.encode() if _email_encryption_key else None
```

#### 단계 3: `imap_utils.py` 방어 코드 강화

```python
@staticmethod
def get_cipher():
    key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', None)
    if not key:
        raise ValueError("EMAIL_ENCRYPTION_KEY가 설정되지 않아 이메일 암호화를 사용할 수 없습니다.")
    return Fernet(key)
```

---

## 4. HSTS 단계적 활성화 계획

### 전제 조건 (이미 충족)

- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` ✅
- `SECURE_SSL_REDIRECT`는 환경변수로 제어 ✅
- `HSTS_SECONDS` 환경변수가 0이면 HSTS 미설정 ✅
- Railway에서 HTTPS 종료는 프록시가 담당 (Django → HTTP, 브라우저 → HTTPS) ✅

### 단계별 활성화

#### 1단계 — 파일럿 (5분, 안전 검증)

Railway 환경변수 추가:

```
HSTS_SECONDS=300
```

- 브라우저가 5분 동안만 HTTPS를 기억
- 문제 발생 시 즉시 제거 가능
- 검증: 브라우저 Network 탭에서 `Strict-Transport-Security: max-age=300; includeSubDomains` 확인

#### 2단계 — 단기 (1주일, 안정 확인)

```
HSTS_SECONDS=86400
```

- 1일 (86400초)
- 운영 안정성 확인 후 진행

#### 3단계 — 장기 (검증 후 1년)

```
HSTS_SECONDS=31536000
```

- 1년 (31536000초)
- `SECURE_HSTS_PRELOAD = False` 유지 — 프리로드 등록은 별도 신청 절차 필요

### 주의사항

- `SECURE_HSTS_PRELOAD = True` 설정 + hstspreload.org 등록 전까지 Preload 금지
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`는 현재 코드에 이미 설정됨
- HSTS 활성화 후 Railway 도메인에서 HTTP 접근 시도 → 브라우저가 자동 HTTPS 전환

---

## 5. Railway 환경변수 전체 목록

### 필수 (프로덕션 운영 불가 시 오류 발생)

| 환경변수       | 설명                | 현재 상태                  | 예시                             |
| -------------- | ------------------- | -------------------------- | -------------------------------- |
| `SECRET_KEY`   | Django 시크릿 키    | 필수 (없으면 RuntimeError) | `django-...50자 이상 랜덤...`    |
| `DATABASE_URL` | PostgreSQL 연결 URL | Railway 플러그인 자동 설정 | `postgresql://user:pass@host/db` |

### 강력 권장 (기능 비활성화 위험)

| 환경변수               | 설명                                | 미설정 시 동작            | 예시                           |
| ---------------------- | ----------------------------------- | ------------------------- | ------------------------------ |
| `EMAIL_ENCRYPTION_KEY` | IMAP/SMTP 비밀번호 Fernet 암호화 키 | 하드코딩 fallback 사용 🔴 | `Fernet.generate_key()` 출력값 |

### 보안 강화용 (선택, 환경변수로 제어)

| 환경변수                | 설명                         | 기본값              | 권장값                                          |
| ----------------------- | ---------------------------- | ------------------- | ----------------------------------------------- |
| `HSTS_SECONDS`          | HSTS 유효기간(초)            | `0` (비활성화)      | `300` → `86400` → `31536000`                    |
| `SECURE_SSL_REDIRECT`   | HTTP → HTTPS 강제 리다이렉트 | `False`             | `true` (Railway는 프록시 HTTPS 종료이므로 선택) |
| `RAILWAY_PUBLIC_DOMAIN` | Railway 배포 도메인          | Railway가 자동 설정 | `web-production-5096.up.railway.app`            |

### 백업 / 기능 연동용

| 환경변수              | 설명                       | 미설정 시 동작                      |
| --------------------- | -------------------------- | ----------------------------------- |
| `BACKUP_API_TOKEN`    | 백업 API Bearer Token      | 백업 API 500 오류                   |
| `GMAIL_CLIENT_ID`     | Gmail OAuth2 클라이언트 ID | Gmail 연동 비활성화                 |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth2 시크릿        | Gmail 연동 비활성화                 |
| `GMAIL_REDIRECT_URI`  | Gmail OAuth 콜백 URL       | 기본값 `your-domain.com` 사용       |
| `OPENAI_API_KEY`      | AI 분석 기능               | AI 분석 비활성화                    |
| `REDIS_URL`           | Celery 브로커              | `redis://localhost:6379/0` fallback |

### 선택 (배포 불필요)

| 환경변수 | 설명                                                |
| -------- | --------------------------------------------------- |
| `DEBUG`  | `true` 설정 시 디버그 모드 (프로덕션에서 절대 금지) |

---

## 6. 로컬 개발 동작

### 환경 감지 로직 (`settings.py`)

```python
if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("DATABASE_URL"):
    from sales_project.settings_production import *
else:
    # 로컬 설정 인라인 적용
    SECRET_KEY = "django-insecure-..."
    DEBUG = True
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", ...]
```

### 로컬 개발 특이사항

- `SECRET_KEY`: 하드코딩 insecure key 사용 — 로컬 전용이므로 허용
- `DEBUG = True`: CSRF_COOKIE_SECURE/SESSION_COOKIE_SECURE가 False → HTTPS 불필요
- `EMAIL_ENCRYPTION_KEY`: `None` → `imap_utils.py`가 랜덤 키 생성 → **IMAP 비밀번호 재입력 불가**
- `DATA_UPLOAD_MAX_MEMORY_SIZE`: 25MB 설정됨
- `MEDIA_ROOT`: `BASE_DIR / "media"` (로컬 디렉터리)
- `.env` 파일 지원: `python-dotenv`로 자동 로드 (Railway/DATABASE_URL 없을 때만)

### 로컬에서 프로덕션 설정 테스트

```bash
# .env 파일에 추가
DATABASE_URL=sqlite:///./db.sqlite3  # 로컬 SQLite를 프로덕션 경로로 사용
SECRET_KEY=로컬테스트용-시크릿키
EMAIL_ENCRYPTION_KEY=테스트용-Fernet-키

# 실행
conda run -n sales-env python manage.py runserver
```

---

## 7. 환경변수 미설정 시 위험

| 환경변수                | 미설정 시 동작                                        | 위험도                         |
| ----------------------- | ----------------------------------------------------- | ------------------------------ |
| `SECRET_KEY`            | `RuntimeError` — 앱 시작 불가                         | 🔴 Critical                    |
| `DATABASE_URL`          | SQLite fallback — 데이터 유실 위험                    | 🟠 High                        |
| `EMAIL_ENCRYPTION_KEY`  | 하드코딩 Base64 키 사용 — 암호화 무력화               | 🟡 Medium                      |
| `BACKUP_API_TOKEN`      | 백업 API 500 오류, GitHub Actions 실패                | 🟡 Medium                      |
| `HSTS_SECONDS`          | HSTS 비활성화 — HTTPS 강제 없음                       | 🟢 Low                         |
| `SECURE_SSL_REDIRECT`   | HTTP → HTTPS 리다이렉트 없음                          | 🟢 Low (Railway 프록시가 처리) |
| `RAILWAY_PUBLIC_DOMAIN` | `ALLOWED_HOSTS` 동적 추가 없음 (명시적 도메인은 정상) | 🟢 Low                         |

---

## 8. 권장 코드 변경 사항

### 변경 1 — `settings_production.py`: ALLOWED_HOSTS 정리

```python
# 변경 전
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.0.54',
    '192.168.0.1',
    'web-production-5096.up.railway.app',
    '*.railway.app',         # 무효 와일드카드
    '*.up.railway.app',      # 무효 와일드카드
]

# 변경 후
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'web-production-5096.up.railway.app',
]
# (Railway 환경 감지 블록에서 RAILWAY_PUBLIC_DOMAIN 추가는 유지)
```

**영향 범위**: ALLOWED_HOSTS 와일드카드는 Django가 이미 무시 중 → 제거해도 동작 변화 없음

---

### 변경 2 — `settings_production.py`: EMAIL_ENCRYPTION_KEY fallback 제거

```python
# 변경 전
EMAIL_ENCRYPTION_KEY = (_email_encryption_key or 'YXNkZmFzZGZhc2RmYXNkZmFzZGZhc2RmYXNkZmFzZGY=').encode()

# 변경 후
EMAIL_ENCRYPTION_KEY = _email_encryption_key.encode() if _email_encryption_key else None
```

**전제 조건**: Railway 환경변수 `EMAIL_ENCRYPTION_KEY` 설정 완료 후 적용

**영향 범위**: `imap_utils.py`의 `get_cipher()` 메서드가 `None` 처리 필요 → 변경 3 필요

---

### 변경 3 — `imap_utils.py`: get_cipher() 방어 코드 추가

```python
# 변경 전
@staticmethod
def get_cipher():
    key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', Fernet.generate_key())
    return Fernet(key)

# 변경 후
@staticmethod
def get_cipher():
    key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', None)
    if not key:
        raise ValueError("EMAIL_ENCRYPTION_KEY 설정이 없어 이메일 암호화 기능을 사용할 수 없습니다.")
    return Fernet(key)
```

**영향 범위**: IMAP/SMTP 비밀번호 저장/조회 시 환경변수 없으면 명확한 오류 발생 (무음 실패 방지)

---

### 변경 4 — `settings_production.py`: 파일 업로드 크기 제한 추가

```python
# 프로덕션에도 파일 업로드 크기 제한 추가 (로컬과 일치)
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400   # 25MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400   # 25MB
```

**영향 범위**: 로컬 설정과 동일하게 맞추는 것 — 동작 변화 없음

---

### 변경 5 — `settings_production.py`: SITE_DOMAIN 환경변수 우선

```python
# 변경 전
if 'RAILWAY_ENVIRONMENT' in os.environ:
    SITE_DOMAIN = 'https://web-production-5096.up.railway.app'
else:
    SITE_DOMAIN = 'http://127.0.0.1:8000'

# 변경 후
if 'RAILWAY_ENVIRONMENT' in os.environ:
    _railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-5096.up.railway.app')
    SITE_DOMAIN = f'https://{_railway_domain}'
else:
    SITE_DOMAIN = 'http://127.0.0.1:8000'
```

---

## 9. 권장 추가 테스트

### 기존 테스트 유지 전제 (75/75 통과)

아래 테스트는 `reporting/tests.py` 파일에 새 클래스를 추가한다:

```python
class ProductionSettingsTests(TestCase):
    """settings_production.py 보안 설정 검증 테스트"""

    def test_allowed_hosts_no_wildcards(self):
        """ALLOWED_HOSTS에 Django 미지원 와일드카드 없음 확인"""
        from django.conf import settings
        for host in settings.ALLOWED_HOSTS:
            self.assertFalse(
                host.startswith('*.'),
                f"ALLOWED_HOSTS에 미지원 와일드카드 발견: {host}"
            )

    def test_email_encryption_key_format(self):
        """EMAIL_ENCRYPTION_KEY가 None이거나 bytes 형식인지 확인"""
        from django.conf import settings
        key = getattr(settings, 'EMAIL_ENCRYPTION_KEY', None)
        if key is not None:
            self.assertIsInstance(key, bytes, "EMAIL_ENCRYPTION_KEY는 bytes여야 합니다")
            # Fernet 키는 44바이트 base64 URL-safe
            self.assertGreaterEqual(len(key), 32, "EMAIL_ENCRYPTION_KEY가 너무 짧습니다")

    def test_hsts_seconds_non_negative(self):
        """HSTS_SECONDS 환경변수가 음수가 아닌지 확인"""
        import os
        val = int(os.environ.get('HSTS_SECONDS', '0'))
        self.assertGreaterEqual(val, 0, "HSTS_SECONDS는 0 이상이어야 합니다")

    def test_secure_nosniff_enabled(self):
        """MIME 스니핑 방지 설정 확인"""
        from django.conf import settings as django_settings
        # 로컬 개발 환경에서는 이 설정이 없을 수 있음
        if not django_settings.DEBUG:
            self.assertTrue(
                getattr(django_settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
                "프로덕션에서 SECURE_CONTENT_TYPE_NOSNIFF가 활성화되어야 합니다"
            )

class EmailEncryptionSafetyTests(TestCase):
    """IMAP/SMTP 암호화 키 안전성 테스트"""

    def test_get_cipher_without_key_raises(self):
        """EMAIL_ENCRYPTION_KEY=None일 때 get_cipher()가 ValueError 발생 확인"""
        from unittest.mock import patch
        from reporting.imap_utils import EmailEncryption

        with patch('django.conf.settings.EMAIL_ENCRYPTION_KEY', None):
            with self.assertRaises((ValueError, TypeError)):
                EmailEncryption.get_cipher()
```

---

## 10. 배포 체크리스트

### Railway 환경변수 확인

- [ ] `SECRET_KEY` 설정 여부 확인 (50자 이상 랜덤)
- [ ] `DATABASE_URL` 설정 여부 확인 (Railway PostgreSQL 플러그인)
- [ ] `EMAIL_ENCRYPTION_KEY` 유효한 Fernet 키로 설정
  - 키 생성: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
  - 기존 IMAP/SMTP 비밀번호 재입력 여부 확인 (키 변경 시)
- [ ] `BACKUP_API_TOKEN` 설정 (백업 API 사용 시)
- [ ] `GMAIL_REDIRECT_URI` 실제 도메인으로 업데이트 (`your-domain.com` 제거)

### HSTS 단계적 활성화

- [ ] 1단계: `HSTS_SECONDS=300` 설정
- [ ] 검증: 브라우저 개발자 도구 → Network → Strict-Transport-Security 헤더 확인
- [ ] 48시간 후 문제 없으면 `HSTS_SECONDS=86400` 업데이트
- [ ] 1주일 안정 운영 후 `HSTS_SECONDS=31536000` 업데이트

### 코드 변경 체크리스트

- [ ] `ALLOWED_HOSTS` 와일드카드 항목 제거 확인
- [ ] `EMAIL_ENCRYPTION_KEY` fallback 제거 후 Railway 환경변수 설정 완료 확인
- [ ] `imap_utils.py` `get_cipher()` 방어 코드 적용 확인
- [ ] `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` 프로덕션 설정 추가 확인
- [ ] `SITE_DOMAIN` 환경변수 우선 처리 확인

### 코드 검증

- [ ] `python manage.py check` → 0 issues
- [ ] `python manage.py makemigrations --check --dry-run` → No changes detected
- [ ] `python manage.py test reporting` → 75/75 (+ 신규 테스트) 통과

### URL 확인

- [ ] `https://web-production-5096.up.railway.app/` → 302 (로그인 리다이렉트)
- [ ] `https://web-production-5096.up.railway.app/reporting/login/` → 200
- [ ] `https://web-production-5096.up.railway.app/reporting/debug/user-company/` → 404
- [ ] Response Headers: `Strict-Transport-Security: max-age=300...` (HSTS 활성화 후)
- [ ] Response Headers: `X-Content-Type-Options: nosniff`
- [ ] Response Headers: `Referrer-Policy: strict-origin-when-cross-origin`

---

## 11. 롤백 체크리스트

### HSTS 롤백 (가장 중요)

- [ ] Railway 환경변수 `HSTS_SECONDS=0` 또는 삭제
- [ ] **주의**: `HSTS_SECONDS=31536000`으로 설정 후에는 브라우저 캐시로 인해 즉시 롤백 불가
  - 사용자 브라우저마다 캐시된 기간 동안 HTTPS 강제 유지
  - 이 때문에 반드시 `300`(5분)부터 시작해야 함

### EMAIL_ENCRYPTION_KEY 변경 롤백

- [ ] 이전 키 값 보관 필수 (Railway Variables 히스토리 확인)
- [ ] 새 키로 변경 후 기존 암호 복호화 불가 → 사용자 IMAP/SMTP 비밀번호 재입력 필요
- [ ] 롤백: 이전 키 값으로 환경변수 복원 → 기존 암호 다시 복호화 가능

### ALLOWED_HOSTS 롤백

- [ ] `settings_production.py`에서 명시적 도메인 복원
- [ ] `git revert` 또는 해당 줄 수동 복구
- [ ] `git push` 후 Railway 자동 재배포

---

## 12. 변경될 파일 목록

| 파일                                   | 변경 내용                                                                                                  | 중요도 |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------ |
| `sales_project/settings_production.py` | ALLOWED_HOSTS 와일드카드 제거, EMAIL_ENCRYPTION_KEY fallback 제거, 파일 업로드 크기 추가, SITE_DOMAIN 수정 | ⭐⭐⭐ |
| `reporting/imap_utils.py`              | `get_cipher()` None 방어 코드 추가                                                                         | ⭐⭐   |
| `reporting/tests.py`                   | `ProductionSettingsTests`, `EmailEncryptionSafetyTests` 추가                                               | ⭐⭐   |

**변경하지 않는 파일**:

- `reporting/views.py` — Phase 8에서 완료
- `reporting/urls.py` — Phase 8에서 완료
- `reporting/file_views.py` — Phase 8에서 완료
- `sales_project/settings.py` — 로컬 설정, 변경 불필요
- `railway.toml`, `nixpacks.toml` — 배포 설정 이상 없음

---

## 13. 검증 명령어

```bash
# 1. Django 기본 검사
conda run -n sales-env python manage.py check

# 2. 마이그레이션 확인
conda run -n sales-env python manage.py makemigrations --check --dry-run

# 3. 전체 테스트 실행
conda run -n sales-env python manage.py test reporting --verbosity=2

# 4. Static files 수집 (프로덕션 배포 전)
conda run -n sales-env python manage.py collectstatic --noinput

# 5. URL smoke test (개발 서버)
# /reporting/login/ → 200
# /reporting/debug/user-company/ → 404
# / → 302

# 6. 보안 헤더 확인 (프로덕션 배포 후)
curl -I https://web-production-5096.up.railway.app/reporting/login/
# X-Content-Type-Options: nosniff 확인
# Strict-Transport-Security: max-age=300... (HSTS 설정 후)
# Referrer-Policy: strict-origin-when-cross-origin 확인
```

---

## 실행 순서

```
1. Railway 환경변수 설정 (코드 변경 전)
   → EMAIL_ENCRYPTION_KEY 생성 및 입력
   → HSTS_SECONDS=300 추가
   → BACKUP_API_TOKEN, GMAIL_REDIRECT_URI 확인

2. settings_production.py 코드 변경
   → ALLOWED_HOSTS 와일드카드 제거
   → EMAIL_ENCRYPTION_KEY fallback 제거
   → 파일 업로드 크기 추가
   → SITE_DOMAIN 수정

3. imap_utils.py get_cipher() 방어 코드 추가

4. tests.py 새 테스트 클래스 추가

5. 검증 명령어 전체 실행

6. git commit + push → Railway 자동 재배포

7. 프로덕션 헤더 확인 (curl -I)

8. HSTS 단계적 증가 (300 → 86400 → 31536000)

9. AGENT_REPORT.md 업데이트
```

---

## 위험 평가

| 위험                                                | 확률                    | 영향                  | 대응                                   |
| --------------------------------------------------- | ----------------------- | --------------------- | -------------------------------------- |
| EMAIL_ENCRYPTION_KEY 변경으로 기존 암호 복호화 불가 | 높음 (키 변경 시)       | IMAP/SMTP 재인증 필요 | 키 변경 전 사용자 공지, 재입력 안내    |
| HSTS 장기 설정 후 HTTP 전환 불가                    | 낮음 (300초부터 시작)   | 최대 5분 HTTPS 강제   | 5분 기다리면 해소                      |
| ALLOWED_HOSTS 정리로 접속 불가                      | 매우 낮음               | 403 Bad Request       | 명시적 도메인이 이미 존재하므로 무영향 |
| imap_utils.py ValueError로 기존 IMAP 기능 중단      | 환경변수 미설정 시 발생 | IMAP 조회 실패        | 환경변수 설정 후 코드 적용             |
