from __future__ import annotations

import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.deps import get_storage
from app.core.log_events import (
    node_cover_upload_fail,
    node_cover_upload_start,
    node_cover_upload_success,
)
from app.domains.media.application.ports.storage_port import IStorageGateway
from app.domains.media.application.storage_service import StorageService
from app.providers.db.session import get_db


async def require_profile_optional(
    user=Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Profile-centric mode: no extra membership checks."""
    return None

router = APIRouter(tags=["media"])


@router.post("/media")
async def upload_media(
    file: Annotated[UploadFile, File(...)] = ...,  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    storage: Annotated[IStorageGateway, Depends(get_storage)] = ...,  # noqa: B008
    _member: Annotated[object, Depends(require_profile_optional)] = ...,
):
    """Accept an uploaded image and return its public URL."""
    node_cover_upload_start(str(getattr(user, "id", None)))
    try:
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Unsupported media type")
        data = await file.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")
        service = StorageService(storage)
        url = service.save_file(io.BytesIO(data), file.filename, file.content_type)
    except Exception as exc:
        node_cover_upload_fail(str(getattr(user, "id", None)), str(exc))
        raise
    node_cover_upload_success(str(getattr(user, "id", None)))
    # Совместимый с Editor.js ImageTool формат + поле url для обратной совместимости
    return {"success": 1, "file": {"url": url}, "url": url}


# Алиас для админки: поддерживаем POST /admin/media
@router.post("/admin/media")
async def upload_media_admin(
    file: Annotated[UploadFile, File(...)] = ...,  # noqa: B008
    user=Depends(get_current_user),  # noqa: B008
    storage: Annotated[IStorageGateway, Depends(get_storage)] = ...,  # noqa: B008
    _member: Annotated[object, Depends(require_profile_optional)] = ...,
):
    return await upload_media(file=file, user=user, storage=storage, _member=_member)
