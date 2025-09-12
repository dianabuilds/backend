from __future__ import annotations

# ruff: noqa: E402
import sys
import types
from datetime import datetime
from types import SimpleNamespace

mod = sys.modules.get("app.domains.users.application.nft_service")
if isinstance(mod, SimpleNamespace):
    new_mod = types.ModuleType("app.domains.users.application.nft_service")
    new_mod.__dict__.update(mod.__dict__)
    sys.modules["app.domains.users.application.nft_service"] = new_mod

from app.kernel.preview import PreviewContext
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.application.nft_service import user_has_nft
from app.domains.users.infrastructure.models.user import User


async def has_access_async(
    node: Node, user: User | None, preview: PreviewContext | None = None
) -> bool:
    """Return True if the user may access the given node."""
    if not node.is_visible or not node.is_public or not node.is_recommendable:
        return False

    is_premium = False
    if preview and preview.plan:
        is_premium = preview.plan == "premium"
    elif user:
        now = preview.now if preview and preview.now else datetime.utcnow()
        is_premium = user.is_premium and (not user.premium_until or user.premium_until > now)
    if node.premium_only and not is_premium:
        return False

    if node.nft_required and not await user_has_nft(user, node.nft_required):
        return False
    return True

