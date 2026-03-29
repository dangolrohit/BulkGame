from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def admin_role_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("accounts:login"))
        if not getattr(request.user, "is_admin_role", False):
            messages.error(request, "You do not have access to the admin panel.")
            return redirect(reverse("core:dashboard"))
        return view_func(request, *args, **kwargs)

    return _wrapped
