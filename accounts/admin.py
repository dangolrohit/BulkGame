from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Soft delete", {"fields": ("deleted_at",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2", "role", "is_staff", "is_superuser"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("last_login", "date_joined")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "timezone")
    search_fields = ("user__email",)
