from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_session
from app.models.notification import Notification, NotificationType
from app.models.notification_campaign import NotificationCampaign, CampaignStatus
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services.notification_ws import manager as ws_manager


# Регистр запущенных задач (в памяти)
_tasks: dict[UUID, asyncio.Task] = {}


def _build_user_filter(filters: Dict[str, Any]):
    conds = []
    if not filters:
        return conds
    if (role := filters.get("role")):
        conds.append(User.role == role)
    if filters.get("is_active") is True:
        conds.append(User.is_active.is_(True))
    if filters.get("is_active") is False:
        conds.append(User.is_active.is_(False))
    if filters.get("is_premium") is True:
        conds.append(User.is_premium.is_(True))
    if filters.get("is_premium") is False:
        conds.append(User.is_premium.is_(False))
    if (created_from := filters.get("created_from")):
        conds.append(User.created_at >= created_from)
    if (created_to := filters.get("created_to")):
        conds.append(User.created_at <= created_to)
    return conds


async def estimate_recipients(session: AsyncSession, filters: Dict[str, Any]) -> int:
    stmt = select(User.id)
    conds = _build_user_filter(filters)
    if conds:
        stmt = stmt.where(and_(*conds))
    result = await session.execute(stmt)
    # На больших данных лучше COUNT(*), но здесь достаточно получить все id и сосчитать
    ids = result.scalars().all()
    return len(ids)


async def _send_ws(user_id: UUID, notif: Notification):
    try:
        data = NotificationOut.model_validate(notif).model_dump()
        await ws_manager.send_notification(user_id, data)
    except Exception:
        pass


async def run_campaign(campaign_id: UUID, chunk_size: int = 1000):
    async with db_session() as session:
        camp: Optional[NotificationCampaign] = await session.get(NotificationCampaign, campaign_id)
        if not camp or camp.status in (CampaignStatus.canceled, CampaignStatus.done):
            return
        camp.status = CampaignStatus.running
        camp.started_at = datetime.utcnow()
        await session.commit()

        filters = camp.filters or {}

        # Считаем total
        stmt_ids = select(User.id)
        conds = _build_user_filter(filters)
        if conds:
            stmt_ids = stmt_ids.where(and_(*conds))
        result = await session.execute(stmt_ids)
        user_ids = result.scalars().all()
        camp.total = len(user_ids)
        await session.commit()

        try:
            for i in range(0, len(user_ids), chunk_size):
                # Проверка отмены
                camp2: Optional[NotificationCampaign] = await session.get(NotificationCampaign, campaign_id)
                if not camp2 or camp2.status == CampaignStatus.canceled:
                    break

                batch = user_ids[i:i + chunk_size]
                # Вставка Notifications
                # (Можно оптимизировать bulk_save_objects, но создадим обычные объекты)
                notifs = []
                for uid in batch:
                    notif = Notification(user_id=uid, title=camp.title, message=camp.message, type=NotificationType(camp.type))
                    session.add(notif)
                    notifs.append((uid, notif))
                await session.commit()  # получаем id и created_at

                # Обновляем счётчики
                camp2.sent += len(batch)
                await session.commit()

                # Пуш в WS (не блокируем транзакцию)
                await asyncio.gather(*[_send_ws(uid, n) for uid, n in notifs])

                await asyncio.sleep(0)  # уступаем цикл

            camp3: Optional[NotificationCampaign] = await session.get(NotificationCampaign, campaign_id)
            if camp3 and camp3.status != CampaignStatus.canceled:
                camp3.status = CampaignStatus.done
                camp3.finished_at = datetime.utcnow()
                await session.commit()
        except Exception:
            camp4: Optional[NotificationCampaign] = await session.get(NotificationCampaign, campaign_id)
            if camp4:
                camp4.status = CampaignStatus.failed
                camp4.finished_at = datetime.utcnow()
                await session.commit()


def start_campaign_async(campaign_id: UUID):
    # Уже запущена?
    if campaign_id in _tasks and not _tasks[campaign_id].done():
        return
    _tasks[campaign_id] = asyncio.create_task(run_campaign(campaign_id))


async def cancel_campaign(session: AsyncSession, campaign_id: UUID):
    camp = await session.get(NotificationCampaign, campaign_id)
    if not camp:
        return False
    camp.status = CampaignStatus.canceled
    await session.commit()
    # Задача сама завершится при следующей проверке статуса
    return True
