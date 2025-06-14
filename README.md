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
# fake secret key
SECRET_KEY="bot!_telegram!_env!_!@#"

# 0 False, 1 True
DEBUG="1"

# Comma Separated values
ALLOWED_HOSTS="127.0.0.1, localhost"

# fake values
DB_ENGINE="django.db.backends.postgresql"
POSTGRES_DB="bot_database"
POSTGRES_USER="bot_user"
POSTGRES_PASSWORD="bot_user_password"
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
- API PROD : [https://bot-telegram-test-server1.onrender.com/swagger/](https://bot-telegram-test-server1.onrender.com/)
- SWAGGER: [https://bot-telegram-test-server1.onrender.com/swagger/](https://bot-telegram-test-server1.onrender.com/swagger/)


