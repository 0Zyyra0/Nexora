"""
Django settings for the portfolio project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------
# Core / security
# -----------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-ME-before-deploying-#p0rtf0l10#",
)

# Local development = True
# Production on cPanel = False
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,alimoraaddi.ir,www.alimoraaddi.ir",
    ).split(",")
    if host.strip()
]


# -----------------------------------------------------------------------
# CSRF
# -----------------------------------------------------------------------

_csrf_origins = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://alimoraaddi.ir,https://alimoraaddi.ir,"
    "http://www.alimoraaddi.ir,https://www.alimoraaddi.ir",
)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in _csrf_origins.split(",")
    if origin.strip()
]


# -----------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Local apps
    "portfolio.apps.PortfolioConfig",
]


# -----------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves collected static files.
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


# -----------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------

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

                # Makes `profile` available in every template.
                "portfolio.context_processors.profile",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# -----------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        # shared hosting: wait for a busy lock instead of failing with a 500
        "OPTIONS": {"timeout": 20},
    }
}


# -----------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
    },
]


# -----------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------------
# Static files
# -----------------------------------------------------------------------

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# Plain static storage (no manifest): a missing/stale collectstatic can never
# turn into a 500 error. STORAGES works on Django 4.2+ (STATICFILES_STORAGE was
# removed in 5.1).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Let WhiteNoise find files straight from static/ and each app's static dir, so
# the site styles itself correctly even if `collectstatic` was never run (this
# host has no terminal). If collectstatic *has* been run, that still works too.
WHITENOISE_USE_FINDERS = True


# -----------------------------------------------------------------------
# Media / uploaded files
# -----------------------------------------------------------------------

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# -----------------------------------------------------------------------
# Default primary key
# -----------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------------------------------------------------
# Pagination / misc project settings
# -----------------------------------------------------------------------

BLOG_POSTS_PER_PAGE = 6
PROJECTS_PER_PAGE = 9


# -----------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------

LOGIN_URL = "/accounts/login/"

LOGIN_REDIRECT_URL = "/accounts/profile/"

LOGOUT_REDIRECT_URL = "/"


# EmailBackend makes the site's own login form, which asks for an email,
# authenticate correctly. ModelBackend stays second so /admin/ can continue
# using the normal Django username authentication.

AUTHENTICATION_BACKENDS = [
    "portfolio.auth_backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]


# -----------------------------------------------------------------------
# Production security
# -----------------------------------------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# -----------------------------------------------------------------------
# Logging — real tracebacks end up in logs/django-errors.log (readable from
# cPanel's File Manager) instead of being lost behind a bare "Server Error (500)".
# -----------------------------------------------------------------------

LOG_DIR = BASE_DIR / "logs"
try:
    LOG_DIR.mkdir(exist_ok=True)
    _log_handler = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(LOG_DIR / "django-errors.log"),
        "maxBytes": 1_000_000,
        "backupCount": 3,
        "encoding": "utf-8",
        "formatter": "verbose",
    }
except OSError:  # read-only filesystem: fall back to stderr
    _log_handler = {"class": "logging.StreamHandler", "formatter": "verbose"}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {"errors": _log_handler},
    "loggers": {
        "django.request": {"handlers": ["errors"], "level": "WARNING", "propagate": False},
        "portfolio": {"handlers": ["errors"], "level": "INFO", "propagate": False},
    },
}
