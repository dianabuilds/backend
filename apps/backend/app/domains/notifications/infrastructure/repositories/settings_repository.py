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

    async def get(
        self, user_id: UUID, node_id: int | UUID
    ) -> NodeNotificationSetting | None:
        """Fetch notification settings for a node identified by either id type."""
        nodes = sa.table(
            "nodes",
            sa.column("id", sa.BigInteger()),
            sa.column("alt_id", sa.String()),
        )
        if isinstance(node_id, UUID):
            result = await self._db.execute(
                select(nodes.c.id).where(nodes.c.alt_id == str(node_id))
            )
            row = result.one_or_none()
            if row is None:
                return None
            node_pk = row.id
        else:
            node_pk = node_id
        res = await self._db.execute(
            select(NodeNotificationSetting).where(
                NodeNotificationSetting.user_id == user_id,
                NodeNotificationSetting.node_id == node_pk,
            )
        )
        return res.scalar_one_or_none()

    async def upsert(
        self, user_id: UUID, node_id: int | UUID, enabled: bool
    ) -> NodeNotificationSetting:
        """Create or update notification settings for given node."""
        setting = await self.get(user_id, node_id)
        if setting:
            setting.enabled = enabled
        else:
            nodes = sa.table(
                "nodes",
                sa.column("id", sa.BigInteger()),
                sa.column("alt_id", sa.String()),
            )
            if isinstance(node_id, UUID):
                result = await self._db.execute(
                    select(nodes.c.id).where(nodes.c.alt_id == str(node_id))
                )
                node_pk = result.one().id
            else:
                node_pk = node_id
            setting = NodeNotificationSetting(
                user_id=user_id,
                node_id=node_pk,
                enabled=enabled,
            )
            self._db.add(setting)
        await self._db.commit()
        await self._db.refresh(setting)
        return setting
