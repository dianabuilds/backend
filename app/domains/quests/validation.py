from __future__ import annotations

"""Utilities for validating quests and quest graphs.

The original implementation was removed during refactoring which made
modules importing these helpers fail to load.  As a result the admin
router couldn't be included and requests to ``/admin/quests`` returned a
404.  This lightweight module restores the functions expected by the
routers so that the endpoints can be registered again.

The current implementation performs only minimal validation: it simply
returns an empty ``ValidationReport`` meaning no problems were detected.
This is sufficient for the admin quest listing and can be extended later
with real checks.
"""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.schemas.quest_validation import ValidationReport


async def validate_version_graph(_db: AsyncSession, _version_id: UUID) -> Dict[str, Any]:
    """Validate a quest version graph.

    Currently returns an empty report.  The return value is a dictionary
    compatible with older code that expects ``dict``-like access.
    """

    return {"errors": 0, "warnings": 0, "items": []}


async def validate_quest(_db: AsyncSession, _quest: Quest) -> ValidationReport:
    """Validate a quest before publishing.

    Returns an empty :class:`ValidationReport` indicating no issues.
    """

    return ValidationReport(errors=0, warnings=0, items=[])


__all__ = ["validate_version_graph", "validate_quest"]
