from django.contrib import admin
from .models import PollUser

@admin.register(PollUser)
class PollUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "telegram_id", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name", "telegram_id")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)