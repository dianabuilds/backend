from __future__ import annotations

import pytest

from domains.platform.flags.application.mapper import legacy_from_feature
from domains.platform.flags.application.service import FlagService
from domains.platform.flags.domain.models import (
    FeatureFlag,
    Flag,
    FlagRule,
    FlagRuleType,
    FlagStatus,
)
from domains.platform.flags.ports import FlagStore


class MemoryStore(FlagStore):
    def __init__(self, features: list[FeatureFlag] | None = None) -> None:
        self._flags: dict[str, Flag] = {}
        if features:
            for feature in features:
                self._flags[feature.slug] = legacy_from_feature(feature)

    async def get(self, slug: str) -> Flag | None:
        return self._flags.get(slug)

    async def upsert(self, flag: Flag) -> Flag:
        self._flags[flag.slug] = flag
        return flag

    async def delete(self, slug: str) -> None:
        self._flags.pop(slug, None)

    async def list(self) -> list[Flag]:
        return list(self._flags.values())


@pytest.mark.asyncio
async def test_evaluate_disabled_flag() -> None:
    service = FlagService(
        store=MemoryStore(
            [
                FeatureFlag(slug="disabled", status=FlagStatus.DISABLED, meta={}),
            ]
        )
    )
    assert await service.evaluate("disabled", {}) is False


@pytest.mark.asyncio
async def test_evaluate_testers_flag() -> None:
    feature = FeatureFlag(
        slug="beta",
        status=FlagStatus.TESTERS,
        rules=(FlagRule(type=FlagRuleType.USER, value="u1", priority=10),),
        meta={},
    )
    service = FlagService(store=MemoryStore([feature]))
    assert await service.evaluate("beta", {"sub": "u1"}) is True
    assert await service.evaluate("beta", {"sub": "u2"}) is False


@pytest.mark.asyncio
async def test_evaluate_premium_flag() -> None:
    feature = FeatureFlag(slug="premium", status=FlagStatus.PREMIUM, meta={})
    service = FlagService(store=MemoryStore([feature]))
    assert await service.evaluate("premium", {"role": "premium"}) is True
    assert await service.evaluate("premium", {"plan": "Premium"}) is True
    assert await service.evaluate("premium", {"sub": "u1"}) is False


@pytest.mark.asyncio
async def test_evaluate_percentage_rule() -> None:
    feature = FeatureFlag(
        slug="gradual",
        status=FlagStatus.CUSTOM,
        rules=(
            FlagRule(
                type=FlagRuleType.PERCENTAGE,
                value="default",
                rollout=100,
                priority=1,
            ),
        ),
        meta={},
    )
    service = FlagService(store=MemoryStore([feature]))
    assert await service.evaluate("gradual", {"sub": "u1"}) is True


@pytest.mark.asyncio
async def test_upsert_reads_status() -> None:
    store = MemoryStore()
    service = FlagService(store=store)
    result = await service.upsert(
        {
            "slug": "testers",
            "status": "testers",
            "testers": ["u1"],
            "description": "Beta",
        }
    )
    assert result.status is FlagStatus.TESTERS
    assert "u1" in result.testers


@pytest.mark.asyncio
async def test_evaluate_segment_rule() -> None:
    feature = FeatureFlag(
        slug="segments",
        status=FlagStatus.CUSTOM,
        rules=(FlagRule(type=FlagRuleType.SEGMENT, value="beta", priority=15),),
        meta={},
    )
    service = FlagService(store=MemoryStore([feature]))
    assert await service.evaluate("segments", {"segments": ["beta"]}) is True
    assert await service.evaluate("segments", {"segments": ["alpha"]}) is False


@pytest.mark.asyncio
async def test_upsert_preserves_segments() -> None:
    store = MemoryStore()
    service = FlagService(store=store)
    await service.upsert(
        {
            "slug": "segment-rollout",
            "status": "custom",
            "segments": ["beta", "qa"],
        }
    )
    stored = await service.get("segment-rollout")
    assert stored is not None
    assert {"beta", "qa"}.issubset(stored.segments)
