from django.urls import path

from fb_remover import views

app_name = "fb_remover"

urlpatterns = [
    path("jobs/queue/", views.queue_delete_job, name="queue_job"),
    path("jobs/<int:job_id>/status/", views.delete_job_status, name="job_status"),
]
