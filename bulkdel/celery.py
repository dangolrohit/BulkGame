import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bulkdel.settings")

app = Celery("bulkdel")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
