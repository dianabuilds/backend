from __future__ import annotations

from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quest import Quest
from app.schemas.quest_validation import ValidationReport, ValidationItem


async def validate_quest(db: AsyncSession, quest: Quest) -> ValidationReport:
    """Базовая валидация:
    - квест не помечен как удалённый
    - существует entry_node_id
    - список nodes не пуст
    - entry входит в список nodes
    - нет дубликатов в nodes
    """
    items: list[ValidationItem] = []

    # Квест не должен быть помечен как удалённый
    if getattr(quest, "is_deleted", False):
        items.append(ValidationItem(level="error", code="deleted", message="Quest is deleted"))

    nodes = list((getattr(quest, "nodes", None) or []))

    # Должен существовать стартовый узел
    entry = getattr(quest, "entry_node_id", None)
    if not entry:
        items.append(ValidationItem(level="error", code="no_entry", message="Entry node is not set"))

    # Должен быть хотя бы один узел
    if not nodes:
        items.append(ValidationItem(level="warning", code="no_nodes", message="Quest has no nodes"))

    # Entry должен входить в набор узлов (если он есть)
    if entry and nodes and entry not in nodes:
        items.append(ValidationItem(level="error", code="entry_not_in_nodes", message="Entry node is not in nodes list"))

    # Дубликаты узлов
    if nodes:
        seen = set()
        dups = set()
        for n in nodes:
            if n is None:
                continue
            if n in seen:
                dups.add(n)
            seen.add(n)
        if dups:
            items.append(ValidationItem(level="warning", code="duplicate_nodes", message=f"Duplicate nodes detected: {len(dups)}"))

    errors = sum(1 for i in items if i.level == "error")
    warnings = sum(1 for i in items if i.level == "warning")
    return ValidationReport(errors=errors, warnings=warnings, items=items)
