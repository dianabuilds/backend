from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.system_v2_repository import EvalRunsRepository
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/ai/platform",
    tags=["admin-ai-platform"],
    responses=ADMIN_AUTH_RESPONSES,
)

AdminRequired = Annotated[None, Depends(require_admin_role())]


@router.post("/evals/run")
async def run_evals(
    payload: dict[str, Any] = Body(...),
    _: AdminRequired = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> dict[str, Any]:
    repo = EvalRunsRepository(db)
    row = await repo.create(spec=payload or {}, profile_id=(payload or {}).get("profile_id"))
    # Enqueue background job here in future (rq/celery/etc)
    return {"id": str(row.id), "status": row.status}
