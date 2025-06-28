from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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


class PollUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    register = models.CharField(max_length=100, unique=True, null=True, blank=True)
    telegram_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_professor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PollUserManager()

    def __str__(self):
        return self.email

class Group(models.Model):
    chat_id = models.BigIntegerField(unique=True)
    fetch_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)

class PollUserGroup(models.Model):
    poll_user = models.ForeignKey(PollUser, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    bind_date = models.DateTimeField(auto_now_add=True)
