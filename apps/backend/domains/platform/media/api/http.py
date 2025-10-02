from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except ImportError:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user
from domains.platform.media.application.storage_service import (
    StorageService,
)

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["media"])

    @router.post(
        "/media",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
    )
    async def upload_media(
        req: Request,
        file: UploadFile = File(...),
        _csrf: None = Depends(csrf_protect),
        _claims: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:  # noqa: B008
        c = get_container(req)
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="unsupported_media_type")
        data = await file.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="file_too_large")
        url = StorageService(c.media.storage).save_file(
            io.BytesIO(data), file.filename, file.content_type
        )
        return {"success": 1, "file": {"url": url}, "url": url}

    @router.get("/media/file/{name:path}")
    async def fetch_file(
        req: Request, name: str, _claims: dict[str, Any] = Depends(get_current_user)
    ) -> FileResponse:
        c = get_container(req)
        base = Path(c.media.upload_dir).resolve()
        candidate = (base / name).resolve()
        # Prevent path traversal by ensuring the resolved path stays under base
        try:
            candidate.relative_to(base)
        except ValueError as exc:
            logger.warning("media fetch rejected for invalid path %s: %s", name, exc)
            raise HTTPException(status_code=400, detail="invalid_path") from exc
        file_path = candidate
        if not file_path.exists():
            raise HTTPException(status_code=404)
        # Best-effort content-type guess
        return FileResponse(str(file_path))

    return router
