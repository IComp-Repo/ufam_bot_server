from django.urls import path
from .views import RegisterView,LoginView, SendPollView, SendQuizView, TelegramWebhookView, BindGroupView, UserGroupsView, CookieTokenRefreshView, LogoutView

urlpatterns = [
    # Authentication
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("aut/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    # Poll and Quiz
    path("send-poll/", SendPollView.as_view(), name="send_poll"),
    path('send-quiz/', SendQuizView.as_view(), name='send_quiz'),
    path("bind-group/", BindGroupView.as_view(), name="bind_group"),
    path("telegram/webhook/", TelegramWebhookView.as_view(), name="telegram-webhook"),
    path("user-groups/", UserGroupsView.as_view(), name="user-groups"),

]
