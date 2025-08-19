#!/bin/sh
set -euo pipefail
PY=/venv/bin/python

log(){ printf '%s %s\n' "$(date +'%H:%M:%S')" "$*"; }

# --- DB host/port (dev: compose / prod: PG*) ---
if [ -n "${PGHOST:-}" ]; then
  DB_HOST="$PGHOST"; DB_PORT="${PGPORT:-5432}"
elif [ -n "${POSTGRES_HOST:-}" ]; then
  DB_HOST="$POSTGRES_HOST"; DB_PORT="${POSTGRES_PORT:-5432}"
else
  DB_HOST="psql"; DB_PORT="5432"    # dev: nome do serviço no docker-compose
fi

# Espera DB (desligue com WAIT_FOR_DB=0)
if [ "${WAIT_FOR_DB:-1}" != "0" ] && [ -n "$DB_HOST" ]; then
  log "Aguardando DB em ${DB_HOST}:${DB_PORT}..."
  i=0; until nc -z "$DB_HOST" "$DB_PORT"; do
    i=$((i+1)); [ $i -gt "${DB_WAIT_MAX_TRIES:-60}" ] && log "Timeout DB" && exit 1
    sleep 2
  done
fi

# --- Broker URL (aceita CELERY_BROKER_URL, REDIS_URL, UPSTASH_REDIS_URL) ---
BROKER_URL="${CELERY_BROKER_URL:-${REDIS_URL:-${UPSTASH_REDIS_URL:-redis://redis:6379/0}}}"
[ -z "$BROKER_URL" ] && { echo "ERRO: defina CELERY_BROKER_URL/REDIS_URL"; exit 1; }

# Parse seguro (ignora credenciais user:pass@ e pega host/porta certos)
SCHEME="${BROKER_URL%%://*}"
REST="${BROKER_URL#*://}"
case "$REST" in *@*) REST="${REST#*@}";; esac
HOSTPORT="${REST%%/*}"
BROKER_HOST="${HOSTPORT%%:*}"
if [ "$HOSTPORT" = "$BROKER_HOST" ]; then BROKER_PORT=""; else BROKER_PORT="${HOSTPORT#*:}"; fi
[ -z "$BROKER_PORT" ] && { [ "$SCHEME" = "rediss" ] && BROKER_PORT=6380 || BROKER_PORT=6379; }

# Espera broker (desligue com WAIT_FOR_BROKER=0)
if [ "${WAIT_FOR_BROKER:-1}" != "0" ]; then
  log "Aguardando broker em ${BROKER_HOST}:${BROKER_PORT}..."
  i=0; until nc -z "$BROKER_HOST" "$BROKER_PORT"; do
    i=$((i+1)); [ $i -gt "${BROKER_WAIT_MAX_TRIES:-60}" ] && log "Timeout broker" && exit 1
    sleep 2
  done
fi

export CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP="${CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP:-true}"

log "Iniciando Celery worker..."
exec "$PY" -m celery -A project worker -l info --concurrency "${CELERY_WORKER_CONCURRENCY:-2}"
