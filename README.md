# BOT TEST SERVER

## Índice

- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)

## Instalação

### Clonando o Repositório

```bash
git clone https://github.com/IComp-Projects/bot_telegram_test_server.git
cd .\bot_telegram_test_server\
```
## Configuração

### Variáveis de Ambiente

Dentro da pasta chamada dotenv_files renomear o arquivo .env-example para .env
```bash
DJANGO_ENV=dev
SECRET_KEY="dev-secret"
DEBUG="1"
ALLOWED_HOSTS="127.0.0.1,localhost"
CSRF_TRUSTED_ORIGINS="http://127.0.0.1:8000,http://localhost:8000"

DJANGO_SUPERUSER_EMAIL="admin@example.com"
DJANGO_SUPERUSER_PASSWORD="admin123"

TELEGRAM_BOT_TOKEN="your-telegram-bot-token"

# Redis local no compose
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=true

DB_ENGINE="django.db.backends.postgresql"
POSTGRES_DB="ufam_db"
POSTGRES_USER="ufam_user"
POSTGRES_PASSWORD="ufam_pass"
POSTGRES_HOST="psql"
POSTGRES_PORT="5432"
```
## Execução

### Buildando e Iniciando os Contêineres

Para construir as imagens Docker e iniciar a aplicação, execute:
```bash
docker-compose up --build
```
Para vizualizar os  contêineres:
- Docker desktop : [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) ou use: 
    ```bash
    docker ps -a 
    ```

Para mudança dentro da aplicação, execute:
```bash
docker-compose up 
```
### Acessando a aplicação e vizualizando as rotas de api

Após inicializar, a aplicação estará disponível em:
- API LOCAL: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) 



