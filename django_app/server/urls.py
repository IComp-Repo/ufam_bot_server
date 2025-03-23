from rest_framework.routers import DefaultRouter
from .views import UserViewSet, QuizViewSet, ClassroomViewSet, ProfessorViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'quiz', QuizViewSet, basename='quiz')
router.register(r'classroom', ClassroomViewSet, basename='classroom')
router.register(r'professor', ProfessorViewSet, basename='professor')

urlpatterns = router.urls
