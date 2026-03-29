from __future__ import annotations

from django.conf import settings
from django.db import transaction
from billing.models import CreditTransaction, CreditWallet


def get_or_create_wallet(user):
    wallet, _ = CreditWallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def grant_signup_bonus(user) -> CreditTransaction | None:
    wallet = get_or_create_wallet(user)
    if CreditTransaction.objects.filter(
        user=user,
        transaction_type=CreditTransaction.TransactionType.SIGNUP_BONUS,
    ).exists():
        return None
    bonus = settings.SIGNUP_CREDIT_BONUS
    before = wallet.balance
    wallet.balance += bonus
    wallet.lifetime_added += bonus
    wallet.save(update_fields=["balance", "lifetime_added", "updated_at"])
    return CreditTransaction.objects.create(
        user=user,
        transaction_type=CreditTransaction.TransactionType.SIGNUP_BONUS,
        amount=bonus,
        balance_before=before,
        balance_after=wallet.balance,
        note="Welcome bonus",
        created_by=None,
    )


@transaction.atomic
def add_credits(
    user,
    amount: int,
    *,
    transaction_type=CreditTransaction.TransactionType.TOPUP,
    note: str = "",
    created_by=None,
) -> CreditTransaction:
    if amount <= 0:
        raise ValueError("Top-up amount must be positive")
    wallet = get_or_create_wallet(user)
    before = wallet.balance
    wallet.balance += amount
    wallet.lifetime_added += amount
    wallet.save(update_fields=["balance", "lifetime_added", "updated_at"])
    return CreditTransaction.objects.create(
        user=user,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=before,
        balance_after=wallet.balance,
        note=note,
        created_by=created_by,
    )


@transaction.atomic
def charge_credit_for_successful_delete(
    user,
    *,
    note: str = "",
    created_by=None,
) -> CreditTransaction:
    get_or_create_wallet(user)
    wallet = CreditWallet.objects.select_for_update().get(user=user)
    if wallet.balance < 1:
        raise ValueError("Insufficient credits")
    before = wallet.balance
    wallet.balance -= 1
    wallet.lifetime_used += 1
    wallet.save(update_fields=["balance", "lifetime_used", "updated_at"])
    return CreditTransaction.objects.create(
        user=user,
        transaction_type=CreditTransaction.TransactionType.USAGE,
        amount=-1,
        balance_before=before,
        balance_after=wallet.balance,
        note=note or "Facebook post delete",
        created_by=created_by,
    )


@transaction.atomic
def refund_credits(
    user,
    amount: int,
    *,
    note: str = "",
    created_by=None,
) -> CreditTransaction:
    if amount <= 0:
        raise ValueError("Refund amount must be positive")
    wallet = CreditWallet.objects.select_for_update().get(user=user)
    before = wallet.balance
    wallet.balance += amount
    wallet.lifetime_used = max(0, wallet.lifetime_used - amount)
    wallet.save(update_fields=["balance", "lifetime_used", "updated_at"])
    return CreditTransaction.objects.create(
        user=user,
        transaction_type=CreditTransaction.TransactionType.REFUND,
        amount=amount,
        balance_before=before,
        balance_after=wallet.balance,
        note=note,
        created_by=created_by,
    )
