from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.application.pricing_service import estimate_cost_usd
from app.domains.ai.infrastructure.models.usage_models import AIUsage
from app.domains.ai.providers.base import LLMUsage

logger = logging.getLogger(__name__)


async def record_usage(
    db: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID | None,
    provider: str,
    model: str,
    usage: LLMUsage,
    cost: float | None = None,
) -> None:
    """Persist usage statistics for an LLM call."""
    try:
        calc_cost = cost
        if calc_cost is None:
            calc_cost = estimate_cost_usd(
                model, usage.prompt_tokens, usage.completion_tokens
            )
        row = AIUsage(
            workspace_id=workspace_id,
            user_id=user_id,
            provider=provider,
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost=float(calc_cost) if calc_cost is not None else None,
        )
        db.add(row)
        await db.flush()
    except Exception as e:
        logger.warning("record_usage failed: %s", e)
