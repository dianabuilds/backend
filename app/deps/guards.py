from __future__ import annotations

from app.models.transition import NodeTransition
from app.models.user import User


def check_transition(transition: NodeTransition, user: User) -> bool:
    """Check whether a user can access a transition based on its condition."""
    cond = transition.condition or {}
    if cond.get("premium_required") and not user.is_premium:
        return False
    # Placeholder for NFT, tags and cooldown checks
    return True
