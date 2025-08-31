from __future__ import annotations

from fastapi import HTTPException, status

from app.domains.users.infrastructure.models.user import User


class TagPolicy:
    """Authorization rules for tag management."""

    @staticmethod
    def ensure_can_manage(user: User) -> None:
        """Only moderators and admins may manage tags."""
        if user.role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage tags",
        )
