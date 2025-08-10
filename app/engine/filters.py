"""Common access and visibility filters for navigation.

This module centralises the logic that determines whether a node should be
offered to the user.  According to the navigation specification all sources
of transitions (compass, echo, random, manual) must apply the same filters so
that a user never receives a link to a node that is hidden or restricted.
"""

from __future__ import annotations

from app.models.node import Node
from app.models.user import User


def has_access(node: Node, user: User | None) -> bool:
    """Return True if the user may access the given node.

    The rules are intentionally very small but they are shared by all engines
    so that manual transitions, compass recommendations, echo traces and
    random suggestions all respect the same visibility constraints.

    The function can be extended in the future with additional rules such as
    NFT checks or language restrictions.
    """

    if not node.is_visible or not node.is_public or not node.is_recommendable:
        return False
    if node.premium_only and (not user or not user.is_premium):
        return False
    return True


__all__ = ["has_access"]

