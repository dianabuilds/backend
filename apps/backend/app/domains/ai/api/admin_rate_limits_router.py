from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import admin_required
from app.domains.ai.rate_limit import set_limits_from_dict, get_limits_snapshot

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/rate_limits")
async def get_rate_limits(_=Depends(admin_required)) -> Dict[str, Any]:
    """
    Текущие рантайм-лимиты RPM по провайдерам и моделям (оверрайды).
    """
    return get_limits_snapshot()


@router.post("/rate_limits")
async def set_rate_limits(payload: Dict[str, Any], _=Depends(admin_required)) -> Dict[str, Any]:
    """
    Установить рантайм-лимиты RPM.
    Формат:
    {
      "providers": { "openai": 60, "anthropic": 30, "openai_compatible": 45 },
      "models": { "gpt-4o-mini": 120, "claude-3-haiku": 100 }
    }
    Значения null/0/"" — удаляют оверрайд.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")
    set_limits_from_dict(payload)
    return {"ok": True, **get_limits_snapshot()}
