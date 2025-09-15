from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend import get_container
from domains.platform.iam.security import (
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/users", tags=["users"])

    @router.get("/me")
    async def me(req: Request, claims=Depends(get_current_user)) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        user = await c.users.service.get(user_id)
        return {"user": (None if not user else user.__dict__)}

    @router.get("/{user_id}")
    async def get_user(
        req: Request, user_id: str, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        user = await c.users.service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user_not_found")
        return {"user": user.__dict__}

    return router
