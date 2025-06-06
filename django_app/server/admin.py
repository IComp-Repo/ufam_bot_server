from django.contrib import admin
from .models import PollUser

@admin.register(PollUser)
class PollUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'register', 'is_professor')
