# BOT TEST SERVER

## Índice

- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)

## Instalação

### Clonando o Repositório

```bash
https://github.com/IComp-Projects/bot_telegram_test_server.git
cd .\bot_telegram_test_server\
```
## Configuração

### Variáveis de Ambiente

Crie uma pasta chamada dotenv_files e dentro dessa pasta criar um arquivo`.env` na raiz do projeto com as seguintes variáveis
```bash
SECRET_KEY="CHANGE-ME"

# 0 False, 1 True
DEBUG="1"

# Comma Separated values
ALLOWED_HOSTS="127.0.0.1, localhost"

DB_ENGINE="django.db.backends.postgresql"
POSTGRES_DB="CHANGE-ME"
POSTGRES_USER="CHANGE-ME"
POSTGRES_PASSWORD="CHANGE-ME"
POSTGRES_HOST="localhost"
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
### Acessando a aplicação

Após inicializar, a aplicação estará disponível em:
- API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)


