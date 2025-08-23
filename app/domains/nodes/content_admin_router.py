from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import app.domains.quests.validation  # noqa: F401
from app.core.db.session import get_db
from app.domains.tags.models import Tag
from app.schemas.node_common import ContentStatus
from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor
from app.validation.base import run_validators

from .dao import NodeItemDAO
from .models import NodeItem

router = APIRouter(
    prefix="/admin/nodes",
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
        select(NodeItem).where(NodeItem.workspace_id == workspace_id)
    )
    items = result.scalars().all()

    counts: dict[str, int] = {
        ContentStatus.draft.value: 0,
        ContentStatus.in_review.value: 0,
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
        "reviews": counts.get(ContentStatus.in_review.value, 0),
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


@router.get("/all", summary="List nodes")
async def list_nodes(
    workspace_id: UUID,
    node_type: str | None = None,
    status: ContentStatus | None = None,
    tag: UUID | None = None,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(NodeItem).where(NodeItem.workspace_id == workspace_id)
    if node_type:
        stmt = stmt.where(NodeItem.type == node_type)
    if status:
        stmt = stmt.where(NodeItem.status == status)
    if tag:
        stmt = stmt.join(NodeItem.tags).where(Tag.id == tag)
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


@router.post("/{node_type}", summary="Create node item")
async def create_node(
    node_type: str,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    item = await NodeItemDAO.create(
        db,
        workspace_id=workspace_id,
        type=node_type,
        slug=f"{node_type}-{uuid4().hex[:8]}",
        title=f"New {node_type}",
    )
    await db.commit()
    return {
        "workspace_id": str(workspace_id),
        "type": item.type,
        "id": str(item.id),
    }


@router.get("/{node_type}/{node_id}", summary="Get node item")
async def get_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": node_type,
        "id": str(node_id),
        "workspace_id": str(workspace_id),
    }


@router.patch("/{node_type}/{node_id}", summary="Update node item")
async def update_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": node_type,
        "id": str(node_id),
        "workspace_id": str(workspace_id),
        "action": "update",
    }


@router.post("/{node_type}/{node_id}/publish", summary="Publish node item")
async def publish_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
) -> dict:
    return {
        "type": node_type,
        "id": str(node_id),
        "workspace_id": str(workspace_id),
        "status": "published",
    }


@router.post("/{node_type}/{node_id}/validate", summary="Validate node item")
async def validate_node_item(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> dict:
    report = await run_validators(node_type, node_id, db)
    return {
        "type": node_type,
        "id": str(node_id),
        "workspace_id": str(workspace_id),
        "report": report,
    }
