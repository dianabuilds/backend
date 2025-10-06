from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin
from packages.fastapi_rate_limit import optional_rate_limiter


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/ai/admin", tags=["admin-ai"])

    # Playground: quick prompt test
    @router.post(
        "/playground",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def playground(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt_required")
        model = str(body.get("model") or "") or None
        model_id = str(body.get("model_id") or "") or None
        provider = str(body.get("provider") or "") or None
        c = get_container(req)
        svc = c.ai_service
        if not svc:
            raise HTTPException(status_code=503, detail="ai_unavailable")
        return await svc.generate(
            prompt, model=model, provider=provider, model_id=model_id
        )

    # Models
    @router.get("/models")
    async def list_models(req: Request, _admin: None = Depends(require_admin)) -> dict:
        c = get_container(req)
        items = await c.ai_registry.list_models()
        return {"items": [asdict(m) for m in items]}

    @router.post(
        "/models",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def upsert_model(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        m = await c.ai_registry.upsert_model(body)
        return {"model": asdict(m)}

    @router.delete(
        "/models/{model_id}",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def delete_model(
        req: Request,
        model_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        await c.ai_registry.delete_model(model_id)
        return {"ok": True}

    # Providers
    @router.get("/providers")
    async def list_providers(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict:
        from domains.product.ai.application.registry import redact_provider

        c = get_container(req)
        items = await c.ai_registry.list_providers()
        return {"items": [redact_provider(p) for p in items]}

    @router.post(
        "/providers",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def upsert_provider(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        p = await c.ai_registry.upsert_provider(body)
        # redact api_key in response
        out = asdict(p)
        if out.get("api_key"):
            out["api_key"] = "***"
        return {"provider": out}

    @router.delete(
        "/providers/{slug}",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def delete_provider(
        req: Request,
        slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        await c.ai_registry.delete_provider(slug)
        return {"ok": True}

    # Fallbacks
    @router.get("/fallbacks")
    async def list_fallbacks(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict:
        c = get_container(req)
        items = await c.ai_registry.list_fallbacks()
        return {"items": [asdict(r) for r in items]}

    @router.post(
        "/fallbacks",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def upsert_fallback(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        r = await c.ai_registry.upsert_fallback(body)
        return {"rule": asdict(r)}

    @router.delete(
        "/fallbacks/{rule_id}",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def delete_fallback(
        req: Request,
        rule_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        c = get_container(req)
        await c.ai_registry.delete_fallback(rule_id)
        return {"ok": True}

    return router
