from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

    @router.get(
        "",
        dependencies=([Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []),
    )
    async def list_my_notifications(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        c = get_container(req)
        import uuid as _uuid

        sub = str(claims.get("sub"))
        # Resolve UUID id if sub is not a UUID (e.g., email in dev)
        user = await c.users.service.get(sub)
        if user:
            user_id = user.id
        else:
            try:
                _uuid.UUID(sub)
                user_id = sub
            except Exception:
                user_id = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{sub}"))
        rows = await c.notifications.repo.list_for_user(
            user_id,
            placement="inbox",
            limit=limit,
            offset=offset,
        )
        items = [_serialize_notification(row) for row in rows]
        unread = sum(1 for item in items if item.get("read_at") is None)
        return {"items": items, "unread": unread}

    @router.post(
        "/read/{notif_id}",
        dependencies=([Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []),
    )
    async def mark_read(
        req: Request,
        notif_id: str,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        import uuid as _uuid

        sub = str(claims.get("sub"))
        user = await c.users.service.get(sub)
        if user:
            user_id = user.id
        else:
            try:
                _uuid.UUID(sub)
                user_id = sub
            except Exception:
                user_id = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{sub}"))
        updated = await c.notifications.repo.mark_read(user_id, notif_id)
        if not updated:
            raise HTTPException(status_code=404, detail="not_found")
        return {"notification": _serialize_notification(updated)}

    # Admin send
    @router.post(
        "/admin/send",
        dependencies=([Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []),
    )
    async def admin_send(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(body.get("user_id") or "")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id_required")
        title = str(body.get("title") or "")
        message = str(body.get("message") or "")
        type_ = str(body.get("type") or "system")
        placement = str(body.get("placement") or "inbox")
        topic_key = body.get("topic_key")
        channel_key = body.get("channel_key")
        priority = str(body.get("priority") or "normal")
        cta_label = body.get("cta_label")
        cta_url = body.get("cta_url")
        raw_meta = body.get("meta")
        event_id = body.get("event_id")

        meta_payload: Mapping[str, Any] | None = None
        if isinstance(raw_meta, Mapping):
            meta_payload = raw_meta
        elif isinstance(raw_meta, str) and raw_meta.strip():
            try:
                meta_payload = json.loads(raw_meta)
            except json.JSONDecodeError:
                meta_payload = None

        dto = await c.notifications.notify.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type_=type_,
            placement=placement,
            topic_key=topic_key,
            channel_key=channel_key,
            priority=priority,
            cta_label=cta_label,
            cta_url=cta_url,
            meta=meta_payload,
            event_id=event_id,
        )
        return {"notification": _serialize_notification(dto)}

    return router


def _serialize_notification(row: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(row)
    for field in ("created_at", "updated_at", "read_at"):
        value = data.get(field)
        if isinstance(value, datetime):
            data[field] = value.isoformat()
    meta = data.get("meta")
    if isinstance(meta, Mapping):
        data["meta"] = dict(meta)
    elif isinstance(meta, str):
        try:
            data["meta"] = json.loads(meta)
        except json.JSONDecodeError:
            data["meta"] = {}
    else:
        data["meta"] = {}
    data["priority"] = str(data.get("priority") or "normal")
    data["is_read"] = data.get("read_at") is not None
    return data
