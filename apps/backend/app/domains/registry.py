from __future__ import annotations

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def register_domain_routers(app: FastAPI) -> None:
    """
    Подключает роутеры доменов. Вызывается из app/main.py до SPA fallback.
    На старте миграции подключаем только те домены, где уже есть доменные роутеры.
    """
    # Auth
    try:
        from app.domains.auth.api.routers import router as auth_router

        app.include_router(auth_router)
    except Exception as exc:
        logger.exception("Failed to load auth router. Startup aborted")
        raise RuntimeError("Failed to load auth router") from exc

    # AI
    try:
        from app.domains.ai.api.routers import router as ai_router

        app.include_router(ai_router)
    except Exception as exc:
        logger.exception("Failed to load ai router. Startup aborted")
        raise RuntimeError("Failed to load ai router") from exc

    # Quests
    try:
        from app.domains.quests.api.routers import router as quests_router

        app.include_router(quests_router)
    except Exception as exc:
        logger.exception("Failed to load quests router. Startup aborted")
        raise RuntimeError("Failed to load quests router") from exc

    # Moderation
    try:
        from app.domains.moderation.api.routers import router as moderation_router

        app.include_router(moderation_router)
    except Exception as exc:
        logger.exception("Failed to load moderation router. Startup aborted")
        raise RuntimeError("Failed to load moderation router") from exc

    # Notifications
    try:
        from app.domains.notifications.api.routers import router as notifications_router

        app.include_router(notifications_router)
    except Exception as exc:
        logger.exception("Failed to load notifications router. Startup aborted")
        raise RuntimeError("Failed to load notifications router") from exc
    # Notifications WS
    try:
        from app.domains.notifications.api.routers import (
            ws_router as notifications_ws_router,
        )

        app.include_router(notifications_ws_router)
    except Exception as exc:
        logger.exception("Failed to load notifications ws router. Startup aborted")
        raise RuntimeError("Failed to load notifications ws router") from exc
    # Admin Notifications
    try:
        from app.domains.notifications.api.admin_router import (
            router as admin_notifications_router,
        )

        app.include_router(admin_notifications_router)
    except Exception as exc:
        logger.exception("Failed to load admin notifications router. Startup aborted")
        raise RuntimeError("Failed to load admin notifications router") from exc
    # Admin Notifications Broadcast
    try:
        from app.domains.notifications.api.broadcast_router import (
            router as admin_notifications_broadcast_router,
        )

        app.include_router(admin_notifications_broadcast_router)
    except Exception as exc:
        logger.exception(
            "Failed to load admin notifications broadcast router. Startup aborted"
        )
        raise RuntimeError(
            "Failed to load admin notifications broadcast router"
        ) from exc
    # Admin Notifications Campaigns
    try:
        from app.domains.notifications.api.campaigns_router import (
            router as admin_notifications_campaigns_router,
        )

        app.include_router(admin_notifications_campaigns_router)
    except Exception as exc:
        logger.exception(
            "Failed to load admin notifications campaigns router. Startup aborted"
        )
        raise RuntimeError(
            "Failed to load admin notifications campaigns router"
        ) from exc

    # Payments
    try:
        from app.domains.payments.api.routers import router as payments_router

        app.include_router(payments_router)
    except Exception as exc:
        logger.exception("Failed to load payments router. Startup aborted")
        raise RuntimeError("Failed to load payments router") from exc
    # Payments Admin
    try:
        from app.domains.payments.api_admin import router as payments_admin_router

        app.include_router(payments_admin_router)
    except Exception as exc:
        logger.exception("Failed to load payments admin router. Startup aborted")
        raise RuntimeError("Failed to load payments admin router") from exc

    # Premium
    try:
        from app.domains.premium.api.routers import router as premium_router

        app.include_router(premium_router)
    except Exception as exc:
        logger.exception("Failed to load premium router. Startup aborted")
        raise RuntimeError("Failed to load premium router") from exc
    # Premium Admin
    try:
        from app.domains.premium.api_admin import router as premium_admin_router

        app.include_router(premium_admin_router)
    except Exception as exc:
        logger.exception("Failed to load premium admin router. Startup aborted")
        raise RuntimeError("Failed to load premium admin router") from exc

    # Media
    try:
        from app.domains.media.api.routers import router as media_router

        app.include_router(media_router)
        app.include_router(media_router, prefix="/workspaces/{workspace_id}")
    except Exception as exc:
        logger.exception("Failed to load media router. Startup aborted")
        raise RuntimeError("Failed to load media router") from exc

    # Achievements
    try:
        from app.domains.achievements.api.routers import router as achievements_router

        app.include_router(achievements_router)
    except Exception as exc:
        logger.exception("Failed to load achievements router. Startup aborted")
        raise RuntimeError("Failed to load achievements router") from exc

    # Navigation
    try:
        from app.domains.navigation.api.routers import router as navigation_router

        app.include_router(navigation_router)
    except Exception as exc:
        logger.exception("Failed to load navigation router. Startup aborted")
        raise RuntimeError("Failed to load navigation router") from exc
    try:
        from app.domains.navigation.api.transitions_router import (
            router as transitions_router,
        )

        app.include_router(transitions_router)
    except Exception as exc:
        logger.exception("Failed to load transitions router. Startup aborted")
        raise RuntimeError("Failed to load transitions router") from exc
    # Navigation public traces
    try:
        from app.domains.navigation.api.traces_router import (
            router as public_traces_router,
        )

        app.include_router(public_traces_router)
    except Exception as exc:
        logger.exception("Failed to load public traces router. Startup aborted")
        raise RuntimeError("Failed to load public traces router") from exc
    # Navigation public navigation
    try:
        from app.domains.navigation.api.public_navigation_router import (
            router as public_navigation_router,
        )

        app.include_router(public_navigation_router)
    except Exception as exc:
        logger.exception("Failed to load public navigation router. Startup aborted")
        raise RuntimeError("Failed to load public navigation router") from exc

    # Nodes
    try:
        from app.domains.nodes.api.nodes_router import router as nodes_router

        app.include_router(nodes_router)
        app.include_router(nodes_router, prefix="/workspaces/{workspace_id}")
    except Exception as exc:
        logger.exception("Failed to load nodes router. Startup aborted")
        raise RuntimeError("Failed to load nodes router") from exc

    # Tags
    try:
        from app.domains.tags.api.routers import router as tags_router

        app.include_router(tags_router)
    except Exception as exc:
        logger.exception("Failed to load tags router. Startup aborted")
        raise RuntimeError("Failed to load tags router") from exc

    # Search
    try:
        from app.domains.search.api.routers import router as search_router

        app.include_router(search_router)
    except Exception as exc:
        logger.exception("Failed to load search router. Startup aborted")
        raise RuntimeError("Failed to load search router") from exc

    # Admin
    try:
        from app.domains.admin.api.routers import router as admin_router

        app.include_router(admin_router)
    except Exception as exc:
        logger.exception("Failed to load admin router. Startup aborted")
        raise RuntimeError("Failed to load admin router") from exc
    # Admin flags
    try:
        from app.domains.admin.api.flags_router import router as admin_flags_router

        app.include_router(admin_flags_router)
    except Exception as exc:
        logger.exception("Failed to load admin flags router. Startup aborted")
        raise RuntimeError("Failed to load admin flags router") from exc
    # Admin cache
    try:
        from app.domains.admin.api.cache_router import router as admin_cache_router

        app.include_router(admin_cache_router)
    except Exception as exc:
        logger.exception("Failed to load admin cache router. Startup aborted")
        raise RuntimeError("Failed to load admin cache router") from exc
    # Admin jobs
    try:
        from app.domains.admin.api.jobs_router import router as admin_jobs_router

        app.include_router(admin_jobs_router)
    except Exception as exc:
        logger.exception("Failed to load admin jobs router. Startup aborted")
        raise RuntimeError("Failed to load admin jobs router") from exc
    # Admin dashboard
    try:
        from app.domains.admin.api.dashboard_router import (
            router as admin_dashboard_router,
        )

        app.include_router(admin_dashboard_router)
    except Exception as exc:
        logger.exception("Failed to load admin dashboard router. Startup aborted")
        raise RuntimeError("Failed to load admin dashboard router") from exc
    # Admin hotfix patches
    try:
        from app.domains.admin.api.hotfix_patches_router import (
            router as admin_hotfix_patches_router,
        )

        app.include_router(admin_hotfix_patches_router)
    except Exception as exc:
        logger.exception("Failed to load admin hotfix patches router. Startup aborted")
        raise RuntimeError("Failed to load admin hotfix patches router") from exc
    # AI Admin routers are included via app.domains.ai.api.routers aggregator
    # Quests admin validation
    try:
        from app.domains.quests.api.admin_validation_router import (
            router as quests_admin_validation_router,
        )

        app.include_router(quests_admin_validation_router)
    except Exception as exc:
        logger.exception(
            "Failed to load quests admin validation router. Startup aborted"
        )
        raise RuntimeError("Failed to load quests admin validation router") from exc
    # Admin users
    try:
        from app.domains.users.api.admin_router import router as admin_users_router

        app.include_router(admin_users_router)
    except Exception as exc:
        logger.exception("Failed to load admin users router. Startup aborted")
        raise RuntimeError("Failed to load admin users router") from exc
    # Admin workspaces
    try:
        from app.domains.workspaces.api import router as admin_workspaces_router

        app.include_router(admin_workspaces_router)
    except Exception as exc:
        logger.exception("Failed to load admin workspaces router. Startup aborted")
        raise RuntimeError("Failed to load admin workspaces router") from exc
    # Admin nodes content
    try:
        from app.domains.nodes.api.content_router import (
            router as admin_nodes_content_router,
        )

        app.include_router(admin_nodes_content_router)
    except Exception as exc:
        logger.exception("Failed to load admin nodes content router. Startup aborted")
        raise RuntimeError("Failed to load admin nodes content router") from exc
    # Admin articles (isolated nodes)
    try:
        from app.domains.nodes.api.articles_admin_router import (
            router as admin_articles_router,
        )

        app.include_router(admin_articles_router)
    except Exception as exc:
        logger.exception("Failed to load admin articles router. Startup aborted")
        raise RuntimeError("Failed to load admin articles router") from exc
    # Admin nodes
    try:
        from app.domains.nodes.api.admin_nodes_router import (
            router as admin_nodes_router,
        )

        app.include_router(admin_nodes_router)
    except Exception as exc:
        logger.exception("Failed to load admin nodes router. Startup aborted")
        raise RuntimeError("Failed to load admin nodes router") from exc
    # Admin drafts
    try:
        from app.domains.nodes.api.admin_drafts_router import (
            router as admin_drafts_router,
        )

        app.include_router(admin_drafts_router)
    except Exception as exc:
        logger.exception("Failed to load admin drafts router. Startup aborted")
        raise RuntimeError("Failed to load admin drafts router") from exc
    # Admin quest steps
    try:
        from app.api.admin.quests.steps import graph_router as admin_quest_graph_router
        from app.api.admin.quests.steps import router as admin_quest_steps_router

        app.include_router(admin_quest_steps_router)
        app.include_router(admin_quest_graph_router)
    except Exception as exc:
        logger.exception("Failed to load admin quest steps router. Startup aborted")
        raise RuntimeError("Failed to load admin quest steps router") from exc
    # Admin transitions
    try:
        from app.domains.navigation.api.admin_transitions_router import (
            router as admin_transitions_router,
        )

        app.include_router(admin_transitions_router)
    except Exception as exc:
        logger.exception("Failed to load admin transitions router. Startup aborted")
        raise RuntimeError("Failed to load admin transitions router") from exc
    # Admin transitions simulate
    try:
        from app.domains.navigation.api.admin_transitions_simulate import (
            router as admin_transitions_simulate_router,
        )

        app.include_router(admin_transitions_simulate_router)
    except Exception as exc:
        logger.exception(
            "Failed to load admin transitions simulate router. Startup aborted"
        )
        raise RuntimeError("Failed to load admin transitions simulate router") from exc
    # Admin rate limit
    try:
        from app.domains.admin.api.ratelimit_router import (
            router as admin_ratelimit_router,
        )

        app.include_router(admin_ratelimit_router)
    except Exception as exc:
        logger.exception("Failed to load admin ratelimit router. Startup aborted")
        raise RuntimeError("Failed to load admin ratelimit router") from exc
    # Admin audit
    try:
        from app.domains.admin.api.audit_router import router as admin_audit_router

        app.include_router(admin_audit_router)
    except Exception as exc:
        logger.exception("Failed to load admin audit router. Startup aborted")
        raise RuntimeError("Failed to load admin audit router") from exc
    # Admin metrics (telemetry)
    try:
        from app.domains.telemetry.api.admin_metrics_router import (
            router as admin_metrics_router,
        )

        app.include_router(admin_metrics_router)
    except Exception as exc:
        logger.exception("Failed to load admin metrics router. Startup aborted")
        raise RuntimeError("Failed to load admin metrics router") from exc
    # Admin tags
    try:
        from app.domains.tags.api.admin_router import router as admin_tags_router

        app.include_router(admin_tags_router)
    except Exception as exc:
        logger.exception("Failed to load admin tags router. Startup aborted")
        raise RuntimeError("Failed to load admin tags router") from exc
    # Admin echo (navigation)
    try:
        from app.domains.navigation.api.admin_echo_router import (
            router as admin_echo_router,
        )

        app.include_router(admin_echo_router)
    except Exception as exc:
        logger.exception("Failed to load admin echo router. Startup aborted")
        raise RuntimeError("Failed to load admin echo router") from exc
    # Admin traces (navigation)
    try:
        from app.domains.navigation.api.admin_traces_router import (
            router as admin_traces_router,
        )

        app.include_router(admin_traces_router)
    except Exception as exc:
        logger.exception("Failed to load admin traces router. Startup aborted")
        raise RuntimeError("Failed to load admin traces router") from exc
    # Admin navigation tools
    try:
        from app.domains.navigation.api.admin_navigation_router import (
            router as admin_navigation_router,
        )

        app.include_router(admin_navigation_router)
    except Exception as exc:
        logger.exception("Failed to load admin navigation router. Startup aborted")
        raise RuntimeError("Failed to load admin navigation router") from exc
    # Admin moderation cases
    try:
        from app.domains.moderation.api.cases_router import (
            router as admin_moderation_cases_router,
        )

        app.include_router(admin_moderation_cases_router)
    except Exception as exc:
        logger.exception(
            "Failed to load admin moderation cases router. Startup aborted"
        )
        raise RuntimeError("Failed to load admin moderation cases router") from exc
    # Admin restrictions
    try:
        from app.domains.moderation.api.restrictions_router import (
            router as admin_restrictions_router,
        )

        app.include_router(admin_restrictions_router)
    except Exception as exc:
        logger.exception("Failed to load admin restrictions router. Startup aborted")
        raise RuntimeError("Failed to load admin restrictions router") from exc
    # AI settings/stats are included via app.domains.ai.api.routers aggregator
    # Admin Search
    try:
        from app.domains.search.api.admin_router import router as admin_search_router

        app.include_router(admin_search_router)
    except Exception as exc:
        logger.exception("Failed to load admin search router. Startup aborted")
        raise RuntimeError("Failed to load admin search router") from exc

    # Worlds
    try:
        from app.domains.worlds.api.routers import router as worlds_router

        app.include_router(worlds_router)
    except Exception as exc:
        logger.exception("Failed to load worlds router. Startup aborted")
        raise RuntimeError("Failed to load worlds router") from exc

    # Users
    try:
        from app.domains.users.api.routers import router as users_router

        app.include_router(users_router)
    except Exception as exc:
        logger.exception("Failed to load users router. Startup aborted")
        raise RuntimeError("Failed to load users router") from exc
