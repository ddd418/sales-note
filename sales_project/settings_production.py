import os
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-o9d76l+p#vrgs6r601a=w6pgzi56i-vik9z(g+1qi(k3-)1n+w')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.0.54',
    '192.168.0.1',
    'web-production-5096.up.railway.app',  # Railway 도메인 추가
    '*.railway.app',
    '*.up.railway.app',
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

# Railway 환경 감지
if 'RENDER' in os.environ:
    ALLOWED_HOSTS.extend(['*.onrender.com'])
elif 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_STATIC_URL' in os.environ:
    ALLOWED_HOSTS.extend(['*.railway.app', '*.up.railway.app'])
    # Railway에서 제공하는 실제 URL이 있다면 추가
    if 'RAILWAY_PUBLIC_DOMAIN' in os.environ:
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        ALLOWED_HOSTS.append(railway_domain)
        CSRF_TRUSTED_ORIGINS.extend([f'https://{railway_domain}', f'http://{railway_domain}'])

# CSRF 쿠키 설정
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG

# Railway 환경에서 CSRF 더 관대하게 설정 (임시 디버깅용)
if DEBUG or 'RAILWAY_ENVIRONMENT' in os.environ:
    # 임시로 CSRF 검증을 느슨하게 설정
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
    'reporting',
    'tailwind',
    'theme',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Railway용 static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF 미들웨어 재활성화
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
            ],
            # 프로덕션에서도 템플릿 캐시 비활성화 (템플릿 오류 디버깅용)
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'sales_project.wsgi.application'

# Database
# Railway PostgreSQL with external host (to avoid internal DNS issues)
if 'RAILWAY_ENVIRONMENT' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'railway',
            'USER': 'postgres', 
            'PASSWORD': 'WbFqzWRREczQXtbpAVTfASQhZgdHtAGL',
            'HOST': 'caboose.proxy.rlwy.net',
            'PORT': '51196',
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }
elif 'DATABASE_URL' in os.environ:
    # Fallback to DATABASE_URL if available
    database_url = os.environ.get('DATABASE_URL')
    # Replace internal host with external host if needed
    if 'postgres.railway.internal' in database_url:
        database_url = database_url.replace(
            'postgres.railway.internal:5432',
            'caboose.proxy.rlwy.net:51196'
        )
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
else:
    # Local SQLite
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
] if (BASE_DIR / 'theme' / 'static').exists() else []

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
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

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

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
