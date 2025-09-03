# Comandos para setar webhook para ambiente de produção

```bash
curl -X POST "https://api.telegram.org/bot7929781204:AAH2lM2eMt9g19kmRx1QfSRyUEEdXz373Ko/setWebhook"   -d "url=https://web-production-9089.up.railway.app/api/telegram/webhook/"   -d 'allowed_updates=["message","my_chat_member"]'   -d "secret_token=Bot23082025"
```

# Comandos para setar webhook para ambiente local

```bash
curl -X POST "https://api.telegram.org/bot7929781204:AAH2lM2eMt9g19kmRx1QfSRyUEEdXz373Ko/setWebhook"   -d "url=<link da url do ngrok>/api/telegram/webhook/"   -d 'allowed_updates=["message","my_chat_member"]'   -d "secret_token=<Bot23082025>"
```