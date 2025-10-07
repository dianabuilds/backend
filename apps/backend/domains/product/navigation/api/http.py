from __future__ import annotations

from fastapi import APIRouter

from domains.platform.iam.security import require_role_db
from domains.product.navigation.api.admin import register_admin_relations_routes
from domains.product.navigation.api.public import (
    register_relations_routes,
    register_transition_routes,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/navigation")
    register_transition_routes(router)
    register_relations_routes(router)
    admin_required = require_role_db("moderator")
    register_admin_relations_routes(router, admin_required)
    return router
