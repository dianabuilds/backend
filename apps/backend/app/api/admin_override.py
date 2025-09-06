from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_optional
from app.domains.admin.application.feature_flag_service import (
    FeatureFlagKey,
    get_effective_flags,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db


async def admin_override_dependency(
    request: Request,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> None:
    """Parse admin override headers if feature flag enabled."""
    header = request.headers.get("X-Admin-Override")
    reason = request.headers.get("X-Override-Reason")
    if not (header and header.lower() == "on" and reason):
        return
    preview_header = request.headers.get("X-Feature-Flags")
    flags = await get_effective_flags(db, preview_header, current_user)
    if FeatureFlagKey.ADMIN_OVERRIDE.value in flags:
        request.state.admin_override = True
        request.state.override_reason = reason


def register_admin_override(app: FastAPI) -> None:
    """Attach admin override dependency to all GET/PUT/DELETE routes."""
    dep = Depends(admin_override_dependency)
    for route in app.routes:
        if isinstance(route, APIRoute) and {"GET", "PUT", "DELETE"} & route.methods:
            route.dependencies.append(dep)
