from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.events.adapters.redis_bus import RedisBus
from domains.platform.iam.security import require_admin
from packages.core.config import load_settings
from packages.fastapi_rate_limit import optional_rate_limiter


class PubIn(BaseModel):
    topic: str
    payload: dict
    key: str | None = None


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/events")

    @router.get("/health")
    def health() -> dict:  # pragma: no cover - simple
        return {"ok": True}

    @router.get(
        "/stats/{topic}",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    def stats(
        topic: str, group: str | None = None, _admin: None = Depends(require_admin)
    ) -> dict:  # pragma: no cover - simple
        s = load_settings()
        bus = RedisBus(s.redis_url)
        g = group or "relay"
        return {
            "topic": topic,
            "xlen": bus.xlen(topic),
            "pending": bus.xpending(topic, g),
        }

    @router.post(
        "/dev/publish",
        dependencies=(optional_rate_limiter(times=30, seconds=60)),
        summary="Publish an event (dev)",
    )
    def dev_publish(
        body: PubIn, req: Request, _admin: None = Depends(require_admin)
    ) -> dict:
        try:
            c = get_container(req)
            c.events.publish(body.topic, body.payload, key=body.key)
            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail="publish_failed") from e

    return router
