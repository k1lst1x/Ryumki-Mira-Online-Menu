"""
Django settings for menu project.
Версия фреймворка ожидается: Django 5.2.x
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# =========================
# БАЗОВОЕ
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

# На проде ключ только из окружения
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-u98(_p&s38sb8g+ovt34kdy$9k!j$t5ip2npeu14jc#168@806",
)

DEBUG = os.getenv("DJANGO_DEBUG", "true").strip().lower() == "true"

ALLOWED_HOSTS = [h.strip() for h in os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",") if h.strip()]

# =========================
# ПРИЛОЖЕНИЯ
# =========================
INSTALLED_APPS = [
    # встроенные
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # сторонние
    "rest_framework",

    # кастомные
    "menuapp",
    "rosetta",
]

# =========================
# MIDDLEWARE
# =========================
# AgeGate должен видеть куки и язык → ставим после Session и Locale,
# но до Common, чтобы как можно раньше отсекать небезопасные запросы.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "menuapp.middleware.AgeGate21Middleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =========================
# URLS & WSGI
# =========================
ROOT_URLCONF = "menu.urls"
WSGI_APPLICATION = "menu.wsgi.application"
LOGIN_URL = "/admin-django/login/"

# =========================
# ШАБЛОНЫ
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # глобальные шаблоны
        "APP_DIRS": True,                   # шаблоны из app/templates
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",  # i18n в шаблонах

                # твои процессоры (держи их чистыми, без дублей LANG)
                "menuapp.context_processors.cart_processor",
                "menuapp.context_processors.nav_categories",
                "menuapp.context_processors.brand_contacts",
                "menuapp.context_processors.i18n_context",

            ],
        },
    },
]

# =========================
# БАЗА ДАННЫХ
# =========================
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "menu_db"),
        "USER": os.getenv("POSTGRES_USER", "menu_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "menu_pass"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "600")),  # keep-alive
        "OPTIONS": {},
    }
}

# =========================
# ПАРОЛИ
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =========================
# ЛОКАЛИ / I18N
# =========================
LANGUAGE_CODE = "ru"

LANGUAGES = (
    ("ru", "Русский"),
    ("kk", "Қазақша"),
    ("en", "English"),
)

USE_I18N = True
TIME_ZONE = "Asia/Almaty"
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Можно явно зафиксировать имя и путь куки языка (не обязательно):
LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_PATH = "/"

# =========================
# СТАТИКА / МЕДИА
# =========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]     # dev
STATIC_ROOT = BASE_DIR / "staticfiles"       # collectstatic для прод

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =========================
# DJANGO REST FRAMEWORK
# =========================
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# =========================
# АУТЕНТИФИКАЦИЯ
# =========================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# =========================
# EMAIL (dev)
# =========================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =========================
# БРЕНД-КОНТАКТЫ (navbar)
# =========================
BRAND_CONTACTS = {
    "whatsapp_phone": "+77024292219",
    "instagram_url": "https://www.instagram.com/ryumki_mira/",
    "dgis_url": "https://2gis.kz/almaty/geo/70000001104426373",
}

# =========================
# БЕЗОПАСНОСТЬ (включай через env на проде)
# =========================
# Пример: DJANGO_CSRF_TRUSTED_ORIGINS="https://example.com,https://www.example.com"
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =========================
# ПРОЧЕЕ
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
