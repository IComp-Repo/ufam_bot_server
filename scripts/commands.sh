#!/bin/sh
set -e

echo "Detectando ambiente..."

# Se PGHOST estiver presente, estamos em produção (Railway)
if [ -n "$PGHOST" ]; then
  echo "Ambiente: PRODUÇÃO (Railway)"
  DB_HOST="$PGHOST"
  DB_PORT="$PGPORT"
else
  echo "Ambiente: DESENVOLVIMENTO (local)"
  DB_HOST="$POSTGRES_HOST"
  DB_PORT="$POSTGRES_PORT"
fi

# Espera o banco de dados iniciar
echo "Aguardando banco de dados em $DB_HOST:$DB_PORT..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Ainda esperando banco de dados..."
  sleep 2
done

echo "Banco de dados disponível!"

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Aplicando migrações..."
python manage.py makemigrations || true
python manage.py migrate --noinput

echo "Criando superusuário (se não existir)..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email="${DJANGO_SUPERUSER_EMAIL}").exists():
    User.objects.create_superuser(email="${DJANGO_SUPERUSER_EMAIL}", password="${DJANGO_SUPERUSER_PASSWORD}")
EOF

# Decide como iniciar o servidor
if [ -n "$PGHOST" ]; then
  echo "Iniciando Gunicorn (produção)..."
  exec gunicorn project.wsgi:application --bind 0.0.0.0:8000
else
  echo "Iniciando servidor de desenvolvimento (runserver)..."
  exec python manage.py runserver 0.0.0.0:8000
fi
