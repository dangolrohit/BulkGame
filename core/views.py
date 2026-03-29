from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

from billing.models import CreditWallet
from billing.services import get_or_create_wallet
from channels.models import FacebookPage
from fb_remover.models import DeleteJob
from tools.visibility import tools_visible_to_users


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    user = request.user
    if getattr(user, "is_admin_role", False):
        return redirect("adminpanel:dashboard")

    get_or_create_wallet(user)
    wallet = CreditWallet.objects.filter(user=user).first()
    balance = wallet.balance if wallet else 0

    recent_jobs = (
        DeleteJob.objects.filter(user=user)
        .select_related("page", "tool")
        .order_by("-created_at")[:10]
    )
    pages = FacebookPage.objects.filter(user=user).order_by("page_name")[:12]
    tool_list = tools_visible_to_users()

    total_deleted = (
        DeleteJob.objects.filter(user=user).aggregate(s=Sum("success_count"))["s"] or 0
    )

    return render(
        request,
        "core/dashboard_user.html",
        {
            "balance": balance,
            "recent_jobs": recent_jobs,
            "pages": pages,
            "tools": tool_list,
            "total_deleted": total_deleted,
        },
    )
