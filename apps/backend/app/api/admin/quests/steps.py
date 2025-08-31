from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.quests.services import QuestStepService
from app.models.quests import QuestStep
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role


class QuestStepBase(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    type: str = Field(default="normal")
    content: dict[str, Any] | None = None
    rewards: dict[str, Any] | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    @field_validator("content", "rewards", mode="before")
    @classmethod
    def _parse_json(cls, v: Any) -> Any:  # noqa: ANN001
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
            except Exception:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None


class QuestStepCreate(QuestStepBase):
    pass


class QuestStepUpdate(QuestStepBase):
    pass


class QuestStepPatch(BaseModel):
    key: str | None = None
    title: str | None = None
    type: str | None = None
    content: dict[str, Any] | None = None
    rewards: dict[str, Any] | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    @field_validator("content", "rewards", mode="before")
    @classmethod
    def _parse_json(cls, v: Any) -> Any:  # noqa: ANN001
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
            except Exception:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None


class QuestStepOut(QuestStepBase):
    id: UUID
    quest_id: UUID = Field(alias="questId")
    order: int

    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )


class QuestStepPage(BaseModel):
    total: int
    items: list[QuestStepOut]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


admin_required = require_admin_role({"admin", "moderator", "editor"})

router = APIRouter(
    prefix="/admin/quests/{quest_id}/steps",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=QuestStepPage, summary="List quest steps")
async def list_steps(
    quest_id: UUID,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestStepPage:
    svc = QuestStepService()
    steps = await svc.list_steps(db, quest_id, limit=limit, offset=offset)
    total_res = await db.execute(
        select(func.count()).select_from(QuestStep).where(QuestStep.quest_id == quest_id)
    )
    total = int(total_res.scalar() or 0)
    items = [QuestStepOut.model_validate(s, from_attributes=True) for s in steps]
    return QuestStepPage(total=total, items=items)


@router.post("", response_model=QuestStepOut, status_code=201, summary="Create quest step")
async def create_step(
    quest_id: UUID,
    payload: QuestStepCreate,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestStepOut:
    svc = QuestStepService()
    step = await svc.create_step(
        db,
        quest_id,
        key=payload.key,
        title=payload.title,
        type=payload.type,
        content=payload.content,
        rewards=payload.rewards,
    )
    await db.commit()
    return QuestStepOut.model_validate(step, from_attributes=True)


@router.get("/{step_id}", response_model=QuestStepOut, summary="Get quest step")
async def get_step(
    quest_id: UUID,
    step_id: UUID,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestStepOut:
    step = await db.get(QuestStep, step_id)
    if not step or step.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Step not found")
    return QuestStepOut.model_validate(step, from_attributes=True)


@router.put("/{step_id}", response_model=QuestStepOut, summary="Replace quest step")
async def put_step(
    quest_id: UUID,
    step_id: UUID,
    payload: QuestStepUpdate,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestStepOut:
    step = await db.get(QuestStep, step_id)
    if not step or step.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Step not found")
    svc = QuestStepService()
    step = await svc.update_step(db, step_id, **payload.model_dump())
    await db.commit()
    return QuestStepOut.model_validate(step, from_attributes=True)


@router.patch("/{step_id}", response_model=QuestStepOut, summary="Update quest step")
async def patch_step(
    quest_id: UUID,
    step_id: UUID,
    payload: QuestStepPatch,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> QuestStepOut:
    step = await db.get(QuestStep, step_id)
    if not step or step.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Step not found")
    svc = QuestStepService()
    step = await svc.update_step(
        db, step_id, **payload.model_dump(exclude_unset=True)
    )
    await db.commit()
    return QuestStepOut.model_validate(step, from_attributes=True)


@router.delete("/{step_id}", response_model=dict, summary="Delete quest step")
async def delete_step(
    quest_id: UUID,
    step_id: UUID,
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    step = await db.get(QuestStep, step_id)
    if not step or step.quest_id != quest_id:
        raise HTTPException(status_code=404, detail="Step not found")
    svc = QuestStepService()
    await svc.delete_step(db, step_id)
    await db.commit()
    return {"status": "ok"}
