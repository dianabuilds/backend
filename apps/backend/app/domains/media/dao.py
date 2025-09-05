from __future__ import annotations

import builtins
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.db.pagination import scope_by_workspace

from .models import MediaAsset


class MediaAssetDAO:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> MediaAsset:
        asset = MediaAsset(**kwargs)
        db.add(asset)
        await db.flush()
        return asset

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[MediaAsset]:
        stmt = select(MediaAsset).order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
        stmt = scope_by_workspace(stmt, workspace_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
