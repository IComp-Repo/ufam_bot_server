import secrets

from django.db import models
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