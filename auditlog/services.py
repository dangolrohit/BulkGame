from __future__ import annotations

from typing import Any

from auditlog.models import AuditLog


def log_action(
    *,
    action: str,
    actor=None,
    target_user=None,
    object_type: str = "",
    object_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id is not None else "",
        metadata_json=metadata or {},
    )
