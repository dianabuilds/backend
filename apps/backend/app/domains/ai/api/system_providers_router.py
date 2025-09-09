from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.application.settings_service import SettingsService
from app.domains.ai.infrastructure.repositories.settings_repository import (
    AISettingsRepository,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

# Require admin explicitly; call the factory to get dependency
AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/providers")
async def list_providers(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    service = SettingsService(AISettingsRepository(db))
    settings = await service.get_ai_settings()
    provider = settings.get("provider")
    if not provider:
        return []
    return [
        {
            "id": "default",
            "code": provider,
            "base_url": settings.get("base_url"),
            "health": "unknown",
        }
    ]


@router.post("/providers")
async def add_provider(
    _: AdminRequired,
    payload: dict[str, Any] = Body(...),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    code = payload.get("code") or payload.get("provider")
    service = SettingsService(AISettingsRepository(db))
    settings = await service.update_ai_settings(
        provider=code,
        base_url=payload.get("base_url"),
        model=payload.get("model"),
        api_key=payload.get("api_key"),
        model_map=payload.get("model_map"),
        cb=payload.get("cb"),
    )
    return {
        "id": "default",
        "code": settings.get("provider"),
        "base_url": settings.get("base_url"),
        "health": "unknown",
    }
