from __future__ import annotations

import io
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.deps import get_storage
from app.core.log_events import (
    node_cover_upload_fail,
    node_cover_upload_start,
    node_cover_upload_success,
)
from app.domains.media.application.ports.storage_port import IStorageGateway
from app.domains.media.application.storage_service import StorageService
from app.domains.media.dao import MediaAssetDAO
from app.domains.media.schemas import MediaAssetOut
from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor

router = APIRouter(
    prefix="/admin/media",
    tags=["admin-media"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[MediaAssetOut], summary="List media assets")
async def list_media_assets(
    workspace_id: UUID,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> list[MediaAssetOut]:
    items = await MediaAssetDAO.list(
        db,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )
    return [MediaAssetOut.model_validate(i) for i in items]


@router.post("", summary="Upload media asset")
async def upload_media_asset(
    workspace_id: UUID,
    file: Annotated[UploadFile, File(...)] = ...,  # noqa: B008
    _: Annotated[object, Depends(require_ws_editor)] = ...,  # noqa: B008
    storage: Annotated[IStorageGateway, Depends(get_storage)] = ...,  # noqa: B008
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    node_cover_upload_start(str(getattr(_, "id", None)))
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
            workspace_id=workspace_id,
            url=url,
            type=file.content_type,
            metadata_json=None,
        )
        await db.commit()
    except Exception as exc:
        node_cover_upload_fail(str(getattr(_, "id", None)), str(exc))
        raise
    node_cover_upload_success(str(getattr(_, "id", None)))
    return {
        "success": 1,
        "file": {"url": url},
        "url": url,
        "asset": MediaAssetOut.model_validate(asset),
    }
