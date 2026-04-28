import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError(
        'SECRET_KEY 환경변수가 설정되지 않았습니다. '
        '프로덕션 배포 전 반드시 설정하세요.'
    )
SECRET_KEY = _secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'web-production-5096.up.railway.app',  # Railway 명시적 도메인
    # *.railway.app 와일드카드는 Django ALLOWED_HOSTS에서 지원되지 않으므로 제거
]

# CSRF 설정 (초기화)
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-5096.up.railway.app',
    'http://web-production-5096.up.railway.app',  # HTTP도 추가
    'https://*.railway.app',
    'https://*.up.railway.app',
    'http://*.railway.app',
    'http://*.up.railway.app',
]

# Railway 환경 감지 — 명시적 도메인만 추가 (와일드카드 미지원)
if 'RENDER' in os.environ:
    ALLOWED_HOSTS.extend(['onrender.com'])
elif 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_STATIC_URL' in os.environ:
    # RAILWAY_PUBLIC_DOMAIN 환경변수가 있으면 동적으로 추가
    if 'RAILWAY_PUBLIC_DOMAIN' in os.environ:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain and railway_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(railway_domain)
            CSRF_TRUSTED_ORIGINS.extend([f'https://{railway_domain}', f'http://{railway_domain}'])

# CSRF 쿠키 설정
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # JavaScript에서 CSRF 토큰을 읽을 수 있도록 False로 설정
SESSION_COOKIE_SECURE = not DEBUG

# Phase 8: 보안 헤더 설정 ─────────────────────────────────────────────────────
# Railway는 HTTPS를 프록시에서 종료하므로 X-Forwarded-Proto 헤더를 신뢰합니다.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# 브라우저가 Content-Type을 변경하지 못하게 합니다. (MIME 스니핑 방지)
SECURE_CONTENT_TYPE_NOSNIFF = True
# Referer 헤더 정책
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
# SSL 리다이렉트: 환경변수로 제어 (Railway에서는 프록시가 처리하므로 기본 비활성화)
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
# HSTS: 환경변수 HSTS_SECONDS가 설정된 경우에만 활성화 (기본 비활성화)
_hsts_seconds = int(os.environ.get('HSTS_SECONDS', '0'))
if _hsts_seconds > 0:
    SECURE_HSTS_SECONDS = _hsts_seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # 프리로드는 사이트 운영자가 명시적으로 신청할 때만
# ──────────────────────────────────────────────────────────────────────────────

# CSRF 쿠키 SameSite 정책 — Lax는 Railway 환경에서 Cross-origin POST를 허용하는 안전한 기본값
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'reporting',
    'todos',
    'ai_chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Railway용 static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF 미들웨어 재활성화
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'reporting.middleware.TimezoneMiddleware',  # 한국 시간대 미들웨어
    'reporting.middleware.CompanyFilterMiddleware',  # 회사 필터링 미들웨어 추가
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'reporting.middleware.PerformanceMonitoringMiddleware',  # 임시로 비활성화
]

ROOT_URLCONF = 'sales_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'reporting.context_processors.manager_filter_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'sales_project.wsgi.application'

# Database
# Railway/Production PostgreSQL

if 'DATABASE_URL' in os.environ:
    # Use DATABASE_URL from environment (PostgreSQL plugin in Railway)
    DATABASES = {
        'default': dj_database_url.parse(
            os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Additional static files directories
STATICFILES_DIRS = [
    BASE_DIR / 'theme' / 'static',
    BASE_DIR / 'static',
] if (BASE_DIR / 'theme' / 'static').exists() else [BASE_DIR / 'static']

# Static files for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise configuration for better MIME type handling
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tailwind CSS settings
TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = [
    "127.0.0.1",
]

# Login/Logout redirect URLs
LOGIN_URL = '/reporting/login/'
LOGIN_REDIRECT_URL = '/reporting/dashboard/'
LOGOUT_REDIRECT_URL = '/reporting/login/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'reporting': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Railway Volume 파일 저장소 설정
# Mount Path: /data/media (250GB)
MEDIA_URL = '/media/'
MEDIA_ROOT = '/data/media'

# 기본 파일 저장소 (로컬 파일 시스템)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# 파일 정리 정책 설정
FILE_CLEANUP_SETTINGS = {
    # 영구 보관 파일 (삭제하지 않음)
    'PERMANENT_PATHS': [
        'document_templates/',    # 서류 템플릿
        'business_card_logos/',   # 서명 관리 회사 로고
    ],
    # 영구 보관 최대 파일 크기 (5MB 이하는 영구 보관)
    'PERMANENT_MAX_SIZE_MB': 5,
    # 임시 파일 보관 기간 (100일)
    'TEMP_FILE_RETENTION_DAYS': 100,
}

# 절대 URL 생성을 위한 도메인 설정
# RAILWAY_PUBLIC_DOMAIN 환경변수가 있으면 우선 사용, 없으면 하드코딩 fallback
if 'RAILWAY_ENVIRONMENT' in os.environ:
    _railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'web-production-5096.up.railway.app')
    SITE_DOMAIN = f'https://{_railway_domain}'
else:
    SITE_DOMAIN = 'http://127.0.0.1:8000'

# Gmail API 설정
GMAIL_CLIENT_ID = os.environ.get('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET')
GMAIL_REDIRECT_URI = os.environ.get('GMAIL_REDIRECT_URI')

# 이메일 비밀번호 암호화 키 (IMAP/SMTP)
# Railway 환경변수 EMAIL_ENCRYPTION_KEY 에 Fernet 키를 설정해야 합니다.
# 키 생성: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 환경변수가 없으면 IMAP/SMTP 암호화 기능은 비활성화되며 명확한 오류가 발생합니다.
_email_encryption_key = os.environ.get('EMAIL_ENCRYPTION_KEY')
if not _email_encryption_key:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        'EMAIL_ENCRYPTION_KEY 환경변수가 설정되지 않았습니다. '
        'IMAP/SMTP 이메일 비밀번호 암호화 기능이 비활성화됩니다. '
        '프로덕션에서는 반드시 Fernet 키를 생성하여 설정하세요. '
        '키 생성: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )
EMAIL_ENCRYPTION_KEY = _email_encryption_key.encode() if _email_encryption_key else None
