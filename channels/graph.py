from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings


def _get_json(url: str, *, params: dict | None = None) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=30)
    except requests.RequestException as exc:
        raise OSError("Network error calling Facebook") from exc
    data = response.json()
    if response.status_code != 200:
        err = data.get("error") or {}
        msg = err.get("message", "Graph API error.")
        code = err.get("code", "")
        raise ValueError(f"{msg}" + (f" (code {code})" if code else ""))
    return data


def graph_me(access_token: str) -> dict[str, Any]:
    """
    Validate token and return user fields from Graph API /me.
    """
    version = settings.FACEBOOK_GRAPH_API_VERSION
    url = f"https://graph.facebook.com/{version}/me"
    params = {
        "fields": "id,name,email",
        "access_token": access_token,
    }
    data = _get_json(url, params=params)
    return {
        "id": str(data.get("id", "")),
        "name": data.get("name") or "",
        "email": data.get("email") or "",
    }


def graph_fetch_managed_pages(user_access_token: str) -> list[dict[str, Any]]:
    """
    Pages the user can manage (requires pages_show_list on the user token).
    Tries richer fields first, then falls back to id,name,access_token only.
    """
    version = settings.FACEBOOK_GRAPH_API_VERSION
    base = f"https://graph.facebook.com/{version}/me/accounts"
    field_sets = (
        "id,name,access_token,fan_count,picture{url}",
        "id,name,access_token,fan_count",
        "id,name,access_token",
    )
    last_err: Exception | None = None
    for field_str in field_sets:
        params = {
            "fields": field_str,
            "access_token": user_access_token,
            "limit": 100,
        }
        out: list[dict[str, Any]] = []
        next_url: str | None = base
        first = True
        try:
            while next_url:
                if first:
                    data = _get_json(next_url, params=params)
                    first = False
                else:
                    data = _get_json(next_url)
                for item in data.get("data") or []:
                    out.append(item)
                next_url = (data.get("paging") or {}).get("next")
            return out
        except ValueError as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    return []


def graph_fetch_page_feed(
    page_id: str,
    page_access_token: str,
    *,
    max_posts: int = 200,
) -> list[dict[str, Any]]:
    """
    Published posts for a Page (page access token + pages_read_engagement or compatible perms).
    """
    version = settings.FACEBOOK_GRAPH_API_VERSION
    field_sets = (
        "id,message,created_time,permalink_url,full_picture",
        "id,message,created_time,permalink_url",
    )
    last_err: Exception | None = None
    for fields in field_sets:
        initial_params = {
            "fields": fields,
            "access_token": page_access_token,
            "limit": min(100, max_posts),
        }
        query = urlencode(initial_params)
        next_url: str | None = f"https://graph.facebook.com/{version}/{page_id}/feed?{query}"
        out: list[dict[str, Any]] = []
        try:
            while next_url and len(out) < max_posts:
                data = _get_json(next_url)
                for item in data.get("data") or []:
                    out.append(item)
                    if len(out) >= max_posts:
                        break
                next_url = (data.get("paging") or {}).get("next")
            return out
        except ValueError as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    return []


def graph_delete_object(object_id: str, access_token: str) -> tuple[bool, str]:
    """
    DELETE a Graph object (e.g. a Page feed post). Token must include permission to remove it
    (e.g. pages_manage_posts for Page content).
    """
    version = settings.FACEBOOK_GRAPH_API_VERSION
    url = f"https://graph.facebook.com/{version}/{object_id}"
    params = {"access_token": access_token}
    try:
        response = requests.delete(url, params=params, timeout=30)
    except requests.RequestException:
        return False, "Network error calling Facebook"
    try:
        data = response.json()
    except ValueError:
        return False, (response.text or "Invalid response")[:300]

    if response.status_code == 204:
        return True, ""
    if response.status_code == 200:
        if data is True:
            return True, ""
        if isinstance(data, dict) and data.get("success") is True:
            return True, ""

    if not isinstance(data, dict):
        return False, str(data)[:300]

    err = data.get("error") or {}
    msg = err.get("message", "Delete failed")
    code = err.get("code")
    if code is not None:
        msg = f"{msg} (code {code})"
    return False, msg
