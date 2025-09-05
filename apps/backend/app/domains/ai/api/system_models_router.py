from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_models_repository import (
    AISystemModelRepository,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/system",
    tags=["admin-ai-system"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role)]


@router.get("/models")
async def list_models(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[dict[str, Any]]:
    repo = AISystemModelRepository(db)
    rows = await repo.list_models()
    return [r.as_dict() for r in rows]


@router.post("/models")
async def add_model(
    payload: dict[str, Any],
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = AISystemModelRepository(db)
    row = await repo.upsert_model(
        code=payload.get("code"),
        provider=payload.get("provider"),
        name=payload.get("name"),
        active=bool(payload.get("active", True)),
    )
    return row.as_dict()
