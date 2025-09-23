from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from datetime import UTC

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/audit", tags=["audit"])

    @router.get("")
    async def list_events(
        req: Request,
        limit: int = Query(default=100, ge=1, le=1000),
        actions: list[str] | None = Query(default=None),
        action: str | None = Query(default=None),
        actor_id: str | None = Query(default=None),
        date_from: str | None = Query(default=None, alias="from"),
        date_to: str | None = Query(default=None, alias="to"),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        c = get_container(req)
        # Support single 'action' or multiple 'actions'. If single contains comma, split.
        acts = list(actions or [])
        if action:
            parts = [p.strip() for p in str(action).split(",") if p.strip()]
            acts.extend(parts)
        items = await c.audit.repo.list(
            limit=int(limit),
            actions=acts or None,
            actor_id=actor_id,
            date_from=date_from,
            date_to=date_to,
        )
        # Normalize timestamp field for clients that expect 'created_at'
        from datetime import datetime

        normalized: list[dict[str, Any]] = []
        for r in items:
            if "created_at" in r and r.get("created_at") is not None:
                normalized.append(r)
                continue
            ts = r.get("ts")
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(float(ts) / 1000.0, tz=UTC)
                r = {**r, "created_at": dt.isoformat()}
            normalized.append(r)
        return {"items": normalized}

    @router.post("")
    @router.post(
        "",
        dependencies=([Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []),
    )
    async def log_event(
        req: Request,
        payload: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        p = payload or {}
        await c.audit.service.log(
            actor_id=p.get("actor_id"),
            action=str(p.get("action", "")),
            resource_type=p.get("resource_type"),
            resource_id=p.get("resource_id"),
            before=p.get("before"),
            after=p.get("after"),
            ip=p.get("ip"),
            user_agent=p.get("user_agent"),
            reason=p.get("reason"),
            extra=p.get("extra"),
        )
        return {"ok": True}

    return router
