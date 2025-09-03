from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.search.application.ports.relevance_port import IRelevanceRepository
from app.models.search_config import ConfigVersion, SearchRelevanceActive
from app.schemas.search_settings import RelevancePayload


class SearchConfigRepository(IRelevanceRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_active(self) -> tuple[int, RelevancePayload, datetime] | None:
        res = await self._db.execute(
            select(SearchRelevanceActive)
            .order_by(SearchRelevanceActive.id.desc())
            .limit(1)
        )
        row = res.scalars().first()
        if row is None:
            return None
        payload = RelevancePayload.model_validate(row.payload)
        return int(row.version), payload, row.updated_at

    async def create_default_active(
        self, *, version: int, payload: RelevancePayload, updated_by: str | None
    ) -> datetime:
        active = SearchRelevanceActive(
            version=version,
            payload=payload.model_dump(),
            updated_at=datetime.utcnow(),
            updated_by=updated_by,
        )
        self._db.add(active)
        await self._db.flush()
        return active.updated_at

    async def get_max_version(self) -> int:
        max_ver = (
            await self._db.execute(
                select(func.max(ConfigVersion.version)).where(
                    ConfigVersion.type == "relevance"
                )
            )
        ).scalar() or 0
        return int(max_ver)

    async def add_version(
        self,
        *,
        version: int,
        payload: RelevancePayload,
        checksum: str,
        created_by: str | None,
    ) -> None:
        cfg = ConfigVersion(
            type="relevance",
            version=version,
            status="active",
            payload=payload.model_dump(),
            created_at=datetime.utcnow(),
            created_by=created_by,
            checksum=checksum,
        )
        self._db.add(cfg)

    async def set_active(
        self, *, version: int, payload: RelevancePayload, updated_by: str | None
    ) -> datetime:
        active = SearchRelevanceActive(
            version=version,
            payload=payload.model_dump(),
            updated_at=datetime.utcnow(),
            updated_by=updated_by,
        )
        self._db.add(active)
        await self._db.flush()
        return active.updated_at

    async def get_version_payload(self, *, version: int) -> RelevancePayload | None:
        res = await self._db.execute(
            select(ConfigVersion).where(
                ConfigVersion.type == "relevance", ConfigVersion.version == int(version)
            )
        )
        cfg = res.scalars().first()
        if not cfg:
            return None
        return RelevancePayload.model_validate(cfg.payload)
