"""
Django settings for BulkGame (Facebook Bulk Post Remover SaaS).
"""

from pathlib import Path

import environ
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Subpath on VPS (e.g. /bulkgame). Nginx should strip this prefix when proxying; Django uses it for URL generation.
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME", default="").strip() or None
_subpath = (FORCE_SCRIPT_NAME or "").rstrip("/")
if _subpath:
    STATIC_URL = f"{_subpath}/static/"
    MEDIA_URL = f"{_subpath}/media/"
else:
    STATIC_URL = "static/"
    MEDIA_URL = "media/"

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts.apps.AccountsConfig",
    "billing",
    "tools",
    "channels",
    "fb_remover",
    "adminpanel",
    "auditlog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.SoftDeletedUserMiddleware",
]

ROOT_URLCONF = "bulkdel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.navigation",
            ],
        },
    },
]

WSGI_APPLICATION = "bulkdel.wsgi.application"

if env("DATABASE_URL", default=None):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# STATIC_URL / MEDIA_URL are set above from FORCE_SCRIPT_NAME (do not overwrite here).
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.CustomUser"

LOGIN_URL = reverse_lazy("accounts:login")
LOGIN_REDIRECT_URL = reverse_lazy("core:dashboard")
LOGOUT_REDIRECT_URL = reverse_lazy("core:home")

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60 * 30

# Facebook OAuth (Phase 2+)
FACEBOOK_APP_ID = env("FACEBOOK_APP_ID", default="")
FACEBOOK_APP_SECRET = env("FACEBOOK_APP_SECRET", default="")
FACEBOOK_REDIRECT_URI = env(
    "FACEBOOK_REDIRECT_URI",
    default="http://127.0.0.1:8000/channels/facebook/callback/",
)
FACEBOOK_GRAPH_API_VERSION = env("FACEBOOK_GRAPH_API_VERSION", default="v21.0")

# Fernet key for encrypting tokens at rest (generate with: from cryptography.fernet import Fernet; Fernet.generate_key())
FERNET_KEY = env("FERNET_KEY", default="")

# Signup bonus credits
SIGNUP_CREDIT_BONUS = 5

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}
