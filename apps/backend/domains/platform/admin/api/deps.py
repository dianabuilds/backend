from __future__ import annotations

from fastapi import Request

from ..service import AdminService
from ..wires import AdminContainer


def get_admin_service(request: Request) -> AdminService:
    container = getattr(request.app.state, "container", None)  # type: ignore[attr-defined]
    if not isinstance(container, AdminContainer):
        admin = getattr(container, "admin", None)
        if admin is None:
            raise RuntimeError("Admin container is not configured")
        return admin.service
    return container.service
