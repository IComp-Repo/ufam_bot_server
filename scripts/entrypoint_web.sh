#!/bin/sh
set -eu

PY=/venv/bin/python
GUNI=/venv/bin/gunicorn

echo "Detectando ambiente..."
ENV="${DJANGO_ENV:-dev}"

if [ "${ENV}" = "prod" ] || [ -n "${PGHOST:-}" ]; then
  echo "Ambiente: PRODUÇÃO (Railway)"
  DB_HOST="${PGHOST:?PGHOST não definido}"
  DB_PORT="${PGPORT:-5432}"
  USE_GUNICORN=1
else
  echo "Ambiente: DESENVOLVIMENTO (local)"
  DB_HOST="${POSTGRES_HOST:-psql}"
  DB_PORT="${POSTGRES_PORT:-5432}"
  USE_GUNICORN=0
fi

echo "Aguardando banco de dados em ${DB_HOST}:${DB_PORT}..."
ATTEMPTS=0
until nc -z "${DB_HOST}" "${DB_PORT}"; do
  ATTEMPTS=$((ATTEMPTS+1))
  [ $ATTEMPTS -gt 60 ] && echo "Timeout aguardando DB" && exit 1
  sleep 2
done
echo "Banco de dados disponível!"

echo "Coletando arquivos estáticos..."
$PY manage.py collectstatic --noinput

echo "Aplicando migrações..."
$PY manage.py migrate --noinput

if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "Garantindo superusuário..."
  $PY manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
email = "${DJANGO_SUPERUSER_EMAIL}"
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password="${DJANGO_SUPERUSER_PASSWORD}")
EOF
else
  echo "Variáveis de superusuário ausentes; pulando criação."
fi

if [ "$USE_GUNICORN" = "1" ]; then
  echo "Iniciando Gunicorn (produção)..."
  exec $GUNI project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
else
  echo "Iniciando servidor de desenvolvimento..."
  exec $PY manage.py runserver 0.0.0.0:8000
fi
