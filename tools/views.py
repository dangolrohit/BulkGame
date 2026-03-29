from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from tools.models import Tool
from tools.visibility import tools_visible_to_users, user_can_use_tool


@login_required
def tool_list(request):
    if getattr(request.user, "is_admin_role", False):
        return render(request, "tools/admin_note.html")
    tools = tools_visible_to_users()
    items = []
    for t in tools:
        items.append(
            {
                "tool": t,
                "can_use": user_can_use_tool(request.user, t),
            }
        )
    return render(request, "tools/list.html", {"items": items})


@login_required
def facebook_bulk_remover(request, slug="facebook-bulk-post-remover"):
    if getattr(request.user, "is_admin_role", False):
        raise Http404()
    tool = get_object_or_404(Tool, slug=slug)
    if not tool.is_published or tool.is_hidden:
        raise Http404()
    can_use = user_can_use_tool(request.user, tool)
    from channels.models import FacebookPage

    pages = FacebookPage.objects.filter(user=request.user).order_by("page_name")
    return render(
        request,
        "tools/facebook_bulk_remover.html",
        {
            "tool": tool,
            "can_use": can_use,
            "pages": pages,
        },
    )
