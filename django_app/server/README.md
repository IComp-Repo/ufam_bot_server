# API - Poll MiniApp (Django)

Esta documentação lista todas as rotas disponíveis na API.

PROD -> https://bot-telegram-test-server1.onrender.com/
## Autenticação JWT

As rotas protegidas devem conter no header:

```
Authorization: Bearer <token_jwt>
```

---

## Auth e Usuários

### POST `/api/register/`

Registra um novo professor no sistema.

#### Body (JSON):
```json
{
  "email": "professor@exemplo.com",
  "password": "senha123",
  "register": "123456"
}
```

#### Response:
- `201 Created`: Registro bem-sucedido + tokens JWT.
- `403 Forbidden`: Tentativa de cadastro de aluno.
- `400 Bad Request`: Erros de validação.

---

### POST `/api/login/`

Autentica o usuário e retorna os tokens JWT.

#### Body (JSON):
```json
{
  "email": "professor@exemplo.com",
  "password": "senha123"
}
```

#### Response:
- `200 OK`: Token de acesso e refresh.
- `401 Unauthorized`: Credenciais inválidas.

---

## Envio de Enquetes

### POST `/api/send_poll/`

Envia uma enquete para um grupo do Telegram vinculado.

#### Body (JSON):
```json
{
  "chatId": "123456789",
  "question": "Qual sua matéria favorita?",
  "options": ["Matemática", "História", "Física"]
}
```

#### Response:
- `200 OK`: Enquete enviada.
- `403 Forbidden`: Chat não vinculado ou usuário não autenticado.
- `400 Bad Request`: Dados inválidos.
- `500 Internal Server Error`: Falha ao enviar a enquete.

---

## Integração com Telegram

### POST `/api/telegram/webhook/`

Endpoint chamado diretamente pelo Telegram via Webhook. Responsável por responder ao comando `/start`.

#### Request do Telegram (JSON simplificado):
```json
{
  "message": {
    "text": "/start",
    "chat": {
      "id": "123456789"
    }
  }
}
```

#### Response:
- `200 OK`: Mensagem com botão enviada ao usuário no Telegram.

---

## Notas

- Todas as rotas começam com `/api/`.
- O webhook precisa estar corretamente configurado com o bot no Telegram.
- O envio de enquetes exige um chat_id vinculado, embora isso possa ser desativado em versões futuras.
