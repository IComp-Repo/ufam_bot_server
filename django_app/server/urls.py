from rest_framework.routers import DefaultRouter
from .views import UserViewSet, QuizViewSet, ClassroomViewSet, ProfessorViewSet, NotificationViewSet
from django.urls import path

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'quiz', QuizViewSet, basename='quiz')
router.register(r'classroom', ClassroomViewSet, basename='classroom')
router.register(r'professor', ProfessorViewSet, basename='professor')
router.register(r'notification', NotificationViewSet, basename='notification')

# URLs customizadas para deletar && recuperar usuário pelo telegram_id
urlpatterns = [
    path('users/telegram/delete/', 
         UserViewSet.as_view({'delete': 'delete_by_telegram_id'}), 
         name='user-delete-by-telegram'),

    path('users/telegram/<str:telegram_id>/', 
         UserViewSet.as_view({'get': 'retrieve_by_telegram'}), 
         name='user-by-telegram')
] + router.urls
