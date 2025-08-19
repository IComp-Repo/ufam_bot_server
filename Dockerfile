FROM python:3.11.3-alpine3.18
LABEL maintainer="martinhoprata95@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:/scripts:${PATH}"

# --------- SO deps ----------
# build-deps: para compilar wheels (psycopg2, cryptography, etc.)
# runtime-deps: libs necessárias em runtime + netcat para 'nc' + bash
RUN apk add --no-cache \
      bash \
      netcat-openbsd \
      libpq \
      libffi \
      openssl \
    && apk add --no-cache --virtual .build-deps \
      gcc \
      musl-dev \
      python3-dev \
      postgresql-dev \
      libffi-dev \
      openssl-dev

# --------- venv + pip deps (cache) ----------
WORKDIR /django_app
COPY django_app/requirements.txt /django_app/requirements.txt

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r /django_app/requirements.txt

# --------- app code + scripts ----------
COPY django_app /django_app
COPY scripts /scripts

# permissões + diretórios de static/media
RUN adduser --disabled-password --no-create-home duser && \
    mkdir -p /data/web/static /data/web/media && \
    chown -R duser:duser /venv /data/web/static /data/web/media /django_app /scripts && \
    chmod -R 755 /data/web/static /data/web/media && \
    apk add --no-cache dos2unix && \
    dos2unix /scripts/*.sh && \
    chmod +x /scripts/*.sh && \
    apk del .build-deps

EXPOSE 8000
USER duser

# Por padrão, chamaremos o entrypoint web; no compose dá pra sobrescrever.
CMD ["bash", "-lc", "commands.sh"]
