from django.urls import path
from .views import RegisterView, LoginView, SendPollView
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("send-poll/", SendPollView.as_view(), name="send_poll")
]
