from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag

_CACHE_TTL = 30  # seconds
_cache: tuple[float, dict[str, bool]] | None = None

# Predefined feature flags available in the system with optional descriptions.
KNOWN_FLAGS: dict[str, str] = {
    "moderation.enabled": "Enable moderation section in admin UI",
    "payments": "Enable payments module",
    "ai.validation": "Enable AI-based validation for nodes",
}


def _now() -> float:
    return time.time()


async def _load_flags(db: AsyncSession) -> dict[str, bool]:
    res = await db.execute(select(FeatureFlag))
    items: list[FeatureFlag] = list(res.scalars().all())
    return {it.key: bool(it.value) for it in items}


async def ensure_known_flags(db: AsyncSession) -> None:
    """Ensure that all KNOWN_FLAGS exist in the database."""
    res = await db.execute(select(FeatureFlag.key))
    existing = set(res.scalars().all())
    created = False
    for key, desc in KNOWN_FLAGS.items():
        if key not in existing:
            db.add(FeatureFlag(key=key, value=False, description=desc))
            created = True
    if created:
        await db.flush()
        invalidate_cache()


async def get_flags_map(db: AsyncSession) -> dict[str, bool]:
    global _cache
    if _cache and _cache[0] > _now():
        return _cache[1]
    data = await _load_flags(db)
    _cache = (_now() + _CACHE_TTL, data)
    return data


def parse_preview_flags(header_val: str | None) -> set[str]:
    if not header_val:
        return set()
    vals = [p.strip() for p in header_val.split(",") if p.strip()]
    return set(vals)


async def get_effective_flags(db: AsyncSession, preview_header: str | None) -> set[str]:
    base = await get_flags_map(db)
    active = {k for k, v in base.items() if v}
    preview = parse_preview_flags(preview_header)
    return active.union(preview)


async def set_flag(
    db: AsyncSession,
    key: str,
    value: bool | None = None,
    description: str | None = None,
    updated_by: str | None = None,
) -> FeatureFlag:
    existing = await db.get(FeatureFlag, key)
    if existing is None:
        existing = FeatureFlag(
            key=key, value=bool(value) if value is not None else False
        )
        db.add(existing)
    if value is not None:
        existing.value = bool(value)
    if description is not None:
        existing.description = description
    if updated_by is not None:
        existing.updated_by = updated_by
    # updated_at обновится за счёт onupdate; в async orm произойдёт на flush/commit
    await db.flush()
    # invalidate cache
    invalidate_cache()
    return existing


def invalidate_cache() -> None:
    global _cache
    _cache = None
