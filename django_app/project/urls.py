from django.contrib import admin
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path, include
from django.views.generic import TemplateView

schema_view = get_schema_view(
   openapi.Info(
      title="Poll Miniapp API",
      default_version='v1',
      description="API para criação e envio de enquetes via Telegram",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="martinhoprata95@gmail.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path('admin/', admin.site.urls),
    path('api/', include('server.urls')),

    # Swagger UI and Redoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Custom 404 error handler
handler404 = "server.views.custom_404"
