from django.contrib import admin

from billing.models import CreditRequest, CreditTransaction, CreditWallet


@admin.register(CreditWallet)
class CreditWalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "lifetime_added", "lifetime_used", "updated_at")
    search_fields = ("user__email",)


@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "requested_amount",
        "status",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status",)
    search_fields = ("user__email", "message", "admin_note")
    readonly_fields = ("created_at", "reviewed_at")


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "balance_after", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__email", "note")
    readonly_fields = ("created_at",)
