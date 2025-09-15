from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user
from domains.product.navigation.application.ports import NextInput


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/navigation")

    @router.post("/next")
    def next_step(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "")
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        data = NextInput(
            user_id=uid,
            current_node_id=(
                int(body.get("current_node_id"))
                if body.get("current_node_id") is not None
                else None
            ),
            strategy=str(body.get("strategy") or "random"),
        )
        svc = container.navigation_service
        step = svc.next(data)
        return {"node_id": step.node_id, "reason": step.reason}

    return router
