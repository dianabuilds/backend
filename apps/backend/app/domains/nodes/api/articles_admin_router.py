from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.domains.nodes.service import publish_content
from app.schemas.quest_editor import ValidateResult
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/workspaces/{workspace_id}/articles",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

admin_required = require_admin_role()


class PublishIn(BaseModel):
    access: Literal["everyone", "premium_only", "early_access"] = "everyone"
    cover: str | None = None


def _serialize(item: NodeItem) -> dict:
    return {
        "id": str(item.id),
        "workspace_id": str(item.workspace_id),
        "type": item.type,
        "slug": item.slug,
        "title": item.title,
        "summary": item.summary,
        "status": item.status.value,
    }


@router.post("", summary="Create article (admin)")
async def create_article(
    payload: dict | None = None,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.create(workspace_id, "article", actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_id}", summary="Get article (admin)")
async def get_article(
    node_id: UUID,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.get(workspace_id, "article", node_id)
    return _serialize(item)


@router.patch("/{node_id}", summary="Update article (admin)")
async def update_article(
    node_id: UUID,
    payload: dict,
    workspace_id: UUID = Path(...),  # noqa: B008
    next: int = Query(0),
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.update(
        workspace_id,
        "article",
        node_id,
        payload,
        actor_id=current_user.id,
    )
    if next:
        from app.domains.telemetry.application.ux_metrics_facade import ux_metrics

        ux_metrics.inc_save_next()
    return _serialize(item)


@router.post("/{node_id}/publish", summary="Publish article (admin)")
async def publish_article(
    node_id: UUID,
    payload: PublishIn | None = None,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    svc = NodeService(db)
    item = await svc.publish(
        workspace_id,
        "article",
        node_id,
        actor_id=current_user.id,
        access=(payload.access if payload else "everyone"),
        cover=(payload.cover if payload else None),
    )
    await publish_content(
        node_id=item.id,
        slug=item.slug,
        author_id=current_user.id,
        workspace_id=workspace_id,
    )
    return _serialize(item)


@router.post("/{node_id}/validate", summary="Validate article (admin)", response_model=ValidateResult)
async def validate_article(
    node_id: UUID,
    workspace_id: UUID = Path(...),  # noqa: B008
    current_user=Depends(admin_required),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ValidateResult:
    svc = NodeService(db)
    await svc.get(workspace_id, "article", node_id)
    return ValidateResult(ok=True, errors=[], warnings=[])
