"""Django settings for Promocode."""

import logging
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# Common settings

DEBUG = env("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env(
    "DJANGO_ALLOWED_HOSTS",
    list,
    default=["localhost", "127.0.0.1"],
)


# Integrations

ANTIFRAUD_ADDRESS = env("ANTIFRAUD_ADDRESS", default="localhost:9090")


# Caching

REDIS_URI = (
    "redis://"
    f"{env('REDIS_HOST', default='localhost')}"
    ":"
    f"{env('REDIS_PORT', default='6379')}"
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URI,
        "TIMEOUT": None,
        "KEY_PREFIX": "django",
    }
}


# Database

DB_URI = env.db_url("POSTGRES_CONN", default="sqlite:///db.sqlite3")

DATABASES = {"default": {**DB_URI, "CONN_MAX_AGE": 50}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth."
            "password_validation.UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        )
    },
]


# Static files (CSS, JavaScript, Images)

STATIC_ROOT = BASE_DIR / "static"

STATIC_URL = env("DJANGO_STATIC_URL", default="static/")

STATICFILES_DIRS = []

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


# Files

FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440


# Cors

CORS_ALLOWED_ORIGINS_FROM_ENV = env("DJANGO_CORS_ALLOWED_ORIGINS", list, ["*"])

if CORS_ALLOWED_ORIGINS_FROM_ENV == ["*"]:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS_FROM_ENV


# Forms

FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

FORMS_URLFIELD_ASSUME_HTTPS = False


# Internationalization

DATE_FORMAT = "N j, Y"

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",  # '2006-10-25'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y",  # '10/25/06'
    "%b %d %Y",  # 'Oct 25 2006'
    "%b %d, %Y",  # 'Oct 25, 2006'
    "%d %b %Y",  # '25 Oct 2006'
    "%d %b, %Y",  # '25 Oct, 2006'
    "%B %d %Y",  # 'October 25 2006'
    "%B %d, %Y",  # 'October 25, 2006'
    "%d %B %Y",  # '25 October 2006'
    "%d %B, %Y",  # '25 October, 2006'
]

DATETIME_FORMAT = "N j, Y, H:i:s"

DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
    "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
    "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
    "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
    "%m/%d/%y %H:%M:%S",  # '10/25/06 14:30:59'
    "%m/%d/%y %H:%M:%S.%f",  # '10/25/06 14:30:59.000200'
    "%m/%d/%y %H:%M",  # '10/25/06 14:30'
]

DECIMAL_SEPARATOR = "."

FIRST_DAY_OF_WEEK = 1

FORMAT_MODULE_PATH = None

LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="en-us")

LANGUAGES = [("en", _("English")), ("ru", _("Russian"))]

LOCALE_PATHS = []

MONTH_DAY_FORMAT = "F j"

NUMBER_GROUPING = 0

SHORT_DATE_FORMAT = "m/d/Y"

SHORT_DATETIME_FORMAT = "m/d/Y H:i:s"

THOUSAND_SEPARATOR = ","

TIME_FORMAT = "H:i:s"

TIME_INPUT_FORMATS = [
    "%H:%M:%S",  # '14:30:59'
    "%H:%M:%S.%f",  # '14:30:59.000200'
    "%H:%M",  # '14:30'
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_THOUSAND_SEPARATOR = True

USE_TZ = True

YEAR_MONTH_FORMAT = "F Y"


# HTTP

DATA_UPLOAD_MAX_MEMORY_SIZE = None

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

DATA_UPLOAD_MAX_NUMBER_FILES = None

DEFAULT_CHARSET = "utf-8"

FORCE_SCRIPT_NAME = None

INTERNAL_IPS = env(
    "DJANGO_INTERNAL_IPS",
    list,
    default=["127.0.0.1"],
)

MIDDLEWARE = [
    "django_guid.middleware.guid_middleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

SIGNING_BACKEND = "django.core.signing.TimestampSigner"

USE_X_FORWARDED_HOST = False

USE_X_FORWARDED_PORT = False

WSGI_APPLICATION = "config.wsgi.application"


# Notifiers

# Telegram

NOTIFIER_TELEGRAM_BOT_TOKEN = env(
    "DJANGO_NOTIFIER_TELEGRAM_BOT_TOKEN", default=None
)

NOTIFIER_TELEGRAM_CHAT_ID = env(
    "DJANGO_NOTIFIER_TELEGRAM_CHAT_ID", default=None
)

NOTIFIER_TELEGRAM_THREAD_ID = env(
    "DJANGO_NOTIFIER_TELEGRAM_THREAD_ID", default=None
)


# Logging

LOGGER_NAME = "promocode"

LOGGER = logging.getLogger(LOGGER_NAME)

LOGGING_FILTERS = {
    "require_debug_true": {
        "()": "django.utils.log.RequireDebugTrue",
    },
    "require_debug_false": {
        "()": "django.utils.log.RequireDebugFalse",
    },
    "correlation_id": {
        "()": "django_guid.log_filters.CorrelationId",
    },
}

LOGGING_FORMATTERS = {
    "json": {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "format": (
            "{levelname}{correlation_id}{asctime}"
            "{name}{pathname}{lineno}{message}"
        ),
        "style": "{",
    },
    "text": {
        "()": "colorlog.ColoredFormatter",
        "format": (
            "{log_color}[{levelname}]{reset} "
            "{light_black}{asctime} {name} | {pathname}:{lineno}{reset}\n"
            "{bold_black}{message}{reset}"
        ),
        "log_colors": {
            "DEBUG": "bold_green",
            "INFO": "bold_cyan",
            "WARNING": "bold_yellow",
            "ERROR": "bold_red",
            "CRITICAL": "bold_purple",
        },
        "style": "{",
    },
}

LOGGING_HANDLERS = {
    "console_debug": {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "filters": ["require_debug_true"],
        "formatter": "text",
    },
    "console_prod": {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "filters": ["require_debug_false", "correlation_id"],
        "formatter": "json",
    },
}

LOGGING_LOGGERS = {
    "django": {
        "handlers": ["console_debug", "console_prod"],
        "level": "INFO" if DEBUG else "ERROR",
        "propagate": False,
    },
    "django.request": {
        "handlers": ["console_debug", "console_prod"],
        "level": "INFO" if DEBUG else "ERROR",
        "propagate": False,
    },
    "django.server": {
        "handlers": ["console_debug"],
        "level": "INFO",
        "filters": ["require_debug_true"],
        "propagate": False,
    },
    "django.template": {"handlers": []},
    "django.db.backends.schema": {"handlers": []},
    "django.security": {"handlers": [], "propagate": True},
    "django.db.backends": {
        "handlers": ["console_debug"],
        "filters": ["require_debug_true"],
        "level": "DEBUG",
        "propagate": False,
    },
    "health-check": {
        "handlers": ["console_debug", "console_prod"],
        "level": "INFO" if DEBUG else "ERROR",
        "propagate": False,
    },
    LOGGER_NAME: {
        "handlers": ["console_debug", "console_prod"],
        "level": "DEBUG" if DEBUG else "INFO",
        "propagate": False,
    },
    "root": {
        "handlers": ["console_debug", "console_prod"],
        "level": "INFO" if DEBUG else "ERROR",
        "propagate": False,
    },
}

if NOTIFIER_TELEGRAM_BOT_TOKEN and NOTIFIER_TELEGRAM_CHAT_ID:
    LOGGING_HANDLERS["telegram"] = {
        "class": "config.notifiers.telegram.LoggingHandler",
        "level": "INFO",
        "filters": ["require_debug_false"],
        "token": NOTIFIER_TELEGRAM_BOT_TOKEN,
        "chat_id": NOTIFIER_TELEGRAM_CHAT_ID,
        "thread_id": NOTIFIER_TELEGRAM_THREAD_ID,
        "retries": 5,
        "delay": 2,
        "timeout": 5,
    }
    LOGGING_LOGGERS["django"]["handlers"].append("telegram")
    LOGGING_LOGGERS["django.request"]["handlers"].append("telegram")
    LOGGING_LOGGERS["health-check"]["handlers"].append("telegram")
    LOGGING_LOGGERS[LOGGER_NAME]["handlers"].append("telegram")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": LOGGING_FILTERS,
    "formatters": LOGGING_FORMATTERS,
    "handlers": LOGGING_HANDLERS,
    "loggers": LOGGING_LOGGERS,
}

LOGGING_CONFIG = "logging.config.dictConfig"


# Models

ABSOLUTE_URL_OVERRIDES = {}

FIXTURE_DIRS = []

INSTALLED_APPS = [
    # Build-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Healthcheck
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    # Third-party apps
    "corsheaders",
    "django_extensions",
    "django_guid",
    "ninja",
    # Internal apps
    # API v1 apps
    "api.v1.ping",
]

# GUID

DJANGO_GUID = {
    "GUID_HEADER_NAME": "Correlation-ID",
    "VALIDATE_GUID": True,
    "RETURN_HEADER": True,
    "EXPOSE_HEADER": True,
    "INTEGRATIONS": [],
    "IGNORE_URLS": [],
    "UUID_LENGTH": 32,
}


# Security

LANGUAGE_COOKIE_AGE = 31449600

LANGUAGE_COOKIE_DOMAIN = None

LANGUAGE_COOKIE_HTTPONLY = False

LANGUAGE_COOKIE_NAME = "django_language"

LANGUAGE_COOKIE_PATH = "/"

LANGUAGE_COOKIE_SAMESITE = "Lax"

LANGUAGE_COOKIE_SECURE = False

SECURE_PROXY_SSL_HEADER = None

CSRF_COOKIE_AGE = 31449600

CSRF_COOKIE_DOMAIN = None

CSRF_COOKIE_HTTPONLY = False

CSRF_COOKIE_NAME = "djangocsrftoken"

CSRF_COOKIE_PATH = "/"

CSRF_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = False

CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"

CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

CSRF_TRUSTED_ORIGINS = env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    list,
    default=["http://localhost", "http://127.0.0.1"],
)

CSRF_USE_SESSIONS = False

SECRET_KEY = env("RANDOM_SECRET", default="very_insecure_key")

SECRET_KEY_FALLBACKS = []


# Sessions

SESSION_CACHE_ALIAS = "default"

SESSION_COOKIE_AGE = 1209600

SESSION_COOKIE_DOMAIN = None

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_NAME = "djangosessionid"

SESSION_COOKIE_PATH = "/"

SESSION_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = False

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SESSION_FILE_PATH = None

SESSION_SAVE_EVERY_REQUEST = False

SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"


# Templates

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "autoescape": True,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
            "string_if_invalid": "",
            "file_charset": "utf-8",
        },
    }
]


# Testing

TEST_NON_SERIALIZED_APPS = []

TEST_RUNNER = "django.test.runner.DiscoverRunner"


# URLs

ROOT_URLCONF = "config.urls"


# debug-toolbar

DEBUG_TOOLBAR_CONFIG = {"SHOW_COLLAPSED": True, "UPDATE_ON_FETCH": True}

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
