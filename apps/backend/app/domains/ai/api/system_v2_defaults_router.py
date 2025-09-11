from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_v2_repository import DefaultsRepository
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/defaults")
async def get_defaults(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = DefaultsRepository(db)
    row = await repo.get()
    return {
        "provider_id": str(row.provider_id) if row and row.provider_id else None,
        "model_id": str(row.model_id) if row and row.model_id else None,
        "bundle_id": str(row.bundle_id) if row and row.bundle_id else None,
    }


@router.put("/defaults")
async def put_defaults(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = DefaultsRepository(db)
    row = await repo.set(
        payload.get("provider_id"),
        payload.get("model_id"),
        payload.get("bundle_id"),
    )
    return {
        "provider_id": str(row.provider_id) if row and row.provider_id else None,
        "model_id": str(row.model_id) if row and row.model_id else None,
        "bundle_id": str(row.bundle_id) if row and row.bundle_id else None,
    }
