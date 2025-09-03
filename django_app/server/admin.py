from django.contrib import admin
from .models import(
    PollUser,
    TelegramLinkToken,
    Group,
    PollUserGroup,
)

@admin.register(PollUser)
class PollUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "telegram_id", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name", "telegram_id")
    list_filter = ("is_active", "is_staff", "is_superuser")
    ordering = ("email",)

@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "created_at", "expires_at", "used_at")
    search_fields = ("token", "user__email", "user__name")
    list_filter = ("used_at",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "chat_id", "fetch_date")
    search_fields = ("title", "chat_id")
    ordering = ("-fetch_date",)

@admin.register(PollUserGroup)
class PollUserGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "poll_user", "group", "bind_date")
    search_fields = ("poll_user__email", "poll_user__name", "group__title", "group__chat_id")
    ordering = ("-bind_date",)