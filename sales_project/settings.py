import os

if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("DATABASE_URL"):
    from sales_project.settings_production import *
else:
    from pathlib import Path
    from django.contrib.messages import constants as messages
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = "django-insecure-o9d76l+p#vrgs6r601a=w6pgzi56i-vik9z(g+1qi(k3-)1n+w"
    DEBUG = True
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "192.168.0.54", "192.168.0.1", "*"]
    
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "reporting",
        "tailwind",
        "theme",
    ]
    
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "reporting.middleware.CompanyFilterMiddleware",
        "reporting.middleware.PerformanceMonitoringMiddleware",
    ]
    
    ROOT_URLCONF = "sales_project.urls"
    TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
    WSGI_APPLICATION = "sales_project.wsgi.application"
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
    AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}, {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}, {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}]
    
    LANGUAGE_CODE = "ko-kr"
    TIME_ZONE = "Asia/Seoul"
    USE_I18N = True
    USE_TZ = True
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "staticfiles"
    STATICFILES_DIRS = [BASE_DIR / "theme" / "static"]
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    LOGIN_URL = "reporting:login"
    LOGIN_REDIRECT_URL = "reporting:dashboard"
    LOGOUT_REDIRECT_URL = "reporting:login"
    MESSAGE_TAGS = {messages.DEBUG: "debug", messages.INFO: "info", messages.SUCCESS: "success", messages.WARNING: "warning", messages.ERROR: "error"}
    LOGGING = {"version": 1, "disable_existing_loggers": False, "formatters": {"verbose": {"format": "[{levelname}] {asctime} {name} {process:d} {thread:d} {message}", "style": "{"}}, "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}}, "loggers": {"reporting": {"handlers": ["console"], "level": "INFO", "propagate": False}, "django": {"handlers": ["console"], "level": "INFO", "propagate": False}}}
    TAILWIND_APP_NAME = "theme"
    INTERNAL_IPS = ["127.0.0.1"]
    NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = "Lax"
    CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000", "http://192.168.0.54:8000", "http://192.168.1.*:8000", "http://192.168.0.*:8000", "https://web-production-5096.up.railway.app", "https://*.railway.app", "https://*.up.railway.app"]
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_AGE = 86400
    SESSION_SAVE_EVERY_REQUEST = True
