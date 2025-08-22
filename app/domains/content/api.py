from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor

router = APIRouter(
    prefix="/admin/content",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("/{content_type}", summary="Create content item")
async def create_content(
    content_type: str,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {"type": content_type, "workspace_id": str(workspace_id)}


@router.get("/{content_type}/{content_id}", summary="Get content item")
async def get_content(
    content_type: str,
    content_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": content_type,
        "id": str(content_id),
        "workspace_id": str(workspace_id),
    }


@router.patch("/{content_type}/{content_id}", summary="Update content item")
async def update_content(
    content_type: str,
    content_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": content_type,
        "id": str(content_id),
        "workspace_id": str(workspace_id),
        "action": "update",
    }


@router.post("/{content_type}/{content_id}/publish", summary="Publish content item")
async def publish_content(
    content_type: str,
    content_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": content_type,
        "id": str(content_id),
        "workspace_id": str(workspace_id),
        "status": "published",
    }
