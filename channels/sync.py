from __future__ import annotations

from django.db import transaction

from channels.graph import graph_fetch_managed_pages
from channels.models import FacebookConnection, FacebookPage


def _picture_url(picture: object) -> str:
    if not picture or not isinstance(picture, dict):
        return ""
    direct = picture.get("url")
    if direct:
        return str(direct)[:1024]
    data = picture.get("data")
    if isinstance(data, dict) and data.get("url"):
        return str(data["url"])[:1024]
    return ""


@transaction.atomic
def sync_pages_for_connection(connection: FacebookConnection) -> int:
    """
    Upsert FacebookPage rows for every Page returned by /me/accounts.
    """
    token = connection.access_token
    raw_list = graph_fetch_managed_pages(token)
    user = connection.user
    count = 0
    for item in raw_list:
        pid = str(item.get("id") or "").strip()
        name = (item.get("name") or pid or "Page")[:512]
        page_token = item.get("access_token")
        if not pid or not page_token:
            continue
        try:
            fan = int(item.get("fan_count") or 0)
        except (TypeError, ValueError):
            fan = 0
        pic = _picture_url(item.get("picture"))
        fp, _created = FacebookPage.objects.update_or_create(
            connection=connection,
            page_id=pid,
            defaults={
                "user": user,
                "page_name": name,
                "page_image_url": pic,
                "followers_count": fan,
            },
        )
        fp.page_access_token = page_token
        fp.save()
        count += 1
    return count
