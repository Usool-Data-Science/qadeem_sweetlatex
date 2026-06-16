from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from sweetlatexBE.settings.base import ADMIN_EMAIL, ADMIN_PASSWORD

User = get_user_model()


class Command(BaseCommand):
    help = "Create default admin user if not exists"

    def handle(self, *args, **kwargs):

        if User.objects.filter(email=ADMIN_EMAIL).exists():
            user = User.objects.get(email=ADMIN_EMAIL)
            user.set_password(ADMIN_PASSWORD)
            user.save()
            return

        user = User.objects.create_superuser(email=ADMIN_EMAIL, password=ADMIN_PASSWORD)

        self.stdout.write(
            self.style.SUCCESS(f"Admin user created successfully: {user.email}")
        )
