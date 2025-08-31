from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.ai.application.settings_service import SettingsService
from app.domains.ai.infrastructure.repositories.settings_repository import (
    AISettingsRepository,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai", tags=["admin-ai-settings"], responses=ADMIN_AUTH_RESPONSES
)
compat_router = APIRouter(
    prefix="/admin/ai/quests",
    tags=["admin-ai-settings-compat"],
    responses=ADMIN_AUTH_RESPONSES,
)

admin_required = require_admin_role()


@router.get("/settings")
async def get_settings(
    _=Depends(admin_required), db: Annotated[AsyncSession, Depends(get_db)] = ...
) -> dict[str, Any]:
    service = SettingsService(AISettingsRepository(db))
    return await service.get_ai_settings()


@router.put("/settings")
async def put_settings(
    payload: dict[str, Any],
    _=Depends(admin_required),
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


@compat_router.get("/settings")
async def get_settings_compat(
    _=Depends(admin_required), db: Annotated[AsyncSession, Depends(get_db)] = ...
) -> dict[str, Any]:
    service = SettingsService(AISettingsRepository(db))
    return await service.get_ai_settings()


@compat_router.put("/settings")
async def put_settings_compat(
    payload: dict[str, Any],
    _=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    return await put_settings(payload, _, db)
