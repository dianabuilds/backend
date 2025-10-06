from __future__ import annotations

from fastapi import APIRouter

from .analytics import register_analytics_routes
from .bans import register_comment_ban_routes
from .comments import register_comment_routes
from .moderation import register_moderation_routes
from .nodes import register_nodes_routes


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin/nodes", tags=["admin-nodes"])
    register_nodes_routes(router)
    register_comment_routes(router)
    register_comment_ban_routes(router)
    register_analytics_routes(router)
    register_moderation_routes(router)
    return router
