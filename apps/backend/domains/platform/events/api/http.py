from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from apps.backend import get_container
from domains.platform.events.adapters.redis_bus import RedisBus
from domains.platform.iam.security import require_admin
from packages.core.config import load_settings

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/events")

    @router.get("/health")
    def health() -> dict:  # pragma: no cover - simple
        return {"ok": True}

    @router.get(
        "/stats/{topic}",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
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

    class PubIn(BaseModel):
        topic: str
        payload: dict
        key: str | None = None

    @router.post(
        "/dev/publish",
        dependencies=(
            [Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []
        ),
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
