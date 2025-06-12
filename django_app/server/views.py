from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import PollUser
from .serializers import RegisterSerializer, LoginSerializer, SendPollSerializer
import requests
import os

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

TELEGRAM_API = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"


class TelegramWebhookView(APIView):
    @swagger_auto_schema(
        operation_description="Recebe atualizações do Telegram Bot.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'text': openapi.Schema(type=openapi.TYPE_STRING),
                        'chat': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            }
        ),
        responses={200: openapi.Response(description="Atualização recebida com sucesso.")}
    )
    def post(self, request):
        update = request.data
        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if text == "/start":
            requests.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": "Vamos começar 🖥️\nUse o botão abaixo para criar uma enquete!",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {
                                "text": "Criar enquete",
                                "web_app": {"url": "https://poll-miniapp.vercel.app/"}
                            }
                        ]
                    ]
                }
            })

        return Response({"status": "ok"})


class RegisterView(APIView):
    @swagger_auto_schema(
        operation_description="Cria um novo usuário professor.",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(description="Usuário registrado com sucesso."),
            400: "Dados inválidos.",
            403: "Somente professores podem se cadastrar."
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            if not serializer.validated_data.get('is_professor'):
                return Response({"error": "Somente professores podem se cadastrar."}, status=403)

            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Usuário registrado com sucesso!",
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    @swagger_auto_schema(
        operation_description="Autentica um usuário e retorna um token JWT.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(description="Login realizado com sucesso."),
            401: "Credenciais inválidas."
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            try:
                user = PollUser.objects.get(email=email)
                if check_password(password, user.password):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "message": "Login realizado com sucesso!",
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                    }, status=200)
            except PollUser.DoesNotExist:
                pass
        return Response({"error": "Credenciais inválidas."}, status=401)


class SendPollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Envia uma enquete para um grupo do Telegram.",
        request_body=SendPollSerializer,
        responses={
            200: openapi.Response(description="Poll enviada com sucesso!"),
            400: "Erro de validação.",
            500: "Erro ao enviar a Poll."
        }
    )
    def post(self, request):
        serializer = SendPollSerializer(data=request.data)
        if serializer.is_valid():
            chat_id = serializer.validated_data['chatId']
            question = serializer.validated_data['question']
            options = serializer.validated_data['options']

            try:
                requests.post(f"{TELEGRAM_API}/sendPoll", json={
                    "chat_id": chat_id,
                    "question": question,
                    "options": options,
                    "is_anonymous": False,
                })
                return Response({"message": "Poll enviada com sucesso!"}, status=200)
            except requests.RequestException:
                return Response({"error": "Erro ao enviar a Poll."}, status=500)
        return Response(serializer.errors, status=400)
