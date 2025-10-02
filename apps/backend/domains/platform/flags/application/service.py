from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from domains.platform.flags.application.mapper import (
    feature_from_legacy,
    legacy_from_feature,
)
from domains.platform.flags.domain.models import FeatureFlag, Flag, FlagStatus
from domains.platform.flags.ports import FlagStore


def _stable_bucket(user_id: str) -> int:
    h = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100


def _coerce_set(values: Any) -> set[str]:
    if not values:
        return set()
    iterable: Iterable[Any]
    if isinstance(values, (set, frozenset, list, tuple)):
        iterable = values
    else:
        iterable = [values]
    return {str(v).strip() for v in iterable if str(v).strip()}


@dataclass
class FlagService:
    store: FlagStore

    async def evaluate(self, slug: str, user: dict[str, Any] | None = None) -> bool:
        flag = await self.store.get(slug)
        if not flag:
            return False
        return self._eval_flag(flag, user or {})

    def _eval_flag(self, flag: Flag | FeatureFlag, user: dict[str, Any]) -> bool:
        if isinstance(flag, FeatureFlag):
            flag = legacy_from_feature(flag)
        if not flag.enabled:
            return False
        uid = str(user.get("sub") or user.get("user_id") or "").strip()
        role = str(user.get("role") or "").lower()
        plan = str(user.get("plan") or "").lower()
        segments = user.get("segments")
        segment_set = _coerce_set(segments)
        has_audience_rules = bool(flag.users or flag.roles or flag.segments)

        if uid and uid in {u.strip() for u in flag.users}:
            return True
        lowered_roles = {r.lower() for r in flag.roles}
        if role and role in lowered_roles:
            return True
        if plan and plan in lowered_roles:
            return True
        if segment_set and segment_set.intersection({s.lower() for s in flag.segments}):
            return True
        if has_audience_rules:
            return False

        rollout = int(flag.rollout or 0)
        if rollout >= 100:
            return True
        if rollout <= 0:
            return False
        if not uid:
            return False
        return _stable_bucket(uid) < rollout

    async def upsert(self, data: dict[str, Any]) -> FeatureFlag:
        slug_raw = str(data.get("slug") or "").strip()
        if not slug_raw:
            raise ValueError("slug_required")

        status_value = str(data.get("status") or "").strip().lower()
        try:
            status = FlagStatus(status_value) if status_value else None
        except ValueError as exc:
            raise ValueError("invalid_status") from exc

        testers = _coerce_set(data.get("testers") or data.get("users"))
        roles = _coerce_set(data.get("roles"))
        segments = _coerce_set(data.get("segments"))

        if status is FlagStatus.PREMIUM:
            roles.add("premium")
        enabled = data.get("enabled")
        if enabled is None:
            enabled = status is not FlagStatus.DISABLED if status is not None else True
        enabled = bool(enabled)
        if status is None:
            status = FlagStatus.ALL if enabled else FlagStatus.DISABLED

        rollout_value = data.get("rollout")
        if rollout_value is None:
            rollout = 0 if status is FlagStatus.DISABLED else 100
        else:
            try:
                rollout = int(rollout_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_rollout") from exc
            rollout = max(0, min(100, rollout))
        if status is FlagStatus.DISABLED:
            rollout = 0

        description = data.get("description")
        description_str = (
            str(description).strip() if isinstance(description, str) else None
        )
        meta_raw = data.get("meta") if isinstance(data.get("meta"), dict) else None
        meta_dict = dict(meta_raw) if isinstance(meta_raw, dict) else None

        flag = Flag(
            slug=slug_raw,
            enabled=enabled,
            description=description_str or None,
            rollout=rollout,
            users=testers,
            roles=roles,
            segments=segments,
            meta=meta_dict,
        )
        stored = await self.store.upsert(flag)
        return feature_from_legacy(stored)

    async def delete(self, slug: str) -> None:
        await self.store.delete(slug)

    async def get(self, slug: str) -> FeatureFlag | None:
        flag = await self.store.get(slug)
        if not flag:
            return None
        return feature_from_legacy(flag)

    async def list(self) -> list[FeatureFlag]:
        flags = await self.store.list()
        return [feature_from_legacy(flag) for flag in flags]


__all__ = ["FlagService"]
