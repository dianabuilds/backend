from __future__ import annotations

from app.core.preview import PreviewContext
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
)
from app.domains.users.infrastructure.models.user import User


def check_transition(
    transition: NodeTransition,
    user: User | None,
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
    # Placeholder for NFT, tags and cooldown checks
    return True
