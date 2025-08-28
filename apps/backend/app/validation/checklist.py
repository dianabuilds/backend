from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.models import NodeItem
from app.domains.nodes.infrastructure.models.node import Node
from app.schemas.nodes_common import NodeType, Status
from app.schemas.quest_validation import ValidationItem, ValidationReport
from .base import validator


@validator(NodeType.article.value)
async def checklist_validator(db: AsyncSession, node_id: UUID) -> ValidationReport:
    item = await db.get(NodeItem, node_id)
    if not item:
        return ValidationReport(
            errors=1,
            warnings=0,
            items=[ValidationItem(level="error", code="not_found", message="Node not found")],
        )

    errors: list[ValidationItem] = []
    warnings: list[ValidationItem] = []

    # Unique slug check (against other NodeItems and published Nodes)
    q = await db.execute(
        select(NodeItem.id).where(NodeItem.slug == item.slug, NodeItem.id != item.id)
    )
    if q.scalar_one_or_none() is not None:
        errors.append(
            ValidationItem(level="error", code="slug_exists", message="Slug already in use")
        )
    q = await db.execute(select(Node.id).where(Node.slug == item.slug, Node.id != item.id))
    if q.scalar_one_or_none() is not None:
        errors.append(
            ValidationItem(level="error", code="slug_exists", message="Slug already in use")
        )

    # Required fields
    if not item.title or not item.title.strip():
        errors.append(
            ValidationItem(level="error", code="title_missing", message="Title is required")
        )
    if not item.summary or not item.summary.strip():
        errors.append(
            ValidationItem(level="error", code="summary_missing", message="Summary is required")
        )
    if not item.primary_tag_id:
        errors.append(
            ValidationItem(level="error", code="tag_missing", message="Primary tag is required")
        )

    # Cover is recommended
    if not item.cover_media_id:
        warnings.append(
            ValidationItem(level="warning", code="cover_missing", message="Cover is missing")
        )

    # Review status
    if item.status != Status.in_review:
        warnings.append(
            ValidationItem(level="warning", code="not_in_review", message="Not in review")
        )

    report = ValidationReport(
        errors=len([i for i in errors if i.level == "error"]),
        warnings=len(warnings),
        items=errors + warnings,
    )
    return report
