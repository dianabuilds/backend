"""Deprecated quest admin endpoints.

These routes exist for backwards compatibility and redirect to the new
generic node administration endpoints.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/admin/quests", tags=["admin"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def redirect_quests(path: str, request: Request):
    """Redirect legacy quest admin requests to node endpoints."""

    new_path = request.url.path.replace("/admin/quests", "/admin/nodes/quest", 1)
    new_url = request.url.replace(path=new_path)
    return RedirectResponse(str(new_url), status_code=307)

