from __future__ import annotations

from fastapi import HTTPException, status

from app.kernel.preview import PreviewContext
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
)
from app.domains.users.infrastructure.models.user import User


class TransitionPolicy:
    """Authorization rules for transitions."""

    @staticmethod
    def ensure_can_delete(
        transition: NodeTransition,
        user: User,
        preview: PreviewContext | None = None,
    ) -> None:
        """Only creator or moderator/admin may delete."""
        role = preview.role if preview and preview.role else user.role
        if transition.created_by == user.id or role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this transition",
        )

