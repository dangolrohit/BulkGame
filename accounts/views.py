from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from accounts.forms import AppLoginForm, SignupForm
from accounts.settings_service import flash_settings_messages, process_account_settings_post
from billing.services import grant_signup_bonus


class AppLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AppLoginForm
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


def signup(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            grant_signup_bonus(user)
            login(request, user)
            messages.success(request, "Account created. You received 5 welcome credits.")
            return redirect("core:dashboard")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def user_settings(request):
    if getattr(request.user, "is_admin_role", False):
        return redirect("adminpanel:settings")
    profile = request.user.profile
    if request.method == "POST":
        tuples = process_account_settings_post(request, request.user)
        flash_settings_messages(request, tuples)
        return redirect("accounts:settings")
    return render(request, "accounts/settings.html", {"profile": profile})
