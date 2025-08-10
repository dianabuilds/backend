"""Common access and visibility filters for navigation.

This module centralises the logic that determines whether a node should be
offered to the user.  According to the navigation specification all sources
of transitions (compass, echo, random, manual) must apply the same filters so
that a user never receives a link to a node that is hidden or restricted.
"""

from __future__ import annotations

import anyio

from app.models.node import Node
from app.models.user import User
from app.services.nft import user_has_nft


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


__all__ = ["has_access", "has_access_async"]
