import time
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from channels.graph import graph_fetch_page_feed, graph_me
from channels.models import FacebookConnection, FacebookPage
from channels.sync import sync_pages_for_connection
from fb_remover.models import FacebookPostCache

SESSION_FB_PENDING = "channels_fb_pending"
PENDING_TTL_SECONDS = 600


def _clear_fb_pending(request):
    request.session.pop(SESSION_FB_PENDING, None)


def _get_fb_pending(request):
    raw = request.session.get(SESSION_FB_PENDING)
    if not raw or not isinstance(raw, dict):
        return None
    ts = raw.get("ts") or 0
    if time.time() - ts > PENDING_TTL_SECONDS:
        _clear_fb_pending(request)
        return None
    return raw


@login_required
@require_http_methods(["GET", "POST"])
def channel_home(request):
    if getattr(request.user, "is_admin_role", False):
        return render(request, "channels/admin_note.html")

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        if action == "scan":
            token = request.POST.get("access_token", "").strip()
            if not token:
                messages.error(request, "Paste a user access token first.")
            else:
                try:
                    me = graph_me(token)
                    request.session[SESSION_FB_PENDING] = {
                        "token": token,
                        "facebook_user_id": me["id"],
                        "name": me["name"],
                        "email": me.get("email") or "",
                        "ts": time.time(),
                    }
                    request.session.modified = True
                    messages.success(
                        request,
                        "Token is valid. Graph API returned this Facebook user.",
                    )
                except ValueError as e:
                    _clear_fb_pending(request)
                    messages.error(request, str(e))
                except OSError:
                    _clear_fb_pending(request)
                    messages.error(
                        request,
                        "Could not reach Facebook. Check your network and try again.",
                    )

        elif action == "save":
            pending = _get_fb_pending(request)
            if not pending:
                messages.error(request, "Scan a token again before saving.")
            else:
                token = pending.get("token") or ""
                uid = pending.get("facebook_user_id") or ""
                if not token or not uid:
                    _clear_fb_pending(request)
                    messages.error(request, "Session expired. Scan your token again.")
                else:
                    try:
                        me = graph_me(token)
                        if me["id"] != uid:
                            _clear_fb_pending(request)
                            messages.error(
                                request,
                                "Token no longer matches the scanned user. Scan again.",
                            )
                        else:
                            conn = FacebookConnection.objects.filter(
                                user=request.user,
                                facebook_user_id=uid,
                            ).first()
                            if conn:
                                conn.access_token = token
                                conn.is_active = True
                                conn.save()
                            else:
                                conn = FacebookConnection(
                                    user=request.user,
                                    facebook_user_id=uid,
                                )
                                conn.access_token = token
                                conn.save()
                            _clear_fb_pending(request)
                            try:
                                n = sync_pages_for_connection(conn)
                                if n:
                                    messages.success(
                                        request,
                                        f"Facebook connection saved. Synced {n} page(s).",
                                    )
                                else:
                                    messages.warning(
                                        request,
                                        "Connection saved, but Facebook returned no pages. "
                                        "Your user token needs the pages_show_list permission "
                                        "and must be allowed to see the Pages you manage.",
                                    )
                            except ValueError as e:
                                messages.warning(
                                    request,
                                    f"Connection saved, but listing pages failed: {e}",
                                )
                            except OSError:
                                messages.warning(
                                    request,
                                    "Connection saved, but we could not reach Facebook to list pages.",
                                )
                    except ValueError as e:
                        messages.error(request, str(e))

        elif action == "sync_pages":
            try:
                cid = int(request.POST.get("connection_id", "0"))
            except ValueError:
                cid = 0
            conn = get_object_or_404(
                FacebookConnection,
                pk=cid,
                user=request.user,
                is_active=True,
            )
            try:
                n = sync_pages_for_connection(conn)
                if n:
                    messages.success(request, f"Synced {n} page(s) from Facebook.")
                else:
                    messages.warning(
                        request,
                        "No pages returned. Check pages_show_list on your user token.",
                    )
            except ValueError as e:
                messages.error(request, str(e))
            except OSError:
                messages.error(request, "Could not reach Facebook.")

        elif action == "clear":
            _clear_fb_pending(request)
            messages.info(request, "Cleared pending token from this session.")

        else:
            messages.error(request, "Unknown action.")

        return redirect("channels:home")

    connections = (
        FacebookConnection.objects.filter(user=request.user, is_active=True)
        .annotate(page_count=Count("pages"))
        .order_by("-connected_at")
    )

    pending = _get_fb_pending(request)
    pending_save = pending is not None
    scan_result = None
    if pending:
        scan_result = {
            "id": pending.get("facebook_user_id"),
            "name": pending.get("name") or "",
            "email": pending.get("email") or "",
        }

    return render(
        request,
        "channels/home.html",
        {
            "connections": connections,
            "scan_result": scan_result,
            "pending_save": pending_save,
            "graph_version": settings.FACEBOOK_GRAPH_API_VERSION,
            "pending_ttl_minutes": PENDING_TTL_SECONDS // 60,
        },
    )


@login_required
@require_GET
def facebook_connect(request):
    if getattr(request.user, "is_admin_role", False):
        return redirect("adminpanel:dashboard")
    if not settings.FACEBOOK_APP_ID:
        messages.warning(
            request,
            "Facebook app is not configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in your environment.",
        )
        return redirect("channels:home")
    messages.info(request, "Facebook OAuth will be wired in Phase 2.")
    return redirect("channels:home")


@login_required
@require_GET
def facebook_callback(request):
    messages.info(request, "OAuth callback placeholder — implement token exchange in Phase 2.")
    return redirect("channels:home")


def _parse_fb_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    s = str(value).strip()
    if s.endswith("+0000"):
        s = s[:-5] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@login_required
@require_GET
def my_pages_json(request):
    if getattr(request.user, "is_admin_role", False):
        return JsonResponse({"error": "Forbidden"}, status=403)
    pages = FacebookPage.objects.filter(user=request.user).order_by("page_name")
    return JsonResponse(
        {
            "pages": [
                {
                    "pk": p.pk,
                    "name": p.page_name,
                    "facebook_id": p.page_id,
                }
                for p in pages
            ],
        },
    )


@login_required
@require_GET
def page_posts_json(request):
    if getattr(request.user, "is_admin_role", False):
        return JsonResponse({"error": "Forbidden"}, status=403)
    try:
        page_pk = int(request.GET.get("page", "0"))
    except ValueError:
        return JsonResponse({"error": "Invalid page"}, status=400)
    if page_pk <= 0:
        return JsonResponse({"error": "Missing page"}, status=400)

    page = get_object_or_404(FacebookPage, pk=page_pk, user=request.user)
    days_raw = (request.GET.get("days") or "all").strip().lower()

    allowed_limits = (10, 20, 30, 50, 100)
    try:
        limit = int(request.GET.get("limit", "50"))
    except ValueError:
        limit = 50
    if limit not in allowed_limits:
        limit = 50

    try:
        raw_posts = graph_fetch_page_feed(
            page.page_id,
            page.page_access_token,
            max_posts=limit,
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except OSError:
        return JsonResponse({"error": "Could not reach Facebook."}, status=503)

    now = datetime.now(timezone.utc)
    cutoff: datetime | None = None
    if days_raw != "all":
        try:
            cutoff = now - timedelta(days=int(days_raw))
        except ValueError:
            cutoff = None

    payload: list[dict] = []
    for post in raw_posts:
        ct = _parse_fb_datetime(post.get("created_time"))
        if cutoff is not None and ct is not None and ct < cutoff:
            continue
        pid = post.get("id")
        if not pid:
            continue
        pid = str(pid)
        msg = post.get("message") or ""
        permalink = post.get("permalink_url") or ""
        image = post.get("full_picture") or ""

        FacebookPostCache.objects.update_or_create(
            page=page,
            post_id=pid,
            defaults={
                "message": msg,
                "permalink_url": permalink[:1024] if permalink else "",
                "image_url": image[:1024] if image else "",
                "created_time": ct,
                "is_deleted": False,
                "deleted_at": None,
            },
        )
        payload.append(
            {
                "id": pid,
                "message": msg,
                "created_time": post.get("created_time") or "",
                "permalink_url": permalink,
                "image_url": image,
            },
        )

    return JsonResponse(
        {
            "posts": payload,
            "page_name": page.page_name,
            "limit": limit,
        },
    )
