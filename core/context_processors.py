def _nav_section(path: str) -> str:
    if path.startswith("/tools"):
        return "tools"
    if path.startswith("/channels"):
        return "channel"
    if path.startswith("/billing"):
        return "billing"
    if path.startswith("/settings"):
        return "settings"
    if path.startswith("/dashboard"):
        return "dashboard"
    return "dashboard"


def _admin_nav_section(path: str) -> str:
    if path.startswith("/admin-panel/credit-requests"):
        return "credit_requests"
    if path.startswith("/admin-panel/users"):
        return "users"
    if path.startswith("/admin-panel/tools"):
        return "tools"
    if path.startswith("/admin-panel/audit"):
        return "audit"
    if path.startswith("/admin-panel/settings"):
        return "settings"
    if path.startswith("/admin-panel"):
        return "dashboard"
    return "dashboard"


def navigation(request):
    user = getattr(request, "user", None)
    path = getattr(request, "path", "") or ""
    is_admin = bool(
        user and user.is_authenticated and getattr(user, "is_admin_role", False)
    )
    show_user_sidenav = bool(
        user and user.is_authenticated and not is_admin
    )
    return {
        "nav_is_admin": is_admin,
        "nav_user_sidenav": show_user_sidenav,
        "nav_section": _nav_section(path),
        "nav_admin_section": _admin_nav_section(path) if is_admin else "",
    }
