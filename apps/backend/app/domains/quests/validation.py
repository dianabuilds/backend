# mypy: ignore-errors
"""Utilities for validating quests and quest graphs."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.models import NodeItem
from app.schemas.quest_validation import ValidationItem, ValidationReport
from app.validation.base import validator


async def validate_version_graph(_db: AsyncSession, _version_id: UUID) -> dict[str, Any]:
    """Validate a quest version graph.

    Currently returns an empty report compatible with older code.
    """

    return {"errors": 0, "warnings": 0, "items": []}


async def validate_quest(_db: AsyncSession, _quest: Any) -> ValidationReport:
    """Validate a quest before publishing.

    Returns an empty :class:`ValidationReport` indicating no issues.
    """

    return ValidationReport(errors=0, warnings=0, items=[])


@validator("quest")
async def quest_graph_validator(db: AsyncSession, node_id: UUID) -> ValidationReport:
    """Validate quest graph stored within a :class:`NodeItem`."""

    item = await db.get(NodeItem, node_id)
    if item is None:
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
