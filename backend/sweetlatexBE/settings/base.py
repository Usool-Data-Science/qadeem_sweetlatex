from datetime import timedelta
from os import getenv, path
from pathlib import Path

from common.utils import as_bool
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
env_path = path.join(BASE_DIR, ".docker-envs", ".env.dev")
if path.isfile(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


# Security
SECRET_KEY = getenv(
    "DJANGO_SECRET_KEY",
)
ADMIN_EMAIL = getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = getenv("ADMIN_PASSWORD")

# Applications
LOCAL_APPS = [
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    "common.apps.CommonConfig",
    "tasks.apps.TasksConfig",
    "interactions.apps.InteractionsConfig",
    "recommendations.apps.RecommendationsConfig",
    "chatbot.apps.ChatbotConfig",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "social_django",
    "djoser",
    "django_celery_beat",
    "cloudinary_storage",
    "cloudinary",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    *LOCAL_APPS,
    *THIRD_PARTY_APPS,
]

AUTH_USER_MODEL = "accounts.CustomUser"
APPEND_SLASH = True

# Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sweetlatexBE.urls"
WSGI_APPLICATION = "sweetlatexBE.wsgi.application"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Authentication
AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.CustomJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "contact": "5/day",
        "product": "100/day",
        "cart": "30/minute",
        "interaction_log": "120/min",
        "recommendations": "30/min",
        "chatbot": "20/min",
    },
}

# Social OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv("GOOGLE_AUTH_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv("GOOGLE_AUTH_SECRET_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["first_name", "last_name"]

# JWT
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Custom Auth Cookie
AUTH_COOKIE = "access"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = "None"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static & Media
STORAGES = {
    # "default" handles all file/image field uploads (ImageField, FileField).
    # Your project uses Cloudinary for media — keep it here.
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    # "staticfiles" handles collectstatic and static file serving.
    # WhiteNoise serves them efficiently through Gunicorn without Nginx.
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = getenv("EMAIL_HOST")
EMAIL_PORT = int(getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = as_bool(getenv("EMAIL_USE_TLS", "True"))
DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")

# ── ML / AI settings ─────────────────────────────────────────────────────────
LLM_PROVIDER = getenv("LLM_PROVIDER", "gemini")
LLM_MODEL_NAME = getenv("LLM_MODEL_NAME", "gemini-1.5-flash")
GOOGLE_API_KEY = getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1")

PINECONE_API_KEY = getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = getenv("PINECONE_INDEX_NAME", "sweetlatex-rag")
PINECONE_DIMENSION = int(getenv("PINECONE_DIMENSION", "384"))

CLIP_MODEL_NAME = getenv("CLIP_MODEL_NAME", "ViT-B/32")
FAISS_INDEX_PATH = getenv("FAISS_INDEX_PATH", "/app/faiss_index")
SASREC_MODEL_PATH = getenv("SASREC_MODEL_PATH", "/app/ml_models/sasrec.pt")
BPR_MODEL_PATH = getenv("BPR_MODEL_PATH", "/app/ml_models/bpr.pkl")

FUSION_ALPHA = float(getenv("FUSION_ALPHA", "0.35"))
FUSION_BETA = float(getenv("FUSION_BETA", "0.40"))
FUSION_GAMMA = float(getenv("FUSION_GAMMA", "0.25"))
