from __future__ import annotations

import pytest

from domains.platform.flags.application.mapper import (
    feature_from_legacy as mapper_feature_from_legacy,
)
from domains.platform.flags.application.mapper import (
    legacy_from_feature as mapper_legacy_from_feature,
)
from domains.platform.flags.domain.models import (
    FeatureFlag,
    Flag,
    FlagRule,
    FlagRuleType,
    FlagStatus,
)


def test_feature_flag_to_legacy_adds_premium_role() -> None:
    feature = FeatureFlag(slug="premium", status=FlagStatus.PREMIUM, meta={})
    legacy = mapper_legacy_from_feature(feature)
    assert legacy.enabled is True
    assert "premium" in {role.lower() for role in legacy.roles}


def test_feature_flag_to_legacy_percentage_rollout() -> None:
    feature = FeatureFlag(
        slug="rollout",
        status=FlagStatus.CUSTOM,
        rollout=None,
        rules=(
            FlagRule(
                type=FlagRuleType.PERCENTAGE, value="default", rollout=30, priority=10
            ),
        ),
        meta={},
    )
    legacy = mapper_legacy_from_feature(feature)
    assert legacy.rollout == 30


def test_legacy_to_feature_flag_infers_status_for_users() -> None:
    legacy = Flag(slug="testers", enabled=True, users={"user-1"}, meta={})
    feature = mapper_feature_from_legacy(legacy)
    assert feature.status is FlagStatus.TESTERS
    assert any(rule.type is FlagRuleType.USER for rule in feature.rules)


def test_legacy_to_feature_flag_percentage_rule() -> None:
    legacy = Flag(
        slug="gradual", enabled=True, rollout=45, meta={}, users=set(), roles=set()
    )
    feature = mapper_feature_from_legacy(legacy)
    assert feature.status is FlagStatus.CUSTOM
    percentage_rules = [
        rule for rule in feature.rules if rule.type is FlagRuleType.PERCENTAGE
    ]
    assert percentage_rules and percentage_rules[0].rollout == 45


@pytest.mark.parametrize(
    "flag_enabled, expected",
    [
        (False, FlagStatus.DISABLED),
        (True, FlagStatus.ALL),
    ],
)
def test_infer_status_default(flag_enabled: bool, expected: FlagStatus) -> None:
    legacy = Flag(slug="default", enabled=flag_enabled, meta={})
    assert __infer_status(legacy) is expected


def __infer_status(flag: Flag) -> FlagStatus:
    return mapper_feature_from_legacy(flag).status


def test_feature_flag_to_legacy_preserves_segments() -> None:
    feature = FeatureFlag(
        slug="segments",
        status=FlagStatus.CUSTOM,
        rules=(FlagRule(type=FlagRuleType.SEGMENT, value="beta", priority=15),),
        meta={},
    )
    legacy = mapper_legacy_from_feature(feature)
    assert "beta" in legacy.segments


def test_legacy_to_feature_flag_segments() -> None:
    legacy = Flag(slug="segments", enabled=True, segments={"beta"}, meta={})
    feature = mapper_feature_from_legacy(legacy)
    assert any(rule.type is FlagRuleType.SEGMENT for rule in feature.rules)
    assert "beta" in feature.segments
