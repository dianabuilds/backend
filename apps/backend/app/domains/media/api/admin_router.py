from __future__ import annotations

import io
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.media.infrastructure.deps import get_storage
from app.domains.telemetry.log_events import (
    node_cover_upload_fail,
    node_cover_upload_start,
    node_cover_upload_success,
)
from app.domains.media.application.ports.storage_port import IStorageGateway
from app.domains.media.application.storage_service import StorageService
from app.domains.media.dao import MediaAssetDAO
from app.domains.media.schemas import MediaAssetOut
from app.kernel.db import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/media",
    tags=["admin-media"],
    responses=ADMIN_AUTH_RESPONSES,
)


# Explicit CORS preflight endpoint to avoid auth/validation on OPTIONS
@router.options("")
async def _preflight() -> dict:
    return {"ok": True}


@router.get("", response_model=list[MediaAssetOut], summary="List media assets")
async def list_media_assets(
    limit: int = 100,
    offset: int = 0,
    _: Annotated[object, Depends(require_admin_role())] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[MediaAssetOut]:
    items = await MediaAssetDAO.list(db, limit=limit, offset=offset)
    return [MediaAssetOut.model_validate(i) for i in items]


@router.post("", summary="Upload media asset")
async def upload_media_asset(
    file: Annotated[UploadFile, File(...)] = ...,  # noqa: B008
    current_user: Annotated["User", Depends(require_admin_role())] = ...,  # noqa: B008
    storage: Annotated[IStorageGateway, Depends(get_storage)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    from app.domains.users.infrastructure.models.user import User  # local import

    node_cover_upload_start(str(getattr(current_user, "id", None)))
    try:
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Unsupported media type")
        data = await file.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")
        service = StorageService(storage)
        url = service.save_file(io.BytesIO(data), file.filename, file.content_type)
        asset = await MediaAssetDAO.create(
            db,
            profile_id=getattr(current_user, "id", None),
            url=url,
            type=file.content_type,
            metadata_json=None,
        )
        await db.commit()
    except Exception as exc:
        node_cover_upload_fail(str(getattr(current_user, "id", None)), str(exc))
        raise
    node_cover_upload_success(str(getattr(current_user, "id", None)))
    return {
        "success": 1,
        "file": {"url": url},
        "url": url,
        "asset": MediaAssetOut.model_validate(asset),
    }


