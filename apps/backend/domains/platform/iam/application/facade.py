from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request

from domains.platform.iam import security


class IamFacade:
    """Facade exposing IAM security helpers for product domains."""

    async def get_current_user(self, request: Request) -> dict[str, Any]:
        return await security.get_current_user(request)

    async def csrf_protect(self, request: Request) -> None:
        await security.csrf_protect(request)

    async def require_admin(self, request: Request) -> None:
        await security.require_admin(request)

    def require_role_db(self, min_role: str) -> Callable[..., Awaitable[None]]:
        return security.require_role_db(min_role)


iam_facade = IamFacade()

get_current_user = iam_facade.get_current_user
csrf_protect = iam_facade.csrf_protect
require_admin = iam_facade.require_admin
require_role_db = iam_facade.require_role_db

__all__ = [
    "IamFacade",
    "iam_facade",
    "get_current_user",
    "csrf_protect",
    "require_admin",
    "require_role_db",
]
