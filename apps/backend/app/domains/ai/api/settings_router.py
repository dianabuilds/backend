from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.application.settings_service import SettingsService
from app.domains.ai.infrastructure.repositories.settings_repository import (
    AISettingsRepository,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/ai", tags=["admin-ai-settings"], responses=ADMIN_AUTH_RESPONSES)

admin_required = require_admin_role()
AdminRequired = Annotated[None, Depends(admin_required)]


@router.get("/settings")
async def get_settings(
    _: AdminRequired, db: Annotated[AsyncSession, Depends(get_db)] = ...
) -> dict[str, Any]:
    service = SettingsService(AISettingsRepository(db))
    return await service.get_ai_settings()


@router.put("/settings")
async def put_settings(
    payload: dict[str, Any],
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    provider = payload.get("provider")
    base_url = payload.get("base_url")
    model = payload.get("model")
    api_key: str | None = payload.get("api_key", None)
    model_map = payload.get("model_map")
    cb = payload.get("cb")
    service = SettingsService(AISettingsRepository(db))
    return await service.update_ai_settings(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        model_map=model_map if isinstance(model_map, dict) else None,
        cb=cb if isinstance(cb, dict) else None,
    )
