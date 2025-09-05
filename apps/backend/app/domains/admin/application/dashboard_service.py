from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.domains.moderation.infrastructure.models.moderation_models import (
    UserRestriction,
)
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.stats_service import NavigationStatsService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.payments.manager import get_active_subscriptions_stats
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.users.infrastructure.models.user import User
from app.models.ops_incident import OpsIncident
from app.providers.cache import cache as shared_cache

CACHE_KEY = "admin:dashboard"
CACHE_TTL = 60

navcache = NavigationCacheService(CoreCacheAdapter())
nav_stats = NavigationStatsService()


class DashboardService:
    @staticmethod
    async def get_dashboard(db: AsyncSession) -> dict[str, Any]:
        cached = await shared_cache.get(CACHE_KEY)
        if cached:
            return json.loads(cached)

        now = datetime.utcnow()
        day_ago = now - timedelta(hours=24)
        week_ago = now - timedelta(days=7)

        new_registrations = (
            await db.execute(
                select(func.count()).select_from(User).where(User.created_at >= day_ago)
            )
        ).scalar() or 0
        active_premium = (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_premium)
            )
        ).scalar() or 0
        active_subscriptions, active_subscriptions_change = (
            await get_active_subscriptions_stats(db)
        )
        active_users = (
            await db.execute(
                select(func.count())
                .select_from(User)
                .where(User.last_login_at >= day_ago)
            )
        ).scalar() or 0
        nodes_created = (
            await db.execute(
                select(func.count())
                .select_from(Node)
                .where(Node.created_at >= week_ago)
            )
        ).scalar() or 0
        nodes_without_outgoing_pct = await nav_stats.get_nodes_without_outgoing_pct(db)
        quests_created = (
            await db.execute(
                select(func.count())
                .select_from(Quest)
                .where(Quest.created_at >= day_ago)
            )
        ).scalar() or 0
        incidents_count = (
            await db.execute(
                select(func.count())
                .select_from(OpsIncident)
                .where(OpsIncident.created_at >= day_ago)
            )
        ).scalar() or 0

        result = await db.execute(
            select(Node.id, Node.title).order_by(Node.created_at.desc()).limit(5)
        )
        latest_nodes = [
            {"id": str(row.id), "title": row.title or ""} for row in result.all()
        ]

        result = await db.execute(
            select(UserRestriction.id, UserRestriction.user_id, UserRestriction.reason)
            .order_by(UserRestriction.created_at.desc())
            .limit(5)
        )
        latest_restrictions = [
            {"id": str(r.id), "user_id": str(r.user_id), "reason": r.reason or ""}
            for r in result.all()
        ]

        db_ok = True
        try:
            await db.execute(select(1))
        except Exception:
            db_ok = False

        redis_ok = True
        try:
            await navcache._cache.get("__healthcheck__")
        except Exception:
            redis_ok = False

        try:
            nav_keys = len(
                await navcache._cache.scan(f"{settings.cache.key_version}:nav*")
            )
            comp_keys = len(
                await navcache._cache.scan(f"{settings.cache.key_version}:comp*")
            )
        except Exception:
            nav_keys = 0
            comp_keys = 0

        data = {
            "kpi": {
                "active_users_24h": active_users,
                "new_registrations_24h": new_registrations,
                "active_premium": active_premium,
                "active_subscriptions": active_subscriptions,
                "active_subscriptions_change_pct": active_subscriptions_change,
                "nodes_7d": nodes_created,
                "nodes_without_outgoing_pct": nodes_without_outgoing_pct,
                "quests_24h": quests_created,
                "incidents_24h": incidents_count,
            },
            "latest_nodes": latest_nodes,
            "latest_restrictions": latest_restrictions,
            "system": {
                "db_ok": db_ok,
                "redis_ok": redis_ok,
                "nav_keys": nav_keys,
                "comp_keys": comp_keys,
            },
        }

        await shared_cache.set(CACHE_KEY, json.dumps(data), CACHE_TTL)
        return data
