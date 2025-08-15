from __future__ import annotations

from fastapi import HTTPException, status
from app.models.node import Node
from app.models.user import User


class NodePolicy:
    """Authorization rules for Node operations."""

    @staticmethod
    def ensure_can_view(node: Node, user: User) -> None:
        """Allow viewing if node is public or user is owner/mod/admin."""
        if node.is_public and node.is_visible:
            return
        if node.author_id == user.id:
            return
        if user.role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this node",
        )

    @staticmethod
    def ensure_can_edit(node: Node, user: User) -> None:
        """Allow editing for owner or moderator/admin."""
        if node.author_id == user.id or user.role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this node",
        )
