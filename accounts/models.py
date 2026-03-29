from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, full_name, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=[("user", "User"), ("admin", "Admin")],
        default="user",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def is_admin_role(self) -> bool:
        return self.role == "admin"


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    status = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "accounts_userprofile"

    def __str__(self):
        return f"Profile: {self.user.email}"
