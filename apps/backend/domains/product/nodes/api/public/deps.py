from __future__ import annotations

from app.api_gateway.routers import get_container
from fastapi import Depends

from domains.product.nodes.application.use_cases import (
    build_catalog_mutations_service,
    build_comments_service,
    build_engagement_service,
)


def get_catalog_mutations_service(container=Depends(get_container)):
    return build_catalog_mutations_service(container)


def get_engagement_service(container=Depends(get_container)):
    return build_engagement_service(container)


def get_comments_service(container=Depends(get_container)):
    return build_comments_service(container)
