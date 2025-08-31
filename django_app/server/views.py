import os
from datetime import datetime

import requests

from django.contrib.auth.hashers import check_password
from django.utils.timezone import make_aware

from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import PollUser, Group, PollUserGroup
from .serializers import (
    BindGroupSerializer,
    GroupSerializer,
    LoginSerializer,
    RegisterSerializer,
    SendPollSerializer,
    SendQuizSerializer,
)

from .tasks import send_quiz_task

from project.settings.base import TELEGRAM_API



COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"   # em produção: true (HTTPS)
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")                  # Sempre none pois nosso front e back estão em domínios diferentes
REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/api/auth/token/refresh/")
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
REFRESH_TTL_DAYS = int(os.getenv("REFRESH_TTL_DAYS", "14"))


def set_refresh_cookie(response: Response, refresh_str: str):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_str,
        max_age=REFRESH_TTL_DAYS * 24 * 3600,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=REFRESH_COOKIE_PATH,  # cookie só é enviado nessa rota
    )

class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Gera um novo access token lendo o refresh do cookie HttpOnly.",
        responses={200: openapi.Response(description="Token renovado com sucesso.")}
    )
    def post(self, request):
        refresh_from_cookie = request.COOKIES.get(REFRESH_COOKIE_NAME)

        if not refresh_from_cookie:
            return Response({
                "data": {
                    "success": False,
                    "message": "Refresh token ausente.",
                    "errors": {"refresh": ["Cookie não encontrado."]}
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_from_cookie)
            new_access = str(token.access_token)

            return Response({
                "data": {
                    "success": True,
                    "message": "Token renovado com sucesso.",
                    "tokens": {
                        "access_token": new_access
                    }
                }
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                "data": {
                    "success": False,
                    "message": "Refresh inválido ou expirado.",
                    "errors": {"refresh": ["Token inválido/expirado."]}
                }
            }, status=status.HTTP_401_UNAUTHORIZED)


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
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        sender = message.get("from", {})
        sender_id = sender.get('id')

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

        if text == "/bind":
            if (chat_type := chat.get('type')) and chat_type != 'group':
                return Response({"status": 'bad request'})

            chat_title = chat.get("title")

            bind_response = requests.post(f'https://bot-telegram-test-server1.onrender.com/api/bind-group/', json={
                'telegram_id': sender_id,
                'chat_id': chat_id,
                'chat_title': chat_title
            })

            if not bind_response.ok:
                requests.post(f"{TELEGRAM_API}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"Erro! Não foi possível salvar o grupo {chat_title}.",
                })
                return Response({"data": {"status":bind_response.status_code}})
            
            requests.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"Sucesso! O grupo {chat_title} foi salvo.",
            })

        return Response({"data": {"status": "ok"}})


class RegisterView(APIView):
    @swagger_auto_schema(
        operation_description="Cria um novo usuário.",
        request_body=RegisterSerializer,
        responses={201: openapi.Response(description="Usuário registrado.")}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"data": {"success": False, "errors": serializer.errors}},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        access = str(refresh.access_token)
        refresh_str = str(refresh)

        resp = Response({
            "data": {
                "success": True,
                "message": "Usuário registrado com sucesso.",
                "user": {
                    "name": user.name,
                    "email": user.email
                },
                "tokens": {
                    "access_token": access  
                }
            }
        }, status=status.HTTP_201_CREATED)

        # grava o refresh como cookie HttpOnly
        set_refresh_cookie(resp, refresh_str)
        return resp


class LoginView(APIView):
    @swagger_auto_schema(
        operation_description="Autentica um usuário e retorna um token JWT.",
        request_body=LoginSerializer,
        responses={200: openapi.Response(description="Login realizado com sucesso.")}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "data": {"success": False, "errors": serializer.errors}
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = PollUser.objects.get(email=email)
        except PollUser.DoesNotExist:
            return Response({
                "data": {"success": False, "errors": {"email": ["Usuário não encontrado."]}}
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({
                "data": {"success": False, "errors": {"password": ["Senha incorreta."]}}
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Gera tokens
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh_str = str(refresh)

        resp = Response({
            "data": {
                "success": True,
                "message": "Login realizado com sucesso.",
                "user": {
                    "name": user.name,
                    "email": user.email
                },
                "tokens": {
                    "access_token": access
                }
            }
        }, status=status.HTTP_200_OK)

        # Seta o refresh em cookie HttpOnly
        set_refresh_cookie(resp, refresh_str)
        return resp



class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Faz logout e apaga o cookie de refresh.",
        responses={200: openapi.Response(description="Logout realizado.")}
    )
    def post(self, request):
        resp = Response({
            "data": {
                "success": True,
                "message": "Logout realizado. Cookies limpos."
            }
        }, status=status.HTTP_200_OK)
        resp.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path=REFRESH_COOKIE_PATH,
            samesite=COOKIE_SAMESITE,
        )
        return resp


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

        if not serializer.is_valid():
            return Response({
                "data": {
                    "success": False,
                    "message": "Erro de validação nos dados enviados.",
                    "errors": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data['chatId']
        question = serializer.validated_data['question']
        options = serializer.validated_data['options']

        try:
            response = requests.post(f"{TELEGRAM_API}/sendPoll", json={
                "chat_id": chat_id,
                "question": question,
                "options": options,
                "is_anonymous": False,
            })

            if response.status_code == 200:
                return Response({
                    "data": {
                        "success": True,
                        "message": "Enquete enviada com sucesso.",
                        "poll": {
                            "chat_id": chat_id,
                            "question": question,
                            "options": options
                        }
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "data": {
                        "success": False,
                        "message": "Erro na API do Telegram.",
                        "errors": response.json()
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except requests.RequestException as e:
            return Response({
                "data": {
                    "success": False,
                    "message": "Falha na comunicação com o Telegram.",
                    "errors": {"exception": str(e)}
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SendQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Envia múltiplas perguntas tipo quiz para um grupo do Telegram. Pode ser agendado.",
        request_body=SendQuizSerializer,
        responses={
            200: openapi.Response(description="Quizzes enviados ou agendados com sucesso."),
            400: "Erro de validação.",
            500: "Erro ao enviar para o Telegram."
        }
    )
    def post(self, request):
        serializer = SendQuizSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "data": {
                    "success": False,
                    "message": "Erro de validação nos dados enviados.",
                    "errors": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data['chatId']
        questions = serializer.validated_data['questions']
        schedule_date = serializer.validated_data.get('schedule_date')
        schedule_time = serializer.validated_data.get('schedule_time')

        if schedule_date and schedule_time:
            try:
                scheduled_datetime = make_aware(datetime.combine(schedule_date, schedule_time))
                send_quiz_task.apply_async((chat_id, questions), eta=scheduled_datetime)
                return Response({
                    "data": {
                        "success": True,
                        "message": f"Quizzes agendados para {scheduled_datetime.strftime('%d/%m/%Y %H:%M')}."
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "data": {
                        "success": False,
                        "message": "Erro ao agendar envio dos quizzes.",
                        "errors": str(e)
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            send_quiz_task.delay(chat_id, questions)
            return Response({
                "data": {
                    "success": True,
                    "message": "Quizzes enviados imediatamente."
                }
            }, status=status.HTTP_200_OK)


class BindGroupView(APIView):
    @swagger_auto_schema(
        operation_description="Vincula um grupo do Telegram a um professor e/ou staff usando telegram_id e chat_id.",
        request_body=BindGroupSerializer,
        responses={
            200: openapi.Response(description="Grupo vinculado com sucesso ou vínculo já existente."),
            400: "Requisição inválida.",
            403: "Usuário com permissões insuficientes para vincular grupos.",
            404: "Usuário ou grupo não encontrados."
        }
    )
    def post(self, request):
        serializer = BindGroupSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = serializer.validated_data['telegram_id']

        try:
            user = PollUser.objects.get(telegram_id=telegram_id)
        except PollUser.DoesNotExist:
            return Response({
                "success": False,
                "message": "Usuário não cadastrado"
            }, status=status.HTTP_404_NOT_FOUND)

        chat_id = serializer.validated_data['chat_id']
        chat_title = serializer.validated_data['chat_title']

        group, _ = Group.objects.get_or_create(
                chat_id=chat_id,
                defaults={'title': chat_title}
            )
        if group.title != chat_title:
            group.title = chat_title
            group.save()

        if not (user.is_professor or user.is_staff):
            return Response({
                "success": False,
                "message": f"Permissões insuficientes. Usuário não pode vincular grupos."
            }, status=status.HTTP_403_FORBIDDEN)

        poll_user_group, created = PollUser.objects.bind_group(user, group)

        return Response({
            "success": True,
            "message": "Grupo vinculado com sucesso" if created else "Vínculo existente. Atualizando dados do grupo.",
            "data": {
                "bind_date": poll_user_group.bind_date
            }
        }, status=status.HTTP_200_OK)


class UserGroupsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Lista todos os grupos vinculados ao usuário autenticado.",
        responses={200: openapi.Response(description="Lista de grupos vinculados.")}
    )

    def get(self, request):
        user = request.user
        groups = PollUser.objects.list_groups(user)
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
