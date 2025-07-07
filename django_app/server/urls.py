from django.urls import path
from .views import RegisterView, LoginView, SendPollView, SendQuizView, TelegramWebhookView, PingView, BindGroupView, UserGroupsView

urlpatterns = [

    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("send-poll/", SendPollView.as_view(), name="send_poll"),
    path('send-quiz/', SendQuizView.as_view(), name='send_quiz'),
    path("bind-group/", BindGroupView.as_view(), name="bind_group"),
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    path("ping/", PingView.as_view(), name="ping"),
    path("user-groups/", UserGroupsView.as_view(), name="user-groups"),
]
