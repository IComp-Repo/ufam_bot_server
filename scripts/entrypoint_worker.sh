#!/bin/sh
set -eu
PY=/venv/bin/python

# Espera DB
DB_HOST="${PGHOST:-${POSTGRES_HOST:-psql}}"
DB_PORT="${PGPORT:-${POSTGRES_PORT:-5432}}"
echo "Aguardando DB em ${DB_HOST}:${DB_PORT}..."
ATTEMPTS=0
until nc -z "${DB_HOST}" "${DB_PORT}"; do
  ATTEMPTS=$((ATTEMPTS+1))
  [ $ATTEMPTS -gt 60 ] && echo "Timeout DB" && exit 1
  sleep 2
done

# Espera broker
BROKER_URL="${CELERY_BROKER_URL:-redis://redis:6379/0}"
BROKER_HOST="$(echo "$BROKER_URL" | sed -E 's#^[a-z]+://([^:/@]+)(:([0-9]+))?.*$#\1#')"
BROKER_PORT="$(echo "$BROKER_URL" | sed -E 's#^[a-z]+://([^:/@]+):?([0-9]+)?.*$#\2#')"
[ -z "${BROKER_PORT}" ] && BROKER_PORT=6379
echo "Aguardando broker em ${BROKER_HOST}:${BROKER_PORT}..."
ATTEMPTS=0
until nc -z "${BROKER_HOST}" "${BROKER_PORT}"; do
  ATTEMPTS=$((ATTEMPTS+1))
  [ $ATTEMPTS -gt 60 ] && echo "Timeout broker" && exit 1
  sleep 2
done

export CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP="true"
CONC="${CELERY_WORKER_CONCURRENCY:-2}"

echo "Iniciando Celery worker..."
exec $PY -m celery -A project worker -l info --concurrency "${CONC}"
