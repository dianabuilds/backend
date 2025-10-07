from __future__ import annotations

import logging

from fastapi import APIRouter

from domains.product.nodes.api.public import (
    register_catalog_mutation_routes,
    register_catalog_routes,
    register_comment_routes,
    register_engagement_routes,
)

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/nodes")
    register_catalog_routes(router)
    register_catalog_mutation_routes(router)
    register_engagement_routes(router)
    register_comment_routes(router)
    return router
