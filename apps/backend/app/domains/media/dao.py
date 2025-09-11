from __future__ import annotations

import builtins

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[MediaAsset]:
        """List media assets (profile-centric)."""
        stmt = select(MediaAsset).order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
