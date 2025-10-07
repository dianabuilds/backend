from __future__ import annotations

import logging

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Request
from httpx import HTTPError

from domains.platform.iam.security import get_current_user
from domains.product.ai.application.errors import ProviderError
from packages.fastapi_rate_limit import optional_rate_limiter

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/ai")

    @router.get("/health")
    async def health(container=Depends(get_container)):
        try:
            svc = container.ai_service
        except AttributeError as exc:
            logger.warning("ai_service_not_bound", exc_info=exc)
            raise HTTPException(status_code=503, detail="ai_unavailable") from exc
        except RuntimeError as exc:
            logger.warning("ai_service_initialization_failed", exc_info=exc)
            raise HTTPException(status_code=503, detail="ai_unavailable") from exc
        return {"status": "ok" if svc else "unavailable"}

    @router.post(
        "/generate",
        dependencies=(optional_rate_limiter(times=30, seconds=60)),
    )
    async def generate(
        body: dict,
        req: Request,
        container=Depends(get_container),
    ):
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt_required")
        try:
            svc = container.ai_service
        except AttributeError as exc:
            logger.warning("ai_service_not_bound", exc_info=exc)
            raise HTTPException(status_code=503, detail="ai_unavailable") from exc
        except RuntimeError as exc:
            logger.warning("ai_service_initialization_failed", exc_info=exc)
            raise HTTPException(status_code=503, detail="ai_unavailable") from exc
        if not svc:
            raise HTTPException(status_code=503, detail="ai_unavailable")
        try:
            await get_current_user(req)
        except HTTPException as exc:
            if exc.status_code not in {401, 403}:
                raise
        model_name: str | None = None
        provider_name: str | None = None
        try:
            reg = container.ai_registry
            items = await reg.list_models()
            act = [m for m in items if (m.status or "active") != "disabled"]

            def prio(m) -> int:
                default_priority = 1000
                try:
                    if m.params and isinstance(m.params, dict):
                        value = m.params.get("fallback_priority")
                        if value is not None:
                            return int(value)
                except (TypeError, ValueError):
                    return default_priority
                return default_priority

            chosen = next(
                (m for m in act if bool(getattr(m, "is_default", False))), None
            )
            if not chosen and act:
                chosen = sorted(act, key=lambda x: prio(x))[0]
            if chosen:
                model_name = str(chosen.name)
                provider_name = str(chosen.provider_slug)
        except (AttributeError, RuntimeError) as exc:
            logger.warning("ai_registry_unavailable", exc_info=exc)
        except HTTPError as exc:
            logger.warning("ai_registry_http_error", exc_info=exc)
        try:
            result = await svc.generate(
                prompt, model=model_name, provider=provider_name
            )
        except ProviderError as exc:
            code = exc.code or "provider_error"
            if code == "prompt_json_invalid":
                status = 400
            elif code in {"provider_not_configured"}:
                status = 503
            else:
                status = 502
            logger.warning(
                "ai_generation_failed",
                extra={"code": code, "provider": provider_name, "model": model_name},
                exc_info=exc,
            )
            raise HTTPException(status_code=status, detail=code) from exc
        return result

    return router
