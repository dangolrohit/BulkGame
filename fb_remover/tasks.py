from celery import shared_task
from django.db import transaction
from django.utils import timezone

from billing.services import charge_credit_for_successful_delete
from channels.graph import graph_delete_object
from fb_remover.models import DeleteJob, DeleteJobItem, FacebookPostCache


@shared_task
def process_delete_job(job_id: int):
    job = DeleteJob.objects.select_related("user", "page", "tool").get(pk=job_id)
    job.status = DeleteJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    page = job.page
    page_token = page.page_access_token

    success = 0
    failed = 0
    charged = 0

    for item in job.items.select_related("post").all():
        ok, err_msg = graph_delete_object(item.facebook_post_id, page_token)
        item.processed_at = timezone.now()
        if ok:
            item.status = DeleteJobItem.Status.SUCCESS
            item.credit_charged = True
            item.error_message = ""
            item.save(
                update_fields=[
                    "status",
                    "credit_charged",
                    "processed_at",
                    "error_message",
                ],
            )
            try:
                with transaction.atomic():
                    charge_credit_for_successful_delete(
                        job.user,
                        note=f"Delete job #{job.pk} post {item.facebook_post_id}",
                    )
                charged += 1
                success += 1
                FacebookPostCache.objects.filter(
                    page=page, post_id=item.facebook_post_id
                ).update(is_deleted=True, deleted_at=timezone.now())
            except ValueError:
                item.status = DeleteJobItem.Status.FAILED
                item.error_message = "Insufficient credits during processing"
                item.credit_charged = False
                item.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "credit_charged",
                        "processed_at",
                    ],
                )
                failed += 1
        else:
            item.status = DeleteJobItem.Status.FAILED
            item.error_message = err_msg[:2000] if err_msg else "Delete failed"
            item.save(
                update_fields=["status", "error_message", "processed_at"],
            )
            failed += 1

    job.success_count = success
    job.failed_count = failed
    job.credits_used = charged
    job.finished_at = timezone.now()
    if failed == 0:
        job.status = DeleteJob.Status.COMPLETED
    elif success == 0:
        job.status = DeleteJob.Status.FAILED
    else:
        job.status = DeleteJob.Status.PARTIAL
    job.save(
        update_fields=[
            "success_count",
            "failed_count",
            "credits_used",
            "finished_at",
            "status",
        ],
    )
