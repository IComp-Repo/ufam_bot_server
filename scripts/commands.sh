#!/bin/sh
set -e

echo "Aguardando PostgreSQL ($PGHOST:$PGPORT)..."

while ! nc -z "$PGHOST" "$PGPORT"; do
  echo "Waiting for Postgres Database Startup ($PGHOST:$PGPORT) ..."
  sleep 2
done

echo "Postgres Database Started Successfully ($PGHOST:$PGPORT)"

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Aplicando migrações do banco de dados..."
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "Criando super usuário Django..."
python manage.py create_superuser || true

echo "Iniciando Celery..."
celery -A project worker -l info &

echo "Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000

wait
