from django.contrib import admin

from tools.models import Tool, UserToolAccess


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_published", "is_hidden", "is_in_maintenance", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserToolAccess)
class UserToolAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "tool", "is_enabled", "granted_by", "created_at")
    list_filter = ("is_enabled",)
