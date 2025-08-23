from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import sqlalchemy as sa
from uuid import uuid4

from app.core.db.session import get_db
from app.schemas.content_common import ContentStatus
from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor
from app.domains.tags.models import Tag
from .models import ContentItem
from app.domains.content.dao import ContentItemDAO
from app.validation.base import run_validators
import app.domains.quests.validation  # noqa: F401

router = APIRouter(
    prefix="/admin/content",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/", summary="Content dashboard")
async def content_dashboard(
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(ContentItem).where(ContentItem.workspace_id == workspace_id)
    )
    items = result.scalars().all()

    counts: dict[str, int] = {
        ContentStatus.draft.value: 0,
        ContentStatus.review.value: 0,
        ContentStatus.published.value: 0,
    }
    for item in items:
        counts[item.status.value] = counts.get(item.status.value, 0) + 1

    latest_items = sorted(items, key=lambda x: x.updated_at, reverse=True)[:5]

    validation_errors = []
    for item in items:
        report = await run_validators(item.type, item.id, db)
        if report.errors:
            validation_errors.append(
                {
                    "id": str(item.id),
                    "type": item.type,
                    "errors": report.errors,
                }
            )

    return {
        "workspace_id": str(workspace_id),
        "drafts": counts.get(ContentStatus.draft.value, 0),
        "reviews": counts.get(ContentStatus.review.value, 0),
        "published": counts.get(ContentStatus.published.value, 0),
        "latest": [
            {
                "id": str(item.id),
                "type": item.type,
                "status": item.status.value,
            }
            for item in latest_items
        ],
        "validation_errors": validation_errors,
    }


@router.get("/all", summary="List content items")
async def list_content(
    workspace_id: UUID,
    content_type: str | None = None,
    status: ContentStatus | None = None,
    tag: UUID | None = None,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(ContentItem).where(ContentItem.workspace_id == workspace_id)
    if content_type:
        stmt = stmt.where(ContentItem.type == content_type)
    if status:
        stmt = stmt.where(ContentItem.status == status)
    if tag:
        stmt = stmt.join(ContentItem.tags).where(Tag.id == tag)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {
        "workspace_id": str(workspace_id),
        "items": [
            {
                "id": str(item.id),
                "type": item.type,
                "status": item.status.value,
            }
            for item in items
        ],
    }


@router.post("/{content_type}", summary="Create content item")
async def create_content(
    content_type: str,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    item = await ContentItemDAO.create(
        db,
        workspace_id=workspace_id,
        type=content_type,
        slug=f"{content_type}-{uuid4().hex[:8]}",
        title=f"New {content_type}",
    )
    await db.commit()
    return {
        "workspace_id": str(workspace_id),
        "type": item.type,
        "id": str(item.id),
    }


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


@router.post("/{content_type}/{content_id}/validate", summary="Validate content item")
async def validate_content_item(
    content_type: str,
    content_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    report = await run_validators(content_type, content_id, db)
    return {"type": content_type, "id": str(content_id), "workspace_id": str(workspace_id), "report": report}
