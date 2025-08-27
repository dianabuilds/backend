"""Deprecated quest admin endpoints.

These routes exist for backwards compatibility and redirect to the new
generic node administration endpoints.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/admin/quests", tags=["admin"])


@router.api_route(
    "",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def redirect_quests(request: Request, path: str = ""):
    """Redirect legacy quest admin requests to node endpoints."""

    if path == "":
        # Listing quests used to be ``/admin/quests``.
        new_url = request.url.replace(path="/admin/nodes")
        new_url = new_url.include_query_params(type="quest")
    elif path == "create":
        # ``/admin/quests/create`` -> ``/admin/nodes/quest``
        new_url = request.url.replace(path="/admin/nodes/quest")
    else:
        new_path = request.url.path.replace("/admin/quests", "/admin/nodes/quest", 1)
        new_url = request.url.replace(path=new_path)
    return RedirectResponse(str(new_url), status_code=307)
