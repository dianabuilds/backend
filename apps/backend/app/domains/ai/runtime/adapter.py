from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.ai_system_v2 import AIModel, AIRoutingProfile
from app.domains.ai.infrastructure.repositories.system_v2_repository import (
    ModelsRepository,
    ProfilesRepository,
)


@dataclass
class RouteDecision:
    provider_id: str
    model_id: str
    params: dict[str, Any]


async def route(
    session: AsyncSession, task: str, user_context: dict[str, Any], payload: dict[str, Any]
) -> RouteDecision:
    """Select a provider/model per routing profiles and context.

    Minimal implementation: pick first enabled rule matching task and capability hints.
    """
    prof_repo = ProfilesRepository(session)
    model_repo = ModelsRepository(session)
    profiles = await prof_repo.list()
    # choose first enabled profile (later: select based on user_context)
    profile: AIRoutingProfile | None = next((p for p in profiles if p.enabled), None)
    if profile is None:
        raise RuntimeError("no routing profiles configured")
    # Prefetch models
    models = {str(m.id): m for m in await model_repo.list()}
    for rule in profile.rules or []:
        if (rule or {}).get("task") != task:
            continue
        sel = (rule or {}).get("selector") or {}
        caps_req = set(sel.get("capabilities") or [])
        m: AIModel | None = models.get(((rule or {}).get("route") or {}).get("model_id"))
        if m is None:
            continue
        caps_have = set(m.capabilities or [])
        if not caps_req.issubset(caps_have):
            continue
        params = ((rule.get("route") or {}).get("params")) or {}
        return RouteDecision(provider_id=str(m.provider_id), model_id=str(m.id), params=params)
    raise RuntimeError("no matching rule found for task")


__all__ = ["RouteDecision", "route"]
