from django.urls import path

from billing import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_home, name="home"),
]
