from __future__ import annotations

from fastapi import APIRouter

# Reuse the existing admin nodes routers, but expose them under the
# profile-centric prefix. Handlers inside use the path parameter name
# "account_id"; keeping the same name here allows reuse without copy.
from app.domains.nodes.content_admin_router import id_router, type_router
from app.security import ADMIN_AUTH_RESPONSES

router = APIRouter(
    prefix="/admin/profiles/{account_id}/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

# Register the reused sub-routers under the new prefix.
router.include_router(id_router)
router.include_router(type_router)

