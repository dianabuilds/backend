from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.providers import OpenAIProvider
from app.domains.ai.router import resolve
from app.domains.nodes.models import NodeItem
from app.schemas.quest_validation import ValidationItem, ValidationReport

from .bundle import BUNDLE as VALIDATION_BUNDLE


async def run_ai_validation(db: AsyncSession, node_id: UUID) -> ValidationReport:
    """Run LLM-based validation for a node.

    This function attempts to validate node content using a large language
    model selected from :data:`VALIDATION_BUNDLE`. If the LLM call fails for
    any reason, an empty report is returned so that validation gracefully
    falls back to local checks only.
    """

    item = await db.get(NodeItem, node_id)
    if not item:
        return ValidationReport(
            errors=1,
            warnings=0,
            items=[
                ValidationItem(
                    level="error",
                    code="not_found",
                    message="Node not found",
                )
            ],
        )

    prompt = (
        "You are an assistant that validates content. "
        "Given the following title and summary, return a JSON array where each "
        "item has fields: level (error|warning), code, message and fix. "
        f"Title: {item.title!r}\nSummary: {item.summary!r}"
    )

    model = resolve(VALIDATION_BUNDLE, {})
    provider = OpenAIProvider()
    try:
        raw = await provider.complete(
            model=model.get("name", ""),
            prompt=prompt,
            system="You return JSON.",
            json_mode=True,
            max_tokens=512,
        )
        data = json.loads(raw)
    except Exception as err:
        _ = err
        data = []

    items: list[ValidationItem] = []
    errors = 0
    warnings = 0
    for it in data:
        level = str(it.get("level", "warning"))
        if level == "error":
            errors += 1
        else:
            warnings += 1
        items.append(
            ValidationItem(
                level=level,
                code=it.get("code", "ai"),
                message=it.get("message", ""),
                hint=it.get("fix"),
            )
        )
    return ValidationReport(errors=errors, warnings=warnings, items=items)


__all__ = ["run_ai_validation"]
