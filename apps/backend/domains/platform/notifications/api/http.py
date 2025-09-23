from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.platform.notifications.logic.dispatcher import dispatch
from packages.core import validate_notifications_request


class PreferenceBody(BaseModel):
    preferences: dict[str, Any]


class TestNotificationBody(BaseModel):
    channel: str = Field(min_length=1)
    payload: dict[str, Any] | None = None


class SendIn(BaseModel):
    channel: str = Field(min_length=1, examples=["log", "webhook"])
    payload: dict[str, Any]


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications")

    @router.get("/preferences")
    async def get_preferences(
        req: Request,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated")
        container = get_container(req)
        prefs = await container.notifications.preference_service.get_preferences(user_id)
        return {"preferences": prefs}

    @router.put("/preferences", dependencies=[Depends(csrf_protect)])
    async def set_preferences(
        req: Request,
        body: PreferenceBody,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated")
        container = get_container(req)
        await container.notifications.preference_service.set_preferences(user_id, body.preferences)
        return {"ok": True}

    @router.post("/test", dependencies=[Depends(csrf_protect)])
    async def test_notification(
        body: TestNotificationBody,
        _claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        payload = body.payload or {}
        dispatch(body.channel, payload)
        return {"ok": True}

    @router.post("/send")
    async def send_notification(
        body: SendIn,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        try:
            validate_notifications_request("/v1/notifications/send", "post", body.model_dump())
        except Exception as exc:
            raise HTTPException(status_code=422, detail="schema_validation_failed") from exc
        try:
            dispatch(body.channel, body.payload)
        except Exception as exc:  # pragma: no cover - thin wrapper around dispatcher
            raise HTTPException(status_code=502, detail="publish_failed") from exc
        return {"ok": True}

    return router


__all__ = ["make_router"]
