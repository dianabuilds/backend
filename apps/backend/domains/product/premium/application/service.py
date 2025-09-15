from __future__ import annotations

from typing import Any


class PremiumService:
    def __init__(self, plans: dict[str, dict[str, Any]] | None = None) -> None:
        # plans: plan_slug -> {quota_key: {"month": limit}, "__grace__": 0}
        self._plans = plans or {"free": {"__grace__": 0, "stories": {"month": 0}}}
        self._user_plans: dict[str, str] = {}
        self._usage: dict[tuple[str, str, str], int] = (
            {}
        )  # (user_id, quota_key, scope) -> used

    async def set_user_plan(self, user_id: str, plan: str) -> None:
        self._user_plans[str(user_id)] = str(plan)

    async def get_effective_plan_slug(self, user_id: str | None) -> str:
        if not user_id:
            return "free"
        return self._user_plans.get(str(user_id), "free")

    async def get_quota_status(
        self, user_id: str, *, quota_key: str, scope: str = "month"
    ) -> dict:
        plan = await self.get_effective_plan_slug(user_id)
        conf = self._plans.get(plan, {})
        total = int(((conf.get(quota_key) or {}).get(scope)) or 0)
        used = int(self._usage.get((str(user_id), quota_key, scope), 0))
        return {"limit": total, "used": used, "remaining": max(0, total - used)}
