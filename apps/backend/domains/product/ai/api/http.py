from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import get_current_user


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
        dependencies=([Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []),
    )
    async def generate(
        body: dict,
        req: Request,
        container=Depends(get_container),
    ):
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt_required")
        svc = container.ai_service
        if not svc:
            raise HTTPException(status_code=503, detail="ai_unavailable")
        try:
            await get_current_user(req)
        except HTTPException as exc:
            if exc.status_code not in {401, 403}:
                raise
        # Determine default model/provider from registry settings
        model_name: str | None = None
        provider_name: str | None = None
        try:
            reg = container.ai_registry
            items = await reg.list_models()
            # Filter to enabled/active
            act = [m for m in items if (m.status or "active") != "disabled"]

            def prio(m) -> int:
                p = 1000
                try:
                    if m.params and isinstance(m.params, dict):
                        v = m.params.get("fallback_priority")
                        if v is not None:
                            p = int(v)
                except Exception:
                    pass
                return p

            chosen = None
            for m in act:
                if bool(getattr(m, "is_default", False)):
                    chosen = m
                    break
            if not chosen and act:
                chosen = sorted(act, key=lambda x: prio(x))[0]
            if chosen:
                model_name = str(chosen.name)
                provider_name = str(chosen.provider_slug)
        except Exception:
            pass
        # user_id = str(claims.get("sub") or "") if claims else ""
        return await svc.generate(prompt, model=model_name, provider=provider_name)

    return router
