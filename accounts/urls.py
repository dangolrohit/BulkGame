from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("settings/", views.user_settings, name="settings"),
]
