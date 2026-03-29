from django.conf import settings
from django.db import models

from .crypto import decrypt_token, encrypt_token


class FacebookConnection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="facebook_connections",
    )
    facebook_user_id = models.CharField(max_length=64)
    _access_token = models.TextField(db_column="access_token")
    refresh_metadata = models.JSONField(default=dict, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "channels_facebookconnection"
        ordering = ["-connected_at"]

    def __str__(self):
        return f"FB {self.facebook_user_id} ({self.user_id})"

    @property
    def access_token(self) -> str:
        return decrypt_token(self._access_token)

    @access_token.setter
    def access_token(self, value: str) -> None:
        self._access_token = encrypt_token(value)


class FacebookPage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="facebook_pages",
    )
    connection = models.ForeignKey(
        FacebookConnection,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    page_id = models.CharField(max_length=64)
    page_name = models.CharField(max_length=512)
    page_image_url = models.URLField(max_length=1024, blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    posts_count = models.PositiveIntegerField(default=0)
    _page_access_token = models.TextField(db_column="page_access_token")
    is_selected_default = models.BooleanField(default=False)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "channels_facebookpage"
        unique_together = [["connection", "page_id"]]
        ordering = ["page_name"]

    def __str__(self):
        return self.page_name

    @property
    def page_access_token(self) -> str:
        return decrypt_token(self._page_access_token)

    @page_access_token.setter
    def page_access_token(self, value: str) -> None:
        self._page_access_token = encrypt_token(value)
