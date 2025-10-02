from __future__ import annotations

from domains.platform.flags.api import http
from domains.platform.flags.domain.models import (
    FeatureFlag,
    FlagRule,
    FlagRuleType,
    FlagStatus,
)


def make_flag(**kwargs) -> FeatureFlag:
    defaults = dict(
        slug="demo",
        status=FlagStatus.ALL,
        description=None,
        rollout=100,
        rules=(),
        meta={},
        created_at=None,
        updated_at=None,
        created_by=None,
        updated_by=None,
    )
    defaults.update(kwargs)
    return FeatureFlag(**defaults)


def test_audience_hint_from_status_all():
    flag = make_flag(status=FlagStatus.ALL)
    assert http._audience_hint(flag) == "all"


def test_audience_hint_from_rules_custom():
    flag = make_flag(
        status=FlagStatus.DISABLED,
        rules=(
            FlagRule(
                type=FlagRuleType.SEGMENT,
                value="beta",
                rollout=None,
                priority=10,
                meta=None,
            ),
        ),
    )
    assert http._audience_hint(flag) == "custom"


def test_serialize_flag_includes_effective_and_audience():
    flag = make_flag(
        status=FlagStatus.TESTERS,
        rules=(FlagRule(type=FlagRuleType.USER, value="u1", rollout=None, priority=10, meta=None),),
    )
    payload = http._serialize_flag(flag, effective=True)
    assert payload["effective"] is True
    assert payload["audience"] == "testers"
