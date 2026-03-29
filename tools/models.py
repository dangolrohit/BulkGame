from django.conf import settings
from django.db import models


class Tool(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=128)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_in_maintenance = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tools_tool"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def is_usable_by_users(self) -> bool:
        return self.is_published and not self.is_hidden and not self.is_in_maintenance


class UserToolAccess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tool_access",
    )
    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="user_access",
    )
    is_enabled = models.BooleanField(default=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tool_access_granted",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tools_usertoolaccess"
        unique_together = [["user", "tool"]]

    def __str__(self):
        return f"{self.user_id} → {self.tool.slug}"
