from django.conf import settings
from django.db import models


class FacebookPostCache(models.Model):
    page = models.ForeignKey(
        "channels.FacebookPage",
        on_delete=models.CASCADE,
        related_name="cached_posts",
    )
    post_id = models.CharField(max_length=64)
    message = models.TextField(blank=True)
    image_url = models.URLField(max_length=1024, blank=True)
    permalink_url = models.URLField(max_length=1024, blank=True)
    created_time = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    cached_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fb_remover_facebookpostcache"
        unique_together = [["page", "post_id"]]
        ordering = ["-created_time"]

    def __str__(self):
        return self.post_id


class DeleteJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delete_jobs",
    )
    page = models.ForeignKey(
        "channels.FacebookPage",
        on_delete=models.CASCADE,
        related_name="delete_jobs",
    )
    tool = models.ForeignKey(
        "tools.Tool",
        on_delete=models.PROTECT,
        related_name="delete_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    requested_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    credits_reserved = models.PositiveIntegerField(default=0)
    credits_used = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fb_remover_deletejob"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job {self.pk} ({self.status})"


class DeleteJobItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    job = models.ForeignKey(
        DeleteJob,
        on_delete=models.CASCADE,
        related_name="items",
    )
    post = models.ForeignKey(
        FacebookPostCache,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delete_job_items",
    )
    facebook_post_id = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)
    credit_charged = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "fb_remover_deletejobitem"
        ordering = ["id"]

    def __str__(self):
        return f"{self.facebook_post_id} ({self.status})"
