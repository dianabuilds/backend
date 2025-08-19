from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_config import ConfigVersion, SearchRelevanceActive
from app.schemas.search_settings import (
    RelevancePayload,
    RelevanceGetOut,
    RelevancePutIn,
    RelevanceApplyOut,
    RelevanceDryRunOut,
    DryRunDiffItem,
)

_CACHE_TTL = 30  # seconds
_cache: Tuple[float, int, RelevancePayload, datetime] | None = None


def _now() -> float:
    return time.time()


def _checksum(payload: RelevancePayload) -> str:
    return hashlib.sha256(json.dumps(payload.model_dump(), sort_keys=True).encode()).hexdigest()


async def get_active_relevance(db: AsyncSession) -> RelevanceGetOut:
    global _cache
    if _cache and _cache[0] > _now():
        _, ver, payload, ts = _cache
        return RelevanceGetOut(version=ver, payload=payload, updated_at=ts)
    res = await db.execute(select(SearchRelevanceActive).order_by(SearchRelevanceActive.id.desc()).limit(1))
    row = res.scalars().first()
    if row is None:
        # создаём дефолт
        payload = RelevancePayload()
        active = SearchRelevanceActive(version=1, payload=payload.model_dump(), updated_at=datetime.utcnow())
        db.add(active)
        await db.flush()
        _cache = (_now() + _CACHE_TTL, 1, payload, active.updated_at)
        return RelevanceGetOut(version=1, payload=payload, updated_at=active.updated_at)
    payload = RelevancePayload.model_validate(row.payload)
    _cache = (_now() + _CACHE_TTL, int(row.version), payload, row.updated_at)
    return RelevanceGetOut(version=int(row.version), payload=payload, updated_at=row.updated_at)


async def dry_run_relevance(db: AsyncSession, payload: RelevancePayload, sample: List[str]) -> RelevanceDryRunOut:
    # MVP: Возвращаем заглушку диффа — список запросов без реального пересчёта
    diff: List[DryRunDiffItem] = [
        DryRunDiffItem(query=q, topBefore=[], topAfter=[], moved=[]) for q in (sample or [])
    ]
    warnings: List[str] = []
    return RelevanceDryRunOut(diff=diff, warnings=warnings)


async def apply_relevance(db: AsyncSession, payload: RelevancePayload, actor_id: str | None = None) -> RelevanceApplyOut:
    # версионируем
    # версия = max(version where type='relevance') + 1
    max_ver = (
        await db.execute(select(func.max(ConfigVersion.version)).where(ConfigVersion.type == "relevance"))
    ).scalar() or 0
    ver = int(max_ver) + 1
    cfg = ConfigVersion(
        type="relevance",
        version=ver,
        status="active",
        payload=payload.model_dump(),
        created_at=datetime.utcnow(),
        created_by=actor_id,
        checksum=_checksum(payload),
    )
    db.add(cfg)
    # активная запись
    active = SearchRelevanceActive(version=ver, payload=payload.model_dump(), updated_at=datetime.utcnow(), updated_by=actor_id)
    db.add(active)
    # инвалидация кэша
    global _cache
    _cache = None
    return RelevanceApplyOut(version=ver, payload=payload, updated_at=active.updated_at)


async def rollback_relevance(db: AsyncSession, to_version: int, actor_id: str | None = None) -> RelevanceApplyOut:
    res = await db.execute(
        select(ConfigVersion).where(ConfigVersion.type == "relevance", ConfigVersion.version == to_version)
    )
    cfg = res.scalars().first()
    if not cfg:
        raise ValueError("version_not_found")
    payload = RelevancePayload.model_validate(cfg.payload)
    return await apply_relevance(db, payload, actor_id)
