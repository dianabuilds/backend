from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/ai")

    @router.get("/health")
    async def health(container=Depends(get_container)):
        try:
            svc = container.ai_service
            return {"status": "ok" if svc else "unavailable"}
        except Exception:
            return {"status": "unavailable"}

    @router.post(
        "/generate",
        dependencies=(
            [Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []
        ),
    )
    async def generate(
        body: dict,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt_required")
        svc = container.ai_service
        # user_id = str(claims.get("sub") or "") if claims else ""
        return await svc.generate(prompt)

    return router
