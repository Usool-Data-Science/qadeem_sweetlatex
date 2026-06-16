from os import getenv, path

from dotenv import load_dotenv

from .base import *

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
# Load environment variables
env_path = path.join(BASE_DIR, ".docker-envs", ".env.prod")
if path.isfile(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# -----------------------------------------------------------------------------
# General & Security
# -----------------------------------------------------------------------------
DEBUG = False
ALLOWED_HOSTS = getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# -----------------------------------------------------------------------------
# Session & CSRF Cookies
# -----------------------------------------------------------------------------
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"  # correct for admin on same domain
SESSION_COOKIE_DOMAIN = ".sweetlatex.com"  # scope explicitly
SESSION_COOKIE_AGE = 1209600  # 2 weeks

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # must be False so JS can read it
CSRF_COOKIE_SAMESITE = "Lax"  # match session cookie
CSRF_COOKIE_DOMAIN = ".sweetlatex.com"  # scope explicitly
CSRF_TRUSTED_ORIGINS = getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = getenv("CORS_ALLOWED_ORIGINS", "").split(",")
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
# Authentication (Djoser)
# -----------------------------------------------------------------------------
SITE_NAME = getenv("SITE_NAME")
DOMAIN = getenv("DOMAIN")

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
AUTH_COOKIE_DOMAIN = ".sweetlatex.com"
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = "Lax"  # admin is also on sweetlatex.com
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_MAX_AGE = 1209600

# -----------------------------------------------------------------------------
# Database (PostgreSQL for production)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("DB_NAME"),
        "USER": getenv("DB_USER"),
        "PASSWORD": getenv("DB_PASSWORD"),
        "HOST": getenv("DB_HOST"),
        "PORT": getenv("DB_PORT"),
    }
}

# -----------------------------------------------------------------------------
# Stripe
# -----------------------------------------------------------------------------
STRIPE_API_KEY = getenv("STRIPE_API_KEY")
STRIPE_SECRET_KEY = getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_SUCCESS_URL = getenv("STRIPE_SUCCESS_URL", "https://sweetlatex.com/success")
STRIPE_CANCEL_URL = getenv("STRIPE_CANCEL_URL", "https://sweetlatex.com/cancel")

# -----------------------------------------------------------------------------
# Redis / Celery
# -----------------------------------------------------------------------------
REDIS_URL = getenv("REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
