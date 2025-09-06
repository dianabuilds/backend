from __future__ import annotations  # mypy: ignore-errors

import time
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag
from app.domains.users.infrastructure.models.user import User

_CACHE_TTL = 30  # seconds
_cache: tuple[float, dict[str, tuple[bool, str]]] | None = None


# Predefined feature flags available in the system with optional descriptions.
class FeatureFlagKey(StrEnum):
    PAYMENTS = "payments"
    AI_VALIDATION = "ai.validation"
    REFERRALS_PROGRAM = "referrals.program"
    AI_QUEST_WIZARD = "ai.quest_wizard"
    CONTENT_SCHEDULING = "content.scheduling"
    ADMIN_BETA_DASHBOARD = "admin.beta_dashboard"
    NOTIFICATIONS_DIGEST = "notifications.digest"
    PREMIUM_GIFTING = "premium.gifting"
    NODE_NAVIGATION_V2 = "nodes.navigation_v2"
    WEIGHTED_MANUAL_TRANSITIONS = "navigation.weighted_manual_transitions"
    FALLBACK_POLICY = "navigation.fallback_policy"
    ADMIN_OVERRIDE = "admin.override"
    NAV_CACHE_V2 = "navigation.cache_v2"
    PROFILE_ENABLED = "profile.enabled"
    ROUTING_ACCOUNTS_V2 = "routing.accounts_v2"


# Predefined feature flags available in the system with optional descriptions
# and default audience.
KNOWN_FLAGS: dict[FeatureFlagKey, tuple[str, str]] = {
    FeatureFlagKey.PAYMENTS: ("Enable payments module", "all"),
    FeatureFlagKey.AI_VALIDATION: ("Enable AI-based validation for nodes", "all"),
    FeatureFlagKey.REFERRALS_PROGRAM: ("Enable referrals program", "all"),
    FeatureFlagKey.AI_QUEST_WIZARD: ("Enable AI Quest Wizard", "premium"),
    FeatureFlagKey.CONTENT_SCHEDULING: ("Enable scheduled publishing for content", "all"),
    FeatureFlagKey.ADMIN_BETA_DASHBOARD: ("Enable beta version of admin dashboard", "all"),
    FeatureFlagKey.NOTIFICATIONS_DIGEST: ("Enable daily notifications digest", "all"),
    FeatureFlagKey.PREMIUM_GIFTING: ("Allow gifting premium subscriptions", "all"),
    FeatureFlagKey.NODE_NAVIGATION_V2: ("Enable experimental node navigation v2", "all"),
    FeatureFlagKey.WEIGHTED_MANUAL_TRANSITIONS: (
        "Enable weighted sorting for manual transitions",
        "all",
    ),
    FeatureFlagKey.FALLBACK_POLICY: (
        "Enable fallback navigation policy",
        "all",
    ),
    FeatureFlagKey.ADMIN_OVERRIDE: ("Enable admin override headers", "all"),
    FeatureFlagKey.NAV_CACHE_V2: (
        "Enable space aware navigation cache",
        "all",
    ),
    FeatureFlagKey.PROFILE_ENABLED: ("Enable user profile feature", "all"),
    FeatureFlagKey.ROUTING_ACCOUNTS_V2: (
        "Enable accounts v2 routing",
        "all",
    ),
}


def _now() -> float:
    return time.time()


async def _load_flags(db: AsyncSession) -> dict[str, tuple[bool, str]]:
    res = await db.execute(select(FeatureFlag))
    items: list[FeatureFlag] = list(res.scalars().all())
    return {it.key: (bool(it.value), it.audience) for it in items}


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
    for key, (desc, audience) in KNOWN_FLAGS.items():
        if key.value not in existing:
            db.add(
                FeatureFlag(
                    key=key.value,
                    value=False,
                    description=desc,
                    audience=audience,
                )
            )
            created = True
    if created:
        await db.flush()
        invalidate_cache()


async def get_flags_map(db: AsyncSession) -> dict[str, tuple[bool, str]]:
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


def _audience_matches(audience: str, user: User | None) -> bool:
    if audience == "all":
        return True
    if audience == "premium":
        return bool(user and getattr(user, "is_premium", False))
    if audience == "beta":
        return bool(user and getattr(user, "is_beta", False))
    return False


async def get_effective_flags(
    db: AsyncSession, preview_header: str | None, user: User | None
) -> set[str]:
    base = await get_flags_map(db)
    active = {k for k, (v, audience) in base.items() if v and _audience_matches(audience, user)}
    preview = parse_preview_flags(preview_header)
    return active.union(preview)


async def set_flag(
    db: AsyncSession,
    key: FeatureFlagKey | str,
    value: bool | None = None,
    description: str | None = None,
    updated_by: str | None = None,
    audience: str | None = None,
) -> FeatureFlag:
    try:
        key_enum = FeatureFlagKey(key)
    except ValueError as exc:
        raise ValueError(f"Unknown feature flag: {key}") from exc

    existing = await db.get(FeatureFlag, key_enum.value)
    if existing is None:
        default_audience = KNOWN_FLAGS.get(key_enum, ("", "all"))[1]
        existing = FeatureFlag(
            key=key_enum.value,
            value=bool(value) if value is not None else False,
            audience=audience or default_audience,
        )
        db.add(existing)
    if value is not None:
        existing.value = bool(value)
    if description is not None:
        existing.description = description
    if updated_by is not None:
        existing.updated_by = updated_by
    if audience is not None:
        existing.audience = audience
    # updated_at обновится за счёт onupdate; в async orm произойдёт на flush/commit
    await db.flush()
    # invalidate cache
    invalidate_cache()
    return existing


def invalidate_cache() -> None:
    global _cache
    _cache = None
