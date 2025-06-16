# /django_app/server/management/commands/create_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Cria um superusuário a partir de variáveis de ambiente, se ele não existir.'

    def handle(self, *args, **options):
        User = get_user_model()
        # Use a variável de ambiente para o e-mail como identificador principal
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not email or not password:
            self.stdout.write(self.style.ERROR('As variáveis de ambiente DJANGO_SUPERUSER_EMAIL e DJANGO_SUPERUSER_PASSWORD devem ser definidas.'))
            return

        # 1. Busque o usuário pelo EMAIL, não pelo username
        if not User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Criando superusuário para: {email}'))

            # 2. Crie o superusuário usando email e password
            User.objects.create_superuser(
                email=email,
                password=password
            )
        else:
            self.stdout.write(self.style.WARNING(f'Superusuário com email "{email}" já existe.'))