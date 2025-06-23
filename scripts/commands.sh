#!/bin/sh
set -e

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo "Waiting for Postgres Database Startup ($POSTGRES_HOST $POSTGRES_PORT) ..."
  sleep 2
done

echo "Postgres Database Started Successfully ($POSTGRES_HOST:$POSTGRES_PORT)"

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
