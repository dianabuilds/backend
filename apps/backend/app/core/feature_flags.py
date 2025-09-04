from __future__ import annotations

import time
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag

_CACHE_TTL = 30  # seconds
_cache: tuple[float, dict[str, bool]] | None = None


# Predefined feature flags available in the system with optional descriptions.
class FeatureFlagKey(StrEnum):
    MODERATION_ENABLED = "moderation.enabled"
    PAYMENTS = "payments"
    AI_VALIDATION = "ai.validation"
    QUESTS_NODES_REDIRECT = "quests.nodes_redirect"


# Predefined feature flags available in the system with optional descriptions.
KNOWN_FLAGS: dict[FeatureFlagKey, str] = {
    FeatureFlagKey.MODERATION_ENABLED: "Enable moderation section in admin UI",
    FeatureFlagKey.PAYMENTS: "Enable payments module",
    FeatureFlagKey.AI_VALIDATION: "Enable AI-based validation for nodes",
    FeatureFlagKey.QUESTS_NODES_REDIRECT: (
        "Redirect /nodes/:slug to /quests/{id}/versions/current"
    ),
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

    for key in existing:
        try:
            FeatureFlagKey(key)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Unknown feature flag: {key}") from exc

    created = False
    for key, desc in KNOWN_FLAGS.items():
        if key.value not in existing:
            db.add(FeatureFlag(key=key.value, value=False, description=desc))
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
    key: FeatureFlagKey | str,
    value: bool | None = None,
    description: str | None = None,
    updated_by: str | None = None,
) -> FeatureFlag:
    try:
        key_enum = FeatureFlagKey(key)
    except ValueError as exc:
        raise ValueError(f"Unknown feature flag: {key}") from exc

    existing = await db.get(FeatureFlag, key_enum.value)
    if existing is None:
        existing = FeatureFlag(
            key=key_enum.value, value=bool(value) if value is not None else False
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
