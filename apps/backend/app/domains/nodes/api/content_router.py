"""CRUD API router for node content items.

This module exposes the administrative content management endpoints under
``app.domains.nodes.api``.  The actual implementation lives in
``app.domains.nodes.content_admin_router``.  Re-exporting the router here makes
it discoverable alongside other domain API routers.
"""

from app.domains.nodes.content_admin_router import router

__all__ = ["router"]
