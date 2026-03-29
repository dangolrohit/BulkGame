from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_role_required
from accounts.models import CustomUser
from accounts.settings_service import flash_settings_messages, process_account_settings_post
from auditlog.models import AuditLog
from auditlog.services import log_action
from billing.models import CreditRequest, CreditTransaction, CreditWallet
from billing.services import add_credits, get_or_create_wallet
from fb_remover.models import DeleteJob
from tools.models import Tool


@login_required
@admin_role_required
def dashboard(request):
    total_users = CustomUser.objects.filter(deleted_at__isnull=True).count()
    active_users = CustomUser.objects.filter(
        deleted_at__isnull=True, is_active=True
    ).count()
    credits_added = CreditWallet.objects.aggregate(s=Sum("lifetime_added"))["s"] or 0
    credits_used = CreditWallet.objects.aggregate(s=Sum("lifetime_used"))["s"] or 0
    posts_deleted = DeleteJob.objects.aggregate(s=Sum("success_count"))["s"] or 0
    tools_summary = Tool.objects.all()
    recent_audit = AuditLog.objects.select_related("actor", "target_user")[:15]

    return render(
        request,
        "adminpanel/dashboard.html",
        {
            "total_users": total_users,
            "active_users": active_users,
            "credits_added": credits_added,
            "credits_used": credits_used,
            "posts_deleted": posts_deleted,
            "tools_summary": tools_summary,
            "recent_audit": recent_audit,
        },
    )


@login_required
@admin_role_required
def user_list(request):
    rows = []
    for u in CustomUser.objects.filter(deleted_at__isnull=True).order_by("-date_joined"):
        get_or_create_wallet(u)
        wallet = u.credit_wallet
        deleted_posts = (
            DeleteJob.objects.filter(user=u).aggregate(s=Sum("success_count"))["s"] or 0
        )
        rows.append(
            {
                "user": u,
                "credits": wallet.balance,
                "deleted_posts": deleted_posts,
            }
        )
    return render(request, "adminpanel/user_list.html", {"rows": rows})


@login_required
@admin_role_required
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, deleted_at__isnull=True)
    get_or_create_wallet(user)
    wallet = user.credit_wallet
    connections = user.facebook_connections.filter(is_active=True)
    pages = user.facebook_pages.all()[:50]
    jobs = user.delete_jobs.select_related("page", "tool").order_by("-created_at")[:20]
    return render(
        request,
        "adminpanel/user_detail.html",
        {
            "u": user,
            "wallet": wallet,
            "connections": connections,
            "pages": pages,
            "jobs": jobs,
        },
    )


@login_required
@admin_role_required
def user_topup(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, deleted_at__isnull=True)
    get_or_create_wallet(user)
    wallet = user.credit_wallet
    recent = CreditTransaction.objects.filter(
        user=user,
        transaction_type=CreditTransaction.TransactionType.TOPUP,
    )[:10]
    if request.method == "POST":
        try:
            amount = int(request.POST.get("amount", "0"))
        except ValueError:
            amount = 0
        note = request.POST.get("note", "").strip()
        if amount <= 0:
            messages.error(request, "Enter a positive amount.")
        else:
            add_credits(
                user,
                amount,
                transaction_type=CreditTransaction.TransactionType.TOPUP,
                note=note,
                created_by=request.user,
            )
            log_action(
                action="credit_topup",
                actor=request.user,
                target_user=user,
                object_type="CreditTransaction",
                metadata={"amount": amount, "note": note},
            )
            messages.success(request, f"Added {amount} credits.")
            return redirect("adminpanel:user_detail", pk=user.pk)
    return render(
        request,
        "adminpanel/user_topup.html",
        {"u": user, "wallet": wallet, "recent_topups": recent},
    )


@login_required
@admin_role_required
@require_POST
def user_soft_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own account this way.")
        return redirect("adminpanel:user_list")
    user.is_active = False
    user.deleted_at = timezone.now()
    user.save(update_fields=["is_active", "deleted_at"])
    log_action(
        action="user_soft_delete",
        actor=request.user,
        target_user=user,
        object_type="CustomUser",
        object_id=str(user.pk),
    )
    messages.success(request, "User deactivated and soft-deleted.")
    return redirect("adminpanel:user_list")


@login_required
@admin_role_required
def tool_list(request):
    tools = Tool.objects.all().order_by("sort_order", "name")
    return render(request, "adminpanel/tool_list.html", {"tools": tools})


@login_required
@admin_role_required
def tool_edit(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == "POST":
        tool.name = request.POST.get("name", tool.name).strip()
        tool.slug = request.POST.get("slug", tool.slug).strip()
        tool.description = request.POST.get("description", "")
        tool.sort_order = int(request.POST.get("sort_order") or tool.sort_order)
        tool.save()
        log_action(
            action="tool_edit",
            actor=request.user,
            object_type="Tool",
            object_id=str(tool.pk),
            metadata={"slug": tool.slug},
        )
        messages.success(request, "Tool updated.")
        return redirect("adminpanel:tool_list")
    return render(request, "adminpanel/tool_edit.html", {"tool": tool})


@login_required
@admin_role_required
@require_POST
def tool_publish(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    tool.is_published = True
    tool.is_hidden = False
    tool.save(update_fields=["is_published", "is_hidden", "updated_at"])
    log_action(action="tool_publish", actor=request.user, object_type="Tool", object_id=str(tool.pk))
    messages.success(request, "Tool published and visible.")
    return redirect("adminpanel:tool_list")


@login_required
@admin_role_required
@require_POST
def tool_hide(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    tool.is_hidden = True
    tool.save(update_fields=["is_hidden", "updated_at"])
    log_action(action="tool_hide", actor=request.user, object_type="Tool", object_id=str(tool.pk))
    messages.success(request, "Tool hidden from users.")
    return redirect("adminpanel:tool_list")


@login_required
@admin_role_required
@require_POST
def tool_maintenance(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    tool.is_in_maintenance = request.POST.get("enable") == "1"
    tool.save(update_fields=["is_in_maintenance", "updated_at"])
    log_action(
        action="tool_maintenance_toggle",
        actor=request.user,
        object_type="Tool",
        object_id=str(tool.pk),
        metadata={"enabled": tool.is_in_maintenance},
    )
    messages.success(request, "Maintenance flag updated.")
    return redirect("adminpanel:tool_list")


@login_required
@admin_role_required
def credit_requests_list(request):
    pending = (
        CreditRequest.objects.filter(status=CreditRequest.Status.PENDING)
        .select_related("user")
        .order_by("created_at")
    )
    recent_done = (
        CreditRequest.objects.exclude(status=CreditRequest.Status.PENDING)
        .select_related("user", "reviewed_by")
        .order_by("-pk")[:40]
    )
    return render(
        request,
        "adminpanel/credit_requests.html",
        {
            "pending_requests": pending,
            "recent_done": recent_done,
        },
    )


@login_required
@admin_role_required
@require_POST
def credit_request_decide(request, pk):
    cr = get_object_or_404(CreditRequest, pk=pk)
    if cr.status != CreditRequest.Status.PENDING:
        messages.error(request, "This request was already handled.")
        return redirect("adminpanel:credit_requests")

    decision = request.POST.get("decision", "").strip()
    admin_note = (request.POST.get("admin_note") or "").strip()

    if decision == "approve":
        get_or_create_wallet(cr.user)
        add_credits(
            cr.user,
            cr.requested_amount,
            transaction_type=CreditTransaction.TransactionType.TOPUP,
            note=f"Credit request #{cr.pk} approved."
            + (f" User note: {cr.message[:300]}" if cr.message else ""),
            created_by=request.user,
        )
        cr.status = CreditRequest.Status.APPROVED
        cr.reviewed_by = request.user
        cr.reviewed_at = timezone.now()
        cr.admin_note = admin_note
        cr.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "admin_note",
            ],
        )
        log_action(
            action="credit_request_approved",
            actor=request.user,
            target_user=cr.user,
            object_type="CreditRequest",
            object_id=str(cr.pk),
            metadata={"amount": cr.requested_amount},
        )
        messages.success(
            request,
            f"Approved {cr.requested_amount} credits for {cr.user.email}.",
        )
    elif decision == "reject":
        cr.status = CreditRequest.Status.REJECTED
        cr.reviewed_by = request.user
        cr.reviewed_at = timezone.now()
        cr.admin_note = admin_note
        cr.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "admin_note",
            ],
        )
        log_action(
            action="credit_request_rejected",
            actor=request.user,
            target_user=cr.user,
            object_type="CreditRequest",
            object_id=str(cr.pk),
        )
        messages.success(request, "Request rejected.")
    else:
        messages.error(request, "Invalid action.")

    return redirect("adminpanel:credit_requests")


@login_required
@admin_role_required
def audit_list(request):
    logs = AuditLog.objects.select_related("actor", "target_user")[:200]
    return render(request, "adminpanel/audit_list.html", {"logs": logs})


@login_required
@admin_role_required
def settings_view(request):
    profile = request.user.profile
    if request.method == "POST":
        tuples = process_account_settings_post(request, request.user)
        flash_settings_messages(request, tuples)
        return redirect("adminpanel:settings")
    return render(request, "adminpanel/settings.html", {"profile": profile})
