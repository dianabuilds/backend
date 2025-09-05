from __future__ import annotations

from fastapi import HTTPException, status

from app.core.preview import PreviewContext
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User


class NodePolicy:
    """Authorization rules for Node operations."""

    @staticmethod
    def ensure_can_view(node: Node, user: User, preview: PreviewContext | None = None) -> None:
        """Allow viewing if node is visible or user is owner/mod/admin."""
        role = preview.role if preview and preview.role else user.role
        if node.is_visible:
            return
        if node.author_id == user.id:
            return
        if role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this node",
        )

    @staticmethod
    def ensure_can_edit(node: Node, user: User, preview: PreviewContext | None = None) -> None:
        """Allow editing for owner or moderator/admin."""
        role = preview.role if preview and preview.role else user.role
        if node.author_id == user.id or role in {"moderator", "admin"}:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this node",
        )
