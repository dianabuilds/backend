from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_v2_repository import PresetsRepository
from app.domains.ai.validation_v2 import validate_preset
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.get("/presets")
async def list_presets(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = PresetsRepository(db)
    rows = await repo.list()
    return [{"id": str(r.id), "name": r.name, "task": r.task, "params": r.params} for r in rows]


@router.post("/presets")
async def create_preset(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_preset(payload)
    repo = PresetsRepository(db)
    row = await repo.create(payload)
    return {"id": str(row.id), "name": row.name, "task": row.task, "params": row.params}


@router.put("/presets/{preset_id}")
async def update_preset(
    preset_id: str,
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    validate_preset(
        {
            **payload,
            "name": payload.get("name", "tmp"),
            "task": payload.get("task", "chat"),
            "params": payload.get("params", {}),
        }
    )
    repo = PresetsRepository(db)
    row = await repo.update(preset_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="preset not found")
    return {"id": str(row.id), "name": row.name, "task": row.task, "params": row.params}


@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = PresetsRepository(db)
    await repo.delete(preset_id)
    return {"ok": True}
