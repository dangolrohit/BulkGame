from django.core.management.base import BaseCommand

from accounts.models import CustomUser


class Command(BaseCommand):
    help = (
        "Create or reset the root admin account for BulkGame (email root@bulkdel.local, password admin). "
        "Change the password in production."
    )

    def handle(self, *args, **options):
        email = "root@bulkdel.local"
        password = "admin"
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "full_name": "root",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not created:
            user.full_name = "root"
            user.role = "admin"
            user.is_staff = True
            user.is_superuser = True
        user.set_password(password)
        user.is_active = True
        user.deleted_at = None
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Root admin ready. Log in with email: {email}  password: {password}"
            )
        )
