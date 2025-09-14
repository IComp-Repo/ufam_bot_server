import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

def get_list(name: str, default=None):
    if default is None:
        default = []
    v = os.getenv(name)
    if not v:
        return default
    return [i.strip() for i in v.split(",") if i.strip()]

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = get_bool("DEBUG", False)

# aceita múltiplos, com defaults seguros
ALLOWED_HOSTS = get_list(
    "ALLOWED_HOSTS",
    [".up.railway.app", "localhost", "127.0.0.1"]
)

# precisa de esquema (https)
CSRF_TRUSTED_ORIGINS = get_list(
    "CSRF_TRUSTED_ORIGINS",
    ["https://*.up.railway.app"]
)

CORS_ALLOWED_ORIGINS = [
    "https://web-production-9089.up.railway.app",
    "https://poll-miniapp.vercel.app",
    "http://localhost:3000",  # React, Next.js
    "http://localhost:5173",  # Vite
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# WhiteNoise: arquivos estáticos comprimidos com manifest
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# por estar atrás de proxy (Railway)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    'corsheaders',        
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'server',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "project.urls"  
WSGI_APPLICATION = "project.wsgi.application"

# -------- Banco de dados --------
# Se Railway estiver presente, ele expõe PG* (PGHOST etc.).
if os.getenv("PGHOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("PGDATABASE", "postgres"),
            "USER": os.getenv("PGUSER", "postgres"),
            "PASSWORD": os.getenv("PGPASSWORD", ""),
            "HOST": os.getenv("PGHOST", "localhost"),
            "PORT": os.getenv("PGPORT", "5432"),
        }
    }
else:
    # Dev/local (docker-compose) com POSTGRES_*
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": os.getenv("POSTGRES_DB", "ufam_db"),
            "USER": os.getenv("POSTGRES_USER", "ufam_user"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "ufam_pass"),
            "HOST": os.getenv("POSTGRES_HOST", "psql"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

# -------- Static/Media --------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Manaus"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------- Celery --------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

# -------- Bot --------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# -------- Logging simples --------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# -------- Groq Cloud --------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_ALLOWED_USERS = get_list("GROQ_ALLOWED_USERS", [])  # emails permitidos a usar o serviço

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTH_USER_MODEL = 'server.PollUser'


TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Bot username, usado para emissao do link
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "PollsICompBot")
BOT_USER_ID = os.getenv("TELEGRAM_BOT_ID") 
BACKEND_API_BASE = os.getenv("BACKEND_API_BASE", "https://web-production-9089.up.railway.app")  
BIND_GROUP_URL = f"{BACKEND_API_BASE.rstrip('/')}/api/bind-group/" 

# Configurações de cookie para refresh token
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"   
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")                  # Sempre none pois nosso front e back estão em domínios diferentes
REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/api/auth/token/refresh/")
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
REFRESH_TTL_DAYS = int(os.getenv("REFRESH_TTL_DAYS", "14"))
