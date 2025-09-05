from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.ai.infrastructure.repositories.system_defaults_repository import (
    AIDefaultModelRepository,
)
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
    repo = AIDefaultModelRepository(db)
    row = await repo.get_default()
    return row.as_dict() if row else {}


@router.post("/defaults")
async def set_defaults(
    payload: dict[str, Any],
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = AIDefaultModelRepository(db)
    row = await repo.set_default(
        provider=payload.get("provider"),
        model=payload.get("model"),
    )
    return row.as_dict()
