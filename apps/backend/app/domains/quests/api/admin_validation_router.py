from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import admin_required
from app.core.db.session import get_db
from app.domains.quests.infrastructure.models.quest_version_models import QuestVersion
from app.domains.quests.validation import validate_version_graph

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/versions/{version_id}/validation")
async def get_version_validation(
    version_id: str,
    recalc: Annotated[
        bool, Query(description="Пересчитать отчёт принудительно")
    ] = False,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _admin: Annotated[Any, Depends(admin_required)] = ...,
) -> dict[str, Any]:
    res = await db.execute(select(QuestVersion).where(QuestVersion.id == version_id))
    ver: QuestVersion | None = res.scalars().first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")

    report = None
    if not recalc:
        meta = ver.meta or {}
        report = meta.get("validation")
    if report is None:
        report = await validate_version_graph(db, version_id)
    return {"version_id": version_id, "report": report}
