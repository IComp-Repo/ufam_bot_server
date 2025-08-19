from .base import *

DEBUG = False


# Cookies e HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Ative HSTS se já tiver HTTPS estável
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 semana (ajuste progressivo)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
