from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.infrastructure.models.notification_settings_models import (
    NodeNotificationSetting,
)


class NodeNotificationSettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, user_id: UUID, node_id: UUID) -> NodeNotificationSetting | None:
        res = await self._db.execute(
            select(NodeNotificationSetting).where(
                NodeNotificationSetting.user_id == user_id,
                NodeNotificationSetting.node_alt_id == node_id,
            )
        )
        return res.scalar_one_or_none()

    async def upsert(self, user_id: UUID, node_id: UUID, enabled: bool) -> NodeNotificationSetting:
        setting = await self.get(user_id, node_id)
        if setting:
            setting.enabled = enabled
        else:
            nodes = sa.table(
                "nodes",
                sa.column("id", sa.BigInteger()),
                sa.column("alt_id", sa.String()),
            )
            node_pk = await self._db.execute(
                select(nodes.c.id).where(nodes.c.alt_id == str(node_id))
            )
            node_pk_id = node_pk.scalar_one()
            setting = NodeNotificationSetting(
                user_id=user_id,
                node_alt_id=node_id,
                node_id=node_pk_id,
                enabled=enabled,
            )
            self._db.add(setting)
        await self._db.commit()
        await self._db.refresh(setting)
        return setting
