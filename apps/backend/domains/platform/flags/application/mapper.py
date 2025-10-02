from __future__ import annotations

from domains.platform.flags.domain.models import (
    FeatureFlag,
    Flag,
    FlagRule,
    FlagRuleType,
    FlagStatus,
)


def feature_from_legacy(flag: Flag) -> FeatureFlag:
    status = _infer_status(flag)
    rules: list[FlagRule] = []
    for user in sorted(flag.users):
        rules.append(
            FlagRule(
                type=FlagRuleType.USER,
                value=user,
                priority=10,
            )
        )
    for segment in sorted(flag.segments):
        rules.append(
            FlagRule(
                type=FlagRuleType.SEGMENT,
                value=segment,
                priority=15,
            )
        )
    for role in sorted(flag.roles):
        rules.append(
            FlagRule(
                type=FlagRuleType.ROLE,
                value=role,
                priority=20,
            )
        )
    if flag.rollout not in (None, 0, 100):
        rules.append(
            FlagRule(
                type=FlagRuleType.PERCENTAGE,
                value="default",
                rollout=int(flag.rollout),
                priority=30,
            )
        )
    return FeatureFlag(
        slug=flag.slug,
        status=status,
        description=flag.description,
        rollout=flag.rollout,
        rules=tuple(rules),
        meta=dict(flag.meta or {}),
    )


def legacy_from_feature(feature: FeatureFlag) -> Flag:
    enabled = feature.status is not FlagStatus.DISABLED
    rollout = feature.rollout
    if rollout is None:
        rollout = 100 if enabled else 0
    percentage_rules = [
        rule.rollout
        for rule in feature.rules
        if rule.type is FlagRuleType.PERCENTAGE and rule.rollout is not None
    ]
    if percentage_rules:
        rollout = percentage_rules[0]
    users = {rule.value for rule in feature.rules if rule.type is FlagRuleType.USER}
    segments = {rule.value for rule in feature.rules if rule.type is FlagRuleType.SEGMENT}
    roles = {rule.value for rule in feature.rules if rule.type is FlagRuleType.ROLE}
    if feature.status is FlagStatus.PREMIUM:
        roles.add("premium")
    return Flag(
        slug=feature.slug,
        enabled=enabled,
        description=feature.description,
        rollout=int(rollout),
        users=users,
        roles=roles,
        segments=segments,
        meta=dict(feature.meta or {}),
    )


def _infer_status(flag: Flag) -> FlagStatus:
    if not flag.enabled:
        return FlagStatus.DISABLED
    if any(role.lower() == "premium" for role in flag.roles):
        return FlagStatus.PREMIUM
    if flag.users:
        return FlagStatus.TESTERS
    if flag.segments:
        return FlagStatus.CUSTOM
    if flag.rollout not in (None, 0, 100):
        return FlagStatus.CUSTOM
    return FlagStatus.ALL


__all__ = ["feature_from_legacy", "legacy_from_feature"]
