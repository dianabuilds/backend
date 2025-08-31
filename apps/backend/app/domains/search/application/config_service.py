from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime

from app.domains.search.application.ports.relevance_port import IRelevanceRepository
from app.schemas.search_settings import (
    DryRunDiffItem,
    RelevanceApplyOut,
    RelevanceDryRunOut,
    RelevanceGetOut,
    RelevancePayload,
)


def _now() -> float:
    return time.time()


def _checksum(payload: RelevancePayload) -> str:
    return hashlib.sha256(
        json.dumps(payload.model_dump(), sort_keys=True).encode()
    ).hexdigest()


class ConfigService:
    _CACHE_TTL = 30  # seconds
    # cls-level кеш: (expires_ts, version, payload, updated_at)
    _cache: tuple[float, int, RelevancePayload, datetime] | None = None

    def __init__(self, repo: IRelevanceRepository) -> None:
        self._repo = repo

    async def get_active_relevance(self) -> RelevanceGetOut:
        if ConfigService._cache and ConfigService._cache[0] > _now():
            _, ver, payload, ts = ConfigService._cache
            return RelevanceGetOut(version=ver, payload=payload, updated_at=ts)

        row = await self._repo.get_active()
        if row is None:
            # создаём дефолт
            payload = RelevancePayload()
            ts = await self._repo.create_default_active(
                version=1, payload=payload, updated_by=None
            )
            ConfigService._cache = (_now() + ConfigService._CACHE_TTL, 1, payload, ts)
            return RelevanceGetOut(version=1, payload=payload, updated_at=ts)

        ver, payload, ts = row
        ConfigService._cache = (
            _now() + ConfigService._CACHE_TTL,
            int(ver),
            payload,
            ts,
        )
        return RelevanceGetOut(version=int(ver), payload=payload, updated_at=ts)

    async def dry_run_relevance(
        self, payload: RelevancePayload, sample: list[str]
    ) -> RelevanceDryRunOut:
        # MVP: Возвращаем заглушку диффа — список запросов без реального пересчёта
        diff: list[DryRunDiffItem] = [
            DryRunDiffItem(query=q, topBefore=[], topAfter=[], moved=[])
            for q in (sample or [])
        ]
        warnings: list[str] = []
        return RelevanceDryRunOut(diff=diff, warnings=warnings)

    async def apply_relevance(
        self, payload: RelevancePayload, actor_id: str | None = None
    ) -> RelevanceApplyOut:
        max_ver = await self._repo.get_max_version()
        ver = int(max_ver) + 1
        cs = _checksum(payload)
        await self._repo.add_version(
            version=ver, payload=payload, checksum=cs, created_by=actor_id
        )
        ts = await self._repo.set_active(
            version=ver, payload=payload, updated_by=actor_id
        )
        ConfigService._cache = None  # invalidate cache
        return RelevanceApplyOut(version=ver, payload=payload, updated_at=ts)

    async def rollback_relevance(
        self, to_version: int, actor_id: str | None = None
    ) -> RelevanceApplyOut:
        payload = await self._repo.get_version_payload(version=int(to_version))
        if not payload:
            raise ValueError("version_not_found")
        return await self.apply_relevance(payload, actor_id)
