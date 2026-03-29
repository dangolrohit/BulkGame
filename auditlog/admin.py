from django.contrib import admin

from auditlog.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_user", "object_type", "object_id")
    list_filter = ("action",)
    search_fields = ("action", "object_id")
    readonly_fields = ("created_at",)
