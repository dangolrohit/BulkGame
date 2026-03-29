from django.urls import path

from adminpanel import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="user_list"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/topup/", views.user_topup, name="user_topup"),
    path("users/<int:pk>/delete/", views.user_soft_delete, name="user_delete"),
    path("tools/", views.tool_list, name="tool_list"),
    path("tools/<int:pk>/edit/", views.tool_edit, name="tool_edit"),
    path("tools/<int:pk>/publish/", views.tool_publish, name="tool_publish"),
    path("tools/<int:pk>/hide/", views.tool_hide, name="tool_hide"),
    path("tools/<int:pk>/maintenance/", views.tool_maintenance, name="tool_maintenance"),
    path("credit-requests/", views.credit_requests_list, name="credit_requests"),
    path(
        "credit-requests/<int:pk>/decide/",
        views.credit_request_decide,
        name="credit_request_decide",
    ),
    path("audit/", views.audit_list, name="audit_list"),
    path("settings/", views.settings_view, name="settings"),
]
