from django.urls import path
from .views import RegisterView, LoginView, SendPollView, TelegramWebhookView
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("send-poll/", SendPollView.as_view(), name="send_poll"),
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),

]
