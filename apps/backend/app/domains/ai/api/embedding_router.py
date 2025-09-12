from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Body, Depends

from app.kernel.config import settings
from app.domains.ai.application.embedding_service import EMBEDDING_DIM, get_embedding
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/embedding", tags=["admin"])


@router.get(
    "/status",
    summary="Проверка статуса embedding-провайдера",
    responses=ADMIN_AUTH_RESPONSES,
)
async def embedding_status(_: Annotated[User, Depends(require_admin_role)]):
    info = {
        "backend": settings.embedding.name,
        "dim": EMBEDDING_DIM,
        "api_base_configured": bool(settings.embedding.api_base),
        "model": settings.embedding.model,
    }
    try:
        t0 = time.perf_counter()
        vec = get_embedding("health check")
        dt_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "ok": True,
            "vector_len": len(vec),
            "sample_norm": (sum(v * v for v in vec) ** 0.5),
            "took_ms": round(dt_ms, 2),
            "info": info,
            "preview": vec[:8],
        }
    except Exception as e:
        logger.exception("Embedding health check failed")
        return {"ok": False, "error": str(e), "info": info}


@router.post(
    "/test",
    summary="Протестировать векторизацию произвольного текста",
    responses=ADMIN_AUTH_RESPONSES,
)
async def embedding_test(
    text: Annotated[str, Body(..., embed=True, description="Текст для эмбеддинга")],
    _: Annotated[User, Depends(require_admin_role)],
):
    try:
        t0 = time.perf_counter()
        vec = get_embedding(text)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "ok": True,
            "vector_len": len(vec),
            "took_ms": round(dt_ms, 2),
            "preview": vec[:16],
        }
    except Exception as e:
        logger.exception("Embedding test failed")
        return {"ok": False, "error": str(e)}
