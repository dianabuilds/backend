from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import csrf_protect, get_current_user


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/profile")

    @router.put("/{user_id}/username")
    def update_username(
        user_id: str,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        # Only owner or admin may edit username
        sub = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if sub != user_id and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        svc = container.profile_service
        try:
            username = body.get("username")
            if not isinstance(username, str):
                raise HTTPException(status_code=400, detail="username_required")
            return svc.update_username(
                user_id, username, subject={"user_id": sub or user_id}
            )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail="forbidden") from e
        except ValueError as e:
            # Domain validation errors
            raise HTTPException(status_code=400, detail=str(e)) from e

    return router
