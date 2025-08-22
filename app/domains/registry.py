from __future__ import annotations

from fastapi import FastAPI


def register_domain_routers(app: FastAPI) -> None:
    """
    Подключает роутеры доменов. Вызывается из app/main.py до SPA fallback.
    На старте миграции подключаем только те домены, где уже есть доменные роутеры.
    """
    # Auth
    try:
        from app.domains.auth.api.routers import router as auth_router
        app.include_router(auth_router)
    except Exception:
        pass

    # AI
    try:
        from app.domains.ai.api.routers import router as ai_router
        app.include_router(ai_router)
    except Exception:
        pass

    # Quests
    try:
        from app.domains.quests.api.routers import router as quests_router
        app.include_router(quests_router)
    except Exception:
        pass
    # Quests admin versions (domain wrapper)
    try:
        from app.domains.quests.api.admin_versions_router import router as quests_admin_versions_router
        app.include_router(quests_admin_versions_router)
    except Exception:
        pass
    # Quests admin (domain wrapper)
    try:
        from app.domains.quests.api.admin_router import router as quests_admin_router
        app.include_router(quests_admin_router)
    except Exception:
        pass

    # Moderation
    try:
        from app.domains.moderation.api.routers import router as moderation_router
        app.include_router(moderation_router)
    except Exception:
        pass

    # Notifications
    try:
        from app.domains.notifications.api.routers import router as notifications_router
        app.include_router(notifications_router)
    except Exception:
        pass
    # Notifications WS
    try:
        from app.domains.notifications.api.routers import ws_router as notifications_ws_router
        app.include_router(notifications_ws_router)
    except Exception:
        pass
    # Admin Notifications
    try:
        from app.domains.notifications.api.admin_router import router as admin_notifications_router
        app.include_router(admin_notifications_router)
    except Exception:
        pass
    # Admin Notifications Broadcast
    try:
        from app.domains.notifications.api.broadcast_router import router as admin_notifications_broadcast_router
        app.include_router(admin_notifications_broadcast_router)
    except Exception:
        pass

    # Payments
    try:
        from app.domains.payments.api.routers import router as payments_router
        app.include_router(payments_router)
    except Exception:
        pass
    # Payments Admin
    try:
        from app.domains.payments.api_admin import router as payments_admin_router
        app.include_router(payments_admin_router)
    except Exception:
        pass

    # Premium
    try:
        from app.domains.premium.api.routers import router as premium_router
        app.include_router(premium_router)
    except Exception:
        pass
    # Premium Admin
    try:
        from app.domains.premium.api_admin import router as premium_admin_router
        app.include_router(premium_admin_router)
    except Exception:
        pass

    # Media
    try:
        from app.domains.media.api.routers import router as media_router
        app.include_router(media_router)
    except Exception:
        pass

    # Achievements
    try:
        from app.domains.achievements.api.routers import router as achievements_router
        app.include_router(achievements_router)
    except Exception:
        pass

    # Navigation
    try:
        from app.domains.navigation.api.routers import router as navigation_router
        app.include_router(navigation_router)
    except Exception:
        pass
    try:
        from app.domains.navigation.api.transitions_router import router as transitions_router
        app.include_router(transitions_router)
    except Exception:
        pass
    # Navigation public traces
    try:
        from app.domains.navigation.api.traces_router import router as public_traces_router
        app.include_router(public_traces_router)
    except Exception:
        pass
    # Navigation public navigation
    try:
        from app.domains.navigation.api.public_navigation_router import router as public_navigation_router
        app.include_router(public_navigation_router)
    except Exception:
        pass

    # Tags
    try:
        from app.domains.tags.api.routers import router as tags_router
        app.include_router(tags_router)
    except Exception:
        pass

    # Search
    try:
        from app.domains.search.api.routers import router as search_router
        app.include_router(search_router)
    except Exception:
        pass

    # Admin
    try:
        from app.domains.admin.api.routers import router as admin_router
        app.include_router(admin_router)
    except Exception:
        pass
    # Admin flags
    try:
        from app.domains.admin.api.flags_router import router as admin_flags_router
        app.include_router(admin_flags_router)
    except Exception:
        pass
    # Admin cache
    try:
        from app.domains.admin.api.cache_router import router as admin_cache_router
        app.include_router(admin_cache_router)
    except Exception:
        pass
    # Admin dashboard
    try:
        from app.domains.admin.api.dashboard_router import router as admin_dashboard_router
        app.include_router(admin_dashboard_router)
    except Exception:
        pass
    # AI Admin routers are included via app.domains.ai.api.routers aggregator
    # Quests admin validation
    try:
        from app.domains.quests.api.admin_validation_router import router as quests_admin_validation_router
        app.include_router(quests_admin_validation_router)
    except Exception:
        pass
    # Admin users
    try:
        from app.domains.users.api.admin_router import router as admin_users_router
        app.include_router(admin_users_router)
    except Exception:
        pass
    # Admin nodes (nodes)
    try:
        from app.domains.nodes.api.admin_nodes_router import router as admin_nodes_router
        app.include_router(admin_nodes_router)
    except Exception:
        pass
    # Admin transitions
    try:
        from app.domains.navigation.api.admin_transitions_router import router as admin_transitions_router
        app.include_router(admin_transitions_router)
    except Exception:
        pass
    # Admin rate limit
    try:
        from app.domains.admin.api.ratelimit_router import router as admin_ratelimit_router
        app.include_router(admin_ratelimit_router)
    except Exception:
        pass
    # Admin audit
    try:
        from app.domains.admin.api.audit_router import router as admin_audit_router
        app.include_router(admin_audit_router)
    except Exception:
        pass
    # Admin metrics (telemetry)
    try:
        from app.domains.telemetry.api.admin_metrics_router import router as admin_metrics_router
        app.include_router(admin_metrics_router)
    except Exception:
        pass
    # Admin tags
    try:
        from app.domains.tags.api.admin_router import router as admin_tags_router
        app.include_router(admin_tags_router)
    except Exception:
        pass
    # Admin echo (navigation)
    try:
        from app.domains.navigation.api.admin_echo_router import router as admin_echo_router
        app.include_router(admin_echo_router)
    except Exception:
        pass
    # Admin traces (navigation)
    try:
        from app.domains.navigation.api.admin_traces_router import router as admin_traces_router
        app.include_router(admin_traces_router)
    except Exception:
        pass
    # Admin navigation tools
    try:
        from app.domains.navigation.api.admin_navigation_router import router as admin_navigation_router
        app.include_router(admin_navigation_router)
    except Exception:
        pass
    # Admin moderation cases
    try:
        from app.domains.moderation.api.cases_router import router as admin_moderation_cases_router
        app.include_router(admin_moderation_cases_router)
    except Exception:
        pass
    # Admin restrictions
    try:
        from app.domains.moderation.api.restrictions_router import router as admin_restrictions_router
        app.include_router(admin_restrictions_router)
    except Exception:
        pass
    # AI settings/stats are included via app.domains.ai.api.routers aggregator
    # Admin Search
    try:
        from app.domains.search.api.admin_router import router as admin_search_router
        app.include_router(admin_search_router)
    except Exception:
        pass

    # Worlds
    try:
        from app.domains.worlds.api.routers import router as worlds_router
        app.include_router(worlds_router)
    except Exception:
        pass

    # Users
    try:
        from app.domains.users.api.routers import router as users_router
        app.include_router(users_router)
    except Exception:
        pass
