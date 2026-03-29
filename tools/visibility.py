from __future__ import annotations

from tools.models import Tool, UserToolAccess


def tools_visible_to_users():
    return Tool.objects.filter(is_published=True, is_hidden=False).order_by(
        "sort_order", "name"
    )


def user_can_use_tool(user, tool: Tool) -> bool:
    if not tool.is_published or tool.is_hidden or tool.is_in_maintenance:
        return False
    access = UserToolAccess.objects.filter(user=user, tool=tool).first()
    if access is not None and not access.is_enabled:
        return False
    return True
