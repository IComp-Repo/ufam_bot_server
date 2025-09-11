import os
from datetime import datetime

import requests

from django.contrib.auth.hashers import check_password
from django.utils.timezone import make_aware
from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from rest_framework import status, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import (
    PollUser,
    Group,
    PollUserGroup,
    TelegramLinkToken,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizMessage,
    QuizAnswer
)

from .serializers import (
    BindGroupSerializer,
    UserGroupListItemSerializer,
    LoginSerializer,
    RegisterSerializer,
    SendPollSerializer,
    SendQuizSerializer,
)

from .tasks import send_quiz_task

from project.settings.base import (
    TELEGRAM_API,
    BOT_USERNAME,
    BOT_USER_ID,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    REFRESH_TTL_DAYS,
)



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

# View para custom 404 page
# Dá para melhorar depois
def custom_404(request, exception):
    return render(request, "404.html", status=404)


def safe_send_message(chat_id, text, reply_markup=None):
    """Envia mensagem ao Telegram sem quebrar o webhook em caso de erro."""
    try:
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
    except Exception:
        pass


def is_event_for_our_bot(new_chat_member: dict) -> bool:
    """Confirma que o update my_chat_member é sobre o NOSSO bot."""
    u = (new_chat_member or {}).get("user") or {}
    if not u.get("is_bot"):
        return False
    if BOT_USER_ID:
        try:
            return str(u.get("id")) == str(int(BOT_USER_ID))
        except Exception:
            pass
    bot_username = (u.get("username") or "").lower().lstrip("@")
    return bot_username == BOT_USERNAME.lower().lstrip("@")


# ========== Views ==========
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
        

class TelegramLinkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Gera deep-link /start <token> para vincular o Telegram.")
    def post(self, request):
        if not BOT_USERNAME:
            return Response({
                "data": {"success": False, "message": "BOT_USERNAME não configurado no servidor."}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token_obj = TelegramLinkToken.issue(request.user, ttl_minutes=15)
        deep_link = f"https://t.me/{BOT_USERNAME}?start={token_obj.token}"
        return Response({
            "data": {
                "success": True,
                "message": "Deep-link gerado.",
                "deep_link": deep_link,
                "expires_at": token_obj.expires_at
            }
        }, status=status.HTTP_200_OK)


class TelegramWebhookView(APIView):
    @swagger_auto_schema(
        operation_description="Recebe atualizações do Telegram Bot.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "message": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "text": openapi.Schema(type=openapi.TYPE_STRING),
                        "chat": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
                "my_chat_member": openapi.Schema(type=openapi.TYPE_OBJECT),
            },
        ),
        responses={200: openapi.Response(description="Atualização recebida com sucesso.")},
    )
    def post(self, request):
        update = request.data or {}
        print(request.data)
        message = update.get("message", {}) or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat", {}) or {}
        chat_id = chat.get("id")
        chat_type = (chat.get("type") or "").lower() 
        sender = message.get("from", {}) or {}
        sender_id = sender.get("id")

        # --- util: extrai comando e argumento, lidando com /start@SeuBot ---
        def parse_command(s: str):
            if not s.startswith("/"):
                return None, None
            head, *rest = s.split(maxsplit=1)
            # remove @botusername do comando (em grupos costuma vir /start@MeuBot)
            cmd = head.split("@", 1)[0].lower()  # "/start"
            arg = rest[0] if rest else ""
            return cmd, arg

        cmd, arg = parse_command(text)


        if cmd == "/start":
            # se NÃO for chat privado, avisa para usar no privado e sai
            if chat_type != "private":
                safe_send_message(
                    chat_id,
                    "⚠️ Este comando deve ser usado no chat privado do bot.\n"
                    "Abra o chat com o bot e envie: /start"
                )
                return Response({"data": {"status": "start_in_group_blocked"}}, status=status.HTTP_200_OK)

            # /start <token> → vincula
            if arg:
                token = arg
                try:
                    t = TelegramLinkToken.objects.select_related("user").get(token=token)
                    
                    if not t.is_valid:
                        safe_send_message(chat_id, "Este link expirou. Gere outro no app.")
                        return Response({"data": {"status": "expired_token"}}, status=status.HTTP_200_OK)
                    
                    user = t.user
                    
                    #verifica se o usuário já tem telegram_id diferente do sender_id
                    if user.telegram_id and user.telegram_id != sender_id:
                        safe_send_message(
                            chat_id,
                            "⚠️ Este Telegram já está vinculado a outra conta.\n"
                            "Se acredita ser um erro, entre em contato com o suporte."
                        )
                        return Response({"data": {"status": "user_already_linked"}}, status=status.HTTP_200_OK)
                    
                    #verifica se o telegram_id já está em uso por outro usuário
                    existing_user = PollUser.objects.filter(telegram_id=sender_id).exclude(id=user.id).first()
                    if existing_user:
                        safe_send_message(
                            chat_id,
                            "⚠️ Este Telegram já está vinculado a outra conta.\n"
                            "Se acredita ser um erro, entre em contato com o suporte."
                        )
                        return Response({"data": {"status": "telegram_id_in_use"}}, status=status.HTTP_200_OK)
                    
                    #vincula e marca token como usado
                    user.telegram_id = sender_id
                    user.save(update_fields=["telegram_id"])
                    t.mark_used()

                    safe_send_message(
                        chat_id,
                        "✅ Conta vinculada com sucesso ao Knowledge Check Bot!\n\n"
                        "👉 Agora, adicione o bot a um grupo que você administra\n"
                        "ou envie o comando /bind diretamente no grupo."
                    )
                    return Response({"data": {"status": "linked"}}, status=status.HTTP_200_OK)
               
                except TelegramLinkToken.DoesNotExist:
                    safe_send_message(chat_id, "Link inválido ou expirado. Gere outro no app.")
                    return Response({"data": {"status": "invalid_token"}}, status=status.HTTP_200_OK)

            # /start sem token → mensagem de boas-vindas COM botão (apenas no privado)
            safe_send_message(
                chat_id,
                "Vamos começar 🖥️\nUse o botão abaixo para criar uma enquete!",
                reply_markup={
                    "inline_keyboard": [
                        [{"text": "Criar enquete", "web_app": {"url": "https://poll-miniapp.vercel.app/"}}]
                    ]
                },
            )
            return Response({"data": {"status": "start"}}, status=status.HTTP_200_OK)

        #Auto-bind via my_chat_member 
        if "my_chat_member" in update:
            mcm = update.get("my_chat_member") or {}

            mch_chat = mcm.get("chat") or {}
            group_chat_id = mch_chat.get("id")
            chat_title = mch_chat.get("title") or ""

            actor = mcm.get("from") or {}          
            inviter_tg_id = actor.get("id")

            new_member = mcm.get("new_chat_member") or {}
            new_status = new_member.get("status")

            if new_status in ("member", "administrator") and is_event_for_our_bot(new_member):
                # precisa que o "actor" já tenha feito /start <token>
                try:
                    inviter = PollUser.objects.get(telegram_id=inviter_tg_id)
                except PollUser.DoesNotExist:
                    safe_send_message(
                        group_chat_id,
                        "Quem adicionou o bot ainda não conectou a conta.\n"
                        "No privado do bot, gere o link no app e use /start <token>.\n"
                        "Depois, remova e adicione o bot novamente ou envie /bind no grupo."
                    )
                    return Response({"data": {"status": "inviter_not_linked"}}, status=status.HTTP_200_OK)

                group, _ = Group.objects.get_or_create(
                    chat_id=str(group_chat_id),
                    defaults={"title": chat_title},
                )
                if chat_title and group.title != chat_title:
                    group.title = chat_title
                    group.save(update_fields=["title"])

                PollUserGroup.objects.get_or_create(
                    poll_user=inviter,
                    group=group,
                )

                safe_send_message(
                    group_chat_id,
                    "✅ Bot conectado e grupo vinculado à sua conta do Knowledge Check Bot com sucesso! 🤖🎉"
                )

                return Response({"data": {"status": "auto_bound"}}, status=status.HTTP_200_OK)

            if is_event_for_our_bot(new_member) and new_status in ("kicked", "left"):
                return Response({"data": {"status": "bot_removed"}}, status=status.HTTP_200_OK)

            return Response({"data": {"status": "ignored"}}, status=status.HTTP_200_OK)
        
        if "poll_answer" in update:
            pa = update["poll_answer"]
            tg_poll_id = pa.get("poll_id")
            user = pa.get("user") or {}
            tg_user_id = user.get("id")
            option_ids = pa.get("option_ids") or []

            print("[poll_answer] pid=", repr(tg_poll_id), "uid=", tg_user_id, "opts=", option_ids)

            if not tg_poll_id or not option_ids or tg_user_id is None:
                return Response({"data": {"status": "skip"}}, status=200)

            try:
                question = QuizQuestion.objects.filter(telegram_poll_id=str(tg_poll_id)).first()
                print("[poll_answer] qq_found=", bool(question), "qq_id=", getattr(question, "id", None))

                if not question:
                    return Response({"data": {"status": "question_not_found"}}, status=200)

                chosen = int(option_ids[0])
                is_correct = (chosen == int(question.correct_option_index))

                obj, created = QuizAnswer.objects.update_or_create(
                    question=question,
                    telegram_user_id=int(tg_user_id),
                    defaults={
                        "chosen_option_index": chosen,
                        "is_correct": is_correct,
                        "answered_at": make_aware(datetime.now()), 
                    },
                )
                print("[poll_answer] saved:", {"id": obj.id, "created": created, "is_correct": obj.is_correct})
                return Response({"data": {"status": "answer_recorded", "correct": is_correct}}, status=200)

            except Exception as e:
                import traceback; traceback.print_exc()
                return Response({"data": {"status": "exception", "detail": str(e)}}, status=200)
        

        if text == "/bind":
            chat_type = chat.get("type")
            if chat_type not in ("group", "supergroup"):
                return Response({"data": {"status": "bad_request"}}, status=status.HTTP_200_OK)

            chat_title = chat.get("title") or ""
            try:
                inviter = PollUser.objects.get(telegram_id=sender_id)
            except PollUser.DoesNotExist:
                safe_send_message(
                    chat_id,
                    "⚠️ Você ainda não conectou sua conta.\n\n"
                    "👉 No chat privado com o bot, gere seu link no app e depois use:\n"
                    "/start <token>"
                )
                return Response({"data": {"status": "user_not_linked"}}, status=status.HTTP_200_OK)

            group, _ = Group.objects.get_or_create(
                chat_id=str(chat_id),
                defaults={"title": chat_title},
            )
            if chat_title and group.title != chat_title:
                group.title = chat_title
                group.save(update_fields=["title"])

            PollUserGroup.objects.get_or_create(
                poll_user=inviter,
                group=group,
            )

            safe_send_message(
            chat_id,
            f"✅ Sucesso! O grupo {chat_title or chat_id} foi vinculado à sua conta no Knowledge Check Bot! 🤖🎉"
            )
            return Response({"data": {"status": "bound"}}, status=status.HTTP_200_OK)

        return Response({"data": {"status": "ok"}}, status=status.HTTP_200_OK)


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
                    "message": "Erro na validação dos dados.",
                    "errors": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data['chatId']
        # formato esperado: [{"question": str, "options": [str, ...], "correct_option_id": int}, ...]
        questions = serializer.validated_data['questions']
        schedule_date = serializer.validated_data.get('schedule_date')
        schedule_time = serializer.validated_data.get('schedule_time')

        # 1) cria o pacote do quiz
        quiz = Quiz.objects.create(
            creator=request.user,
            title=f"Quiz de {request.user.name or request.user.email}"
        )

        # 2) Se agendado → enfileira a task com a NOVA assinatura
        if schedule_date and schedule_time:
            try:
                eta_dt = make_aware(datetime.combine(schedule_date, schedule_time))
                # >>> task agora recebe (quiz_id, chat_id, questions)
                send_quiz_task.apply_async((quiz.id, chat_id, questions), eta=eta_dt)

                return Response({
                    "data": {
                        "success": True,
                        "message": f"Quiz agendado para {eta_dt.strftime('%d/%m/%Y %H:%M')}.",
                        "quiz": {"id": quiz.id, "title": quiz.title}
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "data": {
                        "success": False,
                        "message": "Erro ao agendar envio do quiz.",
                        "errors": str(e)
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3) Envio imediato: envia cada pergunta agora e grava tudo
        created_questions = []
        failed = []

        for idx, q in enumerate(questions):
            text = q["question"]
            options = q["options"]
            # aceita tanto correct_option_id quanto correctOption (compat)
            correct_idx = q.get("correct_option_id", q.get("correctOption"))

            try:
                tg_resp = requests.post(f"{TELEGRAM_API}/sendPoll", json={
                    "chat_id": chat_id,
                    "question": text,
                    "options": options,
                    "type": "quiz",
                    "correct_option_id": correct_idx,
                    "is_anonymous": False,
                }, timeout=20)

                if tg_resp.status_code != 200:
                    failed.append({
                        "index": idx,
                        "question": text,
                        "status": "error",
                        "error": tg_resp.text,
                    })
                    continue

                result = tg_resp.json().get("result", {})
                message_id = result.get("message_id")
                poll_obj = result.get("poll") or {}
                telegram_poll_id = poll_obj.get("id")  # se não vier, webhook 'poll' fará o backfill

                # cria QuizQuestion
                qq = QuizQuestion.objects.create(
                    quiz=quiz,
                    text=text,
                    correct_option_index=correct_idx,
                    telegram_poll_id=telegram_poll_id
                )

                # cria opções
                for o_idx, opt in enumerate(options):
                    QuizOption.objects.create(question=qq, option_index=o_idx, text=opt)

                # registra mensagem
                if message_id is not None:
                    QuizMessage.objects.create(
                        question=qq,
                        chat_id=str(chat_id),   
                        message_id=message_id
                    )

                created_questions.append(qq.id)

            except requests.RequestException as e:
                failed.append({
                    "index": idx,
                    "question": text,
                    "status": "error",
                    "error": str(e),
                })

        if not created_questions and failed:
            return Response({
                "data": {
                    "success": False,
                    "message": "Falha ao enviar todas as perguntas do quiz.",
                    "errors": failed
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": {
                "success": True,
                "message": f"{len(created_questions)} perguntas enviadas."
                           + (f" {len(failed)} falharam." if failed else ""),
                "quiz": {"id": quiz.id, "title": quiz.title},
                "question_ids": created_questions,
                "failed": failed
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
        qs = (PollUserGroup.objects
              .filter(poll_user=request.user)
              .select_related('group')
              .order_by('-bind_date'))
        data = UserGroupListItemSerializer(qs, many=True).data
        return Response({"data": {"success": True, "groups": data}}, status=status.HTTP_200_OK)
    

class QuizDashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        my_quizzes = Quiz.objects.filter(creator=request.user)
        total_quizzes = my_quizzes.count()
        total_questions = QuizQuestion.objects.filter(quiz__in=my_quizzes).count()
        total_answers = QuizAnswer.objects.filter(question__quiz__in=my_quizzes).count()
        participants = (QuizAnswer.objects
                        .filter(question__quiz__in=my_quizzes)
                        .values("telegram_user_id").distinct().count())
        accuracy = 0.0
        correct = QuizAnswer.objects.filter(question__quiz__in=my_quizzes, is_correct=True).count()
        if total_answers:
            accuracy = round(100.0 * correct / total_answers, 2)
        return Response({
            "data": {
                "total_quizzes": total_quizzes,
                "total_questions": total_questions,
                "total_answers": total_answers,
                "participants": participants,
                "accuracy": accuracy
            }
        }, status=200)
    

class QuizDashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        my_quizzes = Quiz.objects.filter(creator=request.user)
        total_quizzes = my_quizzes.count()
        total_questions = QuizQuestion.objects.filter(quiz__in=my_quizzes).count()

        answers_qs = QuizAnswer.objects.filter(question__quiz__in=my_quizzes)

        agg = answers_qs.aggregate(
            total_answers=Count('id'),
            correct_answers=Count('id', filter=Q(is_correct=True)),
            incorrect_answers=Count('id', filter=Q(is_correct=False)),
            participants=Count('telegram_user_id', distinct=True),
        )

        total_answers = agg['total_answers'] or 0
        correct = agg['correct_answers'] or 0
        incorrect = agg['incorrect_answers'] or 0
        participants = agg['participants'] or 0

        accuracy = round(100.0 * correct / total_answers, 2) if total_answers else 0.0

        return Response({
            "data": {
                "total_quizzes": total_quizzes,
                "total_questions": total_questions,
                "total_answers": total_answers,
                "participants": participants,
                "correct_answers": correct,
                "incorrect_answers": incorrect,
                "accuracy": accuracy
            }
        }, status=200)
    
    
class QuizResponsesPerDayView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        qs = (QuizAnswer.objects
              .filter(question__quiz__creator=request.user)
              .annotate(day=TruncDate("answered_at"))
              .values("day")
              .annotate(responses=Count("id"))
              .order_by("day"))
        return Response({"data": list(qs)}, status=200)
    

class QuizLastActivitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10

        rows = (
            QuizQuestion.objects
            .filter(quiz__creator=request.user)
            .annotate(
                total_answers=Count("answers"),
                correct_answers=Count("answers", filter=Q(answers__is_correct=True)),
                incorrect_answers=Count("answers", filter=Q(answers__is_correct=False)),
                participants=Count("answers__telegram_user_id", distinct=True),
            )
            .order_by("-created_at")[:limit]
        )

        data = []
        for q in rows:
            total = q.total_answers or 0
            correct = q.correct_answers or 0
            incorrect = q.incorrect_answers or 0
            accuracy = round(100.0 * correct / total, 2) if total else 0.0

            data.append({
                "question_id": q.id,
                "question": q.text,
                "created_at": q.created_at,
                "answers": total,
                "correct_answers": correct,
                "incorrect_answers": incorrect,
                "accuracy": accuracy,
                "participants": q.participants or 0,
            })

        return Response({"data": data}, status=200)


class QuizQuestionStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, question_id: int):
        try:
            q = QuizQuestion.objects.select_related("quiz__creator").get(id=question_id, quiz__creator=request.user)
        except QuizQuestion.DoesNotExist:
            return Response({"message": "Not found"}, status=404)

        total = q.answers.count()
        correct = q.answers.filter(is_correct=True).count()
        accuracy = round(100.0 * correct / total, 2) if total else 0.0

        # distribuição por opção
        by_opt = (QuizAnswer.objects
                  .filter(question=q)
                  .values("chosen_option_index")
                  .annotate(count=Count("id"))
                  .order_by("chosen_option_index"))
        options = []
        opt_map = {o.option_index: o.text for o in q.options.all()}
        for row in by_opt:
            idx = row["chosen_option_index"]
            options.append({
                "option_index": idx,
                "text": opt_map.get(idx, f"Opção {idx}"),
                "count": row["count"],
                "is_correct": (idx == q.correct_option_index),
            })

        return Response({
            "data": {
                "question_id": q.id,
                "text": q.text,
                "total_answers": total,
                "accuracy": accuracy,
                "options": options,
            }
        }, status=200)
