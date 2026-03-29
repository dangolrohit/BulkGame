from django.conf import settings
from django.db import models


class CreditWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="credit_wallet",
    )
    balance = models.PositiveIntegerField(default=0)
    lifetime_added = models.PositiveIntegerField(default=0)
    lifetime_used = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_creditwallet"

    def __str__(self):
        return f"Wallet {self.user_id}: {self.balance}"


class CreditTransaction(models.Model):
    class TransactionType(models.TextChoices):
        SIGNUP_BONUS = "signup_bonus", "Signup bonus"
        TOPUP = "topup", "Top-up"
        USAGE = "usage", "Usage"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="credit_transactions",
    )
    transaction_type = models.CharField(
        max_length=32,
        choices=TransactionType.choices,
    )
    amount = models.IntegerField(
        help_text="Positive for credit added, negative for usage.",
    )
    balance_before = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_transactions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_credittransaction"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} → {self.balance_after}"


class CreditRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="credit_requests",
    )
    requested_amount = models.PositiveIntegerField()
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_requests_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_creditrequest"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CreditRequest {self.pk} ({self.status})"
