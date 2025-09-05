from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, cast

from fastapi import Request

PreviewMode = Literal["off", "read_only", "dry_run", "shadow"]


@dataclass
class PreviewContext:
    mode: PreviewMode = "off"
    preview_user: str | None = None
    seed: int | None = None
    now: datetime | None = None
    locale: str | None = None
    role: str | None = None
    plan: str | None = None
    device: str | None = None


async def get_preview_context(request: Request) -> PreviewContext:
    q = request.query_params
    h = request.headers
    raw_mode = q.get("preview_mode") or h.get("X-Preview-Mode") or "off"
    mode_val = raw_mode if raw_mode in {"off", "read_only", "dry_run", "shadow"} else "off"
    preview_user = q.get("preview_user") or h.get("X-Preview-User")
    seed = q.get("preview_seed") or h.get("X-Preview-Seed")
    seed_val = int(seed) if seed is not None else None
    time_str = (
        q.get("preview_now")
        or h.get("X-Preview-Now")
        or q.get("preview_time")
        or h.get("X-Preview-Time")
    )
    time_val = datetime.fromisoformat(time_str) if time_str else None
    locale = q.get("preview_locale") or h.get("X-Preview-Locale")
    role = q.get("preview_role") or h.get("X-Preview-Role")
    plan = q.get("preview_plan") or h.get("X-Preview-Plan")
    device = q.get("preview_device") or h.get("X-Preview-Device")
    return PreviewContext(
        mode=cast(PreviewMode, mode_val),
        preview_user=preview_user,
        seed=seed_val,
        now=time_val,
        locale=locale,
        role=role,
        plan=plan,
        device=device,
    )


__all__ = ["PreviewContext", "PreviewMode", "get_preview_context"]
