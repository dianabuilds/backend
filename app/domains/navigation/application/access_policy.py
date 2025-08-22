from __future__ import annotations

import anyio

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.users.application.nft_service import user_has_nft


async def has_access_async(node: Node, user: User | None) -> bool:
    """Return True if the user may access the given node."""
    if not node.is_visible or not node.is_public or not node.is_recommendable:
        return False
    if node.premium_only and (not user or not user.is_premium):
        return False
    if node.nft_required and not await user_has_nft(user, node.nft_required):
        return False
    return True


def has_access(node: Node, user: User | None) -> bool:
    """Synchronous wrapper kept for backward compatibility."""
    return anyio.run(has_access_async, node, user)
