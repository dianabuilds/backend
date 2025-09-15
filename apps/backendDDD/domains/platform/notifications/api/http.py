from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.backendDDD.domains.platform.iam.security import csrf_protect, require_admin
from apps.backendDDD.domains.platform.notifications.logic.dispatcher import dispatch
from apps.backendDDD.packages.core.api_contracts import validate_notifications_request


class SendIn(BaseModel):
    channel: str = Field(min_length=1, examples=["log", "webhook"])
    payload: dict[str, Any]


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications")

    @router.post("/send")
    def send(
        body: SendIn,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        # Contract validation against OpenAPI schema (if present)
        try:
            validate_notifications_request(
                "/v1/notifications/send", "post", body.model_dump()
            )
        except Exception as e:
            raise HTTPException(
                status_code=422, detail="schema_validation_failed"
            ) from e
        try:
            dispatch(body.channel, body.payload)
        except Exception as e:  # pragma: no cover - thin wrapper
            raise HTTPException(status_code=502, detail="publish_failed") from e
        return {"ok": True}

    return router
