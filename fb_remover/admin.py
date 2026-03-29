from django.contrib import admin

from fb_remover.models import DeleteJob, DeleteJobItem, FacebookPostCache


class DeleteJobItemInline(admin.TabularInline):
    model = DeleteJobItem
    extra = 0
    readonly_fields = ("processed_at",)


@admin.register(DeleteJob)
class DeleteJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "requested_count", "success_count", "failed_count", "created_at")
    list_filter = ("status",)
    inlines = [DeleteJobItemInline]


@admin.register(FacebookPostCache)
class FacebookPostCacheAdmin(admin.ModelAdmin):
    list_display = ("post_id", "page", "is_deleted", "created_time")
    list_filter = ("is_deleted",)
