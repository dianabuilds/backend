from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.moderation.infrastructure.models.moderation_models import UserRestriction
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.core.config import settings
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter

router = APIRouter(prefix="/admin", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()

navcache = NavigationCacheService(CoreCacheAdapter())


@router.get("/dashboard", summary="Admin dashboard data")
async def admin_dashboard(
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    new_registrations = (
        (await db.execute(select(func.count()).select_from(User).where(User.created_at >= day_ago)))).scalar() or 0
    active_premium = ((await db.execute(select(func.count()).select_from(User).where(User.is_premium == True)))).scalar() or 0  # noqa: E712
    nodes_created = ((await db.execute(select(func.count()).select_from(Node).where(Node.created_at >= day_ago)))).scalar() or 0
    quests_created = ((await db.execute(select(func.count()).select_from(Quest).where(Quest.created_at >= day_ago)))).scalar() or 0

    result = await db.execute(select(Node.id, Node.title).order_by(Node.created_at.desc()).limit(5))
    latest_nodes = [{"id": str(row.id), "title": row.title or ""} for row in result.all()]

    result = await db.execute(
        select(UserRestriction.id, UserRestriction.user_id, UserRestriction.reason).order_by(UserRestriction.created_at.desc()).limit(5)
    )
    latest_restrictions = [{"id": str(r.id), "user_id": str(r.user_id), "reason": r.reason or ""} for r in result.all()]

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
        nav_keys = len(await navcache._cache.scan(f"{settings.cache.key_version}:nav*"))
        comp_keys = len(await navcache._cache.scan(f"{settings.cache.key_version}:comp*"))
    except Exception:
        nav_keys = 0
        comp_keys = 0

    return {
        "kpi": {
            "active_users_24h": 0,
            "new_registrations_24h": new_registrations,
            "active_premium": active_premium,
            "nodes_24h": nodes_created,
            "quests_24h": quests_created,
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
