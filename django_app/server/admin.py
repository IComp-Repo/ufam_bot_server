from django.contrib import admin
from .models import (
    User, Notification, Professor, Student, Classroom,
    ClassroomMember, Quiz, Question, Answer, Tag, Option,
    Response, QuizResult
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'nickname', 'created_at')
    search_fields = ('telegram_id', 'nickname')
    list_filter = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'sent_at')
    search_fields = ('user__nickname', 'message')
    list_filter = ('sent_at',)

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__nickname',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'register')
    search_fields = ('user__nickname', 'register')
    list_filter = ('register',)

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'professor', 'created_at')
    search_fields = ('name', 'professor__user__nickname')
    list_filter = ('created_at',)

@admin.register(ClassroomMember)
class ClassroomMemberAdmin(admin.ModelAdmin):
    list_display = ('class_instance', 'student', 'joined_at')
    search_fields = ('class_instance__name', 'student__user__nickname')
    list_filter = ('joined_at',)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_instance', 'created_by', 'created_at')
    search_fields = ('title', 'class_instance__name', 'created_by__user__nickname')
    list_filter = ('created_at',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'created_at')
    search_fields = ('quiz__title', 'text')
    list_filter = ('created_at',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question')
    search_fields = ('text', 'question__text')
    list_filter = ('question__quiz__title',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('questions',)  # Para seleção múltipla de questões

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('is_correct',)

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'submitted_at')
    search_fields = ('user__nickname', 'question__text', 'selected_option__text')
    list_filter = ('is_correct', 'submitted_at')

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed_at')
    search_fields = ('user__nickname', 'quiz__title')
    list_filter = ('score', 'completed_at')