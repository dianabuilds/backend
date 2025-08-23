from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.models import NodeItem
from app.security import ADMIN_AUTH_RESPONSES, require_ws_editor, auth_user
from app.domains.users.infrastructure.models.user import User

router = APIRouter(
    prefix="/admin/nodes",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)

navcache = NavigationCacheService(CoreCacheAdapter())


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


@router.get("", summary="List nodes")
async def list_nodes(
    workspace_id: UUID,
    type: str,
    page: int = 1,
    per_page: int = 10,
    q: str | None = None,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    if q:
        items = await svc.search(workspace_id, type, q, page=page, per_page=per_page)
    else:
        items = await svc.list(workspace_id, type, page=page, per_page=per_page)
    return {"items": [_serialize(i) for i in items]}


@router.post("/{node_type}", summary="Create node item")
async def create_node(
    node_type: str,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    current_user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    item = await svc.create(workspace_id, node_type, actor_id=current_user.id)
    return _serialize(item)


@router.get("/{node_type}/{node_id}", summary="Get node item")
async def get_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    item = await svc.get(workspace_id, node_type, node_id)
    return _serialize(item)


@router.patch("/{node_type}/{node_id}", summary="Update node item")
async def update_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    request: Request,
    payload: dict,
    _: object = Depends(require_ws_editor),
    current_user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    item = await svc.update(
        workspace_id,
        node_type,
        node_id,
        payload,
        actor_id=current_user.id,
        request=request,
    )
    return _serialize(item)


@router.post("/{node_type}/{node_id}/publish", summary="Publish node item")
async def publish_node(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    request: Request,
    _: object = Depends(require_ws_editor),
    current_user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    item = await svc.publish(
        workspace_id,
        node_type,
        node_id,
        actor_id=current_user.id,
        request=request,
    )
    return _serialize(item)


@router.post("/{node_type}/{node_id}/validate", summary="Validate node item")
async def validate_node_item(
    node_type: str,
    node_id: UUID,
    workspace_id: UUID,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    svc = NodeService(db, navcache)
    report = await svc.validate(node_type, node_id)
    return {"report": report}
