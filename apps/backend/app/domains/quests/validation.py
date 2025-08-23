from __future__ import annotations

"""Utilities for validating quests and quest graphs."""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.schemas.quest_validation import ValidationItem, ValidationReport
from app.validation.base import validator


async def validate_version_graph(_db: AsyncSession, _version_id: UUID) -> Dict[str, Any]:
    """Validate a quest version graph.

    Currently returns an empty report compatible with older code.
    """

    return {"errors": 0, "warnings": 0, "items": []}


async def validate_quest(_db: AsyncSession, _quest: Quest) -> ValidationReport:
    """Validate a quest before publishing.

    Returns an empty :class:`ValidationReport` indicating no issues.
    """

    return ValidationReport(errors=0, warnings=0, items=[])


@validator("quest")
async def quest_graph_validator(db: AsyncSession, quest_id: UUID) -> ValidationReport:
    """Simple quest validator registered in the global validation registry."""

    res = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = res.scalars().first()
    if quest is None:
        return ValidationReport(
            errors=1,
            warnings=0,
            items=[
                ValidationItem(
                    level="error",
                    code="quest_not_found",
                    message="Quest not found",
                    hint="Создайте квест перед валидацией",
                )
            ],
        )
    return ValidationReport(errors=0, warnings=0, items=[])


__all__ = ["validate_version_graph", "validate_quest"]
