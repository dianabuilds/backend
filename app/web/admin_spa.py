from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, Response

router = APIRouter(tags=["admin-spa"])

DIST_DIR = Path(__file__).resolve().parent.parent.parent / "admin-frontend" / "dist"

@router.get("/admin", include_in_schema=False)
@router.get("/admin/{_:path}", include_in_schema=False)
async def serve_admin_app(_: str = "") -> Response:
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Admin SPA build not found</h1>")
