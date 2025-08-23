from pathlib import Path
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, Response

router = APIRouter(tags=["admin-spa"])

DIST_DIR = Path(__file__).resolve().parent.parent.parent / "admin-frontend" / "dist"


@router.get("/admin", include_in_schema=False)
@router.get("/admin/{_:path}", include_in_schema=False)
async def serve_admin_app(request: Request, _: str = "") -> Response:
    # In test environment, always return placeholder to keep tests deterministic
    if os.getenv("TESTING") == "True":
        return HTMLResponse("<h1>Admin SPA build not found</h1>")

    # Отдаём SPA только для HTML-запросов (браузерная навигация).
    # API-запросы (Accept: application/json) не должны попадать сюда.
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
