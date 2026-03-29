from django.contrib import admin

from channels.models import FacebookConnection, FacebookPage


@admin.register(FacebookConnection)
class FacebookConnectionAdmin(admin.ModelAdmin):
    list_display = ("user", "facebook_user_id", "is_active", "connected_at")
    search_fields = ("user__email", "facebook_user_id")


@admin.register(FacebookPage)
class FacebookPageAdmin(admin.ModelAdmin):
    list_display = ("page_name", "user", "page_id", "synced_at")
    search_fields = ("page_name", "page_id", "user__email")
