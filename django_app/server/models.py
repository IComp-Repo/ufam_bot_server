import secrets

from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models import( 
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)


class PollUserManager(BaseUserManager):
    def create_user(self, email, telegram_id=None, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, telegram_id=telegram_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)

    def bind_group(self, user, group):
        return PollUserGroup.objects.get_or_create(poll_user=user, group=group)

    def list_groups(self, user):
        return Group.objects.filter(pollusergroup__poll_user=user)


class PollUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True, null=True)

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) #admin user; 
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PollUserManager()

    def __str__(self):
        return self.name or self.email


class Group(models.Model):
    chat_id = models.CharField(unique=True)
    fetch_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)


class PollUserGroup(models.Model):
    poll_user = models.ForeignKey(PollUser, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    bind_date = models.DateTimeField(auto_now_add=True)


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(
        "server.PollUser",              
        on_delete=models.CASCADE,
        related_name="tg_link_tokens",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["token"])]

    def __str__(self):
        st = "used" if self.used_at else "active"
        return f"{self.user_id}:{self.token[:6]}… ({st})"

    @classmethod
    def issue(cls, user, ttl_minutes=15):
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timezone.timedelta(minutes=ttl_minutes),
        )

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    @property
    def is_valid(self):
        return self.used_at is None and timezone.now() <= self.expires_at
    

class Quiz(models.Model):
    """Um conjunto de perguntas (ou 1) enviado por um criador."""
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255, blank=True, default="")  
    created_at = models.DateTimeField(auto_now_add=True)


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=512)
    correct_option_index = models.IntegerField()
    telegram_poll_id = models.CharField(max_length=128, unique=True, null=True, blank=True)  # id do poll (quiz) do Telegram
    created_at = models.DateTimeField(auto_now_add=True)


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    option_index = models.IntegerField()  # posição enviada ao Telegram
    text = models.CharField(max_length=255)

    class Meta:
        unique_together = (("question", "option_index"),)


class QuizMessage(models.Model):
    """Mensagem real (quiz) enviada em um chat."""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="messages")
    chat_id = models.CharField(max_length=64)  
    message_id = models.BigIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("chat_id", "message_id"),)


class QuizAnswer(models.Model):
    """Resposta de um usuário a uma pergunta do quiz."""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="answers")
    telegram_user_id = models.BigIntegerField()
    chosen_option_index = models.IntegerField()
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("question", "telegram_user_id"),)  # 1 resposta por usuário (última sobrescreve)
        indexes = [models.Index(fields=["question", "telegram_user_id"])]
