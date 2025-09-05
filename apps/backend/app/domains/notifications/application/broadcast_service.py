from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.infrastructure.models.campaign_models import (
    CampaignStatus,
    NotificationCampaign,
)
from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


def _apply_user_filters(q, filters: dict[str, Any]):
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


async def estimate_recipients(db: AsyncSession, filters: dict[str, Any]) -> int:
    q = select(User)
    q = _apply_user_filters(q, filters or {})
    res = await db.execute(q)
    return len(list(res.scalars().all()))


async def run_campaign(db: AsyncSession, campaign_id: UUID) -> None:
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp or camp.status in (CampaignStatus.canceled, CampaignStatus.done):
        return

    camp.status = CampaignStatus.running  # type: ignore[assignment]
    camp.started_at = datetime.utcnow()
    await db.commit()

    filters = camp.filters or {}
    q = select(User.id)
    q = _apply_user_filters(q, filters)
    res = await db.execute(q)
    user_ids = list(res.scalars().all())
    camp.total = len(user_ids)
    await db.commit()

    sent = 0
    failed = 0

    from app.domains.notifications.infrastructure.models.notification_models import (
        Notification,
    )
    from app.domains.notifications.infrastructure.transports.websocket import (
        manager as ws_manager,
    )
    from app.schemas.notification import NotificationOut, NotificationType

    try:
        for uid in user_ids:
            try:
                notif = Notification(
                    user_id=uid,
                    title=camp.title,
                    message=camp.message,
                    type=NotificationType(camp.type),
                )
                db.add(notif)
                await db.commit()
                sent += 1
                try:
                    data = NotificationOut.model_validate(notif).model_dump()
                    await ws_manager.send_notification(uid, data)
                except Exception:
                    pass
            except Exception:
                await db.rollback()
                failed += 1
        camp.status = CampaignStatus.done  # type: ignore[assignment]
    except Exception:
        camp.status = CampaignStatus.failed  # type: ignore[assignment]
    finally:
        camp.sent = sent
        camp.failed = failed
        camp.finished_at = datetime.utcnow()
        await db.commit()


def start_campaign_async(campaign_id: UUID) -> None:
    try:
        from workers.notifications import enqueue_campaign

        enqueue_campaign(campaign_id)
    except Exception as e:  # pragma: no cover - только логирование
        logger.warning(
            "notification_broadcast_enqueue_failed cid=%s err=%s", campaign_id, e
        )


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
