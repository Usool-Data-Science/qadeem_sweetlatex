from os import getenv, path

from dotenv import load_dotenv

from .base import *

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
env_file = path.join(BASE_DIR, ".docker-envs", ".env.dev")
if path.isfile(env_file):
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

# -----------------------------------------------------------------------------
# General & Security
# -----------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# -----------------------------------------------------------------------------
# Session & CSRF Cookies
# -----------------------------------------------------------------------------
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_AGE = 1209600  # 2 weeks

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False  # must be False so JS can read it
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_DOMAIN = None

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-session-id",
]

# -----------------------------------------------------------------------------
# Database (SQLite for local dev)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "sqlite" / "db.sqlite3",
    }
}

# -----------------------------------------------------------------------------
# Redis / Celery
# -----------------------------------------------------------------------------
REDIS_URL = getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# -----------------------------------------------------------------------------
# Stripe
# -----------------------------------------------------------------------------
STRIPE_API_KEY = getenv("STRIPE_API_KEY")
STRIPE_SECRET_KEY = getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_SUCCESS_URL = getenv("STRIPE_SUCCESS_URL", "http://localhost:3000/success")
STRIPE_CANCEL_URL = getenv("STRIPE_CANCEL_URL", "http://localhost:3000/cancel")

# -----------------------------------------------------------------------------
# Authentication (Djoser)
# -----------------------------------------------------------------------------
SITE_NAME = getenv("SITE_NAME", "Sweetlatex Dev")
DOMAIN = getenv("DOMAIN", "localhost:8000")

DJOSER = {
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "TOKEN_MODEL": None,
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": getenv("REDIRECT_URLS", "").split(","),
    "SERIALIZERS": {
        "user": "accounts.serializers.UserUpdateSerializer",
        "current_user": "accounts.serializers.UserUpdateSerializer",
    },
}

# -----------------------------------------------------------------------------
# Custom Auth Cookie
# -----------------------------------------------------------------------------
AUTH_COOKIE_SECURE = False
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_MAX_AGE = 1209600
