from django.urls import path

from tools import views

app_name = "tools"

urlpatterns = [
    path("", views.tool_list, name="list"),
    path(
        "facebook-bulk-post-remover/",
        views.facebook_bulk_remover,
        name="facebook_bulk_remover",
    ),
]
