from __future__ import annotations

from typing import Callable, Awaitable, Dict, List, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.quest_validation import ValidationReport


class Validator(Protocol):
    """Callable protocol for content validators."""

    async def __call__(self, db: AsyncSession, content_id: UUID) -> ValidationReport: ...


_registry: Dict[str, List[Validator]] = {}


def register(content_type: str, validator: Validator) -> None:
    """Register a validator for a specific content type."""

    _registry.setdefault(content_type, []).append(validator)


def validator(content_type: str) -> Callable[[Validator], Validator]:
    """Decorator to register a validator for a content type."""

    def decorator(func: Validator) -> Validator:
        register(content_type, func)
        return func

    return decorator


async def run_validators(content_type: str, content_id: UUID, db: AsyncSession) -> ValidationReport:
    """Run all validators for a content type and aggregate their reports."""

    report = ValidationReport(errors=0, warnings=0, items=[])
    for func in _registry.get(content_type, []):
        res = await func(db, content_id)
        report.errors += res.errors
        report.warnings += res.warnings
        report.items.extend(res.items)
    return report
