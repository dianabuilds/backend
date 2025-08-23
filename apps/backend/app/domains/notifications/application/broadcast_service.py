from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

from app.domains.notifications.infrastructure.models.campaign_models import NotificationCampaign, CampaignStatus
from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


def _apply_user_filters(q, filters: Dict[str, Any]):
    conds = []
    role = filters.get("role")
    if role:
        conds.append(User.role == role)
    is_active = filters.get("is_active")
    if is_active is not None:
        conds.append(User.is_active.is_(bool(is_active)))
    is_premium = filters.get("is_premium")
    if is_premium is not None:
        conds.append(User.is_premium.is_(bool(is_premium)))
    created_from = filters.get("created_from")
    if created_from:
        conds.append(User.created_at >= created_from)
    created_to = filters.get("created_to")
    if created_to:
        conds.append(User.created_at <= created_to)
    if conds:
        q = q.where(and_(*conds))
    return q


async def estimate_recipients(db: AsyncSession, filters: Dict[str, Any]) -> int:
    q = select(User)
    q = _apply_user_filters(q, filters or {})
    res = await db.execute(q)
    return len(list(res.scalars().all()))


def start_campaign_async(campaign_id: UUID) -> None:
    """
    Лёгкий асинхронный запуск кампании. В реальной системе должен вызывать воркер.
    Здесь — безопасный no-op с логированием, чтобы не блокировать API.
    """
    async def _runner(cid: UUID) -> None:
        try:
            logger.info("notification_broadcast_start cid=%s", cid)
            # Без отдельного sessionmaker не меняем статус — оставляем очередь для внешнего воркера
            await asyncio.sleep(0)  # уступаем цикл
        except Exception as e:
            logger.warning("notification_broadcast_runner error cid=%s: %s", cid, e)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner(campaign_id))
    except RuntimeError:
        # Нет активного цикла (например, при синхронном вызове) — запускаем fire-and-forget
        asyncio.run(_runner(campaign_id))


async def cancel_campaign(db: AsyncSession, campaign_id: UUID) -> bool:
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        return False
    # Разрешаем отмену из очереди/запущенной
    if camp.status in (CampaignStatus.queued, CampaignStatus.running):
        camp.status = CampaignStatus.canceled  # type: ignore[assignment]
        camp.finished_at = datetime.utcnow()
        await db.commit()
        return True
    return False
