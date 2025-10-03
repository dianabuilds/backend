from __future__ import annotations

from fastapi import APIRouter

from .admin_analytics import register_analytics_routes
from .admin_bans import register_comment_ban_routes
from .admin_comments import register_comment_routes
from .admin_moderation import register_moderation_routes
from .admin_nodes import register_nodes_routes


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin/nodes", tags=["admin-nodes"])
    register_nodes_routes(router)
    register_comment_routes(router)
    register_comment_ban_routes(router)
    register_analytics_routes(router)
    register_moderation_routes(router)
    return router
