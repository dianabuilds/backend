from __future__ import annotations

import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.deps import get_storage
from app.services.storage import Storage

router = APIRouter()


@router.post("/media")
async def upload_media(
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    storage: Storage = Depends(get_storage),
):
    """Accept an uploaded image and return its public URL."""
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Unsupported media type")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    url = storage.save(io.BytesIO(data), file.filename, file.content_type)
    return {"url": url}
