from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from billing.models import CreditRequest, CreditTransaction
from billing.services import get_or_create_wallet


@login_required
@require_http_methods(["GET", "POST"])
def billing_home(request):
    if getattr(request.user, "is_admin_role", False):
        return render(request, "billing/admin_note.html")

    get_or_create_wallet(request.user)
    wallet = request.user.credit_wallet

    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        if action == "request_credit":
            try:
                amount = int(request.POST.get("requested_amount", "0"))
            except ValueError:
                amount = 0
            msg = (request.POST.get("message") or "").strip()
            if amount < 1:
                messages.error(request, "Enter a valid credit amount (at least 1).")
            else:
                CreditRequest.objects.create(
                    user=request.user,
                    requested_amount=amount,
                    message=msg,
                )
                messages.success(
                    request,
                    "Credit request sent. An admin will review it soon.",
                )
            return redirect("billing:home")

    tx_qs = CreditTransaction.objects.filter(user=request.user)
    paginator = Paginator(tx_qs, 10)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    topups = CreditTransaction.objects.filter(
        user=request.user,
        transaction_type=CreditTransaction.TransactionType.TOPUP,
    )[:10]

    my_requests = CreditRequest.objects.filter(user=request.user)[:25]

    return render(
        request,
        "billing/home.html",
        {
            "wallet": wallet,
            "page_obj": page_obj,
            "transactions": page_obj,
            "topups": topups,
            "my_requests": my_requests,
        },
    )
