from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class SoftDeletedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.deleted_at is not None:
            logout(request)
            return redirect(reverse("core:home"))
        return self.get_response(request)
