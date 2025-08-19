from .base import *

DEBUG = False

# Configure os domínios do Railway aqui (sem wildcard aberto em prod)
# Ex.: yourapp.up.railway.app ou domínio próprio
ALLOWED_HOSTS = get_list("ALLOWED_HOSTS", ["yourapp.up.railway.app"])
# Railway exige CSRF_TRUSTED_ORIGINS com HTTPS
# Dica: use "https://*.up.railway.app" se for subdomínio do Railway
CSRF_TRUSTED_ORIGINS = get_list(
    "CSRF_TRUSTED_ORIGINS",
    ["https://yourapp.up.railway.app", "https://*.up.railway.app"],
)

# Cookies e HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Ative HSTS se já tiver HTTPS estável
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 semana (ajuste progressivo)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
