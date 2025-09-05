from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.quest_validation import ValidationReport


class Validator(Protocol):
    """Callable protocol for node validators."""

    async def __call__(self, db: AsyncSession, node_id: UUID) -> ValidationReport: ...


_registry: dict[str, list[Validator]] = {}


def register(node_type: str, validator: Validator) -> None:
    """Register a validator for a specific node type."""

    _registry.setdefault(node_type, []).append(validator)


def validator(node_type: str) -> Callable[[Validator], Validator]:
    """Decorator to register a validator for a node type."""

    def decorator(func: Validator) -> Validator:
        register(node_type, func)
        return func

    return decorator


async def run_validators(node_type: str, node_id: UUID, db: AsyncSession) -> ValidationReport:
    """Run all validators for a node type and aggregate their reports."""

    report = ValidationReport(errors=0, warnings=0, items=[])
    for func in _registry.get(node_type, []):
        res = await func(db, node_id)
        report.errors += res.errors
        report.warnings += res.warnings
        report.items.extend(res.items)
    return report
