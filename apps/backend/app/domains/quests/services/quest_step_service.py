from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quests import QuestStep, QuestStepTransition


class QuestStepService:
    """Service providing CRUD operations and validations for quest steps and transitions."""

    async def list_steps(
        self,
        db: AsyncSession,
        quest_id: UUID,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[QuestStep]:
        stmt = select(QuestStep).where(QuestStep.quest_id == quest_id).order_by(
            QuestStep.order
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def create_step(
        self,
        db: AsyncSession,
        quest_id: UUID,
        *,
        key: str,
        title: str,
        type: str = "normal",
        content: dict | None = None,
        rewards: dict | None = None,
    ) -> QuestStep:
        if type == "start":
            res = await db.execute(
                select(QuestStep).where(
                    QuestStep.quest_id == quest_id, QuestStep.type == "start"
                )
            )
            if res.scalars().first() is not None:
                raise ValueError("start_step_exists")
        res = await db.execute(
            select(func.max(QuestStep.order)).where(QuestStep.quest_id == quest_id)
        )
        max_order = res.scalar() or 0
        step = QuestStep(
            quest_id=quest_id,
            key=key,
            title=title,
            type=type,
            order=int(max_order) + 1,
            content=content,
            rewards=rewards,
        )
        db.add(step)
        await db.flush()
        return step

    async def update_step(
        self, db: AsyncSession, step_id: UUID, **fields: Any
    ) -> QuestStep:
        step = await db.get(QuestStep, step_id)
        if step is None:
            raise ValueError("step_not_found")
        if fields.get("type") == "start" and step.type != "start":
            res = await db.execute(
                select(QuestStep).where(
                    QuestStep.quest_id == step.quest_id,
                    QuestStep.type == "start",
                    QuestStep.id != step.id,
                )
            )
            if res.scalars().first() is not None:
                raise ValueError("start_step_exists")
        for key, value in fields.items():
            setattr(step, key, value)
        await db.flush()
        return step

    async def delete_step(self, db: AsyncSession, step_id: UUID) -> None:
        step = await db.get(QuestStep, step_id)
        if step is None:
            return
        await db.delete(step)
        await db.flush()

    async def create_transition(
        self,
        db: AsyncSession,
        quest_id: UUID,
        *,
        from_step_id: UUID,
        to_step_id: UUID,
        label: str | None = None,
        condition: dict | None = None,
    ) -> QuestStepTransition:
        from_step = await db.get(QuestStep, from_step_id)
        to_step = await db.get(QuestStep, to_step_id)
        if not from_step or not to_step:
            raise ValueError("step_not_found")
        if from_step.quest_id != quest_id or to_step.quest_id != quest_id:
            raise ValueError("invalid_quest_id")
        transition = QuestStepTransition(
            quest_id=quest_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
            label=label,
            condition=condition,
        )
        db.add(transition)
        await db.flush()
        return transition

    async def delete_transition(self, db: AsyncSession, transition_id: UUID) -> None:
        tr = await db.get(QuestStepTransition, transition_id)
        if tr is None:
            return
        await db.delete(tr)
        await db.flush()


__all__ = ["QuestStepService"]
