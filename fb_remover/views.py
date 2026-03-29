import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from billing.services import get_or_create_wallet
from channels.models import FacebookPage
from fb_remover.models import DeleteJob, DeleteJobItem, FacebookPostCache
from tools.models import Tool
from tools.visibility import user_can_use_tool


@login_required
@require_POST
def queue_delete_job(request):
    if getattr(request.user, "is_admin_role", False):
        return HttpResponseBadRequest("Not for admin role")
    try:
        payload = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    page_id = payload.get("page_id")
    post_ids = payload.get("post_ids") or []
    tool_slug = payload.get("tool_slug", "facebook-bulk-post-remover")

    if not page_id or not post_ids:
        return HttpResponseBadRequest("page_id and post_ids required")

    tool = get_object_or_404(Tool, slug=tool_slug)
    if not user_can_use_tool(request.user, tool):
        return JsonResponse({"error": "Tool not available"}, status=403)

    page = get_object_or_404(FacebookPage, pk=page_id, user=request.user)

    get_or_create_wallet(request.user)
    wallet = request.user.credit_wallet
    if wallet is None or wallet.balance < len(post_ids):
        return JsonResponse({"error": "Insufficient credits"}, status=400)

    job = DeleteJob.objects.create(
        user=request.user,
        page=page,
        tool=tool,
        requested_count=len(post_ids),
        credits_reserved=len(post_ids),
    )
    for pid in post_ids:
        post = FacebookPostCache.objects.filter(page=page, post_id=str(pid)).first()
        DeleteJobItem.objects.create(
            job=job,
            post=post,
            facebook_post_id=str(pid),
        )

    from fb_remover.tasks import process_delete_job

    if settings.DEBUG:
        process_delete_job.apply(args=[job.id])
    else:
        process_delete_job.delay(job.id)

    return JsonResponse(
        {
            "job_id": job.id,
            "status": "queued",
            "requested_count": job.requested_count,
        },
    )


@login_required
@require_GET
def delete_job_status(request, job_id):
    if getattr(request.user, "is_admin_role", False):
        return JsonResponse({"error": "Forbidden"}, status=403)
    job = get_object_or_404(DeleteJob, pk=job_id, user=request.user)
    agg = job.items.aggregate(
        pending=Count("id", filter=Q(status=DeleteJobItem.Status.PENDING)),
        success=Count("id", filter=Q(status=DeleteJobItem.Status.SUCCESS)),
        failed=Count("id", filter=Q(status=DeleteJobItem.Status.FAILED)),
        skipped=Count("id", filter=Q(status=DeleteJobItem.Status.SKIPPED)),
    )
    req = job.requested_count
    deleted_ok = agg["success"] or 0
    remaining = agg["pending"] or 0
    processed = deleted_ok + (agg["failed"] or 0) + (agg["skipped"] or 0)
    percent = int(round(100 * processed / req)) if req else 100
    return JsonResponse(
        {
            "job_id": job.id,
            "status": job.status,
            "requested_count": req,
            "deleted": deleted_ok,
            "failed": agg["failed"] or 0,
            "skipped": agg["skipped"] or 0,
            "remaining": remaining,
            "processed": processed,
            "percent": min(100, max(0, percent)),
        },
    )
