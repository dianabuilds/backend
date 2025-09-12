from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.kernel.preview import PreviewContext
from app.domains.users.application.nft_service import user_has_nft

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from app.domains.navigation.infrastructure.models.transition_models import (
        NodeTransition,
    )
    from app.domains.users.infrastructure.models.user import User


async def check_transition(
    transition: "NodeTransition",
    user: "User" | None,
    preview: PreviewContext | None = None,
) -> bool:
    """Check whether a user can access a transition based on its condition."""
    cond = transition.condition or {}
    premium_required = cond.get("premium_required")
    if premium_required:
        plan = preview.plan if preview and preview.plan else None
        if plan:
            is_premium = plan == "premium"
        else:
            is_premium = bool(user and user.is_premium)
        if not is_premium:
            return False

    nft_required = cond.get("nft_required")
    if nft_required:
        if not user or not await user_has_nft(user, nft_required):
            return False

    tags = cond.get("tags")
    if tags:
        user_tags = set(getattr(user, "tags", []) or [])
        if not set(tags).issubset(user_tags):
            return False

    cooldown = cond.get("cooldown")
    if cooldown:
        if not user:
            return False
        last_times = getattr(user, "transition_cooldowns", {})
        last = last_times.get(str(transition.id))
        now = preview.now if preview and preview.now else datetime.utcnow()
        if last and (now - last).total_seconds() < cooldown:
            return False

    return True


__all__ = ["check_transition"]

