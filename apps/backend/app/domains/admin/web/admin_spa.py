from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

router = APIRouter(tags=["admin-spa"])

# Navigate up to backend/apps/backend root, then to 'admin/dist'
DIST_DIR = Path(__file__).resolve().parents[4] / "admin" / "dist"


@router.get("/admin", include_in_schema=False)
@router.get("/admin/{_:path}", include_in_schema=False)
async def serve_admin_app(request: Request, _: str = "") -> Response:
    accept = ""
    try:
        accept = request.headers.get("accept", "")
    except Exception:
        accept = ""
    accept_lower = accept.lower()
    if "text/html" not in accept_lower:
        return Response(status_code=404)

    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Admin SPA build not found</h1>")


__all__ = ["router", "serve_admin_app"]
