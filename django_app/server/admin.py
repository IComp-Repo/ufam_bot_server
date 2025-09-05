from django.contrib import admin
from django.db.models import Count, Q, F
from .models import(
    PollUser,
    TelegramLinkToken,
    Group,
    PollUserGroup,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizMessage,
    QuizAnswer,
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

# -----------------------

class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 0
    fields = ("option_index", "text")
    ordering = ("option_index",)

class QuizMessageInline(admin.TabularInline):
    model = QuizMessage
    extra = 0
    fields = ("chat_id", "message_id", "sent_at")
    readonly_fields = ("sent_at",)
    ordering = ("-sent_at",)

class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    fields = ("telegram_user_id", "chosen_option_index", "is_correct", "answered_at")
    readonly_fields = ("answered_at",)
    ordering = ("-answered_at",)
    raw_id_fields = ()
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "creator", "created_at",
                    "questions_count", "answers_count")
    list_filter = (
        ("creator", admin.RelatedOnlyFieldListFilter),
        "created_at",
    )
    search_fields = ("title", "creator__email", "creator__username", "creator__name")
    date_hierarchy = "created_at"
    raw_id_fields = ("creator",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            questions_count_agg=Count("questions", distinct=True),
            answers_count_agg=Count("questions__answers", distinct=True),
        )

    @admin.display(description="Perguntas")
    def questions_count(self, obj):
        return obj.questions_count_agg

    @admin.display(description="Respostas")
    def answers_count(self, obj):
        return obj.answers_count_agg


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "quiz", "created_at",
                    "total_answers", "correct_answers", "incorrect_answers", "accuracy_pct")
    list_filter = (
        ("quiz", admin.RelatedOnlyFieldListFilter),
        "created_at",
    )
    search_fields = ("text", "quiz__title", "quiz__creator__email", "quiz__creator__username")
    date_hierarchy = "created_at"
    inlines = [QuizOptionInline, QuizMessageInline, QuizAnswerInline]
    raw_id_fields = ("quiz",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            total_answers_agg=Count("answers"),
            correct_answers_agg=Count("answers", filter=Q(answers__is_correct=True)),
            incorrect_answers_agg=Count("answers", filter=Q(answers__is_correct=False)),
        ).select_related("quiz")

    @admin.display(description="Pergunta")
    def short_text(self, obj):
        return (obj.text[:80] + "…") if len(obj.text) > 80 else obj.text

    @admin.display(description="Respostas")
    def total_answers(self, obj):
        return obj.total_answers_agg

    @admin.display(description="Corretas")
    def correct_answers(self, obj):
        return obj.correct_answers_agg

    @admin.display(description="Erradas")
    def incorrect_answers(self, obj):
        return obj.incorrect_answers_agg

    @admin.display(description="Acurácia (%)")
    def accuracy_pct(self, obj):
        tot = obj.total_answers_agg or 0
        if not tot:
            return 0.0
        return round(100.0 * (obj.correct_answers_agg or 0) / tot, 2)


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question_id", "question_text", "telegram_user_id",
                    "chosen_option_index", "option_text", "is_correct", "answered_at")
    list_filter = ("is_correct", "answered_at",
                   ("question", admin.RelatedOnlyFieldListFilter),
                   ("question__quiz", admin.RelatedOnlyFieldListFilter))
    search_fields = ("question__text", "telegram_user_id")
    date_hierarchy = "answered_at"
    raw_id_fields = ("question",)
    ordering = ("-answered_at",)

    @admin.display(description="Pergunta")
    def question_text(self, obj):
        t = obj.question.text
        return (t[:60] + "…") if len(t) > 60 else t

    @admin.display(description="Opção (texto)")
    def option_text(self, obj):
        # pega o texto da opção escolhida (se existir)
        opt = obj.question.options.filter(option_index=obj.chosen_option_index).first()
        return opt.text if opt else f"Opção {obj.chosen_option_index}"

    # Ação util: recalcular is_correct conforme a pergunta
    @admin.action(description="Recalcular 'is_correct' das respostas selecionadas")
    def recalc_is_correct(self, request, queryset):
        updated = 0
        for ans in queryset.select_related("question"):
            should = (ans.chosen_option_index == ans.question.correct_option_index)
            if ans.is_correct != should:
                ans.is_correct = should
                ans.save(update_fields=["is_correct"])
                updated += 1
        self.message_user(request, f"{updated} resposta(s) atualizada(s).")

    actions = ["recalc_is_correct"]


@admin.register(QuizOption)
class QuizOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "option_index", "text")
    list_filter = (("question", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("text", "question__text", "question__quiz__title")
    ordering = ("question", "option_index")
    raw_id_fields = ("question",)


@admin.register(QuizMessage)
class QuizMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "chat_id", "message_id", "sent_at")
    list_filter = (("question", admin.RelatedOnlyFieldListFilter), "sent_at")
    search_fields = ("chat_id", "message_id", "question__text", "question__quiz__title")
    date_hierarchy = "sent_at"
    ordering = ("-sent_at",)
    raw_id_fields = ("question",)