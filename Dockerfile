FROM python:3.11.3-alpine3.18
LABEL maintainer="martinhoprata95@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ARG ENVIRONMENT=production
ENV ENVIRONMENT=$ENVIRONMENT

COPY django_app /django_app
COPY scripts /scripts

WORKDIR /django_app

# Dependências de sistema para Alpine
RUN apk add --no-cache \
  bash \
  build-base \
  libffi-dev \
  jpeg-dev \
  zlib-dev \
  postgresql-dev \
  musl-dev \
  python3-dev \
  dos2unix

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r /django_app/requirements.txt && \
    dos2unix /scripts/commands.sh

RUN mkdir -p /data/web/static /data/web/media && \
    chmod -R 755 /data/web/static /data/web/media && \
    chmod +x /scripts/commands.sh

# Somente produção: cria usuário seguro e ajusta permissões
RUN if [ "$ENVIRONMENT" = "production" ]; then \
      adduser --disabled-password --no-create-home duser && \
      chown -R duser:duser /venv /data /scripts /django_app; \
    fi

ENV PATH="/scripts:/venv/bin:$PATH"

# Somente produção: troca para usuário não-root
# Em local, continua como root
USER ${ENVIRONMENT:-production} = production ? duser : root

EXPOSE 8000

CMD ["commands.sh"]
