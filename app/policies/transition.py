from __future__ import annotations

from fastapi import HTTPException, status
from app.models.transition import NodeTransition
from app.models.user import User


class TransitionPolicy:
    """Authorization rules for transitions."""

    @staticmethod
    def ensure_can_delete(transition: NodeTransition, user: User) -> None:
        """Only creator or moderator/admin may delete."""
        if transition.created_by == user.id or user.role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this transition",
        )
