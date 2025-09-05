from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.models.generation_models import GenerationJobLog
from app.domains.telemetry.application.raw_payload_service import RawPayloadService
from app.domains.telemetry.infrastructure.raw_payload_store import RawPayloadStore

logger = logging.getLogger(__name__)

_MAX_RAW = 30_000
_MAX_PROMPT = 8_000


async def save_stage_log(
    db: AsyncSession,
    *,
    job_id: Any,
    stage: str,
    provider: str,
    model: str,
    prompt: str,
    raw_response: str,
    usage: dict[str, int],
    cost: float,
    status: str = "ok",
) -> None:
    try:
        safe_prompt = (prompt or "")[:_MAX_PROMPT]
        full_raw = raw_response or ""
        raw_url, truncated = RawPayloadService(RawPayloadStore()).store_large_text(
            full_raw, filename_hint=f"{job_id}-{stage}"
        )
        # Дополнительно ограничим «страховочную» длину, если ENV лимит больше _MAX_RAW
        safe_raw = truncated[:_MAX_RAW]

        log = GenerationJobLog(
            job_id=job_id,
            stage=stage,
            provider=provider,
            model=model,
            prompt=safe_prompt,
            raw_response=safe_raw,  # совместимость
            raw_url=raw_url,
            raw_preview=safe_raw,
            usage=usage,
            cost=float(cost),
            status=status,
        )
        db.add(log)
        await db.flush()
    except Exception as e:
        logger.warning("save_stage_log failed for job %s stage %s: %s", job_id, stage, e)
